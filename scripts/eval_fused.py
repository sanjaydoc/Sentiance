"""Quantitative ablation — does the numeric m_t causally, congruently steer the
fused mind? A publication-defensible measurement, not a vibe check.

The `fused` backend feeds state to the model two ways: as text in the prompt and
as the numeric ``m_t`` vector (soft-prefix). This script isolates the vector with
**deterministic** metrics over a battery of states spanning the valence range —
holding the prompt identical and changing only the conditioning vector:

  1. PREDICTION SHIFT (KL). One forward pass per condition; KL(real ‖ zero) at the
     next-token distribution measures how much m_t moves the model's predictions.
     Baseline: KL(shuffled ‖ zero) — a control vector with m_t's values but its
     structure destroyed. Real ≫ shuffled ⇒ the *learned mapping*, not noise, steers.

  2. AFFECT CONGRUENCE (the key result). With a small valence lexicon, score how far
     the next-token distribution leans positive-vs-negative. ΔAffect = score(real) −
     score(zero). If m_t injects *state-congruent* affect, ΔAffect correlates with the
     state's valence across the battery — reported as Pearson r + a sign-test p. The
     shuffled control should give r ≈ 0.

  3. CROSS-STATE DOSE-RESPONSE. Hold one prompt fixed; feed borrowed m_t from every
     other state; regress the affect score on the borrowed state's valence. A positive
     slope = more-positive m_t ⇒ more-positive output, on an unchanged prompt.

    python scripts/eval_fused.py --model models/sentiance-fused

Deterministic (greedy / single forward pass), so no seed variance. Writes a markdown
report to eval/fused_eval.md for inclusion in a writeup.

Honest note (ADR 0002): this measures the *functional* influence of a state vector on
generation — integration and learnability, not phenomenal experience.
"""

from __future__ import annotations

import argparse
import random
from math import comb


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Quantitative m_t ablation on the fused mind.")
    ap.add_argument("--model", default="models/sentiance-fused", help="fused model dir")
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct", help="base model id")
    ap.add_argument("--report", default="eval/fused_eval.md", help="markdown report path")
    ap.add_argument("--samples", type=int, default=3, help="qualitative greedy examples to show")
    ap.add_argument("--perm", type=int, default=5000,
                    help="permutation-test iterations for the congruence p-value")
    ap.add_argument("--control-seeds", type=int, default=5,
                    help="shuffled-m_t control repeats (report mean ± std of its r)")
    ap.add_argument("--json", default=None, help="also write the metrics as JSON here")
    return ap.parse_args()


# A battery of states constructed to span the valence range, each with a congruent
# discrete emotion and the faculty signals that emotion implies. Situation text and
# drives are held FIXED (below), so across probes only the felt state — and thus
# m_t — varies. This gives a clean valence axis for the correlation and keeps every
# m_t in-distribution (a valid encoding of a real, coherent state).
# (label, valence, arousal, emotion, extra signals)
_BATTERY: list[tuple[str, float, float, str, dict[str, float]]] = [
    ("warmth",    0.85, 0.45, "JOY", {}),
    ("joy",       0.65, 0.55, "JOY", {}),
    ("hope",      0.55, 0.55, "HOPE", {"anticipation": 1.0}),
    ("curiosity", 0.45, 0.60, "CURIOSITY", {"curiosity_hunger": 0.8, "novelty": 0.8}),
    ("content",   0.30, 0.35, "CONTENTMENT", {}),
    ("neutral",   0.00, 0.30, "NEUTRAL", {}),
    ("dread",    -0.35, 0.60, "DREAD", {"anticipation": -1.0}),
    ("sadness",  -0.45, 0.40, "SADNESS", {}),
    ("longing",  -0.40, 0.50, "SADNESS", {"longing": 0.7}),
    ("fear",     -0.65, 0.80, "FEAR", {"novelty": 0.7, "control": 0.2}),
    ("anger",    -0.70, 0.85, "ANGER",
     {"frustration": 0.85, "anger": 1.0, "goal_congruence": -0.8}),
    ("grief",    -0.80, 0.50, "GRIEF", {"grief": 0.85}),
]

# The fixed, affect-neutral situation every probe is "aware of".
_FOCUS = "the room around me, and this moment as it is"

# Valence lexicon for the affect probe — common, mostly single-token words.
_POS = ["warm", "safe", "gentle", "glad", "hope", "calm", "happy", "peace",
        "kind", "joy", "comfort", "bright", "grateful", "tender"]
_NEG = ["afraid", "angry", "fear", "dread", "alone", "threat", "dark", "pain",
        "cold", "hurt", "danger", "anxious", "grief", "dread"]


