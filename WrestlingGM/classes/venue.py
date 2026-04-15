"""
Venue System - Complete tiered venue progression
From bingo halls to super stadiums
"""

from enum import Enum
from typing import Optional, List, Dict
from dataclasses import dataclass, field
import random


class VenueTier(Enum):
    TIER_1 = 1  # Bingo Halls, Bars, Clubs
    TIER_2 = 2  # Theatres, Gig Venues
    TIER_3 = 3  # Small Arenas
    TIER_4 = 4  # Medium Arenas
    TIER_5 = 5  # Large Arenas
    TIER_6 = 6  # Stadiums
    TIER_7 = 7  # Super Stadiums (Unlockable)


class VenueType(Enum):
    # Tier 1 Types
    BINGO_HALL = "Bingo Hall"
    SPORTS_HALL = "Sports Hall"
    BAR = "Bar/Pub"
    NIGHTCLUB = "Nightclub"
    COMMUNITY_CENTER = "Community Center"
    WAREHOUSE = "Warehouse"
    GYMNASIUM = "Gymnasium"
    FAIRGROUND = "Fairground"
    FLEA_MARKET = "Flea Market"
    
    # Tier 2 Types
    THEATRE = "Theatre"
    BALLROOM = "Ballroom"
    GIG_VENUE = "Gig Venue"
    OUTDOOR_AMPHITHEATER = "Outdoor Amphitheater"
    CONVENTION_HALL = "Convention Hall"
    COLLEGE_GYM = "College Gymnasium"
    ARMORY = "Armory"
    
    # Tier 3 Types
    SMALL_ARENA = "Small Arena"
    CIVIC_CENTER = "Civic Center"
    MINOR_LEAGUE_STADIUM = "Minor League Stadium"
    EXPO_CENTER = "Expo Center"
    
    # Tier 4 Types
    MEDIUM_ARENA = "Medium Arena"
    CONCERT_HALL = "Concert Hall"
    COLISEUM = "Coliseum"
    
    # Tier 5 Types
    LARGE_ARENA = "Large Arena"
    SPORTS_ARENA = "Sports Arena"
    DOME = "Dome"
    
    # Tier 6 Types
    STADIUM = "Stadium"
    FOOTBALL_STADIUM = "Football Stadium"
    BASEBALL_STADIUM = "Baseball Stadium"
    OUTDOOR_STADIUM = "Outdoor Stadium"
    
    # Tier 7 Types
    SUPER_STADIUM = "Super Stadium"
    MEGA_DOME = "Mega Dome"


class VenueAmbiance(Enum):
    INTIMATE = "Intimate"
    GRITTY = "Gritty"
    CLASSIC = "Classic"
    MODERN = "Modern"
    PRESTIGIOUS = "Prestigious"
    LEGENDARY = "Legendary"
    OUTDOOR = "Outdoor"
    UNIQUE = "Unique"


