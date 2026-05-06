"""
Trainee Pool - Random applicant generator
Creates weekly trainee prospects with diverse backgrounds
Supports passive applicants + paid scouting for premium prospects
"""

import random
from typing import Dict, List, Optional, Tuple
from classes.trainee import Trainee, TraineeSpecialization


# ==================== NAME POOLS (GitHub-Safe) ====================

ALL_FIRST_NAMES = [
    ("M", "Adam"), ("M", "Alex"), ("M", "Austin"), ("M", "Billy"), ("M", "Bobby"),
    ("M", "Brad"), ("M", "Brandon"), ("M", "Brent"), ("M", "Brian"), ("M", "Caleb"),
    ("M", "Carlos"), ("M", "Casey"), ("M", "Chad"), ("M", "Chase"), ("M", "Chris"),
    ("M", "Clay"), ("M", "Cody"), ("M", "Cole"), ("M", "Connor"), ("M", "Craig"),
    ("M", "Damian"), ("M", "Danny"), ("M", "Darius"), ("M", "Dean"), ("M", "Derek"),
    ("M", "Devin"), ("M", "Diego"), ("M", "Dominic"), ("M", "Drake"), ("M", "Drew"),
    ("M", "Dustin"), ("M", "Dylan"), ("M", "Eddie"), ("M", "Eli"), ("M", "Eric"),
    ("M", "Ethan"), ("M", "Evan"), ("M", "Felix"), ("M", "Finn"), ("M", "Frank"),
    ("M", "Garrett"), ("M", "Grant"), ("M", "Greg"), ("M", "Hector"), ("M", "Hunter"),
    ("M", "Isaiah"), ("M", "Ivan"), ("M", "Jack"), ("M", "Jackson"), ("M", "Jake"),
    ("M", "James"), ("M", "Jared"), ("M", "Jason"), ("M", "Jay"), ("M", "Jeff"),
    ("M", "Jeremy"), ("M", "Jesse"), ("M", "Jimmy"), ("M", "Joe"), ("M", "John"),
    ("M", "Johnny"), ("M", "Jordan"), ("M", "Josh"), ("M", "Julian"), ("M", "Justin"),
    ("M", "Keith"), ("M", "Kenny"), ("M", "Kevin"), ("M", "Kyle"), ("M", "Lance"),
    ("M", "Leo"), ("M", "Liam"), ("M", "Logan"), ("M", "Lucas"), ("M", "Luke"),
    ("M", "Marco"), ("M", "Marcus"), ("M", "Mark"), ("M", "Mason"), ("M", "Matt"),
    ("M", "Max"), ("M", "Michael"), ("M", "Miguel"), ("M", "Mike"), ("M", "Milo"),
    ("M", "Nathan"), ("M", "Nick"), ("M", "Noah"), ("M", "Oliver"), ("M", "Omar"),
    ("M", "Oscar"), ("M", "Owen"), ("M", "Patrick"), ("M", "Paul"), ("M", "Pete"),
    ("M", "Phoenix"), ("M", "Preston"), ("M", "Quinn"), ("M", "Rafael"), ("M", "Randy"),
    ("M", "Ray"), ("M", "Reno"), ("M", "Rex"), ("M", "Rick"), ("M", "Ricky"),
    ("M", "Rob"), ("M", "Roman"), ("M", "Ronin"), ("M", "Ryan"), ("M", "Sam"),
    ("M", "Santiago"), ("M", "Scott"), ("M", "Sean"), ("M", "Sebastian"), ("M", "Seth"),
    ("M", "Shane"), ("M", "Shawn"), ("M", "Simon"), ("M", "Spencer"), ("M", "Steve"),
    ("M", "Tanner"), ("M", "Ted"), ("M", "Theo"), ("M", "Thomas"), ("M", "Tim"),
    ("M", "Titus"), ("M", "Tom"), ("M", "Tony"), ("M", "Travis"), ("M", "Trevor"),
    ("M", "Troy"), ("M", "Tyler"), ("M", "Victor"), ("M", "Vince"), ("M", "Wade"),
    ("M", "Walker"), ("M", "Wesley"), ("M", "Will"), ("M", "Xavier"), ("M", "Zack"),
    ("M", "Zane"),
    ("F", "Abby"), ("F", "Alicia"), ("F", "Amanda"), ("F", "Amber"),
    ("F", "Amy"), ("F", "Anna"), ("F", "Aria"), ("F", "Ashley"),
    ("F", "Athena"), ("F", "Beth"), ("F", "Blair"), ("F", "Brandi"),
    ("F", "Britt"), ("F", "Brittany"), ("F", "Brooke"), ("F", "Cameron"),
    ("F", "Carmen"), ("F", "Cassandra"), ("F", "Catalina"), ("F", "Chelsea"),
    ("F", "Chloe"), ("F", "Claire"), ("F", "Crystal"), ("F", "Dana"),
    ("F", "Dani"), ("F", "Daniella"), ("F", "Dawn"), ("F", "Diana"),
    ("F", "Elena"), ("F", "Eliza"), ("F", "Ella"), ("F", "Emily"),
    ("F", "Emma"), ("F", "Eva"), ("F", "Faith"), ("F", "Gabriella"),
    ("F", "Gigi"), ("F", "Grace"), ("F", "Haley"), ("F", "Hannah"),
    ("F", "Holly"), ("F", "Ivy"), ("F", "Jade"), ("F", "Jamie"),
    ("F", "Jasmine"), ("F", "Jenna"), ("F", "Jessica"), ("F", "Jocelyn"),
    ("F", "Julia"), ("F", "Kaitlyn"), ("F", "Kara"), ("F", "Kate"),
    ("F", "Katie"), ("F", "Kelly"), ("F", "Kenzie"), ("F", "Kim"),
    ("F", "Kira"), ("F", "Lacey"), ("F", "Laura"), ("F", "Layla"),
    ("F", "Lexi"), ("F", "Lila"), ("F", "Lily"), ("F", "Lisa"),
    ("F", "Luna"), ("F", "Macy"), ("F", "Madisyn"), ("F", "Maria"), ("F", "Marina"),
    ("F", "Maya"), ("F", "Megan"), ("F", "Melissa"), ("F", "Michelle"),
    ("F", "Mila"), ("F", "Mollie"), ("F", "Morgan"), ("F", "Nadia"),
    ("F", "Nina"), ("F", "Olivia"), ("F", "Penelope"), ("F", "Peyton"),
    ("F", "Piper"), ("F", "Quinn"), ("F", "Rachel"), ("F", "Raquel"),
    ("F", "Rebeca"), ("F", "Riley"), ("F", "Rosa"), ("F", "Rosie"),
    ("F", "Ruby"), ("F", "Sakura"), ("F", "Salma"), ("F", "Sasha"), ("F", "Selena"),
    ("F", "Shakira"), ("F", "Shania"), ("F", "Shannon"), ("F", "Sharon"),
    ("F", "Sheila"), ("F", "Shelby"), ("F", "Sienna"), ("F", "Sierra"),
    ("F", "Sigrid"), ("F", "Simone"), ("F", "Siobhan"), ("F", "Skylar"),
    ("F", "Sloane"), ("F", "Sofia"), ("F", "Solana"), ("F", "Sonia"),
    ("F", "Sophia"), ("F", "Stacy"), ("F", "Stella"), ("F", "Stephanie"),
    ("F", "Sukie"), ("F", "Summer"), ("F", "Suri"), ("F", "Susan"), ("F", "Tara"),
    ("F", "Tasha"), ("F", "Taylor"), ("F", "Tessa"),
    ("F", "Tiffany"), ("F", "Valentina"), ("F", "Vanessa"), ("F", "Victoria"),
    ("F", "Violet"), ("F", "Wendy"), ("F", "Willow"), ("F", "Zoey"),
]

