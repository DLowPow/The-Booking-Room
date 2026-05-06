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
        self.career_stats = None           # CareerStats
        self.achievements = None           # AchievementManager

        # ==================== BOOKING & SHOWS ====================
        self.booked_show = None            # Currently booked show (pre-execution)
        self.show_history: List = []       # Past shows
        self.calendar = None               # CalendarManager
        self.production_settings = None    # ProductionManager

        # ==================== CHAMPIONSHIPS ====================
        self.championship_manager = None   # ChampionshipManager
        self.tournament_manager = None     # TournamentManager (if applicable)

        # ==================== FINANCIALS ====================
        self.banking = None                # BankingManager
        self.loan_shark = None             # LoanSharkManager

        # ==================== COMMUNICATION ====================
        self.inbox = None                  # InboxManager
        self.calls = None                  # CallsManager

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
        self.game_version: str = "2.0.0"  # Bump for new architecture

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
        from classes.promotion import Promotion, Philosophy
        from classes.progression import ProgressionManager
        from classes.career_stats import CareerStats
        from classes.achievements import AchievementManager
        from classes.calendar_manager import CalendarManager
        from classes.production import ProductionManager
        from classes.championship import ChampionshipManager
        from classes.banking import BankingManager
        from classes.loan_shark import LoanSharkManager
        from classes.inbox import InboxManager
        from classes.calls import CallsManager
        from classes.injury_manager import InjuryManager

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
            phil = Philosophy.SPORTS_ENTERTAINMENT

        self.promotion = Promotion(
            name=promotion_name,
            location=location,
            philosophy=phil,
            owner_name=owner_name or "You",
            budget=0,
            fan_base=0,
            prestige=1,
        )

        # === PROGRESSION ===
        self.progression = ProgressionManager()
        self.career_stats = CareerStats()
        self.achievements = AchievementManager()

        # === BOOKING ===
        self.calendar = CalendarManager()
        self.production_settings = ProductionManager()
        self.show_history = []

        # === CHAMPIONSHIPS ===
        self.championship_manager = ChampionshipManager()

        # === FINANCIALS ===
        self.banking = BankingManager()
        self.loan_shark = LoanSharkManager()

        # === COMMUNICATION ===
        self.inbox = InboxManager()
        self.calls = CallsManager()

        # === AI DIRECTOR (the brain) ===
        self.ai_director = AIDirector(
            creative_control_enabled=creative_control_enabled,
            creative_control_difficulty=creative_control_difficulty,
            personality_type=ai_personality,
        )

        # === AI SUPPORTING SYSTEMS ===
        self.event_generator = EventGenerator()
        self.storyline_engine = StorylineEngine()
        self.commentary_generator = CommentaryGenerator(
            ai_director=self.ai_director,
            storyline_engine=self.storyline_engine,
        )
        self.news_generator = NewsGenerator(
            ai_director=self.ai_director,
            storyline_engine=self.storyline_engine,
        )
        self.rival_promotions = RivalPromotionManager()
        self.quest_system = QuestSystem()
        self.relationship_manager = RelationshipManager()

        # === TRAINING SCHOOL (not founded by default) ===
        self.training_school = TrainingSchool()
        self.coach_manager = CoachManager()
        self.coach_pool = CoachPool()
        self.trainee_pool = TraineePool()
        self.trainee_show_manager = TraineeShowManager()

        # === INJURIES ===
        self.injury_manager = InjuryManager()

        # === META ===
        self.first_launch = True
        self.tutorial_active = False
        self.tutorial_step = 0
        self.created_at = datetime.now().isoformat()

        # === GENERATE STARTER RIVALS ===
        try:
            from ai.rival_promotions import RivalSize
            self.rival_promotions.create_starter_rivals(player_size=RivalSize.BACKYARD)
        except Exception:
            pass

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
                if mark_as_indy_god and hasattr(w, "is_indy_god"):
                    w.is_indy_god = True
                self.released_wrestlers.append(w)
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
        Master weekly orchestrator. Called when player skips week or runs show.
        Coordinates ALL system updates and returns a result dict.
        """
        result = {
            "ai_events": [],
            "ai_suggestions": [],
            "storyline_updates": [],
            "news_articles": [],
            "rival_activity": {},
            "training_school": {},
            "trainee_pool_refresh": [],
            "coach_pool_refresh": [],
            "quest_updates": [],
            "relationship_changes": [],
            "messages_added": 0,
        }

        roster_dicts = self.get_roster_as_dicts()
        budget = getattr(self.promotion, "budget", 0)
        fans = getattr(self.promotion, "fan_base", 0)
        prestige = getattr(self.promotion, "prestige", 1)

        # === 1. AI DIRECTOR WEEKLY UPDATE ===
        if self.ai_director:
            try:
                ai_result = self.ai_director.process_weekly_update(
                    roster=roster_dicts,
                    budget=budget,
                    fans=fans,
                    prestige=prestige,
                    current_week=current_week,
                )
                result["ai_events"] = ai_result.get("new_events", [])
                result["ai_suggestions"] = ai_result.get("suggestions", [])
            except Exception as e:
                print(f"AI Director error: {e}")

        # === 2. STORYLINE ENGINE DECAY ===
        if self.storyline_engine:
            try:
                self.storyline_engine.weekly_update()

                # AI auto-proposes storylines based on personality
                if self.ai_director and roster_dicts:
                    chaos = self.ai_director.personality.get_chaos_factor()
                    new_storyline = self.storyline_engine.ai_propose_storyline(
                        roster=roster_dicts,
                        ai_personality_name=self.ai_director.personality.get_name(),
                        chaos_factor=chaos,
                        week=current_week,
                        year=current_year,
                    )
                    if new_storyline:
                        result["storyline_updates"].append({
                            "type": "proposed",
                            "storyline": new_storyline,
                        })

                # Auto-advance storyline beats
                if self.ai_director:
                    chaos = self.ai_director.personality.get_chaos_factor()
                    beats = self.storyline_engine.ai_advance_storylines(
                        week=current_week,
                        year=current_year,
                        chaos_factor=chaos,
                    )
                    if beats:
                        result["storyline_updates"].extend([
                            {"type": "beat", "beat": b} for b in beats
                        ])
            except Exception as e:
                print(f"Storyline engine error: {e}")

        # === 3. NEWS GENERATOR ===
        if self.news_generator and self.promotion:
            try:
                chaos = self.ai_director.personality.get_chaos_factor() if self.ai_director else 0.3
                articles = self.news_generator.generate_weekly_news(
                    roster=roster_dicts,
                    promotion_name=self.promotion.name,
                    week=current_week,
                    year=current_year,
                    chaos_factor=chaos,
                )
                result["news_articles"] = articles
            except Exception as e:
                print(f"News generator error: {e}")

        # === 4. RIVAL PROMOTIONS ===
        if self.rival_promotions:
            try:
                rival_result = self.rival_promotions.process_weekly_operations(
                    current_week=current_week,
                    current_year=current_year,
                    player_roster=roster_dicts,
                    player_free_agents=[w.to_dict() if hasattr(w, "to_dict") else {} for w in self.free_agents],
                    player_prestige=prestige,
                    player_fans=fans,
                )
                result["rival_activity"] = rival_result

                # Maybe add a new rival promotion
                from ai.rival_promotions import RivalSize
                # Determine player size based on level
                player_level = self.progression.level if self.progression else 1
                if player_level <= 10:
                    player_size = RivalSize.BACKYARD
                elif player_level <= 30:
                    player_size = RivalSize.INDIE
                elif player_level <= 50:
                    player_size = RivalSize.REGIONAL
                elif player_level <= 70:
                    player_size = RivalSize.NATIONAL
                elif player_level <= 90:
                    player_size = RivalSize.MAJOR
                else:
                    player_size = RivalSize.GLOBAL

                self.rival_promotions.maybe_create_new_rival(
                    current_week=current_week,
                    player_size=player_size,
                )
            except Exception as e:
                print(f"Rival promotions error: {e}")

        # === 5. TRAINING SCHOOL WEEKLY UPDATE ===
        if self.training_school and self.training_school.is_founded():
            try:
                # Process trainee/school weekly update
                school_result = self.training_school.weekly_update(
                    coach_manager=self.coach_manager,
                    had_trainee_show=False,  # Set to True if a show was run this week
                    current_week=current_week,
                )
                result["training_school"] = school_result

                # Refresh trainee applicant pool
                if self.trainee_pool:
                    new_applicants = self.trainee_pool.generate_weekly_applicants(
                        school_reputation=self.training_school.reputation,
                        school_capacity=self.training_school.get_capacity(),
                        current_trainees=self.training_school.get_trainee_count(),
                        monthly_tuition=self.training_school.get_monthly_tuition(),
                        week=current_week,
                        year=current_year,
                    )
                    result["trainee_pool_refresh"] = new_applicants

                # Refresh coach pool
                if self.coach_pool:
                    new_coaches = self.coach_pool.generate_weekly_coach_pool(
                        school_reputation=self.training_school.reputation,
                        current_pool_size=self.coach_pool.get_pool_count(),
                    )
                    result["coach_pool_refresh"] = new_coaches

                # Process coach weekly updates (payroll)
                if self.coach_manager:
                    coach_result = self.coach_manager.process_weekly_update(
                        school=self.training_school,
                    )
                    if "total_paid" in coach_result and self.promotion:
                        self.promotion.budget = max(0, self.promotion.budget - coach_result["total_paid"])
            except Exception as e:
                print(f"Training school error: {e}")

        # === 6. QUEST SYSTEM ===
        if self.quest_system:
            try:
                quest_updates = self.quest_system.check_progress(
                    storyline_engine=self.storyline_engine,
                    fans=fans,
                    budget=budget,
                )
                result["quest_updates"] = quest_updates
            except Exception as e:
                print(f"Quest system error: {e}")

        # === 7. RELATIONSHIP DECAY ===
        if self.relationship_manager:
            try:
                rel_changes = self.relationship_manager.weekly_decay()
                result["relationship_changes"] = rel_changes
            except Exception as e:
                print(f"Relationship manager error: {e}")

        # === 8. INJURY HEALING ===
        if self.injury_manager:
            try:
                self.injury_manager.process_weekly_healing(self.roster)
            except Exception as e:
                print(f"Injury manager error: {e}")

        return result

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
            except Exception:
                pass

        # Process storyline matches
        if self.storyline_engine and match_results:
            week = self.promotion.current_week if self.promotion else 0
            year = self.promotion.current_year if self.promotion else 1
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
                week = self.promotion.current_week
                year = self.promotion.current_year
                self.news_generator.generate_show_recap(
                    promotion_name=self.promotion.name,
                    venue=venue_name or "the venue",
                    attendance=attendance,
                    rating=avg_rating,
                    week=week,
                    year=year,
                    is_sellout=is_sellout,
                )
            except Exception:
                pass

    # ==================== TRAINING SCHOOL HELPERS ====================

    def has_training_school(self) -> bool:
        """Check if player has founded a training school"""
        return (
            self.training_school is not None
            and self.training_school.is_founded()
        )

    def get_school_summary(self) -> Optional[Dict]:
        """Get school summary if founded"""
        if not self.has_training_school():
            return None
        return self.training_school.get_summary()

    # ==================== AI DIRECTOR HELPERS ====================

    def get_ai_director_info(self) -> Optional[Dict]:
        """Get AI Director display info"""
        if not self.ai_director:
            return None
        return self.ai_director.get_director_info()

    def is_creative_control_enabled(self) -> bool:
        """Check if Creative Control mode is on"""
        if not self.ai_director:
            return False
        return self.ai_director.creative_control_enabled

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
        data["career_stats"] = safe_to_dict(self.career_stats, "career_stats")
        data["achievements"] = safe_to_dict(self.achievements, "achievements")

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
        data["loan_shark"] = safe_to_dict(self.loan_shark, "loan_shark")

        # Communication
        data["inbox"] = safe_to_dict(self.inbox, "inbox")
        data["calls"] = safe_to_dict(self.calls, "calls")

        # AI Systems
        data["ai_director"] = safe_to_dict(self.ai_director, "ai_director")
        data["event_generator"] = safe_to_dict(self.event_generator, "event_generator")
        data["storyline_engine"] = safe_to_dict(self.storyline_engine, "storyline_engine")
        data["news_generator"] = safe_to_dict(self.news_generator, "news_generator")
        data["rival_promotions"] = safe_to_dict(self.rival_promotions, "rival_promotions")
        data["quest_system"] = safe_to_dict(self.quest_system, "quest_system")
        data["relationship_manager"] = safe_to_dict(self.relationship_manager, "relationships")

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
        from classes.career_stats import CareerStats
        from classes.achievements import AchievementManager
        from classes.calendar_manager import CalendarManager
        from classes.production import ProductionManager
        from classes.championship import ChampionshipManager
        from classes.banking import BankingManager
        from classes.loan_shark import LoanSharkManager
        from classes.inbox import InboxManager
        from classes.calls import CallsManager
        from classes.injury_manager import InjuryManager

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
                return klass.from_dict(d)
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
        gs.career_stats = safe_from_dict(CareerStats, "career_stats", CareerStats)
        gs.achievements = safe_from_dict(AchievementManager, "achievements", AchievementManager)

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

        gs.calendar = safe_from_dict(CalendarManager, "calendar", CalendarManager)
        gs.production_settings = safe_from_dict(ProductionManager, "production_settings", ProductionManager)

        # Championships
        gs.championship_manager = safe_from_dict(ChampionshipManager, "championship_manager", ChampionshipManager)

        # Financials
        gs.banking = safe_from_dict(BankingManager, "banking", BankingManager)
        gs.loan_shark = safe_from_dict(LoanSharkManager, "loan_shark", LoanSharkManager)

        # Communication
        gs.inbox = safe_from_dict(InboxManager, "inbox", InboxManager)
        gs.calls = safe_from_dict(CallsManager, "calls", CallsManager)

        # AI Systems
        gs.ai_director = safe_from_dict(AIDirector, "ai_director", AIDirector)
        gs.event_generator = safe_from_dict(EventGenerator, "event_generator", EventGenerator)
        gs.storyline_engine = safe_from_dict(StorylineEngine, "storyline_engine", StorylineEngine)
        gs.news_generator = safe_from_dict(NewsGenerator, "news_generator", NewsGenerator)
        gs.rival_promotions = safe_from_dict(RivalPromotionManager, "rival_promotions", RivalPromotionManager)
        gs.quest_system = safe_from_dict(QuestSystem, "quest_system", QuestSystem)
        gs.relationship_manager = safe_from_dict(RelationshipManager, "relationship_manager", RelationshipManager)

        # Wire commentary generator AFTER director and storyline are loaded
        gs.commentary_generator = CommentaryGenerator(
            ai_director=gs.ai_director,
            storyline_engine=gs.storyline_engine,
        )

        # Wire news generator references
        if gs.news_generator:
            gs.news_generator.ai_director = gs.ai_director
            gs.news_generator.storyline_engine = gs.storyline_engine

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
            data = self.to_dict()
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            self.last_saved = datetime.now().isoformat()
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    @classmethod
    def load_from_file(cls, filepath: str) -> Optional["GameState"]:
        """Load game state from a JSON file"""
        try:
            if not os.path.exists(filepath):
                return None
            with open(filepath, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Load error: {e}")
            return None
