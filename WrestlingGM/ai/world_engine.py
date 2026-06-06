# ai/world_engine.py
"""
World Engine — The conductor / brain of the living world.

Owns:
  - audience_taste (6 class-aligned axes that drift over time)
  - the chemistry matrix (which Classes make great matches)
  - the weekly tick that runs every AI subsystem in order

Reads the whole game_state live. Save-safe: audience_taste + history are
plain dicts/lists stored on game_state.

Class-aligned taste axes (mirror WrestlingStyle):
  power | high_flying | hardcore | striking | technical | charisma
  (All-Rounder satisfies every axis a little — it is not its own axis)
"""

import random

from classes.wrestler import WrestlingStyle, Alignment

# Fail-safe imports of the merged subsystems (old files may still exist mid-rebuild)
try:
    from ai.minds import WrestlerMindManager, MemoryCore, RelationshipManager
except Exception:
    WrestlerMindManager = MemoryCore = RelationshipManager = None

try:
    from ai.storytelling import StorylineEngine
except Exception:
    StorylineEngine = None

try:
    from ai.rivals import RivalPromotionManager
except Exception:
    RivalPromotionManager = None

try:
    from ai.output import NewsGenerator
except Exception:
    NewsGenerator = None


# ==========================================================================
# TASTE AXES + STYLE MAPPING
# ==========================================================================

TASTE_AXES = ["power", "high_flying", "hardcore", "striking", "technical", "charisma"]

# Each Class feeds a taste axis. All-Rounder feeds everything a little.
STYLE_TO_TASTE = {
    WrestlingStyle.POWERHOUSE: "power",
    WrestlingStyle.GIANT: "power",
    WrestlingStyle.HIGH_FLYER: "high_flying",
    WrestlingStyle.LUCHADOR: "high_flying",
    WrestlingStyle.HARDCORE: "hardcore",
    WrestlingStyle.BRAWLER: "hardcore",
    WrestlingStyle.STRIKER: "striking",
    WrestlingStyle.TECHNICIAN: "technical",
    WrestlingStyle.SHOWMAN: "charisma",
    WrestlingStyle.ALL_ROUNDER: "all",   # special: satisfies every axis
}


# ==========================================================================
# CHEMISTRY MATRIX (your "mix well together" rules)
# Symmetric pairs of WrestlingStyle -> bonus multiplier.
# ==========================================================================

_GREAT = 1.20   # showcase contrasts
_GOOD = 1.10    # solid pairings
_NEUTRAL = 1.0
_WEAK = 0.95    # same-flavour, less dynamic

# Pairings explicitly praised by design (order-independent).
CHEMISTRY_PAIRS = {
    frozenset({WrestlingStyle.GIANT, WrestlingStyle.HIGH_FLYER}): _GREAT,
    frozenset({WrestlingStyle.GIANT, WrestlingStyle.LUCHADOR}): _GREAT,
    frozenset({WrestlingStyle.POWERHOUSE, WrestlingStyle.HIGH_FLYER}): _GREAT,
    frozenset({WrestlingStyle.POWERHOUSE, WrestlingStyle.LUCHADOR}): _GOOD,
    frozenset({WrestlingStyle.HARDCORE, WrestlingStyle.STRIKER}): _GREAT,
    frozenset({WrestlingStyle.BRAWLER, WrestlingStyle.STRIKER}): _GREAT,
    frozenset({WrestlingStyle.TECHNICIAN, WrestlingStyle.SHOWMAN}): _GREAT,
    frozenset({WrestlingStyle.TECHNICIAN, WrestlingStyle.STRIKER}): _GOOD,
    frozenset({WrestlingStyle.LUCHADOR, WrestlingStyle.HIGH_FLYER}): _GOOD,
}

# Same-axis = a bit flat (two giants plodding, two flyers flipping)
SAME_AXIS_WEAK = True


