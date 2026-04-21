"""
Calendar System - Tracks weeks, months, shows, and events
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field


# Wrestling calendar uses 52 weeks
# Map weeks to months (rough approximation)
WEEK_TO_MONTH = {}
for week in range(1, 53):
    if week <= 4:
        WEEK_TO_MONTH[week] = "January"
    elif week <= 8:
        WEEK_TO_MONTH[week] = "February"
    elif week <= 13:
        WEEK_TO_MONTH[week] = "March"
    elif week <= 17:
        WEEK_TO_MONTH[week] = "April"
    elif week <= 21:
        WEEK_TO_MONTH[week] = "May"
    elif week <= 26:
        WEEK_TO_MONTH[week] = "June"
    elif week <= 30:
        WEEK_TO_MONTH[week] = "July"
    elif week <= 34:
        WEEK_TO_MONTH[week] = "August"
    elif week <= 39:
        WEEK_TO_MONTH[week] = "September"
    elif week <= 43:
        WEEK_TO_MONTH[week] = "October"
    elif week <= 47:
        WEEK_TO_MONTH[week] = "November"
    else:
        WEEK_TO_MONTH[week] = "December"


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def get_month_for_week(week):
    """Get month name for a given week"""
    return WEEK_TO_MONTH.get(week, "January")


def get_weeks_in_month(month_name):
    """Get list of weeks that fall in a given month"""
    return [w for w, m in WEEK_TO_MONTH.items() if m == month_name]


@dataclass
class CalendarEvent:
    """An event on the calendar"""
    year: int
    week: int
    event_type: str  # 'show', 'ppv', 'tournament', 'milestone'
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
    
    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "week": self.week,
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
        return cls(**data)


class CalendarSystem:
    """Manages the calendar and event history"""
    
    def __init__(self):
        self.events: List[CalendarEvent] = []
    
    def add_show(
        self,
        year: int,
        week: int,
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
        title = f"PPV Event" if is_ppv else f"Weekly Show"
        
        event = CalendarEvent(
            year=year,
            week=week,
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
    
    def add_milestone(self, year: int, week: int, title: str, description: str = ""):
        """Add a milestone to the calendar"""
        event = CalendarEvent(
            year=year,
            week=week,
            event_type="milestone",
            title=title,
            description=description,
        )
        self.events.append(event)
    
    def get_events_for_year(self, year: int) -> List[CalendarEvent]:
        """Get all events for a specific year"""
        return [e for e in self.events if e.year == year]
    
    def get_events_for_week(self, year: int, week: int) -> List[CalendarEvent]:
        """Get events for a specific week"""
        return [e for e in self.events if e.year == year and e.week == week]
    
    def get_events_for_month(self, year: int, month_name: str) -> List[CalendarEvent]:
        """Get events for a specific month"""
        weeks = get_weeks_in_month(month_name)
        return [e for e in self.events if e.year == year and e.week in weeks]
    
    def get_year_calendar(self, year: int) -> Dict:
        """Get calendar data organized by month"""
        months_data = {}
        for month in MONTHS:
            weeks = get_weeks_in_month(month)
            month_events = self.get_events_for_month(year, month)
            months_data[month] = {
                "weeks": weeks,
                "events": month_events,
                "shows_count": len([e for e in month_events if e.event_type in ['show', 'ppv']]),
            }
        return months_data
    
    def get_year_stats(self, year: int) -> Dict:
        """Get summary stats for a year"""
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
        """Get most recent events"""
        sorted_events = sorted(
            self.events,
            key=lambda e: (e.year, e.week),
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
