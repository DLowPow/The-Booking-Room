# ai/storytelling.py
"""
Storytelling — Unified storyline engine + Writers Room 2.0 pitch layer.
Consolidates: storyline_engine.py + writers_room.py

Two layers:
  1. StorylineEngine  — the deep feud/heat system (Storyline objects)
  2. Writers Room 2.0 — the dict-based pitch flow used by the app routes

Memory/mind hooks now import from ai.minds (was ai.memory_core / ai.wrestler_mind).
"""

import random
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Safe hooks into the merged minds module
try:
    from ai.minds import react_to_storyline as _mind_react
except Exception:
    _mind_react = None

try:
    from ai.minds import record_memory as _record_memory
except Exception:
    _record_memory = None


# ==========================================================================
# ========================  STORYLINE ENGINE  =============================
# ==========================================================================

class StorylineType(Enum):
    RIVALRY = "Personal Rivalry"
    TITLE_CHASE = "Title Chase"
    BETRAYAL = "Betrayal"
    MENTOR_STUDENT = "Mentor vs Student"
    FACTION_WAR = "Faction War"
    GRUDGE = "Grudge Match"
    INVASION = "Invasion Storyline"
    UNDERDOG = "Underdog Story"
    LOVE_TRIANGLE = "Love Triangle"
    AUTHORITY = "Authority vs Talent"
    REDEMPTION = "Redemption Arc"
    HEEL_TURN = "Heel Turn"
    FACE_TURN = "Face Turn"
    TOURNAMENT = "Tournament Run"
    LEGACY = "Legacy vs New Era"


class StorylineStage(Enum):
    PITCHED = "Pitched"
    BUILDING = "Building"
    HEATING_UP = "Heating Up"
    PEAK = "Peak Heat"
    BLOW_OFF = "Blow-Off"
    COOLED = "Cooled Down"
    CONCLUDED = "Concluded"


class StorylineIntensity(Enum):
    OPENER = "Opener"
    MID_CARD = "Mid-Card"
    UPPER_MID = "Upper Mid-Card"
    MAIN_EVENT = "Main Event"
    PERSONAL = "Deeply Personal"


class ResolutionType(Enum):
    CLEAN_WIN = "Clean Win"
    DIRTY_WIN = "Dirty Win"
    SCREWJOB = "Screwjob Finish"
    DOUBLE_TURN = "Double Turn"
    NO_CONTEST = "No Contest"
    DRAW = "Draw"
    RECONCILIATION = "Reconciliation"
    TITLE_CHANGE = "Title Change"
    RETIREMENT = "Retirement"
    INJURY_END = "Injury Ends Feud"