def get_style_chemistry(style_a, style_b) -> float:
    """Multiplier for how well two Classes mesh. All-Rounder fits anyone."""
    if style_a is None or style_b is None:
        return _NEUTRAL
    if style_a == WrestlingStyle.ALL_ROUNDER or style_b == WrestlingStyle.ALL_ROUNDER:
        return _GOOD
    pair = frozenset({style_a, style_b})
    if pair in CHEMISTRY_PAIRS:
        return CHEMISTRY_PAIRS[pair]
    # Same taste axis = weaker contrast
    if SAME_AXIS_WEAK and STYLE_TO_TASTE.get(style_a) == STYLE_TO_TASTE.get(style_b):
        return _WEAK
    return _NEUTRAL


def get_alignment_chemistry(align_a, align_b) -> float:
    """Face vs Heel draws the classic dynamic. Same-side = flatter."""
    faces = {Alignment.MEGA_FACE, Alignment.FACE}
    heels = {Alignment.HEEL, Alignment.MEGA_HEEL}
    a_face, a_heel = align_a in faces, align_a in heels
    b_face, b_heel = align_b in faces, align_b in heels
    if (a_face and b_heel) or (a_heel and b_face):
        return 1.12          # face vs heel
    if (a_face and b_face) or (a_heel and b_heel):
        return 0.97          # same alignment, less natural conflict
    return 1.0               # tweeners / x-factor — neutral


def get_match_chemistry(w1, w2) -> float:
    """
    Full chemistry multiplier for two wrestler objects.
    Reads primary_style + alignment off the real Wrestler [19].
    Returns a multiplier (~0.92–1.34) the match engine can apply.
    """
    s1 = getattr(w1, "primary_style", None)
    s2 = getattr(w2, "primary_style", None)
    a1 = getattr(w1, "alignment", None)
    a2 = getattr(w2, "alignment", None)
    style_mult = get_style_chemistry(s1, s2)
    align_mult = get_alignment_chemistry(a1, a2)
    return round(style_mult * align_mult, 3)


# ==========================================================================
# AUDIENCE TASTE — seed, satisfaction, drift
# ==========================================================================

# Philosophy.value -> taste tilts at game start.
PHILOSOPHY_TASTE_SEED = {
    "Strong Style":          {"striking": 25, "technical": 20, "hardcore": 10},
    "Ultraviolent":          {"hardcore": 35, "striking": 10},
    "Lucha Libre":           {"high_flying": 35, "technical": 10},
    "Sports Entertainment":  {"charisma": 30, "power": 10},
    "Technical":             {"technical": 30, "striking": 10},
    "Hardcore":              {"hardcore": 30, "power": 10},
    "High Flying":           {"high_flying": 30, "charisma": 10},
    "Old School":            {"technical": 20, "power": 15, "charisma": 10},
}


def ensure_world_engine(game_state):
    """Create world-engine data on game_state if missing. Save-safe."""
    if not hasattr(game_state, "audience_taste") or not game_state.audience_taste:
        philosophy = ""
        try:
            philosophy = getattr(game_state.promotion, "philosophy", "")
            philosophy = getattr(philosophy, "value", philosophy) or ""
        except Exception:
            philosophy = ""
        game_state.audience_taste = seed_audience_taste(philosophy)
    if not hasattr(game_state, "world_history") or game_state.world_history is None:
        game_state.world_history = []
    return game_state


def seed_audience_taste(philosophy_value=""):
    """Base 50 across all axes, tilted by promotion philosophy."""
    taste = {axis: 50 for axis in TASTE_AXES}
    for axis, boost in PHILOSOPHY_TASTE_SEED.get(philosophy_value, {}).items():
        taste[axis] = min(100, taste[axis] + boost)
    return taste


def get_audience_satisfaction(match_styles, audience_taste):
    """
    0–100 score for how well a match's Classes match what the crowd wants.
    match_styles: list of WrestlingStyle (the workers in the match).
    All-Rounder draws from the crowd's single highest taste.
    """
    if not match_styles or not audience_taste:
        return 50
    scores = []
    for style in match_styles:
        axis = STYLE_TO_TASTE.get(style, "all")
        if axis == "all":
            scores.append(max(audience_taste.values()))
        else:
            scores.append(audience_taste.get(axis, 50))
    return int(sum(scores) / len(scores))


