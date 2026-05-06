"""
Game State - The Central Hub of The Booking Room
Wires every system together: Promotion, Roster, Championships, AI Director,
Storylines, Training School, Rival Promotions, News, Banking, and more.
Handles save/load for the complete game state.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime


class GameState:
    """
    The central game state container. All managers and systems live here.
    Provides unified save/load and orchestration of weekly updates.
    """

    def __init__(self):
        # ==================== CORE GAME ENTITIES ====================
        self.promotion = None              # Promotion object
        self.roster: List = []             # List of Wrestler objects
        self.free_agents: List = []        # List of Wrestler objects (available to sign)
        self.released_wrestlers: List = [] # Released wrestlers (Indy God pool)

        # ==================== PROGRESSION ====================
        self.progression = None            # ProgressionManager

        # ==================== BOOKING & SHOWS ====================
        self.booked_show = None            # Currently booked show (pre-execution)
        self.show_history: List = []       # Past shows
        self.calendar = None               # Calendar System
        self.production_settings = None    # ProductionManager

        # ==================== CHAMPIONSHIPS ====================
        self.championship_manager = None   # ChampionshipManager

        # ==================== FINANCIALS ====================
        self.banking = None                # BankingManager (includes loans + loan shark)

        # ==================== COMMUNICATION ====================
        self.inbox = None                  # InboxManager

        # ==================== AI SYSTEMS ====================
        self.ai_director = None            # AIDirector (personality, mood, decisions)
        self.event_generator = None        # EventGenerator (random events)
        self.storyline_engine = None       # StorylineEngine (rivalries, feuds)
        self.commentary_generator = None   # CommentaryGenerator (live show commentary)
        self.news_generator = None         # NewsGenerator (industry news)
        self.rival_promotions = None       # RivalPromotionManager (AI rivals)

        # ==================== AI SUPPORTING SYSTEMS ====================
        self.quest_system = None           # QuestSystem (player goals)
        self.relationship_manager = None   # RelationshipManager (wrestler dynamics)

        # ==================== FREE AGENCY ====================
        self.free_agency = None            # FreeAgencyManager

        # ==================== TRAINING SCHOOL ====================
        self.training_school = None        # TrainingSchool (main school object)
        self.coach_manager = None          # CoachManager (active coaches)
        self.coach_pool = None             # CoachPool (hireable NPCs)
        self.trainee_pool = None           # TraineePool (applicants)
        self.trainee_show_manager = None   # TraineeShowManager (trainee shows)

        # ==================== INJURY & MEDICAL ====================
        self.injury_manager = None         # InjuryManager

        # ==================== TUTORIAL & ONBOARDING ====================
        self.tutorial_active: bool = False
        self.tutorial_step: int = 0
        self.tutorial_skipped: bool = False
        self.origin_grant_accepted: bool = False
        self.origin_grant_amount: int = 0
        self.first_launch: bool = True

        # ==================== META ====================
        self.session_id: str = ""
        self.created_at: str = datetime.now().isoformat()
        self.last_saved: str = ""
        self.game_version: str = "2.0.0"

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
        from classes.promotion import Promotion
        from classes.philosophy import Philosophy
        from classes.progression import ProgressionManager
        from classes.calendar_system import CalendarSystem
        from classes.production import ProductionManager
        from classes.championship import ChampionshipManager
        from classes.banking import BankingManager
        from classes.inbox import InboxManager
        from classes.injury import InjuryManager
        from classes.free_agency import FreeAgencyManager

        # AI Systems
        from ai.director import AIDirector
        from ai.event_generator import EventGenerator
        from ai.storyline_engine import StorylineEngine
        from ai.commentary import CommentaryGenerator
        from ai.news_generator import NewsGenerator
        from ai.rival_promotions import RivalPromotionManager
        from ai.quest_system import QuestSystem
        from ai.relationships import RelationshipManager

        # Training School
        from classes.training_school import TrainingSchool
        from classes.coach import CoachManager
        from data.coach_pool import CoachPool
        from data.trainee_pool import TraineePool
        from classes.trainee_show import TraineeShowManager

        # === CORE PROMOTION ===
        try:
            phil = Philosophy(philosophy)
        except (ValueError, KeyError):
            phil = None

        # Try to build promotion with whatever signature it has
        try:
            self.promotion = Promotion(
                name=promotion_name,
                location=location,
                philosophy=phil if phil else philosophy,
                owner_name=owner_name or "You",
                budget=0,
                fan_base=0,
                prestige=1,
            )
        except TypeError:
            # Fallback if Promotion has a different signature
            self.promotion = Promotion(promotion_name)
            try:
                self.promotion.location = location
                self.promotion.owner_name = owner_name or "You"
                self.promotion.budget = 0
                self.promotion.fan_base = 0
                self.promotion.prestige = 1
                if phil:
                    self.promotion.philosophy = phil
            except Exception:
                pass

        # === PROGRESSION ===
        try:
            self.progression = ProgressionManager()
        except Exception as e:
            print(f"ProgressionManager init error: {e}")

        # === BOOKING ===
        try:
            self.calendar = CalendarSystem()
        except Exception as e:
            print(f"CalendarSystem init error: {e}")
        try:
            self.production_settings = ProductionManager()
        except Exception as e:
            print(f"ProductionManager init error: {e}")
        self.show_history = []

        # === CHAMPIONSHIPS ===
        try:
            self.championship_manager = ChampionshipManager()
        except Exception as e:
            print(f"ChampionshipManager init error: {e}")

        # === FINANCIALS ===
        try:
            self.banking = BankingManager()
        except Exception as e:
            print(f"BankingManager init error: {e}")

        # === COMMUNICATION ===
        try:
            self.inbox = InboxManager()
        except Exception as e:
            print(f"InboxManager init error: {e}")

        # === AI DIRECTOR (the brain) ===
        try:
            self.ai_director = AIDirector(
                creative_control_enabled=creative_control_enabled,
                creative_control_difficulty=creative_control_difficulty,
                personality_type=ai_personality,
            )
        except Exception as e:
            print(f"AIDirector init error: {e}")

        # === AI SUPPORTING SYSTEMS ===
        try:
            self.event_generator = EventGenerator()
        except Exception as e:
            print(f"EventGenerator init error: {e}")
        try:
            self.storyline_engine = StorylineEngine()
        except Exception as e:
            print(f"StorylineEngine init error: {e}")
        try:
            self.commentary_generator = CommentaryGenerator(
                ai_director=self.ai_director,
                storyline_engine=self.storyline_engine,
            )
        except Exception as e:
            print(f"CommentaryGenerator init error: {e}")
        try:
            self.news_generator = NewsGenerator(
                ai_director=self.ai_director,
                storyline_engine=self.storyline_engine,
            )
        except Exception as e:
            print(f"NewsGenerator init error: {e}")
        try:
            self.rival_promotions = RivalPromotionManager()
        except Exception as e:
            print(f"RivalPromotionManager init error: {e}")
        try:
            self.quest_system = QuestSystem()
        except Exception as e:
            print(f"QuestSystem init error: {e}")
        try:
            self.relationship_manager = RelationshipManager()
        except Exception as e:
            print(f"RelationshipManager init error: {e}")

        # === FREE AGENCY ===
        try:
            self.free_agency = FreeAgencyManager()
            self.free_agency.seed_initial_pool(
                target_size=80,
                include_licensed=True,
                current_week=0,
                current_year=1,
            )
        except Exception as e:
            print(f"FreeAgencyManager init error: {e}")

        # === TRAINING SCHOOL (not founded by default) ===
        try:
            self.training_school = TrainingSchool()
        except Exception as e:
            print(f"TrainingSchool init error: {e}")
        try:
            self.coach_manager = CoachManager()
        except Exception as e:
            print(f"CoachManager init error: {e}")
        try:
            self.coach_pool = CoachPool()
        except Exception as e:
            print(f"CoachPool init error: {e}")
        try:
            self.trainee_pool = TraineePool()
        except Exception as e:
            print(f"TraineePool init error: {e}")
        try:
            self.trainee_show_manager = TraineeShowManager()
        except Exception as e:
            print(f"TraineeShowManager init error: {e}")

        # === INJURIES ===
        try:
            self.injury_manager = InjuryManager()
        except Exception as e:
            print(f"InjuryManager init error: {e}")

        # === META ===
        self.first_launch = True
        self.tutorial_active = False
        self.tutorial_step = 0
        self.created_at = datetime.now().isoformat()

        # === GENERATE STARTER RIVALS ===
        try:
            from ai.rival_promotions import RivalSize
            if self.rival_promotions:
                self.rival_promotions.create_starter_rivals(player_size=RivalSize.BACKYARD)
        except Exception as e:
            print(f"Starter rivals error: {e}")

    # ==================== ROSTER MANAGEMENT ====================

    def add_wrestler_to_roster(self, wrestler) -> bool:
        """Add a wrestler to the active roster"""
        if wrestler not in self.roster:
            self.roster.append(wrestler)
            return True
        return False

    def remove_wrestler_from_roster(self, wrestler_name: str, mark_as_indy_god: bool = True) -> bool:
        """Remove a wrestler from the roster (release them)"""
        for w in self.roster[:]:
            if w.name == wrestler_name:
                self.roster.remove(w)
                if mark_as_indy_god and hasattr(w, "become_indy_god"):
                    try:
                        w.become_indy_god()
                    except Exception:
                        pass
                self.released_wrestlers.append(w)

                # Add released wrestler back to free agency as Indy God
                if self.free_agency and mark_as_indy_god:
                    try:
                        week = getattr(self.promotion, "current_week", 0) if self.promotion else 0
                        year = getattr(self.promotion, "current_year", 1) if self.promotion else 1
                        self.free_agency.add_released_wrestler(w, week, year)
                    except Exception:
                        pass

                return True
        return False

    def get_wrestler_by_name(self, name: str):
        """Find a wrestler in the roster by name"""
        for w in self.roster:
            if w.name == name:
                return w
        return None

    def get_roster_size(self) -> int:
        return len(self.roster)

    def get_active_roster(self) -> List:
        """Get roster excluding injured wrestlers"""
        return [w for w in self.roster if not getattr(w, "is_injured", False)]

    def get_injured_count(self) -> int:
        return len([w for w in self.roster if getattr(w, "is_injured", False)])

    # ==================== ROSTER AS DICT (for AI consumption) ====================

    def get_roster_as_dicts(self) -> List[Dict]:
        """Convert roster to dict format for AI systems"""
        result = []
        for w in self.roster:
            try:
                if hasattr(w, "to_dict"):
                    result.append(w.to_dict())
                else:
                    result.append({
                        "name": getattr(w, "name", "Unknown"),
                        "popularity": getattr(w, "popularity", 30),
                        "morale": getattr(w, "morale", 75),
                        "is_injured": getattr(w, "is_injured", False),
                        "wins": getattr(w, "wins", 0),
                        "losses": getattr(w, "losses", 0),
                        "age": getattr(w, "age", 30),
                    })
            except Exception:
                pass
        return result

    # ==================== WEEKLY UPDATE ORCHESTRATION ====================

    def process_weekly_pulse(self, current_week: int, current_year: int) -> Dict:
        """
        Master weekly orchestrator. Delegates to WeeklyPulse system.
        Called when player skips week or runs show.
        """
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
            }

    # ==================== SHOW EXECUTION HOOKS ====================

    def record_show_completion(
        self,
        avg_rating: float,
        attendance: int,
        is_sellout: bool,
        profit: int,
        venue_name: str = "",
        match_results: List[Dict] = None,
    ):
        """Called when a show is completed. Updates AI, storylines, news, stats."""
        if match_results is None:
            match_results = []

        # AI Director records show
        if self.ai_director:
            try:
                self.ai_director.record_show_result(
                    avg_rating=avg_rating,
                    attendance=attendance,
                    is_sellout=is_sellout,
                    profit=profit,
                )
            except Exception as e:
                print(f"AI Director show record error: {e}")

        # Process storyline matches
        if self.storyline_engine and match_results:
            week = getattr(self.promotion, "current_week", 0) if self.promotion else 0
            year = getattr(self.promotion, "current_year", 1) if self.promotion else 1
            for match in match_results:
                wrestler_names = match.get("wrestler_names", [])
                if not wrestler_names and "wrestlers" in match:
                    wrestler_names = [
                        w if isinstance(w, str) else w.get("name", "")
                        for w in match["wrestlers"]
                    ]
                try:
                    self.storyline_engine.process_match(
                        wrestler_names=wrestler_names,
                        week=week,
                        year=year,
                        match_display=match.get("match_display", ""),
                        rating=match.get("rating", 0),
                        winner=match.get("winner", ""),
                        finish_type=match.get("finish_type", ""),
                    )
                except Exception:
                    pass

        # Generate news show recap
        if self.news_generator and self.promotion:
            try:
                week = getattr(self.promotion, "current_week", 0)
                year = getattr(self.promotion, "current_year", 1)
                self.news_generator.generate_show_recap(
                    promotion_name=self.promotion.name,
                    venue=venue_name or "the venue",
                    attendance=attendance,
                    rating=avg_rating,
                    week=week,
                    year=year,
                    is_sellout=is_sellout,
                )
            except Exception as e:
                print(f"News generator show recap error: {e}")

    # ==================== TRAINING SCHOOL HELPERS ====================

    def has_training_school(self) -> bool:
        """Check if player has founded a training school"""
        return (
            self.training_school is not None
            and hasattr(self.training_school, "is_founded")
            and self.training_school.is_founded()
        )

    def get_school_summary(self) -> Optional[Dict]:
        """Get school summary if founded"""
        if not self.has_training_school():
            return None
        try:
            return self.training_school.get_summary()
        except Exception:
            return None

    # ==================== AI DIRECTOR HELPERS ====================

    def get_ai_director_info(self) -> Optional[Dict]:
        """Get AI Director display info"""
        if not self.ai_director:
            return None
        try:
            return self.ai_director.get_director_info()
        except Exception:
            return None

    def is_creative_control_enabled(self) -> bool:
        """Check if Creative Control mode is on"""
        if not self.ai_director:
            return False
        return getattr(self.ai_director, "creative_control_enabled", False)

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        """Serialize the entire game state to dict"""
        data = {
            "game_version": self.game_version,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_saved": datetime.now().isoformat(),
            "first_launch": self.first_launch,
            "tutorial_active": self.tutorial_active,
            "tutorial_step": self.tutorial_step,
            "tutorial_skipped": self.tutorial_skipped,
            "origin_grant_accepted": self.origin_grant_accepted,
            "origin_grant_amount": self.origin_grant_amount,
        }

        # Helper to safely serialize objects
        def safe_to_dict(obj, key):
            if obj is None:
                return None
            try:
                if hasattr(obj, "to_dict"):
                    return obj.to_dict()
            except Exception as e:
                print(f"Error serializing {key}: {e}")
            return None

        # Core
        data["promotion"] = safe_to_dict(self.promotion, "promotion")
        data["roster"] = [safe_to_dict(w, f"roster_{i}") for i, w in enumerate(self.roster)]
        data["roster"] = [r for r in data["roster"] if r is not None]
        data["free_agents"] = [safe_to_dict(w, f"fa_{i}") for i, w in enumerate(self.free_agents)]
        data["free_agents"] = [r for r in data["free_agents"] if r is not None]
        data["released_wrestlers"] = [safe_to_dict(w, f"rel_{i}") for i, w in enumerate(self.released_wrestlers)]
        data["released_wrestlers"] = [r for r in data["released_wrestlers"] if r is not None]

        # Progression
        data["progression"] = safe_to_dict(self.progression, "progression")

        # Booking & Shows
        data["booked_show"] = safe_to_dict(self.booked_show, "booked_show")
        data["show_history"] = [safe_to_dict(s, f"show_{i}") for i, s in enumerate(self.show_history[-50:])]
        data["show_history"] = [s for s in data["show_history"] if s is not None]
        data["calendar"] = safe_to_dict(self.calendar, "calendar")
        data["production_settings"] = safe_to_dict(self.production_settings, "production")

        # Championships
        data["championship_manager"] = safe_to_dict(self.championship_manager, "championships")

        # Financials
        data["banking"] = safe_to_dict(self.banking, "banking")

        # Communication
        data["inbox"] = safe_to_dict(self.inbox, "inbox")

        # AI Systems
        data["ai_director"] = safe_to_dict(self.ai_director, "ai_director")
        data["event_generator"] = safe_to_dict(self.event_generator, "event_generator")
        data["storyline_engine"] = safe_to_dict(self.storyline_engine, "storyline_engine")
        data["news_generator"] = safe_to_dict(self.news_generator, "news_generator")
        data["rival_promotions"] = safe_to_dict(self.rival_promotions, "rival_promotions")
        data["quest_system"] = safe_to_dict(self.quest_system, "quest_system")
        data["relationship_manager"] = safe_to_dict(self.relationship_manager, "relationships")

        # Free Agency
        data["free_agency"] = safe_to_dict(self.free_agency, "free_agency")

        # Training School
        data["training_school"] = safe_to_dict(self.training_school, "training_school")
        data["coach_manager"] = safe_to_dict(self.coach_manager, "coach_manager")
        data["coach_pool"] = safe_to_dict(self.coach_pool, "coach_pool")
        data["trainee_pool"] = safe_to_dict(self.trainee_pool, "trainee_pool")
        data["trainee_show_manager"] = safe_to_dict(self.trainee_show_manager, "trainee_shows")

        # Injuries
        data["injury_manager"] = safe_to_dict(self.injury_manager, "injury_manager")

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Restore game state from dict"""
        # Lazy imports to avoid circular dependencies
        from classes.promotion import Promotion
        from classes.wrestler import Wrestler
        from classes.progression import ProgressionManager
        from classes.calendar_system import CalendarSystem
        from classes.production import ProductionManager
        from classes.championship import ChampionshipManager
        from classes.banking import BankingManager
        from classes.inbox import InboxManager
        from classes.injury import InjuryManager
        from classes.free_agency import FreeAgencyManager

        # AI
        from ai.director import AIDirector
        from ai.event_generator import EventGenerator
        from ai.storyline_engine import StorylineEngine
        from ai.commentary import CommentaryGenerator
        from ai.news_generator import NewsGenerator
        from ai.rival_promotions import RivalPromotionManager
        from ai.quest_system import QuestSystem
        from ai.relationships import RelationshipManager

        # Training School
        from classes.training_school import TrainingSchool
        from classes.coach import CoachManager
        from data.coach_pool import CoachPool
        from data.trainee_pool import TraineePool
        from classes.trainee_show import TraineeShowManager

        gs = cls()

        # Helper for safe restoration
        def safe_from_dict(klass, data_key, default_factory=None):
            try:
                d = data.get(data_key)
                if d is None:
                    return default_factory() if default_factory else None
                if hasattr(klass, "from_dict"):
                    return klass.from_dict(d)
                return default_factory() if default_factory else None
            except Exception as e:
                print(f"Error restoring {data_key}: {e}")
                return default_factory() if default_factory else None

        # Meta
        gs.game_version = data.get("game_version", "1.0.0")
        gs.session_id = data.get("session_id", "")
        gs.created_at = data.get("created_at", "")
        gs.last_saved = data.get("last_saved", "")
        gs.first_launch = data.get("first_launch", False)
        gs.tutorial_active = data.get("tutorial_active", False)
        gs.tutorial_step = data.get("tutorial_step", 0)
        gs.tutorial_skipped = data.get("tutorial_skipped", False)
        gs.origin_grant_accepted = data.get("origin_grant_accepted", False)
        gs.origin_grant_amount = data.get("origin_grant_amount", 0)

        # Core
        gs.promotion = safe_from_dict(Promotion, "promotion")

        # Roster (list of Wrestlers)
        for wd in data.get("roster", []):
            try:
                gs.roster.append(Wrestler.from_dict(wd))
            except Exception:
                pass

        for wd in data.get("free_agents", []):
            try:
                gs.free_agents.append(Wrestler.from_dict(wd))
            except Exception:
                pass

        for wd in data.get("released_wrestlers", []):
            try:
                gs.released_wrestlers.append(Wrestler.from_dict(wd))
            except Exception:
                pass

        # Progression
        gs.progression = safe_from_dict(ProgressionManager, "progression", ProgressionManager)

        # Booking & Shows
        try:
            from classes.show import Show
            gs.booked_show = safe_from_dict(Show, "booked_show")
            for sd in data.get("show_history", []):
                try:
                    gs.show_history.append(Show.from_dict(sd))
                except Exception:
                    pass
        except Exception:
            pass

        gs.calendar = safe_from_dict(CalendarSystem, "calendar", CalendarSystem)
        gs.production_settings = safe_from_dict(ProductionManager, "production_settings", ProductionManager)

        # Championships
        gs.championship_manager = safe_from_dict(ChampionshipManager, "championship_manager", ChampionshipManager)

        # Financials
        gs.banking = safe_from_dict(BankingManager, "banking", BankingManager)

        # Communication
        gs.inbox = safe_from_dict(InboxManager, "inbox", InboxManager)

        # AI Systems
        gs.ai_director = safe_from_dict(AIDirector, "ai_director", AIDirector)
        gs.event_generator = safe_from_dict(EventGenerator, "event_generator", EventGenerator)
        gs.storyline_engine = safe_from_dict(StorylineEngine, "storyline_engine", StorylineEngine)
        gs.news_generator = safe_from_dict(NewsGenerator, "news_generator", NewsGenerator)
        gs.rival_promotions = safe_from_dict(RivalPromotionManager, "rival_promotions", RivalPromotionManager)
        gs.quest_system = safe_from_dict(QuestSystem, "quest_system", QuestSystem)
        gs.relationship_manager = safe_from_dict(RelationshipManager, "relationship_manager", RelationshipManager)

        # Wire commentary generator AFTER director and storyline are loaded
        try:
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

        # Free Agency
        gs.free_agency = safe_from_dict(FreeAgencyManager, "free_agency", FreeAgencyManager)

        # Training School
        gs.training_school = safe_from_dict(TrainingSchool, "training_school", TrainingSchool)
        gs.coach_manager = safe_from_dict(CoachManager, "coach_manager", CoachManager)
        gs.coach_pool = safe_from_dict(CoachPool, "coach_pool", CoachPool)
        gs.trainee_pool = safe_from_dict(TraineePool, "trainee_pool", TraineePool)
        gs.trainee_show_manager = safe_from_dict(TraineeShowManager, "trainee_show_manager", TraineeShowManager)

        # Injuries
        gs.injury_manager = safe_from_dict(InjuryManager, "injury_manager", InjuryManager)

        return gs

    # ==================== FILE I/O ====================

    def save_to_file(self, filepath: str) -> bool:
        """Save game state to a JSON file"""
        try:
            import os
            # Ensure saves directory exists
            dir_path = os.path.dirname(filepath) if os.path.dirname(filepath) else "saves"
            os.makedirs(dir_path, exist_ok=True)

            data = self.to_dict()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load game state from a JSON file"""
        try:
            import os
            if not os.path.exists(filepath):
                print(f"Save file not found: {filepath}")
                return None

            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Load error: {e}")
            return None

    # ==================== BACKWARDS COMPATIBILITY ====================

    def save(self, save_name: str) -> bool:
        """Backwards-compatible save method for existing app.py"""
        filepath = f"saves/{save_name}.json"
        return self.save_to_file(filepath)

    def load(self, save_name: str) -> bool:
        """Backwards-compatible load method for existing app.py"""
        filepath = f"saves/{save_name}.json"
        loaded = GameState.load_from_file(filepath)
        if loaded:
            # Copy all attributes from loaded state to self
            self.__dict__.update(loaded.__dict__)
            return True
        return False

    def ensure_all_systems(self):
        """Backwards-compatible method — ensures all managers exist"""
        # Training School
        if not hasattr(self, 'training_school') or self.training_school is None:
            try:
                from classes.training_school import TrainingSchool
                self.training_school = TrainingSchool()
            except Exception:
                pass

        # Coach Manager
        if not hasattr(self, 'coach_manager') or self.coach_manager is None:
            try:
                from classes.coach import CoachManager
                self.coach_manager = CoachManager()
            except Exception:
                pass

        # Free Agency
        if not hasattr(self, 'free_agency') or self.free_agency is None:
            try:
                from classes.free_agency import FreeAgencyManager
                self.free_agency = FreeAgencyManager()
            except Exception:
                pass

        # Inbox
        if not hasattr(self, 'inbox') or self.inbox is None:
            try:
                from classes.inbox import InboxManager
                self.inbox = InboxManager()
            except Exception:
                pass

        # AI Director
        if not hasattr(self, 'ai_director') or self.ai_director is None:
            try:
                from ai.director import AIDirector
                self.ai_director = AIDirector()
            except Exception:
                pass

