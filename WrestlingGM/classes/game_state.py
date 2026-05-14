"""
Game State - The Central Hub of The Booking Room
Wires every system together. Handles save/load for the complete game state.
"""
import json
import os
import traceback
from typing import Dict, List, Optional
from datetime import datetime


class GameState:
    """The central game state container."""

    def __init__(self):
        # ===== CORE ENTITIES =====
        self.promotion = None
        # Note: roster is a @property below — backed by _roster_fallback
        self._roster_fallback: List = []
        self.free_agents: List = []
        self.released_wrestlers: List = []

        # ===== PROGRESSION =====
        self.progression = None

        # ===== BOOKING & SHOWS =====
        self.booked_show = None              # dict, not an object
        self.show_history: List = []
        self.calendar = None
        self.production_settings = None

        # ===== CHAMPIONSHIPS =====
        self.championship_manager = None

        # ===== FINANCIALS =====
        self.banking = None

        # ===== COMMUNICATION =====
        self.inbox = None
        self.calls = None

        # ===== AI SYSTEMS =====
        self.ai_director = None
        self.event_generator = None
        self.storyline_engine = None
        self.commentary_generator = None
        self.news_generator = None
        self.rival_promotions = None
        self.quest_system = None
        self.relationship_manager = None

        # ===== FREE AGENCY =====
        self.free_agency = None

        # ===== TRAINING SCHOOL =====
        self.training_school = None
        self.coach_manager = None
        self.coach_pool = None
        self.trainee_pool = None
        self.trainee_show_manager = None

        # ===== INJURY =====
        self.injury_manager = None

        # ===== CLASS ENROLLMENTS (Sub-Round 3A storage) =====
        self.active_enrollments: List = []

        # ===== TAG TEAMS / FACTIONS (Phase 1 - Sub-Round 1A) =====
        self.group_manager = None

        # ===== APP.PY EXPECTED FIELDS =====
        self.game_settings: Dict = {}
        self.origin_story: Optional[Dict] = None
        self.weekly_agent_names: List = []
        self.weekly_agents_week: str = ""
        self.promoter_name: str = ""

        # ===== TUTORIAL =====
        self.tutorial_active: bool = False
        self.tutorial_step: int = 0
        self.tutorial_skipped: bool = False
        self.show_tutorial_prompt: bool = False
        self.origin_grant_accepted: bool = False
        self.origin_grant_amount: int = 0
        self.first_launch: bool = True

        # ===== META =====
        self.session_id: str = ""
        self.created_at: str = datetime.now().isoformat()
        self.last_saved: str = ""
        self.game_version: str = "2.0.0"

        # ===== LIVING WORLD AI =====
        # These hold long-term memory, wrestler mind states, and world history.
        self.ai_memory = None
        self.wrestler_minds = None
        self.living_world_history: List = []
        self.rival_scheduler = None

    # ==================== INITIALIZATION ====================
    def initialize_new_game(
        self,
        promotion_name: str,
        location: str,
        philosophy: str,
        owner_name: str = "",
        creative_control_enabled: bool = False,
        creative_control_difficulty: str = "Normal",
        ai_personality: str = "The Traditionalist",
    ):
        """Initialize a brand new game with all systems set up"""
        # Lazy imports to avoid circular dependencies
        try:
            from classes.promotion import Promotion
        except Exception as e:
            print(f"Promotion import error: {e}")
            Promotion = None

        # Try to resolve Philosophy enum
        phil = None
        try:
            from classes.philosophy import Philosophy
            for p in Philosophy:
                if p.value == philosophy:
                    phil = p
                    break
        except Exception:
            phil = philosophy

        # === CORE PROMOTION ===
        if Promotion:
            try:
                self.promotion = Promotion(
                    name=promotion_name,
                    philosophy=phil if phil else philosophy,
                    owner_name=owner_name or "You",
                    starting_budget=0,
                    location=location,
                )
            except TypeError:
                try:
                    self.promotion = Promotion(promotion_name)
                    self.promotion.location = location
                    self.promotion.owner_name = owner_name or "You"
                    self.promotion.budget = 0
                    self.promotion.fan_base = 0
                    self.promotion.prestige = 1
                    if phil:
                        self.promotion.philosophy = phil
                except Exception as e:
                    print(f"Promotion fallback init error: {e}")

        # === ALL OTHER SYSTEMS (each in its own try block) ===
        self._init_progression()
        self._init_calendar()
        self._init_championship_manager()
        self._init_banking()
        self._init_inbox()
        self._init_calls()
        self._init_ai_director(creative_control_enabled, creative_control_difficulty, ai_personality)
        self._init_supporting_ai()
        self._init_free_agency()
        self._init_training_school()
        self._init_injury_manager()
        self._init_group_manager()  # Phase 1 - Sub-Round 1A

        # === META ===
        self.first_launch = True
        self.tutorial_active = False
        self.tutorial_step = 0
        self.created_at = datetime.now().isoformat()

        # === STARTER RIVALS ===
        try:
            from ai.rival_promotions import RivalSize
            if self.rival_promotions and hasattr(self.rival_promotions, 'create_starter_rivals'):
                self.rival_promotions.create_starter_rivals(player_size=RivalSize.BACKYARD)
        except Exception as e:
            print(f"Starter rivals error: {e}")

    def _init_progression(self):
        try:
            try:
                from classes.progression import ProgressionSystem
                self.progression = ProgressionSystem()
            except ImportError:
                from classes.progression import ProgressionManager
                self.progression = ProgressionManager()
        except Exception as e:
            print(f"Progression init error: {e}")

    def _init_calendar(self):
        try:
            from classes.calendar_system import CalendarSystem
            self.calendar = CalendarSystem()
        except Exception as e:
            print(f"Calendar init error: {e}")

    def _init_championship_manager(self):
        try:
            from classes.championship import ChampionshipManager
            self.championship_manager = ChampionshipManager()
            if hasattr(self.championship_manager, 'setup_default_accolades'):
                self.championship_manager.setup_default_accolades()
        except Exception as e:
            print(f"Championship init error: {e}")

    def _init_banking(self):
        try:
            from classes.banking import BankingManager
            self.banking = BankingManager()
        except Exception as e:
            print(f"Banking init error: {e}")

    def _init_inbox(self):
        try:
            from classes.inbox import InboxManager
            self.inbox = InboxManager()
        except Exception as e:
            print(f"Inbox init error: {e}")

    def _init_calls(self):
        try:
            from classes.calls import CallsManager
            self.calls = CallsManager()
        except Exception as e:
            print(f"Calls init error: {e}")

    def _init_ai_director(self, cc_enabled, cc_difficulty, personality):
        try:
            from ai.director import AIDirector
            try:
                self.ai_director = AIDirector(
                    creative_control_enabled=cc_enabled,
                    creative_control_difficulty=cc_difficulty,
                    personality_type=personality,
                )
            except TypeError:
                self.ai_director = AIDirector()
        except Exception as e:
            print(f"AI Director init error: {e}")

    def _init_supporting_ai(self):
        try:
            from ai.event_generator import EventGenerator
            self.event_generator = EventGenerator()
        except Exception as e:
            print(f"EventGenerator error: {e}")
        try:
            from ai.storyline_engine import StorylineEngine
            self.storyline_engine = StorylineEngine()
        except Exception as e:
            print(f"StorylineEngine error: {e}")
        try:
            from ai.commentary import CommentaryGenerator
            self.commentary_generator = CommentaryGenerator(
                ai_director=self.ai_director,
                storyline_engine=self.storyline_engine,
            )
        except Exception as e:
            print(f"CommentaryGenerator error: {e}")
        try:
            from ai.news_generator import NewsGenerator
            self.news_generator = NewsGenerator(
                ai_director=self.ai_director,
                storyline_engine=self.storyline_engine,
            )
        except Exception as e:
            print(f"NewsGenerator error: {e}")
        try:
            from ai.rival_promotions import RivalPromotionManager
            self.rival_promotions = RivalPromotionManager()
        except Exception as e:
            print(f"RivalPromotions error: {e}")
        try:
            from ai.quest_system import QuestSystem
            self.quest_system = QuestSystem()
        except Exception as e:
            print(f"QuestSystem error: {e}")
        try:
            from ai.relationships import RelationshipManager
            self.relationship_manager = RelationshipManager()
        except Exception as e:
            print(f"RelationshipManager error: {e}")

    def _init_free_agency(self):
        try:
            from classes.free_agency import FreeAgencyManager
            self.free_agency = FreeAgencyManager()
            if hasattr(self.free_agency, 'seed_initial_pool'):
                self.free_agency.seed_initial_pool(
                    target_size=80,
                    include_licensed=True,
                    current_week=0,
                    current_year=1,
                )
        except Exception as e:
            print(f"FreeAgency init error: {e}")

    def _init_training_school(self):
        try:
            from classes.training_school import TrainingSchool
            self.training_school = TrainingSchool()
        except Exception as e:
            print(f"TrainingSchool error: {e}")
        try:
            from classes.coach import CoachManager
            self.coach_manager = CoachManager()
        except Exception as e:
            print(f"CoachManager error: {e}")
        try:
            from data.coach_pool import CoachPool
            self.coach_pool = CoachPool()
        except Exception as e:
            print(f"CoachPool error: {e}")
        try:
            from data.trainee_pool import TraineePool
            self.trainee_pool = TraineePool()
        except Exception as e:
            print(f"TraineePool error: {e}")
        try:
            from classes.trainee_show import TraineeShowManager
            self.trainee_show_manager = TraineeShowManager()
        except Exception as e:
            print(f"TraineeShowManager error: {e}")

    def _init_injury_manager(self):
        try:
            from classes.injury import InjuryManager
            self.injury_manager = InjuryManager()
        except Exception as e:
            print(f"InjuryManager error: {e}")

    def _init_group_manager(self):
        """NEW (Phase 1 - Sub-Round 1A): Initialize the Tag Team / Faction group system."""
        try:
            from classes.group import GroupManager
            self.group_manager = GroupManager()
        except Exception as e:
            print(f"GroupManager init error: {e}")

    # ==================== ROSTER MANAGEMENT ====================
    def add_wrestler_to_roster(self, wrestler) -> bool:
        if self.promotion and wrestler not in self.promotion.roster:
            self.promotion.roster.append(wrestler)
            return True
        return False

    def remove_wrestler_from_roster(self, wrestler_name: str, mark_as_indy_god: bool = True) -> bool:
        if not self.promotion:
            return False
        for w in self.promotion.roster[:]:
            if w.name == wrestler_name:
                self.promotion.roster.remove(w)
                if mark_as_indy_god and hasattr(w, "become_indy_god"):
                    try:
                        w.become_indy_god()
                    except Exception:
                        pass
                self.released_wrestlers.append(w)
                if self.free_agency and mark_as_indy_god:
                    try:
                        week = getattr(self.promotion, "current_week", 0)
                        year = getattr(self.promotion, "current_year", 1)
                        self.free_agency.add_released_wrestler(w, week, year)
                    except Exception:
                        pass
                # Phase 1: Auto-remove from any groups they were in
                if self.group_manager and hasattr(self.group_manager, 'remove_wrestler_from_all_groups'):
                    try:
                        self.group_manager.remove_wrestler_from_all_groups(wrestler_name)
                    except Exception:
                        pass
                return True
        return False

    def get_wrestler_by_name(self, name: str):
        if not self.promotion:
            return None
        for w in self.promotion.roster:
            if w.name == name:
                return w
        return None

    @property
    def roster(self):
        """Convenience property — returns promotion roster"""
        if self.promotion:
            return self.promotion.roster
        return self._roster_fallback

    @roster.setter
    def roster(self, value):
        """Setter for backwards compat"""
        self._roster_fallback = value
        if self.promotion:
            self.promotion.roster = value

    # ==================== WEEKLY UPDATE ====================
    def process_weekly_pulse(self, current_week: int, current_year: int) -> Dict:
        try:
            from systems.weekly_pulse import WeeklyPulse
            pulse = WeeklyPulse(self)
            return pulse.run(current_week, current_year)
        except Exception as e:
            print(f"Weekly pulse error: {e}")
            return {
                "ai_events": [], "ai_suggestions": [],
                "storyline_updates": [], "news_articles": [],
                "rival_activity": {}, "training_school": {},
                "trainee_pool_refresh": [], "coach_pool_refresh": [],
                "quest_updates": [], "relationship_changes": [],
                "messages_added": 0, "highlights": [],
                "money_changes": {"income": 0, "expenses": 0, "net": 0},
                "new_events": [],
            }

    # ==================== SHOW HOOKS ====================
    def record_show_completion(self, avg_rating, attendance, is_sellout, profit, venue_name="", match_results=None):
        if match_results is None:
            match_results = []
        if self.ai_director and hasattr(self.ai_director, 'record_show_result'):
            try:
                self.ai_director.record_show_result(
                    avg_rating=avg_rating, attendance=attendance,
                    is_sellout=is_sellout, profit=profit,
                )
            except Exception:
                pass
        if self.storyline_engine and match_results:
            week = getattr(self.promotion, "current_week", 0) if self.promotion else 0
            year = getattr(self.promotion, "current_year", 1) if self.promotion else 1
            for match in match_results:
                wrestler_names = match.get("wrestler_names", [])
                try:
                    self.storyline_engine.process_match(
                        wrestler_names=wrestler_names, week=week, year=year,
                        match_display=match.get("match_display", ""),
                        rating=match.get("rating", 0),
                        winner=match.get("winner", ""),
                        finish_type=match.get("finish_type", ""),
                    )
                except Exception:
                    pass
        if self.news_generator and self.promotion:
            try:
                week = getattr(self.promotion, "current_week", 0)
                year = getattr(self.promotion, "current_year", 1)
                self.news_generator.generate_show_recap(
                    promotion_name=self.promotion.name,
                    venue=venue_name or "the venue",
                    attendance=attendance, rating=avg_rating,
                    week=week, year=year, is_sellout=is_sellout,
                )
            except Exception:
                pass

    # ==================== HELPERS ====================
    def has_training_school(self) -> bool:
        return (
            self.training_school is not None
            and hasattr(self.training_school, "is_founded")
            and self.training_school.is_founded()
        )

    def get_school_summary(self) -> Optional[Dict]:
        if not self.has_training_school():
            return None
        try:
            return self.training_school.get_summary()
        except Exception:
            return None

    def get_ai_director_info(self) -> Optional[Dict]:
        if not self.ai_director:
            return None
        try:
            if hasattr(self.ai_director, 'get_director_info'):
                return self.ai_director.get_director_info()
        except Exception:
            pass
        return None

    def is_creative_control_enabled(self) -> bool:
        if not self.ai_director:
            return False
        return getattr(self.ai_director, "creative_control_enabled", False)

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        """Serialize the entire game state to dict"""

        def safe(obj, key=""):
            if obj is None:
                return None
            try:
                if hasattr(obj, "to_dict"):
                    return obj.to_dict()
            except Exception as e:
                print(f"Serialize error [{key}]: {e}")
            return None

        def safe_list(items, key_prefix=""):
            result = []
            for i, item in enumerate(items or []):
                d = safe(item, f"{key_prefix}_{i}")
                if d is not None:
                    result.append(d)
            return result

        return {
            # Meta
            "game_version": self.game_version,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_saved": datetime.now().isoformat(),
            "first_launch": self.first_launch,
            "tutorial_active": self.tutorial_active,
            "tutorial_step": self.tutorial_step,
            "tutorial_skipped": self.tutorial_skipped,
            "show_tutorial_prompt": self.show_tutorial_prompt,
            "origin_grant_accepted": self.origin_grant_accepted,
            "origin_grant_amount": self.origin_grant_amount,

            # App.py expected fields
            "game_settings": self.game_settings or {},
            "origin_story": self.origin_story,
            "promoter_name": self.promoter_name,
            "weekly_agent_names": self.weekly_agent_names or [],
            "weekly_agents_week": self.weekly_agents_week,

            # Booked show is a plain dict
            "booked_show": self.booked_show,

            # Class enrollments (plain list of dicts)
            "active_enrollments": self.active_enrollments or [],

            # Core
            "promotion": safe(self.promotion, "promotion"),
            "free_agents": safe_list(self.free_agents, "fa"),
            "released_wrestlers": safe_list(self.released_wrestlers, "rel"),

            # Systems
            "progression": safe(self.progression, "progression"),
            "show_history": safe_list(self.show_history[-50:], "show"),
            "calendar": safe(self.calendar, "calendar"),
            "production_settings": safe(self.production_settings, "production"),
            "championship_manager": safe(self.championship_manager, "championships"),
            "banking": safe(self.banking, "banking"),
            "inbox": safe(self.inbox, "inbox"),
            "calls": safe(self.calls, "calls"),
            "ai_director": safe(self.ai_director, "ai_director"),
            "event_generator": safe(self.event_generator, "event_generator"),
            "storyline_engine": safe(self.storyline_engine, "storyline_engine"),
            "news_generator": safe(self.news_generator, "news_generator"),
            "rival_promotions": safe(self.rival_promotions, "rival_promotions"),
            "quest_system": safe(self.quest_system, "quest_system"),
            "relationship_manager": safe(self.relationship_manager, "relationships"),
            "free_agency": safe(self.free_agency, "free_agency"),
            "training_school": safe(self.training_school, "training_school"),
            "coach_manager": safe(self.coach_manager, "coach_manager"),
            "coach_pool": safe(self.coach_pool, "coach_pool"),
            "trainee_pool": safe(self.trainee_pool, "trainee_pool"),
            "trainee_show_manager": safe(self.trainee_show_manager, "trainee_shows"),
            "injury_manager": safe(self.injury_manager, "injury_manager"),

            # Phase 1 - Sub-Round 1A
            "group_manager": safe(self.group_manager, "group_manager"),

            # Living World AI
            "ai_memory": safe(self.ai_memory, "ai_memory"),
            "wrestler_minds": safe(self.wrestler_minds, "wrestler_minds"),
            "living_world_history": self.living_world_history[-52:] if getattr(self, 'living_world_history', None) else [],
            "rival_scheduler": safe(self.rival_scheduler, "rival_scheduler"),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Restore game state from dict"""
        gs = cls()

        def safe_load(import_path, class_name, data_key, default_factory=True):
            # FIX: was `module = **import**(...)` — markdown bold corruption
            try:
                module = __import__(import_path, fromlist=[class_name])
                klass = getattr(module, class_name)
                d = data.get(data_key)
                if d is None:
                    return klass() if default_factory else None
                if hasattr(klass, "from_dict"):
                    return klass.from_dict(d)
                return klass() if default_factory else None
            except Exception as e:
                print(f"Restore error [{data_key}]: {e}")
                try:
                    if default_factory:
                        module = __import__(import_path, fromlist=[class_name])
                        klass = getattr(module, class_name)
                        return klass()
                except Exception:
                    pass
                return None

        # === META ===
        gs.game_version = data.get("game_version", "2.0.0")
        gs.session_id = data.get("session_id", "")
        gs.created_at = data.get("created_at", "")
        gs.last_saved = data.get("last_saved", "")
        gs.first_launch = data.get("first_launch", False)
        gs.tutorial_active = data.get("tutorial_active", False)
        gs.tutorial_step = data.get("tutorial_step", 0)
        gs.tutorial_skipped = data.get("tutorial_skipped", False)
        gs.show_tutorial_prompt = data.get("show_tutorial_prompt", False)
        gs.origin_grant_accepted = data.get("origin_grant_accepted", False)
        gs.origin_grant_amount = data.get("origin_grant_amount", 0)

        # === APP.PY FIELDS ===
        gs.game_settings = data.get("game_settings", {}) or {}
        gs.origin_story = data.get("origin_story")
        gs.promoter_name = data.get("promoter_name", "")
        gs.weekly_agent_names = data.get("weekly_agent_names", []) or []
        gs.weekly_agents_week = data.get("weekly_agents_week", "")

        # === BOOKED SHOW (plain dict) ===
        gs.booked_show = data.get("booked_show")

        # === CLASS ENROLLMENTS (plain list of dicts) ===
        gs.active_enrollments = data.get("active_enrollments", []) or []

        # === PROMOTION (loads roster too) ===
        gs.promotion = safe_load("classes.promotion", "Promotion", "promotion", default_factory=False)

        # === FREE AGENTS / RELEASED ===
        try:
            from classes.wrestler import Wrestler
            for wd in data.get("free_agents", []):
                try:
                    gs.free_agents.append(Wrestler.from_dict(wd))
                except Exception as e:
                    print(f"Free agent restore error: {e}")
            for wd in data.get("released_wrestlers", []):
                try:
                    gs.released_wrestlers.append(Wrestler.from_dict(wd))
                except Exception as e:
                    print(f"Released wrestler restore error: {e}")
        except Exception as e:
            print(f"Wrestler import error: {e}")

        # === SYSTEMS ===
        # Progression — try both class names
        try:
            from classes.progression import ProgressionSystem as PS
            d = data.get("progression")
            gs.progression = PS.from_dict(d) if (d and hasattr(PS, 'from_dict')) else PS()
        except Exception:
            try:
                from classes.progression import ProgressionManager as PM
                d = data.get("progression")
                gs.progression = PM.from_dict(d) if (d and hasattr(PM, 'from_dict')) else PM()
            except Exception as e:
                print(f"Progression restore error: {e}")

        gs.calendar = safe_load("classes.calendar_system", "CalendarSystem", "calendar")

        # Production — try ProductionManager first, then ShowProduction
        try:
            from classes.production import ProductionManager as PM
            d = data.get("production_settings")
            gs.production_settings = PM.from_dict(d) if (d and hasattr(PM, 'from_dict')) else PM()
        except Exception:
            try:
                from classes.production import ShowProduction as SP
                d = data.get("production_settings")
                gs.production_settings = SP.from_dict(d) if (d and hasattr(SP, 'from_dict')) else SP()
            except Exception as e:
                print(f"Production restore error: {e}")

        gs.championship_manager = safe_load("classes.championship", "ChampionshipManager", "championship_manager")
        gs.banking = safe_load("classes.banking", "BankingManager", "banking")
        gs.inbox = safe_load("classes.inbox", "InboxManager", "inbox")
        gs.calls = safe_load("classes.calls", "CallsManager", "calls")
        gs.ai_director = safe_load("ai.director", "AIDirector", "ai_director")
        gs.event_generator = safe_load("ai.event_generator", "EventGenerator", "event_generator")
        gs.storyline_engine = safe_load("ai.storyline_engine", "StorylineEngine", "storyline_engine")
        gs.news_generator = safe_load("ai.news_generator", "NewsGenerator", "news_generator")
        gs.rival_promotions = safe_load("ai.rival_promotions", "RivalPromotionManager", "rival_promotions")
        gs.quest_system = safe_load("ai.quest_system", "QuestSystem", "quest_system")
        gs.relationship_manager = safe_load("ai.relationships", "RelationshipManager", "relationship_manager")
        gs.free_agency = safe_load("classes.free_agency", "FreeAgencyManager", "free_agency")
        gs.training_school = safe_load("classes.training_school", "TrainingSchool", "training_school")
        gs.coach_manager = safe_load("classes.coach", "CoachManager", "coach_manager")
        gs.coach_pool = safe_load("data.coach_pool", "CoachPool", "coach_pool")
        gs.trainee_pool = safe_load("data.trainee_pool", "TraineePool", "trainee_pool")
        gs.trainee_show_manager = safe_load("classes.trainee_show", "TraineeShowManager", "trainee_show_manager")
        gs.injury_manager = safe_load("classes.injury", "InjuryManager", "injury_manager")

        # Phase 1 - Sub-Round 1A: Group Manager
        gs.group_manager = safe_load("classes.group", "GroupManager", "group_manager")

        # Living World AI
        gs.ai_memory = safe_load("ai.memory_core", "MemoryCore", "ai_memory")
        gs.wrestler_minds = safe_load("ai.wrestler_mind", "WrestlerMindManager", "wrestler_minds")
        gs.living_world_history = data.get("living_world_history", []) or []
        gs.rival_scheduler = safe_load("ai.rival_scheduler", "RivalScheduler", "rival_scheduler")

        # Wire commentary generator AFTER director and storyline are loaded
        try:
            from ai.commentary import CommentaryGenerator
            gs.commentary_generator = CommentaryGenerator(
                ai_director=gs.ai_director,
                storyline_engine=gs.storyline_engine,
            )
        except Exception:
            pass

        # Wire news generator references after load
        if gs.news_generator:
            try:
                gs.news_generator.ai_director = gs.ai_director
                gs.news_generator.storyline_engine = gs.storyline_engine
            except Exception:
                pass

        return gs

    # ==================== FILE I/O ====================
    def save_to_file(self, filepath: str) -> bool:
        """Save game state to a JSON file"""
        try:
            dir_path = os.path.dirname(filepath) if os.path.dirname(filepath) else "saves"
            os.makedirs(dir_path, exist_ok=True)
            data = self.to_dict()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"✅ Saved to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Save error: {e}")
            print(traceback.format_exc())
            return False

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load game state from a JSON file"""
        if not os.path.exists(filepath):
            print(f"❌ Load failed: file not found: {filepath}")
            return None
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            print(f"✅ JSON loaded from {filepath}")
        except Exception as e:
            print(f"❌ JSON parse error: {e}")
            print(traceback.format_exc())
            return None
        try:
            game_state = cls.from_dict(data)
            print(f"✅ GameState reconstructed")
            return game_state
        except Exception as e:
            print(f"❌ from_dict() error: {e}")
            print(traceback.format_exc())
            return None

    # ==================== BACKWARDS COMPATIBILITY ====================
    def save(self, save_name: str) -> bool:
        return self.save_to_file(f"saves/{save_name}.json")

    def load(self, save_name: str) -> bool:
        loaded = GameState.load_from_file(f"saves/{save_name}.json")
        if loaded:
            self.__dict__.update(loaded.__dict__)
            return True
        return False

    def ensure_all_systems(self):
        """Ensure all managers exist after load (handles save migrations)"""
        if not self.training_school:
            self._init_training_school()
        if not self.coach_manager:
            try:
                from classes.coach import CoachManager
                self.coach_manager = CoachManager()
            except Exception:
                pass
        if not self.free_agency:
            self._init_free_agency()
        if not self.inbox:
            self._init_inbox()
        if not self.calls:
            self._init_calls()
        if not self.ai_director:
            self._init_ai_director(False, "Normal", "The Traditionalist")
        if not self.championship_manager:
            self._init_championship_manager()
        if not self.banking:
            self._init_banking()
        if not self.injury_manager:
            self._init_injury_manager()
        # Phase 1 - Sub-Round 1A
        if not self.group_manager:
            self._init_group_manager()
        # Make sure these always exist (avoid AttributeError on old saves)
        if not hasattr(self, 'active_enrollments') or self.active_enrollments is None:
            self.active_enrollments = []

        # ===== LIVING WORLD AI SYSTEMS =====
        if not hasattr(self, 'ai_memory') or self.ai_memory is None:
            try:
                from ai.memory_core import MemoryCore
                self.ai_memory = MemoryCore()
            except Exception:
                self.ai_memory = None

        if not hasattr(self, 'wrestler_minds') or self.wrestler_minds is None:
            try:
                from ai.wrestler_mind import WrestlerMindManager
                self.wrestler_minds = WrestlerMindManager()
            except Exception:
                self.wrestler_minds = None

        if not hasattr(self, 'living_world_history') or self.living_world_history is None:
            self.living_world_history = []

        if not hasattr(self, 'rival_scheduler') or self.rival_scheduler is None:
    try:
        from ai.rival_scheduler import RivalScheduler
        self.rival_scheduler = RivalScheduler()
    except Exception:
        self.rival_scheduler = None

        # Also ensure commentary and news generator references if missing
        if self.news_generator:
            try:
                self.news_generator.ai_director = self.ai_director
                self.news_generator.storyline_engine = self.storyline_engine
            except Exception:
                pass

        if not self.commentary_generator:
            try:
                from ai.commentary import CommentaryGenerator
                self.commentary_generator = CommentaryGenerator(
                    ai_director=self.ai_director,
                    storyline_engine=self.storyline_engine,
                )
            except Exception:
                pass
