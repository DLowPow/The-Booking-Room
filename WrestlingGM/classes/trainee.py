"""
Trainee System - Wrestlers in development at the Training School
4 levels: New Recruit → Beginner → Intermediate → Advanced → Show Ready (graduates)
Pays tuition, gains XP from training + trainee shows, can drop out
Graduates convert to full Wrestler objects
"""
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ==================== TRAINEE LEVELS ====================
class TraineeLevel(Enum):
    NEW_RECRUIT = "New Recruit"
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    GRADUATED = "Graduated"  # Show Ready - moves to main roster pool


class TraineeSpecialization(Enum):
    UNDECIDED = "Undecided"
    STRIKER = "Striker"
    TECHNICIAN = "Technician"
    HIGH_FLYER = "High-Flyer"
    BRAWLER = "Brawler"
    POWERHOUSE = "Powerhouse"
    ALL_ROUNDER = "All-Rounder"
    CHARACTER = "Character/Mic Worker"


class TraineeStatus(Enum):
    ACTIVE = "Active"
    INJURED = "Injured"
    SUSPENDED = "Suspended"
    DROPPED_OUT = "Dropped Out"
    GRADUATED = "Graduated"
    EXPELLED = "Expelled"


# ==================== LEVEL THRESHOLDS ====================
LEVEL_XP_THRESHOLDS = {
    TraineeLevel.NEW_RECRUIT: 0,
    TraineeLevel.BEGINNER: 0,
    TraineeLevel.INTERMEDIATE: 150,
    TraineeLevel.ADVANCED: 400,
    TraineeLevel.GRADUATED: 800,
}

LEVEL_INFO = {
    TraineeLevel.NEW_RECRUIT: {
        "icon": "🆕",
        "color": "#6b7280",
        "description": "Just signed up. Learning the basics. Cannot wrestle yet.",
        "weeks_min": 2,
        "can_wrestle": False,
        "match_minutes_max": 0,
    },
    TraineeLevel.BEGINNER: {
        "icon": "🎓",
        "color": "#3b82f6",
        "description": "Knows how to bump. Ready for short trainee matches.",
        "weeks_min": 8,
        "can_wrestle": True,
        "match_minutes_max": 5,
    },
    TraineeLevel.INTERMEDIATE: {
        "icon": "🎓",
        "color": "#8b5cf6",
        "description": "Solid fundamentals. Can work proper matches.",
        "weeks_min": 12,
        "can_wrestle": True,
        "match_minutes_max": 8,
    },
    TraineeLevel.ADVANCED: {
        "icon": "🎓",
        "color": "#f59e0b",
        "description": "Polished and ready. Can headline trainee shows.",
        "weeks_min": 14,
        "can_wrestle": True,
        "match_minutes_max": 12,
    },
    TraineeLevel.GRADUATED: {
        "icon": "✅",
        "color": "#10b981",
        "description": "Show Ready! Ready to join the main roster.",
        "weeks_min": 0,
        "can_wrestle": True,
        "match_minutes_max": 30,
    },
}


# ==================== SPECIALIZATION TEMPLATES ====================
SPECIALIZATION_INFO = {
    TraineeSpecialization.UNDECIDED: {
        "icon": "❓",
        "stat_focus": [],
        "description": "Hasn't found their style yet.",
    },
    TraineeSpecialization.STRIKER: {
        "icon": "🥊",
        "stat_focus": ["strength", "stamina"],
        "description": "Hard-hitting, kick-based offense.",
    },
    TraineeSpecialization.TECHNICIAN: {
        "icon": "🤼",
        "stat_focus": ["technique", "psychology"],
        "description": "Mat wrestling, submissions, chain wrestling.",
    },
    TraineeSpecialization.HIGH_FLYER: {
        "icon": "🪂",
        "stat_focus": ["speed", "stamina"],
        "description": "Aerial offense, dives, ranas.",
    },
    TraineeSpecialization.BRAWLER: {
        "icon": "👊",
        "stat_focus": ["toughness", "strength"],
        "description": "Hardcore, physical, weapons-friendly.",
    },
    TraineeSpecialization.POWERHOUSE: {
        "icon": "💪",
        "stat_focus": ["strength", "toughness"],
        "description": "Power moves, dominance.",
    },
    TraineeSpecialization.ALL_ROUNDER: {
        "icon": "⭐",
        "stat_focus": ["technique", "speed", "stamina"],
        "description": "Balanced skills across the board.",
    },
    TraineeSpecialization.CHARACTER: {
        "icon": "🎤",
        "stat_focus": ["charisma", "mic_skills"],
        "description": "Promo work and character-driven storytelling.",
    },
}


