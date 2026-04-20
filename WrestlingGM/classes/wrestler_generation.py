"""
Wrestler Generation Rules
Realistic combinations of style, weight, and gender
"""

from classes.enums import Gender, WeightClass, WrestlingStyle


# ==================== MALE WEIGHT RANGES ====================
# (height_min, height_max, weight_min, weight_max) in inches/lbs

MALE_WEIGHT_CLASSES = {
    WeightClass.JUNIOR: (66, 72, 175, 199),           # 5'6"-6'0", 175-199 lbs
    WeightClass.CRUISERWEIGHT: (68, 74, 200, 219),    # 5'8"-6'2", 200-219 lbs
    WeightClass.MIDDLEWEIGHT: (70, 76, 220, 244),     # 5'10"-6'4", 220-244 lbs
    WeightClass.HEAVYWEIGHT: (72, 78, 245, 279),      # 6'0"-6'6", 245-279 lbs
    WeightClass.SUPER_HEAVYWEIGHT: (74, 84, 280, 400),# 6'2"-7'0", 280-400 lbs
}

# ==================== FEMALE WEIGHT RANGES ====================

FEMALE_WEIGHT_CLASSES = {
    WeightClass.LIGHTWEIGHT: (60, 66, 110, 130),      # 5'0"-5'6", 110-130 lbs
    WeightClass.WELTERWEIGHT: (62, 68, 131, 150),     # 5'2"-5'8", 131-150 lbs
    WeightClass.MIDDLEWEIGHT: (64, 70, 151, 175),     # 5'4"-5'10", 151-175 lbs
    WeightClass.HEAVYWEIGHT: (66, 74, 176, 220),      # 5'6"-6'2", 176-220 lbs
    WeightClass.SUPER_HEAVYWEIGHT: (68, 78, 221, 320),# 5'8"-6'6", 221-320 lbs
}


# ==================== STYLE x WEIGHT WEIGHTS ====================
# Higher number = more common combination
# 0 = impossible, 1 = very rare, 5 = uncommon, 10 = common, 20 = very common

MALE_STYLE_WEIGHT_WEIGHTS = {
    WrestlingStyle.HIGH_FLYER: {
        WeightClass.JUNIOR: 25,
        WeightClass.CRUISERWEIGHT: 20,
        WeightClass.MIDDLEWEIGHT: 8,
        WeightClass.HEAVYWEIGHT: 3,
        WeightClass.SUPER_HEAVYWEIGHT: 1,  # Very rare
    },
    WrestlingStyle.POWERHOUSE: {
        WeightClass.JUNIOR: 1,
        WeightClass.CRUISERWEIGHT: 5,
        WeightClass.MIDDLEWEIGHT: 15,
        WeightClass.HEAVYWEIGHT: 25,
        WeightClass.SUPER_HEAVYWEIGHT: 20,
    },
    WrestlingStyle.TECHNICIAN: {
        WeightClass.JUNIOR: 15,
        WeightClass.CRUISERWEIGHT: 20,
        WeightClass.MIDDLEWEIGHT: 18,
        WeightClass.HEAVYWEIGHT: 12,
        WeightClass.SUPER_HEAVYWEIGHT: 3,
    },
    WrestlingStyle.BRAWLER: {
        WeightClass.JUNIOR: 5,
        WeightClass.CRUISERWEIGHT: 10,
        WeightClass.MIDDLEWEIGHT: 18,
        WeightClass.HEAVYWEIGHT: 20,
        WeightClass.SUPER_HEAVYWEIGHT: 12,
    },
    WrestlingStyle.HARDCORE: {
        WeightClass.JUNIOR: 8,
        WeightClass.CRUISERWEIGHT: 12,
        WeightClass.MIDDLEWEIGHT: 18,
        WeightClass.HEAVYWEIGHT: 18,
        WeightClass.SUPER_HEAVYWEIGHT: 8,
    },
    WrestlingStyle.SHOWMAN: {
        WeightClass.JUNIOR: 10,
        WeightClass.CRUISERWEIGHT: 15,
        WeightClass.MIDDLEWEIGHT: 20,
        WeightClass.HEAVYWEIGHT: 18,
        WeightClass.SUPER_HEAVYWEIGHT: 8,
    },
    WrestlingStyle.GIANT: {
        WeightClass.JUNIOR: 0,  # Impossible
        WeightClass.CRUISERWEIGHT: 0,
        WeightClass.MIDDLEWEIGHT: 1,  # Very rare
        WeightClass.HEAVYWEIGHT: 5,
        WeightClass.SUPER_HEAVYWEIGHT: 30,  # Where giants live
    },
    WrestlingStyle.ALL_ROUNDER: {
        WeightClass.JUNIOR: 10,
        WeightClass.CRUISERWEIGHT: 15,
        WeightClass.MIDDLEWEIGHT: 20,
        WeightClass.HEAVYWEIGHT: 18,
        WeightClass.SUPER_HEAVYWEIGHT: 8,
    },
}


