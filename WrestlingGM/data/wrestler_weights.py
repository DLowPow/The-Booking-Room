"""
Wrestler Weight Classes
Defines weight ranges and physical attributes per weight class
"""

from classes.enums import WeightClass, Gender, WrestlingStyle
import random


# Weight class ranges by gender
WEIGHT_RANGES = {
    Gender.MALE: {
        WeightClass.JUNIOR: (170, 200),
        WeightClass.CRUISERWEIGHT: (180, 220),
        WeightClass.MIDDLEWEIGHT: (210, 245),
        WeightClass.HEAVYWEIGHT: (235, 285),
        WeightClass.SUPER_HEAVYWEIGHT: (280, 380),
    },
    Gender.FEMALE: {
        WeightClass.LIGHTWEIGHT: (95, 125),
        WeightClass.WELTERWEIGHT: (115, 145),
        WeightClass.JUNIOR: (135, 160),
        WeightClass.CRUISERWEIGHT: (150, 175),
        WeightClass.MIDDLEWEIGHT: (165, 195),
        WeightClass.HEAVYWEIGHT: (185, 220),
        WeightClass.SUPER_HEAVYWEIGHT: (215, 280),
    },
}


# Height ranges per weight class (in inches)
HEIGHT_RANGES = {
    Gender.MALE: {
        WeightClass.JUNIOR: (64, 70),
        WeightClass.CRUISERWEIGHT: (66, 72),
        WeightClass.MIDDLEWEIGHT: (68, 74),
        WeightClass.HEAVYWEIGHT: (70, 78),
        WeightClass.SUPER_HEAVYWEIGHT: (74, 84),
    },
    Gender.FEMALE: {
        WeightClass.LIGHTWEIGHT: (58, 64),
        WeightClass.WELTERWEIGHT: (60, 66),
        WeightClass.JUNIOR: (62, 68),
        WeightClass.CRUISERWEIGHT: (64, 70),
        WeightClass.MIDDLEWEIGHT: (66, 72),
        WeightClass.HEAVYWEIGHT: (68, 74),
        WeightClass.SUPER_HEAVYWEIGHT: (70, 78),
    },
}


# Style preferences for weight classes
STYLE_TO_WEIGHT_PREFERENCE = {
    WrestlingStyle.LUCHADOR: {
        Gender.MALE: [WeightClass.JUNIOR, WeightClass.CRUISERWEIGHT],
        Gender.FEMALE: [WeightClass.LIGHTWEIGHT, WeightClass.WELTERWEIGHT, WeightClass.JUNIOR],
    },
    WrestlingStyle.POWERHOUSE: {
        Gender.MALE: [WeightClass.HEAVYWEIGHT, WeightClass.SUPER_HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.MIDDLEWEIGHT, WeightClass.HEAVYWEIGHT],
    },
    WrestlingStyle.TECHNICIAN: {
        Gender.MALE: [WeightClass.CRUISERWEIGHT, WeightClass.MIDDLEWEIGHT, WeightClass.HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.WELTERWEIGHT, WeightClass.JUNIOR, WeightClass.CRUISERWEIGHT],
    },
    WrestlingStyle.FIGHTER: {
        Gender.MALE: [WeightClass.MIDDLEWEIGHT, WeightClass.HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.JUNIOR, WeightClass.CRUISERWEIGHT, WeightClass.MIDDLEWEIGHT],
    },
    WrestlingStyle.HARDCORE: {
        Gender.MALE: [WeightClass.MIDDLEWEIGHT, WeightClass.HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.JUNIOR, WeightClass.CRUISERWEIGHT, WeightClass.MIDDLEWEIGHT],
    },
    WrestlingStyle.SHOWMAN: {
        Gender.MALE: [WeightClass.CRUISERWEIGHT, WeightClass.MIDDLEWEIGHT, WeightClass.HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.WELTERWEIGHT, WeightClass.JUNIOR, WeightClass.CRUISERWEIGHT],
    },
    WrestlingStyle.GIANT: {
        Gender.MALE: [WeightClass.SUPER_HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.HEAVYWEIGHT, WeightClass.SUPER_HEAVYWEIGHT],
    },
    WrestlingStyle.ALL_ROUNDER: {
        Gender.MALE: [WeightClass.CRUISERWEIGHT, WeightClass.MIDDLEWEIGHT, WeightClass.HEAVYWEIGHT],
        Gender.FEMALE: [WeightClass.WELTERWEIGHT, WeightClass.JUNIOR, WeightClass.CRUISERWEIGHT, WeightClass.MIDDLEWEIGHT],
    },
}


def get_weight_class_for_style(style, gender):
    """Get appropriate weight class based on style and gender"""
    preferences = STYLE_TO_WEIGHT_PREFERENCE.get(style, {})
    options = preferences.get(gender, [WeightClass.MIDDLEWEIGHT])
    return random.choice(options)


def get_weight_for_class(weight_class, gender):
    """Get weight in pounds for a weight class"""
    ranges = WEIGHT_RANGES.get(gender, WEIGHT_RANGES[Gender.MALE])
    weight_range = ranges.get(weight_class, (180, 220))
    return random.randint(weight_range[0], weight_range[1])


def get_height_for_class(weight_class, gender):
    """Get height in inches for a weight class"""
    ranges = HEIGHT_RANGES.get(gender, HEIGHT_RANGES[Gender.MALE])
    height_range = ranges.get(weight_class, (66, 72))
    return random.randint(height_range[0], height_range[1])


def get_physical_attributes(style, gender):
    """Get all physical attributes for a wrestler"""
    weight_class = get_weight_class_for_style(style, gender)
    weight = get_weight_for_class(weight_class, gender)
    height = get_height_for_class(weight_class, gender)
    
    return {
        "weight_class": weight_class,
        "weight": weight,
        "height": height,
    }


def get_available_weight_classes(gender):
    """Get all weight classes available for a gender"""
    if gender == Gender.MALE:
        return [
            WeightClass.JUNIOR,
            WeightClass.CRUISERWEIGHT,
            WeightClass.MIDDLEWEIGHT,
            WeightClass.HEAVYWEIGHT,
            WeightClass.SUPER_HEAVYWEIGHT,
        ]
    else:
        return [
            WeightClass.LIGHTWEIGHT,
            WeightClass.WELTERWEIGHT,
            WeightClass.JUNIOR,
            WeightClass.CRUISERWEIGHT,
            WeightClass.MIDDLEWEIGHT,
            WeightClass.HEAVYWEIGHT,
            WeightClass.SUPER_HEAVYWEIGHT,
        ]