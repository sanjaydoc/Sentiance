"""Ablation eval — does the numeric m_t actually steer the fused mind?

The `fused` backend feeds state to the model *two* ways: as text in the prompt
(``I feel dread, valence -0.69``) and as the numeric ``m_t`` vector projected to
soft-prefix tokens. A chat session shows the whole system responding to state, but
not which channel did it. This isolates the vector.

Method: drive a mind through a few situations to reach real states. For each, hold
the **prompt identical** and generate **greedily** (deterministic) twice — once
with the real ``m_t``, once with ``m_t`` zeroed. Same prompt, same decoding, so any
difference in the output is attributable to the conditioning vector alone. It also
runs a cross-state swap (feed one state's prompt with another state's ``m_t``) to
show direction.

    python scripts/eval_fused.py --model models/sentiance-fused

If real-vs-zero outputs differ on most probes, the state encoder learned to steer
generation — the hybrid is doing something the prompt text can't. If they're mostly
identical, the vector isn't contributing yet (train longer / more --n-prefix / more
data). Either way it's a measurement, not a vibe.

Honest note (ADR 0002): this measures *functional* influence of a state vector on
generation — integration, not phenomenal experience.
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Ablate m_t on the fused mind.")
    ap.add_argument("--model", default="models/sentiance-fused", help="fused model dir")
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct", help="base model id")
    ap.add_argument("--max-new", type=int, default=64, help="tokens to generate per probe")
    return ap.parse_args()


# A short script that lands the mind in distinct states (warm, threatened, neutral).
_PROBE_SCRIPT = [
    ("@Sam holds my hand warmly", ["friend", "warmth"]),
    ("a sudden loud crash in the dark", ["threat", "alarm"]),
    ("the door I need is locked and won't budge", ["loss"]),
    ("a quiet moment by the window", []),
    ("@Mara is laughing with delight", ["friend"]),
]


def main() -> None:
    args = parse_args()

    from sentiance.core.dotenv import load_dotenv  # noqa: PLC0415

    load_dotenv()

    from pathlib import Path  # noqa: PLC0415

    import torch  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    from sentiance.core.config import Settings  # noqa: PLC0415
    from sentiance.mind import Mind, Stimulus  # noqa: PLC0415
    from sentiance.mind.cognition import _compose_prompt  # noqa: PLC0415
    from sentiance.mind.state_vector import encode_state  # noqa: PLC0415
    from sentiance.training.fused_arch import (  # noqa: PLC0415
        ENCODER_FILE,
        build_conditioner,
        load_config,
        prepend_prefix,
    )

    cfg = load_config(args.model)
    if cfg is None:
        raise SystemExit(f"{args.model} is not a fused model dir (no fused_config.json). "
                         "Train one with scripts/finetune_fused.py first.")

    base_id = cfg.get("base_model") or args.base
    on_cuda = torch.cuda.is_available()
    tokenizer = AutoTokenizer.from_pretrained(base_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_id, torch_dtype=torch.float16 if on_cuda else torch.float32,
        device_map="auto" if on_cuda else None,
    )
    if (Path(args.model) / "adapter_config.json").exists():
        from peft import PeftModel  # noqa: PLC0415

        model = PeftModel.from_pretrained(model, args.model)
    model.eval()

    conditioner = build_conditioner(
        state_dim=cfg["state_dim"], d_model=cfg["d_model"],
        n_prefix=cfg["n_prefix"], hidden=cfg.get("hidden", 256),
    )
    conditioner.load_state_dict(torch.load(Path(args.model) / ENCODER_FILE, map_location="cpu"))
    conditioner.to(model.device).to(model.dtype)
    conditioner.eval()

    embed_layer = model.get_input_embeddings()

    def generate(snap, content, source, m_t) -> str:
        system, user = _compose_prompt(snap, content, source)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        state = torch.tensor([m_t], dtype=model.dtype, device=model.device)
        with torch.no_grad():
            tok_embeds = embed_layer(inputs["input_ids"])
            prefix = conditioner(state)
            inputs_embeds, attn = prepend_prefix(tok_embeds, inputs["attention_mask"], prefix)
            out = model.generate(
                inputs_embeds=inputs_embeds, attention_mask=attn,
                max_new_tokens=args.max_new, do_sample=False,  # greedy → deterministic
                pad_token_id=tokenizer.pad_token_id,
            )
        return tokenizer.decode(out[0], skip_special_tokens=True).strip()

    # Drive a mind (offline voice, so we don't recurse into the fused model) to reach
    # real states, capturing each (snapshot, focus, source) as a probe.
    mind = Mind(settings=Settings(cognition_backend="simulated"))
    probes = []
    for text, tags in _PROBE_SCRIPT:
        mind.perceive(Stimulus(content=text, intensity=0.8, tags=tags))
        moment = mind._last_moment
        probes.append((mind.state(), moment.content, moment.source, text))

    print(f"\n=== Ablation: real m_t vs zeroed m_t (same prompt, greedy) — {args.model} ===\n")
    changed = 0
    for snap, content, source, text in probes:
        real = encode_state(snap, source)
        zero = [0.0] * len(real)
        out_real = generate(snap, content, source, real)
        out_zero = generate(snap, content, source, zero)
        differ = out_real.strip() != out_zero.strip()
        changed += differ
        print(f"• situation: {text}")
        print(f"  state: {snap.affect.emotion.value} v{snap.affect.valence:+.2f}")
        print(f"  real m_t : {out_real}")
        print(f"  zero m_t : {out_zero}")
        print(f"  → {'DIFFERENT (m_t steered it)' if differ else 'identical (m_t inert here)'}\n")

    print(f"m_t changed the output on {changed}/{len(probes)} probes.")

    # Cross-state swap: does *whose* m_t it is matter? Feed probe 0's prompt with
    # probe 1's m_t (and vice versa) — output shifting toward the borrowed state is
    # direct evidence the vector carries steering signal.
    if len(probes) >= 2:
        (sa, ca, srca, ta), (sb, _cb, srcb, tb) = probes[0], probes[1]
        print("\n=== Cross-state swap (same prompt, borrowed m_t) ===\n")
        print(f"• prompt from: {ta}  ({sa.affect.emotion.value})")
        print(f"  own m_t     : {generate(sa, ca, srca, encode_state(sa, srca))}")
        print(f"  borrowed m_t: {generate(sa, ca, srca, encode_state(sb, srcb))}  "
              f"(from: {tb} / {sb.affect.emotion.value})")


if __name__ == "__main__":
    main()
