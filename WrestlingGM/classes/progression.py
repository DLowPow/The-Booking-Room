"""
Progression System - 100 Levels, 10 Tiers
From Backyard Promoter to Wrestling Empire CEO
XP earned from shows + first-time milestones only
49 match types with categorized unlock progression
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import math


# ==================== 10 PROMOTION TIERS ====================

class PromotionTier(Enum):
    BACKYARD = 1
    LOCAL_INDIE = 2
    REGIONAL = 3
    NATIONAL = 4
    MAJOR = 5
    INTERNATIONAL = 6
    CONTINENTAL = 7
    GLOBAL = 8
    INDUSTRY_LEADER = 9
    CEO = 10


TIER_NAMES = {
    PromotionTier.BACKYARD: "Backyard Promoter",
    PromotionTier.LOCAL_INDIE: "Local Indie",
    PromotionTier.REGIONAL: "Regional Territory",
    PromotionTier.NATIONAL: "National Promotion",
    PromotionTier.MAJOR: "Major Promotion",
    PromotionTier.INTERNATIONAL: "International Promotion",
    PromotionTier.CONTINENTAL: "Continental Powerhouse",
    PromotionTier.GLOBAL: "Global Brand",
    PromotionTier.INDUSTRY_LEADER: "Industry Leader",
    PromotionTier.CEO: "Wrestling Empire CEO",
}

TIER_ICONS = {
    PromotionTier.BACKYARD: "🏡",
    PromotionTier.LOCAL_INDIE: "🍺",
    PromotionTier.REGIONAL: "🏛️",
    PromotionTier.NATIONAL: "🎭",
    PromotionTier.MAJOR: "🏟️",
    PromotionTier.INTERNATIONAL: "✈️",
    PromotionTier.CONTINENTAL: "🌍",
    PromotionTier.GLOBAL: "🌎",
    PromotionTier.INDUSTRY_LEADER: "👑",
    PromotionTier.CEO: "🏆",
}


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


# ==================== XP CURVE (100 LEVELS) ====================

MAX_LEVEL = 100


def calculate_xp_for_level(level: int) -> int:
    if level <= 1:
        return 0
    if level > MAX_LEVEL:
        level = MAX_LEVEL
    return int(20 * (level ** 2.15))


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


def get_promotion_tier(level: int) -> PromotionTier:
    if level <= 10: return PromotionTier.BACKYARD
    elif level <= 20: return PromotionTier.LOCAL_INDIE
    elif level <= 30: return PromotionTier.REGIONAL
    elif level <= 40: return PromotionTier.NATIONAL
    elif level <= 50: return PromotionTier.MAJOR
    elif level <= 60: return PromotionTier.INTERNATIONAL
    elif level <= 70: return PromotionTier.CONTINENTAL
    elif level <= 80: return PromotionTier.GLOBAL
    elif level <= 90: return PromotionTier.INDUSTRY_LEADER
    else: return PromotionTier.CEO


def get_tier_name(tier) -> str:
    if isinstance(tier, PromotionTier):
        return TIER_NAMES.get(tier, "Unknown")
    for t in PromotionTier:
        if t.value == tier:
            return TIER_NAMES.get(t, "Unknown")
    return "Unknown"


def get_tier_info(tier) -> Dict:
    if isinstance(tier, int):
        for t in PromotionTier:
            if t.value == tier:
                tier = t
                break
    return {
        "name": TIER_NAMES.get(tier, "Unknown"),
        "icon": TIER_ICONS.get(tier, "🎮"),
        "value": tier.value if isinstance(tier, PromotionTier) else tier,
    }


# ==================== LEVEL REWARDS WITH 49 MATCH TYPES ====================

LEVEL_REWARDS = {
    # ===== TIER 1: BACKYARD (Lvl 1-10) =====
    1: {
        "description": "Welcome to the wrestling business!",
        "unlocks": ["Backyard venues", "Hire up to 5 wrestlers", "Basic ring"],
        "roster_limit": 5, "shows_per_week": 1, "venue_tier_max": 1,
        "max_championships": 0, "match_slots_weekly": 3, "match_slots_ppv": 3,
        "match_types": ["Singles", "Intergender Singles", "Tag Team", "Mixed Tag"],
    },
    2: {
        "description": "Your first regulars are showing up",
        "unlocks": ["Hire up to 6 wrestlers"],
        "roster_limit": 6,
    },
    3: {
        "description": "Word is spreading",
        "unlocks": ["Triple Threat matches", "Hire up to 7 wrestlers"],
        "roster_limit": 7,
        "match_types_add": ["Triple Threat"],
    },
    4: {
        "description": "A real roster forming",
        "unlocks": ["4th match slot"],
        "match_slots_weekly": 4,
    },
    5: {
        "description": "Building a foundation",
        "unlocks": ["Create 1 championship", "Fatal Four Way", "1-on-2 Handicap", "Hire up to 10 wrestlers"],
        "roster_limit": 10, "max_championships": 1,
        "match_types_add": ["Fatal Four Way", "1-on-2 Handicap"],
    },
    7: {
        "description": "Gaining momentum",
        "unlocks": ["Tornado Tag", "Submission Match", "Hire up to 12 wrestlers"],
        "roster_limit": 12,
        "match_types_add": ["Tornado Tag", "Submission Match"],
    },
    9: {
        "description": "Ready to move up",
        "unlocks": ["Hire up to 14 wrestlers"],
        "roster_limit": 14,
    },
    10: {
        "description": "You've outgrown the backyard!",
        "unlocks": ["Extreme Rules", "Iron Man", "6-Man Tag", "5th match slot", "Hire up to 15 wrestlers"],
        "roster_limit": 15,
        "match_slots_weekly": 5, "match_slots_ppv": 5,
        "match_types_add": ["Extreme Rules", "Iron Man", "6-Man Tag"],
    },

    # ===== TIER 2: LOCAL INDIE (Lvl 11-20) =====
    11: {
        "description": "Welcome to the local indie scene!",
        "unlocks": ["Bar & Club venues"],
        "venue_tier_max": 2,
    },
    13: {
        "description": "Building your brand",
        "unlocks": ["Create 2 championships", "Falls Count Anywhere", "I Quit", "Hire up to 18 wrestlers"],
        "roster_limit": 18, "max_championships": 2,
        "match_types_add": ["Falls Count Anywhere", "I Quit"],
    },
    15: {
        "description": "Regulars are packing the bar",
        "unlocks": ["Steel Cage", "Ladder Match", "5-Way Match", "1-on-3 Handicap", "2-on-3 Handicap", "Hire up to 20 wrestlers"],
        "roster_limit": 20,
        "match_types_add": ["Steel Cage", "Ladder Match", "5-Way Match", "1-on-3 Handicap", "2-on-3 Handicap"],
    },
    17: {
        "description": "Promoters are talking about you",
        "unlocks": ["Hire up to 22 wrestlers"],
        "roster_limit": 22,
    },
    18: {
        "description": "Getting serious",
        "unlocks": ["Create 3 championships", "Table Match", "Last Man Standing", "Lumberjack Match"],
        "max_championships": 3,
        "match_types_add": ["Table Match", "Last Man Standing", "Lumberjack Match"],
    },
    20: {
        "description": "Time for a proper venue!",
        "unlocks": ["TLC", "6-Way Match", "Battle Royal", "Special Guest Referee", "PPV Events", "6th match slot", "Hire up to 25 wrestlers"],
        "roster_limit": 25, "match_slots_weekly": 5, "match_slots_ppv": 6,
        "can_run_ppv": True,
        "match_types_add": ["TLC", "6-Way Match", "Battle Royal", "Special Guest Referee"],
    },

    # ===== TIER 3: REGIONAL (Lvl 21-30) =====
    21: {
        "description": "Welcome to the regional scene!",
        "unlocks": ["Community Center venues"],
        "venue_tier_max": 3, "shows_per_week": 2,
    },
    23: {
        "description": "Families are buying tickets",
        "unlocks": ["Hire up to 30 wrestlers"],
        "roster_limit": 30,
    },
    25: {
        "description": "Serious contender",
        "unlocks": ["Create 4 championships", "Hell in a Cell", "8-Man Tag", "3 Stages of Hell", "Brawl", "Hire up to 35 wrestlers"],
        "roster_limit": 35, "max_championships": 4,
        "match_types_add": ["Hell in a Cell", "8-Man Tag", "3 Stages of Hell", "Brawl"],
    },
    27: {
        "description": "Your region knows your name",
        "unlocks": ["Hire up to 38 wrestlers"],
        "roster_limit": 38,
    },
    28: {
        "description": "Major regional force",
        "unlocks": ["8-Way Match", "Casket Match", "Ambulance Match", "Dumpster Match"],
        "match_types_add": ["8-Way Match", "Casket Match", "Ambulance Match", "Dumpster Match"],
    },
    30: {
        "description": "The nation is watching!",
        "unlocks": ["Elimination Chamber", "Gauntlet Eliminator", "MMA Rules", "Kickboxing Rules", "6 match slots", "7 PPV slots", "Hire up to 40 wrestlers"],
        "roster_limit": 40, "match_slots_weekly": 6, "match_slots_ppv": 7,
        "match_types_add": ["Elimination Chamber", "Gauntlet Eliminator", "MMA Rules", "Kickboxing Rules"],
    },

    # ===== TIER 4: NATIONAL (Lvl 31-40) =====
    31: {
        "description": "Welcome to the national stage!",
        "unlocks": ["Theater venues", "TV Deal opportunities"],
        "venue_tier_max": 4, "shows_per_week": 3, "can_get_tv_deal": True,
    },
    33: {
        "description": "The press is covering your shows",
        "unlocks": ["Create 5 championships", "Hire up to 45 wrestlers"],
        "roster_limit": 45, "max_championships": 5,
    },
    35: {
        "description": "Prime time player",
        "unlocks": ["Gauntlet Match", "Inferno Match", "Underground Match", "Bloodline Rules", "8 PPV slots", "Hire up to 50 wrestlers"],
        "roster_limit": 50, "match_slots_ppv": 8,
        "match_types_add": ["Gauntlet Match", "Inferno Match", "Underground Match", "Bloodline Rules"],
    },
    37: {
        "description": "Building an empire",
        "unlocks": ["Hire up to 55 wrestlers"],
        "roster_limit": 55,
    },
    40: {
        "description": "You're a major promotion!",
        "unlocks": ["Create 6 championships", "War Games", "Barbed Wire Deathmatch", "Hire up to 60 wrestlers"],
        "roster_limit": 60, "max_championships": 6,
        "match_slots_weekly": 6, "match_slots_ppv": 8,
        "match_types_add": ["War Games", "Barbed Wire Deathmatch"],
    },

    # ===== TIER 5: MAJOR (Lvl 41-50) =====
    41: {
        "description": "Welcome to arena territory!",
        "unlocks": ["Arena venues"],
        "venue_tier_max": 5, "shows_per_week": 4,
    },
    43: {
        "description": "Arena crowds love your product",
        "unlocks": ["Hire up to 70 wrestlers"],
        "roster_limit": 70,
    },
    45: {
        "description": "Your PPVs are must-see events",
        "unlocks": ["Exploding Barbed Wire", "Landmine Deathmatch", "Hire up to 75 wrestlers"],
        "roster_limit": 75,
        "match_types_add": ["Exploding Barbed Wire", "Landmine Deathmatch"],
    },
    47: {
        "description": "Scouts are watching from overseas",
        "unlocks": ["Create 7 championships", "Hire up to 80 wrestlers"],
        "roster_limit": 80, "max_championships": 7,
    },
    50: {
        "description": "The world is calling!",
        "unlocks": ["Royal Rumble", "Casino Battle Royale", "International touring", "7 match slots", "9 PPV slots", "Hire up to 90 wrestlers"],
        "roster_limit": 90, "match_slots_weekly": 7, "match_slots_ppv": 9,
        "can_tour_international": True,
        "match_types_add": ["Royal Rumble", "Casino Battle Royale"],
    },

    # ===== TIER 6: INTERNATIONAL (Lvl 51-60) =====
    51: {
        "description": "Your brand crosses borders!",
        "unlocks": ["International touring"],
        "shows_per_week": 5,
    },
    53: {
        "description": "International stars want to sign",
        "unlocks": ["Create 8 championships", "Hire up to 100 wrestlers"],
        "roster_limit": 100, "max_championships": 8,
    },
    55: {
        "description": "Multi-language broadcasts",
        "unlocks": ["Hire up to 110 wrestlers"],
        "roster_limit": 110,
    },
    58: {
        "description": "Global streaming deal available",
        "unlocks": ["Create 9 championships", "Hire up to 120 wrestlers"],
        "roster_limit": 120, "max_championships": 9,
    },
    60: {
        "description": "Continental powerhouse!",
        "unlocks": ["Create 10 championships", "10 PPV slots", "Hire up to 130 wrestlers"],
        "roster_limit": 130, "max_championships": 10,
        "match_slots_weekly": 7, "match_slots_ppv": 10,
    },

    # ===== TIER 7: CONTINENTAL (Lvl 61-70) =====
    61: {
        "description": "Large arena territory!",
        "unlocks": ["Large Arena venues", "8 match slots"],
        "venue_tier_max": 6, "shows_per_week": 6, "match_slots_weekly": 8,
    },
    63: {
        "description": "Your brand dominates the continent",
        "unlocks": ["Hire up to 150 wrestlers"],
        "roster_limit": 150,
    },
    65: {
        "description": "Multiple brands possible",
        "unlocks": ["Create 12 championships", "Multi-brand support", "Hire up to 160 wrestlers"],
        "roster_limit": 160, "max_championships": 12, "can_have_brands": True,
    },
    68: {
        "description": "Hall of Fame worthy",
        "unlocks": ["Hire up to 175 wrestlers"],
        "roster_limit": 175,
    },
    70: {
        "description": "Global brand status!",
        "unlocks": ["11 PPV slots", "Hire up to 190 wrestlers"],
        "roster_limit": 190, "match_slots_ppv": 11,
    },

    # ===== TIER 8: GLOBAL (Lvl 71-80) =====
    71: {
        "description": "Welcome to stadium territory!",
        "unlocks": ["Stadium venues", "9 match slots"],
        "venue_tier_max": 7, "match_slots_weekly": 9,
    },
    73: {
        "description": "Your PPVs fill stadiums",
        "unlocks": ["Create 15 championships", "Hire up to 200 wrestlers"],
        "roster_limit": 200, "max_championships": 15,
    },
    75: {
        "description": "You're on every continent",
        "unlocks": ["Hire up to 220 wrestlers"],
        "roster_limit": 220,
    },
    78: {
        "description": "The biggest brand in wrestling",
        "unlocks": ["Hire up to 240 wrestlers"],
        "roster_limit": 240,
    },
    80: {
        "description": "You lead the industry!",
        "unlocks": ["Hall of Fame", "12 PPV slots", "Hire up to 250 wrestlers"],
        "roster_limit": 250, "has_hall_of_fame": True, "match_slots_ppv": 12,
    },

    # ===== TIER 9: INDUSTRY LEADER (Lvl 81-90) =====
    81: {
        "description": "You define professional wrestling",
        "unlocks": ["10 match slots", "Create 18 championships", "Hire up to 275 wrestlers"],
        "roster_limit": 275, "max_championships": 18, "match_slots_weekly": 10, "shows_per_week": 7,
    },
    85: {
        "description": "Competitors follow your blueprint",
        "unlocks": ["Create 20 championships", "Hire up to 300 wrestlers"],
        "roster_limit": 300, "max_championships": 20,
    },
    88: {
        "description": "All-time great status",
        "unlocks": ["Hire up to 350 wrestlers"],
        "roster_limit": 350,
    },
    90: {
        "description": "CEO STATUS!",
        "unlocks": ["14 PPV slots", "Hire up to 400 wrestlers"],
        "roster_limit": 400, "match_slots_ppv": 14,
    },

    # ===== TIER 10: CEO (Lvl 91-100) =====
    91: {
        "description": "You ARE professional wrestling",
        "unlocks": ["Prestige Mode available", "Hire up to 450 wrestlers"],
        "roster_limit": 450, "prestige_mode_available": True,
    },
    95: {
        "description": "Living legend",
        "unlocks": ["Create 25 championships", "Hire up to 500 wrestlers"],
        "roster_limit": 500, "max_championships": 25,
    },
    100: {
        "description": "IMMORTAL STATUS ACHIEVED!",
        "unlocks": ["Unlimited roster", "Unlimited championships", "All content unlocked"],
        "roster_limit": 9999, "max_championships": 99, "all_unlocked": True,
        "match_slots_weekly": 12, "match_slots_ppv": 16, "shows_per_week": 99,
    },
}


def get_level_rewards(level: int) -> Dict:
    return LEVEL_REWARDS.get(level, {})


def get_cumulative_limits(level: int) -> Dict:
    limits = {
        "roster_limit": 5, "shows_per_week": 1, "venue_tier_max": 1,
        "max_championships": 0, "match_slots_weekly": 3, "match_slots_ppv": 3,
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
    match_types = ["Singles", "Intergender Singles", "Tag Team", "Mixed Tag"]
    for lvl in range(1, level + 1):
        rewards = LEVEL_REWARDS.get(lvl, {})
        if "match_types" in rewards:
            match_types = rewards["match_types"]
        if "match_types_add" in rewards:
            for mt in rewards["match_types_add"]:
                if mt not in match_types:
                    match_types.append(mt)
    return match_types


# ==================== XP SOURCES ====================

XP_SOURCES = {
    "show_completed": 50,
    "show_quality_bonus_per_star": 20,
    "show_sellout_bonus": 100,
    "show_attendance_per_500": 8,
    "ppv_completed": 200,
    "ppv_quality_bonus_per_star": 40,
    "ppv_sellout_bonus": 250,
    "five_star_match": 200,
    "four_star_match": 50,
    "four_point_five_star_match": 100,
    "match_of_the_year": 1000,
}

FAN_SOURCES = {
    "show_completed_base": 50,
    "show_per_star_rating": 25,
    "show_sellout_bonus": 100,
    "show_attendance_percentage": 0.05,
    "ppv_completed_base": 200,
    "ppv_per_star_rating": 50,
    "ppv_sellout_bonus": 300,
    "five_star_match": 100,
    "four_star_match": 25,
    "viral_moment_small": 500,
    "viral_moment_medium": 2000,
    "viral_moment_large": 10000,
    "tv_show_per_rating_point": 1000,
    "bad_show_penalty": -50,
    "scandal_penalty": -500,
    "wrestler_walkout_penalty": -100,
}

FAN_SOURCES = {
    "show_completed_base": 50,
    "show_per_star_rating": 25,
    "show_sellout_bonus": 100,
    "show_attendance_percentage": 0.05,
    "ppv_completed_base": 200,
    "ppv_per_star_rating": 50,
    "ppv_sellout_bonus": 300,
    "five_star_match": 100,
    "four_star_match": 25,
    "viral_moment_small": 500,
    "viral_moment_medium": 2000,
    "viral_moment_large": 10000,
    "tv_show_per_rating_point": 1000,
    "bad_show_penalty": -50,
    "scandal_penalty": -500,
    "wrestler_walkout_penalty": -100,
}


def calculate_show_rewards(
    is_ppv: bool, average_match_rating: float, attendance: int,
    capacity: int, venue_prestige: int, five_star_matches: int = 0,
    four_star_matches: int = 0, four_point_five_star_matches: int = 0,
    ticket_price: int = 20, merchandise_modifier: float = 1.0,
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
    result["xp"]["breakdown"].append(f"Quality ({average_match_rating:.1f}★): +{quality_xp}")

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
        result["xp"]["breakdown"].append(f"4★ Matches (x{four_star_matches}): +{four_xp}")

    result["xp"]["total"] = xp

    # Money
    money = 0
    ticket_revenue = attendance * ticket_price
    money += ticket_revenue
    result["money"]["breakdown"].append(f"Tickets ({attendance:,} × ${ticket_price}): +${ticket_revenue:,}")

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
    """Weekly passive - NO XP earned, just fan decay"""
    result = {"xp": 0, "xp_breakdown": [], "fan_change": 0, "fan_breakdown": []}
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
    Achievement(id="first_four_star", name="Great Match", description="Produce a 4+ star match", xp_reward=75, icon="⭐"),
    Achievement(id="first_five_star", name="Five Star Classic", description="Produce a 5-star match", xp_reward=300, fans_reward=200, icon="🌟"),
    Achievement(id="five_star_5", name="Quality Matters", description="Produce 5 five-star matches", xp_reward=500, target=5, icon="🌟"),
    Achievement(id="five_star_10", name="Quality Promotion", description="Produce 10 five-star matches", xp_reward=750, target=10, icon="🌟"),
    Achievement(id="five_star_25", name="Match Factory", description="Produce 25 five-star matches", xp_reward=1500, target=25, icon="✨"),
    Achievement(id="five_star_50", name="Five Star Factory", description="Produce 50 five-star matches", xp_reward=2500, target=50, icon="✨"),
    Achievement(id="five_star_100", name="Century of Classics", description="Produce 100 five-star matches", xp_reward=5000, target=100, icon="💫"),
    Achievement(id="show_average_4star", name="Quality Night", description="Show averages 4+ stars", xp_reward=400, icon="⭐"),
    Achievement(id="show_average_4_5star", name="Legendary Show", description="Show averages 4.5+ stars", xp_reward=750, icon="🌟"),
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
    Achievement(id="money_5000000", name="Multi-Millionaire", description="Have $5,000,000 in the bank", xp_reward=1500, target=5000000, icon="🤑"),
    Achievement(id="roster_5", name="Skeleton Crew", description="Have 5 wrestlers signed", xp_reward=50, target=5, icon="🤼"),
    Achievement(id="roster_10", name="Full Roster", description="Have 10 wrestlers signed", xp_reward=100, target=10, icon="🤼"),
    Achievement(id="roster_25", name="Growing Roster", description="Have 25 wrestlers signed", xp_reward=200, target=25, icon="🤼"),
    Achievement(id="roster_50", name="Deep Roster", description="Have 50 wrestlers signed", xp_reward=400, target=50, icon="🏋️"),
    Achievement(id="roster_100", name="Massive Roster", description="Have 100 wrestlers signed", xp_reward=750, target=100, icon="🏋️"),
    Achievement(id="venue_tier_2", name="Out of the Backyard", description="Run a show at a Bar/Club", xp_reward=100, icon="🍺"),
    Achievement(id="venue_tier_3", name="Community Show", description="Run a show at a Community Center", xp_reward=200, icon="🏛️"),
    Achievement(id="venue_tier_4", name="Theater Debut", description="Run a show at a Theater", xp_reward=400, icon="🎭"),
    Achievement(id="venue_tier_5", name="Arena Show", description="Run a show at an Arena", xp_reward=600, icon="🏟️"),
    Achievement(id="venue_tier_6", name="Large Arena", description="Run a show at a Large Arena", xp_reward=1000, icon="🏟️"),
    Achievement(id="venue_tier_7", name="Stadium Show", description="Run a show at a Stadium", xp_reward=2000, icon="🏟️"),
    Achievement(id="level_10", name="Local Indie", description="Reach Level 10", xp_reward=200, icon="🍺"),
    Achievement(id="level_20", name="Regional Territory", description="Reach Level 20", xp_reward=400, icon="🏛️"),
    Achievement(id="level_30", name="National Promotion", description="Reach Level 30", xp_reward=600, icon="🎭"),
    Achievement(id="level_40", name="Major Promotion", description="Reach Level 40", xp_reward=800, icon="🏟️"),
    Achievement(id="level_50", name="International", description="Reach Level 50", xp_reward=1500, icon="✈️"),
    Achievement(id="level_60", name="Continental Powerhouse", description="Reach Level 60", xp_reward=2000, icon="🌍"),
    Achievement(id="level_70", name="Global Brand", description="Reach Level 70", xp_reward=3000, icon="🌎"),
    Achievement(id="level_80", name="Industry Leader", description="Reach Level 80", xp_reward=5000, icon="👑"),
    Achievement(id="level_90", name="Wrestling Empire CEO", description="Reach Level 90", xp_reward=7500, icon="🏆"),
    Achievement(id="level_100", name="IMMORTAL", description="Reach Level 100", xp_reward=15000, money_reward=1000000, fans_reward=100000, icon="👑"),
    Achievement(id="survive_year_1", name="Survived Year One", description="Complete your first year", xp_reward=500, money_reward=5000, icon="📅"),
    Achievement(id="survive_year_3", name="Three Year Anniversary", description="Run for 3 years", xp_reward=750, money_reward=15000, icon="📅"),
    Achievement(id="survive_year_5", name="Five Year Anniversary", description="Run for 5 years", xp_reward=1000, money_reward=25000, icon="🎂"),
    Achievement(id="survive_year_10", name="Decade of Wrestling", description="Run for 10 years", xp_reward=2500, money_reward=100000, icon="🎂"),
]


# ==================== PROGRESSION SYSTEM CLASS ====================

class ProgressionSystem:
    def __init__(self):
        self.total_xp: int = 0
        self.level: int = 1
        self.promotion_tier: PromotionTier = PromotionTier.BACKYARD

        self.stats: Dict[str, int] = {
            "total_shows": 0, "total_ppvs": 0, "total_tv_shows": 0,
            "sellouts": 0, "total_matches": 0,
            "five_star_matches": 0, "four_star_matches": 0,
            "four_point_five_star_matches": 0,
            "total_attendance": 0, "highest_attendance": 0,
            "wrestlers_signed_total": 0, "wrestlers_released": 0,
            "wrestlers_retired": 0,
            "championships_created": 0, "title_changes": 0, "title_defenses": 0,
            "storylines_started": 0, "storylines_completed": 0,
            "total_revenue": 0, "total_expenses": 0,
            "highest_weekly_profit": 0, "weeks_profitable": 0,
            "weeks_played": 0, "years_played": 0,
            "highest_show_rating": 0, "peak_fans": 0, "peak_budget": 0,
            "peak_roster_size": 0, "unique_venues_used": 0,
            "highest_venue_tier_used": 1,
            "viral_moments": 0, "scandals": 0,
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

        self.xp_log.append({"amount": amount, "source": source, "total": self.total_xp, "level": self.level})
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
            attendance=attendance, capacity=capacity,
            venue_prestige=venue_prestige,
            five_star_matches=five_star_matches,
            four_star_matches=four_star_matches,
            four_point_five_star_matches=four_point_five_star_matches,
            ticket_price=ticket_price,
            merchandise_modifier=merchandise_modifier,
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

        earned_achievements = self.check_achievements(
            fans=total_fans, budget=current_budget,
            roster_size=roster_size, profitable=(weekly_profit > 0),
        )

        result["leveled_up"] = False
        result["new_level"] = self.level
        result["new_unlocks"] = []
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
        elif aid == "first_profit": return context.get("profitable", False)
        elif aid == "first_championship": return stats["championships_created"] >= 1
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
        elif aid == "money_5000000": return context.get("budget", 0) >= 5000000
        elif aid == "roster_5": return context.get("roster_size", 0) >= 5
        elif aid == "roster_10": return context.get("roster_size", 0) >= 10
        elif aid == "roster_25": return context.get("roster_size", 0) >= 25
        elif aid == "roster_50": return context.get("roster_size", 0) >= 50
        elif aid == "roster_100": return context.get("roster_size", 0) >= 100
        elif aid == "venue_tier_2": return context.get("venue_tier", 0) >= 2
        elif aid == "venue_tier_3": return context.get("venue_tier", 0) >= 3
        elif aid == "venue_tier_4": return context.get("venue_tier", 0) >= 4
        elif aid == "venue_tier_5": return context.get("venue_tier", 0) >= 5
        elif aid == "venue_tier_6": return context.get("venue_tier", 0) >= 6
        elif aid == "venue_tier_7": return context.get("venue_tier", 0) >= 7
        elif aid == "level_10": return self.level >= 10
        elif aid == "level_20": return self.level >= 20
        elif aid == "level_30": return self.level >= 30
        elif aid == "level_40": return self.level >= 40
        elif aid == "level_50": return self.level >= 50
        elif aid == "level_60": return self.level >= 60
        elif aid == "level_70": return self.level >= 70
        elif aid == "level_80": return self.level >= 80
        elif aid == "level_90": return self.level >= 90
        elif aid == "level_100": return self.level >= 100
        elif aid == "survive_year_1": return stats["years_played"] >= 1
        elif aid == "survive_year_3": return stats["years_played"] >= 3
        elif aid == "survive_year_5": return stats["years_played"] >= 5
        elif aid == "survive_year_10": return stats["years_played"] >= 10
        return False

    def get_earned_achievements(self) -> List[Achievement]:
        return [a for a in self.achievements if a.is_earned]

    def get_unearned_achievements(self, include_hidden: bool = False) -> List[Achievement]:
        if include_hidden:
            return [a for a in self.achievements if not a.is_earned]
        return [a for a in self.achievements if not a.is_earned and not a.is_hidden]

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
        try:
            system.promotion_tier = PromotionTier(data.get("promotion_tier", 1))
        except (ValueError, KeyError):
            system.promotion_tier = get_promotion_tier(system.level)
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
