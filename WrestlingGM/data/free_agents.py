"""
Free Agents - Tiered roster generation system
100 Men + 100 Women, locked by level
"""

import random
from typing import List, Optional, Dict
from classes.wrestler import Wrestler
from classes.enums import Gender, WrestlingStyle, Alignment


# ==================== NAME POOLS ====================

FIRST_NAMES_MALE = [
    # Tier 1 - Indie/Local names
    "Adam", "Alex", "Austin", "Billy", "Bobby", "Brad", "Brandon", "Brent",
    "Brian", "Caleb", "Carlos", "Casey", "Chad", "Chase", "Chris", "Clay",
    "Cody", "Cole", "Connor", "Craig", "Damian", "Danny", "Darius", "Dean",
    "Derek", "Devin", "Diego", "Dominic", "Drake", "Drew", "Dustin", "Dylan",
    "Eddie", "Eli", "Eric", "Ethan", "Evan", "Felix", "Finn", "Frank",
    "Garrett", "Grant", "Greg", "Hector", "Hunter", "Isaiah", "Ivan", "Jack",
    "Jackson", "Jake", "James", "Jared", "Jason", "Jay", "Jeff", "Jeremy",
    "Jesse", "Jimmy", "Joe", "John", "Johnny", "Jordan", "Josh", "Julian",
    "Justin", "Keith", "Kenny", "Kevin", "Kyle", "Lance", "Leo", "Liam",
    "Logan", "Lucas", "Luke", "Marco", "Marcus", "Mark", "Mason", "Matt",
    "Max", "Michael", "Miguel", "Mike", "Milo", "Nathan", "Nick", "Noah",
    "Oliver", "Omar", "Oscar", "Owen", "Patrick", "Paul", "Pete", "Phoenix",
    "Preston", "Quinn", "Rafael", "Randy", "Ray", "Reno", "Rex", "Rick",
    "Ricky", "Rob", "Roman", "Ronin", "Ryan", "Sam", "Santiago", "Scott",
    "Sean", "Sebastian", "Seth", "Shane", "Shawn", "Simon", "Spencer", "Steve",
    "Tanner", "Ted", "Theo", "Thomas", "Tim", "Titus", "Tom", "Tony",
    "Travis", "Trevor", "Troy", "Tyler", "Victor", "Vince", "Wade", "Walker",
    "Wesley", "Will", "Xavier", "Zack", "Zane",
]

FIRST_NAMES_FEMALE = [
    "Aaliyah", "Abby", "Alexa", "Alicia", "Amanda", "Amber", "Amy", "Angel",
    "Anna", "Aria", "Ashley", "Athena", "Becky", "Bella", "Beth", "Bianca",
    "Blair", "Brandi", "Britt", "Brittany", "Brooke", "Cameron", "Carmen",
    "Cassandra", "Catalina", "Chelsea", "Chloe", "Claire", "Crystal", "Dana",
    "Dani", "Daniella", "Dawn", "Deonna", "Diana", "Elena", "Eliza", "Ella",
    "Emily", "Emma", "Eva", "Faith", "Gabriella", "Gigi", "Grace", "Haley",
    "Hannah", "Harley", "Holly", "Ivy", "Jade", "Jamie", "Jasmine", "Jenna",
    "Jessica", "Jocelyn", "Julia", "Kaitlyn", "Kara", "Kate", "Katie", "Kelly",
    "Kenzie", "Kim", "Kira", "Lacey", "Laura", "Layla", "Lexi", "Lila",
    "Lily", "Lisa", "Liv", "Luna", "Macy", "Madison", "Maria", "Marina",
    "Maya", "Megan", "Melissa", "Mercedes", "Michelle", "Mila", "Molly",
    "Morgan", "Nadia", "Natalie", "Natalya", "Nicole", "Nikki", "Nina",
    "Nyla", "Olivia", "Paige", "Penelope", "Peyton", "Piper", "Quinn",
    "Rachel", "Raquel", "Rebecca", "Riley", "Rosa", "Rosie", "Ruby", "Sage",
    "Samantha", "Sara", "Sasha", "Savannah", "Scarlett", "Serena", "Sierra",
    "Skye", "Sofia", "Sophia", "Stella", "Stephanie", "Summer", "Tara",
    "Tasha", "Taylor", "Tegan", "Tessa", "Tiffany", "Toni", "Trinity",
    "Valentina", "Vanessa", "Victoria", "Violet", "Wendy", "Willow", "Zelina", "Zoey",
]

