"""
Wrestling Styles Configuration
Defines stat bonuses and characteristics for each style
"""

from classes.enums import WrestlingStyle


# Stat bonuses for each style
STYLE_STAT_BONUSES = {
    WrestlingStyle.LUCHADOR: {
        "aerial": 25,
        "speed": 20,
        "power": -15,
        "technical": 5,
    },
    WrestlingStyle.POWERHOUSE: {
        "power": 25,
        "speed": -10,
        "aerial": -15,
        "stamina": 10,
    },
    WrestlingStyle.TECHNICIAN: {
        "technical": 25,
        "stamina": 15,
        "aerial": -5,
        "hardcore": -10,
    },
    WrestlingStyle.FIGHTER: {
        "power": 15,
        "hardcore": 15,
        "technical": 5,
        "speed": -5,
    },
    WrestlingStyle.HARDCORE: {
        "hardcore": 25,
        "stamina": 10,
        "speed": -5,
        "technical": -10,
    },
    WrestlingStyle.SHOWMAN: {
        "charisma": 25,
        "technical": -5,
        "hardcore": -10,
    },
    WrestlingStyle.GIANT: {
        "power": 25,
        "speed": -20,
        "aerial": -25,
        "stamina": 10,
    },
    WrestlingStyle.ALL_ROUNDER: {},
}


# Style descriptions for the UI
STYLE_DESCRIPTIONS = {
    WrestlingStyle.LUCHADOR: "High-flying aerial specialist with masks and traditions",
    WrestlingStyle.POWERHOUSE: "Pure strength and power-based offense",
    WrestlingStyle.TECHNICIAN: "Mat-based wrestling with submissions and chain wrestling",
    WrestlingStyle.FIGHTER: "MMA-influenced striker with grappling skills",
    WrestlingStyle.HARDCORE: "Weapons, blood, and extreme violence specialist",
    WrestlingStyle.SHOWMAN: "Charisma-driven entertainer who connects with fans",
    WrestlingStyle.GIANT: "Massive size used to dominate opponents",
    WrestlingStyle.ALL_ROUNDER: "Versatile wrestler who can do a bit of everything",
}


# Match type bonuses for each style
STYLE_MATCH_BONUSES = {
    WrestlingStyle.LUCHADOR: {
        "Ladder": 1.5, "TLC": 1.4, "Tag Team": 1.3, "6-Man Tag": 1.4,
    },
    WrestlingStyle.POWERHOUSE: {
        "Standard": 1.2, "Cage": 1.3, "Last Man Standing": 1.4,
    },
    WrestlingStyle.TECHNICIAN: {
        "Submission": 1.5, "Iron Man": 1.4, "I Quit": 1.4, "Standard": 1.2,
    },
    WrestlingStyle.FIGHTER: {
        "Submission": 1.3, "I Quit": 1.3, "Cage": 1.3, "Standard": 1.2,
    },
    WrestlingStyle.HARDCORE: {
        "Hardcore": 1.5, "Deathmatch": 1.5, "Tables": 1.4, "TLC": 1.3,
        "Inferno": 1.4, "Buried Alive": 1.4,
    },
    WrestlingStyle.SHOWMAN: {
        "Royal Rumble": 1.3, "Battle Royal": 1.3, "Standard": 1.2,
    },
    WrestlingStyle.GIANT: {
        "Last Man Standing": 1.5, "Battle Royal": 1.4, "Royal Rumble": 1.4,
        "Cage": 1.3,
    },
    WrestlingStyle.ALL_ROUNDER: {},
}


def get_style_bonuses(style):
    """Get stat bonuses for a wrestling style"""
    return STYLE_STAT_BONUSES.get(style, {})


def get_style_description(style):
    """Get description for a wrestling style"""
    return STYLE_DESCRIPTIONS.get(style, "Unknown style")


def get_match_bonus(style, match_type):
    """Get match type bonus for a style"""
    bonuses = STYLE_MATCH_BONUSES.get(style, {})
    return bonuses.get(match_type, 1.0)