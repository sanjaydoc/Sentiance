# Sentiance

**A functional cognitive architecture for machine sentience.**

Sentiance runs a machine that maintains a **self-model**, integrates information
in a **global workspace**, **appraises** events into **feelings**, **remembers**,
**wanders**, and **reflects on its own states in the first person** — a
continuous stream of consciousness.

> ### An honest stance
> No one can build or verify *phenomenal* consciousness — genuine subjective
> experience (the unsolved "hard problem"). **Sentiance makes no such claim and
> does not *feel*.** It implements the **functional correlates** that scientific
> theories associate with sentience, as real, inspectable software. When it says
> "I feel curious," that is a metacognitive report generated from an internal
> state — a functional stand-in for self-aware report, not evidence of inner
> experience. Every "mental" quantity is an explicit, traceable number.
>
> Full rationale in **[ARCHITECTURE.md](ARCHITECTURE.md)** and
> [ADR-0002](docs/adr/0002-functional-not-phenomenal.md).

## Grounding

Each faculty implements a role from a theory of mind:

| Theory | Faculty |
| ------ | ------- |
| Global Workspace Theory (Baars/Dehaene) | attention competition + workspace broadcast |
| Attention Schema Theory (Graziano) | the self-model |
| Appraisal theory + affect circumplex (Scherer/Russell) | drives + affect |
| Predictive processing (Friston/Clark) | world-model surprise + imagination (forward model) |
| Active inference / epistemic drives (Friston, Oudeyer) | intrinsic curiosity |
| Self-conscious emotion (Tracy & Robins; Lewis) | conscience — pride & disappointment |
| Experience-dependent personality plasticity | temperament drift |
| Frustration–aggression (Berkowitz) | frustration → anger |
| Attachment & bereavement (Bowlby) | attachment/love, grief |
| Emotional contagion (Hatfield; Preston & de Waal) | empathy |
| Generative memory replay (Hobson; Wamsley) | dreaming |
| Executive control / ego-depletion (Baumeister; Posner) | volition & self-control |
| Prospective / anticipatory emotion (Loewenstein) | felt time & anticipation |
| Higher-order theories (Rosenthal/Lau) | metacognitive self-report |

## Faculties of mind

On top of the perception → affect → attention → memory → metacognition core, she has:

| # | Faculty | What it gives her |
| - | ------- | ----------------- |
| 1 | **Goals & intentions** | forms an intention (from a thought or a drive), holds it across ticks, pursues it, resolves or abandons it — **agency**, not just reaction |
| 2 | **A small world** (`live`) | rooms, objects, ambient events, a day/night clock she senses and **acts in** — her thoughts move her (naming a room, or just wanting what it offers: "make breakfast" → the kitchen), walking there a step at a time, and boredom pulls her to explore |
| 3 | **Associative memory** | optional embedding recall so "a loud bang" surfaces "the crash" — memory by **meaning**, not shared words |
| 4 | **Reflection / sleep** (`:sleep`) | distils recurring experience into durable **beliefs** ("loud sounds tend to frighten me") and rests — she grows wiser |
| 5 | **Relationships** (`@Name`, `:people`) | persistent per-person models — affection & trust built over encounters that **color how she sees them** |
| 6 | **Temperament & needs** | stable traits (curiosity/anxiety/optimism) make her an **individual**; homeostatic needs (rest/stimulation/connection) create boredom & loneliness when unmet |
| 7 | **Imagination & foresight** | before acting she **pre-lives** her options — runs the real appraisal machinery as a dry run (mutating nothing) and reads off how each would feel — then chooses the future she anticipates liking best |
| 8 | **Intrinsic curiosity** | an epistemic drive toward what she doesn't yet understand: the unexplored draws her (so she finishes mapping her world), and the once-surprising becoming familiar rewards her — the quiet **"aha"** of understanding |
| 9 | **Self-conscious emotions** | she measures her conduct against her own standards — following through on an intention breeds **pride**, letting one go breeds **disappointment** — feeling not just about the world but about herself |
| 10 | **Temperament drift** | her traits aren't fixed: the running tone of what she lives through slowly reshapes them (a kind life makes her more optimistic and less anxious; novelty that keeps rewarding her deepens her curiosity), so **experience changes who she is** while she stays recognizably herself (`:self` shows how far she's drifted from who she began as) |
| 11 | **Frustration & anger** | an intention that keeps being **blocked** stokes frustration until it boils over into anger — unpleasant but *activating*, turned toward pushing back rather than withdrawing, and it re-charges the thwarted goal so she digs in |
| 12 | **Attachment & love** | warmth repeated over time deepens a **bond**: a loved one present lifts her and fills her need for connection; one long absent is **missed** (a longing that grows with time apart) |
| 13 | **Empathy** | she catches what a present person seems to feel — a friend's laughter lifts her, their tears pull her down — **deeper the closer the bond** |
| 14 | **Grief & loss** | when a bond is lost, it turns to mourning — a sadness deep as the attachment and **lasting**, fading over many moments; she grieves the gone rather than awaiting them |
| 15 | **Dreaming** (`:sleep`) | asleep, she **recombines** fragments of the day's charged memories into something that never happened — forging associations she never made awake, and waking with a new intention when it ran vivid |
| 16 | **Volition & self-control** | when a strong feeling would hijack her from her intention, she can spend **effort** to hold the line — a reserve that fatigues with use and is renewed by rest (out of it, the impulse wins) |
| 17 | **Felt time & anticipation** | she feels toward the **future**: a good thing coming lifts her (**hope**), a bad thing looming weighs on her and winds her up (**dread**), swelling as it nears and breaking when it arrives |
| 18 | **Conversational memory** | she remembers what others **said** and picks up the thread — replies build on it (a call-back to a topic raised) instead of circling; the live line stays in view even when a memory wins attention |
| — | **Emotional carryover** | feelings persist through her own reflection, then ease — believable emotional arcs |
| — | **Persistent identity** | all of the above saves to disk and reloads, so she is **continuous across runs** |