def drift_audience_taste(game_state, booked_styles, avg_rating=3.0):
    """
    The living crowd: well-received styles RISE, overexposed styles COOL.
    Call once per show with the Classes that were booked.
    """
    taste = getattr(game_state, "audience_taste", None)
    if not taste or not booked_styles:
        return taste

    # Count how often each axis appeared this show
    axis_counts = {axis: 0 for axis in TASTE_AXES}
    for style in booked_styles:
        axis = STYLE_TO_TASTE.get(style, "all")
        if axis == "all":
            for a in TASTE_AXES:
                axis_counts[a] += 0.4
        else:
            axis_counts[axis] += 1

    quality = (avg_rating - 3.0)  # -3..+2 swing
    for axis, count in axis_counts.items():
        if count <= 0:
            # Unseen styles slowly cool toward neutral
            taste[axis] += -1 if taste[axis] > 50 else (1 if taste[axis] < 50 else 0)
            continue
        # Good shows train the crowd to want more; bad shows sour them
        delta = int(quality * 2) + (1 if count >= 2 else 0)
        # Overexposure penalty: hammering one axis hard cools it slightly
        if count >= 3:
            delta -= 1
        taste[axis] = max(5, min(100, taste[axis] + delta))

    game_state.audience_taste = taste
    return taste


# ==========================================================================
# THE CONDUCTOR — weekly tick
# ==========================================================================

