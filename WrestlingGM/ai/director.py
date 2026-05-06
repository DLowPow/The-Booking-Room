"""
AI Director - The Brain of The Booking Room
Coordinates personality, mood, memory, decisions, and all AI outputs
Connects to: Voice, Events, Storylines, Commentary, News, Rival Promotions
Supports Creative Control levels: Off, Light, Heavy, Russo Mode
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ai.personality import (
    PersonalityManager, PersonalityType, MoodState,
    CreativeControlLevel, MOOD_TRIGGERS
)
from ai.voice import VoiceEngine, VoiceContext


class AIDirector:
    """
    Central AI coordinator for the entire game.
    Every message, event, commentary line, and booking suggestion
    flows through the Director and gets tinted by the active personality.
    """

    def __init__(
        self,
        creative_control_enabled: bool = False,
        creative_control_difficulty: str = "Normal",
        personality_type: str = "The Traditionalist",
    ):
        # Map personality
        pt_map = {
            "The Showman": PersonalityType.SHOWMAN,
            "The Mastermind": PersonalityType.MASTERMIND,
            "The Mad Scientist": PersonalityType.MAD_SCIENTIST,
            "The Traditionalist": PersonalityType.TRADITIONALIST,
        }
        pt = pt_map.get(personality_type, PersonalityType.TRADITIONALIST)

        self.personality = PersonalityManager(personality_type=pt)
        self.voice = VoiceEngine(self.personality)

        # Creative control
        self.creative_control_enabled = creative_control_enabled
        if creative_control_enabled:
            cc_map = {
                "Easy": CreativeControlLevel.LIGHT,
                "Normal": CreativeControlLevel.HEAVY,
                "Hard": CreativeControlLevel.RUSSO_MODE,
            }
            self.personality.set_creative_control(
                cc_map.get(creative_control_difficulty, CreativeControlLevel.LIGHT)
            )
        else:
            self.personality.set_creative_control(CreativeControlLevel.OFF)

        # Director state
        self.weeks_active: int = 0
        self.shows_directed: int = 0
        self.last_show_rating: float = 0.0
        self.consecutive_bad_shows: int = 0
        self.consecutive_good_shows: int = 0

        # Active events tracking
        self.active_events: List = []
        self.resolved_events: List = []
        self.event_cooldowns: Dict[str, int] = {}

        # Match history for AI decisions
        self.recent_matches: List[Dict] = []
        self.wrestler_push_list: List[str] = []
        self.wrestler_depush_list: List[str] = []

        # Booking suggestions queue
        self.pending_suggestions: List[Dict] = []
        self.accepted_suggestions: int = 0
        self.rejected_suggestions: int = 0

    # ==================== CORE WEEKLY UPDATE ====================

    def process_weekly_update(
        self,
        roster: List[Dict],
        budget: int,
        fans: int,
        prestige: int,
        current_week: int,
    ) -> Dict:
        """Process all weekly AI updates. Called by process_week_advancement."""
        self.weeks_active += 1
        self.personality.weekly_update()

        result = {
            "new_events": [],
            "suggestions": [],
            "mood_change": None,
            "messages": [],
        }

        # Update mood based on game state
        self._evaluate_game_state(budget, fans, prestige, roster)

        # Decay event cooldowns
        for event_type in list(self.event_cooldowns.keys()):
            self.event_cooldowns[event_type] -= 1
            if self.event_cooldowns[event_type] <= 0:
                del self.event_cooldowns[event_type]

        # Generate random events (if creative control enabled)
        if self.creative_control_enabled:
            new_events = self._generate_weekly_events(roster, budget, fans, prestige, current_week)
            result["new_events"] = new_events

        # Generate booking suggestions
        if self.creative_control_enabled and roster:
            suggestions = self._generate_booking_suggestions(roster)
            result["suggestions"] = suggestions
            self.pending_suggestions.extend(suggestions)

        # Pick/update favorites
        if roster and self.weeks_active % 4 == 0:
            self.personality.pick_favorite(roster)

        return result

    # ==================== GAME STATE EVALUATION ====================

    def _evaluate_game_state(self, budget, fans, prestige, roster):
        """Evaluate the current game state and trigger mood changes"""

        # Budget concerns
        if budget < 1000:
            self.personality.process_mood_trigger("money_crisis")
        elif budget > 50000:
            self.personality.process_mood_trigger("fan_growth")

        # Fan concerns
        if fans < 100:
            self.personality.process_mood_trigger("fan_loss")
        elif fans > 10000:
            self.personality.process_mood_trigger("fan_growth")

        # Roster concerns
        injured = len([w for w in roster if w.get("is_injured", False)])
        if injured > len(roster) * 0.3:
            self.personality.process_mood_trigger("injury_crisis")

        # Show streak evaluation
        if self.consecutive_bad_shows >= 3:
            self.personality.process_mood_trigger("terrible_show")
        elif self.consecutive_good_shows >= 3:
            self.personality.process_mood_trigger("great_show")

    # ==================== SHOW RESULTS ====================

    def record_show_result(self, avg_rating: float, attendance: int, is_sellout: bool, profit: int):
        """Record show results and update AI mood accordingly"""
        self.shows_directed += 1
        self.last_show_rating = avg_rating

        if avg_rating >= 4.0:
            self.personality.process_mood_trigger("great_show")
            self.consecutive_good_shows += 1
            self.consecutive_bad_shows = 0
        elif avg_rating >= 3.0:
            self.personality.process_mood_trigger("good_show")
            self.consecutive_good_shows += 1
            self.consecutive_bad_shows = 0
        elif avg_rating >= 2.0:
            self.personality.process_mood_trigger("bad_show")
            self.consecutive_bad_shows += 1
            self.consecutive_good_shows = 0
        else:
            self.personality.process_mood_trigger("terrible_show")
            self.consecutive_bad_shows += 1
            self.consecutive_good_shows = 0

        if is_sellout:
            self.personality.process_mood_trigger("sellout")

        # Store for memory
        self.personality.remember_event("show_completed", {
            "rating": avg_rating,
            "attendance": attendance,
            "is_sellout": is_sellout,
            "profit": profit,
        })

    def record_match_result(self, winner_name: str, loser_name: str, rating: float):
        """Record individual match result for AI tracking"""
        self.recent_matches.append({
            "winner": winner_name,
            "loser": loser_name,
            "rating": rating,
        })
        # Keep last 50 matches
        if len(self.recent_matches) > 50:
            self.recent_matches = self.recent_matches[-50:]

        if rating >= 5.0:
            self.personality.process_mood_trigger("five_star_match")
        elif rating >= 4.0:
            self.personality.process_mood_trigger("good_show")

    # ==================== EVENT GENERATION ====================

    def _generate_weekly_events(self, roster, budget, fans, prestige, current_week) -> List:
        """Generate random weekly events based on AI personality and game state"""
        events = []
        chaos = self.personality.get_chaos_factor()

        # Higher chaos = more events
        event_chance = 0.1 + (chaos * 0.3)

        if random.random() > event_chance:
            return events

        # Possible event types
        event_pool = []

        if roster:
            event_pool.extend([
                "morale_issue", "contract_demand", "backstage_incident",
                "viral_moment", "media_opportunity",
            ])

        if budget < 5000:
            event_pool.append("financial_pressure")

        if fans > 5000:
            event_pool.extend(["sponsor_offer", "media_interview"])

        if prestige > 30:
            event_pool.append("talent_interest")

        if not event_pool:
            return events

        event_type = random.choice(event_pool)

        # Check cooldown
        if event_type in self.event_cooldowns:
            return events

        event = self._create_event(event_type, roster, budget, current_week)
        if event:
            events.append(event)
            self.active_events.append(event)
            self.event_cooldowns[event_type] = random.randint(2, 6)

        return events

    def _create_event(self, event_type, roster, budget, current_week):
        """Create a specific event with personality-tinted description"""
        from ai.event_generator import EventSeverity

        if event_type == "morale_issue" and roster:
            wrestler = random.choice(roster)
            if wrestler.get("morale", 75) < 50:
                return SimpleEvent(
                    id=f"event_{current_week}_{event_type}",
                    event_type=event_type,
                    severity=EventSeverity.MINOR,
                    title=f"{wrestler['name']} is unhappy",
                    description=f"{wrestler['name']} has low morale and is considering their options.",
                    wrestlers_involved=[wrestler['name']],
                    options=[
                        {"label": "Give a raise (+$100/wk)", "effects": {"salary_change": 100, "morale": 15}},
                        {"label": "Promise a push", "effects": {"morale": 10}},
                        {"label": "Ignore it", "effects": {"morale": -5}},
                    ],
                )

        elif event_type == "viral_moment" and roster:
            wrestler = random.choice(roster)
            return SimpleEvent(
                id=f"event_{current_week}_{event_type}",
                event_type=event_type,
                severity=EventSeverity.MINOR,
                title=f"{wrestler['name']} goes viral!",
                description=f"A clip of {wrestler['name']} has gone viral on social media! This could boost your promotion.",
                wrestlers_involved=[wrestler['name']],
                options=[
                    {"label": "Capitalize on it!", "effects": {"morale": 10}},
                    {"label": "Ignore it", "effects": {}},
                ],
            )

        elif event_type == "financial_pressure":
            return SimpleEvent(
                id=f"event_{current_week}_{event_type}",
                event_type=event_type,
                severity=EventSeverity.MAJOR,
                title="Financial Warning",
                description=f"Your budget is critically low at ${budget:,}. Consider cutting costs or taking a loan.",
                wrestlers_involved=[],
                options=[
                    {"label": "Cut production costs", "effects": {}},
                    {"label": "Release lowest-paid wrestler", "effects": {}},
                    {"label": "Take it week by week", "effects": {}},
                ],
            )

        return None

    # ==================== BOOKING SUGGESTIONS ====================

    def _generate_booking_suggestions(self, roster) -> List[Dict]:
        """Generate personality-tinted booking suggestions"""
        suggestions = []

        if len(roster) < 2:
            return suggestions

        # Pick two random wrestlers for a suggestion
        available = [w for w in roster if not w.get("is_injured", False)]
        if len(available) < 2:
            return suggestions

        w1, w2 = random.sample(available, 2)
        suggestion_text = self.personality.get_booking_suggestion(
            wrestler1=w1["name"], wrestler2=w2["name"]
        )

        if suggestion_text:
            suggestions.append({
                "text": suggestion_text,
                "wrestlers": [w1["name"], w2["name"]],
                "personality": self.personality.get_name(),
            })

        return suggestions

    # ==================== EVENT MANAGEMENT ====================

    def get_active_events(self) -> List:
        """Get all active unresolved events"""
        return [e for e in self.active_events if not getattr(e, 'resolved', False)]

    def resolve_event(self, event_id: str, option_index: int) -> Dict:
        """Resolve an event with the chosen option"""
        event = None
        for e in self.active_events:
            if e.id == event_id:
                event = e
                break

        if not event:
            return {"success": False, "message": "Event not found"}

        if option_index < 0 or option_index >= len(event.options):
            return {"success": False, "message": "Invalid option"}

        chosen = event.options[option_index]
        effects = chosen.get("effects", {})

        event.resolved = True
        self.active_events.remove(event)
        self.resolved_events.append(event)

        return {
            "success": True,
            "message": f"Resolved: {chosen['label']}",
            "effects": effects,
            "event": event,
        }

    # ==================== VOICE / TEXT GENERATION ====================

    def generate_show_reaction(self, avg_rating: float) -> str:
        """Get AI personality's reaction to a show"""
        return self.personality.get_show_reaction(avg_rating)

    def generate_greeting(self) -> str:
        return self.personality.get_greeting()

    def generate_booking_pitch(self, wrestler1: str = "", wrestler2: str = "") -> str:
        greeting = self.personality.get_greeting()
        suggestion = self.personality.get_booking_suggestion(wrestler1, wrestler2)
        sign_off = self.personality.get_sign_off()
        return f"{greeting}\n\n{suggestion}\n\n{sign_off}"

    def generate_mood_message(self) -> Optional[str]:
        return self.voice.generate_mood_message()

    # ==================== AI INFO ====================

    def get_director_info(self) -> Dict:
        """Get display info about the current AI Director"""
        mood_info = self.personality.get_mood_display()
        return {
            "name": self.personality.get_name(),
            "icon": self.personality.get_icon(),
            "color": self.personality.get_color(),
            "description": self.personality.get_description(),
            "mood": mood_info,
            "favorite_wrestler": self.personality.favorite_wrestler,
            "weeks_active": self.weeks_active,
            "shows_directed": self.shows_directed,
            "creative_control": self.personality.creative_control_level.value,
            "chaos_factor": f"{self.personality.get_chaos_factor() * 100:.0f}%",
        }

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "personality": self.personality.to_dict(),
            "creative_control_enabled": self.creative_control_enabled,
            "weeks_active": self.weeks_active,
            "shows_directed": self.shows_directed,
            "last_show_rating": self.last_show_rating,
            "consecutive_bad_shows": self.consecutive_bad_shows,
            "consecutive_good_shows": self.consecutive_good_shows,
            "active_events": [e.to_dict() for e in self.active_events if hasattr(e, 'to_dict')],
            "resolved_events": [e.to_dict() for e in self.resolved_events[-20:] if hasattr(e, 'to_dict')],
            "event_cooldowns": self.event_cooldowns,
            "recent_matches": self.recent_matches[-30:],
            "wrestler_push_list": self.wrestler_push_list,
            "wrestler_depush_list": self.wrestler_depush_list,
            "accepted_suggestions": self.accepted_suggestions,
            "rejected_suggestions": self.rejected_suggestions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AIDirector":
        director = cls(
            creative_control_enabled=data.get("creative_control_enabled", False),
        )
        if "personality" in data:
            director.personality = PersonalityManager.from_dict(data["personality"])
            director.voice = VoiceEngine(director.personality)
        director.weeks_active = data.get("weeks_active", 0)
        director.shows_directed = data.get("shows_directed", 0)
        director.last_show_rating = data.get("last_show_rating", 0.0)
        director.consecutive_bad_shows = data.get("consecutive_bad_shows", 0)
        director.consecutive_good_shows = data.get("consecutive_good_shows", 0)
        director.event_cooldowns = data.get("event_cooldowns", {})
        director.recent_matches = data.get("recent_matches", [])
        director.wrestler_push_list = data.get("wrestler_push_list", [])
        director.wrestler_depush_list = data.get("wrestler_depush_list", [])
        director.accepted_suggestions = data.get("accepted_suggestions", 0)
        director.rejected_suggestions = data.get("rejected_suggestions", 0)

        # Restore events
        for ed in data.get("active_events", []):
            try:
                director.active_events.append(SimpleEvent.from_dict(ed))
            except Exception:
                pass
        for ed in data.get("resolved_events", []):
            try:
                e = SimpleEvent.from_dict(ed)
                e.resolved = True
                director.resolved_events.append(e)
            except Exception:
                pass

        return director


