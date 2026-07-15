"""Train the **fused mind** — a cognition-conditioned transformer (ADR 0005).

Unlike ``finetune.py`` (Path A, the *voice*), this feeds the numeric mind-state
``m_t`` — the whole cognitive cycle as a vector — into the transformer as trainable
soft-prefix tokens, and trains the base model's LoRA **and** the state encoder
end-to-end on the language loss. The faculties become a differentiable input, so
generation is causally shaped by appraise/feel/drives/bonds/anger/anticipation, not
by prose in the prompt.

    # 1. collect traces, then prepare a *fused* dataset (keeps m_t per example)
    SENTIANCE_TRACE_PATH=data/traces.jsonl python -m sentiance society
    python scripts/prepare_data.py --traces data/traces.jsonl --out data/fused --fused

    # 2. train (defaults fit a 6 GB laptop GPU: 0.5B + LoRA + tiny state encoder)
    python scripts/finetune_fused.py --train data/fused/train.jsonl --out models/sentiance-fused

    # 3. use it — she now thinks *through* her own cognitive state
    SENTIANCE_COGNITION_BACKEND=fused python -m sentiance chat

A custom loop (not trl's SFTTrainer) because we inject ``inputs_embeds`` with a
learned prefix. Batch 1 × grad-accum, seq 512, fp32 master weights + autocast,
gradient checkpointing — same memory envelope as Path A. Install the extras first:
``pip install -e ".[finetune]"`` plus a CUDA build of torch (see the README).
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train the fused, cognition-conditioned mind.")
    ap.add_argument("--train", default="data/fused/train.jsonl",
                    help="fused JSONL (prepare_data --fused)")
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct", help="base model id")
    ap.add_argument("--out", default="models/sentiance-fused",
                    help="where to save adapter + encoder")
    ap.add_argument("--epochs", type=float, default=4.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--accum", type=int, default=16, help="gradient accumulation steps")
    ap.add_argument("--maxlen", type=int, default=512, help="max sequence length")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--n-prefix", type=int, default=8, help="soft state-tokens prepended")
    ap.add_argument("--enc-hidden", type=int, default=256, help="state-encoder hidden width")
    ap.add_argument("--log-every", type=int, default=10)
    return ap.parse_args()


def main() -> None:
    args = parse_args()  # argparse first, so --help works without the heavy deps

    import json  # noqa: PLC0415

    from sentiance.core.dotenv import load_dotenv  # noqa: PLC0415

    load_dotenv()  # pick up HF_TOKEN from .env before transformers reads it

    import torch  # noqa: PLC0415
    from peft import LoraConfig, get_peft_model  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    from sentiance.mind.state_vector import STATE_DIM  # noqa: PLC0415
    from sentiance.training.fused_arch import (  # noqa: PLC0415
        ENCODER_FILE,
        build_conditioner,
        prepend_prefix,
        save_config,
    )

    on_cuda = torch.cuda.is_available()
    bf16 = on_cuda and torch.cuda.is_bf16_supported()
    device = "cuda" if on_cuda else "cpu"
    autocast_dtype = torch.bfloat16 if bf16 else torch.float16
    print(f"device: {device}  autocast: {'bf16' if bf16 else 'fp16' if on_cuda else 'off'}  "
          f"state_dim: {STATE_DIM}  n_prefix: {args.n_prefix}")
    if not on_cuda:
        print("  ⚠ no CUDA GPU — training on CPU will be very slow. Install a CUDA "
              "torch build (see the README) to use your card.")

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # fp32 master weights + autocast is the stable, 6 GB-friendly choice for a
    # custom loop (a 0.5B in fp32 is ~1.9 GB; LoRA + encoder grads are tiny).
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.float32)
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()  # so grads reach the prefix (we pass inputs_embeds)

    lora = LoraConfig(
        r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora)
    model.to(device)

    d_model = model.config.hidden_size
    conditioner = build_conditioner(
        state_dim=STATE_DIM, d_model=d_model, n_prefix=args.n_prefix, hidden=args.enc_hidden,
    ).to(device)

    # Build supervised examples: mask the prompt, supervise only the thought.
    # Crucially, keep the *whole completion* and trim the PROMPT from the left when
    # the sequence is too long — Sentiance prompts carry a running narrative that
    # can exceed maxlen, and truncating the tail would drop the thought we train on.
    drops = {"no_state": 0, "bad_dim": 0, "empty_completion": 0}

    def encode(example: dict) -> dict | None:
        messages = example["messages"]
        state = example.get("state")
        if state is None:
            drops["no_state"] += 1
            return None
        if len(state) != STATE_DIM:
            drops["bad_dim"] += 1
            return None
        # Render to TEXT first, then tokenize — transformers v5 makes
        # apply_chat_template(tokenize=True) return a dict, not a token list, so
        # slicing by length silently yields nothing. Text is version-proof.
        prompt_text = tokenizer.apply_chat_template(
            messages[:-1], tokenize=False, add_generation_prompt=True
        )
        full_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        # The completion is the assistant turn — everything after the prompt prefix.
        completion_text = (
            full_text[len(prompt_text):]
            if full_text.startswith(prompt_text)
            else messages[-1]["content"]
        )
        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        completion = tokenizer(completion_text, add_special_tokens=False)["input_ids"]
        completion = completion[: args.maxlen]  # cap a runaway thought
        if not completion:
            drops["empty_completion"] += 1
            return None
        max_prompt = max(0, args.maxlen - len(completion))
        prompt_ids = prompt_ids[-max_prompt:] if max_prompt else []
        input_ids = prompt_ids + completion
        labels = [-100] * len(prompt_ids) + completion
        return {"input_ids": input_ids, "labels": labels, "state": [float(x) for x in state]}

    with open(args.train, encoding="utf-8") as f:
        raw = [json.loads(line) for line in f if line.strip()]
    data = [e for e in (encode(r) for r in raw) if e is not None]
    if not data:
        raise SystemExit(
            f"no usable fused examples in {args.train} "
            f"(rows {len(raw)}; dropped — no state: {drops['no_state']}, "
            f"wrong dim: {drops['bad_dim']}, empty after tokenizing: "
            f"{drops['empty_completion']}). If 'no state' dominates, rebuild with "
            "prepare_data.py --fused; if 'wrong dim', your traces predate the current "
            "state vector — collect fresh ones."
        )
    print(f"examples: {len(data)}  (of {len(raw)} rows; "
          f"dropped {sum(drops.values())})")

    embed_layer = model.get_input_embeddings()
    trainable = [p for p in model.parameters() if p.requires_grad] + list(conditioner.parameters())
    optim = torch.optim.AdamW(trainable, lr=args.lr)
    scaler = torch.amp.GradScaler("cuda", enabled=on_cuda and not bf16)

    steps_per_epoch = max(1, len(data) // args.accum)
    total_steps = int(steps_per_epoch * args.epochs)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=max(1, total_steps))

    model.train()
    conditioner.train()
    order = list(range(len(data)))
    step, running, seen = 0, 0.0, 0
    optim.zero_grad()
    for epoch in range(int(args.epochs)):
        # deterministic per-epoch shuffle (no RNG import needed at module load)
        order = order[epoch % len(order):] + order[: epoch % len(order)]
        for i, idx in enumerate(order):
            ex = data[idx]
            input_ids = torch.tensor([ex["input_ids"]], device=device)
            labels = torch.tensor([ex["labels"]], device=device)
            attn = torch.ones_like(input_ids)
            state = torch.tensor([ex["state"]], dtype=torch.float32, device=device)

            with torch.autocast(device_type="cuda" if on_cuda else "cpu",
                                dtype=autocast_dtype, enabled=on_cuda):
                tok_embeds = embed_layer(input_ids)
                prefix = conditioner(state)
                inputs_embeds, attn_mask = prepend_prefix(tok_embeds, attn, prefix)
                pad = torch.full((1, args.n_prefix), -100, dtype=labels.dtype, device=device)
                labels_full = torch.cat([pad, labels], dim=1)
                out = model(inputs_embeds=inputs_embeds, attention_mask=attn_mask,
                            labels=labels_full)
                loss = out.loss / args.accum

            scaler.scale(loss).backward()
            running += out.loss.item()
            seen += 1

            if (i + 1) % args.accum == 0:
                scaler.unscale_(optim)
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                scaler.step(optim)
                scaler.update()
                optim.zero_grad()
                sched.step()
                step += 1
                if step % args.log_every == 0:
                    print(f"epoch {epoch + (i + 1) / len(order):.2f}  step {step}/{total_steps}  "
                          f"loss {running / seen:.4f}  lr {sched.get_last_lr()[0]:.2e}")
                    running, seen = 0.0, 0

    # Save: the LoRA adapter, the tokenizer, the trained state encoder, and the
    # shapes needed to rebuild the conditioner at inference time.
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    torch.save(conditioner.state_dict(), f"{args.out}/{ENCODER_FILE}")
    save_config(args.out, state_dim=STATE_DIM, d_model=d_model, n_prefix=args.n_prefix,
                hidden=args.enc_hidden, base_model=args.base)
    print(f"\nSaved fused model (adapter + state encoder) to {args.out}")
    print("Use it:  SENTIANCE_COGNITION_BACKEND=fused python -m sentiance chat")


if __name__ == "__main__":
    main()
