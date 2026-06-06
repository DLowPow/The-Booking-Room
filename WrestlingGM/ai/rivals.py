# ai/rivals.py
"""
Rivals — The CPU opponent layer.
Consolidates: rival_promotions.py + rival_scheduler.py

Two systems:
  1. RivalPromotionManager — ongoing CPU promotions (shows, signings, raids, growth)
  2. RivalScheduler        — the scripted "first rival" intro timeline

Both preserved with identical public interfaces.
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==========================================================================
# =========================  RIVAL ENUMS  =================================
# ==========================================================================

class RivalSize(Enum):
    BACKYARD = "Backyard"
    INDIE = "Indie"
    REGIONAL = "Regional"
    NATIONAL = "National"
    MAJOR = "Major"
    GLOBAL = "Global"


class RivalPhilosophy(Enum):
    SPORTS_ENTERTAINMENT = "Sports Entertainment"
    STRONG_STYLE = "Strong Style"
    LUCHA_LIBRE = "Lucha Libre"
    ULTRAVIOLENT = "Ultraviolent"
    HYBRID = "Hybrid"
    OLD_SCHOOL = "Old School"


class RivalStrategy(Enum):
    POACHER = "Talent Poacher"
    DEVELOPER = "Talent Developer"
    SPECTACLE = "Spectacle Booker"
    PURIST = "Wrestling Purist"
    CHAOS = "Chaos Agent"
    BUDGET = "Budget Operation"


class RivalRelationship(Enum):
    FRIENDLY = "Friendly"
    NEUTRAL = "Neutral"
    COMPETITIVE = "Competitive"
    HOSTILE = "Hostile"
    WAR = "At War"


# ==========================================================================
# =========================  DATA POOLS  ==================================
# ==========================================================================

RIVAL_NAME_POOL = {
    RivalSize.BACKYARD: [
        "Garage Wrestling Federation", "Backyard Brawlers United",
        "The Driveway Dynasty", "Suburban Slam", "House Show Heroes",
    ],
    RivalSize.INDIE: [
        "Underground Wrestling Alliance", "Pure Combat Wrestling",
        "Independent Mat Federation", "Bingo Hall Brawlers", "Steel Town Wrestling",
        "Concrete Jungle Combat", "Iron Fist Wrestling", "Shadow Circuit Wrestling",
    ],
    RivalSize.REGIONAL: [
        "Apex Regional Wrestling", "Storm Front Wrestling", "Velocity Pro Wrestling",
        "Phoenix Rising Federation", "Diamond State Wrestling", "Coastal Combat Federation",
    ],
    RivalSize.NATIONAL: [
        "United Wrestling Association", "Continental Championship Wrestling",
        "Pinnacle Wrestling Federation", "All Pro Wrestling Network",
        "Premier Combat Sports", "Apex Wrestling Entertainment",
    ],
    RivalSize.MAJOR: [
        "Global Wrestling Conglomerate", "Empire Pro Wrestling",
        "Dynasty Championship Wrestling", "Titan Wrestling Federation",
        "Legacy Wrestling Network",
    ],
    RivalSize.GLOBAL: [
        "World Wrestling Imperium", "Universal Combat Federation",
        "International Wrestling Alliance", "Apex Global Sports Entertainment",
    ],
}

RIVAL_LOCATIONS = [
    "Tokyo, Japan", "Mexico City, Mexico", "London, England", "Toronto, Canada",
    "Berlin, Germany", "Sydney, Australia", "Los Angeles, USA", "New York, USA",
    "Chicago, USA", "Dallas, USA", "Atlanta, USA", "Philadelphia, USA",
    "Madrid, Spain", "Paris, France", "Rome, Italy", "Manchester, England",
    "Glasgow, Scotland",
]

RIVAL_TIER_STATS = {
    RivalSize.BACKYARD: {
        "budget_range": [500, 3000], "fans_range": [50, 300],
        "prestige_range": [1, 8], "roster_size_range": [4, 8],
        "show_frequency": 0.25, "raid_chance": 0.00,
        "signing_chance": 0.08, "expansion_chance": 0.05,
    },
    RivalSize.INDIE: {
        "budget_range": [3000, 15000], "fans_range": [300, 2000],
        "prestige_range": [8, 25], "roster_size_range": [6, 12],
        "show_frequency": 0.45, "raid_chance": 0.04,
        "signing_chance": 0.12, "expansion_chance": 0.05,
    },
    RivalSize.REGIONAL: {
        "budget_range": [15000, 60000], "fans_range": [2000, 10000],
        "prestige_range": [25, 45], "roster_size_range": [10, 18],
        "show_frequency": 0.65, "raid_chance": 0.08,
        "signing_chance": 0.15, "expansion_chance": 0.04,
    },
    RivalSize.NATIONAL: {
        "budget_range": [60000, 250000], "fans_range": [10000, 50000],
        "prestige_range": [45, 65], "roster_size_range": [15, 25],
        "show_frequency": 0.82, "raid_chance": 0.12,
        "signing_chance": 0.18, "expansion_chance": 0.03,
    },
    RivalSize.MAJOR: {
        "budget_range": [250000, 1000000], "fans_range": [50000, 200000],
        "prestige_range": [65, 85], "roster_size_range": [20, 35],
        "show_frequency": 0.92, "raid_chance": 0.18,
        "signing_chance": 0.22, "expansion_chance": 0.02,
    },
    RivalSize.GLOBAL: {
        "budget_range": [1000000, 10000000], "fans_range": [200000, 2000000],
        "prestige_range": [85, 100], "roster_size_range": [30, 50],
        "show_frequency": 1.0, "raid_chance": 0.24,
        "signing_chance": 0.25, "expansion_chance": 0.01,
    },
}

RIVAL_VENUES_BY_SIZE = {
    RivalSize.BACKYARD: ["Local Park", "Community Garage", "Driveway Setup", "Backyard Stage"],
    RivalSize.INDIE: ["VFW Hall", "Local Bingo Hall", "Bar District Venue", "Community Center"],
    RivalSize.REGIONAL: ["Civic Center", "Convention Hall", "Regional Arena", "Theater District"],
    RivalSize.NATIONAL: ["Sports Arena", "Convention Center", "Music Theater", "Pavilion"],
    RivalSize.MAJOR: ["Major Arena", "Mega Stadium", "Iconic Venue", "Sports Coliseum"],
    RivalSize.GLOBAL: ["Stadium", "Mega Dome", "Iconic Stadium", "Global Arena"],
}


# ==========================================================================
# =========================  RIVAL DATA CLASSES  =========================
# ==========================================================================

@dataclass
class RivalShow:
    week: int
    year: int
    venue: str
    attendance: int
    rating: float
    main_event: str = ""
    notable_match: str = ""
    revenue: int = 0
    profit: int = 0
    fan_change: int = 0
    prestige_change: int = 0
    show_type: str = "Weekly Show"

    def to_dict(self) -> dict:
        return {
            "week": self.week, "year": self.year, "venue": self.venue,
            "attendance": self.attendance, "rating": self.rating,
            "main_event": self.main_event, "notable_match": self.notable_match,
            "revenue": self.revenue, "profit": self.profit,
            "fan_change": self.fan_change, "prestige_change": self.prestige_change,
            "show_type": self.show_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalShow":
        return cls(
            week=data.get("week", 0), year=data.get("year", 1),
            venue=data.get("venue", ""), attendance=data.get("attendance", 0),
            rating=data.get("rating", 0.0), main_event=data.get("main_event", ""),
            notable_match=data.get("notable_match", ""), revenue=data.get("revenue", 0),
            profit=data.get("profit", 0), fan_change=data.get("fan_change", 0),
            prestige_change=data.get("prestige_change", 0),
            show_type=data.get("show_type", "Weekly Show"),
        )


@dataclass
class RivalSigning:
    week: int
    year: int
    wrestler_name: str
    action: str
    from_promotion: str = ""
    success: bool = True
    offer_amount: int = 0
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "week": self.week, "year": self.year,
            "wrestler_name": self.wrestler_name, "action": self.action,
            "from_promotion": self.from_promotion, "success": self.success,
            "offer_amount": self.offer_amount, "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalSigning":
        return cls(
            week=data.get("week", 0), year=data.get("year", 1),
            wrestler_name=data.get("wrestler_name", ""),
            action=data.get("action", "signed"),
            from_promotion=data.get("from_promotion", ""),
            success=data.get("success", True),
            offer_amount=data.get("offer_amount", 0),
            reason=data.get("reason", ""),
        )


@dataclass
class RivalPromotion:
    id: str
    name: str
    size: RivalSize
    philosophy: RivalPhilosophy
    strategy: RivalStrategy
    location: str
    owner_name: str = ""
    founded_year: int = 1
    budget: int = 5000
    fans: int = 500
    prestige: int = 10
    roster: List[str] = field(default_factory=list)
    relationship: RivalRelationship = RivalRelationship.NEUTRAL
    weeks_active: int = 0
    shows_run: int = 0
    show_history: List[RivalShow] = field(default_factory=list)
    signing_history: List[RivalSigning] = field(default_factory=list)
    rivalry_with_player: int = 0
    aggression: int = 50
    ambition: int = 50
    stability: int = 50
    momentum: int = 0
    scandal_heat: int = 0
    notable_champions: Dict[str, str] = field(default_factory=dict)
    color: str = "#6b7280"
    icon: str = "🏟️"
    description: str = ""
    is_active: bool = True

    def get_size_color(self) -> str:
        colors = {
            RivalSize.BACKYARD: "#6b7280", RivalSize.INDIE: "#10b981",
            RivalSize.REGIONAL: "#3b82f6", RivalSize.NATIONAL: "#8b5cf6",
            RivalSize.MAJOR: "#f59e0b", RivalSize.GLOBAL: "#dc2626",
        }
        return colors.get(self.size, "#6b7280")

    def get_relationship_color(self) -> str:
        colors = {
            RivalRelationship.FRIENDLY: "#10b981", RivalRelationship.NEUTRAL: "#6b7280",
            RivalRelationship.COMPETITIVE: "#3b82f6", RivalRelationship.HOSTILE: "#f59e0b",
            RivalRelationship.WAR: "#dc2626",
        }
        return colors.get(self.relationship, "#6b7280")

    def get_threat_level(self, player_prestige: int, player_fans: int) -> str:
        prestige_diff = self.prestige - player_prestige
        fan_diff = self.fans - player_fans
        if prestige_diff > 30 or fan_diff > max(player_fans * 2, 1000):
            return "Major Threat"
        if prestige_diff > 15:
            return "Significant Threat"
        if prestige_diff > 0:
            return "Equal Competition"
        if prestige_diff > -15:
            return "Lesser Competition"
        return "Minor Threat"

    def update_relationship(self):
        if self.rivalry_with_player >= 80:
            self.relationship = RivalRelationship.WAR
        elif self.rivalry_with_player >= 60:
            self.relationship = RivalRelationship.HOSTILE
        elif self.rivalry_with_player >= 35:
            self.relationship = RivalRelationship.COMPETITIVE
        elif self.rivalry_with_player >= 15:
            self.relationship = RivalRelationship.NEUTRAL
        else:
            self.relationship = RivalRelationship.FRIENDLY

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "size": self.size.value,
            "philosophy": self.philosophy.value, "strategy": self.strategy.value,
            "location": self.location, "owner_name": self.owner_name,
            "founded_year": self.founded_year, "budget": self.budget,
            "fans": self.fans, "prestige": self.prestige, "roster": self.roster,
            "relationship": self.relationship.value, "weeks_active": self.weeks_active,
            "shows_run": self.shows_run,
            "show_history": [s.to_dict() for s in self.show_history[-30:]],
            "signing_history": [s.to_dict() for s in self.signing_history[-50:]],
            "rivalry_with_player": self.rivalry_with_player,
            "aggression": self.aggression, "ambition": self.ambition,
            "stability": self.stability, "momentum": self.momentum,
            "scandal_heat": self.scandal_heat, "notable_champions": self.notable_champions,
            "color": self.color, "icon": self.icon, "description": self.description,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalPromotion":
        try:
            size = RivalSize(data.get("size", "Indie"))
        except ValueError:
            size = RivalSize.INDIE
        try:
            philosophy = RivalPhilosophy(data.get("philosophy", "Hybrid"))
        except ValueError:
            philosophy = RivalPhilosophy.HYBRID
        try:
            strategy = RivalStrategy(data.get("strategy", "Wrestling Purist"))
        except ValueError:
            strategy = RivalStrategy.PURIST
        try:
            relationship = RivalRelationship(data.get("relationship", "Neutral"))
        except ValueError:
            relationship = RivalRelationship.NEUTRAL

        rival = cls(
            id=data.get("id", ""), name=data.get("name", ""), size=size,
            philosophy=philosophy, strategy=strategy, location=data.get("location", ""),
            owner_name=data.get("owner_name", ""), founded_year=data.get("founded_year", 1),
            budget=data.get("budget", 5000), fans=data.get("fans", 500),
            prestige=data.get("prestige", 10), roster=data.get("roster", []),
            relationship=relationship, weeks_active=data.get("weeks_active", 0),
            shows_run=data.get("shows_run", 0),
            rivalry_with_player=data.get("rivalry_with_player", 0),
            aggression=data.get("aggression", 50), ambition=data.get("ambition", 50),
            stability=data.get("stability", 50), momentum=data.get("momentum", 0),
            scandal_heat=data.get("scandal_heat", 0),
            notable_champions=data.get("notable_champions", {}),
            color=data.get("color", "#6b7280"), icon=data.get("icon", "🏟️"),
            description=data.get("description", ""), is_active=data.get("is_active", True),
        )
        for item in data.get("show_history", []):
            try:
                rival.show_history.append(RivalShow.from_dict(item))
            except Exception:
                pass
        for item in data.get("signing_history", []):
            try:
                rival.signing_history.append(RivalSigning.from_dict(item))
            except Exception:
                pass
        return rival

# ==========================================================================
# =====================  RIVAL PROMOTION MANAGER  =========================
# ==========================================================================

class RivalPromotionManager:
    """Manages all AI rival promotions: creation, weekly ops, news/social."""

    def __init__(self):
        self.rivals: List[RivalPromotion] = []
        self.next_id: int = 1
        self.weeks_active: int = 0

    # ---- CREATION --------------------------------------------------------
    def create_starter_rivals(self, player_size: RivalSize = RivalSize.BACKYARD):
        rivals_created = []
        size_progression = list(RivalSize)
        player_idx = size_progression.index(player_size)
        for _ in range(random.randint(2, 3)):
            rival = self.generate_rival(player_size)
            if rival:
                self.rivals.append(rival)
                rivals_created.append(rival)
        if player_idx + 1 < len(size_progression):
            for _ in range(random.randint(1, 2)):
                rival = self.generate_rival(size_progression[player_idx + 1])
                if rival:
                    self.rivals.append(rival)
                    rivals_created.append(rival)
        major_size = size_progression[min(player_idx + 3, len(size_progression) - 1)]
        rival = self.generate_rival(major_size, is_major=True)
        if rival:
            self.rivals.append(rival)
            rivals_created.append(rival)
        return rivals_created

    def generate_rival(self, size: RivalSize, is_major: bool = False):
        name_pool = RIVAL_NAME_POOL.get(size, [])
        if not name_pool:
            return None
        used_names = [r.name for r in self.rivals]
        available_names = [n for n in name_pool if n not in used_names] or name_pool
        name = random.choice(available_names)
        stats = RIVAL_TIER_STATS.get(size, RIVAL_TIER_STATS[RivalSize.INDIE])
        rival_id = f"rival_{self.next_id}"
        self.next_id += 1
        rival = RivalPromotion(
            id=rival_id, name=name, size=size,
            philosophy=random.choice(list(RivalPhilosophy)),
            strategy=random.choice(list(RivalStrategy)),
            location=random.choice(RIVAL_LOCATIONS),
            owner_name=self._generate_owner_name(),
            budget=random.randint(*stats["budget_range"]),
            fans=random.randint(*stats["fans_range"]),
            prestige=random.randint(*stats["prestige_range"]),
            roster=self._generate_rival_roster(random.randint(*stats["roster_size_range"])),
            color=self._get_rival_color(size), icon=self._get_rival_icon(size),
            description=self._generate_description(name, size),
        )
        if is_major:
            rival.relationship = RivalRelationship.NEUTRAL
            rival.rivalry_with_player = 10
            rival.aggression = 70
            rival.ambition = 80
            rival.stability = 70
        return rival

    def _generate_owner_name(self):
        first = ["Marcus", "Jasmine", "Kevin", "Sara", "Tony", "Lisa"]
        last = ["Stone", "Sterling", "Cross", "Vega", "Hill", "Black"]
        return f"{random.choice(first)} {random.choice(last)}"

    def _generate_rival_roster(self, size):
        first = ["Axel", "Zane", "Killian", "Jaxon", "Reign", "Kade", "Phoenix",
                 "Storm", "Shadow", "Razor", "Raven", "Luna", "Nova", "Ember",
                 "Skye", "Vixen", "Hex", "Onyx"]
        last = ["Storm", "Vex", "Black", "Cross", "Steele", "Wolfe", "Knight",
                "Sterling", "Reign", "Stone", "Savage", "King"]
        roster, used, attempts = [], set(), 0
        while len(roster) < size and attempts < size * 4:
            name = f"{random.choice(first)} {random.choice(last)}"
            if name not in used:
                roster.append(name)
                used.add(name)
            attempts += 1
        return roster

    def _get_rival_color(self, size):
        return {
            RivalSize.BACKYARD: "#6b7280", RivalSize.INDIE: "#10b981",
            RivalSize.REGIONAL: "#3b82f6", RivalSize.NATIONAL: "#8b5cf6",
            RivalSize.MAJOR: "#f59e0b", RivalSize.GLOBAL: "#dc2626",
        }.get(size, "#6b7280")

    def _get_rival_icon(self, size):
        return {
            RivalSize.BACKYARD: "🏚️", RivalSize.INDIE: "🏟️",
            RivalSize.REGIONAL: "🏛️", RivalSize.NATIONAL: "🏙️",
            RivalSize.MAJOR: "🌆", RivalSize.GLOBAL: "🌍",
        }.get(size, "🏟️")

    def _generate_description(self, name, size):
        return f"{name} — a {size.value.lower()}-level promotion competing for fans."

    # ---- WEEKLY OPERATIONS ----------------------------------------------
    def process_weekly_operations(self, current_week, current_year, player_roster,
                                  player_free_agents, player_prestige, player_fans):
        self.weeks_active += 1
        results = {
            "shows_run": [], "signings": [], "raids": [], "growth_events": [],
            "rival_news": [], "social_posts": [], "fan_reactions": [],
            "writer_room_prompts": [],
        }
        for rival in self.rivals:
            if not rival.is_active:
                continue
            rival.weeks_active += 1
            stats = RIVAL_TIER_STATS.get(rival.size, RIVAL_TIER_STATS[RivalSize.INDIE])

            if random.random() < stats["show_frequency"]:
                show = self._run_rival_show(rival, current_week, current_year)
                if show:
                    results["shows_run"].append({"rival_name": rival.name, "rival_id": rival.id, "show": show.to_dict()})
                    results["rival_news"].append(self._make_show_news(rival, show))
                    results["social_posts"].extend(self._make_show_social(rival, show))
                    results["fan_reactions"].extend(self._make_fan_reactions(rival, show))
                    results["writer_room_prompts"].append(self._make_writer_prompt(rival, show))

            if player_free_agents and random.random() < stats["signing_chance"]:
                signing = self._attempt_free_agent_signing(rival, player_free_agents, current_week, current_year)
                if signing:
                    results["signings"].append({"rival_name": rival.name, "rival_id": rival.id, "signing": signing.to_dict()})
                    results["rival_news"].append(self._make_signing_news(rival, signing))
                    if not signing.success:
                        results["fan_reactions"].append(self._make_failed_signing_reaction(rival, signing))

            if player_roster and random.random() < stats["raid_chance"]:
                raid = self._attempt_roster_raid(rival, player_roster, current_week, current_year)
                if raid:
                    results["raids"].append({"rival_name": rival.name, "rival_id": rival.id, "raid": raid.to_dict()})
                    rival.rivalry_with_player += 15
                    rival.update_relationship()
                    results["rival_news"].append(self._make_raid_news(rival, raid))
                    results["social_posts"].append(self._make_raid_social(rival, raid))

            if player_prestige > rival.prestige:
                rival.rivalry_with_player += 1
            if player_fans > rival.fans:
                rival.rivalry_with_player += 1
            rival.rivalry_with_player = max(0, min(100, rival.rivalry_with_player))
            rival.update_relationship()

            if random.random() < stats["expansion_chance"]:
                growth = self._process_growth_event(rival)
                if growth:
                    results["growth_events"].append({"rival_name": rival.name, "rival_id": rival.id, "event": growth})
                    results["rival_news"].append(self._make_growth_news(rival, growth))
        return results

    # ---- INTERNAL SIM ----------------------------------------------------
    def _run_rival_show(self, rival, week, year):
        if not rival.roster or len(rival.roster) < 4 or rival.budget < 300:
            return None
        venue = random.choice(RIVAL_VENUES_BY_SIZE.get(rival.size, ["Local Venue"]))
        attendance = random.randint(max(30, rival.fans // 10), max(rival.fans // 3, 80))
        rating = max(1.0, min(5.0, 2.5 + (rival.prestige / 55.0) + random.uniform(-0.8, 0.8)))
        main = random.sample(rival.roster, min(2, len(rival.roster)))
        main_event = " vs ".join(main)
        notable = ""
        others = [w for w in rival.roster if w not in main]
        if len(others) >= 2:
            notable = " vs ".join(random.sample(others, 2))
        revenue = int(attendance * random.uniform(8, 25))
        profit = revenue - random.randint(300, 1500)
        fan_change = prestige_change = 0
        if rating >= 4.2:
            fan_change = int(rival.fans * 0.05) + random.randint(50, 200); prestige_change = 2
        elif rating >= 3.5:
            fan_change = int(rival.fans * 0.02) + random.randint(20, 80); prestige_change = 1
        elif rating < 2.0:
            fan_change = -int(rival.fans * 0.02) - random.randint(10, 40); prestige_change = -1
        show = RivalShow(week=week, year=year, venue=venue, attendance=attendance,
                         rating=rating, main_event=main_event, notable_match=notable,
                         revenue=revenue, profit=profit, fan_change=fan_change,
                         prestige_change=prestige_change)
        rival.show_history.append(show)
        rival.shows_run += 1
        rival.budget += profit
        rival.fans = max(50, rival.fans + fan_change)
        rival.prestige = max(0, min(100, rival.prestige + prestige_change))
        rival.momentum = int((rival.momentum + prestige_change) * 0.9)
        return show

    def _attempt_free_agent_signing(self, rival, free_agents, week, year):
        if not free_agents or rival.budget < 1000:
            return None
        suitable = [w for w in free_agents if w.get("popularity", 30) <= rival.prestige + 15]
        if not suitable:
            return None
        chosen = random.choice(suitable)
        cost = random.randint(500, 2500)
        success = random.random() < (0.6 + ((rival.prestige - chosen.get("popularity", 30)) / 200))
        reason = "" if success else random.choice(["offered lower wages", "incompatible style",
                                                   "better offer elsewhere", "personal preference"])
        signing = RivalSigning(week=week, year=year, wrestler_name=chosen.get("name", "Unknown Wrestler"),
                               action="signed", from_promotion="Free Agent Market",
                               success=success, offer_amount=cost, reason=reason)
        rival.signing_history.append(signing)
        if success:
            rival.roster.append(signing.wrestler_name)
            rival.budget -= cost
        return signing

    def _attempt_roster_raid(self, rival, player_roster, week, year):
        if not player_roster or rival.budget < 5000 or rival.size == RivalSize.BACKYARD:
            return None
        targetable = [w for w in player_roster if w.get("morale", 75) < 60 or w.get("loyalty", 75) < 60]
        if not targetable:
            return None
        chosen = random.choice(targetable)
        raid_success = random.random() < (0.25 + ((100 - chosen.get("loyalty", 50)) / 200))
        raid = RivalSigning(week=week, year=year, wrestler_name=chosen.get("name", "Player Wrestler"),
                            action="raided", from_promotion="Player Promotion",
                            success=raid_success, offer_amount=random.randint(3000, 12000))
        if raid_success:
            rival.roster.append(raid.wrestler_name)
            rival.budget -= raid.offer_amount
        rival.signing_history.append(raid)
        return raid

    def _process_growth_event(self, rival):
        if rival.prestige >= 90 and rival.size != RivalSize.GLOBAL:
            sizes = list(RivalSize)
            idx = sizes.index(rival.size)
            if idx + 1 < len(sizes):
                old = rival.size
                rival.size = sizes[idx + 1]
                rival.budget = max(rival.budget, RIVAL_TIER_STATS[rival.size]["budget_range"][0])
                return {"type": "promotion",
                        "description": f"{rival.name} has been promoted to {rival.size.value} tier!",
                        "old_size": old.value, "new_size": rival.size.value}
        if rival.show_history and len(rival.show_history) >= 5:
            avg = sum(s.rating for s in rival.show_history[-5:]) / 5
            if avg < 2.0:
                rival.prestige = max(0, rival.prestige - 2)
                rival.fans = max(50, int(rival.fans * 0.96))
                rival.momentum -= 2
                return {"type": "decline", "description": f"{rival.name} is losing popularity due to poor shows."}
        return None

    # ---- NEWS & SOCIAL HELPERS ------------------------------------------
    def _make_show_news(self, rival, show):
        star = f"{show.rating:.1f}★"
        headline = f"{rival.name} draws {show.attendance} fans for {star} show"
        if show.rating >= 4.2:
            body = f"{rival.name} delivered a standout show at {show.venue}, drawing {show.attendance} fans and earning a {star} rating."
        elif show.rating >= 3.5:
            body = f"{rival.name} ran a solid event with a {star} rating and {show.attendance} fans."
        elif show.rating < 2.0:
            body = f"{rival.name}'s latest event stumbled with a {star} rating."
        else:
            body = f"{rival.name} held a routine show with {show.attendance} fans and a {star} rating."
        return {"headline": headline, "body": body, "type": "show_recap"}

    def _make_signing_news(self, rival, signing):
        w = signing.wrestler_name
        if signing.success:
            return {"headline": f"{w} joins {rival.name}",
                    "body": f"{rival.name} has signed free agent {w}.", "type": "signing"}
        return {"headline": f"{rival.name} fails to sign {w}",
                "body": f"{rival.name} attempted to sign {w} but the deal fell through due to {signing.reason}.", "type": "signing"}

    def _make_raid_news(self, rival, raid):
        w = raid.wrestler_name
        if raid.success:
            return {"headline": f"{rival.name} poaches {w} from player",
                    "body": f"{rival.name} successfully raided and signed {w} away from your promotion.", "type": "raid"}
        return {"headline": f"{rival.name} fails to poach {w}",
                "body": f"{rival.name} tried to poach {w}, but the offer was declined.", "type": "raid"}

    def _make_growth_news(self, rival, growth):
        if growth["type"] == "promotion":
            return {"headline": f"{rival.name} moves up to {growth['new_size']}!", "body": growth["description"], "type": "growth"}
        return {"headline": f"{rival.name} on the decline", "body": growth["description"], "type": "growth"}

    def _make_show_social(self, rival, show):
        posts = []
        if show.rating >= 4.2:
            posts.append({"author": "FanCommunity", "content": f"{rival.name} absolutely killed it! {show.main_event} stole the show! ⭐⭐⭐⭐"})
        elif show.rating >= 3.5:
            posts.append({"author": "FanCommunity", "content": f"Good vibes from {rival.name}'s latest event."})
        elif show.rating < 2.0:
            posts.append({"author": "FanCommunity", "content": f"Ouch! {rival.name}'s show was a flop. 🤔"})
        posts.append({"author": "NewsBot", "content": f"Did you catch {rival.name}'s event? {show.rating:.1f}★ with {show.attendance} fans."})
        return posts

    def _make_fan_reactions(self, rival, show):
        if show.rating >= 4.2:
            return [{"sentiment": "positive", "comment": "Amazing matches! Can't wait for the next show."}]
        if show.rating >= 3.5:
            return [{"sentiment": "positive", "comment": "Solid show, but room to get even better."}]
        if show.rating < 2.0:
            return [{"sentiment": "negative", "comment": "Terrible show, hope they change things fast!"}]
        return []

    def _make_failed_signing_reaction(self, rival, signing):
        return {"sentiment": "negative", "comment": f"Rumor has it {signing.wrestler_name} turned down {rival.name}."}

    def _make_raid_social(self, rival, raid):
        if raid.success:
            return {"author": "Insider", "content": f"{rival.name} just poached {raid.wrestler_name} from the player! 🔥"}
        return {"author": "Insider", "content": f"{rival.name} tried to steal {raid.wrestler_name}, but it failed."}

    def _make_writer_prompt(self, rival, show):
        return {"prompt_type": "rival_update", "rival_id": rival.id, "rival_name": rival.name,
                "summary": f"{rival.name} ran a {show.rating:.1f}★ show at {show.venue}, gaining {show.fan_change} fans."}

    # ---- UTILITY ---------------------------------------------------------
    def get_all_rivals(self):
        return [r for r in self.rivals if r.is_active]

    def get_rival(self, rival_id):
        return next((r for r in self.rivals if r.id == rival_id), None)

    def get_rivals_by_size(self, size):
        return [r for r in self.get_all_rivals() if r.size == size]

    def get_top_rival(self):
        active = self.get_all_rivals()
        return max(active, key=lambda r: r.prestige) if active else None

    def get_biggest_threat(self, player_prestige, player_fans):
        active = self.get_all_rivals()
        if not active:
            return None
        threats = [r for r in active if r.prestige >= player_prestige - 5 and r.fans >= player_fans / 2] or active
        return max(threats, key=lambda r: r.rivalry_with_player + r.prestige)

    def get_hostile_rivals(self):
        return [r for r in self.get_all_rivals()
                if r.relationship in (RivalRelationship.HOSTILE, RivalRelationship.WAR)]

    def get_industry_summary(self, player_prestige, player_fans):
        active = self.get_all_rivals()
        if not active:
            return {"total_rivals": 0, "industry_leader": "Player", "player_rank": 1, "hostile_count": 0}
        all_promotions = active + [{"name": "Player", "prestige": player_prestige, "fans": player_fans}]
        leader = max(all_promotions, key=lambda p: p.prestige if hasattr(p, "prestige") else p["prestige"])
        leader_name = leader.name if hasattr(leader, "name") else leader["name"]
        sorted_p = sorted(all_promotions, key=lambda p: p.prestige if hasattr(p, "prestige") else p["prestige"], reverse=True)
        player_rank = next((i + 1 for i, p in enumerate(sorted_p)
                            if (hasattr(p, "name") and p.name == "Player") or (isinstance(p, dict) and p["name"] == "Player")),
                           len(sorted_p))
        return {"total_rivals": len(active), "industry_leader": leader_name,
                "is_player_leader": leader_name == "Player", "player_rank": player_rank,
                "total_promotions": len(all_promotions), "hostile_count": len(self.get_hostile_rivals())}

    # ---- SERIALIZATION ---------------------------------------------------
    def to_dict(self):
        return {"rivals": [r.to_dict() for r in self.rivals],
                "next_id": self.next_id, "weeks_active": self.weeks_active}

    @classmethod
    def from_dict(cls, data):
        manager = cls()
        manager.next_id = data.get("next_id", 1)
        manager.weeks_active = data.get("weeks_active", 0)
        for entry in data.get("rivals", []):
            try:
                manager.rivals.append(RivalPromotion.from_dict(entry))
            except Exception:
                pass
        return manager


# ==========================================================================
# ========================  RIVAL SCHEDULER  ==============================
# The scripted "first rival" intro timeline.
# ==========================================================================

RIVAL_INTRO_MESSAGES = {
    1: {"sender": "Unknown Promoter", "subject": "Finally...",
        "body": "Oooh, there's a new show in town. Finally, some competition.", "icon": "👁️"},
    2: {"sender": "Unknown Promoter", "subject": "A Word Of Advice",
        "body": "Hey. Stop running shows the same day as mine. There are only so many fans in this town.", "icon": "⚠️"},
    3: {"sender": "Unknown Promoter", "subject": "Fine.",
        "body": "You want the spotlight that badly? Fine. I'll take the weekend after and let the fans compare us properly.", "icon": "🎭"},
}

RIVAL_PROMO_NAMES = [
    "Underground Wrestling Alliance", "Steel Town Wrestling", "Shadow Circuit Wrestling",
    "Iron Fist Wrestling", "Concrete Jungle Combat",
]

RIVAL_VENUES = [
    "Local Bingo Hall", "Community Center", "VFW Hall",
    "Old Sports Club", "Warehouse Arena", "Downtown Rec Hall",
]


@dataclass
class ScheduledRivalShow:
    show_id: str
    rival_name: str
    day: int
    month: int
    year: int
    venue: str
    reason: str = ""
    completed: bool = False
    attendance: int = 0
    rating: float = 0.0
    fan_reaction: str = ""

    def to_dict(self):
        return {
            "show_id": self.show_id, "rival_name": self.rival_name,
            "day": self.day, "month": self.month, "year": self.year,
            "venue": self.venue, "reason": self.reason, "completed": self.completed,
            "attendance": self.attendance, "rating": self.rating,
            "fan_reaction": self.fan_reaction,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            show_id=data.get("show_id", ""), rival_name=data.get("rival_name", "Unknown Rival"),
            day=data.get("day", 1), month=data.get("month", 1), year=data.get("year", 1),
            venue=data.get("venue", "Local Venue"), reason=data.get("reason", ""),
            completed=data.get("completed", False), attendance=data.get("attendance", 0),
            rating=data.get("rating", 0.0), fan_reaction=data.get("fan_reaction", ""),
        )


class RivalScheduler:
    """Controls the visible scripted rival timeline (first 3 shows, then dynamic)."""

    def __init__(self):
        self.active = True
        self.rival_name = random.choice(RIVAL_PROMO_NAMES)
        self.rival_identity_revealed = False
        self.player_completed_shows = 0
        self.intro_stage = 0
        self.scheduled_shows: List[ScheduledRivalShow] = []
        self.completed_shows: List[ScheduledRivalShow] = []
        self.next_rival_show_day = None
        self.next_rival_show_month = None
        self.next_rival_show_year = None
        self.next_rival_show_venue = None
        self.last_player_show_day = None
        self.last_player_show_month = None
        self.last_player_show_year = None

    # ---- PUBLIC API ------------------------------------------------------
    def on_player_show_completed(self, game_state, show_result=None):
        promotion = getattr(game_state, "promotion", None)
        if not promotion:
            return {"created": False, "reason": "No promotion"}
        self.player_completed_shows += 1
        day = getattr(promotion, "current_day", 1)
        month = getattr(promotion, "current_month", 1)
        year = getattr(promotion, "current_year", 1)
        self.last_player_show_day = day
        self.last_player_show_month = month
        self.last_player_show_year = year
        created_show = None
        message = None
        if self.player_completed_shows == 1:
            created_show = self.schedule_rival_show(day, month, year, reason="intro_same_day_show_1")
            created_show.completed = True
            self._simulate_rival_show_result(created_show)
            message = self._send_intro_message(game_state, 1)
        elif self.player_completed_shows == 2:
            created_show = self.schedule_rival_show(day, month, year, reason="intro_same_day_show_2")
            created_show.completed = True
            self._simulate_rival_show_result(created_show)
            message = self._send_intro_message(game_state, 2)
        elif self.player_completed_shows == 3:
            future = self._add_days(day, month, year, 2)
            created_show = self.schedule_rival_show(future["day"], future["month"], future["year"],
                                                    reason="intro_two_days_after_show_3")
            message = self._send_intro_message(game_state, 3)
            self.plan_next_regular_rival_show(future["day"], future["month"], future["year"])
        else:
            self._react_to_player_show_date(game_state, day, month, year)
            if not self.has_upcoming_show_after(day, month, year):
                self.plan_next_regular_rival_show(day, month, year)
        return {"created": created_show is not None,
                "rival_show": created_show.to_dict() if created_show else None,
                "message_sent": message is not None,
                "player_completed_shows": self.player_completed_shows}

    def get_calendar_events(self):
        events = []
        for show in self.scheduled_shows + self.completed_shows:
            events.append({
                "type": "rival_show", "title": show.rival_name,
                "day": show.day, "month": show.month, "year": show.year,
                "venue": show.venue, "completed": show.completed,
                "rating": show.rating, "attendance": show.attendance,
                "reason": show.reason, "color": "#ef4444", "icon": "⚔️",
            })
        return events

    def get_next_rival_show_preview(self):
        upcoming = self.get_upcoming_shows()
        if not upcoming:
            return None
        show = upcoming[0]
        return {
            "rival_name": show.rival_name, "day": show.day,
            "month": show.month, "year": show.year, "venue": show.venue,
            "message": (f"{show.rival_name} is currently planning a show at "
                        f"{show.venue} on {show.day}/{show.month}/Y{show.year}."),
        }

    def get_upcoming_shows(self):
        return [s for s in self.scheduled_shows if not s.completed]

    def complete_due_rival_shows(self, game_state):
        promotion = getattr(game_state, "promotion", None)
        if not promotion:
            return []
        cd = getattr(promotion, "current_day", 1)
        cm = getattr(promotion, "current_month", 1)
        cy = getattr(promotion, "current_year", 1)
        completed_now = []
        for show in self.scheduled_shows[:]:
            if self._date_lte(show.day, show.month, show.year, cd, cm, cy):
                show.completed = True
                self._simulate_rival_show_result(show)
                self.scheduled_shows.remove(show)
                self.completed_shows.append(show)
                completed_now.append(show.to_dict())
                self.plan_next_regular_rival_show(show.day, show.month, show.year)
        return completed_now

    # ---- SCHEDULING ------------------------------------------------------
    def schedule_rival_show(self, day, month, year, reason=""):
        show = ScheduledRivalShow(
            show_id=f"rival_show_{year}_{month}_{day}_{len(self.scheduled_shows) + len(self.completed_shows) + 1}",
            rival_name=self.rival_name, day=day, month=month, year=year,
            venue=random.choice(RIVAL_VENUES), reason=reason,
        )
        if show.completed:
            self.completed_shows.append(show)
        else:
            self.scheduled_shows.append(show)
        return show

    def plan_next_regular_rival_show(self, start_day, start_month, start_year):
        date = self._add_days(start_day, start_month, start_year, random.randint(21, 42))
        show = self.schedule_rival_show(date["day"], date["month"], date["year"], reason="regular_cpu_show")
        self.next_rival_show_day = show.day
        self.next_rival_show_month = show.month
        self.next_rival_show_year = show.year
        self.next_rival_show_venue = show.venue
        return show

    def has_upcoming_show_after(self, day, month, year):
        for show in self.get_upcoming_shows():
            if not self._date_lte(show.day, show.month, show.year, day, month, year):
                return True
        return False

    # ---- REACTIONS -------------------------------------------------------
    def _react_to_player_show_date(self, game_state, day, month, year):
        upcoming = self.get_upcoming_shows()
        if not upcoming:
            return
        ns = upcoming[0]
        if ns.day == day and ns.month == month and ns.year == year:
            self._send_custom_message(
                game_state,
                sender=self.rival_name if self.rival_identity_revealed else "Unknown Promoter",
                subject="You're Doing This Again?",
                body="Same day again? Fine. If you want a fight for the fans, I'll give you one.",
                icon="⚔️")

    def _send_intro_message(self, game_state, stage):
        data = RIVAL_INTRO_MESSAGES.get(stage)
        if not data:
            return None
        self.intro_stage = max(self.intro_stage, stage)
        return self._send_custom_message(game_state, data["sender"], data["subject"], data["body"], data["icon"])

    def _send_custom_message(self, game_state, sender, subject, body, icon="📨"):
        inbox = getattr(game_state, "inbox", None)
        promotion = getattr(game_state, "promotion", None)
        if not inbox or not promotion:
            return None
        try:
            inbox.add_message(sender=sender, subject=subject, body=body,
                              year=getattr(promotion, "current_year", 1),
                              month=getattr(promotion, "current_month", 1),
                              day=getattr(promotion, "current_day", 1),
                              message_type="rival", icon=icon)
            return True
        except TypeError:
            try:
                inbox.add_message(sender, subject, body)
                return True
            except Exception:
                return None
        except Exception:
            return None

    # ---- RESULT SIM ------------------------------------------------------
    def _simulate_rival_show_result(self, show):
        show.attendance = random.randint(80, 450)
        base = random.uniform(1.8, 3.6)
        if show.reason == "intro_same_day_show_1": base += 0.1
        elif show.reason == "intro_same_day_show_2": base += 0.2
        elif show.reason == "intro_two_days_after_show_3": base += 0.3
        show.rating = round(max(1.0, min(5.0, base)), 1)
        if show.rating >= 3.5:
            show.fan_reaction = "Fans are starting to notice them."
        elif show.rating <= 2.0:
            show.fan_reaction = "Fans were not impressed."
        else:
            show.fan_reaction = "The show created mild local buzz."

    # ---- DATE HELPERS ----------------------------------------------------
    def _add_days(self, day, month, year, days_to_add):
        day += days_to_add
        while day > 28:
            day -= 28
            month += 1
            if month > 12:
                month = 1
                year += 1
        return {"day": day, "month": month, "year": year}

    def _date_lte(self, da, ma, ya, db, mb, yb):
        if ya != yb: return ya < yb
        if ma != mb: return ma < mb
        return da <= db

    # ---- SERIALIZATION ---------------------------------------------------
    def to_dict(self):
        return {
            "active": self.active, "rival_name": self.rival_name,
            "rival_identity_revealed": self.rival_identity_revealed,
            "player_completed_shows": self.player_completed_shows,
            "intro_stage": self.intro_stage,
            "scheduled_shows": [s.to_dict() for s in self.scheduled_shows],
            "completed_shows": [s.to_dict() for s in self.completed_shows[-50:]],
            "next_rival_show_day": self.next_rival_show_day,
            "next_rival_show_month": self.next_rival_show_month,
            "next_rival_show_year": self.next_rival_show_year,
            "next_rival_show_venue": self.next_rival_show_venue,
            "last_player_show_day": self.last_player_show_day,
            "last_player_show_month": self.last_player_show_month,
            "last_player_show_year": self.last_player_show_year,
        }

    @classmethod
    def from_dict(cls, data):
        sch = cls()
        sch.active = data.get("active", True)
        sch.rival_name = data.get("rival_name", sch.rival_name)
        sch.rival_identity_revealed = data.get("rival_identity_revealed", False)
        sch.player_completed_shows = data.get("player_completed_shows", 0)
        sch.intro_stage = data.get("intro_stage", 0)
        sch.scheduled_shows = [ScheduledRivalShow.from_dict(i) for i in data.get("scheduled_shows", [])]
        sch.completed_shows = [ScheduledRivalShow.from_dict(i) for i in data.get("completed_shows", [])]
        sch.next_rival_show_day = data.get("next_rival_show_day")
        sch.next_rival_show_month = data.get("next_rival_show_month")
        sch.next_rival_show_year = data.get("next_rival_show_year")
        sch.next_rival_show_venue = data.get("next_rival_show_venue")
        sch.last_player_show_day = data.get("last_player_show_day")
        sch.last_player_show_month = data.get("last_player_show_month")
        sch.last_player_show_year = data.get("last_player_show_year")
        return sch