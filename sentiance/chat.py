"""An interactive REPL for talking to a single mind.

You type experiences; the mind perceives them, feels, remembers, and thinks out
loud (via whichever ``Cognition`` backend is configured — the local Ollama voice
when ``SENTIANCE_COGNITION_BACKEND=ollama``). After each experience the mind
takes a couple of idle ticks so you can watch it reflect.

Line grammar:
- plain text            → an experience; append ``#tag`` tokens to hint appraisal
                          (e.g. ``a loud crash #threat``, ``a friend waves #friend``)
- empty line           → let the mind wander one tick
- ``:idle N``          → let it wander N ticks
- ``:self``            → print its model of itself
- ``:help``            → show commands
- ``:quit`` / Ctrl-C   → leave
"""

from __future__ import annotations

import re
from pathlib import Path

from sentiance.core.config import Settings
from sentiance.mind import Mind, TickResult
from sentiance.mind.state import Stimulus

_TAG_RE = re.compile(r"#(\w+)")
_REFLECT_TICKS = 2  # idle ticks taken after each experience so the mind thinks

Parsed = tuple[str, object]


def parse_line(line: str) -> Parsed:
    """Turn a REPL line into a ``(command, arg)`` pair. Pure and testable."""
    text = line.strip()
    if not text:
        return ("idle", 1)
    if text in (":q", ":quit", ":exit"):
        return ("quit", None)
    if text in (":help", ":h", "?"):
        return ("help", None)
    if text == ":self":
        return ("self", None)
    if text == ":people":
        return ("people", None)
    if text == ":save":
        return ("save", None)
    if text == ":sleep":
        return ("sleep", None)
    if text.startswith(":idle"):
        rest = text[len(":idle"):].strip()
        n = int(rest) if rest.isdigit() else 3
        return ("idle", max(1, n))

    tags = _TAG_RE.findall(text)
    content = _TAG_RE.sub("", text)
    content = re.sub(r"\s+", " ", content).strip()
    return ("perceive", Stimulus(content=content, intensity=0.6, tags=tags))


_HELP = (
    "  <text>        an experience (add #tags: #threat #friend #reward ...)\n"
    "  <empty>       let the mind wander one tick\n"
    "  :idle N       let it wander N ticks\n"
    "  :self         its current model of itself\n"
    "  :people       who it knows (name people as @Sam in an experience)\n"
    "  :sleep        reflect: distil recent experience into durable beliefs\n"
    "  :save         write its memory to disk now\n"
    "  :help         this help\n"
    "  :quit         leave (saves automatically)"
)


def default_persist_path(settings: Settings) -> str:
    """Where this named mind's memory lives across runs — a ``memory/`` folder in
    the current working directory (i.e. alongside the project), so her state
    stays with the project rather than in your home directory."""
    if settings.persist_path:
        return settings.persist_path
    return str(Path("memory") / f"{settings.agent_name.lower()}.json")


def format_tick(result: TickResult) -> str:
    m, rep = result.moment, result.report
    head = (
        f"  t{m.tick:<3} [{m.affect.emotion.value:<11}] "
        f"v{m.affect.valence:+.2f} a{m.affect.arousal:.2f}  ·  {m.content}"
    )
    return f"{head}\n      ↳ {rep.text}  (confidence {rep.confidence:.2f})"


def _print_self(mind: Mind) -> None:
    s = mind.state()
    drives = ", ".join(f"{d.value}:{v:.2f}" for d, v in s.drives.items())
    print(f"  focus:     {s.current_focus}")
    print(f"  mood:      valence {s.affect.mood_valence:+.2f}, arousal {s.affect.mood_arousal:.2f}")
    print("  drives:    {" + drives + "}")
    n, t = mind.needs, mind.temperament
    print(f"  needs:     rest {n.rest:.2f}, stimulation {n.stimulation:.2f}, "
          f"connection {n.connection:.2f}")
    drift = t.drift_from_innate()
    print(f"  temperament: curiosity {t.curiosity:.2f}, anxiety {t.anxiety:.2f}, "
          f"optimism {t.optimism:.2f}")
    if any(abs(d) >= 0.02 for d in drift.values()):
        moved = ", ".join(f"{k} {v:+.2f}" for k, v in drift.items() if abs(v) >= 0.02)
        print(f"    (drifted from who she was: {moved})")
    if s.goals:
        print("  goals:     " + "; ".join(s.goals))
    if s.beliefs:
        print("  beliefs:   " + "; ".join(s.beliefs))
    print(f"  narrative: {s.narrative}")