FEMALE_STYLE_WEIGHT_WEIGHTS = {
    WrestlingStyle.HIGH_FLYER: {
        WeightClass.LIGHTWEIGHT: 25,
        WeightClass.WELTERWEIGHT: 20,
        WeightClass.MIDDLEWEIGHT: 10,
        WeightClass.HEAVYWEIGHT: 3,
        WeightClass.SUPER_HEAVYWEIGHT: 1,
    },
    WrestlingStyle.POWERHOUSE: {
        WeightClass.LIGHTWEIGHT: 2,
        WeightClass.WELTERWEIGHT: 5,
        WeightClass.MIDDLEWEIGHT: 15,
        WeightClass.HEAVYWEIGHT: 20,
        WeightClass.SUPER_HEAVYWEIGHT: 12,
    },
    WrestlingStyle.TECHNICIAN: {
        WeightClass.LIGHTWEIGHT: 15,
        WeightClass.WELTERWEIGHT: 20,
        WeightClass.MIDDLEWEIGHT: 18,
        WeightClass.HEAVYWEIGHT: 10,
        WeightClass.SUPER_HEAVYWEIGHT: 3,
    },
    WrestlingStyle.BRAWLER: {
        WeightClass.LIGHTWEIGHT: 5,
        WeightClass.WELTERWEIGHT: 10,
        WeightClass.MIDDLEWEIGHT: 18,
        WeightClass.HEAVYWEIGHT: 18,
        WeightClass.SUPER_HEAVYWEIGHT: 8,
    },
    WrestlingStyle.HARDCORE: {
        WeightClass.LIGHTWEIGHT: 8,
        WeightClass.WELTERWEIGHT: 12,
        WeightClass.MIDDLEWEIGHT: 18,
        WeightClass.HEAVYWEIGHT: 15,
        WeightClass.SUPER_HEAVYWEIGHT: 5,
    },
    WrestlingStyle.SHOWMAN: {
        WeightClass.LIGHTWEIGHT: 12,
        WeightClass.WELTERWEIGHT: 18,
        WeightClass.MIDDLEWEIGHT: 20,
        WeightClass.HEAVYWEIGHT: 12,
        WeightClass.SUPER_HEAVYWEIGHT: 5,
    },
    WrestlingStyle.GIANT: {
        WeightClass.LIGHTWEIGHT: 0,
        WeightClass.WELTERWEIGHT: 0,
        WeightClass.MIDDLEWEIGHT: 0,
        WeightClass.HEAVYWEIGHT: 2,   # Very rare
        WeightClass.SUPER_HEAVYWEIGHT: 8,  # Rare but possible
    },
    WrestlingStyle.ALL_ROUNDER: {
        WeightClass.LIGHTWEIGHT: 10,
        WeightClass.WELTERWEIGHT: 15,
        WeightClass.MIDDLEWEIGHT: 20,
        WeightClass.HEAVYWEIGHT: 15,
        WeightClass.SUPER_HEAVYWEIGHT: 5,
    },
}


# ==================== STYLE GENDER WEIGHTS ====================
# How common each style is by gender

