---
license: apache-2.0
base_model: Qwen/Qwen2.5-0.5B-Instruct
library_name: peft
pipeline_tag: text-generation
tags:
  - cognitive-architecture
  - state-conditioning
  - affective-computing
  - lora
  - sentiance
  - functional-cognition
---

# Model card — Sentiance fused mind (`sentiance-fused`)

A small language model **conditioned on a cognitive-architecture state vector**. It
is the "fused mind" of the [Sentiance](https://github.com/sanjaydoc/Sentiance)
project (Path B / ADR 0005): a Qwen2.5-0.5B base with a LoRA adapter **and** a
trained *state encoder* that turns the mind's whole-cycle state vector `m_t` into
soft-prefix tokens, so generation is causally conditioned on the numeric state — not
on state described in words.

> **Honest stance (non-negotiable).** This is a **functional** artifact. `m_t` is a
> vector of functional variables (a valence, a drive level, a bond strength) named
> for the roles they play in the architecture. Conditioning a transformer on them
> buys *integration and end-to-end learnability* — **not** phenomenal experience.
> **No claim of consciousness or sentience is made or implied.** See
> [ADR 0002](docs/adr/0002-functional-not-phenomenal.md).

## What it is

- **Base:** `Qwen/Qwen2.5-0.5B-Instruct` (Apache-2.0).
- **Adapter:** LoRA (r=16, α=32) on the attention + MLP projections.
- **State encoder:** a small MLP mapping the 41-dim `m_t` → `n_prefix` (default 16)
  soft-prefix embeddings, trained **jointly** with the LoRA on the next-token loss.
- **`m_t`** encodes one tick of the cognitive cycle: valence/arousal/mood, a 14-way
  emotion one-hot, four drives, the attention source, goal presence, and 13
  per-faculty signals (frustration, longing, empathy, grief, curiosity, anticipation…).
  See `sentiance/mind/state_vector.py`.
- **Trained *state-blind*:** the felt state is **removed from the prompt** so `m_t` is
  the model's *only* state channel. (This is essential — see Results.)

## Intended use

Research into cognitive architectures + LLMs, affective/state-conditioned
generation, and neuro-symbolic integration. It is the inner voice of a Sentiance
`Mind`: `SENTIANCE_COGNITION_BACKEND=fused`.

**Not** a general chat model, an assistant, or a source of factual answers.

## How to run

This is **not** a plain `AutoModelForCausalLM` — the adapter alone is just a Qwen
fine-tune. The fused behavior needs the Sentiance runtime to compute `m_t` each tick
and inject it through the state encoder:

```bash
pip install -e ".[finetune]"     # from the Sentiance repo
# place the model dir at models/sentiance-fused (adapter + state_encoder.pt + fused_config.json)
SENTIANCE_COGNITION_BACKEND=fused python -m sentiance chat
```

## Results — does `m_t` actually steer it?

Measured with `scripts/eval_fused.py` (deterministic ablation over a 12-state
battery spanning valence −0.80…+0.85; prompt held identical, only the vector
changed) on a **12-state battery** spanning valence −0.80…+0.85. 234 blended training
examples.

**The effect is real but *data-scale-limited* — report it as a distribution, not a
single number.** Across training seeds (3-seed sweeps):

| conditioning | per-seed `r(valence, ΔAffect)` | mean ± std | strong (r≥0.5, p≤0.05) | mean `KL(real‖zero)` |
| --- | --- | --- | --- | --- |
| **prefix** (soft tokens) | +0.82, +0.74, −0.46 | **+0.37 ± 0.59** | 2/3 | 0.004 |
| **FiLM** (per-layer γ/β) | +0.83, −0.26, +0.63 | **+0.40 ± 0.47** | 2/3 | **0.10** |

The **best seeds are strong and significant** (r ≈ 0.8, permutation p ≈ 0.001–0.003,
dose-response slope > 0), but **~1 seed in 3 fails** and the variance is large — so
the honest summary is *directional but noisy*, limited by the small dataset, not
robust.

**Two controls both give `r ≈ 0`:** a *shuffled* `m_t` (structure destroyed), and the
*state-in-prompt* model (state left in the words, so the vector is redundant and
ignored). So the core claim holds as an **ablation**: *state-as-vector conditions the
model; state-as-text does not.*

**prefix vs FiLM (a negative result worth reporting):** injecting `m_t` deep (FiLM,
into every layer) makes its influence on the distribution **~25× larger** (KL 0.10 vs
0.004) but does **not** improve seed-to-seed reliability — both are noisy at this data
scale. The bottleneck is **data, not conditioning depth.**

Regenerate the numbers for any checkpoint with `scripts/eval_fused.py` (single) or
`scripts/robustness_fused.py` (across seeds).

## Limitations

- **Directional but noisy.** Mean congruence `r ≈ 0.4` across seeds with large std;
  ~1 seed in 3 does not learn the mapping. Not yet seed-robust — needs more data.
- **Small & blended.** ~234 self-generated examples across several characters; the
  voice is repetitive.
- **0.5B base**, English only, short first-person thoughts — not general text.
- **Self-generated data.** Traces come from Sentiance's own (partly rule-based)
  cognitive cycle, so the model learns *that* system's regularities, not the world's.
- **Functional only.** Nothing here evidences subjective experience.

## Training data & reproducibility

Self-labeled traces exported from Sentiance runs (`society` / `live` / `chat`),
deduplicated (incl. near-echo filtering), prepared **state-blind**. The full
pipeline (collect → prepare → train → eval) and the ablation control are documented
in the repo README and reproducible on a 6 GB laptop GPU.

## License & attribution

- This adapter + encoder: MIT (as the Sentiance repo).
- Base model `Qwen/Qwen2.5-0.5B-Instruct`: **Apache-2.0** — retain its notice; this
  is a derivative. See the Qwen model card for details.

## Citation

```
@software{sentiance_fused,
  title  = {Sentiance: a functional cognitive architecture with a
            cognition-conditioned language model (the fused mind)},
  author = {Sentiance contributors},
  year   = {2026},
  url    = {https://github.com/sanjaydoc/Sentiance}
}
```
