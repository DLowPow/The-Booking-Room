"""
Promotion Class - The player's wrestling company
"""

import random
from typing import List, Dict, Optional
from classes.enums import Philosophy, WrestlingStyle
from classes.wrestler import Wrestler


class Championship:
    """Represents a championship title"""
    
    def __init__(
        self,
        name: str,
        prestige: int = 50,
        weight_class_restriction: Optional[str] = None,
        gender_restriction: Optional[str] = None,
        is_tag_title: bool = False,
    ):
        self.name = name
        self.prestige = prestige
        self.weight_class_restriction = weight_class_restriction
        self.gender_restriction = gender_restriction
        self.is_tag_title = is_tag_title
        self.current_holder: Optional[str] = None  # Wrestler name
        self.title_history: List[Dict] = []
        self.days_held: int = 0
        self.defenses: int = 0
    
    def award_title(self, wrestler_name: str, date: str = "Week 1"):
        """Award title to a new champion"""
        if self.current_holder:
            # Record previous reign
            self.title_history.append({
                "champion": self.current_holder,
                "days_held": self.days_held,
                "defenses": self.defenses,
                "lost_to": wrestler_name,
                "date_lost": date
            })
        
        self.current_holder = wrestler_name
        self.days_held = 0
        self.defenses = 0
    
    def record_defense(self):
        """Record a successful title defense"""
        self.defenses += 1
        self.prestige = min(100, self.prestige + 1)
    
    def vacate(self):
        """Vacate the championship"""
        if self.current_holder:
            self.title_history.append({
                "champion": self.current_holder,
                "days_held": self.days_held,
                "defenses": self.defenses,
                "lost_to": "VACATED",
                "date_lost": "Unknown"
            })
        self.current_holder = None
        self.days_held = 0
        self.defenses = 0
        self.prestige = max(1, self.prestige - 10)
    
    def weekly_update(self):
        """Process weekly changes"""
        if self.current_holder:
            self.days_held += 7


class Show:
    """Represents a weekly show or PPV"""
    
    def __init__(
        self,
        name: str,
        is_ppv: bool = False,
        capacity: int = 5000,
        ticket_price: int = 25,
        broadcast_deal: int = 0,  # Weekly TV money
    ):
        self.name = name
        self.is_ppv = is_ppv
        self.capacity = capacity
        self.ticket_price = ticket_price
        self.broadcast_deal = broadcast_deal
        self.match_slots = 7 if is_ppv else 5


