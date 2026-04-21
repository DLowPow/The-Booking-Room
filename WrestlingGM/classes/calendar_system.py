"""
Calendar System - Real day-based booking system
Each year is 12 months with real days
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import date, timedelta


# Standard 365 day year (no leap years for simplicity)
MONTHS = [
    {"number": 1, "name": "January", "short": "Jan", "days": 31},
    {"number": 2, "name": "February", "short": "Feb", "days": 28},
    {"number": 3, "name": "March", "short": "Mar", "days": 31},
    {"number": 4, "name": "April", "short": "Apr", "days": 30},
    {"number": 5, "name": "May", "short": "May", "days": 31},
    {"number": 6, "name": "June", "short": "Jun", "days": 30},
    {"number": 7, "name": "July", "short": "Jul", "days": 31},
    {"number": 8, "name": "August", "short": "Aug", "days": 31},
    {"number": 9, "name": "September", "short": "Sep", "days": 30},
    {"number": 10, "name": "October", "short": "Oct", "days": 31},
    {"number": 11, "name": "November", "short": "Nov", "days": 30},
    {"number": 12, "name": "December", "short": "Dec", "days": 31},
]

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_NAMES_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def days_in_month(month_num: int) -> int:
    """Get number of days in a month"""
    return MONTHS[month_num - 1]["days"]


def get_month_info(month_num: int) -> Dict:
    """Get month info"""
    return MONTHS[month_num - 1]


def date_to_day_of_year(month: int, day: int) -> int:
    """Convert month/day to day of year (1-365)"""
    day_of_year = day
    for m in range(1, month):
        day_of_year += MONTHS[m - 1]["days"]
    return day_of_year


def day_of_year_to_date(day_of_year: int) -> tuple:
    """Convert day of year to (month, day)"""
    days_remaining = day_of_year
    for month in MONTHS:
        if days_remaining <= month["days"]:
            return (month["number"], days_remaining)
        days_remaining -= month["days"]
    return (12, 31)


def get_day_of_week(year: int, month: int, day: int) -> int:
    """Get day of week (0=Mon, 6=Sun) for a date"""
    # Simple calculation: Day 1 of Year 1 = Monday (0)
    total_days = 0
    
    # Add days for completed years
    for y in range(1, year):
        total_days += 365
    
    # Add days for completed months in current year
    for m in range(1, month):
        total_days += MONTHS[m - 1]["days"]
    
    # Add days in current month
    total_days += (day - 1)
    
    return total_days % 7


def format_date(year: int, month: int, day: int, short: bool = False) -> str:
    """Format a date nicely"""
    month_info = MONTHS[month - 1]
    day_of_week = get_day_of_week(year, month, day)
    
    if short:
        return f"{day:02d}/{month:02d}"
    
    return f"{DAY_NAMES_FULL[day_of_week]}, {month_info['name']} {day}, Year {year}"


@dataclass
class CalendarEvent:
    """An event on the calendar"""
    year: int
    month: int
    day: int
    event_type: str
    title: str
    description: str = ""
    venue: str = ""
    attendance: int = 0
    capacity: int = 0
    rating: float = 0.0
    profit: int = 0
    is_sellout: bool = False
    main_event: str = ""
    matches_count: int = 0
    
    @property
    def date_string(self) -> str:
        return format_date(self.year, self.month, self.day)
    
    @property
    def short_date(self) -> str:
        return f"{self.day:02d}/{self.month:02d}/Y{self.year}"
    
    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "venue": self.venue,
            "attendance": self.attendance,
            "capacity": self.capacity,
            "rating": self.rating,
            "profit": self.profit,
            "is_sellout": self.is_sellout,
            "main_event": self.main_event,
            "matches_count": self.matches_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CalendarEvent":
        # Handle backward compatibility with week-based events
        if 'week' in data and 'month' not in data:
            # Convert old week format
            week = data.get('week', 1)
            day_of_year = ((week - 1) * 7) + 6  # Saturday of that week
            month, day = day_of_year_to_date(day_of_year)
            data['month'] = month
            data['day'] = day
            data.pop('week', None)
        
        return cls(
            year=data.get('year', 1),
            month=data.get('month', 1),
            day=data.get('day', 1),
            event_type=data.get('event_type', 'show'),
            title=data.get('title', 'Show'),
            description=data.get('description', ''),
            venue=data.get('venue', ''),
            attendance=data.get('attendance', 0),
            capacity=data.get('capacity', 0),
            rating=data.get('rating', 0.0),
            profit=data.get('profit', 0),
            is_sellout=data.get('is_sellout', False),
            main_event=data.get('main_event', ''),
            matches_count=data.get('matches_count', 0),
        )


class CalendarSystem:
    """Manages the calendar and event history"""
    
    def __init__(self):
        self.events: List[CalendarEvent] = []
    
    def add_show(
        self,
        year: int,
        month: int,
        day: int,
        venue: str,
        attendance: int,
        capacity: int,
        rating: float,
        profit: int,
        is_sellout: bool = False,
        main_event: str = "",
        matches_count: int = 0,
        is_ppv: bool = False,
    ):
        """Add a show to the calendar"""
        event_type = "ppv" if is_ppv else "show"
        title = "PPV Event" if is_ppv else "Weekly Show"
        
        event = CalendarEvent(
            year=year,
            month=month,
            day=day,
            event_type=event_type,
            title=title,
            venue=venue,
            attendance=attendance,
            capacity=capacity,
            rating=rating,
            profit=profit,
            is_sellout=is_sellout,
            main_event=main_event,
            matches_count=matches_count,
        )
        self.events.append(event)
    
    def get_events_for_year(self, year: int) -> List[CalendarEvent]:
        return [e for e in self.events if e.year == year]
    
    def get_events_for_date(self, year: int, month: int, day: int) -> List[CalendarEvent]:
        return [
            e for e in self.events
            if e.year == year and e.month == month and e.day == day
        ]
    
    def get_events_for_month(self, year: int, month: int) -> List[CalendarEvent]:
        return [
            e for e in self.events
            if e.year == year and e.month == month
        ]
    
    def get_month_calendar_data(self, year: int, month: int) -> Dict:
        """Get calendar grid data for a specific month"""
        month_info = MONTHS[month - 1]
        events = self.get_events_for_month(year, month)
        
        # Get first day of month and its day of week
        first_day_of_week = get_day_of_week(year, month, 1)
        days_in_this_month = month_info["days"]
        
        # Build the grid
        grid_days = []
        
        # Add empty cells before day 1
        for _ in range(first_day_of_week):
            grid_days.append({"day": None, "events": []})
        
        # Add all days
        for day in range(1, days_in_this_month + 1):
            day_events = [e for e in events if e.day == day]
            day_of_week = get_day_of_week(year, month, day)
            grid_days.append({
                "day": day,
                "day_of_week": day_of_week,
                "day_name": DAY_NAMES[day_of_week],
                "events": day_events,
                "has_event": len(day_events) > 0,
            })
        
        # Pad to complete grid (6 rows of 7 = 42 cells)
        while len(grid_days) < 42:
            grid_days.append({"day": None, "events": []})
        
        # Group into weeks
        weeks = []
        for i in range(0, len(grid_days), 7):
            weeks.append(grid_days[i:i+7])
        
        # Remove trailing empty weeks
        while weeks and all(d["day"] is None for d in weeks[-1]):
            weeks.pop()
        
        return {
            "month_info": month_info,
            "weeks": weeks,
            "total_events": len(events),
            "shows_count": len([e for e in events if e.event_type in ['show', 'ppv']]),
        }
    
    def get_year_stats(self, year: int) -> Dict:
        year_events = self.get_events_for_year(year)
        shows = [e for e in year_events if e.event_type == 'show']
        ppvs = [e for e in year_events if e.event_type == 'ppv']
        all_shows = shows + ppvs
        
        total_attendance = sum(e.attendance for e in all_shows)
        total_profit = sum(e.profit for e in all_shows)
        sellouts = len([e for e in all_shows if e.is_sellout])
        
        avg_rating = 0.0
        if all_shows:
            avg_rating = sum(e.rating for e in all_shows) / len(all_shows)
        
        return {
            "total_shows": len(shows),
            "total_ppvs": len(ppvs),
            "total_attendance": total_attendance,
            "total_profit": total_profit,
            "sellouts": sellouts,
            "average_rating": avg_rating,
        }
    
    def get_recent_events(self, count: int = 10) -> List[CalendarEvent]:
        sorted_events = sorted(
            self.events,
            key=lambda e: (e.year, e.month, e.day),
            reverse=True
        )
        return sorted_events[:count]
    
    def to_dict(self) -> dict:
        return {
            "events": [e.to_dict() for e in self.events]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CalendarSystem":
        system = cls()
        for event_data in data.get("events", []):
            system.events.append(CalendarEvent.from_dict(event_data))
        return system