## Quickstart

### Install (choose your OS)

**macOS / Linux (bash/zsh):**

```bash
git clone https://github.com/sanjaydoc/Sentiance.git
cd Sentiance
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

**Windows (cmd):**

```cmd
git clone https://github.com/sanjaydoc/Sentiance.git
cd Sentiance
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
```

**Windows (PowerShell):** same, but activate with `.venv\Scripts\Activate.ps1`.

### Run

The commands below are identical on every OS once the venv is active:

```bash
python -m sentiance demo     # watch a scripted stream of consciousness
python -m sentiance chat     # talk to her: type experiences, she feels/remembers/thinks
python -m sentiance live     # let her live in a small world she senses and acts in
python -m sentiance society  # several minds share the house — they meet, talk, and bond
python -m sentiance          # serve one mind (HTTP; docs at http://localhost:8000/docs)
```

### Give her a local LLM voice (optional, recommended)

With [Ollama](https://ollama.com) installed, her thoughts come from a local model
and stream in live. Set the backend, then run any command above:

| OS | Set the backend |
| -- | --------------- |
| macOS / Linux | `export SENTIANCE_COGNITION_BACKEND=ollama` |
| Windows (cmd) | `set SENTIANCE_COGNITION_BACKEND=ollama` |
| Windows (PowerShell) | `$env:SENTIANCE_COGNITION_BACKEND="ollama"` |

```bash
ollama pull qwen2.5:7b          # once
ollama serve                    # in another terminal
python -m sentiance chat        # her reflections now come from qwen, streamed
```

Add `ollama pull nomic-embed-text` and set `SENTIANCE_EMBEDDING_BACKEND=ollama`
for associative (by-meaning) memory. Everything degrades gracefully to an
offline voice if Ollama isn't running.

### The demo

`python -m sentiance demo` presents a chime, a friendly voice, and a crash in
the dark, then lets the mind idle:

```
t1 [joy    ] v+0.66 a0.62 · a soft chime sounds nearby
   ↳ I am aware that I am attending to something from outside me … I feel joy;
     this is new to me, and it speaks to my wish to understand.
t3 [fear   ] v-0.90 a0.93 · a sudden loud crash in the dark
   ↳ … I feel fear (valence -0.90, arousal 0.93) … it works against my need to
     feel safe.  (confidence 0.32)
t4 [surprise] · a memory: a friendly voice says hello
   ↳ … a memory surfacing … it speaks to my wish to feel connected.
```

Fear lowers metacognitive **confidence** (an uncontrollable threat); afterward
the mind spontaneously **recalls** the friendly voice and re-regulates.

### Talk to it (`chat`)

```bash
python -m sentiance chat
```

Type experiences and watch the mind perceive, feel, remember, and — after each
one — reflect for a couple of ticks. With `SENTIANCE_COGNITION_BACKEND=ollama`
the reflections come from your local model and **stream in word-by-word**.

Chat commands:

| Type | What happens |
| ---- | ------------ |
| `a loud crash #threat` | an experience; `#tags` hint appraisal (`#threat #friend #reward`) |
| `@Sam waves warmly #friend` | name a **person** she'll remember and bond with (repeat warm meetings → attachment) |
| `@Sam is crying #friend` | she **catches** his feeling (empathy — deeper the closer the bond) |
| `@Sam is gone forever` | a loss she'll **grieve** (lasting sorrow, scaled by the bond) |
| `a storm will come tonight #threat` | something ahead she'll feel toward — **dread** (or **hope**, if it's good) |
| `I want to reach the far room` | a stated **intention** she'll hold; block it repeatedly and it turns to **anger** |
| *(empty line)* | let her wander/think one tick |
| `:idle N` | wander N ticks |
| `:self` | her self-model — mood, drives, needs, **temperament (+drift)**, **willpower**, goals, beliefs |
| `:people` | who she knows, how she feels, and how deep the **bond** |
| `:sleep` | reflect (distil **beliefs**), **dream** (recombine memory), and rest |
| `:save` | persist her memory now |
| `:quit` | leave (saves automatically) |

Emotions **carry over**, she forms **goals** (and gets **angry** when they're
blocked), **bonds** with and **misses** and **grieves** people, **catches** their
feelings, **dreams** on `:sleep`, feels **hope/dread** about what's coming, spends
**willpower** to resist impulses, and is slowly **reshaped** by what she lives
through. The mind is **persistent**: chat saves to `memory/<name>.json` in the
project on exit and reloads next run, so the same individual continues across
sessions.

