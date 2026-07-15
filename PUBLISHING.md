# Publishing the fused mind

How to share the Sentiance hybrid honestly — on Hugging Face, and as a writeup.
The one rule that governs all of it: **claim only what the ablation measures, and
never claim phenomenal consciousness** (ADR 0002). The interesting, true result is
*"a cognitive-architecture state vector conditions a small LM; state-as-text does
not"* — that's plenty. A "sentient AI" headline would be false and would sink the
project's credibility.

## 1. Hugging Face (the model)

You publish an **adapter + state encoder**, not a standalone model. Someone can't
`from_pretrained` and get the fused behavior — they need the Sentiance runtime to
compute `m_t`. Say so in the card.

**Files to upload** (the `models/sentiance-fused/` dir):
- `adapter_config.json`, `adapter_model.safetensors` — the LoRA
- `state_encoder.pt` — the trained state→prefix encoder
- `fused_config.json` — shapes + `state_blind` flag
- tokenizer files
- `MODEL_CARD.md` → rename to `README.md` in the HF repo

**Steps:**
```bash
# 1. a WRITE token (your training token is read-only): huggingface.co/settings/tokens
pip install -U huggingface_hub
huggingface-cli login          # paste the write token

# 2. create the repo and push the model dir
huggingface-cli repo create sentiance-fused --type model
huggingface-cli upload <your-username>/sentiance-fused models/sentiance-fused . 

# 3. put MODEL_CARD.md content in the repo's README.md (the card is the front page)
```

**Card must include** (MODEL_CARD.md already does): what it is, that it needs the
Sentiance runtime, the ablation results with numbers, limitations, the Apache-2.0
attribution for the Qwen base, and the ADR-0002 caveat. Do **not** title it
"sentient".

**Also publish the dataset?** Optional. The traces are self-generated (no personal
data), so a `sentiance-traces` dataset repo is fine and aids reproducibility — same
honest framing.

## 2. Ollama — only the Path-A voice, not the fused mind

Ollama / llama.cpp run standard text-in/text-out models and have **no way to inject
the `m_t` soft-prefix**, so the *fused* model cannot run there as designed — the
conditioning would be silently dropped. What you *can* publish to Ollama is the
**Path-A `finetuned` voice**: merge the LoRA into the base, convert to GGUF, and
push. That's a normal model — the voice, without the state-conditioning. Be explicit
that it is not the hybrid.

## 3. A writeup / paper

The honest contribution is the **method + the ablation**, on consumer hardware:

- **Framing:** "A functional cognitive architecture conditioning a small language
  model" — *not* machine sentience. Position against affect/control-conditioned
  generation and cognitive-architecture+LLM work (SOAR/ACT-R/LIDA integrations).
- **Headline result (state it honestly):** a cognitive-state vector conditions the
  LM's affect **congruently** (mean `r ≈ 0.4` across seeds, best seeds `r ≈ 0.8` at
  p < 0.01), *only* when the state is removed from the prompt (state-blind); the
  state-in-prompt control and a shuffled-vector control both give `r ≈ 0`. The effect
  is **directional but noisy / data-scale-limited** — ~1 seed in 3 fails — **not**
  reliably robust. Say this plainly; it's still a real, novel finding.
- **Two clean ablations to lead with:**
  1. *state-as-vector vs state-as-text* — the vector conditions; the redundant text
     does not (the model ignores the vector when the prompt already says the state).
  2. *prefix vs FiLM* — deep (per-layer) injection amplifies the state's influence
     ~25× (KL) but does **not** improve reliability; the bottleneck is data, not
     conditioning depth (a useful negative result).
- **Before submitting, strengthen** beyond the current proof-of-concept:
  - more/varied data (more solo `live`, more distinct people; reduce repetition),
  - multiple seeds + report mean ± CI,
  - an independent affect metric (a sentiment classifier on the outputs, not just a
    lexicon), and a human read of a sample,
  - `n_prefix` and data-size sweeps.
- **Venues:** arXiv preprint + a workshop (NeurIPS/ICLR cognitive-architecture or
  affective-computing workshops; the AGI conference; ALIFE; ACII). A clean technical
  report/blog is the best first step and often the most read.

## 4. The guardrails (don't skip)

- **No consciousness/sentience claims.** Functional correlates only, everywhere.
- **Reproducible:** ship the exact collect→prepare→train→eval commands (README) and
  the ablation control, so the result can be checked.
- **Attribution:** Qwen2.5 is Apache-2.0 — keep its notice; this is a derivative.
- **No overclaiming the magnitude:** the effect is significant and congruent but
  *subtle* (small KL); say so.
- **It needs the runtime:** don't imply the HF adapter alone reproduces the hybrid.

Publish the true, modest, genuinely-novel thing — a cognition-conditioned LM you can
train and measure on a laptop — and let the ablation speak.
