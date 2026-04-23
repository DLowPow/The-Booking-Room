"""
Venue System - Realistic venues with time limits, perks, day modifiers
Bars, community centers, arenas, stadiums with unique traits
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


class VenueTier(Enum):
    BACKYARD = 1
    BAR_CLUB = 2
    COMMUNITY = 3
    THEATER = 4
    ARENA = 5
    LARGE_ARENA = 6
    STADIUM = 7


class VenuePerk(Enum):
    ALCOHOL_SALES = "Alcohol Sales"
    EARLY_OPEN = "Early Open Discount"
    LATE_NIGHT = "Late Night Shows"
    FAMILY_FRIENDLY = "Family Friendly"
    PREMIUM_SEATING = "Premium Seating"
    VIP_LOUNGE = "VIP Lounge"
    PARKING_INCLUDED = "Free Parking"
    CONCESSION_DEAL = "Concession Revenue Share"
    PYRO_ALLOWED = "Pyro Allowed"
    OUTDOOR = "Outdoor Venue"
    HISTORIC = "Historic Venue"
    TV_READY = "TV Production Ready"
    MERCH_TABLES = "Merch Table Space"
    BACKSTAGE_LARGE = "Large Backstage Area"
    CHEAP_RENTAL = "Budget Friendly"
    SOUND_SYSTEM = "Pro Sound System"
    STREAMING_SETUP = "Streaming Ready"


class VenueRestriction(Enum):
    NO_HARDCORE = "No Hardcore Matches"
    NO_PYRO = "No Pyrotechnics"
    NO_BLOOD = "No Blood/Blading"
    NOISE_CURFEW = "Noise Curfew (10PM)"
    NOISE_CURFEW_LATE = "Noise Curfew (11PM)"
    NO_ALCOHOL = "No Alcohol"
    AGE_RESTRICTED = "21+ Only"
    FAMILY_ONLY = "Family Content Only"
    MAX_CAPACITY_STRICT = "Strict Fire Code"
    NO_TABLES_SPOTS = "No Table Spots"
    SETUP_TIME_LIMITED = "Limited Setup Time"
    SHARED_SPACE = "Shared Space (Quick Cleanup)"


# ==================== DAY OF WEEK ====================

class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


# Default day modifiers (attendance multiplier, cost multiplier)
DEFAULT_DAY_MODIFIERS = {
    "Monday": {"attendance": 0.70, "cost": 0.80, "label": "Slow Night"},
    "Tuesday": {"attendance": 0.75, "cost": 0.80, "label": "Quiet"},
    "Wednesday": {"attendance": 0.80, "cost": 0.85, "label": "Midweek"},
    "Thursday": {"attendance": 0.85, "cost": 0.90, "label": "Getting Busy"},
    "Friday": {"attendance": 1.10, "cost": 1.10, "label": "Friday Night"},
    "Saturday": {"attendance": 1.25, "cost": 1.20, "label": "Prime Time"},
    "Sunday": {"attendance": 1.05, "cost": 1.00, "label": "Weekend"},
}


# ==================== MATCH TIME SYSTEM ====================

MATCH_TIME_OPTIONS = {
    "Quick": {
        "minutes": 5,
        "label": "Quick (5 min)",
        "rating_modifier": -0.5,
        "description": "Squash match. Low ceiling but safe.",
        "min_skill": 0,
        "crowd_energy": -10,
        "fatigue": 3,
    },
    "Short": {
        "minutes": 8,
        "label": "Short (8 min)",
        "rating_modifier": -0.2,
        "description": "Short and sweet. Gets the job done.",
        "min_skill": 0,
        "crowd_energy": -5,
        "fatigue": 5,
    },
    "Standard": {
        "minutes": 12,
        "label": "Standard (12 min)",
        "rating_modifier": 0.0,
        "description": "Normal match length. Balanced risk/reward.",
        "min_skill": 25,
        "crowd_energy": 0,
        "fatigue": 8,
    },
    "Long": {
        "minutes": 18,
        "label": "Long (18 min)",
        "rating_modifier": 0.3,
        "description": "Extended match. Higher ceiling if wrestlers can go.",
        "min_skill": 40,
        "crowd_energy": 5,
        "fatigue": 12,
    },
    "Epic": {
        "minutes": 25,
        "label": "Epic (25 min)",
        "rating_modifier": 0.6,
        "description": "Major match. Big reward but needs top talent.",
        "min_skill": 55,
        "crowd_energy": 10,
        "fatigue": 18,
    },
    "Broadway": {
        "minutes": 30,
        "label": "Broadway (30 min)",
        "rating_modifier": 0.8,
        "description": "Classic length. Only elite wrestlers can deliver.",
        "min_skill": 70,
        "crowd_energy": 15,
        "fatigue": 25,
    },
}


def get_time_quality_modifier(time_option: str, avg_skill: float) -> float:
    """Calculate rating modifier based on time and wrestler skill"""
    option = MATCH_TIME_OPTIONS.get(time_option, MATCH_TIME_OPTIONS["Standard"])
    base_mod = option["rating_modifier"]
    min_skill = option["min_skill"]

    if avg_skill < min_skill:
        # Penalty for wrestlers who can't go that long
        skill_gap = min_skill - avg_skill
        penalty = -(skill_gap * 0.03)
        return base_mod + penalty
    else:
        # Bonus for skilled wrestlers in long matches
        skill_bonus = (avg_skill - min_skill) * 0.005
        return base_mod + min(skill_bonus, 0.3)


# ==================== OVERRUN SYSTEM ====================

OVERRUN_PENALTIES = {
    "warning": {
        "minutes_over": 5,
        "fine": 500,
        "prestige_loss": 1,
        "message": "⚠️ Show ran slightly over time. Small fine.",
    },
    "moderate": {
        "minutes_over": 10,
        "fine": 2000,
        "prestige_loss": 3,
        "venue_trust_loss": 10,
        "message": "⚠️ Show overran by 10+ minutes! Venue is unhappy.",
    },
    "severe": {
        "minutes_over": 15,
        "fine": 5000,
        "prestige_loss": 5,
        "venue_trust_loss": 25,
        "venue_ban_weeks": 4,
        "message": "🚫 Show severely overran! Venue may ban you.",
    },
    "catastrophic": {
        "minutes_over": 25,
        "fine": 10000,
        "prestige_loss": 10,
        "venue_trust_loss": 50,
        "venue_ban_weeks": 12,
        "fan_loss": 500,
        "message": "🚫 CATASTROPHIC overrun! Major fines and venue ban!",
    },
}


def calculate_overrun_penalty(minutes_over: int) -> Dict:
    """Get the penalty for overrunning the show"""
    if minutes_over <= 0:
        return {"penalty_level": "none", "fine": 0, "message": "✅ Show finished on time!"}

    if minutes_over <= 5:
        penalty = OVERRUN_PENALTIES["warning"].copy()
    elif minutes_over <= 10:
        penalty = OVERRUN_PENALTIES["moderate"].copy()
    elif minutes_over <= 20:
        penalty = OVERRUN_PENALTIES["severe"].copy()
    else:
        penalty = OVERRUN_PENALTIES["catastrophic"].copy()

    # Scale fine by actual minutes
    scale = minutes_over / penalty["minutes_over"]
    penalty["fine"] = int(penalty["fine"] * scale)
    penalty["actual_minutes_over"] = minutes_over
    return penalty


# ==================== VENUE TIER DEFAULTS ====================

VENUE_TIER_DEFAULTS = {
    VenueTier.BACKYARD: {
        "capacity_range": (20, 75),
        "cost_range": (50, 200),
        "max_show_minutes": 90,
        "prestige_range": (1, 10),
        "ticket_price_range": (5, 10),
        "default_perks": [VenuePerk.CHEAP_RENTAL, VenuePerk.OUTDOOR],
        "default_restrictions": [VenueRestriction.NO_PYRO, VenueRestriction.SETUP_TIME_LIMITED],
        "buffer_minutes": 15,
        "alcohol_revenue_per_head": 0,
        "concession_revenue_per_head": 2,
    },
    VenueTier.BAR_CLUB: {
        "capacity_range": (50, 250),
        "cost_range": (150, 800),
        "max_show_minutes": 120,
        "prestige_range": (5, 20),
        "ticket_price_range": (10, 20),
        "default_perks": [VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT],
        "default_restrictions": [VenueRestriction.NO_PYRO, VenueRestriction.NOISE_CURFEW_LATE, VenueRestriction.AGE_RESTRICTED],
        "buffer_minutes": 15,
        "alcohol_revenue_per_head": 8,
        "concession_revenue_per_head": 3,
    },
    VenueTier.COMMUNITY: {
        "capacity_range": (100, 500),
        "cost_range": (200, 1500),
        "max_show_minutes": 150,
        "prestige_range": (10, 30),
        "ticket_price_range": (10, 25),
        "default_perks": [VenuePerk.FAMILY_FRIENDLY, VenuePerk.PARKING_INCLUDED, VenuePerk.MERCH_TABLES],
        "default_restrictions": [VenueRestriction.NO_BLOOD, VenueRestriction.NO_ALCOHOL, VenueRestriction.NOISE_CURFEW],
        "buffer_minutes": 20,
        "alcohol_revenue_per_head": 0,
        "concession_revenue_per_head": 5,
    },
    VenueTier.THEATER: {
        "capacity_range": (300, 2000),
        "cost_range": (1000, 5000),
        "max_show_minutes": 180,
        "prestige_range": (20, 45),
        "ticket_price_range": (15, 40),
        "default_perks": [VenuePerk.SOUND_SYSTEM, VenuePerk.PREMIUM_SEATING, VenuePerk.BACKSTAGE_LARGE],
        "default_restrictions": [VenueRestriction.NO_PYRO],
        "buffer_minutes": 20,
        "alcohol_revenue_per_head": 5,
        "concession_revenue_per_head": 6,
    },
    VenueTier.ARENA: {
        "capacity_range": (2000, 8000),
        "cost_range": (5000, 20000),
        "max_show_minutes": 180,
        "prestige_range": (35, 65),
        "ticket_price_range": (20, 60),
        "default_perks": [VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.CONCESSION_DEAL],
        "default_restrictions": [],
        "buffer_minutes": 30,
        "alcohol_revenue_per_head": 7,
        "concession_revenue_per_head": 8,
    },
    VenueTier.LARGE_ARENA: {
        "capacity_range": (8000, 25000),
        "cost_range": (15000, 60000),
        "max_show_minutes": 210,
        "prestige_range": (50, 80),
        "ticket_price_range": (30, 100),
        "default_perks": [VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP],
        "default_restrictions": [],
        "buffer_minutes": 30,
        "alcohol_revenue_per_head": 10,
        "concession_revenue_per_head": 10,
    },
    VenueTier.STADIUM: {
        "capacity_range": (20000, 80000),
        "cost_range": (50000, 250000),
        "max_show_minutes": 240,
        "prestige_range": (70, 100),
        "ticket_price_range": (40, 150),
        "default_perks": [VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP, VenuePerk.CONCESSION_DEAL],
        "default_restrictions": [],
        "buffer_minutes": 45,
        "alcohol_revenue_per_head": 12,
        "concession_revenue_per_head": 15,
    },
}


# ==================== VENUE CLASS ====================

@dataclass
class Venue:
    id: str
    name: str
    city: str
    tier: VenueTier
    capacity: int
    rental_cost: int
    prestige: int = 20

    # Time system
    max_show_minutes: int = 120
    buffer_minutes: int = 15

    # Revenue modifiers
    alcohol_revenue_per_head: int = 0
    concession_revenue_per_head: int = 5

    # Perks and restrictions
    perks: List[VenuePerk] = field(default_factory=list)
    restrictions: List[VenueRestriction] = field(default_factory=list)

    # Day modifiers (override defaults)
    day_modifiers: Dict = field(default_factory=dict)
    best_days: List[str] = field(default_factory=list)
    worst_days: List[str] = field(default_factory=list)

    # Ticket pricing
    base_ticket_price: int = 15
    vip_ticket_price: int = 0
    vip_capacity_pct: float = 0.0

    # Tracking
    events_held: int = 0
    total_attendance: int = 0
    total_revenue: int = 0
    trust_level: int = 100
    is_banned_until_week: int = 0
    is_unlocked: bool = True

    # Description and flavor
    description: str = ""
    atmosphere: str = "Standard"

    def get_tier_name(self) -> str:
        names = {
            VenueTier.BACKYARD: "🏡 Backyard",
            VenueTier.BAR_CLUB: "🍺 Bar/Club",
            VenueTier.COMMUNITY: "🏛️ Community Center",
            VenueTier.THEATER: "🎭 Theater",
            VenueTier.ARENA: "🏟️ Arena",
            VenueTier.LARGE_ARENA: "🏟️ Large Arena",
            VenueTier.STADIUM: "🏟️ Stadium",
        }
        return names.get(self.tier, "Unknown")

    def get_available_minutes(self) -> int:
        """Total minutes available for matches (max - buffer)"""
        return self.max_show_minutes - self.buffer_minutes

    def get_day_modifier(self, day_name: str) -> Dict:
        """Get attendance/cost modifiers for a specific day"""
        if day_name in self.day_modifiers:
            return self.day_modifiers[day_name]
        return DEFAULT_DAY_MODIFIERS.get(day_name, {"attendance": 1.0, "cost": 1.0, "label": ""})

    def get_rental_cost(self, day_name: str = "Saturday") -> int:
        """Get rental cost adjusted for day of week"""
        day_mod = self.get_day_modifier(day_name)
        return int(self.rental_cost * day_mod.get("cost", 1.0))

    def get_expected_attendance(self, prestige: int, day_name: str = "Saturday") -> int:
        """Calculate expected attendance based on prestige and day"""
        base = min(self.capacity, int(self.capacity * (prestige / 100) * 0.8))
        base = max(int(self.capacity * 0.15), base)
        day_mod = self.get_day_modifier(day_name)
        adjusted = int(base * day_mod.get("attendance", 1.0))

        # Trust affects attendance
        trust_mod = self.trust_level / 100
        adjusted = int(adjusted * trust_mod)

        # Perks affect attendance
        if VenuePerk.HISTORIC in self.perks:
            adjusted = int(adjusted * 1.05)
        if VenuePerk.PARKING_INCLUDED in self.perks:
            adjusted = int(adjusted * 1.03)

        return min(adjusted, self.capacity)

    def get_ticket_price_range(self) -> Dict:
        """Get ticket prices including VIP if available"""
        result = {"standard": self.base_ticket_price}
        if VenuePerk.PREMIUM_SEATING in self.perks and self.vip_ticket_price > 0:
            result["vip"] = self.vip_ticket_price
            result["vip_capacity"] = int(self.capacity * self.vip_capacity_pct)
        return result

    def calculate_revenue(self, attendance: int, day_name: str = "Saturday") -> Dict:
        """Calculate all revenue streams for this venue"""
        ticket_revenue = attendance * self.base_ticket_price

        # VIP revenue
        vip_revenue = 0
        if VenuePerk.PREMIUM_SEATING in self.perks and self.vip_ticket_price > 0:
            vip_count = min(int(attendance * self.vip_capacity_pct), int(self.capacity * self.vip_capacity_pct))
            vip_revenue = vip_count * (self.vip_ticket_price - self.base_ticket_price)

        # Alcohol revenue
        alcohol_revenue = 0
        if VenuePerk.ALCOHOL_SALES in self.perks:
            alcohol_revenue = attendance * self.alcohol_revenue_per_head

        # Concession revenue
        concession_revenue = attendance * self.concession_revenue_per_head
        if VenuePerk.CONCESSION_DEAL in self.perks:
            concession_revenue = int(concession_revenue * 1.25)

        return {
            "tickets": ticket_revenue,
            "vip": vip_revenue,
            "alcohol": alcohol_revenue,
            "concessions": concession_revenue,
            "total": ticket_revenue + vip_revenue + alcohol_revenue + concession_revenue,
        }

    def can_host_match_type(self, match_type: str) -> tuple:
        """Check if venue restrictions allow this match type"""
        hardcore_types = ["Hardcore", "Deathmatch", "Tables", "TLC", "Inferno", "Buried Alive", "Last Man Standing"]
        blood_types = ["Hardcore", "Deathmatch", "Inferno", "Buried Alive", "Hell in a Cell"]
        pyro_types = ["Inferno"]
        table_types = ["Tables", "TLC"]

        if VenueRestriction.NO_HARDCORE in self.restrictions:
            if match_type in hardcore_types:
                return False, f"🚫 {self.name} does not allow hardcore matches"

        if VenueRestriction.NO_BLOOD in self.restrictions:
            if match_type in blood_types:
                return False, f"🚫 {self.name} does not allow blood matches"

        if VenueRestriction.NO_PYRO in self.restrictions:
            if match_type in pyro_types:
                return False, f"🚫 {self.name} does not allow pyrotechnics"

        if VenueRestriction.NO_TABLES_SPOTS in self.restrictions:
            if match_type in table_types:
                return False, f"🚫 {self.name} does not allow table spots"

        return True, "OK"

    def is_available(self, current_week: int = 0) -> bool:
        """Check if venue is available (not banned)"""
        if not self.is_unlocked:
            return False
        if self.is_banned_until_week > 0 and current_week < self.is_banned_until_week:
            return False
        return True

    def apply_overrun_penalty(self, minutes_over: int, current_week: int = 0):
        """Apply penalties for overrunning the show"""
        penalty = calculate_overrun_penalty(minutes_over)
        if "venue_trust_loss" in penalty:
            self.trust_level = max(0, self.trust_level - penalty["venue_trust_loss"])
        if "venue_ban_weeks" in penalty:
            self.is_banned_until_week = current_week + penalty["venue_ban_weeks"]
        return penalty

    def record_event(self, attendance: int, revenue: int):
        """Record that an event was held here"""
        self.events_held += 1
        self.total_attendance += attendance
        self.total_revenue += revenue
        # Restore trust slowly
        if self.trust_level < 100:
            self.trust_level = min(100, self.trust_level + 2)

    def get_perks_display(self) -> List[Dict]:
        """Get display-friendly list of perks"""
        perk_icons = {
            VenuePerk.ALCOHOL_SALES: "🍺",
            VenuePerk.EARLY_OPEN: "🌅",
            VenuePerk.LATE_NIGHT: "🌙",
            VenuePerk.FAMILY_FRIENDLY: "👨‍👩‍👧‍👦",
            VenuePerk.PREMIUM_SEATING: "💎",
            VenuePerk.VIP_LOUNGE: "🥂",
            VenuePerk.PARKING_INCLUDED: "🅿️",
            VenuePerk.CONCESSION_DEAL: "🍿",
            VenuePerk.PYRO_ALLOWED: "🔥",
            VenuePerk.OUTDOOR: "🌳",
            VenuePerk.HISTORIC: "🏛️",
            VenuePerk.TV_READY: "📺",
            VenuePerk.MERCH_TABLES: "👕",
            VenuePerk.BACKSTAGE_LARGE: "🚪",
            VenuePerk.CHEAP_RENTAL: "💲",
            VenuePerk.SOUND_SYSTEM: "🔊",
            VenuePerk.STREAMING_SETUP: "📡",
        }
        return [{"icon": perk_icons.get(p, "✅"), "name": p.value} for p in self.perks]

    def get_restrictions_display(self) -> List[Dict]:
        """Get display-friendly list of restrictions"""
        return [{"icon": "🚫", "name": r.value} for r in self.restrictions]

    def get_best_days_display(self) -> str:
        if self.best_days:
            return ", ".join(self.best_days)
        return "Saturday, Friday"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "city": self.city,
            "tier": self.tier.value, "capacity": self.capacity,
            "rental_cost": self.rental_cost, "prestige": self.prestige,
            "max_show_minutes": self.max_show_minutes,
            "buffer_minutes": self.buffer_minutes,
            "alcohol_revenue_per_head": self.alcohol_revenue_per_head,
            "concession_revenue_per_head": self.concession_revenue_per_head,
            "perks": [p.value for p in self.perks],
            "restrictions": [r.value for r in self.restrictions],
            "day_modifiers": self.day_modifiers,
            "best_days": self.best_days,
            "worst_days": self.worst_days,
            "base_ticket_price": self.base_ticket_price,
            "vip_ticket_price": self.vip_ticket_price,
            "vip_capacity_pct": self.vip_capacity_pct,
            "events_held": self.events_held,
            "total_attendance": self.total_attendance,
            "total_revenue": self.total_revenue,
            "trust_level": self.trust_level,
            "is_banned_until_week": self.is_banned_until_week,
            "is_unlocked": self.is_unlocked,
            "description": self.description,
            "atmosphere": self.atmosphere,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Venue":
        venue = cls(
            id=data["id"], name=data["name"], city=data.get("city", ""),
            tier=VenueTier(data["tier"]), capacity=data["capacity"],
            rental_cost=data["rental_cost"], prestige=data.get("prestige", 20),
            max_show_minutes=data.get("max_show_minutes", 120),
            buffer_minutes=data.get("buffer_minutes", 15),
            alcohol_revenue_per_head=data.get("alcohol_revenue_per_head", 0),
            concession_revenue_per_head=data.get("concession_revenue_per_head", 5),
            base_ticket_price=data.get("base_ticket_price", 15),
            vip_ticket_price=data.get("vip_ticket_price", 0),
            vip_capacity_pct=data.get("vip_capacity_pct", 0.0),
            events_held=data.get("events_held", 0),
            total_attendance=data.get("total_attendance", 0),
            total_revenue=data.get("total_revenue", 0),
            trust_level=data.get("trust_level", 100),
            is_banned_until_week=data.get("is_banned_until_week", 0),
            is_unlocked=data.get("is_unlocked", True),
            description=data.get("description", ""),
            atmosphere=data.get("atmosphere", "Standard"),
        )
        venue.perks = [VenuePerk(p) for p in data.get("perks", [])]
        venue.restrictions = [VenueRestriction(r) for r in data.get("restrictions", [])]
        venue.day_modifiers = data.get("day_modifiers", {})
        venue.best_days = data.get("best_days", [])
        venue.worst_days = data.get("worst_days", [])
        return venue
