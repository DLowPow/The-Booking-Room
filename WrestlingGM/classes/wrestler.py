"""
Wrestler Class - Core entity for all wrestlers in the game
NEW: Career levels (Show Ready → Icon → Indy God), alignment with crowd reactions,
morale states with gameplay effects, signature moves, contract types, traits that matter
"""

import random
from enum import Enum
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field


# ==================== ENUMS ====================

class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"


class WeightClass(Enum):
    JUNIOR = "Junior Heavyweight"
    CRUISERWEIGHT = "Cruiserweight"
    MIDDLEWEIGHT = "Middleweight"
    HEAVYWEIGHT = "Heavyweight"
    SUPER_HEAVYWEIGHT = "Super Heavyweight"


class WrestlingStyle(Enum):
    ALL_ROUNDER = "All-Rounder"
    POWERHOUSE = "Powerhouse"
    HIGH_FLYER = "High-Flyer"
    TECHNICIAN = "Technician"
    BRAWLER = "Brawler"
    HARDCORE = "Hardcore"
    SHOWMAN = "Showman"
    STRIKER = "Striker"
    LUCHADOR = "Luchador"
    GIANT = "Giant"


class Alignment(Enum):
    MEGA_FACE = "Mega Face"
    FACE = "Face"
    TWEENER = "Tweener"
    HEEL = "Heel"
    MEGA_HEEL = "Mega Heel"
    X_FACTOR = "X-Factor"
    COOLED_OFF = "Cooled Off"


class CrowdReaction(Enum):
    LOVED = "Loved"
    CHEERED = "Cheered"
    RESPECTED = "Respected"
    MIXED = "Mixed Reaction"
    BOOED = "Booed"
    HATED = "Hated"
    DEAD_SILENT = "Dead Silent"
    CULT_FOLLOWING = "Cult Following"


class MoraleState(Enum):
    FIRED_UP = "Fired Up"
    HAPPY = "Happy"
    STABLE = "Stable"
    UNHAPPY = "Unhappy"
    ANGRY = "Angry"
    DONE = "Done"


class WrestlerLevel(Enum):
    SHOW_READY = "Show Ready"
    INDY_WRESTLER = "Indy Wrestler"
    INDY_STAR = "Indy Star"
    INDY_DARLING = "Indy Darling"
    RISING_STAR = "Rising Star"
    ESTABLISHED = "Established Talent"
    MAIN_EVENTER = "Main Eventer"
    TOP_STAR = "Top Star"
    LEGEND = "Legend"
    ICON = "Icon"
    INDY_GOD = "Indy God"


class ContractType(Enum):
    PER_APPEARANCE = "Per Appearance"
    EXCLUSIVE = "Exclusive"
    LEGENDS_DEAL = "Legends Deal"
    DEVELOPMENTAL = "Developmental"
    HANDSHAKE = "Handshake Deal"


# ==================== CONSTANTS ====================

# Reputation thresholds for level progression
LEVEL_REPUTATION_THRESHOLDS = {
    WrestlerLevel.SHOW_READY: 0,
    WrestlerLevel.INDY_WRESTLER: 21,
    WrestlerLevel.INDY_STAR: 51,
    WrestlerLevel.INDY_DARLING: 101,
    WrestlerLevel.RISING_STAR: 201,
    WrestlerLevel.ESTABLISHED: 401,
    WrestlerLevel.MAIN_EVENTER: 701,
    WrestlerLevel.TOP_STAR: 1001,
    WrestlerLevel.LEGEND: 1501,
    WrestlerLevel.ICON: 2501,
}