# ==================== SIMPLE EVENT CLASS ====================

@dataclass
class SimpleEvent:
    """Lightweight event for AI-generated scenarios"""
    id: str
    event_type: str
    severity: object
    title: str
    description: str
    wrestlers_involved: List[str] = field(default_factory=list)
    options: List[Dict] = field(default_factory=list)
    resolved: bool = False
    week_created: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity.value if hasattr(self.severity, 'value') else str(self.severity),
            "title": self.title,
            "description": self.description,
            "wrestlers_involved": self.wrestlers_involved,
            "options": self.options,
            "resolved": self.resolved,
            "week_created": self.week_created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleEvent":
        from ai.event_generator import EventSeverity
        severity_map = {
            "Minor": EventSeverity.MINOR,
            "Major": EventSeverity.MAJOR,
            "Critical": EventSeverity.CRITICAL,
        }
        return cls(
            id=data.get("id", ""),
            event_type=data.get("event_type", ""),
            severity=severity_map.get(data.get("severity", "Minor"), EventSeverity.MINOR),
            title=data.get("title", ""),
            description=data.get("description", ""),
            wrestlers_involved=data.get("wrestlers_involved", []),
            options=data.get("options", []),
            resolved=data.get("resolved", False),
            week_created=data.get("week_created", 0),
        )
