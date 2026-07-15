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


def save_config(out_dir: str | Path, *, state_dim: int, d_model: int, n_prefix: int,
                hidden: int, base_model: str) -> None:
    """Record the shapes needed to rebuild the conditioner at inference time."""
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
