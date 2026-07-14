"""A locally-run fine-tuned voice — the small model trained *by* Sentiance.

Once you've fine-tuned a small base model on her traces (Path A — see
``scripts/finetune.py`` and the README), this backend loads it in-process and uses
it as the mind's inner voice, exactly where qwen/Claude sit. It reuses the shared
prompt builder, so the trained model is dropped into the same architecture — the
self-model, affect, and memory still surround it.

Everything heavy (torch, transformers, peft) is imported lazily and only when this
backend is actually selected. If those aren't installed, or the model directory
isn't there, or generation errors, it **degrades gracefully** to the offline
voice — so the cognitive cycle never stalls and the test suite needs no ML deps.

Runs on your GPU when CUDA is available (a 0.5B model needs ~1 GB VRAM to
generate), otherwise on CPU — slower, but fine for a stream of thought.
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

if TYPE_CHECKING:
    from sentiance.mind.memory import Memory
    from sentiance.mind.state import ContentSource, SelfModelState, Stimulus


class TransformersCognition:
    """Inner voice from a locally-loaded (optionally LoRA-adapted) small model."""

    def __init__(
        self,
        *,
        model_path: str = "models/sentiance-voice",
        base_model: str = "Qwen/Qwen2.5-0.5B-Instruct",
        max_tokens: int = 128,
        fallback: Cognition | None = None,
    ) -> None:
        self.model_path = model_path
        self.base_model = base_model
        self.max_tokens = max_tokens
        self.fallback: Cognition = fallback or SimulatedCognition()
        self._pipe: object | None = None  # (model, tokenizer), built lazily
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
        if self._pipe is not None:
            return self._pipe  # type: ignore[return-value]
        if self._failed:
            return None
        try:
            import torch  # noqa: PLC0415 - optional heavy dependency, lazy
            from transformers import (  # noqa: PLC0415
                AutoModelForCausalLM,
                AutoTokenizer,
            )

            path = self.model_path
            is_adapter = (Path(path) / "adapter_config.json").exists()
            source_id = path if Path(path).exists() and not is_adapter else self.base_model

            tokenizer = AutoTokenizer.from_pretrained(source_id)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            on_cuda = torch.cuda.is_available()
            model = AutoModelForCausalLM.from_pretrained(
                source_id,
                torch_dtype=torch.float16 if on_cuda else torch.float32,
                device_map="auto" if on_cuda else None,
            )
            if is_adapter:  # the LoRA adapter trained on her traces
                from peft import PeftModel  # noqa: PLC0415

                model = PeftModel.from_pretrained(model, path)
            model.eval()
            self._pipe = (model, tokenizer, torch)
        except Exception:  # noqa: BLE001 - missing libs / model → fall back for good
            self._failed = True
            return None
        return self._pipe  # type: ignore[return-value]

    def _generate(
        self,
        loaded: tuple,
        self_model: SelfModelState,
        moment_content: str,
        source: ContentSource,
    ) -> str:
        model, tokenizer, torch = loaded
        system, user = _compose_prompt(self_model, moment_content, source)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                pad_token_id=tokenizer.pad_token_id,
            )
        new_tokens = out[0][inputs["input_ids"].shape[1]:]
        return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
