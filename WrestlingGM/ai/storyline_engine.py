"""
AI Storyline Engine - The Rivalry & Feud System
Tracks storylines from inception to blow-off with heat mechanics
AI Director can propose, advance, and resolve storylines based on personality
Integrates with match engine for rating bonuses and storyline beats
"""

import random
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ==================== STORYLINE TYPES ====================

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
    PITCHED = "Pitched"           # AI suggested, awaiting approval
    BUILDING = "Building"         # Just started
    HEATING_UP = "Heating Up"     # Getting traction
    PEAK = "Peak Heat"            # Maximum intensity
    BLOW_OFF = "Blow-Off"         # Final match phase
    COOLED = "Cooled Down"        # Lost momentum
    CONCLUDED = "Concluded"       # Finished


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


# ==================== STORYLINE TEMPLATES ====================

STORYLINE_TEMPLATES = {
    StorylineType.RIVALRY: {
        "description": "Two wrestlers with personal beef. Classic feud structure.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 4, "heat_per_match": 15,
        "ideal_weeks": 8, "icon": "⚔️",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
    StorylineType.TITLE_CHASE: {
        "description": "Challenger pursues a championship over multiple weeks.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 3, "heat_per_match": 20,
        "ideal_weeks": 6, "icon": "🏆",
        "personality_fit": ["Traditionalist", "Mastermind"],
    },
    StorylineType.BETRAYAL: {
        "description": "Former friend or partner turns on the protagonist.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 5, "heat_per_match": 18,
        "ideal_weeks": 10, "icon": "🗡️",
        "personality_fit": ["Showman", "Mad Scientist"],
    },
    StorylineType.MENTOR_STUDENT: {
        "description": "Trainer and protégé face off in passing-the-torch story.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 3, "heat_per_match": 12,
        "ideal_weeks": 6, "icon": "🎓",
        "personality_fit": ["Traditionalist"],
    },
    StorylineType.FACTION_WAR: {
        "description": "Two stables battle for supremacy.",
        "min_participants": 4, "max_participants": 12,
        "ideal_matches": 6, "heat_per_match": 14,
        "ideal_weeks": 12, "icon": "⚔️",
        "personality_fit": ["Mastermind", "Mad Scientist"],
    },
    StorylineType.GRUDGE: {
        "description": "Short, intense feud with definitive blow-off.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 2, "heat_per_match": 25,
        "ideal_weeks": 4, "icon": "💢",
        "personality_fit": ["Showman", "Mad Scientist"],
    },
    StorylineType.INVASION: {
        "description": "Outside force disrupts your promotion.",
        "min_participants": 4, "max_participants": 10,
        "ideal_matches": 5, "heat_per_match": 16,
        "ideal_weeks": 10, "icon": "🚨",
        "personality_fit": ["Mastermind", "Showman"],
    },
    StorylineType.UNDERDOG: {
        "description": "Lower-card wrestler chases bigger star.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 4, "heat_per_match": 13,
        "ideal_weeks": 8, "icon": "🌟",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
    StorylineType.LOVE_TRIANGLE: {
        "description": "Romantic complication causing in-ring drama.",
        "min_participants": 3, "max_participants": 4,
        "ideal_matches": 3, "heat_per_match": 11,
        "ideal_weeks": 8, "icon": "💔",
        "personality_fit": ["Showman"],
    },
    StorylineType.AUTHORITY: {
        "description": "Wrestler vs management. Power struggle.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 4, "heat_per_match": 17,
        "ideal_weeks": 10, "icon": "👔",
        "personality_fit": ["Showman", "Mastermind"],
    },
    StorylineType.REDEMPTION: {
        "description": "Fallen star fights back to the top.",
        "min_participants": 2, "max_participants": 3,
        "ideal_matches": 5, "heat_per_match": 14,
        "ideal_weeks": 10, "icon": "🔥",
        "personality_fit": ["Traditionalist", "Mad Scientist"],
    },
    StorylineType.HEEL_TURN: {
        "description": "Beloved face turns evil. Shock storyline.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 2, "heat_per_match": 22,
        "ideal_weeks": 4, "icon": "😈",
        "personality_fit": ["Showman", "Mad Scientist"],
    },
    StorylineType.FACE_TURN: {
        "description": "Hated heel becomes a hero. Crowd-pleaser.",
        "min_participants": 2, "max_participants": 4,
        "ideal_matches": 2, "heat_per_match": 22,
        "ideal_weeks": 4, "icon": "😇",
        "personality_fit": ["Traditionalist", "Mastermind"],
    },
    StorylineType.TOURNAMENT: {
        "description": "Tournament-based storyline with bracket progression.",
        "min_participants": 4, "max_participants": 16,
        "ideal_matches": 7, "heat_per_match": 12,
        "ideal_weeks": 8, "icon": "🏅",
        "personality_fit": ["Traditionalist"],
    },
    StorylineType.LEGACY: {
        "description": "Established star vs rising newcomer.",
        "min_participants": 2, "max_participants": 2,
        "ideal_matches": 3, "heat_per_match": 16,
        "ideal_weeks": 6, "icon": "👑",
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


# ==================== STORYLINE DATA CLASSES ====================

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
    """A specific moment in a storyline (interview, attack, run-in, etc)"""
    week: int
    year: int
    beat_type: str  # "promo", "attack", "interview", "betrayal_reveal", "run_in"
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

    def add_match(self, week: int, year: int, match_display: str, rating: float,
                  winner: str = "", finish_type: str = ""):
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
        match = StorylineMatch(
            week=week, year=year, match_display=match_display,
            rating=rating, winner=winner, finish_type=finish_type,
            heat_gained=heat_gained,
        )
        self.matches_in_storyline.append(match)
        self._update_stage()

    def add_beat(self, week: int, year: int, beat_type: str, description: str,
                 wrestlers: List[str] = None, heat_impact: int = 5):
        beat = StorylineBeat(
            week=week, year=year, beat_type=beat_type,
            description=description,
            wrestlers=wrestlers or [],
            heat_impact=heat_impact,
        )
        self.beats.append(beat)
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
            if self.heat < 30 and self.stage in [StorylineStage.HEATING_UP, StorylineStage.PEAK]:
                self.stage = StorylineStage.COOLED
        template = STORYLINE_TEMPLATES.get(self.storyline_type, {})
        ideal_weeks = template.get("ideal_weeks", 8)
        if self.weeks_active > ideal_weeks * 1.5 and self.stage != StorylineStage.PEAK:
            self.stage = StorylineStage.COOLED

    def conclude(self, resolution: ResolutionType, notes: str = "", week: int = 0):
        self.is_active = False
        self.stage = StorylineStage.CONCLUDED
        self.resolution = resolution
        self.resolution_notes = notes
        self.week_concluded = week

    def approve(self):
        """Approve a pitched storyline"""
        if self.stage == StorylineStage.PITCHED:
            self.stage = StorylineStage.BUILDING

    def reject(self):
        """Reject a pitched storyline"""
        self.is_active = False

    def get_match_rating_bonus(self) -> float:
        if not self.is_active or self.stage == StorylineStage.PITCHED:
            return 0.0
        intensity_mult = INTENSITY_MULTIPLIERS.get(self.intensity, {}).get("rating_bonus", 0.2)
        heat_factor = self.heat / 100
        return intensity_mult * heat_factor

    def involves_wrestler(self, wrestler_name: str) -> bool:
        return wrestler_name in self.participants

    def involves_any(self, wrestler_names: List[str]) -> bool:
        return any(name in self.participants for name in wrestler_names)

    def get_heat_color(self) -> str:
        if self.heat >= 80: return "#dc2626"
        if self.heat >= 60: return "#f59e0b"
        if self.heat >= 40: return "#3b82f6"
        if self.heat >= 20: return "#6b7280"
        return "#4b5563"

    def get_stage_color(self) -> str:
        colors = {
            StorylineStage.PITCHED: "#a855f7",
            StorylineStage.BUILDING: "#6b7280",
            StorylineStage.HEATING_UP: "#f59e0b",
            StorylineStage.PEAK: "#dc2626",
            StorylineStage.BLOW_OFF: "#8b5cf6",
            StorylineStage.COOLED: "#4b5563",
            StorylineStage.CONCLUDED: "#10b981",
        }
        return colors.get(self.stage, "#6b7280")

    def get_icon(self) -> str:
        template = STORYLINE_TEMPLATES.get(self.storyline_type, {})
        return template.get("icon", "📖")

    def get_participants_display(self) -> str:
        if len(self.participants) == 2:
            return f"{self.participants[0]} vs {self.participants[1]}"
        elif len(self.participants) <= 4:
            return " vs ".join(self.participants)
        else:
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
                 "heat_gained": m.heat_gained}
                for m in self.matches_in_storyline
            ],
            "beats": [
                {"week": b.week, "year": b.year, "beat_type": b.beat_type,
                 "description": b.description, "wrestlers": b.wrestlers,
                 "heat_impact": b.heat_impact}
                for b in self.beats
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
                match_display=md.get("match_display", ""),
                rating=md.get("rating", 0), winner=md.get("winner", ""),
                finish_type=md.get("finish_type", ""),
                heat_gained=md.get("heat_gained", 0),
            ))
        for bd in data.get("beats", []):
            sl.beats.append(StorylineBeat(
                week=bd.get("week", 0), year=bd.get("year", 1),
                beat_type=bd.get("beat_type", ""),
                description=bd.get("description", ""),
                wrestlers=bd.get("wrestlers", []),
                heat_impact=bd.get("heat_impact", 0),
            ))
        return sl


# ==================== STORYLINE ENGINE ====================

class StorylineEngine:
    """
    AI-driven storyline manager.
    Tracks active feuds, processes weekly updates, proposes new storylines based on
    AI personality, advances storylines through match bookings.
    """

    def __init__(self):
        self.active_storylines: List[Storyline] = []
        self.concluded_storylines: List[Storyline] = []
        self.pitched_storylines: List[Storyline] = []
        self.next_id: int = 1

    def create_storyline(self, name: str, storyline_type: StorylineType,
                         intensity: StorylineIntensity, participants: List[str],
                         description: str = "", week: int = 0, year: int = 1,
                         proposed_by_ai: bool = False, ai_personality: str = "") -> Optional[Storyline]:
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
            description=description if description else template.get("description", ""),
            week_started=week, year_started=year,
            proposed_by_ai=proposed_by_ai,
            ai_personality=ai_personality,
            stage=StorylineStage.PITCHED if proposed_by_ai else StorylineStage.BUILDING,
        )
        self.next_id += 1
        if proposed_by_ai:
            self.pitched_storylines.append(storyline)
        else:
            self.active_storylines.append(storyline)
        return storyline

    def approve_pitch(self, sl_id: str) -> bool:
        """Player approves an AI-pitched storyline"""
        for sl in self.pitched_storylines[:]:
            if sl.id == sl_id:
                sl.approve()
                self.pitched_storylines.remove(sl)
                self.active_storylines.append(sl)
                return True
        return False

    def reject_pitch(self, sl_id: str) -> bool:
        """Player rejects an AI-pitched storyline"""
        for sl in self.pitched_storylines[:]:
            if sl.id == sl_id:
                sl.reject()
                self.pitched_storylines.remove(sl)
                return True
        return False

    def get_storyline(self, sl_id: str) -> Optional[Storyline]:
        for sl in self.active_storylines + self.pitched_storylines + self.concluded_storylines:
            if sl.id == sl_id:
                return sl
        return None

    def get_active_storylines(self) -> List[Storyline]:
        return [sl for sl in self.active_storylines if sl.is_active]

    def get_pitched_storylines(self) -> List[Storyline]:
        return list(self.pitched_storylines)

    def get_storylines_for_wrestler(self, wrestler_name: str) -> List[Storyline]:
        return [sl for sl in self.active_storylines if sl.involves_wrestler(wrestler_name)]

    def get_storylines_for_match(self, wrestler_names: List[str]) -> List[Storyline]:
        matching = []
        for sl in self.active_storylines:
            if not sl.is_active:
                continue
            involved = [name for name in wrestler_names if sl.involves_wrestler(name)]
            if len(involved) >= 2:
                matching.append(sl)
        return matching

    def process_match(self, wrestler_names: List[str], week: int, year: int,
                      match_display: str, rating: float, winner: str = "",
                      finish_type: str = "") -> List[Storyline]:
        advanced = []
        for sl in self.get_storylines_for_match(wrestler_names):
            sl.add_match(week, year, match_display, rating, winner, finish_type)
            advanced.append(sl)
        return advanced

    def weekly_update(self):
        for sl in self.active_storylines:
            sl.weekly_decay()

    def conclude_storyline(self, sl_id: str, resolution: ResolutionType,
                           notes: str = "", week: int = 0) -> bool:
        sl = self.get_storyline(sl_id)
        if sl and sl.is_active:
            sl.conclude(resolution, notes, week)
            if sl in self.active_storylines:
                self.active_storylines.remove(sl)
            self.concluded_storylines.append(sl)
            return True
        return False

    def get_match_rating_bonus(self, wrestler_names: List[str]) -> float:
        storylines = self.get_storylines_for_match(wrestler_names)
        if not storylines:
            return 0.0
        return max(sl.get_match_rating_bonus() for sl in storylines)

    def get_booking_suggestions(self, max_results: int = 5) -> List[Dict]:
        suggestions = []
        for sl in sorted(self.active_storylines, key=lambda s: -s.weeks_since_match):
            if not sl.is_active or sl.weeks_since_match < 1:
                continue
            urgency = "high" if sl.weeks_since_match >= 3 else "medium" if sl.weeks_since_match >= 2 else "low"
            suggestions.append({
                "storyline_name": sl.name,
                "storyline_id": sl.id,
                "participants": sl.participants,
                "weeks_since": sl.weeks_since_match,
                "heat": sl.heat,
                "urgency": urgency,
                "recommendation": sl.get_recommendation(),
            })
            if len(suggestions) >= max_results:
                break
        return suggestions

    # ==================== AI STORYLINE PROPOSALS ====================

    def ai_propose_storyline(
        self,
        roster: List[Dict],
        ai_personality_name: str,
        chaos_factor: float,
        week: int,
        year: int,
    ) -> Optional[Storyline]:
        """AI Director proposes a new storyline based on personality and roster"""

        if len(roster) < 2:
            return None

        # Don't pitch too many at once
        if len(self.pitched_storylines) >= 3:
            return None

        # Don't pitch too many active storylines
        if len(self.active_storylines) >= 6:
            return None

        # Roll for proposal chance based on chaos
        proposal_chance = 0.2 + (chaos_factor * 0.4)
        if random.random() > proposal_chance:
            return None

        # Filter storyline types that fit personality
        suitable_types = []
        for sl_type, template in STORYLINE_TEMPLATES.items():
            personality_fits = template.get("personality_fit", [])
            simplified_name = ai_personality_name.replace("The ", "")
            if simplified_name in personality_fits or not personality_fits:
                suitable_types.append(sl_type)

        if not suitable_types:
            suitable_types = list(STORYLINE_TEMPLATES.keys())

        # Pick storyline type
        chosen_type = random.choice(suitable_types)
        template = STORYLINE_TEMPLATES[chosen_type]

        # Pick participants
        available = [w for w in roster if not w.get("is_injured", False)]

        # Filter out wrestlers already in active storylines
        active_wrestlers = set()
        for sl in self.active_storylines:
            active_wrestlers.update(sl.participants)
        available = [w for w in available if w["name"] not in active_wrestlers]

        num_needed = template["min_participants"]
        if len(available) < num_needed:
            return None

        participants = random.sample(available, num_needed)
        participant_names = [p["name"] for p in participants]

        # Determine intensity based on participant popularity
        avg_pop = sum(p.get("popularity", 30) for p in participants) / len(participants)
        if avg_pop >= 70:
            intensity = StorylineIntensity.MAIN_EVENT
        elif avg_pop >= 50:
            intensity = StorylineIntensity.UPPER_MID
        elif avg_pop >= 30:
            intensity = StorylineIntensity.MID_CARD
        else:
            intensity = StorylineIntensity.OPENER

        # Personal storyline chance for high-chaos personalities
        if chaos_factor > 0.7 and random.random() < 0.3:
            intensity = StorylineIntensity.PERSONAL

        # Generate name
        name = self._generate_storyline_name(chosen_type, participant_names)

        # Create as pitched
        return self.create_storyline(
            name=name,
            storyline_type=chosen_type,
            intensity=intensity,
            participants=participant_names,
            description=template["description"],
            week=week,
            year=year,
            proposed_by_ai=True,
            ai_personality=ai_personality_name,
        )

    def _generate_storyline_name(self, sl_type: StorylineType, participants: List[str]) -> str:
        """Generate a creative name for a storyline"""
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

        suffix_list = suffixes.get(sl_type, [""])
        suffix = random.choice(suffix_list)
        return f"{base}{suffix}".strip()

    # ==================== AI AUTO-ADVANCE ====================

    def ai_advance_storylines(self, week: int, year: int, chaos_factor: float) -> List[Dict]:
        """AI generates storyline beats (interviews, attacks, run-ins) between matches"""
        beats_generated = []

        for sl in self.active_storylines:
            if not sl.is_active or sl.stage == StorylineStage.PITCHED:
                continue

            # Higher heat = more beats
            beat_chance = 0.15 + (sl.heat / 100) * 0.3 + (chaos_factor * 0.2)

            if random.random() > beat_chance:
                continue

            beat = self._generate_beat(sl, week, year, chaos_factor)
            if beat:
                sl.add_beat(
                    week=week, year=year,
                    beat_type=beat["type"],
                    description=beat["description"],
                    wrestlers=beat["wrestlers"],
                    heat_impact=beat["heat_impact"],
                )
                beats_generated.append({
                    "storyline_id": sl.id,
                    "storyline_name": sl.name,
                    **beat,
                })

        return beats_generated

    def _generate_beat(self, storyline: Storyline, week: int, year: int, chaos: float) -> Optional[Dict]:
        """Generate a storyline beat"""
        beat_types = ["promo", "interview", "attack", "run_in", "social_media", "backstage"]

        # Personal storylines get more aggressive beats
        if storyline.intensity == StorylineIntensity.PERSONAL:
            beat_types.extend(["betrayal_reveal", "ambush", "vendetta"])

        beat_type = random.choice(beat_types)

        if len(storyline.participants) < 2:
            return None

        w1, w2 = storyline.participants[0], storyline.participants[1]

        templates = {
            "promo": [
                f"{w1} cut a fiery promo about {w2} this week!",
                f"{w1} addressed the rivalry with {w2} in a powerful interview.",
                f"{w1} broke kayfabe and called out {w2} directly.",
            ],
            "interview": [
                f"{w1} gave a behind-the-scenes interview about their issues with {w2}.",
                f"{w2} appeared on a podcast to discuss the {storyline.name} feud.",
            ],
            "attack": [
                f"{w1} attacked {w2} in the parking lot!",
                f"{w2} ambushed {w1} during their entrance!",
                f"A backstage brawl broke out between {w1} and {w2}!",
            ],
            "run_in": [
                f"{w1} ran in during {w2}'s match and caused chaos!",
                f"{w2} interfered in another match to send a message to {w1}!",
            ],
            "social_media": [
                f"{w1} posted a brutal callout video aimed at {w2}.",
                f"Social media war between {w1} and {w2} is heating up!",
            ],
            "backstage": [
                f"Backstage tensions erupted between {w1} and {w2}!",
                f"Cameras caught {w1} confronting {w2} in the locker room.",
            ],
            "betrayal_reveal": [
                f"SHOCKING REVEAL: {w1}'s real motives against {w2} were exposed!",
                f"The truth came out about {w1} and {w2}'s history!",
            ],
            "ambush": [
                f"{w1} ambushed {w2} with a vicious attack!",
                f"{w2} was jumped by {w1} backstage!",
            ],
            "vendetta": [
                f"{w1} swore revenge on {w2} in a personal vendetta!",
                f"This isn't business anymore — {w1} wants to END {w2}!",
            ],
        }

        description = random.choice(templates.get(beat_type, [f"{w1} and {w2} continue their feud."]))
        heat_impact = random.randint(3, 8) if beat_type not in ["attack", "ambush", "betrayal_reveal"] else random.randint(8, 15)

        return {
            "type": beat_type,
            "description": description,
            "wrestlers": [w1, w2],
            "heat_impact": heat_impact,
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "active_storylines": [sl.to_dict() for sl in self.active_storylines],
            "pitched_storylines": [sl.to_dict() for sl in self.pitched_storylines],
            "concluded_storylines": [sl.to_dict() for sl in self.concluded_storylines[-30:]],
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StorylineEngine":
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