# ==================== TRAINEE CLASS ====================
@dataclass
class Trainee:
    """A wrestler-in-training at the school"""

    # Identity
    id: str
    name: str
    age: int = 22
    gender: str = "Male"
    hometown: str = ""

    # Training progress
    level: TraineeLevel = TraineeLevel.NEW_RECRUIT
    xp: int = 0
    weeks_at_current_level: int = 0
    weeks_in_school: int = 0
    week_enrolled: int = 0
    year_enrolled: int = 1

    # Specialization
    specialization: TraineeSpecialization = TraineeSpecialization.UNDECIDED
    weeks_until_specialize: int = 8  # Picks specialization after this many weeks

    # Stats (lower than main roster — 10-60 range to start)
    strength: int = 30
    speed: int = 30
    technique: int = 25
    charisma: int = 25
    stamina: int = 30
    toughness: int = 30
    mic_skills: int = 20
    psychology: int = 20

    # Mental state
    morale: int = 75
    discipline: int = 70  # How well they follow rules
    work_ethic: int = 65  # How hard they train

    # Drop-out / status
    status: TraineeStatus = TraineeStatus.ACTIVE
    weeks_since_show: int = 0
    weeks_with_low_morale: int = 0
    has_coach_assigned: bool = False
    drop_out_warnings: int = 0

    # Tuition tracking
    tuition_paid_total: int = 0
    weeks_behind_on_tuition: int = 0
    monthly_tuition: int = 150  # Set by school tier

    # Match/show history
    trainee_matches_wrestled: int = 0
    trainee_match_wins: int = 0
    trainee_match_losses: int = 0
    best_trainee_match_rating: float = 0.0
    avg_trainee_match_rating: float = 0.0

    # Coaching/training
    weeks_trained: int = 0
    coach_id: str = ""
    last_coach_name: str = ""

    # Special flags
    is_natural_talent: bool = False  # 5% rolled at creation - faster XP
    is_problem_child: bool = False   # 5% rolled at creation - drop-out risk
    is_high_potential: bool = False  # Roll based on starting stats

    # Promising Indy conversion (if released after graduation)
    became_promising_indy: bool = False
    week_dropped_out: int = 0

    # ==================== CREATION ====================
    @staticmethod
    def generate_random_trainee(
        trainee_id: str,
        name: str,
        age: int = None,
        gender: str = None,
        monthly_tuition: int = 150,
        week: int = 0,
        year: int = 1,
        quality_modifier: float = 1.0,
    ) -> "Trainee":
        """Generate a randomized trainee applicant"""
        if age is None:
            age = random.randint(18, 28)
        if gender is None:
            gender = random.choice(["Male", "Male", "Female"])  # Slight male bias

        # Base stats with variance
        base = int(25 * quality_modifier)
        variance = 12

        trainee = Trainee(
            id=trainee_id,
            name=name,
            age=age,
            gender=gender,
            monthly_tuition=monthly_tuition,
            week_enrolled=week,
            year_enrolled=year,
            strength=max(10, base + random.randint(-variance, variance)),
            speed=max(10, base + random.randint(-variance, variance)),
            technique=max(10, base - 5 + random.randint(-variance, variance)),
            charisma=max(10, base + random.randint(-variance, variance)),
            stamina=max(10, base + random.randint(-variance, variance)),
            toughness=max(10, base + random.randint(-variance, variance)),
            mic_skills=max(10, base - 8 + random.randint(-variance, variance)),
            psychology=max(10, base - 10 + random.randint(-variance, variance)),
            morale=random.randint(70, 90),
            discipline=random.randint(50, 90),
            work_ethic=random.randint(50, 90),
        )

        # Roll for special traits
        if random.random() < 0.05:
            trainee.is_natural_talent = True
        if random.random() < 0.05:
            trainee.is_problem_child = True

        # High potential check (avg stat >= 35)
        avg_stat = (trainee.strength + trainee.speed + trainee.technique +
                    trainee.stamina + trainee.toughness) / 5
        if avg_stat >= 35:
            trainee.is_high_potential = True

        return trainee

    # ==================== XP & LEVEL PROGRESSION ====================
    def add_xp(self, amount: int, source: str = "training") -> Optional[Dict]:
        """Add XP and check for level-up. Returns level-up info if leveled."""
        if self.status != TraineeStatus.ACTIVE:
            return None

        # Natural talent gets bonus XP
        if self.is_natural_talent:
            amount = int(amount * 1.25)
        # Problem children get less XP
        if self.is_problem_child:
            amount = int(amount * 0.85)
        # Low morale = less XP
        if self.morale < 30:
            amount = int(amount * 0.5)
        elif self.morale < 50:
            amount = int(amount * 0.75)

        self.xp += amount

        # Check for level-up
        level_up = self._check_level_up()
        return level_up

    def _check_level_up(self) -> Optional[Dict]:
        """Check if trainee should level up"""
        current_level_value = list(TraineeLevel).index(self.level)

        # Check next level
        next_levels = list(TraineeLevel)[current_level_value + 1:]
        for next_level in next_levels:
            threshold = LEVEL_XP_THRESHOLDS.get(next_level, 99999)
            min_weeks = LEVEL_INFO.get(self.level, {}).get("weeks_min", 0)

            # Must meet XP AND minimum weeks at level
            if self.xp >= threshold and self.weeks_at_current_level >= min_weeks:
                old_level = self.level
                self.level = next_level
                self.weeks_at_current_level = 0

                # Stat boost on level-up
                self._apply_level_up_boost()

                return {
                    "leveled_up": True,
                    "old_level": old_level.value,
                    "new_level": next_level.value,
                    "is_graduation": next_level == TraineeLevel.GRADUATED,
                }
            else:
                break  # Can't skip levels
        return None

    def _apply_level_up_boost(self):
        """Apply stat boost on level-up"""
        boost = random.randint(2, 5)

        # If specialized, focus on those stats
        if self.specialization != TraineeSpecialization.UNDECIDED:
            spec_info = SPECIALIZATION_INFO.get(self.specialization, {})
            focus_stats = spec_info.get("stat_focus", [])
            for stat in focus_stats:
                current = getattr(self, stat, 0)
                setattr(self, stat, min(80, current + boost + 1))

        # Small boost to all stats
        small_boost = random.randint(1, 3)
        for stat in ["strength", "speed", "technique", "charisma",
                     "stamina", "toughness", "mic_skills", "psychology"]:
            current = getattr(self, stat, 0)
            setattr(self, stat, min(80, current + small_boost))

    def get_xp_to_next_level(self) -> Tuple[int, int]:
        """Get current XP and threshold for next level"""
        current_level_value = list(TraineeLevel).index(self.level)
        next_levels = list(TraineeLevel)[current_level_value + 1:]

        if not next_levels:
            return (self.xp, self.xp)  # Already maxed

        next_level = next_levels[0]
        threshold = LEVEL_XP_THRESHOLDS.get(next_level, 99999)
        return (self.xp, threshold)

    def get_xp_progress_percentage(self) -> float:
        """Get % progress to next level (0-100)"""
        current, target = self.get_xp_to_next_level()
        current_level_value = list(TraineeLevel).index(self.level)
        prev_threshold = LEVEL_XP_THRESHOLDS.get(self.level, 0)

        if target == current:
            return 100.0
        if target <= prev_threshold:
            return 100.0

        progress = (current - prev_threshold) / (target - prev_threshold) * 100
        return max(0.0, min(100.0, progress))

    # ==================== SPECIALIZATION ====================
    def assign_specialization(self, spec: TraineeSpecialization):
        """Lock in a specialization path"""
        self.specialization = spec
        self.weeks_until_specialize = 0

        # Boost stats related to spec
        spec_info = SPECIALIZATION_INFO.get(spec, {})
        for stat in spec_info.get("stat_focus", []):
            current = getattr(self, stat, 0)
            setattr(self, stat, min(80, current + 5))

    def auto_pick_specialization(self) -> TraineeSpecialization:
        """Auto-pick specialization based on highest stats"""
        # Find best stat path
        scores = {
            TraineeSpecialization.STRIKER: self.strength + self.stamina,
            TraineeSpecialization.TECHNICIAN: self.technique + self.psychology,
            TraineeSpecialization.HIGH_FLYER: self.speed + self.stamina,
            TraineeSpecialization.BRAWLER: self.toughness + self.strength,
            TraineeSpecialization.POWERHOUSE: self.strength + self.toughness,
            TraineeSpecialization.ALL_ROUNDER: (self.technique + self.speed + self.stamina) // 2,
            TraineeSpecialization.CHARACTER: self.charisma + self.mic_skills,
        }
        best_spec = max(scores, key=scores.get)
        self.assign_specialization(best_spec)
        return best_spec

    # ==================== COACHING ====================
    def assign_coach(self, coach_id: str, coach_name: str = "") -> Tuple[bool, str]:
        """
        Assign a personal coach to this trainee.
        Returns (success, message).
        """
        if self.status != TraineeStatus.ACTIVE:
            return (False, f"{self.name} is {self.status.value} and cannot accept a coach right now")

        previous = self.last_coach_name
        self.coach_id = coach_id
        self.last_coach_name = coach_name or coach_id
        self.has_coach_assigned = True

        # Slight morale boost when getting a coach
        self.morale = min(100, self.morale + 3)

        if previous and previous != coach_name:
            return (True, f"{self.name}'s coach changed from {previous} to {self.last_coach_name}")
        return (True, f"{self.last_coach_name} is now coaching {self.name}")

    def unassign_coach(self) -> Tuple[bool, str]:
        """Remove the current coach assignment."""
        if not self.has_coach_assigned:
            return (False, f"{self.name} has no coach assigned")

        previous = self.last_coach_name
        self.coach_id = ""
        self.has_coach_assigned = False
        # Don't clear last_coach_name — keep for history display

        # Small morale hit from losing coach
        self.morale = max(0, self.morale - 5)

        return (True, f"{previous} is no longer coaching {self.name}")

    # ==================== WEEKLY UPDATE ====================
    def weekly_update(self, has_coach: bool = False, had_show_this_week: bool = False) -> Dict:
        """Process weekly trainee update. Returns event info."""
        result = {
            "trainee_name": self.name,
            "level_up": None,
            "specialized": None,
            "dropped_out": False,
            "morale_change": 0,
            "xp_gained": 0,
            "warnings": [],
        }

        if self.status != TraineeStatus.ACTIVE:
            return result

        self.weeks_in_school += 1
        self.weeks_at_current_level += 1
        self.has_coach_assigned = has_coach

        # Track shows
        if had_show_this_week:
            self.weeks_since_show = 0
        else:
            self.weeks_since_show += 1

        # Auto-specialize after enough weeks
        if (self.specialization == TraineeSpecialization.UNDECIDED
            and self.weeks_in_school >= 8):
            spec = self.auto_pick_specialization()
            result["specialized"] = spec.value

        # Weekly training XP
        base_xp = random.randint(10, 25)
        if has_coach:
            base_xp += random.randint(5, 12)
        if self.work_ethic >= 80:
            base_xp = int(base_xp * 1.15)
        elif self.work_ethic <= 40:
            base_xp = int(base_xp * 0.7)

        level_event = self.add_xp(base_xp, "weekly_training")
        result["xp_gained"] = base_xp
        if level_event:
            result["level_up"] = level_event

        # Morale changes
        morale_change = 0
        if has_coach:
            morale_change += 1
        else:
            morale_change -= 2
            result["warnings"].append("No coach assigned")

        if self.weeks_since_show >= 4:
            morale_change -= 3
            result["warnings"].append(f"{self.weeks_since_show} weeks without a show")

        if not has_coach and self.weeks_in_school >= 4:
            morale_change -= 1

        self.morale = max(0, min(100, self.morale + morale_change))
        result["morale_change"] = morale_change

        # Track low morale
        if self.morale < 30:
            self.weeks_with_low_morale += 1
        else:
            self.weeks_with_low_morale = 0

        # Drop-out check
        drop_chance = self._calculate_drop_out_chance()
        if drop_chance > 0 and random.random() < drop_chance:
            self.drop_out("Voluntarily quit due to dissatisfaction")
            result["dropped_out"] = True
            result["warnings"].append("DROPPED OUT")

        return result

    def _calculate_drop_out_chance(self) -> float:
        """Calculate chance of dropping out this week"""
        chance = 0.0

        if self.morale < 30:
            chance += 0.05
        if not self.has_coach_assigned:
            chance += 0.03
        if self.weeks_since_show >= 4:
            chance += 0.08
        if self.is_problem_child:
            chance += 0.04
        if self.weeks_with_low_morale >= 4:
            chance += 0.10

        return min(0.30, chance)  # Cap at 30%

    # ==================== TRAINEE SHOW PARTICIPATION ====================
    def can_wrestle_in_trainee_show(self) -> bool:
        """Check if this trainee can be booked on a trainee show"""
        if self.status != TraineeStatus.ACTIVE:
            return False
        return LEVEL_INFO.get(self.level, {}).get("can_wrestle", False)

    def get_max_match_minutes(self) -> int:
        """Get max match time for this trainee's level"""
        return LEVEL_INFO.get(self.level, {}).get("match_minutes_max", 0)

    def record_trainee_match(self, won: bool, rating: float, xp_reward: int = 0) -> Optional[Dict]:
        """Record a trainee match result"""
        self.trainee_matches_wrestled += 1
        if won:
            self.trainee_match_wins += 1
        else:
            self.trainee_match_losses += 1

        # Track ratings
        if rating > self.best_trainee_match_rating:
            self.best_trainee_match_rating = rating

        total_matches = self.trainee_matches_wrestled
        if total_matches > 0:
            self.avg_trainee_match_rating = (
                (self.avg_trainee_match_rating * (total_matches - 1) + rating) / total_matches
            )

        # XP gain
        if xp_reward == 0:
            xp_reward = 30 + int(rating * 10)
        if won:
            xp_reward = int(xp_reward * 1.2)
        if rating >= 4.0:
            xp_reward += 50

        # Morale boost from matches
        if rating >= 3.5:
            self.morale = min(100, self.morale + 5)
        elif rating < 2.0:
            self.morale = max(0, self.morale - 3)

        return self.add_xp(xp_reward, "trainee_match")

    # ==================== CLASSES (PROMO/STAT BOOST) ====================
    def attend_class(self, class_type: str, success_level: str = "good") -> Dict:
        """Process class attendance. Returns stat changes."""
        result = {"stat_changes": {}, "morale_change": 0, "xp_gained": 0}

        success_multipliers = {
            "excellent": 3,
            "good": 2,
            "average": 1,
            "poor": 0,
            "disastrous": -1,
        }

        boost = success_multipliers.get(success_level, 1)

        # Class-to-stat mapping
        class_stats = {
            "promo": ["mic_skills", "charisma"],
            "charisma": ["charisma"],
            "strength": ["strength"],
            "speed": ["speed"],
            "technique": ["technique"],
            "stamina": ["stamina"],
            "toughness": ["toughness"],
            "psychology": ["psychology"],
        }

        stats_to_boost = class_stats.get(class_type, [])

        for stat in stats_to_boost:
            current = getattr(self, stat, 0)
            new_value = max(10, min(80, current + boost))
            setattr(self, stat, new_value)
            result["stat_changes"][stat] = new_value - current

        # Morale impact for promo classes
        if class_type == "promo":
            if success_level == "excellent":
                self.morale = min(100, self.morale + 10)
                result["morale_change"] = 10
            elif success_level == "poor":
                self.morale = max(0, self.morale - 5)
                result["morale_change"] = -5
            elif success_level == "disastrous":
                self.morale = max(0, self.morale - 15)
                result["morale_change"] = -15

        # XP from class
        xp = 10 + (boost * 5)
        result["xp_gained"] = xp
        self.add_xp(xp, "class")

        return result

    # ==================== STATUS CHANGES ====================
    def drop_out(self, reason: str = ""):
        """Trainee quits the school"""
        self.status = TraineeStatus.DROPPED_OUT

    def graduate(self, week: int = 0):
        """Trainee successfully graduates → Show Ready"""
        self.status = TraineeStatus.GRADUATED
        self.level = TraineeLevel.GRADUATED

    def expel(self, reason: str = ""):
        """School kicks them out (discipline issues)"""
        self.status = TraineeStatus.EXPELLED

    def injure(self, weeks: int = 2):
        """Mark trainee as injured"""
        self.status = TraineeStatus.INJURED

    def recover(self):
        """Trainee returns from injury/suspension"""
        self.status = TraineeStatus.ACTIVE

    # ==================== CONVERSION TO WRESTLER ====================
    def to_wrestler_data(self) -> Dict:
        """Convert graduated trainee to wrestler data for main roster"""
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "hometown": self.hometown,
            "strength": self.strength,
            "speed": self.speed,
            "technique": self.technique,
            "charisma": self.charisma,
            "stamina": self.stamina,
            "toughness": self.toughness,
            "mic_skills": self.mic_skills,
            "psychology": self.psychology,
            "popularity": 25,  # Show Ready starting popularity
            "morale": self.morale,
            "loyalty": 75,  # Loyal to the school that trained them
            "wrestler_level": "Show Ready",
            "alma_mater": True,  # Trained at this school
            "specialization": self.specialization.value,
            "career_wins": self.trainee_match_wins,
            "career_losses": self.trainee_match_losses,
        }

    # ==================== TUITION ====================
    def pay_tuition(self, amount: int):
        """Record tuition payment"""
        self.tuition_paid_total += amount
        self.weeks_behind_on_tuition = 0

    def fail_tuition_payment(self):
        """Trainee couldn't pay this month"""
        self.weeks_behind_on_tuition += 4
        self.morale = max(0, self.morale - 5)

    # ==================== UI HELPERS ====================
    def get_level_color(self) -> str:
        return LEVEL_INFO.get(self.level, {}).get("color", "#6b7280")

    def get_level_icon(self) -> str:
        return LEVEL_INFO.get(self.level, {}).get("icon", "🎓")

    def get_specialization_icon(self) -> str:
        return SPECIALIZATION_INFO.get(self.specialization, {}).get("icon", "❓")

    def get_status_color(self) -> str:
        colors = {
            TraineeStatus.ACTIVE: "#10b981",
            TraineeStatus.INJURED: "#dc2626",
            TraineeStatus.SUSPENDED: "#f59e0b",
            TraineeStatus.DROPPED_OUT: "#6b7280",
            TraineeStatus.GRADUATED: "#fbbf24",
            TraineeStatus.EXPELLED: "#7c2d12",
        }
        return colors.get(self.status, "#6b7280")

    def get_morale_emoji(self) -> str:
        if self.morale >= 80:
            return "🤩"
        if self.morale >= 60:
            return "😊"
        if self.morale >= 40:
            return "😐"
        if self.morale >= 20:
            return "😟"
        return "😡"

    def get_overall_rating(self) -> int:
        """Calculate overall trainee rating (0-100)"""
        physical_avg = (self.strength + self.speed + self.technique +
                        self.stamina + self.toughness) / 5
        mental_avg = (self.charisma + self.mic_skills + self.psychology) / 3
        # FIX: was `(physical_avg _0.7) + (mental_avg_ 0.3)` — markdown corruption
        return int((physical_avg * 0.7) + (mental_avg * 0.3))

    def get_special_traits_display(self) -> List[str]:
        """Get list of special traits for display"""
        traits = []
        if self.is_natural_talent:
            traits.append("⭐ Natural Talent")
        if self.is_high_potential:
            traits.append("📈 High Potential")
        if self.is_problem_child:
            traits.append("⚠️ Problem Child")
        return traits

    def get_summary_line(self) -> str:
        """One-line summary for lists"""
        return (f"{self.name} ({self.age}) — "
                f"{self.level.value} • "
                f"{self.specialization.value} • "
                f"OVR {self.get_overall_rating()}")

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "hometown": self.hometown,
            "level": self.level.value,
            "xp": self.xp,
            "weeks_at_current_level": self.weeks_at_current_level,
            "weeks_in_school": self.weeks_in_school,
            "week_enrolled": self.week_enrolled,
            "year_enrolled": self.year_enrolled,
            "specialization": self.specialization.value,
            "weeks_until_specialize": self.weeks_until_specialize,
            "strength": self.strength,
            "speed": self.speed,
            "technique": self.technique,
            "charisma": self.charisma,
            "stamina": self.stamina,
            "toughness": self.toughness,
            "mic_skills": self.mic_skills,
            "psychology": self.psychology,
            "morale": self.morale,
            "discipline": self.discipline,
            "work_ethic": self.work_ethic,
            "status": self.status.value,
            "weeks_since_show": self.weeks_since_show,
            "weeks_with_low_morale": self.weeks_with_low_morale,
            "has_coach_assigned": self.has_coach_assigned,
            "drop_out_warnings": self.drop_out_warnings,
            "tuition_paid_total": self.tuition_paid_total,
            "weeks_behind_on_tuition": self.weeks_behind_on_tuition,
            "monthly_tuition": self.monthly_tuition,
            "trainee_matches_wrestled": self.trainee_matches_wrestled,
            "trainee_match_wins": self.trainee_match_wins,
            "trainee_match_losses": self.trainee_match_losses,
            "best_trainee_match_rating": self.best_trainee_match_rating,
            "avg_trainee_match_rating": self.avg_trainee_match_rating,
            "weeks_trained": self.weeks_trained,
            "coach_id": self.coach_id,
            "last_coach_name": self.last_coach_name,
            "is_natural_talent": self.is_natural_talent,
            "is_problem_child": self.is_problem_child,
            "is_high_potential": self.is_high_potential,
            "became_promising_indy": self.became_promising_indy,
            "week_dropped_out": self.week_dropped_out,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trainee":
        try:
            level = TraineeLevel(data.get("level", "New Recruit"))
        except ValueError:
            level = TraineeLevel.NEW_RECRUIT
        try:
            spec = TraineeSpecialization(data.get("specialization", "Undecided"))
        except ValueError:
            spec = TraineeSpecialization.UNDECIDED
        try:
            status = TraineeStatus(data.get("status", "Active"))
        except ValueError:
            status = TraineeStatus.ACTIVE

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            age=data.get("age", 22),
            gender=data.get("gender", "Male"),
            hometown=data.get("hometown", ""),
            level=level,
            xp=data.get("xp", 0),
            weeks_at_current_level=data.get("weeks_at_current_level", 0),
            weeks_in_school=data.get("weeks_in_school", 0),
            week_enrolled=data.get("week_enrolled", 0),
            year_enrolled=data.get("year_enrolled", 1),
            specialization=spec,
            weeks_until_specialize=data.get("weeks_until_specialize", 8),
            strength=data.get("strength", 30),
            speed=data.get("speed", 30),
            technique=data.get("technique", 25),
            charisma=data.get("charisma", 25),
            stamina=data.get("stamina", 30),
            toughness=data.get("toughness", 30),
            mic_skills=data.get("mic_skills", 20),
            psychology=data.get("psychology", 20),
            morale=data.get("morale", 75),
            discipline=data.get("discipline", 70),
            work_ethic=data.get("work_ethic", 65),
            status=status,
            weeks_since_show=data.get("weeks_since_show", 0),
            weeks_with_low_morale=data.get("weeks_with_low_morale", 0),
            has_coach_assigned=data.get("has_coach_assigned", False),
            drop_out_warnings=data.get("drop_out_warnings", 0),
            tuition_paid_total=data.get("tuition_paid_total", 0),
            weeks_behind_on_tuition=data.get("weeks_behind_on_tuition", 0),
            monthly_tuition=data.get("monthly_tuition", 150),
            trainee_matches_wrestled=data.get("trainee_matches_wrestled", 0),
            trainee_match_wins=data.get("trainee_match_wins", 0),
            trainee_match_losses=data.get("trainee_match_losses", 0),
            best_trainee_match_rating=data.get("best_trainee_match_rating", 0.0),
            avg_trainee_match_rating=data.get("avg_trainee_match_rating", 0.0),
            weeks_trained=data.get("weeks_trained", 0),
            coach_id=data.get("coach_id", ""),
            last_coach_name=data.get("last_coach_name", ""),
            is_natural_talent=data.get("is_natural_talent", False),
            is_problem_child=data.get("is_problem_child", False),
            is_high_potential=data.get("is_high_potential", False),
            became_promising_indy=data.get("became_promising_indy", False),
            week_dropped_out=data.get("week_dropped_out", 0),
        )
