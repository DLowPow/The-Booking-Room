"""
Wrestler Mind Engine
Gives wrestlers ambition, frustration, loyalty, trust, and weekly thoughts.
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class WrestlerMind:
    wrestler_name: str
    ambition: int = 50
    ego: int = 50
    loyalty: int = 50
    patience: int = 50
    trust_in_player: int = 50
    frustration: int = 0
    morale_pressure: int = 0
    weeks_unbooked: int = 0
    poaching_risk: int = 0
    current_thoughts: List[str] = field(default_factory=list)

    def clamp(self):
        for attr in [
            "ambition", "ego", "loyalty", "patience", "trust_in_player",
            "frustration", "morale_pressure", "poaching_risk"
        ]:
            setattr(self, attr, max(0, min(100, getattr(self, attr))))

    def weekly_update(self, wrestler, was_booked=False):
        self.current_thoughts.clear()

        popularity = getattr(wrestler, "popularity", 50)

        if not was_booked:
            self.weeks_unbooked += 1
            frustration_gain = 3 + int(self.ambition / 25)
            self.frustration += frustration_gain
        else:
            self.weeks_unbooked = 0
            self.frustration -= 5
            self.trust_in_player += 2

        if self.weeks_unbooked >= 2 and self.ambition > 60:
            self.current_thoughts.append("I should be doing more than sitting around.")

        if self.frustration > 65:
            self.current_thoughts.append("Creative clearly has no plan for me.")

        if popularity > 70 and self.ego > 60 and self.weeks_unbooked > 0:
            self.current_thoughts.append("Someone with my name value should be featured.")

        self.poaching_risk = int(
            (self.frustration * 0.45) +
            ((100 - self.loyalty) * 0.30) +
            ((100 - self.trust_in_player) * 0.25)
        )

        self.clamp()

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(
            wrestler_name=data.get("wrestler_name", ""),
            ambition=data.get("ambition", random.randint(35, 85)),
            ego=data.get("ego", random.randint(25, 85)),
            loyalty=data.get("loyalty", random.randint(25, 85)),
            patience=data.get("patience", random.randint(25, 85)),
            trust_in_player=data.get("trust_in_player", 50),
            frustration=data.get("frustration", 0),
            morale_pressure=data.get("morale_pressure", 0),
            weeks_unbooked=data.get("weeks_unbooked", 0),
            poaching_risk=data.get("poaching_risk", 0),
            current_thoughts=data.get("current_thoughts", []),
        )


class WrestlerMindManager:
    def __init__(self):
        self.minds: Dict[str, WrestlerMind] = {}

    def ensure_mind(self, wrestler):
        name = getattr(wrestler, "name", "Unknown")
        if name not in self.minds:
            self.minds[name] = WrestlerMind(
                wrestler_name=name,
                ambition=random.randint(35, 90),
                ego=random.randint(20, 90),
                loyalty=random.randint(25, 90),
                patience=random.randint(25, 85),
            )
        return self.minds[name]

    def weekly_update(self, roster, booked_names=None):
        booked_names = booked_names or set()
        results = []

        for wrestler in roster:
            mind = self.ensure_mind(wrestler)
            was_booked = getattr(wrestler, "name", "") in booked_names
            mind.weekly_update(wrestler, was_booked=was_booked)

            if mind.current_thoughts:
                results.append({
                    "wrestler": mind.wrestler_name,
                    "thoughts": mind.current_thoughts,
                    "frustration": mind.frustration,
                    "poaching_risk": mind.poaching_risk,
                })

        return results

    def to_dict(self):
        return {"minds": {name: mind.to_dict() for name, mind in self.minds.items()}}

    @classmethod
    def from_dict(cls, data):
        manager = cls()
        for name, mind_data in data.get("minds", {}).items():
            manager.minds[name] = WrestlerMind.from_dict(mind_data)
        return manager