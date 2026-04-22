"""
Progression System - XP, Levels, and Unlocks
100 Level system with exponential growth curve
XP, Money, and Fans earned from shows
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
class Unlock:
    id: str
    name: str
    category: UnlockCategory
    description: str
    level_required: int
    prestige_required: int = 0
    fans_required: int = 0
    money_required: int = 0
    other_requirements: Dict = field(default_factory=dict)
    is_unlocked: bool = False
    unlock_date: str = ""


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
    """Calculate XP required for a specific level"""
    if level <= 1:
        return 0
    if level > MAX_LEVEL:
        level = MAX_LEVEL

    if level <= 10:
        return int(25 * (level ** 1.8))
    elif level <= 25:
        base = calculate_xp_for_level(10)
        additional = int(150 * ((level - 10) ** 1.9))
        return base + additional
    elif level <= 50:
        base = calculate_xp_for_level(25)
        additional = int(500 * ((level - 25) ** 2.0))
        return base + additional
    elif level <= 75:
        base = calculate_xp_for_level(50)
        additional = int(2000 * ((level - 50) ** 2.1))
        return base + additional
    else:
        base = calculate_xp_for_level(75)
        additional = int(10000 * ((level - 75) ** 2.2))
        return base + additional


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
# UPDATED: Standard renamed to Singles, Intergender added

LEVEL_REWARDS = {
    1: {
        "description": "Welcome to the wrestling business!",
        "unlocks": [
            "Tier 1 venues (Bingo Halls, Bars, Community Centers)",
            "Hire up to 5 wrestlers",
            "Run 1 show per week",
            "Basic production items",
            "Standard singles matches",
        ],
        "roster_limit": 5,
        "shows_per_week": 1,
        "venue_tier_max": 1,
        "max_championships": 0,
        "match_types": ["Singles", "Tag Team"],
    },
    3: {
        "description": "You're learning the ropes!",
        "unlocks": [
            "Hire up to 8 wrestlers",
            "Triple Threat matches",
            "Intergender Singles unlocked",
        ],
        "roster_limit": 8,
        "match_types": ["Singles", "Tag Team", "Triple Threat", "Intergender Singles"],
    },
    5: {
        "description": "Building a foundation",
        "unlocks": [
            "Hire up to 10 wrestlers",
            "Create 1 championship",
            "Standard production items",
        ],
        "roster_limit": 10,
        "max_championships": 1,
    },
    7: {
        "description": "Gaining momentum",
        "unlocks": [
            "Hire up to 12 wrestlers",
            "Fatal Four Way matches",
            "Intergender Tag matches",
        ],
        "roster_limit": 12,
        "match_types": ["Singles", "Tag Team", "Triple Threat", "Fatal Four Way", "Intergender Singles", "Intergender Tag"],
    },
    10: {
        "description": "Local territory status!",
        "unlocks": [
            "Tier 2 venues (Theatres, Ballrooms, Gig Venues)",
            "Hire up to 15 wrestlers",
            "Run 2 shows per week",
            "Hardcore matches",
            "6-Man Tag matches",
        ],
        "roster_limit": 15,
        "shows_per_week": 2,
        "venue_tier_max": 2,
        "match_types": ["Singles", "Tag Team", "Triple Threat", "Fatal Four Way", "Hardcore", "6-Man Tag", "Intergender Singles", "Intergender Tag"],
    },
    12: {
        "description": "Making a name",
        "unlocks": [
            "Hire up to 18 wrestlers",
            "Create 2 championships",
        ],
        "roster_limit": 18,
        "max_championships": 2,
    },
    15: {
        "description": "Territorial recognition",
        "unlocks": [
            "Hire up to 20 wrestlers",
            "Submission matches",
            "Cage matches",
            "Premium production items",
        ],
        "roster_limit": 20,
        "match_types_add": ["Submission", "Cage"],
    },
    18: {
        "description": "Growing ambitions",
        "unlocks": [
            "Hire up to 25 wrestlers",
            "Create 3 championships",
            "Ladder matches",
        ],
        "roster_limit": 25,
        "max_championships": 3,
        "match_types_add": ["Ladder"],
    },
    20: {
        "description": "Regional territory!",
        "unlocks": [
            "Tier 3 venues (Small Arenas)",
            "Hire up to 30 wrestlers",
            "PPV Events",
            "Tables matches",
            "Last Man Standing",
            "Run 3 shows per week",
        ],
        "roster_limit": 30,
        "venue_tier_max": 3,
        "shows_per_week": 3,
        "can_run_ppv": True,
        "match_types_add": ["Tables", "Last Man Standing"],
    },
    23: {
        "description": "Expanding horizons",
        "unlocks": [
            "Hire up to 35 wrestlers",
            "Iron Man matches",
            "I Quit matches",
        ],
        "roster_limit": 35,
        "match_types_add": ["Iron Man", "I Quit"],
    },
    25: {
        "description": "Serious contender",
        "unlocks": [
            "Hire up to 40 wrestlers",
            "Create 4 championships",
            "TLC matches",
        ],
        "roster_limit": 40,
        "max_championships": 4,
        "match_types_add": ["TLC"],
    },
    28: {
        "description": "Building an empire",
        "unlocks": [
            "Hire up to 45 wrestlers",
            "Hell in a Cell",
            "Elite production items",
        ],
        "roster_limit": 45,
        "match_types_add": ["Hell in a Cell"],
    },
    30: {
        "description": "Major regional force",
        "unlocks": [
            "Hire up to 50 wrestlers",
            "Create 5 championships",
            "Elimination Chamber",
            "Run 4 shows per week",
        ],
        "roster_limit": 50,
        "max_championships": 5,
        "shows_per_week": 4,
        "match_types_add": ["Elimination Chamber"],
    },
    35: {
        "description": "National promotion!",
        "unlocks": [
            "Tier 4 venues (Medium Arenas)",
            "Hire up to 60 wrestlers",
            "TV Deal opportunities",
            "Battle Royal (10 man)",
            "Gauntlet matches",
        ],
        "roster_limit": 60,
        "venue_tier_max": 4,
        "can_get_tv_deal": True,
        "match_types_add": ["Battle Royal", "Gauntlet"],
    },
    40: {
        "description": "Prime time player",
        "unlocks": [
            "Hire up to 70 wrestlers",
            "Create 6 championships",
            "War Games",
        ],
        "roster_limit": 70,
        "max_championships": 6,
        "match_types_add": ["War Games"],
    },
    45: {
        "description": "Wrestling powerhouse",
        "unlocks": [
            "Hire up to 80 wrestlers",
            "Inferno matches",
            "Buried Alive",
        ],
        "roster_limit": 80,
        "match_types_add": ["Inferno", "Buried Alive"],
    },
    50: {
        "description": "International promotion!",
        "unlocks": [
            "Tier 5 venues (Large Arenas)",
            "Hire up to 100 wrestlers",
            "International touring",
            "Create 7 championships",
            "Royal Rumble (20 man)",
            "Run 5 shows per week",
        ],
        "roster_limit": 100,
        "venue_tier_max": 5,
        "shows_per_week": 5,
        "max_championships": 7,
        "can_tour_international": True,
        "match_types_add": ["Royal Rumble"],
    },
    55: {
        "description": "Global ambitions",
        "unlocks": ["Hire up to 110 wrestlers", "Create 8 championships"],
        "roster_limit": 110,
        "max_championships": 8,
    },
    60: {
        "description": "Wrestling empire",
        "unlocks": ["Hire up to 120 wrestlers", "Multiple brands/shows", "Royal Rumble (30 man)"],
        "roster_limit": 120,
        "can_have_brands": True,
    },
    65: {
        "description": "Continental powerhouse!",
        "unlocks": [
            "Tier 6 venues (Stadiums)",
            "Hire up to 140 wrestlers",
            "Create 10 championships",
            "Run 6 shows per week",
        ],
        "roster_limit": 140,
        "venue_tier_max": 6,
        "shows_per_week": 6,
        "max_championships": 10,
    },
    70: {
        "description": "Dominant force",
        "unlocks": ["Hire up to 160 wrestlers", "Stadium shows"],
        "roster_limit": 160,
    },
    75: {
        "description": "Industry leader",
        "unlocks": ["Hire up to 180 wrestlers", "Create 12 championships"],
        "roster_limit": 180,
        "max_championships": 12,
    },
    80: {
        "description": "Global promotion!",
        "unlocks": ["Hire up to 200 wrestlers", "Hall of Fame", "Worldwide touring"],
        "roster_limit": 200,
        "has_hall_of_fame": True,
    },
    85: {
        "description": "Wrestling giant",
        "unlocks": ["Hire up to 225 wrestlers", "Create 15 championships"],
        "roster_limit": 225,
        "max_championships": 15,
    },
    90: {
        "description": "Legendary promotion!",
        "unlocks": [
            "Tier 7 venues (Super Stadiums)",
            "Hire up to 250 wrestlers",
            "Custom venue creation",
            "Run unlimited shows",
        ],
        "roster_limit": 250,
        "venue_tier_max": 7,
        "shows_per_week": 99,
    },
    95: {
        "description": "All-time great",
        "unlocks": ["Hire up to 300 wrestlers", "Create 20 championships", "Prestige mode available"],
        "roster_limit": 300,
        "max_championships": 20,
        "prestige_mode_available": True,
    },
    100: {
        "description": "IMMORTAL STATUS ACHIEVED!",
        "unlocks": [
            "Unlimited roster",
            "Unlimited championships",
            "All content unlocked",
            "Legacy bonuses active",
            "Immortal badge",
        ],
        "roster_limit": 9999,
        "max_championships": 99,
        "all_unlocked": True,
    },
}


def get_level_rewards(level: int) -> Dict:
    return LEVEL_REWARDS.get(level, {})


def get_cumulative_limits(level: int) -> Dict:
    limits = {
        "roster_limit": 5,
        "shows_per_week": 1,
        "venue_tier_max": 1,
        "max_championships": 0,
        "can_run_ppv": False,
        "can_get_tv_deal": False,
        "can_tour_international": False,
        "can_have_brands": False,
        "has_hall_of_fame": False,
        "prestige_mode_available": False,
        "all_unlocked": False,
    }
    for lvl in range(1, level + 1):
        rewards = LEVEL_REWARDS.get(lvl, {})
        for key in limits:
            if key in rewards:
                limits[key] = rewards[key]
    return limits


def get_unlocked_match_types(level: int) -> List[str]:
    """Get all match types unlocked at a given level"""
    match_types = ["Singles", "Tag Team"]
    for lvl in range(1, level + 1):
        rewards = LEVEL_REWARDS.get(lvl, {})
        if "match_types" in rewards:
            match_types = rewards["match_types"]
        if "match_types_add" in rewards:
            match_types.extend(rewards["match_types_add"])
    return list(set(match_types))

# ==================== XP SOURCES ====================

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
    
    # First-time milestone bonuses (one-time only)
    "first_show": 200,
    "first_sellout": 250,
    "first_ppv": 500,
    "first_five_star": 300,
    "first_wrestler_signed": 100,
    "first_championship_created": 200,
    "first_title_change": 150,
    "first_profit_week": 250,
    
    # Removed: weekly_base, weekly_per_active_wrestler, weekly_per_1000_fans
    # Removed: wrestler_signed (per-signing XP)
    # Removed: championship_created (per-creation XP)
    # Removed: title_defense, new_champion_crowned (per-event XP)
}


def calculate_show_rewards(
    is_ppv: bool,
    average_match_rating: float,
    attendance: int,
    capacity: int,
    venue_prestige: int,
    five_star_matches: int = 0,
    four_star_matches: int = 0,
    four_point_five_star_matches: int = 0,
    ticket_price: int = 20,
    merchandise_modifier: float = 1.0,
    tv_deal_revenue: int = 0,
) -> Dict:
    result = {
        "xp": {"total": 0, "breakdown": []},
        "money": {"total": 0, "breakdown": []},
        "fans": {"total": 0, "breakdown": []},
    }

    fill_rate = attendance / capacity if capacity > 0 else 0
    is_sellout = fill_rate >= 0.95

    # XP
    xp = 0
    if is_ppv:
        base_xp = XP_SOURCES["ppv_completed"]
        result["xp"]["breakdown"].append(f"PPV Completed: +{base_xp}")
    else:
        base_xp = XP_SOURCES["show_completed"]
        result["xp"]["breakdown"].append(f"Show Completed: +{base_xp}")
    xp += base_xp

    if is_ppv:
        quality_xp = int(average_match_rating * XP_SOURCES["ppv_quality_bonus_per_star"])
    else:
        quality_xp = int(average_match_rating * XP_SOURCES["show_quality_bonus_per_star"])
    xp += quality_xp
    result["xp"]["breakdown"].append(f"Quality ({average_match_rating:.2f}★): +{quality_xp}")

    if is_sellout:
        sellout_xp = XP_SOURCES["ppv_sellout_bonus"] if is_ppv else XP_SOURCES["show_sellout_bonus"]
        xp += sellout_xp
        result["xp"]["breakdown"].append(f"Sellout Bonus: +{sellout_xp}")

    attendance_xp = int((attendance / 500) * XP_SOURCES["show_attendance_per_500"])
    xp += attendance_xp
    result["xp"]["breakdown"].append(f"Attendance ({attendance:,}): +{attendance_xp}")

    if five_star_matches > 0:
        five_xp = five_star_matches * XP_SOURCES["five_star_match"]
        xp += five_xp
        result["xp"]["breakdown"].append(f"5★ Matches (x{five_star_matches}): +{five_xp}")

    if four_point_five_star_matches > 0:
        four_five_xp = four_point_five_star_matches * XP_SOURCES["four_point_five_star_match"]
        xp += four_five_xp
        result["xp"]["breakdown"].append(f"4.5★ Matches (x{four_point_five_star_matches}): +{four_five_xp}")

    if four_star_matches > 0:
        four_xp = four_star_matches * XP_SOURCES["four_star_match"]
        xp += four_xp
        result["xp"]["breakdown"].append(f"4★+ Matches (x{four_star_matches}): +{four_xp}")

    result["xp"]["total"] = xp

    # Money
    money = 0
    ticket_revenue = attendance * ticket_price
    money += ticket_revenue
    result["money"]["breakdown"].append(f"Ticket Sales ({attendance:,} × ${ticket_price}): +${ticket_revenue:,}")

    merch_per_person = 5 + int(average_match_rating * 2)
    merch_revenue = int(attendance * merch_per_person * 0.3 * merchandise_modifier)
    money += merch_revenue
    result["money"]["breakdown"].append(f"Merchandise: +${merch_revenue:,}")

    concession_revenue = int(attendance * 3)
    money += concession_revenue
    result["money"]["breakdown"].append(f"Concessions: +${concession_revenue:,}")

    if tv_deal_revenue > 0:
        money += tv_deal_revenue
        result["money"]["breakdown"].append(f"TV Revenue: +${tv_deal_revenue:,}")

    if is_ppv:
        ppv_bonus = int(attendance * 10)
        money += ppv_bonus
        result["money"]["breakdown"].append(f"PPV Premium: +${ppv_bonus:,}")

    result["money"]["total"] = money

    # Fans
    fans = 0
    if is_ppv:
        base_fans = FAN_SOURCES["ppv_completed_base"]
    else:
        base_fans = FAN_SOURCES["show_completed_base"]
    fans += base_fans
    result["fans"]["breakdown"].append(f"Show Completed: +{base_fans}")

    if is_ppv:
        quality_fans = int(average_match_rating * FAN_SOURCES["ppv_per_star_rating"])
    else:
        quality_fans = int(average_match_rating * FAN_SOURCES["show_per_star_rating"])
    fans += quality_fans
    result["fans"]["breakdown"].append(f"Quality Bonus: +{quality_fans}")

    new_fans_from_attendance = int(attendance * FAN_SOURCES["show_attendance_percentage"])
    fans += new_fans_from_attendance
    result["fans"]["breakdown"].append(f"New Fans from Crowd: +{new_fans_from_attendance}")

    if is_sellout:
        sellout_fans = FAN_SOURCES["ppv_sellout_bonus"] if is_ppv else FAN_SOURCES["show_sellout_bonus"]
        fans += sellout_fans
        result["fans"]["breakdown"].append(f"Sellout Buzz: +{sellout_fans}")

    if five_star_matches > 0:
        five_star_fans = five_star_matches * FAN_SOURCES["five_star_match"]
        fans += five_star_fans
        result["fans"]["breakdown"].append(f"5★ Match Buzz: +{five_star_fans}")

    prestige_fans = int(venue_prestige * 0.5)
    fans += prestige_fans
    result["fans"]["breakdown"].append(f"Venue Prestige: +{prestige_fans}")

    result["fans"]["total"] = fans
    return result


def calculate_weekly_passive(active_wrestlers: int, total_fans: int) -> Dict:
    result = {
        "xp": 0,
        "xp_breakdown": [],
        "fan_change": 0,
        "fan_breakdown": [],
    }

    base_xp = XP_SOURCES["weekly_base"]
    result["xp"] += base_xp
    result["xp_breakdown"].append(f"Weekly Base: +{base_xp}")

    wrestler_xp = active_wrestlers * XP_SOURCES["weekly_per_active_wrestler"]
    result["xp"] += wrestler_xp
    result["xp_breakdown"].append(f"Active Roster ({active_wrestlers}): +{wrestler_xp}")

    fan_xp = int((total_fans / 1000) * XP_SOURCES["weekly_per_1000_fans"])
    result["xp"] += fan_xp
    result["xp_breakdown"].append(f"Fan Base ({total_fans:,}): +{fan_xp}")

    if total_fans > 1000:
        natural_decay = -int(total_fans * 0.005)
        result["fan_change"] = natural_decay
        result["fan_breakdown"].append(f"Natural Decay: {natural_decay}")

    return result


# ==================== ACHIEVEMENTS ====================

DEFAULT_ACHIEVEMENTS = [
    Achievement(id="first_show", name="Opening Night", description="Run your first show", xp_reward=100, fans_reward=50, icon="🎬"),
    Achievement(id="first_sellout", name="Standing Room Only", description="Sell out a venue", xp_reward=150, fans_reward=100, icon="🎟️"),
    Achievement(id="first_profit", name="In The Black", description="End a week with profit", xp_reward=150, money_reward=1000, icon="💰"),
    Achievement(id="first_ppv", name="Special Attraction", description="Run your first PPV", xp_reward=250, fans_reward=200, icon="📺"),
    Achievement(id="first_championship", name="Gold Standard", description="Create your first championship", xp_reward=100, prestige_reward=5, icon="🏆"),
    Achievement(id="shows_10", name="Getting Started", description="Run 10 shows", xp_reward=150, target=10, icon="📋"),
    Achievement(id="shows_25", name="Consistent Booking", description="Run 25 shows", xp_reward=250, target=25, icon="📋"),
    Achievement(id="shows_50", name="Half Century", description="Run 50 shows", xp_reward=400, target=50, icon="📋"),
    Achievement(id="shows_100", name="Century of Shows", description="Run 100 shows", xp_reward=750, money_reward=10000, target=100, icon="💯"),
    Achievement(id="shows_250", name="Promotion Machine", description="Run 250 shows", xp_reward=1000, target=250, icon="⚙️"),
    Achievement(id="shows_500", name="Workhorse Promotion", description="Run 500 shows", xp_reward=2000, target=500, icon="🏆"),
    Achievement(id="shows_1000", name="Thousand Show Legacy", description="Run 1000 shows", xp_reward=5000, money_reward=100000, target=1000, icon="👑"),
    Achievement(id="first_four_star", name="Great Match", description="Produce your first 4+ star match", xp_reward=75, icon="⭐"),
    Achievement(id="first_five_star", name="Five Star Classic", description="Produce your first 5-star match", xp_reward=300, fans_reward=200, icon="🌟"),
    Achievement(id="five_star_5", name="Quality Matters", description="Produce 5 five-star matches", xp_reward=500, target=5, icon="🌟"),
    Achievement(id="five_star_10", name="Quality Promotion", description="Produce 10 five-star matches", xp_reward=750, target=10, icon="🌟"),
    Achievement(id="five_star_25", name="Match Factory", description="Produce 25 five-star matches", xp_reward=1500, target=25, icon="✨"),
    Achievement(id="five_star_50", name="Five Star Factory", description="Produce 50 five-star matches", xp_reward=2500, target=50, icon="✨"),
    Achievement(id="five_star_100", name="Century of Classics", description="Produce 100 five-star matches", xp_reward=5000, target=100, icon="💫"),
    Achievement(id="show_average_4star", name="Quality Night", description="Have a show average 4+ stars", xp_reward=400, icon="⭐"),
    Achievement(id="show_average_4_5star", name="Legendary Show", description="Have a show average 4.5+ stars", xp_reward=750, icon="🌟"),
    Achievement(id="fans_500", name="First Followers", description="Reach 500 fans", xp_reward=50, target=500, icon="👤"),
    Achievement(id="fans_1000", name="Building a Following", description="Reach 1,000 fans", xp_reward=100, target=1000, icon="👥"),
    Achievement(id="fans_5000", name="Growing Fanbase", description="Reach 5,000 fans", xp_reward=200, target=5000, icon="👥"),
    Achievement(id="fans_10000", name="Local Fame", description="Reach 10,000 fans", xp_reward=350, target=10000, icon="🌟"),
    Achievement(id="fans_25000", name="Regional Recognition", description="Reach 25,000 fans", xp_reward=500, target=25000, icon="📈"),
    Achievement(id="fans_50000", name="Growing Empire", description="Reach 50,000 fans", xp_reward=750, target=50000, icon="📈"),
    Achievement(id="fans_100000", name="National Recognition", description="Reach 100,000 fans", xp_reward=1000, target=100000, icon="🌍"),
    Achievement(id="fans_250000", name="Major Promotion", description="Reach 250,000 fans", xp_reward=1500, target=250000, icon="🌍"),
    Achievement(id="fans_500000", name="Half Million Strong", description="Reach 500,000 fans", xp_reward=2000, target=500000, icon="🌎"),
    Achievement(id="fans_1000000", name="Global Phenomenon", description="Reach 1,000,000 fans", xp_reward=3500, target=1000000, icon="🌎"),
    Achievement(id="money_10000", name="Paying the Bills", description="Have $10,000 in the bank", xp_reward=50, target=10000, icon="💵"),
    Achievement(id="money_50000", name="Building Savings", description="Have $50,000 in the bank", xp_reward=100, target=50000, icon="💵"),
    Achievement(id="money_100000", name="Comfortable", description="Have $100,000 in the bank", xp_reward=200, target=100000, icon="💰"),
    Achievement(id="money_500000", name="Wealthy Promotion", description="Have $500,000 in the bank", xp_reward=400, target=500000, icon="💰"),
    Achievement(id="money_1000000", name="Millionaire", description="Have $1,000,000 in the bank", xp_reward=750, target=1000000, icon="🤑"),
    Achievement(id="roster_5", name="Skeleton Crew", description="Have 5 wrestlers signed", xp_reward=50, target=5, icon="🤼"),
    Achievement(id="roster_10", name="Full Roster", description="Have 10 wrestlers signed", xp_reward=100, target=10, icon="🤼"),
    Achievement(id="roster_25", name="Growing Roster", description="Have 25 wrestlers signed", xp_reward=200, target=25, icon="🤼"),
    Achievement(id="roster_50", name="Deep Roster", description="Have 50 wrestlers signed", xp_reward=400, target=50, icon="🏋️"),
    Achievement(id="venue_tier_2", name="Moving Up", description="Run a show at a Tier 2 venue", xp_reward=100, icon="🏛️"),
    Achievement(id="venue_tier_3", name="Arena Show", description="Run a show at a Tier 3 venue", xp_reward=200, icon="🏟️"),
    Achievement(id="venue_tier_5", name="The Big Time", description="Run a show at a Tier 5 venue", xp_reward=600, icon="🏟️"),
    Achievement(id="venue_tier_6", name="Stadium Show", description="Run a show at a stadium", xp_reward=1000, icon="🏟️"),
    Achievement(id="level_10", name="Local Territory", description="Reach Level 10", xp_reward=200, icon="📈"),
    Achievement(id="level_20", name="Regional Power", description="Reach Level 20", xp_reward=400, icon="📈"),
    Achievement(id="level_35", name="National Promotion", description="Reach Level 35", xp_reward=750, icon="📈"),
    Achievement(id="level_50", name="International Recognition", description="Reach Level 50", xp_reward=1500, icon="🌍"),
    Achievement(id="level_100", name="IMMORTAL", description="Reach Level 100 - Maximum level achieved!", xp_reward=15000, money_reward=1000000, fans_reward=100000, icon="👑"),
    Achievement(id="survive_year_1", name="Survived Year One", description="Complete your first year without going bankrupt", xp_reward=500, money_reward=5000, icon="📅"),
    Achievement(id="survive_year_5", name="Five Year Anniversary", description="Run your promotion for 5 years", xp_reward=1000, money_reward=25000, icon="🎂"),
]


# ==================== PROGRESSION CLASS ====================

class ProgressionSystem:
    def __init__(self):
        self.total_xp: int = 0
        self.level: int = 1
        self.promotion_tier: PromotionTier = PromotionTier.BACKYARD
        
        self.stats: Dict[str, int] = {
            "total_shows": 0, "total_ppvs": 0, "total_tv_shows": 0, "sellouts": 0,
            "total_matches": 0, "five_star_matches": 0, "four_star_matches": 0,
            "four_point_five_star_matches": 0, "total_attendance": 0,
            "highest_attendance": 0, "wrestlers_signed_total": 0,
            "wrestlers_released": 0, "wrestlers_retired": 0,
            "championships_created": 0, "title_changes": 0, "title_defenses": 0,
            "storylines_started": 0, "storylines_completed": 0,
            "total_revenue": 0, "total_expenses": 0,
            "highest_weekly_profit": 0, "weeks_profitable": 0,
            "weeks_played": 0, "years_played": 0,
            "highest_show_rating": 0, "peak_fans": 0, "peak_budget": 0,
            "peak_roster_size": 0, "unique_venues_used": 0,
            "highest_venue_tier_used": 1, "viral_moments": 0, "scandals": 0,
        }
        
        self.achievements: List[Achievement] = [
            Achievement(
                id=a.id, name=a.name, description=a.description,
                xp_reward=a.xp_reward, money_reward=a.money_reward,
                prestige_reward=a.prestige_reward, fans_reward=a.fans_reward,
                is_hidden=a.is_hidden, target=a.target, icon=a.icon,
            )
            for a in DEFAULT_ACHIEVEMENTS
        ]
        
        self.unlocked_features: List[str] = []
        self.xp_log: List[Dict] = []
        self.level_up_history: List[Dict] = []
    
    def add_xp(self, amount: int, source: str) -> Tuple[int, bool, List[str]]:
        old_level = self.level
        self.total_xp += amount
        self.level = get_level_from_xp(self.total_xp)
        self.promotion_tier = get_promotion_tier(self.level)
        
        self.xp_log.append({
            "amount": amount, "source": source,
            "total": self.total_xp, "level": self.level,
        })
        
        if len(self.xp_log) > 100:
            self.xp_log = self.xp_log[-100:]
        
        new_unlocks = []
        did_level_up = self.level > old_level
        
        if did_level_up:
            for lvl in range(old_level + 1, self.level + 1):
                rewards = get_level_rewards(lvl)
                if rewards:
                    self.level_up_history.append({"level": lvl, "rewards": rewards})
                    if "unlocks" in rewards:
                        new_unlocks.extend(rewards["unlocks"])
        
        return self.level, did_level_up, new_unlocks
    
    def process_show_completion(
        self, is_ppv, average_match_rating, attendance, capacity,
        venue_prestige, venue_tier, venue_id, five_star_matches=0,
        four_star_matches=0, four_point_five_star_matches=0,
        ticket_price=20, merchandise_modifier=1.0, tv_deal_revenue=0,
        total_matches=0,
    ) -> Dict:
        rewards = calculate_show_rewards(
            is_ppv=is_ppv, average_match_rating=average_match_rating,
            attendance=attendance, capacity=capacity, venue_prestige=venue_prestige,
            five_star_matches=five_star_matches, four_star_matches=four_star_matches,
            four_point_five_star_matches=four_point_five_star_matches,
            ticket_price=ticket_price, merchandise_modifier=merchandise_modifier,
            tv_deal_revenue=tv_deal_revenue,
        )
        
        if is_ppv:
            self.stats["total_ppvs"] += 1
        else:
            self.stats["total_shows"] += 1
        
        self.stats["total_attendance"] += attendance
        self.stats["total_matches"] += total_matches
        self.stats["five_star_matches"] += five_star_matches
        self.stats["four_star_matches"] += four_star_matches
        self.stats["four_point_five_star_matches"] += four_point_five_star_matches
        
        if attendance > self.stats["highest_attendance"]:
            self.stats["highest_attendance"] = attendance
        if average_match_rating > self.stats["highest_show_rating"]:
            self.stats["highest_show_rating"] = average_match_rating
        if attendance >= capacity * 0.95:
            self.stats["sellouts"] += 1
        if venue_tier > self.stats["highest_venue_tier_used"]:
            self.stats["highest_venue_tier_used"] = venue_tier
        
        new_level, leveled_up, new_unlocks = self.add_xp(
            rewards["xp"]["total"],
            f"{'PPV' if is_ppv else 'Show'}: {attendance:,} attendance"
        )
        
        earned_achievements = self.check_achievements(
            venue_tier=venue_tier, venue_id=venue_id,
            average_rating=average_match_rating,
        )
        
        rewards["leveled_up"] = leveled_up
        rewards["new_level"] = new_level
        rewards["new_unlocks"] = new_unlocks
        rewards["achievements_earned"] = earned_achievements
        
        return rewards
    
    def process_weekly_update(
        self, active_wrestlers, total_fans, current_budget,
        weekly_profit, roster_size,
    ) -> Dict:
        result = calculate_weekly_passive(active_wrestlers, total_fans)
        
        self.stats["weeks_played"] += 1
        if self.stats["weeks_played"] % 52 == 0:
            self.stats["years_played"] += 1
        if weekly_profit > 0:
            self.stats["weeks_profitable"] += 1
            if weekly_profit > self.stats["highest_weekly_profit"]:
                self.stats["highest_weekly_profit"] = weekly_profit
        if total_fans > self.stats["peak_fans"]:
            self.stats["peak_fans"] = total_fans
        if current_budget > self.stats["peak_budget"]:
            self.stats["peak_budget"] = current_budget
        if roster_size > self.stats["peak_roster_size"]:
            self.stats["peak_roster_size"] = roster_size
        
        new_level, leveled_up, new_unlocks = self.add_xp(result["xp"], "Weekly progression")
        
        earned_achievements = self.check_achievements(
            fans=total_fans, budget=current_budget,
            roster_size=roster_size, profitable=(weekly_profit > 0),
        )
        
        result["leveled_up"] = leveled_up
        result["new_level"] = new_level
        result["new_unlocks"] = new_unlocks
        result["achievements_earned"] = earned_achievements
        
        return result
    
    def update_stat(self, stat: str, value: int = 1, set_value: bool = False):
        if stat in self.stats:
            if set_value:
                self.stats[stat] = value
            else:
                self.stats[stat] += value
    
    def check_achievements(self, **context) -> List[Achievement]:
        newly_earned = []
        for achievement in self.achievements:
            if achievement.is_earned:
                continue
            earned = self._check_single_achievement(achievement, context)
            if earned:
                achievement.is_earned = True
                newly_earned.append(achievement)
                self.total_xp += achievement.xp_reward
                self.level = get_level_from_xp(self.total_xp)
                self.promotion_tier = get_promotion_tier(self.level)
                self.xp_log.append({
                    "amount": achievement.xp_reward,
                    "source": f"Achievement: {achievement.name}",
                    "total": self.total_xp, "level": self.level,
                })
        return newly_earned
    
    def _check_single_achievement(self, achievement, context):
        aid = achievement.id
        stats = self.stats
        
        if aid == "first_show": return stats["total_shows"] >= 1
        elif aid == "first_ppv": return stats["total_ppvs"] >= 1
        elif aid == "first_sellout": return stats["sellouts"] >= 1
        elif aid == "shows_10": return stats["total_shows"] + stats["total_ppvs"] >= 10
        elif aid == "shows_25": return stats["total_shows"] + stats["total_ppvs"] >= 25
        elif aid == "shows_50": return stats["total_shows"] + stats["total_ppvs"] >= 50
        elif aid == "shows_100": return stats["total_shows"] + stats["total_ppvs"] >= 100
        elif aid == "shows_250": return stats["total_shows"] + stats["total_ppvs"] >= 250
        elif aid == "shows_500": return stats["total_shows"] + stats["total_ppvs"] >= 500
        elif aid == "shows_1000": return stats["total_shows"] + stats["total_ppvs"] >= 1000
        elif aid == "first_four_star": return stats["four_star_matches"] >= 1
        elif aid == "first_five_star": return stats["five_star_matches"] >= 1
        elif aid == "five_star_5": return stats["five_star_matches"] >= 5
        elif aid == "five_star_10": return stats["five_star_matches"] >= 10
        elif aid == "five_star_25": return stats["five_star_matches"] >= 25
        elif aid == "five_star_50": return stats["five_star_matches"] >= 50
        elif aid == "five_star_100": return stats["five_star_matches"] >= 100
        elif aid == "show_average_4star": return context.get("average_rating", 0) >= 4.0
        elif aid == "show_average_4_5star": return context.get("average_rating", 0) >= 4.5
        elif aid == "level_10": return self.level >= 10
        elif aid == "level_20": return self.level >= 20
        elif aid == "level_35": return self.level >= 35
        elif aid == "level_50": return self.level >= 50
        elif aid == "level_100": return self.level >= 100
        elif aid == "survive_year_1": return stats["years_played"] >= 1
        elif aid == "survive_year_5": return stats["years_played"] >= 5
        elif aid == "first_profit": return context.get("profitable", False)
        elif aid == "first_championship": return stats["championships_created"] >= 1
        elif aid == "fans_500": return context.get("fans", 0) >= 500
        elif aid == "fans_1000": return context.get("fans", 0) >= 1000
        elif aid == "fans_5000": return context.get("fans", 0) >= 5000
        elif aid == "fans_10000": return context.get("fans", 0) >= 10000
        elif aid == "fans_25000": return context.get("fans", 0) >= 25000
        elif aid == "fans_50000": return context.get("fans", 0) >= 50000
        elif aid == "fans_100000": return context.get("fans", 0) >= 100000
        elif aid == "fans_250000": return context.get("fans", 0) >= 250000
        elif aid == "fans_500000": return context.get("fans", 0) >= 500000
        elif aid == "fans_1000000": return context.get("fans", 0) >= 1000000
        elif aid == "money_10000": return context.get("budget", 0) >= 10000
        elif aid == "money_50000": return context.get("budget", 0) >= 50000
        elif aid == "money_100000": return context.get("budget", 0) >= 100000
        elif aid == "money_500000": return context.get("budget", 0) >= 500000
        elif aid == "money_1000000": return context.get("budget", 0) >= 1000000
        elif aid == "roster_5": return context.get("roster_size", 0) >= 5
        elif aid == "roster_10": return context.get("roster_size", 0) >= 10
        elif aid == "roster_25": return context.get("roster_size", 0) >= 25
        elif aid == "roster_50": return context.get("roster_size", 0) >= 50
        elif aid == "venue_tier_2": return context.get("venue_tier", 0) >= 2
        elif aid == "venue_tier_3": return context.get("venue_tier", 0) >= 3
        elif aid == "venue_tier_5": return context.get("venue_tier", 0) >= 5
        elif aid == "venue_tier_6": return context.get("venue_tier", 0) >= 6
        return False
    
    def get_progress_display(self) -> Dict:
        current_level, xp_into_level, xp_needed, percentage = get_xp_progress(self.total_xp)
        return {
            "level": current_level, "total_xp": self.total_xp,
            "xp_into_level": xp_into_level, "xp_needed": xp_needed,
            "percentage": percentage, "promotion_tier": self.promotion_tier.name,
            "tier_name": get_tier_name(self.promotion_tier),
            "max_level": MAX_LEVEL, "is_max_level": current_level >= MAX_LEVEL,
        }
    
    def get_limits(self) -> Dict:
        return get_cumulative_limits(self.level)
    
    def get_unlocked_match_types(self) -> List[str]:
        return get_unlocked_match_types(self.level)
    
    def get_earned_achievements(self) -> List[Achievement]:
        return [a for a in self.achievements if a.is_earned]
    
    def get_unearned_achievements(self, include_hidden: bool = False) -> List[Achievement]:
        if include_hidden:
            return [a for a in self.achievements if not a.is_earned]
        return [a for a in self.achievements if not a.is_earned and not a.is_hidden]
    
    def to_dict(self) -> dict:
        return {
            "total_xp": self.total_xp,
            "level": self.level,
            "promotion_tier": self.promotion_tier.value,
            "stats": self.stats,
            "achievements": [a.to_dict() for a in self.achievements],
            "unlocked_features": self.unlocked_features,
            "xp_log": self.xp_log[-50:],
            "level_up_history": self.level_up_history[-20:],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProgressionSystem":
        system = cls()
        system.total_xp = data.get("total_xp", 0)
        system.level = data.get("level", 1)
        system.promotion_tier = PromotionTier(data.get("promotion_tier", 1))
        system.stats = data.get("stats", system.stats)
        system.unlocked_features = data.get("unlocked_features", [])
        system.xp_log = data.get("xp_log", [])
        system.level_up_history = data.get("level_up_history", [])
        
        saved_achievements = {a["id"]: a for a in data.get("achievements", [])}
        for achievement in system.achievements:
            if achievement.id in saved_achievements:
                saved = saved_achievements[achievement.id]
                achievement.is_earned = saved.get("is_earned", False)
                achievement.earned_date = saved.get("earned_date", "")
                achievement.progress = saved.get("progress", 0)
        
        return system
