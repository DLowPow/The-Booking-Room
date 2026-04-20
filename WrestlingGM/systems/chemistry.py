"""
Style Chemistry System
Determines how well two wrestling styles work together
8 Wrestling Styles: Luchador, Powerhouse, Technician, Fighter, Hardcore, Showman, Giant, All Rounder
"""

from classes.enums import WrestlingStyle


# Chemistry ratings: how well two styles work together
# Scale: 0.5 (bad) to 1.5 (amazing)
# None = neutral (1.0)
STYLE_CHEMISTRY = {
    # Classic David vs Goliath - works great
    (WrestlingStyle.GIANT, WrestlingStyle.LUCHADOR): 1.4,
    (WrestlingStyle.GIANT, WrestlingStyle.TECHNICIAN): 1.25,
    
    # Power vs Speed - dynamic
    (WrestlingStyle.POWERHOUSE, WrestlingStyle.LUCHADOR): 1.35,
    (WrestlingStyle.POWERHOUSE, WrestlingStyle.TECHNICIAN): 1.25,
    
    # Hardcore pairings
    (WrestlingStyle.FIGHTER, WrestlingStyle.HARDCORE): 1.3,
    (WrestlingStyle.HARDCORE, WrestlingStyle.HARDCORE): 1.25,
    (WrestlingStyle.HARDCORE, WrestlingStyle.POWERHOUSE): 1.2,
    
    # Technical excellence
    (WrestlingStyle.TECHNICIAN, WrestlingStyle.FIGHTER): 1.3,
    (WrestlingStyle.TECHNICIAN, WrestlingStyle.LUCHADOR): 1.2,
    
    # Lucha specialties
    (WrestlingStyle.LUCHADOR, WrestlingStyle.LUCHADOR): 1.3,
    (WrestlingStyle.LUCHADOR, WrestlingStyle.SHOWMAN): 1.2,
    
    # Fighter pairings (MMA style)
    (WrestlingStyle.FIGHTER, WrestlingStyle.FIGHTER): 1.25,
    (WrestlingStyle.FIGHTER, WrestlingStyle.POWERHOUSE): 1.2,
    
    # Showman shines with characters
    (WrestlingStyle.SHOWMAN, WrestlingStyle.GIANT): 1.25,
    (WrestlingStyle.SHOWMAN, WrestlingStyle.POWERHOUSE): 1.2,
    
    # All Rounder works with everyone
    (WrestlingStyle.ALL_ROUNDER, WrestlingStyle.LUCHADOR): 1.15,
    (WrestlingStyle.ALL_ROUNDER, WrestlingStyle.TECHNICIAN): 1.15,
    (WrestlingStyle.ALL_ROUNDER, WrestlingStyle.FIGHTER): 1.15,
    (WrestlingStyle.ALL_ROUNDER, WrestlingStyle.POWERHOUSE): 1.15,
    
    # Clashing styles (worse chemistry normally)
    (WrestlingStyle.TECHNICIAN, WrestlingStyle.TECHNICIAN): 0.85,
    (WrestlingStyle.GIANT, WrestlingStyle.GIANT): 0.65,
    (WrestlingStyle.SHOWMAN, WrestlingStyle.TECHNICIAN): 0.75,
    (WrestlingStyle.SHOWMAN, WrestlingStyle.FIGHTER): 0.8,
    (WrestlingStyle.HARDCORE, WrestlingStyle.TECHNICIAN): 0.8,
    (WrestlingStyle.HARDCORE, WrestlingStyle.LUCHADOR): 0.85,
    (WrestlingStyle.GIANT, WrestlingStyle.POWERHOUSE): 0.85,
}


def get_chemistry(style1: WrestlingStyle, style2: WrestlingStyle) -> float:
    """Get chemistry modifier between two wrestling styles"""
    # Check both orderings
    if (style1, style2) in STYLE_CHEMISTRY:
        return STYLE_CHEMISTRY[(style1, style2)]
    if (style2, style1) in STYLE_CHEMISTRY:
        return STYLE_CHEMISTRY[(style2, style1)]
    return 1.0  # Neutral chemistry
