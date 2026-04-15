from classes.enums import WrestlingStyle

# Chemistry ratings: how well two styles work together
# Scale: 0.5 (bad) to 1.5 (amazing)
# None = neutral (1.0)

STYLE_CHEMISTRY = {
    (WrestlingStyle.GIANT, WrestlingStyle.HIGH_FLYER): 1.4,
    (WrestlingStyle.GIANT, WrestlingStyle.LUCHADOR): 1.35,
    (WrestlingStyle.POWERHOUSE, WrestlingStyle.TECHNICIAN): 1.25,
    (WrestlingStyle.POWERHOUSE, WrestlingStyle.HIGH_FLYER): 1.3,
    (WrestlingStyle.BRAWLER, WrestlingStyle.HARDCORE): 1.3,
    (WrestlingStyle.BRAWLER, WrestlingStyle.STRONG_STYLE): 1.25,
    (WrestlingStyle.TECHNICIAN, WrestlingStyle.SUBMISSION_ARTIST): 1.2,
    (WrestlingStyle.STRONG_STYLE, WrestlingStyle.STRONG_STYLE): 1.3,
    (WrestlingStyle.LUCHADOR, WrestlingStyle.LUCHADOR): 1.25,
    (WrestlingStyle.HIGH_FLYER, WrestlingStyle.HIGH_FLYER): 1.2,
    
    # Clashing styles (worse chemistry normally)
    (WrestlingStyle.TECHNICIAN, WrestlingStyle.TECHNICIAN): 0.85,
    (WrestlingStyle.GIANT, WrestlingStyle.GIANT): 0.7,
    (WrestlingStyle.SHOWMAN, WrestlingStyle.STRONG_STYLE): 0.75,
    (WrestlingStyle.HARDCORE, WrestlingStyle.TECHNICIAN): 0.8,
}

def get_chemistry(style1: WrestlingStyle, style2: WrestlingStyle) -> float:
    """Get chemistry modifier between two wrestling styles"""
    # Check both orderings
    if (style1, style2) in STYLE_CHEMISTRY:
        return STYLE_CHEMISTRY[(style1, style2)]
    if (style2, style1) in STYLE_CHEMISTRY:
        return STYLE_CHEMISTRY[(style2, style1)]
    return 1.0  # Neutral chemistry