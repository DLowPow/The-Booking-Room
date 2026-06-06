# ai/writers_room.py
"""
Writers Room 2.0 - Central AI Creative System for Wrestling GM
ADDITIVE MODULE. Stores all data inside game_state as plain dicts/lists
so existing save_to_file() serialization captures it automatically.
"""

import random
import time

# ---- Safe imports of partially-wired systems -----------------------------
# These won't crash if the modules aren't fully connected yet.
try:
    from ai.wrestler_mind import react_to_storyline as _mind_react
except Exception:
    _mind_react = None

try:
    from ai.memory_core import record_memory as _record_memory
except Exception:
    _record_memory = None


# ==========================================================================
# DIRECTOR PERSONALITIES
# Different directors produce different pitch styles / risk profiles.
# ==========================================================================
DIRECTOR_PROFILES = {
    "traditional": {
        "name": "Traditional Booker",
        "blurb": "Long builds, clean payoffs, protects the stars.",
        "risk_bias": -10, "heat_bias": 5, "twist_chance": 0.15,
        "favored_types": ["rivalry", "championship", "redemption"],
    },
    "chaos": {
        "name": "Chaos Booker",
        "blurb": "Swerves, betrayals, nothing is safe.",
        "risk_bias": 25, "heat_bias": 15, "twist_chance": 0.55,
        "favored_types": ["betrayal", "faction_war", "double_turn"],
    },
    "corporate": {
        "name": "Corporate Executive",
        "blurb": "Merch movers, mainstream-friendly, low risk.",
        "risk_bias": -15, "heat_bias": 0, "twist_chance": 0.10,
        "favored_types": ["championship", "corporate_authority", "underdog"],
    },
    "indie": {
        "name": "Indie Visionary",
        "blurb": "Workrate feuds, slow-burn psychology, cult heat.",
        "risk_bias": 10, "heat_bias": 20, "twist_chance": 0.30,
        "favored_types": ["rivalry", "respect", "trilogy"],
    },
}

# ==========================================================================
# WRITER ARCHETYPES (seed pool). Players can hire/fire later.
# ==========================================================================
WRITER_NAMES = [
    "Tom Graves", "Lena Marsh", "Dex Carrow", "Priya Anand",
    "Marco Bellini", "Janelle Pike", "Rhys Okafor", "Sara Vance",
]

WRITER_STYLES = ["Chaos", "Realism", "Drama", "Comedy", "Sports"]
WRITER_SPECIALTIES = [
    "Faction Warfare", "Championship Chases", "Underdog Stories",
    "Heel Turns", "Tag Team Drama", "Long-Term Booking", "Shock Swerves",
]

STORYLINE_PHASES = ["setup", "rising", "complication", "climax", "fallout"]


# ==========================================================================
# BOOTSTRAP - call from ensure_full_ai_systems(game_state)
# ==========================================================================
def ensure_writers_room(game_state):
    """Create Writers Room data on game_state if missing. Save-safe."""
    if not hasattr(game_state, "storylines") or game_state.storylines is None:
        game_state.storylines = []

    if not hasattr(game_state, "writers") or not game_state.writers:
        game_state.writers = _generate_starting_writers()

    if not hasattr(game_state, "active_director") or not game_state.active_director:
        game_state.active_director = "traditional"

    if not hasattr(game_state, "pending_pitches"):
        game_state.pending_pitches = []

    return game_state


def _generate_starting_writers(count=3):
    names = random.sample(WRITER_NAMES, k=min(count, len(WRITER_NAMES)))
    writers = []
    for n in names:
        style = random.choice(WRITER_STYLES)
        writers.append({
            "id": f"wr_{random.randint(1000,9999)}",
            "name": n,
            "style": style,
            "creativity": random.randint(45, 95),
            "discipline": random.randint(30, 90),
            "chaos": random.randint(20, 95),
            "realism": random.randint(20, 95),
            "specialty": random.choice(WRITER_SPECIALTIES),
            "morale": 70,
        })
    return writers


# ==========================================================================
# STORYLINE DATA MODEL
# ==========================================================================
def new_storyline(title, stype, participants, planned_length=8):
    return {
        "id": f"sl_{int(time.time())}_{random.randint(100,999)}",
        "title": title,
        "type": stype,
        "participants": participants,          # list of wrestler ids/names
        "heat": 0,
        "momentum": 0,
        "fan_reaction": "neutral",
        "current_phase": "setup",
        "weeks_running": 0,
        "planned_length": planned_length,
        "history": [],                          # list of weekly beat strings
        "future_plans": [],
        "twists": [],
        "status": "active",                     # active | paused | concluded
        "writer_id": None,
        "director": None,
    }


