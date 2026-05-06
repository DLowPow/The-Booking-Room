"""
Training School - The main school management system
School is OPTIONAL - player must purchase a venue to open one
6 tier progression with ADJUSTABLE tuition and class fees
Player sets their own rates within tier-based ranges
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from classes.trainee import Trainee, TraineeLevel, TraineeStatus
from classes.coach import Coach, CoachStatus


# ==================== SCHOOL TIER ENUMS ====================

class SchoolTier(Enum):
    NONE = "Not Founded"
    SCHOOL_GYM = "School Gym"
    UNDER_THE_ARCHES = "Under the Arches"
    INDIE_CAMP = "Indie Training Camp"
    WRESTLING_ACADEMY = "Wrestling Academy"
    PRO_TRAINING_CENTER = "Pro Training Center"
    PERFORMANCE_CENTER = "Performance Center"


class SchoolStatus(Enum):
    NOT_FOUNDED = "Not Founded"
    OPERATIONAL = "Operational"
    UPGRADING = "Upgrading"
    CLOSED_TEMPORARILY = "Closed Temporarily"
    SHUTDOWN = "Shutdown"


# ==================== SCHOOL TIER DATA ====================

SCHOOL_TIER_INFO = {
    SchoolTier.NONE: {
        "name": "Not Founded",
        "icon": "❌",
        "color": "#6b7280",
        "description": "No training school established yet.",
        "purchase_cost": 0,
        "monthly_overhead": 0,
        "trainee_capacity": 0,
        "coach_slots": 0,
        # Tuition pricing (player adjustable)
        "recommended_tuition": 0,
        "min_tuition": 0,
        "max_tuition": 0,
        # Class discount for roster wrestlers training here
        "class_discount_percent": 0,
        "starting_reputation": 0,
        "trainee_show_capacity_min": 0,
        "trainee_show_capacity_max": 0,
        "training_speed_multiplier": 1.0,
        "max_concurrent_classes": 0,
    },
    SchoolTier.SCHOOL_GYM: {
        "name": "School Gym",
        "icon": "🏫",
        "color": "#6b7280",
        "description": "A rented high school gym, weekends only. Bare bones, but it's a start.",
        "purchase_cost": 1500,
        "monthly_overhead": 400,
        "trainee_capacity": 4,
        "coach_slots": 1,
        # Tuition: $200-$700, recommended $350
        "recommended_tuition": 350,
        "min_tuition": 200,
        "max_tuition": 700,
        "class_discount_percent": 40,
        "starting_reputation": 5,
        "trainee_show_capacity_min": 25,
        "trainee_show_capacity_max": 75,
        "training_speed_multiplier": 0.85,
        "max_concurrent_classes": 1,
    },
    SchoolTier.UNDER_THE_ARCHES: {
        "name": "Under the Arches",
        "icon": "🌉",
        "color": "#92400e",
        "description": "A small space under railway arches. Cold, raw, but real wrestling happens here.",
        "purchase_cost": 5000,
        "monthly_overhead": 800,
        "trainee_capacity": 6,
        "coach_slots": 2,
        # Tuition: $300-$1000, recommended $500
        "recommended_tuition": 500,
        "min_tuition": 300,
        "max_tuition": 1000,
        "class_discount_percent": 50,
        "starting_reputation": 12,
        "trainee_show_capacity_min": 40,
        "trainee_show_capacity_max": 120,
        "training_speed_multiplier": 0.95,
        "max_concurrent_classes": 2,
    },
    SchoolTier.INDIE_CAMP: {
        "name": "Indie Training Camp",
        "icon": "🏛️",
        "color": "#10b981",
        "description": "A dedicated indie training facility with proper equipment.",
        "purchase_cost": 15000,
        "monthly_overhead": 2000,
        "trainee_capacity": 10,
        "coach_slots": 3,
        # Tuition: $500-$1700, recommended $850
        "recommended_tuition": 850,
        "min_tuition": 500,
        "max_tuition": 1700,
        "class_discount_percent": 60,
        "starting_reputation": 25,
        "trainee_show_capacity_min": 75,
        "trainee_show_capacity_max": 250,
        "training_speed_multiplier": 1.0,
        "max_concurrent_classes": 3,
    },
    SchoolTier.WRESTLING_ACADEMY: {
        "name": "Wrestling Academy",
        "icon": "🎓",
        "color": "#3b82f6",
        "description": "A respected academy with multiple rings and full-time coaches.",
        "purchase_cost": 50000,
        "monthly_overhead": 5500,
        "trainee_capacity": 15,
        "coach_slots": 5,
        # Tuition: $800-$2800, recommended $1400
        "recommended_tuition": 1400,
        "min_tuition": 800,
        "max_tuition": 2800,
        "class_discount_percent": 75,
        "starting_reputation": 40,
        "trainee_show_capacity_min": 150,
        "trainee_show_capacity_max": 500,
        "training_speed_multiplier": 1.10,
        "max_concurrent_classes": 5,
    },
    SchoolTier.PRO_TRAINING_CENTER: {
        "name": "Pro Training Center",
        "icon": "🏟️",
        "color": "#8b5cf6",
        "description": "Professional-grade facility producing top tier talent regularly.",
        "purchase_cost": 150000,
        "monthly_overhead": 14000,
        "trainee_capacity": 20,
        "coach_slots": 7,
        # Tuition: $1200-$4400, recommended $2200
        "recommended_tuition": 2200,
        "min_tuition": 1200,
        "max_tuition": 4400,
        "class_discount_percent": 85,
        "starting_reputation": 60,
        "trainee_show_capacity_min": 250,
        "trainee_show_capacity_max": 800,
        "training_speed_multiplier": 1.20,
        "max_concurrent_classes": 8,
    },
    SchoolTier.PERFORMANCE_CENTER: {
        "name": "Performance Center",
        "icon": "🌍",
        "color": "#fbbf24",
        "description": "World-class facility. The dream factory. Where stars are made.",
        "purchase_cost": 500000,
        "monthly_overhead": 35000,
        "trainee_capacity": 30,
        "coach_slots": 12,
        # Tuition: $2000-$7000, recommended $3500
        "recommended_tuition": 3500,
        "min_tuition": 2000,
        "max_tuition": 7000,
        "class_discount_percent": 100,  # FREE roster training!
        "starting_reputation": 80,
        "trainee_show_capacity_min": 500,
        "trainee_show_capacity_max": 1500,
        "training_speed_multiplier": 1.35,
        "max_concurrent_classes": 15,
    },
}


# ==================== UPGRADE PATHS ====================

UPGRADE_PATHS = {
    SchoolTier.SCHOOL_GYM: SchoolTier.UNDER_THE_ARCHES,
    SchoolTier.UNDER_THE_ARCHES: SchoolTier.INDIE_CAMP,
    SchoolTier.INDIE_CAMP: SchoolTier.WRESTLING_ACADEMY,
    SchoolTier.WRESTLING_ACADEMY: SchoolTier.PRO_TRAINING_CENTER,
    SchoolTier.PRO_TRAINING_CENTER: SchoolTier.PERFORMANCE_CENTER,
}


# ==================== PRICING TIER LABELS ====================

def get_pricing_tier_label(tuition_ratio: float) -> Tuple[str, str, str]:
    """
    Get a label/icon/color for current pricing relative to recommended.
    Returns (label, icon, color)
    """
    if tuition_ratio <= 0.65:
        return ("Bargain", "💸", "#10b981")
    elif tuition_ratio <= 0.85:
        return ("Affordable", "💵", "#3b82f6")
    elif tuition_ratio <= 1.15:
        return ("Standard", "💰", "#8b5cf6")
    elif tuition_ratio <= 1.50:
        return ("Premium", "💎", "#f59e0b")
    else:
        return ("Elite", "👑", "#dc2626")


# ==================== SCHOOL CLASS ====================

@dataclass
class TrainingSchool:
    """Main Training School management with adjustable rates"""

    # Identity
    name: str = ""
    location: str = ""
    tier: SchoolTier = SchoolTier.NONE
    status: SchoolStatus = SchoolStatus.NOT_FOUNDED

    # Reputation (0-100)
    reputation: int = 0
    reputation_history: List[int] = field(default_factory=list)

    # ==================== ADJUSTABLE PRICING ====================
    # Player-set tuition (overrides recommended)
    current_tuition: int = 0
    # Player-set markup % on roster classes (0 = no markup, can be negative for further discount)
    class_markup_percent: int = 0
    # Whether player has customized rates (vs using defaults)
    rates_customized: bool = False

    # Roster
    trainees: List[Trainee] = field(default_factory=list)
    alumni: List[Dict] = field(default_factory=list)

    # Financial tracking
    total_invested: int = 0
    total_tuition_collected: int = 0
    total_overhead_paid: int = 0
    total_roster_class_savings: int = 0  # Track how much player saved on roster training
    weeks_operational: int = 0
    months_operational: int = 0

    # Stats
    total_recruited: int = 0
    total_graduated: int = 0
    total_dropped_out: int = 0
    total_signed_to_main: int = 0
    total_released_to_indies: int = 0
    trainee_shows_run: int = 0

    # Founding info
    week_founded: int = 0
    year_founded: int = 1

    # Upgrade tracking
    is_upgrading: bool = False
    upgrade_target: Optional[SchoolTier] = None
    upgrade_weeks_remaining: int = 0

    # ==================== FOUNDING / PURCHASE ====================

    @staticmethod
    def get_purchase_cost(tier: SchoolTier) -> int:
        return SCHOOL_TIER_INFO.get(tier, {}).get("purchase_cost", 0)

    @staticmethod
    def get_tier_info(tier: SchoolTier) -> Dict:
        return SCHOOL_TIER_INFO.get(tier, {})

    def found_school(
        self,
        name: str,
        location: str,
        tier: SchoolTier,
        week: int = 0,
        year: int = 1,
    ) -> bool:
        """Found a new training school at the chosen tier"""
        if self.status != SchoolStatus.NOT_FOUNDED:
            return False

        if tier == SchoolTier.NONE:
            return False

        tier_info = SCHOOL_TIER_INFO.get(tier, {})
        if not tier_info:
            return False

        self.name = name
        self.location = location
        self.tier = tier
        self.status = SchoolStatus.OPERATIONAL
        self.reputation = tier_info["starting_reputation"]
        self.week_founded = week
        self.year_founded = year
        self.total_invested = tier_info["purchase_cost"]

        # Set tuition to recommended default
        self.current_tuition = tier_info["recommended_tuition"]
        self.class_markup_percent = 0
        self.rates_customized = False

        return True

    def is_founded(self) -> bool:
        return self.status != SchoolStatus.NOT_FOUNDED and self.tier != SchoolTier.NONE

    def is_operational(self) -> bool:
        return self.status == SchoolStatus.OPERATIONAL

    # ==================== ADJUSTABLE PRICING SYSTEM ====================

    def get_recommended_tuition(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("recommended_tuition", 0)

    def get_min_tuition(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("min_tuition", 0)

    def get_max_tuition(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("max_tuition", 0)

    def get_monthly_tuition(self) -> int:
        """Get the current monthly tuition (player-set or recommended)"""
        if self.current_tuition > 0:
            return self.current_tuition
        return self.get_recommended_tuition()

    def set_tuition(self, amount: int) -> Tuple[bool, str]:
        """
        Set monthly tuition rate. Must be within tier's min/max range.
        Returns (success, message)
        """
        if not self.is_operational():
            return (False, "School is not operational")

        min_tuition = self.get_min_tuition()
        max_tuition = self.get_max_tuition()

        if amount < min_tuition:
            return (False, f"Tuition cannot be lower than ${min_tuition:,}")
        if amount > max_tuition:
            return (False, f"Tuition cannot exceed ${max_tuition:,}")

        self.current_tuition = amount
        self.rates_customized = True

        # Apply tuition to existing trainees
        for trainee in self.trainees:
            trainee.monthly_tuition = amount

        return (True, f"Tuition set to ${amount:,}/month")

    def get_tuition_ratio(self) -> float:
        """Get current tuition as ratio of recommended (1.0 = recommended)"""
        recommended = self.get_recommended_tuition()
        if recommended == 0:
            return 1.0
        return self.get_monthly_tuition() / recommended

    def get_pricing_tier(self) -> Dict:
        """Get pricing tier info for UI display"""
        ratio = self.get_tuition_ratio()
        label, icon, color = get_pricing_tier_label(ratio)
        return {
            "label": label,
            "icon": icon,
            "color": color,
            "ratio": ratio,
            "ratio_percent": int(ratio * 100),
        }

    def get_applicant_modifier(self) -> float:
        """
        Get modifier for weekly applicant generation based on tuition.
        Cheaper = more applicants. Premium = fewer but higher quality.
        """
        ratio = self.get_tuition_ratio()

        # Curve: 50% tuition = 2.0x applicants, 100% = 1.0x, 200% = 0.25x
        if ratio <= 0.65:
            return 2.0  # Bargain bin floods with applicants
        elif ratio <= 0.85:
            return 1.5
        elif ratio <= 1.15:
            return 1.0  # Recommended price
        elif ratio <= 1.50:
            return 0.6  # Premium pricing limits applicants
        else:
            return 0.3  # Elite pricing only attracts serious students

    def get_quality_modifier(self) -> float:
        """
        Get quality modifier for applicants based on tuition.
        Premium pricing attracts higher-quality prospects.
        """
        ratio = self.get_tuition_ratio()

        if ratio <= 0.65:
            return 0.85  # Cheaper = lower quality applicants
        elif ratio <= 0.85:
            return 0.95
        elif ratio <= 1.15:
            return 1.0  # Standard quality
        elif ratio <= 1.50:
            return 1.15  # Premium attracts better talent
        else:
            return 1.30  # Elite price = elite prospects

    def get_reputation_drift(self) -> int:
        """Weekly reputation drift based on pricing strategy"""
        ratio = self.get_tuition_ratio()

        if ratio <= 0.65:
            return -1  # Cheap school slowly loses reputation
        elif ratio >= 1.50:
            return 1  # Premium school slowly gains reputation
        return 0

    # ==================== CLASS FEE ADJUSTMENT ====================

    def get_class_discount_percent(self) -> int:
        """Base discount % from school tier"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("class_discount_percent", 0)

    def set_class_markup(self, percent: int) -> Tuple[bool, str]:
        """
        Set markup % on roster classes (-50 to +100).
        Negative = further discount, positive = upcharge (rare use case).
        """
        if not self.is_operational():
            return (False, "School is not operational")

        if percent < -50:
            return (False, "Markup cannot be lower than -50%")
        if percent > 100:
            return (False, "Markup cannot exceed +100%")

        self.class_markup_percent = percent
        self.rates_customized = True

        if percent < 0:
            return (True, f"Class fees set to {abs(percent)}% additional discount")
        elif percent > 0:
            return (True, f"Class fees set to +{percent}% markup")
        else:
            return (True, "Class fees set to standard discount only")

    def calculate_class_cost(self, base_cost: int) -> int:
        """
        Calculate final cost for a roster class after school discount and markup.
        base_cost = the standard cost defined in training_classes.py
        """
        if not self.is_operational():
            return base_cost

        # Apply tier discount first
        discount_pct = self.get_class_discount_percent()
        discounted = base_cost * (1 - discount_pct / 100)

        # Apply markup/extra discount
        markup_multiplier = 1 + (self.class_markup_percent / 100)
        final_cost = int(discounted * markup_multiplier)

        return max(0, final_cost)

    def get_total_class_savings(self, base_cost: int) -> int:
        """How much money saved on a class vs paying base cost"""
        final = self.calculate_class_cost(base_cost)
        return max(0, base_cost - final)

    def record_class_savings(self, base_cost: int):
        """Track lifetime savings from owning a school"""
        savings = self.get_total_class_savings(base_cost)
        self.total_roster_class_savings += savings

    # ==================== TIER UPGRADES ====================

    def can_upgrade(self) -> bool:
        if not self.is_operational():
            return False
        return self.tier in UPGRADE_PATHS

    def get_next_tier(self) -> Optional[SchoolTier]:
        return UPGRADE_PATHS.get(self.tier)

    def get_upgrade_cost(self) -> int:
        next_tier = self.get_next_tier()
        if not next_tier:
            return 0

        next_cost = SCHOOL_TIER_INFO[next_tier]["purchase_cost"]
        current_cost = SCHOOL_TIER_INFO[self.tier]["purchase_cost"]
        upgrade_cost = int((next_cost - current_cost) * 1.25)
        return max(upgrade_cost, 1000)

    def start_upgrade(self) -> Tuple[bool, str]:
        if self.is_upgrading:
            return (False, "Upgrade already in progress")

        if not self.can_upgrade():
            return (False, "Cannot upgrade further")

        next_tier = self.get_next_tier()
        if not next_tier:
            return (False, "No upgrade path available")

        self.is_upgrading = True
        self.upgrade_target = next_tier
        self.upgrade_weeks_remaining = 4
        self.status = SchoolStatus.UPGRADING

        return (True, f"Upgrading to {next_tier.value}! Complete in 4 weeks.")

    def complete_upgrade(self) -> Tuple[bool, str]:
        if not self.is_upgrading or not self.upgrade_target:
            return (False, "No upgrade in progress")

        old_tier = self.tier
        self.tier = self.upgrade_target
        self.is_upgrading = False
        self.upgrade_target = None
        self.upgrade_weeks_remaining = 0
        self.status = SchoolStatus.OPERATIONAL

        # Reputation boost from upgrade
        new_tier_info = SCHOOL_TIER_INFO[self.tier]
        self.reputation = min(100, max(self.reputation, new_tier_info["starting_reputation"]))

        # Reset tuition to new tier's recommended (player can re-customize)
        if not self.rates_customized:
            self.current_tuition = new_tier_info["recommended_tuition"]
        else:
            # Keep player customization but clamp to new tier's range
            self.current_tuition = max(
                new_tier_info["min_tuition"],
                min(new_tier_info["max_tuition"], self.current_tuition)
            )

        return (True, f"Upgrade complete! {old_tier.value} → {self.tier.value}")

    # ==================== TIER PROPERTIES ====================

    def get_capacity(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("trainee_capacity", 0)

    def get_coach_slots(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("coach_slots", 0)

    def get_monthly_overhead(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("monthly_overhead", 0)

    def get_max_concurrent_classes(self) -> int:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("max_concurrent_classes", 0)

    def get_training_speed_multiplier(self) -> float:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("training_speed_multiplier", 1.0)

    def get_show_capacity_range(self) -> Tuple[int, int]:
        info = SCHOOL_TIER_INFO.get(self.tier, {})
        return (
            info.get("trainee_show_capacity_min", 0),
            info.get("trainee_show_capacity_max", 0),
        )

    def has_capacity(self) -> bool:
        return len(self.trainees) < self.get_capacity()

    def get_available_slots(self) -> int:
        return max(0, self.get_capacity() - len(self.trainees))

    # ==================== TRAINEE MANAGEMENT ====================

    def enroll_trainee(self, trainee: Trainee) -> Tuple[bool, str]:
        if not self.is_operational():
            return (False, "School is not operational")

        if not self.has_capacity():
            return (False, "School at capacity")

        # Apply current tuition rate to trainee
        trainee.monthly_tuition = self.get_monthly_tuition()
        self.trainees.append(trainee)
        self.total_recruited += 1

        return (True, f"{trainee.name} enrolled successfully")

    def remove_trainee(self, trainee_id: str, reason: str = "") -> Optional[Trainee]:
        for i, trainee in enumerate(self.trainees):
            if trainee.id == trainee_id:
                removed = self.trainees.pop(i)
                if reason == "graduated":
                    self.total_graduated += 1
                elif reason == "dropped_out":
                    self.total_dropped_out += 1
                return removed
        return None

    def get_trainee(self, trainee_id: str) -> Optional[Trainee]:
        for trainee in self.trainees:
            if trainee.id == trainee_id:
                return trainee
        return None

    def get_active_trainees(self) -> List[Trainee]:
        return [t for t in self.trainees if t.status == TraineeStatus.ACTIVE]

    def get_graduated_trainees(self) -> List[Trainee]:
        return [t for t in self.trainees if t.status == TraineeStatus.GRADUATED]

    def get_trainees_by_level(self, level: TraineeLevel) -> List[Trainee]:
        return [t for t in self.trainees if t.level == level]

    def get_trainee_count(self) -> int:
        return len(self.trainees)

    def get_active_trainee_count(self) -> int:
        return len(self.get_active_trainees())

    # ==================== ALUMNI TRACKING ====================

    def add_alumni(self, trainee: Trainee, fate: str, notes: str = ""):
        self.alumni.append({
            "name": trainee.name,
            "id": trainee.id,
            "level_at_departure": trainee.level.value,
            "specialization": trainee.specialization.value,
            "weeks_at_school": trainee.weeks_in_school,
            "fate": fate,
            "notes": notes,
            "best_match_rating": trainee.best_trainee_match_rating,
            "trainee_matches": trainee.trainee_matches_wrestled,
        })

        if fate == "signed_main":
            self.total_signed_to_main += 1
            self.modify_reputation(3)
        elif fate == "released_indies":
            self.total_released_to_indies += 1
            self.modify_reputation(2)

        if len(self.alumni) > 200:
            self.alumni = self.alumni[-200:]

    def get_alumni_count(self) -> int:
        return len(self.alumni)

    # ==================== REPUTATION ====================

    def modify_reputation(self, amount: int):
        self.reputation = max(0, min(100, self.reputation + amount))

    def record_weekly_reputation(self):
        self.reputation_history.append(self.reputation)
        if len(self.reputation_history) > 52:
            self.reputation_history = self.reputation_history[-52:]

    def get_reputation_tier(self) -> str:
        if self.reputation >= 80:
            return "Legendary"
        elif self.reputation >= 60:
            return "Elite"
        elif self.reputation >= 40:
            return "Respected"
        elif self.reputation >= 20:
            return "Local"
        else:
            return "Unknown"

    def get_reputation_color(self) -> str:
        if self.reputation >= 80:
            return "#fbbf24"
        elif self.reputation >= 60:
            return "#a855f7"
        elif self.reputation >= 40:
            return "#3b82f6"
        elif self.reputation >= 20:
            return "#10b981"
        else:
            return "#6b7280"

    # ==================== FINANCIAL OPERATIONS ====================

    def collect_monthly_tuition(self) -> Tuple[int, List[str]]:
        """Collect tuition from all active trainees. Returns (total, defaulters)"""
        total_collected = 0
        defaulters = []
        tuition_amount = self.get_monthly_tuition()

        for trainee in self.get_active_trainees():
            # Premium tuition has higher default rate from low-morale trainees
            ratio = self.get_tuition_ratio()
            default_chance = 0.3 if trainee.morale < 25 else 0.0
            if ratio > 1.5:
                default_chance += 0.10  # Premium pricing harder to maintain

            if default_chance > 0 and random.random() < default_chance:
                trainee.fail_tuition_payment()
                defaulters.append(trainee.name)
            else:
                trainee.pay_tuition(tuition_amount)
                total_collected += tuition_amount

        self.total_tuition_collected += total_collected
        return (total_collected, defaulters)

    def pay_monthly_overhead(self) -> int:
        overhead = self.get_monthly_overhead()
        self.total_overhead_paid += overhead
        return overhead

    def get_monthly_profit_estimate(self) -> int:
        """Estimated monthly profit at current tuition rate (full capacity)"""
        active_count = self.get_active_trainee_count()
        income = active_count * self.get_monthly_tuition()
        overhead = self.get_monthly_overhead()
        return income - overhead

    def get_max_monthly_profit(self) -> int:
        """Max possible profit if school were at full capacity"""
        capacity = self.get_capacity()
        income = capacity * self.get_monthly_tuition()
        overhead = self.get_monthly_overhead()
        return income - overhead

    def get_lifetime_profit(self) -> int:
        return self.total_tuition_collected - self.total_overhead_paid

    # ==================== WEEKLY UPDATE ====================

    def weekly_update(
        self,
        coach_manager=None,
        had_trainee_show: bool = False,
        current_week: int = 0,
    ) -> Dict:
        """Process weekly school operations"""
        result = {
            "school_name": self.name,
            "trainee_updates": [],
            "graduations": [],
            "dropouts": [],
            "rep_change": 0,
            "monthly_processed": False,
            "tuition_collected": 0,
            "overhead_paid": 0,
            "defaulters": [],
            "upgrade_complete": False,
            "events": [],
        }

        if not self.is_operational() and not self.is_upgrading:
            return result

        self.weeks_operational += 1
        old_rep = self.reputation

        # Process upgrade
        if self.is_upgrading:
            self.upgrade_weeks_remaining -= 1
            if self.upgrade_weeks_remaining <= 0:
                success, msg = self.complete_upgrade()
                if success:
                    result["upgrade_complete"] = True
                    result["events"].append(msg)
            return result

        # Apply weekly reputation drift from pricing strategy
        rep_drift = self.get_reputation_drift()
        if rep_drift != 0:
            self.modify_reputation(rep_drift)

        # Process each trainee
        for trainee in self.trainees[:]:
            has_coach = trainee.has_coach_assigned

            update = trainee.weekly_update(
                has_coach=has_coach,
                had_show_this_week=had_trainee_show,
            )
            result["trainee_updates"].append(update)

            # Handle graduations
            if update.get("level_up") and update["level_up"].get("is_graduation"):
                trainee.graduate(week=current_week)
                result["graduations"].append({
                    "name": trainee.name,
                    "id": trainee.id,
                })
                self.modify_reputation(2)

            # Handle dropouts
            if update.get("dropped_out"):
                self.add_alumni(trainee, "dropped_out", "Quit due to dissatisfaction")
                self.remove_trainee(trainee.id, "dropped_out")
                self.modify_reputation(-2)
                result["dropouts"].append({"name": trainee.name})

        # Monthly processing every 4 weeks
        if self.weeks_operational % 4 == 0:
            tuition, defaulters = self.collect_monthly_tuition()
            overhead = self.pay_monthly_overhead()
            self.months_operational += 1
            result["monthly_processed"] = True
            result["tuition_collected"] = tuition
            result["overhead_paid"] = overhead
            result["defaulters"] = defaulters

        # Record reputation
        self.record_weekly_reputation()
        result["rep_change"] = self.reputation - old_rep

        return result

    # ==================== TRAINEE SHOW TRACKING ====================

    def record_trainee_show(self, attendance: int, rating: float):
        self.trainee_shows_run += 1

        if rating >= 4.0:
            self.modify_reputation(2)
        elif rating >= 3.0:
            self.modify_reputation(1)
        elif rating < 2.0:
            self.modify_reputation(-1)

    # ==================== UI HELPERS ====================

    def get_tier_icon(self) -> str:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("icon", "🏫")

    def get_tier_color(self) -> str:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("color", "#6b7280")

    def get_tier_description(self) -> str:
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("description", "")

    def get_status_color(self) -> str:
        colors = {
            SchoolStatus.NOT_FOUNDED: "#6b7280",
            SchoolStatus.OPERATIONAL: "#10b981",
            SchoolStatus.UPGRADING: "#f59e0b",
            SchoolStatus.CLOSED_TEMPORARILY: "#ef4444",
            SchoolStatus.SHUTDOWN: "#7c2d12",
        }
        return colors.get(self.status, "#6b7280")

    def get_pricing_summary(self) -> Dict:
        """Detailed pricing info for UI display"""
        pricing_tier = self.get_pricing_tier()
        return {
            "current_tuition": self.get_monthly_tuition(),
            "recommended_tuition": self.get_recommended_tuition(),
            "min_tuition": self.get_min_tuition(),
            "max_tuition": self.get_max_tuition(),
            "tuition_ratio_percent": pricing_tier["ratio_percent"],
            "pricing_label": pricing_tier["label"],
            "pricing_icon": pricing_tier["icon"],
            "pricing_color": pricing_tier["color"],
            "applicant_modifier": self.get_applicant_modifier(),
            "applicant_modifier_percent": int(self.get_applicant_modifier() * 100),
            "quality_modifier": self.get_quality_modifier(),
            "quality_modifier_percent": int(self.get_quality_modifier() * 100),
            "rep_drift": self.get_reputation_drift(),
            "class_discount_percent": self.get_class_discount_percent(),
            "class_markup_percent": self.class_markup_percent,
            "rates_customized": self.rates_customized,
        }

    def get_summary(self) -> Dict:
        """Get summary stats for UI display"""
        pricing = self.get_pricing_summary()
        return {
            "name": self.name,
            "tier": self.tier.value,
            "tier_icon": self.get_tier_icon(),
            "tier_color": self.get_tier_color(),
            "status": self.status.value,
            "status_color": self.get_status_color(),
            "reputation": self.reputation,
            "reputation_tier": self.get_reputation_tier(),
            "reputation_color": self.get_reputation_color(),
            "trainee_count": self.get_active_trainee_count(),
            "capacity": self.get_capacity(),
            "available_slots": self.get_available_slots(),
            "monthly_overhead": self.get_monthly_overhead(),
            "monthly_tuition": self.get_monthly_tuition(),
            "monthly_profit_estimate": self.get_monthly_profit_estimate(),
            "max_monthly_profit": self.get_max_monthly_profit(),
            "lifetime_profit": self.get_lifetime_profit(),
            "lifetime_class_savings": self.total_roster_class_savings,
            "weeks_operational": self.weeks_operational,
            "total_graduated": self.total_graduated,
            "total_recruited": self.total_recruited,
            "alumni_count": self.get_alumni_count(),
            "is_upgrading": self.is_upgrading,
            "upgrade_target": self.upgrade_target.value if self.upgrade_target else None,
            "upgrade_weeks_remaining": self.upgrade_weeks_remaining,
            "pricing": pricing,
        }

    def get_purchase_options(self) -> List[Dict]:
        """Get all available tiers for initial purchase (UI display)"""
        options = []
        for tier in SchoolTier:
            if tier == SchoolTier.NONE:
                continue
            info = SCHOOL_TIER_INFO[tier]
            options.append({
                "tier": tier.value,
                "tier_key": tier.name,
                "name": info["name"],
                "icon": info["icon"],
                "color": info["color"],
                "description": info["description"],
                "purchase_cost": info["purchase_cost"],
                "monthly_overhead": info["monthly_overhead"],
                "recommended_tuition": info["recommended_tuition"],
                "min_tuition": info["min_tuition"],
                "max_tuition": info["max_tuition"],
                "trainee_capacity": info["trainee_capacity"],
                "coach_slots": info["coach_slots"],
                "starting_reputation": info["starting_reputation"],
                "max_concurrent_classes": info["max_concurrent_classes"],
                "training_speed": f"{int(info['training_speed_multiplier'] * 100)}%",
                "class_discount": info["class_discount_percent"],
                "show_capacity_range": (
                    info["trainee_show_capacity_min"],
                    info["trainee_show_capacity_max"],
                ),
                "monthly_profit_at_recommended": (
                    info["trainee_capacity"] * info["recommended_tuition"]
                    - info["monthly_overhead"]
                ),
                "monthly_profit_at_max": (
                    info["trainee_capacity"] * info["max_tuition"]
                    - info["monthly_overhead"]
                ),
            })
        return options

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "tier": self.tier.value,
            "status": self.status.value,
            "reputation": self.reputation,
            "reputation_history": self.reputation_history,
            "current_tuition": self.current_tuition,
            "class_markup_percent": self.class_markup_percent,
            "rates_customized": self.rates_customized,
            "trainees": [t.to_dict() for t in self.trainees],
            "alumni": self.alumni,
            "total_invested": self.total_invested,
            "total_tuition_collected": self.total_tuition_collected,
            "total_overhead_paid": self.total_overhead_paid,
            "total_roster_class_savings": self.total_roster_class_savings,
            "weeks_operational": self.weeks_operational,
            "months_operational": self.months_operational,
            "total_recruited": self.total_recruited,
            "total_graduated": self.total_graduated,
            "total_dropped_out": self.total_dropped_out,
            "total_signed_to_main": self.total_signed_to_main,
            "total_released_to_indies": self.total_released_to_indies,
            "trainee_shows_run": self.trainee_shows_run,
            "week_founded": self.week_founded,
            "year_founded": self.year_founded,
            "is_upgrading": self.is_upgrading,
            "upgrade_target": self.upgrade_target.value if self.upgrade_target else None,
            "upgrade_weeks_remaining": self.upgrade_weeks_remaining,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrainingSchool":
        try:
            tier = SchoolTier(data.get("tier", "Not Founded"))
        except ValueError:
            tier = SchoolTier.NONE
        try:
            status = SchoolStatus(data.get("status", "Not Founded"))
        except ValueError:
            status = SchoolStatus.NOT_FOUNDED

        upgrade_target = None
        if data.get("upgrade_target"):
            try:
                upgrade_target = SchoolTier(data["upgrade_target"])
            except ValueError:
                upgrade_target = None

        school = cls(
            name=data.get("name", ""),
            location=data.get("location", ""),
            tier=tier,
            status=status,
            reputation=data.get("reputation", 0),
            reputation_history=data.get("reputation_history", []),
            current_tuition=data.get("current_tuition", 0),
            class_markup_percent=data.get("class_markup_percent", 0),
            rates_customized=data.get("rates_customized", False),
            alumni=data.get("alumni", []),
            total_invested=data.get("total_invested", 0),
            total_tuition_collected=data.get("total_tuition_collected", 0),
            total_overhead_paid=data.get("total_overhead_paid", 0),
            total_roster_class_savings=data.get("total_roster_class_savings", 0),
            weeks_operational=data.get("weeks_operational", 0),
            months_operational=data.get("months_operational", 0),
            total_recruited=data.get("total_recruited", 0),
            total_graduated=data.get("total_graduated", 0),
            total_dropped_out=data.get("total_dropped_out", 0),
            total_signed_to_main=data.get("total_signed_to_main", 0),
            total_released_to_indies=data.get("total_released_to_indies", 0),
            trainee_shows_run=data.get("trainee_shows_run", 0),
            week_founded=data.get("week_founded", 0),
            year_founded=data.get("year_founded", 1),
            is_upgrading=data.get("is_upgrading", False),
            upgrade_target=upgrade_target,
            upgrade_weeks_remaining=data.get("upgrade_weeks_remaining", 0),
        )

        for td in data.get("trainees", []):
            try:
                school.trainees.append(Trainee.from_dict(td))
            except Exception:
                pass

        # Default tuition if not set
        if school.current_tuition == 0 and school.is_founded():
            school.current_tuition = school.get_recommended_tuition()

        return school
