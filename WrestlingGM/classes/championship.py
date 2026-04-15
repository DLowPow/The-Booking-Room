"""
Championship System - Create and manage titles
Tournaments and Accolades
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import random


class ChampionshipLevel(Enum):
    WORLD = "World Championship"
    SINGLES = "Singles Championship"
    TAG = "Tag Team Championship"
    TROPHY = "Trophy/Special"


class ChampionshipGender(Enum):
    MENS = "Men's"
    WOMENS = "Women's"
    INTERGENDER = "Intergender"


class ChampionshipRule(Enum):
    STANDARD = "Standard"
    HARDCORE = "Hardcore Only"
    TWENTY_FOUR_SEVEN = "24/7 Defense"
    TOURNAMENT_ONLY = "Tournament Only"
    OPEN_CHALLENGE = "Open Challenge"
    IRON_MAN = "Iron Man Only"
    SUBMISSION = "Submission Only"
    LADDER = "Ladder Match Only"


class TournamentFormat(Enum):
    SINGLE_ELIMINATION = "Single Elimination"
    DOUBLE_ELIMINATION = "Double Elimination"
    ROUND_ROBIN = "Round Robin"
    GAUNTLET = "Gauntlet"
    BATTLE_ROYAL = "Battle Royal"
    KING_OF_THE_RING = "King/Queen of the Ring"


class TournamentStatus(Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class AccoladeType(Enum):
    KING_OF_THE_RING = "King of the Ring"
    QUEEN_OF_THE_RING = "Queen of the Ring"
    WRESTLER_OF_THE_YEAR = "Wrestler of the Year"
    MATCH_OF_THE_YEAR = "Match of the Year"
    TAG_TEAM_OF_THE_YEAR = "Tag Team of the Year"
    ROOKIE_OF_THE_YEAR = "Rookie of the Year"
    MOST_IMPROVED = "Most Improved"
    BEST_PROMO = "Best on the Mic"
    IRON_MAN_AWARD = "Iron Man Award"
    MOST_POPULAR = "Most Popular"
    MOST_HATED = "Most Hated"
    BREAKOUT_STAR = "Breakout Star"


# ==================== CHAMPIONSHIP COSTS ====================

CHAMPIONSHIP_COSTS = {
    ChampionshipLevel.WORLD: {
        "creation_cost": 25000,
        "weekly_maintenance": 500,
        "prestige_requirement": 30,
        "level_requirement": 5,
        "description": "The top prize in your promotion. Main event level.",
    },
    ChampionshipLevel.SINGLES: {
        "creation_cost": 15000,
        "weekly_maintenance": 300,
        "prestige_requirement": 20,
        "level_requirement": 5,
        "description": "A secondary singles title for midcard talent.",
    },
    ChampionshipLevel.TAG: {
        "creation_cost": 12000,
        "weekly_maintenance": 250,
        "prestige_requirement": 15,
        "level_requirement": 10,
        "description": "A championship for tag teams.",
    },
    ChampionshipLevel.TROPHY: {
        "creation_cost": 5000,
        "weekly_maintenance": 100,
        "prestige_requirement": 10,
        "level_requirement": 5,
        "description": "A special trophy or cup awarded periodically.",
    },
}


# ==================== SLOT COSTS ====================

# Cost to unlock each championship slot
SLOT_COSTS = {
    1: 0,        # First slot is free at level 5
    2: 10000,
    3: 25000,
    4: 50000,
    5: 75000,
    6: 100000,
    7: 150000,
    8: 200000,
    9: 300000,
    10: 500000,
}


# ==================== CHAMPIONSHIP CLASS ====================

@dataclass
class TitleReign:
    """Record of a single title reign"""
    champion: str
    date_won: str
    date_lost: str = ""
    defenses: int = 0
    days_held: int = 0
    lost_to: str = ""
    how_won: str = ""
    how_lost: str = ""


@dataclass
class Championship:
    """A championship title"""
    
    # Identity
    id: str
    name: str
    level: ChampionshipLevel
    gender: ChampionshipGender
    rules: ChampionshipRule = ChampionshipRule.STANDARD
    
    # Status
    is_active: bool = True
    current_champion: str = ""
    current_champion_tag_partner: str = ""  # For tag titles
    
    # Prestige
    prestige: int = 50
    lineage_prestige: int = 0  # Built up over time
    
    # Current reign
    current_defenses: int = 0
    current_reign_weeks: int = 0
    
    # History
    title_history: List[TitleReign] = field(default_factory=list)
    total_reigns: int = 0
    
    # Costs
    creation_cost: int = 15000
    weekly_maintenance: int = 300
    
    # Stats
    longest_reign_weeks: int = 0
    longest_reign_holder: str = ""
    most_defenses: int = 0
    most_defenses_holder: str = ""
    
    # Custom rules
    is_tag_title: bool = False
    custom_match_type: str = ""  # If rules require specific match type
    
    def award_title(
        self,
        champion_name: str,
        date: str = "",
        how_won: str = "Defeated previous champion",
        tag_partner: str = "",
    ) -> Optional[TitleReign]:
        """Award the title to a new champion"""
        previous_reign = None
        
        # Record previous reign if there was one
        if self.current_champion:
            previous_reign = TitleReign(
                champion=self.current_champion,
                date_won=f"Reign #{self.total_reigns}",
                date_lost=date,
                defenses=self.current_defenses,
                days_held=self.current_reign_weeks * 7,
                lost_to=champion_name,
                how_lost="Lost championship",
            )
            self.title_history.append(previous_reign)
            
            # Check records
            if self.current_reign_weeks > self.longest_reign_weeks:
                self.longest_reign_weeks = self.current_reign_weeks
                self.longest_reign_holder = self.current_champion
            
            if self.current_defenses > self.most_defenses:
                self.most_defenses = self.current_defenses
                self.most_defenses_holder = self.current_champion
        
        # Set new champion
        self.current_champion = champion_name
        self.current_champion_tag_partner = tag_partner
        self.current_defenses = 0
        self.current_reign_weeks = 0
        self.total_reigns += 1
        
        # Prestige boost for title change
        self.prestige = min(100, self.prestige + 2)
        self.lineage_prestige += 1
        
        return previous_reign
    
    def record_defense(self, against: str = ""):
        """Record a successful title defense"""
        self.current_defenses += 1
        self.prestige = min(100, self.prestige + 1)
        self.lineage_prestige += 1
    
    def vacate(self, reason: str = ""):
        """Vacate the championship"""
        if self.current_champion:
            reign = TitleReign(
                champion=self.current_champion,
                date_won=f"Reign #{self.total_reigns}",
                date_lost="Vacated",
                defenses=self.current_defenses,
                days_held=self.current_reign_weeks * 7,
                lost_to="VACATED",
                how_lost=reason if reason else "Title vacated",
            )
            self.title_history.append(reign)
        
        self.current_champion = ""
        self.current_champion_tag_partner = ""
        self.current_defenses = 0
        self.current_reign_weeks = 0
        self.prestige = max(1, self.prestige - 10)
    
    def weekly_update(self):
        """Process weekly updates"""
        if self.current_champion:
            self.current_reign_weeks += 1
        
        # Titles without champions lose prestige
        if not self.current_champion:
            self.prestige = max(1, self.prestige - 1)
        
        # Inactive titles (no defenses in a while) lose prestige
        if self.current_champion and self.current_reign_weeks > 8 and self.current_defenses == 0:
            self.prestige = max(1, self.prestige - 1)
    
    def get_match_type_requirement(self) -> Optional[str]:
        """Get required match type based on rules"""
        rule_match_types = {
            ChampionshipRule.HARDCORE: "Deathmatch",
            ChampionshipRule.IRON_MAN: "Iron Man",
            ChampionshipRule.SUBMISSION: "Submission",
            ChampionshipRule.LADDER: "Ladder",
        }
        return rule_match_types.get(self.rules)
    
    def can_wrestler_compete(self, wrestler_gender: str) -> bool:
        """Check if a wrestler can compete for this title based on gender"""
        if self.gender == ChampionshipGender.INTERGENDER:
            return True
        elif self.gender == ChampionshipGender.MENS:
            return wrestler_gender in ["Male", "Intergender"]
        elif self.gender == ChampionshipGender.WOMENS:
            return wrestler_gender in ["Female", "Intergender"]
        return True
    
    def get_champion_display(self) -> str:
        """Get display string for current champion"""
        if not self.current_champion:
            return "VACANT"
        
        if self.is_tag_title and self.current_champion_tag_partner:
            return f"{self.current_champion} & {self.current_champion_tag_partner}"
        
        return self.current_champion
    
    def get_reign_info(self) -> Dict:
        """Get current reign info"""
        return {
            "champion": self.get_champion_display(),
            "defenses": self.current_defenses,
            "weeks": self.current_reign_weeks,
            "is_vacant": not self.current_champion,
        }
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "gender": self.gender.value,
            "rules": self.rules.value,
            "is_active": self.is_active,
            "current_champion": self.current_champion,
            "current_champion_tag_partner": self.current_champion_tag_partner,
            "prestige": self.prestige,
            "lineage_prestige": self.lineage_prestige,
            "current_defenses": self.current_defenses,
            "current_reign_weeks": self.current_reign_weeks,
            "title_history": [
                {
                    "champion": r.champion,
                    "date_won": r.date_won,
                    "date_lost": r.date_lost,
                    "defenses": r.defenses,
                    "days_held": r.days_held,
                    "lost_to": r.lost_to,
                    "how_won": r.how_won,
                    "how_lost": r.how_lost,
                }
                for r in self.title_history
            ],
            "total_reigns": self.total_reigns,
            "creation_cost": self.creation_cost,
            "weekly_maintenance": self.weekly_maintenance,
            "longest_reign_weeks": self.longest_reign_weeks,
            "longest_reign_holder": self.longest_reign_holder,
            "most_defenses": self.most_defenses,
            "most_defenses_holder": self.most_defenses_holder,
            "is_tag_title": self.is_tag_title,
            "custom_match_type": self.custom_match_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Championship":
        champ = cls(
            id=data["id"],
            name=data["name"],
            level=ChampionshipLevel(data["level"]),
            gender=ChampionshipGender(data["gender"]),
            rules=ChampionshipRule(data.get("rules", "Standard")),
            is_active=data.get("is_active", True),
            current_champion=data.get("current_champion", ""),
            current_champion_tag_partner=data.get("current_champion_tag_partner", ""),
            prestige=data.get("prestige", 50),
            lineage_prestige=data.get("lineage_prestige", 0),
            current_defenses=data.get("current_defenses", 0),
            current_reign_weeks=data.get("current_reign_weeks", 0),
            total_reigns=data.get("total_reigns", 0),
            creation_cost=data.get("creation_cost", 15000),
            weekly_maintenance=data.get("weekly_maintenance", 300),
            longest_reign_weeks=data.get("longest_reign_weeks", 0),
            longest_reign_holder=data.get("longest_reign_holder", ""),
            most_defenses=data.get("most_defenses", 0),
            most_defenses_holder=data.get("most_defenses_holder", ""),
            is_tag_title=data.get("is_tag_title", False),
            custom_match_type=data.get("custom_match_type", ""),
        )
        
        # Restore history
        for reign_data in data.get("title_history", []):
            champ.title_history.append(TitleReign(
                champion=reign_data["champion"],
                date_won=reign_data.get("date_won", ""),
                date_lost=reign_data.get("date_lost", ""),
                defenses=reign_data.get("defenses", 0),
                days_held=reign_data.get("days_held", 0),
                lost_to=reign_data.get("lost_to", ""),
                how_won=reign_data.get("how_won", ""),
                how_lost=reign_data.get("how_lost", ""),
            ))
        
        return champ


# ==================== TOURNAMENT CLASS ====================

@dataclass
class TournamentMatch:
    """A single match in a tournament"""
    round_number: int
    match_number: int
    wrestler1: str = ""
    wrestler2: str = ""
    winner: str = ""
    match_rating: float = 0.0
    is_completed: bool = False


@dataclass 
class Tournament:
    """A tournament event"""
    
    id: str
    name: str
    tournament_format: TournamentFormat
    status: TournamentStatus = TournamentStatus.PLANNING
    
    # Settings
    size: int = 8  # Number of participants
    gender: ChampionshipGender = ChampionshipGender.INTERGENDER
    
    # For title
    for_championship: str = ""  # Championship ID if for a title
    
    # Participants
    participants: List[str] = field(default_factory=list)
    
    # Bracket/Matches
    matches: List[TournamentMatch] = field(default_factory=list)
    current_round: int = 1
    
    # Results
    winner: str = ""
    runner_up: str = ""
    
    # Rewards
    xp_reward: int = 200
    prestige_reward: int = 5
    winner_momentum_bonus: int = 20
    winner_popularity_bonus: int = 10
    
    # Accolade
    grants_accolade: str = ""  # Accolade type if applicable
    
    # Timing
    week_started: int = 0
    week_completed: int = 0
    
    def add_participant(self, wrestler_name: str) -> bool:
        """Add a participant to the tournament"""
        if len(self.participants) >= self.size:
            return False
        if wrestler_name in self.participants:
            return False
        self.participants.append(wrestler_name)
        return True
    
    def remove_participant(self, wrestler_name: str) -> bool:
        """Remove a participant"""
        if wrestler_name in self.participants:
            self.participants.remove(wrestler_name)
            return True
        return False
    
    def is_full(self) -> bool:
        """Check if tournament is full"""
        return len(self.participants) >= self.size
    
    def generate_bracket(self):
        """Generate the tournament bracket"""
        if not self.is_full():
            return
        
        self.status = TournamentStatus.IN_PROGRESS
        self.matches = []
        
        if self.tournament_format == TournamentFormat.SINGLE_ELIMINATION:
            self._generate_single_elimination()
        elif self.tournament_format == TournamentFormat.GAUNTLET:
            self._generate_gauntlet()
        elif self.tournament_format == TournamentFormat.ROUND_ROBIN:
            self._generate_round_robin()
        elif self.tournament_format == TournamentFormat.BATTLE_ROYAL:
            self._generate_battle_royal()
    
    def _generate_single_elimination(self):
        """Generate single elimination bracket"""
        shuffled = self.participants.copy()
        random.shuffle(shuffled)
        
        match_num = 1
        for i in range(0, len(shuffled), 2):
            if i + 1 < len(shuffled):
                self.matches.append(TournamentMatch(
                    round_number=1,
                    match_number=match_num,
                    wrestler1=shuffled[i],
                    wrestler2=shuffled[i + 1],
                ))
                match_num += 1
    
    def _generate_gauntlet(self):
        """Generate gauntlet order"""
        shuffled = self.participants.copy()
        random.shuffle(shuffled)
        
        for i in range(len(shuffled) - 1):
            self.matches.append(TournamentMatch(
                round_number=i + 1,
                match_number=1,
                wrestler1=shuffled[i] if i == 0 else "",  # Winner of previous
                wrestler2=shuffled[i + 1],
            ))
    
    def _generate_round_robin(self):
        """Generate round robin schedule"""
        match_num = 1
        round_num = 1
        
        for i in range(len(self.participants)):
            for j in range(i + 1, len(self.participants)):
                self.matches.append(TournamentMatch(
                    round_number=round_num,
                    match_number=match_num,
                    wrestler1=self.participants[i],
                    wrestler2=self.participants[j],
                ))
                match_num += 1
                if match_num > 3:
                    match_num = 1
                    round_num += 1
    
    def _generate_battle_royal(self):
        """Generate battle royal (one match)"""
        self.matches.append(TournamentMatch(
            round_number=1,
            match_number=1,
            wrestler1="Battle Royal",
            wrestler2=f"{len(self.participants)} participants",
        ))
    
    def get_current_round_matches(self) -> List[TournamentMatch]:
        """Get matches for the current round"""
        return [m for m in self.matches if m.round_number == self.current_round and not m.is_completed]
    
    def record_match_result(self, match_number: int, winner: str, rating: float = 3.0):
        """Record a match result"""
        for match in self.matches:
            if match.match_number == match_number and match.round_number == self.current_round:
                match.winner = winner
                match.match_rating = rating
                match.is_completed = True
                break
        
        # Check if round is complete
        round_matches = [m for m in self.matches if m.round_number == self.current_round]
        if all(m.is_completed for m in round_matches):
            self._advance_round()
    
    def _advance_round(self):
        """Advance to next round"""
        if self.tournament_format == TournamentFormat.SINGLE_ELIMINATION:
            # Get winners of current round
            winners = [m.winner for m in self.matches if m.round_number == self.current_round]
            
            if len(winners) <= 1:
                # Tournament is over
                self.winner = winners[0] if winners else ""
                self.status = TournamentStatus.COMPLETED
                return
            
            # Create next round matches
            self.current_round += 1
            match_num = 1
            for i in range(0, len(winners), 2):
                if i + 1 < len(winners):
                    self.matches.append(TournamentMatch(
                        round_number=self.current_round,
                        match_number=match_num,
                        wrestler1=winners[i],
                        wrestler2=winners[i + 1],
                    ))
                    match_num += 1
                else:
                    # Bye
                    self.matches.append(TournamentMatch(
                        round_number=self.current_round,
                        match_number=match_num,
                        wrestler1=winners[i],
                        wrestler2="BYE",
                        winner=winners[i],
                        is_completed=True,
                    ))
                    match_num += 1
    
    def is_complete(self) -> bool:
        """Check if tournament is complete"""
        return self.status == TournamentStatus.COMPLETED
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tournament_format": self.tournament_format.value,
            "status": self.status.value,
            "size": self.size,
            "gender": self.gender.value,
            "for_championship": self.for_championship,
            "participants": self.participants,
            "matches": [
                {
                    "round_number": m.round_number,
                    "match_number": m.match_number,
                    "wrestler1": m.wrestler1,
                    "wrestler2": m.wrestler2,
                    "winner": m.winner,
                    "match_rating": m.match_rating,
                    "is_completed": m.is_completed,
                }
                for m in self.matches
            ],
            "current_round": self.current_round,
            "winner": self.winner,
            "runner_up": self.runner_up,
            "xp_reward": self.xp_reward,
            "prestige_reward": self.prestige_reward,
            "grants_accolade": self.grants_accolade,
            "week_started": self.week_started,
            "week_completed": self.week_completed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Tournament":
        tourney = cls(
            id=data["id"],
            name=data["name"],
            tournament_format=TournamentFormat(data["tournament_format"]),
            status=TournamentStatus(data.get("status", "Planning")),
            size=data.get("size", 8),
            gender=ChampionshipGender(data.get("gender", "Intergender")),
            for_championship=data.get("for_championship", ""),
            participants=data.get("participants", []),
            current_round=data.get("current_round", 1),
            winner=data.get("winner", ""),
            runner_up=data.get("runner_up", ""),
            xp_reward=data.get("xp_reward", 200),
            prestige_reward=data.get("prestige_reward", 5),
            grants_accolade=data.get("grants_accolade", ""),
            week_started=data.get("week_started", 0),
            week_completed=data.get("week_completed", 0),
        )
        
        for match_data in data.get("matches", []):
            tourney.matches.append(TournamentMatch(
                round_number=match_data["round_number"],
                match_number=match_data["match_number"],
                wrestler1=match_data.get("wrestler1", ""),
                wrestler2=match_data.get("wrestler2", ""),
                winner=match_data.get("winner", ""),
                match_rating=match_data.get("match_rating", 0),
                is_completed=match_data.get("is_completed", False),
            ))
        
        return tourney


# ==================== ACCOLADE CLASS ====================

@dataclass
class Accolade:
    """A non-title accolade/award"""
    id: str
    name: str
    accolade_type: AccoladeType
    description: str = ""
    
    # History
    history: List[Dict] = field(default_factory=list)
    current_holder: str = ""
    
    # When awarded
    frequency: str = "annual"  # "annual", "tournament", "custom"
    last_awarded_year: int = 0
    
    def award(self, wrestler_name: str, year: int, week: int = 0, details: str = ""):
        """Award the accolade to a wrestler"""
        self.history.append({
            "winner": wrestler_name,
            "year": year,
            "week": week,
            "details": details,
        })
        self.current_holder = wrestler_name
        self.last_awarded_year = year
    
    def get_winners(self) -> List[Dict]:
        """Get all winners"""
        return self.history
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "accolade_type": self.accolade_type.value,
            "description": self.description,
            "history": self.history,
            "current_holder": self.current_holder,
            "frequency": self.frequency,
            "last_awarded_year": self.last_awarded_year,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Accolade":
        acc = cls(
            id=data["id"],
            name=data["name"],
            accolade_type=AccoladeType(data["accolade_type"]),
            description=data.get("description", ""),
            frequency=data.get("frequency", "annual"),
            last_awarded_year=data.get("last_awarded_year", 0),
        )
        acc.history = data.get("history", [])
        acc.current_holder = data.get("current_holder", "")
        return acc


# ==================== CHAMPIONSHIP MANAGER ====================

class ChampionshipManager:
    """Manages all championships, tournaments, and accolades"""
    
    def __init__(self):
        self.championships: List[Championship] = []
        self.tournaments: List[Tournament] = []
        self.accolades: List[Accolade] = []
        self.unlocked_slots: int = 0
        self.max_slots: int = 10
    
    def get_slot_cost(self, slot_number: int) -> int:
        """Get cost to unlock a specific slot"""
        return SLOT_COSTS.get(slot_number, 500000)
    
    def get_next_slot_cost(self) -> int:
        """Get cost for the next slot"""
        next_slot = self.unlocked_slots + 1
        return self.get_slot_cost(next_slot)
    
    def unlock_slot(self, budget: int) -> tuple:
        """
        Unlock next championship slot.
        Returns (success, cost, new_total_slots)
        """
        if self.unlocked_slots >= self.max_slots:
            return False, 0, self.unlocked_slots
        
        cost = self.get_next_slot_cost()
        if budget < cost:
            return False, cost, self.unlocked_slots
        
        self.unlocked_slots += 1
        return True, cost, self.unlocked_slots
    
    def can_create_championship(self, level: int, prestige: int) -> tuple:
        """Check if a new championship can be created"""
        if len(self.championships) >= self.unlocked_slots:
            return False, f"No available slots ({len(self.championships)}/{self.unlocked_slots}). Unlock more slots."
        
        return True, "Can create championship"
    
    def create_championship(
        self,
        name: str,
        level: ChampionshipLevel,
        gender: ChampionshipGender,
        rules: ChampionshipRule = ChampionshipRule.STANDARD,
    ) -> Optional[Championship]:
        """Create a new championship"""
        if len(self.championships) >= self.unlocked_slots:
            return None
        
        costs = CHAMPIONSHIP_COSTS.get(level, {})
        
        champ_id = f"title_{name.lower().replace(' ', '_')}_{len(self.championships)}"
        
        championship = Championship(
            id=champ_id,
            name=name,
            level=level,
            gender=gender,
            rules=rules,
            is_tag_title=(level == ChampionshipLevel.TAG),
            creation_cost=costs.get("creation_cost", 15000),
            weekly_maintenance=costs.get("weekly_maintenance", 300),
        )
        
        # Set initial prestige based on level
        prestige_starts = {
            ChampionshipLevel.WORLD: 60,
            ChampionshipLevel.SINGLES: 45,
            ChampionshipLevel.TAG: 40,
            ChampionshipLevel.TROPHY: 30,
        }
        championship.prestige = prestige_starts.get(level, 40)
        
        self.championships.append(championship)
        return championship
    
    def get_championship(self, championship_id: str) -> Optional[Championship]:
        """Get a championship by ID"""
        for c in self.championships:
            if c.id == championship_id:
                return c
        return None
    
    def get_championship_by_name(self, name: str) -> Optional[Championship]:
        """Get a championship by name"""
        for c in self.championships:
            if c.name == name:
                return c
        return None
    
    def retire_championship(self, championship_id: str):
        """Retire/deactivate a championship"""
        champ = self.get_championship(championship_id)
        if champ:
            champ.is_active = False
            if champ.current_champion:
                champ.vacate("Championship retired")
    
    def get_active_championships(self) -> List[Championship]:
        """Get all active championships"""
        return [c for c in self.championships if c.is_active]
    
    def get_total_maintenance_cost(self) -> int:
        """Get total weekly maintenance cost for all titles"""
        return sum(c.weekly_maintenance for c in self.championships if c.is_active)
    
    def weekly_update(self):
        """Process weekly updates for all championships"""
        for championship in self.championships:
            if championship.is_active:
                championship.weekly_update()
    
    # ==================== TOURNAMENTS ====================
    
    def create_tournament(
        self,
        name: str,
        tournament_format: TournamentFormat,
        size: int = 8,
        gender: ChampionshipGender = ChampionshipGender.INTERGENDER,
        for_championship: str = "",
        grants_accolade: str = "",
        current_week: int = 0,
    ) -> Tournament:
        """Create a new tournament"""
        tourney_id = f"tourney_{name.lower().replace(' ', '_')}_{current_week}"
        
        tournament = Tournament(
            id=tourney_id,
            name=name,
            tournament_format=tournament_format,
            size=size,
            gender=gender,
            for_championship=for_championship,
            grants_accolade=grants_accolade,
            week_started=current_week,
        )
        
        self.tournaments.append(tournament)
        return tournament
    
    def get_active_tournaments(self) -> List[Tournament]:
        """Get tournaments in progress"""
        return [t for t in self.tournaments if t.status == TournamentStatus.IN_PROGRESS]
    
    def get_planning_tournaments(self) -> List[Tournament]:
        """Get tournaments being planned"""
        return [t for t in self.tournaments if t.status == TournamentStatus.PLANNING]
    
    # ==================== ACCOLADES ====================
    
    def create_accolade(
        self,
        name: str,
        accolade_type: AccoladeType,
        description: str = "",
        frequency: str = "annual",
    ) -> Accolade:
        """Create a new accolade"""
        acc_id = f"accolade_{name.lower().replace(' ', '_')}"
        
        accolade = Accolade(
            id=acc_id,
            name=name,
            accolade_type=accolade_type,
            description=description,
            frequency=frequency,
        )
        
        self.accolades.append(accolade)
        return accolade
    
    def setup_default_accolades(self):
        """Create default accolades"""
        defaults = [
            ("King of the Ring", AccoladeType.KING_OF_THE_RING, "Winner of the King of the Ring tournament", "tournament"),
            ("Queen of the Ring", AccoladeType.QUEEN_OF_THE_RING, "Winner of the Queen of the Ring tournament", "tournament"),
            ("Wrestler of the Year", AccoladeType.WRESTLER_OF_THE_YEAR, "Best overall performer of the year", "annual"),
            ("Match of the Year", AccoladeType.MATCH_OF_THE_YEAR, "Best match of the year", "annual"),
            ("Rookie of the Year", AccoladeType.ROOKIE_OF_THE_YEAR, "Best newcomer of the year", "annual"),
            ("Most Popular", AccoladeType.MOST_POPULAR, "Fan favorite of the year", "annual"),
        ]
        
        for name, acc_type, desc, freq in defaults:
            if not any(a.name == name for a in self.accolades):
                self.create_accolade(name, acc_type, desc, freq)
    
    def get_accolade(self, accolade_id: str) -> Optional[Accolade]:
        """Get an accolade by ID"""
        for a in self.accolades:
            if a.id == accolade_id:
                return a
        return None
    
    # ==================== SAVE/LOAD ====================
    
    def to_dict(self) -> dict:
        return {
            "championships": [c.to_dict() for c in self.championships],
            "tournaments": [t.to_dict() for t in self.tournaments],
            "accolades": [a.to_dict() for a in self.accolades],
            "unlocked_slots": self.unlocked_slots,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChampionshipManager":
        manager = cls()
        manager.unlocked_slots = data.get("unlocked_slots", 0)
        
        for c_data in data.get("championships", []):
            manager.championships.append(Championship.from_dict(c_data))
        
        for t_data in data.get("tournaments", []):
            manager.tournaments.append(Tournament.from_dict(t_data))
        
        for a_data in data.get("accolades", []):
            manager.accolades.append(Accolade.from_dict(a_data))
        
        return manager