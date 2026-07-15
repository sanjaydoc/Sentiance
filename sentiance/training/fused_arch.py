"""The fused-mind conditioning module — shared by the trainer and the backend.

The fused mind (ADR 0005) turns the numeric mind-state ``m_t`` (state_vector.py)
into a small set of **soft prefix tokens** that are prepended to the transformer's
input embeddings. The base model + LoRA then generate the next thought *conditioned
on the actual cognitive state* — appraise/feel/drives/bonds/anger/anticipation as
a differentiable signal, not prose. Training back-propagates the language loss
through the LoRA weights **and** this encoder, so the mapping (state → language) is
learned end-to-end.

Putting the definition here — imported lazily, torch only touched inside the
factory — means ``scripts/finetune_fused.py`` (which trains it) and
``sentiance/mind/fused_model.py`` (which runs it live) build the **exact same
module**, so the numbers the model learns on are the numbers it later runs on.

Honest stance (ADR 0002): this is integration and end-to-end learnability, not
phenomenality. The prefix tokens are a learned function of functional variables;
nothing here is claimed to be experienced.
"""

from __future__ import annotations

import json
from pathlib import Path

# Files the trainer writes into the fused-model dir alongside the LoRA adapter.
ENCODER_FILE = "state_encoder.pt"
CONFIG_FILE = "fused_config.json"

# How m_t reaches the transformer:
#   "prefix" — soft tokens prepended to the input (shallow; the model can ignore it)
#   "film"   — per-layer affine (γ,β) modulation of hidden states (deep; injected
#              throughout the stack, much harder to ignore — ADR 0005)
CONDITIONING_PREFIX = "prefix"
CONDITIONING_FILM = "film"


def build_conditioner(state_dim: int, d_model: int, n_prefix: int = 8, hidden: int = 256):
    """A small MLP: ``m_t`` (B, state_dim) → ``n_prefix`` soft tokens (B, n_prefix,
    d_model). Torch is imported here so importing this module needs no ML deps."""
    from torch import nn  # noqa: PLC0415

    class StateConditioner(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.state_dim = state_dim
            self.d_model = d_model
            self.n_prefix = n_prefix
            self.net = nn.Sequential(
                nn.Linear(state_dim, hidden),
                nn.GELU(),
                nn.Linear(hidden, hidden),
                nn.GELU(),
                nn.Linear(hidden, n_prefix * d_model),
            )
            # Start near zero so an untrained conditioner barely perturbs the base
            # model — training grows the signal rather than fighting a random one.
            last = self.net[-1]
            nn.init.zeros_(last.weight)
            nn.init.zeros_(last.bias)

        def forward(self, state):  # state: (B, state_dim) float
            out = self.net(state)
            return out.view(state.shape[0], self.n_prefix, self.d_model)

    return StateConditioner()


def prepend_prefix(input_embeds, attention_mask, prefix_embeds):
    """Prepend the ``n_prefix`` soft tokens to token embeddings and extend the mask.

    Returns ``(inputs_embeds, attention_mask)`` ready for the base model — the same
    assembly at train and inference time."""
    import torch  # noqa: PLC0415

    fused = torch.cat([prefix_embeds.to(input_embeds.dtype), input_embeds], dim=1)
    b, p = prefix_embeds.shape[0], prefix_embeds.shape[1]
    pre = torch.ones(b, p, dtype=attention_mask.dtype, device=attention_mask.device)
    mask = torch.cat([pre, attention_mask], dim=1)
    return fused, mask


# --- FiLM: per-layer affine modulation of hidden states ---------------------


def build_film(state_dim: int, d_model: int, n_layers: int, hidden: int = 256):
    """An MLP: ``m_t`` (B, state_dim) → per-layer ``(γ, β)`` each (B, n_layers,
    d_model). The output head is zero-initialised so an untrained FiLM is the
    identity (``h·(1+0)+0``) and training grows the modulation from there."""
    from torch import nn  # noqa: PLC0415

    class FiLM(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.n_layers = n_layers
            self.d_model = d_model
            self.trunk = nn.Sequential(
                nn.Linear(state_dim, hidden), nn.GELU(),
                nn.Linear(hidden, hidden), nn.GELU(),
            )
            self.head = nn.Linear(hidden, n_layers * 2 * d_model)
            nn.init.zeros_(self.head.weight)
            nn.init.zeros_(self.head.bias)

        def forward(self, state):  # (B, state_dim) → gamma, beta : (B, n_layers, d_model)
            gb = self.head(self.trunk(state)).view(state.shape[0], self.n_layers, 2, self.d_model)
            return gb[:, :, 0, :], gb[:, :, 1, :]

    return FiLM()


def find_decoder_layers(model):
    """Locate the transformer's decoder-layer ``ModuleList`` (works through a PEFT
    wrapper): the list whose entries carry a ``self_attn`` — i.e. the blocks."""
    from torch import nn  # noqa: PLC0415

    for module in model.modules():
        if isinstance(module, nn.ModuleList) and len(module) >= 2 and all(
            hasattr(layer, "self_attn") for layer in module
        ):
            return module
    raise RuntimeError("could not locate decoder layers for FiLM conditioning")


class FiLMController:
    """Registers a forward hook on each decoder layer that modulates its hidden
    states by ``h·(1+γ_i)+β_i`` using the currently-set ``(γ, β)``. Set them before
    each forward; the hooks are part of the autograd graph, so gradients reach FiLM."""

    def __init__(self, layers) -> None:
        self._layers = list(layers)
        self._handles: list = []
        self._gamma = None
        self._beta = None

    @property
    def n_layers(self) -> int:
        return len(self._layers)

    def set(self, gamma, beta) -> None:
        self._gamma, self._beta = gamma, beta

    def clear(self) -> None:
        self._gamma = self._beta = None

    def attach(self) -> FiLMController:
        for idx, layer in enumerate(self._layers):
            self._handles.append(layer.register_forward_hook(self._make_hook(idx)))
        return self

    def detach(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles = []

    def _make_hook(self, idx: int):
        def hook(module, args, output):
            if self._gamma is None:
                return output
            hs = output[0] if isinstance(output, tuple) else output
            g = self._gamma[:, idx, :].unsqueeze(1).to(hs.dtype)  # (B,1,d) broadcast over seq
            b = self._beta[:, idx, :].unsqueeze(1).to(hs.dtype)
            hs = hs * (1 + g) + b
            return (hs, *tuple(output[1:])) if isinstance(output, tuple) else hs

        return hook


def save_config(out_dir: str | Path, *, state_dim: int, d_model: int, n_prefix: int,
                hidden: int, base_model: str, state_blind: bool = True,
                conditioning: str = CONDITIONING_PREFIX, n_layers: int = 0) -> None:
    """Record everything needed to rebuild the conditioner at inference time:
    shapes, ``state_blind`` (matching prompt), and ``conditioning`` (prefix|film,
    with ``n_layers`` for film) so the backend/eval reconstruct the same wiring."""
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / CONFIG_FILE).write_text(
        json.dumps(
            {
                "state_dim": state_dim,
                "d_model": d_model,
                "n_prefix": n_prefix,
                "hidden": hidden,
                "base_model": base_model,
                "state_blind": state_blind,
                "conditioning": conditioning,
                "n_layers": n_layers,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_config(model_dir: str | Path) -> dict | None:
    """The fused config written by the trainer, or None if this isn't a fused dir."""
    p = Path(model_dir) / CONFIG_FILE
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None
