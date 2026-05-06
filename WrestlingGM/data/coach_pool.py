"""
Coach Pool - NPC coach generator
Creates hireable trainers across all specialties and skill tiers
Includes legendary coaches unlocked at high school reputation
"""

import random
from typing import Dict, List, Optional, Tuple
from classes.coach import Coach, CoachType, CoachSpecialty, CoachStatus, SPECIALTY_INFO


# ==================== NAME POOLS (GitHub-Safe) ====================

COACH_FIRST_NAMES_MALE = [
    "Adam", "Bobby", "Brad", "Brian", "Chad", "Chris", "Dean", "Derek",
    "Eric", "Frank", "Greg", "Hector", "Ivan", "Jack", "Jason", "Jeff",
    "Jim", "Joe", "John", "Keith", "Kevin", "Mark", "Mike", "Pat",
    "Paul", "Pete", "Randy", "Ray", "Rick", "Rob", "Ron", "Sam",
    "Scott", "Sean", "Steve", "Ted", "Tim", "Tom", "Tony", "Vince",
    "Wade", "Walter", "Wayne", "Bruno", "Carlos", "Diego", "Hiroshi",
    "Klaus", "Boris", "Marco", "Antonio",
]

COACH_FIRST_NAMES_FEMALE = [
    "Amy", "Anna", "Beth", "Carol", "Dana", "Diana", "Eva", "Grace",
    "Helen", "Jane", "Janet", "Julia", "Karen", "Kim", "Linda", "Lisa",
    "Maria", "Mary", "Michelle", "Nancy", "Patricia", "Rachel", "Rebecca",
    "Sandra", "Sarah", "Sharon", "Susan", "Teresa", "Victoria", "Wendy",
    "Yumi", "Greta", "Catalina", "Olga",
]

COACH_LAST_NAMES = [
    "Adams", "Anderson", "Armstrong", "Banks", "Barrett", "Bishop", "Blake",
    "Brooks", "Brown", "Burke", "Campbell", "Carter", "Clark", "Cole",
    "Cooper", "Cross", "Davis", "Dawson", "Dixon", "Donovan", "Dunn",
    "Edwards", "Evans", "Fisher", "Fletcher", "Ford", "Foster", "Garcia",
    "Gibson", "Graves", "Green", "Griffin", "Hall", "Harper", "Harris",
    "Hayes", "Henderson", "Hernandez", "Hill", "Holmes", "Hudson", "Hunter",
    "Jackson", "Jacobs", "James", "Jenkins", "Johnson", "Jones", "Kelly",
    "Kennedy", "King", "Knight", "Lane", "Lawson", "Lee", "Lewis", "Long",
    "Lopez", "Lynch", "Marshall", "Martin", "Martinez", "Matthews", "Miller",
    "Mitchell", "Monroe", "Moore", "Morgan", "Morrison", "Murphy", "Nash",
    "Nelson", "Newman", "Owen", "Palmer", "Parker", "Patterson", "Pierce",
    "Porter", "Powers", "Price", "Reed", "Reeves", "Reid", "Richards",
    "Riley", "Rivera", "Roberts", "Robinson", "Rodriguez", "Rogers",
    "Russell", "Ryan", "Sanders", "Scott", "Sharp", "Shaw", "Shepherd",
    "Simmons", "Sinclair", "Smith", "Spencer", "Stevens", "Sullivan",
    "Taylor", "Thomas", "Thompson", "Torres", "Turner", "Vaughn", "Walker",
    "Wallace", "Ward", "Watson", "Webb", "Wells", "West", "White",
    "Williams", "Wilson", "Wright", "Young",
]


# ==================== COACH BACKGROUNDS ====================

VETERAN_BACKGROUNDS = [
    "Former 20-year ring veteran with respected reputation.",
    "Trained at the legendary dungeons of pro wrestling.",
    "Multi-time tag team champion turned trainer.",
    "Submission specialist who never lost a shoot fight.",
    "Old-school territory wrestler with countless miles.",
    "Career midcarder turned excellent teacher.",
    "Former amateur wrestling champion turned pro.",
    "Lucha libre veteran with high-flying expertise.",
    "Hardcore legend with scars to prove it.",
    "Technical wizard with a focus on chain wrestling.",
]

