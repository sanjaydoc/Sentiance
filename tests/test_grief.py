"""Grief & loss — the lasting sorrow that is the cost of having loved."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.grief import Grief, signals_loss
from sentiance.mind.state import Emotion, Stimulus


def _befriend(mind: Mind, name: str, times: int = 15) -> None:
    for _ in range(times):
        mind.perceive(Stimulus(content=f"@{name} holds me close, warm and kind",
                               intensity=0.7, tags=["friend", "warmth", "reward"]))


def test_loss_cues_are_recognized() -> None:
    assert signals_loss("@Kai is gone forever")
    assert signals_loss("@Kai has died")
    assert not signals_loss("@Kai is making tea")


def test_deeper_bonds_grieve_harder_and_longer() -> None:
    shallow = Grief()
    deep = Grief()
    shallow.bereave("A", attachment=0.2)
    deep.bereave("B", attachment=0.9)
    assert deep.step() < shallow.step()  # deeper attachment → sharper grief


def test_mourning_fades_over_time() -> None:
    g = Grief()
    g.bereave("Kai", attachment=0.8)
    first = g.step()
    for _ in range(60):
        g.step()
    assert not g.grieving  # the acute grief eventually settles
    assert first < -0.3


def test_losing_a_loved_one_brings_lasting_grief() -> None:
    mind = Mind(settings=Settings())
    _befriend(mind, "Kai")
    assert mind.relationships.known("Kai").attachment > 0.4

    mind.perceive(Stimulus(content="@Kai is gone forever, passed away", intensity=0.6))
    assert mind.grieving
    assert mind.affect.emotion is Emotion.GRIEF
    assert mind.relationships.known("Kai").lost is True

    # The sorrow lasts across many following moments (it doesn't vanish next tick).
    still_low = 0
    for _ in range(15):
        r = mind.idle()
        if r.moment.affect.valence < -0.1:
            still_low += 1
    assert still_low >= 10  # a persistent, background sadness


def test_she_grieves_the_lost_rather_than_awaiting_them() -> None:
    mind = Mind(settings=Settings())
    _befriend(mind, "Kai")
    mind.perceive(Stimulus(content="@Kai is gone forever", intensity=0.6))
    for _ in range(30):
        mind.idle()
    # She doesn't sit waiting for someone who won't return.
    assert mind.longing is None or mind.longing[0] != "Kai"


def test_grief_persists_across_a_reload(tmp_path) -> None:
    mind = Mind(settings=Settings())
    _befriend(mind, "Kai")
    mind.perceive(Stimulus(content="@Kai has died", intensity=0.6))
    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert reborn.grief.grieving  # she wakes still carrying the loss
    assert reborn.relationships.known("Kai").lost is True