LAST_NAMES = [
    "Adams", "Alexander", "Alvarez", "Anderson", "Armstrong", "Atlas", "Austin",
    "Avalon", "Baker", "Banks", "Barrett", "Bates", "Bell", "Bishop", "Black",
    "Blade", "Blake", "Blaze", "Bolt", "Bourne", "Briggs", "Brooks", "Brown",
    "Burke", "Burns", "Cage", "Campbell", "Cannon", "Carmine", "Carter",
    "Cassidy", "Castle", "Chance", "Chase", "Clark", "Cole", "Collins",
    "Cooper", "Corbin", "Cross", "Crowe", "Cruz", "Cutter", "Dalton",
    "Daniels", "Dante", "Davis", "Dawson", "Diamond", "Dixon", "Donovan",
    "Drake", "Dunn", "Easton", "Edwards", "Ellis", "Evans", "Falcon",
    "Finlay", "Fisher", "Fletcher", "Ford", "Fox", "Frost", "Fury",
    "Gage", "Garcia", "Garza", "Gibson", "Gold", "Graves", "Gray",
    "Green", "Griffin", "Grimes", "Guerrero", "Gunn", "Guzman", "Hall",
    "Hardy", "Harper", "Harris", "Hart", "Hawk", "Hayes", "Hazard",
    "Henderson", "Hendrix", "Hernandez", "Hill", "Holland", "Holmes",
    "Holt", "Hudson", "Hunter", "Iron", "Ivory", "Jackson", "Jacobs",
    "James", "Jarrett", "Jefferson", "Jenkins", "Johnson", "Jones",
    "Jordan", "Justice", "Kane", "Keane", "Kelly", "Kendrick", "Kennedy",
    "King", "Kingston", "Knight", "Knox", "Kross", "Lane", "Lawson",
    "Lee", "Lewis", "Logan", "Long", "Lopez", "Lux", "Lynch", "Lyons",
    "Mack", "Maddox", "Magnus", "Marshall", "Martin", "Martinez",
    "Mason", "Matthews", "Maxwell", "Mercer", "Miles", "Miller",
    "Mitchell", "Monroe", "Montana", "Moore", "Morgan", "Morrison",
    "Murphy", "Nash", "Neville", "Newman", "Noble", "North", "Nox",
    "Oliver", "Onyx", "Orion", "Orton", "Owen", "Page", "Palmer",
    "Parker", "Patterson", "Payne", "Phoenix", "Pierce", "Porter",
    "Powers", "Price", "Prince", "Quinn", "Raines", "Ramsey", "Raven",
    "Reed", "Reeves", "Regal", "Reid", "Rhodes", "Richards", "Ridge",
    "Riley", "Rivera", "Roberts", "Robinson", "Rodriguez", "Rogers",
    "Romano", "Rose", "Ross", "Rowe", "Rush", "Russell", "Ryan",
    "Ryker", "Samuels", "Sanders", "Santos", "Savage", "Scott", "Sharp",
    "Shaw", "Shepherd", "Silver", "Simmons", "Sinclair", "Slater",
    "Smith", "Snow", "Solace", "Solomon", "Sparks", "Spencer", "Stark",
    "Steel", "Sterling", "Stevens", "Stone", "Storm", "Strickland",
    "Strong", "Sullivan", "Swerve", "Tate", "Taylor", "Thomas",
    "Thompson", "Thunder", "Torres", "Trent", "Tucker", "Turner",
    "Valentine", "Vance", "Vaughn", "Vega", "Vice", "Viper", "Volt",
    "Walker", "Wallace", "Ward", "Warren", "Washington", "Watson",
    "Watts", "Webb", "Wells", "West", "White", "Wilder", "Williams",
    "Wilson", "Wolf", "Wood", "Wright", "Wyatt", "Young", "Ziggler",
]

