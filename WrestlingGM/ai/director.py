"""
AI Director - Main controller for all AI systems
Coordinates events, personality, dialogue, and quests
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ai.personality import PersonalityEngine
from ai.dialogue import DialogueSystem
from ai.event_generator import EventGenerator, GameEvent
from ai.quest_system import QuestSystem
from ai.relationships import RelationshipManager


class AIDirector:
    """
    Central AI controller that coordinates all game AI systems.
    Manages events, personalities, relationships, quests, and dialogue.
    """
    
    def __init__(
        self,
        creative_control_enabled: bool = False,
        creative_control_difficulty: str = "Normal"
    ):
        # Core systems
        self.personality_engine = PersonalityEngine()
        self.dialogue_system = DialogueSystem()
        self.relationship_manager = RelationshipManager()
        self.quest_system = QuestSystem()
        
        # Event generator
        self.event_generator = EventGenerator(
            creative_control_enabled=creative_control_enabled,
            creative_control_difficulty=creative_control_difficulty,
        )
        
        # Settings
        self.creative_control_enabled = creative_control_enabled
        self.creative_control_difficulty = creative_control_difficulty
        
        # Active events
        self.active_events: List[GameEvent] = []
        self.event_history: List[GameEvent] = []
        
        # Messages for the player
        self.pending_messages: List[Dict] = []
    
    def process_weekly_update(
        self,
        roster: List[Dict],
        budget: int,
        fans: int,
        prestige: int,
        current_week: int,
        current_year: int = 1,
        active_storylines: List[Dict] = None,
        recent_show_quality: float = 3.0,
    ) -> Dict:
        """
        Process all AI systems for a weekly update.
        Returns events, messages, and updates.
        """
        result = {
            "new_events": [],
            "expired_events": [],
            "quest_updates": [],
            "messages": [],
            "relationship_changes": [],
        }
        
        # Update personalities
        self.personality_engine.weekly_update()
        
        # Update relationships
        relationship_updates = self.relationship_manager.weekly_decay()
        result["relationship_changes"] = relationship_updates
        
        # Generate new events
        new_events = self.event_generator.generate_weekly_events(
            roster=roster,
            budget=budget,
            fans=fans,
            prestige=prestige,
            current_week=current_week,
            active_storylines=active_storylines,
            recent_show_quality=recent_show_quality,
        )
        
        for event in new_events:
            self.active_events.append(event)
            result["new_events"].append(event)
        
        # Check for expired events
        expired = self._process_expired_events(current_week)
        result["expired_events"] = expired
        
        # Update quests
        quest_updates = self.quest_system.check_progress(
            fans=fans,
            budget=budget,
            prestige=prestige,
            roster_size=len(roster),
            current_week=current_week,
        )
        result["quest_updates"] = quest_updates
        
        # Collect pending messages
        result["messages"] = self.pending_messages.copy()
        self.pending_messages.clear()
        
        return result
    
    def _process_expired_events(self, current_week: int) -> List[GameEvent]:
        """Process events that have passed their deadline"""
        expired = []
        
        for event in self.active_events[:]:
            weeks_passed = current_week - event.week_created
            
            if weeks_passed >= event.deadline_weeks and not event.is_resolved:
                # Auto-resolve with default option
                if 0 <= event.auto_resolve_option < len(event.options):
                    event.resolution = f"Auto-resolved: {event.options[event.auto_resolve_option]['text']}"
                else:
                    event.resolution = "Ignored - consequences applied"
                
                event.is_resolved = True
                expired.append(event)
                self.active_events.remove(event)
                self.event_history.append(event)
        
        return expired
    
    def resolve_event(self, event_id: str, option_index: int) -> Dict:
        """Resolve an event with the chosen option"""
        result = {
            "success": False,
            "event": None,
            "effects": {},
            "message": "",
        }
        
        # Find the event
        event = None
        for e in self.active_events:
            if e.id == event_id:
                event = e
                break
        
        if not event:
            result["message"] = "Event not found"
            return result
        
        if option_index < 0 or option_index >= len(event.options):
            result["message"] = "Invalid option"
            return result
        
        # Get the chosen option
        option = event.options[option_index]
        
        # Mark as resolved
        event.is_resolved = True
        event.resolution = option["text"]
        
        # Move to history
        self.active_events.remove(event)
        self.event_history.append(event)
        
        result["success"] = True
        result["event"] = event
        result["effects"] = option.get("effects", {})
        result["message"] = f"Resolved: {option['text']}"
        
        # Update personalities based on effects
        self._apply_event_effects(event, option.get("effects", {}))
        
        return result
    
    def _apply_event_effects(self, event: GameEvent, effects: Dict):
        """Apply effects from an event resolution"""
        wrestlers = event.wrestlers_involved
        
        if not wrestlers:
            return
        
        primary_wrestler = wrestlers[0]
        
        # Morale changes
        if "morale" in effects:
            event_type = "praised_by_management" if effects["morale"] > 0 else "criticized"
            self.personality_engine.update_mood(
                primary_wrestler,
                event_type,
                abs(effects["morale"]) // 5
            )
        
        if "wrestler_morale" in effects:
            event_type = "praised_by_management" if effects["wrestler_morale"] > 0 else "criticized"
            self.personality_engine.update_mood(
                primary_wrestler,
                event_type,
                abs(effects["wrestler_morale"]) // 5
            )
        
        # Target effects (for confrontations)
        if len(wrestlers) > 1 and "target_morale" in effects:
            event_type = "praised_by_management" if effects["target_morale"] > 0 else "criticized"
            self.personality_engine.update_mood(
                wrestlers[1],
                event_type,
                abs(effects["target_morale"]) // 5
            )
        
        # Loyalty changes
        if "loyalty" in effects:
            profile = self.personality_engine.get_or_create_profile(primary_wrestler)
            profile.loyalty = max(0, min(100, profile.loyalty + effects["loyalty"]))
        
        # Ego changes
        if "ego" in effects:
            profile = self.personality_engine.get_or_create_profile(primary_wrestler)
            profile.ego = max(0, min(100, profile.ego + effects["ego"]))
        
        # Create grudges for negative interactions
        if len(wrestlers) > 1 and effects.get("target_morale", 0) < -10:
            self.personality_engine.add_grudge(wrestlers[1], primary_wrestler, 15)
        
        # Create relationships for feuds
        if len(wrestlers) > 1 and effects.get("creates_feud"):
            self.relationship_manager.add_relationship(
                primary_wrestler, wrestlers[1], "Rival", 50
            )
    
    def add_message(self, message_type: str, message: str, priority: int = 1):
        """Add a message for the player"""
        self.pending_messages.append({
            "type": message_type,
            "message": message,
            "priority": priority,
        })
    
    def get_active_events(self) -> List[GameEvent]:
        """Get all active events"""
        return self.active_events
    
    def get_critical_events(self) -> List[GameEvent]:
        """Get critical/major events that need immediate attention"""
        from ai.event_generator import EventSeverity
        return [
            e for e in self.active_events
            if e.severity in [EventSeverity.CRITICAL, EventSeverity.MAJOR]
        ]
    
    def get_events_by_category(self, category: str) -> List[GameEvent]:
        """Get events filtered by category"""
        from ai.event_generator import EventCategory
        try:
            cat = EventCategory(category)
            return [e for e in self.active_events if e.category == cat]
        except ValueError:
            return []
    
    def get_wrestler_mood(self, wrestler_name: str) -> str:
        """Get a wrestler's current mood"""
        profile = self.personality_engine.get_or_create_profile(wrestler_name)
        return profile.mood.value
    
    def get_wrestler_personality_summary(self, wrestler_name: str) -> Dict:
        """Get a summary of a wrestler's personality"""
        profile = self.personality_engine.get_or_create_profile(wrestler_name)
        return {
            "traits": [t.value for t in profile.traits],
            "mood": profile.mood.value,
            "ego": profile.ego,
            "loyalty": profile.loyalty,
            "professionalism": profile.professionalism,
            "friends": profile.friends,
            "enemies": profile.enemies,
            "grudges": list(profile.grudges.keys()),
        }
    
    def get_relationship_between(self, wrestler1: str, wrestler2: str) -> Optional[Dict]:
        """Get relationship between two wrestlers"""
        rel = self.relationship_manager.get_relationship(wrestler1, wrestler2)
        if rel:
            return {
                "type": rel.relationship_type.value,
                "intensity": rel.intensity,
                "duration_weeks": rel.duration_weeks,
            }
        return None
    
    def start_feud(self, wrestler1: str, wrestler2: str, intensity: int = 50):
        """Manually start a feud between two wrestlers"""
        self.relationship_manager.add_relationship(
            wrestler1, wrestler2, "Rival", intensity, "Booked feud"
        )
        self.personality_engine.add_grudge(wrestler1, wrestler2, intensity // 2)
        self.personality_engine.add_grudge(wrestler2, wrestler1, intensity // 2)
    
    def end_feud(self, wrestler1: str, wrestler2: str):
        """End a feud between two wrestlers"""
        self.relationship_manager.remove_relationship(wrestler1, wrestler2)
        self.personality_engine.reduce_grudge(wrestler1, wrestler2, 100)
        self.personality_engine.reduce_grudge(wrestler2, wrestler1, 100)
    
    def record_match_result(
        self,
        winner: str,
        loser: str,
        match_rating: float,
        was_clean: bool = True
    ):
        """Record a match result for AI processing"""
        # Update winner
        self.personality_engine.update_mood(winner, "won_match", 1)
        if match_rating >= 4.0:
            self.personality_engine.update_mood(winner, "good_match", 1)
        if match_rating >= 5.0:
            self.personality_engine.update_mood(winner, "five_star_match", 2)
        
        # Update loser
        if was_clean:
            self.personality_engine.update_mood(loser, "lost_clean", 1)
        else:
            self.personality_engine.update_mood(loser, "lost_match", 1)
        
        # Check if this affects any rivalry
        rel = self.relationship_manager.get_relationship(winner, loser)
        if rel and rel.relationship_type.value == "Rival":
            self.relationship_manager.intensify_rivalry(winner, loser, 5)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            "creative_control_enabled": self.creative_control_enabled,
            "creative_control_difficulty": self.creative_control_difficulty,
            "personality_engine": self.personality_engine.to_dict(),
            "relationship_manager": self.relationship_manager.to_dict(),
            "quest_system": self.quest_system.to_dict(),
            "event_generator": self.event_generator.to_dict(),
            "active_events": [e.to_dict() for e in self.active_events],
            "event_history": [e.to_dict() for e in self.event_history[-50:]],
            "pending_messages": self.pending_messages,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AIDirector":
        """Create from dictionary"""
        director = cls(
            creative_control_enabled=data.get("creative_control_enabled", False),
            creative_control_difficulty=data.get("creative_control_difficulty", "Normal"),
        )
        
        # Restore sub-systems
        if "personality_engine" in data:
            director.personality_engine = PersonalityEngine.from_dict(data["personality_engine"])
        
        if "relationship_manager" in data:
            director.relationship_manager = RelationshipManager.from_dict(data["relationship_manager"])
        
        if "quest_system" in data:
            director.quest_system = QuestSystem.from_dict(data["quest_system"])
        
        if "event_generator" in data:
            director.event_generator = EventGenerator.from_dict(data["event_generator"])
        
        # Restore events
        if "active_events" in data:
            from ai.event_generator import GameEvent
            director.active_events = [GameEvent.from_dict(e) for e in data["active_events"]]
        
        if "event_history" in data:
            from ai.event_generator import GameEvent
            director.event_history = [GameEvent.from_dict(e) for e in data["event_history"]]
        
        director.pending_messages = data.get("pending_messages", [])
        
        return director