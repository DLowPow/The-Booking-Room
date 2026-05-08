"""
Championship System - Create and manage titles, tournaments, accolades, trophies

Phases supported:
  Phase 1: Group system foundation (held_by_group_id field for faction-held titles)
  Phase 2: Trios championships, Tag/Trios Trophies, faction-held title display
  Phase 3: Auto-vacate logic (champion injured 3+ weeks → vacate)

Title structure:
  Singles: current_champion only
  Tag (2): current_champion + current_champion_tag_partner
  Trios (3): + current_champion_tag_partner_2
  Trophies: Permanent historical awards, never auto-vacate
"""
import re
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ==================== ENUMS ====================
class ChampionshipLevel(Enum):
    WORLD = "World Championship"
    SINGLES = "Singles Championship"
    TAG = "Tag Team Championship"
    TRIOS = "Trios Championship"            # NEW (Phase 2)
    TROPHY = "Trophy/Special"
    TAG_TROPHY = "Tag Team Trophy"          # NEW (Phase 2) - e.g. Dusty Classic
    TRIOS_TROPHY = "Trios Trophy"           # NEW (Phase 2) - e.g. King of Trios


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
        "prestige_requirement": 30,
        "level_requirement": 5,
        "description": "The top prize in your promotion. Main event level.",
    },
    ChampionshipLevel.SINGLES: {
        "creation_cost": 15000,
        "prestige_requirement": 20,
        "level_requirement": 5,
        "description": "A secondary singles title for midcard talent.",
    },
    ChampionshipLevel.TAG: {
        "creation_cost": 12000,
        "prestige_requirement": 15,
        "level_requirement": 10,
        "description": "A championship for tag teams (2 champions).",
    },
    ChampionshipLevel.TRIOS: {
        "creation_cost": 15000,
        "prestige_requirement": 20,
        "level_requirement": 15,
        "description": "A championship for trios (3 champions).",
    },
    ChampionshipLevel.TROPHY: {
        "creation_cost": 5000,
        "prestige_requirement": 10,
        "level_requirement": 5,
        "description": "A special trophy or cup awarded periodically. Permanent record.",
    },
    ChampionshipLevel.TAG_TROPHY: {
        "creation_cost": 8000,
        "prestige_requirement": 15,
        "level_requirement": 10,
        "description": "A tag team trophy (e.g. Dusty Classic). Tournament-style award.",
    },
    ChampionshipLevel.TRIOS_TROPHY: {
        "creation_cost": 10000,
        "prestige_requirement": 20,
        "level_requirement": 15,
        "description": "A trios trophy (e.g. King of Trios). Tournament-style award.",
    },
}

