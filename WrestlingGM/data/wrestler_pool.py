"""
Wrestler Pool - Free agent generator + Licensed real-world talent
- Random free agents across all 11 career levels
- LICENSED_WRESTLERS section for real-world talent partnerships
- Indy God pool for released stars (cult favorites)
- Distribution scales with player promotion size

Pulls names from data/wrestler_names.py (single source of truth)
"""

import random
from typing import Dict, List, Optional, Tuple
from classes.wrestler import (
    Wrestler, Gender, WeightClass, WrestlingStyle, Alignment,
    WrestlerLevel, ContractType, CrowdReaction
)
from data.wrestler_names import (
    FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES,
    NICKNAMES_BY_TIER, HOMETOWNS, FINISHER_NAMES, SIGNATURE_MOVES
)


# ==================== CAREER LEVEL STAT TEMPLATES ====================

# Stat ranges for each career level (min, max)
LEVEL_STAT_TEMPLATES = {
    WrestlerLevel.SHOW_READY: {
        "stat_range": (25, 45), "popularity": (15, 30),
        "booking_fee": (200, 500), "reputation": (5, 20),
        "nickname_tier": 1,
    },
    WrestlerLevel.INDY_WRESTLER: {
        "stat_range": (35, 55), "popularity": (25, 40),
        "booking_fee": (400, 800), "reputation": (25, 50),
        "nickname_tier": 1,
    },
    WrestlerLevel.INDY_STAR: {
        "stat_range": (45, 65), "popularity": (35, 50),
        "booking_fee": (700, 1400), "reputation": (55, 100),
        "nickname_tier": 2,
    },
    WrestlerLevel.INDY_DARLING: {
        "stat_range": (55, 70), "popularity": (45, 60),
        "booking_fee": (1200, 2200), "reputation": (105, 200),
        "nickname_tier": 2,
    },
    WrestlerLevel.RISING_STAR: {
        "stat_range": (60, 75), "popularity": (55, 70),
        "booking_fee": (2000, 3500), "reputation": (205, 400),
        "nickname_tier": 3,
    },
    WrestlerLevel.ESTABLISHED: {
        "stat_range": (65, 80), "popularity": (60, 75),
        "booking_fee": (3000, 5500), "reputation": (405, 700),
        "nickname_tier": 3,
    },
    WrestlerLevel.MAIN_EVENTER: {
        "stat_range": (72, 85), "popularity": (70, 85),
        "booking_fee": (5000, 9000), "reputation": (705, 1000),
        "nickname_tier": 4,
    },
    WrestlerLevel.TOP_STAR: {
        "stat_range": (78, 90), "popularity": (80, 92),
        "booking_fee": (8000, 14000), "reputation": (1005, 1500),
        "nickname_tier": 4,
    },
    WrestlerLevel.LEGEND: {
        "stat_range": (85, 95), "popularity": (88, 96),
        "booking_fee": (12000, 22000), "reputation": (1505, 2500),
        "nickname_tier": 5,
    },
    WrestlerLevel.ICON: {
        "stat_range": (90, 100), "popularity": (94, 100),
        "booking_fee": (20000, 40000), "reputation": (2505, 5000),
        "nickname_tier": 5,
    },
    WrestlerLevel.INDY_GOD: {
        "stat_range": (75, 95), "popularity": (75, 95),
        "booking_fee": (10000, 25000), "reputation": (1500, 3000),
        "nickname_tier": 4,
    },
}


# ==================== LICENSED WRESTLERS (Real-World Talent) ====================
# Pre-defined real wrestlers with hand-crafted stats based on their actual personas
# Each entry can be toggled active/inactive when licensing deals are signed

