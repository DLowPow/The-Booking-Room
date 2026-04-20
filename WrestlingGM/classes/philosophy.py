"""
Philosophy system with detailed perks and modifiers
"""

from classes.enums import Philosophy, WrestlingStyle
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PhilosophyProfile:
    """Contains all modifiers for a philosophy"""
    name: str
    description: str
    starting_budget: int
    
    # Fan modifiers
    starting_fans: int
    fan_loyalty: float          # How sticky fans are (1.0 = normal)
    fan_volatility: float       # How much fans react to bad shows (1.0 = normal)
    fan_growth_rate: float      # How fast you gain fans (1.0 = normal)
    
    # Financial modifiers
    wrestler_salary_modifier: float   # How much wrestlers ask for
    merchandise_modifier: float
    ticket_price_modifier: float
    sponsor_appeal: float             # Ability to get sponsors
    
    # Media modifiers
    tv_appeal: float                  # How attractive to TV networks
    publicity_modifier: float         # Media coverage
    production_cost_modifier: float   # Cost of production
    
    # Wrestling modifiers
    match_time_preference: tuple      # (min, max) preferred match length
    style_bonuses: Dict[WrestlingStyle, float]
    prestige_start: int
    
    # Special perks
    perks: List[str]
    drawbacks: List[str]


PHILOSOPHY_PROFILES = {
    Philosophy.ULTRAVIOLENT: PhilosophyProfile(
        name="Ultraviolent",
        description="Blood, guts, and absolute chaos. Your fans crave violence and you deliver.",
        starting_budget=150000,
        
        # Fans
        starting_fans=500,
        fan_loyalty=1.4,            # Very loyal fanbase
        fan_volatility=0.7,         # Don't leave easily
        fan_growth_rate=0.8,        # Harder to grow mainstream
        
        # Financial
        wrestler_salary_modifier=0.8,   # Wrestlers accept less
        merchandise_modifier=1.1,       # Cult merchandise sells well
        ticket_price_modifier=0.9,      # Cheaper tickets
        sponsor_appeal=0.5,             # Hard to get sponsors
        
        # Media
        tv_appeal=0.4,                  # Networks avoid you
        publicity_modifier=0.6,         # Less mainstream coverage
        production_cost_modifier=0.7,   # Low production needs
        
        # Wrestling
        match_time_preference=(8, 20),
        style_bonuses={
            WrestlingStyle.HARDCORE: 1.4,
            WrestlingStyle.BRAWLER: 1.3,
            WrestlingStyle.POWERHOUSE: 1.15,
            WrestlingStyle.STRONG_STYLE: 1.15,
            WrestlingStyle.HIGH_FLYER: 0.9,
            WrestlingStyle.TECHNICIAN: 0.8,
            WrestlingStyle.SHOWMAN: 0.75,
        },
        prestige_start=35,
        
        perks=[
            "Loyal fanbase rarely abandons you",
            "Wrestlers accept lower pay",
            "Low production costs",
            "Hardcore matches boost ratings significantly",
            "Injury drama creates buzz",
        ],
        drawbacks=[
            "Very difficult to get TV deals",
            "Limited sponsor opportunities",
            "Higher injury rates",
            "Slow fanbase growth",
            "Low mainstream appeal",
        ],
    ),
    
    Philosophy.SPORTS_ENTERTAINMENT: PhilosophyProfile(
        name="Sports Entertainment",
        description="It's all about the spectacle! Big characters, bigger moments, mainstream appeal.",
        starting_budget=500000,
        
        # Fans
        starting_fans=2000,
        fan_loyalty=0.7,            # Fickle fans
        fan_volatility=1.4,         # React strongly to bad shows
        fan_growth_rate=1.3,        # Can grow fast
        
        # Financial
        wrestler_salary_modifier=1.4,   # Wrestlers want more money
        merchandise_modifier=1.5,       # Merch sells great
        ticket_price_modifier=1.3,      # Premium tickets
        sponsor_appeal=1.5,             # Sponsors love you
        
        # Media
        tv_appeal=1.5,                  # Networks want you
        publicity_modifier=1.4,         # Lots of coverage
        production_cost_modifier=1.5,   # Expensive production
        
        # Wrestling
        match_time_preference=(10, 25),
        style_bonuses={
            WrestlingStyle.SHOWMAN: 1.4,
            WrestlingStyle.POWERHOUSE: 1.25,
            WrestlingStyle.GIANT: 1.25,
            WrestlingStyle.ALL_ROUNDER: 1.15,
            WrestlingStyle.TECHNICIAN: 0.85,
            WrestlingStyle.STRONG_STYLE: 0.8,
            WrestlingStyle.HARDCORE: 0.7,
        },
        prestige_start=50,
        
        perks=[
            "High starting budget",
            "Easy to get TV deals",
            "Excellent merchandise sales",
            "Sponsors eager to partner",
            "Fast fanbase growth potential",
            "Mainstream media coverage",
        ],
        drawbacks=[
            "Fans are volatile and fickle",
            "Wrestlers demand high salaries",
            "Expensive production costs",
            "Bad shows hurt you more",
            "Workrate-focused matches underperform",
        ],
    ),
    
    Philosophy.STRONGSTYLE: PhilosophyProfile(
        name="Strong Style",
        description="In-ring excellence above all. Technical mastery and athletic competition.",
        starting_budget=300000,
        
        # Fans
        starting_fans=1000,
        fan_loyalty=1.1,            # Appreciative fans
        fan_volatility=1.0,         # Normal reactions
        fan_growth_rate=1.0,        # Steady growth
        
        # Financial
        wrestler_salary_modifier=1.0,   # Standard pay
        merchandise_modifier=1.0,
        ticket_price_modifier=1.1,
        sponsor_appeal=1.0,
        
        # Media
        tv_appeal=1.0,
        publicity_modifier=0.9,         # Less mainstream buzz
        production_cost_modifier=0.9,   # Don't need flashy production
        
        # Wrestling
        match_time_preference=(12, 35),
        style_bonuses={
            WrestlingStyle.TECHNICIAN: 1.35,
            WrestlingStyle.STRONG_STYLE: 1.3,
            WrestlingStyle.SUBMISSION_ARTIST: 1.25,
            WrestlingStyle.HIGH_FLYER: 1.2,
            WrestlingStyle.ALL_ROUNDER: 1.15,
            WrestlingStyle.SHOWMAN: 0.85,
            WrestlingStyle.GIANT: 0.9,
        },
        prestige_start=60,
        
        perks=[
            "High starting prestige",
            "Balanced across all areas",
            "Great matches boost reputation significantly",
            "Respected by wrestling purists",
            "Wrestlers want to work for you",
            "Lower production costs",
        ],
        drawbacks=[
            "Less mainstream appeal",
            "Slower merchandise growth",
            "Need consistently good matches",
            "Character-driven wrestlers underperform",
        ],
    ),
    
    Philosophy.LUCHA: PhilosophyProfile(
        name="Lucha Libre",
        description="High-flying action, colorful masks, family traditions, and cultural pride.",
        starting_budget=250000,
        
        # Fans
        starting_fans=1500,
        fan_loyalty=1.2,            # Cultural connection
        fan_volatility=0.9,
        fan_growth_rate=1.1,
        
        # Financial
        wrestler_salary_modifier=0.9,   # Honor to work lucha
        merchandise_modifier=1.3,       # Masks sell great!
        ticket_price_modifier=1.0,
        sponsor_appeal=1.1,             # Cultural sponsors
        
        # Media
        tv_appeal=1.1,
        publicity_modifier=1.0,
        production_cost_modifier=0.85,  # Traditional production
        
        # Wrestling
        match_time_preference=(8, 22),
        style_bonuses={
            WrestlingStyle.LUCHADOR: 1.5,
            WrestlingStyle.HIGH_FLYER: 1.35,
            WrestlingStyle.TECHNICIAN: 1.15,
            WrestlingStyle.ALL_ROUNDER: 1.1,
            WrestlingStyle.GIANT: 0.85,
            WrestlingStyle.HARDCORE: 0.75,
            WrestlingStyle.BRAWLER: 0.8,
        },
        prestige_start=50,
        
        perks=[
            "Excellent mask merchandise sales",
            "Strong cultural fanbase",
            "Multi-generational appeal",
            "Tag team and trios matches shine",
            "Lower production costs",
            "Loyal wrestlers",
        ],
        drawbacks=[
            "Hardcore matches hurt reputation",
            "Power-based wrestlers struggle",
            "Limited appeal outside lucha markets",
            "Need luchador talent to succeed",
        ],
    ),
}


