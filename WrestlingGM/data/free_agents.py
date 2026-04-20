"""
Free Agents - Tiered roster generation system
"""

import random
from typing import List, Optional, Dict
from classes.wrestler import Wrestler
from classes.enums import Gender, WrestlingStyle, Alignment


FIRST_NAMES_MALE = [
    "Adam", "Alex", "Austin", "Billy", "Bobby", "Brad",
]

FIRST_NAMES_FEMALE = [
    "Aaliyah", "Abby", "Alexa", "Alicia", "Amanda",
]

LAST_NAMES = [
    "Adams", "Alexander", "Alvarez", "Anderson",
]


def generate_free_agents(count: int = 50, level: int = 1) -> List[Wrestler]:
    """Placeholder"""
    return []


def generate_all_free_agents() -> Dict[int, List[Wrestler]]:
    """Placeholder"""
    return {1: [], 2: [], 3: [], 4: [], 5: []}


def get_tier_for_level(level: int) -> int:
    return 1


def generate_wrestler_for_tier(tier, gender=None, used_names=None):
    return None


TIER_CONFIG = {
    1: {"name": "Rookies", "level_required": 1, "salary_range": (100, 300), "stat_range": (25, 50)},
    2: {"name": "Indie", "level_required": 5, "salary_range": (250, 600), "stat_range": (35, 60)},
    3: {"name": "Rising", "level_required": 10, "salary_range": (500, 1200), "stat_range": (45, 75)},
    4: {"name": "Veterans", "level_required": 20, "salary_range": (1000, 3000), "stat_range": (60, 85)},
    5: {"name": "Main Event", "level_required": 35, "salary_range": (2500, 8000), "stat_range": (75, 98)},
}