STORYLINE_TEMPLATES = {
    StorylineType.RIVALRY: {
        "description": "Two wrestlers with personal beef. Classic feud structure.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 4, "heat_per_match": 15, "ideal_weeks": 8, "icon": "⚔️",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
    StorylineType.TITLE_CHASE: {
        "description": "Challenger pursues a championship over multiple weeks.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 3, "heat_per_match": 20, "ideal_weeks": 6, "icon": "🏆",
        "personality_fit": ["Traditionalist", "Mastermind"],
    },
    StorylineType.BETRAYAL: {
        "description": "Former friend or partner turns on the protagonist.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 5, "heat_per_match": 18, "ideal_weeks": 10, "icon": "🗡️",
        "personality_fit": ["Showman", "Mad Scientist"],
    },
    StorylineType.MENTOR_STUDENT: {
        "description": "Trainer and protégé face off in passing-the-torch story.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 3, "heat_per_match": 12, "ideal_weeks": 6, "icon": "🎓",
        "personality_fit": ["Traditionalist"],
    },
    StorylineType.FACTION_WAR: {
        "description": "Two stables battle for supremacy.",
        "min_participants": 4, "max_participants": 12,
        "ideal_matches": 6, "heat_per_match": 14, "ideal_weeks": 12, "icon": "⚔️",
        "personality_fit": ["Mastermind", "Mad Scientist"],
    },
    StorylineType.GRUDGE: {
        "description": "Short, intense feud with definitive blow-off.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 2, "heat_per_match": 25, "ideal_weeks": 4, "icon": "💢",
        "personality_fit": ["Showman", "Mad Scientist"],
    },
    StorylineType.INVASION: {
        "description": "Outside force disrupts your promotion.",
        "min_participants": 4, "max_participants": 10,
        "ideal_matches": 5, "heat_per_match": 16, "ideal_weeks": 10, "icon": "🚨",
        "personality_fit": ["Mastermind", "Showman"],
    },
    StorylineType.UNDERDOG: {
        "description": "Lower-card wrestler chases bigger star.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 4, "heat_per_match": 13, "ideal_weeks": 8, "icon": "🌟",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
    StorylineType.LOVE_TRIANGLE: {
        "description": "Romantic complication causing in-ring drama.",
        "min_participants": 3, "max_participants": 4,
        "ideal_matches": 3, "heat_per_match": 11, "ideal_weeks": 8, "icon": "💔",
        "personality_fit": ["Showman"],
    },
    StorylineType.AUTHORITY: {
        "description": "Wrestler vs management. Power struggle.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 4, "heat_per_match": 17, "ideal_weeks": 10, "icon": "👔",
        "personality_fit": ["Showman", "Mastermind"],
    },
    StorylineType.REDEMPTION: {
        "description": "Fallen star fights back to the top.",
        "min_participants": 2, "max_participants": 3,
        "ideal_matches": 5, "heat_per_match": 14, "ideal_weeks": 10, "icon": "🔥",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
    StorylineType.HEEL_TURN: {
        "description": "Beloved face turns evil. Shock storyline.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 2, "heat_per_match": 22, "ideal_weeks": 4, "icon": "😈",
        "personality_fit": ["Showman", "Mad Scientist"],
    },
    StorylineType.FACE_TURN: {
        "description": "Hated heel becomes a hero. Crowd-pleaser.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 2, "heat_per_match": 22, "ideal_weeks": 4, "icon": "😇",
        "personality_fit": ["Traditionalist", "Mastermind"],
    },
    StorylineType.TOURNAMENT: {
        "description": "Tournament-based storyline with bracket progression.",
        "min_participants": 4, "max_participants": 16,
        "ideal_matches": 7, "heat_per_match": 12, "ideal_weeks": 8, "icon": "🏅",
        "personality_fit": ["Traditionalist"],
    },
    StorylineType.LEGACY: {
        "description": "Established star vs rising newcomer.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 3, "heat_per_match": 16, "ideal_weeks": 6, "icon": "👑",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
}

INTENSITY_MULTIPLIERS = {
    StorylineIntensity.OPENER: {"heat": 0.5, "rating_bonus": 0.05, "fan_bonus": 0.3},
    StorylineIntensity.MID_CARD: {"heat": 0.7, "rating_bonus": 0.1, "fan_bonus": 0.5},
    StorylineIntensity.UPPER_MID: {"heat": 1.0, "rating_bonus": 0.2, "fan_bonus": 1.0},
    StorylineIntensity.MAIN_EVENT: {"heat": 1.3, "rating_bonus": 0.4, "fan_bonus": 1.5},
    StorylineIntensity.PERSONAL: {"heat": 1.5, "rating_bonus": 0.5, "fan_bonus": 2.0},
}


@dataclass
class StorylineMatch:
    week: int
    year: int
    match_display: str
    rating: float
    winner: str = ""
    finish_type: str = ""
    heat_gained: int = 0


@dataclass
class StorylineBeat:
    week: int
    year: int
    beat_type: str
    description: str
    wrestlers: List[str] = field(default_factory=list)
    heat_impact: int = 0


@dataclass
class Storyline:
    id: str
    name: str
    storyline_type: StorylineType
    intensity: StorylineIntensity
    participants: List[str] = field(default_factory=list)
    stage: StorylineStage = StorylineStage.BUILDING
    heat: int = 10
    week_started: int = 0
    year_started: int = 1
    matches_in_storyline: List[StorylineMatch] = field(default_factory=list)
    beats: List[StorylineBeat] = field(default_factory=list)
    weeks_active: int = 0
    weeks_since_match: int = 0
    is_active: bool = True
    description: str = ""
    notes: str = ""
    resolution: Optional[ResolutionType] = None
    resolution_notes: str = ""
    week_concluded: int = 0
    fan_investment: int = 0
    proposed_by_ai: bool = False
    ai_personality: str = ""

    def add_match(self, week, year, match_display, rating, winner="", finish_type=""):
        template = STORYLINE_TEMPLATES.get(self.storyline_type, {})
        base_heat = template.get("heat_per_match", 15)
        intensity_mult = INTENSITY_MULTIPLIERS.get(self.intensity, {}).get("heat", 1.0)
        heat_gained = int(base_heat * intensity_mult)
        if rating >= 4.5:
            heat_gained = int(heat_gained * 1.5)
        elif rating >= 4.0:
            heat_gained = int(heat_gained * 1.3)
        elif rating < 2.5:
            heat_gained = int(heat_gained * 0.5)
        self.heat = min(100, self.heat + heat_gained)
        self.weeks_since_match = 0
        self.fan_investment += int(heat_gained * 0.5)
        self.matches_in_storyline.append(StorylineMatch(
            week=week, year=year, match_display=match_display,
            rating=rating, winner=winner, finish_type=finish_type,
            heat_gained=heat_gained,
        ))
        self._update_stage()

    def add_beat(self, week, year, beat_type, description, wrestlers=None, heat_impact=5):
        self.beats.append(StorylineBeat(
            week=week, year=year, beat_type=beat_type, description=description,
            wrestlers=wrestlers or [], heat_impact=heat_impact,
        ))
        self.heat = min(100, self.heat + heat_impact)

    def _update_stage(self):
        if not self.is_active:
            return
        match_count = len(self.matches_in_storyline)
        template = STORYLINE_TEMPLATES.get(self.storyline_type, {})
        ideal_matches = template.get("ideal_matches", 4)
        if self.heat >= 80 and match_count >= ideal_matches:
            self.stage = StorylineStage.PEAK
        elif self.heat >= 60:
            self.stage = StorylineStage.HEATING_UP
        elif self.heat >= 30:
            self.stage = StorylineStage.HEATING_UP if match_count > 0 else StorylineStage.BUILDING
        else:
            self.stage = StorylineStage.COOLED if match_count > 0 else StorylineStage.BUILDING

    def weekly_decay(self):
        if not self.is_active or self.stage == StorylineStage.PITCHED:
            return
        self.weeks_active += 1
        self.weeks_since_match += 1
        if self.weeks_since_match >= 2:
            decay = 5 + (self.weeks_since_match - 2) * 3
            self.heat = max(0, self.heat - decay)
            if self.heat < 30 and self.stage in (StorylineStage.HEATING_UP, StorylineStage.PEAK):
                self.stage = StorylineStage.COOLED
        template = STORYLINE_TEMPLATES.get(self.storyline_type, {})
        ideal_weeks = template.get("ideal_weeks", 8)
        if self.weeks_active > ideal_weeks * 1.5 and self.stage != StorylineStage.PEAK:
            self.stage = StorylineStage.COOLED

    def conclude(self, resolution, notes="", week=0):
        self.is_active = False
        self.stage = StorylineStage.CONCLUDED
        self.resolution = resolution
        self.resolution_notes = notes
        self.week_concluded = week

    def approve(self):
        if self.stage == StorylineStage.PITCHED:
            self.stage = StorylineStage.BUILDING

    def reject(self):
        self.is_active = False

    def get_match_rating_bonus(self) -> float:
        if not self.is_active or self.stage == StorylineStage.PITCHED:
            return 0.0
        intensity_mult = INTENSITY_MULTIPLIERS.get(self.intensity, {}).get("rating_bonus", 0.2)
        return intensity_mult * (self.heat / 100)

    def involves_wrestler(self, wrestler_name) -> bool:
        return wrestler_name in self.participants

    def involves_any(self, wrestler_names) -> bool:
        return any(name in self.participants for name in wrestler_names)

    def get_heat_color(self) -> str:
        if self.heat >= 80: return "#dc2626"
        if self.heat >= 60: return "#f59e0b"
        if self.heat >= 40: return "#3b82f6"
        if self.heat >= 20: return "#6b7280"
        return "#4b5563"

    def get_stage_color(self) -> str:
        colors = {
            StorylineStage.PITCHED: "#a855f7", StorylineStage.BUILDING: "#6b7280",
            StorylineStage.HEATING_UP: "#f59e0b", StorylineStage.PEAK: "#dc2626",
            StorylineStage.BLOW_OFF: "#8b5cf6", StorylineStage.COOLED: "#4b5563",
            StorylineStage.CONCLUDED: "#10b981",
        }
        return colors.get(self.stage, "#6b7280")

    def get_icon(self) -> str:
        return STORYLINE_TEMPLATES.get(self.storyline_type, {}).get("icon", "📖")

    def get_participants_display(self) -> str:
        if len(self.participants) == 2:
            return f"{self.participants[0]} vs {self.participants[1]}"
        if len(self.participants) <= 4:
            return " vs ".join(self.participants)
        return f"{self.participants[0]} & {len(self.participants) - 1} others"

    def get_recommendation(self) -> str:
        if not self.is_active:
            return "Storyline concluded."
        if self.stage == StorylineStage.PITCHED:
            return "📝 Pitched by AI — awaiting your approval."
        if self.weeks_since_match == 0:
            return "✅ Recently booked. Build the heat!"
        if self.weeks_since_match == 1:
            return "💭 Consider booking these wrestlers next week."
        if self.weeks_since_match == 2:
            return "⚠️ Heat is starting to drop. Book a match soon!"
        if self.weeks_since_match >= 3:
            return f"🚨 {self.weeks_since_match} weeks without a match! Heat is decaying fast."
        return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "storyline_type": self.storyline_type.value,
            "intensity": self.intensity.value,
            "participants": self.participants,
            "stage": self.stage.value, "heat": self.heat,
            "week_started": self.week_started, "year_started": self.year_started,
            "matches_in_storyline": [
                {"week": m.week, "year": m.year, "match_display": m.match_display,
                 "rating": m.rating, "winner": m.winner, "finish_type": m.finish_type,
                 "heat_gained": m.heat_gained} for m in self.matches_in_storyline
            ],
            "beats": [
                {"week": b.week, "year": b.year, "beat_type": b.beat_type,
                 "description": b.description, "wrestlers": b.wrestlers,
                 "heat_impact": b.heat_impact} for b in self.beats
            ],
            "weeks_active": self.weeks_active,
            "weeks_since_match": self.weeks_since_match,
            "is_active": self.is_active,
            "description": self.description, "notes": self.notes,
            "resolution": self.resolution.value if self.resolution else None,
            "resolution_notes": self.resolution_notes,
            "week_concluded": self.week_concluded,
            "fan_investment": self.fan_investment,
            "proposed_by_ai": self.proposed_by_ai,
            "ai_personality": self.ai_personality,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Storyline":
        sl = cls(
            id=data["id"], name=data["name"],
            storyline_type=StorylineType(data["storyline_type"]),
            intensity=StorylineIntensity(data["intensity"]),
            participants=data.get("participants", []),
            stage=StorylineStage(data.get("stage", "Building")),
            heat=data.get("heat", 10),
            week_started=data.get("week_started", 0),
            year_started=data.get("year_started", 1),
            weeks_active=data.get("weeks_active", 0),
            weeks_since_match=data.get("weeks_since_match", 0),
            is_active=data.get("is_active", True),
            description=data.get("description", ""),
            notes=data.get("notes", ""),
            resolution_notes=data.get("resolution_notes", ""),
            week_concluded=data.get("week_concluded", 0),
            fan_investment=data.get("fan_investment", 0),
            proposed_by_ai=data.get("proposed_by_ai", False),
            ai_personality=data.get("ai_personality", ""),
        )
        if data.get("resolution"):
            try:
                sl.resolution = ResolutionType(data["resolution"])
            except ValueError:
                sl.resolution = None
        for md in data.get("matches_in_storyline", []):
            sl.matches_in_storyline.append(StorylineMatch(
                week=md.get("week", 0), year=md.get("year", 1),
                match_display=md.get("match_display", ""), rating=md.get("rating", 0),
                winner=md.get("winner", ""), finish_type=md.get("finish_type", ""),
                heat_gained=md.get("heat_gained", 0),
            ))
        for bd in data.get("beats", []):
            sl.beats.append(StorylineBeat(
                week=bd.get("week", 0), year=bd.get("year", 1),
                beat_type=bd.get("beat_type", ""), description=bd.get("description", ""),
                wrestlers=bd.get("wrestlers", []), heat_impact=bd.get("heat_impact", 0),
            ))
        return sl
# ==========================================================================
# ========================  STORYLINE ENGINE CLASS  =======================
# ==========================================================================

class StorylineEngine:
    """AI-driven storyline manager (feuds, heat, AI proposals, beats)."""

    def __init__(self):
        self.active_storylines: List[Storyline] = []
        self.concluded_storylines: List[Storyline] = []
        self.pitched_storylines: List[Storyline] = []
        self.next_id: int = 1

    def create_storyline(self, name, storyline_type, intensity, participants,
                         description="", week=0, year=1,
                         proposed_by_ai=False, ai_personality=""):
        template = STORYLINE_TEMPLATES.get(storyline_type, {})
        min_p = template.get("min_participants", 2)
        max_p = template.get("max_participants", 4)
        if len(participants) < min_p or len(participants) > max_p:
            return None
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        sl_id = f"sl_{safe_name}_{self.next_id}"
        storyline = Storyline(
            id=sl_id, name=name, storyline_type=storyline_type,
            intensity=intensity, participants=participants,
            description=description or template.get("description", ""),
            week_started=week, year_started=year,
            proposed_by_ai=proposed_by_ai, ai_personality=ai_personality,
            stage=StorylineStage.PITCHED if proposed_by_ai else StorylineStage.BUILDING,
        )
        self.next_id += 1
        if proposed_by_ai:
            self.pitched_storylines.append(storyline)
        else:
            self.active_storylines.append(storyline)
        return storyline

    def approve_pitch(self, sl_id):
        for sl in self.pitched_storylines[:]:
            if sl.id == sl_id:
                sl.approve()
                self.pitched_storylines.remove(sl)
                self.active_storylines.append(sl)
                return True
        return False

    def reject_pitch(self, sl_id):
        for sl in self.pitched_storylines[:]:
            if sl.id == sl_id:
                sl.reject()
                self.pitched_storylines.remove(sl)
                return True
        return False

    def get_storyline(self, sl_id):
        for sl in self.active_storylines + self.pitched_storylines + self.concluded_storylines:
            if sl.id == sl_id:
                return sl
        return None

    def get_active_storylines(self):
        return [sl for sl in self.active_storylines if sl.is_active]

    def get_pitched_storylines(self):
        return list(self.pitched_storylines)

    def get_storylines_for_wrestler(self, wrestler_name):
        return [sl for sl in self.active_storylines if sl.involves_wrestler(wrestler_name)]

    def get_storylines_for_match(self, wrestler_names):
        matching = []
        for sl in self.active_storylines:
            if not sl.is_active:
                continue
            involved = [name for name in wrestler_names if sl.involves_wrestler(name)]
            if len(involved) >= 2:
                matching.append(sl)
        return matching

    def process_match(self, wrestler_names, week, year, match_display, rating,
                      winner="", finish_type=""):
        advanced = []
        for sl in self.get_storylines_for_match(wrestler_names):
            sl.add_match(week, year, match_display, rating, winner, finish_type)
            advanced.append(sl)
        return advanced

    def weekly_update(self):
        for sl in self.active_storylines:
            sl.weekly_decay()

    def conclude_storyline(self, sl_id, resolution, notes="", week=0):
        sl = self.get_storyline(sl_id)
        if sl and sl.is_active:
            sl.conclude(resolution, notes, week)
            if sl in self.active_storylines:
                self.active_storylines.remove(sl)
            self.concluded_storylines.append(sl)
            return True
        return False

    def get_match_rating_bonus(self, wrestler_names):
        storylines = self.get_storylines_for_match(wrestler_names)
        if not storylines:
            return 0.0
        return max(sl.get_match_rating_bonus() for sl in storylines)

    def get_booking_suggestions(self, max_results=5):
        suggestions = []
        for sl in sorted(self.active_storylines, key=lambda s: -s.weeks_since_match):
            if not sl.is_active or sl.weeks_since_match < 1:
                continue
            urgency = ("high" if sl.weeks_since_match >= 3
                       else "medium" if sl.weeks_since_match >= 2 else "low")
            suggestions.append({
                "storyline_name": sl.name, "storyline_id": sl.id,
                "participants": sl.participants, "weeks_since": sl.weeks_since_match,
                "heat": sl.heat, "urgency": urgency,
                "recommendation": sl.get_recommendation(),
            })
            if len(suggestions) >= max_results:
                break
        return suggestions

    # ---- AI PROPOSALS ----------------------------------------------------
    def ai_propose_storyline(self, roster, ai_personality_name, chaos_factor, week, year):
        if len(roster) < 2:
            return None
        if len(self.pitched_storylines) >= 3:
            return None
        if len(self.active_storylines) >= 6:
            return None
        proposal_chance = 0.2 + (chaos_factor * 0.4)
        if random.random() > proposal_chance:
            return None

        suitable_types = []
        for sl_type, template in STORYLINE_TEMPLATES.items():
            fits = template.get("personality_fit", [])
            simplified = ai_personality_name.replace("The ", "")
            if simplified in fits or not fits:
                suitable_types.append(sl_type)
        if not suitable_types:
            suitable_types = list(STORYLINE_TEMPLATES.keys())

        chosen_type = random.choice(suitable_types)
        template = STORYLINE_TEMPLATES[chosen_type]

        available = [w for w in roster if not w.get("is_injured", False)]
        active_wrestlers = set()
        for sl in self.active_storylines:
            active_wrestlers.update(sl.participants)
        available = [w for w in available if w["name"] not in active_wrestlers]

        num_needed = template["min_participants"]
        if len(available) < num_needed:
            return None

        participants = random.sample(available, num_needed)
        participant_names = [p["name"] for p in participants]

        avg_pop = sum(p.get("popularity", 30) for p in participants) / len(participants)
        if avg_pop >= 70:
            intensity = StorylineIntensity.MAIN_EVENT
        elif avg_pop >= 50:
            intensity = StorylineIntensity.UPPER_MID
        elif avg_pop >= 30:
            intensity = StorylineIntensity.MID_CARD
        else:
            intensity = StorylineIntensity.OPENER
        if chaos_factor > 0.7 and random.random() < 0.3:
            intensity = StorylineIntensity.PERSONAL

        name = self._generate_storyline_name(chosen_type, participant_names)
        return self.create_storyline(
            name=name, storyline_type=chosen_type, intensity=intensity,
            participants=participant_names, description=template["description"],
            week=week, year=year, proposed_by_ai=True,
            ai_personality=ai_personality_name,
        )

    def _generate_storyline_name(self, sl_type, participants):
        if len(participants) == 2:
            base = f"{participants[0]} vs {participants[1]}"
        elif len(participants) <= 4:
            base = " & ".join(participants[:2]) + " vs " + " & ".join(participants[2:])
        else:
            base = f"{participants[0]} and Allies"
        suffixes = {
            StorylineType.RIVALRY: ["— Bad Blood", "— The Rivalry", "— Personal", ""],
            StorylineType.TITLE_CHASE: ["— The Chase", "— Road to Gold", "— Championship Pursuit"],
            StorylineType.BETRAYAL: ["— The Betrayal", "— Backstabber", "— Trust Broken"],
            StorylineType.GRUDGE: ["— Grudge Match", "— Settle the Score", "— No Mercy"],
            StorylineType.HEEL_TURN: ["— The Turn", "— Dark Side", "— Snapped"],
            StorylineType.FACE_TURN: ["— Redemption", "— The Light", "— Reform"],
            StorylineType.UNDERDOG: ["— David vs Goliath", "— The Underdog", "— Against All Odds"],
            StorylineType.LEGACY: ["— Old vs New", "— Legacy", "— Generation War"],
        }
        suffix = random.choice(suffixes.get(sl_type, [""]))
        return f"{base}{suffix}".strip()

    # ---- AI AUTO-ADVANCE -------------------------------------------------
    def ai_advance_storylines(self, week, year, chaos_factor):
        beats_generated = []
        for sl in self.active_storylines:
            if not sl.is_active or sl.stage == StorylineStage.PITCHED:
                continue
            beat_chance = 0.15 + (sl.heat / 100) * 0.3 + (chaos_factor * 0.2)
            if random.random() > beat_chance:
                continue
            beat = self._generate_beat(sl, week, year, chaos_factor)
            if beat:
                sl.add_beat(week=week, year=year, beat_type=beat["type"],
                            description=beat["description"], wrestlers=beat["wrestlers"],
                            heat_impact=beat["heat_impact"])
                beats_generated.append({"storyline_id": sl.id,
                                        "storyline_name": sl.name, **beat})
        return beats_generated

    def _generate_beat(self, storyline, week, year, chaos):
        beat_types = ["promo", "interview", "attack", "run_in", "social_media", "backstage"]
        if storyline.intensity == StorylineIntensity.PERSONAL:
            beat_types.extend(["betrayal_reveal", "ambush", "vendetta"])
        beat_type = random.choice(beat_types)
        if len(storyline.participants) < 2:
            return None
        w1, w2 = storyline.participants[0], storyline.participants[1]
        templates = {
            "promo": [f"{w1} cut a fiery promo about {w2} this week!",
                      f"{w1} addressed the rivalry with {w2} in a powerful interview.",
                      f"{w1} broke kayfabe and called out {w2} directly."],
            "interview": [f"{w1} gave a behind-the-scenes interview about their issues with {w2}.",
                          f"{w2} appeared on a podcast to discuss the {storyline.name} feud."],
            "attack": [f"{w1} attacked {w2} in the parking lot!",
                       f"{w2} ambushed {w1} during their entrance!",
                       f"A backstage brawl broke out between {w1} and {w2}!"],
            "run_in": [f"{w1} ran in during {w2}'s match and caused chaos!",
                       f"{w2} interfered in another match to send a message to {w1}!"],
            "social_media": [f"{w1} posted a brutal callout video aimed at {w2}.",
                             f"Social media war between {w1} and {w2} is heating up!"],
            "backstage": [f"Backstage tensions erupted between {w1} and {w2}!",
                          f"Cameras caught {w1} confronting {w2} in the locker room."],
            "betrayal_reveal": [f"SHOCKING REVEAL: {w1}'s real motives against {w2} were exposed!",
                                f"The truth came out about {w1} and {w2}'s history!"],
            "ambush": [f"{w1} ambushed {w2} with a vicious attack!",
                       f"{w2} was jumped by {w1} backstage!"],
            "vendetta": [f"{w1} swore revenge on {w2} in a personal vendetta!",
                         f"This isn't business anymore — {w1} wants to END {w2}!"],
        }
        description = random.choice(templates.get(beat_type, [f"{w1} and {w2} continue their feud."]))
        heat_impact = (random.randint(8, 15)
                       if beat_type in ("attack", "ambush", "betrayal_reveal")
                       else random.randint(3, 8))
        return {"type": beat_type, "description": description,
                "wrestlers": [w1, w2], "heat_impact": heat_impact}

    # ---- SERIALIZATION ---------------------------------------------------
    def to_dict(self):
        return {
            "active_storylines": [sl.to_dict() for sl in self.active_storylines],
            "pitched_storylines": [sl.to_dict() for sl in self.pitched_storylines],
            "concluded_storylines": [sl.to_dict() for sl in self.concluded_storylines[-30:]],
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data):
        manager = cls()
        manager.next_id = data.get("next_id", 1)
        for sd in data.get("active_storylines", []):
            try:
                manager.active_storylines.append(Storyline.from_dict(sd))
            except Exception:
                pass
        for sd in data.get("pitched_storylines", []):
            try:
                manager.pitched_storylines.append(Storyline.from_dict(sd))
            except Exception:
                pass
        for sd in data.get("concluded_storylines", []):
            try:
                manager.concluded_storylines.append(Storyline.from_dict(sd))
            except Exception:
                pass
        return manager


# ==========================================================================
# ====================  WRITERS ROOM 2.0 (PITCH LAYER)  ===================
# Dict-based pitch flow used by the app routes. Lives alongside the engine.
# ==========================================================================

DIRECTOR_PROFILES = {
    "traditional": {
        "name": "Traditional Booker",
        "blurb": "Long builds, clean payoffs, protects the stars.",
        "risk_bias": -10, "heat_bias": 5, "twist_chance": 0.15,
        "favored_types": ["rivalry", "championship", "redemption"],
    },
    "chaos": {
        "name": "Chaos Booker",
        "blurb": "Swerves, betrayals, nothing is safe.",
        "risk_bias": 25, "heat_bias": 15, "twist_chance": 0.55,
        "favored_types": ["betrayal", "faction_war", "double_turn"],
    },
    "corporate": {
        "name": "Corporate Executive",
        "blurb": "Merch movers, mainstream-friendly, low risk.",
        "risk_bias": -15, "heat_bias": 0, "twist_chance": 0.10,
        "favored_types": ["championship", "corporate_authority", "underdog"],
    },
    "indie": {
        "name": "Indie Visionary",
        "blurb": "Workrate feuds, slow-burn psychology, cult heat.",
        "risk_bias": 10, "heat_bias": 20, "twist_chance": 0.30,
        "favored_types": ["rivalry", "respect", "trilogy"],
    },
}

WRITER_NAMES = [
    "Tom Graves", "Lena Marsh", "Dex Carrow", "Priya Anand",
    "Marco Bellini", "Janelle Pike", "Rhys Okafor", "Sara Vance",
]
WRITER_STYLES = ["Chaos", "Realism", "Drama", "Comedy", "Sports"]
WRITER_SPECIALTIES = [
    "Faction Warfare", "Championship Chases", "Underdog Stories",
    "Heel Turns", "Tag Team Drama", "Long-Term Booking", "Shock Swerves",
]
STORYLINE_PHASES = ["setup", "rising", "complication", "climax", "fallout"]


def ensure_writers_room(game_state):
    """Create Writers Room data on game_state if missing. Save-safe."""
    if not hasattr(game_state, "storylines") or game_state.storylines is None:
        game_state.storylines = []
    if not hasattr(game_state, "writers") or not game_state.writers:
        game_state.writers = _generate_starting_writers()
    if not hasattr(game_state, "active_director") or not game_state.active_director:
        game_state.active_director = "traditional"
    if not hasattr(game_state, "pending_pitches"):
        game_state.pending_pitches = []
    return game_state


def _generate_starting_writers(count=3):
    names = random.sample(WRITER_NAMES, k=min(count, len(WRITER_NAMES)))
    writers = []
    for n in names:
        writers.append({
            "id": f"wr_{random.randint(1000,9999)}",
            "name": n, "style": random.choice(WRITER_STYLES),
            "creativity": random.randint(45, 95), "discipline": random.randint(30, 90),
            "chaos": random.randint(20, 95), "realism": random.randint(20, 95),
            "specialty": random.choice(WRITER_SPECIALTIES), "morale": 70,
        })
    return writers


def new_storyline(title, stype, participants, planned_length=8):
    return {
        "id": f"sl_{int(time.time())}_{random.randint(100,999)}",
        "title": title, "type": stype, "participants": participants,
        "heat": 0, "momentum": 0, "fan_reaction": "neutral",
        "current_phase": "setup", "weeks_running": 0,
        "planned_length": planned_length, "history": [],
        "future_plans": [], "twists": [], "status": "active",
        "writer_id": None, "director": None,
    }


def generate_pitches(game_state, participant_names, mode="ai",
                     director_key=None, count=3):
    director_key = director_key or getattr(game_state, "active_director", "traditional")
    director = DIRECTOR_PROFILES.get(director_key, DIRECTOR_PROFILES["traditional"])
    pitches = []
    for _ in range(count):
        stype = random.choice(director["favored_types"] + ["rivalry", "championship"])
        pitches.append(_build_single_pitch(game_state, participant_names, stype, director, mode))
    game_state.pending_pitches = pitches
    return pitches


def _build_single_pitch(game_state, names, stype, director, mode):
    a = names[0] if len(names) > 0 else "Wrestler A"
    b = names[1] if len(names) > 1 else "Wrestler B"
    base_heat = random.randint(35, 75) + director["heat_bias"]
    base_risk = random.randint(20, 60) + director["risk_bias"]
    return {
        "pitch_id": f"p_{random.randint(10000,99999)}",
        "type": stype, "title": _pitch_title(stype, a, b),
        "summary": _pitch_narrative(stype, a, b), "participants": names,
        "projected": {
            "expected_heat": max(0, min(100, base_heat)),
            "popularity_gain": random.randint(2, 14),
            "risk": max(0, min(100, base_risk)),
            "duration_weeks": random.randint(4, 12),
            "morale_impact": random.randint(-8, 10),
        },
        "director": director["name"], "mode": mode,
        "twist_seed": random.random() < director["twist_chance"],
    }


def _pitch_title(stype, a, b):
    templates = {
        "rivalry": f"{a} vs {b}: Bad Blood", "betrayal": f"The {a} Betrayal",
        "championship": f"{a}'s Title Pursuit", "faction_war": f"War of Factions: {a} & Allies",
        "redemption": f"The Redemption of {a}", "double_turn": f"{a} / {b}: The Double Turn",
        "respect": f"{a} vs {b}: Respect on the Line", "trilogy": f"{a} vs {b}: The Trilogy",
        "underdog": f"{a}: The Long Shot", "corporate_authority": f"{a} vs The Front Office",
    }
    return templates.get(stype, f"{a} vs {b}")


def _pitch_narrative(stype, a, b):
    pool = {
        "rivalry": [f"The crowd is desperate for {a} and {b} to finally collide. "
                    f"A slow-burn rivalry could carry a main event for months."],
        "betrayal": [f"The audience is cooling on {a}. Turning them on {b} and "
                     f"revealing a long-game betrayal could reignite both acts."],
        "championship": [f"{a} is over enough to chase gold. A multi-week pursuit gives "
                         f"the title meaning and tests {a} against the division."],
        "faction_war": [f"{a} is building a following. A faction forming around them "
                        f"sets up a war that can involve the whole roster."],
        "redemption": [f"{a} has been buried for too long. A redemption arc against "
                       f"{b} could turn sympathy into a genuine connection."],
        "double_turn": [f"Risky, but if {a} and {b} swap alignments mid-feud, the pop "
                        f"could be the moment of the year."],
    }
    return random.choice(pool.get(stype, [f"A fresh program between {a} and {b}."]))


def accept_pitch(game_state, pitch_id, edits=None, writer_id=None):
    pitch = next((p for p in getattr(game_state, "pending_pitches", [])
                  if p["pitch_id"] == pitch_id), None)
    if not pitch:
        return None
    edits = edits or {}
    title = edits.get("title", pitch["title"])
    length = edits.get("planned_length", pitch["projected"]["duration_weeks"])
    sl = new_storyline(title, pitch["type"], pitch["participants"], length)
    sl["heat"] = pitch["projected"]["expected_heat"]
    sl["director"] = getattr(game_state, "active_director", "traditional")
    sl["writer_id"] = writer_id or _auto_assign_writer(game_state, pitch["type"])
    if pitch.get("twist_seed"):
        sl["future_plans"].append("planned_twist")
    game_state.storylines.append(sl)
    game_state.pending_pitches = []
    _memory_hook(game_state, sl, event="storyline_started")
    return sl


def _auto_assign_writer(game_state, stype):
    writers = getattr(game_state, "writers", [])
    if not writers:
        return None
    matches = [w for w in writers if stype.replace("_", " ").lower() in w["specialty"].lower()]
    pool = matches or writers
    return max(pool, key=lambda w: w["creativity"])["id"]


def advance_storyline_week(game_state, storyline):
    if storyline["status"] != "active":
        return storyline
    storyline["weeks_running"] += 1
    writer = _get_writer(game_state, storyline.get("writer_id"))
    director = DIRECTOR_PROFILES.get(storyline.get("director"), DIRECTOR_PROFILES["traditional"])

    progress = storyline["weeks_running"] / max(1, storyline["planned_length"])
    idx = min(int(progress * (len(STORYLINE_PHASES) - 1)), len(STORYLINE_PHASES) - 1)
    storyline["current_phase"] = STORYLINE_PHASES[idx]

    beat = _wr_generate_beat(storyline, writer, director)
    storyline["history"].append({"week": storyline["weeks_running"],
                                 "phase": storyline["current_phase"], "beat": beat})

    creativity = writer["creativity"] if writer else 60
    quality_roll = random.randint(-15, 15) + (creativity - 60) // 4
    storyline["heat"] = max(0, min(100, storyline["heat"] + quality_roll))
    storyline["momentum"] = quality_roll

    twist_chance = director["twist_chance"]
    if writer:
        twist_chance += (writer["chaos"] - 50) / 200.0
    if random.random() < max(0.02, twist_chance):
        twist = _wr_generate_twist(storyline)
        storyline["twists"].append({"week": storyline["weeks_running"], "twist": twist})
        storyline["heat"] = min(100, storyline["heat"] + random.randint(3, 12))

    storyline["fan_reaction"] = _fan_reaction(storyline["heat"])
    _mind_hook(game_state, storyline)

    if storyline["weeks_running"] >= storyline["planned_length"]:
        storyline["status"] = "concluded"
        _memory_hook(game_state, storyline, event="storyline_concluded")
    return storyline


def advance_all_storylines(game_state):
    ensure_writers_room(game_state)
    return [advance_storyline_week(game_state, sl) for sl in game_state.storylines]


def _wr_generate_beat(storyline, writer, director):
    phase = storyline["current_phase"]
    p = storyline["participants"]
    a = p[0] if p else "the champion"
    b = p[1] if len(p) > 1 else "the challenger"
    beats = {
        "setup": [f"Tension simmers between {a} and {b} after a tense confrontation."],
        "rising": [f"{a} gains the upper hand, drawing a loud crowd reaction."],
        "complication": [f"An unexpected interference complicates things for {a}."],
        "climax": [f"{a} and {b} tear the house down in a near-classic."],
        "fallout": [f"The dust settles; {a} is changed by the feud with {b}."],
    }
    return random.choice(beats.get(phase, [f"{a} and {b} continue their program."]))


def _wr_generate_twist(storyline):
    return random.choice([
        "A surprise heel turn shocks the arena.",
        "A returning veteran inserts themselves into the feud.",
        "A betrayal from a trusted ally.",
        "A contract stipulation is revealed.",
        "An injury angle raises the stakes.",
        "A title is put on the line unexpectedly.",
    ])


def _fan_reaction(heat):
    if heat >= 80: return "red_hot"
    if heat >= 60: return "invested"
    if heat >= 40: return "neutral"
    if heat >= 20: return "cooling"
    return "rejected"


def _get_writer(game_state, writer_id):
    for w in getattr(game_state, "writers", []):
        if w["id"] == writer_id:
            return w
    return None


def _mind_hook(game_state, storyline):
    if _mind_react is None:
        return
    try:
        _mind_react(game_state, storyline)
    except Exception:
        pass


def _memory_hook(game_state, storyline, event):
    if _record_memory is None:
        return
    try:
        for name in storyline["participants"]:
            _record_memory(game_state, wrestler=name, event=event,
                           detail=storyline["title"], week=storyline.get("weeks_running", 0))
    except Exception:
        pass