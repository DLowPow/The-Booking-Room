# ai/minds.py
"""
Minds — Unified wrestler psychology, long-term memory, and relationships.
Consolidates: wrestler_mind.py + memory_core.py + relationships.py

Adds the previously-missing module-level helpers:
    - record_memory(game_state, ...)
    - react_to_storyline(game_state, storyline)
so Writers Room storyline hooks actually do something.

Save-safe: all manager classes implement to_dict()/from_dict().
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


# ==========================================================================
# ============================  MEMORY CORE  ===============================
# ==========================================================================

@dataclass
class AIMemory:
    id: str
    week: int
    year: int
    memory_type: str
    subject: str
    description: str
    importance: int = 50
    emotional_weight: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            week=data.get("week", 0),
            year=data.get("year", 1),
            memory_type=data.get("memory_type", "general"),
            subject=data.get("subject", ""),
            description=data.get("description", ""),
            importance=data.get("importance", 50),
            emotional_weight=data.get("emotional_weight", 0),
            tags=data.get("tags", []),
        )


class MemoryCore:
    def __init__(self):
        self.memories: List[AIMemory] = []

    def remember(self, week, year, memory_type, subject, description,
                 importance=50, emotional_weight=0, tags=None):
        memory = AIMemory(
            id=str(uuid.uuid4()),
            week=week, year=year, memory_type=memory_type,
            subject=subject, description=description,
            importance=importance, emotional_weight=emotional_weight,
            tags=tags or [],
        )
        self.memories.append(memory)
        self.memories = self.memories[-300:]
        return memory

    def get_recent(self, limit=10):
        return self.memories[-limit:]

    def get_for_subject(self, subject, limit=10):
        results = [m for m in self.memories if m.subject == subject]
        return results[-limit:]

    def to_dict(self):
        return {"memories": [m.to_dict() for m in self.memories]}

    @classmethod
    def from_dict(cls, data):
        core = cls()
        for item in data.get("memories", []):
            core.memories.append(AIMemory.from_dict(item))
        return core


# ==========================================================================
# ===========================  WRESTLER MIND  ==============================
# ==========================================================================

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
    # NEW: creative satisfaction tracks how happy they are with their stories
    creative_satisfaction: int = 50
    current_thoughts: List[str] = field(default_factory=list)

    def clamp(self):
        for attr in [
            "ambition", "ego", "loyalty", "patience", "trust_in_player",
            "frustration", "morale_pressure", "poaching_risk",
            "creative_satisfaction",
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

    def react_to_storyline(self, storyline: dict):
        """
        NEW: A wrestler reacts to being booked in a storyline.
        Good heat raises satisfaction + trust; bad/cooling storylines hurt it.
        Returns a short thought string (or '').
        """
        heat = storyline.get("heat", 0) if isinstance(storyline, dict) else 0
        reaction = storyline.get("fan_reaction", "neutral") if isinstance(storyline, dict) else "neutral"

        if reaction in ("red_hot", "invested") or heat >= 60:
            self.creative_satisfaction += 6
            self.trust_in_player += 3
            self.frustration = max(0, self.frustration - 6)
            thought = "This story is making me. I'm finally getting somewhere."
        elif reaction in ("cooling", "rejected") or heat < 25:
            self.creative_satisfaction -= 5
            self.frustration += 4
            thought = "This story is doing nothing for me."
        else:
            self.creative_satisfaction += 1
            thought = ""

        self.clamp()
        if thought:
            self.current_thoughts.append(thought)
        return thought

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
            creative_satisfaction=data.get("creative_satisfaction", 50),
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

    def get_mind_by_name(self, name):
        return self.minds.get(name)

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
                    "creative_satisfaction": mind.creative_satisfaction,
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


# ==========================================================================
# ===========================  RELATIONSHIPS  ==============================
# ==========================================================================

class RelationshipType(Enum):
    FRIEND = "Friend"
    BEST_FRIEND = "Best Friend"
    RIVAL = "Rival"
    ENEMY = "Enemy"
    MENTOR = "Mentor"
    PROTEGE = "Protege"
    TAG_PARTNER = "Tag Partner"
    FACTION_MATE = "Faction Mate"
    EX_TAG_PARTNER = "Ex-Tag Partner"
    EX_FACTION = "Ex-Faction"
    ROMANTIC = "Romantic"
    EX_ROMANTIC = "Ex-Romantic"
    FAMILY = "Family"
    NEUTRAL = "Neutral"


class RelationshipStatus(Enum):
    ACTIVE = "Active"
    DECLINING = "Declining"
    STRAINED = "Strained"
    BROKEN = "Broken"


@dataclass
class Relationship:
    wrestler1: str
    wrestler2: str
    relationship_type: RelationshipType
    intensity: int = 50
    duration_weeks: int = 0
    origin: str = ""
    is_public: bool = False
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    notable_events: List[str] = field(default_factory=list)

    def get_intensity_color(self) -> str:
        if self.intensity >= 80: return "#dc2626"
        if self.intensity >= 60: return "#f59e0b"
        if self.intensity >= 40: return "#3b82f6"
        if self.intensity >= 20: return "#6b7280"
        return "#4b5563"

    def get_type_color(self) -> str:
        colors = {
            RelationshipType.FRIEND: "#3b82f6", RelationshipType.BEST_FRIEND: "#10b981",
            RelationshipType.RIVAL: "#f59e0b", RelationshipType.ENEMY: "#dc2626",
            RelationshipType.MENTOR: "#8b5cf6", RelationshipType.PROTEGE: "#a78bfa",
            RelationshipType.TAG_PARTNER: "#10b981", RelationshipType.FACTION_MATE: "#06b6d4",
            RelationshipType.EX_TAG_PARTNER: "#6b7280", RelationshipType.EX_FACTION: "#6b7280",
            RelationshipType.ROMANTIC: "#ec4899", RelationshipType.EX_ROMANTIC: "#9d174d",
            RelationshipType.FAMILY: "#fbbf24", RelationshipType.NEUTRAL: "#9ca3af",
        }
        return colors.get(self.relationship_type, "#9ca3af")

    def get_type_icon(self) -> str:
        icons = {
            RelationshipType.FRIEND: "🤝", RelationshipType.BEST_FRIEND: "💛",
            RelationshipType.RIVAL: "⚔️", RelationshipType.ENEMY: "💢",
            RelationshipType.MENTOR: "🎓", RelationshipType.PROTEGE: "📚",
            RelationshipType.TAG_PARTNER: "🤜🤛", RelationshipType.FACTION_MATE: "👥",
            RelationshipType.EX_TAG_PARTNER: "💔", RelationshipType.EX_FACTION: "🚪",
            RelationshipType.ROMANTIC: "💕", RelationshipType.EX_ROMANTIC: "💔",
            RelationshipType.FAMILY: "👨‍👩‍👧", RelationshipType.NEUTRAL: "—",
        }
        return icons.get(self.relationship_type, "—")

    def add_notable_event(self, event: str):
        self.notable_events.append(event)
        if len(self.notable_events) > 20:
            self.notable_events = self.notable_events[-20:]

    def to_dict(self) -> dict:
        return {
            "wrestler1": self.wrestler1, "wrestler2": self.wrestler2,
            "relationship_type": self.relationship_type.value,
            "intensity": self.intensity, "duration_weeks": self.duration_weeks,
            "origin": self.origin, "is_public": self.is_public,
            "status": self.status.value, "notable_events": self.notable_events,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        try:
            rt = RelationshipType(data["relationship_type"])
        except (ValueError, KeyError):
            rt = RelationshipType.NEUTRAL
        try:
            status = RelationshipStatus(data.get("status", "Active"))
        except ValueError:
            status = RelationshipStatus.ACTIVE
        return cls(
            wrestler1=data["wrestler1"], wrestler2=data["wrestler2"],
            relationship_type=rt, intensity=data.get("intensity", 50),
            duration_weeks=data.get("duration_weeks", 0),
            origin=data.get("origin", ""), is_public=data.get("is_public", False),
            status=status, notable_events=data.get("notable_events", []),
        )


class RelationshipManager:
    def __init__(self):
        self.relationships: List[Relationship] = []

    def add_relationship(self, wrestler1, wrestler2, relationship_type,
                         intensity=50, origin="", is_public=False) -> Relationship:
        existing = self.get_relationship(wrestler1, wrestler2)
        if existing:
            try:
                existing.relationship_type = RelationshipType(relationship_type)
            except ValueError:
                existing.relationship_type = RelationshipType.NEUTRAL
            existing.intensity = intensity
            existing.origin = origin
            existing.is_public = is_public
            return existing
        try:
            rt = RelationshipType(relationship_type)
        except ValueError:
            rt = RelationshipType.NEUTRAL
        rel = Relationship(wrestler1=wrestler1, wrestler2=wrestler2,
                           relationship_type=rt, intensity=intensity,
                           origin=origin, is_public=is_public)
        self.relationships.append(rel)
        return rel

    def remove_relationship(self, wrestler1, wrestler2) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel:
            self.relationships.remove(rel)
            return True
        return False

    def get_relationship(self, wrestler1, wrestler2) -> Optional[Relationship]:
        for rel in self.relationships:
            if (rel.wrestler1 == wrestler1 and rel.wrestler2 == wrestler2) or \
               (rel.wrestler1 == wrestler2 and rel.wrestler2 == wrestler1):
                return rel
        return None

    def get_wrestler_relationships(self, wrestler_name) -> List[Relationship]:
        return [r for r in self.relationships
                if r.wrestler1 == wrestler_name or r.wrestler2 == wrestler_name]

    def get_other_wrestler(self, rel, wrestler_name) -> str:
        return rel.wrestler2 if rel.wrestler1 == wrestler_name else rel.wrestler1

    def get_friends(self, wrestler_name) -> List[str]:
        out = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type in (RelationshipType.FRIEND, RelationshipType.BEST_FRIEND):
                out.append(self.get_other_wrestler(rel, wrestler_name))
        return out

    def get_enemies(self, wrestler_name) -> List[str]:
        out = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type in (RelationshipType.ENEMY, RelationshipType.RIVAL):
                out.append(self.get_other_wrestler(rel, wrestler_name))
        return out

    def get_tag_partners(self, wrestler_name) -> List[str]:
        return [self.get_other_wrestler(r, wrestler_name)
                for r in self.get_wrestler_relationships(wrestler_name)
                if r.relationship_type == RelationshipType.TAG_PARTNER]

    def get_faction_mates(self, wrestler_name) -> List[str]:
        return [self.get_other_wrestler(r, wrestler_name)
                for r in self.get_wrestler_relationships(wrestler_name)
                if r.relationship_type == RelationshipType.FACTION_MATE]

    def are_friends(self, w1, w2) -> bool:
        rel = self.get_relationship(w1, w2)
        return rel is not None and rel.relationship_type in (
            RelationshipType.FRIEND, RelationshipType.BEST_FRIEND)

    def are_enemies(self, w1, w2) -> bool:
        rel = self.get_relationship(w1, w2)
        return rel is not None and rel.relationship_type in (
            RelationshipType.ENEMY, RelationshipType.RIVAL)

    def are_tag_partners(self, w1, w2) -> bool:
        rel = self.get_relationship(w1, w2)
        return rel is not None and rel.relationship_type == RelationshipType.TAG_PARTNER

    def intensify_rivalry(self, w1, w2, amount=10):
        rel = self.get_relationship(w1, w2)
        if rel and rel.relationship_type in (RelationshipType.RIVAL, RelationshipType.ENEMY):
            rel.intensity = min(100, rel.intensity + amount)
        elif not rel:
            self.add_relationship(w1, w2, "Rival", amount)

    def strengthen_friendship(self, w1, w2, amount=5):
        rel = self.get_relationship(w1, w2)
        if rel and rel.relationship_type in (RelationshipType.FRIEND, RelationshipType.BEST_FRIEND):
            rel.intensity = min(100, rel.intensity + amount)
            if rel.intensity >= 85 and rel.relationship_type == RelationshipType.FRIEND:
                rel.relationship_type = RelationshipType.BEST_FRIEND
        elif not rel:
            self.add_relationship(w1, w2, "Friend", 50 + amount)

    def weekly_decay(self) -> List[Dict]:
        changes = []
        for rel in self.relationships[:]:
            rel.duration_weeks += 1
            if rel.relationship_type in (RelationshipType.RIVAL, RelationshipType.ENEMY):
                if rel.intensity > 20:
                    rel.intensity -= 2
            elif rel.relationship_type in (RelationshipType.FRIEND, RelationshipType.BEST_FRIEND):
                if rel.duration_weeks > 52 and rel.intensity > 30:
                    rel.intensity -= 1
            elif rel.relationship_type == RelationshipType.TAG_PARTNER:
                if rel.intensity < 90 and rel.duration_weeks % 4 == 0:
                    rel.intensity = min(90, rel.intensity + 1)
            elif rel.relationship_type == RelationshipType.ROMANTIC:
                rel.intensity = max(0, min(100, rel.intensity + random.choice([-2, -1, 0, 0, 1, 2])))

            if rel.intensity >= 40:
                rel.status = RelationshipStatus.ACTIVE
            elif rel.intensity >= 20:
                rel.status = RelationshipStatus.DECLINING
            elif rel.intensity > 0:
                rel.status = RelationshipStatus.STRAINED
            else:
                rel.status = RelationshipStatus.BROKEN

            if rel.intensity <= 0:
                self.relationships.remove(rel)
                changes.append({
                    "wrestlers": [rel.wrestler1, rel.wrestler2],
                    "change": "relationship_ended",
                    "message": f"The {rel.relationship_type.value.lower()} between "
                               f"{rel.wrestler1} and {rel.wrestler2} has ended.",
                })
        return changes

    def form_tag_team(self, w1, w2, team_name=""):
        rel = self.add_relationship(w1, w2, "Tag Partner", intensity=75,
                                    origin=f"Formed tag team: {team_name}" if team_name else "Formed tag team",
                                    is_public=True)
        if team_name:
            rel.add_notable_event(f"Formed tag team '{team_name}'")

    def break_up_tag_team(self, w1, w2, turn_enemies=False):
        rel = self.get_relationship(w1, w2)
        if rel and rel.relationship_type == RelationshipType.TAG_PARTNER:
            if turn_enemies:
                rel.relationship_type = RelationshipType.RIVAL
                rel.intensity = 70
                rel.add_notable_event("Tag team broke up — became enemies")
                rel.is_public = True
            else:
                rel.relationship_type = RelationshipType.EX_TAG_PARTNER
                rel.intensity = 30
                rel.add_notable_event("Tag team amicably split")

    def suggest_storyline_pairs(self, min_intensity=50) -> List[Dict]:
        suggestions = []
        type_map = {
            RelationshipType.RIVAL: ("Personal Rivalry", "Existing rivalry — storyline writes itself."),
            RelationshipType.ENEMY: ("Grudge Match", "Deep hatred — perfect for a grudge."),
            RelationshipType.TAG_PARTNER: ("Betrayal", "Strong tag bond — set up a shocking betrayal."),
            RelationshipType.BEST_FRIEND: ("Betrayal", "Best friends — betrayal would be devastating."),
            RelationshipType.MENTOR: ("Mentor vs Student", "Passing of the torch."),
            RelationshipType.PROTEGE: ("Mentor vs Student", "Student wants to surpass their teacher."),
            RelationshipType.EX_TAG_PARTNER: ("Personal Rivalry", "Former partners — unfinished business."),
            RelationshipType.EX_FACTION: ("Grudge Match", "Former faction member — bad blood remains."),
            RelationshipType.FAMILY: ("Legacy", "Family ties — legacy potential."),
            RelationshipType.FACTION_MATE: ("Faction War", "Set up internal conflict."),
            RelationshipType.ROMANTIC: ("Love Triangle", "Perfect for triangle drama."),
            RelationshipType.EX_ROMANTIC: ("Personal Rivalry", "Past romance — fuel for a feud."),
        }
        for rel in self.relationships:
            if rel.intensity < min_intensity:
                continue
            mapping = type_map.get(rel.relationship_type)
            if not mapping:
                continue
            suggestions.append({
                "wrestler1": rel.wrestler1, "wrestler2": rel.wrestler2,
                "relationship_type": rel.relationship_type.value,
                "intensity": rel.intensity, "is_public": rel.is_public,
                "duration_weeks": rel.duration_weeks,
                "suggested_storyline": mapping[0], "reasoning": mapping[1],
            })
        suggestions.sort(key=lambda s: -s["intensity"])
        return suggestions

    def get_chemistry_modifier(self, w1, w2) -> float:
        rel = self.get_relationship(w1, w2)
        if not rel:
            return 1.0
        modifiers = {
            RelationshipType.FRIEND: 1.10, RelationshipType.BEST_FRIEND: 1.15,
            RelationshipType.TAG_PARTNER: 1.20, RelationshipType.FACTION_MATE: 1.10,
            RelationshipType.MENTOR: 1.12, RelationshipType.PROTEGE: 1.12,
            RelationshipType.RIVAL: 1.25, RelationshipType.ENEMY: 1.20,
            RelationshipType.EX_TAG_PARTNER: 1.15, RelationshipType.EX_FACTION: 1.10,
            RelationshipType.FAMILY: 1.10, RelationshipType.ROMANTIC: 1.05,
            RelationshipType.EX_ROMANTIC: 1.18, RelationshipType.NEUTRAL: 1.0,
        }
        base = modifiers.get(rel.relationship_type, 1.0)
        return base + (rel.intensity - 50) / 200

    def get_relationship_count(self) -> int:
        return len(self.relationships)

    def get_hottest_rivalries(self, limit=10) -> List[Relationship]:
        rivalries = [r for r in self.relationships
                     if r.relationship_type in (RelationshipType.RIVAL, RelationshipType.ENEMY)]
        rivalries.sort(key=lambda r: -r.intensity)
        return rivalries[:limit]

    def to_dict(self) -> dict:
        return {"relationships": [rel.to_dict() for rel in self.relationships]}

    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipManager":
        manager = cls()
        for rel_data in data.get("relationships", []):
            try:
                manager.relationships.append(Relationship.from_dict(rel_data))
            except Exception:
                pass
        return manager


# ==========================================================================
# =====================  MODULE-LEVEL HOOK FUNCTIONS  ======================
# These are what writers_room/storytelling call. Previously missing = dead.
# ==========================================================================

def record_memory(game_state, wrestler="", event="", detail="", week=0, year=1,
                  importance=55, tags=None):
    """Save-safe memory writer. Creates MemoryCore on game_state if needed."""
    core = getattr(game_state, "ai_memory", None)
    if core is None:
        core = MemoryCore()
        game_state.ai_memory = core
    try:
        core.remember(
            week=week, year=year, memory_type=event or "storyline",
            subject=wrestler, description=f"{event}: {detail}".strip(": "),
            importance=importance, emotional_weight=importance,
            tags=tags or ["storyline"],
        )
    except Exception:
        pass


def react_to_storyline(game_state, storyline):
    """
    Each participant's WrestlerMind reacts to the storyline's current state.
    Save-safe; creates the mind manager if missing.
    """
    mgr = getattr(game_state, "wrestler_minds", None)
    if mgr is None:
        mgr = WrestlerMindManager()
        game_state.wrestler_minds = mgr

    participants = []
    if isinstance(storyline, dict):
        participants = storyline.get("participants", storyline.get("wrestlers", []))

    for name in participants:
        mind = mgr.minds.get(name)
        if mind is None:
            # Create a bare mind keyed by name (no wrestler object needed)
            mind = WrestlerMind(wrestler_name=name)
            mgr.minds[name] = mind
        try:
            mind.react_to_storyline(storyline)
        except Exception:
            pass