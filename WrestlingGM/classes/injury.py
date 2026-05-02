"""
Injury System - Track wrestler injuries, recovery, and surgery decisions
Integrates with inbox for notifications and morale system
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class InjuryType(Enum):
    MINOR_BRUISE = "Minor Bruising"
    STINGER = "Stinger"
    SPRAIN = "Sprain"
    CONCUSSION = "Concussion"
    PULLED_MUSCLE = "Pulled Muscle"
    TORN_MUSCLE = "Torn Muscle"
    BROKEN_NOSE = "Broken Nose"
    BROKEN_FINGER = "Broken Finger"
    CRACKED_RIB = "Cracked Rib"
    BROKEN_RIB = "Broken Rib"
    DISLOCATED_SHOULDER = "Dislocated Shoulder"
    TORN_ACL = "Torn ACL"
    TORN_MCL = "Torn MCL"
    TORN_ROTATOR_CUFF = "Torn Rotator Cuff"
    HERNIATED_DISC = "Herniated Disc"
    BROKEN_ARM = "Broken Arm"
    BROKEN_LEG = "Broken Leg"
    NECK_INJURY = "Neck Injury"
    BACK_INJURY = "Back Injury"
    KNEE_INJURY = "Knee Injury"


class InjurySeverity(Enum):
    MINOR = "Minor"
    MODERATE = "Moderate"
    SERIOUS = "Serious"
    SEVERE = "Severe"
    CAREER_THREATENING = "Career Threatening"


class InjuryStatus(Enum):
    ACTIVE = "Active"
    RECOVERING = "Recovering"
    SURGERY_NEEDED = "Surgery Needed"
    SURGERY_SCHEDULED = "Surgery Scheduled"
    POST_SURGERY = "Post-Surgery Recovery"
    CLEARED = "Cleared to Compete"
    CHRONIC = "Chronic (Managed)"


INJURY_DATA = {
    InjuryType.MINOR_BRUISE: {"severity": InjurySeverity.MINOR, "base_recovery_days": 3, "surgery_chance": 0, "description": "Minor bruising from hard bumps."},
    InjuryType.STINGER: {"severity": InjurySeverity.MINOR, "base_recovery_days": 5, "surgery_chance": 0, "description": "Nerve pain in the neck/shoulder area."},
    InjuryType.SPRAIN: {"severity": InjurySeverity.MINOR, "base_recovery_days": 10, "surgery_chance": 0, "description": "Sprained joint from awkward landing."},
    InjuryType.CONCUSSION: {"severity": InjurySeverity.MODERATE, "base_recovery_days": 21, "surgery_chance": 0, "description": "Head trauma requiring rest and monitoring."},
    InjuryType.PULLED_MUSCLE: {"severity": InjurySeverity.MINOR, "base_recovery_days": 14, "surgery_chance": 0, "description": "Muscle strain from overexertion."},
    InjuryType.TORN_MUSCLE: {"severity": InjurySeverity.SERIOUS, "base_recovery_days": 60, "surgery_chance": 40, "description": "Torn muscle fiber requiring possible surgery."},
    InjuryType.BROKEN_NOSE: {"severity": InjurySeverity.MINOR, "base_recovery_days": 14, "surgery_chance": 10, "description": "Broken nose from a stiff shot."},
    InjuryType.BROKEN_FINGER: {"severity": InjurySeverity.MINOR, "base_recovery_days": 21, "surgery_chance": 5, "description": "Broken finger, can work through it if taped."},
    InjuryType.CRACKED_RIB: {"severity": InjurySeverity.MODERATE, "base_recovery_days": 30, "surgery_chance": 5, "description": "Cracked rib from impact."},
    InjuryType.BROKEN_RIB: {"severity": InjurySeverity.SERIOUS, "base_recovery_days": 45, "surgery_chance": 15, "description": "Fully broken rib, risk of internal damage."},
    InjuryType.DISLOCATED_SHOULDER: {"severity": InjurySeverity.MODERATE, "base_recovery_days": 30, "surgery_chance": 25, "description": "Shoulder popped out of socket."},
    InjuryType.TORN_ACL: {"severity": InjurySeverity.SEVERE, "base_recovery_days": 180, "surgery_chance": 90, "description": "Torn anterior cruciate ligament. Surgery almost certainly required."},
    InjuryType.TORN_MCL: {"severity": InjurySeverity.SERIOUS, "base_recovery_days": 90, "surgery_chance": 50, "description": "Torn medial collateral ligament."},
    InjuryType.TORN_ROTATOR_CUFF: {"severity": InjurySeverity.SEVERE, "base_recovery_days": 150, "surgery_chance": 85, "description": "Torn rotator cuff requiring surgery."},
    InjuryType.HERNIATED_DISC: {"severity": InjurySeverity.SEVERE, "base_recovery_days": 120, "surgery_chance": 60, "description": "Spinal disc herniation. Careful management needed."},
    InjuryType.BROKEN_ARM: {"severity": InjurySeverity.SERIOUS, "base_recovery_days": 60, "surgery_chance": 30, "description": "Fractured arm bone."},
    InjuryType.BROKEN_LEG: {"severity": InjurySeverity.SERIOUS, "base_recovery_days": 90, "surgery_chance": 40, "description": "Fractured leg bone."},
    InjuryType.NECK_INJURY: {"severity": InjurySeverity.CAREER_THREATENING, "base_recovery_days": 180, "surgery_chance": 70, "description": "Serious neck injury. Career may be at risk."},
    InjuryType.BACK_INJURY: {"severity": InjurySeverity.SEVERE, "base_recovery_days": 120, "surgery_chance": 50, "description": "Significant back injury."},
    InjuryType.KNEE_INJURY: {"severity": InjurySeverity.MODERATE, "base_recovery_days": 45, "surgery_chance": 30, "description": "General knee injury."},
}

SURGERY_COSTS = {
    InjurySeverity.MINOR: 500,
    InjurySeverity.MODERATE: 2000,
    InjurySeverity.SERIOUS: 5000,
    InjurySeverity.SEVERE: 15000,
    InjurySeverity.CAREER_THREATENING: 30000,
}

SURGERY_RECOVERY_REDUCTION = 0.3  # Surgery reduces recovery time by 30%


@dataclass
class Injury:
    id: str
    wrestler_name: str
    injury_type: InjuryType
    severity: InjurySeverity
    status: InjuryStatus = InjuryStatus.ACTIVE
    description: str = ""
    recovery_days_total: int = 0
    recovery_days_remaining: int = 0
    date_injured: str = ""
    date_cleared: str = ""
    surgery_needed: bool = False
    surgery_cost: int = 0
    surgery_decision_made: bool = False
    promotion_pays_surgery: bool = False
    morale_impact: int = 0
    match_where_injured: str = ""
    can_work_through: bool = False

    def daily_recovery(self, medical_bonus: int = 0) -> bool:
        """Process one day of recovery. Returns True if cleared."""
        if self.status in [InjuryStatus.CLEARED, InjuryStatus.SURGERY_NEEDED]:
            return self.status == InjuryStatus.CLEARED

        bonus_days = medical_bonus * 0.01
        self.recovery_days_remaining -= (1 + bonus_days)

        if self.recovery_days_remaining <= 0:
            self.recovery_days_remaining = 0
            self.status = InjuryStatus.CLEARED
            return True

        return False

    def schedule_surgery(self, promotion_pays: bool = True):
        """Schedule surgery for this injury"""
        self.surgery_decision_made = True
        self.promotion_pays_surgery = promotion_pays
        self.status = InjuryStatus.SURGERY_SCHEDULED

        # Surgery reduces recovery time
        self.recovery_days_remaining = int(self.recovery_days_remaining * (1 - SURGERY_RECOVERY_REDUCTION))

        # Morale impact
        if promotion_pays:
            self.morale_impact = 15  # Wrestler appreciates it
        else:
            self.morale_impact = -20  # Wrestler resents paying themselves

    def decline_surgery(self):
        """Decline surgery - longer recovery, risk of reinjury"""
        self.surgery_decision_made = True
        self.surgery_needed = False
        self.status = InjuryStatus.RECOVERING
        # Recovery takes 50% longer without surgery
        self.recovery_days_remaining = int(self.recovery_days_remaining * 1.5)
        self.morale_impact = -5

    def get_recovery_percentage(self) -> float:
        if self.recovery_days_total <= 0:
            return 100.0
        recovered = self.recovery_days_total - self.recovery_days_remaining
        return min(100.0, (recovered / self.recovery_days_total) * 100)

    def get_severity_color(self) -> str:
        colors = {
            InjurySeverity.MINOR: "#10b981",
            InjurySeverity.MODERATE: "#f59e0b",
            InjurySeverity.SERIOUS: "#ef4444",
            InjurySeverity.SEVERE: "#dc2626",
            InjurySeverity.CAREER_THREATENING: "#7f1d1d",
        }
        return colors.get(self.severity, "#6b7280")

    def to_dict(self) -> dict:
        return {
            "id": self.id, "wrestler_name": self.wrestler_name,
            "injury_type": self.injury_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "description": self.description,
            "recovery_days_total": self.recovery_days_total,
            "recovery_days_remaining": self.recovery_days_remaining,
            "date_injured": self.date_injured,
            "date_cleared": self.date_cleared,
            "surgery_needed": self.surgery_needed,
            "surgery_cost": self.surgery_cost,
            "surgery_decision_made": self.surgery_decision_made,
            "promotion_pays_surgery": self.promotion_pays_surgery,
            "morale_impact": self.morale_impact,
            "match_where_injured": self.match_where_injured,
            "can_work_through": self.can_work_through,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Injury":
        return cls(
            id=data["id"], wrestler_name=data["wrestler_name"],
            injury_type=InjuryType(data["injury_type"]),
            severity=InjurySeverity(data["severity"]),
            status=InjuryStatus(data.get("status", "Active")),
            description=data.get("description", ""),
            recovery_days_total=data.get("recovery_days_total", 0),
            recovery_days_remaining=data.get("recovery_days_remaining", 0),
            date_injured=data.get("date_injured", ""),
            date_cleared=data.get("date_cleared", ""),
            surgery_needed=data.get("surgery_needed", False),
            surgery_cost=data.get("surgery_cost", 0),
            surgery_decision_made=data.get("surgery_decision_made", False),
            promotion_pays_surgery=data.get("promotion_pays_surgery", False),
            morale_impact=data.get("morale_impact", 0),
            match_where_injured=data.get("match_where_injured", ""),
            can_work_through=data.get("can_work_through", False),
        )


class InjuryManager:
    def __init__(self):
        self.active_injuries: List[Injury] = []
        self.injury_history: List[Injury] = []
        self.next_id: int = 1

    def generate_injury(self, wrestler_name: str, match_type: str = "",
                        date_str: str = "", medical_reduction: int = 0,
                        weapon_injury_mod: int = 0) -> Optional[Injury]:
        """Generate a random injury based on match context"""

        # Base injury chance
        injury_chance = random.randint(1, 100)
        threshold = 8 + weapon_injury_mod  # ~8% base chance per match

        # Medical reduction lowers chance
        threshold = max(1, threshold - int(medical_reduction * 0.05))

        if injury_chance > threshold:
            return None

        # Determine injury type based on weighted randomness
        minor_types = [InjuryType.MINOR_BRUISE, InjuryType.STINGER, InjuryType.SPRAIN,
                       InjuryType.PULLED_MUSCLE, InjuryType.BROKEN_FINGER]
        moderate_types = [InjuryType.CONCUSSION, InjuryType.CRACKED_RIB,
                          InjuryType.DISLOCATED_SHOULDER, InjuryType.KNEE_INJURY, InjuryType.BROKEN_NOSE]
        serious_types = [InjuryType.TORN_MUSCLE, InjuryType.BROKEN_RIB,
                         InjuryType.TORN_MCL, InjuryType.BROKEN_ARM, InjuryType.BROKEN_LEG]
        severe_types = [InjuryType.TORN_ACL, InjuryType.TORN_ROTATOR_CUFF,
                        InjuryType.HERNIATED_DISC, InjuryType.BACK_INJURY]
        career_types = [InjuryType.NECK_INJURY]

        severity_roll = random.randint(1, 100)
        if severity_roll <= 45:
            injury_type = random.choice(minor_types)
        elif severity_roll <= 75:
            injury_type = random.choice(moderate_types)
        elif severity_roll <= 90:
            injury_type = random.choice(serious_types)
        elif severity_roll <= 98:
            injury_type = random.choice(severe_types)
        else:
            injury_type = random.choice(career_types)

        injury_data = INJURY_DATA[injury_type]
        severity = injury_data["severity"]

        # Calculate recovery with some variance
        base_days = injury_data["base_recovery_days"]
        variance = random.randint(-int(base_days * 0.2), int(base_days * 0.2))
        recovery_days = max(1, base_days + variance)

        # Medical bonus reduces recovery
        if medical_reduction > 0:
            recovery_days = int(recovery_days * (1 - medical_reduction * 0.003))

        # Determine if surgery needed
        surgery_needed = random.randint(1, 100) <= injury_data["surgery_chance"]
        surgery_cost = SURGERY_COSTS.get(severity, 5000) if surgery_needed else 0

        # Can work through minor injuries
        can_work = severity == InjurySeverity.MINOR and random.random() < 0.5

        injury = Injury(
            id=f"injury_{self.next_id}",
            wrestler_name=wrestler_name,
            injury_type=injury_type,
            severity=severity,
            status=InjuryStatus.SURGERY_NEEDED if surgery_needed else InjuryStatus.RECOVERING,
            description=injury_data["description"],
            recovery_days_total=recovery_days,
            recovery_days_remaining=recovery_days,
            date_injured=date_str,
            surgery_needed=surgery_needed,
            surgery_cost=surgery_cost,
            match_where_injured=match_type,
            can_work_through=can_work,
        )

        self.next_id += 1
        self.active_injuries.append(injury)
        return injury

    def process_daily_recovery(self, medical_bonus: int = 0) -> List[Injury]:
        """Process one day of recovery for all injured wrestlers. Returns newly cleared injuries."""
        cleared = []
        for injury in self.active_injuries[:]:
            if injury.daily_recovery(medical_bonus):
                cleared.append(injury)
                self.active_injuries.remove(injury)
                self.injury_history.append(injury)
        return cleared

    def get_injury(self, injury_id: str) -> Optional[Injury]:
        for inj in self.active_injuries:
            if inj.id == injury_id:
                return inj
        return None

    def get_wrestler_injuries(self, wrestler_name: str) -> List[Injury]:
        return [inj for inj in self.active_injuries if inj.wrestler_name == wrestler_name]

    def get_injuries_needing_surgery_decision(self) -> List[Injury]:
        return [inj for inj in self.active_injuries
                if inj.surgery_needed and not inj.surgery_decision_made]

    def get_active_count(self) -> int:
        return len(self.active_injuries)

    def to_dict(self) -> dict:
        return {
            "active_injuries": [inj.to_dict() for inj in self.active_injuries],
            "injury_history": [inj.to_dict() for inj in self.injury_history[-50:]],
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InjuryManager":
        manager = cls()
        manager.next_id = data.get("next_id", 1)
        for ind in data.get("active_injuries", []):
            manager.active_injuries.append(Injury.from_dict(ind))
        for ind in data.get("injury_history", []):
            manager.injury_history.append(Injury.from_dict(ind))
        return manager
