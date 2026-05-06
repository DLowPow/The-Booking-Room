"""
AI System for The Booking Room
Personality-driven AI Director with storylines, events, news, and commentary
"""

from ai.personality import (
    PersonalityManager,
    PersonalityType,
    MoodState,
    CreativeControlLevel,
    PERSONALITIES,
)
from ai.voice import VoiceEngine, VoiceContext
from ai.director import AIDirector, SimpleEvent
from ai.event_generator import (
    EventGenerator,
    EventSeverity,
    EventCategory,
)
from ai.storyline_engine import (
    StorylineEngine,
    Storyline,
    StorylineType,
    StorylineStage,
    StorylineIntensity,
    ResolutionType,
)
from ai.commentary import (
    CommentaryGenerator,
    CommentaryBeat,
    MatchBroadcast,
    ShowBroadcast,
    CommentarySpeaker,
    BeatType,
    CrowdReaction,
)
from ai.news_generator import (
    NewsGenerator,
    NewsArticle,
    NewsCategory,
    NewsImportance,
)
from ai.rival_promotions import (
    RivalPromotionManager,
    RivalPromotion,
    RivalSize,
    RivalPhilosophy,
    RivalStrategy,
    RivalRelationship,
)

__all__ = [
    # Personality
    "PersonalityManager", "PersonalityType", "MoodState",
    "CreativeControlLevel", "PERSONALITIES",
    # Voice
    "VoiceEngine", "VoiceContext",
    # Director
    "AIDirector", "SimpleEvent",
    # Events
    "EventGenerator", "EventSeverity", "EventCategory",
    # Storylines
    "StorylineEngine", "Storyline", "StorylineType",
    "StorylineStage", "StorylineIntensity", "ResolutionType",
    # Commentary
    "CommentaryGenerator", "CommentaryBeat", "MatchBroadcast",
    "ShowBroadcast", "CommentarySpeaker", "BeatType", "CrowdReaction",
    # News
    "NewsGenerator", "NewsArticle", "NewsCategory", "NewsImportance",
    # Rivals
    "RivalPromotionManager", "RivalPromotion", "RivalSize",
    "RivalPhilosophy", "RivalStrategy", "RivalRelationship",
]
