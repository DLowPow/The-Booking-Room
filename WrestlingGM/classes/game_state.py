"""
Game State
Central save/load container for The Booking Room.

This file is intentionally defensive:
- Old saves should still load.
- Missing systems should be rebuilt safely.
- New AI/CPU systems should not crash older saves.
"""

from __future__ import annotations

import json
import os
import traceback
from typing import Any, Dict, List, Optional


def _safe_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            return None
    return obj


def _safe_from_dict(module_path: str, class_name: str, data: Any) -> Any:
    if data is None:
        return None

    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)

        if hasattr(cls, "from_dict"):
            return cls.from_dict(data)

        obj = cls()
        if isinstance(data, dict):
            for key, value in data.items():
                try:
                    setattr(obj, key, value)
                except Exception:
                    pass
        return obj

    except Exception as e:
        print(f"Safe load failed for {module_path}.{class_name}: {e}")
        return None


class GameState:
    """
    Main game container.

    The app expects this object to own:
    - promotion
    - progression
    - ai_director
    - calendar
    - inbox
    - calls
    - injury_manager
    - banking
    - championships
    - training school systems
    - free agency
    - group manager
    - rival scheduler
    """

    SAVE_VERSION = 3

    def __init__(self):
        self.save_version = self.SAVE_VERSION

        # Core identity
        self.promoter_name: str = "Player"
        self.game_settings: Dict[str, Any] = {}

        # Core systems
        self.promotion = None
        self.progression = None
        self.ai_director = None
        self.event_generator = None
        self.voice_engine = None
        self.weekly_pulse = None

        # Player-facing systems
        self.calendar = None
        self.calendar_system = None
        self.inbox = None
        self.calls = None
        self.injury_manager = None
        self.banking = None
        self.free_agency = None
        self.free_agents: List[Any] = []

        # Championships / groups
        self.championship_manager = None
        self.group_manager = None

        # Training school
        self.training_school = None
        self.coach_manager = None
        self.coach_pool = None
        self.trainee_pool = None
        self.trainee_show_manager = None
        self.active_enrollments: List[Dict[str, Any]] = []

        # AI / living world systems
        self.ai_memory = None
        self.wrestler_minds = None
        self.living_world_history: List[Dict[str, Any]] = []
        self.rival_scheduler = None

        # Game flow
        self.booked_show = None
        self.last_show_result = None
        self.show_history: List[Dict[str, Any]] = []

        # Tutorial / story flags
        self.origin_story = None
        self.origin_grant_accepted = False
        self.origin_grant_amount = 0
        self.show_tutorial_prompt = False
        self.tutorial_active = False
        self.tutorial_step = 0
        self.tutorial_skipped = False
        self.first_launch = True

        # Free agency UI helpers
        self.weekly_agent_names: List[str] = []
        self.weekly_agents_week: str = ""

    # ==================== INITIALIZATION ====================

    def initialize_new_game(
        self,
        promotion_name: str,
        location: str,
        philosophy: str = "Strong Style",
        owner_name: str = "Player",
        creative_control_enabled: bool = False,
        creative_control_difficulty: str = "Normal",
        ai_personality: str = "The Traditionalist",
    ):
        """Create a new game with all major systems initialized."""
        self.promoter_name = owner_name

        from classes.promotion import Promotion
        from classes.progression import ProgressionSystem
        from classes.philosophy import Philosophy

        philosophy_value = philosophy
        try:
            for p in Philosophy:
                if p.value == philosophy:
                    philosophy_value = p
                    break
        except Exception:
            pass

        self.promotion = Promotion(
            name=promotion_name,
            philosophy=philosophy_value,
            owner_name=owner_name,
            starting_budget=0,
            location=location,
        )

        self.progression = ProgressionSystem()

        self._init_ai_director(
            creative_control_enabled,
            creative_control_difficulty,
            ai_personality,
        )

        self._init_calendar()
        self._init_inbox()
        self._init_calls()
        self._init_championship_manager()
        self._init_banking()
        self._init_injury_manager()
        self._init_training_school()
        self._init_coach_manager()
        self._init_free_agency()
        self._init_group_manager()
        self._init_rival_scheduler()

        self.active_enrollments = []
        self.show_history = []
        self.living_world_history = []

        return self

    # ==================== SYSTEM INIT HELPERS ====================

    def _init_ai_director(
        self,
        creative_control_enabled: bool = False,
        creative_control_difficulty: str = "Normal",
        ai_personality: str = "The Traditionalist",
    ):
        try:
            from ai.director import AIDirector

            try:
                self.ai_director = AIDirector(
                    creative_control_enabled=creative_control_enabled,
                    creative_control_difficulty=creative_control_difficulty,
                    personality=ai_personality,
                )
            except TypeError:
                try:
                    self.ai_director = AIDirector(
                        creative_control_enabled=creative_control_enabled,
                        creative_control_difficulty=creative_control_difficulty,
                    )
                except TypeError:
                    self.ai_director = AIDirector()

        except Exception as e:
            print(f"AI Director init error: {e}")
            self.ai_director = None

    def _init_calendar(self):
        try:
            from classes.calendar_system import CalendarSystem

            self.calendar = CalendarSystem()
            self.calendar_system = self.calendar
        except Exception as e:
            print(f"Calendar init error: {e}")
            self.calendar = None
            self.calendar_system = None

    def _init_inbox(self):
        try:
            from classes.inbox import InboxManager

            self.inbox = InboxManager()
        except Exception as e:
            print(f"Inbox init error: {e}")
            self.inbox = None

    def _init_calls(self):
        try:
            from classes.calls import CallsManager

            self.calls = CallsManager()
        except Exception as e:
            print(f"Calls init error: {e}")
            self.calls = None

    def _init_championship_manager(self):
        try:
            from classes.championship import ChampionshipManager

            self.championship_manager = ChampionshipManager()

            try:
                self.championship_manager.setup_default_accolades()
            except Exception:
                pass

        except Exception as e:
            print(f"Championship init error: {e}")
            self.championship_manager = None

    def _init_banking(self):
        try:
            from classes.banking import BankingManager

            self.banking = BankingManager()
        except Exception as e:
            print(f"Banking init error: {e}")
            self.banking = None

    def _init_injury_manager(self):
        try:
            from classes.injury import InjuryManager

            self.injury_manager = InjuryManager()
        except Exception as e:
            print(f"Injury init error: {e}")
            self.injury_manager = None

    def _init_training_school(self):
        try:
            from classes.training_school import TrainingSchool

            self.training_school = TrainingSchool()
        except Exception as e:
            print(f"Training school init error: {e}")
            self.training_school = None

    def _init_coach_manager(self):
        try:
            from classes.coach import CoachManager
            from data.coach_pool import CoachPool

            self.coach_manager = CoachManager()
            self.coach_pool = CoachPool()
        except Exception as e:
            print(f"Coach init error: {e}")
            self.coach_manager = None
            self.coach_pool = None

    def _init_free_agency(self):
        try:
            from classes.free_agency import FreeAgencyManager
            from data.wrestler_pool import generate_free_agents

            self.free_agency = FreeAgencyManager()

            # Generate starter free agents
            agents = generate_free_agents(count=50, level=1)
            self.free_agents = agents

            # Push them into FreeAgencyManager if it supports it
            if hasattr(self.free_agency, "populate_from_wrestlers"):
                self.free_agency.populate_from_wrestlers(agents)
            elif hasattr(self.free_agency, "add_wrestler"):
                for wrestler in agents:
                    self.free_agency.add_wrestler(wrestler)
            elif hasattr(self.free_agency, "listings"):
                self.free_agency.listings = []

                try:
                    from classes.free_agency import AgentListing, FreeAgentTier

                    for wrestler in agents:
                        tier = FreeAgentTier.ROOKIE
                        listing = AgentListing(wrestler=wrestler, tier=tier)
                        self.free_agency.listings.append(listing)
                except Exception:
                    pass

        except Exception as e:
            print(f"Free agency init error: {e}")
            self.free_agency = None
            self.free_agents = []

    def _init_group_manager(self):
        try:
            from classes.group import GroupManager

            self.group_manager = GroupManager()
        except Exception as e:
            print(f"Group manager init error: {e}")
            self.group_manager = None

    def _init_rival_scheduler(self):
        try:
            from ai.rival_scheduler import RivalScheduler

            self.rival_scheduler = RivalScheduler()
        except Exception as e:
            print(f"Rival scheduler init error: {e}")
            self.rival_scheduler = None

    # ==================== MIGRATION SAFETY ====================

    def ensure_all_systems(self):
        """
        Ensure all managers exist after loading older saves.

        This method is intentionally defensive. If one optional system fails,
        the game should still load.
        """
        if not hasattr(self, "game_settings") or self.game_settings is None:
            self.game_settings = {}

        if not hasattr(self, "free_agents") or self.free_agents is None:
            self.free_agents = []

        if not hasattr(self, "show_history") or self.show_history is None:
            self.show_history = []

        if not hasattr(self, "living_world_history") or self.living_world_history is None:
            self.living_world_history = []

        if not hasattr(self, "active_enrollments") or self.active_enrollments is None:
            self.active_enrollments = []

        if not hasattr(self, "weekly_agent_names") or self.weekly_agent_names is None:
            self.weekly_agent_names = []

        if not hasattr(self, "weekly_agents_week"):
            self.weekly_agents_week = ""

        if not hasattr(self, "calendar_system"):
            self.calendar_system = None

        if self.calendar is None and self.calendar_system is not None:
            self.calendar = self.calendar_system

        if self.calendar is None:
            self._init_calendar()

        self.calendar_system = self.calendar

        if self.progression is None:
            try:
                from classes.progression import ProgressionSystem

                self.progression = ProgressionSystem()
            except Exception:
                self.progression = None

        if self.ai_director is None:
            self._init_ai_director(False, "Normal", "The Traditionalist")

        if self.inbox is None:
            self._init_inbox()

        if self.calls is None:
            self._init_calls()

        if self.championship_manager is None:
            self._init_championship_manager()

        if self.banking is None:
            self._init_banking()

        if self.injury_manager is None:
            self._init_injury_manager()

        if self.training_school is None:
            self._init_training_school()

        if self.coach_manager is None or self.coach_pool is None:
            self._init_coach_manager()

        if self.free_agency is None:
            self._init_free_agency()

        if self.group_manager is None:
            self._init_group_manager()

        # Rival Scheduler - scripted CPU rival intro and calendar
        if not hasattr(self, "rival_scheduler") or self.rival_scheduler is None:
            self._init_rival_scheduler()

        if not hasattr(self, "booked_show"):
            self.booked_show = None

        if not hasattr(self, "last_show_result"):
            self.last_show_result = None

        return self

    # ==================== GAMEPLAY HELPERS ====================

    def has_training_school(self) -> bool:
        school = getattr(self, "training_school", None)
        if not school:
            return False

        try:
            return bool(school.is_founded())
        except Exception:
            pass

        try:
            status = getattr(school, "status", None)
            if hasattr(status, "value"):
                return status.value.lower() not in ["not founded", "closed"]
            return str(status).lower() not in ["none", "not founded", "closed"]
        except Exception:
            return False

    def get_ai_director_info(self) -> Dict[str, Any]:
        ai = getattr(self, "ai_director", None)
        if not ai:
            return {
                "enabled": False,
                "personality": "None",
                "creative_control": False,
                "difficulty": "Normal",
            }

        return {
            "enabled": True,
            "personality": getattr(ai, "personality", getattr(ai, "personality_type", "Unknown")),
            "creative_control": getattr(ai, "creative_control_enabled", False),
            "difficulty": getattr(ai, "creative_control_difficulty", "Normal"),
        }

    def process_weekly_pulse(self, week: int = 0, year: int = 1) -> Dict[str, Any]:
        """
        Weekly orchestrator wrapper used by app.py.

        Living World does not run here anymore. RivalScheduler is show/date based.
        """
        result = {
            "week": week,
            "year": year,
            "messages": [],
            "events": [],
        }

        try:
            if self.weekly_pulse is None:
                try:
                    from systems.weekly_pulse import WeeklyPulse

                    self.weekly_pulse = WeeklyPulse()
                except Exception:
                    self.weekly_pulse = None

            if self.weekly_pulse:
                if hasattr(self.weekly_pulse, "process_week"):
                    pulse = self.weekly_pulse.process_week(self, week, year)
                elif hasattr(self.weekly_pulse, "run"):
                    pulse = self.weekly_pulse.run(self, week, year)
                else:
                    pulse = None

                if isinstance(pulse, dict):
                    result.update(pulse)

        except Exception as e:
            print(f"Weekly pulse error: {e}")

        return result

    def record_show_completion(
        self,
        avg_rating: float,
        attendance: int,
        is_sellout: bool,
        profit: int,
        venue_name: str,
        match_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Stores player show history and gives AI systems a clean hook.
        """
        promotion = getattr(self, "promotion", None)

        show_record = {
            "avg_rating": avg_rating,
            "attendance": attendance,
            "is_sellout": is_sellout,
            "profit": profit,
            "venue_name": venue_name,
            "match_results": match_results or [],
            "year": getattr(promotion, "current_year", 1),
            "month": getattr(promotion, "current_month", 1),
            "day": getattr(promotion, "current_day", 1),
            "week": getattr(promotion, "current_week", 0),
        }

        if not hasattr(self, "show_history") or self.show_history is None:
            self.show_history = []

        self.show_history.append(show_record)
        self.show_history = self.show_history[-100:]

        self.last_show_result = show_record

        try:
            if self.ai_director and hasattr(self.ai_director, "record_show"):
                self.ai_director.record_show(show_record)
        except Exception:
            pass

        return show_record

    # ==================== SAVE / LOAD ====================

    def to_dict(self) -> Dict[str, Any]:
        self.ensure_all_systems()

        return {
            "save_version": self.SAVE_VERSION,
            "promoter_name": self.promoter_name,
            "game_settings": self.game_settings,

            "promotion": _safe_to_dict(self.promotion),
            "progression": _safe_to_dict(self.progression),
            "ai_director": _safe_to_dict(self.ai_director),
            "event_generator": _safe_to_dict(self.event_generator),
            "voice_engine": _safe_to_dict(self.voice_engine),
            "weekly_pulse": _safe_to_dict(self.weekly_pulse),

            "calendar": _safe_to_dict(self.calendar),
            "inbox": _safe_to_dict(self.inbox),
            "calls": _safe_to_dict(self.calls),
            "injury_manager": _safe_to_dict(self.injury_manager),
            "banking": _safe_to_dict(self.banking),
            "free_agency": _safe_to_dict(self.free_agency),
            "free_agents": [
                _safe_to_dict(w)
                for w in (self.free_agents or [])
            ],

            "championship_manager": _safe_to_dict(self.championship_manager),
            "group_manager": _safe_to_dict(self.group_manager),

            "training_school": _safe_to_dict(self.training_school),
            "coach_manager": _safe_to_dict(self.coach_manager),
            "coach_pool": _safe_to_dict(self.coach_pool),
            "trainee_pool": _safe_to_dict(self.trainee_pool),
            "trainee_show_manager": _safe_to_dict(self.trainee_show_manager),
            "active_enrollments": self.active_enrollments or [],

            "ai_memory": _safe_to_dict(self.ai_memory),
            "wrestler_minds": _safe_to_dict(self.wrestler_minds),
            "living_world_history": self.living_world_history or [],
            "rival_scheduler": _safe_to_dict(self.rival_scheduler),

            "booked_show": self.booked_show,
            "last_show_result": self.last_show_result,
            "show_history": self.show_history[-100:] if self.show_history else [],

            "origin_story": self.origin_story,
            "origin_grant_accepted": self.origin_grant_accepted,
            "origin_grant_amount": self.origin_grant_amount,
            "show_tutorial_prompt": self.show_tutorial_prompt,
            "tutorial_active": self.tutorial_active,
            "tutorial_step": self.tutorial_step,
            "tutorial_skipped": self.tutorial_skipped,
            "first_launch": self.first_launch,

            "weekly_agent_names": self.weekly_agent_names or [],
            "weekly_agents_week": self.weekly_agents_week or "",
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        gs = cls()

        gs.save_version = data.get("save_version", 1)
        gs.promoter_name = data.get("promoter_name", "Player")
        gs.game_settings = data.get("game_settings", {}) or {}

        gs.promotion = _safe_from_dict("classes.promotion", "Promotion", data.get("promotion"))
        gs.progression = _safe_from_dict("classes.progression", "ProgressionSystem", data.get("progression"))
        gs.ai_director = _safe_from_dict("ai.director", "AIDirector", data.get("ai_director"))
        gs.event_generator = data.get("event_generator")
        gs.voice_engine = data.get("voice_engine")
        gs.weekly_pulse = None

        gs.calendar = _safe_from_dict("classes.calendar_system", "CalendarSystem", data.get("calendar"))
        gs.calendar_system = gs.calendar
        gs.inbox = _safe_from_dict("classes.inbox", "InboxManager", data.get("inbox"))
        gs.calls = _safe_from_dict("classes.calls", "CallsManager", data.get("calls"))
        gs.injury_manager = _safe_from_dict("classes.injury", "InjuryManager", data.get("injury_manager"))
        gs.banking = _safe_from_dict("classes.banking", "BankingManager", data.get("banking"))
        gs.free_agency = _safe_from_dict("classes.free_agency", "FreeAgencyManager", data.get("free_agency"))

        gs.free_agents = []
        for item in data.get("free_agents", []) or []:
            wrestler = _safe_from_dict("classes.wrestler", "Wrestler", item)
            if wrestler:
                gs.free_agents.append(wrestler)

        gs.championship_manager = _safe_from_dict(
            "classes.championship",
            "ChampionshipManager",
            data.get("championship_manager"),
        )
        gs.group_manager = _safe_from_dict("classes.group", "GroupManager", data.get("group_manager"))

        gs.training_school = _safe_from_dict("classes.training_school", "TrainingSchool", data.get("training_school"))
        gs.coach_manager = _safe_from_dict("classes.coach", "CoachManager", data.get("coach_manager"))
        gs.coach_pool = _safe_from_dict("data.coach_pool", "CoachPool", data.get("coach_pool"))
        gs.trainee_pool = _safe_from_dict("data.trainee_pool", "TraineePool", data.get("trainee_pool"))
        gs.trainee_show_manager = _safe_from_dict(
            "classes.trainee_show",
            "TraineeShowManager",
            data.get("trainee_show_manager"),
        )
        gs.active_enrollments = data.get("active_enrollments", []) or []

        gs.ai_memory = data.get("ai_memory")
        gs.wrestler_minds = data.get("wrestler_minds")
        gs.living_world_history = data.get("living_world_history", []) or []
        gs.rival_scheduler = _safe_from_dict(
            "ai.rival_scheduler",
            "RivalScheduler",
            data.get("rival_scheduler"),
        )

        gs.booked_show = data.get("booked_show")
        gs.last_show_result = data.get("last_show_result")
        gs.show_history = data.get("show_history", []) or []

        gs.origin_story = data.get("origin_story")
        gs.origin_grant_accepted = data.get("origin_grant_accepted", False)
        gs.origin_grant_amount = data.get("origin_grant_amount", 0)
        gs.show_tutorial_prompt = data.get("show_tutorial_prompt", False)
        gs.tutorial_active = data.get("tutorial_active", False)
        gs.tutorial_step = data.get("tutorial_step", 0)
        gs.tutorial_skipped = data.get("tutorial_skipped", False)
        gs.first_launch = data.get("first_launch", True)

        gs.weekly_agent_names = data.get("weekly_agent_names", []) or []
        gs.weekly_agents_week = data.get("weekly_agents_week", "") or ""

        gs.ensure_all_systems()
        return gs

    def save_to_file(self, filepath: str) -> bool:
        try:
            folder = os.path.dirname(filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Save failed: {e}")
            traceback.print_exc()
            return False

    @classmethod
    def load_from_file(cls, filepath: str) -> Optional["GameState"]:
        try:
            if not os.path.exists(filepath):
                print(f"Save file not found: {filepath}")
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            return cls.from_dict(data)

        except Exception as e:
            print(f"Load failed: {e}")
            traceback.print_exc()
            return None