NICKNAMES_BY_TIER = {
    1: [None, None, None, None, None, None, None,  # Most have no nickname
        "The Kid", "Junior", "Scrappy", "The Rookie", "Baby Face"],
    2: [None, None, None, None,
        "The Prospect", "The Underdog", "The Local Hero", "The Workhorse",
        "The Dark Horse", "Dynamite", "Danger"],
    3: [None, None, None,
        "The Rising Star", "The Future", "The Prodigy", "Lightning",
        "The Warrior", "The Natural", "Showtime", "The Outlaw"],
    4: [None, None,
        "The Ace", "The Machine", "The Hitman", "The Destroyer",
        "The Viper", "The Architect", "The Icon", "The Nightmare",
        "The Boss", "The King", "The Queen"],
    5: ["The Legend", "The Phenom", "The Showstopper", "The Game",
        "The Best in the World", "The Greatest", "The Immortal",
        "The Untouchable", "The Chosen One", "The Franchise"],
}

HOMETOWNS = [
    "New York City, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
    "Philadelphia, PA", "Phoenix, AZ", "San Antonio, TX", "San Diego, CA",
    "Dallas, TX", "Austin, TX", "Jacksonville, FL", "San Francisco, CA",
    "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Boston, MA",
    "Detroit, MI", "Nashville, TN", "Portland, OR", "Las Vegas, NV",
    "Atlanta, GA", "Miami, FL", "Minneapolis, MN", "Tampa, FL",
    "New Orleans, LA", "Cleveland, OH", "Pittsburgh, PA", "Cincinnati, OH",
    "St. Louis, MO", "Kansas City, MO", "Orlando, FL", "Sacramento, CA",
    "Toronto, Canada", "Montreal, Canada", "Calgary, Canada",
    "Vancouver, Canada", "Winnipeg, Canada",
    "Mexico City, Mexico", "Guadalajara, Mexico", "Monterrey, Mexico",
    "Tijuana, Mexico",
    "Tokyo, Japan", "Osaka, Japan", "Nagoya, Japan",
    "London, England", "Manchester, England", "Birmingham, England",
    "Glasgow, Scotland", "Dublin, Ireland", "Belfast, Northern Ireland",
    "Berlin, Germany", "Munich, Germany",
    "Paris, France", "Lyon, France",
    "Madrid, Spain", "Barcelona, Spain",
    "Rome, Italy", "Milan, Italy",
    "São Paulo, Brazil", "Rio de Janeiro, Brazil",
    "Buenos Aires, Argentina",
    "Sydney, Australia", "Melbourne, Australia",
    "Auckland, New Zealand",
    "Johannesburg, South Africa", "Cape Town, South Africa",
    "Lagos, Nigeria",
    "Seoul, South Korea",
    "Mumbai, India", "Delhi, India",
    "Manila, Philippines",
]

FINISHER_NAMES = [
    "The Shutdown", "Lights Out", "Final Chapter", "Breaking Point",
    "Death Valley Driver", "End of Days", "Sudden Impact", "Last Ride",
    "Total Destruction", "Coup de Grace", "Checkmate", "Point of No Return",
    "The Silencer", "Blackout", "Critical Hit", "Flatline",
    "Superkick", "Powerbomb", "DDT", "Stunner", "Cutter", "Spear",
    "Piledriver", "Brainbuster", "Burning Hammer", "Tiger Driver",
    "Package Piledriver", "Canadian Destroyer", "Phoenix Splash",
    "Shooting Star Press", "Frog Splash", "Moonsault", "Spiral Tap",
    "Claymore Kick", "Kinshasa", "Black Mass", "Ripcord Knee",
    "Cross Rhodes", "Sister Abigail", "Tombstone", "Chokeslam",
    "One Winged Angel", "Rain Maker", "Bitter End", "Last Call",
    "Skull Crushing Finale", "Code Red", "Spanish Fly", "Vertebreaker",
    "Go To Sleep", "Styles Clash", "Destino", "Made In Japan",
    "The Reckoning", "Nightmare Driver", "Paradise Lock", "Poison Rana",
    "Swanton Bomb", "Twist of Fate", "Rock Bottom", "F5",
    "Lightning Spiral", "Thunder Driver", "Storm Breaker", "Fire Thunder",
]

