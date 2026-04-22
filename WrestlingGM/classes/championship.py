"""
Championship System - Create and manage titles, tournaments, and accolades
With match type restrictions and tag team support
"""

import re
import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


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
    SINGLE_ELIMINATION_8 = "Single Elimination (8)"
    SINGLE_ELIMINATION_16 = "Single Elimination (16)"


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


# ==================== COSTS ====================

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
        "description": "A championship for tag teams (2 champions).",
    },
    ChampionshipLevel.TROPHY: {
        "creation_cost": 5000,
        "weekly_maintenance": 100,
        "prestige_requirement": 10,
        "level_requirement": 5,
        "description": "A special trophy or cup awarded periodically.",
    },
}

SLOT_COSTS = {
    1: 0,
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


# ==================== TITLE REIGN ====================

@dataclass
class TitleReign:
    champion: str
    date_won: str
    date_lost: str = ""
    defenses: int = 0
    days_held: int = 0
    lost_to: str = ""
    how_won: str = ""
    how_lost: str = ""
    tag_partner: str = ""


# ==================== CHAMPIONSHIP ====================

@dataclass
class Championship:
    id: str
    name: str
    level: ChampionshipLevel
    gender: ChampionshipGender
    rules: ChampionshipRule = ChampionshipRule.STANDARD

    is_active: bool = True
    current_champion: str = ""
    current_champion_tag_partner: str = ""

    prestige: int = 50
    lineage_prestige: int = 0

    current_defenses: int = 0
    current_reign_weeks: int = 0

    title_history: List[TitleReign] = field(default_factory=list)
    total_reigns: int = 0

    creation_cost: int = 15000
    weekly_maintenance: int = 300

    longest_reign_weeks: int = 0
    longest_reign_holder: str = ""
    most_defenses: int = 0
    most_defenses_holder: str = ""

    is_tag_title: bool = False
    custom_match_type: str = ""

    def award_title(self, champion_name: str, date: str = "", how_won: str = "Defeated previous champion", tag_partner: str = "") -> Optional[TitleReign]:
        """Award the title to a new champion (or champions for tag titles)"""
        previous_reign = None
        if self.current_champion:
            previous_reign = TitleReign(
                champion=self.current_champion,
                date_won=f"Reign #{self.total_reigns}",
                date_lost=date,
                defenses=self.current_defenses,
                days_held=self.current_reign_weeks * 7,
                lost_to=champion_name,
                how_lost="Lost championship",
                tag_partner=self.current_champion_tag_partner,
            )
            self.title_history.append(previous_reign)
            if self.current_reign_weeks > self.longest_reign_weeks:
                self.longest_reign_weeks = self.current_reign_weeks
                self.longest_reign_holder = self.get_champion_display()
            if self.current_defenses > self.most_defenses:
                self.most_defenses = self.current_defenses
                self.most_defenses_holder = self.get_champion_display()

        self.current_champion = champion_name
        self.current_champion_tag_partner = tag_partner
        self.current_defenses = 0
        self.current_reign_weeks = 0
        self.total_reigns += 1
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
                tag_partner=self.current_champion_tag_partner,
            )
            self.title_history.append(reign)
        self.current_champion = ""
        self.current_champion_tag_partner = ""
        self.current_defenses = 0
        self.current_reign_weeks = 0
        self.prestige = max(1, self.prestige - 10)

    def weekly_update(self):
        """Process weekly title updates"""
        if self.current_champion:
            self.current_reign_weeks += 1
        if not self.current_champion:
            self.prestige = max(1, self.prestige - 1)
        if self.current_champion and self.current_reign_weeks > 8 and self.current_defenses == 0:
            self.prestige = max(1, self.prestige - 1)

    def can_be_defended_in(self, match_type: str, num_participants: int = 2) -> tuple:
        """Check if this championship can be defended in this match type"""
        # Tag title check
        is_tag = self.is_tag_title or self.level == ChampionshipLevel.TAG
        tag_match_types = ['Tag Team', 'Intergender Tag', '6-Man Tag', 'War Games']
        
        if is_tag and match_type not in tag_match_types:
            return False, "Tag titles can only be defended in tag matches"
        
        if not is_tag and match_type in tag_match_types:
            return False, "Singles titles cannot be defended in tag matches"
        
        # Rule-based restrictions
        if self.rules == ChampionshipRule.HARDCORE:
            allowed = ['Hardcore', 'Deathmatch', 'Tables', 'TLC', 'Last Man Standing', 'Inferno', 'Buried Alive']
            if match_type not in allowed:
                return False, "This title requires Hardcore/Deathmatch type matches"
        elif self.rules == ChampionshipRule.IRON_MAN:
            if match_type != 'Iron Man':
                return False, "This title can only be defended in Iron Man matches"
        elif self.rules == ChampionshipRule.SUBMISSION:
            if match_type not in ['Submission', 'I Quit']:
                return False, "This title requires Submission/I Quit matches"
        elif self.rules == ChampionshipRule.LADDER:
            if match_type not in ['Ladder', 'TLC']:
                return False, "This title requires Ladder matches"
        elif self.rules == ChampionshipRule.TOURNAMENT_ONLY:
            return False, "This title can only change hands in tournaments"
        
        return True, "Can be defended"

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
        """Get display string for current champion(s)"""
        if not self.current_champion:
            return "VACANT"
        if (self.is_tag_title or self.level == ChampionshipLevel.TAG) and self.current_champion_tag_partner:
            return f"{self.current_champion} & {self.current_champion_tag_partner}"
        return self.current_champion

    def get_reign_info(self) -> Dict:
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
                    "tag_partner": r.tag_partner,
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
                tag_partner=reign_data.get("tag_partner", ""),
            ))
        return champ


