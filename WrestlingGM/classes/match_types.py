"""
Match Types and their bonuses
"""

from classes.enums import WrestlingStyle, MatchType


# Styles that excel in specific match types
MATCH_TYPE_BONUSES = {
    MatchType.IRON_MAN: {
        WrestlingStyle.TECHNICIAN: 1.4,
        WrestlingStyle.SUBMISSION_ARTIST: 1.3,
        WrestlingStyle.ALL_ROUNDER: 1.2,
        WrestlingStyle.STRONG_STYLE: 1.15,
    },
    MatchType.SUBMISSION: {
        WrestlingStyle.SUBMISSION_ARTIST: 1.5,
        WrestlingStyle.TECHNICIAN: 1.35,
        WrestlingStyle.STRONG_STYLE: 1.15,
    },
    MatchType.LADDER: {
        WrestlingStyle.HIGH_FLYER: 1.4,
        WrestlingStyle.LUCHADOR: 1.35,
        WrestlingStyle.HARDCORE: 1.2,
        WrestlingStyle.ALL_ROUNDER: 1.1,
    },
    MatchType.DEATHMATCH: {
        WrestlingStyle.HARDCORE: 1.5,
        WrestlingStyle.BRAWLER: 1.3,
        WrestlingStyle.STRONG_STYLE: 1.1,
    },
    MatchType.CAGE: {
        WrestlingStyle.BRAWLER: 1.25,
        WrestlingStyle.HARDCORE: 1.2,
        WrestlingStyle.POWERHOUSE: 1.15,
        WrestlingStyle.HIGH_FLYER: 1.1,
    },
    MatchType.TABLES: {
        WrestlingStyle.HARDCORE: 1.3,
        WrestlingStyle.POWERHOUSE: 1.25,
        WrestlingStyle.BRAWLER: 1.2,
    },
    MatchType.BATTLE_ROYAL: {
        WrestlingStyle.POWERHOUSE: 1.3,
        WrestlingStyle.GIANT: 1.4,
        WrestlingStyle.BRAWLER: 1.2,
        WrestlingStyle.ALL_ROUNDER: 1.15,
    },
    MatchType.LAST_MAN_STANDING: {
        WrestlingStyle.BRAWLER: 1.35,
        WrestlingStyle.HARDCORE: 1.3,
        WrestlingStyle.STRONG_STYLE: 1.25,
        WrestlingStyle.POWERHOUSE: 1.2,
    },
    MatchType.I_QUIT: {
        WrestlingStyle.SUBMISSION_ARTIST: 1.5,
        WrestlingStyle.TECHNICIAN: 1.3,
        WrestlingStyle.BRAWLER: 1.15,
    },
}


def get_match_type_bonus(match_type: MatchType, style: WrestlingStyle) -> float:
    """Get bonus for a style in a specific match type"""
    bonuses = MATCH_TYPE_BONUSES.get(match_type, {})
    return bonuses.get(style, 1.0)