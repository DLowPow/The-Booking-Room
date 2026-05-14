"""
AI Rival Promotions - CPU opponent layer for The Booking Room.

This system controls rival wrestling companies. It is designed to feel alive
without creating fake noise every week.

Rivals can:
- Run shows
- Gain or lose fans
- Sign free agents
- Attempt to poach player talent
- Grow, decline, or become hostile
- Generate news-ready stories
- Generate social-feed-ready reactions
- Generate future Writers Room prompts

Future hooks included:
- rival_news
- social_posts
- fan_reactions
- writer_room_prompts
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==================== RIVAL TYPES ====================

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


# ==================== DATA POOLS ====================

RIVAL_NAME_POOL = {
    RivalSize.BACKYARD: [
        "Garage Wrestling Federation",
        "Backyard Brawlers United",
        "The Driveway Dynasty",
        "Suburban Slam",
        "House Show Heroes",
    ],
    RivalSize.INDIE: [
        "Underground Wrestling Alliance",
        "Pure Combat Wrestling",
        "Independent Mat Federation",
        "Bingo Hall Brawlers",
        "Steel Town Wrestling",
        "Concrete Jungle Combat",
        "Iron Fist Wrestling",
        "Shadow Circuit Wrestling",
    ],
    RivalSize.REGIONAL: [
        "Apex Regional Wrestling",
        "Storm Front Wrestling",
        "Velocity Pro Wrestling",
        "Phoenix Rising Federation",
        "Diamond State Wrestling",
        "Coastal Combat Federation",
    ],
    RivalSize.NATIONAL: [
        "United Wrestling Association",
        "Continental Championship Wrestling",
        "Pinnacle Wrestling Federation",
        "All Pro Wrestling Network",
        "Premier Combat Sports",
        "Apex Wrestling Entertainment",
    ],
    RivalSize.MAJOR: [
        "Global Wrestling Conglomerate",
        "Empire Pro Wrestling",
        "Dynasty Championship Wrestling",
        "Titan Wrestling Federation",
        "Legacy Wrestling Network",
    ],
    RivalSize.GLOBAL: [
        "World Wrestling Imperium",
        "Universal Combat Federation",
        "International Wrestling Alliance",
        "Apex Global Sports Entertainment",
    ],
}

RIVAL_LOCATIONS = [
    "Tokyo, Japan",
    "Mexico City, Mexico",
    "London, England",
    "Toronto, Canada",
    "Berlin, Germany",
    "Sydney, Australia",
    "Los Angeles, USA",
    "New York, USA",
    "Chicago, USA",
    "Dallas, USA",
    "Atlanta, USA",
    "Philadelphia, USA",
    "Madrid, Spain",
    "Paris, France",
    "Rome, Italy",
    "Manchester, England",
    "Glasgow, Scotland",
]

RIVAL_TIER_STATS = {
    RivalSize.BACKYARD: {
        "budget_range": [500, 3000],
        "fans_range": [50, 300],
        "prestige_range": [1, 8],
        "roster_size_range": [4, 8],
        "show_frequency": 0.25,
        "raid_chance": 0.00,
        "signing_chance": 0.08,
        "expansion_chance": 0.05,
    },
    RivalSize.INDIE: {
        "budget_range": [3000, 15000],
        "fans_range": [300, 2000],
        "prestige_range": [8, 25],
        "roster_size_range": [6, 12],
        "show_frequency": 0.45,
        "raid_chance": 0.04,
        "signing_chance": 0.12,
        "expansion_chance": 0.05,
    },
    RivalSize.REGIONAL: {
        "budget_range": [15000, 60000],
        "fans_range": [2000, 10000],
        "prestige_range": [25, 45],
        "roster_size_range": [10, 18],
        "show_frequency": 0.65,
        "raid_chance": 0.08,
        "signing_chance": 0.15,
        "expansion_chance": 0.04,
    },
    RivalSize.NATIONAL: {
        "budget_range": [60000, 250000],
        "fans_range": [10000, 50000],
        "prestige_range": [45, 65],
        "roster_size_range": [15, 25],
        "show_frequency": 0.82,
        "raid_chance": 0.12,
        "signing_chance": 0.18,
        "expansion_chance": 0.03,
    },
    RivalSize.MAJOR: {
        "budget_range": [250000, 1000000],
        "fans_range": [50000, 200000],
        "prestige_range": [65, 85],
        "roster_size_range": [20, 35],
        "show_frequency": 0.92,
        "raid_chance": 0.18,
        "signing_chance": 0.22,
        "expansion_chance": 0.02,
    },
    RivalSize.GLOBAL: {
        "budget_range": [1000000, 10000000],
        "fans_range": [200000, 2000000],
        "prestige_range": [85, 100],
        "roster_size_range": [30, 50],
        "show_frequency": 1.0,
        "raid_chance": 0.24,
        "signing_chance": 0.25,
        "expansion_chance": 0.01,
    },
}

RIVAL_VENUES_BY_SIZE = {
    RivalSize.BACKYARD: [
        "Local Park",
        "Community Garage",
        "Driveway Setup",
        "Backyard Stage",
    ],
    RivalSize.INDIE: [
        "VFW Hall",
        "Local Bingo Hall",
        "Bar District Venue",
        "Community Center",
    ],
    RivalSize.REGIONAL: [
        "Civic Center",
        "Convention Hall",
        "Regional Arena",
        "Theater District",
    ],
    RivalSize.NATIONAL: [
        "Sports Arena",
        "Convention Center",
        "Music Theater",
        "Pavilion",
    ],
    RivalSize.MAJOR: [
        "Major Arena",
        "Mega Stadium",
        "Iconic Venue",
        "Sports Coliseum",
    ],
    RivalSize.GLOBAL: [
        "Stadium",
        "Mega Dome",
        "Iconic Stadium",
        "Global Arena",
    ],
}


# ==================== DATA CLASSES ====================

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
            "week": self.week,
            "year": self.year,
            "venue": self.venue,
            "attendance": self.attendance,
            "rating": self.rating,
            "main_event": self.main_event,
            "notable_match": self.notable_match,
            "revenue": self.revenue,
            "profit": self.profit,
            "fan_change": self.fan_change,
            "prestige_change": self.prestige_change,
            "show_type": self.show_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalShow":
        return cls(
            week=data.get("week", 0),
            year=data.get("year", 1),
            venue=data.get("venue", ""),
            attendance=data.get("attendance", 0),
            rating=data.get("rating", 0.0),
            main_event=data.get("main_event", ""),
            notable_match=data.get("notable_match", ""),
            revenue=data.get("revenue", 0),
            profit=data.get("profit", 0),
            fan_change=data.get("fan_change", 0),
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
            "week": self.week,
            "year": self.year,
            "wrestler_name": self.wrestler_name,
            "action": self.action,
            "from_promotion": self.from_promotion,
            "success": self.success,
            "offer_amount": self.offer_amount,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalSigning":
        return cls(
            week=data.get("week", 0),
            year=data.get("year", 1),
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
            RivalSize.BACKYARD: "#6b7280",
            RivalSize.INDIE: "#10b981",
            RivalSize.REGIONAL: "#3b82f6",
            RivalSize.NATIONAL: "#8b5cf6",
            RivalSize.MAJOR: "#f59e0b",
            RivalSize.GLOBAL: "#dc2626",
        }
        return colors.get(self.size, "#6b7280")

    def get_relationship_color(self) -> str:
        colors = {
            RivalRelationship.FRIENDLY: "#10b981",
            RivalRelationship.NEUTRAL: "#6b7280",
            RivalRelationship.COMPETITIVE: "#3b82f6",
            RivalRelationship.HOSTILE: "#f59e0b",
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
            "id": self.id,
            "name": self.name,
            "size": self.size.value,
            "philosophy": self.philosophy.value,
            "strategy": self.strategy.value,
            "location": self.location,
            "owner_name": self.owner_name,
            "founded_year": self.founded_year,
            "budget": self.budget,
            "fans": self.fans,
            "prestige": self.prestige,
            "roster": self.roster,
            "relationship": self.relationship.value,
            "weeks_active": self.weeks_active,
            "shows_run": self.shows_run,
            "show_history": [s.to_dict() for s in self.show_history[-30:]],
            "signing_history": [s.to_dict() for s in self.signing_history[-50:]],
            "rivalry_with_player": self.rivalry_with_player,
            "aggression": self.aggression,
            "ambition": self.ambition,
            "stability": self.stability,
            "momentum": self.momentum,
            "scandal_heat": self.scandal_heat,
            "notable_champions": self.notable_champions,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
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
            id=data.get("id", ""),
            name=data.get("name", ""),
            size=size,
            philosophy=philosophy,
            strategy=strategy,
            location=data.get("location", ""),
            owner_name=data.get("owner_name", ""),
            founded_year=data.get("founded_year", 1),
            budget=data.get("budget", 5000),
            fans=data.get("fans", 500),
            prestige=data.get("prestige", 10),
            roster=data.get("roster", []),
            relationship=relationship,
            weeks_active=data.get("weeks_active", 0),
            shows_run=data.get("shows_run", 0),
            rivalry_with_player=data.get("rivalry_with_player", 0),
            aggression=data.get("aggression", 50),
            ambition=data.get("ambition", 50),
            stability=data.get("stability", 50),
            momentum=data.get("momentum", 0),
            scandal_heat=data.get("scandal_heat", 0),
            notable_champions=data.get("notable_champions", {}),
            color=data.get("color", "#6b7280"),
            icon=data.get("icon", "🏟️"),
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
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

    # ==================== RIVAL PROMOTION MANAGER ====================

class RivalPromotionManager:
    """
    Manages all AI rival promotions in the game world.
    Generates new rivals, runs their weekly operations, processes signings/raids,
    and produces news and social feedback when things actually happen.
    """

    def __init__(self):
        self.rivals: List[RivalPromotion] = []
        self.next_id: int = 1
        self.weeks_active: int = 0

    # ==================== RIVAL CREATION ====================

    def create_starter_rivals(
        self, player_size: RivalSize = RivalSize.BACKYARD
    ) -> List[RivalPromotion]:
        """Create an initial set of rivals near the player's starting size."""
        rivals_created: List[RivalPromotion] = []

        size_progression = list(RivalSize)
        player_idx = size_progression.index(player_size)

        # A few rivals at player's level
        for _ in range(random.randint(2, 3)):
            rival = self.generate_rival(player_size)
            if rival:
                self.rivals.append(rival)
                rivals_created.append(rival)

        # One or two rivals one tier above (if available)
        if player_idx + 1 < len(size_progression):
            for _ in range(random.randint(1, 2)):
                rival = self.generate_rival(size_progression[player_idx + 1])
                if rival:
                    self.rivals.append(rival)
                    rivals_created.append(rival)

        # One major rival several tiers above (big industry leader)
        major_size = size_progression[min(player_idx + 3, len(size_progression) - 1)]
        rival = self.generate_rival(major_size, is_major=True)
        if rival:
            self.rivals.append(rival)
            rivals_created.append(rival)

        return rivals_created

    def generate_rival(
        self, size: RivalSize, is_major: bool = False
    ) -> Optional[RivalPromotion]:
        """Generate a single rival promotion using random attributes."""
        name_pool = RIVAL_NAME_POOL.get(size, [])
        if not name_pool:
            return None

        # Avoid reusing names
        used_names = [r.name for r in self.rivals]
        available_names = [n for n in name_pool if n not in used_names]
        if not available_names:
            available_names = name_pool

        name = random.choice(available_names)
        location = random.choice(RIVAL_LOCATIONS)
        philosophy = random.choice(list(RivalPhilosophy))
        strategy = random.choice(list(RivalStrategy))
        stats = RIVAL_TIER_STATS.get(size, RIVAL_TIER_STATS[RivalSize.INDIE])
        budget = random.randint(*stats["budget_range"])
        fans = random.randint(*stats["fans_range"])
        prestige = random.randint(*stats["prestige_range"])
        roster_size = random.randint(*stats["roster_size_range"])
        roster = self._generate_rival_roster(roster_size)
        owner = self._generate_owner_name()

        rival_id = f"rival_{self.next_id}"
        self.next_id += 1

        rival = RivalPromotion(
            id=rival_id,
            name=name,
            size=size,
            philosophy=philosophy,
            strategy=strategy,
            location=location,
            owner_name=owner,
            budget=budget,
            fans=fans,
            prestige=prestige,
            roster=roster,
            color=self._get_rival_color(size),
            icon=self._get_rival_icon(size),
            description=self._generate_description(name, philosophy, strategy, size),
        )

        if is_major:
            rival.relationship = RivalRelationship.NEUTRAL
            rival.rivalry_with_player = 10
            rival.aggression = 70
            rival.ambition = 80
            rival.stability = 70

        return rival

    def _generate_owner_name(self) -> str:
        first = ["Marcus", "Jasmine", "Kevin", "Sara", "Tony", "Lisa"]
        last = ["Stone", "Sterling", "Cross", "Vega", "Hill", "Black"]
        return f"{random.choice(first)} {random.choice(last)}"

    def _generate_rival_roster(self, size: int) -> List[str]:
        """Generate fictional wrestler names for a rival roster."""
        first = [
            "Axel", "Zane", "Killian", "Jaxon", "Reign", "Kade",
            "Phoenix", "Storm", "Shadow", "Razor", "Raven", "Luna",
            "Nova", "Ember", "Skye", "Vixen", "Hex", "Onyx",
        ]
        last = [
            "Storm", "Vex", "Black", "Cross", "Steele", "Wolfe",
            "Knight", "Sterling", "Reign", "Stone", "Savage", "King",
        ]
        roster: List[str] = []
        used = set()
        attempts = 0
        while len(roster) < size and attempts < size * 4:
            name = f"{random.choice(first)} {random.choice(last)}"
            if name not in used:
                roster.append(name)
                used.add(name)
            attempts += 1
        return roster

    # ==================== WEEKLY OPERATIONS ====================

    def process_weekly_operations(
        self,
        current_week: int,
        current_year: int,
        player_roster: List[Dict],
        player_free_agents: List[Dict],
        player_prestige: int,
        player_fans: int,
    ) -> Dict[str, List[Dict]]:
        """
        Process all rival activity for the week.
        Returns a dict with keys:
        - shows_run
        - signings
        - raids
        - growth_events
        - rival_news
        - social_posts
        - fan_reactions
        - writer_room_prompts
        """
        self.weeks_active += 1
        results: Dict[str, List[Dict]] = {
            "shows_run": [],
            "signings": [],
            "raids": [],
            "growth_events": [],
            "rival_news": [],
            "social_posts": [],
            "fan_reactions": [],
            "writer_room_prompts": [],
        }

        for rival in self.rivals:
            if not rival.is_active:
                continue

            # Weekly tick
            rival.weeks_active += 1
            stats = RIVAL_TIER_STATS.get(rival.size, RIVAL_TIER_STATS[RivalSize.INDIE])

            # Show: the rival runs a show depending on show_frequency
            if random.random() < stats["show_frequency"]:
                show = self._run_rival_show(rival, current_week, current_year)
                if show:
                    results["shows_run"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "show": show.to_dict(),
                    })
                    results["rival_news"].append(self._make_show_news(rival, show))
                    results["social_posts"].extend(self._make_show_social(rival, show))
                    results["fan_reactions"].extend(self._make_fan_reactions(rival, show))
                    results["writer_room_prompts"].append(self._make_writer_prompt(rival, show))

            # Free agent signing: small chance to sign if budget allows
            if player_free_agents and random.random() < stats["signing_chance"]:
                signing = self._attempt_free_agent_signing(rival, player_free_agents, current_week, current_year)
                if signing:
                    results["signings"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "signing": signing.to_dict(),
                    })
                    results["rival_news"].append(self._make_signing_news(rival, signing))
                    if not signing.success:
                        results["fan_reactions"].append(self._make_failed_signing_reaction(rival, signing))

            # Roster raid: some rivals try to poach from the player's roster
            if player_roster and random.random() < stats["raid_chance"]:
                raid = self._attempt_roster_raid(rival, player_roster, current_week, current_year)
                if raid:
                    results["raids"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "raid": raid.to_dict(),
                    })
                    rival.rivalry_with_player += 15
                    rival.update_relationship()
                    results["rival_news"].append(self._make_raid_news(rival, raid))
                    results["social_posts"].append(self._make_raid_social(rival, raid))

            # Rivalry and momentum adjustments: update based on player prestige/fans
            if player_prestige > rival.prestige:
                rival.rivalry_with_player += 1
            if player_fans > rival.fans:
                rival.rivalry_with_player += 1
            rival.rivalry_with_player = max(0, min(100, rival.rivalry_with_player))
            rival.update_relationship()

            # Potential growth or decline
            if random.random() < stats["expansion_chance"]:
                growth = self._process_growth_event(rival)
                if growth:
                    results["growth_events"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "event": growth,
                    })
                    results["rival_news"].append(self._make_growth_news(rival, growth))

        return results

    # ==================== INTERNAL SIMULATION ====================

    def _run_rival_show(self, rival: RivalPromotion, week: int, year: int) -> Optional[RivalShow]:
        """Simulate running a rival show with attendance, rating, revenue, and profit."""
        if not rival.roster or len(rival.roster) < 4 or rival.budget < 300:
            return None

        venues = RIVAL_VENUES_BY_SIZE.get(rival.size, ["Local Venue"])
        venue = random.choice(venues)

        max_attendance = max(rival.fans // 3, 80)
        min_attendance = max(30, rival.fans // 10)
        attendance = random.randint(min_attendance, max_attendance)
        base_rating = 2.5 + (rival.prestige / 55.0)
        rating = max(1.0, min(5.0, base_rating + random.uniform(-0.8, 0.8)))

        wrestlers_in_main = random.sample(rival.roster, min(2, len(rival.roster)))
        main_event = " vs ".join(wrestlers_in_main)
        notable_match = ""
        if len(rival.roster) >= 4:
            others = [w for w in rival.roster if w not in wrestlers_in_main]
            if len(others) >= 2:
                pair = random.sample(others, 2)
                notable_match = " vs ".join(pair)

        ticket_price = random.uniform(8, 25)
        revenue = int(attendance * ticket_price)
        production_cost = random.randint(300, 1500)
        profit = revenue - production_cost

        fan_change = 0
        prestige_change = 0
        if rating >= 4.2:
            fan_change = int(rival.fans * 0.05) + random.randint(50, 200)
            prestige_change = 2
        elif rating >= 3.5:
            fan_change = int(rival.fans * 0.02) + random.randint(20, 80)
            prestige_change = 1
        elif rating < 2.0:
            fan_change = -int(rival.fans * 0.02) - random.randint(10, 40)
            prestige_change = -1

        show = RivalShow(
            week=week,
            year=year,
            venue=venue,
            attendance=attendance,
            rating=rating,
            main_event=main_event,
            notable_match=notable_match,
            revenue=revenue,
            profit=profit,
            fan_change=fan_change,
            prestige_change=prestige_change,
        )

        rival.show_history.append(show)
        rival.shows_run += 1
        rival.budget += profit
        rival.fans = max(50, rival.fans + fan_change)
        rival.prestige = max(0, min(100, rival.prestige + prestige_change))
        rival.momentum = int((rival.momentum + prestige_change) * 0.9)

        return show

    def _attempt_free_agent_signing(
        self, rival: RivalPromotion, free_agents: List[Dict], week: int, year: int
    ) -> Optional[RivalSigning]:
        """Attempt to sign a free agent from the global pool."""
        if not free_agents or rival.budget < 1000:
            return None

        suitable = [
            w for w in free_agents
            if w.get("popularity", 30) <= rival.prestige + 15
        ]
        if not suitable:
            return None

        chosen = random.choice(suitable)
        cost = random.randint(500, 2500)
        success_chance = 0.6 + ((rival.prestige - chosen.get("popularity", 30)) / 200)

        success = random.random() < success_chance
        reason = ""
        if not success:
            reason = random.choice([
                "offered lower wages",
                "incompatible style",
                "better offer elsewhere",
                "personal preference",
            ])

        signing = RivalSigning(
            week=week,
            year=year,
            wrestler_name=chosen.get("name", "Unknown Wrestler"),
            action="signed",
            from_promotion="Free Agent Market",
            success=success,
            offer_amount=cost,
            reason=reason,
        )

        rival.signing_history.append(signing)
        if success:
            rival.roster.append(signing.wrestler_name)
            rival.budget -= cost

        return signing

    def _attempt_roster_raid(
        self, rival: RivalPromotion, player_roster: List[Dict], week: int, year: int
    ) -> Optional[RivalSigning]:
        """Try to poach a wrestler from the player's roster."""
        if not player_roster or rival.budget < 5000 or rival.size == RivalSize.BACKYARD:
            return None

        # Identify vulnerable talent: low morale or loyalty
        targetable = [
            w for w in player_roster
            if w.get("morale", 75) < 60 or w.get("loyalty", 75) < 60
        ]
        if not targetable:
            return None

        chosen = random.choice(targetable)
        base_chance = 0.25 + ((100 - chosen.get("loyalty", 50)) / 200)
        raid_success = random.random() < base_chance

        raid = RivalSigning(
            week=week,
            year=year,
            wrestler_name=chosen.get("name", "Player Wrestler"),
            action="raided",
            from_promotion="Player Promotion",
            success=raid_success,
            offer_amount=random.randint(3000, 12000),
        )

        if raid_success:
            rival.roster.append(raid.wrestler_name)
            rival.budget -= raid.offer_amount

        rival.signing_history.append(raid)
        return raid

    def _process_growth_event(self, rival: RivalPromotion) -> Optional[Dict]:
        """Handle potential promotion or decline based on prestige and recent shows."""
        # Promotion logic: increase in tier if prestige is high enough
        if rival.prestige >= 90 and rival.size != RivalSize.GLOBAL:
            sizes = list(RivalSize)
            curr_idx = sizes.index(rival.size)
            if curr_idx + 1 < len(sizes):
                old = rival.size
                rival.size = sizes[curr_idx + 1]
                stats = RIVAL_TIER_STATS[rival.size]
                rival.budget = max(rival.budget, stats["budget_range"][0])
                return {
                    "type": "promotion",
                    "description": f"{rival.name} has been promoted to {rival.size.value} tier!",
                    "old_size": old.value,
                    "new_size": rival.size.value,
                }

        # Decline logic: loss due to bad average ratings
        if rival.show_history and len(rival.show_history) >= 5:
            recent = rival.show_history[-5:]
            avg_rating = sum(s.rating for s in recent) / len(recent)
            if avg_rating < 2.0:
                rival.prestige = max(0, rival.prestige - 2)
                rival.fans = max(50, int(rival.fans * 0.96))
                rival.momentum -= 2
                return {
                    "type": "decline",
                    "description": f"{rival.name} is losing popularity due to poor shows.",
                }

        return None

    # ==================== NEWS & SOCIAL HELPERS ====================

    def _make_show_news(self, rival: RivalPromotion, show: RivalShow) -> Dict[str, str]:
        """Create a news snippet for a successful or notable show."""
        star_rating = f"{show.rating:.1f}★"
        headline = f"{rival.name} draws {show.attendance} fans for {star_rating} show"
        if show.rating >= 4.2:
            body = (
                f"{rival.name} delivered a standout show at {show.venue}, drawing {show.attendance} fans "
                f"and earning a {show.rating:.1f}★ rating. Momentum is building for the promotion."
            )
        elif show.rating >= 3.5:
            body = (
                f"{rival.name} ran a solid event this week with a {show.rating:.1f}★ rating and "
                f"{show.attendance} fans, continuing to grow their audience."
            )
        elif show.rating < 2.0:
            body = (
                f"{rival.name}'s latest event stumbled with a {show.rating:.1f}★ rating, signaling a need for change."
            )
        else:
            body = (
                f"{rival.name} held a routine show with {show.attendance} fans and an average {show.rating:.1f}★ rating."
            )
        return {"headline": headline, "body": body, "type": "show_recape"}

    def _make_signing_news(self, rival: RivalPromotion, signing: RivalSigning) -> Dict[str, str]:
        """Create a news snippet for a signing or failed signing."""
        wrestler = signing.wrestler_name
        if signing.success:
            headline = f"{wrestler} joins {rival.name}"
            body = (
                f"{rival.name} has signed free agent {wrestler}. "
                f"The signing is seen as a good fit for the promotion."
            )
        else:
            headline = f"{rival.name} fails to sign {wrestler}"
            body = (
                f"{rival.name} attempted to sign {wrestler} but the deal fell through due to {signing.reason}."
            )
        return {"headline": headline, "body": body, "type": "signing"}

    def _make_raid_news(self, rival: RivalPromotion, raid: RivalSigning) -> Dict[str, str]:
        """Create a news snippet for a raid."""
        wrestler = raid.wrestler_name
        if raid.success:
            headline = f"{rival.name} poaches {wrestler} from player"
            body = f"{rival.name} successfully raided and signed {wrestler} away from your promotion."
        else:
            headline = f"{rival.name} fails to poach {wrestler}"
            body = f"{rival.name} tried to poach {wrestler}, but the offer was declined."
        return {"headline": headline, "body": body, "type": "raid"}

    def _make_growth_news(self, rival: RivalPromotion, growth: Dict[str, str]) -> Dict[str, str]:
        """Create a news snippet for a growth or decline event."""
        if growth["type"] == "promotion":
            headline = f"{rival.name} moves up to {growth['new_size']}!"
            body = growth["description"]
        else:
            headline = f"{rival.name} on the decline"
            body = growth["description"]
        return {"headline": headline, "body": body, "type": "growth"}

    def _make_show_social(self, rival: RivalPromotion, show: RivalShow) -> List[Dict[str, str]]:
        """Generate social media posts for a show."""
        posts: List[Dict[str, str]] = []
        if show.rating >= 4.2:
            posts.append({
                "author": "FanCommunity",
                "content": f"{rival.name} absolutely killed it this week! {show.main_event} stole the show! ⭐⭐⭐⭐",
            })
        elif show.rating >= 3.5:
            posts.append({
                "author": "FanCommunity",
                "content": f"Good vibes from {rival.name}'s latest event. Not a bad show at all!",
            })
        elif show.rating < 2.0:
            posts.append({
                "author": "FanCommunity",
                "content": f"Ouch! {rival.name}'s show was a flop. What went wrong? 🤔",
            })
        # Always push a general buzz post
        posts.append({
            "author": "NewsBot",
            "content": f"Did you catch {rival.name}'s event this week? Rating {show.rating:.1f}★ with {show.attendance} fans.",
        })
        return posts

    def _make_fan_reactions(self, rival: RivalPromotion, show: RivalShow) -> List[Dict[str, str]]:
        """Generate fan reactions (feedback) for a show."""
        reactions: List[Dict[str, str]] = []
        if show.rating >= 4.2:
            reactions.append({"sentiment": "positive", "comment": "Amazing matches! Can't wait for the next show."})
        elif show.rating >= 3.5:
            reactions.append({"sentiment": "positive", "comment": "Solid show, but room to get even better."})
        elif show.rating < 2.0:
            reactions.append({"sentiment": "negative", "comment": "Terrible show, hope they change things fast!"})
        return reactions

    def _make_failed_signing_reaction(self, rival: RivalPromotion, signing: RivalSigning) -> Dict[str, str]:
        """Generate a fan reaction for a failed signing attempt."""
        return {
            "sentiment": "negative",
            "comment": f"Rumor has it {signing.wrestler_name} turned down {rival.name}. They need to up their game!",
        }

    def _make_raid_social(self, rival: RivalPromotion, raid: RivalSigning) -> Dict[str, str]:
        """Social post when a raid is attempted."""
        if raid.success:
            return {
                "author": "Insider",
                "content": f"{rival.name} just poached {raid.wrestler_name} from the player’s roster! 🔥",
            }
        return {
            "author": "Insider",
            "content": f"{rival.name} tried to steal {raid.wrestler_name}, but it failed.",
        }

    def _make_writer_prompt(self, rival: RivalPromotion, show: RivalShow) -> Dict[str, str]:
        """Create a simple Writers Room prompt based on rival show performance."""
        prompt = {
            "prompt_type": "rival_update",
            "rival_id": rival.id,
            "rival_name": rival.name,
            "summary": (
                f"{rival.name} ran a show with a {show.rating:.1f}★ rating at {show.venue}. "
                f"They gained {show.fan_change} fans and improved prestige by {show.prestige_change}."
            ),
        }
        return prompt

    # ==================== MANAGER UTILITY METHODS ====================

    def get_all_rivals(self) -> List[RivalPromotion]:
        return [r for r in self.rivals if r.is_active]

    def get_rival(self, rival_id: str) -> Optional[RivalPromotion]:
        for r in self.rivals:
            if r.id == rival_id:
                return r
        return None

    def get_rivals_by_size(self, size: RivalSize) -> List[RivalPromotion]:
        return [r for r in self.get_all_rivals() if r.size == size]

    def get_top_rival(self) -> Optional[RivalPromotion]:
        """Get the rival with the highest prestige."""
        active = self.get_all_rivals()
        if not active:
            return None
        return max(active, key=lambda r: r.prestige)

    def get_biggest_threat(self, player_prestige: int, player_fans: int) -> Optional[RivalPromotion]:
        """Get the rival that poses the biggest combined prestige/fan threat."""
        active = self.get_all_rivals()
        if not active:
            return None
        threats = [
            r for r in active
            if r.prestige >= player_prestige - 5 and r.fans >= player_fans / 2
        ]
        if not threats:
            threats = active
        return max(threats, key=lambda r: r.rivalry_with_player + r.prestige)

    def get_hostile_rivals(self) -> List[RivalPromotion]:
        """Return rivals at hostile or war status."""
        return [
            r for r in self.get_all_rivals()
            if r.relationship in [RivalRelationship.HOSTILE, RivalRelationship.WAR]
        ]

    def get_industry_summary(self, player_prestige: int, player_fans: int) -> Dict[str, any]:
        """Provide a summary of the wrestling industry for display."""
        active = self.get_all_rivals()
        if not active:
            return {
                "total_rivals": 0,
                "industry_leader": "Player",
                "player_rank": 1,
                "hostile_count": 0,
            }

        all_promotions = active + [{"name": "Player", "prestige": player_prestige, "fans": player_fans}]
        leader = max(all_promotions, key=lambda p: p.prestige if hasattr(p, "prestige") else p["prestige"])
        leader_name = leader.name if hasattr(leader, "name") else leader["name"]

        # Determine the player's position
        sorted_by_prestige = sorted(all_promotions, key=lambda p: p.prestige if hasattr(p, "prestige") else p["prestige"], reverse=True)
        player_rank = next(
            (i + 1 for i, p in enumerate(sorted_by_prestige) if (hasattr(p, "name") and p.name == "Player") or (isinstance(p, dict) and p["name"] == "Player")),
            len(sorted_by_prestige)
        )

        return {
            "total_rivals": len(active),
            "industry_leader": leader_name,
            "is_player_leader": leader_name == "Player",
            "player_rank": player_rank,
            "total_promotions": len(all_promotions),
            "hostile_count": len(self.get_hostile_rivals()),
        }

    # ==================== DATA SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "rivals": [r.to_dict() for r in self.rivals],
            "next_id": self.next_id,
            "weeks_active": self.weeks_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalPromotionManager":
        manager = cls()
        manager.next_id = data.get("next_id", 1)
        manager.weeks_active = data.get("weeks_active", 0)
        for entry in data.get("rivals", []):
            try:
                manager.rivals.append(RivalPromotion.from_dict(entry))
            except Exception:
                pass
        return manager
