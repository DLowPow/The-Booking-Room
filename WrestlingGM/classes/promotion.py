"""
Promotion Class - The player's wrestling company

A clean data container for:
- Company identity (name, initials, philosophy, location, owner)
- Finances (budget, revenue tracking)
- Roster reference
- Reputation (prestige, fan_base, tv_rating)
- Game date (year/month/day/week)
- Time progression (advance_days)

Championships, shows, events, and weekly processing are handled by
their respective managers (ChampionshipManager, AIDirector, WeeklyPulse).
"""
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from classes.wrestler import Wrestler


class Promotion:
    """The player's wrestling promotion/company"""

    def __init__(
        self,
        name: str,
        philosophy=None,
        owner_name: str = "Player",
        starting_budget: int = 0,
        location: str = "United States",
        initials: str = "",
    ):
        # FIX: was `def **init**(self, ...)` — markdown bold corruption
        # ===== Identity =====
        self.name = name
        self.initials = initials or self._auto_generate_initials(name)
        self.philosophy = philosophy  # Philosophy enum or string
        self.owner_name = owner_name
        self.location = location

        # ===== Finances =====
        self.budget = starting_budget
        self.weekly_income = 0
        self.weekly_expenses = 0
        self.total_revenue = 0
        self.total_expenses = 0

        # ===== Roster =====
        self.roster: List = []

        # ===== Reputation =====
        self.prestige = 50           # Industry respect (0-100)
        self.fan_base = 0            # Number of fans
        self.tv_rating = 0.0         # TV ratings
        self.merchandise_modifier = 1.0

        # ===== Game Date =====
        self.current_week = 1
        self.current_year = 1
        self.current_month = 1
        self.current_day = 1

        # ===== Game Log =====
        self.game_log: List[str] = []

        # Apply philosophy bonuses
        self._apply_philosophy_bonuses()

    # ============== INITIALS ==============
    @staticmethod
    def _auto_generate_initials(name: str) -> str:
        """
        Auto-generate initials from a promotion name.
        Used as a fallback if no initials provided.

        Examples:
            "World Wrestling Federation" -> "WWF"
            "Ring of Honor" -> "ROH"
            "NXT" -> "NXT"
            "Stardom" -> "STARD" (single word, first 5 chars)
        """
        if not name or not name.strip():
            return "GM"

        # Strip special chars, split by whitespace
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', name.strip())
        words = cleaned.split()

        if not words:
            return "GM"

        # Single word: take first 5 chars uppercase
        if len(words) == 1:
            return words[0][:5].upper()

        # Multiple words: first letter of each, capped at 5
        initials = ''.join(w[0].upper() for w in words if w)
        return initials[:5]

    def set_initials(self, initials: str) -> bool:
        """
        Manually set the promotion initials.
        Returns True if accepted, False if invalid.
        """
        if not initials or not initials.strip():
            return False
        # Strip and uppercase, cap at 5 chars
        cleaned = ''.join(c for c in initials.strip().upper() if c.isalnum())
        if not cleaned:
            return False
        self.initials = cleaned[:5]
        return True

    def _apply_philosophy_bonuses(self):
        """Apply starting bonuses based on philosophy"""
        if not self.philosophy:
            return
        # Get philosophy value (works for enum or string)
        phil_val = self.philosophy.value if hasattr(self.philosophy, 'value') else str(self.philosophy)

        if phil_val == "Ultraviolent":
            self.merchandise_modifier = 0.9
        elif phil_val == "Sports Entertainment":
            self.merchandise_modifier = 1.3
        elif phil_val == "Strong Style":
            self.merchandise_modifier = 1.0
            self.prestige = 60
        elif phil_val == "Lucha Libre":
            self.merchandise_modifier = 1.1

    # ============== ROSTER HELPERS ==============
    def get_available_wrestlers(self) -> List:
        """Get wrestlers who aren't injured"""
        return [w for w in self.roster if not getattr(w, 'is_injured', False)]

    def get_roster_size(self) -> int:
        """Total roster count"""
        return len(self.roster)

    def get_injured_count(self) -> int:
        """Count of injured wrestlers"""
        return sum(1 for w in self.roster if getattr(w, 'is_injured', False))

    # ============== FINANCES ==============
    def calculate_weekly_expenses(self) -> int:
        """Calculate total weekly expenses (booking fees only — no contracts at low levels)"""
        wrestler_fees = sum(
            getattr(w, 'booking_fee', getattr(w, 'salary', 0))
            for w in self.roster
        )
        misc_costs = 2000  # Office, staff, etc.
        self.weekly_expenses = wrestler_fees + misc_costs
        return self.weekly_expenses

    def calculate_weekly_income(self) -> int:
        """Calculate base weekly income (merch from fan base)"""
        # FIX: was `int(self.fan_base _0.5_ self.merchandise_modifier)` — markdown corruption
        merch = int(self.fan_base * 0.5 * self.merchandise_modifier)
        self.weekly_income = merch
        return self.weekly_income

    def add_revenue(self, amount: int):
        """Track revenue inflow"""
        self.budget += amount
        self.total_revenue += amount

    def deduct_expense(self, amount: int):
        """Track expense outflow"""
        self.budget -= amount
        self.total_expenses += amount

    # ============== TIME PROGRESSION ==============
    def advance_week(self):
        """Advance the game by 7 days"""
        self.advance_days(7)

    def advance_days(self, days: int = 1):
        """Advance by specific number of days"""
        from classes.calendar_system import days_in_month, date_to_day_of_year

        for _ in range(days):
            self.current_day += 1
            if self.current_day > days_in_month(self.current_month):
                self.current_day = 1
                self.current_month += 1
                if self.current_month > 12:
                    self.current_month = 1
                    self.current_year += 1

            # Update week counter for backward compatibility
            day_of_year = date_to_day_of_year(self.current_month, self.current_day)
            self.current_week = ((day_of_year - 1) // 7) + 1

        # Process wrestler weekly updates (aging, fatigue recovery, etc.)
        for wrestler in self.roster:
            if hasattr(wrestler, 'weekly_update'):
                try:
                    wrestler.weekly_update()
                except Exception:
                    pass

    def advance_to_date(self, year: int, month: int, day: int):
        """Jump directly to a specific date"""
        from classes.calendar_system import date_to_day_of_year

        self.current_year = year
        self.current_month = month
        self.current_day = day
        day_of_year = date_to_day_of_year(month, day)
        self.current_week = ((day_of_year - 1) // 7) + 1

    # ============== LOGGING ==============
    def log(self, message: str):
        """Add message to game log"""
        timestamp = f"[Y{self.current_year} {self.current_day:02d}/{self.current_month:02d}]"
        entry = f"{timestamp} {message}"
        self.game_log.append(entry)
        # Keep log trimmed
        if len(self.game_log) > 500:
            self.game_log = self.game_log[-500:]
        print(entry)

    # ============== UI HELPERS ==============
    def get_display_name(self, use_initials: bool = False) -> str:
        """
        Get the promotion's display name.
        If use_initials=True and initials exist, returns the initials instead.
        """
        if use_initials and self.initials:
            return self.initials
        return self.name

    def get_short_name(self) -> str:
        """
        Get a short name for use in tight UI spaces.
        Returns initials if available, otherwise the first 12 chars of name.
        """
        if self.initials:
            return self.initials
        return self.name[:12] + ('...' if len(self.name) > 12 else '')

    # ============== SAVE/LOAD ==============
    def to_dict(self) -> dict:
        """Serialize promotion to dictionary"""
        phil_val = (
            self.philosophy.value
            if hasattr(self.philosophy, 'value')
            else (str(self.philosophy) if self.philosophy else "Strong Style")
        )
        return {
            "name": self.name,
            "initials": self.initials,
            "philosophy": phil_val,
            "owner_name": self.owner_name,
            "location": self.location,
            "budget": self.budget,
            "weekly_income": self.weekly_income,
            "weekly_expenses": self.weekly_expenses,
            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "prestige": self.prestige,
            "fan_base": self.fan_base,
            "tv_rating": self.tv_rating,
            "merchandise_modifier": self.merchandise_modifier,
            "current_week": self.current_week,
            "current_year": self.current_year,
            "current_month": self.current_month,
            "current_day": self.current_day,
            "roster": [w.to_dict() for w in self.roster if hasattr(w, 'to_dict')],
            "game_log": self.game_log[-100:],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Promotion":
        """Deserialize promotion from dictionary"""
        # Try to get Philosophy enum
        philosophy = data.get("philosophy", "Strong Style")
        try:
            from classes.philosophy import Philosophy
            for p in Philosophy:
                if p.value == philosophy:
                    philosophy = p
                    break
        except Exception:
            pass

        promotion = cls(
            name=data["name"],
            philosophy=philosophy,
            owner_name=data.get("owner_name", "Player"),
            starting_budget=data.get("budget", 0),
            location=data.get("location", "United States"),
            initials=data.get("initials", ""),  # Falls back to auto-gen if missing
        )

        # Restore finances
        promotion.budget = data.get("budget", 0)
        promotion.weekly_income = data.get("weekly_income", 0)
        promotion.weekly_expenses = data.get("weekly_expenses", 0)
        promotion.total_revenue = data.get("total_revenue", 0)
        promotion.total_expenses = data.get("total_expenses", 0)

        # Restore reputation
        promotion.prestige = data.get("prestige", 50)
        promotion.fan_base = data.get("fan_base", 0)
        promotion.tv_rating = data.get("tv_rating", 0.0)
        promotion.merchandise_modifier = data.get("merchandise_modifier", 1.0)

        # Restore date
        promotion.current_week = data.get("current_week", 1)
        promotion.current_year = data.get("current_year", 1)
        promotion.current_month = data.get("current_month", 1)
        promotion.current_day = data.get("current_day", 1)

        # Restore log
        promotion.game_log = data.get("game_log", [])

        # Restore roster
        try:
            from classes.wrestler import Wrestler
            for wrestler_data in data.get("roster", []):
                try:
                    wrestler = Wrestler.from_dict(wrestler_data)
                    promotion.roster.append(wrestler)
                except Exception as e:
                    print(f"Error loading wrestler: {e}")
        except Exception:
            pass

        return promotion

    def __repr__(self) -> str:
        # FIX: was `def **repr**(self)` — markdown bold corruption
        phil = self.philosophy.value if hasattr(self.philosophy, 'value') else str(self.philosophy)
        return f"Promotion({self.name} [{self.initials}], {phil}, {len(self.roster)} wrestlers)"
