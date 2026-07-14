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
| Predictive processing (Friston/Clark) | world-model surprise |
| Higher-order theories (Rosenthal/Lau) | metacognitive self-report |

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Watch a mind's stream of consciousness through a short experience:
python -m sentiance demo

# Talk to it — type experiences and watch it feel, remember, and think:
python -m sentiance chat

# Or serve one living mind (docs at http://localhost:8000/docs):
python -m sentiance
```

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
the reflections come from your local model (e.g. `qwen2.5:7b`) and **stream in
word-by-word** as it thinks. Append `#tags` to hint appraisal (`#threat`,
`#friend`, `#reward`, …); `:idle N` to let it wander, `:self` to see its
self-model, `:save` to persist now, `:quit` to leave.

Emotions **carry over** — a frightening experience stays with the mind through
its next few thoughts, then eases. And the mind is **persistent**: chat saves to
`~/.sentiance/<name>.json` on exit and reloads it next run, so the same
individual continues across sessions rather than waking blank.

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
python -m pytest            # 43 tests; use `python -m pytest`, not bare pytest
python -m pytest -k chat    # just the REPL parsing + scripted-run tests
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
perceive → predict/surprise → appraise → feel → attend → BROADCAST
         → remember + update self-model + reflect → learn → deliberate
```

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
    memory.py        # working / episodic / semantic
    self_model.py    # attention schema / narrative identity
    metacognition.py # first-person self-report
    cognition.py     # Cognition port: Simulated (offline) + LLM (drop-in)
    workspace.py     # global broadcast
    persistence.py   # durable identity (save/load across runs)
    mind.py          # the cycle
  app.py       # FastAPI runtime
  chat.py      # interactive REPL (streaming, persistent)
  __main__.py  # serve / demo / chat
tests/         # faculties + cycle + HTTP + LLM/Ollama + chat + persistence (43 tests)
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
