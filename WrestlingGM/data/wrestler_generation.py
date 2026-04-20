"""
Wrestler Generator
Main generator for free agents and wrestlers
"""

import random
from typing import List, Optional, Dict
from classes.wrestler import Wrestler
from classes.enums import Gender, WrestlingStyle, Alignment
from data.wrestler_names import (
    FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES,
    NICKNAMES_BY_TIER, HOMETOWNS, FINISHER_NAMES, SIGNATURE_MOVES
)
from data.wrestling_styles import get_style_bonuses
from data.wrestler_weights import get_physical_attributes


# ==================== TIER DEFINITIONS ====================

TIER_CONFIG = {
    1: {
        "name": "Rookies and Local Talent",
        "level_required": 1,
        "stat_range": (25, 50),
        "popularity_range": (5, 25),
        "salary_range": (100, 300),
        "age_range": (18, 25),
        "consistency_range": (30, 60),
        "trait_chance": 0.1,
        "max_traits": 1,
        "count_male": 25,
        "count_female": 25,
    },
    2: {
        "name": "Independent Circuit",
        "level_required": 5,
        "stat_range": (35, 60),
        "popularity_range": (15, 40),
        "salary_range": (250, 600),
        "age_range": (21, 30),
        "consistency_range": (40, 70),
        "trait_chance": 0.2,
        "max_traits": 1,
        "count_male": 25,
        "count_female": 25,
    },
    3: {
        "name": "Rising Stars",
        "level_required": 10,
        "stat_range": (45, 75),
        "popularity_range": (30, 55),
        "salary_range": (500, 1200),
        "age_range": (23, 33),
        "consistency_range": (50, 80),
        "trait_chance": 0.4,
        "max_traits": 2,
        "count_male": 20,
        "count_female": 20,
    },
    4: {
        "name": "Established Veterans",
        "level_required": 20,
        "stat_range": (60, 85),
        "popularity_range": (50, 75),
        "salary_range": (1000, 3000),
        "age_range": (26, 38),
        "consistency_range": (60, 90),
        "trait_chance": 0.6,
        "max_traits": 2,
        "count_male": 20,
        "count_female": 20,
    },
    5: {
        "name": "Main Event Stars",
        "level_required": 35,
        "stat_range": (75, 98),
        "popularity_range": (70, 95),
        "salary_range": (2500, 8000),
        "age_range": (28, 42),
        "consistency_range": (75, 95),
        "trait_chance": 0.8,
        "max_traits": 3,
        "count_male": 10,
        "count_female": 10,
    },
}


TRAITS_BY_TIER = {
    1: ["underdog"],
    2: ["underdog", "tag_specialist", "spot_monkey"],
    3: ["spot_monkey", "tag_specialist", "submission_specialist",
        "hardcore_legend", "giant_killer"],
    4: ["ring_general", "submission_specialist", "hardcore_legend",
        "giant_killer", "iron_man", "veteran_presence", "natural_talent"],
    5: ["ring_general", "iron_man", "showstopper", "natural_talent",
        "veteran_presence", "ladder_match_expert", "deathmatch_king"],
}


# ==================== HELPER FUNCTIONS ====================

def _generate_stat(stat_range, style_bonus=0):
    """Generate a stat within range with optional style bonus"""
    base = random.randint(stat_range[0], stat_range[1])
    return max(1, min(100, base + style_bonus))


def _generate_unique_name(gender, used_names):
    """Generate a unique wrestler name"""
    first = ""
    last = ""
    for _ in range(100):
        if gender == Gender.MALE:
            first = random.choice(FIRST_NAMES_MALE)
        else:
            first = random.choice(FIRST_NAMES_FEMALE)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        if name not in used_names:
            return name
    return f"{first} {last} Jr."


# ==================== MAIN GENERATOR ====================