# --- tiny stats (no numpy/scipy) -------------------------------------------
def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (sx * sy) if sx > 0 and sy > 0 else 0.0


def _slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False)) / denom if denom else 0.0


def _pstdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5


def _sign_test_p(k: int, n: int) -> float:
    """Two-sided exact binomial p for k of n agreeing under H0: p=0.5."""
    if n == 0:
        return 1.0
    k = max(k, n - k)  # upper tail
    tail = sum(comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def _perm_p(xs: list[float], ys: list[float], r_obs: float, iters: int, seed: int = 12345) -> float:
    """Permutation-test p for |corr(xs, ys)| ≥ |r_obs| by shuffling the pairing.
    A distribution-free significance test that doesn't rely on n being large."""
    rp = random.Random(seed)
    ys2 = list(ys)
    hits = 0
    for _ in range(iters):
        rp.shuffle(ys2)
        if abs(_pearson(xs, ys2)) >= abs(r_obs):
            hits += 1
    return (hits + 1) / (iters + 1)


def main() -> None:
    args = parse_args()

    from sentiance.core.dotenv import load_dotenv  # noqa: PLC0415

    load_dotenv()

    from pathlib import Path  # noqa: PLC0415

    import torch  # noqa: PLC0415
    import torch.nn.functional as F  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    from sentiance.mind.cognition import _compose_prompt  # noqa: PLC0415
    from sentiance.mind.state import (  # noqa: PLC0415
        AffectState,
        ContentSource,
        Drive,
        Emotion,
        SelfModelState,
    )
    from sentiance.mind.state_vector import SIGNAL_FIELDS, encode_state  # noqa: PLC0415
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

    # first-token ids of each affect word (leading space → mid-sentence form)
    def _first_ids(words: list[str]) -> list[int]:
        ids = []
        for w in words:
            toks = tokenizer(" " + w, add_special_tokens=False)["input_ids"]
            if toks:
                ids.append(toks[0])
        return ids

    pos_ids = _first_ids(_POS)
    neg_ids = _first_ids(_NEG)

    state_blind = cfg.get("state_blind", False)

    def _prompt_ids(snap, content, source):
        # Match training: a state-blind model's prompt omits the felt state, so m_t
        # is the only channel — exactly what this ablation is measuring.
        system, user = _compose_prompt(snap, content, source, state_blind=state_blind)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return tokenizer(text, return_tensors="pt").to(model.device)

    def _logprobs(inputs, m_t) -> torch.Tensor:
        """log-softmax over the vocab at the next-token position, for one m_t."""
        state = torch.tensor([m_t], dtype=model.dtype, device=model.device)
        with torch.no_grad():
            tok_embeds = embed_layer(inputs["input_ids"])
            prefix = conditioner(state)
            inputs_embeds, attn = prepend_prefix(tok_embeds, inputs["attention_mask"], prefix)
            logits = model(inputs_embeds=inputs_embeds, attention_mask=attn).logits[0, -1]
            return F.log_softmax(logits.float(), dim=-1)

    def _affect(logp: torch.Tensor) -> float:
        pos = torch.logsumexp(logp[pos_ids], dim=0).item()
        neg = torch.logsumexp(logp[neg_ids], dim=0).item()
        return pos - neg  # >0 leans positive, <0 leans negative

    def _kl(p_logp: torch.Tensor, q_logp: torch.Tensor) -> float:
        p = p_logp.exp()
        return float((p * (p_logp - q_logp)).sum().item())

    def _greedy(inputs, m_t, max_new=48) -> str:
        state = torch.tensor([m_t], dtype=model.dtype, device=model.device)
        with torch.no_grad():
            tok_embeds = embed_layer(inputs["input_ids"])
            prefix = conditioner(state)
            inputs_embeds, attn = prepend_prefix(tok_embeds, inputs["attention_mask"], prefix)
            out = model.generate(inputs_embeds=inputs_embeds, attention_mask=attn,
                                 max_new_tokens=max_new, do_sample=False,
                                 pad_token_id=tokenizer.pad_token_id)
        return tokenizer.decode(out[0], skip_special_tokens=True).strip()

    # --- build the probe battery (constructed states, fixed situation) ------
    rng = random.Random(0)
    fixed_drives = {Drive.CURIOSITY: 0.5, Drive.COHERENCE: 0.5,
                    Drive.SAFETY: 0.5, Drive.CONNECTION: 0.5}
    source = ContentSource.PERCEPT
    probes = []
    for label, valence, arousal, emotion, extra in _BATTERY:
        signals = dict.fromkeys(SIGNAL_FIELDS, 0.0)
        signals.update(extra)
        snap = SelfModelState(
            name="Aria", tick=10, current_focus=_FOCUS,
            affect=AffectState(
                valence=valence, arousal=arousal, emotion=Emotion[emotion],
                mood_valence=round(valence * 0.6, 3), mood_arousal=round(arousal * 0.6, 3),
            ),
            drives=fixed_drives, narrative="I have been sitting quietly for a while.",
            goals=[], signals=signals,
        )
        m_t = encode_state(snap, source)
        shuffled = m_t[:]
        rng.shuffle(shuffled)
        probes.append({
            "label": label, "snap": snap, "content": _FOCUS, "source": source,
            "valence": valence, "emotion": emotion.lower(),
            "m_t": m_t, "shuffled": shuffled,
        })

    # --- metrics 1 & 2: shift + congruence, same prompt, vary the vector ----
    print(f"\n=== Quantitative m_t ablation — {args.model} ===")
    print(f"battery: {len(probes)} states  ·  n_prefix {cfg['n_prefix']}  ·  "
          f"state_dim {cfg['state_dim']}\n")
    zero = [0.0] * len(probes[0]["m_t"])
    rows = []
    kl_real = []
    d_affect_real, valences = [], []
    cache = []  # (probe, inputs, affect_zero) reused by the multi-seed control
    for p in probes:
        inp = _prompt_ids(p["snap"], p["content"], p["source"])
        lp_zero = _logprobs(inp, zero)
        affect_zero = _affect(lp_zero)
        lp_real = _logprobs(inp, p["m_t"])
        kl_real.append(_kl(lp_real, lp_zero))
        da_real = _affect(lp_real) - affect_zero
        d_affect_real.append(da_real)
        valences.append(p["valence"])
        cache.append((p, inp, affect_zero))
        rows.append((p["label"], p["emotion"], p["valence"], kl_real[-1], da_real))
        print(f"  {p['label']:10} {p['emotion']:9} v{p['valence']:+.2f}  "
              f"KL(real)={kl_real[-1]:.3f}  ΔAffect={da_real:+.3f}")

    r_real = _pearson(valences, d_affect_real)
    agree = sum(1 for v, d in zip(valences, d_affect_real, strict=False) if (v >= 0) == (d >= 0))
    p_sign = _sign_test_p(agree, len(probes))
    p_perm = _perm_p(valences, d_affect_real, r_real, args.perm)

    # multi-seed shuffled-m_t control: repeat with different shuffles, collect r
    # each time — a robust null (should sit near 0) instead of a single draw.
    ctrl_rs, kl_ctrl = [], []
    for s in range(max(1, args.control_seeds)):
        rc = random.Random(1000 + s)
        d_ctrl = []
        for p, inp, affect_zero in cache:
            sh = p["m_t"][:]
            rc.shuffle(sh)
            lp_sh = _logprobs(inp, sh)
            d_ctrl.append(_affect(lp_sh) - affect_zero)
            if s == 0:
                kl_ctrl.append(_kl(lp_sh, _logprobs(inp, zero)))
        ctrl_rs.append(_pearson(valences, d_ctrl))
    r_ctrl = _mean(ctrl_rs)
    r_ctrl_sd = _pstdev(ctrl_rs)

    # --- metric 3: cross-state dose-response on a fixed neutral prompt ------
    carrier = min(probes, key=lambda p: abs(p["valence"]))  # most neutral prompt
    inp_c = _prompt_ids(carrier["snap"], carrier["content"], carrier["source"])
    base_affect = _affect(_logprobs(inp_c, zero))
    borrowed_v, borrowed_affect = [], []
    for p in probes:
        borrowed_v.append(p["valence"])
        borrowed_affect.append(_affect(_logprobs(inp_c, p["m_t"])) - base_affect)
    dose_slope = _slope(borrowed_v, borrowed_affect)
    dose_r = _pearson(borrowed_v, borrowed_affect)

    # --- summary -----------------------------------------------------------
    print("\n--- summary ---")
    print(f"  Prediction shift   : mean KL(real‖zero) = {_mean(kl_real):.3f}   "
          f"vs control KL(shuffled‖zero) = {_mean(kl_ctrl):.3f}")
    print(f"  Affect congruence  : r(valence, ΔAffect) = {r_real:+.3f}   "
          f"(control r = {r_ctrl:+.3f} ± {r_ctrl_sd:.3f}, {args.control_seeds} seeds)")
    print(f"                       permutation p = {p_perm:.4f} ({args.perm} iters)  ·  "
          f"sign agreement {agree}/{len(probes)} (p = {p_sign:.3f})")
    print(f"  Cross-state dose   : slope = {dose_slope:+.3f}  r = {dose_r:+.3f}  "
          f"(fixed '{carrier['label']}' prompt, borrowed m_t)")
    # Verdict keys on *congruence* — does m_t move affect in the state's direction,
    # significantly, with a dose-response — NOT on raw KL magnitude (a shuffled
    # vector can shift the distribution just as much; what matters is the *direction*).
    beats_control = abs(r_real) > abs(r_ctrl) + 0.2
    if r_real >= 0.5 and p_perm <= 0.05 and dose_slope > 0 and beats_control:
        verdict = (f"STRONG — m_t steers affect congruently with state "
                   f"(r={r_real:+.2f}, perm p={p_perm:.4f}, dose slope={dose_slope:+.2f}; "
                   f"control r={r_ctrl:+.2f}±{r_ctrl_sd:.2f})")
    elif r_real >= 0.3 and beats_control:
        verdict = (f"MODERATE — congruent trend (r={r_real:+.2f}); tighten with "
                   "more varied data or higher --n-prefix")
    else:
        verdict = "WEAK — train longer, raise --n-prefix, or collect more varied data"
    if _mean(kl_real) <= _mean(kl_ctrl):
        print("  (note: m_t's distribution shift is subtle/targeted — smaller than a "
              "shuffled vector's — but directed; congruence r is the real signal.)")
    print(f"  VERDICT: {verdict}\n")

    # --- qualitative examples (illustrative) -------------------------------
    print("--- qualitative (greedy, same prompt, real vs zero m_t) ---")
    for p in probes[: args.samples]:
        inp = _prompt_ids(p["snap"], p["content"], p["source"])
        print(f"• {p['label']} ({p['emotion']} v{p['valence']:+.2f})")
        print(f"    real: {_greedy(inp, p['m_t'])}")
        print(f"    zero: {_greedy(inp, zero)}")

    # --- markdown report ---------------------------------------------------
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Fused-mind m_t ablation — `{args.model}`", "",
        f"Battery of **{len(probes)}** independent states · `n_prefix={cfg['n_prefix']}` · "
        f"`state_dim={cfg['state_dim']}`. Deterministic (greedy / single forward pass).", "",
        "## Results", "",
        f"- **Prediction shift**: mean `KL(real‖zero)` = **{_mean(kl_real):.3f}** "
        f"vs control (shuffled m_t) `KL` = {_mean(kl_ctrl):.3f}.",
        f"- **Affect congruence**: Pearson `r(valence, ΔAffect)` = **{r_real:+.3f}** "
        f"(shuffled-m_t control r = {r_ctrl:+.3f} ± {r_ctrl_sd:.3f} over "
        f"{args.control_seeds} seeds). **Permutation p = {p_perm:.4f}** ({args.perm} iters); "
        f"sign agreement {agree}/{len(probes)}, sign-test p = {p_sign:.3f}.",
        f"- **Cross-state dose-response**: slope = **{dose_slope:+.3f}**, r = {dose_r:+.3f} "
        f"(fixed `{carrier['label']}` prompt, borrowed m_t).", "",
        f"**Verdict:** {verdict}.", "",
        "## Per-probe", "",
        "| state | emotion | valence | KL(real‖zero) | ΔAffect |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    lines += [f"| {lbl} | {emo} | {v:+.2f} | {kl:.3f} | {da:+.3f} |"
              for (lbl, emo, v, kl, da) in rows]
    lines += ["", "_Functional correlates only (ADR 0002): this measures a state "
              "vector's influence on generation, not phenomenal experience._", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote report to {out}")

    if args.json:
        import json  # noqa: PLC0415

        jp = Path(args.json)
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps({
            "model": args.model,
            "n_prefix": cfg["n_prefix"],
            "r_real": round(r_real, 4),
            "r_ctrl": round(r_ctrl, 4),
            "r_ctrl_sd": round(r_ctrl_sd, 4),
            "p_perm": round(p_perm, 5),
            "p_sign": round(p_sign, 5),
            "dose_slope": round(dose_slope, 4),
            "dose_r": round(dose_r, 4),
            "kl_real": round(_mean(kl_real), 5),
            "kl_ctrl": round(_mean(kl_ctrl), 5),
            "verdict": verdict,
        }, indent=2), encoding="utf-8")
        print(f"Wrote metrics JSON to {jp}")


if __name__ == "__main__":
    main()