SLOT_COSTS = {
    1: 0, 2: 10000, 3: 25000, 4: 50000, 5: 75000,
    6: 100000, 7: 150000, 8: 200000, 9: 300000, 10: 500000,
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
    # Phase 2 additions
    tag_partner_2: str = ""                            # 3rd holder for trios
    team_members_snapshot: List[str] = field(default_factory=list)  # Full team at time of win
    held_by_group_name: str = ""                       # Group display name (historical)


# ==================== CHAMPIONSHIP ====================
@dataclass
class Championship:
    id: str
    name: str
    level: ChampionshipLevel
    gender: ChampionshipGender
    rules: ChampionshipRule = ChampionshipRule.STANDARD
    is_active: bool = True

    # Current champion(s)
    current_champion: str = ""
    current_champion_tag_partner: str = ""             # 2nd holder (tag/trios)
    current_champion_tag_partner_2: str = ""           # 3rd holder (trios only) — Phase 2

    # Prestige & history
    prestige: int = 50
    lineage_prestige: int = 0
    current_defenses: int = 0
    current_reign_weeks: int = 0
    title_history: List[TitleReign] = field(default_factory=list)
    total_reigns: int = 0

    # Costs
    creation_cost: int = 15000

    # Records
    longest_reign_weeks: int = 0
    longest_reign_holder: str = ""
    most_defenses: int = 0
    most_defenses_holder: str = ""

    # Type flags
    is_tag_title: bool = False
    is_trios_title: bool = False                       # Phase 2
    is_trophy: bool = False                            # Phase 2 (never auto-vacate)
    custom_match_type: str = ""

    # Phase 1: Group system integration
    held_by_group_id: str = ""                         # Links to a registered group/faction

    # Phase 3: Auto-vacate tracking
    champion_weeks_injured: int = 0                    # How long current champ has been hurt
    weeks_until_auto_vacate: int = 3                   # Threshold (configurable per-title)

    # ==================== AWARD / DEFEND / VACATE ====================
    def award_title(
        self,
        champion_name: str,
        date: str = "",
        how_won: str = "Defeated previous champion",
        tag_partner: str = "",
        tag_partner_2: str = "",
        held_by_group_id: str = "",
        held_by_group_name: str = "",
        team_members: Optional[List[str]] = None,
    ) -> Optional[TitleReign]:
        """
        Award the championship to a new champion (or team).

        Args:
            champion_name: Primary champion
            date: Date string for the win
            how_won: Description of how won
            tag_partner: 2nd holder (tag/trios titles)
            tag_partner_2: 3rd holder (trios only)
            held_by_group_id: Phase 2 — links to a group (faction-held title)
            held_by_group_name: Phase 2 — group display name for history snapshot
            team_members: Phase 2 — full member list snapshot
        """
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
                tag_partner_2=self.current_champion_tag_partner_2,
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
        self.current_champion_tag_partner_2 = tag_partner_2
        self.held_by_group_id = held_by_group_id
        self.current_defenses = 0
        self.current_reign_weeks = 0
        self.champion_weeks_injured = 0
        self.total_reigns += 1
        self.prestige = min(100, self.prestige + 2)
        self.lineage_prestige += 1

        # Trophy popularity bonus is handled by app.py route (+10 pop per holder)

        return previous_reign

    def record_defense(self, against: str = ""):
        """Record a successful title defense (trophies don't track defenses)."""
        if self.is_trophy:
            return
        self.current_defenses += 1
        self.prestige = min(100, self.prestige + 1)
        self.lineage_prestige += 1

    def vacate(self, reason: str = ""):
        """Vacate the title — clears all champion fields."""
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
                tag_partner_2=self.current_champion_tag_partner_2,
            )
            self.title_history.append(reign)
        self.current_champion = ""
        self.current_champion_tag_partner = ""
        self.current_champion_tag_partner_2 = ""
        self.held_by_group_id = ""
        self.current_defenses = 0
        self.current_reign_weeks = 0
        self.champion_weeks_injured = 0
        self.prestige = max(1, self.prestige - 10)

    def weekly_update(self):
        """Weekly tick — handled by ChampionshipManager.weekly_update()."""
        if self.current_champion:
            self.current_reign_weeks += 1
        if not self.current_champion and not self.is_trophy:
            self.prestige = max(1, self.prestige - 1)
        if self.current_champion and self.current_reign_weeks > 8 and self.current_defenses == 0 and not self.is_trophy:
            self.prestige = max(1, self.prestige - 1)

    # ==================== PHASE 3: AUTO-VACATE LOGIC ====================
    def get_champion_names(self) -> List[str]:
        """Returns list of all current champion names (1, 2, or 3 entries)."""
        names = []
        if self.current_champion:
            names.append(self.current_champion)
        if self.current_champion_tag_partner:
            names.append(self.current_champion_tag_partner)
        if self.current_champion_tag_partner_2:
            names.append(self.current_champion_tag_partner_2)
        return names

    def check_for_vacancy(self, promotion=None, group_manager=None) -> Optional[str]:
        """
        Check if title should be auto-vacated based on champion availability.
        Returns vacancy reason string if vacated, None if still valid.

        Rules (per design spec):
          - Trophies: NEVER auto-vacate
          - Singles: champion injured 3+ weeks → vacate
          - Tag (2 indie holders): EITHER injured 3+ weeks → vacate
          - Trios (3 indie holders): ANY injured 3+ weeks → vacate
          - Tag (faction-held): vacate if <2 of correct gender available
          - Trios (faction-held): vacate if <3 of correct gender available
        """
        # Trophies are permanent records — never auto-vacate
        if self.is_trophy:
            return None

        # No champion to check
        if not self.current_champion:
            return None

        # Faction-held titles: check faction can field enough members
        if self.held_by_group_id and group_manager:
            try:
                group = group_manager.get_group(self.held_by_group_id) if hasattr(group_manager, 'get_group') else None
                if group:
                    required = 3 if self.is_trios_title else (2 if self.is_tag_title else 1)
                    available = self._count_available_members(group, promotion)
                    if available < required:
                        return f"Faction can't field {required} healthy {self.gender.value} member(s)"
                    return None
            except Exception:
                pass  # Fall through to per-wrestler check

        # Per-wrestler injury check
        champion_names = self.get_champion_names()
        if not champion_names or not promotion:
            return None

        for name in champion_names:
            wrestler = self._find_wrestler(promotion, name)
            if not wrestler:
                # Champion no longer on roster — immediate vacate
                return f"{name} no longer on roster"

            if getattr(wrestler, 'is_injured', False):
                # Increment injury weeks counter for THIS championship
                # (we use the championship's counter rather than the wrestler's
                # so multiple titles track independently)
                self.champion_weeks_injured += 1
                if self.champion_weeks_injured >= self.weeks_until_auto_vacate:
                    return f"{name} injured {self.champion_weeks_injured}+ weeks"
                # Still injured but under threshold — don't reset counter, but no vacate yet
                return None

        # Nobody injured — reset counter
        self.champion_weeks_injured = 0
        return None

    def _find_wrestler(self, promotion, name: str):
        """Helper: find a wrestler in the promotion's roster by name."""
        if not promotion or not hasattr(promotion, 'roster'):
            return None
        for w in promotion.roster:
            if getattr(w, 'name', '') == name:
                return w
        return None

    def _count_available_members(self, group, promotion) -> int:
        """Count how many group members are healthy + correct gender."""
        if not promotion or not group:
            return 0

        member_names = []
        if hasattr(group, 'members'):
            member_names = list(group.members)
        elif hasattr(group, 'member_ids'):
            member_names = list(group.member_ids)

        count = 0
        for name in member_names:
            wrestler = self._find_wrestler(promotion, name)
            if not wrestler:
                continue
            if getattr(wrestler, 'is_injured', False):
                continue
            # Gender check
            if self.gender != ChampionshipGender.INTERGENDER:
                w_gender = getattr(wrestler.gender, 'value', str(wrestler.gender)) if hasattr(wrestler, 'gender') else 'Unknown'
                if self.gender == ChampionshipGender.MENS and w_gender not in ['Male', 'Intergender']:
                    continue
                if self.gender == ChampionshipGender.WOMENS and w_gender not in ['Female', 'Intergender']:
                    continue
            count += 1
        return count

    # ==================== MATCH TYPE VALIDATION ====================
    def can_be_defended_in(self, match_type: str, num_participants: int = 2) -> tuple:
        """Check if this championship can be defended in this match type."""
        # Trophies cannot be defended in normal matches (they're awarded, not defended)
        if self.is_trophy:
            return False, "Trophies are not defended in regular matches"

        is_tag = self.is_tag_title or self.level == ChampionshipLevel.TAG
        is_trios = self.is_trios_title or self.level == ChampionshipLevel.TRIOS

        # Trios match types
        trios_types = ['6-Man Tag', 'Trios Match']
        # Tag match types (2v2)
        tag_types = ['Tag Team', 'Mixed Tag', 'Tornado Tag']
        # All multi-team types
        all_team_types = tag_types + trios_types + ['8-Man Tag', 'War Games']

        # Handicap matches cannot have title defenses
        handicap_types = ['1-on-2 Handicap', '1-on-3 Handicap', '2-on-3 Handicap']
        if match_type in handicap_types:
            return False, "Titles cannot be defended in handicap matches"

        # Battle royals/gauntlets - no team title defenses
        rumble_types = [
            'Battle Royal', 'Casino Battle Royale', 'Royal Rumble',
            'Gauntlet Match', 'Gauntlet Eliminator',
        ]
        if match_type in rumble_types and (is_tag or is_trios):
            return False, "Tag/Trios titles cannot be defended in battle royals"

        # Trios title checks
        if is_trios:
            if match_type not in trios_types:
                return False, "Trios titles can only be defended in 6-Man Tag or Trios matches"

        # Tag title checks
        elif is_tag:
            if match_type not in tag_types:
                return False, "Tag titles can only be defended in 2v2 tag matches"

        # Singles title checks
        else:
            if match_type in all_team_types:
                return False, "Singles titles cannot be defended in team matches"

        # Rule-based restrictions
        if self.rules == ChampionshipRule.HARDCORE:
            allowed = [
                'Extreme Rules', 'Falls Count Anywhere',
                'Barbed Wire Deathmatch', 'Exploding Barbed Wire', 'Landmine Deathmatch',
                'Table Match', 'TLC', 'Ladder Match',
                'Last Man Standing', 'Steel Cage', 'Hell in a Cell',
                'Inferno Match', 'Ambulance Match', 'Casket Match',
                'Dumpster Match', 'Underground Match', 'Brawl',
                '3 Stages of Hell', 'Bloodline Rules',
            ]
            if match_type not in allowed:
                return False, "This title requires Hardcore/Deathmatch type matches"
        elif self.rules == ChampionshipRule.IRON_MAN:
            if match_type != 'Iron Man':
                return False, "This title can only be defended in Iron Man matches"
        elif self.rules == ChampionshipRule.SUBMISSION:
            if match_type not in ['Submission Match', 'I Quit']:
                return False, "This title requires Submission/I Quit matches"
        elif self.rules == ChampionshipRule.LADDER:
            if match_type not in ['Ladder Match', 'TLC']:
                return False, "This title requires Ladder matches"
        elif self.rules == ChampionshipRule.TOURNAMENT_ONLY:
            return False, "This title can only change hands in tournaments"

        # Combat sports titles
        combat_types = ['MMA Rules', 'Kickboxing Rules']
        if match_type in combat_types and self.rules not in [ChampionshipRule.STANDARD, ChampionshipRule.OPEN_CHALLENGE]:
            return False, "This title cannot be defended under combat sports rules"

        return True, "Can be defended"

    def can_wrestler_compete(self, wrestler_gender: str) -> bool:
        if self.gender == ChampionshipGender.INTERGENDER:
            return True
        elif self.gender == ChampionshipGender.MENS:
            return wrestler_gender in ["Male", "Intergender"]
        elif self.gender == ChampionshipGender.WOMENS:
            return wrestler_gender in ["Female", "Intergender"]
        return True

    # ==================== DISPLAY HELPERS ====================
    def get_champion_display(self) -> str:
        """Get human-readable champion display string."""
        if not self.current_champion:
            return "VACANT"

        # Trios: 3 names
        if self.is_trios_title or self.level == ChampionshipLevel.TRIOS:
            parts = [self.current_champion]
            if self.current_champion_tag_partner:
                parts.append(self.current_champion_tag_partner)
            if self.current_champion_tag_partner_2:
                parts.append(self.current_champion_tag_partner_2)
            return " & ".join(parts)

        # Tag: 2 names
        if (self.is_tag_title or self.level == ChampionshipLevel.TAG) and self.current_champion_tag_partner:
            return f"{self.current_champion} & {self.current_champion_tag_partner}"

        # Singles
        return self.current_champion

    def get_reign_info(self) -> Dict:
        return {
            "champion": self.get_champion_display(),
            "champion_names": self.get_champion_names(),
            "defenses": self.current_defenses,
            "weeks": self.current_reign_weeks,
            "is_vacant": not self.current_champion,
            "held_by_group_id": self.held_by_group_id,
            "is_trophy": self.is_trophy,
            "is_tag": self.is_tag_title or self.level == ChampionshipLevel.TAG,
            "is_trios": self.is_trios_title or self.level == ChampionshipLevel.TRIOS,
        }

    def get_summary(self) -> Dict:
        """Compact summary for UI display."""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "gender": self.gender.value,
            "rules": self.rules.value,
            "champion_display": self.get_champion_display(),
            "champion_names": self.get_champion_names(),
            "prestige": self.prestige,
            "current_defenses": self.current_defenses,
            "current_reign_weeks": self.current_reign_weeks,
            "total_reigns": self.total_reigns,
            "is_active": self.is_active,
            "is_tag_title": self.is_tag_title,
            "is_trios_title": self.is_trios_title,
            "is_trophy": self.is_trophy,
            "held_by_group_id": self.held_by_group_id,
            "is_vacant": not self.current_champion,
        }

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "level": self.level.value,
            "gender": self.gender.value, "rules": self.rules.value,
            "is_active": self.is_active,
            "current_champion": self.current_champion,
            "current_champion_tag_partner": self.current_champion_tag_partner,
            "current_champion_tag_partner_2": self.current_champion_tag_partner_2,
            "prestige": self.prestige,
            "lineage_prestige": self.lineage_prestige,
            "current_defenses": self.current_defenses,
            "current_reign_weeks": self.current_reign_weeks,
            "title_history": [
                {
                    "champion": r.champion, "date_won": r.date_won, "date_lost": r.date_lost,
                    "defenses": r.defenses, "days_held": r.days_held, "lost_to": r.lost_to,
                    "how_won": r.how_won, "how_lost": r.how_lost,
                    "tag_partner": r.tag_partner,
                    "tag_partner_2": r.tag_partner_2,
                    "team_members_snapshot": r.team_members_snapshot,
                    "held_by_group_name": r.held_by_group_name,
                }
                for r in self.title_history
            ],
            "total_reigns": self.total_reigns,
            "creation_cost": self.creation_cost,
            "longest_reign_weeks": self.longest_reign_weeks,
            "longest_reign_holder": self.longest_reign_holder,
            "most_defenses": self.most_defenses,
            "most_defenses_holder": self.most_defenses_holder,
            "is_tag_title": self.is_tag_title,
            "is_trios_title": self.is_trios_title,
            "is_trophy": self.is_trophy,
            "custom_match_type": self.custom_match_type,
            "held_by_group_id": self.held_by_group_id,
            "champion_weeks_injured": self.champion_weeks_injured,
            "weeks_until_auto_vacate": self.weeks_until_auto_vacate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Championship":
        # Handle level — fall back to SINGLES if unknown (e.g. old save with new enum)
        try:
            level = ChampionshipLevel(data["level"])
        except (ValueError, KeyError):
            level = ChampionshipLevel.SINGLES

        champ = cls(
            id=data["id"], name=data["name"],
            level=level,
            gender=ChampionshipGender(data["gender"]),
            rules=ChampionshipRule(data.get("rules", "Standard")),
            is_active=data.get("is_active", True),
            current_champion=data.get("current_champion", ""),
            current_champion_tag_partner=data.get("current_champion_tag_partner", ""),
            current_champion_tag_partner_2=data.get("current_champion_tag_partner_2", ""),
            prestige=data.get("prestige", 50),
            lineage_prestige=data.get("lineage_prestige", 0),
            current_defenses=data.get("current_defenses", 0),
            current_reign_weeks=data.get("current_reign_weeks", 0),
            total_reigns=data.get("total_reigns", 0),
            creation_cost=data.get("creation_cost", 15000),
            longest_reign_weeks=data.get("longest_reign_weeks", 0),
            longest_reign_holder=data.get("longest_reign_holder", ""),
            most_defenses=data.get("most_defenses", 0),
            most_defenses_holder=data.get("most_defenses_holder", ""),
            is_tag_title=data.get("is_tag_title", False),
            is_trios_title=data.get("is_trios_title", False),
            is_trophy=data.get("is_trophy", False),
            custom_match_type=data.get("custom_match_type", ""),
            held_by_group_id=data.get("held_by_group_id", ""),
            champion_weeks_injured=data.get("champion_weeks_injured", 0),
            weeks_until_auto_vacate=data.get("weeks_until_auto_vacate", 3),
        )
        for rd in data.get("title_history", []):
            champ.title_history.append(TitleReign(
                champion=rd["champion"], date_won=rd.get("date_won", ""),
                date_lost=rd.get("date_lost", ""), defenses=rd.get("defenses", 0),
                days_held=rd.get("days_held", 0), lost_to=rd.get("lost_to", ""),
                how_won=rd.get("how_won", ""), how_lost=rd.get("how_lost", ""),
                tag_partner=rd.get("tag_partner", ""),
                tag_partner_2=rd.get("tag_partner_2", ""),
                team_members_snapshot=rd.get("team_members_snapshot", []),
                held_by_group_name=rd.get("held_by_group_name", ""),
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
                1: {"name": "Quarter Finals", "matches": [
                    {"match": i+1, "wrestler1": shuffled[i*2], "wrestler2": shuffled[i*2+1], "winner": "", "rating": 0}
                    for i in range(4)
                ], "completed": False},
                2: {"name": "Semi Finals", "matches": [
                    {"match": i+1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0}
                    for i in range(2)
                ], "completed": False},
                3: {"name": "Final", "matches": [
                    {"match": 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0}
                ], "completed": False},
            }
        elif self.size == 16:
            self.total_rounds = 4
            self.rounds = {
                1: {"name": "First Round", "matches": [
                    {"match": i+1, "wrestler1": shuffled[i*2], "wrestler2": shuffled[i*2+1], "winner": "", "rating": 0}
                    for i in range(8)
                ], "completed": False},
                2: {"name": "Quarter Finals", "matches": [
                    {"match": i+1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0}
                    for i in range(4)
                ], "completed": False},
                3: {"name": "Semi Finals", "matches": [
                    {"match": i+1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0}
                    for i in range(2)
                ], "completed": False},
                4: {"name": "Final", "matches": [
                    {"match": 1, "wrestler1": "", "wrestler2": "", "winner": "", "rating": 0}
                ], "completed": False},
            }
        self.current_round = 1
        self.status = TournamentStatus.IN_PROGRESS
        return True

    def record_match_result(self, match_number: int, winner: str, rating: float):
        if self.current_round not in self.rounds:
            return
        rd = self.rounds[self.current_round]
        for m in rd["matches"]:
            if m["match"] == match_number:
                m["winner"] = winner
                m["rating"] = rating
                break
        if all(m.get("winner") for m in rd["matches"]):
            rd["completed"] = True
            self._advance_to_next_round()

    def _advance_to_next_round(self):
        winners = [m["winner"] for m in self.rounds[self.current_round]["matches"]]
        next_r = self.current_round + 1
        if next_r > self.total_rounds:
            self.winner = winners[0] if winners else ""
            self.status = TournamentStatus.COMPLETED
            return
        if next_r in self.rounds:
            for i, m in enumerate(self.rounds[next_r]["matches"]):
                if i*2 < len(winners): m["wrestler1"] = winners[i*2]
                if i*2+1 < len(winners): m["wrestler2"] = winners[i*2+1]
        self.current_round = next_r

    def is_complete(self) -> bool:
        return self.status == TournamentStatus.COMPLETED

    def get_bracket_display(self) -> List[Dict]:
        return [{"round": rn, "name": rd["name"], "matches": rd["matches"],
                 "completed": rd["completed"], "is_current": rn == self.current_round}
                for rn, rd in sorted(self.rounds.items())]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "tournament_format": self.tournament_format.value,
            "status": self.status.value, "size": self.size,
            "gender": self.gender.value, "is_ppv": self.is_ppv,
            "for_championship": self.for_championship,
            "participants": self.participants, "rounds": self.rounds,
            "current_round": self.current_round, "total_rounds": self.total_rounds,
            "winner": self.winner, "runner_up": self.runner_up,
            "xp_reward": self.xp_reward, "prestige_reward": self.prestige_reward,
            "grants_accolade": self.grants_accolade,
            "week_started": self.week_started, "week_completed": self.week_completed,
            "venue_id": self.venue_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tournament":
        t = cls(
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
            winner=data.get("winner", ""), runner_up=data.get("runner_up", ""),
            xp_reward=data.get("xp_reward", 200),
            prestige_reward=data.get("prestige_reward", 5),
            grants_accolade=data.get("grants_accolade", ""),
            week_started=data.get("week_started", 0),
            week_completed=data.get("week_completed", 0),
            venue_id=data.get("venue_id", ""),
        )
        t.rounds = {int(k): v for k, v in data.get("rounds", {}).items()}
        return t


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
        self.history.append({"winner": wrestler_name, "year": year, "week": week, "details": details})
        self.current_holder = wrestler_name
        self.last_awarded_year = year

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "accolade_type": self.accolade_type.value,
            "description": self.description, "history": self.history,
            "current_holder": self.current_holder, "frequency": self.frequency,
            "last_awarded_year": self.last_awarded_year,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Accolade":
        a = cls(id=data["id"], name=data["name"],
                accolade_type=AccoladeType(data["accolade_type"]),
                description=data.get("description", ""),
                frequency=data.get("frequency", "annual"),
                last_awarded_year=data.get("last_awarded_year", 0))
        a.history = data.get("history", [])
        a.current_holder = data.get("current_holder", "")
        return a


# ==================== CHAMPIONSHIP MANAGER ====================
class ChampionshipManager:
    def __init__(self):
        # FIX: was `def **init**(self):` — markdown bold corruption
        self.championships: List[Championship] = []
        self.tournaments: List[Tournament] = []
        self.accolades: List[Accolade] = []
        self.unlocked_slots: int = 0
        self.max_slots: int = 10

    # ==================== SLOTS ====================
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

    # ==================== CREATE / RETIRE ====================
    def create_championship(
        self,
        name: str,
        level: ChampionshipLevel,
        gender: ChampionshipGender,
        rules: ChampionshipRule = ChampionshipRule.STANDARD,
    ) -> Optional[Championship]:
        """
        Create a new championship/trophy.
        Auto-detects is_tag_title, is_trios_title, is_trophy from level.
        """
        if len(self.championships) >= self.unlocked_slots:
            return None

        costs = CHAMPIONSHIP_COSTS.get(level, {})
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        champ_id = f"title_{safe_name}_{len(self.championships)}"

        # Auto-detect type flags from level
        is_tag = level in [ChampionshipLevel.TAG, ChampionshipLevel.TAG_TROPHY]
        is_trios = level in [ChampionshipLevel.TRIOS, ChampionshipLevel.TRIOS_TROPHY]
        is_trophy = level in [
            ChampionshipLevel.TROPHY,
            ChampionshipLevel.TAG_TROPHY,
            ChampionshipLevel.TRIOS_TROPHY,
        ]

                championship = Championship(
            id=champ_id,
            name=name,
            level=level,
            gender=gender,
            rules=rules,
            is_tag_title=is_tag,
            is_trios_title=is_trios,
            is_trophy=is_trophy,
            creation_cost=costs.get("creation_cost", 15000),
        )

        # Starting prestige scaled by tier
        prestige_starts = {
            ChampionshipLevel.WORLD: 60,
            ChampionshipLevel.SINGLES: 45,
            ChampionshipLevel.TAG: 40,
            ChampionshipLevel.TRIOS: 42,
            ChampionshipLevel.TROPHY: 30,
            ChampionshipLevel.TAG_TROPHY: 35,
            ChampionshipLevel.TRIOS_TROPHY: 38,
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

    def get_championships_held_by_group(self, group_id: str) -> List[Championship]:
        """Phase 2: Find all titles currently held by a given group/faction."""
        return [c for c in self.championships if c.held_by_group_id == group_id and c.is_active]

    def retire_championship(self, championship_id: str):
        champ = self.get_championship(championship_id)
        if champ:
            champ.is_active = False
            if champ.current_champion:
                champ.vacate("Championship retired")

    def get_active_championships(self) -> List[Championship]:
        return [c for c in self.championships if c.is_active]

    def get_active_titles(self) -> List[Championship]:
        """Active titles only (excludes trophies). For auto-vacate processing."""
        return [c for c in self.championships if c.is_active and not c.is_trophy]

    def get_active_trophies(self) -> List[Championship]:
        """Active trophies only (never auto-vacate)."""
        return [c for c in self.championships if c.is_active and c.is_trophy]


    # ==================== WEEKLY UPDATE ====================
    def weekly_update(self):
        """Tick all active championships forward 1 week."""
        for c in self.championships:
            if c.is_active:
                c.weekly_update()

    def process_auto_vacancies(self, promotion=None, group_manager=None) -> List[Dict]:
        """
        Phase 3: Check all active titles for auto-vacancy conditions.
        Returns list of vacancy events for inbox notifications.

        Run this once per week from process_week_advancement().
        """
        vacancies = []
        for champ in self.get_active_titles():
            try:
                reason = champ.check_for_vacancy(promotion, group_manager)
                if reason:
                    title_name = champ.name
                    former_champion = champ.get_champion_display()
                    champ.vacate(reason)
                    vacancies.append({
                        "title": title_name,
                        "former_champion": former_champion,
                        "reason": reason,
                    })
            except Exception as e:
                print(f"Auto-vacancy check error for {champ.name}: {e}")
        return vacancies

    # ==================== TOURNAMENTS ====================
    def create_tournament(self, name, tournament_format, size=8, gender=ChampionshipGender.INTERGENDER, for_championship="", grants_accolade="", current_week=0):
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        t = Tournament(id=f"tourney_{safe_name}_{current_week}", name=name,
                       tournament_format=tournament_format, size=size, gender=gender,
                       for_championship=for_championship, grants_accolade=grants_accolade,
                       week_started=current_week)
        self.tournaments.append(t)
        return t

    def get_tournament(self, tid):
        return next((t for t in self.tournaments if t.id == tid), None)

    def get_active_tournaments(self):
        return [t for t in self.tournaments if t.status == TournamentStatus.IN_PROGRESS]

    def get_planning_tournaments(self):
        return [t for t in self.tournaments if t.status == TournamentStatus.PLANNING]

    def get_completed_tournaments(self):
        return [t for t in self.tournaments if t.status == TournamentStatus.COMPLETED]

    # ==================== ACCOLADES ====================
    def create_accolade(self, name, accolade_type, description="", frequency="annual"):
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
        a = Accolade(id=f"accolade_{safe_name}", name=name, accolade_type=accolade_type,
                     description=description, frequency=frequency)
        self.accolades.append(a)
        return a

    def setup_default_accolades(self):
        defaults = [
            ("King of the Ring", AccoladeType.KING_OF_THE_RING, "Winner of the King of the Ring tournament", "tournament"),
            ("Queen of the Ring", AccoladeType.QUEEN_OF_THE_RING, "Winner of the Queen of the Ring tournament", "tournament"),
            ("Wrestler of the Year", AccoladeType.WRESTLER_OF_THE_YEAR, "Best overall performer", "annual"),
            ("Match of the Year", AccoladeType.MATCH_OF_THE_YEAR, "Best match of the year", "annual"),
            ("Rookie of the Year", AccoladeType.ROOKIE_OF_THE_YEAR, "Best newcomer", "annual"),
            ("Most Popular", AccoladeType.MOST_POPULAR, "Fan favorite", "annual"),
        ]
        for name, at, desc, freq in defaults:
            if not any(a.name == name for a in self.accolades):
                self.create_accolade(name, at, desc, freq)

    def get_accolade(self, aid):
        return next((a for a in self.accolades if a.id == aid), None)

    # ==================== SERIALIZATION ====================
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
        for cd in data.get("championships", []):
            try:
                manager.championships.append(Championship.from_dict(cd))
            except Exception as e:
                print(f"Championship restore error: {e}")
        for td in data.get("tournaments", []):
            try:
                manager.tournaments.append(Tournament.from_dict(td))
            except Exception as e:
                print(f"Tournament restore error: {e}")
        for ad in data.get("accolades", []):
            try:
                manager.accolades.append(Accolade.from_dict(ad))
            except Exception as e:
                print(f"Accolade restore error: {e}")
        return manager
