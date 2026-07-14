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
python -m sentiance demo    # watch a scripted stream of consciousness
python -m sentiance chat    # talk to her: type experiences, she feels/remembers/thinks
python -m sentiance live    # let her live in a small world she senses and acts in
python -m sentiance         # serve one mind (HTTP; docs at http://localhost:8000/docs)
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
python -m pytest            # 135 tests; use `python -m pytest`, not bare pytest
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
@Mara holds my hand warmly #friend #warmth        (repeat ~10× — a bond forms)
:people                                            (see her attachment to Mara grow)
@Mara is gone forever                              (she begins to grieve)
:idle 5                                            (the sorrow lingers across ticks)
```

Or **hope / dread of the future**, then **dreaming**:

```text
a warm reunion with friends is coming tomorrow #reward
:idle 4                                            (hope brightens the wait)
a fierce storm will come tonight #threat
:idle 6                                            (dread deepens as it nears)
:sleep                                             (she dreams — memory recombined)
```

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
    cognition.py     # Cognition port: Simulated / LLM (Anthropic) / Ollama
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
    workspace.py     # global broadcast
    persistence.py   # durable identity (save/load across runs)
    mind.py          # the cycle
  world.py     # a small environment to live in
  app.py       # FastAPI runtime
  chat.py      # interactive REPL (streaming, persistent)
  live.py      # let the mind live in the world
  __main__.py  # serve / demo / chat / live
tests/         # 135 tests: every faculty + full cycle + HTTP + LLM/Ollama + chat
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

`SENTIANCE_*` env vars (see [.env.example](.env.example)): `AGENT_NAME`,
`MOOD_INERTIA`, `EMOTION_DECAY`, `ATTENTION_TEMPERATURE`, `WORKING_MEMORY_SIZE`,
`COGNITION_BACKEND`.

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