# Helper functions to get gendered name lists
FIRST_NAMES_MALE = [name for gender, name in ALL_FIRST_NAMES if gender == "M"]
FIRST_NAMES_FEMALE = [name for gender, name in ALL_FIRST_NAMES if gender == "F"]

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

NICKNAMES_PREFIX = [
    "The", "Big", "Lil'", "Sweet", "Mean", "Wild", "Cold",
    "Hot", "Fast", "Slow", "Smooth", "Crazy", "Quiet", "Loud",
]

NICKNAMES_DESCRIPTOR = [
    "Phenom", "Prodigy", "Beast", "Machine", "Legend", "Heartbreaker",
    "Wildcard", "Hammer", "Bullet", "Storm",
    "Demon", "Angel", "Outlaw", "Renegade", "Showstopper",
    "Future", "Truth", "Comeback Kid", "Chosen One", "Diamond", "Outsider",
]

HOMETOWNS = [
    # USA
    "Brooklyn, NY", "Detroit, MI", "Chicago, IL", "Philadelphia, PA",
    "Memphis, TN", "Atlanta, GA", "Dallas, TX", "Houston, TX",
    "Los Angeles, CA", "Phoenix, AZ", "Denver, CO", "Seattle, WA",
    "Boston, MA", "Miami, FL", "Tampa, FL", "Orlando, FL",
    "Pittsburgh, PA", "Cleveland, OH", "Minneapolis, MN", "St. Louis, MO",
    # International
    "Tokyo, Japan", "Osaka, Japan", "Mexico City, Mexico",
    "London, England", "Manchester, England", "Glasgow, Scotland",
    "Toronto, Canada", "Montreal, Canada", "Vancouver, Canada",
    "Sydney, Australia", "Melbourne, Australia",
    "Berlin, Germany", "Hamburg, Germany", "Munich, Germany",
    "Madrid, Spain", "Barcelona, Spain", "Rome, Italy",
    "Paris, France", "Buenos Aires, Argentina", "Sao Paulo, Brazil",
    "Seoul, South Korea", "Mumbai, India", "Dublin, Ireland",
]