LEVEL_INFO = {
    WrestlerLevel.SHOW_READY: {
        "icon": "🎫", "color": "#6b7280", "tier": 1,
        "description": "Just graduated. Ready for indie shows.",
        "fee_multiplier": 1.0,
    },
    WrestlerLevel.INDY_WRESTLER: {
        "icon": "🤼", "color": "#10b981", "tier": 2,
        "description": "Working the indie scene regularly.",
        "fee_multiplier": 1.3,
    },
    WrestlerLevel.INDY_STAR: {
        "icon": "⭐", "color": "#3b82f6", "tier": 3,
        "description": "Standing out on the indies.",
        "fee_multiplier": 1.7,
    },
    WrestlerLevel.INDY_DARLING: {
        "icon": "💎", "color": "#06b6d4", "tier": 4,
        "description": "Beloved on the indies. Buzz building.",
        "fee_multiplier": 2.2,
    },
    WrestlerLevel.RISING_STAR: {
        "icon": "📈", "color": "#a855f7", "tier": 5,
        "description": "On the verge of breaking through.",
        "fee_multiplier": 2.8,
    },
    WrestlerLevel.ESTABLISHED: {
        "icon": "🌟", "color": "#8b5cf6", "tier": 6,
        "description": "Proven main roster talent.",
        "fee_multiplier": 3.5,
    },
    WrestlerLevel.MAIN_EVENTER: {
        "icon": "🎤", "color": "#ec4899", "tier": 7,
        "description": "Carries shows. Main event caliber.",
        "fee_multiplier": 5.0,
    },
    WrestlerLevel.TOP_STAR: {
        "icon": "👑", "color": "#f59e0b", "tier": 8,
        "description": "Face of a promotion. Draws money.",
        "fee_multiplier": 7.5,
    },
    WrestlerLevel.LEGEND: {
        "icon": "🏆", "color": "#fbbf24", "tier": 9,
        "description": "Hall of Fame caliber.",
        "fee_multiplier": 10.0,
    },
    WrestlerLevel.ICON: {
        "icon": "⚡", "color": "#eab308", "tier": 10,
        "description": "Industry-defining figure. Once in a generation.",
        "fee_multiplier": 15.0,
    },
    WrestlerLevel.INDY_GOD: {
        "icon": "😈", "color": "#dc2626", "tier": 11,
        "description": "Released from a major. Now an indie legend with massive cult following.",
        "fee_multiplier": 8.0,
    },
}

# Morale state thresholds (high to low)
MORALE_THRESHOLDS = [
    (90, MoraleState.FIRED_UP),
    (70, MoraleState.HAPPY),
    (50, MoraleState.STABLE),
    (30, MoraleState.UNHAPPY),
    (10, MoraleState.ANGRY),
    (0, MoraleState.DONE),
]

MORALE_EFFECTS = {
    MoraleState.FIRED_UP: {
        "match_rating_mod": 0.5, "promo_quality": 1.2,
        "icon": "🔥", "color": "#dc2626",
        "description": "Performing at peak level",
    },
    MoraleState.HAPPY: {
        "match_rating_mod": 0.2, "promo_quality": 1.1,
        "icon": "😊", "color": "#10b981",
        "description": "Motivated and ready",
    },
    MoraleState.STABLE: {
        "match_rating_mod": 0.0, "promo_quality": 1.0,
        "icon": "😐", "color": "#6b7280",
        "description": "Doing the job",
    },
    MoraleState.UNHAPPY: {
        "match_rating_mod": -0.2, "promo_quality": 0.85,
        "icon": "😟", "color": "#f59e0b",
        "description": "Going through the motions",
    },
    MoraleState.ANGRY: {
        "match_rating_mod": -0.4, "promo_quality": 0.7,
        "icon": "😡", "color": "#ef4444",
        "description": "Phoning it in. Walkout risk.",
    },
    MoraleState.DONE: {
        "match_rating_mod": -0.6, "promo_quality": 0.5,
        "icon": "🚪", "color": "#7c2d12",
        "description": "Demands release. Refuses to perform.",
    },
}


# ==================== WRESTLER CLASS ====================

