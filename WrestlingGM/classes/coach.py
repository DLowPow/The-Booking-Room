"""
Coach System - Trainers who develop your trainees and roster
Two types: Veteran wrestlers (cheap, dual-purpose) and NPC coaches (expensive, specialized)
Coaches boost trainee XP, reduce injury risk in classes, earn weekly income
Now integrates with TrainingSchool for tier-based payroll discounts
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==================== COACH ENUMS ====================

class CoachType(Enum):
    VETERAN = "Veteran Wrestler"      # Pulled from your roster
    NPC = "Hired Coach"                # Dedicated NPC trainer
    LEGEND = "Legendary Coach"         # Premium tier, unlocked at high reputation


class CoachSpecialty(Enum):
    STRIKING = "Striking"
    TECHNICAL = "Technical"
    HIGH_FLYING = "High-Flying"
    POWER = "Power"
    HARDCORE = "Hardcore"
    PROMO = "Promo & Charisma"
    PSYCHOLOGY = "Ring Psychology"
    CONDITIONING = "Conditioning"
    ALL_AROUND = "All-Around"


class CoachStatus(Enum):
    AVAILABLE = "Available"
    ASSIGNED = "Assigned"
    INJURED = "Injured"
    RESTING = "Resting"
    RETIRED = "Retired"


# ==================== SPECIALTY INFO ====================

SPECIALTY_INFO = {
    CoachSpecialty.STRIKING: {
        "icon": "🥊",
        "color": "#dc2626",
        "stat_focus": ["strength", "stamina"],
        "boosted_classes": ["strength", "speed"],
        "description": "Develops hard-hitting offense and stamina.",
    },
    CoachSpecialty.TECHNICAL: {
        "icon": "🤼",
        "color": "#3b82f6",
        "stat_focus": ["technique", "psychology"],
        "boosted_classes": ["technique", "psychology"],
        "description": "Mat wrestling, submissions, ring science.",
    },
    CoachSpecialty.HIGH_FLYING: {
        "icon": "🪂",
        "color": "#8b5cf6",
        "stat_focus": ["speed", "stamina"],
        "boosted_classes": ["speed", "stamina"],
        "description": "Aerial offense, agility, athleticism.",
    },
    CoachSpecialty.POWER: {
        "icon": "💪",
        "color": "#f59e0b",
        "stat_focus": ["strength", "toughness"],
        "boosted_classes": ["strength", "toughness"],
        "description": "Power moves, dominance, raw force.",
    },
    CoachSpecialty.HARDCORE: {
        "icon": "🩸",
        "color": "#7c2d12",
        "stat_focus": ["toughness", "strength"],
        "boosted_classes": ["toughness", "strength"],
        "description": "Pain tolerance, weapons, extreme matches.",
    },
    CoachSpecialty.PROMO: {
        "icon": "🎤",
        "color": "#ec4899",
        "stat_focus": ["charisma", "mic_skills"],
        "boosted_classes": ["promo", "charisma"],
        "description": "Mic work, character, crowd connection.",
    },
    CoachSpecialty.PSYCHOLOGY: {
        "icon": "🧠",
        "color": "#06b6d4",
        "stat_focus": ["psychology", "technique"],
        "boosted_classes": ["psychology", "technique"],
        "description": "Match storytelling, pacing, crowd manipulation.",
    },
    CoachSpecialty.CONDITIONING: {
        "icon": "🦾",
        "color": "#10b981",
        "stat_focus": ["stamina", "toughness"],
        "boosted_classes": ["stamina", "toughness"],
        "description": "Endurance, recovery, physical fitness.",
    },
    CoachSpecialty.ALL_AROUND: {
        "icon": "⭐",
        "color": "#fbbf24",
        "stat_focus": ["technique", "psychology", "stamina"],
        "boosted_classes": ["technique", "psychology", "stamina"],
        "description": "Balanced training across all disciplines.",
    },
}


# ==================== SCHOOL TIER PAYROLL DISCOUNTS ====================

# When coaches work at YOUR school (vs. being external hires),
# you save on their weekly salary due to centralized HR/equipment
# Bigger school = bigger admin efficiency
SCHOOL_TIER_PAYROLL_DISCOUNT = {
    "Not Founded": 0,           # No school = full price
    "School Gym": 10,           # 10% discount
    "Under the Arches": 15,     # 15% discount
    "Indie Training Camp": 20,  # 20% discount
    "Wrestling Academy": 25,    # 25% discount
    "Pro Training Center": 30,  # 30% discount
    "Performance Center": 40,   # 40% discount (max efficiency)
}


# ==================== COACH CLASS ====================

@dataclass
class Coach:
    """A coach at the Training School with school-aware pricing"""

    # Identity
    id: str
    name: str
    coach_type: CoachType
    specialty: CoachSpecialty

    # Skill rating (affects XP boost and stat gain quality)
    skill_rating: int = 50  # 0-100

    # BASE cost & income (full price without school)
    base_weekly_cost: int = 200  # Standard weekly salary
    base_hire_cost: int = 0      # One-time hire fee (NPCs only)

    # Status
    status: CoachStatus = CoachStatus.AVAILABLE
    weeks_employed: int = 0
    weeks_assigned_consecutive: int = 0

    # Stats tracking
    trainees_coached: int = 0
    graduates_produced: int = 0
    total_xp_given: int = 0
    classes_taught: int = 0

    # Trait flags
    is_legendary: bool = False           # Premium coach
    is_player_wrestler: bool = False     # Pulled from roster
    wrestler_id: str = ""                # If from roster, link to wrestler
    description: str = ""

    # NPC bio
    age: int = 45
    background: str = ""

    # Coaching effectiveness (calculated)
    xp_bonus_percent: int = 10      # % XP bonus to assigned trainees
    injury_risk_reduction: int = 30 # % reduction in class injury risk

    # ==================== PRICING METHODS ====================

    def get_weekly_cost_with_school(self, school=None) -> int:
        """Get actual weekly cost after school payroll discount"""
        if not school or not hasattr(school, 'is_operational') or not school.is_operational():
            return self.base_weekly_cost

        # Get school tier discount
        tier_name = school.tier.value if hasattr(school.tier, 'value') else str(school.tier)
        discount_pct = SCHOOL_TIER_PAYROLL_DISCOUNT.get(tier_name, 0)

        if discount_pct <= 0:
            return self.base_weekly_cost

        discount_amount = int(self.base_weekly_cost * (discount_pct / 100))
        final_cost = self.base_weekly_cost - discount_amount
        return max(50, final_cost)  # Floor of $50/week minimum

    def get_hire_cost_with_school(self, school=None) -> int:
        """Get hire fee (school doesn't discount upfront fees)"""
        return self.base_hire_cost

    def get_savings_with_school(self, school=None) -> int:
        """Calculate weekly $ saved by hiring through your school"""
        if not school or not hasattr(school, 'is_operational') or not school.is_operational():
            return 0
        return max(0, self.base_weekly_cost - self.get_weekly_cost_with_school(school))

    @property
    def weekly_cost(self) -> int:
        """Backwards-compatible property — returns base cost"""
        return self.base_weekly_cost

    @property
    def hire_cost(self) -> int:
        """Backwards-compatible property — returns base hire cost"""
        return self.base_hire_cost

    # ==================== CALCULATED PROPERTIES ====================

    def calculate_xp_bonus(self) -> int:
        """Calculate XP bonus % based on skill rating and type"""
        base = int(self.skill_rating * 0.25)  # 50 skill = 12% bonus
        if self.coach_type == CoachType.LEGEND:
            base += 15
        elif self.coach_type == CoachType.NPC:
            base += 5
        return min(50, base)

    def calculate_injury_risk_reduction(self) -> int:
        """Calculate injury risk reduction % based on skill"""
        base = int(self.skill_rating * 0.4)  # 50 skill = 20% reduction
        if self.coach_type == CoachType.LEGEND:
            base += 20
        return min(70, base)

    def calculate_stat_gain_bonus(self) -> int:
        """Bonus to stat gain rolls in classes"""
        if self.coach_type == CoachType.LEGEND:
            return 2
        if self.coach_type == CoachType.NPC and self.skill_rating >= 70:
            return 1
        if self.coach_type == CoachType.VETERAN and self.skill_rating >= 75:
            return 1
        return 0

    def update_effectiveness(self):
        """Recalculate effectiveness values"""
        self.xp_bonus_percent = self.calculate_xp_bonus()
        self.injury_risk_reduction = self.calculate_injury_risk_reduction()

    # ==================== STATUS MANAGEMENT ====================

    def assign(self):
        """Mark coach as assigned to a trainee/class"""
        self.status = CoachStatus.ASSIGNED
        self.weeks_assigned_consecutive += 1

    def unassign(self):
        """Free up coach"""
        if self.status == CoachStatus.ASSIGNED:
            self.status = CoachStatus.AVAILABLE
        self.weeks_assigned_consecutive = 0

    def rest(self):
        """Coach takes a rest week"""
        self.status = CoachStatus.RESTING
        self.weeks_assigned_consecutive = 0

    def retire(self):
        """Coach retires from coaching"""
        self.status = CoachStatus.RETIRED

    # ==================== WEEKLY UPDATE ====================

    def weekly_update(self, was_assigned: bool = False, school=None) -> Dict:
        """Process weekly coach update with school-aware pricing"""
        result = {
            "coach_name": self.name,
            "income_paid": 0,
            "savings": 0,
            "events": [],
        }

        if self.status == CoachStatus.RETIRED:
            return result

        self.weeks_employed += 1

        # Calculate actual cost with school discount
        actual_cost = self.get_weekly_cost_with_school(school)
        savings = self.get_savings_with_school(school)
        result["income_paid"] = actual_cost
        result["savings"] = savings

        # Veterans coaching too long get burned out
        if self.is_player_wrestler and self.weeks_assigned_consecutive >= 8:
            if random.random() < 0.3:
                self.rest()
                result["events"].append(f"{self.name} is taking a break from coaching")

        # NPC coaches occasionally get sick or take time off
        elif self.coach_type == CoachType.NPC:
            if was_assigned and random.random() < 0.02:
                self.status = CoachStatus.RESTING
                result["events"].append(f"{self.name} is taking a sick week")

        # Legend coaches retire eventually
        if self.coach_type == CoachType.LEGEND and self.weeks_employed > 52:
            if random.random() < 0.05:
                self.retire()
                result["events"].append(f"{self.name} has retired from coaching")

        return result

    # ==================== STATS RECORDING ====================

    def record_class_taught(self, xp_given: int):
        """Record completing a class"""
        self.classes_taught += 1
        self.total_xp_given += xp_given

    def record_graduate(self):
        """Record a trainee they coached graduating"""
        self.graduates_produced += 1

    # ==================== UI HELPERS ====================

    def get_specialty_icon(self) -> str:
        return SPECIALTY_INFO.get(self.specialty, {}).get("icon", "🎓")

    def get_specialty_color(self) -> str:
        return SPECIALTY_INFO.get(self.specialty, {}).get("color", "#6b7280")

    def get_type_color(self) -> str:
        colors = {
            CoachType.VETERAN: "#10b981",
            CoachType.NPC: "#3b82f6",
            CoachType.LEGEND: "#fbbf24",
        }
        return colors.get(self.coach_type, "#6b7280")

    def get_type_icon(self) -> str:
        icons = {
            CoachType.VETERAN: "🤼",
            CoachType.NPC: "👨‍🏫",
            CoachType.LEGEND: "🌟",
        }
        return icons.get(self.coach_type, "🎓")

    def get_status_color(self) -> str:
        colors = {
            CoachStatus.AVAILABLE: "#10b981",
            CoachStatus.ASSIGNED: "#f59e0b",
            CoachStatus.INJURED: "#dc2626",
            CoachStatus.RESTING: "#6b7280",
            CoachStatus.RETIRED: "#4b5563",
        }
        return colors.get(self.status, "#6b7280")

    def get_skill_tier(self) -> str:
        """Return skill tier description"""
        if self.skill_rating >= 90:
            return "Hall of Fame"
        if self.skill_rating >= 75:
            return "Elite"
        if self.skill_rating >= 60:
            return "Veteran"
        if self.skill_rating >= 45:
            return "Experienced"
        if self.skill_rating >= 30:
            return "Journeyman"
        return "Rookie"

    def get_summary_line(self, school=None) -> str:
        """Get summary line with school-discounted price"""
        cost = self.get_weekly_cost_with_school(school)
        return (f"{self.get_specialty_icon()} {self.name} — "
                f"{self.specialty.value} • "
                f"Skill {self.skill_rating}/100 • "
                f"${cost}/wk")

    def can_boost_class(self, class_type: str) -> bool:
        """Check if this coach's specialty boosts a given class"""
        boosted = SPECIALTY_INFO.get(self.specialty, {}).get("boosted_classes", [])
        return class_type in boosted

    def get_pricing_display(self, school=None) -> Dict:
        """Get pricing info for UI display"""
        actual_cost = self.get_weekly_cost_with_school(school)
        savings = self.get_savings_with_school(school)
        return {
            "base_weekly": self.base_weekly_cost,
            "actual_weekly": actual_cost,
            "savings_weekly": savings,
            "hire_cost": self.base_hire_cost,
            "has_discount": savings > 0,
            "discount_percent": int((savings / self.base_weekly_cost * 100)) if self.base_weekly_cost > 0 else 0,
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "coach_type": self.coach_type.value,
            "specialty": self.specialty.value,
            "skill_rating": self.skill_rating,
            "base_weekly_cost": self.base_weekly_cost,
            "base_hire_cost": self.base_hire_cost,
            "status": self.status.value,
            "weeks_employed": self.weeks_employed,
            "weeks_assigned_consecutive": self.weeks_assigned_consecutive,
            "trainees_coached": self.trainees_coached,
            "graduates_produced": self.graduates_produced,
            "total_xp_given": self.total_xp_given,
            "classes_taught": self.classes_taught,
            "is_legendary": self.is_legendary,
            "is_player_wrestler": self.is_player_wrestler,
            "wrestler_id": self.wrestler_id,
            "description": self.description,
            "age": self.age,
            "background": self.background,
            "xp_bonus_percent": self.xp_bonus_percent,
            "injury_risk_reduction": self.injury_risk_reduction,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Coach":
        try:
            ct = CoachType(data.get("coach_type", "Hired Coach"))
        except ValueError:
            ct = CoachType.NPC
        try:
            spec = CoachSpecialty(data.get("specialty", "All-Around"))
        except ValueError:
            spec = CoachSpecialty.ALL_AROUND
        try:
            status = CoachStatus(data.get("status", "Available"))
        except ValueError:
            status = CoachStatus.AVAILABLE

        # Backwards compatibility - check for old field names
        base_weekly = data.get("base_weekly_cost", data.get("weekly_cost", 200))
        base_hire = data.get("base_hire_cost", data.get("hire_cost", 0))

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            coach_type=ct,
            specialty=spec,
            skill_rating=data.get("skill_rating", 50),
            base_weekly_cost=base_weekly,
            base_hire_cost=base_hire,
            status=status,
            weeks_employed=data.get("weeks_employed", 0),
            weeks_assigned_consecutive=data.get("weeks_assigned_consecutive", 0),
            trainees_coached=data.get("trainees_coached", 0),
            graduates_produced=data.get("graduates_produced", 0),
            total_xp_given=data.get("total_xp_given", 0),
            classes_taught=data.get("classes_taught", 0),
            is_legendary=data.get("is_legendary", False),
            is_player_wrestler=data.get("is_player_wrestler", False),
            wrestler_id=data.get("wrestler_id", ""),
            description=data.get("description", ""),
            age=data.get("age", 45),
            background=data.get("background", ""),
            xp_bonus_percent=data.get("xp_bonus_percent", 10),
            injury_risk_reduction=data.get("injury_risk_reduction", 30),
        )


# ==================== COACH MANAGER ====================

class CoachManager:
    """Manages all coaches at the Training School with school-aware pricing"""

    def __init__(self):
        self.coaches: List[Coach] = []
        self.next_id_num: int = 1
        self.lifetime_payroll_paid: int = 0
        self.lifetime_savings: int = 0

    def _next_coach_id(self) -> str:
        cid = f"coach_{self.next_id_num}"
        self.next_id_num += 1
        return cid

    # ==================== HIRING / CREATION ====================

    def hire_coach(self, coach: Coach) -> bool:
        """Add a coach to the school"""
        if coach.id == "":
            coach.id = self._next_coach_id()
        coach.update_effectiveness()
        self.coaches.append(coach)
        return True

    def fire_coach(self, coach_id: str) -> bool:
        """Remove a coach from the school"""
        for i, coach in enumerate(self.coaches):
            if coach.id == coach_id:
                self.coaches.pop(i)
                return True
        return False

    def promote_wrestler_to_coach(
        self,
        wrestler_id: str,
        wrestler_name: str,
        wrestler_age: int,
        primary_stat_value: int,
        specialty: CoachSpecialty,
        weekly_cost: int = 200,
    ) -> Optional[Coach]:
        """Convert a roster wrestler into a coach"""
        # Skill rating based on the wrestler's primary stat
        skill_rating = min(95, primary_stat_value + random.randint(-5, 10))

        coach = Coach(
            id=self._next_coach_id(),
            name=wrestler_name,
            coach_type=CoachType.VETERAN,
            specialty=specialty,
            skill_rating=skill_rating,
            base_weekly_cost=weekly_cost,
            base_hire_cost=0,
            is_player_wrestler=True,
            wrestler_id=wrestler_id,
            age=wrestler_age,
            background=f"Former active wrestler now coaching {specialty.value.lower()}.",
        )
        coach.update_effectiveness()
        self.coaches.append(coach)
        return coach

    # ==================== QUERIES ====================

    def get_coach(self, coach_id: str) -> Optional[Coach]:
        for coach in self.coaches:
            if coach.id == coach_id:
                return coach
        return None

    def get_all_coaches(self) -> List[Coach]:
        return list(self.coaches)

    def get_active_coaches(self) -> List[Coach]:
        return [c for c in self.coaches if c.status != CoachStatus.RETIRED]

    def get_available_coaches(self) -> List[Coach]:
        return [c for c in self.coaches if c.status == CoachStatus.AVAILABLE]

    def get_coaches_by_specialty(self, specialty: CoachSpecialty) -> List[Coach]:
        return [c for c in self.coaches if c.specialty == specialty]

    def get_coaches_by_type(self, coach_type: CoachType) -> List[Coach]:
        return [c for c in self.coaches if c.coach_type == coach_type]

    def get_best_coach_for_class(self, class_type: str) -> Optional[Coach]:
        """Find the best available coach to teach a given class"""
        available = self.get_available_coaches()
        if not available:
            return None

        # Prioritize coaches whose specialty boosts this class
        boosted = [c for c in available if c.can_boost_class(class_type)]
        pool = boosted if boosted else available

        return max(pool, key=lambda c: c.skill_rating)

    def get_coach_count(self) -> int:
        return len(self.get_active_coaches())

    def get_total_weekly_cost(self, school=None) -> int:
        """Total weekly payroll for all active coaches (school-aware)"""
        return sum(c.get_weekly_cost_with_school(school) for c in self.get_active_coaches())

    def get_total_base_cost(self) -> int:
        """Total weekly payroll without any discounts"""
        return sum(c.base_weekly_cost for c in self.get_active_coaches())

    def get_total_savings(self, school=None) -> int:
        """Total weekly savings from school discount"""
        return sum(c.get_savings_with_school(school) for c in self.get_active_coaches())

    # ==================== WEEKLY PROCESSING ====================

    def process_weekly_update(
        self,
        assigned_coach_ids: List[str] = None,
        school=None,
    ) -> Dict:
        """Process all coaches' weekly updates with school discounts"""
        if assigned_coach_ids is None:
            assigned_coach_ids = []

        result = {
            "total_paid": 0,
            "total_savings": 0,
            "events": [],
            "retired_coaches": [],
        }

        for coach in self.coaches[:]:
            if coach.status == CoachStatus.RETIRED:
                continue

            was_assigned = coach.id in assigned_coach_ids
            update = coach.weekly_update(was_assigned=was_assigned, school=school)

            result["total_paid"] += update["income_paid"]
            result["total_savings"] += update.get("savings", 0)
            result["events"].extend(update["events"])

            if coach.status == CoachStatus.RETIRED:
                result["retired_coaches"].append(coach.name)

        # Track lifetime stats
        self.lifetime_payroll_paid += result["total_paid"]
        self.lifetime_savings += result["total_savings"]

        return result

    # ==================== COACH ASSIGNMENT ====================

    def assign_coach_to_class(self, coach_id: str) -> bool:
        """Mark a coach as actively teaching"""
        coach = self.get_coach(coach_id)
        if coach and coach.status == CoachStatus.AVAILABLE:
            coach.assign()
            return True
        return False

    def unassign_coach(self, coach_id: str) -> bool:
        """Free up a coach"""
        coach = self.get_coach(coach_id)
        if coach:
            coach.unassign()
            return True
        return False

    # ==================== UI SUMMARY ====================

    def get_payroll_summary(self, school=None) -> Dict:
        """Get full payroll summary for UI display"""
        active = self.get_active_coaches()
        return {
            "active_count": len(active),
            "total_weekly_cost": self.get_total_weekly_cost(school),
            "total_base_cost": self.get_total_base_cost(),
            "weekly_savings": self.get_total_savings(school),
            "lifetime_paid": self.lifetime_payroll_paid,
            "lifetime_savings": self.lifetime_savings,
            "by_type": {
                "veterans": len(self.get_coaches_by_type(CoachType.VETERAN)),
                "npcs": len(self.get_coaches_by_type(CoachType.NPC)),
                "legends": len(self.get_coaches_by_type(CoachType.LEGEND)),
            },
            "available_count": len(self.get_available_coaches()),
            "assigned_count": len([c for c in active if c.status == CoachStatus.ASSIGNED]),
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "coaches": [c.to_dict() for c in self.coaches],
            "next_id_num": self.next_id_num,
            "lifetime_payroll_paid": self.lifetime_payroll_paid,
            "lifetime_savings": self.lifetime_savings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoachManager":
        manager = cls()
        manager.next_id_num = data.get("next_id_num", 1)
        manager.lifetime_payroll_paid = data.get("lifetime_payroll_paid", 0)
        manager.lifetime_savings = data.get("lifetime_savings", 0)
        for cd in data.get("coaches", []):
            try:
                manager.coaches.append(Coach.from_dict(cd))
            except Exception:
                pass
        return manager