BACKGROUNDS = [
    "Former amateur wrestler",
    "Trained in martial arts since childhood",
    "Football scholarship dropout",
    "Lifelong wrestling fan",
    "Backyard wrestling veteran",
    "Powerlifter looking for a new challenge",
    "Theatre kid who loves performance",
    "MMA fighter switching disciplines",
    "Bodybuilder turned grappler",
    "Crossfit athlete with a passion for wrestling",
    "Family wrestling lineage (3rd generation)",
    "Former gymnast",
    "High school sports star",
    "Trained in lucha libre back home",
    "Catch wrestling enthusiast",
    "Boxing background",
    "Self-taught wrestler from rural town",
    "Dance background brings unique style",
    "Stuntman looking for a new path",
    "Military veteran starting fresh",
]


# ==================== APPLICANT QUALITY TIERS ====================

class ApplicantTier:
    """Quality tier for trainee applicants"""
    WALK_IN = "walk_in"          # Free, lowest quality
    BASIC = "basic"              # Standard quality
    PROMISING = "promising"      # Above average
    PREMIUM = "premium"          # Paid scouting only
    BLUE_CHIP = "blue_chip"      # Rare, paid scouting only


TIER_INFO = {
    ApplicantTier.WALK_IN: {
        "name": "Walk-In",
        "icon": "🚶",
        "color": "#6b7280",
        "quality_modifier": 0.7,
        "natural_talent_chance": 0.02,
        "problem_child_chance": 0.10,
        "scouting_cost": 0,
        "description": "Off the street. Low expectations.",
    },
    ApplicantTier.BASIC: {
        "name": "Standard Applicant",
        "icon": "📝",
        "color": "#3b82f6",
        "quality_modifier": 1.0,
        "natural_talent_chance": 0.05,
        "problem_child_chance": 0.07,
        "scouting_cost": 0,
        "description": "Average prospect with potential.",
    },
    ApplicantTier.PROMISING: {
        "name": "Promising Prospect",
        "icon": "⭐",
        "color": "#10b981",
        "quality_modifier": 1.25,
        "natural_talent_chance": 0.10,
        "problem_child_chance": 0.05,
        "scouting_cost": 500,
        "description": "Has shown real potential. Worth investing in.",
    },
    ApplicantTier.PREMIUM: {
        "name": "Premium Recruit",
        "icon": "💎",
        "color": "#a855f7",
        "quality_modifier": 1.5,
        "natural_talent_chance": 0.20,
        "problem_child_chance": 0.03,
        "scouting_cost": 2500,
        "description": "Elite prospect. Coaches are excited.",
    },
    ApplicantTier.BLUE_CHIP: {
        "name": "Blue Chip Talent",
        "icon": "🌟",
        "color": "#fbbf24",
        "quality_modifier": 1.8,
        "natural_talent_chance": 0.40,
        "problem_child_chance": 0.02,
        "scouting_cost": 7500,
        "description": "Once-in-a-generation prospect. Sign immediately.",
    },
}


