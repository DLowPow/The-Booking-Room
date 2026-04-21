"""
Calendar System - Real monthly calendar with shows and events
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field


# Month info: name, days, weeks (4 weeks per month roughly)
MONTHS = [
    {"number": 1, "name": "January", "short": "Jan", "days": 28, "start_week": 1, "end_week": 4},
    {"number": 2, "name": "February", "short": "Feb", "days": 28, "start_week": 5, "end_week": 8},
    {"number": 3, "name": "March", "short": "Mar", "days": 35, "start_week": 9, "end_week": 13},
    {"number": 4, "name": "April", "short": "Apr", "days": 28, "start_week": 14, "end_week": 17},
    {"number": 5, "name": "May", "short": "May", "days": 28, "start_week": 18, "end_week": 21},
    {"number": 6, "name": "June", "short": "Jun", "days": 35, "start_week": 22, "end_week": 26},
    {"number": 7, "name": "July", "short": "Jul", "days": 28, "start_week": 27, "end_week": 30},
    {"number": 8, "name": "August", "short": "Aug", "days": 28, "start_week": 31, "end_week": 34},
    {"number": 9, "name": "September", "short": "Sep", "days": 35, "start_week": 35, "end_week": 39},
    {"number": 10, "name": "October", "short": "Oct", "days": 28, "start_week": 40, "end_week": 43},
    {"number": 11, "name": "November", "short": "Nov", "days": 28, "start_week": 44, "end_week": 47},
    {"number": 12, "name": "December", "short": "Dec", "days": 35, "start_week": 48, "end_week": 52},
]


def get_month_for_week(week_number: int) -> Dict:
    """Get month info for a given week number"""
    for month in MONTHS:
        if month["start_week"] <= week_number <= month["end_week"]:
            return month
    return MONTHS[0]


def get_week_in_month(week_number: int) -> int:
    """Get which week of the month (1-5) this week represents"""
    month = get_month_for_week(week_number)
    return week_number - month["start_week"] + 1


def week_to_date_range(week_number: int) -> str:
    """Convert week number to a date range string like 'Jan 1-7'"""
    month = get_month_for_week(week_number)
    week_in_month = get_week_in_month(week_number)
    start_day = ((week_in_month - 1) * 7) + 1
    end_day = min(start_day + 6, month["days"])
    return f"{month['short']} {start_day}-{end_day}"


@dataclass
class CalendarEvent:
    """An event on the calendar"""
    year: int
    week: int
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
        return [e for e in self.events if e.year == year]
    
    def get_events_for_week(self, year: int, week: int) -> List[CalendarEvent]:
        return [e for e in self.events if e.year == year and e.week == week]
    
    def get_events_for_month(self, year: int, month_number: int) -> List[CalendarEvent]:
        """Get events for a specific month by number (1-12)"""
        month_info = MONTHS[month_number - 1]
        return [
            e for e in self.events
            if e.year == year and month_info["start_week"] <= e.week <= month_info["end_week"]
        ]
    
    def get_month_calendar_data(self, year: int, month_number: int) -> Dict:
        """Get detailed calendar data for a specific month"""
        month_info = MONTHS[month_number - 1]
        events = self.get_events_for_month(year, month_number)
        
        # Build week structure
        weeks_data = []
        for week_num in range(month_info["start_week"], month_info["end_week"] + 1):
            week_events = [e for e in events if e.week == week_num]
            week_in_month = week_num - month_info["start_week"] + 1
            start_day = ((week_in_month - 1) * 7) + 1
            
            # Build days for this week
            days = []
            for day_offset in range(7):
                day_num = start_day + day_offset
                if day_num > month_info["days"]:
                    days.append({"day": None, "events": []})
                else:
                    days.append({
                        "day": day_num,
                        "is_show_day": day_offset == 5,  # Saturday is show day (index 5 = Sat)
                        "week_number": week_num,
                        "events": week_events if day_offset == 5 else [],
                    })
            
            weeks_data.append({
                "week_number": week_num,
                "week_in_month": week_in_month,
                "days": days,
                "events": week_events,
            })
        
        return {
            "month_info": month_info,
            "weeks": weeks_data,
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