def _announce_goals(mind: Mind) -> None:
    labels = {
        "formed": "new intention",
        "resolved": "intention resolved",
        "abandoned": "intention let go",
    }
    for event, goal in mind.last_goal_events:
        print(f"      ({labels[event]}: {goal.description})")


def _announce_curiosity(mind: Mind) -> None:
    if mind.last_curiosity is not None:
        _content, lift = mind.last_curiosity
        print(f"      (it clicks — I understand this now, +{lift:.2f})")


def _announce_self_judgment(mind: Mind) -> None:
    j = mind.last_self_judgment
    if j is not None:
        print(f"      ({j.emotion.value}: {j.reason})")
    if mind.last_anger:
        print("      (frustration boils over — she digs in rather than backing down)")


def _reflect(mind: Mind) -> None:
    """One reflection step: the mind thinks (streaming the thought live), then we
    show the feeling and report it evokes."""
    streamed = {"any": False}

    def emit(chunk: str) -> None:
        if not streamed["any"]:
            print("  ", end="", flush=True)  # indent before the first token
            streamed["any"] = True
        print(chunk, end="", flush=True)

    thought = mind.think(on_token=emit)
    if thought is None:  # calm/neutral — let the mind wander instead
        print(format_tick(mind.idle(deliberate=False)))
        _announce_goals(mind)
        _announce_curiosity(mind)
        _announce_self_judgment(mind)
        return
    if not streamed["any"]:  # backend didn't stream (e.g. simulated) — show it now
        print(f"  {thought.content}", end="")
    print()

    result = mind.perceive(thought, deliberate=False)
    a, rep = result.moment.affect, result.report
    print(f"      [{a.emotion.value} v{a.valence:+.2f} a{a.arousal:.2f}]  ↳ {rep.text}")
    _announce_goals(mind)
    _announce_curiosity(mind)
    _announce_self_judgment(mind)


def run_chat(mind: Mind | None = None, persist_path: str | None = None) -> None:
    # A mind we create persists to disk by default (durable identity across runs);
    # an injected mind (e.g. in tests) only persists if a path is given explicitly.
    owns_mind = mind is None
    mind = mind or Mind()
    name = mind.settings.agent_name
    path = persist_path or (default_persist_path(mind.settings) if owns_mind else None)

    print(f"— {name} is awake (cognition: {mind.settings.cognition_backend}) —")
    if path:
        recovered = mind.load(path)
        if recovered:
            print(f"  …{name} remembers {recovered} moments from before.")
    print("Type an experience, or :help. Ctrl-C to leave.\n")

    def _leave() -> None:
        if path:
            mind.save(path)
            print(f"— {name} sleeps, remembering ({path}) —")
        else:
            print(f"— {name} rests —")

    while True:
        try:
            line = input("you> ")
        except (EOFError, KeyboardInterrupt):
            print()
            _leave()
            return

        command, arg = parse_line(line)
        if command == "quit":
            _leave()
            return
        if command == "help":
            print(_HELP)
            continue
        if command == "save":
            if path:
                mind.save(path)
                print(f"  …saved to {path}")
            else:
                print("  (no persistence path set)")
            continue
        if command == "sleep":
            added = mind.sleep()
            if added:
                print(f"  …{name} sleeps and reflects. New beliefs:")
                for belief in added:
                    print(f"    • {belief}")
            else:
                print(f"  …{name} sleeps, but nothing new crystallizes yet.")
            continue
        if command == "people":
            lines = mind.relationships.summary()
            print("\n".join(f"  {line}" for line in lines) if lines else "  (no one known yet)")
            continue
        if command == "self":
            _print_self(mind)
            continue
        if command == "idle":
            for _ in range(int(arg)):  # type: ignore[arg-type]
                _reflect(mind)
            continue

        # An experience: perceive it, then let the mind reflect a couple of ticks.
        # deliberate=False — we drive deliberation ourselves in _reflect (to stream).
        assert isinstance(arg, Stimulus)
        print(format_tick(mind.perceive(arg, deliberate=False)))
        _announce_goals(mind)
        _announce_curiosity(mind)
        _announce_self_judgment(mind)
        for _ in range(_REFLECT_TICKS):
            _reflect(mind)