def get_philosophy_profile(philosophy: Philosophy) -> PhilosophyProfile:
    """Get the full profile for a philosophy"""
    return PHILOSOPHY_PROFILES.get(philosophy)


def get_style_modifier(philosophy: Philosophy, style: WrestlingStyle) -> float:
    """Returns multiplier for wrestler style under given philosophy"""
    profile = PHILOSOPHY_PROFILES.get(philosophy)
    if profile:
        return profile.style_bonuses.get(style, 1.0)
    return 1.0


def get_starting_budget(philosophy: Philosophy) -> int:
    """Get starting budget for a philosophy"""
    profile = PHILOSOPHY_PROFILES.get(philosophy)
    return profile.starting_budget if profile else 300000


def display_philosophy_info(philosophy: Philosophy) -> str:
    """Get formatted display string for a philosophy"""
    profile = get_philosophy_profile(philosophy)
    if not profile:
        return "Unknown philosophy"
    
    lines = [
        f"\n{'='*50}",
        f"📋 {profile.name.upper()}",
        f"{'='*50}",
        f"\n{profile.description}\n",
        f"💰 Starting Budget: ${profile.starting_budget:,}",
        f"👥 Starting Fans: {profile.starting_fans:,}",
        f"📊 Starting Prestige: {profile.prestige_start}",
        f"\n✅ PERKS:",
    ]
    
    for perk in profile.perks:
        lines.append(f"   • {perk}")
    
    lines.append(f"\n❌ DRAWBACKS:")
    for drawback in profile.drawbacks:
        lines.append(f"   • {drawback}")
    
    return "\n".join(lines)