LICENSED_WRESTLERS = {
    "connor_mills": {
        "active": True,  # Set to False to disable until deal is signed
        "name": "Connor Mills",
        "nickname": "True Grit",
        "age": 26,
        "gender": "Male",
        "hometown": "London, England",
        "height": 185,  # 6'01"
        "weight": 181,
        "wrestler_level": WrestlerLevel.RISING_STAR,
        "alignment": Alignment.HEEL,
        "primary_style": WrestlingStyle.TECHNICIAN,
        "secondary_style": WrestlingStyle.STRIKER,
        "stats": {
            "power": 60, "speed": 78, "technical": 85,
            "stamina": 75, "charisma": 72, "hardcore": 55,
            "aerial": 75, "mic_skills": 70, "psychology": 80,
            "toughness": 70,
        },
        "hidden_stats": {
            "consistency": 80, "work_ethic": 85, "loyalty": 65,
            "ego": 60, "professionalism": 80,
        },
        "popularity": 65, "morale": 75, "reputation": 280,
        "booking_fee": 250,
        "finisher_name": "Mills Shot",
        "signature_moves": ["Future Shock DDT", "Disaster Kick", "Springboard Cutter"],
        "unique_traits": ["British Strong Style", "Indie Darling", "Smark Favorite"],
    },

    "michael_oku": {
        "active": True,  # Set to False to disable until deal is signed
        "name": "Michael Oku",
        "nickname": "The OJMO",
        "age": 33,
        "gender": "Male",
        "hometown": "London, England",
        "height": 182,  # 6'0"
        "weight": 176,
        "wrestler_level": WrestlerLevel.INDY_DARLING,
        "alignment": Alignment.FACE,
        "primary_style": WrestlingStyle.HIGH_FLYER,
        "secondary_style": WrestlingStyle.TECHNICIAN,
        "stats": {
            "power": 55, "speed": 88, "technical": 80,
            "stamina": 82, "charisma": 75, "hardcore": 50,
            "aerial": 90, "mic_skills": 68, "psychology": 78,
            "toughness": 70,
        },
        "hidden_stats": {
            "consistency": 85, "work_ethic": 90, "loyalty": 75,
            "ego": 35, "professionalism": 90,
        },
        "popularity": 75, "morale": 85, "reputation": 175,
        "booking_fee": 1200,
        "finisher_name": "Half Crab",
        "signature_moves": ["Frog Splash", "Springboard Moonsault", "Tope Suicida"],
        "unique_traits": ["Underdog Hero", "Submission Specialist", "RevPro Champion"],
    },

    # Template for adding more licensed wrestlers in the future:
    # "wrestler_id": {
    #     "active": False,
    #     "name": "Wrestler Name",
    #     "nickname": "The Nickname",
    #     "age": 30,
    #     "gender": "Male" / "Female",
    #     "hometown": "City, Country",
    #     "height": 72, "weight": 220,
    #     "wrestler_level": WrestlerLevel.MAIN_EVENTER,
    #     "alignment": Alignment.FACE,
    #     "primary_style": WrestlingStyle.ALL_ROUNDER,
    #     "secondary_style": WrestlingStyle.HIGH_FLYER,
    #     "stats": {...10 stats...},
    #     "hidden_stats": {...5 hidden stats...},
    #     "popularity": 70, "morale": 80, "reputation": 750,
    #     "booking_fee": 5000,
    #     "finisher_name": "Their Finisher",
    #     "signature_moves": [...3 moves...],
    #     "unique_traits": [...2-3 traits...],
    # },
}


# ==================== WRESTLER POOL MANAGER ====================

