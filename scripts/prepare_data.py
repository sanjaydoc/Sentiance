"""Turn a Sentiance trace file into train/val fine-tuning sets.

    python scripts/prepare_data.py --traces data/traces.jsonl --out data

Pure Python (no ML deps). Writes ``data/train.jsonl`` (+ ``val.jsonl``) as chat
examples ready for ``scripts/finetune.py``.

Add ``--fused`` to build the dataset for the **fused mind** instead: each example
keeps its numeric ``m_t`` (the whole cognitive cycle as a vector) so a
cognition-conditioned transformer can be trained on it (``scripts/finetune_fused.py``,
ADR 0005). Point ``--out`` at a separate dir (e.g. ``data/fused``) so it doesn't
overwrite the Path-A voice dataset.
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
    ap.add_argument("--fused", action="store_true",
                    help="keep each example's numeric m_t for the fused, "
                         "cognition-conditioned transformer (finetune_fused.py)")
    args = ap.parse_args()

    stats = prepare(
        args.traces, args.out,
        agent=args.agent, min_thought_words=args.min_words,
        similar_threshold=args.similar_threshold, val_frac=args.val_frac, seed=args.seed,
        include_state=args.fused,
    )
    by_agent = ", ".join(f"{name} {n}" for name, n in stats["by_agent"].items())
    kind = "fused (with m_t)" if stats.get("fused") else "voice"
    print(f"traces read: {stats['rows']}  (by agent: {by_agent})  ·  dataset: {kind}")
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