# ==================== TRAINEE POOL MANAGER ====================

class TraineePool:
    """Manages the pool of available trainee applicants"""

    def __init__(self):
        self.available_applicants: List[Dict] = []
        self.next_id_num: int = 1
        self.weeks_active: int = 0
        self.total_generated: int = 0
        self.total_signed: int = 0
        self.used_names: set = set()  # Track used names to avoid duplicates

    # ==================== NAME GENERATION ====================

    def _generate_unique_name(self, gender: str = None) -> Tuple[str, str]:
        """Generate a unique first/last name combo"""
        if gender is None:
            gender = random.choice(["Male", "Male", "Female"])

        first_pool = FIRST_NAMES_MALE if gender == "Male" else FIRST_NAMES_FEMALE

        attempts = 0
        while attempts < 20:
            first = random.choice(first_pool)
            last = random.choice(LAST_NAMES)
            full_name = f"{first} {last}"
            if full_name not in self.used_names:
                self.used_names.add(full_name)
                return (full_name, gender)
            attempts += 1

        # Fallback: add a number suffix
        first = random.choice(first_pool)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last} Jr."
        self.used_names.add(full_name)
        return (full_name, gender)

    def _generate_nickname(self) -> str:
        """Generate an optional nickname"""
        if random.random() < 0.4:
            prefix = random.choice(NICKNAMES_PREFIX)
            descriptor = random.choice(NICKNAMES_DESCRIPTOR)
            return f"{prefix} {descriptor}"
        return ""

    # ==================== APPLICANT GENERATION ====================

    def generate_applicant(
        self,
        tier: str = ApplicantTier.BASIC,
        monthly_tuition: int = 150,
        week: int = 0,
        year: int = 1,
        force_gender: str = None,
    ) -> Dict:
        """Generate a single trainee applicant"""
        tier_data = TIER_INFO.get(tier, TIER_INFO[ApplicantTier.BASIC])

        # Generate identity
        full_name, gender = self._generate_unique_name(force_gender)
        nickname = self._generate_nickname()
        age = random.randint(18, 30)
        hometown = random.choice(HOMETOWNS)
        background = random.choice(BACKGROUNDS)

        # Create the trainee object
        trainee_id = f"trainee_{self.next_id_num}"
        self.next_id_num += 1

        trainee = Trainee.generate_random_trainee(
            trainee_id=trainee_id,
            name=full_name,
            age=age,
            gender=gender,
            monthly_tuition=monthly_tuition,
            week=week,
            year=year,
            quality_modifier=tier_data["quality_modifier"],
        )
        trainee.hometown = hometown

        # Override trait roll based on tier
        trainee.is_natural_talent = random.random() < tier_data["natural_talent_chance"]
        trainee.is_problem_child = random.random() < tier_data["problem_child_chance"]

        # High potential check
        avg_stat = (trainee.strength + trainee.speed + trainee.technique +
                    trainee.stamina + trainee.toughness) / 5
        if avg_stat >= 38:
            trainee.is_high_potential = True

        # Build applicant data structure
        applicant = {
            "trainee": trainee,
            "tier": tier,
            "tier_data": tier_data,
            "nickname": nickname,
            "background": background,
            "week_appeared": week,
            "year_appeared": year,
            "weeks_available": 0,
            "preview_stats": self._build_preview_stats(trainee, tier),
        }

        self.total_generated += 1
        return applicant

    def _build_preview_stats(self, trainee: Trainee, tier: str) -> Dict:
        """Build preview stats display for the recruitment screen"""
        # Higher tiers reveal more accurate stats
        accuracy = TIER_INFO.get(tier, {}).get("quality_modifier", 1.0)

        if accuracy >= 1.5:
            # Premium+ shows exact stats
            return {
                "physical_avg": (trainee.strength + trainee.speed + trainee.stamina + trainee.toughness) / 4,
                "mental_avg": (trainee.charisma + trainee.mic_skills + trainee.psychology) / 3,
                "technique": trainee.technique,
                "overall": trainee.get_overall_rating(),
                "is_exact": True,
            }
        elif accuracy >= 1.0:
            # Standard shows approximate
            return {
                "physical_avg": int((trainee.strength + trainee.speed + trainee.stamina + trainee.toughness) / 4 / 5) * 5,
                "mental_avg": int((trainee.charisma + trainee.mic_skills + trainee.psychology) / 3 / 5) * 5,
                "technique": int(trainee.technique / 5) * 5,
                "overall": int(trainee.get_overall_rating() / 5) * 5,
                "is_exact": False,
            }
        else:
            # Walk-in only shows vague description
            ovr = trainee.get_overall_rating()
            if ovr >= 50:
                desc = "Looks promising"
            elif ovr >= 35:
                desc = "Could go either way"
            else:
                desc = "Very raw"
            return {
                "description": desc,
                "is_exact": False,
                "vague": True,
            }

    # ==================== WEEKLY GENERATION ====================

    def generate_weekly_applicants(
        self,
        school_reputation: int,
        school_capacity: int,
        current_trainees: int,
        monthly_tuition: int,
        week: int = 0,
        year: int = 1,
    ) -> List[Dict]:
        """Generate the weekly batch of passive walk-in applicants"""
        self.weeks_active += 1

        # Don't generate if school is full
        if current_trainees >= school_capacity:
            return []

        # Number of applicants based on school reputation
        if school_reputation >= 80:
            num_applicants = random.randint(3, 5)
        elif school_reputation >= 60:
            num_applicants = random.randint(2, 4)
        elif school_reputation >= 40:
            num_applicants = random.randint(2, 3)
        elif school_reputation >= 20:
            num_applicants = random.randint(1, 2)
        else:
            num_applicants = random.randint(0, 2)

        # Cap by capacity
        space_available = school_capacity - current_trainees
        num_applicants = min(num_applicants, space_available)

        new_applicants = []
        for _ in range(num_applicants):
            # Tier distribution based on reputation
            tier = self._roll_applicant_tier(school_reputation)
            applicant = self.generate_applicant(
                tier=tier,
                monthly_tuition=monthly_tuition,
                week=week,
                year=year,
            )
            new_applicants.append(applicant)
            self.available_applicants.append(applicant)

        # Age existing applicants - they leave after 3 weeks
        self._age_applicants()

        return new_applicants

    def _roll_applicant_tier(self, school_reputation: int) -> str:
        """Roll for applicant tier based on school reputation"""
        roll = random.random()

        # Better reputation = better odds for higher tier walk-ins
        if school_reputation >= 80:
            if roll < 0.10: return ApplicantTier.PROMISING
            if roll < 0.50: return ApplicantTier.BASIC
            return ApplicantTier.WALK_IN
        elif school_reputation >= 60:
            if roll < 0.05: return ApplicantTier.PROMISING
            if roll < 0.45: return ApplicantTier.BASIC
            return ApplicantTier.WALK_IN
        elif school_reputation >= 40:
            if roll < 0.30: return ApplicantTier.BASIC
            return ApplicantTier.WALK_IN
        elif school_reputation >= 20:
            if roll < 0.20: return ApplicantTier.BASIC
            return ApplicantTier.WALK_IN
        else:
            if roll < 0.10: return ApplicantTier.BASIC
            return ApplicantTier.WALK_IN

    def _age_applicants(self):
        """Increment time available - applicants leave after 3 weeks"""
        kept = []
        for applicant in self.available_applicants:
            applicant["weeks_available"] += 1
            if applicant["weeks_available"] < 3:
                kept.append(applicant)
            else:
                # Free up the name
                trainee = applicant.get("trainee")
                if trainee and trainee.name in self.used_names:
                    self.used_names.discard(trainee.name)
        self.available_applicants = kept

    # ==================== PAID SCOUTING ====================

    def scout_for_prospects(
        self,
        scouting_tier: str,
        budget: int,
        monthly_tuition: int,
        week: int = 0,
        year: int = 1,
    ) -> Tuple[Optional[Dict], int, str]:
        """
        Pay to scout for a higher-tier prospect.
        Returns: (applicant_dict_or_None, cost_paid, message)
        """
        if scouting_tier not in [ApplicantTier.PROMISING, ApplicantTier.PREMIUM, ApplicantTier.BLUE_CHIP]:
            return (None, 0, "Invalid scouting tier")

        tier_data = TIER_INFO[scouting_tier]
        cost = tier_data["scouting_cost"]

        if budget < cost:
            return (None, 0, f"Not enough budget. Need ${cost:,}")

        # Blue chip has a chance to fail (rare prospect)
        if scouting_tier == ApplicantTier.BLUE_CHIP:
            if random.random() < 0.4:
                return (None, cost, "Scouts came back empty. No blue chip found this time.")

        applicant = self.generate_applicant(
            tier=scouting_tier,
            monthly_tuition=monthly_tuition,
            week=week,
            year=year,
        )
        self.available_applicants.append(applicant)

        return (applicant, cost, f"Scout found a {tier_data['name']}!")

    # ==================== APPLICANT MANAGEMENT ====================

    def get_applicant(self, trainee_id: str) -> Optional[Dict]:
        """Get a specific applicant by trainee ID"""
        for applicant in self.available_applicants:
            if applicant["trainee"].id == trainee_id:
                return applicant
        return None

    def remove_applicant(self, trainee_id: str) -> bool:
        """Remove applicant from pool (after signing or rejection)"""
        for i, applicant in enumerate(self.available_applicants):
            if applicant["trainee"].id == trainee_id:
                self.available_applicants.pop(i)
                return True
        return False

    def sign_applicant(self, trainee_id: str) -> Optional[Trainee]:
        """Sign an applicant - returns the Trainee object and removes from pool"""
        applicant = self.get_applicant(trainee_id)
        if not applicant:
            return None

        trainee = applicant["trainee"]
        self.remove_applicant(trainee_id)
        self.total_signed += 1
        return trainee

    def get_available_applicants(self) -> List[Dict]:
        """Get all current applicants"""
        return list(self.available_applicants)

    def get_applicants_by_tier(self, tier: str) -> List[Dict]:
        """Filter applicants by tier"""
        return [a for a in self.available_applicants if a.get("tier") == tier]

    def get_applicant_count(self) -> int:
        return len(self.available_applicants)

    def clear_pool(self):
        """Clear all applicants (for testing or reset)"""
        for applicant in self.available_applicants:
            trainee = applicant.get("trainee")
            if trainee and trainee.name in self.used_names:
                self.used_names.discard(trainee.name)
        self.available_applicants = []

    # ==================== UI HELPERS ====================

    def get_tier_color(self, tier: str) -> str:
        return TIER_INFO.get(tier, {}).get("color", "#6b7280")

    def get_tier_icon(self, tier: str) -> str:
        return TIER_INFO.get(tier, {}).get("icon", "📝")

    def get_tier_name(self, tier: str) -> str:
        return TIER_INFO.get(tier, {}).get("name", "Unknown")

    def get_scouting_options(self) -> List[Dict]:
        """Get available paid scouting options for UI display"""
        return [
            {
                "tier": ApplicantTier.PROMISING,
                "name": TIER_INFO[ApplicantTier.PROMISING]["name"],
                "icon": TIER_INFO[ApplicantTier.PROMISING]["icon"],
                "color": TIER_INFO[ApplicantTier.PROMISING]["color"],
                "cost": TIER_INFO[ApplicantTier.PROMISING]["scouting_cost"],
                "description": TIER_INFO[ApplicantTier.PROMISING]["description"],
                "guarantee": "Guaranteed find",
            },
            {
                "tier": ApplicantTier.PREMIUM,
                "name": TIER_INFO[ApplicantTier.PREMIUM]["name"],
                "icon": TIER_INFO[ApplicantTier.PREMIUM]["icon"],
                "color": TIER_INFO[ApplicantTier.PREMIUM]["color"],
                "cost": TIER_INFO[ApplicantTier.PREMIUM]["scouting_cost"],
                "description": TIER_INFO[ApplicantTier.PREMIUM]["description"],
                "guarantee": "Guaranteed find",
            },
            {
                "tier": ApplicantTier.BLUE_CHIP,
                "name": TIER_INFO[ApplicantTier.BLUE_CHIP]["name"],
                "icon": TIER_INFO[ApplicantTier.BLUE_CHIP]["icon"],
                "color": TIER_INFO[ApplicantTier.BLUE_CHIP]["color"],
                "cost": TIER_INFO[ApplicantTier.BLUE_CHIP]["scouting_cost"],
                "description": TIER_INFO[ApplicantTier.BLUE_CHIP]["description"],
                "guarantee": "60% find chance",
            },
        ]

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "available_applicants": [
                {
                    "trainee": a["trainee"].to_dict(),
                    "tier": a["tier"],
                    "nickname": a.get("nickname", ""),
                    "background": a.get("background", ""),
                    "week_appeared": a.get("week_appeared", 0),
                    "year_appeared": a.get("year_appeared", 1),
                    "weeks_available": a.get("weeks_available", 0),
                    "preview_stats": a.get("preview_stats", {}),
                }
                for a in self.available_applicants
            ],
            "next_id_num": self.next_id_num,
            "weeks_active": self.weeks_active,
            "total_generated": self.total_generated,
            "total_signed": self.total_signed,
            "used_names": list(self.used_names),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TraineePool":
        pool = cls()
        pool.next_id_num = data.get("next_id_num", 1)
        pool.weeks_active = data.get("weeks_active", 0)
        pool.total_generated = data.get("total_generated", 0)
        pool.total_signed = data.get("total_signed", 0)
        pool.used_names = set(data.get("used_names", []))

        for ad in data.get("available_applicants", []):
            try:
                tier = ad.get("tier", ApplicantTier.BASIC)
                trainee = Trainee.from_dict(ad["trainee"])
                applicant = {
                    "trainee": trainee,
                    "tier": tier,
                    "tier_data": TIER_INFO.get(tier, TIER_INFO[ApplicantTier.BASIC]),
                    "nickname": ad.get("nickname", ""),
                    "background": ad.get("background", ""),
                    "week_appeared": ad.get("week_appeared", 0),
                    "year_appeared": ad.get("year_appeared", 1),
                    "weeks_available": ad.get("weeks_available", 0),
                    "preview_stats": ad.get("preview_stats", {}),
                }
                pool.available_applicants.append(applicant)
            except Exception:
                pass

        return pool
