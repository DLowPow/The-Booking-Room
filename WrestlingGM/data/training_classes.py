"""
Training Classes - All available training classes for wrestlers
Physical classes (with injury risk) and Non-Physical classes (with morale risk)
Specialty combo classes for multi-stat development
Integrates with TrainingSchool for tier-based discounts and markup
Players without a school pay base cost; school owners get tier discounts
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ==================== CLASS ENUMS ====================

class ClassCategory(Enum):
    PHYSICAL = "Physical"
    NON_PHYSICAL = "Non-Physical"
    SPECIALTY = "Specialty Combo"
    TRAINEE_ONLY = "Trainee Only"


class ClassDifficulty(Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    ELITE = "Elite"


class PerformanceLevel(Enum):
    DISASTROUS = "Disastrous"
    POOR = "Poor"
    AVERAGE = "Average"
    GOOD = "Good"
    EXCELLENT = "Excellent"


# ==================== STAT CEILING ====================

# Stats can only be raised to this maximum via training classes
# Beyond this, wrestlers must improve through actual matches
STAT_CEILING_FROM_TRAINING = 80


# ==================== PERFORMANCE INFO ====================

PERFORMANCE_INFO = {
    PerformanceLevel.EXCELLENT: {
        "icon": "⭐",
        "color": "#fbbf24",
        "stat_boost": 3,
        "morale_change": 10,
        "weight": 15,
        "description": "Captured the room. Career-defining performance.",
    },
    PerformanceLevel.GOOD: {
        "icon": "✅",
        "color": "#10b981",
        "stat_boost": 2,
        "morale_change": 5,
        "weight": 30,
        "description": "Solid showing. Real growth.",
    },
    PerformanceLevel.AVERAGE: {
        "icon": "➖",
        "color": "#6b7280",
        "stat_boost": 1,
        "morale_change": 0,
        "weight": 35,
        "description": "Did the work. Got the basics.",
    },
    PerformanceLevel.POOR: {
        "icon": "⚠️",
        "color": "#f59e0b",
        "stat_boost": 0,
        "morale_change": -5,
        "weight": 15,
        "description": "Underwhelming effort. Little to show.",
    },
    PerformanceLevel.DISASTROUS: {
        "icon": "💀",
        "color": "#dc2626",
        "stat_boost": 0,
        "morale_change": -15,
        "weight": 5,
        "description": "Embarrassed themselves. Setback.",
    },
}


# ==================== CLASS DATACLASS ====================

@dataclass
class TrainingClass:
    """A single training class definition with base cost (pre-discount)"""
    id: str
    name: str
    category: ClassCategory
    difficulty: ClassDifficulty
    icon: str
    color: str
    description: str

    # BASE cost & duration (full price when player has no school)
    base_weekly_cost: int
    duration_weeks: int

    # Stat targeting
    primary_stat: str = ""
    secondary_stats: List[str] = field(default_factory=list)
    primary_boost_max: int = 3
    secondary_boost_max: int = 1

    # Risks
    base_injury_risk_percent: int = 0
    base_morale_risk: bool = False
    is_promo_class: bool = False

    # Eligibility
    min_wrestler_level: int = 0
    requires_show_ready: bool = False
    requires_specialty_match: bool = False
    intended_for_trainees: bool = False
    intended_for_roster: bool = True

    # Coach compatibility
    boosting_coach_specialties: List[str] = field(default_factory=list)

    # Match availability
    match_rating_debuff_percent: int = 10

    # Class size
    min_students: int = 1
    max_students: int = 6

    # ==================== PRICING METHODS ====================

    def get_base_total_cost(self) -> int:
        """Total cost over the entire class duration at base rate (no discount)"""
        return self.base_weekly_cost * self.duration_weeks

    def get_weekly_cost_with_school(self, school=None) -> int:
        """Get weekly cost after school discount/markup"""
        if not school or not hasattr(school, 'is_operational') or not school.is_operational():
            return self.base_weekly_cost
        return school.calculate_class_cost(self.base_weekly_cost)

    def get_total_cost_with_school(self, school=None) -> int:
        """Get total class cost after school discount/markup"""
        weekly = self.get_weekly_cost_with_school(school)
        return weekly * self.duration_weeks

    def get_savings_with_school(self, school=None) -> int:
        """Calculate $ saved by using your school vs base price"""
        base_total = self.get_base_total_cost()
        actual_total = self.get_total_cost_with_school(school)
        return max(0, base_total - actual_total)

    # ==================== UI HELPERS ====================

    def get_difficulty_color(self) -> str:
        colors = {
            ClassDifficulty.BEGINNER: "#10b981",
            ClassDifficulty.INTERMEDIATE: "#3b82f6",
            ClassDifficulty.ADVANCED: "#f59e0b",
            ClassDifficulty.ELITE: "#dc2626",
        }
        return colors.get(self.difficulty, "#6b7280")

    def get_category_color(self) -> str:
        colors = {
            ClassCategory.PHYSICAL: "#dc2626",
            ClassCategory.NON_PHYSICAL: "#3b82f6",
            ClassCategory.SPECIALTY: "#fbbf24",
            ClassCategory.TRAINEE_ONLY: "#10b981",
        }
        return colors.get(self.category, "#6b7280")

    def get_risk_summary(self) -> str:
        """Get a short risk summary for UI display"""
        if self.base_injury_risk_percent > 0:
            return f"⚠️ {self.base_injury_risk_percent}% injury risk/week"
        if self.base_morale_risk:
            return "💭 Morale at stake"
        return "✅ No physical risk"

    def get_stats_affected(self) -> List[str]:
        """Get all stats affected by this class"""
        stats = []
        if self.primary_stat:
            stats.append(self.primary_stat)
        stats.extend(self.secondary_stats)
        return stats

    def get_summary_line(self, school=None) -> str:
        weekly = self.get_weekly_cost_with_school(school)
        total = self.get_total_cost_with_school(school)
        return (f"{self.icon} {self.name} — "
                f"${weekly}/wk × {self.duration_weeks} weeks "
                f"(Total: ${total:,})")


# ==================== CLASS CATALOG ====================

TRAINING_CLASSES: Dict[str, TrainingClass] = {

    # ==================== PHYSICAL CLASSES ====================

    "strength_camp": TrainingClass(
        id="strength_camp",
        name="Strength Camp",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.INTERMEDIATE,
        icon="💪",
        color="#dc2626",
        description="Power lifting and strength training. Build raw power.",
        base_weekly_cost=300,
        duration_weeks=4,
        primary_stat="strength",
        primary_boost_max=3,
        base_injury_risk_percent=8,
        boosting_coach_specialties=["Power", "Striking", "Hardcore"],
    ),

    "speed_agility": TrainingClass(
        id="speed_agility",
        name="Speed & Agility",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.INTERMEDIATE,
        icon="⚡",
        color="#fbbf24",
        description="Quickness drills, footwork, and agility training.",
        base_weekly_cost=300,
        duration_weeks=4,
        primary_stat="speed",
        primary_boost_max=3,
        base_injury_risk_percent=6,
        boosting_coach_specialties=["High-Flying", "Striking", "Conditioning"],
    ),

    "technical_wrestling": TrainingClass(
        id="technical_wrestling",
        name="Technical Wrestling",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.ADVANCED,
        icon="🤼",
        color="#3b82f6",
        description="Mat wrestling, submissions, and chain wrestling fundamentals.",
        base_weekly_cost=400,
        duration_weeks=6,
        primary_stat="technique",
        primary_boost_max=3,
        base_injury_risk_percent=5,
        boosting_coach_specialties=["Technical", "Psychology", "All-Around"],
    ),

    "conditioning": TrainingClass(
        id="conditioning",
        name="Conditioning",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.BEGINNER,
        icon="🦾",
        color="#10b981",
        description="Endurance and cardiovascular fitness training.",
        base_weekly_cost=250,
        duration_weeks=4,
        primary_stat="stamina",
        primary_boost_max=3,
        base_injury_risk_percent=4,
        boosting_coach_specialties=["Conditioning", "All-Around"],
    ),

    "toughness_training": TrainingClass(
        id="toughness_training",
        name="Toughness Training",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.ADVANCED,
        icon="🛡️",
        color="#7c2d12",
        description="Pain tolerance, body conditioning, and durability.",
        base_weekly_cost=350,
        duration_weeks=4,
        primary_stat="toughness",
        primary_boost_max=3,
        base_injury_risk_percent=12,
        boosting_coach_specialties=["Hardcore", "Power"],
    ),

    "high_flying_camp": TrainingClass(
        id="high_flying_camp",
        name="High-Flying Camp",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.ELITE,
        icon="🪂",
        color="#8b5cf6",
        description="Aerial maneuvers, dives, and high-risk offense.",
        base_weekly_cost=500,
        duration_weeks=6,
        primary_stat="speed",
        secondary_stats=["technique"],
        primary_boost_max=2,
        secondary_boost_max=1,
        base_injury_risk_percent=15,
        boosting_coach_specialties=["High-Flying"],
    ),

    "hardcore_training": TrainingClass(
        id="hardcore_training",
        name="Hardcore Training",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.ELITE,
        icon="🩸",
        color="#7c2d12",
        description="Weapon work, extreme matches, and pain management.",
        base_weekly_cost=400,
        duration_weeks=4,
        primary_stat="toughness",
        secondary_stats=["strength"],
        primary_boost_max=2,
        secondary_boost_max=1,
        base_injury_risk_percent=18,
        boosting_coach_specialties=["Hardcore"],
    ),

    "ring_psychology": TrainingClass(
        id="ring_psychology",
        name="Ring Psychology",
        category=ClassCategory.PHYSICAL,
        difficulty=ClassDifficulty.ADVANCED,
        icon="🧠",
        color="#06b6d4",
        description="Match storytelling, pacing, and crowd manipulation.",
        base_weekly_cost=400,
        duration_weeks=6,
        primary_stat="psychology",
        primary_boost_max=3,
        base_injury_risk_percent=2,
        boosting_coach_specialties=["Psychology", "Technical", "All-Around"],
    ),

    # ==================== NON-PHYSICAL CLASSES ====================

    "promo_school": TrainingClass(
        id="promo_school",
        name="Promo School",
        category=ClassCategory.NON_PHYSICAL,
        difficulty=ClassDifficulty.INTERMEDIATE,
        icon="🎤",
        color="#ec4899",
        description="Mic work training. Pass/fail performance check at end.",
        base_weekly_cost=250,
        duration_weeks=4,
        primary_stat="mic_skills",
        primary_boost_max=3,
        base_morale_risk=True,
        is_promo_class=True,
        boosting_coach_specialties=["Promo"],
    ),

    "charisma_workshop": TrainingClass(
        id="charisma_workshop",
        name="Charisma Workshop",
        category=ClassCategory.NON_PHYSICAL,
        difficulty=ClassDifficulty.BEGINNER,
        icon="🌟",
        color="#fbbf24",
        description="Stage presence, body language, and crowd connection.",
        base_weekly_cost=300,
        duration_weeks=4,
        primary_stat="charisma",
        primary_boost_max=3,
        base_morale_risk=False,
        boosting_coach_specialties=["Promo"],
    ),

    "acting_coach": TrainingClass(
        id="acting_coach",
        name="Acting Coach",
        category=ClassCategory.NON_PHYSICAL,
        difficulty=ClassDifficulty.ADVANCED,
        icon="🎬",
        color="#a855f7",
        description="Method acting, character work, and emotional range.",
        base_weekly_cost=500,
        duration_weeks=6,
        primary_stat="charisma",
        secondary_stats=["mic_skills"],
        primary_boost_max=2,
        secondary_boost_max=1,
        base_morale_risk=False,
        boosting_coach_specialties=["Promo"],
    ),

    "media_training": TrainingClass(
        id="media_training",
        name="Media Training",
        category=ClassCategory.NON_PHYSICAL,
        difficulty=ClassDifficulty.INTERMEDIATE,
        icon="📺",
        color="#3b82f6",
        description="Interview skills, soundbites, and media presence.",
        base_weekly_cost=400,
        duration_weeks=4,
        primary_stat="mic_skills",
        secondary_stats=["charisma"],
        primary_boost_max=2,
        secondary_boost_max=1,
        base_morale_risk=False,
        boosting_coach_specialties=["Promo"],
    ),

    "character_development": TrainingClass(
        id="character_development",
        name="Character Development",
        category=ClassCategory.NON_PHYSICAL,
        difficulty=ClassDifficulty.ELITE,
        icon="👔",
        color="#8b5cf6",
        description="Build a character. Backstory, motivations, mannerisms.",
        base_weekly_cost=600,
        duration_weeks=8,
        primary_stat="charisma",
        secondary_stats=["mic_skills", "psychology"],
        primary_boost_max=1,
        secondary_boost_max=1,
        base_morale_risk=False,
        boosting_coach_specialties=["Promo", "Psychology"],
    ),

    # ==================== SPECIALTY COMBO CLASSES ====================

    "main_event_bootcamp": TrainingClass(
        id="main_event_bootcamp",
        name="Main Event Bootcamp",
        category=ClassCategory.SPECIALTY,
        difficulty=ClassDifficulty.ELITE,
        icon="🏆",
        color="#fbbf24",
        description="Total physical overhaul. All physical stats improve.",
        base_weekly_cost=2000,
        duration_weeks=12,
        primary_stat="",
        secondary_stats=["strength", "speed", "technique", "stamina", "toughness"],
        primary_boost_max=0,
        secondary_boost_max=1,
        base_injury_risk_percent=20,
        min_wrestler_level=5,
        boosting_coach_specialties=["All-Around"],
        max_students=3,
    ),

    "total_performer": TrainingClass(
        id="total_performer",
        name="Total Performer",
        category=ClassCategory.SPECIALTY,
        difficulty=ClassDifficulty.ELITE,
        icon="🎭",
        color="#a855f7",
        description="Complete character/promo overhaul. All non-physical stats improve.",
        base_weekly_cost=1500,
        duration_weeks=12,
        primary_stat="",
        secondary_stats=["charisma", "mic_skills", "psychology"],
        primary_boost_max=0,
        secondary_boost_max=1,
        base_morale_risk=False,
        min_wrestler_level=5,
        boosting_coach_specialties=["Promo", "Psychology"],
        max_students=3,
    ),

    "legend_maker": TrainingClass(
        id="legend_maker",
        name="Legend Maker",
        category=ClassCategory.SPECIALTY,
        difficulty=ClassDifficulty.ELITE,
        icon="🌟",
        color="#fbbf24",
        description="Elite intensive. Pick 3 stats, each gains +2. Rare opportunity.",
        base_weekly_cost=5000,
        duration_weeks=16,
        primary_stat="",
        secondary_stats=[],
        primary_boost_max=0,
        secondary_boost_max=2,
        base_injury_risk_percent=25,
        min_wrestler_level=8,
        requires_show_ready=True,
        boosting_coach_specialties=["All-Around"],
        max_students=1,
    ),

    # ==================== TRAINEE-ONLY CLASSES ====================

    "trainee_fundamentals": TrainingClass(
        id="trainee_fundamentals",
        name="Trainee Fundamentals",
        category=ClassCategory.TRAINEE_ONLY,
        difficulty=ClassDifficulty.BEGINNER,
        icon="🎓",
        color="#10b981",
        description="Core wrestling basics for new trainees. Bumps, locks, grips.",
        base_weekly_cost=150,
        duration_weeks=4,
        primary_stat="technique",
        secondary_stats=["stamina"],
        primary_boost_max=2,
        secondary_boost_max=1,
        base_injury_risk_percent=4,
        intended_for_trainees=True,
        intended_for_roster=False,
        boosting_coach_specialties=["All-Around", "Technical"],
    ),

    "trainee_promo_basics": TrainingClass(
        id="trainee_promo_basics",
        name="Trainee Promo Basics",
        category=ClassCategory.TRAINEE_ONLY,
        difficulty=ClassDifficulty.BEGINNER,
        icon="🎙️",
        color="#ec4899",
        description="Mic basics for trainees. Building confidence on camera.",
        base_weekly_cost=100,
        duration_weeks=4,
        primary_stat="mic_skills",
        secondary_stats=["charisma"],
        primary_boost_max=2,
        secondary_boost_max=1,
        base_morale_risk=True,
        is_promo_class=True,
        intended_for_trainees=True,
        intended_for_roster=False,
        boosting_coach_specialties=["Promo"],
    ),
}


# ==================== HELPER FUNCTIONS ====================

def get_class(class_id: str) -> Optional[TrainingClass]:
    """Get a class by ID"""
    return TRAINING_CLASSES.get(class_id)


def get_all_classes() -> List[TrainingClass]:
    """Get all available classes"""
    return list(TRAINING_CLASSES.values())


def get_classes_by_category(category: ClassCategory) -> List[TrainingClass]:
    """Get all classes in a category"""
    return [c for c in TRAINING_CLASSES.values() if c.category == category]


def get_classes_for_roster() -> List[TrainingClass]:
    """Get all classes available to main roster wrestlers"""
    return [c for c in TRAINING_CLASSES.values() if c.intended_for_roster]


def get_classes_for_trainees() -> List[TrainingClass]:
    """Get all classes available to trainees"""
    return [c for c in TRAINING_CLASSES.values() if c.intended_for_trainees]


def get_classes_targeting_stat(stat_name: str) -> List[TrainingClass]:
    """Get all classes that improve a specific stat"""
    return [
        c for c in TRAINING_CLASSES.values()
        if c.primary_stat == stat_name or stat_name in c.secondary_stats
    ]


def get_physical_classes() -> List[TrainingClass]:
    return get_classes_by_category(ClassCategory.PHYSICAL)


def get_non_physical_classes() -> List[TrainingClass]:
    return get_classes_by_category(ClassCategory.NON_PHYSICAL)


def get_specialty_classes() -> List[TrainingClass]:
    return get_classes_by_category(ClassCategory.SPECIALTY)


# ==================== ELIGIBILITY CHECKS ====================

def can_wrestler_take_class(
    training_class: TrainingClass,
    wrestler_data: Dict,
) -> Tuple[bool, str]:
    """
    Check if a wrestler can take a given class.
    Returns (can_take, reason_if_not)
    """
    wrestler_level = wrestler_data.get("level_number", 0)
    if training_class.min_wrestler_level > 0 and wrestler_level < training_class.min_wrestler_level:
        return (False, f"Requires Level {training_class.min_wrestler_level}+ wrestler")

    if training_class.requires_show_ready:
        wrestler_level_name = wrestler_data.get("wrestler_level", "")
        if wrestler_level_name == "Trainee":
            return (False, "Requires Show Ready or higher")

    if training_class.primary_stat:
        current_value = wrestler_data.get(training_class.primary_stat, 0)
        if current_value >= STAT_CEILING_FROM_TRAINING:
            return (False, f"Stat already at training ceiling ({STAT_CEILING_FROM_TRAINING})")

    if wrestler_data.get("is_injured", False):
        return (False, "Wrestler is currently injured")

    if wrestler_data.get("current_training_id"):
        return (False, "Already enrolled in another class")

    is_trainee = wrestler_data.get("is_trainee", False)
    if is_trainee and not training_class.intended_for_trainees:
        return (False, "Class not for trainees")
    if not is_trainee and not training_class.intended_for_roster:
        return (False, "Class is for trainees only")

    return (True, "")


def get_eligible_classes_for_wrestler(wrestler_data: Dict) -> List[Dict]:
    """Get all classes a wrestler can take, with reasons for ineligible ones"""
    results = []
    is_trainee = wrestler_data.get("is_trainee", False)

    if is_trainee:
        classes = get_classes_for_trainees()
    else:
        classes = get_classes_for_roster()

    for cls in classes:
        can_take, reason = can_wrestler_take_class(cls, wrestler_data)
        results.append({
            "class": cls,
            "eligible": can_take,
            "reason": reason if not can_take else "",
        })

    return results


# ==================== INJURY RISK CALCULATION ====================

def calculate_injury_risk(
    training_class: TrainingClass,
    wrestler_data: Dict,
    coach_injury_reduction_percent: int = 0,
) -> float:
    """
    Calculate actual injury risk for a wrestler in a class.
    Returns percentage chance per week (0-100).
    """
    if training_class.base_injury_risk_percent == 0:
        return 0.0

    base_risk = float(training_class.base_injury_risk_percent)

    # Age modifier
    age = wrestler_data.get("age", 30)
    if age <= 25:
        base_risk *= 0.8
    elif age <= 35:
        base_risk *= 1.0
    elif age <= 45:
        base_risk *= 1.3
    else:
        base_risk *= 1.7

    # Toughness modifier
    toughness = wrestler_data.get("toughness", 50)
    if toughness >= 70:
        base_risk *= 0.7
    elif toughness >= 50:
        base_risk *= 1.0
    else:
        base_risk *= 1.4

    # Coach reduction (up to 70%)
    if coach_injury_reduction_percent > 0:
        reduction_multiplier = 1.0 - (coach_injury_reduction_percent / 100.0)
        base_risk *= reduction_multiplier

    return max(0.0, min(100.0, base_risk))


# ==================== PERFORMANCE ROLLING ====================

def roll_performance(
    wrestler_data: Dict,
    training_class: TrainingClass,
    coach_skill_bonus: int = 0,
    has_low_morale: bool = False,
) -> PerformanceLevel:
    """
    Roll a performance level for class completion.
    Returns the performance level achieved.
    """
    weights = {
        PerformanceLevel.EXCELLENT: PERFORMANCE_INFO[PerformanceLevel.EXCELLENT]["weight"],
        PerformanceLevel.GOOD: PERFORMANCE_INFO[PerformanceLevel.GOOD]["weight"],
        PerformanceLevel.AVERAGE: PERFORMANCE_INFO[PerformanceLevel.AVERAGE]["weight"],
        PerformanceLevel.POOR: PERFORMANCE_INFO[PerformanceLevel.POOR]["weight"],
        PerformanceLevel.DISASTROUS: PERFORMANCE_INFO[PerformanceLevel.DISASTROUS]["weight"],
    }

    # Adjust based on work ethic
    work_ethic = wrestler_data.get("work_ethic", 65)
    if work_ethic >= 80:
        weights[PerformanceLevel.EXCELLENT] += 10
        weights[PerformanceLevel.GOOD] += 5
        weights[PerformanceLevel.POOR] -= 5
        weights[PerformanceLevel.DISASTROUS] -= 3
    elif work_ethic <= 40:
        weights[PerformanceLevel.EXCELLENT] -= 10
        weights[PerformanceLevel.POOR] += 10
        weights[PerformanceLevel.DISASTROUS] += 5

    # Coach skill boost
    if coach_skill_bonus >= 1:
        weights[PerformanceLevel.EXCELLENT] += coach_skill_bonus * 5
        weights[PerformanceLevel.GOOD] += coach_skill_bonus * 3
        weights[PerformanceLevel.DISASTROUS] -= coach_skill_bonus * 2

    # Low morale penalty
    if has_low_morale:
        weights[PerformanceLevel.EXCELLENT] -= 8
        weights[PerformanceLevel.GOOD] -= 5
        weights[PerformanceLevel.POOR] += 8
        weights[PerformanceLevel.DISASTROUS] += 5

    # Promo class extra volatility
    if training_class.is_promo_class:
        charisma = wrestler_data.get("charisma", 50)
        if charisma >= 70:
            weights[PerformanceLevel.EXCELLENT] += 8
        elif charisma <= 30:
            weights[PerformanceLevel.DISASTROUS] += 10
            weights[PerformanceLevel.POOR] += 5

    # Ensure no negative weights
    for k in weights:
        weights[k] = max(1, weights[k])

    levels = list(weights.keys())
    weight_values = list(weights.values())
    return random.choices(levels, weights=weight_values, k=1)[0]


# ==================== STAT GAIN APPLICATION ====================

def calculate_stat_gains(
    training_class: TrainingClass,
    performance: PerformanceLevel,
    chosen_stats: Optional[List[str]] = None,
) -> Dict[str, int]:
    """
    Calculate actual stat gains based on class and performance.
    chosen_stats only used for Legend Maker (player picks 3 stats).
    Returns dict of {stat_name: gain_value}
    """
    gains: Dict[str, int] = {}
    perf_info = PERFORMANCE_INFO[performance]
    base_boost = perf_info["stat_boost"]

    if base_boost <= 0:
        return gains

    # Special handling for Legend Maker
    if training_class.id == "legend_maker" and chosen_stats:
        for stat in chosen_stats[:3]:
            gains[stat] = min(training_class.secondary_boost_max, base_boost)
        return gains

    # Primary stat
    if training_class.primary_stat:
        boost = min(training_class.primary_boost_max, base_boost)
        gains[training_class.primary_stat] = boost

    # Secondary stats
    secondary_boost = max(1, base_boost - 1)
    secondary_boost = min(training_class.secondary_boost_max, secondary_boost)
    for stat in training_class.secondary_stats:
        gains[stat] = secondary_boost

    return gains


def apply_stat_gains_with_ceiling(
    wrestler_data: Dict,
    gains: Dict[str, int],
) -> Dict[str, int]:
    """
    Apply stat gains respecting the training ceiling.
    Returns actual gains applied.
    """
    actual_gains: Dict[str, int] = {}
    for stat, gain in gains.items():
        current = wrestler_data.get(stat, 0)
        if current >= STAT_CEILING_FROM_TRAINING:
            actual_gains[stat] = 0
            continue
        new_value = min(STAT_CEILING_FROM_TRAINING, current + gain)
        actual_gains[stat] = new_value - current

    return actual_gains


# ==================== CLASS RECOMMENDATIONS ====================

def get_recommended_classes_for_wrestler(
    wrestler_data: Dict,
    max_results: int = 5,
) -> List[Dict]:
    """
    Get personalized class recommendations based on wrestler's lowest stats.
    Returns list of {"class": TrainingClass, "reason": str}
    """
    recommendations = []
    eligible = get_eligible_classes_for_wrestler(wrestler_data)
    eligible = [e for e in eligible if e["eligible"]]

    # Find wrestler's lowest 3 stats
    stat_values = {
        "strength": wrestler_data.get("strength", 0),
        "speed": wrestler_data.get("speed", 0),
        "technique": wrestler_data.get("technique", 0),
        "charisma": wrestler_data.get("charisma", 0),
        "stamina": wrestler_data.get("stamina", 0),
        "toughness": wrestler_data.get("toughness", 0),
        "mic_skills": wrestler_data.get("mic_skills", 0),
        "psychology": wrestler_data.get("psychology", 0),
    }
    sorted_stats = sorted(stat_values.items(), key=lambda x: x[1])
    lowest_stats = [s[0] for s in sorted_stats[:3]]

    scored = []
    for entry in eligible:
        cls = entry["class"]
        score = 0
        reason_parts = []

        if cls.primary_stat in lowest_stats:
            score += 10
            reason_parts.append(f"Boosts low {cls.primary_stat}")

        for stat in cls.secondary_stats:
            if stat in lowest_stats:
                score += 5
                reason_parts.append(f"Also boosts {stat}")

        # Penalize injury risk for older wrestlers
        age = wrestler_data.get("age", 30)
        if age > 40 and cls.base_injury_risk_percent > 10:
            score -= 5

        if score > 0:
            scored.append({
                "class": cls,
                "reason": " · ".join(reason_parts) if reason_parts else "Solid choice",
                "score": score,
            })

    scored.sort(key=lambda x: -x["score"])
    return scored[:max_results]


# ==================== UI METADATA ====================

def get_category_summary(category: ClassCategory, school=None) -> Dict:
    """Get summary stats for a category, optionally with school discounts applied"""
    classes = get_classes_by_category(category)
    if not classes:
        return {"count": 0, "min_cost": 0, "max_cost": 0, "avg_duration": 0}

    weekly_costs = [c.get_weekly_cost_with_school(school) for c in classes]
    total_costs = [c.get_total_cost_with_school(school) for c in classes]

    return {
        "count": len(classes),
        "min_cost": min(weekly_costs),
        "max_cost": max(weekly_costs),
        "min_total": min(total_costs),
        "max_total": max(total_costs),
        "avg_duration": sum(c.duration_weeks for c in classes) / len(classes),
    }


def get_full_catalog_for_ui(school=None) -> Dict:
    """
    Build the full catalog organized for UI display.
    If school is provided, costs are calculated with discount applied.
    """
    def class_to_dict(c: TrainingClass) -> Dict:
        weekly = c.get_weekly_cost_with_school(school)
        total = c.get_total_cost_with_school(school)
        savings = c.get_savings_with_school(school)
        base_total = c.get_base_total_cost()

        return {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "color": c.color,
            "description": c.description,
            "weekly_cost": weekly,
            "base_weekly_cost": c.base_weekly_cost,
            "duration_weeks": c.duration_weeks,
            "total_cost": total,
            "base_total_cost": base_total,
            "savings": savings,
            "has_discount": savings > 0,
            "is_free": total == 0,
            "primary_stat": c.primary_stat,
            "secondary_stats": c.secondary_stats,
            "injury_risk": c.base_injury_risk_percent,
            "is_promo": c.is_promo_class,
            "min_level": c.min_wrestler_level,
            "max_students": c.max_students,
            "difficulty": c.difficulty.value,
            "difficulty_color": c.get_difficulty_color(),
            "risk_summary": c.get_risk_summary(),
        }

    return {
        "physical": [class_to_dict(c) for c in get_physical_classes()],
        "non_physical": [class_to_dict(c) for c in get_non_physical_classes()],
        "specialty": [class_to_dict(c) for c in get_specialty_classes()],
        "trainee_only": [class_to_dict(c) for c in get_classes_by_category(ClassCategory.TRAINEE_ONLY)],
    }


def get_school_discount_preview(school=None) -> Dict:
    """Get a preview of school discount status for UI banners"""
    if not school or not hasattr(school, 'is_operational') or not school.is_operational():
        return {
            "has_school": False,
            "discount_percent": 0,
            "markup_percent": 0,
            "effective_discount": 0,
            "label": "No School — Pay Full Price",
            "color": "#6b7280",
        }

    base_discount = school.get_class_discount_percent()
    markup = school.class_markup_percent

    # Effective discount after markup
    after_discount = 100 - base_discount
    after_markup = after_discount * (1 + markup / 100)
    effective_discount = max(0, 100 - after_markup)

    if effective_discount >= 100:
        label = "🌟 ALL TRAINING FREE"
        color = "#fbbf24"
    elif effective_discount >= 75:
        label = f"💎 {int(effective_discount)}% OFF"
        color = "#a855f7"
    elif effective_discount >= 50:
        label = f"⭐ {int(effective_discount)}% OFF"
        color = "#3b82f6"
    elif effective_discount >= 25:
        label = f"✅ {int(effective_discount)}% OFF"
        color = "#10b981"
    elif effective_discount > 0:
        label = f"💵 {int(effective_discount)}% OFF"
        color = "#10b981"
    else:
        label = "Standard Pricing"
        color = "#6b7280"

    return {
        "has_school": True,
        "school_tier": school.tier.value,
        "discount_percent": base_discount,
        "markup_percent": markup,
        "effective_discount": int(effective_discount),
        "label": label,
        "color": color,
        "lifetime_savings": school.total_roster_class_savings,
    }
