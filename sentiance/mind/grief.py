"""Grief & loss — the lasting sorrow of losing someone she was bonded to.

Longing is for someone who might still return; **grief** is for someone who
won't. When a loved one is marked gone, the bond doesn't simply vanish — it turns
to mourning: a sadness that is *deep in proportion to the attachment* and *lasting*
(it fades over many moments, not one), pulling down not just the passing feeling
but the slow background mood. The memory of them remains after the acute grief
settles — the bittersweet residue of having loved.

A functional correlate of grief as the counterpart of attachment (Bowlby); no
claim the sorrow is felt.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sentiance.mind.util import clamp

# Strong cues that a person is gone for good.
_LOSS_CUES = frozenset(
    {
        "gone", "died", "die", "dies", "dead", "death", "dying", "goodbye",
        "farewell", "passed", "perished", "buried", "forever", "lost",
    }
)


def signals_loss(text: str) -> bool:
    """Does this moment announce that someone is gone for good?"""
    words = {w.strip(".,!?;:'\"").lower() for w in text.split()}
    return bool(words & _LOSS_CUES)


@dataclass
class Loss:
    name: str
    weight: float  # how deep the bond was — how much there is to mourn
    intensity: float  # the acute grief right now, which fades over time


@dataclass
class Grief:
    losses: list[Loss] = field(default_factory=list)
    fade: float = 0.02  # mourning settles slowly

    def bereave(self, name: str, attachment: float) -> Loss:
        """Mark a loss and begin mourning it, as deeply as the bond was strong."""
        loss = Loss(
            name=name,
            weight=clamp(attachment),
            intensity=clamp(0.3 + 0.7 * attachment),
        )
        self.losses.append(loss)
        return loss

    def step(self) -> float:
        """Advance mourning one moment. Returns the sadness pull (<= 0) it presses
        on her feeling now; lets long-settled grief go (the memory stays elsewhere)."""
        total = sum(loss.intensity for loss in self.losses)
        for loss in self.losses:
            loss.intensity = clamp(loss.intensity - self.fade)
        self.losses = [loss for loss in self.losses if loss.intensity > 0.02]
        return -clamp(total)

    @property
    def grieving(self) -> bool:
        return any(loss.intensity > 0.05 for loss in self.losses)

    def mourning_for(self) -> list[str]:
        return [loss.name for loss in self.losses if loss.intensity > 0.05]

    def dump(self) -> dict:
        return {"losses": [{"name": lo.name, "weight": lo.weight,
                            "intensity": lo.intensity} for lo in self.losses]}

    def load(self, data: dict) -> None:
        self.losses = [
            Loss(name=lo["name"], weight=float(lo["weight"]), intensity=float(lo["intensity"]))
            for lo in data.get("losses", [])
        ]
