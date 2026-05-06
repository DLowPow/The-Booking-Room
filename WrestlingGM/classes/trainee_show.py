"""
Trainee Show System - Trainee-only show booking and execution
Trainee shows run alongside main shows on the same calendar
Only enrolled trainees can compete; awards XP, generates revenue
Bad shows hurt school reputation, great shows build prestige
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from classes.trainee import Trainee, TraineeLevel, TraineeStatus


# ==================== TRAINEE SHOW ENUMS ====================

class TraineeShowType(Enum):
    OPEN_HOUSE = "Open House"
    SHOWCASE = "Training Showcase"
    GRADUATION = "Graduation Card"
    INTER_SCHOOL = "Inter-School Battle"


class TraineeShowStatus(Enum):
    SCHEDULED = "Scheduled"
    READY = "Ready to Run"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


# ==================== SHOW TYPE INFO ====================

TRAINEE_SHOW_INFO = {
    TraineeShowType.OPEN_HOUSE: {
        "name": "Open House",
        "icon": "🏠",
        "color": "#10b981",
        "description": "A casual showcase for friends, family, and locals. Low stakes, low cost.",
        "min_capacity": 25,
        "max_capacity": 75,
        "ticket_price_range": [3, 8],
        "venue_cost_range": [50, 150],
        "min_matches": 2,
        "max_matches": 4,
        "min_match_minutes": 4,
        "max_match_minutes": 6,
        "xp_per_match_min": 25,
        "xp_per_match_max": 50,
        "min_trainees_needed": 4,
        "min_school_tier": "School Gym",
        "rep_required": 0,
        "min_level_allowed": "Beginner",
    },
    TraineeShowType.SHOWCASE: {
        "name": "Training Showcase",
        "icon": "🎓",
        "color": "#3b82f6",
        "description": "A proper trainee show with a real card and ticketed audience.",
        "min_capacity": 50,
        "max_capacity": 200,
        "ticket_price_range": [8, 15],
        "venue_cost_range": [100, 400],
        "min_matches": 3,
        "max_matches": 6,
        "min_match_minutes": 5,
        "max_match_minutes": 8,
        "xp_per_match_min": 50,
        "xp_per_match_max": 100,
        "min_trainees_needed": 6,
        "min_school_tier": "Under the Arches",
        "rep_required": 10,
        "min_level_allowed": "Beginner",
    },
    TraineeShowType.GRADUATION: {
        "name": "Graduation Card",
        "icon": "🎉",
        "color": "#a855f7",
        "description": "A landmark show celebrating advanced trainees ready to graduate. High stakes, high reward.",
        "min_capacity": 100,
        "max_capacity": 400,
        "ticket_price_range": [12, 25],
        "venue_cost_range": [300, 1000],
        "min_matches": 4,
        "max_matches": 7,
        "min_match_minutes": 6,
        "max_match_minutes": 12,
        "xp_per_match_min": 100,
        "xp_per_match_max": 200,
        "min_trainees_needed": 8,
        "min_school_tier": "Indie Training Camp",
        "rep_required": 25,
        "min_level_allowed": "Intermediate",
    },
    TraineeShowType.INTER_SCHOOL: {
        "name": "Inter-School Battle",
        "icon": "⚔️",
        "color": "#f59e0b",
        "description": "Your trainees face off against rival school students. Big crowd, big rewards.",
        "min_capacity": 150,
        "max_capacity": 600,
        "ticket_price_range": [15, 30],
        "venue_cost_range": [500, 1500],
        "min_matches": 5,
        "max_matches": 8,
        "min_match_minutes": 6,
        "max_match_minutes": 12,
        "xp_per_match_min": 150,
        "xp_per_match_max": 300,
        "min_trainees_needed": 10,
        "min_school_tier": "Wrestling Academy",
        "rep_required": 40,
        "min_level_allowed": "Intermediate",
    },
}


# ==================== TRAINEE MATCH CLASS ====================

@dataclass
class TraineeMatch:
    """A single match on a trainee show card"""
    match_index: int
    trainee_ids: List[str] = field(default_factory=list)
    trainee_names: List[str] = field(default_factory=list)
    match_type: str = "Singles"
    match_minutes: int = 6
    is_main_event: bool = False

    # Results (populated when show is run)
    winner_id: str = ""
    winner_name: str = ""
    rating: float = 0.0
    xp_awarded: int = 0
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "match_index": self.match_index,
            "trainee_ids": self.trainee_ids,
            "trainee_names": self.trainee_names,
            "match_type": self.match_type,
            "match_minutes": self.match_minutes,
            "is_main_event": self.is_main_event,
            "winner_id": self.winner_id,
            "winner_name": self.winner_name,
            "rating": self.rating,
            "xp_awarded": self.xp_awarded,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TraineeMatch":
        return cls(
            match_index=data.get("match_index", 0),
            trainee_ids=data.get("trainee_ids", []),
            trainee_names=data.get("trainee_names", []),
            match_type=data.get("match_type", "Singles"),
            match_minutes=data.get("match_minutes", 6),
            is_main_event=data.get("is_main_event", False),
            winner_id=data.get("winner_id", ""),
            winner_name=data.get("winner_name", ""),
            rating=data.get("rating", 0.0),
            xp_awarded=data.get("xp_awarded", 0),
            completed=data.get("completed", False),
        )


# ==================== TRAINEE SHOW CLASS ====================

@dataclass
class TraineeShow:
    """A scheduled or completed trainee show"""

    # Identity
    id: str
    name: str
    show_type: TraineeShowType
    status: TraineeShowStatus = TraineeShowStatus.SCHEDULED

    # Date/scheduling
    week: int = 0
    year: int = 1
    day: int = 1
    month: int = 1

    # Venue & pricing
    venue_name: str = "School Gym"
    venue_capacity: int = 50
    ticket_price: int = 5
    venue_cost: int = 100

    # Matches/card
    matches: List[TraineeMatch] = field(default_factory=list)

    # Results (populated when run)
    attendance: int = 0
    is_sellout: bool = False
    avg_rating: float = 0.0
    revenue: int = 0
    profit: int = 0
    school_rep_change: int = 0
    total_xp_awarded: int = 0
    notes: str = ""

    # ==================== VALIDATION ====================

    def is_ready_to_run(self) -> Tuple[bool, str]:
        """Check if the show has enough matches to run"""
        info = TRAINEE_SHOW_INFO.get(self.show_type, {})
        min_matches = info.get("min_matches", 2)

        if len(self.matches) < min_matches:
            return (False, f"Need at least {min_matches} matches (currently {len(self.matches)})")

        # Verify all matches have trainees
        for i, match in enumerate(self.matches):
            if len(match.trainee_ids) < 2:
                return (False, f"Match {i+1} needs at least 2 trainees")

        return (True, "Ready to run")

    # ==================== MATCH MANAGEMENT ====================

    def add_match(self, match: TraineeMatch) -> Tuple[bool, str]:
        """Add a match to the card"""
        info = TRAINEE_SHOW_INFO.get(self.show_type, {})
        max_matches = info.get("max_matches", 6)

        if len(self.matches) >= max_matches:
            return (False, f"Max {max_matches} matches reached")

        match.match_index = len(self.matches)
        self.matches.append(match)
        self._update_main_event()

        return (True, "Match added")

    def remove_match(self, match_index: int) -> bool:
        """Remove a match from the card"""
        if 0 <= match_index < len(self.matches):
            self.matches.pop(match_index)
            # Re-index
            for i, match in enumerate(self.matches):
                match.match_index = i
            self._update_main_event()
            return True
        return False

    def _update_main_event(self):
        """Mark the last match as main event"""
        for match in self.matches:
            match.is_main_event = False
        if self.matches:
            self.matches[-1].is_main_event = True

    def reorder_matches(self, new_order: List[int]) -> bool:
        """Reorder matches by their indices"""
        if len(new_order) != len(self.matches):
            return False

        try:
            new_matches = [self.matches[i] for i in new_order]
            self.matches = new_matches
            for i, match in enumerate(self.matches):
                match.match_index = i
            self._update_main_event()
            return True
        except (IndexError, TypeError):
            return False

    # ==================== SHOW EXECUTION ====================

    def run_show(self, school_reputation: int, school_tier_speed_mult: float = 1.0) -> Dict:
        """
        Execute the trainee show, calculate results, award XP.
        Returns dict of results.
        """
        ready, msg = self.is_ready_to_run()
        if not ready:
            return {"success": False, "message": msg}

        info = TRAINEE_SHOW_INFO.get(self.show_type, {})

        # Calculate attendance based on school rep + show type
        rep_factor = 0.4 + (school_reputation / 100 * 0.6)
        base_attendance = int(self.venue_capacity * rep_factor)
        attendance_variance = random.randint(-20, 20)
        self.attendance = max(10, min(self.venue_capacity, base_attendance + attendance_variance))
        self.is_sellout = self.attendance >= self.venue_capacity

        # Calculate revenue
        self.revenue = self.attendance * self.ticket_price
        self.profit = self.revenue - self.venue_cost

        # Run each match
        ratings = []
        total_xp = 0
        xp_min = info.get("xp_per_match_min", 50)
        xp_max = info.get("xp_per_match_max", 100)

        for match in self.matches:
            rating, winner_idx, xp_per_wrestler = self._simulate_trainee_match(
                match, xp_min, xp_max, school_tier_speed_mult
            )
            match.rating = rating
            match.completed = True
            ratings.append(rating)

            if winner_idx is not None and 0 <= winner_idx < len(match.trainee_ids):
                match.winner_id = match.trainee_ids[winner_idx]
                match.winner_name = match.trainee_names[winner_idx]

            match.xp_awarded = xp_per_wrestler
            total_xp += xp_per_wrestler * len(match.trainee_ids)

        # Calculate average rating
        self.avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        # Cap at 4.0 for trainee shows (they're not main events!)
        self.avg_rating = min(4.0, self.avg_rating)
        self.total_xp_awarded = total_xp

        # School reputation change
        if self.avg_rating >= 3.5:
            self.school_rep_change = 2
        elif self.avg_rating >= 2.5:
            self.school_rep_change = 1
        elif self.avg_rating >= 1.5:
            self.school_rep_change = 0
        else:
            self.school_rep_change = -1

        # Sellout bonus
        if self.is_sellout:
            self.school_rep_change += 1

        self.status = TraineeShowStatus.COMPLETED

        return {
            "success": True,
            "attendance": self.attendance,
            "is_sellout": self.is_sellout,
            "revenue": self.revenue,
            "profit": self.profit,
            "avg_rating": self.avg_rating,
            "school_rep_change": self.school_rep_change,
            "total_xp_awarded": self.total_xp_awarded,
            "matches": [m.to_dict() for m in self.matches],
        }

    def _simulate_trainee_match(
        self,
        match: TraineeMatch,
        xp_min: int,
        xp_max: int,
        school_speed_mult: float,
    ) -> Tuple[float, Optional[int], int]:
        """
        Simulate a single trainee match.
        Returns (rating, winner_index, xp_per_wrestler)
        """
        if not match.trainee_ids:
            return (0.0, None, 0)

        # Trainee match ratings are LOW (cap at 4.0 stars)
        base_rating = random.uniform(1.5, 3.0)

        # Main event gets a bonus
        if match.is_main_event:
            base_rating += 0.3

        # Longer matches get small bonus
        if match.match_minutes >= 8:
            base_rating += 0.2

        # Random variance
        rating = base_rating + random.uniform(-0.3, 0.5)
        rating = max(1.0, min(4.0, rating))

        # Pick winner (random for trainees - everyone needs experience)
        winner_idx = random.randint(0, len(match.trainee_ids) - 1)

        # Calculate XP for participants
        base_xp = random.randint(xp_min, xp_max)
        # Bonus XP for high-rated matches
        if rating >= 3.5:
            base_xp = int(base_xp * 1.5)
        elif rating >= 3.0:
            base_xp = int(base_xp * 1.2)

        # School tier speed multiplier
        base_xp = int(base_xp * school_speed_mult)

        return (rating, winner_idx, base_xp)

    # ==================== UI HELPERS ====================

    def get_type_icon(self) -> str:
        return TRAINEE_SHOW_INFO.get(self.show_type, {}).get("icon", "🎓")

    def get_type_color(self) -> str:
        return TRAINEE_SHOW_INFO.get(self.show_type, {}).get("color", "#6b7280")

    def get_status_color(self) -> str:
        colors = {
            TraineeShowStatus.SCHEDULED: "#3b82f6",
            TraineeShowStatus.READY: "#10b981",
            TraineeShowStatus.COMPLETED: "#a855f7",
            TraineeShowStatus.CANCELLED: "#6b7280",
        }
        return colors.get(self.status, "#6b7280")

    def get_match_count(self) -> int:
        return len(self.matches)

    def get_estimated_revenue(self) -> int:
        """Estimate revenue at full capacity"""
        return self.venue_capacity * self.ticket_price

    def get_estimated_profit(self) -> int:
        """Estimate max profit at full capacity"""
        return self.get_estimated_revenue() - self.venue_cost

    def get_total_match_minutes(self) -> int:
        """Total run time of all matches"""
        return sum(m.match_minutes for m in self.matches)

    def get_summary(self) -> Dict:
        """Get summary for UI display"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.show_type.value,
            "type_icon": self.get_type_icon(),
            "type_color": self.get_type_color(),
            "status": self.status.value,
            "status_color": self.get_status_color(),
            "date": f"{self.month}/{self.day}/Y{self.year}",
            "week": self.week,
            "venue_name": self.venue_name,
            "venue_capacity": self.venue_capacity,
            "ticket_price": self.ticket_price,
            "venue_cost": self.venue_cost,
            "match_count": self.get_match_count(),
            "total_minutes": self.get_total_match_minutes(),
            "estimated_revenue": self.get_estimated_revenue(),
            "estimated_profit": self.get_estimated_profit(),
            "attendance": self.attendance,
            "is_sellout": self.is_sellout,
            "avg_rating": self.avg_rating,
            "revenue": self.revenue,
            "profit": self.profit,
            "school_rep_change": self.school_rep_change,
            "total_xp_awarded": self.total_xp_awarded,
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "show_type": self.show_type.value,
            "status": self.status.value,
            "week": self.week,
            "year": self.year,
            "day": self.day,
            "month": self.month,
            "venue_name": self.venue_name,
            "venue_capacity": self.venue_capacity,
            "ticket_price": self.ticket_price,
            "venue_cost": self.venue_cost,
            "matches": [m.to_dict() for m in self.matches],
            "attendance": self.attendance,
            "is_sellout": self.is_sellout,
            "avg_rating": self.avg_rating,
            "revenue": self.revenue,
            "profit": self.profit,
            "school_rep_change": self.school_rep_change,
            "total_xp_awarded": self.total_xp_awarded,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TraineeShow":
        try:
            st = TraineeShowType(data.get("show_type", "Open House"))
        except ValueError:
            st = TraineeShowType.OPEN_HOUSE
        try:
            status = TraineeShowStatus(data.get("status", "Scheduled"))
        except ValueError:
            status = TraineeShowStatus.SCHEDULED

        show = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            show_type=st,
            status=status,
            week=data.get("week", 0),
            year=data.get("year", 1),
            day=data.get("day", 1),
            month=data.get("month", 1),
            venue_name=data.get("venue_name", "School Gym"),
            venue_capacity=data.get("venue_capacity", 50),
            ticket_price=data.get("ticket_price", 5),
            venue_cost=data.get("venue_cost", 100),
            attendance=data.get("attendance", 0),
            is_sellout=data.get("is_sellout", False),
            avg_rating=data.get("avg_rating", 0.0),
            revenue=data.get("revenue", 0),
            profit=data.get("profit", 0),
            school_rep_change=data.get("school_rep_change", 0),
            total_xp_awarded=data.get("total_xp_awarded", 0),
            notes=data.get("notes", ""),
        )

        for md in data.get("matches", []):
            try:
                show.matches.append(TraineeMatch.from_dict(md))
            except Exception:
                pass

        return show