class WorldEngine:
    """
    The brain. Instantiates + ticks every AI subsystem each week,
    letting each feed the next. Lives on game_state; save-safe via to_dict.
    """

    def __init__(self):
        self.weeks_ticked = 0

    def ensure_systems(self, game_state):
        """Create any missing subsystems on game_state. Idempotent."""
        ensure_world_engine(game_state)

        if WrestlerMindManager and (not getattr(game_state, "wrestler_minds", None)):
            game_state.wrestler_minds = WrestlerMindManager()
        if MemoryCore and (not getattr(game_state, "ai_memory", None)):
            game_state.ai_memory = MemoryCore()
        if RelationshipManager and (not getattr(game_state, "relationship_manager", None)):
            game_state.relationship_manager = RelationshipManager()
        if StorylineEngine and (not getattr(game_state, "storyline_engine", None)):
            game_state.storyline_engine = StorylineEngine()
        if RivalPromotionManager and (not getattr(game_state, "rival_promotions", None)):
            mgr = RivalPromotionManager()
            try:
                mgr.create_starter_rivals()
            except Exception:
                pass
            game_state.rival_promotions = mgr
        if NewsGenerator and (not getattr(game_state, "news_generator", None)):
            game_state.news_generator = NewsGenerator(
                ai_director=getattr(game_state, "ai_director", None),
                storyline_engine=getattr(game_state, "storyline_engine", None),
            )
        return game_state

    def weekly_tick(self, game_state):
        """
        The heartbeat. Runs subsystems in order so each feeds the next.
        Every step is fail-safe — one broken system never stops the week.
        """
        self.ensure_systems(game_state)
        self.weeks_ticked += 1

        promotion = getattr(game_state, "promotion", None)
        week = getattr(promotion, "current_week", 0)
        year = getattr(promotion, "current_year", 1)
        roster = getattr(promotion, "roster", []) if promotion else []
        level = getattr(getattr(game_state, "progression", None), "level", 1) or 1

        summary = {"week": week, "year": year, "minds": 0, "rivals": 0, "news": 0}

        # 1) Wrestler psychology
        try:
            booked = self._booked_names(game_state)
            if getattr(game_state, "wrestler_minds", None):
                results = game_state.wrestler_minds.weekly_update(roster, booked)
                summary["minds"] = len(results)
        except Exception as e:
            print(f"WorldEngine minds error: {e}")

        # 2) Relationships drift
        try:
            if getattr(game_state, "relationship_manager", None):
                game_state.relationship_manager.weekly_decay()
        except Exception as e:
            print(f"WorldEngine relationships error: {e}")

        # 3) Storylines decay/advance (object engine)
        try:
            if getattr(game_state, "storyline_engine", None):
                game_state.storyline_engine.weekly_update()
                chaos = self._chaos(game_state)
                game_state.storyline_engine.ai_advance_storylines(week, year, chaos)
        except Exception as e:
            print(f"WorldEngine storyline error: {e}")

        # 4) Rival promotions — the relentless CPU (scales with player level)
        try:
            if getattr(game_state, "rival_promotions", None):
                fa = getattr(game_state, "free_agents", []) or []
                fa_dicts = [{"name": getattr(w, "name", ""),
                             "popularity": getattr(w, "popularity", 30)} for w in fa]
                roster_dicts = [{"name": getattr(w, "name", ""),
                                 "morale": getattr(w, "morale", 75),
                                 "loyalty": getattr(w, "loyalty", 75)} for w in roster]
                res = game_state.rival_promotions.process_weekly_operations(
                    current_week=week, current_year=year,
                    player_roster=roster_dicts, player_free_agents=fa_dicts,
                    player_prestige=getattr(promotion, "prestige", 0),
                    player_fans=getattr(promotion, "fan_base", 0),
                )
                summary["rivals"] = len(res.get("shows_run", []))
                self._publish_rival_news(game_state, res, week, year)
        except Exception as e:
            print(f"WorldEngine rivals error: {e}")

        # 5) News feed
        try:
            if getattr(game_state, "news_generator", None):
                roster_dicts = [{"name": getattr(w, "name", ""),
                                 "popularity": getattr(w, "popularity", 30),
                                 "wins": getattr(w, "wins", 0)} for w in roster]
                arts = game_state.news_generator.generate_weekly_news(
                    roster_dicts, getattr(promotion, "name", "Promotion"),
                    week, year, chaos_factor=self._chaos(game_state))
                summary["news"] = len(arts)
        except Exception as e:
            print(f"WorldEngine news error: {e}")

        game_state.world_history.append(summary)
        game_state.world_history = game_state.world_history[-52:]
        return summary

    # ---- helpers ---------------------------------------------------------
    def _booked_names(self, game_state):
        booked = set()
        bs = getattr(game_state, "booked_show", None)
        if isinstance(bs, dict):
            for match in bs.get("card", []):
                for k, v in match.items():
                    if k.startswith("wrestler") and v:
                        booked.add(v)
        return booked

    def _chaos(self, game_state):
        try:
            d = getattr(game_state, "ai_director", None)
            if d and getattr(d, "personality", None):
                return d.personality.get_chaos_factor()
        except Exception:
            pass
        return 0.3

    def _publish_rival_news(self, game_state, res, week, year):
        if not hasattr(game_state, "news_feed") or game_state.news_feed is None:
            game_state.news_feed = []
        for item in res.get("rival_news", [])[:5]:
            game_state.news_feed.insert(0, {
                "headline": item.get("headline", ""),
                "body": item.get("body", ""),
                "category": "Rival Promotion",
                "importance": "Notable",
                "week": week, "year": year,
                "sentiment": "neutral", "source": "World Engine", "icon": "⚔️",
            })
        game_state.news_feed = game_state.news_feed[:100]

    # ---- serialization ---------------------------------------------------
    def to_dict(self):
        return {"weeks_ticked": self.weeks_ticked}

    @classmethod
    def from_dict(cls, data):
        we = cls()
        we.weeks_ticked = data.get("weeks_ticked", 0)
        return we


def ensure_world_systems(game_state):
    """Convenience bootstrap for app.py. Returns the WorldEngine."""
    if not getattr(game_state, "world_engine", None):
        game_state.world_engine = WorldEngine()
    game_state.world_engine.ensure_systems(game_state)
    return game_state.world_engine


def run_world_week(game_state):
    """Convenience weekly tick for app.py's process_week_advancement."""
    we = ensure_world_systems(game_state)
    return we.weekly_tick(game_state)