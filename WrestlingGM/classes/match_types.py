"""
Match Types and their bonuses
8 Wrestling Styles: Luchador, Powerhouse, Technician, Fighter, Hardcore, Showman, Giant, All Rounder
"""

from classes.enums import WrestlingStyle, MatchType


# Styles that excel in specific match types
MATCH_TYPE_BONUSES = {
    MatchType.IRON_MAN: {
        WrestlingStyle.TECHNICIAN: 1.5,
        WrestlingStyle.ALL_ROUNDER: 1.25,
        WrestlingStyle.FIGHTER: 1.2,
        WrestlingStyle.LUCHADOR: 1.15,
    },
    MatchType.SUBMISSION: {
        WrestlingStyle.TECHNICIAN: 1.5,
        WrestlingStyle.FIGHTER: 1.3,
        WrestlingStyle.POWERHOUSE: 1.1,
    },
    MatchType.LADDER: {
        WrestlingStyle.LUCHADOR: 1.5,
        WrestlingStyle.HARDCORE: 1.25,
        WrestlingStyle.SHOWMAN: 1.15,
        WrestlingStyle.ALL_ROUNDER: 1.1,
    },
    MatchType.DEATHMATCH: {
        WrestlingStyle.HARDCORE: 1.5,
        WrestlingStyle.FIGHTER: 1.3,
        WrestlingStyle.POWERHOUSE: 1.15,
    },
    MatchType.CAGE: {
        WrestlingStyle.FIGHTER: 1.3,
        WrestlingStyle.HARDCORE: 1.25,
        WrestlingStyle.POWERHOUSE: 1.2,
        WrestlingStyle.LUCHADOR: 1.1,
    },
    MatchType.TABLES: {
        WrestlingStyle.HARDCORE: 1.35,
        WrestlingStyle.POWERHOUSE: 1.25,
        WrestlingStyle.FIGHTER: 1.2,
        WrestlingStyle.GIANT: 1.15,
    },
    MatchType.BATTLE_ROYAL: {
        WrestlingStyle.GIANT: 1.5,
        WrestlingStyle.POWERHOUSE: 1.3,
        WrestlingStyle.FIGHTER: 1.2,
        WrestlingStyle.ALL_ROUNDER: 1.15,
        WrestlingStyle.SHOWMAN: 1.1,
    },
    MatchType.LAST_MAN_STANDING: {
        WrestlingStyle.FIGHTER: 1.4,
        WrestlingStyle.HARDCORE: 1.3,
        WrestlingStyle.POWERHOUSE: 1.25,
        WrestlingStyle.GIANT: 1.2,
    },
    MatchType.I_QUIT: {
        WrestlingStyle.TECHNICIAN: 1.5,
        WrestlingStyle.FIGHTER: 1.3,
        WrestlingStyle.HARDCORE: 1.15,
    },
}


def get_match_type_bonus(match_type: MatchType, style: WrestlingStyle) -> float:
    """Get bonus for a style in a specific match type"""
    bonuses = MATCH_TYPE_BONUSES.get(match_type, {})
    return bonuses.get(style, 1.0)
