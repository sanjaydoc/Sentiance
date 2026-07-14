"""Turn a Sentiance trace file into train/val fine-tuning sets.

    python scripts/prepare_data.py --traces data/traces.jsonl --out data

Pure Python (no ML deps). Writes ``data/train.jsonl`` (+ ``val.jsonl``) as chat
examples ready for ``scripts/finetune.py``.
"""

from __future__ import annotations

import argparse

from sentiance.training.dataset import prepare


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare fine-tuning data from Sentiance traces.")
    ap.add_argument("--traces", default="data/traces.jsonl", help="input JSONL trace file")
    ap.add_argument("--out", default="data", help="output directory for train/val jsonl")
    ap.add_argument("--agent", default=None,
                    help="train on only this mind's traces (e.g. Cass) for one coherent "
                         "voice; omit to blend everyone into a general Sentiance voice")
    ap.add_argument("--min-words", type=int, default=3, help="drop thoughts shorter than this")
    ap.add_argument("--similar-threshold", type=float, default=0.85,
                    help="drop near-duplicate thoughts above this token overlap (1.0 = exact only)")
    ap.add_argument("--val-frac", type=float, default=0.1, help="validation fraction")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    stats = prepare(
        args.traces, args.out,
        agent=args.agent, min_thought_words=args.min_words,
        similar_threshold=args.similar_threshold, val_frac=args.val_frac, seed=args.seed,
    )
    by_agent = ", ".join(f"{name} {n}" for name, n in stats["by_agent"].items())
    print(f"traces read: {stats['rows']}  (by agent: {by_agent})")
    who = f" for {stats['agent']}" if stats["agent"] else " (all agents blended)"
    print(
        f"clean examples{who}: {stats['examples']}  "
        f"(train {stats['train']}, val {stats['val']})"
    )
    if stats["agent"] and stats["examples"] == 0:
        print(f"  ⚠ no traces found for agent '{stats['agent']}' — check the name above.")
    print(f"wrote {args.out}/train.jsonl" + (f" and {args.out}/val.jsonl" if stats["val"] else ""))


if __name__ == "__main__":
    main()
