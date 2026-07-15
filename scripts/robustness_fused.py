"""Robustness harness — is the m_t effect real, or a lucky seed?

A single fused run can give r=+0.89 or r=-0.29 on similar data — the zero-init
encoder either catches the m_t signal during optimization or doesn't. So one number
means nothing. This trains the fused model across several seeds on the **same** data
and reports the **distribution** of the congruence r (mean ± std, min/max, how many
seeds cleared the significance bar). That distribution is the publishable claim:
"the effect holds across N/M seeds", not "it worked once".

    python scripts/robustness_fused.py --train data/fused/train.jsonl --seeds 5

Each seed trains a fresh model (subprocess to finetune_fused.py) and is evaluated
(subprocess to eval_fused.py --json). ~20 min per seed on a 6 GB GPU, so 5 seeds is
~1.5–2 h — reduce with --seeds 3 or --epochs 3. Per-seed models land in
models/robust/seed<k>/ (delete afterwards to reclaim disk).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train + eval the fused mind across seeds.")
    ap.add_argument("--train", default="data/fused/train.jsonl", help="fused (state-blind) JSONL")
    ap.add_argument("--seeds", type=int, default=5, help="number of seeds (0..N-1)")
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--epochs", type=float, default=4.0)
    ap.add_argument("--n-prefix", type=int, default=16)
    ap.add_argument("--conditioning", choices=["prefix", "film"], default="prefix",
                    help="conditioning path to test across seeds (film = per-layer γ/β)")
    ap.add_argument("--out-root", default="models/robust", help="per-seed model dirs go here")
    ap.add_argument("--report", default="eval/robustness.md", help="summary markdown path")
    return ap.parse_args()


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _pstdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5


def main() -> None:
    args = parse_args()
    out_root = Path(args.out_root)
    eval_dir = Path("eval/robust")
    eval_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for seed in range(args.seeds):
        model_dir = out_root / f"seed{seed}"
        json_path = eval_dir / f"seed{seed}.json"
        print(f"\n{'=' * 60}\n seed {seed}/{args.seeds - 1} — training\n{'=' * 60}")
        train = subprocess.run(
            [sys.executable, "scripts/finetune_fused.py",
             "--train", args.train, "--out", str(model_dir),
             "--base", args.base, "--epochs", str(args.epochs),
             "--n-prefix", str(args.n_prefix), "--conditioning", args.conditioning,
             "--seed", str(seed)],
            check=False,
        )
        if train.returncode != 0:
            print(f"  seed {seed}: training failed — skipping")
            continue
        print(f"\n seed {seed} — evaluating")
        ev = subprocess.run(
            [sys.executable, "scripts/eval_fused.py",
             "--model", str(model_dir), "--base", args.base,
             "--json", str(json_path)],
            check=False,
        )
        if ev.returncode != 0 or not json_path.exists():
            print(f"  seed {seed}: eval failed — skipping")
            continue
        m = json.loads(json_path.read_text(encoding="utf-8"))
        m["seed"] = seed
        results.append(m)

    if not results:
        raise SystemExit("no seeds completed — check the training/eval errors above")

    rs = [m["r_real"] for m in results]
    perms = [m["p_perm"] for m in results]
    n_strong = sum(1 for m in results if m["r_real"] >= 0.5 and m["p_perm"] <= 0.05)
    n_pos = sum(1 for m in results if m["r_real"] > 0)

    print(f"\n{'=' * 60}\n ROBUSTNESS across {len(results)} seeds\n{'=' * 60}")
    for m in results:
        print(f"  seed {m['seed']}: r={m['r_real']:+.3f}  perm_p={m['p_perm']:.4f}  "
              f"dose={m['dose_slope']:+.3f}")
    print(f"\n  r(valence, ΔAffect): mean {_mean(rs):+.3f} ± {_pstdev(rs):.3f}  "
          f"(min {min(rs):+.3f}, max {max(rs):+.3f})")
    print(f"  positive-r seeds: {n_pos}/{len(results)}   "
          f"strong (r≥0.5 & perm p≤0.05): {n_strong}/{len(results)}")
    # ROBUST requires the effect to hold on (nearly) *every* seed — no seed flipping
    # negative, and most clearing significance. A 2/3 with a negative outlier and a
    # large std is "directional but noisy", not robust — don't overclaim.
    n = len(results)
    all_positive = min(rs) > 0
    if n_strong >= 0.8 * n and all_positive:
        verdict = ("ROBUST — the m_t effect holds across (nearly) all seeds "
                   "(publishable with error bars)")
    elif n_pos >= 0.6 * n and n_strong >= 0.5 * n:
        verdict = ("DIRECTIONAL BUT NOISY — mostly positive and often significant, but "
                   "high variance and a failing seed remain; report mean ± std honestly, "
                   "and note the effect is data-scale-limited")
    else:
        verdict = ("NOT ROBUST — the single-seed result was largely luck; "
                   "needs more data or a stronger conditioning path")
    print(f"\n  VERDICT: {verdict}\n")

    rep = Path(args.report)
    rep.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Fused-mind robustness — {len(results)} seeds", "",
        f"Same data (`{args.train}`), `n_prefix={args.n_prefix}`, `epochs={args.epochs}`.", "",
        "| seed | r(valence, ΔAffect) | permutation p | dose slope |",
        "| ---: | ---: | ---: | ---: |",
        *[f"| {m['seed']} | {m['r_real']:+.3f} | {m['p_perm']:.4f} | {m['dose_slope']:+.3f} |"
          for m in results],
        "",
        f"**r across seeds:** mean **{_mean(rs):+.3f} ± {_pstdev(rs):.3f}** "
        f"(min {min(rs):+.3f}, max {max(rs):+.3f}).",
        f"**Positive-r:** {n_pos}/{len(results)}.  **Strong (r≥0.5 & p≤0.05):** "
        f"{n_strong}/{len(results)}.  **Median perm p:** {sorted(perms)[len(perms) // 2]:.4f}.",
        "",
        f"**Verdict:** {verdict}.", "",
        "_Functional correlates only (ADR 0002)._", "",
    ]
    rep.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote robustness report to {rep}")


if __name__ == "__main__":
    main()
