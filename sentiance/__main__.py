"""``python -m sentiance`` — serve a mind, or watch its stream of consciousness.

- ``python -m sentiance``        → serve the mind on :8000 (docs at /docs)
- ``python -m sentiance demo``   → feed a short scripted experience and print the
                                    conscious moments + first-person reports
"""

from __future__ import annotations

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


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
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