MALE_STYLE_WEIGHTS = {
    WrestlingStyle.HIGH_FLYER: 15,
    WrestlingStyle.POWERHOUSE: 18,
    WrestlingStyle.TECHNICIAN: 15,
    WrestlingStyle.BRAWLER: 15,
    WrestlingStyle.HARDCORE: 8,
    WrestlingStyle.SHOWMAN: 12,
    WrestlingStyle.GIANT: 3,  # Rare
    WrestlingStyle.ALL_ROUNDER: 14,
}

FEMALE_STYLE_WEIGHTS = {
    WrestlingStyle.HIGH_FLYER: 18,  # More common in women's wrestling
    WrestlingStyle.POWERHOUSE: 12,
    WrestlingStyle.TECHNICIAN: 16,
    WrestlingStyle.BRAWLER: 12,
    WrestlingStyle.HARDCORE: 6,
    WrestlingStyle.SHOWMAN: 18,  # Very common
    WrestlingStyle.GIANT: 1,  # Very rare
    WrestlingStyle.ALL_ROUNDER: 17,
}


# ==================== HELPER FUNCTIONS ====================

import random


def select_style_for_gender(gender: Gender) -> WrestlingStyle:
    """Select a style weighted by gender realism"""
    if gender == Gender.FEMALE:
        weights_dict = FEMALE_STYLE_WEIGHTS
    else:
        weights_dict = MALE_STYLE_WEIGHTS
    
    styles = list(weights_dict.keys())
    weights = list(weights_dict.values())
    
    return random.choices(styles, weights=weights, k=1)[0]


def select_weight_class_for_style(style: WrestlingStyle, gender: Gender) -> WeightClass:
    """Select a weight class based on style and gender"""
    if gender == Gender.FEMALE:
        weights_dict = FEMALE_STYLE_WEIGHT_WEIGHTS.get(style, FEMALE_STYLE_WEIGHT_WEIGHTS[WrestlingStyle.ALL_ROUNDER])
    else:
        weights_dict = MALE_STYLE_WEIGHT_WEIGHTS.get(style, MALE_STYLE_WEIGHT_WEIGHTS[WrestlingStyle.ALL_ROUNDER])
    
    # Filter out impossible (weight 0)
    classes = []
    weights = []
    for wc, w in weights_dict.items():
        if w > 0:
            classes.append(wc)
            weights.append(w)
    
    if not classes:
        # Fallback
        if gender == Gender.FEMALE:
            return WeightClass.MIDDLEWEIGHT
        return WeightClass.MIDDLEWEIGHT
    
    return random.choices(classes, weights=weights, k=1)[0]


def get_height_weight_for_class(weight_class: WeightClass, gender: Gender) -> tuple:
    """Get random height and weight for a weight class"""
    if gender == Gender.FEMALE:
        ranges = FEMALE_WEIGHT_CLASSES.get(weight_class)
    else:
        ranges = MALE_WEIGHT_CLASSES.get(weight_class)
    
    if not ranges:
        # Fallback to middleweight
        if gender == Gender.FEMALE:
            ranges = FEMALE_WEIGHT_CLASSES[WeightClass.MIDDLEWEIGHT]
        else:
            ranges = MALE_WEIGHT_CLASSES[WeightClass.MIDDLEWEIGHT]
    
    height_min, height_max, weight_min, weight_max = ranges
    height = random.randint(height_min, height_max)
    weight = random.randint(weight_min, weight_max)
    
    return height, weight


def generate_realistic_wrestler_attributes(gender: Gender = None) -> dict:
    """
    Generate realistic style + weight class + height + weight combination.
    Returns a dict with all values.
    """
    if gender is None:
        gender = random.choice([Gender.MALE, Gender.FEMALE])
    
    # Pick style first based on gender
    style = select_style_for_gender(gender)
    
    # Pick weight class based on style and gender
    weight_class = select_weight_class_for_style(style, gender)
    
    # Get height and weight
    height, weight = get_height_weight_for_class(weight_class, gender)
    
    return {
        "gender": gender,
        "style": style,
        "weight_class": weight_class,
        "height": height,
        "weight": weight,
    }