# ==========================================================================
# PITCH GENERATION  (Step 3 of your flow)
# ==========================================================================
def generate_pitches(game_state, participant_names, mode="ai",
                     director_key=None, count=3):
    """
    Returns a list of pitch dicts. Does NOT commit anything.
    mode: 'ai' | 'manual' | 'hybrid'
    """
    director_key = director_key or getattr(game_state, "active_director", "traditional")
    director = DIRECTOR_PROFILES.get(director_key, DIRECTOR_PROFILES["traditional"])

    pitches = []
    for _ in range(count):
        stype = random.choice(director["favored_types"] + ["rivalry", "championship"])
        pitch = _build_single_pitch(game_state, participant_names, stype, director, mode)
        pitches.append(pitch)

    # Persist so the UI can reference them by id after a page reload (save-safe)
    game_state.pending_pitches = pitches
    return pitches


def _build_single_pitch(game_state, names, stype, director, mode):
    a = names[0] if len(names) > 0 else "Wrestler A"
    b = names[1] if len(names) > 1 else "Wrestler B"

    narrative = _pitch_narrative(stype, a, b)

    # Projected outcomes, biased by the director personality
    base_heat = random.randint(35, 75) + director["heat_bias"]
    base_risk = random.randint(20, 60) + director["risk_bias"]
    pop_gain = random.randint(2, 14)
    morale = random.randint(-8, 10)
    duration = random.randint(4, 12)

    return {
        "pitch_id": f"p_{random.randint(10000,99999)}",
        "type": stype,
        "title": _pitch_title(stype, a, b),
        "summary": narrative,
        "participants": names,
        "projected": {
            "expected_heat": max(0, min(100, base_heat)),
            "popularity_gain": pop_gain,
            "risk": max(0, min(100, base_risk)),
            "duration_weeks": duration,
            "morale_impact": morale,
        },
        "director": director["name"],
        "mode": mode,
        "twist_seed": random.random() < director["twist_chance"],
    }


def _pitch_title(stype, a, b):
    templates = {
        "rivalry":            f"{a} vs {b}: Bad Blood",
        "betrayal":           f"The {a} Betrayal",
        "championship":       f"{a}'s Title Pursuit",
        "faction_war":        f"War of Factions: {a} & Allies",
        "redemption":         f"The Redemption of {a}",
        "double_turn":        f"{a} / {b}: The Double Turn",
        "respect":            f"{a} vs {b}: Respect on the Line",
        "trilogy":            f"{a} vs {b}: The Trilogy",
        "underdog":           f"{a}: The Long Shot",
        "corporate_authority":f"{a} vs The Front Office",
    }
    return templates.get(stype, f"{a} vs {b}")


def _pitch_narrative(stype, a, b):
    pool = {
        "rivalry": [
            f"The crowd is desperate for {a} and {b} to finally collide. "
            f"A slow-burn rivalry could carry a main event for months.",
        ],
        "betrayal": [
            f"The audience is cooling on {a}. Turning them on {b} and "
            f"revealing a long-game betrayal could reignite both acts.",
        ],
        "championship": [
            f"{a} is over enough to chase gold. A multi-week pursuit gives "
            f"the title meaning and tests {a} against the division.",
        ],
        "faction_war": [
            f"{a} is building a following. A faction forming around them "
            f"sets up a war that can involve the whole roster.",
        ],
        "redemption": [
            f"{a} has been buried for too long. A redemption arc against "
            f"{b} could turn sympathy into a genuine connection.",
        ],
        "double_turn": [
            f"Risky, but if {a} and {b} swap alignments mid-feud, the pop "
            f"could be the moment of the year.",
        ],
    }
    options = pool.get(stype, [f"A fresh program between {a} and {b}."])
    return random.choice(options)


# ==========================================================================
# COMMIT A PITCH -> creates a persistent storyline (Step 4)
# ==========================================================================
def accept_pitch(game_state, pitch_id, edits=None, writer_id=None):
    pitch = next((p for p in getattr(game_state, "pending_pitches", [])
                  if p["pitch_id"] == pitch_id), None)
    if not pitch:
        return None

    edits = edits or {}
    title = edits.get("title", pitch["title"])
    length = edits.get("planned_length", pitch["projected"]["duration_weeks"])

    sl = new_storyline(title, pitch["type"], pitch["participants"], length)
    sl["heat"] = pitch["projected"]["expected_heat"]
    sl["director"] = getattr(game_state, "active_director", "traditional")
    sl["writer_id"] = writer_id or _auto_assign_writer(game_state, pitch["type"])
    if pitch.get("twist_seed"):
        sl["future_plans"].append("planned_twist")

    game_state.storylines.append(sl)
    game_state.pending_pitches = []  # clear board

    _memory_hook(game_state, sl, event="storyline_started")
    return sl