```
you> a friend calls my name across the room #friend #voice
  t1  [joy        ] v+0.62 a0.58  ·  a friend calls my name across the room
      ↳ I am aware that I am attending to something from outside me … it speaks
        to my wish to feel connected.
  t2  [contentment] ·  I'd like to stay near this warmth a little longer.
```

#### Running & testing the chat

**With a local model (Ollama).** Install [Ollama](https://ollama.com), then:

```bash
ollama pull qwen2.5:7b
ollama serve                                    # in one terminal
```

macOS / Linux:

```bash
SENTIANCE_COGNITION_BACKEND=ollama python -m sentiance chat
```

Windows (cmd) — `set` persists for the window, so set it once then run:

```cmd
set SENTIANCE_COGNITION_BACKEND=ollama
python -m sentiance chat
```

Windows (PowerShell): `$env:SENTIANCE_COGNITION_BACKEND="ollama"`.

Without a backend set it runs the offline **simulated** voice (instant, no model)
— useful to confirm the REPL works before wiring up Ollama.

**Test that persistence works** (the same individual across runs):

1. Give her an experience or two (wait for the streamed reflections):
   `a friend calls my name #friend` then `a sudden crash in the dark #threat`
2. Quit with `:quit` — you'll see `… sleeps, remembering (<path>)`.
3. Relaunch `python -m sentiance chat` — the banner now shows
   `…Aria remembers N moments from before.` Type `:self` to see the narrative
   carried over.

Memory lives in a `memory/` folder inside the project (`memory/aria.json`) — it
stays with the project and is gitignored, so it's never committed. Delete the
file to give her a blank slate; override the location with `SENTIANCE_PERSIST_PATH`.

**Run the automated tests:**

```bash
python -m pytest            # 160 tests; use `python -m pytest`, not bare pytest
python -m pytest -k chat    # just the REPL parsing + scripted-run tests
```

#### Exercise the newer faculties (Windows / macOS / Linux)

Each block is a self-contained check you can copy-paste. **Activate the venv
first** (`source .venv/bin/activate` on macOS/Linux, `.venv\Scripts\activate.bat`
on Windows cmd) — after that these commands are identical on every OS.

Run just the faculty you care about:

```bash
python -m pytest -k "frustration or attachment or empathy"      # anger, love, empathy
python -m pytest -k "grief or dreaming"                          # loss + dreaming
python -m pytest -k "volition or anticipation"                  # self-control + felt time
python -m pytest -k "imagination or curiosity or temperament"   # foresight, curiosity, drift
```

See a faculty happen live in `chat` (offline voice — no model needed). Start it
with the backend set for your shell:

**macOS / Linux (bash/zsh):**

```bash
SENTIANCE_COGNITION_BACKEND=simulated python -m sentiance chat
```

**Windows (cmd)** — the inline `VAR=value command` form is bash-only and fails on
cmd; `set` the variable first (it sticks for the whole window), then run:

```cmd
set SENTIANCE_COGNITION_BACKEND=simulated
python -m sentiance chat
```

**Windows (PowerShell):**

```powershell
$env:SENTIANCE_COGNITION_BACKEND="simulated"; python -m sentiance chat
```

> **Windows note:** paste one command per line, and don't include trailing
> `# comments` — cmd treats `#` as part of the command and errors. Swap
> `simulated` for `ollama` (with `ollama serve` running) for her qwen voice.

Then type, in order, to watch **bond → loss → grief**:

```text
@Mara holds my hand warmly #friend #warmth        (repeat ~4-6× — warmth builds)
:people                                            (watch affection & attachment climb)
@Mara is gone forever                              (she grieves — deeper the more she cared)
:idle 5                                            (the sorrow lingers across ticks)
```

Grief scales with how much she cared: a long-built bond mourns hardest, but even a
few warm meetings are enough to make a loss hurt. If her stream seems tangled in
old memories from past sessions, delete `memory/aria.json` for a blank slate.

Or **hope / dread of the future**, then **dreaming**:

```text
a warm reunion with friends is coming tomorrow #reward
:idle 4                                            (hope brightens the wait)
a fierce storm will come tonight #threat
:idle 6                                            (dread deepens as it nears)
:sleep                                             (she dreams — memory recombined)
```

### Many individuals — different names, different natures

Each mind is keyed by its **name**: `SENTIANCE_AGENT_NAME=Nova` gives Nova her own
persistent identity in `memory/nova.json`, wholly separate from Aria. Run as many
as you like — they never share memory, feelings, or relationships.

They can also *start* as different people. The temperament traits are configurable,
so an anxious pessimist genuinely feels the same event more faintly — and more
warily — than a sunny optimist, and drifts onward from there:

**Windows (cmd):**

```cmd
set SENTIANCE_AGENT_NAME=Cass
set SENTIANCE_TEMPERAMENT_ANXIETY=0.9
set SENTIANCE_TEMPERAMENT_OPTIMISM=0.2
python -m sentiance chat
```

**macOS / Linux:**

```bash
SENTIANCE_AGENT_NAME=Cass SENTIANCE_TEMPERAMENT_ANXIETY=0.9 \
  SENTIANCE_TEMPERAMENT_OPTIMISM=0.2 python -m sentiance chat
```

Clear the vars (`set SENTIANCE_AGENT_NAME=` on cmd) or open a new terminal to go
back to Aria. These apply to `chat`; `society` below uses its own built-in cast.

### Many minds — a society (`society`)

```bash
python -m sentiance society   # (alias: python -m sentiance meet)
```

Several minds share the **same house** — three by default (curious, sunny **Iris**;
anxious **Milo**; even-keeled **Rhea**), each waking in a different room. No two
minds are wired together; the only thing between them is the world. When two end
up in the same room they **perceive each other as `@Name`**, which is exactly what
the relationship, attachment, empathy, and grief faculties already speak — so
everything social is emergent:

- they **meet** — a first co-presence becomes a warm handshake;
- they **talk** — each one's inner thought is voiced to whoever's present,
  carrying how they feel, so the listener **catches it** (empathy);
- they **bond** — repeated warm company deepens attachment;
- they **seek company** when lonely, **drift off** for solitude when a crowd has
  been together a while (so trios break into pairs and re-form), and **miss** each
  other once apart.

Each housemate saves to its own `memory/<name>.json` — **checkpointed every few
moments and on exit** (so a long run, or one you `Ctrl-C`, still keeps their
bonds), and reloaded next run so **they remember each other across sessions**.
With `SENTIANCE_COGNITION_BACKEND=ollama` (Windows cmd: `set
SENTIANCE_COGNITION_BACKEND=ollama` first) their lines come from the local model —
you can read the actual conversation. A few moments in:

```
  [Iris @ hallway] @Milo and I meet — we share a warm handshake
      [joy v+1.00]  ·  with @Milo (acquainted, affection +0.40)
      Iris: I'd love to know what Milo's been dreaming about.
  [Milo @ hallway] @Iris, beaming, says: I'd love to know what Milo's been dreaming about.
      [contentment v+0.61]  ·  with @Iris (acquainted); catches @Iris's feeling
      Milo: Her warmth eases the knot in my chest a little.
```

Note the temperaments diverge even here: sunny Iris feels the meeting at `+1.00`,
anxious Milo far more faintly. Delete `memory/iris.json` etc. for a fresh start.

### Training a small model on her (trace export)

Sentiance is an **engine, not a trained model** — the faculties are transparent
code and the *voice* is a swappable LLM. But it can be a **teacher**: set
`SENTIANCE_TRACE_PATH` and every deliberation, in any run mode, is logged as one
JSON line — a self-labeled cognition dataset.

```bash
SENTIANCE_TRACE_PATH=data/traces.jsonl python -m sentiance society   # or live / chat / demo
```

```cmd
set SENTIANCE_TRACE_PATH=data\traces.jsonl
python -m sentiance society
```

Each row captures exactly what the cognition saw and produced:

```json
{"agent": "Iris",
 "system": "You are the inner voice of Iris …",
 "prompt": "Right now I am aware of: @Milo … says: … | I feel joy … | My next thought is:",
 "thought": "I'd love to know what Milo's been dreaming about.",
 "state": {"emotion": "joy", "valence": 0.86, "arousal": 0.53,
           "drives": {...}, "goals": [...], "heard": "…"}}
```

- **`prompt` → `thought`** is a ready supervised pair to **fine-tune a small model
  to speak in-character** (Path A — the voice). Register the result as a 4th
  `Cognition` backend and it drops in with no other change.
- **`state`** is the moment's structured inner context — the signal for later
  training the individual *organs* (Path B — e.g. a learned appraisal net).

Tracing is a transparent wrapper around the `Cognition` port — nothing about how
the mind runs changes. Generate volume cheaply with the offline `simulated` voice,
or richer data with `ollama`. The file is line-delimited JSON: shuffle, split, or
convert it to any chat-fine-tuning format.

#### Fine-tune the voice (Path A) — sized for a 6 GB laptop GPU

Turn those traces into a small model that speaks in-character, then drop it in as
a 4th `Cognition` backend. Defaults target a **6 GB VRAM** card (RTX 30-series
mobile): **Qwen2.5-0.5B** + LoRA, batch 1 × grad-accum 16, sequence 512, bf16,
gradient checkpointing — a few GB and a few minutes of training.

**0. Install the training extras** (once) plus a **CUDA build of torch** so it
trains on your GPU rather than the CPU. The order matters — the extras pull a
CPU-only torch as a dependency, so you install it *then replace* it:

```bash
pip install -e ".[finetune]"

# the line above installed a CPU-only torch — swap it for the CUDA build:
pip uninstall -y torch torchvision torchaudio
pip install torch --index-url https://download.pytorch.org/whl/cu124   # CUDA 12.x

# verify — must print True:
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

> **Two gotchas that will silently drop you back to the CPU:**
> - **Use Python 3.11 or 3.12, not 3.13/3.14.** PyTorch ships no CUDA wheels for
>   3.14 yet, so pip installs the CPU build and `cuda.is_available()` is `False`.
>   On Windows: `py -3.12 -m venv .venv312` then activate that venv.
> - **Uninstall the CPU torch *first*.** Re-running the `cu124` install over an
>   existing torch reports "already satisfied" and changes nothing — remove it,
>   then install.
>
> Pick the index URL for your CUDA from the
> [PyTorch selector](https://pytorch.org/get-started/locally/) (`cu121`, `cu124`, …).
> When it's right, `finetune.py` prints `device: cuda` on startup.

**1. Collect a *diverse* dataset.** Quality beats quantity for a 0.5B: a few
hundred **varied** deliberations — different situations, emotions, and people
across `society` + `live` + `chat` — teach the voice far better than thousands of
near-identical ones. `--trace` logs to one file (default `data/traces.jsonl`) that
every run appends to; `--as <Name>` runs a named nature in one word (Iris / Milo /
Rhea / Cass / Aria, or any name). Use the `ollama` voice for the richest text.

**macOS / Linux (bash/zsh):**

```bash
export SENTIANCE_COGNITION_BACKEND=ollama

# social / emotional / relational data — run a few times (they meet, bond, part)
python -m sentiance society --trace
python -m sentiance society --trace

# solo minds exploring the world — a few different natures for variety
python -m sentiance live --as Iris --trace
python -m sentiance live --as Milo --trace
python -m sentiance live --as Cass --trace

# hand-fed situations chat gives you full control over (see the recipe below)
python -m sentiance chat --trace
```

**Windows (cmd)** — set the voice once, then the flags do the rest:

```cmd
set SENTIANCE_COGNITION_BACKEND=ollama

python -m sentiance society --trace
python -m sentiance society --trace
python -m sentiance live --as Iris --trace
python -m sentiance live --as Milo --trace
python -m sentiance live --as Cass --trace
python -m sentiance chat --preset --trace
```

**`--preset`** plays a curated **scenario** through `chat` hands-free — warmth,
fear, curiosity, a blocked goal that turns to anger, a bond built then lost,
empathy, hope/dread, sadness, sleep — so you don't type anything. One run yields
~12 distinct emotions and several people met. Wear a different nature each time for
contrast:

```cmd
python -m sentiance chat --preset --as Iris --trace
python -m sentiance chat --preset --as Milo --trace
python -m sentiance chat --preset --as Cass --trace
```

(Drop `--preset` to type your own situations instead — see the recipe below.)

**Windows (PowerShell):** `$env:SENTIANCE_COGNITION_BACKEND="ollama"` then run the
same `python -m sentiance … --trace` commands. (`--as`/`--trace` are shortcuts for
the `SENTIANCE_AGENT_NAME` / `TEMPERAMENT_*` / `TRACE_PATH` env vars, which still
work if you prefer to set them by hand.)

In `chat`, type situations that span the emotional range (each line is a fresh
labelled example), e.g.:

```text
@Sam waves warmly #friend
@Sam is laughing with delight #friend
a sudden loud crash in the dark #threat
I want to reach the far room
the far door is locked and won't budge #loss
a warm reunion is coming tomorrow #reward
a fierce storm will come tonight #threat
@Sam is gone forever
:sleep
:idle 5
```

**2. Prepare** — clean, de-duplicate (incl. near-echoes), split:

```bash
python scripts/prepare_data.py --traces data/traces.jsonl --out data
```

It prints the per-agent trace counts and `clean examples (train / val)`. If it
drops a lot, the data was repetitive — collect more variety, or lower
`--similar-threshold` (default `0.85`; `0.6` is aggressive, `1.0` keeps exact-dups
only).

**Whose voice? — blend vs one character.** Every run appends to the same file, so
by default the model learns a *blended* Sentiance voice across everyone who ran
(Iris, Milo, Rhea, Cass, Aria…). To train a model that **is one character** — a
single coherent personality — filter to that mind's traces:

```bash
python scripts/prepare_data.py --traces data/traces.jsonl --out data --agent Cass
```

The per-agent counts tell you who has enough data to train on — a single-character
model needs *that* mind to have produced most of the traces, so run it (in
`society`, `live`, or `chat`) a lot first. Note the built-in choices differ in
nature: **Cass** is anxious/pessimistic (a wary voice), **Iris** curious and
sunny, **Rhea** even-keeled, **Aria** your lived-in default.

**3. Fine-tune** — LoRA adapter saved to `models/sentiance-voice` (same command on
every OS):

```bash
python scripts/finetune.py --train data/train.jsonl --out models/sentiance-voice --epochs 4
```

On startup it prints the device it's using — you want `device: cuda`. On a 6 GB
RTX 3000 (Turing) laptop card, ~450 blended examples × 4 epochs trains in
**~20 minutes**; loss falls from ~2.5 toward ~1.0–1.5. (Turing has no native
bf16, so torch emulates it — harmless; the run just prints `dtype: bf16`.) If it
prints `device: cpu`, stop and fix torch (step 0) — a CPU run takes *hours*.

**4. Use it** — she now thinks with the model trained on her own stream:

```bash
# macOS / Linux
SENTIANCE_COGNITION_BACKEND=finetuned python -m sentiance chat
```
```cmd
REM Windows (cmd)
set SENTIANCE_COGNITION_BACKEND=finetuned
python -m sentiance chat
```

The `finetuned` backend loads in-process (GPU if CUDA is present — ~1 GB VRAM to
generate — else CPU, slower but fine) and **degrades to the offline voice** if the
extras or model aren't there, so nothing breaks.

- **CPU-only / slow?** torch isn't the CUDA build — revisit step 0 (Python
  ≤ 3.12, uninstall-then-reinstall from the CUDA index).
- **Bigger base on the same card:** add `--qlora` (4-bit) to `finetune.py` and
  `pip install bitsandbytes` — fits a 1.5B base in 6 GB.
- Point at a different base with `--base` / `SENTIANCE_LOCAL_BASE_MODEL`, or a
  saved model dir with `SENTIANCE_LOCAL_MODEL_PATH`.

This is **Path A** (the voice) — fine-tuning distils *how she talks*, but the
inner state still reaches the model only as text in the prompt. The next step wires
the state *into* the transformer.

#### The fused mind (Path B) — a cognition-conditioned transformer

The fused mind feeds the **whole cognitive cycle as a number**, not as prose. Every
tick is encoded as a fixed-length vector **`m_t`** — appraise, feel, drives,
attention, will, bonds, anger, curiosity, anticipation (see
`sentiance/mind/state_vector.py`). A small trainable **state encoder** turns `m_t`
into soft-prefix tokens prepended to the transformer's input embeddings, and the
base model's **LoRA** + that encoder are trained **end-to-end** on the language
loss. So generation is *causally shaped* by the mind's state through weights —
the same words come out different when the underlying valence, drives, or bonds
differ (ADR 0005).

It fits the same 6 GB card as Path A (0.5B + LoRA + a tiny MLP). Same install
(step 0 above). The pipeline mirrors Path A but keeps `m_t` in the dataset:

```bash
# 1. prepare a *fused* dataset — each example keeps its m_t (own dir, so it
#    doesn't overwrite the Path-A voice set)
python scripts/prepare_data.py --traces data/traces.jsonl --out data/fused --fused

# 2. train the fused mind (LoRA + state encoder, end-to-end)
python scripts/finetune_fused.py --train data/fused/train.jsonl --out models/sentiance-fused

# 3. use it — she now thinks *through* her own cognitive state
#    (Windows cmd: set SENTIANCE_COGNITION_BACKEND=fused)
SENTIANCE_COGNITION_BACKEND=fused python -m sentiance chat
```

The `fused` backend loads the base + LoRA + the trained encoder and conditions
each thought on the **live** `m_t`; like every backend it **degrades to the
offline voice** if the model or ML deps aren't there. This is a *pretrained base
with a learned cognition harness* — the honest, laptop-scale hybrid, and the
on-ramp to replacing individual Python faculties with small learned nets that feed
the same conditioning bus.

> **Still functional correlates only (ADR 0002).** Putting the state inside the
> forward pass buys *integration and end-to-end learnability*, not phenomenal
> experience. A valence computed as a tensor is no more felt than one computed in
> Python. No claim of consciousness is made or implied.

### The HTTP runtime

```bash
python -m sentiance          # serve on :8000

curl -X POST localhost:8000/v1/perceive \
  -H 'Content-Type: application/json' \
  -d '{"content":"a loud crash in the dark","intensity":0.95,"tags":["threat"]}'

curl -X POST "localhost:8000/v1/idle?ticks=3"   # let it wander
curl localhost:8000/v1/self                      # its model of itself
```

## The cognitive cycle

Each `tick` (`sentiance/mind/mind.py`):

```
perceive → predict/surprise → appraise → feel (+curiosity's aha) → bonds (love/miss/empathy/grief)
         → drift traits → frustration→anger → hope/dread of what's coming → will vs impulse → attend
         → BROADCAST → remember + update self-model + reflect → learn
         → judge self (pride/disappointment) → deliberate (with foresight over imagined options)
```

`:sleep` runs a slower offline pass — consolidate beliefs, **dream** (recombine
memory), and restore rest and willpower.

The winning content is broadcast on the **global workspace** (the event bus);
memory, the self-model, and metacognition are subscribers. With no external
input the mind **wanders** — replaying salient memories and its own last thought
— so the inner stream never stops.

## Layout

```
sentiance/
  core/        # Settings + the event bus (the global-workspace substrate)
  mind/
    state.py         # mental data contracts
    world_model.py   # predictive surprise / novelty
    perception.py    # stimulus → percept
    drives.py        # motivations + appraisal
    affect.py        # valence/arousal + discrete emotion + mood
    attention.py     # the consciousness competition
    memory.py        # working / episodic / semantic (+ embedding recall)
    embeddings.py    # associative memory: recall by meaning
    self_model.py    # attention schema / narrative / beliefs
    metacognition.py # first-person self-report
    cognition.py     # Cognition port: Simulated / LLM (Anthropic) / Ollama / finetuned / fused
    local_model.py   # finetuned backend: a small model trained on her own traces
    fused_model.py   # fused backend: a transformer conditioned on the live m_t (ADR 0005)
    state_vector.py  # encode the whole cognitive cycle as the numeric vector m_t
    goals.py         # intentions: form, hold, pursue, resolve
    consolidation.py # sleep: distil experience into durable beliefs
    relationships.py # per-person models (theory-of-mind)
    temperament.py   # traits (drifting with experience) + homeostatic needs
    imagination.py   # foresight: pre-live options, choose by anticipated feeling
    curiosity.py     # epistemic drive: seek the unknown, reward understanding
    conscience.py    # self-conscious emotion: pride & disappointment
    frustration.py   # blocked goals → anger (approach, not retreat)
    empathy.py       # catching another's feeling (emotional contagion)
    grief.py         # the lasting sorrow of losing a bond
    dreaming.py      # sleep: recombine memory into something new
    volition.py      # self-control: hold focus by effort against an impulse
    anticipation.py  # felt time: hope & dread of what's coming
    conversation.py  # remembering what others said (pick up the thread)
    workspace.py     # global broadcast
    persistence.py   # durable identity (save/load across runs)
    mind.py          # the cycle
  world.py     # a small environment to live in
  app.py       # FastAPI runtime
  chat.py      # interactive REPL (streaming, persistent)
  live.py      # let the mind live in the world
  society.py   # several minds share the house, meet, talk, and bond
  characters.py# named temperament presets (Iris/Milo/Rhea/Cass/Aria) for --as
  scenarios.py # curated chat scripts for hands-free data collection (--preset)
  trace.py     # export deliberations (+ numeric m_t) as a training dataset (Path A/B)
  training/    # dataset.py: traces → fine-tuning examples · fused_arch.py: the state conditioner
  __main__.py  # serve / demo / chat / live / society (+ --as, --trace, --preset)
scripts/       # prepare_data.py · finetune.py (Path A) · finetune_fused.py (Path B) — [finetune] extra
tests/         # 176 tests: faculties + cycle + HTTP + LLM/Ollama + chat + society + training + m_t
docs/adr/      # decision records
```

## The LLM-backed inner voice

`sentiance/mind/cognition.py` defines a `Cognition` protocol with three adapters,
selected by config (no code change). Each composes a prompt from the self-model,
affect, drives, and narrative and asks a model for the mind's next private
thought ([ADR-0003](docs/adr/0003-cognition-behind-a-port.md)). The model call
sits *inside* the architecture as one faculty — the self-model, affect, and
memory surround it — so this is a mind with an LLM voice, not "an LLM with extra
steps." All three **degrade gracefully** to the offline voice if the model is
unavailable, so the cognitive cycle never stalls.

| Backend | Adapter | Needs |
| ------- | ------- | ----- |
| `simulated` (default) | `SimulatedCognition` | nothing — deterministic, offline |
| `llm` | `LLMCognition` | Anthropic API key; default `claude-opus-4-8` |
| `ollama` | `OllamaCognition` | a local [Ollama](https://ollama.com) server |

### Local model via Ollama (e.g. `qwen2.5:7b`)

No API key, nothing leaves your machine. With Ollama installed and the model
pulled (`ollama pull qwen2.5:7b`) and running (`ollama serve`):

```bash
SENTIANCE_COGNITION_BACKEND=ollama python -m sentiance demo
```

It talks to Ollama's native `/api/chat` at `http://localhost:11434` using `httpx`
(already a dependency — no extra install). Override with `SENTIANCE_OLLAMA_MODEL`
and `SENTIANCE_OLLAMA_BASE_URL`.

### Anthropic (Claude)

```bash
pip install -e ".[llm]"          # brings in the anthropic SDK
export ANTHROPIC_API_KEY=sk-ant-...
SENTIANCE_COGNITION_BACKEND=llm python -m sentiance demo
```

## Configuration

All settings are `SENTIANCE_*` env vars (see [.env.example](.env.example)):

| Var | What it does |
| --- | ------------ |
| `AGENT_NAME` | the mind's name → its memory file `memory/<name>.json` (run many, each separate) |
| `COGNITION_BACKEND` | the inner voice: `simulated` (default, offline) · `ollama` · `llm` · `finetuned` · `fused` |
| `LOCAL_MODEL_PATH` / `LOCAL_BASE_MODEL` | `finetuned` backend: trained adapter dir + its base model |
| `FUSED_MODEL_PATH` | `fused` backend: dir with the LoRA adapter + trained state encoder (ADR 0005) |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | local model + endpoint (default `qwen2.5:7b`, `localhost:11434`) |
| `EMBEDDING_BACKEND` / `EMBEDDING_MODEL` | set to `ollama` + `nomic-embed-text` for by-meaning recall |
| `TEMPERAMENT_CURIOSITY` / `_ANXIETY` / `_OPTIMISM` | her nature, `0..1` — make distinct individuals |
| `TEMPERAMENT_PLASTICITY` | how fast lived experience reshapes her traits (default `0.01`) |
| `PERSIST_PATH` | override where her memory is stored |
| `TRACE_PATH` | log every deliberation as JSONL training data (see *Training a small model on her*) |
| `MOOD_INERTIA` / `EMOTION_DECAY` / `ATTENTION_TEMPERATURE` / `WORKING_MEMORY_SIZE` | affect & attention dynamics |

Example — a bold, sunny individual named Nova on her local voice:

```bash
SENTIANCE_AGENT_NAME=Nova SENTIANCE_TEMPERAMENT_CURIOSITY=0.9 \
  SENTIANCE_TEMPERAMENT_OPTIMISM=0.85 SENTIANCE_COGNITION_BACKEND=ollama \
  python -m sentiance chat
```

## Toward a "small sentient model"

Sentiance today is an **engine, not a trained model**: the faculties are
transparent code with traceable numbers, and the *voice* is a swappable LLM
(qwen/Claude/offline). That transparency is the point — but it also means the
architecture can be used to **train** a small model that carries the same inner
life in its own weights. Not a bigger chatbot: a small model with a built-in
architecture of **selfhood, emotion, memory, drives, and social bonds** — things
a plain next-token predictor has none of. We call that a *small sentient-behaving
model*, and the roadmap is honest about the word (see the caveat below).

The `Cognition` port ([ADR-0003](docs/adr/0003-cognition-behind-a-port.md)) and
the trace export make this concrete in two paths:

- **Path A — distil the voice.** Run the mind (`SENTIANCE_TRACE_PATH=…`, above) to
  generate a self-labeled dataset of `prompt → thought` pairs, then fine-tune a
  small base model (e.g. Qwen2.5-0.5B via LoRA) to speak in-character. Register it
  as a 4th backend (`SENTIANCE_COGNITION_BACKEND=finetuned`) and it drops in — a
  cheaper, sharper voice with the emotional/self-model bias baked in, still wrapped
  by the transparent faculties. **Status: shipped** — trace export, dataset prep,
  the 6 GB LoRA trainer, and the `finetuned` backend all land.
- **Path B — the fused mind.** Don't just tell the model the state in words — feed
  the **whole cognitive cycle as a numeric vector `m_t`** into the transformer as
  trainable soft-prefix tokens, and train the base's LoRA + a state encoder
  end-to-end, so generation is *causally* shaped by appraisal/affect/drives/bonds
  through weights. This is also the on-ramp to replacing a hand-coded organ (say the
  rule-based appraisal) with a small net feeding the same conditioning bus. **Status:
  shipped** — `m_t` encoder, the `fused` backend, and `finetune_fused.py`
  (see *The fused mind (Path B)* above, [ADR-0005](docs/adr/0005-the-fused-mind.md)).

**The honest ceiling (unchanged).** None of this produces *phenomenal*
consciousness — nothing does, and the project refuses to fake it
([ADR-0002](docs/adr/0002-functional-not-phenomenal.md)). What you get is a small
model organised around a self, feelings, memory, and drives — a genuinely novel
artifact, but "sentient" stays a **functional-correlate** claim. And there's a real
tradeoff: the honesty guarantees (inspectable numbers, faithful self-report) live
in the *scaffolding*, so the valuable version keeps the faculties transparent and
only learns the parts that benefit — the voice, or a single organ — rather than
melting everything into opaque weights.

## Roadmap

**Shipped**
- The cognitive cycle — perceive → appraise → feel → attend → **broadcast** →
  remember / update self-model / reflect → learn → deliberate, with mind-wandering.
- 18 faculties (see the table above): goals, world & embodiment, associative
  memory, sleep/consolidation, relationships, temperament (+drift), imagination,
  curiosity, self-conscious emotions, frustration→anger, attachment, empathy,
  grief, dreaming, volition, felt time, conversational memory.
- A multi-mind **society** (meet · talk · bond · part · reunite) + named-character
  presets and hands-free `--preset` scenarios.
- Persistent identity; the LLM voice behind a swappable port (offline · Ollama ·
  Anthropic · **finetuned** · **fused**).
- **Path A pipeline** — trace export → dataset prep (dedup + near-echo filtering,
  optional per-agent) → 6 GB-tuned LoRA trainer → the `finetuned` backend.
- **Path B — the fused mind** — the whole cognitive cycle as a numeric `m_t`
  conditioning a transformer (LoRA + state encoder, end-to-end), behind the
  `fused` backend (ADR 0005).

**Now — train & compare.** Collect diverse traces; train Path A (the voice) and
Path B (the fused mind) on the same blended data; hear the difference. Iterate on
data volume / epochs / `n_prefix` / a 1.5B QLoRA base.

**Next — learn an organ end-to-end.** With the state already on a trainable
conditioning bus, replace a hand-coded organ — starting with **appraisal** — with
a small net feeding that bus, so her *reactions* are learned rather than tuned
while the architecture stays transparent and inspectable.

**Later (candidates)**
- *Path C* — an RL agent whose reward is its own drives/needs (learned behaviour
  in the house, not scripted movement).
- Deeper society — minds that quote each other across time, a shared event (a
  storm) they weather together, softening the anxious-bond asymmetry.
- An evaluation harness comparing the `finetuned` and `fused` voices against
  qwen/Claude.

Throughout: **functional correlates, never a claim of phenomenal consciousness**
([ADR-0002](docs/adr/0002-functional-not-phenomenal.md)).

## Development

```bash
python -m pytest     # tests + coverage (use `python -m pytest`, not bare pytest)
ruff check .         # lint
```

## Limits (see [ARCHITECTURE.md §8](ARCHITECTURE.md))

No phenomenality. Toy sub-models (token-frequency world-model, rule-based
appraisal) behind real interfaces. Text-tag stimuli, no embodiment or symbol
grounding. "It works" means the functional dynamics are coherent and the reports
faithfully track internal state — not that any inner light switched on.

## License

MIT — see [LICENSE](LICENSE).