SIGNATURE_MOVES = [
    "Suplex", "Dropkick", "Enzuigiri", "Clothesline", "Backbreaker",
    "Neckbreaker", "Slam", "Fisherman Suplex", "German Suplex",
    "Northern Lights Suplex", "Dragon Suplex", "Falcon Arrow",
    "Blue Thunder Bomb", "Michinoku Driver", "Tilt-a-Whirl",
    "Hurricanrana", "Frankensteiner", "Tope Suicida", "Suicide Dive",
    "Plancha", "Springboard Elbow", "Top Rope Elbow", "Leg Drop",
    "Senton", "Splash", "Crossbody", "Tornado DDT", "Snap DDT",
    "Running Knee", "Bicycle Knee", "Spinning Heel Kick",
    "Roundhouse Kick", "Superkick", "Big Boot", "Lariat", "Discus Lariat",
    "Pop-Up Powerbomb", "Sitout Powerbomb", "Running Powerbomb",
    "Spinebuster", "Side Slam", "STO", "Flatliner", "Complete Shot",
]


# ==================== TIER DEFINITIONS ====================

"""
Tier 1: Rookies/Jobbers (Level 1+) - Cheap, low stats
Tier 2: Local talent (Level 5+) - Affordable, decent stats
Tier 3: Rising stars (Level 10+) - Mid-range cost and stats
Tier 4: Established (Level 20+) - Good stats, notable
Tier 5: Main eventers (Level 35+) - Expensive, elite stats
"""

TIER_CONFIG = {
    1: {
        "name": "Rookies & Local Talent",
        "level_required": 1,
        "stat_range": (25, 50),
        "popularity_range": (5, 25),
        "salary_range": (100, 300),
        "age_range": (18, 25),
        "consistency_range": (30, 60),
        "trait_chance": 0.1,
        "max_traits": 1,
        "count_male": 25,
        "count_female": 25,
    },
    2: {
        "name": "Independent Circuit",
        "level_required": 5,
        "stat_range": (35, 60),
        "popularity_range": (15, 40),
        "salary_range": (250, 600),
        "age_range": (21, 30),
        "consistency_range": (40, 70),
        "trait_chance": 0.2,
        "max_traits": 1,
        "count_male": 25,
        "count_female": 25,
    },
    3: {
        "name": "Rising Stars",
        "level_required": 10,
        "stat_range": (45, 75),
        "popularity_range": (30, 55),
        "salary_range": (500, 1200),
        "age_range": (23, 33),
        "consistency_range": (50, 80),
        "trait_chance": 0.4,
        "max_traits": 2,
        "count_male": 20,
        "count_female": 20,
    },
    4: {
        "name": "Established Veterans",
        "level_required": 20,
        "stat_range": (60, 85),
        "popularity_range": (50, 75),
        "salary_range": (1000, 3000),
        "age_range": (26, 38),
        "consistency_range": (60, 90),
        "trait_chance": 0.6,
        "max_traits": 2,
        "count_male": 20,
        "count_female": 20,
    },
    5: {
        "name": "Main Event Stars",
        "level_required": 35,
        "stat_range": (75, 98),
        "popularity_range": (70, 95),
        "salary_range": (2500, 8000),
        "age_range": (28, 42),
        "consistency_range": (75, 95),
        "trait_chance": 0.8,
        "max_traits": 3,
        "count_male": 10,
        "count_female": 10,
    },
}


