"""
Calendar System - Day-based booking
Players choose specific dates for shows
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field


# Each month has its actual days (using non-leap year)
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

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_days_in_year() -> int:
    """Total days in a year"""
    return sum(m["days"] for m in MONTHS)


def day_of_year_to_date(day_of_year: int) -> Dict:
    """Convert day of year (1-365) to month/day"""
    if day_of_year < 1:
        day_of_year = 1
    if day_of_year > 365:
        day_of_year = 365
    
    days_remaining = day_of_year
    for month in MONTHS:
        if days_remaining <= month["days"]:
            return {
                "month": month["number"],
                "month_name": month["name"],
                "month_short": month["short"],
                "day": days_remaining,
            }
        days_remaining -= month["days"]
    
    # Fallback
    return {"month": 12, "month_name": "December", "month_short": "Dec", "day": 31}


def date_to_day_of_year(month: int, day: int) -> int:
    """Convert month/day to day of year"""
    day_of_year = 0
    for m in MONTHS:
        if m["number"] < month:
            day_of_year += m["days"]
        else:
            break
    return day_of_year + day


def get_day_of_week(year: int, day_of_year: int) -> int:
    """Get day of week (0=Mon, 6=Sun) - simple cycle"""
    # Simple: each year starts on Monday for consistency
    return (day_of_year - 1) % 7


def get_day_of_week_name(year: int, day_of_year: int) -> str:
    """Get day of week name"""
    return DAYS_OF_WEEK[get_day_of_week(year, day_of_year)]


def format_date(year: int, month: int, day: int) -> str:
    """Format as DD/MM"""
    return f"{day:02d}/{month:02d}"


def format_full_date(year: int, month: int, day: int) -> str:
    """Format as 'Mon, Jan 1, Year 1'"""
    day_of_year = date_to_day_of_year(month, day)
    day_name = get_day_of_week_name(year, day_of_year)
    month_name = MONTHS[month - 1]["short"]
    return f"{day_name}, {month_name} {day}, Year {year}"


@dataclass
class CalendarEvent:
    """An event on a specific date"""
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
    
    def get_day_of_year(self) -> int:
        return date_to_day_of_year(self.month, self.day)
    
    def get_date_string(self) -> str:
        return format_date(self.year, self.month, self.day)
    
    def get_full_date_string(self) -> str:
        return format_full_date(self.year, self.month, self.day)
    
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
        # Backward compatibility for old "week" based events
        if "week" in data and "month" not in data:
            week = data.get("week", 1)
            day_of_year = (week - 1) * 7 + 6  # Saturday of that week
            date_info = day_of_year_to_date(day_of_year)
            data["month"] = date_info["month"]
            data["day"] = date_info["day"]
            data.pop("week", None)
        
        return cls(
            year=data.get("year", 1),
            month=data.get("month", 1),
            day=data.get("day", 1),
            event_type=data.get("event_type", "show"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            venue=data.get("venue", ""),
            attendance=data.get("attendance", 0),
            capacity=data.get("capacity", 0),
            rating=data.get("rating", 0.0),
            profit=data.get("profit", 0),
            is_sellout=data.get("is_sellout", False),
            main_event=data.get("main_event", ""),
            matches_count=data.get("matches_count", 0),
        )


class CalendarSystem:
    """Day-based calendar system"""
    
    def __init__(self):
        self.events: List[CalendarEvent] = []
        self.scheduled_shows: List[Dict] = []  # Future scheduled shows
    
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
        """Add a completed show to the calendar"""
        event_type = "ppv" if is_ppv else "show"
        title = f"PPV Event" if is_ppv else f"Weekly Show"
        
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
    
    def schedule_show(self, year: int, month: int, day: int, show_data: Dict):
        """Schedule a show for a future date"""
        self.scheduled_shows.append({
            "year": year,
            "month": month,
            "day": day,
            "data": show_data,
        })
    
    def get_scheduled_show(self, year: int, month: int, day: int) -> Optional[Dict]:
        """Get scheduled show for a specific date"""
        for s in self.scheduled_shows:
            if s["year"] == year and s["month"] == month and s["day"] == day:
                return s["data"]
        return None
    
    def remove_sc
