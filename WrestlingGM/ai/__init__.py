"""
AI package exports for The Booking Room.
Points at the consolidated 7-file structure:
  minds · output · events · director · storytelling · rivals · world_engine

Every import is fail-safe so the package loads even mid-rebuild.
"""

# ---- File 1: minds (wrestler_mind + memory_core + relationships) ----
try:
    from ai.minds import (
        WrestlerMindManager, WrestlerMind,
        MemoryCore, AIMemory,
        RelationshipManager, Relationship,
        RelationshipType, RelationshipStatus,
        record_memory, react_to_storyline,
    )
except Exception as e:
    print(f"[ai.__init__] minds import error: {e}")

# ---- File 2: output (commentary + news_generator) ----
try:
    from ai.output import (
        CommentaryGenerator, MatchBroadcast, ShowBroadcast, CommentaryBeat,
        CommentarySpeaker, BeatType, CrowdReaction,
        NewsGenerator, NewsArticle, NewsCategory, NewsImportance,
    )
except Exception as e:
    print(f"[ai.__init__] output import error: {e}")

# ---- File 3: events (event_generator + quest_system) ----
try:
    from ai.events import (
        EventGenerator, EventSeverity, EventCategory,
        QuestSystem, Quest, QuestType, QuestStatus,
        QuestDifficulty, QuestSource,
    )
except Exception as e:
    print(f"[ai.__init__] events import error: {e}")

# ---- File 4: director (personality + voice + director) ----
try:
    from ai.director import (
        AIDirector, SimpleEvent,
        PersonalityManager, PersonalityType, MoodState, CreativeControlLevel,
        VoiceEngine, VoiceContext,
    )
except Exception as e:
    print(f"[ai.__init__] director import error: {e}")

# ---- File 5: storytelling (storyline_engine + writers_room 2.0) ----
try:
    from ai.storytelling import (
        StorylineEngine, Storyline,
        StorylineType, StorylineStage, StorylineIntensity, ResolutionType,
        # Writers Room 2.0 pitch layer
        ensure_writers_room, generate_pitches, accept_pitch,
        advance_all_storylines, advance_storyline_week,
        new_storyline, DIRECTOR_PROFILES,
    )
except Exception as e:
    print(f"[ai.__init__] storytelling import error: {e}")

# ---- File 6: rivals (rival_promotions + rival_scheduler) ----
try:
    from ai.rivals import (
        RivalPromotionManager, RivalPromotion,
        RivalScheduler, ScheduledRivalShow,
        RivalSize, RivalPhilosophy, RivalStrategy, RivalRelationship,
    )
except Exception as e:
    print(f"[ai.__init__] rivals import error: {e}")

# ---- File 7: world_engine (the conductor + audience taste) ----
try:
    from ai.world_engine import (
        WorldEngine, ensure_world_systems, run_world_week,
        ensure_world_engine, seed_audience_taste,
        get_match_chemistry, get_audience_satisfaction, drift_audience_taste,
        TASTE_AXES,
    )
except Exception as e:
    print(f"[ai.__init__] world_engine import error: {e}")


__all__ = [
    # minds
    "WrestlerMindManager", "WrestlerMind", "MemoryCore", "AIMemory",
    "RelationshipManager", "Relationship", "RelationshipType", "RelationshipStatus",
    "record_memory", "react_to_storyline",
    # output
    "CommentaryGenerator", "MatchBroadcast", "ShowBroadcast", "CommentaryBeat",
    "CommentarySpeaker", "BeatType", "CrowdReaction",
    "NewsGenerator", "NewsArticle", "NewsCategory", "NewsImportance",
    # events
    "EventGenerator", "EventSeverity", "EventCategory",
    "QuestSystem", "Quest", "QuestType", "QuestStatus",
    "QuestDifficulty", "QuestSource",
    # director
    "AIDirector", "SimpleEvent", "PersonalityManager", "PersonalityType",
    "MoodState", "CreativeControlLevel", "VoiceEngine", "VoiceContext",
    # storytelling
    "StorylineEngine", "Storyline", "StorylineType", "StorylineStage",
    "StorylineIntensity", "ResolutionType",
    "ensure_writers_room", "generate_pitches", "accept_pitch",
    "advance_all_storylines", "advance_storyline_week", "new_storyline",
    "DIRECTOR_PROFILES",
    # rivals
    "RivalPromotionManager", "RivalPromotion", "RivalScheduler",
    "ScheduledRivalShow", "RivalSize", "RivalPhilosophy",
    "RivalStrategy", "RivalRelationship",
    # world_engine
    "WorldEngine", "ensure_world_systems", "run_world_week",
    "ensure_world_engine", "seed_audience_taste",
    "get_match_chemistry", "get_audience_satisfaction", "drift_audience_taste",
    "TASTE_AXES",
]