# Traits available per tier
TRAITS_BY_TIER = {
    1: [
        "underdog",
    ],
    2: [
        "underdog", "tag_specialist", "spot_monkey",
    ],
    3: [
        "spot_monkey", "tag_specialist", "submission_specialist",
        "hardcore_legend", "giant_killer",
    ],
    4: [
        "ring_general", "submission_specialist", "hardcore_legend",
        "giant_killer", "iron_man", "veteran_presence",
        "natural_talent",
    ],
    5: [
        "ring_general", "iron_man", "showstopper",
        "natural_talent", "veteran_presence", "ladder_match_expert",
        "deathmatch_king",
    ],
}


# ==================== GENERATION FUNCTIONS ====================

def _generate_stat(stat_range: tuple, style_bonus: int = 0) -> int:
    """Generate a stat within range with optional style bonus"""
    base = random.randint(stat_range[0], stat_range[1])
    return max(1, min(100, base + style_bonus))


def _get_style_bonuses(style: WrestlingStyle) -> Dict[str, int]:
    """Get stat bonuses based on wrestling style"""
    bonuses = {
        WrestlingStyle.POWERHOUSE: {"power": 20, "speed": -10, "aerial": -10},
        WrestlingStyle.HIGH_FLYER: {"aerial": 20, "speed": 15, "power": -10},
        WrestlingStyle.TECHNICIAN: {"technical": 20, "stamina": 10, "hardcore": -10},
        WrestlingStyle.BRAWLER: {"hardcore": 15, "power": 10, "technical": -10},
        WrestlingStyle.HARDCORE: {"hardcore": 25, "stamina": 10, "speed": -5},
        WrestlingStyle.SHOWMAN: {"charisma": 25, "technical": -5},
        WrestlingStyle.LUCHADOR: {"aerial": 20, "speed": 20, "power": -15},
        WrestlingStyle.STRONG_STYLE: {"power": 10, "technical": 10, "stamina": 10},
        WrestlingStyle.SUBMISSION_ARTIST: {"technical": 20, "stamina": 10, "aerial": -10},
        WrestlingStyle.GIANT: {"power": 25, "speed": -20, "aerial": -20},
        WrestlingStyle.ALL_ROUNDER: {},
    }
    return bonuses.get(style, {})


