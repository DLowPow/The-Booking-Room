from enum import Enum


class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    INTERGENDER = "Intergender"


class WeightClass(Enum):
    JUNIOR = "Junior Heavyweight"
    CRUISERWEIGHT = "Cruiserweight"
    MIDDLEWEIGHT = "Middleweight"
    HEAVYWEIGHT = "Heavyweight"
    SUPER_HEAVYWEIGHT = "Super Heavyweight"


class WrestlingStyle(Enum):
    HIGH_FLYER = "High Flyer"
    POWERHOUSE = "Powerhouse"
    TECHNICIAN = "Technician"
    BRAWLER = "Brawler"
    HARDCORE = "Hardcore"
    SHOWMAN = "Showman"
    GIANT = "Giant"
    ALL_ROUNDER = "All Rounder"


class Alignment(Enum):
    FACE = "Face"
    HEEL = "Heel"
    TWEENER = "Tweener"


class Philosophy(Enum):
    ULTRAVIOLENT = "Ultraviolent"
    SPORTS_ENTERTAINMENT = "Sports Entertainment"
    WORKRATE = "Strong Style"
    LUCHA = "Lucha Libre"


class MatchType(Enum):
    STANDARD = "Standard"
    IRON_MAN = "Iron Man"
    SUBMISSION = "Submission"
    LADDER = "Ladder"
    CAGE = "Steel Cage"
    DEATHMATCH = "Deathmatch"
    TABLES = "Tables"
    BATTLE_ROYAL = "Battle Royal"
    TAG_TEAM = "Tag Team"
    FALLS_COUNT_ANYWHERE = "Falls Count Anywhere"
    LAST_MAN_STANDING = "Last Man Standing"
    I_QUIT = "I Quit"
    TRIPLE_THREAT = "Triple Threat"
    FATAL_FOUR_WAY = "Fatal Four Way"
    ROYAL_RUMBLE = "Royal Rumble"
    ELIMINATION_CHAMBER = "Elimination Chamber"
