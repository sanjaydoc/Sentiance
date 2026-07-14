"""Fine-tune a small model on Sentiance's traces — LoRA, tuned for ~6 GB VRAM.

    # 1. collect data while she lives, then prepare it
    #    (Windows cmd: set SENTIANCE_TRACE_PATH=data\\traces.jsonl)
    SENTIANCE_TRACE_PATH=data/traces.jsonl python -m sentiance society
    python scripts/prepare_data.py --traces data/traces.jsonl --out data

    # 2. train the voice (defaults fit a 6 GB laptop GPU)
    python scripts/finetune.py --train data/train.jsonl --out models/sentiance-voice

    # 3. use it — she now thinks with the model trained on her
    #    (Windows cmd: set SENTIANCE_COGNITION_BACKEND=finetuned)
    SENTIANCE_COGNITION_BACKEND=finetuned python -m sentiance chat

Defaults: Qwen2.5-0.5B-Instruct + LoRA, batch 1 × grad-accum 16, seq 512, bf16,
gradient checkpointing — this trains in a few GB. For a bigger base on the same
card add ``--qlora`` (4-bit; needs ``pip install bitsandbytes``). Install the
extras first: ``pip install -e ".[finetune]"`` and a CUDA build of torch
(see the README) so it runs on your GPU rather than the CPU.
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="LoRA fine-tune a small model on Sentiance traces.")
    ap.add_argument("--train", default="data/train.jsonl", help="chat-format JSONL (prepare_data)")
    ap.add_argument("--val", default="data/val.jsonl", help="optional validation JSONL")
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct", help="base model id")
    ap.add_argument("--out", default="models/sentiance-voice", help="where to save the adapter")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=1, help="per-device batch size")
    ap.add_argument("--accum", type=int, default=16, help="gradient accumulation steps")
    ap.add_argument("--maxlen", type=int, default=512, help="max sequence length")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--qlora", action="store_true", help="4-bit QLoRA (needs bitsandbytes)")
    return ap.parse_args()


def main() -> None:
    args = parse_args()  # argparse first, so --help works without the heavy deps

    import os  # noqa: PLC0415

    import torch  # noqa: PLC0415
    from datasets import load_dataset  # noqa: PLC0415
    from peft import LoraConfig  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415
    from trl import SFTConfig, SFTTrainer  # noqa: PLC0415

    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    print(f"device: {'cuda' if torch.cuda.is_available() else 'cpu'}  "
          f"dtype: {'bf16' if bf16 else 'fp16/fp32'}  qlora: {args.qlora}")

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict = {"torch_dtype": torch.bfloat16 if bf16 else torch.float16}
    if args.qlora:
        from transformers import BitsAndBytesConfig  # noqa: PLC0415

        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if bf16 else torch.float16,
        )
    model = AutoModelForCausalLM.from_pretrained(args.base, **model_kwargs)
    model.config.use_cache = False

    data_files = {"train": args.train}
    if os.path.exists(args.val):
        data_files["validation"] = args.val
    ds = load_dataset("json", data_files=data_files)

    def to_text(example: dict) -> dict:
        return {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False)}

    ds = ds.map(to_text, remove_columns=["messages"])

    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )

    cfg = SFTConfig(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        save_strategy="epoch",
        bf16=bf16,
        fp16=not bf16 and torch.cuda.is_available(),
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit" if args.qlora else "adamw_torch",
        max_seq_length=args.maxlen,
        dataset_text_field="text",
        packing=False,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=cfg,
        train_dataset=ds["train"],
        eval_dataset=ds.get("validation"),
        peft_config=lora,
        tokenizer=tokenizer,
    )
    trainer.train()
    trainer.save_model(args.out)  # saves the LoRA adapter
    tokenizer.save_pretrained(args.out)
    print(f"\nSaved adapter to {args.out}")
    print("Use it:  SENTIANCE_COGNITION_BACKEND=finetuned python -m sentiance chat")


if __name__ == "__main__":
    main()
