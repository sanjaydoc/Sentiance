"""The fused mind as an inner voice — a cognition-conditioned transformer.

This is the ``fused`` cognition backend (ADR 0005). Unlike ``finetuned`` (Path A),
which only reads the mind-state as text in the prompt, this backend feeds the
**numeric** mind-state ``m_t`` (the whole cognitive cycle — appraise, feel, drives,
bonds, anger, anticipation…) into the transformer as trainable soft-prefix tokens.
The base model + LoRA were trained end-to-end with the same state encoder, so the
faculties **causally shape** what she thinks next, through weights rather than words.

Everything heavy (torch, transformers, peft) is imported lazily and only when this
backend is selected. If the model dir, the trained encoder, or the ML deps aren't
there — or generation errors — it **degrades gracefully** to the offline voice, so
the cognitive cycle never stalls and the tests need no ML deps.

Honest stance (ADR 0002): conditioning generation on functional state buys
integration, not phenomenal experience. Nothing here is claimed to be felt.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sentiance.mind.cognition import (
    Cognition,
    OnToken,
    SimulatedCognition,
    _compose_prompt,
    _thought_to_stimulus,
)
from sentiance.mind.state_vector import encode_state

if TYPE_CHECKING:
    from sentiance.mind.memory import Memory
    from sentiance.mind.state import ContentSource, SelfModelState, Stimulus


class FusedCognition:
    """Inner voice from a base+LoRA model conditioned on the live ``m_t`` each tick."""

    def __init__(
        self,
        *,
        model_path: str = "models/sentiance-fused",
        base_model: str = "Qwen/Qwen2.5-0.5B-Instruct",
        max_tokens: int = 128,
        fallback: Cognition | None = None,
    ) -> None:
        self.model_path = model_path
        self.base_model = base_model
        self.max_tokens = max_tokens
        self.fallback: Cognition = fallback or SimulatedCognition()
        self._loaded: tuple | None = None  # (model, tokenizer, conditioner, torch, cfg)
        self._failed = False

    def deliberate(
        self,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        memory: Memory,
        on_token: OnToken | None = None,
    ) -> Stimulus | None:
        loaded = self._ensure()
        if loaded is None:
            return self.fallback.deliberate(moment_content, source, self_model, memory, on_token)
        try:
            text = self._generate(loaded, self_model, moment_content, source)
        except Exception:  # noqa: BLE001 - the inner loop must survive any model error
            return self.fallback.deliberate(moment_content, source, self_model, memory, on_token)
        if on_token is not None and text:
            on_token(text)  # non-streaming: hand the whole thought over at once
        return _thought_to_stimulus(text, self_model.affect)

    # --- internals --------------------------------------------------------

    def _ensure(self) -> tuple | None:
        if self._loaded is not None:
            return self._loaded
        if self._failed:
            return None
        try:
            import torch  # noqa: PLC0415
            from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

            from sentiance.training.fused_arch import (  # noqa: PLC0415
                CONDITIONING_FILM,
                ENCODER_FILE,
                FiLMController,
                build_conditioner,
                build_film,
                find_decoder_layers,
                load_config,
            )

            cfg = load_config(self.model_path)
            if cfg is None:
                self._failed = True  # not a fused model dir — nothing to condition on
                return None

            path = self.model_path
            is_adapter = (Path(path) / "adapter_config.json").exists()
            base_id = cfg.get("base_model") or self.base_model
            on_cuda = torch.cuda.is_available()
            tokenizer = AutoTokenizer.from_pretrained(base_id)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            model = AutoModelForCausalLM.from_pretrained(
                base_id,
                torch_dtype=torch.float16 if on_cuda else torch.float32,
                device_map="auto" if on_cuda else None,
            )
            if is_adapter:
                from peft import PeftModel  # noqa: PLC0415

                model = PeftModel.from_pretrained(model, path)
            model.eval()

            kind = cfg.get("conditioning", "prefix")
            controller = None
            if kind == CONDITIONING_FILM:
                layers = find_decoder_layers(model)
                conditioner = build_film(
                    state_dim=cfg["state_dim"], d_model=cfg["d_model"],
                    n_layers=cfg.get("n_layers") or len(layers), hidden=cfg.get("hidden", 256),
                )
                controller = FiLMController(layers).attach()
            else:
                conditioner = build_conditioner(
                    state_dim=cfg["state_dim"], d_model=cfg["d_model"],
                    n_prefix=cfg["n_prefix"], hidden=cfg.get("hidden", 256),
                )
            weights = torch.load(Path(path) / ENCODER_FILE, map_location="cpu")
            conditioner.load_state_dict(weights)
            conditioner.to(model.device).to(model.dtype)
            conditioner.eval()

            self._loaded = (model, tokenizer, conditioner, torch, cfg, controller)
        except Exception:  # noqa: BLE001 - missing libs / model / encoder → fall back
            self._failed = True
            return None
        return self._loaded

    def _generate(
        self,
        loaded: tuple,
        self_model: SelfModelState,
        moment_content: str,
        source: ContentSource,
    ) -> str:
        model, tokenizer, conditioner, torch, cfg, controller = loaded
        from sentiance.training.fused_arch import prepend_prefix  # noqa: PLC0415

        # Match the prompt the model was trained on: a state-blind model gets its
        # state only from m_t, so the prompt must omit the felt-state text.
        system, user = _compose_prompt(
            self_model, moment_content, source, state_blind=cfg.get("state_blind", False)
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        m_t = encode_state(self_model, source)  # the live mind-state
        state = torch.tensor([m_t], dtype=model.dtype, device=model.device)
        gen = {"max_new_tokens": self.max_tokens, "do_sample": True, "temperature": 0.8,
               "top_p": 0.9, "pad_token_id": tokenizer.pad_token_id}

        with torch.no_grad():
            if controller is not None:  # FiLM: modulate every layer, generate normally
                gamma, beta = conditioner(state)
                controller.set(gamma, beta)
                out = model.generate(input_ids=inputs["input_ids"],
                                     attention_mask=inputs["attention_mask"], **gen)
                controller.clear()
                new = out[0][inputs["input_ids"].shape[1]:]  # drop the prompt tokens
                return tokenizer.decode(new, skip_special_tokens=True).strip()
            # prefix: state → soft tokens prepended to the embeddings
            tok_embeds = model.get_input_embeddings()(inputs["input_ids"])
            prefix = conditioner(state)
            inputs_embeds, attention_mask = prepend_prefix(
                tok_embeds, inputs["attention_mask"], prefix
            )
            out = model.generate(inputs_embeds=inputs_embeds, attention_mask=attention_mask, **gen)
        # With inputs_embeds, generate returns only the newly-generated tokens.
        return tokenizer.decode(out[0], skip_special_tokens=True).strip()