NPC_BACKGROUNDS = [
    "Trained dozens of current pros at their previous school.",
    "Combat sports background, transitioned to pro wrestling.",
    "Former MMA coach now teaching wrestling fundamentals.",
    "Strength and conditioning specialist for athletes.",
    "Theatre and performance coach with wrestling expertise.",
    "Former wrestling promoter now focused on training.",
    "Independent circuit veteran with diverse experience.",
    "Junior college wrestling coach with pro background.",
    "Boxing trainer who fell in love with pro wrestling.",
    "Yoga and movement specialist for athletes.",
    "Former gymnastics coach for high-flyers.",
    "Sports psychology expert focused on character work.",
    "Powerlifting champion turned wrestling instructor.",
    "Stunt coordinator with wrestling background.",
    "Personal trainer specializing in combat athletes.",
]

LEGEND_BACKGROUNDS = [
    "Hall of Fame inductee. Trained generations of champions.",
    "Considered one of the greatest trainers in wrestling history.",
    "Their gym has produced more world champions than any other.",
    "Legendary figure who learned from the all-time greats.",
    "Multiple Hall of Fame inductions. Living wrestling history.",
    "The mentor every wrestler dreams of training under.",
    "Their methods revolutionized professional wrestling.",
    "A walking encyclopedia of wrestling knowledge.",
    "Former world champion turned legendary teacher.",
    "Pioneer of multiple wrestling styles still used today.",
]


# ==================== COACH POOL MANAGER ====================

