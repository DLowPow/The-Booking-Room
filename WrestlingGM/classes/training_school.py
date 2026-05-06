"""
Training School - The main school management system
School is OPTIONAL - player must purchase a venue to open one
6 tier progression: School Gym → Under the Arches → Indie Camp →
Wrestling Academy → Pro Training Center → Performance Center
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
        "monthly_tuition_per_trainee": 0,
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
        "monthly_tuition_per_trainee": 200,
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
        "monthly_tuition_per_trainee": 300,
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
        "monthly_tuition_per_trainee": 500,
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
        "monthly_tuition_per_trainee": 800,
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
        "monthly_tuition_per_trainee": 1200,
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
        "monthly_tuition_per_trainee": 1800,
        "starting_reputation": 80,
        "trainee_show_capacity_min": 500,
        "trainee_show_capacity_max": 1500,
        "training_speed_multiplier": 1.35,
        "max_concurrent_classes": 15,
    },
}


# ==================== UPGRADE COSTS ====================

UPGRADE_PATHS = {
    SchoolTier.SCHOOL_GYM: SchoolTier.UNDER_THE_ARCHES,
    SchoolTier.UNDER_THE_ARCHES: SchoolTier.INDIE_CAMP,
    SchoolTier.INDIE_CAMP: SchoolTier.WRESTLING_ACADEMY,
    SchoolTier.WRESTLING_ACADEMY: SchoolTier.PRO_TRAINING_CENTER,
    SchoolTier.PRO_TRAINING_CENTER: SchoolTier.PERFORMANCE_CENTER,
}


# ==================== SCHOOL CLASS ====================

@dataclass
class TrainingSchool:
    """Main Training School management"""

    # Identity
    name: str = ""
    location: str = ""
    tier: SchoolTier = SchoolTier.NONE
    status: SchoolStatus = SchoolStatus.NOT_FOUNDED

    # Reputation (0-100)
    reputation: int = 0
    reputation_history: List[int] = field(default_factory=list)

    # Roster
    trainees: List[Trainee] = field(default_factory=list)
    alumni: List[Dict] = field(default_factory=list)  # Graduates who left

    # Financial tracking
    total_invested: int = 0
    total_tuition_collected: int = 0
    total_overhead_paid: int = 0
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
        """Get the cost to purchase/found a school at given tier"""
        return SCHOOL_TIER_INFO.get(tier, {}).get("purchase_cost", 0)

    @staticmethod
    def get_tier_info(tier: SchoolTier) -> Dict:
        """Get all info for a tier"""
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

        return True

    def is_founded(self) -> bool:
        """Check if school exists"""
        return self.status != SchoolStatus.NOT_FOUNDED and self.tier != SchoolTier.NONE

    def is_operational(self) -> bool:
        """Check if school is currently running"""
        return self.status == SchoolStatus.OPERATIONAL

    # ==================== TIER UPGRADES ====================

    def can_upgrade(self) -> bool:
        """Check if school can be upgraded"""
        if not self.is_operational():
            return False
        return self.tier in UPGRADE_PATHS

    def get_next_tier(self) -> Optional[SchoolTier]:
        """Get the next tier this school can upgrade to"""
        return UPGRADE_PATHS.get(self.tier)

    def get_upgrade_cost(self) -> int:
        """Get cost of next tier upgrade (difference + 25% upgrade premium)"""
        next_tier = self.get_next_tier()
        if not next_tier:
            return 0

        next_cost = SCHOOL_TIER_INFO[next_tier]["purchase_cost"]
        current_cost = SCHOOL_TIER_INFO[self.tier]["purchase_cost"]
        upgrade_cost = int((next_cost - current_cost) * 1.25)
        return max(upgrade_cost, 1000)

    def start_upgrade(self) -> Tuple[bool, str]:
        """Begin upgrade to next tier"""
        if self.is_upgrading:
            return (False, "Upgrade already in progress")

        if not self.can_upgrade():
            return (False, "Cannot upgrade further")

        next_tier = self.get_next_tier()
        if not next_tier:
            return (False, "No upgrade path available")

        self.is_upgrading = True
        self.upgrade_target = next_tier
        self.upgrade_weeks_remaining = 4  # 4 week upgrade time
        self.status = SchoolStatus.UPGRADING

        return (True, f"Upgrading to {next_tier.value}! Complete in 4 weeks.")

    def complete_upgrade(self) -> Tuple[bool, str]:
        """Complete the upgrade process"""
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

        return (True, f"Upgrade complete! {old_tier.value} → {self.tier.value}")

    # ==================== TIER PROPERTIES ====================

    def get_capacity(self) -> int:
        """Get max trainees this school can hold"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("trainee_capacity", 0)

    def get_coach_slots(self) -> int:
        """Get max coaches this school supports"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("coach_slots", 0)

    def get_monthly_overhead(self) -> int:
        """Get monthly operational cost"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("monthly_overhead", 0)

    def get_monthly_tuition(self) -> int:
        """Get tuition charged per trainee per month"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("monthly_tuition_per_trainee", 0)

    def get_max_concurrent_classes(self) -> int:
        """Get how many classes can run simultaneously"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("max_concurrent_classes", 0)

    def get_training_speed_multiplier(self) -> float:
        """Get XP gain multiplier"""
        return SCHOOL_TIER_INFO.get(self.tier, {}).get("training_speed_multiplier", 1.0)

    def get_show_capacity_range(self) -> Tuple[int, int]:
        """Get min/max venue capacity for trainee shows"""
        info = SCHOOL_TIER_INFO.get(self.tier, {})
        return (
            info.get("trainee_show_capacity_min", 0),
            info.get("trainee_show_capacity_max", 0),
        )

    def has_capacity(self) -> bool:
        """Check if school has room for more trainees"""
        return len(self.trainees) < self.get_capacity()

    def get_available_slots(self) -> int:
        """Get number of empty trainee slots"""
        return max(0, self.get_capacity() - len(self.trainees))

    # ==================== TRAINEE MANAGEMENT ====================

    def enroll_trainee(self, trainee: Trainee) -> Tuple[bool, str]:
        """Enroll a trainee at the school"""
        if not self.is_operational():
            return (False, "School is not operational")

        if not self.has_capacity():
            return (False, "School at capacity")

        # Set trainee tuition based on school tier
        trainee.monthly_tuition = self.get_monthly_tuition()
        self.trainees.append(trainee)
        self.total_recruited += 1

        return (True, f"{trainee.name} enrolled successfully")

    def remove_trainee(self, trainee_id: str, reason: str = "") -> Optional[Trainee]:
        """Remove a trainee from the school"""
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
        """Get all currently active trainees"""
        return [t for t in self.trainees if t.status == TraineeStatus.ACTIVE]

    def get_graduated_trainees(self) -> List[Trainee]:
        """Get trainees ready for main roster"""
        return [t for t in self.trainees if t.status == TraineeStatus.GRADUATED]

    def get_trainees_by_level(self, level: TraineeLevel) -> List[Trainee]:
        return [t for t in self.trainees if t.level == level]

    def get_trainee_count(self) -> int:
        return len(self.trainees)

    def get_active_trainee_count(self) -> int:
        return len(self.get_active_trainees())

    # ==================== ALUMNI TRACKING ====================

    def add_alumni(self, trainee: Trainee, fate: str, notes: str = ""):
        """Track a trainee who has left the school"""
        self.alumni.append({
            "name": trainee.name,
            "id": trainee.id,
            "level_at_departure": trainee.level.value,
            "specialization": trainee.specialization.value,
            "weeks_at_school": trainee.weeks_in_school,
            "fate": fate,  # "signed_main", "released_indies", "dropped_out", "expelled"
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

        # Cap alumni history
        if len(self.alumni) > 200:
            self.alumni = self.alumni[-200:]

    def get_alumni_count(self) -> int:
        return len(self.alumni)

    # ==================== REPUTATION ====================

    def modify_reputation(self, amount: int):
        """Change school reputation"""
        old_rep = self.reputation
        self.reputation = max(0, min(100, self.reputation + amount))

    def record_weekly_reputation(self):
        """Track reputation history"""
        self.reputation_history.append(self.reputation)
        if len(self.reputation_history) > 52:
            self.reputation_history = self.reputation_history[-52:]

    def get_reputation_tier(self) -> str:
        """Get reputation tier name"""
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
            # Trainees with high morale always pay; low morale ones might default
            if trainee.morale < 25 and random.random() < 0.3:
                # They couldn't pay
                trainee.fail_tuition_payment()
                defaulters.append(trainee.name)
            else:
                trainee.pay_tuition(tuition_amount)
                total_collected += tuition_amount

        self.total_tuition_collected += total_collected
        return (total_collected, defaulters)

    def pay_monthly_overhead(self) -> int:
        """Deduct monthly overhead. Returns amount paid"""
        overhead = self.get_monthly_overhead()
        self.total_overhead_paid += overhead
        return overhead

    def get_monthly_profit_estimate(self) -> int:
        """Calculate estimated monthly profit"""
        active_count = self.get_active_trainee_count()
        income = active_count * self.get_monthly_tuition()
        overhead = self.get_monthly_overhead()
        return income - overhead

    def get_lifetime_profit(self) -> int:
        """Get total profit over school lifetime"""
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
            return result  # Skip normal operations during upgrade

        # Process each trainee
        coach_assigned = coach_manager and len(coach_manager.get_active_coaches()) > 0 if coach_manager else False

        for trainee in self.trainees[:]:
            # Check for trainee assigned coach
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
        """Record results of a trainee show"""
        self.trainee_shows_run += 1

        # Reputation impact
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

    def get_summary(self) -> Dict:
        """Get summary stats for UI display"""
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
            "lifetime_profit": self.get_lifetime_profit(),
            "weeks_operational": self.weeks_operational,
            "total_graduated": self.total_graduated,
            "total_recruited": self.total_recruited,
            "alumni_count": self.get_alumni_count(),
            "is_upgrading": self.is_upgrading,
            "upgrade_target": self.upgrade_target.value if self.upgrade_target else None,
            "upgrade_weeks_remaining": self.upgrade_weeks_remaining,
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
                "monthly_tuition": info["monthly_tuition_per_trainee"],
                "trainee_capacity": info["trainee_capacity"],
                "coach_slots": info["coach_slots"],
                "starting_reputation": info["starting_reputation"],
                "max_concurrent_classes": info["max_concurrent_classes"],
                "training_speed": f"{int(info['training_speed_multiplier'] * 100)}%",
                "show_capacity_range": (
                    info["trainee_show_capacity_min"],
                    info["trainee_show_capacity_max"],
                ),
                "monthly_profit_at_full": (
                    info["trainee_capacity"] * info["monthly_tuition_per_trainee"]
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
            "trainees": [t.to_dict() for t in self.trainees],
            "alumni": self.alumni,
            "total_invested": self.total_invested,
            "total_tuition_collected": self.total_tuition_collected,
            "total_overhead_paid": self.total_overhead_paid,
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
            alumni=data.get("alumni", []),
            total_invested=data.get("total_invested", 0),
            total_tuition_collected=data.get("total_tuition_collected", 0),
            total_overhead_paid=data.get("total_overhead_paid", 0),
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

        return school