def generate_wrestler_for_tier(tier, gender=None, used_names=None):
    """Generate a wrestler for a specific tier"""
    config = TIER_CONFIG.get(tier, TIER_CONFIG[1])
    if used_names is None:
        used_names = set()

    if gender is None:
        gender = random.choice([Gender.MALE, Gender.FEMALE])

    name = _generate_unique_name(gender, used_names)
    used_names.add(name)

    tier_nicknames = NICKNAMES_BY_TIER.get(tier, [None])
    nickname = random.choice(tier_nicknames)

    age = random.randint(config["age_range"][0], config["age_range"][1])
    style = random.choice(list(WrestlingStyle))

    # Get physical attributes based on style and gender
    physical = get_physical_attributes(style, gender)
    height = physical["height"]
    weight = physical["weight"]

    # Secondary style
    secondary_style = None
    if random.random() < (tier * 0.15):
        secondary_style = random.choice(list(WrestlingStyle))
        if secondary_style == style:
            secondary_style = None

    alignment = random.choice(list(Alignment))

    # Generate stats with style bonuses
    stat_range = config["stat_range"]
    style_bonuses = get_style_bonuses(style)

    power = _generate_stat(stat_range, style_bonuses.get("power", 0))
    speed = _generate_stat(stat_range, style_bonuses.get("speed", 0))
    technical = _generate_stat(stat_range, style_bonuses.get("technical", 0))
    stamina = _generate_stat(stat_range, style_bonuses.get("stamina", 0))
    charisma = _generate_stat(stat_range, style_bonuses.get("charisma", 0))
    hardcore = _generate_stat(stat_range, style_bonuses.get("hardcore", 0))
    aerial = _generate_stat(stat_range, style_bonuses.get("aerial", 0))

    # Hidden stats
    consistency = random.randint(
        config["consistency_range"][0],
        config["consistency_range"][1]
    )
    work_ethic = random.randint(30 + (tier * 8), 60 + (tier * 8))
    loyalty = random.randint(30, 90)
    ego = random.randint(max(10, 20 + (tier * 8)), min(100, 40 + (tier * 12)))
    professionalism = random.randint(30 + (tier * 5), 60 + (tier * 8))

    popularity = random.randint(
        config["popularity_range"][0],
        config["popularity_range"][1]
    )

    salary = random.randint(
        config["salary_range"][0],
        config["salary_range"][1]
    )

    # Traits
    traits = []
    if random.random() < config["trait_chance"]:
        available_traits = TRAITS_BY_TIER.get(tier, [])
        if available_traits:
            num_traits = random.randint(1, config["max_traits"])
            num_traits = min(num_traits, len(available_traits))
            traits = random.sample(available_traits, num_traits)

    num_sigs = min(tier, 4)
    signatures = random.sample(SIGNATURE_MOVES, num_sigs)

    injury_prone = random.randint(20 + (tier * 3), 40 + (tier * 8))

    wrestler = Wrestler(
        name=name,
        nickname=nickname,
        age=age,
        gender=gender,
        hometown=random.choice(HOMETOWNS),
        height=height,
        weight=weight,
        primary_style=style,
        secondary_style=secondary_style,
        alignment=alignment,
        power=power,
        speed=speed,
        technical=technical,
        stamina=stamina,
        charisma=charisma,
        hardcore=hardcore,
        aerial=aerial,
        consistency=consistency,
        work_ethic=work_ethic,
        loyalty=loyalty,
        ego=ego,
        professionalism=professionalism,
        popularity=popularity,
        momentum=50,
        morale=70,
        injury_prone=injury_prone,
        salary=salary,
        unique_traits=traits,
        finisher_name=random.choice(FINISHER_NAMES),
        signature_moves=signatures,
    )

    wrestler.is_signed = False
    wrestler.contract_length = 0

    if tier >= 3:
        wrestler.wins = random.randint(50 * (tier - 2), 150 * (tier - 2))
        wrestler.losses = random.randint(20 * (tier - 2), 80 * (tier - 2))
    if tier >= 4:
        wrestler.titles_held = random.randint(1, tier * 2)

    return wrestler


# ==================== POOL GENERATORS ====================

def generate_all_free_agents():
    """Generate the complete free agent pool. Returns dict by tier."""
    all_agents = {}
    used_names = set()

    for tier in range(1, 6):
        config = TIER_CONFIG[tier]
        tier_agents = []

        for _ in range(config["count_male"]):
            wrestler = generate_wrestler_for_tier(tier, Gender.MALE, used_names)
            tier_agents.append(wrestler)

        for _ in range(config["count_female"]):
            wrestler = generate_wrestler_for_tier(tier, Gender.FEMALE, used_names)
            tier_agents.append(wrestler)

        random.shuffle(tier_agents)
        all_agents[tier] = tier_agents

    return all_agents


def generate_free_agents(count=50, level=1):
    """Generate free agents appropriate for the player level."""
    all_agents = generate_all_free_agents()
    available = []
    for tier, agents in all_agents.items():
        tier_config = TIER_CONFIG[tier]
        if level >= tier_config["level_required"]:
            available.extend(agents)
    if len(available) > count:
        return random.sample(available, count)
    return available


def get_free_agents_for_level(level):
    """Get free agents organized by tier for a specific level."""
    all_agents = generate_all_free_agents()
    result = []
    for tier in range(1, 6):
        config = TIER_CONFIG[tier]
        is_unlocked = level >= config["level_required"]
        result.append({
            "tier": tier,
            "name": config["name"],
            "level_required": config["level_required"],
            "is_unlocked": is_unlocked,
            "wrestlers": all_agents.get(tier, []) if is_unlocked else [],
            "count": len(all_agents.get(tier, [])),
            "salary_range": config["salary_range"],
            "stat_range": config["stat_range"],
        })
    return result


def get_tier_for_level(level):
    """Get the highest tier available at a given level."""
    highest = 1
    for tier, config in TIER_CONFIG.items():
        if level >= config["level_required"]:
            highest = tier
    return highest


def generate_legend(name=""):
    """Generate a legendary wrestler (Tier 5+)"""
    used_names = set()
    wrestler = generate_wrestler_for_tier(5, Gender.MALE, used_names)
    if name:
        wrestler.name = name
    wrestler.age = random.randint(38, 55)
    wrestler.popularity = random.randint(85, 99)
    wrestler.wins = random.randint(500, 2000)
    wrestler.losses = random.randint(100, 500)
    wrestler.titles_held = random.randint(5, 25)
    wrestler.five_star_matches = random.randint(5, 30)
    wrestler.salary = random.randint(5000, 15000)
    return wrestler


def refresh_free_agent_pool(current_agents, level, max_agents=200):
    """Refresh the free agent pool."""
    if len(current_agents) > 20:
        num_to_remove = random.randint(3, 8)
        for _ in range(num_to_remove):
            if current_agents:
                current_agents.pop(random.randint(0, len(current_agents) - 1))

    highest_tier = get_tier_for_level(level)
    used_names = {w.name for w in current_agents}

    num_to_add = random.randint(3, 8)
    for _ in range(num_to_add):
        if len(current_agents) >= max_agents:
            break

        tier_weights = {1: 40, 2: 30, 3: 20, 4: 8, 5: 2}
        available_tiers = [t for t in range(1, highest_tier + 1)]
        weights = [tier_weights.get(t, 10) for t in available_tiers]
        tier = random.choices(available_tiers, weights=weights, k=1)[0]

        gender = random.choice([Gender.MALE, Gender.FEMALE])
        wrestler = generate_wrestler_for_tier(tier, gender, used_names)
        current_agents.append(wrestler)
        used_names.add(wrestler.name)

    return current_agents