def _auto_assign_writer(game_state, stype):
    writers = getattr(game_state, "writers", [])
    if not writers:
        return None
    # Prefer a writer whose specialty matches; else best creativity.
    matches = [w for w in writers if stype.replace("_", " ").lower()
               in w["specialty"].lower()]
    pool = matches or writers
    return max(pool, key=lambda w: w["creativity"])["id"]


# ==========================================================================
# WEEKLY PROGRESSION  - call from your weekly advance loop
# ==========================================================================
def advance_storyline_week(game_state, storyline):
    if storyline["status"] != "active":
        return storyline

    storyline["weeks_running"] += 1
    writer = _get_writer(game_state, storyline.get("writer_id"))
    director = DIRECTOR_PROFILES.get(storyline.get("director"), DIRECTOR_PROFILES["traditional"])

    # ---- Phase advancement based on planned length -----------------------
    progress = storyline["weeks_running"] / max(1, storyline["planned_length"])
    idx = min(int(progress * (len(STORYLINE_PHASES) - 1)), len(STORYLINE_PHASES) - 1)
    storyline["current_phase"] = STORYLINE_PHASES[idx]

    # ---- Beat generation -------------------------------------------------
    beat = _generate_beat(storyline, writer, director)
    storyline["history"].append({
        "week": storyline["weeks_running"],
        "phase": storyline["current_phase"],
        "beat": beat,
    })

    # ---- Heat / momentum dynamics ---------------------------------------
    creativity = writer["creativity"] if writer else 60
    quality_roll = random.randint(-15, 15) + (creativity - 60) // 4
    storyline["heat"] = max(0, min(100, storyline["heat"] + quality_roll))
    storyline["momentum"] = quality_roll

    # ---- Twists ----------------------------------------------------------
    twist_chance = director["twist_chance"]
    if writer:
        twist_chance += (writer["chaos"] - 50) / 200.0
    if random.random() < max(0.02, twist_chance):
        twist = _generate_twist(storyline)
        storyline["twists"].append({"week": storyline["weeks_running"], "twist": twist})
        storyline["heat"] = min(100, storyline["heat"] + random.randint(3, 12))

    # ---- Fan reaction label ---------------------------------------------
    storyline["fan_reaction"] = _fan_reaction(storyline["heat"])

    # ---- Wrestler psychology hook ---------------------------------------
    _mind_hook(game_state, storyline)

    # ---- Natural conclusion ---------------------------------------------
    if storyline["weeks_running"] >= storyline["planned_length"]:
        storyline["status"] = "concluded"
        _memory_hook(game_state, storyline, event="storyline_concluded")

    return storyline


def advance_all_storylines(game_state):
    """Convenience: call once per game week."""
    ensure_writers_room(game_state)
    results = []
    for sl in game_state.storylines:
        results.append(advance_storyline_week(game_state, sl))
    return results


def _generate_beat(storyline, writer, director):
    phase = storyline["current_phase"]
    p = storyline["participants"]
    a = p[0] if p else "the champion"
    b = p[1] if len(p) > 1 else "the challenger"
    beats = {
        "setup":        [f"Tension simmers between {a} and {b} after a tense confrontation."],
        "rising":       [f"{a} gains the upper hand, drawing a loud crowd reaction."],
        "complication": [f"An unexpected interference complicates things for {a}."],
        "climax":       [f"{a} and {b} tear the house down in a near-classic."],
        "fallout":      [f"The dust settles; {a} is changed by the feud with {b}."],
    }
    return random.choice(beats.get(phase, [f"{a} and {b} continue their program."]))


def _generate_twist(storyline):
    twists = [
        "A surprise heel turn shocks the arena.",
        "A returning veteran inserts themselves into the feud.",
        "A betrayal from a trusted ally.",
        "A contract stipulation is revealed.",
        "An injury angle raises the stakes.",
        "A title is put on the line unexpectedly.",
    ]
    return random.choice(twists)


def _fan_reaction(heat):
    if heat >= 80: return "red_hot"
    if heat >= 60: return "invested"
    if heat >= 40: return "neutral"
    if heat >= 20: return "cooling"
    return "rejected"


def _get_writer(game_state, writer_id):
    for w in getattr(game_state, "writers", []):
        if w["id"] == writer_id:
            return w
    return None


# ==========================================================================
# INTEGRATION HOOKS (fail-safe)
# ==========================================================================
def _mind_hook(game_state, storyline):
    if _mind_react is None:
        return
    try:
        _mind_react(game_state, storyline)
    except Exception:
        pass  # never let psychology break the week advance


def _memory_hook(game_state, storyline, event):
    if _record_memory is None:
        return
    try:
        for name in storyline["participants"]:
            _record_memory(game_state, wrestler=name, event=event,
                           detail=storyline["title"], week=storyline.get("weeks_running", 0))
    except Exception:
        pass