class CoachPool:
    """Manages the pool of available NPC coaches for hire"""

    def __init__(self):
        self.available_coaches: List[Coach] = []
        self.legendary_coaches: List[Coach] = []  # Unlocked at high reputation
        self.next_id_num: int = 1
        self.weeks_active: int = 0
        self.total_generated: int = 0
        self.total_hired: int = 0
        self.used_names: set = set()

    # ==================== NAME GENERATION ====================

    def _generate_unique_name(self, gender: str = None) -> str:
        """Generate a unique coach name"""
        if gender is None:
            gender = random.choice(["Male", "Male", "Male", "Female"])  # Coach pool skews male

        first_pool = COACH_FIRST_NAMES_MALE if gender == "Male" else COACH_FIRST_NAMES_FEMALE

        attempts = 0
        while attempts < 20:
            first = random.choice(first_pool)
            last = random.choice(COACH_LAST_NAMES)
            full_name = f"{first} {last}"
            if full_name not in self.used_names:
                self.used_names.add(full_name)
                return full_name
            attempts += 1

        # Fallback
        first = random.choice(first_pool)
        last = random.choice(COACH_LAST_NAMES)
        full_name = f"Coach {first} {last}"
        self.used_names.add(full_name)
        return full_name

    # ==================== COACH GENERATION ====================

    def _next_coach_id(self) -> str:
        cid = f"npc_coach_{self.next_id_num}"
        self.next_id_num += 1
        return cid

    def generate_npc_coach(
        self,
        skill_min: int = 40,
        skill_max: int = 80,
        force_specialty: CoachSpecialty = None,
    ) -> Coach:
        """Generate a single NPC coach for hire"""
        name = self._generate_unique_name()
        age = random.randint(35, 60)

        # Pick specialty
        if force_specialty:
            specialty = force_specialty
        else:
            specialty = random.choice(list(CoachSpecialty))

        # Skill rating
        skill_rating = random.randint(skill_min, skill_max)

        # Cost based on skill
        weekly_cost = self._calculate_weekly_cost(skill_rating, CoachType.NPC)
        hire_cost = self._calculate_hire_cost(skill_rating, CoachType.NPC)

        # Background
        background = random.choice(NPC_BACKGROUNDS)
        description = self._build_description(name, specialty, skill_rating)

        coach = Coach(
            id=self._next_coach_id(),
            name=name,
            coach_type=CoachType.NPC,
            specialty=specialty,
            skill_rating=skill_rating,
            weekly_cost=weekly_cost,
            hire_cost=hire_cost,
            age=age,
            background=background,
            description=description,
        )
        coach.update_effectiveness()

        self.total_generated += 1
        return coach

    def generate_legendary_coach(self) -> Coach:
        """Generate a legendary Hall of Fame caliber coach"""
        name = self._generate_unique_name()
        age = random.randint(55, 75)

        specialty = random.choice(list(CoachSpecialty))
        skill_rating = random.randint(85, 100)

        weekly_cost = self._calculate_weekly_cost(skill_rating, CoachType.LEGEND)
        hire_cost = self._calculate_hire_cost(skill_rating, CoachType.LEGEND)

        background = random.choice(LEGEND_BACKGROUNDS)
        description = self._build_legendary_description(name, specialty, skill_rating)

        coach = Coach(
            id=self._next_coach_id(),
            name=name,
            coach_type=CoachType.LEGEND,
            specialty=specialty,
            skill_rating=skill_rating,
            weekly_cost=weekly_cost,
            hire_cost=hire_cost,
            age=age,
            background=background,
            description=description,
            is_legendary=True,
        )
        coach.update_effectiveness()

        self.total_generated += 1
        return coach

    def _calculate_weekly_cost(self, skill: int, coach_type: CoachType) -> int:
        """Calculate weekly cost based on skill and type"""
        if coach_type == CoachType.LEGEND:
            # $3000 - $5000/week
            return 3000 + int((skill - 85) * 130)
        elif coach_type == CoachType.NPC:
            # $400 - $2000/week scaled by skill
            base = 400
            scaled = int((skill - 40) * 40)
            return base + scaled
        else:  # VETERAN (handled in coach.py)
            return 200

    def _calculate_hire_cost(self, skill: int, coach_type: CoachType) -> int:
        """Calculate one-time hire fee"""
        if coach_type == CoachType.LEGEND:
            # $10,000 - $25,000
            return 10000 + int((skill - 85) * 1000)
        elif coach_type == CoachType.NPC:
            # $1,000 - $5,000
            return 1000 + int((skill - 40) * 100)
        return 0

    def _build_description(self, name: str, specialty: CoachSpecialty, skill: int) -> str:
        """Build a flavor description for the coach"""
        spec_info = SPECIALTY_INFO.get(specialty, {})
        spec_desc = spec_info.get("description", "")

        if skill >= 75:
            return f"{name} is an elite trainer specializing in {specialty.value}. {spec_desc}"
        elif skill >= 60:
            return f"{name} is a respected veteran of {specialty.value} training. {spec_desc}"
        elif skill >= 45:
            return f"{name} is an experienced trainer with knowledge of {specialty.value}. {spec_desc}"
        else:
            return f"{name} is a trainer focused on {specialty.value}. {spec_desc}"

    def _build_legendary_description(self, name: str, specialty: CoachSpecialty, skill: int) -> str:
        """Build description for legendary coaches"""
        spec_info = SPECIALTY_INFO.get(specialty, {})
        spec_desc = spec_info.get("description", "")

        return (f"🌟 LEGEND: {name} is a legendary figure in {specialty.value} training. "
                f"{spec_desc} Wrestlers come from around the world to learn from them.")

    # ==================== WEEKLY GENERATION ====================

    def generate_weekly_coach_pool(
        self,
        school_reputation: int,
        current_pool_size: int = 0,
    ) -> List[Coach]:
        """Refresh the available coach pool weekly"""
        self.weeks_active += 1

        # Maintain pool of 4-8 NPC coaches based on reputation
        if school_reputation >= 60:
            target_pool_size = 8
        elif school_reputation >= 40:
            target_pool_size = 6
        elif school_reputation >= 20:
            target_pool_size = 5
        else:
            target_pool_size = 4

        coaches_needed = max(0, target_pool_size - current_pool_size)
        new_coaches = []

        # Generate fresh NPC coaches
        for _ in range(coaches_needed):
            # Skill range based on school reputation
            if school_reputation >= 70:
                skill_range = (55, 85)
            elif school_reputation >= 40:
                skill_range = (45, 75)
            elif school_reputation >= 20:
                skill_range = (40, 65)
            else:
                skill_range = (35, 55)

            coach = self.generate_npc_coach(
                skill_min=skill_range[0],
                skill_max=skill_range[1],
            )
            new_coaches.append(coach)
            self.available_coaches.append(coach)

        # Maybe add a legendary coach (rare, only at high reputation)
        if school_reputation >= 80 and len(self.legendary_coaches) < 2:
            if random.random() < 0.10:  # 10% chance per week
                legend = self.generate_legendary_coach()
                self.legendary_coaches.append(legend)
                new_coaches.append(legend)

        # Age out old coaches (they leave after 4 weeks if not hired)
        self._age_coaches()

        return new_coaches

    def _age_coaches(self):
        """Remove coaches who've been available too long"""
        # Track weeks_available on each coach (using weeks_employed as a proxy when not hired)
        # We'll use a simple approach: remove some random coaches each week to keep pool fresh
        if len(self.available_coaches) > 8:
            # Remove oldest coaches (first ones in list)
            num_to_remove = len(self.available_coaches) - 8
            for _ in range(num_to_remove):
                if self.available_coaches:
                    removed = self.available_coaches.pop(0)
                    if removed.name in self.used_names:
                        self.used_names.discard(removed.name)

    # ==================== COACH MANAGEMENT ====================

    def get_coach(self, coach_id: str) -> Optional[Coach]:
        """Get a specific coach from the pool"""
        for coach in self.available_coaches + self.legendary_coaches:
            if coach.id == coach_id:
                return coach
        return None

    def hire_coach(self, coach_id: str) -> Optional[Coach]:
        """Hire a coach from the pool, removing them from availability"""
        for i, coach in enumerate(self.available_coaches):
            if coach.id == coach_id:
                self.available_coaches.pop(i)
                self.total_hired += 1
                return coach

        for i, coach in enumerate(self.legendary_coaches):
            if coach.id == coach_id:
                self.legendary_coaches.pop(i)
                self.total_hired += 1
                return coach

        return None

    def get_available_coaches(self) -> List[Coach]:
        """Get all available NPC coaches"""
        return list(self.available_coaches)

    def get_legendary_coaches(self) -> List[Coach]:
        """Get available legendary coaches (premium tier)"""
        return list(self.legendary_coaches)

    def get_coaches_by_specialty(self, specialty: CoachSpecialty) -> List[Coach]:
        """Filter available coaches by specialty"""
        all_coaches = self.available_coaches + self.legendary_coaches
        return [c for c in all_coaches if c.specialty == specialty]

    def get_coaches_by_skill_tier(self, min_skill: int, max_skill: int = 100) -> List[Coach]:
        """Filter coaches by skill range"""
        all_coaches = self.available_coaches + self.legendary_coaches
        return [c for c in all_coaches if min_skill <= c.skill_rating <= max_skill]

    def get_pool_count(self) -> int:
        return len(self.available_coaches) + len(self.legendary_coaches)

    def clear_pool(self):
        """Clear all available coaches (for testing or refresh)"""
        for coach in self.available_coaches + self.legendary_coaches:
            if coach.name in self.used_names:
                self.used_names.discard(coach.name)
        self.available_coaches = []
        self.legendary_coaches = []

    # ==================== INITIAL POOL GENERATION ====================

    def generate_starter_pool(self, school_reputation: int = 10) -> List[Coach]:
        """Generate the initial pool of coaches when starting the school"""
        starter_coaches = []

        # 4 entry-level NPC coaches
        for _ in range(4):
            coach = self.generate_npc_coach(skill_min=40, skill_max=60)
            starter_coaches.append(coach)
            self.available_coaches.append(coach)

        return starter_coaches

    # ==================== UI HELPERS ====================

    def get_filter_options(self) -> Dict:
        """Get UI filter options"""
        return {
            "specialties": [
                {"value": s.value, "label": s.value, "icon": SPECIALTY_INFO[s]["icon"]}
                for s in CoachSpecialty
            ],
            "skill_tiers": [
                {"value": "rookie", "label": "Rookie (0-44)", "min": 0, "max": 44},
                {"value": "journeyman", "label": "Journeyman (45-59)", "min": 45, "max": 59},
                {"value": "veteran", "label": "Veteran (60-74)", "min": 60, "max": 74},
                {"value": "elite", "label": "Elite (75-89)", "min": 75, "max": 89},
                {"value": "legend", "label": "Legend (90+)", "min": 90, "max": 100},
            ],
        }

    def get_pool_summary(self) -> Dict:
        """Get summary stats for UI display"""
        return {
            "total_available": len(self.available_coaches),
            "legendary_available": len(self.legendary_coaches),
            "specialties_covered": len(set(c.specialty for c in self.available_coaches + self.legendary_coaches)),
            "avg_weekly_cost": int(sum(c.weekly_cost for c in self.available_coaches) / max(len(self.available_coaches), 1)),
            "min_hire_cost": min((c.hire_cost for c in self.available_coaches), default=0),
            "max_hire_cost": max((c.hire_cost for c in self.available_coaches + self.legendary_coaches), default=0),
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "available_coaches": [c.to_dict() for c in self.available_coaches],
            "legendary_coaches": [c.to_dict() for c in self.legendary_coaches],
            "next_id_num": self.next_id_num,
            "weeks_active": self.weeks_active,
            "total_generated": self.total_generated,
            "total_hired": self.total_hired,
            "used_names": list(self.used_names),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoachPool":
        pool = cls()
        pool.next_id_num = data.get("next_id_num", 1)
        pool.weeks_active = data.get("weeks_active", 0)
        pool.total_generated = data.get("total_generated", 0)
        pool.total_hired = data.get("total_hired", 0)
        pool.used_names = set(data.get("used_names", []))

        for cd in data.get("available_coaches", []):
            try:
                pool.available_coaches.append(Coach.from_dict(cd))
            except Exception:
                pass

        for cd in data.get("legendary_coaches", []):
            try:
                pool.legendary_coaches.append(Coach.from_dict(cd))
            except Exception:
                pass

        return pool
