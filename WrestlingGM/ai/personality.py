"""
Personality Engine - Makes wrestlers behave consistently
Each wrestler has personality traits that affect their behavior
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import random


class PersonalityTrait(Enum):
    """Core personality traits that affect behavior"""
    # Positive traits
    HUMBLE = "Humble"
    TEAM_PLAYER = "Team Player"
    HARD_WORKER = "Hard Worker"
    PROFESSIONAL = "Professional"
    LOYAL = "Loyal"
    MENTOR = "Mentor"
    EASY_GOING = "Easy Going"
    GRATEFUL = "Grateful"
    PUNCTUAL = "Punctual"
    LEADER = "Leader"
    
    # Negative traits
    EGO_MANIAC = "Ego Maniac"
    DIVA = "Diva"
    TROUBLEMAKER = "Troublemaker"
    BACKSTABBER = "Backstabber"
    LAZY = "Lazy"
    UNRELIABLE = "Unreliable"
    HOT_HEAD = "Hot Head"
    JEALOUS = "Jealous"
    POLITICAL = "Political"
    SELFISH = "Selfish"
    
    # Neutral/Situational traits
    AMBITIOUS = "Ambitious"
    COMPETITIVE = "Competitive"
    SENSITIVE = "Sensitive"
    INTROVERT = "Introvert"
    EXTROVERT = "Extrovert"
    PERFECTIONIST = "Perfectionist"
    RISK_TAKER = "Risk Taker"
    CAUTIOUS = "Cautious"
    MONEY_MOTIVATED = "Money Motivated"
    LEGACY_FOCUSED = "Legacy Focused"


class MoodState(Enum):
    """Current mood of a wrestler"""
    ECSTATIC = "Ecstatic"
    HAPPY = "Happy"
    CONTENT = "Content"
    NEUTRAL = "Neutral"
    ANNOYED = "Annoyed"
    FRUSTRATED = "Frustrated"
    ANGRY = "Angry"
    FURIOUS = "Furious"
    DEPRESSED = "Depressed"


@dataclass
class PersonalityProfile:
    """Complete personality profile for a wrestler"""
    
    # Core traits (2-4 traits per wrestler)
    traits: List[PersonalityTrait] = field(default_factory=list)
    
    # Behavioral scores (0-100)
    ego: int = 50
    loyalty: int = 50
    professionalism: int = 50
    ambition: int = 50
    patience: int = 50
    greed: int = 50
    volatility: int = 50  # How unpredictable they are
    
    # Current state
    mood: MoodState = MoodState.NEUTRAL
    mood_momentum: int = 0  # Positive = improving, Negative = worsening
    
    # Relationships matter
    friends: List[str] = field(default_factory=list)  # Wrestler names
    enemies: List[str] = field(default_factory=list)
    mentors: List[str] = field(default_factory=list)
    proteges: List[str] = field(default_factory=list)
    
    # Triggers - what sets them off
    triggers: List[str] = field(default_factory=list)
    
    # Memory of recent events
    recent_events: List[Dict] = field(default_factory=list)
    grudges: Dict[str, int] = field(default_factory=dict)  # name -> intensity
    
    def has_trait(self, trait: PersonalityTrait) -> bool:
        return trait in self.traits
    
    def is_positive_personality(self) -> bool:
        """Check if wrestler has generally positive personality"""
        positive_traits = [
            PersonalityTrait.HUMBLE, PersonalityTrait.TEAM_PLAYER,
            PersonalityTrait.HARD_WORKER, PersonalityTrait.PROFESSIONAL,
            PersonalityTrait.LOYAL, PersonalityTrait.MENTOR,
            PersonalityTrait.EASY_GOING, PersonalityTrait.GRATEFUL,
        ]
        return any(t in self.traits for t in positive_traits)
    
    def is_problematic(self) -> bool:
        """Check if wrestler has problematic personality"""
        problem_traits = [
            PersonalityTrait.EGO_MANIAC, PersonalityTrait.DIVA,
            PersonalityTrait.TROUBLEMAKER, PersonalityTrait.BACKSTABBER,
            PersonalityTrait.HOT_HEAD, PersonalityTrait.SELFISH,
        ]
        return any(t in self.traits for t in problem_traits)
    
    def to_dict(self) -> dict:
        return {
            "traits": [t.value for t in self.traits],
            "ego": self.ego,
            "loyalty": self.loyalty,
            "professionalism": self.professionalism,
            "ambition": self.ambition,
            "patience": self.patience,
            "greed": self.greed,
            "volatility": self.volatility,
            "mood": self.mood.value,
            "mood_momentum": self.mood_momentum,
            "friends": self.friends,
            "enemies": self.enemies,
            "mentors": self.mentors,
            "proteges": self.proteges,
            "triggers": self.triggers,
            "recent_events": self.recent_events[-20:],
            "grudges": self.grudges,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PersonalityProfile":
        profile = cls()
        profile.traits = [PersonalityTrait(t) for t in data.get("traits", [])]
        profile.ego = data.get("ego", 50)
        profile.loyalty = data.get("loyalty", 50)
        profile.professionalism = data.get("professionalism", 50)
        profile.ambition = data.get("ambition", 50)
        profile.patience = data.get("patience", 50)
        profile.greed = data.get("greed", 50)
        profile.volatility = data.get("volatility", 50)
        profile.mood = MoodState(data.get("mood", "Neutral"))
        profile.mood_momentum = data.get("mood_momentum", 0)
        profile.friends = data.get("friends", [])
        profile.enemies = data.get("enemies", [])
        profile.mentors = data.get("mentors", [])
        profile.proteges = data.get("proteges", [])
        profile.triggers = data.get("triggers", [])
        profile.recent_events = data.get("recent_events", [])
        profile.grudges = data.get("grudges", {})
        return profile


class PersonalityEngine:
    """
    Manages personality-based behaviors and decisions.
    Used by AI Director to determine wrestler actions.
    """
    
    # Trait influences on behavior chances
    TRAIT_MODIFIERS = {
        PersonalityTrait.EGO_MANIAC: {
            "demand_raise": 2.0,
            "refuse_to_lose": 2.5,
            "demand_main_event": 2.0,
            "complain_publicly": 1.5,
            "mentor_others": 0.2,
        },
        PersonalityTrait.DIVA: {
            "demand_raise": 1.8,
            "backstage_drama": 2.0,
            "refuse_storyline": 1.5,
            "demand_special_treatment": 2.0,
        },
        PersonalityTrait.TROUBLEMAKER: {
            "start_fight": 2.0,
            "spread_rumors": 1.8,
            "undermine_management": 1.5,
            "no_show": 1.3,
        },
        PersonalityTrait.BACKSTABBER: {
            "go_into_business": 2.0,
            "leak_to_press": 1.8,
            "talk_to_rivals": 1.5,
            "blame_others": 1.7,
        },
        PersonalityTrait.LOYAL: {
            "demand_raise": 0.5,
            "talk_to_rivals": 0.2,
            "defend_company": 2.0,
            "stay_during_crisis": 2.0,
        },
        PersonalityTrait.PROFESSIONAL: {
            "no_show": 0.1,
            "refuse_to_lose": 0.3,
            "backstage_drama": 0.3,
            "go_into_business": 0.1,
            "exceed_expectations": 1.5,
        },
        PersonalityTrait.HUMBLE: {
            "demand_raise": 0.5,
            "demand_main_event": 0.3,
            "refuse_to_lose": 0.4,
            "mentor_others": 1.8,
        },
        PersonalityTrait.HOT_HEAD: {
            "start_fight": 2.5,
            "explode_on_camera": 2.0,
            "walk_out": 1.5,
            "confront_management": 1.8,
        },
        PersonalityTrait.MONEY_MOTIVATED: {
            "demand_raise": 2.0,
            "talk_to_rivals": 1.5,
            "accept_paycut": 0.2,
            "work_hurt": 0.5,
        },
        PersonalityTrait.AMBITIOUS: {
            "demand_main_event": 1.5,
            "demand_title_shot": 1.5,
            "work_extra_hard": 1.5,
            "politic_backstage": 1.3,
        },
        PersonalityTrait.MENTOR: {
            "mentor_others": 2.5,
            "help_young_talent": 2.0,
            "accept_lesser_role": 1.5,
        },
        PersonalityTrait.TEAM_PLAYER: {
            "help_storyline": 1.5,
            "accept_loss": 1.8,
            "support_others": 1.7,
            "complain": 0.4,
        },
    }
    
    # Mood thresholds
    MOOD_THRESHOLDS = {
        MoodState.ECSTATIC: 90,
        MoodState.HAPPY: 75,
        MoodState.CONTENT: 60,
        MoodState.NEUTRAL: 45,
        MoodState.ANNOYED: 30,
        MoodState.FRUSTRATED: 20,
        MoodState.ANGRY: 10,
        MoodState.FURIOUS: 0,
    }
    
    def __init__(self):
        self.profiles: Dict[str, PersonalityProfile] = {}
    
    def get_or_create_profile(self, wrestler_name: str, wrestler_stats: Dict = None) -> PersonalityProfile:
        """Get existing profile or create new one based on wrestler stats"""
        if wrestler_name in self.profiles:
            return self.profiles[wrestler_name]
        
        profile = self._generate_profile(wrestler_stats or {})
        self.profiles[wrestler_name] = profile
        return profile
    
    def _generate_profile(self, stats: Dict) -> PersonalityProfile:
        """Generate a personality profile based on wrestler stats"""
        profile = PersonalityProfile()
        
        # Use stats to influence personality
        ego = stats.get("ego", 50)
        loyalty = stats.get("loyalty", 50)
        professionalism = stats.get("professionalism", 50)
        popularity = stats.get("popularity", 50)
        
        profile.ego = ego
        profile.loyalty = loyalty
        profile.professionalism = professionalism
        profile.ambition = random.randint(30, 80)
        profile.patience = random.randint(30, 70)
        profile.greed = random.randint(20, 70)
        profile.volatility = random.randint(20, 60)
        
        # Assign traits based on stats
        possible_traits = []
        
        # High ego
        if ego > 70:
            possible_traits.extend([
                PersonalityTrait.EGO_MANIAC,
                PersonalityTrait.DIVA,
                PersonalityTrait.AMBITIOUS,
            ])
        elif ego < 30:
            possible_traits.extend([
                PersonalityTrait.HUMBLE,
                PersonalityTrait.TEAM_PLAYER,
            ])
        
        # Loyalty
        if loyalty > 70:
            possible_traits.extend([
                PersonalityTrait.LOYAL,
                PersonalityTrait.GRATEFUL,
            ])
        elif loyalty < 30:
            possible_traits.extend([
                PersonalityTrait.BACKSTABBER,
                PersonalityTrait.SELFISH,
            ])
        
        # Professionalism
        if professionalism > 70:
            possible_traits.extend([
                PersonalityTrait.PROFESSIONAL,
                PersonalityTrait.HARD_WORKER,
                PersonalityTrait.PUNCTUAL,
            ])
        elif professionalism < 30:
            possible_traits.extend([
                PersonalityTrait.TROUBLEMAKER,
                PersonalityTrait.UNRELIABLE,
                PersonalityTrait.LAZY,
            ])
        
        # Veterans often become mentors
        age = stats.get("age", 25)
        if age > 35 and professionalism > 50:
            possible_traits.append(PersonalityTrait.MENTOR)
        
        # Popular wrestlers can develop egos
        if popularity > 80:
            if random.random() < 0.3:
                possible_traits.append(PersonalityTrait.EGO_MANIAC)
        
        # Add some random traits
        all_traits = list(PersonalityTrait)
        random_traits = random.sample(all_traits, 2)
        possible_traits.extend(random_traits)
        
        # Select 2-4 traits
        num_traits = random.randint(2, 4)
        if possible_traits:
            selected = random.sample(list(set(possible_traits)), min(num_traits, len(set(possible_traits))))
            profile.traits = selected
        
        # Generate triggers
        profile.triggers = self._generate_triggers(profile)
        
        return profile
    
    def _generate_triggers(self, profile: PersonalityProfile) -> List[str]:
        """Generate what triggers this wrestler"""
        triggers = []
        
        if profile.has_trait(PersonalityTrait.EGO_MANIAC):
            triggers.extend(["losing clean", "not in main event", "being disrespected"])
        
        if profile.has_trait(PersonalityTrait.JEALOUS):
            triggers.extend(["others getting pushed", "title shots for others"])
        
        if profile.has_trait(PersonalityTrait.HOT_HEAD):
            triggers.extend(["criticism", "being corrected", "losing"])
        
        if profile.has_trait(PersonalityTrait.MONEY_MOTIVATED):
            triggers.extend(["others earning more", "no raise", "bonus denied"])
        
        if profile.has_trait(PersonalityTrait.AMBITIOUS):
            triggers.extend(["stuck in midcard", "no title opportunities"])
        
        # Everyone has some triggers
        if not triggers:
            triggers = ["losing streak", "being ignored"]
        
        return triggers
    
    def calculate_behavior_chance(
        self,
        wrestler_name: str,
        behavior: str,
        context: Dict = None
    ) -> float:
        """
        Calculate the chance (0.0 to 1.0) of a wrestler exhibiting a behavior.
        Context can include: recent_loss, denied_raise, momentum, etc.
        """
        profile = self.get_or_create_profile(wrestler_name)
        context = context or {}
        
        # Base chance
        base_chance = 0.05  # 5% base for most behaviors
        
        # Positive behaviors have different base
        positive_behaviors = ["mentor_others", "help_storyline", "exceed_expectations", "support_others"]
        if behavior in positive_behaviors:
            base_chance = 0.1
        
        # Apply trait modifiers
        modifier = 1.0
        for trait in profile.traits:
            trait_mods = self.TRAIT_MODIFIERS.get(trait, {})
            if behavior in trait_mods:
                modifier *= trait_mods[behavior]
        
        # Apply stat modifiers
        if behavior in ["demand_raise", "demand_main_event", "refuse_to_lose"]:
            modifier *= (profile.ego / 50)  # High ego increases chance
        
        if behavior in ["no_show", "walk_out", "talk_to_rivals"]:
            modifier *= ((100 - profile.loyalty) / 50)  # Low loyalty increases chance
        
        if behavior in ["backstage_drama", "start_fight", "explode_on_camera"]:
            modifier *= (profile.volatility / 50)
        
        # Apply mood modifiers
        mood_modifier = self._get_mood_modifier(profile.mood, behavior)
        modifier *= mood_modifier
        
        # Apply context modifiers
        if context.get("recent_loss") and behavior in ["refuse_to_lose", "complain", "demand_main_event"]:
            modifier *= 1.5
        
        if context.get("denied_raise") and behavior in ["talk_to_rivals", "demand_raise", "walk_out"]:
            modifier *= 2.0
        
        if context.get("low_momentum") and behavior in ["complain", "demand_title_shot"]:
            modifier *= 1.3
        
        if context.get("on_losing_streak") and behavior in ["walk_out", "refuse_storyline", "go_into_business"]:
            modifier *= 1.5
        
        # Apply grudge modifiers
        if context.get("opponent") and context["opponent"] in profile.grudges:
            grudge_intensity = profile.grudges[context["opponent"]]
            if behavior in ["refuse_to_lose", "go_into_business", "start_fight"]:
                modifier *= (1 + grudge_intensity / 50)
        
        # Calculate final chance
        final_chance = base_chance * modifier
        
        # Cap at reasonable values
        return max(0.01, min(0.95, final_chance))
    
    def _get_mood_modifier(self, mood: MoodState, behavior: str) -> float:
        """Get modifier based on current mood"""
        negative_behaviors = [
            "demand_raise", "refuse_to_lose", "walk_out", "no_show",
            "backstage_drama", "complain", "talk_to_rivals"
        ]
        positive_behaviors = [
            "mentor_others", "help_storyline", "exceed_expectations",
            "support_others", "accept_loss"
        ]
        
        mood_values = {
            MoodState.ECSTATIC: 0.3,
            MoodState.HAPPY: 0.5,
            MoodState.CONTENT: 0.7,
            MoodState.NEUTRAL: 1.0,
            MoodState.ANNOYED: 1.3,
            MoodState.FRUSTRATED: 1.6,
            MoodState.ANGRY: 2.0,
            MoodState.FURIOUS: 2.5,
        }
        
        base = mood_values.get(mood, 1.0)
        
        if behavior in negative_behaviors:
            return base  # Bad mood increases negative behavior
        elif behavior in positive_behaviors:
            return 1 / base if base > 0 else 1.0  # Bad mood decreases positive behavior
        
        return 1.0
    
    def update_mood(
        self,
        wrestler_name: str,
        event_type: str,
        intensity: int = 1
    ):
        """Update wrestler's mood based on events"""
        profile = self.get_or_create_profile(wrestler_name)
        
        # Mood changes based on events
        mood_changes = {
            # Positive events
            "won_match": 10,
            "won_title": 25,
            "main_evented": 15,
            "got_raise": 20,
            "good_match": 8,
            "five_star_match": 20,
            "fan_favorite": 10,
            "praised_by_management": 12,
            
            # Negative events
            "lost_match": -5,
            "lost_clean": -10,
            "lost_title": -20,
            "denied_raise": -15,
            "bad_match": -8,
            "demoted": -18,
            "criticized": -10,
            "passed_over": -12,
            "injured": -15,
            "friend_released": -10,
            "enemy_pushed": -8,
        }
        
        change = mood_changes.get(event_type, 0) * intensity
        profile.mood_momentum += change
        
        # Update actual mood based on momentum
        self._recalculate_mood(profile)
        
        # Record the event
        profile.recent_events.append({
            "type": event_type,
            "intensity": intensity,
            "mood_change": change,
        })
        
        # Keep only recent events
        if len(profile.recent_events) > 20:
            profile.recent_events = profile.recent_events[-20:]
    
    def _recalculate_mood(self, profile: PersonalityProfile):
        """Recalculate mood based on momentum"""
        # Normalize momentum to 0-100 range
        normalized = max(0, min(100, 50 + profile.mood_momentum))
        
        for mood, threshold in sorted(self.MOOD_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if normalized >= threshold:
                profile.mood = mood
                break
        
        # Mood momentum decays over time
        if profile.mood_momentum > 0:
            profile.mood_momentum = max(0, profile.mood_momentum - 2)
        elif profile.mood_momentum < 0:
            profile.mood_momentum = min(0, profile.mood_momentum + 2)
    
    def add_grudge(self, wrestler_name: str, target_name: str, intensity: int = 10):
        """Add or increase a grudge against another wrestler"""
        profile = self.get_or_create_profile(wrestler_name)
        
        current = profile.grudges.get(target_name, 0)
        profile.grudges[target_name] = min(100, current + intensity)
    
    def reduce_grudge(self, wrestler_name: str, target_name: str, amount: int = 5):
        """Reduce a grudge (over time or through resolution)"""
        profile = self.get_or_create_profile(wrestler_name)
        
        if target_name in profile.grudges:
            profile.grudges[target_name] = max(0, profile.grudges[target_name] - amount)
            if profile.grudges[target_name] == 0:
                del profile.grudges[target_name]
    
    def add_relationship(
        self,
        wrestler_name: str,
        other_name: str,
        relationship_type: str
    ):
        """Add a relationship between wrestlers"""
        profile = self.get_or_create_profile(wrestler_name)
        
        if relationship_type == "friend":
            if other_name not in profile.friends:
                profile.friends.append(other_name)
            if other_name in profile.enemies:
                profile.enemies.remove(other_name)
        
        elif relationship_type == "enemy":
            if other_name not in profile.enemies:
                profile.enemies.append(other_name)
            if other_name in profile.friends:
                profile.friends.remove(other_name)
        
        elif relationship_type == "mentor":
            if other_name not in profile.mentors:
                profile.mentors.append(other_name)
        
        elif relationship_type == "protege":
            if other_name not in profile.proteges:
                profile.proteges.append(other_name)
    
    def weekly_update(self):
        """Process weekly updates for all personalities"""
        for name, profile in self.profiles.items():
            # Mood momentum decays
            if profile.mood_momentum > 0:
                profile.mood_momentum = max(0, profile.mood_momentum - 1)
            elif profile.mood_momentum < 0:
                profile.mood_momentum = min(0, profile.mood_momentum + 1)
            
            self._recalculate_mood(profile)
            
            # Grudges slowly fade
            for target in list(profile.grudges.keys()):
                self.reduce_grudge(name, target, 1)
    
    def to_dict(self) -> dict:
        return {
            name: profile.to_dict()
            for name, profile in self.profiles.items()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PersonalityEngine":
        engine = cls()
        for name, profile_data in data.items():
            engine.profiles[name] = PersonalityProfile.from_dict(profile_data)
        return engine