"""
Rival Scheduler - scripted rival introduction and long-term CPU calendar logic.

This system controls the first visible rival experience:

Show 1:
- Rival appears.
- Rival runs the same day as the player.
- Player receives a mysterious first message.

Show 2:
- Rival runs the same day again.
- Rival warns player to stop running the same day.

Show 3:
- Rival adapts and runs 2 days after the player.
- After this, rival becomes a normal CPU competitor.

After Show 3:
- Rival books shows roughly every 3-6 weeks.
- Rival date/venue can be previewed during venue selection.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


RIVAL_INTRO_MESSAGES = {
    1: {
        "sender": "Unknown Promoter",
        "subject": "Finally...",
        "body": (
            "Oooh, there's a new show in town. "
            "Finally, some competition."
        ),
        "icon": "👁️",
    },
    2: {
        "sender": "Unknown Promoter",
        "subject": "A Word Of Advice",
        "body": (
            "Hey. Stop running shows the same day as mine. "
            "There are only so many fans in this town."
        ),
        "icon": "⚠️",
    },
    3: {
        "sender": "Unknown Promoter",
        "subject": "Fine.",
        "body": (
            "You want the spotlight that badly? Fine. "
            "I'll take the weekend after and let the fans compare us properly."
        ),
        "icon": "🎭",
    },
}


RIVAL_PROMO_NAMES = [
    "Underground Wrestling Alliance",
    "Steel Town Wrestling",
    "Shadow Circuit Wrestling",
    "Iron Fist Wrestling",
    "Concrete Jungle Combat",
]


RIVAL_VENUES = [
    "Local Bingo Hall",
    "Community Center",
    "VFW Hall",
    "Old Sports Club",
    "Warehouse Arena",
    "Downtown Rec Hall",
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

    def to_dict(self) -> dict:
        return {
            "show_id": self.show_id,
            "rival_name": self.rival_name,
            "day": self.day,
            "month": self.month,
            "year": self.year,
            "venue": self.venue,
            "reason": self.reason,
            "completed": self.completed,
            "attendance": self.attendance,
            "rating": self.rating,
            "fan_reaction": self.fan_reaction,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledRivalShow":
        return cls(
            show_id=data.get("show_id", ""),
            rival_name=data.get("rival_name", "Unknown Rival"),
            day=data.get("day", 1),
            month=data.get("month", 1),
            year=data.get("year", 1),
            venue=data.get("venue", "Local Venue"),
            reason=data.get("reason", ""),
            completed=data.get("completed", False),
            attendance=data.get("attendance", 0),
            rating=data.get("rating", 0.0),
            fan_reaction=data.get("fan_reaction", ""),
        )


class RivalScheduler:
    """
    Controls the visible rival timeline.
    """

    def __init__(self):
        self.active: bool = True
        self.rival_name: str = random.choice(RIVAL_PROMO_NAMES)
        self.rival_identity_revealed: bool = False

        self.player_completed_shows: int = 0
        self.intro_stage: int = 0

        self.scheduled_shows: List[ScheduledRivalShow] = []
        self.completed_shows: List[ScheduledRivalShow] = []

        self.next_rival_show_day: Optional[int] = None
        self.next_rival_show_month: Optional[int] = None
        self.next_rival_show_year: Optional[int] = None
        self.next_rival_show_venue: Optional[str] = None

        self.last_player_show_day: Optional[int] = None
        self.last_player_show_month: Optional[int] = None
        self.last_player_show_year: Optional[int] = None

    # ==================== PUBLIC API ====================

    def on_player_show_completed(self, game_state, show_result: Optional[Dict] = None) -> Dict:
        """
        Call this after the player completes a show.

        Creates scripted rival behaviour for the first 3 player shows,
        then moves into dynamic scheduling.
        """
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
            created_show = self.schedule_rival_show(
                day=day,
                month=month,
                year=year,
                reason="intro_same_day_show_1",
            )
            created_show.completed = True
            self._simulate_rival_show_result(created_show)
            message = self._send_intro_message(game_state, 1)

        elif self.player_completed_shows == 2:
            created_show = self.schedule_rival_show(
                day=day,
                month=month,
                year=year,
                reason="intro_same_day_show_2",
            )
            created_show.completed = True
            self._simulate_rival_show_result(created_show)
            message = self._send_intro_message(game_state, 2)

        elif self.player_completed_shows == 3:
            future_date = self._add_days(day, month, year, 2)
            created_show = self.schedule_rival_show(
                day=future_date["day"],
                month=future_date["month"],
                year=future_date["year"],
                reason="intro_two_days_after_show_3",
            )
            message = self._send_intro_message(game_state, 3)

            self.plan_next_regular_rival_show(
                start_day=future_date["day"],
                start_month=future_date["month"],
                start_year=future_date["year"],
            )

        else:
            # After the intro, the rival reacts to player dates but does not spam messages.
            self._react_to_player_show_date(game_state, day, month, year)

            if not self.has_upcoming_show_after(day, month, year):
                self.plan_next_regular_rival_show(day, month, year)

        return {
            "created": created_show is not None,
            "rival_show": created_show.to_dict() if created_show else None,
            "message_sent": message is not None,
            "player_completed_shows": self.player_completed_shows,
        }

    def get_calendar_events(self) -> List[Dict]:
        """
        Returns rival shows in a calendar-friendly format.
        """
        events = []

        for show in self.scheduled_shows + self.completed_shows:
            events.append({
                "type": "rival_show",
                "title": show.rival_name,
                "day": show.day,
                "month": show.month,
                "year": show.year,
                "venue": show.venue,
                "completed": show.completed,
                "rating": show.rating,
                "attendance": show.attendance,
                "reason": show.reason,
                "color": "#ef4444",
                "icon": "⚔️",
            })

        return events

    def get_next_rival_show_preview(self) -> Optional[Dict]:
        """
        Used later by the venue selection screen.
        """
        upcoming = self.get_upcoming_shows()
        if not upcoming:
            return None

        show = upcoming[0]
        return {
            "rival_name": show.rival_name,
            "day": show.day,
            "month": show.month,
            "year": show.year,
            "venue": show.venue,
            "message": (
                f"{show.rival_name} is currently planning a show at "
                f"{show.venue} on {show.day}/{show.month}/Y{show.year}."
            ),
        }

    def get_upcoming_shows(self) -> List[ScheduledRivalShow]:
        return [show for show in self.scheduled_shows if not show.completed]

    def complete_due_rival_shows(self, game_state) -> List[Dict]:
        """
        Mark rival shows complete if the current calendar date has reached them.
        """
        promotion = getattr(game_state, "promotion", None)
        if not promotion:
            return []

        current_day = getattr(promotion, "current_day", 1)
        current_month = getattr(promotion, "current_month", 1)
        current_year = getattr(promotion, "current_year", 1)

        completed_now = []

        for show in self.scheduled_shows[:]:
            if self._date_lte(show.day, show.month, show.year, current_day, current_month, current_year):
                show.completed = True
                self._simulate_rival_show_result(show)

                self.scheduled_shows.remove(show)
                self.completed_shows.append(show)
                completed_now.append(show.to_dict())

                self.plan_next_regular_rival_show(show.day, show.month, show.year)

        return completed_now

    # ==================== SCHEDULING ====================

    def schedule_rival_show(self, day: int, month: int, year: int, reason: str = "") -> ScheduledRivalShow:
        show = ScheduledRivalShow(
            show_id=f"rival_show_{year}_{month}_{day}_{len(self.scheduled_shows) + len(self.completed_shows) + 1}",
            rival_name=self.rival_name,
            day=day,
            month=month,
            year=year,
            venue=random.choice(RIVAL_VENUES),
            reason=reason,
        )

        if show.completed:
            self.completed_shows.append(show)
        else:
            self.scheduled_shows.append(show)

        return show

    def plan_next_regular_rival_show(self, start_day: int, start_month: int, start_year: int) -> ScheduledRivalShow:
        gap = random.randint(21, 42)
        date = self._add_days(start_day, start_month, start_year, gap)

        show = self.schedule_rival_show(
            day=date["day"],
            month=date["month"],
            year=date["year"],
            reason="regular_cpu_show",
        )

        self.next_rival_show_day = show.day
        self.next_rival_show_month = show.month
        self.next_rival_show_year = show.year
        self.next_rival_show_venue = show.venue

        return show

    def has_upcoming_show_after(self, day: int, month: int, year: int) -> bool:
        for show in self.get_upcoming_shows():
            if not self._date_lte(show.day, show.month, show.year, day, month, year):
                return True
        return False

    # ==================== REACTIONS ====================

    def _react_to_player_show_date(self, game_state, day: int, month: int, year: int):
        """
        Future hook:
        Rival can react if player books same day, close date, or avoids them.
        For now this only stores behaviour-ready data.
        """
        upcoming = self.get_upcoming_shows()
        if not upcoming:
            return

        next_show = upcoming[0]

        same_day = (
            next_show.day == day and
            next_show.month == month and
            next_show.year == year
        )

        if same_day:
            self._send_custom_message(
                game_state,
                sender=self.rival_name if self.rival_identity_revealed else "Unknown Promoter",
                subject="You're Doing This Again?",
                body=(
                    "Same day again? Fine. If you want a fight for the fans, "
                    "I'll give you one."
                ),
                icon="⚔️",
            )

    def _send_intro_message(self, game_state, stage: int):
        data = RIVAL_INTRO_MESSAGES.get(stage)
        if not data:
            return None

        self.intro_stage = max(self.intro_stage, stage)

        return self._send_custom_message(
            game_state,
            sender=data["sender"],
            subject=data["subject"],
            body=data["body"],
            icon=data["icon"],
        )

    def _send_custom_message(self, game_state, sender: str, subject: str, body: str, icon: str = "📨"):
        inbox = getattr(game_state, "inbox", None)
        promotion = getattr(game_state, "promotion", None)

        if not inbox or not promotion:
            return None

        try:
            inbox.add_message(
                sender=sender,
                subject=subject,
                body=body,
                year=getattr(promotion, "current_year", 1),
                month=getattr(promotion, "current_month", 1),
                day=getattr(promotion, "current_day", 1),
                message_type="rival",
                icon=icon,
            )
            return True
        except TypeError:
            try:
                inbox.add_message(sender, subject, body)
                return True
            except Exception:
                return None
        except Exception:
            return None

    # ==================== RESULT SIMULATION ====================

    def _simulate_rival_show_result(self, show: ScheduledRivalShow):
        """
        Simulates rival result. Later this can use actual rival roster strength.
        """
        show.attendance = random.randint(80, 450)

        base_rating = random.uniform(1.8, 3.6)

        if show.reason == "intro_same_day_show_1":
            base_rating += 0.1
        elif show.reason == "intro_same_day_show_2":
            base_rating += 0.2
        elif show.reason == "intro_two_days_after_show_3":
            base_rating += 0.3

        show.rating = round(max(1.0, min(5.0, base_rating)), 1)

        if show.rating >= 3.5:
            show.fan_reaction = "Fans are starting to notice them."
        elif show.rating <= 2.0:
            show.fan_reaction = "Fans were not impressed."
        else:
            show.fan_reaction = "The show created mild local buzz."

    # ==================== DATE HELPERS ====================

    def _add_days(self, day: int, month: int, year: int, days_to_add: int) -> Dict[str, int]:
        """
        Simple 28-day month calendar because the game calendar appears month-based.
        If your game uses real month lengths later, we can upgrade this.
        """
        day += days_to_add

        while day > 28:
            day -= 28
            month += 1

            if month > 12:
                month = 1
                year += 1

        return {
            "day": day,
            "month": month,
            "year": year,
        }

    def _date_lte(
        self,
        day_a: int,
        month_a: int,
        year_a: int,
        day_b: int,
        month_b: int,
        year_b: int,
    ) -> bool:
        if year_a != year_b:
            return year_a < year_b
        if month_a != month_b:
            return month_a < month_b
        return day_a <= day_b

    # ==================== SAVE / LOAD ====================

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "rival_name": self.rival_name,
            "rival_identity_revealed": self.rival_identity_revealed,
            "player_completed_shows": self.player_completed_shows,
            "intro_stage": self.intro_stage,
            "scheduled_shows": [show.to_dict() for show in self.scheduled_shows],
            "completed_shows": [show.to_dict() for show in self.completed_shows[-50:]],
            "next_rival_show_day": self.next_rival_show_day,
            "next_rival_show_month": self.next_rival_show_month,
            "next_rival_show_year": self.next_rival_show_year,
            "next_rival_show_venue": self.next_rival_show_venue,
            "last_player_show_day": self.last_player_show_day,
            "last_player_show_month": self.last_player_show_month,
            "last_player_show_year": self.last_player_show_year,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RivalScheduler":
        scheduler = cls()

        scheduler.active = data.get("active", True)
        scheduler.rival_name = data.get("rival_name", scheduler.rival_name)
        scheduler.rival_identity_revealed = data.get("rival_identity_revealed", False)
        scheduler.player_completed_shows = data.get("player_completed_shows", 0)
        scheduler.intro_stage = data.get("intro_stage", 0)

        scheduler.scheduled_shows = [
            ScheduledRivalShow.from_dict(item)
            for item in data.get("scheduled_shows", [])
        ]

        scheduler.completed_shows = [
            ScheduledRivalShow.from_dict(item)
            for item in data.get("completed_shows", [])
        ]

        scheduler.next_rival_show_day = data.get("next_rival_show_day")
        scheduler.next_rival_show_month = data.get("next_rival_show_month")
        scheduler.next_rival_show_year = data.get("next_rival_show_year")
        scheduler.next_rival_show_venue = data.get("next_rival_show_venue")

        scheduler.last_player_show_day = data.get("last_player_show_day")
        scheduler.last_player_show_month = data.get("last_player_show_month")
        scheduler.last_player_show_year = data.get("last_player_show_year")

        return scheduler
