"""
Wrestling Style Profiles - Perks and Drawbacks per style
"""

from classes.enums import WrestlingStyle
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StyleProfile:
    """Detailed profile for each wrestling style"""
    name: str
    description: str
    icon: str
    
    # Stat preferences (what stats matter most)
    primary_stats: List[str] = field(default_factory=list)
    weak_stats: List[str] = field(default_factory=list)
    
    # Match type bonuses
    match_bonuses: Dict[str, float] = field(default_factory=dict)
    match_penalties: Dict[str, float] = field(default_factory=dict)
    
    # Style chemistry
    great_against: List[str] = field(default_factory=list)
    poor_against: List[str] = field(default_factory=list)
    
    # Perks and drawbacks
    perks: List[str] = field(default_factory=list)
    drawbacks: List[str] = field(default_factory=list)


STYLE_PROFILES = {
    WrestlingStyle.LUCHADOR: StyleProfile(
        name="Luchador",
        description="High-flying aerial specialists. Masters of ropes and ladders.",
        icon="🦅",
        primary_stats=["Aerial", "Speed", "Charisma"],
        weak_stats=["Power", "Hardcore"],
        match_bonuses={
            "Ladder": 1.4,
            "TLC": 1.3,
            "Tag Team": 1.2,
            "6-Man Tag": 1.25,
            "Triple Threat": 1.15,
        },
        match_penalties={
            "Iron Man": 0.85,
            "Submission": 0.8,
            "Hell in a Cell": 0.9,
            "Last Man Standing": 0.85,
        },
        great_against=["Giant", "Powerhouse"],
        poor_against=["Luchador"],
        perks=[
            "Excels in ladder and high-spot matches",
            "Strong tag team chemistry",
            "Crowd loves the high-flying spots",
            "David vs Goliath bonus against Giants",
            "Fast-paced matches keep crowd engaged",
            "Lower salary expectations early career",
        ],
        drawbacks=[
            "Higher injury risk from aerial moves",
            "Struggles in slow-paced submission matches",
            "Less effective against equally agile opponents",
            "Smaller frame limits power offense",
            "May lose credibility against larger opponents",
        ],
    ),
    
    WrestlingStyle.POWERHOUSE: StyleProfile(
        name="Powerhouse",
        description="Strong, dominating wrestlers who throw bodies around.",
        icon="💪",
        primary_stats=["Power", "Stamina", "Charisma"],
        weak_stats=["Speed", "Aerial"],
        match_bonuses={
            "Standard": 1.15,
            "Last Man Standing": 1.3,
            "Cage": 1.25,
            "Tables": 1.3,
            "Battle Royal": 1.3,
            "War Games": 1.25,
        },
        match_penalties={
            "Ladder": 0.85,
            "Iron Man": 0.9,
            "TLC": 0.85,
        },
        great_against=["Luchador", "Technician"],
        poor_against=["Giant"],
        perks=[
            "Dominates with impactful power moves",
            "Strong in brawling and weapon matches",
            "Intimidating presence boosts crowd reactions",
            "Excellent in Battle Royals and War Games",
            "Hard to lift means hard to put away",
            "Believable as a top star",
        ],
        drawbacks=[
            "Slower pace can lose audience attention",
            "Struggles with high-flying opponents",
            "Limited move set in long matches",
            "Higher salary demands as they grow",
            "Stamina becomes issue in longer matches",
        ],
    ),
    
    WrestlingStyle.TECHNICIAN: StyleProfile(
        name="Technician",
        description="Mat wrestling masters who win with submissions and chain wrestling.",
        icon="🔧",
        primary_stats=["Technical", "Stamina", "Speed"],
        weak_stats=["Hardcore", "Power"],
        match_bonuses={
            "Iron Man": 1.5,
            "Submission": 1.5,
            "I Quit": 1.4,
            "Standard": 1.2,
        },
        match_penalties={
            "Hardcore": 0.7,
            "Deathmatch": 0.6,
            "Tables": 0.8,
            "TLC": 0.8,
            "Ladder": 0.85,
        },
        great_against=["Powerhouse", "Brawler"],
        poor_against=["Showman"],
        perks=[
            "Mastery of Iron Man and Submission matches",
            "Long matches showcase their skills",
            "Respected by smart wrestling fans",
            "High consistency in match quality",
            "Great chemistry with most opponents",
            "Builds prestige for the promotion",
        ],
        drawbacks=[
            "Struggles in hardcore environments",
            "Less crowd reaction without character work",
            "Power-based opponents can overwhelm them",
            "Slower matches don't suit casual fans",
            "Limited in spectacle-driven shows",
        ],
    ),
    
    WrestlingStyle.FIGHTER: StyleProfile(
        name="Fighter",
        description="Striking specialists with MMA backgrounds. Hard hitters and grapplers.",
        icon="👊",
        primary_stats=["Power", "Technical", "Stamina"],
        weak_stats=["Aerial", "Charisma"],
        match_bonuses={
            "Standard": 1.2,
            "Submission": 1.3,
            "Last Man Standing": 1.35,
            "I Quit": 1.3,
            "Cage": 1.25,
            "Hardcore": 1.15,
        },
        match_penalties={
            "Ladder": 0.8,
            "TLC": 0.8,
            "Iron Man": 0.9,
        },
        great_against=["Showman", "Luchador"],
        poor_against=["Hardcore"],
        perks=[
            "Stiff strikes look devastating",
            "Versatile in many match types",
            "Believable as a legitimate threat",
            "Strong in fight-based stipulations",
            "Realistic style appeals to MMA fans",
            "Can transition between styles",
        ],
        drawbacks=[
            "Less spectacular than other styles",
            "Charisma often takes a back seat",
            "Can injure opponents with stiff style",
            "Not ideal for ladder/spot matches",
            "Some fans find style too slow",
        ],
    ),
    
    WrestlingStyle.HARDCORE: StyleProfile(
        name="Hardcore",
        description="Extreme wrestlers who thrive in violence, weapons, and blood.",
        icon="🩸",
        primary_stats=["Hardcore", "Stamina", "Charisma"],
        weak_stats=["Technical", "Aerial"],
        match_bonuses={
            "Hardcore": 1.5,
            "Deathmatch": 1.6,
            "Tables": 1.4,
            "TLC": 1.3,
            "Last Man Standing": 1.35,
            "Inferno": 1.4,
            "Buried Alive": 1.4,
        },
        match_penalties={
            "Iron Man": 0.6,
            "Submission": 0.7,
            "Standard": 0.85,
        },
        great_against=["Fighter", "Brawler"],
        poor_against=["Technician"],
        perks=[
            "Dominates all hardcore stipulations",
            "Crowds go wild for extreme spots",
            "Cult following develops quickly",
            "Higher fan loyalty in indie scene",
            "Major bonus in Ultraviolent promotions",
            "Memorable career-defining matches",
        ],
        drawbacks=[
            "Higher injury rates and shorter careers",
            "Limited in mainstream/family-friendly events",
            "Struggles in technical or submission matches",
            "Sponsor companies avoid these wrestlers",
            "Cannot compete in TV-friendly stipulations",
        ],
    ),
    
    WrestlingStyle.SHOWMAN: StyleProfile(
        name="Showman",
        description="Larger-than-life characters who connect with the crowd.",
        icon="🎤",
        primary_stats=["Charisma", "Speed", "All-Around"],
        weak_stats=["Technical"],
        match_bonuses={
            "Standard": 1.25,
            "Triple Threat": 1.3,
            "Battle Royal": 1.3,
            "Royal Rumble": 1.4,
        },
        match_penalties={
            "Submission": 0.8,
            "Iron Man": 0.85,
            "I Quit": 0.85,
        },
        great_against=["Technician", "Fighter"],
        poor_against=["Hardcore"],
        perks=[
            "Massive crowd reactions",
            "Sells huge merchandise",
            "Can carry weak opponents",
            "Boosts attendance significantly",
            "Perfect for Sports Entertainment",
            "Drives fan engagement and growth",
        ],
        drawbacks=[
            "Match quality often lower than other styles",
            "Demands more money quickly",
            "Higher ego potential",
            "Workrate fans may dismiss them",
            "Can't carry technical or hardcore matches",
        ],
    ),
    
    WrestlingStyle.GIANT: StyleProfile(
        name="Giant",
        description="Massive wrestlers who use their size to dominate.",
        icon="🗿",
        primary_stats=["Power", "Charisma"],
        weak_stats=["Speed", "Stamina", "Aerial", "Technical"],
        match_bonuses={
            "Battle Royal": 1.5,
            "Royal Rumble": 1.4,
            "Standard": 1.15,
            "Last Man Standing": 1.3,
            "Tables": 1.3,
        },
        match_penalties={
            "Iron Man": 0.5,
            "Submission": 0.7,
            "Ladder": 0.7,
            "TLC": 0.7,
            "Triple Threat": 0.85,
        },
        great_against=["Luchador", "Showman"],
        poor_against=["Giant"],
        perks=[
            "Towering presence draws fans in",
            "Dominates Battle Royals and Royal Rumbles",
            "Spectacular matches against smaller opponents",
            "Believable as an unstoppable force",
            "Can be massive draw with right booking",
            "Memorable for their pure size",
        ],
        drawbacks=[
            "Limited match length due to stamina",
            "Cannot perform aerial or fast-paced spots",
            "Struggles in technical wrestling",
            "Higher injury risk to body and joints",
            "Match quality drops in long matches",
            "Demands top-tier salary quickly",
        ],
    ),
    
    WrestlingStyle.ALL_ROUNDER: StyleProfile(
        name="All Rounder",
        description="Versatile wrestlers who can do a bit of everything.",
        icon="⚡",
        primary_stats=["Balanced"],
        weak_stats=[],
        match_bonuses={
            "Standard": 1.1,
            "Triple Threat": 1.15,
            "Fatal Four Way": 1.15,
            "Ladder": 1.1,
            "Tag Team": 1.1,
        },
        match_penalties={},
        great_against=[],
        poor_against=[],
        perks=[
            "Adaptable to any match type",
            "Good chemistry with all styles",
            "Reliable performer in any situation",
            "Can fill any role on the card",
            "Solid match quality consistently",
            "Backup for almost any booking",
        ],
        drawbacks=[
            "Master of none - no specialty bonuses",
            "Less memorable than specialists",
            "Doesn't excel in any single match type",
            "Average ratings instead of elite",
            "Harder to push as a top star",
        ],
    ),
}


def get_style_profile(style: WrestlingStyle) -> StyleProfile:
    """Get the profile for a wrestling style"""
    return STYLE_PROFILES.get(style)


def get_all_styles() -> list:
    """Get list of all styles for display"""
    return [
        {
            "value": style.value,
            "name": profile.name,
            "icon": profile.icon,
            "description": profile.description,
            "perks": profile.perks,
            "drawbacks": profile.drawbacks,
        }
        for style, profile in STYLE_PROFILES.items()
    ]