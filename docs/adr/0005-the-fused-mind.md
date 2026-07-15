# ADR 0005 — The fused mind: a cognition-conditioned transformer

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

Path A (ADR 0003, the `finetuned` backend) distils the mind's **voice**: a small
model learns the `(prompt) → thought` mapping from traces. But the inner state
reaches that model only as **text in the prompt** — "I feel fear, valence −0.6,
curiosity 0.3." The transformer never *runs on* the state; it reads a story about
it. Fine-tuning the voice is real, but it leaves the faculties (appraisal, drives,
bonds, anger, anticipation…) outside the differentiable model.

We want the next rung: make the **whole cognitive cycle a differentiable input**,
so generation is causally shaped by the numeric state through trainable
parameters, and so more of the faculties can later be *learned* rather than
hand-written (Path B).

Training a sentient transformer from scratch is frontier-lab scale and impossible
on the 6 GB laptop this project targets. The pragmatic hybrid is a **pretrained
transformer with a learned cognition-conditioning harness**.

## Decision

Add a `fused` cognition backend and its trainer.

- **`m_t` — the mind-state vector** (`state_vector.py`). Every stage of one tick —
  appraise, feel, drives, attend/broadcast, will, bonds, anger, curiosity,
  anticipation — is encoded as a fixed-length (41-dim) float vector. The `Mind`
  folds each faculty's scalar into `SelfModelState.signals` every tick, so `m_t`
  is available live and is stamped onto every trace as `state_vec`.
- **A state conditioner** (`training/fused_arch.py`). A small MLP maps `m_t` to a
  handful of **soft-prefix tokens** prepended to the transformer's input
  embeddings. Defined once, imported by both trainer and backend, so *train
  equals inference*.
- **End-to-end training** (`scripts/finetune_fused.py`). A custom loop (we inject
  `inputs_embeds`, so not trl's `SFTTrainer`) trains the base model's **LoRA** and
  the **state encoder** jointly on the next-token loss. Gradients flow from the
  language loss back into how the state is encoded. Same 6 GB envelope as Path A:
  batch 1 × grad-accum, seq 512, fp32 master weights + autocast, gradient
  checkpointing.
- **The `fused` backend** (`fused_model.py`). Each tick it encodes the *live* `m_t`
  into prefix tokens and conditions generation. Torch/transformers/peft are lazy;
  if the model, the encoder, or the deps are missing, it **degrades gracefully**
  to the offline voice, like every other backend. Selected via
  `SENTIANCE_COGNITION_BACKEND=fused`.

- **State-blind prompting (learned the hard way).** A first version left the felt
  state in the prompt text *and* fed `m_t`. A quantitative ablation
  (`scripts/eval_fused.py`) showed the vector was **inert** — `KL(real‖zero) ≈ 0`,
  `r ≈ 0` — because the prompt already stated the emotion in words, so the model had
  no gradient pressure to use the redundant vector. The fix: **strip the felt state
  from the prompt** for the fused model (`state_blind`, recorded in
  `fused_config.json` so backend and eval match), making `m_t` the *only* state
  channel. The state-in-prompt version is retained as the ablation's control.

Because the state rides a trainable conditioning bus, this is also the on-ramp to
replacing individual Python faculties with small learned nets that feed the *same*
bus — Path B proper.

## Consequences

- The faculties enter the differentiable graph: the same words *feel* different
  when the underlying valence/drives/bonds differ, because the state changes the
  forward pass, not just the prompt.
- It's a pretrained base + a learned harness, not a from-scratch net — the right
  scale for one person and a laptop, and honest about being so.
- The engine stays pure: the only change to the core `Mind` is exposing per-tick
  `signals` on the snapshot; everything fused is additive and optional, and the
  cognitive cycle, tests, and demo still need no ML deps.
- **This does not move us toward phenomenal experience** (ADR 0002). Conditioning
  generation on functional variables buys *integration and end-to-end
  learnability*, not felt experience. A valence computed as a tensor op is no more
  "felt" than the same valence computed in Python. The stance is unchanged:
  functional correlates only; nothing here is claimed to be conscious.