class WrestlerPool:
    """
    Manages free agent generation and licensed talent.
    Generates random wrestlers across all career levels.
    Provides licensed (real-world) wrestler integration.
    """

    def __init__(self):
        self.next_id_num: int = 1
        self.used_names: set = set()
        self.total_generated: int = 0
        self.total_signed: int = 0

    # ==================== NAME GENERATION ====================

    def _generate_unique_name(self, gender: str = None) -> Tuple[str, str]:
        """Generate a unique first/last name combo using shared name pools"""
        if gender is None:
            gender = random.choice(["Male", "Male", "Female"])

        first_pool = FIRST_NAMES_MALE if gender == "Male" else FIRST_NAMES_FEMALE

        attempts = 0
        while attempts < 30:
            first = random.choice(first_pool)
            last = random.choice(LAST_NAMES)
            full_name = f"{first} {last}"
            if full_name not in self.used_names:
                self.used_names.add(full_name)
                return (full_name, gender)
            attempts += 1

        # Fallback: append Jr. if all combos exhausted
        first = random.choice(first_pool)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last} Jr."
        self.used_names.add(full_name)
        return (full_name, gender)

    def _pick_nickname_for_tier(self, tier: int) -> Optional[str]:
        """Pick a tier-appropriate nickname (or None) from shared pool"""
        nicknames = NICKNAMES_BY_TIER.get(tier, [None])
        return random.choice(nicknames)

    # ==================== RANDOM WRESTLER GENERATION ====================

    def generate_wrestler(
        self,
        level: WrestlerLevel = WrestlerLevel.SHOW_READY,
        force_gender: str = None,
        force_alignment: Alignment = None,
        force_style: WrestlingStyle = None,
    ) -> Wrestler:
        """Generate a single random wrestler at the given career level"""
        template = LEVEL_STAT_TEMPLATES.get(level, LEVEL_STAT_TEMPLATES[WrestlerLevel.SHOW_READY])

        full_name, gender = self._generate_unique_name(force_gender)
        nickname = self._pick_nickname_for_tier(template.get("nickname_tier", 1))
        hometown = random.choice(HOMETOWNS)
        age = self._age_for_level(level)
        height = random.randint(66, 78) if gender == "Male" else random.randint(62, 72)
        weight = self._weight_for_gender_and_style(gender, force_style)

        # Pick alignment
        if force_alignment:
            alignment = force_alignment
        else:
            alignment = random.choices(
                [Alignment.FACE, Alignment.HEEL, Alignment.TWEENER, Alignment.X_FACTOR],
                weights=[40, 35, 20, 5],
            )[0]

        # Pick wrestling style
        if force_style:
            primary_style = force_style
        else:
            primary_style = random.choice(list(WrestlingStyle))

        secondary_style = random.choice(list(WrestlingStyle)) if random.random() < 0.6 else None
        if secondary_style == primary_style:
            secondary_style = None

        # Generate stats
        stat_min, stat_max = template["stat_range"]

        # Style-specific stat boosts
        style_boosts = self._get_style_stat_priorities(primary_style)

        stats = {}
        for stat_name in ["power", "speed", "technical", "stamina", "charisma",
                          "hardcore", "aerial", "mic_skills", "psychology", "toughness"]:
            base = random.randint(stat_min, stat_max)
            if stat_name in style_boosts:
                base = min(100, base + random.randint(5, 15))
            stats[stat_name] = base

        # Hidden stats
        hidden_stats = {
            "consistency": random.randint(40, 85),
            "work_ethic": random.randint(40, 90),
            "loyalty": random.randint(30, 85),
            "ego": random.randint(20, 80),
            "professionalism": random.randint(40, 90),
        }

        # Status stats
        pop_min, pop_max = template["popularity"]
        popularity = random.randint(pop_min, pop_max)
        morale = random.randint(60, 90)
        rep_min, rep_max = template["reputation"]
        reputation = random.randint(rep_min, rep_max)

        # Booking fee
        fee_min, fee_max = template["booking_fee"]
        booking_fee = random.randint(fee_min, fee_max)

        # Pick finisher and signatures from shared pool
        finisher = random.choice(FINISHER_NAMES)
        sig_count = random.randint(2, 4)
        signature_moves = random.sample(SIGNATURE_MOVES, min(sig_count, len(SIGNATURE_MOVES)))

        # Build wrestler
        wrestler = Wrestler(
            name=full_name,
            nickname=nickname,
            age=age,
            gender=Gender.MALE if gender == "Male" else Gender.FEMALE,
            hometown=hometown,
            height=height,
            weight=weight,
            primary_style=primary_style,
            secondary_style=secondary_style,
            alignment=alignment,
            wrestler_level=level,
            reputation=reputation,
            popularity=popularity,
            morale=morale,
            booking_fee=booking_fee,
            contract_type=ContractType.PER_APPEARANCE,
            finisher_name=finisher,
            signature_moves=signature_moves,
            **stats,
            **hidden_stats,
        )

        self.total_generated += 1
        return wrestler

    def _age_for_level(self, level: WrestlerLevel) -> int:
        """Generate age appropriate for the career level"""
        age_ranges = {
            WrestlerLevel.SHOW_READY: (19, 26),
            WrestlerLevel.INDY_WRESTLER: (21, 30),
            WrestlerLevel.INDY_STAR: (23, 32),
            WrestlerLevel.INDY_DARLING: (25, 34),
            WrestlerLevel.RISING_STAR: (24, 33),
            WrestlerLevel.ESTABLISHED: (26, 38),
            WrestlerLevel.MAIN_EVENTER: (28, 40),
            WrestlerLevel.TOP_STAR: (28, 42),
            WrestlerLevel.LEGEND: (35, 50),
            WrestlerLevel.ICON: (35, 55),
            WrestlerLevel.INDY_GOD: (32, 45),
        }
        age_range = age_ranges.get(level, (25, 35))
        return random.randint(age_range[0], age_range[1])

    def _weight_for_gender_and_style(self, gender: str, style: WrestlingStyle = None) -> int:
        """Generate weight based on gender and style"""
        if gender == "Male":
            if style == WrestlingStyle.GIANT:
                return random.randint(290, 380)
            elif style == WrestlingStyle.POWERHOUSE:
                return random.randint(255, 295)
            elif style == WrestlingStyle.HIGH_FLYER or style == WrestlingStyle.LUCHADOR:
                return random.randint(165, 210)
            else:
                return random.randint(195, 260)
        else:
            if style == WrestlingStyle.POWERHOUSE:
                return random.randint(170, 220)
            elif style == WrestlingStyle.HIGH_FLYER or style == WrestlingStyle.LUCHADOR:
                return random.randint(115, 155)
            else:
                return random.randint(130, 180)

    def _get_style_stat_priorities(self, style: WrestlingStyle) -> List[str]:
        """Get the stats that get boosted based on wrestling style"""
        priorities = {
            WrestlingStyle.POWERHOUSE: ["power", "toughness"],
            WrestlingStyle.HIGH_FLYER: ["speed", "aerial", "stamina"],
            WrestlingStyle.TECHNICIAN: ["technical", "psychology", "stamina"],
            WrestlingStyle.BRAWLER: ["power", "hardcore", "toughness"],
            WrestlingStyle.HARDCORE: ["hardcore", "toughness", "power"],
            WrestlingStyle.SHOWMAN: ["charisma", "mic_skills"],
            WrestlingStyle.STRIKER: ["power", "speed", "stamina"],
            WrestlingStyle.LUCHADOR: ["aerial", "speed", "technical"],
            WrestlingStyle.GIANT: ["power", "toughness"],
            WrestlingStyle.ALL_ROUNDER: ["technical", "stamina"],
        }
        return priorities.get(style, [])

    # ==================== LICENSED WRESTLERS ====================

    def get_licensed_wrestlers(self, only_active: bool = True) -> List[Wrestler]:
        """Get all licensed (real-world) wrestlers, optionally filtered to active only"""
        wrestlers = []
        for wrestler_id, data in LICENSED_WRESTLERS.items():
            if only_active and not data.get("active", False):
                continue
            try:
                wrestler = self._build_licensed_wrestler(data)
                wrestlers.append(wrestler)
            except Exception as e:
                print(f"Error building licensed wrestler {wrestler_id}: {e}")
        return wrestlers

    def _build_licensed_wrestler(self, data: Dict) -> Wrestler:
        """Build a Wrestler object from licensed talent data"""
        stats = data.get("stats", {})
        hidden = data.get("hidden_stats", {})

        gender = Gender.MALE if data.get("gender", "Male") == "Male" else Gender.FEMALE

        wrestler = Wrestler(
            name=data["name"],
            nickname=data.get("nickname"),
            age=data.get("age", 28),
            gender=gender,
            hometown=data.get("hometown", "Unknown"),
            height=data.get("height", 72),
            weight=data.get("weight", 220),
            primary_style=data.get("primary_style", WrestlingStyle.ALL_ROUNDER),
            secondary_style=data.get("secondary_style"),
            alignment=data.get("alignment", Alignment.FACE),
            wrestler_level=data.get("wrestler_level", WrestlerLevel.RISING_STAR),
            reputation=data.get("reputation", 200),
            power=stats.get("power", 50),
            speed=stats.get("speed", 50),
            technical=stats.get("technical", 50),
            stamina=stats.get("stamina", 50),
            charisma=stats.get("charisma", 50),
            hardcore=stats.get("hardcore", 50),
            aerial=stats.get("aerial", 50),
            mic_skills=stats.get("mic_skills", 50),
            psychology=stats.get("psychology", 50),
            toughness=stats.get("toughness", 50),
            consistency=hidden.get("consistency", 70),
            work_ethic=hidden.get("work_ethic", 75),
            loyalty=hidden.get("loyalty", 70),
            ego=hidden.get("ego", 50),
            professionalism=hidden.get("professionalism", 80),
            popularity=data.get("popularity", 50),
            morale=data.get("morale", 80),
            booking_fee=data.get("booking_fee", 2000),
            contract_type=ContractType.PER_APPEARANCE,
            finisher_name=data.get("finisher_name", "Finisher"),
            signature_moves=data.get("signature_moves", []),
            unique_traits=data.get("unique_traits", []),
        )

        # Mark as licensed
        wrestler.add_trait("Licensed Talent")

        return wrestler

    def get_licensed_wrestler_by_id(self, wrestler_id: str) -> Optional[Wrestler]:
        """Get a specific licensed wrestler by their ID"""
        data = LICENSED_WRESTLERS.get(wrestler_id)
        if not data or not data.get("active", False):
            return None
        return self._build_licensed_wrestler(data)

    def list_licensed_wrestlers_info(self) -> List[Dict]:
        """Get summary info for all licensed wrestlers (for UI display)"""
        info_list = []
        for wrestler_id, data in LICENSED_WRESTLERS.items():
            info_list.append({
                "id": wrestler_id,
                "name": data.get("name"),
                "nickname": data.get("nickname"),
                "active": data.get("active", False),
                "level": data.get("wrestler_level", WrestlerLevel.SHOW_READY).value,
                "alignment": data.get("alignment", Alignment.FACE).value,
                "popularity": data.get("popularity", 50),
                "booking_fee": data.get("booking_fee", 0),
                "hometown": data.get("hometown", ""),
            })
        return info_list

    # ==================== POOL GENERATION ====================

    def generate_starter_pool(
        self,
        target_size: int = 100,
        include_licensed: bool = True,
    ) -> List[Wrestler]:
        """
        Generate the initial free agent pool with distribution across all levels.
        Distribution:
          30% Show Ready / Indy Wrestler (cheap, plentiful)
          25% Indy Star / Indy Darling (mid-range)
          20% Rising Star / Established (premium)
          15% Main Eventer / Top Star (expensive)
          10% Legend / Icon / Indy God (rare)
        """
        wrestlers = []

        # Distribution by level
        distribution = {
            WrestlerLevel.SHOW_READY: int(target_size * 0.18),
            WrestlerLevel.INDY_WRESTLER: int(target_size * 0.12),
            WrestlerLevel.INDY_STAR: int(target_size * 0.15),
            WrestlerLevel.INDY_DARLING: int(target_size * 0.10),
            WrestlerLevel.RISING_STAR: int(target_size * 0.12),
            WrestlerLevel.ESTABLISHED: int(target_size * 0.08),
            WrestlerLevel.MAIN_EVENTER: int(target_size * 0.10),
            WrestlerLevel.TOP_STAR: int(target_size * 0.05),
            WrestlerLevel.LEGEND: int(target_size * 0.05),
            WrestlerLevel.ICON: int(target_size * 0.02),
            WrestlerLevel.INDY_GOD: int(target_size * 0.03),
        }

        for level, count in distribution.items():
            for _ in range(count):
                try:
                    wrestler = self.generate_wrestler(level=level)
                    wrestlers.append(wrestler)
                except Exception as e:
                    print(f"Error generating wrestler at {level.value}: {e}")

        # Add licensed wrestlers
        if include_licensed:
            licensed = self.get_licensed_wrestlers(only_active=True)
            wrestlers.extend(licensed)

        return wrestlers

    def generate_weekly_refresh(self, current_pool_size: int, target_pool_size: int = 80) -> List[Wrestler]:
        """Generate new free agents to refresh the pool weekly"""
        if current_pool_size >= target_pool_size:
            return []

        needed = target_pool_size - current_pool_size
        # Don't refresh too aggressively
        refresh_count = min(needed, random.randint(2, 6))

        new_wrestlers = []
        for _ in range(refresh_count):
            # Mostly mid-tier refreshes
            level = random.choices(
                [
                    WrestlerLevel.SHOW_READY,
                    WrestlerLevel.INDY_WRESTLER,
                    WrestlerLevel.INDY_STAR,
                    WrestlerLevel.INDY_DARLING,
                    WrestlerLevel.RISING_STAR,
                    WrestlerLevel.ESTABLISHED,
                    WrestlerLevel.MAIN_EVENTER,
                ],
                weights=[20, 18, 18, 14, 12, 10, 8],
            )[0]
            wrestler = self.generate_wrestler(level=level)
            new_wrestlers.append(wrestler)

        return new_wrestlers

    def generate_indy_god_pool(self, count: int = 5) -> List[Wrestler]:
        """Generate Indy God free agents (released from majors)"""
        gods = []
        for _ in range(count):
            wrestler = self.generate_wrestler(level=WrestlerLevel.INDY_GOD)
            wrestler.become_indy_god()
            gods.append(wrestler)
        return gods

    # ==================== LICENSED WRESTLER MANAGEMENT ====================

    @staticmethod
    def activate_licensed_wrestler(wrestler_id: str) -> bool:
        """Toggle a licensed wrestler to active (when deal is signed)"""
        if wrestler_id in LICENSED_WRESTLERS:
            LICENSED_WRESTLERS[wrestler_id]["active"] = True
            return True
        return False

    @staticmethod
    def deactivate_licensed_wrestler(wrestler_id: str) -> bool:
        """Toggle a licensed wrestler to inactive (when deal expires)"""
        if wrestler_id in LICENSED_WRESTLERS:
            LICENSED_WRESTLERS[wrestler_id]["active"] = False
            return True
        return False

    @staticmethod
    def get_licensed_wrestler_count() -> Tuple[int, int]:
        """Returns (active_count, total_count)"""
        total = len(LICENSED_WRESTLERS)
        active = sum(1 for d in LICENSED_WRESTLERS.values() if d.get("active", False))
        return (active, total)