def generate_wrestler_for_tier(
    tier: int,
    gender: Gender = None,
    used_names: set = None,
) -> Wrestler:
    """Generate a wrestler for a specific tier"""
    config = TIER_CONFIG.get(tier, TIER_CONFIG[1])
    used_names = used_names or set()
    
    # Gender
    if gender is None:
        gender = random.choice([Gender.MALE, Gender.FEMALE])
    
    # Generate unique name
    name = _generate_unique_name(gender, used_names)
    used_names.add(name)
    
    # Nickname (higher tiers more likely)
    tier_nicknames = NICKNAMES_BY_TIER.get(tier, [None])
    nickname = random.choice(tier_nicknames)
    
    # Physical attributes
    if gender == Gender.MALE:
        height = random.randint(66, 80)
        weight = random.randint(180, 300)
    else:
        height = random.randint(60, 72)
        weight = random.randint(110, 180)
    
    # Age
    age = random.randint(config["age_range"][0], config["age_range"][1])
    
    # Wrestling style
    style = random.choice(list(WrestlingStyle))
    
    # Secondary style (higher tiers more likely)
    secondary_style = None
    if random.random() < (tier * 0.15):
        secondary_style = random.choice(list(WrestlingStyle))
        if secondary_style == style:
            secondary_style = None
    
    # Alignment
    alignment = random.choice(list(Alignment))
    
    # Stats with style bonuses
    stat_range = config["stat_range"]
    style_bonuses = _get_style_bonuses(style)
    
    power = _generate_stat(stat_range, style_bonuses.get("power", 0))
    speed = _generate_stat(stat_range, style_bonuses.get("speed", 0))
    technical = _generate_stat(stat_range, style_bonuses.get("technical", 0))
    stamina = _generate_stat(stat_range, style_bonuses.get("stamina", 0))
    charisma = _generate_stat(stat_range, style_bonuses.get("charisma", 0))
    hardcore = _generate_stat(stat_range, style_bonuses.get("hardcore", 0))
    aerial = _generate_stat(stat_range, style_bonuses.get("aerial", 0))
    
    # Giants get size adjustments
    if style == WrestlingStyle.GIANT:
        if gender == Gender.MALE:
            height = random.randint(76, 84)
            weight = random.randint(280, 380)
        else:
            height = random.randint(70, 76)
            weight = random.randint(170, 220)
    
    # Luchadors get size adjustments
    if style == WrestlingStyle.LUCHADOR:
        if gender == Gender.MALE:
            height = random.randint(64, 72)
            weight = random.randint(160, 210)
        else:
            height = random.randint(58, 66)
            weight = random.randint(100, 150)
    
    # Hidden stats (improve with tier)
    consistency = random.randint(
        config["consistency_range"][0],
        config["consistency_range"][1]
    )
    work_ethic = random.randint(30 + (tier * 8), 60 + (tier * 8))
    loyalty = random.randint(30, 90)
    ego = random.randint(max(10, 20 + (tier * 8)), min(100, 40 + (tier * 12)))
    professionalism = random.randint(30 + (tier * 5), 60 + (tier * 8))
    
    # Popularity
    popularity = random.randint(
        config["popularity_range"][0],
        config["popularity_range"][1]
    )
    
    # Salary
    salary = random.randint(
        config["salary_range"][0],
        config["salary_range"][1]
    )
    
    # Traits
    traits = []
    if random.random() < config["trait_chance"]:
        available_traits = TRAITS_BY_TIER.get(tier, [])
        if available_traits:
            num_traits = random.randint(1, config["max_traits"])
            num_traits = min(num_traits, len(available_traits))
            traits = random.sample(available_traits, num_traits)
    
    # Signature moves (more for higher tiers)
    num_sigs = min(tier, 4)
    signatures = random.sample(SIGNATURE_MOVES, num_sigs)
    
    # Injury prone (higher tier = more wear and tear)
    injury_prone = random.randint(20 + (tier * 3), 40 + (tier * 8))
    
    wrestler = Wrestler(
        name=name,
        nickname=nickname,
        age=age,
        gender=gender,
        hometown=random.choice(HOMETOWNS),
        height=height,
        weight=weight,
        primary_style=style,
        secondary_style=secondary_style,
        alignment=alignment,
        power=power,
        speed=speed,
        technical=technical,
        stamina=stamina,
        charisma=charisma,
        hardcore=hardcore,
        aerial=aerial,
        consistency=consistency,
        work_ethic=work_ethic,
        loyalty=loyalty,
        ego=ego,
        professionalism=professionalism,
        popularity=popularity,
        momentum=50,
        morale=70,
        injury_prone=injury_prone,
        salary=salary,
        unique_traits=traits,
        finisher_name=random.choice(FINISHER_NAMES),
        signature_moves=signatures,
    )
    
    wrestler.is_signed = False
    wrestler.contract_length = 0
    
    # Higher tier wrestlers have some career history
    if tier >= 3:
        wrestler.wins = random.randint(50 * (tier - 2), 150 * (tier - 2))
        wrestler.losses = random.randint(20 * (tier - 2), 80 * (tier - 2))
    if tier >= 4:
        wrestler.titles_held = random.randint(1, tier * 2)
    
    return wrestler


def _generate_unique_name(gender: Gender, used_names: set) -> str:
    """Generate a unique wrestler name"""
    attempts = 0
    while attempts < 100:
        if gender == Gender.MALE:
            first = random.choice(FIRST_NAMES_MALE)
        else:
            first = random.choice(FIRST_NAMES_FEMALE)
        
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        if name not in used_names:
            return name
        
        attempts += 1
    
    # Fallback with number
    return f"{first} {last} Jr."


