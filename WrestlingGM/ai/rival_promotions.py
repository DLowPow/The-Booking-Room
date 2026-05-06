"""
AI Rival Promotions - Competing wrestling companies
AI-controlled promotions that sign talent, run shows, raid rosters
Creates industry pressure, competition for free agents, and dynamic news
Each rival has its own personality, philosophy, and strategy
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
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
    POACHER = "Talent Poacher"          # Aggressively raids other rosters
    DEVELOPER = "Talent Developer"      # Builds homegrown stars
    SPECTACLE = "Spectacle Booker"      # Big shows, big moments
    PURIST = "Wrestling Purist"         # Quality matches over storylines
    CHAOS = "Chaos Agent"               # Unpredictable booking
    BUDGET = "Budget Operation"         # Runs lean, profits margin


class RivalRelationship(Enum):
    FRIENDLY = "Friendly"
    NEUTRAL = "Neutral"
    COMPETITIVE = "Competitive"
    HOSTILE = "Hostile"
    WAR = "At War"


# ==================== RIVAL DATA TEMPLATES ====================

RIVAL_NAME_POOL = {
    RivalSize.BACKYARD: [
        "Garage Wrestling Federation", "Backyard Brawlers United",
        "The Driveway Dynasty", "Bedroom Wrestling Inc",
        "Suburban Slam", "House Show Heroes",
    ],
    RivalSize.INDIE: [
        "Underground Wrestling Alliance", "Pure Combat Wrestling",
        "Independent Mat Federation", "Bingo Hall Brawlers",
        "Steel Town Wrestling", "Concrete Jungle Combat",
        "Iron Fist Wrestling", "Shadow Circuit Wrestling",
    ],
    RivalSize.REGIONAL: [
        "Apex Regional Wrestling", "Storm Front Wrestling",
        "Velocity Pro Wrestling", "Phoenix Rising Federation",
        "Diamond State Wrestling", "Coastal Combat Federation",
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
    "Tokyo, Japan", "Mexico City, Mexico", "London, England",
    "Toronto, Canada", "Berlin, Germany", "Sydney, Australia",
    "Los Angeles, USA", "New York, USA", "Chicago, USA",
    "Dallas, USA", "Atlanta, USA", "Philadelphia, USA",
    "Madrid, Spain", "Paris, France", "Rome, Italy",
    "Buenos Aires, Argentina", "São Paulo, Brazil",
    "Seoul, South Korea", "Manchester, England", "Glasgow, Scotland",
]


# ==================== RIVAL STATS ====================

RIVAL_TIER_STATS = {
    RivalSize.BACKYARD: {
        "budget_range": [500, 3000],
        "fans_range": [50, 300],
        "prestige_range": [1, 8],
        "roster_size_range": [4, 8],
        "show_frequency": 0.3,  # Chance per week of running a show
        "raid_chance": 0.05,
        "expansion_chance": 0.10,
    },
    RivalSize.INDIE: {
        "budget_range": [3000, 15000],
        "fans_range": [300, 2000],
        "prestige_range": [8, 25],
        "roster_size_range": [6, 12],
        "show_frequency": 0.5,
        "raid_chance": 0.10,
        "expansion_chance": 0.08,
    },
    RivalSize.REGIONAL: {
        "budget_range": [15000, 60000],
        "fans_range": [2000, 10000],
        "prestige_range": [25, 45],
        "roster_size_range": [10, 18],
        "show_frequency": 0.7,
        "raid_chance": 0.15,
        "expansion_chance": 0.06,
    },
    RivalSize.NATIONAL: {
        "budget_range": [60000, 250000],
        "fans_range": [10000, 50000],
        "prestige_range": [45, 65],
        "roster_size_range": [15, 25],
        "show_frequency": 0.85,
        "raid_chance": 0.20,
        "expansion_chance": 0.05,
    },
    RivalSize.MAJOR: {
        "budget_range": [250000, 1000000],
        "fans_range": [50000, 200000],
        "prestige_range": [65, 85],
        "roster_size_range": [20, 35],
        "show_frequency": 0.95,
        "raid_chance": 0.25,
        "expansion_chance": 0.03,
    },
    RivalSize.GLOBAL: {
        "budget_range": [1000000, 10000000],
        "fans_range": [200000, 2000000],
        "prestige_range": [85, 100],
        "roster_size_range": [30, 50],
        "show_frequency": 1.0,
        "raid_chance": 0.30,
        "expansion_chance": 0.02,
    },
}


# ==================== RIVAL PROMOTION CLASS ====================

@dataclass
class RivalShow:
    """A show run by a rival promotion"""
    week: int
    year: int
    venue: str
    attendance: int
    rating: float
    main_event: str = ""
    notable_match: str = ""
    revenue: int = 0


@dataclass
class RivalSigning:
    """A wrestler signing or release event"""
    week: int
    year: int
    wrestler_name: str
    action: str  # "signed", "released", "raided"
    from_promotion: str = ""


@dataclass
class RivalPromotion:
    """A complete rival wrestling promotion"""
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
    rivalry_with_player: int = 0  # 0-100 hostility score
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
        """Compare to player to determine threat level"""
        prestige_diff = self.prestige - player_prestige
        fan_diff = self.fans - player_fans

        if prestige_diff > 30 or fan_diff > player_fans * 2:
            return "Major Threat"
        elif prestige_diff > 15:
            return "Significant Threat"
        elif prestige_diff > 0:
            return "Equal Competition"
        elif prestige_diff > -15:
            return "Lesser Competition"
        else:
            return "Minor Threat"

    def update_relationship(self):
        """Update relationship based on rivalry score"""
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
            "show_history": [
                {"week": s.week, "year": s.year, "venue": s.venue,
                 "attendance": s.attendance, "rating": s.rating,
                 "main_event": s.main_event, "notable_match": s.notable_match,
                 "revenue": s.revenue}
                for s in self.show_history[-20:]
            ],
            "signing_history": [
                {"week": s.week, "year": s.year, "wrestler_name": s.wrestler_name,
                 "action": s.action, "from_promotion": s.from_promotion}
                for s in self.signing_history[-30:]
            ],
            "rivalry_with_player": self.rivalry_with_player,
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
            notable_champions=data.get("notable_champions", {}),
            color=data.get("color", "#6b7280"),
            icon=data.get("icon", "🏟️"),
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
        )

        for sd in data.get("show_history", []):
            rival.show_history.append(RivalShow(
                week=sd.get("week", 0), year=sd.get("year", 1),
                venue=sd.get("venue", ""), attendance=sd.get("attendance", 0),
                rating=sd.get("rating", 0), main_event=sd.get("main_event", ""),
                notable_match=sd.get("notable_match", ""),
                revenue=sd.get("revenue", 0),
            ))

        for sd in data.get("signing_history", []):
            rival.signing_history.append(RivalSigning(
                week=sd.get("week", 0), year=sd.get("year", 1),
                wrestler_name=sd.get("wrestler_name", ""),
                action=sd.get("action", "signed"),
                from_promotion=sd.get("from_promotion", ""),
            ))

        return rival


# ==================== RIVAL VENUES ====================

RIVAL_VENUES_BY_SIZE = {
    RivalSize.BACKYARD: ["Local Park", "Community Garage", "Driveway Setup", "Backyard Stage"],
    RivalSize.INDIE: ["VFW Hall", "Local Bingo Hall", "Bar District Venue", "Community Center"],
    RivalSize.REGIONAL: ["Civic Center", "Convention Hall", "Regional Arena", "Theater District"],
    RivalSize.NATIONAL: ["Sports Arena", "Convention Center", "Music Theater", "Pavilion"],
    RivalSize.MAJOR: ["Major Arena", "Mega Stadium", "Iconic Venue", "Sports Coliseum"],
    RivalSize.GLOBAL: ["Stadium", "Mega Dome", "Iconic Stadium", "Global Arena"],
}


# ==================== RIVAL PROMOTION GENERATOR ====================

class RivalPromotionManager:
    """
    Manages all AI rival promotions in the game world.
    Generates new rivals, runs their weekly operations, processes signings/raids,
    and creates news about their activities.
    """

    def __init__(self):
        self.rivals: List[RivalPromotion] = []
        self.next_id: int = 1
        self.weeks_active: int = 0

    # ==================== RIVAL CREATION ====================

    def create_starter_rivals(self, player_size: RivalSize = RivalSize.BACKYARD) -> List[RivalPromotion]:
        """Create initial roster of rival promotions appropriate to player size"""
        rivals_created = []

        # Create rivals at player's size and one tier above
        size_progression = list(RivalSize)
        player_idx = size_progression.index(player_size)

        # 2-3 rivals at player's level
        for _ in range(random.randint(2, 3)):
            rival = self.generate_rival(player_size)
            if rival:
                self.rivals.append(rival)
                rivals_created.append(rival)

        # 1-2 rivals one tier above (if available)
        if player_idx + 1 < len(size_progression):
            for _ in range(random.randint(1, 2)):
                rival = self.generate_rival(size_progression[player_idx + 1])
                if rival:
                    self.rivals.append(rival)
                    rivals_created.append(rival)

        # 1 major rival (industry leader)
        major_size = size_progression[min(player_idx + 3, len(size_progression) - 1)]
        rival = self.generate_rival(major_size, is_major=True)
        if rival:
            self.rivals.append(rival)
            rivals_created.append(rival)

        return rivals_created

    def generate_rival(self, size: RivalSize, is_major: bool = False) -> Optional[RivalPromotion]:
        """Generate a single rival promotion"""
        name_pool = RIVAL_NAME_POOL.get(size, [])
        if not name_pool:
            return None

        # Filter out already-used names
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

        # Generate fictional roster names
        roster_size = random.randint(*stats["roster_size_range"])
        roster = self._generate_rival_roster(roster_size, name)

        # Owner name
        first_names = ["Marcus", "Jasmine", "Kevin", "Sara", "Tony", "Lisa", "Derek", "Amanda", "Eric", "Nina"]
        last_names = ["Stone", "Sterling", "Cross", "Vega", "Hill", "Black", "Ross", "King", "Rivera", "Storm"]
        owner_name = f"{random.choice(first_names)} {random.choice(last_names)}"

        rival_id = f"rival_{self.next_id}"
        self.next_id += 1

        rival = RivalPromotion(
            id=rival_id,
            name=name,
            size=size,
            philosophy=philosophy,
            strategy=strategy,
            location=location,
            owner_name=owner_name,
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

        return rival

    def _generate_rival_roster(self, size: int, promotion_name: str) -> List[str]:
        """Generate fictional wrestler names for a rival roster"""
        first_names = [
            "Axel", "Zane", "Killian", "Jaxon", "Reign", "Kade", "Phoenix", "Storm",
            "Diamond", "Steel", "Crash", "Blaze", "Viper", "Thunder", "Shadow", "Razor",
            "Carla", "Jade", "Raven", "Luna", "Nova", "Ember", "Skye", "Vixen",
            "Rage", "Hex", "Onyx", "Crimson", "Knox", "Talon", "Wrath", "Fury",
        ]
        last_names = [
            "Storm", "Vex", "Black", "Cross", "Steele", "Wolfe", "Knight", "Sterling",
            "Reign", "Stone", "Savage", "King", "Frost", "Rage", "Vortex", "Dynamite",
            "Phoenix", "Hex", "Slayer", "Carnage", "Mayhem", "Vengeance",
        ]

        roster = []
        used = set()
        attempts = 0
        while len(roster) < size and attempts < size * 3:
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            if name not in used:
                roster.append(name)
                used.add(name)
            attempts += 1

        return roster

    def _get_rival_color(self, size: RivalSize) -> str:
        colors = {
            RivalSize.BACKYARD: "#6b7280",
            RivalSize.INDIE: "#10b981",
            RivalSize.REGIONAL: "#3b82f6",
            RivalSize.NATIONAL: "#8b5cf6",
            RivalSize.MAJOR: "#f59e0b",
            RivalSize.GLOBAL: "#dc2626",
        }
        return colors.get(size, "#6b7280")

    def _get_rival_icon(self, size: RivalSize) -> str:
        icons = {
            RivalSize.BACKYARD: "🏠",
            RivalSize.INDIE: "🏛️",
            RivalSize.REGIONAL: "🏟️",
            RivalSize.NATIONAL: "🏛️",
            RivalSize.MAJOR: "🏟️",
            RivalSize.GLOBAL: "🌍",
        }
        return icons.get(size, "🏟️")

    def _generate_description(self, name: str, philosophy: RivalPhilosophy,
                              strategy: RivalStrategy, size: RivalSize) -> str:
        philosophy_desc = {
            RivalPhilosophy.SPORTS_ENTERTAINMENT: "entertainment-focused product",
            RivalPhilosophy.STRONG_STYLE: "hard-hitting Japanese-inspired style",
            RivalPhilosophy.LUCHA_LIBRE: "high-flying Mexican wrestling tradition",
            RivalPhilosophy.ULTRAVIOLENT: "extreme hardcore product",
            RivalPhilosophy.HYBRID: "diverse wrestling blend",
            RivalPhilosophy.OLD_SCHOOL: "traditional wrestling fundamentals",
        }

        strategy_desc = {
            RivalStrategy.POACHER: "known for raiding other rosters",
            RivalStrategy.DEVELOPER: "focused on developing homegrown talent",
            RivalStrategy.SPECTACLE: "famous for grand spectacles",
            RivalStrategy.PURIST: "committed to in-ring quality",
            RivalStrategy.CHAOS: "famously unpredictable",
            RivalStrategy.BUDGET: "running a lean operation",
        }

        return (f"{name} is a {size.value.lower()}-level promotion specializing in "
                f"{philosophy_desc.get(philosophy, 'wrestling')}, {strategy_desc.get(strategy, 'in the industry')}.")

    # ==================== WEEKLY OPERATIONS ====================

    def process_weekly_operations(
        self,
        current_week: int,
        current_year: int,
        player_roster: List[Dict],
        player_free_agents: List[Dict],
        player_prestige: int,
        player_fans: int,
    ) -> Dict:
        """Process all rival promotion weekly activities"""
        self.weeks_active += 1
        results = {
            "shows_run": [],
            "signings": [],
            "raids": [],
            "news_events": [],
            "growth_events": [],
        }

        for rival in self.rivals:
            if not rival.is_active:
                continue

            rival.weeks_active += 1
            stats = RIVAL_TIER_STATS.get(rival.size, RIVAL_TIER_STATS[RivalSize.INDIE])

            # Run shows
            if random.random() < stats["show_frequency"]:
                show = self._run_rival_show(rival, current_week, current_year)
                if show:
                    results["shows_run"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "show": show,
                    })

            # Sign free agents
            if player_free_agents and random.random() < 0.15:
                signing = self._attempt_free_agent_signing(rival, player_free_agents, current_week, current_year)
                if signing:
                    results["signings"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "signing": signing,
                    })

            # Raid player roster
            if player_roster and random.random() < stats["raid_chance"] * 0.3:
                raid = self._attempt_roster_raid(rival, player_roster, current_week, current_year)
                if raid:
                    results["raids"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "raid": raid,
                    })
                    rival.rivalry_with_player += 15
                    rival.update_relationship()

            # Update rivalry based on player success
            if player_prestige > rival.prestige:
                rival.rivalry_with_player += 1
            if player_fans > rival.fans:
                rival.rivalry_with_player += 1
            rival.rivalry_with_player = max(0, min(100, rival.rivalry_with_player))
            rival.update_relationship()

            # Growth/decline
            if random.random() < stats["expansion_chance"]:
                growth = self._process_growth(rival)
                if growth:
                    results["growth_events"].append({
                        "rival_name": rival.name,
                        "rival_id": rival.id,
                        "event": growth,
                    })

        return results

    def _run_rival_show(self, rival: RivalPromotion, week: int, year: int) -> Optional[RivalShow]:
        """Simulate a rival running a show"""
        if not rival.roster or len(rival.roster) < 4:
            return None

        venues = RIVAL_VENUES_BY_SIZE.get(rival.size, ["Local Venue"])
        venue = random.choice(venues)

        # Calculate attendance based on size and fans
        max_attendance = rival.fans // 3
        min_attendance = max(50, rival.fans // 10)
        attendance = random.randint(min_attendance, max(min_attendance + 1, max_attendance))

        # Calculate show rating
        base_rating = 2.5 + (rival.prestige / 50)
        variance = random.uniform(-0.8, 0.8)
        rating = max(1.0, min(5.0, base_rating + variance))

        # Pick main event from roster
        wrestlers_in_main = random.sample(rival.roster, min(2, len(rival.roster)))
        main_event = " vs ".join(wrestlers_in_main)

        # Pick notable match
        notable_match = ""
        if len(rival.roster) >= 4:
            other_wrestlers = [w for w in rival.roster if w not in wrestlers_in_main]
            if len(other_wrestlers) >= 2:
                pair = random.sample(other_wrestlers, 2)
                notable_match = " vs ".join(pair)

        # Calculate revenue
        revenue = int(attendance * random.uniform(8, 25))

        show = RivalShow(
            week=week, year=year, venue=venue,
            attendance=attendance, rating=rating,
            main_event=main_event, notable_match=notable_match,
            revenue=revenue,
        )

        rival.show_history.append(show)
        rival.shows_run += 1
        rival.budget += revenue

        # Fan growth from successful shows
        if rating >= 4.0:
            rival.fans = int(rival.fans * 1.02)
            rival.prestige = min(100, rival.prestige + 1)
        elif rating >= 3.0:
            rival.fans = int(rival.fans * 1.005)

        return show

    def _attempt_free_agent_signing(
        self, rival: RivalPromotion, free_agents: List[Dict],
        week: int, year: int
    ) -> Optional[RivalSigning]:
        """Rival tries to sign a free agent"""
        if not free_agents or rival.budget < 1000:
            return None

        # Pick a free agent that fits rival's level
        suitable = [w for w in free_agents if w.get("popularity", 30) <= rival.prestige + 20]
        if not suitable:
            return None

        chosen = random.choice(suitable)

        signing = RivalSigning(
            week=week, year=year,
            wrestler_name=chosen["name"],
            action="signed",
        )

        rival.signing_history.append(signing)
        rival.roster.append(chosen["name"])
        rival.budget -= random.randint(500, 2000)

        return signing

    def _attempt_roster_raid(
        self, rival: RivalPromotion, player_roster: List[Dict],
        week: int, year: int
    ) -> Optional[RivalSigning]:
        """Rival tries to poach from player's roster"""
        if not player_roster or rival.budget < 5000:
            return None

        # Higher-level rivals can raid better wrestlers
        if rival.size == RivalSize.BACKYARD:
            return None  # Backyards don't raid

        # Pick a wrestler with low loyalty/morale from player roster
        targetable = [
            w for w in player_roster
            if w.get("morale", 75) < 60 or w.get("loyalty", 75) < 60
        ]

        if not targetable:
            return None

        chosen = random.choice(targetable)

        # Raid attempt - not guaranteed to succeed
        raid_chance = 0.3 + ((100 - chosen.get("loyalty", 75)) / 100 * 0.4)
        if random.random() > raid_chance:
            return None  # Failed raid

        signing = RivalSigning(
            week=week, year=year,
            wrestler_name=chosen["name"],
            action="raided",
            from_promotion="Player Promotion",
        )

        rival.signing_history.append(signing)
        rival.roster.append(chosen["name"])
        rival.budget -= random.randint(3000, 10000)

        return signing

    def _process_growth(self, rival: RivalPromotion) -> Optional[Dict]:
        """Process potential growth or decline events"""
        # Promotion to next tier?
        if rival.prestige >= 90 and rival.size != RivalSize.GLOBAL:
            sizes = list(RivalSize)
            current_idx = sizes.index(rival.size)
            if current_idx + 1 < len(sizes):
                old_size = rival.size
                rival.size = sizes[current_idx + 1]
                stats = RIVAL_TIER_STATS[rival.size]
                rival.budget = max(rival.budget, stats["budget_range"][0])
                return {
                    "type": "promoted",
                    "description": f"{rival.name} has expanded to {rival.size.value} level!",
                    "old_size": old_size.value,
                    "new_size": rival.size.value,
                }

        # Decline due to bad shows?
        if rival.show_history and len(rival.show_history) >= 5:
            recent = rival.show_history[-5:]
            avg_recent = sum(s.rating for s in recent) / len(recent)
            if avg_recent < 2.0:
                rival.prestige = max(0, rival.prestige - 2)
                rival.fans = int(rival.fans * 0.95)
                if rival.prestige < 5 and rival.size != RivalSize.BACKYARD:
                    return {
                        "type": "declining",
                        "description": f"{rival.name} is struggling with poor shows.",
                    }

        return None

    # ==================== QUERIES ====================

    def get_all_rivals(self) -> List[RivalPromotion]:
        return [r for r in self.rivals if r.is_active]

    def get_rival(self, rival_id: str) -> Optional[RivalPromotion]:
        for r in self.rivals:
            if r.id == rival_id:
                return r
        return None

    def get_rivals_by_size(self, size: RivalSize) -> List[RivalPromotion]:
        return [r for r in self.rivals if r.is_active and r.size == size]

    def get_top_rival(self) -> Optional[RivalPromotion]:
        """Get the most prestigious rival"""
        active = self.get_all_rivals()
        if not active:
            return None
        return max(active, key=lambda r: r.prestige)

    def get_biggest_threat(self, player_prestige: int, player_fans: int) -> Optional[RivalPromotion]:
        """Get the rival closest in size that's the biggest threat"""
        active = self.get_all_rivals()
        if not active:
            return None
        # Closest in prestige but slightly higher
        threats = [r for r in active if r.prestige >= player_prestige - 10]
        if not threats:
            threats = active
        return max(threats, key=lambda r: r.rivalry_with_player + r.prestige)

    def get_hostile_rivals(self) -> List[RivalPromotion]:
        """Get rivals at hostile or war status"""
        return [
            r for r in self.rivals
            if r.is_active and r.relationship in [RivalRelationship.HOSTILE, RivalRelationship.WAR]
        ]

    def get_industry_summary(self, player_prestige: int, player_fans: int) -> Dict:
        """Get a summary of the wrestling industry"""
        active = self.get_all_rivals()
        if not active:
            return {
                "total_rivals": 0,
                "industry_leader": "Player",
                "your_position": "Sole Player",
            }

        # Find industry leader
        all_promotions = active + [{"name": "Player", "prestige": player_prestige, "fans": player_fans}]
        leader = max(all_promotions, key=lambda r: r.prestige if hasattr(r, 'prestige') else r["prestige"])
        leader_name = leader.name if hasattr(leader, 'name') else leader["name"]

        # Find player's ranking
        sorted_by_prestige = sorted(
            all_promotions,
            key=lambda r: r.prestige if hasattr(r, 'prestige') else r["prestige"],
            reverse=True,
        )
        player_rank = next(
            (i + 1 for i, p in enumerate(sorted_by_prestige)
             if (hasattr(p, 'name') and p.name == "Player") or (isinstance(p, dict) and p.get("name") == "Player")),
            len(sorted_by_prestige),
        )

        return {
            "total_rivals": len(active),
            "industry_leader": leader_name,
            "is_player_leader": leader_name == "Player",
            "player_rank": player_rank,
            "total_promotions": len(all_promotions),
            "hostile_count": len(self.get_hostile_rivals()),
        }

    # ==================== NEW RIVAL EMERGENCE ====================

    def maybe_create_new_rival(self, current_week: int, player_size: RivalSize) -> Optional[RivalPromotion]:
        """Occasionally create new rivals as the industry evolves"""
        if len(self.rivals) >= 12:
            return None

        # 5% chance per week of new rival emerging
        if random.random() > 0.05:
            return None

        # Pick a size near player's level
        sizes = list(RivalSize)
        player_idx = sizes.index(player_size)
        size_options = [
            sizes[max(0, player_idx - 1)],
            player_size,
            sizes[min(len(sizes) - 1, player_idx + 1)],
        ]
        size = random.choice(size_options)

        rival = self.generate_rival(size)
        if rival:
            self.rivals.append(rival)
            return rival

        return None

    # ==================== SERIALIZATION ====================

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
        for rd in data.get("rivals", []):
            try:
                manager.rivals.append(RivalPromotion.from_dict(rd))
            except Exception:
                pass
        return manager
