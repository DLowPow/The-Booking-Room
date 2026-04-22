"""
Progression System - XP, Levels, and Unlocks
100 Level system with exponential growth curve
XP earned from shows + first-time milestones only
8 Wrestling Styles, day-based calendar
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import math


class PromotionTier(Enum):
    BACKYARD = 1
    LOCAL = 2
    REGIONAL = 3
    NATIONAL = 4
    INTERNATIONAL = 5
    CONTINENTAL = 6
    GLOBAL = 7
    LEGENDARY = 8
    IMMORTAL = 9


class UnlockCategory(Enum):
    VENUE = "Venue"
    PRODUCTION = "Production"
    ROSTER = "Roster"
    SHOWS = "Shows"
    MATCH_TYPES = "Match Types"
    CONTRACTS = "Contracts"
    FEATURES = "Features"
    TITLES = "Championships"
    COSMETICS = "Cosmetics"


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    xp_reward: int
    money_reward: int = 0
    prestige_reward: int = 0
    fans_reward: int = 0
    is_hidden: bool = False
    is_earned: bool = False
    earned_date: str = ""
    progress: int = 0
    target: int = 1
    icon: str = "🏆"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "xp_reward": self.xp_reward, "money_reward": self.money_reward,
            "prestige_reward": self.prestige_reward, "fans_reward": self.fans_reward,
            "is_hidden": self.is_hidden, "is_earned": self.is_earned,
            "earned_date": self.earned_date, "progress": self.progress,
            "target": self.target, "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Achievement":
        return cls(**data)


# ==================== LEVEL SYSTEM (100 LEVELS) ====================

MAX_LEVEL = 100


def calculate_xp_for_level(level: int) -> int:
    if level <= 1:
        return 0
    if level > MAX_LEVEL:
        level = MAX_LEVEL
    if level <= 10:
        return int(25 * (level ** 1.8))
    elif level <= 25:
        base = calculate_xp_for_level(10)
        return base + int(150 * ((level - 10) ** 1.9))
    elif level <= 50:
        base = calculate_xp_for_level(25)
        return base + int(500 * ((level - 25) ** 2.0))
    elif level <= 75:
        base = calculate_xp_for_level(50)
        return base + int(2000 * ((level - 50) ** 2.1))
    else:
        base = calculate_xp_for_level(75)
        return base + int(10000 * ((level - 75) ** 2.2))


LEVEL_XP_REQUIREMENTS = {level: calculate_xp_for_level(level) for level in range(1, MAX_LEVEL + 1)}


def get_xp_for_level(level: int) -> int:
    if level <= 0:
        return 0
    if level > MAX_LEVEL:
        return LEVEL_XP_REQUIREMENTS[MAX_LEVEL]
    return LEVEL_XP_REQUIREMENTS.get(level, 0)


def get_level_from_xp(total_xp: int) -> int:
    level = 1
    for lvl in range(1, MAX_LEVEL + 1):
        if total_xp >= LEVEL_XP_REQUIREMENTS[lvl]:
            level = lvl
        else:
            break
    return min(level, MAX_LEVEL)


def get_xp_progress(total_xp: int) -> Tuple[int, int, int, float]:
    current_level = get_level_from_xp(total_xp)
    if current_level >= MAX_LEVEL:
        return current_level, 0, 0, 100.0
    current_level_xp = get_xp_for_level(current_level)
    next_level_xp = get_xp_for_level(current_level + 1)
    xp_into_level = total_xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp
    percentage = (xp_into_level / xp_needed) * 100 if xp_needed > 0 else 100
    return current_level, xp_into_level, xp_needed, percentage


LEVEL_TO_PROMOTION_TIER = {
    (1, 9): PromotionTier.BACKYARD,
    (10, 19): PromotionTier.LOCAL,
    (20, 34): PromotionTier.REGIONAL,
    (35, 49): PromotionTier.NATIONAL,
    (50, 64): PromotionTier.INTERNATIONAL,
    (65, 79): PromotionTier.CONTINENTAL,
    (80, 89): PromotionTier.GLOBAL,
    (90, 99): PromotionTier.LEGENDARY,
    (100, 100): PromotionTier.IMMORTAL,
}


def get_promotion_tier(level: int) -> PromotionTier:
    for (min_lvl, max_lvl), tier in LEVEL_TO_PROMOTION_TIER.items():
        if min_lvl <= level <= max_lvl:
            return tier
    return PromotionTier.IMMORTAL


def get_tier_name(tier: PromotionTier) -> str:
    names = {
        PromotionTier.BACKYARD: "Backyard Federation",
        PromotionTier.LOCAL: "Local Promotion",
        PromotionTier.REGIONAL: "Regional Territory",
        PromotionTier.NATIONAL: "National Promotion",
        PromotionTier.INTERNATIONAL: "International Promotion",
        PromotionTier.CONTINENTAL: "Continental Powerhouse",
        PromotionTier.GLOBAL: "Global Promotion",
        PromotionTier.LEGENDARY: "Legendary Promotion",
        PromotionTier.IMMORTAL: "Immortal Status",
    }
    return names.get(tier, "Unknown")


# ==================== LEVEL REWARDS ====================

LEVEL_REWARDS = {
    1: {
        "description": "Welcome to the wrestling business!",
        "unlocks": [
            "Tier 1 venues", "Hire up to 5 wrestlers",
            "Run 1 show per week", "Basic production items",
        ],
        "roster_limit": 5, "shows_per_week": 1, "venue_tier_max": 1,
        "max_championships": 0, "match_slots_weekly": 4, "match_slots_ppv": 4,
        "match_types": ["Singles", "Tag Team"],
    },
    3: {
        "description": "Learning the ropes!",
        "unlocks": ["Hire up to 8 wrestlers", "Triple Threat", "Intergender Singles"],
        "roster_limit": 8,
        "match_types": ["Singles", "Tag Team", "Triple Threat", "Intergender Singles"],
    },
    5: {
        "description": "Building a foundation",
        "unlocks": ["Hire up to 10 wrestlers", "Create 1 championship"],
        "roster_limit": 10, "max_championships": 1,
    },
    7: {
        "description": "Gaining momentum",
        "unlocks": ["Hire up to 12 wrestlers", "Fatal Four Way", "Intergender Tag"],
        "roster_limit": 12,
        "match_types": ["Singles", "Tag Team", "Triple Threat", "Fatal Four Way", "Intergender Singles", "Intergender Tag"],
    },
    10: {
        "description": "Local territory status!",
        "unlocks": ["Tier 2 venues", "Hire up to 15 wrestlers", "Hardcore", "6-Man Tag"],
        "roster_limit": 15, "shows_per_week": 2, "venue_tier_max": 2,
        "match_slots_weekly": 5, "match_slots_ppv": 5,
        "match_types": ["Singles", "Tag Team", "Triple Threat", "Fatal Four Way", "Hardcore", "6-Man Tag", "Intergender Singles", "Intergender Tag"],
    },
    12: {
        "description": "Making a name",
        "unlocks": ["Hire up to 18 wrestlers", "Create 2 championships"],
        "roster_limit": 18, "max_championships": 2,
    },
    15: {
        "description": "Territorial recognition",
        "unlocks": ["Hire up to 20 wrestlers", "Submission", "Cage"],
        "roster_limit": 20, "match_types_add": ["Submission", "Cage"],
    },
    18: {
        "description": "Growing ambitions",
        "unlocks": ["Hire up to 25 wrestlers", "Create 3 championships", "Ladder"],
        "roster_limit": 25, "max_championships": 3, "match_types_add": ["Ladder"],
    },
    20: {
        "description": "Regional territory!",
        "unlocks": ["Tier 3 venues", "PPV Events", "Tables", "Last Man Standing"],
        "roster_limit": 30, "venue_tier_max": 3, "shows_per_week": 3,
        "can_run_ppv": True, "match_slots_weekly": 5, "match_slots_ppv": 6,
        "match_types_add": ["Tables", "Last Man Standing"],
    },
    23: {
        "description": "Expanding horizons",
        "unlocks": ["Hire up to 35 wrestlers", "Iron Man", "I Quit"],
        "roster_limit": 35, "match_types_add": ["Iron Man", "I Quit"],
    },
    25: {
        "description": "Serious contender",
        "unlocks": ["Hire up to 40 wrestlers", "Create 4 championships", "TLC"],
        "roster_limit": 40, "max_championships": 4, "match_types_add": ["TLC"],
    },
    28: {
        "description": "Building an empire",
        "unlocks": ["Hire up to 45 wrestlers", "Hell in a Cell"],
        "roster_limit": 45, "match_types_add": ["Hell in a Cell"],
    },
    30: {
        "description": "Major regional force",
        "unlocks": ["Hire up to 50 wrestlers", "Create 5 championships", "Elimination Chamber"],
        "roster_limit": 50, "max_championships": 5, "shows_per_week": 4,
        "match_slots_weekly": 6, "match_slots_ppv": 7,
        "match_types_add": ["Elimination Chamber"],
    },
    35: {
        "description": "National promotion!",
        "unlocks": ["Tier 4 venues", "TV Deal opportunities", "Battle Royal", "Gauntlet"],
        "roster_limit": 60, "venue_tier_max": 4, "can_get_tv_deal": True,
        "match_slots_weekly": 6, "match_slots_ppv": 8,
        "match_types_add": ["Battle Royal", "Gauntlet"],
    },
    40: {
        "description": "Prime time player",
        "unlocks": ["Hire up to 70 wrestlers", "Create 6 championships", "War Games"],
        "roster_limit": 70, "max_championships": 6, "match_types_add": ["War Games"],
    },
    45: {
        "description": "Wrestling powerhouse",
        "unlocks": ["Hire up to 80 wrestlers", "Inferno", "Buried Alive"],
        "roster_limit": 80, "match_types_add": ["Inferno", "Buried Alive"],
    },
    50: {
        "description": "International promotion!",
        "unlocks": ["Tier 5 venues", "Royal Rumble", "International touring"],
        "roster_limit": 100, "venue_tier_max": 5, "shows_per_week": 5,
        "max_championships": 7, "can_tour_international": True,
        "match_slots_weekly": 7, "match_slots_ppv": 9,
        "match_types_add": ["Royal Rumble"],
    },
    55: {
        "description": "Global ambitions",
        "unlocks": ["Hire up to 110 wrestlers", "Create 8 championships"],
        "roster_limit": 110, "max_championships": 8,
    },
    60: {
        "description": "Wrestling empire",
        "unlocks": ["Hire up to 120 wrestlers", "Multiple brands"],
        "roster_limit": 120, "can_have_brands": True,
    },
    65: {
        "description": "Continental powerhouse!",
        "unlocks": ["Tier 6 venues (Stadiums)", "Create 10 championships"],
        "roster_limit": 140, "venue_tier_max": 6, "shows_per_week": 6,
        "max_championships": 10,
        "match_slots_weekly": 8, "match_slots_ppv": 10,
    },
    70: {
        "description": "Dominant force",
        "unlocks": ["Hire up to 160 wrestlers"],
        "roster_limit": 160,
    },
    75: {
        "description": "Industry leader",
        "unlocks": ["Hire up to 180 wrestlers", "Create 12 championships"],
        "roster_limit": 180, "max_championships": 12,
    },
    80: {
        "description": "Global promotion!",
        "unlocks": ["Hire up to 200 wrestlers", "Hall of Fame"],
        "roster_limit": 200, "has_hall_of_fame": True,
    },
    85: {
        "description": "Wrestling giant",
        "unlocks": ["Hire up to 225 wrestlers", "Create 15 championships"],
        "roster_limit": 225, "max_championships": 15,
    },
    90: {
        "description": "Legendary promotion!",
        "unlocks": ["Tier 7 venues (Super Stadiums)", "Unlimited shows"],
        "roster_limit": 250, "venue_tier_max": 7, "shows_per_week": 99,
    },
    95: {
        "description": "All-time great",
        "unlocks": ["Hire up to 300 wrestlers", "Create 20 championships"],
        "roster_limit": 300, "max_championships": 20, "prestige_mode_available": True,
    },
    100: {
        "description": "IMMORTAL STATUS ACHIEVED!",
        "unlocks": ["Unlimited roster", "Unlimited championships", "All content unlocked"],
        "roster_limit": 9999, "max_championships": 99, "all_unlocked": True,
    },
}


def get_level_rewards(level: int) -> Dict:
    return LEVEL_REWARDS.get(level, {})


def get_cumulative_limits(level: int) -> Dict:
    limits = {
        "roster_limit": 5, "shows_per_week": 1, "venue_tier_max": 1,
        "max_championships": 0, "match_slots_weekly": 4, "match_slots_ppv": 4,
        "can_run_ppv": False, "can_get_tv_deal": False,
        "can_tour_international": False, "can_have_brands": False,
        "has_hall_of_fame": False, "prestige_mode_available": False,
        "all_unlocked": False,
    }
    for lvl in range(1, level + 1):
        rewards = LEVEL_REWARDS.get(lvl, {})
        for key in limits:
            if key in rewards:
                limits[key] = rewards[key]
    return limits


def get_unlocked_match_types(level: int) -> List[str]:
    match_types = ["Singles", "Tag Team"]
    for lvl in range(1, level + 1):
        rewards = LEVEL_REWARDS.get(lvl, {})
        if "match_types" in rewards:
            match_types = rewards["match_types"]
        if "match_types_add" in rewards:
            match_types.extend(rewards["match_types_add"])
    return list(set(match_types))


# ==================== XP SOURCES (SHOWS ONLY + MILESTONES) ====================

XP_SOURCES = {
    # Shows (main XP source)
    "show_completed": 30,
    "show_quality_bonus_per_star": 15,
    "show_sellout_bonus": 75,
    "show_attendance_per_500": 5,
    # PPV (bigger XP)
    "ppv_completed": 150,
    "ppv_quality_bonus_per_star": 30,
    "ppv_sellout_bonus": 200,
    # Match quality bonuses
    "five_star_match": 150,
    "four_star_match": 40,
    "four_point_five_star_match": 75,
    "match_of_the_year": 750,
}

FAN_SOURCES = {
    "show_completed_base": 50,
    "show_per_star_rating": 25,
    "show_sellout_bonus": 100,
    "show_attendance_percentage": 0.05,
    "ppv_completed_base": 200,
    "ppv_per_star_rating": 50,
    "ppv_sellout_bonus": 300,
    "five

    
