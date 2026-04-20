"""
Philosophy system with detailed perks and modifiers
Based on real wrestling promotions:
- Ultraviolent: CZW, ECW, GCW
- Strong Style: NJPW, NOAH, Progress, Indie
- Sports Entertainment: AEW, WWE, TNA, WCW
- Lucha Libre: Lucha Underground, AAA, CMLL
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
    fan_loyalty: float
    fan_volatility: float
    fan_growth_rate: float
    
    # Financial modifiers
    wrestler_salary_modifier: float
    merchandise_modifier: float
    ticket_price_modifier: float
    sponsor_appeal: float
    
    # Media modifiers
    tv_appeal: float
    publicity_modifier: float
    production_cost_modifier: float
    
    # Wrestling modifiers
    match_time_preference: tuple
    style_bonuses: Dict[WrestlingStyle, float]
    prestige_start: int
    
    # Special perks
    perks: List[str]
    drawbacks: List[str]


PHILOSOPHY_PROFILES = {
    Philosophy.ULTRAVIOLENT: PhilosophyProfile(
        name="Ultraviolent",
        description="Blood, guts, light tubes and barbed wire. Inspired by CZW, ECW, and GCW. Your fans crave violence and you deliver every time.",
        starting_budget=150000,
        
        # Fans - hardcore loyal but small
        starting_fans=500,
        fan_loyalty=1.5,            # Extremely loyal cult following
        fan_volatility=0.6,         # They will never leave you
        fan_growth_rate=0.7,        # Hard to grow beyond cult status
        
        # Financial
        wrestler_salary_modifier=0.7,   # Hardcore guys work cheap
        merchandise_modifier=1.2,       # T-shirts and DVDs sell well
        ticket_price_modifier=0.85,     # Affordable indie pricing
        sponsor_appeal=0.3,             # Almost no mainstream sponsors
        
        # Media
        tv_appeal=0.3,                  # Networks won't touch you
        publicity_modifier=0.8,         # Underground but talked about
        production_cost_modifier=0.6,   # Bingo halls and warehouses
        
        # Wrestling
        match_time_preference=(8, 25),
        style_bonuses={
            WrestlingStyle.HARDCORE: 1.5,
            WrestlingStyle.BRAWLER: 1.35,
            WrestlingStyle.POWERHOUSE: 1.15,
            WrestlingStyle.GIANT: 1.1,
            WrestlingStyle.HIGH_FLYER: 1.1,    # Lucha Underground style spots work
            WrestlingStyle.SHOWMAN: 0.8,
            WrestlingStyle.TECHNICIAN: 0.85,
        },
        prestige_start=30,
        
        perks=[
            "Loyal cult fanbase that never leaves",
            "Wrestlers work for cheap (love the style)",
            "Low venue and production costs",
            "Hardcore matches massively boost ratings",
            "Underground reputation creates buzz",
            "Blood and weapons are encouraged",
        ],
        drawbacks=[
            "Network TV deals are nearly impossible",
            "Mainstream sponsors avoid you",
            "Higher injury rates from violence",
            "Slow to grow beyond cult following",
            "Some wrestlers refuse to work hardcore",
            "Limited venue options (need willing buildings)",
        ],
    ),
    
    Philosophy.SPORTS_ENTERTAINMENT: PhilosophyProfile(
        name="Sports Entertainment",
        description="Larger than life characters, big spectacles, mainstream appeal. Inspired by WWE, AEW, TNA, and WCW. Wrestling meets Hollywood.",
        starting_budget=500000,
        
        # Fans - massive but fickle
        starting_fans=2000,
        fan_loyalty=0.7,            # Casual fans come and go
        fan_volatility=1.4,         # React strongly to everything
        fan_growth_rate=1.4,        # Can grow fast with right product
        
        # Financial
        wrestler_salary_modifier=1.5,   # Stars demand top dollar
        merchandise_modifier=1.6,       # Merchandise is king
        ticket_price_modifier=1.4,      # Premium pricing
        sponsor_appeal=1.6,             # Sponsors love mainstream appeal
        
        # Media
        tv_appeal=1.6,                  # Networks want you
        publicity_modifier=1.5,         # Mainstream media coverage
        production_cost_modifier=1.6,   # Big productions cost big money
        
        # Wrestling
        match_time_preference=(8, 20),
        style_bonuses={
            WrestlingStyle.SHOWMAN: 1.5,
            WrestlingStyle.POWERHOUSE: 1.3,
            WrestlingStyle.GIANT: 1.35,        # Big men sell tickets
            WrestlingStyle.ALL_ROUNDER: 1.2,
            WrestlingStyle.HIGH_FLYER: 1.15,
            WrestlingStyle.BRAWLER: 1.1,
            WrestlingStyle.TECHNICIAN: 0.9,    # Pure tech doesn't pop
            WrestlingStyle.HARDCORE: 0.8,
        },
        prestige_start=55,
        
        perks=[
            "Massive starting budget",
            "Easy to land TV deals",
            "Best-in-class merchandise sales",
            "Sponsors line up to work with you",
            "Fast fanbase growth potential",
            "Mainstream media coverage",
            "Ability to attract crossover stars",
        ],
        drawbacks=[
            "Fans are fickle and demand constant entertainment",
            "Top wrestlers demand huge salaries",
            "Production costs can sink you fast",
            "Bad shows damage your brand significantly",
            "Pure wrestling-focused matches underperform",
            "Need constant storyline rotation to keep fans",
        ],
    ),
    
    Philosophy.WORKRATE: PhilosophyProfile(
        name="Strong Style",
        description="Stiff strikes, technical excellence, sport-like presentation. Inspired by NJPW, NOAH, Progress, and the indie scene. Wrestling as combat sport.",
        starting_budget=300000,
        
        # Fans - smart, knowledgeable
        starting_fans=1000,
        fan_loyalty=1.2,            # Knowledgeable, appreciative fans
        fan_volatility=0.85,        # Won't turn on good wrestling
        fan_growth_rate=1.0,        # Steady organic growth
        
        # Financial
        wrestler_salary_modifier=1.0,   # Fair pay for fair work
        merchandise_modifier=1.1,       # T-shirts sell to the fans
        ticket_price_modifier=1.15,     # Fans pay for quality
        sponsor_appeal=0.85,            # Some sponsors, niche appeal
        
        # Media
        tv_appeal=0.95,                 # Streaming services love this
        publicity_modifier=1.0,         # Industry respect, less mainstream
        production_cost_modifier=0.85,  # Don't need flashy production
        
        # Wrestling
        match_time_preference=(15, 45),  # Long matches
        style_bonuses={
            WrestlingStyle.TECHNICIAN: 1.5,
            WrestlingStyle.HIGH_FLYER: 1.25,
            WrestlingStyle.POWERHOUSE: 1.2,
            WrestlingStyle.BRAWLER: 1.15,
            WrestlingStyle.ALL_ROUNDER: 1.15,
            WrestlingStyle.SHOWMAN: 0.85,
            WrestlingStyle.GIANT: 0.95,
            WrestlingStyle.HARDCORE: 0.9,
        },
        prestige_start=65,
        
        perks=[
            "High starting prestige (industry respect)",
            "Streaming services want your product",
            "Smart fans appreciate quality and stay loyal",
            "Wrestlers want to work here for credibility",
            "Lower production costs (focus on wrestling)",
            "Great matches massively boost reputation",
            "International touring opportunities (Japan)",
        ],
        drawbacks=[
            "Limited mainstream appeal",
            "Slower fan growth (needs word of mouth)",
            "Need consistently great wrestling every show",
            "Character-driven wrestlers underperform",
            "Less merchandise revenue than mainstream",
            "Pure striking can lead to legitimate injuries",
        ],
    ),
    
    Philosophy.LUCHA: PhilosophyProfile(
        name="Lucha Libre",
        description="High-flying action, masks, family traditions, and rich storytelling. Inspired by CMLL, AAA, and Lucha Underground. Wrestling as art and culture.",
        starting_budget=250000,
        
        # Fans - culturally connected
        starting_fans=1500,
        fan_loyalty=1.3,            # Multi-generational families
        fan_volatility=0.9,         # Steady cultural connection
        fan_growth_rate=1.1,        # Growing global appeal
        
        # Financial
        wrestler_salary_modifier=0.85,  # Honor to wear the mask
        merchandise_modifier=1.5,       # Masks and shirts sell HUGE
        ticket_price_modifier=1.0,      # Family-friendly pricing
        sponsor_appeal=1.2,             # Cultural and Latin sponsors
        
        # Media
        tv_appeal=1.15,                 # Streaming, Spanish networks
        publicity_modifier=1.05,        # Cultural moments break through
        production_cost_modifier=0.9,   # Colorful but achievable
        
        # Wrestling
        match_time_preference=(10, 25),
        style_bonuses={
            WrestlingStyle.HIGH_FLYER: 1.5,
            WrestlingStyle.SHOWMAN: 1.3,        # Characters and personas matter
            WrestlingStyle.TECHNICIAN: 1.2,     # Mat work valued
            WrestlingStyle.ALL_ROUNDER: 1.15,
            WrestlingStyle.HARDCORE: 1.15,      # Lucha Underground style works
            WrestlingStyle.BRAWLER: 1.05,
            WrestlingStyle.GIANT: 0.9,
            WrestlingStyle.POWERHOUSE: 0.95,
        },
        prestige_start=50,
        
        perks=[
            "Mask merchandise sales are insane",
            "Multi-generational loyal fanbase",
            "Cultural significance creates passionate fans",
            "Tag team and trios matches shine",
            "Lucha Underground style hardcore works well",
            "Lower production costs",
            "Loyal wrestlers (tradition and honor)",
            "Spanish-language media opportunities",
        ],
        drawbacks=[
            "Power-based and giant wrestlers underperform",
            "Limited appeal in non-Lucha markets",
            "Need authentic luchador talent to succeed",
            "Mask matches require careful storyline planning",
            "Fewer big sponsor opportunities outside cultural ones",
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