# ==================== TOURNAMENT ====================

@dataclass
class Tournament:
    id: str
    name: str
    tournament_format: TournamentFormat
    status: TournamentStatus = TournamentStatus.PLANNING

    size: int = 8
    gender: ChampionshipGender = ChampionshipGender.INTERGENDER
    is_ppv: bool = False

    for_championship: str = ""
    participants: List[str] = field(default_factory=list)

    rounds: Dict = field(default_factory=dict)
    current_round: int = 0
    total_rounds: int = 3

    winner: str = ""
    runner_up: str = ""

    xp_reward: int = 200
    prestige_reward: int = 5
    winner_momentum_bonus: int = 20
    winner_popularity_bonus: int = 10

    grants_accolade: str = ""

    week_started: int = 0
    week_completed: int = 0
    venue_id: str = ""

    def setup_bracket(self) -> bool:
        if len(self.participants) < self.size:
            return False

        shuffled = self.participants.copy()
        random.shuffle(shuffled)

        if self.size == 8:
            self.total_rounds = 3
            self.rounds = {
                1: {
                    "name": "Quarter Finals",
                    "matches": [
                        {"match": 1, "wrestler1": shuffled[0], "wrestler2": shuffled[1], "winner": "", "rating": 0},
                        {"match": 2, "wrestler1": shuffled[2], "wrestler2": shuffled[3], "winner": "", "rating": 0},
                        {"match": 3, "wrestler1": shuffled[4], "wrestler2": shuffled[5], "winner": "", "rating": 0},
                        {"match": 4, "wrestler1": shuffled[6], "wrestler2": shuffled[7], "winner": "", "rating": 0},
                    ],
                    "completed": False,
                },
                2: {
                    "name": "Semi Finals",
                    "matches": [
                        {"match": 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0},
                        {"match": 2, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0},
                    ],
                    "completed": False,
                },
                3: {
                    "name": "Final",
                    "matches": [
                        {"match": 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0},
                    ],
                    "completed": False,
                },
            }
        elif self.size == 16:
            self.total_rounds = 4
            first_round_matches = []
            for i in range(0, 16, 2):
                first_round_matches.append({
                    "match": (i // 2) + 1,
                    "wrestler1": shuffled[i],
                    "wrestler2": shuffled[i + 1],
                    "winner": "", "rating": 0,
                })
            self.rounds = {
                1: {"name": "First Round", "matches": first_round_matches, "completed": False},
                2: {
                    "name": "Quarter Finals",
                    "matches": [{"match": i + 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0} for i in range(4)],
                    "completed": False,
                },
                3: {
                    "name": "Semi Finals",
                    "matches": [
                        {"match": 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0},
                        {"match": 2, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0},
                    ],
                    "completed": False,
                },
                4: {
                    "name": "Final",
                    "matches": [{"match": 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0}],
                    "completed": False,
                },
            }

        self.current_round = 1
        self.status = TournamentStatus.IN_PROGRESS
        return True

    def get_current_round_info(self) -> Dict:
        if self.current_round in self.rounds:
            return self.rounds[self.current_round]
        return {"name": "Unknown", "matches": [], "completed": True}

    def get_current_matches(self) -> List[Dict]:
        round_info = self.get_current_round_info()
        return [m for m in round_info.get("matches", []) if not m.get("winner")]

    def record_match_result(self, match_number: int, winner: str, rating: float):
        if self.current_round not in self.rounds:
            return
        round_data = self.rounds[self.current_round]
        for match in round_data["matches"]:
            if match["match"] == match_number:
                match["winner"] = winner
                match["rating"] = rating
                break
        all_done = all(m.get("winner") for m in round_data["matches"])
        if all_done:
            round_data["completed"] = True
            self._advance_to_next_round()

    def _advance_to_next_round(self):
        current_winners = [m["winner"] for m in self.rounds[self.current_round]["matches"]]
        next_round = self.current_round + 1

        if next_round > self.total_rounds:
            self.winner = current_winners[0] if current_winners else ""
            self.status = TournamentStatus.COMPLETED
            return

        if next_round in self.rounds:
            next_matches = self.rounds[next_round]["matches"]
            for i, match in enumerate(next_matches):
                w1_idx = i * 2
                w2_idx = (i * 2) + 1
                if w1_idx < len(current_winners):
                    match["wrestler1"] = current_winners[w1_idx]
                if w2_idx < len(current_winners):
                    match["wrestler2"] = current_winners[w2_idx]

        self.current_round = next_round

    def is_complete(self) -> bool:
        return self.status == TournamentStatus.COMPLETED

    def get_bracket_display(self) -> List[Dict]:
        display = []
        for round_num in sorted(self.rounds.keys()):
            round_data = self.rounds[round_num]
            display.append({
                "round": round_num,
                "name": round_data["name"],
                "matches": round_data["matches"],
                "completed": round_data["completed"],
                "is_current": round_num == self.current_round,
            })
        return display

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "tournament_format": self.tournament_format.value,
            "status": self.status.value, "size": self.size,
            "gender": self.gender.value, "is_ppv": self.is_ppv,
            "for_championship": self.for_championship,
            "participants": self.participants,
            "rounds": self.rounds, "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "winner": self.winner, "runner_up": self.runner_up,
            "xp_reward": self.xp_reward, "prestige_reward": self.prestige_reward,
            "grants_accolade": self.grants_accolade,
            "week_started": self.week_started, "week_completed": self.week_completed,
            "venue_id": self.venue_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tournament":
        tourney = cls(
            id=data["id"], name=data["name"],
            tournament_format=TournamentFormat(data["tournament_format"]),
            status=TournamentStatus(data.get("status", "Planning")),
            size=data.get("size", 8),
            gender=ChampionshipGender(data.get("gender", "Intergender")),
            is_ppv=data.get("is_ppv", False),
            for_championship=data.get("for_championship", ""),
            participants=data.get("participants", []),
            current_round=data.get("current_round", 0),
            total_rounds=data.get("total_rounds", 3),
            winner=data.get("winner", ""),
            runner_up=data.get("runner_up", ""),
            xp_reward=data.get("xp_reward", 200),
            prestige_reward=data.get("prestige_reward", 5),
            grants_accolade=data.get("grants_accolade", ""),
            week_started=data.get("week_started", 0),
            week_completed=data.get("week_completed", 0),
            venue_id=data.get("venue_id", ""),
        )
        tourney.rounds = {int(k): v for k, v in data.get("rounds", {}).items()}
        return tourney


# ==================== ACCOLADE ====================

@dataclass
class Accolade:
    id: str
    name: str
    accolade_type: AccoladeType
    description: str = ""

    history: List[Dict] = field(default_factory=list)
    current_holder: str = ""

    frequency: str = "annual"
    last_awarded_year: int = 0

    def award(self, wrestler_name: str, year: int, week: int = 0, details: str = ""):
        self.history.append({
            "winner": wrestler_name, "year": year, "week": week, "details": details,
        })
        self.current_holder = wrestler_name
        self.last_awarded_year = year

    def get_winners(self) -> List[Dict]:
        return self.history

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "accolade_type": self.accolade_type.value,
            "description": self.description, "history": self.history,
            "current_holder": self.current_holder,
            "frequency": self.frequency,
            "last_awarded_year": self.last_awarded_year,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Accolade":
        acc = cls(
            id=data["id"], name=data["name"],
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
    def __init__(self):
        self.championships: List[Championship] = []
        self.tournaments: List[Tournament] = []
        self.accolades: List[Accolade] = []
        self.unlocked_slots: int = 0
        self.max_slots: int = 10

    def get_slot_cost(self, slot_number: int) -> int:
        return SLOT_COSTS.get(slot_number, 500000)

    def get_next_slot_cost(self) -> int:
        return self.get_slot_cost(self.unlocked_slots + 1)

    def unlock_slot(self, budget: int) -> tuple:
        if self.unlocked_slots >= self.max_slots:
            return False, 0, self.unlocked_slots
        cost = self.get_next_slot_cost()
        if budget < cost:
            return False, cost, self.unlocked_slots
        self.unlocked_slots += 1
        return True, cost, self.unlocked_slots

    def can_create_championship(self, level: int, prestige: int) -> tuple:
        if len(self.championships) >= self.unlocked_slots:
            return False, f"No available slots ({len(self.championships)}/{self.unlocked_slots}). Unlock more slots."
        return True, "Can create championship"

    def create_championship(self, name: str, level: ChampionshipLevel, gender: ChampionshipGender, rules: ChampionshipRule = ChampionshipRule.STANDARD) -> Optional[Championship]:
        if len(self.championships) >= self.unlocked_slots:
            return None
        costs = CHAMPIONSHIP_COSTS.get(level, {})
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        champ_id = f"title_{safe_name}_{len(self.championships)}"
        championship = Championship(
            id=champ_id, name=name, level=level, gender=gender, rules=rules,
            is_tag_title=(level == ChampionshipLevel.TAG),
            creation_cost=costs.get("creation_cost", 15000),
            weekly_maintenance=costs.get("weekly_maintenance", 300),
        )
        prestige_starts = {
            ChampionshipLevel.WORLD: 60, ChampionshipLevel.SINGLES: 45,
            ChampionshipLevel.TAG: 40, ChampionshipLevel.TROPHY: 30,
        }
        championship.prestige = prestige_starts.get(level, 40)
        self.championships.append(championship)
        return championship

    def get_championship(self, championship_id: str) -> Optional[Championship]:
        for c in self.championships:
            if c.id == championship_id:
                return c
        return None

    def get_championship_by_name(self, name: str) -> Optional[Championship]:
        for c in self.championships:
            if c.name == name:
                return c
        return None

    def retire_championship(self, championship_id: str):
        champ = self.get_championship(championship_id)
        if champ:
            champ.is_active = False
            if champ.current_champion:
                champ.vacate("Championship retired")

    def get_active_championships(self) -> List[Championship]:
        return [c for c in self.championships if c.is_active]

    def get_total_maintenance_cost(self) -> int:
        return sum(c.weekly_maintenance for c in self.championships if c.is_active)

    def weekly_update(self):
        for championship in self.championships:
            if championship.is_active:
                championship.weekly_update()

    # Tournaments
    def create_tournament(self, name: str, tournament_format: TournamentFormat, size: int = 8, gender: ChampionshipGender = ChampionshipGender.INTERGENDER, for_championship: str = "", grants_accolade: str = "", current_week: int = 0) -> Tournament:
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        tourney_id = f"tourney_{safe_name}_{current_week}"
        tournament = Tournament(
            id=tourney_id, name=name, tournament_format=tournament_format,
            size=size, gender=gender, for_championship=for_championship,
            grants_accolade=grants_accolade, week_started=current_week,
        )
        self.tournaments.append(tournament)
        return tournament

    def get_tournament(self, tournament_id: str) -> Optional[Tournament]:
        for t in self.tournaments:
            if t.id == tournament_id:
                return t
        return None

    def get_active_tournaments(self) -> List[Tournament]:
        return [t for t in self.tournaments if t.status == TournamentStatus.IN_PROGRESS]

    def get_planning_tournaments(self) -> List[Tournament]:
        return [t for t in self.tournaments if t.status == TournamentStatus.PLANNING]

    def get_completed_tournaments(self) -> List[Tournament]:
        return [t for t in self.tournaments if t.status == TournamentStatus.COMPLETED]

    # Accolades
    def create_accolade(self, name: str, accolade_type: AccoladeType, description: str = "", frequency: str = "annual") -> Accolade:
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        acc_id = f"accolade_{safe_name}"
        accolade = Accolade(id=acc_id, name=name, accolade_type=accolade_type, description=description, frequency=frequency)
        self.accolades.append(accolade)
        return accolade

    def setup_default_accolades(self):
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
        for a in self.accolades:
            if a.id == accolade_id:
                return a
        return None

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