def generate_all_free_agents() -> Dict[int, List[Wrestler]]:
    """
    Generate the complete free agent pool.
    Returns dict organized by tier.
    100 men + 100 women = 200 total
    """
    all_agents = {}
    used_names = set()
    
    for tier in range(1, 6):
        config = TIER_CONFIG[tier]
        tier_agents = []
        
        # Generate males
        for _ in range(config["count_male"]):
            wrestler = generate_wrestler_for_tier(tier, Gender.MALE, used_names)
            tier_agents.append(wrestler)
        
        # Generate females
        for _ in range(config["count_female"]):
            wrestler = generate_wrestler_for_tier(tier, Gender.FEMALE, used_names)
            tier_agents.append(wrestler)
        
        # Shuffle within tier
        random.shuffle(tier_agents)
        all_agents[tier] = tier_agents
    
    return all_agents


def generate_free_agents(count: int = 50, level: int = 1) -> List[Wrestler]:
    """
    Generate free agents appropriate for the player's level.
    Used for backward compatibility.
    """
    all_agents = generate_all_free_agents()
    
    # Filter by level
    available = []
    for tier, agents in all_agents.items():
        tier_config = TIER_CONFIG[tier]
        if level >= tier_config["level_required"]:
            available.extend(agents)
    
    # If we have more than requested, return a subset
    if len(available) > count:
        return random.sample(available, count)
    
    return available


def get_free_agents_for_level(level: int) -> List[Dict]:
    """
    Get free agents organized by tier for a specific level.
    Returns list of dicts with tier info and wrestlers.
    """
    all_agents = generate_all_free_agents()
    
    result = []
    for tier in range(1, 6):
        config = TIER_CONFIG[tier]
        is_unlocked = level >= config["level_required"]
        
        result.append({
            "tier": tier,
            "name": config["name"],
            "level_required": config["level_required"],
            "is_unlocked": is_unlocked,
            "wrestlers": all_agents.get(tier, []) if is_unlocked else [],
            "count": len(all_agents.get(tier, [])),
            "salary_range": config["salary_range"],
            "stat_range": config["stat_range"],
        })
    
    return result


def get_tier_for_level(level: int) -> int:
    """Get the highest tier available at a given level"""
    highest = 1
    for tier, config in TIER_CONFIG.items():
        if level >= config["level_required"]:
            highest = tier
    return highest


def generate_legend(name: str = None) -> Wrestler:
    """Generate a legendary wrestler (Tier 5+)"""
    used_names = set()
    wrestler = generate_wrestler_for_tier(5, used_names=used_names)
    
    if name:
        wrestler.name = name
    
    wrestler.age = random.randint(38, 55)
    wrestler.popularity = random.randint(85, 99)
    wrestler.wins = random.randint(500, 2000)
    wrestler.losses = random.randint(100, 500)
    wrestler.titles_held = random.randint(5, 25)
    wrestler.five_star_matches = random.randint(5, 30)
    wrestler.salary = random.randint(5000, 15000)
    
    return wrestler


# ==================== REFRESH SYSTEM ====================

def refresh_free_agent_pool(
    current_agents: List[Wrestler],
    level: int,
    max_agents: int = 200
) -> List[Wrestler]:
    """
    Refresh the free agent pool.
    Removes some, adds new ones based on level.
    Called periodically (e.g. every 4 weeks).
    """
    # Remove some random agents (simulating them being signed elsewhere)
    if len(current_agents) > 20:
        num_to_remove = random.randint(3, 8)
        for _ in range(num_to_remove):
            if current_agents:
                current_agents.pop(random.randint(0, len(current_agents) - 1))
    
    # Add new agents
    highest_tier = get_tier_for_level(level)
    used_names = {w.name for w in current_agents}
    
    num_to_add = random.randint(3, 8)
    for _ in range(num_to_add):
        if len(current_agents) >= max_agents:
            break
        
        # Weight toward lower tiers
        tier_weights = {1: 40, 2: 30, 3: 20, 4: 8, 5: 2}
        available_tiers = [t for t in range(1, highest_tier + 1)]
        weights = [tier_weights.get(t, 10) for t in available_tiers]
        
        tier = random.choices(available_tiers, weights=weights, k=1)[0]
        
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        wrestler = generate_wrestler_for_tier(tier, gender, used_names)
        current_agents.append(wrestler)
        used_names.add(wrestler.name)
    
    return current_agents