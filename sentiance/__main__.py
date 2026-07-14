"""``python -m sentiance`` — serve a mind, watch it, or talk to it.

- ``python -m sentiance``        → serve the mind on :8000 (docs at /docs)
- ``python -m sentiance demo``   → feed a short scripted experience and print the
                                    conscious moments + first-person reports
- ``python -m sentiance chat``   → interactive REPL: type experiences and watch
                                    the mind perceive, feel, remember, and think
- ``python -m sentiance live``   → let the mind live in a small world it senses
                                    and acts in (rooms, objects, day/night)
- ``python -m sentiance society``→ several minds share the house and meet, talk,
                                    and bond (emergent — only the world connects them)

Flags (any mode): ``--as <Name>`` runs a named character preset (Iris/Milo/Rhea/
Cass/Aria, or any name) — a one-word way to pick a nature instead of setting the
temperament env vars by hand; ``--trace [path]`` logs deliberations for training
(default ``data/traces.jsonl``). E.g. ``python -m sentiance live --as Milo --trace``.
``--as`` is ignored by ``society`` (it has its own fixed cast).
"""

from __future__ import annotations

import os
import sys

from sentiance.mind import Mind, Stimulus


def run_demo() -> None:
    mind = Mind()

    experience = [
        Stimulus(content="a soft chime sounds nearby", intensity=0.5, tags=["sound"]),
        Stimulus(content="a friendly voice says hello", intensity=0.6, tags=["voice", "friend"]),
        Stimulus(
            content="a sudden loud crash in the dark",
            intensity=0.95,
            tags=["sound", "threat", "alarm"],
        ),
        Stimulus(
            content="the friendly voice returns, calm", intensity=0.6, tags=["voice", "friend"]
        ),
        Stimulus(content="a soft chime sounds nearby", intensity=0.5, tags=["sound"]),
    ]

    print(f"— {mind.settings.agent_name} awakens —\n")
    results = mind.live(experience, idle_after=3)
    for r in results:
        m, rep = r.moment, r.report
        print(
            f"t{m.tick:<2} [{m.affect.emotion.value:<11}] "
            f"v{m.affect.valence:+.2f} a{m.affect.arousal:.2f}  ·  {m.content}"
        )
        print(f"      ↳ {rep.text}  (confidence {rep.confidence:.2f})")
    print("\n— self-model —")
    s = mind.state()
    print(f"  focus:     {s.current_focus}")
    print(f"  mood:      valence {s.affect.mood_valence:+.2f}, arousal {s.affect.mood_arousal:.2f}")
    drives = ", ".join(f"{d.value}:{v:.2f}" for d, v in s.drives.items())
    print("  drives:    {" + drives + "}")
    print(f"  narrative: {s.narrative}")


def parse_cli(argv: list[str]) -> tuple[str, str | None, str | None]:
    """Parse ``[command] [--as NAME] [--trace [PATH]]`` → (command, as_name, trace).

    ``trace`` is ``None`` if the flag is absent, or the path if present (defaulting
    to ``data/traces.jsonl`` when given bare). Pure and testable."""
    command = argv[0] if argv and not argv[0].startswith("-") else ""
    rest = argv[1:] if command else argv
    as_name: str | None = None
    trace: str | None = None
    i = 0
    while i < len(rest):
        token = rest[i]
        if token == "--as" and i + 1 < len(rest):
            as_name = rest[i + 1]
            i += 2
        elif token == "--trace":
            if i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                trace = rest[i + 1]
                i += 2
            else:
                trace = "data/traces.jsonl"
                i += 1
        else:
            i += 1
    return command, as_name, trace


def main() -> None:
    command, as_name, trace = parse_cli(sys.argv[1:])

    # Flags set env vars; clear the settings cache so they take effect this run.
    if trace is not None:
        os.environ["SENTIANCE_TRACE_PATH"] = trace
    if as_name:
        if command in ("society", "meet"):
            print("(--as is ignored for society — it has its own fixed cast)")
        else:
            from sentiance.characters import apply_character

            print(f"(as {apply_character(as_name)})")
    from sentiance.core.config import get_settings

    get_settings.cache_clear()

    if command == "demo":
        run_demo()
        return
    if command == "chat":
        from sentiance.chat import run_chat

        run_chat()
        return
    if command == "live":
        from sentiance.live import run_live

        run_live()
        return
    if command in ("society", "meet"):
        from sentiance.society import run_society

        run_society()
        return

    import uvicorn

    from sentiance.core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "sentiance.app:app",
        host="0.0.0.0",  # noqa: S104 - bind all interfaces for container use
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