class Promotion:
    """Main promotion/company class"""
    
    def __init__(
        self,
        name: str,
        philosophy: Philosophy,
        owner_name: str = "Player",
        starting_budget: int = 100000,
        location: str = "United States",
    ):
        # Identity
        self.name = name
        self.philosophy = philosophy
        self.owner_name = owner_name
        self.location = location
        
        # Finances
        self.budget = starting_budget
        self.weekly_income = 0
        self.weekly_expenses = 0
        self.total_revenue = 0
        self.total_expenses = 0
        
        # Roster
        self.roster: List[Wrestler] = []
        self.free_agents_interested: List[Wrestler] = []
        
        # Championships
        self.championships: List[Championship] = []
        
        # Shows
        self.shows: List[Show] = []
        self.ppv_schedule: List[str] = []
        
        # Reputation
        self.prestige = 50           # Industry respect
        self.fan_base = 1000         # Number of fans
        self.tv_rating = 0.0         # TV ratings
        self.merchandise_modifier = 1.0
        
        # Game State
        self.current_month = 1
        self.current_day = 1
        self.game_log: List[str] = []
        
        # Philosophy bonuses
        self._apply_philosophy_bonuses()
    
    def _apply_philosophy_bonuses(self):
        """Apply starting bonuses based on philosophy"""
        if self.philosophy == Philosophy.ULTRAVIOLENT:
            self.merchandise_modifier = 0.9
            self.fan_base = 800
            # Hardcore fans are loyal
        elif self.philosophy == Philosophy.SPORTS_ENTERTAINMENT:
            self.merchandise_modifier = 1.3
            self.fan_base = 1500
            # Mainstream appeal
        elif self.philosophy == Philosophy.STRONG_STYLE:
            self.merchandise_modifier = 1.0
            self.fan_base = 1000
            self.prestige = 60
            # Respected by industry
        elif self.philosophy == Philosophy.LUCHA:
            self.merchandise_modifier = 1.1
            self.fan_base = 1200
            # Cultural appeal
    
    def get_philosophy_style_bonus(self, style: WrestlingStyle) -> float:
        """Get the bonus modifier for a wrestling style under this philosophy"""
        from classes.philosophy import get_style_modifier
        return get_style_modifier(self.philosophy, style)
    
    # ============== ROSTER MANAGEMENT ==============
    
    def sign_wrestler(self, wrestler: Wrestler) -> bool:
        """Sign a wrestler to the roster"""
        if wrestler in self.roster:
            self.log(f"{wrestler.name} is already signed!")
            return False
        
        # Check budget
        signing_bonus = wrestler.salary * 4  # 4 weeks signing bonus
        if self.budget < signing_bonus:
            self.log(f"Cannot afford to sign {wrestler.name}!")
            return False
        
        self.budget -= signing_bonus
        self.roster.append(wrestler)
        wrestler.is_signed = True
        self.log(f"Signed {wrestler.name} for ${wrestler.salary}/week!")
        return True
    
    def release_wrestler(self, wrestler: Wrestler) -> bool:
        """Release a wrestler from the roster"""
        if wrestler not in self.roster:
            self.log(f"{wrestler.name} is not on the roster!")
            return False
        
        # Pay out remaining contract (buyout = 50%)
        buyout = int(wrestler.salary * wrestler.contract_length * 0.5)
        self.budget -= buyout
        
        self.roster.remove(wrestler)
        wrestler.is_signed = False
        
        # Vacate any titles they hold
        for title in self.championships:
            if title.current_holder == wrestler.name:
                title.vacate()
                self.log(f"{title.name} has been vacated!")
        
        self.log(f"Released {wrestler.name}. Buyout: ${buyout}")
        return True
    
    def get_roster_by_style(self, style: WrestlingStyle) -> List[Wrestler]:
        """Get all wrestlers with a specific style"""
        return [w for w in self.roster if w.primary_style == style or w.secondary_style == style]
    
    def get_available_wrestlers(self) -> List[Wrestler]:
        """Get wrestlers who aren't injured"""
        return [w for w in self.roster if not w.is_injured]
    
    def get_champions(self) -> Dict[str, str]:
        """Get dictionary of title -> champion name"""
        return {title.name: title.current_holder for title in self.championships if title.current_holder}
    
    # ============== CHAMPIONSHIPS ==============
    
    def create_championship(
        self,
        name: str,
        prestige: int = 50,
        weight_class_restriction: Optional[str] = None,
        gender_restriction: Optional[str] = None,
        is_tag_title: bool = False,
    ) -> Championship:
        """Create a new championship"""
        title = Championship(
            name=name,
            prestige=prestige,
            weight_class_restriction=weight_class_restriction,
            gender_restriction=gender_restriction,
            is_tag_title=is_tag_title,
        )
        self.championships.append(title)
        self.log(f"Created the {name}!")
        return title
    
    def award_championship(self, title_name: str, wrestler: Wrestler) -> bool:
        """Award a championship to a wrestler"""
        title = next((t for t in self.championships if t.name == title_name), None)
        if not title:
            self.log(f"Championship {title_name} not found!")
            return False
        
        title.award_title(wrestler.name, f"Year {self.current_year}, Week {self.current_week}")
        wrestler.titles_held += 1
        self.log(f"{wrestler.name} is the new {title_name}!")
        return True
    
    # ============== SHOWS ==============
    
    def create_show(
        self,
        name: str,
        is_ppv: bool = False,
        capacity: int = 5000,
        ticket_price: int = 25,
        broadcast_deal: int = 0,
    ) -> Show:
        """Create a new show"""
        show = Show(
            name=name,
            is_ppv=is_ppv,
            capacity=capacity,
            ticket_price=ticket_price,
            broadcast_deal=broadcast_deal,
        )
        self.shows.append(show)
        self.log(f"Created show: {name}")
        return show
    
    # ============== FINANCES ==============
    
    def calculate_weekly_expenses(self) -> int:
        """Calculate total weekly expenses"""
        wrestler_salaries = sum(w.salary for w in self.roster)
        show_costs = len(self.shows) * 5000  # Base cost per show
        misc_costs = 2000  # Office, staff, etc.
        
        self.weekly_expenses = wrestler_salaries + show_costs + misc_costs
        return self.weekly_expenses
    
    def calculate_weekly_income(self) -> int:
        """Calculate total weekly income"""
        tv_money = sum(show.broadcast_deal for show in self.shows)
        merch = int(self.fan_base * 0.5 * self.merchandise_modifier)
        
        self.weekly_income = tv_money + merch
        return self.weekly_income
    
    def process_finances(self):
        """Process weekly financial transactions"""
        income = self.calculate_weekly_income()
        expenses = self.calculate_weekly_expenses()
        
        net = income - expenses
        self.budget += net
        self.total_revenue += income
        self.total_expenses += expenses
        
        self.log(f"Weekly Finances: +${income} income, -${expenses} expenses = ${net} net")
    
      # ============== GAME PROGRESSION ==============
    
    def advance_week(self):
        """Advance the game by 7 days (one week)"""
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
        
        # Process wrestlers
        for wrestler in self.roster:
            wrestler.weekly_update()
        
        # Process championships
        for title in self.championships:
            title.weekly_update()
        
        # Process finances
        self.process_finances()
        
        # Random events
        self._check_random_events()
        
        self.log(f"Advanced to {self.current_day}/{self.current_month}/Y{self.current_year}")
    
    def advance_to_date(self, year: int, month: int, day: int):
        """Advance directly to a specific date"""
        self.current_year = year
        self.current_month = month
        self.current_day = day
        
        from classes.calendar_system import date_to_day_of_year
        day_of_year = date_to_day_of_year(month, day)
        self.current_week = ((day_of_year - 1) // 7) + 1
    
    def _check_random_events(self):
        """Check for random events"""
        import random
        
        # Contract expirations
        for wrestler in self.roster:
            if wrestler.contract_length <= 0:
                self.log(f"⚠️ {wrestler.name}'s contract has expired!")
        
        # Random injuries during training
        for wrestler in self.roster:
            if not wrestler.is_injured and random.random() < 0.02:
                injury_weeks = random.randint(1, 4)
                wrestler.injure("Minor Training Injury", injury_weeks)
                self.log(f"🏥 {wrestler.name} suffered a minor injury in training! Out {injury_weeks} weeks.")
    
    def log(self, message: str):
        """Add message to game log"""
        timestamp = f"[Y{self.current_year} {self.current_day:02d}/{self.current_month:02d}]"
        self.game_log.append(f"{timestamp} {message}")
        print(f"{timestamp} {message}")
    
    # ============== SAVE/LOAD ==============
    
    def to_dict(self) -> dict:
        """Convert promotion to dictionary for saving"""
        return {
            "name": self.name,
            "philosophy": self.philosophy.value,
            "owner_name": self.owner_name,
            "location": self.location,
            "budget": self.budget,
            "prestige": self.prestige,
            "fan_base": self.fan_base,
            "tv_rating": self.tv_rating,
            "merchandise_modifier": self.merchandise_modifier,
            "current_week": self.current_week,
            "current_year": self.current_year,
            "roster": [w.to_dict() for w in self.roster],
            "championships": [
                {
                    "name": c.name,
                    "prestige": c.prestige,
                    "current_holder": c.current_holder,
                    "title_history": c.title_history,
                }
                for c in self.championships
            ],
            "game_log": self.game_log[-100:],  # Keep last 100 entries
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Promotion":
        """Create promotion from dictionary"""
        promotion = cls(
            name=data["name"],
            philosophy=Philosophy(data["philosophy"]),
            owner_name=data.get("owner_name", "Player"),
            starting_budget=data.get("budget", 100000),
            location=data.get("location", "United States"),
        )
        
        promotion.prestige = data.get("prestige", 50)
        promotion.fan_base = data.get("fan_base", 1000)
        promotion.tv_rating = data.get("tv_rating", 0.0)
        promotion.merchandise_modifier = data.get("merchandise_modifier", 1.0)
        promotion.current_week = data.get("current_week", 1)
        promotion.current_year = data.get("current_year", 1)
        promotion.game_log = data.get("game_log", [])
        
        # Load roster
        for wrestler_data in data.get("roster", []):
            wrestler = Wrestler.from_dict(wrestler_data)
            promotion.roster.append(wrestler)
        
        return promotion
    
    def __repr__(self) -> str:
        return f"Promotion({self.name}, {self.philosophy.value}, {len(self.roster)} wrestlers)"