# ==================== TRAINEE SHOW MANAGER ====================

class TraineeShowManager:
    """Manages all trainee shows (scheduled and completed)"""

    def __init__(self):
        self.scheduled_shows: List[TraineeShow] = []
        self.completed_shows: List[TraineeShow] = []
        self.next_id_num: int = 1
        self.lifetime_revenue: int = 0
        self.lifetime_attendance: int = 0
        self.lifetime_shows_run: int = 0

    def _next_show_id(self) -> str:
        sid = f"trainee_show_{self.next_id_num}"
        self.next_id_num += 1
        return sid

    # ==================== SHOW CREATION ====================

    def can_create_show(
        self,
        show_type: TraineeShowType,
        school_tier_name: str,
        school_reputation: int,
        active_trainees: List[Trainee],
    ) -> Tuple[bool, str]:
        """Check if a show type can be created"""
        info = TRAINEE_SHOW_INFO.get(show_type, {})

        # School tier requirement
        tier_order = [
            "School Gym", "Under the Arches", "Indie Training Camp",
            "Wrestling Academy", "Pro Training Center", "Performance Center",
        ]
        required_tier = info.get("min_school_tier", "School Gym")
        try:
            required_idx = tier_order.index(required_tier)
            current_idx = tier_order.index(school_tier_name)
            if current_idx < required_idx:
                return (False, f"Requires {required_tier} or higher")
        except ValueError:
            return (False, "Invalid school tier")

        # Reputation requirement
        rep_required = info.get("rep_required", 0)
        if school_reputation < rep_required:
            return (False, f"Requires {rep_required}+ school reputation (you have {school_reputation})")

        # Trainee count requirement
        min_trainees = info.get("min_trainees_needed", 4)
        eligible_trainees = [t for t in active_trainees if t.can_wrestle_in_trainee_show()]
        if len(eligible_trainees) < min_trainees:
            return (False, f"Need {min_trainees}+ eligible trainees (you have {len(eligible_trainees)})")

        return (True, "Can create")

    def create_show(
        self,
        show_type: TraineeShowType,
        name: str,
        venue_name: str,
        venue_capacity: int,
        ticket_price: int,
        venue_cost: int,
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
    ) -> Optional[TraineeShow]:
        """Create a new trainee show"""
        show = TraineeShow(
            id=self._next_show_id(),
            name=name,
            show_type=show_type,
            status=TraineeShowStatus.SCHEDULED,
            week=week,
            year=year,
            day=day,
            month=month,
            venue_name=venue_name,
            venue_capacity=venue_capacity,
            ticket_price=ticket_price,
            venue_cost=venue_cost,
        )
        self.scheduled_shows.append(show)
        return show

    def cancel_show(self, show_id: str) -> bool:
        """Cancel a scheduled trainee show"""
        for i, show in enumerate(self.scheduled_shows):
            if show.id == show_id:
                show.status = TraineeShowStatus.CANCELLED
                self.scheduled_shows.pop(i)
                return True
        return False

    # ==================== QUERIES ====================

    def get_show(self, show_id: str) -> Optional[TraineeShow]:
        for show in self.scheduled_shows + self.completed_shows:
            if show.id == show_id:
                return show
        return None

    def get_scheduled_shows(self) -> List[TraineeShow]:
        return list(self.scheduled_shows)

    def get_completed_shows(self) -> List[TraineeShow]:
        return list(self.completed_shows)

    def get_show_for_date(self, year: int, month: int, day: int) -> Optional[TraineeShow]:
        """Get any trainee show scheduled for a specific date"""
        for show in self.scheduled_shows:
            if show.year == year and show.month == month and show.day == day:
                return show
        return None

    def has_show_on_date(self, year: int, month: int, day: int) -> bool:
        """Check if a trainee show is booked for this date"""
        return self.get_show_for_date(year, month, day) is not None

    def get_next_scheduled_show(self) -> Optional[TraineeShow]:
        """Get the next upcoming trainee show"""
        if not self.scheduled_shows:
            return None
        return sorted(
            self.scheduled_shows,
            key=lambda s: (s.year, s.month, s.day),
        )[0]

    # ==================== SHOW EXECUTION ====================

    def run_show(
        self,
        show_id: str,
        active_trainees: List[Trainee],
        school_reputation: int,
        school_tier_speed_mult: float = 1.0,
    ) -> Dict:
        """
        Execute a trainee show, apply XP to trainees, move to completed.
        Returns full show results dict.
        """
        show = self.get_show(show_id)
        if not show:
            return {"success": False, "message": "Show not found"}

        if show.status == TraineeShowStatus.COMPLETED:
            return {"success": False, "message": "Show already completed"}

        # Run the show
        result = show.run_show(school_reputation, school_tier_speed_mult)

        if not result.get("success"):
            return result

        # Apply XP and match records to participating trainees
        trainee_lookup = {t.id: t for t in active_trainees}
        level_up_events = []

        for match in show.matches:
            xp = match.xp_awarded
            for tid in match.trainee_ids:
                trainee = trainee_lookup.get(tid)
                if trainee and trainee.status == TraineeStatus.ACTIVE:
                    won = (tid == match.winner_id)
                    level_event = trainee.record_trainee_match(
                        won=won,
                        rating=match.rating,
                        xp_reward=xp,
                    )
                    if level_event:
                        level_up_events.append({
                            "trainee_name": trainee.name,
                            "event": level_event,
                        })

        # Move show to completed
        if show in self.scheduled_shows:
            self.scheduled_shows.remove(show)
        self.completed_shows.append(show)

        # Update lifetime stats
        self.lifetime_revenue += show.revenue
        self.lifetime_attendance += show.attendance
        self.lifetime_shows_run += 1

        # Cap completed shows history
        if len(self.completed_shows) > 50:
            self.completed_shows = self.completed_shows[-50:]

        result["level_ups"] = level_up_events
        result["show_id"] = show.id
        result["show_name"] = show.name

        return result

    # ==================== STATS ====================

    def get_lifetime_stats(self) -> Dict:
        """Get lifetime trainee show statistics"""
        completed = self.completed_shows
        avg_rating = (
            sum(s.avg_rating for s in completed) / len(completed)
            if completed else 0.0
        )
        sellouts = sum(1 for s in completed if s.is_sellout)

        return {
            "lifetime_shows": self.lifetime_shows_run,
            "lifetime_revenue": self.lifetime_revenue,
            "lifetime_attendance": self.lifetime_attendance,
            "scheduled_count": len(self.scheduled_shows),
            "completed_count": len(self.completed_shows),
            "avg_rating": avg_rating,
            "sellout_count": sellouts,
            "lifetime_profit": sum(s.profit for s in completed),
            "lifetime_xp_awarded": sum(s.total_xp_awarded for s in completed),
        }

    # ==================== UI HELPERS ====================

    def get_show_type_options(
        self,
        school_tier_name: str = "",
        school_reputation: int = 0,
        active_trainees: List[Trainee] = None,
    ) -> List[Dict]:
        """Get all show types available for UI display, with eligibility flags"""
        if active_trainees is None:
            active_trainees = []

        options = []
        for st in TraineeShowType:
            info = TRAINEE_SHOW_INFO[st]
            can_create, reason = self.can_create_show(
                st, school_tier_name, school_reputation, active_trainees
            )

            options.append({
                "type": st.value,
                "type_key": st.name,
                "name": info["name"],
                "icon": info["icon"],
                "color": info["color"],
                "description": info["description"],
                "min_capacity": info["min_capacity"],
                "max_capacity": info["max_capacity"],
                "ticket_price_range": info["ticket_price_range"],
                "venue_cost_range": info["venue_cost_range"],
                "min_matches": info["min_matches"],
                "max_matches": info["max_matches"],
                "min_trainees_needed": info["min_trainees_needed"],
                "min_school_tier": info["min_school_tier"],
                "rep_required": info["rep_required"],
                "min_level_allowed": info["min_level_allowed"],
                "xp_range": (info["xp_per_match_min"], info["xp_per_match_max"]),
                "can_create": can_create,
                "blocking_reason": reason if not can_create else "",
            })

        return options

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "scheduled_shows": [s.to_dict() for s in self.scheduled_shows],
            "completed_shows": [s.to_dict() for s in self.completed_shows[-50:]],
            "next_id_num": self.next_id_num,
            "lifetime_revenue": self.lifetime_revenue,
            "lifetime_attendance": self.lifetime_attendance,
            "lifetime_shows_run": self.lifetime_shows_run,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TraineeShowManager":
        manager = cls()
        manager.next_id_num = data.get("next_id_num", 1)
        manager.lifetime_revenue = data.get("lifetime_revenue", 0)
        manager.lifetime_attendance = data.get("lifetime_attendance", 0)
        manager.lifetime_shows_run = data.get("lifetime_shows_run", 0)

        for sd in data.get("scheduled_shows", []):
            try:
                manager.scheduled_shows.append(TraineeShow.from_dict(sd))
            except Exception:
                pass

        for sd in data.get("completed_shows", []):
            try:
                manager.completed_shows.append(TraineeShow.from_dict(sd))
            except Exception:
                pass

        return manager