class Wrestler:
    """Complete wrestler entity with career progression, alignment, morale that matters"""

    def __init__(
        self,
        # Identity
        name: str,
        nickname: Optional[str] = None,
        age: int = 25,
        gender: Gender = Gender.MALE,
        hometown: str = "Unknown",
        # Physical
        height: int = 72,
        weight: int = 220,
        # Wrestling Style
        primary_style: WrestlingStyle = WrestlingStyle.ALL_ROUNDER,
        secondary_style: Optional[WrestlingStyle] = None,
        alignment: Alignment = Alignment.FACE,
        # Career Level
        wrestler_level: WrestlerLevel = WrestlerLevel.SHOW_READY,
        reputation: int = 0,
        # Core Stats (1-100)
        power: int = 50,
        speed: int = 50,
        technical: int = 50,
        stamina: int = 50,
        charisma: int = 50,
        hardcore: int = 50,
        aerial: int = 50,
        mic_skills: int = 50,
        psychology: int = 50,
        toughness: int = 50,
        # Hidden Stats
        consistency: int = 50,
        work_ethic: int = 50,
        loyalty: int = 50,
        ego: int = 50,
        professionalism: int = 50,
        # Status
        popularity: int = 30,
        momentum: int = 50,
        morale: int = 75,
        injury_prone: int = 50,
        fatigue: int = 0,
        # Contract
        contract_type: ContractType = ContractType.PER_APPEARANCE,
        booking_fee: int = 500,
        contract_length: int = 52,
        is_exclusive: bool = False,
        # Special
        unique_traits: Optional[List[str]] = None,
        finisher_name: str = "",
        signature_moves: Optional[List[str]] = None,
    ):
        # Identity
        self.name = name
        self.nickname = nickname
        self.age = age
        self.gender = gender
        self.hometown = hometown

        # Physical
        self.height = height
        self.weight = weight
        self.weight_class = self._calculate_weight_class()

        # Wrestling Style & Alignment
        self.primary_style = primary_style
        self.secondary_style = secondary_style
        self.alignment = alignment
        self.previous_alignment: Optional[Alignment] = None
        self.alignment_change_week: int = 0
        self.crowd_reaction = self._derive_crowd_reaction()

        # Career Level
        self.wrestler_level = wrestler_level
        self.reputation = reputation

        # Core Stats
        self.power = self._clamp_stat(power)
        self.speed = self._clamp_stat(speed)
        self.technical = self._clamp_stat(technical)
        self.stamina = self._clamp_stat(stamina)
        self.charisma = self._clamp_stat(charisma)
        self.hardcore = self._clamp_stat(hardcore)
        self.aerial = self._clamp_stat(aerial)
        self.mic_skills = self._clamp_stat(mic_skills)
        self.psychology = self._clamp_stat(psychology)
        self.toughness = self._clamp_stat(toughness)

        # Hidden Stats
        self.consistency = self._clamp_stat(consistency)
        self.work_ethic = self._clamp_stat(work_ethic)
        self.loyalty = self._clamp_stat(loyalty)
        self.ego = self._clamp_stat(ego)
        self.professionalism = self._clamp_stat(professionalism)

        # Status
        self.popularity = self._clamp_stat(popularity)
        self.momentum = self._clamp_stat(momentum)
        self.morale = self._clamp_stat(morale)
        self.injury_prone = self._clamp_stat(injury_prone)
        self.fatigue = self._clamp_stat(fatigue)

        # Injury
        self.is_injured = False
        self.injury_weeks_remaining = 0
        self.injury_type: Optional[str] = None
        self.injury_severity: str = ""

        # Contract
        self.contract_type = contract_type
        self.booking_fee = booking_fee
        self.contract_length = contract_length
        self.is_exclusive = is_exclusive
        self.is_signed = True
        self.weeks_signed = 0

        # Indy God status (released from a major)
        self.is_indy_god = False
        self.weeks_as_indy_god = 0
        self.previous_promotions: List[str] = []

        # Special
        self.unique_traits = unique_traits or []
        self.finisher_name = finisher_name or self._generate_finisher_name()
        self.signature_moves = signature_moves or []

        # Career Tracking
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.current_win_streak = 0
        self.current_loss_streak = 0
        self.titles_held = 0
        self.title_reigns_total = 0
        self.five_star_matches = 0
        self.four_star_matches = 0
        self.career_matches = 0
        self.best_match_rating = 0.0

        # Storyline tracking
        self.active_storyline_count = 0
        self.last_storyline_match_week = 0

    # ==================== CALCULATED PROPERTIES ====================

    @property
    def overall_rating(self) -> int:
        """Calculate overall rating from core stats"""
        stats = [
            self.power, self.speed, self.technical, self.stamina,
            self.charisma, self.hardcore, self.aerial,
            self.mic_skills, self.psychology, self.toughness,
        ]
        return int(sum(stats) / len(stats))

    @property
    def display_name(self) -> str:
        if self.nickname:
            return f'{self.name} "{self.nickname}"'
        return self.name

    @property
    def full_display_name(self) -> str:
        """Display name with level icon"""
        level_icon = LEVEL_INFO.get(self.wrestler_level, {}).get("icon", "")
        return f"{level_icon} {self.display_name}"

    @property
    def win_percentage(self) -> float:
        total = self.wins + self.losses + self.draws
        if total == 0:
            return 0.0
        return (self.wins / total) * 100

    @property
    def level_number(self) -> int:
        """Numeric tier 1-11 for level checks"""
        return LEVEL_INFO.get(self.wrestler_level, {}).get("tier", 1)

    @property
    def morale_state(self) -> MoraleState:
        """Get current morale state from value"""
        for threshold, state in MORALE_THRESHOLDS:
            if self.morale >= threshold:
                return state
        return MoraleState.DONE

    # ==================== INTERNAL HELPERS ====================

    def _clamp_stat(self, value: int) -> int:
        return max(1, min(100, value))

    def _calculate_weight_class(self) -> WeightClass:
        if self.weight < 200:
            return WeightClass.JUNIOR
        elif self.weight < 220:
            return WeightClass.CRUISERWEIGHT
        elif self.weight < 240:
            return WeightClass.MIDDLEWEIGHT
        elif self.weight < 265:
            return WeightClass.HEAVYWEIGHT
        else:
            return WeightClass.SUPER_HEAVYWEIGHT

    def _derive_crowd_reaction(self) -> CrowdReaction:
        """Derive crowd reaction from alignment + popularity"""
        align_map = {
            Alignment.MEGA_FACE: CrowdReaction.LOVED,
            Alignment.FACE: CrowdReaction.CHEERED,
            Alignment.TWEENER: CrowdReaction.MIXED,
            Alignment.HEEL: CrowdReaction.BOOED,
            Alignment.MEGA_HEEL: CrowdReaction.HATED,
            Alignment.X_FACTOR: CrowdReaction.CULT_FOLLOWING,
            Alignment.COOLED_OFF: CrowdReaction.DEAD_SILENT,
        }
        return align_map.get(self.alignment, CrowdReaction.MIXED)

    def _generate_finisher_name(self) -> str:
        """Generate a generic finisher name based on style"""
        finishers = {
            WrestlingStyle.POWERHOUSE: ["The Slam", "Powerbomb of Doom", "Ground Zero"],
            WrestlingStyle.HIGH_FLYER: ["Sky Drop", "Top Rope Finish", "Gravity"],
            WrestlingStyle.TECHNICIAN: ["The Lock", "Submission Special", "The Hold"],
            WrestlingStyle.BRAWLER: ["The Knockout", "Final Strike", "End of Days"],
            WrestlingStyle.HARDCORE: ["The Devastator", "Pain & Suffering", "The Massacre"],
            WrestlingStyle.SHOWMAN: ["The Showstopper", "Spotlight Special", "The Curtain Call"],
            WrestlingStyle.STRIKER: ["The Knockout Blow", "One Hitter", "Lights Out"],
            WrestlingStyle.LUCHADOR: ["El Final", "Aerial Assault", "The Vuelta"],
            WrestlingStyle.GIANT: ["The Crusher", "Mountain Falls", "The Avalanche"],
            WrestlingStyle.ALL_ROUNDER: ["The Finisher", "Match Ender", "Game Over"],
        }
        options = finishers.get(self.primary_style, ["Finisher"])
        return random.choice(options)

    # ==================== LEVEL & REPUTATION ====================

    def add_reputation(self, amount: int) -> Optional[Dict]:
        """Add reputation and check for level-up"""
        if self.is_indy_god:
            # Indy Gods don't level up further
            return None

        old_level = self.wrestler_level
        self.reputation = max(0, self.reputation + amount)

        # Check for level-up
        new_level = self._calculate_level_from_reputation()
        if new_level != old_level:
            self.wrestler_level = new_level
            return {
                "leveled_up": True,
                "old_level": old_level.value,
                "new_level": new_level.value,
                "icon": LEVEL_INFO.get(new_level, {}).get("icon", ""),
            }
        return None

    def _calculate_level_from_reputation(self) -> WrestlerLevel:
        """Determine wrestler level based on reputation"""
        if self.is_indy_god:
            return WrestlerLevel.INDY_GOD

        # Find highest level whose threshold is met
        sorted_thresholds = sorted(
            LEVEL_REPUTATION_THRESHOLDS.items(),
            key=lambda x: -x[1]
        )
        for level, threshold in sorted_thresholds:
            if level == WrestlerLevel.INDY_GOD:
                continue
            if self.reputation >= threshold:
                return level
        return WrestlerLevel.SHOW_READY

    def become_indy_god(self):
        """Convert wrestler to Indy God status (called when released)"""
        self.is_indy_god = True
        self.previous_alignment = self.alignment
        self.wrestler_level = WrestlerLevel.INDY_GOD
        self.popularity = min(100, self.popularity + 25)
        # Indy Gods get a cult following
        if self.alignment not in [Alignment.MEGA_FACE, Alignment.MEGA_HEEL]:
            self.alignment = Alignment.X_FACTOR
        self.crowd_reaction = CrowdReaction.CULT_FOLLOWING
        self.add_trait("Indy God")
        self.add_trait("Released from Major Promotion")

    # ==================== ALIGNMENT & CROWD REACTION ====================

    def change_alignment(self, new_alignment: Alignment, week: int = 0) -> Dict:
        """Change wrestler alignment (heel/face turn)"""
        old_alignment = self.alignment
        self.previous_alignment = old_alignment
        self.alignment = new_alignment
        self.alignment_change_week = week
        self.crowd_reaction = self._derive_crowd_reaction()

        # Popularity dip during transition
        self.popularity = max(10, self.popularity - 10)

        return {
            "wrestler": self.name,
            "old_alignment": old_alignment.value,
            "new_alignment": new_alignment.value,
            "is_heel_turn": new_alignment in [Alignment.HEEL, Alignment.MEGA_HEEL],
            "is_face_turn": new_alignment in [Alignment.FACE, Alignment.MEGA_FACE],
        }

    def update_crowd_reaction(self):
        """Recalculate crowd reaction based on alignment + popularity"""
        if self.popularity >= 80:
            if self.alignment in [Alignment.FACE, Alignment.MEGA_FACE]:
                self.alignment = Alignment.MEGA_FACE
                self.crowd_reaction = CrowdReaction.LOVED
            elif self.alignment in [Alignment.HEEL, Alignment.MEGA_HEEL]:
                self.alignment = Alignment.MEGA_HEEL
                self.crowd_reaction = CrowdReaction.HATED
        elif self.popularity < 25:
            self.alignment = Alignment.COOLED_OFF
            self.crowd_reaction = CrowdReaction.DEAD_SILENT
        else:
            self.crowd_reaction = self._derive_crowd_reaction()

    # ==================== PERFORMANCE & MATCH ====================

    def get_performance_rating(self) -> int:
        """Calculate tonight's performance"""
        base = self.overall_rating

        # Consistency variance
        variance = int((100 - self.consistency) * 0.3)
        roll = random.randint(-variance, variance)

        # Fatigue penalty
        fatigue_penalty = int(self.fatigue * 0.2)

        # Morale modifier (now uses morale state effects)
        morale_mod = MORALE_EFFECTS.get(self.morale_state, {}).get("match_rating_mod", 0)
        morale_modifier = int(morale_mod * 20)  # Convert star rating mod to performance mod

        # Momentum bonus
        momentum_modifier = int((self.momentum - 50) * 0.15)

        # Injury penalty
        injury_penalty = 15 if self.is_injured else 0

        # Indy God bonus
        indy_god_bonus = 8 if self.is_indy_god else 0

        # Crowd reaction bonus
        reaction_bonus = 0
        if self.crowd_reaction == CrowdReaction.LOVED:
            reaction_bonus = 8
        elif self.crowd_reaction == CrowdReaction.HATED:
            reaction_bonus = 6
        elif self.crowd_reaction == CrowdReaction.CULT_FOLLOWING:
            reaction_bonus = 7
        elif self.crowd_reaction == CrowdReaction.DEAD_SILENT:
            reaction_bonus = -10

        performance = (base + roll - fatigue_penalty + morale_modifier
                       + momentum_modifier - injury_penalty
                       + indy_god_bonus + reaction_bonus)
        return self._clamp_stat(performance)

    def get_match_rating_modifier(self) -> float:
        """Get match rating modifier from morale state"""
        return MORALE_EFFECTS.get(self.morale_state, {}).get("match_rating_mod", 0.0)

    def add_fatigue(self, amount: int):
        self.fatigue = self._clamp_stat(self.fatigue + amount)

    def rest(self, days: int = 7):
        recovery = days * 5
        self.fatigue = max(0, self.fatigue - recovery)

    # ==================== INJURY ====================

    def injure(self, injury_type: str, weeks: int, severity: str = "Moderate"):
        self.is_injured = True
        self.injury_type = injury_type
        self.injury_weeks_remaining = weeks
        self.injury_severity = severity
        self.morale = max(1, self.morale - 15)

    def heal(self):
        if self.is_injured:
            self.injury_weeks_remaining -= 1
            if self.injury_weeks_remaining <= 0:
                self.is_injured = False
                self.injury_type = None
                self.injury_weeks_remaining = 0
                self.injury_severity = ""

    # ==================== MORALE & MOMENTUM ====================

    def adjust_momentum(self, amount: int):
        self.momentum = self._clamp_stat(self.momentum + amount)

    def adjust_popularity(self, amount: int):
        self.popularity = self._clamp_stat(self.popularity + amount)
        self.update_crowd_reaction()

    def adjust_morale(self, amount: int):
        self.morale = self._clamp_stat(self.morale + amount)

    def will_walk_out(self) -> bool:
        """Check if low-morale wrestler will walk out"""
        if self.morale_state == MoraleState.DONE:
            return random.random() < 0.4
        if self.morale_state == MoraleState.ANGRY:
            return random.random() < 0.1
        return False

    # ==================== MATCH RECORDING ====================

    def record_match(self, result: str, rating: float = 3.0):
        """Record match result with rating"""
        self.career_matches += 1

        if result == "win":
            self.wins += 1
            self.current_win_streak += 1
            self.current_loss_streak = 0
            self.adjust_momentum(5)
            # Reputation gain from win
            rep_gain = 1
            if rating >= 4.5:
                rep_gain = 3
            elif rating >= 4.0:
                rep_gain = 2
            self.add_reputation(rep_gain)
        elif result == "loss":
            self.losses += 1
            self.current_loss_streak += 1
            self.current_win_streak = 0
            self.adjust_momentum(-3)
            # Lose reputation on bad streaks
            if self.current_loss_streak >= 5:
                self.add_reputation(-3)
        elif result == "draw":
            self.draws += 1
            self.current_win_streak = 0
            self.current_loss_streak = 0
            self.adjust_momentum(1)

        # Track match quality
        if rating >= 5.0:
            self.five_star_matches += 1
        elif rating >= 4.0:
            self.four_star_matches += 1

        if rating > self.best_match_rating:
            self.best_match_rating = rating

    def win_championship(self):
        """Track championship win"""
        self.titles_held += 1
        self.title_reigns_total += 1
        self.add_reputation(5)
        self.adjust_momentum(15)
        self.adjust_morale(10)

    def lose_championship(self):
        """Track championship loss"""
        self.titles_held = max(0, self.titles_held - 1)
        self.adjust_momentum(-10)
        self.adjust_morale(-5)

    # ==================== SIGNATURES & FINISHERS ====================

    def add_signature_move(self, move_name: str):
        if move_name not in self.signature_moves:
            self.signature_moves.append(move_name)

    def remove_signature_move(self, move_name: str):
        if move_name in self.signature_moves:
            self.signature_moves.remove(move_name)

    def set_finisher(self, finisher_name: str):
        self.finisher_name = finisher_name

    # ==================== TRAITS ====================

    def has_trait(self, trait: str) -> bool:
        return trait.lower() in [t.lower() for t in self.unique_traits]

    def add_trait(self, trait: str):
        if not self.has_trait(trait):
            self.unique_traits.append(trait)

    def remove_trait(self, trait: str):
        self.unique_traits = [t for t in self.unique_traits if t.lower() != trait.lower()]

    # ==================== CONTRACT ====================

    def calculate_booking_fee(self) -> int:
        """Calculate the wrestler's booking fee based on level"""
        level_mult = LEVEL_INFO.get(self.wrestler_level, {}).get("fee_multiplier", 1.0)
        base = self.booking_fee
        return int(base * level_mult)

    def renew_contract(self, weeks: int, new_fee: int = None):
        self.contract_length = weeks
        if new_fee is not None:
            self.booking_fee = new_fee
        self.adjust_morale(5)

    def is_contract_expiring(self, weeks_warning: int = 4) -> bool:
        return self.contract_length <= weeks_warning

    # ==================== WEEKLY UPDATE ====================

    def weekly_update(self) -> Dict:
        """Process weekly changes"""
        result = {
            "level_up": None,
            "alignment_change": None,
            "walked_out": False,
        }

        self.weeks_signed += 1
        if self.is_indy_god:
            self.weeks_as_indy_god += 1

        # Contract countdown
        if self.contract_length > 0:
            self.contract_length -= 1

        # Heal injuries
        self.heal()

        # Natural fatigue recovery
        self.rest(7)

        # Update crowd reaction periodically
        if self.weeks_signed % 4 == 0:
            self.update_crowd_reaction()

        # Age-based decline (after 35)
        if self.age > 35 and random.random() < 0.05:
            stat_to_decline = random.choice(['power', 'speed', 'stamina', 'aerial'])
            current = getattr(self, stat_to_decline)
            setattr(self, stat_to_decline, max(1, current - 1))

        # Morale drift
        if self.morale > 50:
            self.morale = max(50, self.morale - 1)
        elif self.morale < 50:
            self.morale = min(50, self.morale + 1)

        # Walkout check
        if self.will_walk_out():
            result["walked_out"] = True

        return result

    # ==================== UI HELPERS ====================

    def get_level_icon(self) -> str:
        return LEVEL_INFO.get(self.wrestler_level, {}).get("icon", "🤼")

    def get_level_color(self) -> str:
        return LEVEL_INFO.get(self.wrestler_level, {}).get("color", "#6b7280")

    def get_morale_icon(self) -> str:
        return MORALE_EFFECTS.get(self.morale_state, {}).get("icon", "😐")

    def get_morale_color(self) -> str:
        return MORALE_EFFECTS.get(self.morale_state, {}).get("color", "#6b7280")

    def get_alignment_icon(self) -> str:
        icons = {
            Alignment.MEGA_FACE: "😇", Alignment.FACE: "😊",
            Alignment.TWEENER: "😐", Alignment.HEEL: "😡",
            Alignment.MEGA_HEEL: "😈", Alignment.X_FACTOR: "🌟",
            Alignment.COOLED_OFF: "💀",
        }
        return icons.get(self.alignment, "😐")

    def get_summary(self) -> Dict:
        """Get summary dict for UI"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "nickname": self.nickname,
            "level": self.wrestler_level.value,
            "level_icon": self.get_level_icon(),
            "level_color": self.get_level_color(),
            "level_number": self.level_number,
            "reputation": self.reputation,
            "alignment": self.alignment.value,
            "alignment_icon": self.get_alignment_icon(),
            "crowd_reaction": self.crowd_reaction.value,
            "morale": self.morale,
            "morale_state": self.morale_state.value,
            "morale_icon": self.get_morale_icon(),
            "morale_color": self.get_morale_color(),
            "popularity": self.popularity,
            "momentum": self.momentum,
            "overall_rating": self.overall_rating,
            "is_injured": self.is_injured,
            "is_indy_god": self.is_indy_god,
            "wins": self.wins, "losses": self.losses, "draws": self.draws,
            "win_percentage": self.win_percentage,
            "win_streak": self.current_win_streak,
            "loss_streak": self.current_loss_streak,
            "titles_held": self.titles_held,
            "five_star_matches": self.five_star_matches,
            "booking_fee": self.calculate_booking_fee(),
            "contract_length": self.contract_length,
            "contract_type": self.contract_type.value,
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "name": self.name, "nickname": self.nickname,
            "age": self.age, "gender": self.gender.value, "hometown": self.hometown,
            "height": self.height, "weight": self.weight,
            "primary_style": self.primary_style.value,
            "secondary_style": self.secondary_style.value if self.secondary_style else None,
            "alignment": self.alignment.value,
            "previous_alignment": self.previous_alignment.value if self.previous_alignment else None,
            "alignment_change_week": self.alignment_change_week,
            "crowd_reaction": self.crowd_reaction.value,
            "wrestler_level": self.wrestler_level.value,
            "reputation": self.reputation,
            "power": self.power, "speed": self.speed, "technical": self.technical,
            "stamina": self.stamina, "charisma": self.charisma,
            "hardcore": self.hardcore, "aerial": self.aerial,
            "mic_skills": self.mic_skills, "psychology": self.psychology,
            "toughness": self.toughness,
            "consistency": self.consistency, "work_ethic": self.work_ethic,
            "loyalty": self.loyalty, "ego": self.ego,
            "professionalism": self.professionalism,
            "popularity": self.popularity, "momentum": self.momentum,
            "morale": self.morale, "injury_prone": self.injury_prone, "fatigue": self.fatigue,
            "is_injured": self.is_injured,
            "injury_weeks_remaining": self.injury_weeks_remaining,
            "injury_type": self.injury_type, "injury_severity": self.injury_severity,
            "contract_type": self.contract_type.value,
            "booking_fee": self.booking_fee,
            "contract_length": self.contract_length,
            "is_exclusive": self.is_exclusive, "is_signed": self.is_signed,
            "weeks_signed": self.weeks_signed,
            "is_indy_god": self.is_indy_god,
            "weeks_as_indy_god": self.weeks_as_indy_god,
            "previous_promotions": self.previous_promotions,
            "unique_traits": self.unique_traits,
            "finisher_name": self.finisher_name,
            "signature_moves": self.signature_moves,
            "wins": self.wins, "losses": self.losses, "draws": self.draws,
            "current_win_streak": self.current_win_streak,
            "current_loss_streak": self.current_loss_streak,
            "titles_held": self.titles_held,
            "title_reigns_total": self.title_reigns_total,
            "five_star_matches": self.five_star_matches,
            "four_star_matches": self.four_star_matches,
            "career_matches": self.career_matches,
            "best_match_rating": self.best_match_rating,
            "active_storyline_count": self.active_storyline_count,
            "last_storyline_match_week": self.last_storyline_match_week,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wrestler":
        # Safe enum parsers
        def safe_enum(enum_cls, value, default):
            try:
                return enum_cls(value)
            except (ValueError, KeyError):
                return default

        wrestler = cls(
            name=data["name"],
            nickname=data.get("nickname"),
            age=data.get("age", 25),
            gender=safe_enum(Gender, data.get("gender", "Male"), Gender.MALE),
            hometown=data.get("hometown", "Unknown"),
            height=data.get("height", 72),
            weight=data.get("weight", 220),
            primary_style=safe_enum(WrestlingStyle, data.get("primary_style", "All-Rounder"), WrestlingStyle.ALL_ROUNDER),
            secondary_style=safe_enum(WrestlingStyle, data["secondary_style"], None) if data.get("secondary_style") else None,
            alignment=safe_enum(Alignment, data.get("alignment", "Face"), Alignment.FACE),
            wrestler_level=safe_enum(WrestlerLevel, data.get("wrestler_level", "Show Ready"), WrestlerLevel.SHOW_READY),
            reputation=data.get("reputation", 0),
            power=data.get("power", 50), speed=data.get("speed", 50),
            technical=data.get("technical", 50), stamina=data.get("stamina", 50),
            charisma=data.get("charisma", 50), hardcore=data.get("hardcore", 50),
            aerial=data.get("aerial", 50),
            mic_skills=data.get("mic_skills", 50),
            psychology=data.get("psychology", 50),
            toughness=data.get("toughness", 50),
            consistency=data.get("consistency", 50), work_ethic=data.get("work_ethic", 50),
            loyalty=data.get("loyalty", 50), ego=data.get("ego", 50),
            professionalism=data.get("professionalism", 50),
            popularity=data.get("popularity", 30), momentum=data.get("momentum", 50),
            morale=data.get("morale", 75), injury_prone=data.get("injury_prone", 50),
            fatigue=data.get("fatigue", 0),
            contract_type=safe_enum(ContractType, data.get("contract_type", "Per Appearance"), ContractType.PER_APPEARANCE),
            booking_fee=data.get("booking_fee", data.get("salary", 500)),  # Backwards compat
            contract_length=data.get("contract_length", 52),
            is_exclusive=data.get("is_exclusive", False),
            unique_traits=data.get("unique_traits", []),
            finisher_name=data.get("finisher_name", ""),
            signature_moves=data.get("signature_moves", []),
        )

        # Restore complex state
        wrestler.previous_alignment = safe_enum(Alignment, data["previous_alignment"], None) if data.get("previous_alignment") else None
        wrestler.alignment_change_week = data.get("alignment_change_week", 0)
        wrestler.crowd_reaction = safe_enum(CrowdReaction, data.get("crowd_reaction", "Mixed Reaction"), CrowdReaction.MIXED)

        wrestler.is_injured = data.get("is_injured", False)
        wrestler.injury_weeks_remaining = data.get("injury_weeks_remaining", 0)
        wrestler.injury_type = data.get("injury_type")
        wrestler.injury_severity = data.get("injury_severity", "")

        wrestler.weeks_signed = data.get("weeks_signed", 0)
        wrestler.is_indy_god = data.get("is_indy_god", False)
        wrestler.weeks_as_indy_god = data.get("weeks_as_indy_god", 0)
        wrestler.previous_promotions = data.get("previous_promotions", [])

        wrestler.wins = data.get("wins", 0)
        wrestler.losses = data.get("losses", 0)
        wrestler.draws = data.get("draws", 0)
        wrestler.current_win_streak = data.get("current_win_streak", 0)
        wrestler.current_loss_streak = data.get("current_loss_streak", 0)
        wrestler.titles_held = data.get("titles_held", 0)
        wrestler.title_reigns_total = data.get("title_reigns_total", 0)
        wrestler.five_star_matches = data.get("five_star_matches", 0)
        wrestler.four_star_matches = data.get("four_star_matches", 0)
        wrestler.career_matches = data.get("career_matches", 0)
        wrestler.best_match_rating = data.get("best_match_rating", 0.0)
        wrestler.active_storyline_count = data.get("active_storyline_count", 0)
        wrestler.last_storyline_match_week = data.get("last_storyline_match_week", 0)

        return wrestler

    def __repr__(self) -> str:
        return f"Wrestler({self.name}, Lvl{self.level_number} {self.wrestler_level.value}, OVR{self.overall_rating})"