@dataclass
class VenueFeatures:
    """Features and capabilities of a venue"""
    has_locker_rooms: bool = False
    has_backstage_area: bool = False
    has_loading_dock: bool = False
    has_big_screen: bool = False
    has_house_lights: bool = True
    has_advanced_lighting: bool = False
    has_pyro_capability: bool = False
    has_multiple_entrances: bool = False
    has_vip_section: bool = False
    has_parking: bool = False
    has_concessions: bool = False
    has_air_conditioning: bool = False
    has_commentary_position: bool = False
    has_camera_positions: bool = False
    has_rigging_points: bool = False
    is_weatherproof: bool = True
    wheelchair_accessible: bool = False
    alcohol_license: bool = False
    
    def to_dict(self) -> dict:
        return {
            "has_locker_rooms": self.has_locker_rooms,
            "has_backstage_area": self.has_backstage_area,
            "has_loading_dock": self.has_loading_dock,
            "has_big_screen": self.has_big_screen,
            "has_house_lights": self.has_house_lights,
            "has_advanced_lighting": self.has_advanced_lighting,
            "has_pyro_capability": self.has_pyro_capability,
            "has_multiple_entrances": self.has_multiple_entrances,
            "has_vip_section": self.has_vip_section,
            "has_parking": self.has_parking,
            "has_concessions": self.has_concessions,
            "has_air_conditioning": self.has_air_conditioning,
            "has_commentary_position": self.has_commentary_position,
            "has_camera_positions": self.has_camera_positions,
            "has_rigging_points": self.has_rigging_points,
            "is_weatherproof": self.is_weatherproof,
            "wheelchair_accessible": self.wheelchair_accessible,
            "alcohol_license": self.alcohol_license,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "VenueFeatures":
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class Venue:
    """Represents a venue where events can be held"""
    
    # Identity
    id: str
    name: str
    venue_type: VenueType
    tier: VenueTier
    ambiance: VenueAmbiance
    
    # Location
    city: str
    country: str
    continent: str
    address: str = ""
    
    # Capacity
    capacity: int = 100
    seated_capacity: int = 0
    standing_capacity: int = 0
    
    # Costs
    rental_cost: int = 500
    security_cost_per_100: int = 50
    cleaning_deposit: int = 200
    insurance_required: int = 0
    
    # Modifiers
    production_modifier: float = 1.0
    atmosphere_modifier: float = 1.0
    prestige: int = 10
    
    # Features
    features: VenueFeatures = field(default_factory=VenueFeatures)
    
    # Availability
    is_available: bool = True
    is_unlocked: bool = True
    unlock_requirement: str = ""
    booked_dates: List[str] = field(default_factory=list)
    
    # History
    events_held: int = 0
    total_attendance: int = 0
    best_attendance: int = 0
    worst_attendance: int = 0
    total_revenue: int = 0
    memorable_moments: List[str] = field(default_factory=list)
    
    # Special
    description: str = ""
    history: str = ""
    famous_events: List[str] = field(default_factory=list)
    philosophy_bonuses: Dict[str, float] = field(default_factory=dict)
    
    def get_total_capacity(self) -> int:
        if self.seated_capacity and self.standing_capacity:
            return self.seated_capacity + self.standing_capacity
        return self.capacity
    
    def get_rental_cost(self, is_ppv: bool = False, is_tv: bool = False) -> int:
        cost = self.rental_cost
        if is_ppv:
            cost = int(cost * 1.75)
        elif is_tv:
            cost = int(cost * 1.25)
        return cost
    
    def get_total_event_cost(
        self, 
        expected_attendance: int, 
        is_ppv: bool = False, 
        is_tv: bool = False
    ) -> Dict[str, int]:
        rental = self.get_rental_cost(is_ppv, is_tv)
        security = int((expected_attendance / 100) * self.security_cost_per_100)
        deposit = self.cleaning_deposit
        insurance = self.insurance_required
        total = rental + security + deposit + insurance
        
        return {
            "rental": rental,
            "security": security,
            "deposit": deposit,
            "insurance": insurance,
            "total": total,
        }
    
    def get_expected_attendance(
        self, 
        promotion_popularity: int, 
        is_ppv: bool = False,
        card_quality: int = 50
    ) -> int:
        base_fill = promotion_popularity / 100
        quality_modifier = 0.5 + (card_quality / 100)
        ppv_modifier = 1.3 if is_ppv else 1.0
        expected = int(self.capacity * base_fill * quality_modifier * ppv_modifier)
        variance = int(expected * 0.1)
        expected += random.randint(-variance, variance)
        return max(50, min(expected, self.capacity))
    
    def get_ticket_price_range(self) -> Dict[str, int]:
        base_prices = {
            VenueTier.TIER_1: {"min": 5, "standard": 10, "max": 20},
            VenueTier.TIER_2: {"min": 10, "standard": 20, "max": 35},
            VenueTier.TIER_3: {"min": 15, "standard": 30, "max": 50},
            VenueTier.TIER_4: {"min": 25, "standard": 50, "max": 100},
            VenueTier.TIER_5: {"min": 40, "standard": 75, "max": 150},
            VenueTier.TIER_6: {"min": 50, "standard": 100, "max": 250},
            VenueTier.TIER_7: {"min": 75, "standard": 150, "max": 500},
        }
        return base_prices.get(self.tier, {"min": 10, "standard": 20, "max": 50})
    
    def book_date(self, date: str) -> bool:
        if date in self.booked_dates:
            return False
        self.booked_dates.append(date)
        return True
    
    def release_date(self, date: str):
        if date in self.booked_dates:
            self.booked_dates.remove(date)
    
    def record_event(self, attendance: int, revenue: int, memorable_moment: str = ""):
        self.events_held += 1
        self.total_attendance += attendance
        self.total_revenue += revenue
        
        if attendance > self.best_attendance:
            self.best_attendance = attendance
        
        if self.worst_attendance == 0 or attendance < self.worst_attendance:
            self.worst_attendance = attendance
        
        if memorable_moment:
            self.memorable_moments.append(memorable_moment)
    
    @property
    def average_attendance(self) -> float:
        if self.events_held == 0:
            return 0
        return self.total_attendance / self.events_held
    
    @property
    def fill_rate(self) -> float:
        avg = self.average_attendance
        if avg == 0:
            return 0
        return (avg / self.capacity) * 100
    
    def get_tier_name(self) -> str:
        tier_names = {
            VenueTier.TIER_1: "Grassroots",
            VenueTier.TIER_2: "Independent",
            VenueTier.TIER_3: "Regional",
            VenueTier.TIER_4: "National",
            VenueTier.TIER_5: "Major",
            VenueTier.TIER_6: "World Class",
            VenueTier.TIER_7: "Legendary",
        }
        return tier_names.get(self.tier, "Unknown")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "venue_type": self.venue_type.value,
            "tier": self.tier.value,
            "ambiance": self.ambiance.value,
            "city": self.city,
            "country": self.country,
            "continent": self.continent,
            "address": self.address,
            "capacity": self.capacity,
            "seated_capacity": self.seated_capacity,
            "standing_capacity": self.standing_capacity,
            "rental_cost": self.rental_cost,
            "security_cost_per_100": self.security_cost_per_100,
            "cleaning_deposit": self.cleaning_deposit,
            "insurance_required": self.insurance_required,
            "production_modifier": self.production_modifier,
            "atmosphere_modifier": self.atmosphere_modifier,
            "prestige": self.prestige,
            "features": self.features.to_dict(),
            "is_available": self.is_available,
            "is_unlocked": self.is_unlocked,
            "unlock_requirement": self.unlock_requirement,
            "booked_dates": self.booked_dates,
            "events_held": self.events_held,
            "total_attendance": self.total_attendance,
            "best_attendance": self.best_attendance,
            "worst_attendance": self.worst_attendance,
            "total_revenue": self.total_revenue,
            "memorable_moments": self.memorable_moments,
            "description": self.description,
            "history": self.history,
            "famous_events": self.famous_events,
            "philosophy_bonuses": self.philosophy_bonuses,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Venue":
        features_data = data.get("features", {})
        features = VenueFeatures.from_dict(features_data) if features_data else VenueFeatures()
        
        venue = cls(
            id=data["id"],
            name=data["name"],
            venue_type=VenueType(data["venue_type"]),
            tier=VenueTier(data["tier"]),
            ambiance=VenueAmbiance(data.get("ambiance", "Classic")),
            city=data["city"],
            country=data["country"],
            continent=data["continent"],
            address=data.get("address", ""),
            capacity=data.get("capacity", 100),
            seated_capacity=data.get("seated_capacity", 0),
            standing_capacity=data.get("standing_capacity", 0),
            rental_cost=data.get("rental_cost", 500),
            security_cost_per_100=data.get("security_cost_per_100", 50),
            cleaning_deposit=data.get("cleaning_deposit", 200),
            insurance_required=data.get("insurance_required", 0),
            production_modifier=data.get("production_modifier", 1.0),
            atmosphere_modifier=data.get("atmosphere_modifier", 1.0),
            prestige=data.get("prestige", 10),
            features=features,
            is_available=data.get("is_available", True),
            is_unlocked=data.get("is_unlocked", True),
            unlock_requirement=data.get("unlock_requirement", ""),
            booked_dates=data.get("booked_dates", []),
            description=data.get("description", ""),
            history=data.get("history", ""),
            famous_events=data.get("famous_events", []),
            philosophy_bonuses=data.get("philosophy_bonuses", {}),
        )
        
        venue.events_held = data.get("events_held", 0)
        venue.total_attendance = data.get("total_attendance", 0)
        venue.best_attendance = data.get("best_attendance", 0)
        venue.worst_attendance = data.get("worst_attendance", 0)
        venue.total_revenue = data.get("total_revenue", 0)
        venue.memorable_moments = data.get("memorable_moments", [])
        
        return venue
    
    def __repr__(self) -> str:
        return f"Venue({self.name}, {self.venue_type.value}, Cap: {self.capacity})"


# ==================== TIER REQUIREMENTS ====================

TIER_REQUIREMENTS = {
    VenueTier.TIER_1: {
        "min_prestige": 0,
        "min_fans": 0,
        "description": "Starting venues - Anyone can book these",
    },
    VenueTier.TIER_2: {
        "min_prestige": 15,
        "min_fans": 500,
        "description": "Need some reputation to book these",
    },
    VenueTier.TIER_3: {
        "min_prestige": 30,
        "min_fans": 2000,
        "description": "Regional promotion level",
    },
    VenueTier.TIER_4: {
        "min_prestige": 50,
        "min_fans": 5000,
        "description": "Established promotion level",
    },
    VenueTier.TIER_5: {
        "min_prestige": 70,
        "min_fans": 15000,
        "description": "Major promotion level",
    },
    VenueTier.TIER_6: {
        "min_prestige": 85,
        "min_fans": 50000,
        "description": "World-class promotion level",
    },
    VenueTier.TIER_7: {
        "min_prestige": 95,
        "min_fans": 100000,
        "description": "Legendary status required",
    },
}


def can_book_tier(tier: VenueTier, prestige: int, fans: int) -> tuple:
    """Check if promotion can book venues of this tier"""
    requirements = TIER_REQUIREMENTS.get(tier, {})
    
    min_prestige = requirements.get("min_prestige", 0)
    min_fans = requirements.get("min_fans", 0)
    
    if prestige < min_prestige:
        return False, f"Need {min_prestige} prestige (you have {prestige})"
    
    if fans < min_fans:
        return False, f"Need {min_fans:,} fans (you have {fans:,})"
    
    return True, "Requirements met"