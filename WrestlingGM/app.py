"""
The Booking Room - Flask Web Application
Wrestling GM Simulator with AI Director, Training School, Storylines,
Rival Promotions, Writers Room, 49 match types, iPhone UI
Version 2.1 — Consolidated 7-file AI structure + World Engine
"""

import os
import uuid
import json
import random
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps

# ==================== CORE IMPORTS ====================
from classes.wrestler import (
    Wrestler, Gender, WrestlingStyle, Alignment, WrestlerLevel,
    ContractType, CrowdReaction, MoraleState, LEVEL_INFO
)
from classes.promotion import Promotion
from classes.venue import (
    Venue, VenueTier, VenuePerk, VenueRestriction,
    MATCH_TIME_OPTIONS, get_time_quality_modifier, calculate_overrun_penalty,
    DEFAULT_DAY_MODIFIERS
)
from classes.progression import (
    ProgressionSystem, get_cumulative_limits, get_promotion_tier,
    get_tier_name, get_xp_progress, get_unlocked_match_types, MAX_LEVEL
)
from classes.locations import get_continents, get_countries, get_cities, get_currency
from classes.philosophy import get_philosophy_profile, PHILOSOPHY_PROFILES, Philosophy
from classes.championship import (
    ChampionshipManager, Championship, ChampionshipLevel,
    ChampionshipGender, ChampionshipRule, CHAMPIONSHIP_COSTS, SLOT_COSTS,
)
from classes.group import Group, GroupType, GroupManager, MIN_GROUP_SIZE, MAX_GROUP_SIZE
from classes.production import (
    ShowProduction, get_available_options, ALL_PRODUCTION_OPTIONS, CATEGORY_LABELS
)
from classes.calendar_system import CalendarSystem, MONTHS, format_date, days_in_month, date_to_day_of_year
from classes.inbox import InboxManager, Message
from classes.calls import CallsManager
from classes.injury import InjuryManager
from classes.banking import BankingManager, LoanType, BANK_LOAN_OPTIONS, SHARK_LOAN_OPTIONS
from classes.free_agency import FreeAgencyManager, FreeAgentTier, AgentListing

# ==================== TRAINING SCHOOL IMPORTS ====================
from classes.training_school import TrainingSchool, SchoolTier, SchoolStatus, SCHOOL_TIER_INFO
from classes.coach import CoachManager, CoachSpecialty, CoachStatus, CoachType
from classes.trainee import Trainee, TraineeLevel, TraineeStatus, TraineeSpecialization
from classes.trainee_show import TraineeShowManager, TraineeShowType
from data.trainee_pool import TraineePool
from data.coach_pool import CoachPool
from data.training_classes import (
    get_full_catalog_for_ui, get_school_discount_preview,
    get_class, get_eligible_classes_for_wrestler, get_recommended_classes_for_wrestler,
    can_wrestler_take_class,
    get_classes_for_trainees, get_classes_for_roster,
    roll_performance, calculate_stat_gains, apply_stat_gains_with_ceiling,
    calculate_injury_risk, STAT_CEILING_FROM_TRAINING,
)

# ==================== AI IMPORTS (consolidated 7-file structure) ====================

# director.py  (personality + voice + director merged)
from ai.director import (
    AIDirector, SimpleEvent,
    PersonalityType, CreativeControlLevel,
    VoiceEngine, VoiceContext,
)

# events.py  (event_generator + quest_system merged)
from ai.events import EventGenerator, EventSeverity, QuestSystem

# output.py  (commentary + news_generator merged)
from ai.output import CommentaryGenerator, NewsGenerator

# storytelling.py  (storyline_engine + writers_room merged)
from ai.storytelling import StorylineEngine

# Writers Room 2.0 (now lives in storytelling.py) — fail-safe import
try:
    from ai.storytelling import (
        ensure_writers_room, generate_pitches, accept_pitch,
        advance_all_storylines, DIRECTOR_PROFILES,
    )
    WRITERS_ROOM_2 = True
except Exception as e:
    print(f"Writers Room 2.0 import error: {e}")
    WRITERS_ROOM_2 = False

# rivals.py  (rival_promotions + rival_scheduler merged)
from ai.rivals import RivalPromotionManager

try:
    from ai.rivals import RivalScheduler
except Exception:
    RivalScheduler = None

# minds.py  (wrestler_mind + memory_core + relationships merged)
from ai.minds import RelationshipManager

try:
    from ai.minds import MemoryCore
except Exception:
    MemoryCore = None

try:
    from ai.minds import WrestlerMindManager
except Exception:
    WrestlerMindManager = None

# world_engine.py  (NEW — the conductor + audience taste)
try:
    from ai.world_engine import ensure_world_systems, run_world_week
    WORLD_ENGINE = True
except Exception as e:
    print(f"World Engine import error: {e}")
    WORLD_ENGINE = False

# ==================== SYSTEMS ====================
from systems.match_engine import MatchEngine
from systems.weekly_pulse import WeeklyPulse

# ==================== DATA ====================
from data.venues import get_venues_by_continent, get_all_venues, get_venue_by_id
from data.wrestler_pool import WrestlerPool
from data.wrestler_pool import generate_free_agents, get_free_agents_for_level, get_tier_for_level, TIER_CONFIG

# ==================== SAVE MANAGER ====================
from systems.save_manager import SaveManager

# ==================== GAME STATE ====================
from classes.game_state import GameState


app = Flask(__name__)
app.secret_key = 'the_booking_room_alpha_secret_key_2024'


# ==================== ERROR HANDLING ====================

@app.errorhandler(500)
def internal_error(error):
    return f"<h1>500 Error</h1><pre>{traceback.format_exc()}</pre><p>{str(error)}</p>", 500

@app.errorhandler(Exception)
def handle_exception(error):
    return f"<h1>Error</h1><pre>{traceback.format_exc()}</pre><p>{str(error)}</p>", 500


# ==================== ACCESS CONTROL ====================

DEMO_USERS = {
    "dlowpow": "BookingRoomGM26!",
    "mkbowers": "GMdemo123!",
    "jgrizzle": "wrestlingGM24!",
    "cdowen": "wrestlingGM25!",
    "mgordon": "wrestlingGM26!",
    "friend1": "demo111!",
    "friend2": "demo222!",
    "friend3": "demo333!",
    "friend4": "demo444!",
    "friend5": "demo555!",
}

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_game(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_game_state():
            flash('No active game. Please start or load a game.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== DEV MODE ====================
DEV_USERNAMES = {"dlowpow", "mkbowers"}

def is_dev_user():
    """Check if current user has dev privileges"""
    return session.get('username', '').lower() in DEV_USERNAMES

# Make is_dev_user available in all templates
@app.context_processor
def inject_dev_status():
    return {"is_dev": is_dev_user()}


@app.route('/dev/<action>', methods=['POST'])
@require_login
@require_game
def dev_action(action):
    """Single endpoint for all dev cheats. Username-gated."""
    if not is_dev_user():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    if action == 'add_money':
        amount = int(request.form.get('amount', 100000))
        promotion.budget += amount
        flash(f'💰 +${amount:,} added to budget', 'success')

    elif action == 'add_xp':
        amount = int(request.form.get('amount', 5000))
        if progression:
            try:
                progression.add_xp(amount, "Dev cheat")
                flash(f'📈 +{amount:,} XP added', 'success')
            except Exception as e:
                flash(f'XP error: {e}', 'error')

    elif action == 'add_fans':
        amount = int(request.form.get('amount', 10000))
        promotion.fan_base += amount
        flash(f'👥 +{amount:,} fans added', 'success')

    elif action == 'skip_weeks':
        weeks = int(request.form.get('weeks', 4))
        for _ in range(weeks):
            promotion.advance_days(7)
            try:
                process_week_advancement(game_state)
            except Exception:
                pass
        flash(f'⏩ Skipped {weeks} weeks', 'success')

    elif action == 'set_level':
        target_level = int(request.form.get('level', 50))
        if progression:
            try:
                from classes.progression import get_xp_progress
                while progression.level < target_level:
                    progression.add_xp(10000, "Dev level jump")
                    if progression.level >= 100:
                        break
                flash(f'🚀 Jumped to Level {progression.level}', 'success')
            except Exception as e:
                flash(f'Level jump error: {e}', 'error')

    elif action == 'sign_rookies':
        if hasattr(game_state, 'free_agency') and game_state.free_agency:
            from classes.free_agency import FreeAgentTier
            rookies = game_state.free_agency.get_listings_by_tier(FreeAgentTier.ROOKIE)
            signed = 0
            for listing in rookies[:5]:
                try:
                    success, msg, w, cost = game_state.free_agency.sign_wrestler(
                        listing.wrestler.name,
                        promotion.budget,
                        len(promotion.roster),
                        999,
                    )
                    if success and w:
                        promotion.budget -= cost
                        promotion.roster.append(w)
                        signed += 1
                except Exception:
                    pass
            flash(f'🤼 Auto-signed {signed} rookies', 'success')
        else:
            flash('Free Agency not available', 'error')

    elif action == 'found_school':
        from classes.training_school import TrainingSchool, SchoolTier, SCHOOL_TIER_INFO
        school = game_state.training_school
        if not school:
            school = TrainingSchool()
            game_state.training_school = school
        if school.is_founded():
            flash('School already founded!', 'warning')
        else:
            try:
                school.found_school(
                    name="Dev Test School",
                    location=promotion.location,
                    tier=SchoolTier.SCHOOL_GYM,
                    week=getattr(promotion, 'current_week', 0),
                    year=getattr(promotion, 'current_year', 1),
                )
                flash('🏫 Free school founded!', 'success')
            except Exception as e:
                flash(f'School error: {e}', 'error')

    elif action == 'add_trainees':
        school = game_state.training_school
        if school and school.is_founded():
            try:
                from data.trainee_pool import TraineePool
                pool = game_state.trainee_pool or TraineePool()
                added = 0
                for _ in range(5):
                    try:
                        if hasattr(pool, 'scout_for_prospects'):
                            applicant, cost, msg = pool.scout_for_prospects(
                                scouting_tier='promising',
                                budget=999999,
                                monthly_tuition=school.get_monthly_tuition(),
                            )
                            if applicant:
                                school.enroll_trainee(applicant)
                                added += 1
                    except Exception:
                        pass
                flash(f'🎓 Added {added} trainees', 'success')
            except Exception as e:
                flash(f'Trainee error: {e}', 'error')
        else:
            flash('Found a school first!', 'warning')

    elif action == 'unlock_all':
        if progression:
            try:
                progression.add_xp(999999, "Dev unlock all")
                promotion.budget += 10000000
                promotion.fan_base += 1000000
                flash('🏆 Maxed out — Lvl 100, $10M, 1M fans', 'success')
            except Exception as e:
                flash(f'Unlock error: {e}', 'error')

    else:
        flash(f'Unknown dev action: {action}', 'error')

    save_game_state(game_state)
    return redirect(request.referrer or url_for('dashboard'))


# ==================== GAME SESSION MANAGEMENT ====================

game_sessions = {}


def get_game_state():
    session_id = session.get('session_id')
    if session_id and session_id in game_sessions:
        return game_sessions[session_id]
    return None


def save_game_state(game_state):
    session_id = session.get('session_id')
    if session_id:
        game_sessions[session_id] = game_state


# ==================== AI SYSTEM BOOTSTRAP ====================

def ensure_full_ai_systems(game_state):
    """
    Ensure all AI subsystems exist on game_state. Save-safe + fail-safe.
    The World Engine is the conductor: it bootstraps minds, relationships,
    storyline_engine, rival_promotions, news, and audience_taste in one call.
    Called on new game, load, dashboard, and key progression points.
    """
    # World Engine bootstrap (the conductor builds its organs)
    if WORLD_ENGINE:
        try:
            ensure_world_systems(game_state)
        except Exception as e:
            print(f"World Engine ensure error: {e}")

    # Writers Room 2.0 data bootstrap (storylines / writers / pending_pitches)
    if WRITERS_ROOM_2:
        try:
            ensure_writers_room(game_state)
        except Exception as e:
            print(f"Writers Room 2.0 ensure error: {e}")

    return game_state


def ensure_rival_scheduler(game_state):
    """Ensure RivalScheduler exists for new and old saves."""
    if not hasattr(game_state, "rival_scheduler") or game_state.rival_scheduler is None:
        try:
            if RivalScheduler is not None:
                game_state.rival_scheduler = RivalScheduler()
            else:
                game_state.rival_scheduler = None
        except Exception as e:
            print(f"RivalScheduler init error: {e}")
            game_state.rival_scheduler = None

    return game_state.rival_scheduler


# ==================== UTILITY HELPERS ====================

def get_day_of_week(year, month, day):
    total_days = 0
    for y in range(1, year):
        for m in range(1, 13):
            total_days += days_in_month(m)
    for m in range(1, month):
        total_days += days_in_month(m)
    total_days += day - 1
    return total_days % 7

def get_day_name(day_index):
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[day_index % 7]

def get_active_seasonal_events(month, day):
    events = []
    if month == 4 and 8 <= day <= 14:
        events.append({"name": "Mania Weekend", "description": "Double XP and crowd boost!", "xp_multiplier": 2.0, "attendance_multiplier": 1.5, "fan_growth_multiplier": 2.0, "color": "#f59e0b", "icon": "🏟️"})
    if month == 8 and 24 <= day <= 31:
        events.append({"name": "SummerSlam Week", "description": "Bonus fan growth!", "xp_multiplier": 1.5, "attendance_multiplier": 1.3, "fan_growth_multiplier": 1.5, "color": "#ef4444", "icon": "☀️"})
    if month == 1 and 15 <= day <= 21:
        events.append({"name": "Rumble Season", "description": "Extra attendance boost!", "xp_multiplier": 1.3, "attendance_multiplier": 1.4, "fan_growth_multiplier": 1.3, "color": "#6366f1", "icon": "👑"})
    if month == 11 and 22 <= day <= 28:
        events.append({"name": "Survivor Series", "description": "War Games season!", "xp_multiplier": 1.4, "attendance_multiplier": 1.3, "fan_growth_multiplier": 1.4, "color": "#8b5cf6", "icon": "🏴"})
    return events


# ==================== 49 MATCH TYPE SYSTEM ====================

MATCH_CATEGORIES = {
    "Standard": "🤼 Standard Matches",
    "Tag": "🤝 Tag Team & Handicap",
    "Hardcore": "🩸 Hardcore, Weapons & Deathmatches",
    "Cage": "🔒 Cage & Enclosure",
    "Specialty": "⭐ Specialty & Gimmick",
    "Battle Royal": "👑 Battle Royals & Gauntlets",
    "Combat": "🥊 Combat Sports",
}

def get_match_type_info():
    return {
        "Singles": {"category": "Standard", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": False, "no_dq": False, "description": "Standard one-on-one match"},
        "Intergender Singles": {"category": "Standard", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": False, "description": "Mixed gender singles match"},
        "Triple Threat": {"category": "Standard", "min": 3, "max": 3, "type": "multi", "label": "3-Way", "intergender": True, "no_dq": True, "description": "Three-way, no DQ"},
        "Fatal Four Way": {"category": "Standard", "min": 4, "max": 4, "type": "multi", "label": "4-Way", "intergender": True, "no_dq": True, "description": "Four-way, no DQ"},
        "5-Way Match": {"category": "Standard", "min": 5, "max": 5, "type": "multi", "label": "5-Way", "intergender": True, "no_dq": True, "description": "Five-way, no DQ"},
        "6-Way Match": {"category": "Standard", "min": 6, "max": 6, "type": "multi", "label": "6-Way", "intergender": True, "no_dq": True, "description": "Six-way, no DQ"},
        "8-Way Match": {"category": "Standard", "min": 8, "max": 8, "type": "multi", "label": "8-Way", "intergender": True, "no_dq": True, "description": "Eight-way, no DQ"},
        "Tag Team": {"category": "Tag", "min": 4, "max": 4, "type": "tag", "label": "2v2", "intergender": False, "no_dq": False, "description": "Standard tag team", "teams": [2, 2]},
        "Mixed Tag": {"category": "Tag", "min": 4, "max": 4, "type": "tag", "label": "2v2", "intergender": True, "no_dq": False, "description": "Intergender tag team", "teams": [2, 2]},
        "Tornado Tag": {"category": "Tag", "min": 4, "max": 4, "type": "tag", "label": "2v2 Tornado", "intergender": True, "no_dq": True, "description": "All legal, no DQ", "teams": [2, 2]},
        "6-Man Tag": {"category": "Tag", "min": 6, "max": 6, "type": "tag3", "label": "3v3", "intergender": False, "no_dq": False, "description": "Three-on-three", "teams": [3, 3]},
        "8-Man Tag": {"category": "Tag", "min": 8, "max": 8, "type": "tag4", "label": "4v4", "intergender": False, "no_dq": False, "description": "Four-on-four", "teams": [4, 4]},
        "1-on-2 Handicap": {"category": "Tag", "min": 3, "max": 3, "type": "handicap", "label": "1v2", "intergender": False, "no_dq": False, "description": "One vs two", "teams": [1, 2]},
        "1-on-3 Handicap": {"category": "Tag", "min": 4, "max": 4, "type": "handicap", "label": "1v3", "intergender": False, "no_dq": False, "description": "One vs three", "teams": [1, 3]},
        "2-on-3 Handicap": {"category": "Tag", "min": 5, "max": 5, "type": "handicap", "label": "2v3", "intergender": False, "no_dq": False, "description": "Two vs three", "teams": [2, 3]},
        "Extreme Rules": {"category": "Hardcore", "min": 2, "max": 5, "type": "variable", "label": "No DQ", "intergender": True, "no_dq": True, "description": "No disqualification"},
        "Falls Count Anywhere": {"category": "Hardcore", "min": 2, "max": 6, "type": "variable", "label": "FCA", "intergender": True, "no_dq": True, "description": "Pinfalls anywhere"},
        "Ladder Match": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Ladder", "intergender": True, "no_dq": True, "description": "Climb the ladder"},
        "Table Match": {"category": "Hardcore", "min": 2, "max": 6, "type": "variable", "label": "Tables", "intergender": True, "no_dq": True, "description": "Through a table to win"},
        "TLC": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "TLC", "intergender": True, "no_dq": True, "description": "Tables, Ladders and Chairs"},
        "Barbed Wire Deathmatch": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Deathmatch", "intergender": True, "no_dq": True, "description": "Barbed wire ropes"},
        "Exploding Barbed Wire": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Deathmatch", "intergender": True, "no_dq": True, "description": "Explosive barbed wire"},
        "Landmine Deathmatch": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Deathmatch", "intergender": True, "no_dq": True, "description": "Explosive boards"},
        "Steel Cage": {"category": "Cage", "min": 2, "max": 8, "type": "variable", "label": "Cage", "intergender": True, "no_dq": True, "description": "Escape or pin inside cage"},
        "Hell in a Cell": {"category": "Cage", "min": 2, "max": 6, "type": "variable", "label": "HIAC", "intergender": True, "no_dq": True, "description": "Enclosed in a cell"},
        "Elimination Chamber": {"category": "Cage", "min": 6, "max": 6, "type": "multi", "label": "Chamber", "intergender": True, "no_dq": True, "description": "Six wrestlers, pods"},
        "War Games": {"category": "Cage", "min": 6, "max": 8, "type": "wargames", "label": "War Games", "intergender": True, "no_dq": True, "description": "Two rings, one cage", "teams": [3, 3]},
        "Ambulance Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Into an ambulance"},
        "Casket Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Into a casket"},
        "Dumpster Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Into a dumpster"},
        "I Quit": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Say I Quit"},
        "Inferno Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Ring surrounded by fire"},
        "Iron Man": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": False, "no_dq": False, "description": "Most falls wins"},
        "Last Man Standing": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "10-count to win"},
        "Submission Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": False, "no_dq": False, "description": "Submission only"},
        "3 Stages of Hell": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Best of three falls"},
        "Underground Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "No rules, no ring"},
        "Bloodline Rules": {"category": "Specialty", "min": 2, "max": 8, "type": "variable", "label": "Bloodline", "intergender": True, "no_dq": True, "description": "Tribal rules, no DQ"},
        "Brawl": {"category": "Specialty", "min": 2, "max": 4, "type": "variable", "label": "Brawl", "intergender": True, "no_dq": True, "description": "No ring, just fight"},
        "Lumberjack Match": {"category": "Specialty", "min": 2, "max": 8, "type": "variable", "label": "Lumberjack", "intergender": True, "no_dq": True, "description": "Surrounded by wrestlers"},
        "Special Guest Referee": {"category": "Specialty", "min": 3, "max": 7, "type": "referee", "label": "Guest Ref", "intergender": False, "no_dq": False, "description": "Wrestler as referee"},
        "Battle Royal": {"category": "Battle Royal", "min": 4, "max": 8, "type": "rumble", "label": "Battle Royal", "intergender": True, "no_dq": True, "description": "Over the top rope"},
        "Casino Battle Royale": {"category": "Battle Royal", "min": 8, "max": 21, "type": "rumble", "label": "Casino BR", "intergender": True, "no_dq": True, "description": "Timed entry battle royal"},
        "Royal Rumble": {"category": "Battle Royal", "min": 10, "max": 30, "type": "rumble", "label": "Rumble", "intergender": True, "no_dq": True, "description": "Timed entry elimination"},
        "Gauntlet Match": {"category": "Battle Royal", "min": 4, "max": 30, "type": "gauntlet", "label": "Gauntlet", "intergender": True, "no_dq": True, "description": "Sequential one-on-one"},
        "Gauntlet Eliminator": {"category": "Battle Royal", "min": 4, "max": 8, "type": "gauntlet", "label": "Eliminator", "intergender": True, "no_dq": True, "description": "Short format gauntlet"},
        "MMA Rules": {"category": "Combat", "min": 2, "max": 2, "type": "singles", "label": "MMA", "intergender": False, "no_dq": False, "description": "MMA rules"},
        "Kickboxing Rules": {"category": "Combat", "min": 2, "max": 2, "type": "singles", "label": "Kickboxing", "intergender": False, "no_dq": False, "description": "Standing strikes only"},
    }

def get_match_categories():
    all_types = get_match_type_info()
    categories = {}
    for name, info in all_types.items():
        cat = info.get("category", "Standard")
        if cat not in categories:
            categories[cat] = {"label": MATCH_CATEGORIES.get(cat, cat), "matches": []}
        categories[cat]["matches"].append({"name": name, "info": info})
    return categories

def get_display_for_match(match_data):
    match_type = match_data.get('match_type', 'Singles')
    info = get_match_type_info().get(match_type, {"type": "singles", "min": 2, "max": 2})
    fmt = info.get("type", "singles")
    teams = info.get("teams", None)
    if fmt == "singles":
        return f"{match_data.get('wrestler1', '?')} vs {match_data.get('wrestler2', '?')}"
    elif fmt in ["tag", "handicap"] and teams:
        t1_size, t2_size = teams[0], teams[1]
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, t1_size + 1) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(t1_size + 1, t1_size + t2_size + 1) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"
    elif fmt == "tag3":
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, 4) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(4, 7) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"
    elif fmt == "tag4":
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, 5) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(5, 9) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"
    elif fmt == "wargames":
        ts = teams[0] if teams else 3
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, ts + 1) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(ts + 1, ts * 2 + 1) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"
    elif fmt in ["multi", "variable", "rumble", "gauntlet", "referee"]:
        num = match_data.get('num_participants', info.get('min', 2))
        names = [match_data.get(f'wrestler{i}', '') for i in range(1, num + 1) if match_data.get(f'wrestler{i}')]
        return " vs ".join(names) if len(names) <= 4 else f"{names[0]} vs {names[1]} + {len(names) - 2} others"
    names = [match_data.get(f'wrestler{i}', '') for i in range(1, 9) if match_data.get(f'wrestler{i}')]
    return " vs ".join(names) if names else "TBD"

def get_card_total_time(card):
    total = 0
    for match in card:
        time_option = match.get('match_time', 'Standard')
        time_info = MATCH_TIME_OPTIONS.get(time_option, MATCH_TIME_OPTIONS['Standard'])
        total += time_info['minutes']
    return total


# ==================== TEMPLATE FILTERS ====================

@app.template_filter('money')
def money_filter(amount, symbol="$"):
    return format_money(int(amount), symbol)

@app.template_filter('rating')
def rating_filter(rating):
    full_stars = int(rating)
    half = (rating - full_stars) >= 0.5
    stars = "★" * full_stars
    if half:
        stars += "½"
    return f"{stars} ({rating:.2f})"


# ==================== WEEKLY PULSE HELPER ====================
def process_week_advancement(game_state):
    """Process all weekly systems via the WeeklyPulse orchestrator + World Engine."""
    ensure_full_ai_systems(game_state)

    promotion = game_state.promotion
    progression = game_state.progression
    week = getattr(promotion, 'current_week', 0)
    year = getattr(promotion, 'current_year', 1)

    # Run the Weekly Pulse (orchestrates ALL legacy systems)
    pulse_result = game_state.process_weekly_pulse(week, year)

        # Per-show wrestlers don't cost anything between shows
    # Only deduct weekly salaries if player has contract-based pay (level 31+)
    has_contracts = progression.level >= 31 if progression else False
    total_salaries = 0
    if has_contracts:
        total_salaries = sum(getattr(w, 'booking_fee', getattr(w, 'salary', 0)) for w in promotion.roster)
        promotion.budget -= total_salaries

    # Championship weekly update (no maintenance cost)
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            game_state.championship_manager.weekly_update()
        except Exception:
            pass

    # Process loan payments
    if hasattr(game_state, 'banking') and game_state.banking:
        try:
            loan_result = game_state.banking.process_weekly_payments(promotion.budget)
            promotion.budget -= loan_result.get('total_deducted', 0)
            if hasattr(game_state, 'inbox') and game_state.inbox:
                for msg in loan_result.get('messages', []):
                    try:
                        game_state.inbox.add_message(
                            sender="Banking", subject="Loan Payment",
                            body=msg,
                            year=year, month=getattr(promotion, 'current_month', 1),
                            day=getattr(promotion, 'current_day', 1),
                            message_type="financial", icon="🏦",
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    # Process calls weekly aging (expire old calls)
    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            game_state.calls.process_weekly_aging()
        except Exception:
            pass

    # Progression weekly update
    if progression:
        try:
            progression.process_weekly_update(
                active_wrestlers=len([w for w in promotion.roster if not getattr(w, 'is_injured', False)]),
                total_fans=promotion.fan_base,
                current_budget=promotion.budget,
                weekly_profit=-total_salaries,
                roster_size=len(promotion.roster),
            )
        except Exception:
            pass

    # Process active class enrollments
    try:
        enrollment_result = process_class_enrollments_weekly(game_state)
        if isinstance(pulse_result, dict):
            pulse_result['enrollments'] = enrollment_result
    except Exception as e:
        print(f"Enrollment processing error: {e}")

    # ===== World Engine weekly tick (minds → relationships → storylines → rivals → news) =====
    if WORLD_ENGINE:
        try:
            run_world_week(game_state)
        except Exception as e:
            print(f"World Engine weekly error: {e}")

    # Writers Room 2.0 — advance storylines weekly
    if WRITERS_ROOM_2:
        try:
            advance_all_storylines(game_state)
        except Exception as e:
            print(f"Writers Room 2.0 weekly error: {e}")

    return pulse_result, total_salaries


# ==================== CLASS ENROLLMENT WEEKLY PROCESSOR ====================
def process_class_enrollments_weekly(game_state) -> dict:
    """
    Tick all active training class enrollments by 1 week.

    For each active enrollment:
    - Wrestlers: deducts weekly_cost from budget (auto-cancels if can't pay)
    - Trainees: train free (school covers via tuition)
    - Advances weeks_completed
    - On final week: rolls performance, applies stat gains with ceiling cap
    - Sends inbox notification on completion
    - Trims history to last 10 inactive enrollments to prevent bloat
    """
    enrollments = getattr(game_state, 'active_enrollments', None) or []
    if not enrollments:
        return {"completed": [], "advanced": [], "cancelled": [], "total_cost": 0}

    promotion = game_state.promotion
    school = game_state.training_school

    completed = []
    advanced = []
    cancelled = []
    total_cost_this_week = 0

    for enr in enrollments:
        if not enr.get('is_active', True):
            continue

        # Wrestlers pay weekly; trainees free (school covers via tuition)
        if enr.get('student_type') == 'wrestler':
            cost = enr.get('weekly_cost', 0)
            if promotion.budget >= cost:
                promotion.budget -= cost
                total_cost_this_week += cost
                if school and hasattr(school, 'record_class_savings'):
                    try:
                        school.record_class_savings(enr.get('base_weekly_cost', cost))
                    except Exception:
                        pass
            else:
                enr['is_active'] = False
                enr['cancelled_reason'] = 'insufficient_funds'
                cancelled.append({
                    "name": enr.get('student_name', 'Unknown'),
                    "class": enr.get('class_name', 'Class'),
                    "reason": "insufficient_funds",
                })
                if hasattr(game_state, 'inbox') and game_state.inbox:
                    try:
                        game_state.inbox.add_message(
                            sender="Training School",
                            subject=f"Class cancelled — {enr.get('student_name')}",
                            body=(f"{enr.get('student_name')} was pulled from "
                                  f"{enr.get('class_name')} — insufficient funds to "
                                  f"cover the weekly cost of ${cost:,}."),
                            year=getattr(promotion, 'current_year', 1),
                            month=getattr(promotion, 'current_month', 1),
                            day=getattr(promotion, 'current_day', 1),
                            message_type="financial", icon="⚠️",
                        )
                    except Exception:
                        pass
                continue

        enr['weeks_completed'] = enr.get('weeks_completed', 0) + 1

        if enr['weeks_completed'] >= enr.get('duration_weeks', 4):
            enr['is_active'] = False
            enr['completed'] = True

            training_class = get_class(enr.get('class_id', ''))
            if not training_class:
                continue

            student = None
            if enr.get('student_type') == 'wrestler':
                student = next(
                    (w for w in promotion.roster if w.name == enr.get('student_id')),
                    None,
                )
            elif school:
                student = school.get_trainee(enr.get('student_id'))

            if not student:
                continue

            student_data = {}
            for stat in ["strength", "speed", "technique", "charisma",
                         "stamina", "toughness", "mic_skills",
                         "psychology", "work_ethic"]:
                student_data[stat] = getattr(student, stat, 50)
            student_data["age"] = getattr(student, 'age', 30)

            try:
                performance = roll_performance(student_data, training_class)
                raw_gains = calculate_stat_gains(training_class, performance)
                actual_gains = apply_stat_gains_with_ceiling(student_data, raw_gains)

                for stat, gain in actual_gains.items():
                    if hasattr(student, stat) and gain > 0:
                        current = getattr(student, stat)
                        setattr(student, stat,
                                min(STAT_CEILING_FROM_TRAINING, current + gain))

                if enr.get('student_type') == 'trainee' and hasattr(student, 'add_xp'):
                    try:
                        student.add_xp(40, source="class_completion")
                    except Exception:
                        pass

                completed.append({
                    "name": enr.get('student_name', 'Unknown'),
                    "class": enr.get('class_name', 'Class'),
                    "performance": performance.value,
                    "gains": actual_gains,
                })

                if hasattr(game_state, 'inbox') and game_state.inbox:
                    try:
                        gain_text = ", ".join(
                            f"+{v} {k}" for k, v in actual_gains.items() if v > 0
                        ) or "no stat gains"
                        game_state.inbox.add_message(
                            sender="Training School",
                            subject=f"{enr.get('student_name')} completed {enr.get('class_name')}",
                            body=(f"Performance: {performance.value}\n"
                                  f"Gains: {gain_text}"),
                            year=getattr(promotion, 'current_year', 1),
                            month=getattr(promotion, 'current_month', 1),
                            day=getattr(promotion, 'current_day', 1),
                            message_type="general", icon="🎓",
                        )
                    except Exception:
                        pass
            except Exception as e:
                print(f"Class completion error for {enr.get('student_name')}: {e}")
        else:
            advanced.append({
                "name": enr.get('student_name', 'Unknown'),
                "class": enr.get('class_name', 'Class'),
                "weeks_completed": enr['weeks_completed'],
                "duration_weeks": enr.get('duration_weeks', 4),
            })

    active = [e for e in enrollments if e.get('is_active', True)]
    inactive = [e for e in enrollments if not e.get('is_active', True)]
    game_state.active_enrollments = active + inactive[-10:]

    return {
        "completed": completed,
        "advanced": advanced,
        "cancelled": cancelled,
        "total_cost": total_cost_this_week,
    }

# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        if username in DEMO_USERS and DEMO_USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))


# ==================== INDEX / NEW GAME / LOAD GAME ====================

@app.route('/')
@require_login
def index():
    try:
        saves = SaveManager().list_saves()
    except Exception:
        saves = []
    return render_template('index.html', saves=saves)


@app.route('/new-game', methods=['GET', 'POST'])
@require_login
def new_game():
    if request.method == 'POST':
        promoter_name = request.form.get('promoter_name', 'Player')
        promotion_name = request.form.get('promotion_name', 'My Wrestling')
        promotion_initials = request.form.get('promotion_initials', '').strip().upper()
        continent = request.form.get('continent', 'North America')
        country = request.form.get('country', 'United States')
        city = request.form.get('city', 'New York City')
        philosophy_value = request.form.get('philosophy', 'Strong Style')
        creative_control = request.form.get('creative_control') == 'on'
        cc_difficulty = request.form.get('cc_difficulty', 'Normal')

        ai_personality_map = {
            "Easy": "The Traditionalist",
            "Normal": "The Mastermind",
            "Hard": "The Showman",
        }
        ai_personality = ai_personality_map.get(cc_difficulty, "The Traditionalist")

        game_state = GameState()
        game_state.promoter_name = promoter_name

        phil_enum = Philosophy.STRONG_STYLE
        for p in Philosophy:
            if p.value == philosophy_value:
                phil_enum = p
                break

        profile = get_philosophy_profile(phil_enum)
        currency_code, currency_symbol = get_currency(country)

        # Initialize new game with all systems
        try:
            game_state.initialize_new_game(
                promotion_name=promotion_name,
                location=f"{city}, {country}",
                philosophy=phil_enum.value,
                owner_name=promoter_name,
                creative_control_enabled=creative_control,
                creative_control_difficulty=cc_difficulty,
                ai_personality=ai_personality,
            )

            # Apply initials after game state is initialized
            if game_state.promotion and promotion_initials:
                game_state.promotion.set_initials(promotion_initials)

        except Exception as e:
            print(f"Game init error (using fallback): {e}")
            traceback.print_exc()
            promotion = Promotion(
                name=promotion_name, philosophy=phil_enum,
                owner_name=promoter_name, starting_budget=0,
                location=f"{city}, {country}",
                initials=promotion_initials,
            )
            promotion.fan_base = 0
            promotion.budget = 0
            promotion.prestige = profile.prestige_start
            promotion.merchandise_modifier = profile.merchandise_modifier
            game_state.promotion = promotion
            game_state.progression = ProgressionSystem()
            game_state.ai_director = AIDirector(
                creative_control_enabled=creative_control,
                creative_control_difficulty=cc_difficulty,
            )
            game_state.championship_manager = ChampionshipManager()
            try:
                game_state.championship_manager.setup_default_accolades()
            except Exception:
                pass
            game_state.calendar = CalendarSystem()
            game_state.inbox = InboxManager()
            game_state.calls = CallsManager()
            game_state.injury_manager = InjuryManager()
            game_state.banking = BankingManager()
            game_state.training_school = TrainingSchool()
            game_state.coach_manager = CoachManager()
            game_state.coach_pool = CoachPool()
            game_state.trainee_pool = TraineePool()
            game_state.trainee_show_manager = TraineeShowManager()
            try:
                agents = generate_free_agents(count=50, level=1)
                game_state.free_agents = agents
            except Exception:
                game_state.free_agents = []

        # Apply philosophy bonuses
        try:
            game_state.promotion.prestige = profile.prestige_start
            game_state.promotion.merchandise_modifier = profile.merchandise_modifier
        except Exception:
            pass

        # Game settings
        game_state.game_settings = {
            "continent": continent, "country": country, "city": city,
            "currency_code": currency_code, "currency_symbol": currency_symbol,
            "creative_control_enabled": creative_control,
            "creative_control_difficulty": cc_difficulty,
            "show_day": "Saturday",
        }

        # Origin story
        game_state.origin_story = {
            "sender": profile.origin_sender,
            "subject": profile.origin_subject,
            "message": profile.origin_message,
            "grant": profile.starting_grant,
            "delivered": False,
            "accepted": False,
        }

        # Send origin message to inbox
        if game_state.inbox:
            try:
                game_state.inbox.add_message(
                    sender=profile.origin_sender,
                    subject=profile.origin_subject,
                    body=profile.origin_message,
                    year=1, month=1, day=1,
                    message_type="general", icon="💰",
                )
            except Exception:
                pass

        # Tutorial flags
        game_state.show_tutorial_prompt = True
        game_state.tutorial_active = False
        game_state.tutorial_step = 0
        game_state.first_launch = True

        ensure_full_ai_systems(game_state)

        # Create session
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        game_sessions[session_id] = game_state

        flash(f'{promotion_name} has been created!', 'success')
        return redirect(url_for('dashboard'))

    continents = get_continents()
    philosophies = [
        {
            "value": p.value,
            "name": get_philosophy_profile(p).name,
            "description": get_philosophy_profile(p).description,
            "prestige": get_philosophy_profile(p).prestige_start,
            "match_bonus": get_philosophy_profile(p).match_rating_bonus,
            "fan_growth": get_philosophy_profile(p).fan_growth_modifier,
            "merch": get_philosophy_profile(p).merchandise_modifier,
        }
        for p in Philosophy
    ]
    return render_template('setup.html', continents=continents, philosophies=philosophies)


@app.route('/load-game/<path:save_name>')
@require_login
def load_game(save_name):
    filepath = f"saves/{save_name}.json"
    if not os.path.exists(filepath):
        flash(f'Save file not found: {filepath}', 'error')
        if os.path.exists('saves'):
            files = os.listdir('saves')
            flash(f'Files in saves/: {files}', 'info')
        return redirect(url_for('index'))

    try:
        game_state = GameState.load_from_file(filepath)
        if game_state:
            # Ensure all systems exist after load
            if hasattr(game_state, 'ensure_all_systems'):
                try:
                    game_state.ensure_all_systems()
                except Exception:
                    pass

            ensure_full_ai_systems(game_state)

            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            game_sessions[session_id] = game_state
            promo_name = game_state.promotion.name if game_state.promotion else "Unknown"
            flash(f'Loaded: {promo_name}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Failed to load: {filepath}', 'error')
    except Exception as e:
        flash(f'Load error: {str(e)}', 'error')
        print(f"FULL TRACEBACK:\n{traceback.format_exc()}")
    return redirect(url_for('index'))


# ==================== DASHBOARD ====================
@app.route('/dashboard')
@require_login
@require_game
def dashboard():
    game_state = get_game_state()
    ensure_full_ai_systems(game_state)
    promotion = game_state.promotion
    progression = game_state.progression

    # Origin message check
    origin_message = None
    if hasattr(game_state, 'origin_story') and game_state.origin_story:
        if not game_state.origin_story.get('accepted', False):
            origin_message = game_state.origin_story

    # Tutorial flags
    show_tutorial_prompt = False
    if hasattr(game_state, 'show_tutorial_prompt') and game_state.show_tutorial_prompt:
        if not origin_message:
            show_tutorial_prompt = True
    tutorial_active = getattr(game_state, 'tutorial_active', False)
    tutorial_step = getattr(game_state, 'tutorial_step', 0)

    # Progression
    if progression:
        level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
        tier = get_promotion_tier(level)
        limits = get_cumulative_limits(level)
        tier_name = get_tier_name(tier)
    else:
        level, percentage, tier_name = 1, 0, "Backyard"
        limits = get_cumulative_limits(1)

    # AI Events
    events = []
    critical_events = []
    if game_state.ai_director:
        try:
            events = game_state.ai_director.get_active_events()
            critical_events = [e for e in events if hasattr(e, 'severity') and e.severity in [EventSeverity.CRITICAL, EventSeverity.MAJOR]]
        except Exception:
            pass

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    # Championship count
    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            champ_count = len(game_state.championship_manager.get_active_championships())
        except Exception:
            pass

    # Booked show
    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    booked_show = game_state.booked_show if has_booked_show else None

    # Calendar widget
    current_month = promotion.current_month
    current_day = promotion.current_day
    current_year = promotion.current_year
    num_days = days_in_month(current_month)
    current_dow = get_day_of_week(current_year, current_month, current_day)
    start_day = current_day - current_dow

    calendar_widget_days = []
    cal_system = getattr(game_state, 'calendar', getattr(game_state, 'calendar_system', None))
    for i in range(14):
        d = start_day + i
        m = current_month
        y = current_year
        if d < 1:
            m -= 1
            if m < 1:
                m = 12
                y -= 1
            d = days_in_month(m) + d
        elif d > num_days:
            d -= num_days
            m += 1
            if m > 12:
                m = 1
                y += 1
        is_today = (d == current_day and m == current_month and y == current_year)
        is_booked = False
        if booked_show:
            sd = booked_show.get('show_date', {})
            is_booked = sd.get('year') == y and sd.get('month') == m and sd.get('day') == d
        has_show = False
        if cal_system and hasattr(cal_system, 'events'):
            has_show = any(
                ev.year == y and ev.month == m and ev.day == d
                for ev in cal_system.events
            )
        is_past = (y < current_year) or (y == current_year and m < current_month) or (y == current_year and m == current_month and d < current_day)
        day_events = get_active_seasonal_events(m, d)
        calendar_widget_days.append({
            'day': d, 'month': m, 'year': y,
            'is_today': is_today, 'is_booked': is_booked,
            'has_show': has_show, 'is_past': is_past,
            'is_event': len(day_events) > 0,
            'event_name': day_events[0]['name'] if day_events else '',
            'event_color': day_events[0]['color'] if day_events else '',
        })

    month_names = [m_item.get('name', f'Month {i}') if isinstance(m_item, dict) else str(m_item) for i, m_item in enumerate(MONTHS, 1)]
    current_month_name = month_names[current_month - 1] if current_month <= len(month_names) else f"Month {current_month}"
    seasonal_events = get_active_seasonal_events(current_month, current_day)

    # Unread inbox count
    unread_count = 0
    if hasattr(game_state, 'inbox') and game_state.inbox:
        try:
            unread_count = game_state.inbox.get_unread_count()
        except Exception:
            pass

    # Incoming calls count
    incoming_calls = 0
    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            incoming_calls = game_state.calls.get_incoming_count()
        except Exception:
            pass

    # Has training school
    has_training_school = False
    try:
        has_training_school = game_state.has_training_school()
    except Exception:
        pass

    return render_template('dashboard.html',
        promotion=promotion, progression=progression,
        level=level, xp_percentage=percentage,
        tier_name=tier_name, limits=limits,
        events=events, critical_events=critical_events,
        currency=currency,
        roster_count=len(promotion.roster),
        injured_count=len([w for w in promotion.roster if getattr(w, 'is_injured', False)]),
        champ_count=champ_count,
        has_booked_show=has_booked_show, booked_show=booked_show,
        origin_message=origin_message,
        show_tutorial_prompt=show_tutorial_prompt,
        tutorial_active=tutorial_active, tutorial_step=tutorial_step,
        calendar_widget_days=calendar_widget_days,
        current_month_name=current_month_name,
        seasonal_events=seasonal_events,
        ai_events_count=len(events),
        unread_count=unread_count,
        incoming_calls=incoming_calls,
        has_training_school=has_training_school,
        hide_base_hud=True,
    )


# ==================== ORIGIN STORY & TUTORIAL ====================
@app.route('/accept-origin-grant', methods=['POST'])
@require_login
@require_game
def accept_origin_grant():
    game_state = get_game_state()
    ensure_full_ai_systems(game_state)
    if hasattr(game_state, 'origin_story') and game_state.origin_story:
        if not game_state.origin_story.get('accepted', False):
            grant = game_state.origin_story['grant']
            game_state.promotion.budget += grant
            game_state.origin_story['accepted'] = True
            game_state.origin_story['delivered'] = True
            game_state.origin_grant_accepted = True
            game_state.origin_grant_amount = grant
            save_game_state(game_state)
            flash(f'💰 ${grant:,} received!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/start-tutorial', methods=['POST'])
@require_login
@require_game
def start_tutorial():
    game_state = get_game_state()
    game_state.show_tutorial_prompt = False
    game_state.tutorial_active = True
    game_state.tutorial_step = 1
    save_game_state(game_state)
    flash('📖 Tutorial started!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/skip-tutorial', methods=['POST'])
@require_login
@require_game
def skip_tutorial():
    game_state = get_game_state()
    game_state.show_tutorial_prompt = False
    game_state.tutorial_active = False
    game_state.tutorial_step = 0
    game_state.tutorial_skipped = True
    save_game_state(game_state)
    flash('Tutorial skipped.', 'info')
    return redirect(url_for('dashboard'))


@app.route('/tutorial-next', methods=['POST'])
@require_login
@require_game
def tutorial_next():
    game_state = get_game_state()
    if getattr(game_state, 'tutorial_active', False):
        game_state.tutorial_step = getattr(game_state, 'tutorial_step', 0) + 1
        if game_state.tutorial_step > 6:
            game_state.tutorial_active = False
            game_state.tutorial_step = 0
            flash('🎉 Tutorial complete!', 'success')
        save_game_state(game_state)
    return redirect(url_for('dashboard'))


@app.route('/tutorial')
@require_login
def tutorial():
    return render_template('tutorial.html')


# ==================== APP HUBS ====================
@app.route('/booking-room')
@require_login
@require_game
def booking_room():
    game_state = get_game_state()
    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    return render_template('booking_room.html',
        promotion=game_state.promotion,
        has_booked_show=has_booked_show,
        booked_show=game_state.booked_show if has_booked_show else None,
        hide_base_hud=True,
    )


@app.route('/locker-room')
@require_login
@require_game
def locker_room():
    game_state = get_game_state()
    limits = get_cumulative_limits(game_state.progression.level if game_state.progression else 1)
    return render_template('locker_room.html',
        promotion=game_state.promotion,
        roster_count=len(game_state.promotion.roster),
        roster_limit=limits.get("roster_limit", 5),
        injured_count=len([w for w in game_state.promotion.roster if getattr(w, 'is_injured', False)]),
        hide_base_hud=True,
    )


@app.route('/championship-hub')
@require_login
@require_game
def championship_hub():
    game_state = get_game_state()
    limits = get_cumulative_limits(game_state.progression.level if game_state.progression else 1)
    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            champ_count = len(game_state.championship_manager.get_active_championships())
        except Exception:
            pass
    return render_template('championship_hub.html',
        promotion=game_state.promotion,
        champ_count=champ_count,
        max_champs=limits.get("max_championships", 0),
        hide_base_hud=True,
    )


@app.route('/change-venue')
@require_login
@require_game
def change_venue():
    session['current_venue_id'] = None
    session['current_card'] = []
    session['show_production'] = {}
    return redirect(url_for('book_show'))


# ==================== CALENDAR ====================
@app.route('/calendar')
@require_login
@require_game
def calendar_view():
    game_state = get_game_state()
    promotion = game_state.promotion
    cal_system = getattr(game_state, 'calendar', getattr(game_state, 'calendar_system', None))
    if not cal_system:
        cal_system = CalendarSystem()
        game_state.calendar = cal_system
        save_game_state(game_state)

    current_year = promotion.current_year
    current_month = promotion.current_month
    current_day = promotion.current_day

    view_year = int(request.args.get('year', current_year))
    view_month = int(request.args.get('month', current_month))
    if view_month < 1:
        view_month = 12
        view_year -= 1
    elif view_month > 12:
        view_month = 1
        view_year += 1

    num_days = days_in_month(view_month)
    total_days_before = sum(days_in_month(mi) for y in range(1, view_year) for mi in range(1, 13)) + sum(days_in_month(mi) for mi in range(1, view_month))
    first_weekday = total_days_before % 7

    day_shows = {}
    if hasattr(cal_system, 'events'):
        for event in cal_system.events:
            if event.year == view_year and event.month == view_month:
                d = event.day
                if d not in day_shows:
                    day_shows[d] = []
                day_shows[d].append({
                    'venue': event.venue,
                    'rating': event.rating,
                    'attendance': event.attendance,
                    'is_sellout': getattr(event, 'is_sellout', False),
                    'profit': getattr(event, 'profit', 0),
                })

    calendar_weeks = []
    week = [0] * 7
    day_num = 1
    for i in range(first_weekday, 7):
        if day_num <= num_days:
            week[i] = day_num
            day_num += 1
    calendar_weeks.append(week)
    while day_num <= num_days:
        week = [0] * 7
        for i in range(7):
            if day_num <= num_days:
                week[i] = day_num
                day_num += 1
        calendar_weeks.append(week)

    year_stats = cal_system.get_year_stats(view_year) if hasattr(cal_system, 'get_year_stats') else {}
    prev_month, prev_year = (view_month - 1, view_year) if view_month > 1 else (12, view_year - 1)
    next_month, next_year = (view_month + 1, view_year) if view_month < 12 else (1, view_year + 1)

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    month_names = [m.get('name', f'Month {i}') if isinstance(m, dict) else str(m) for i, m in enumerate(MONTHS, 1)]
    view_month_name = month_names[view_month - 1] if view_month <= len(month_names) else f"Month {view_month}"
    current_month_name = month_names[current_month - 1] if current_month <= len(month_names) else f"Month {current_month}"

    booked_show_date = None
    if hasattr(game_state, 'booked_show') and game_state.booked_show:
        booked_show_date = game_state.booked_show.get('show_date', None)

    return render_template('calendar.html',
        promotion=promotion,
        current_year=current_year, current_month=current_month, current_day=current_day,
        view_year=view_year, view_month=view_month,
        view_month_name=view_month_name, current_month_name=current_month_name,
        calendar_weeks=calendar_weeks, day_shows=day_shows, num_days=num_days,
        year_stats=year_stats, months=MONTHS, month_names=month_names,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        currency=currency, booked_show_date=booked_show_date,
    )


@app.route('/book-for-date/<int:year>/<int:month>/<int:day>')
@require_login
@require_game
def book_for_date(year, month, day):
    game_state = get_game_state()
    promotion = game_state.promotion
    if month < 1 or month > 12:
        flash('Invalid month!', 'error')
        return redirect(url_for('calendar_view'))
    if day < 1 or day > days_in_month(month):
        flash('Invalid day!', 'error')
        return redirect(url_for('calendar_view'))
    if year < promotion.current_year or (year == promotion.current_year and date_to_day_of_year(month, day) < date_to_day_of_year(promotion.current_month, promotion.current_day)):
        flash('Cannot book in the past!', 'error')
        return redirect(url_for('calendar_view'))
    session['show_date'] = {'year': year, 'month': month, 'day': day}
    flash(f'Booking show for {format_date(year, month, day)}', 'success')
    return redirect(url_for('book_show'))


# ==================== ROSTER ====================
@app.route('/roster')
@require_login
@require_game
def roster():
    game_state = get_game_state()
    limits = get_cumulative_limits(game_state.progression.level if game_state.progression else 1)
    sorted_roster = sorted(game_state.promotion.roster, key=lambda w: getattr(w, 'popularity', 0), reverse=True)
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    total_fees = sum(getattr(w, 'booking_fee', getattr(w, 'salary', 0)) for w in game_state.promotion.roster)
    return render_template('roster.html',
        wrestlers=sorted_roster,
        roster_limit=limits.get("roster_limit", 5),
        currency=currency,
        total_salary=total_fees,
    )


@app.route('/wrestler/<path:wrestler_name>')
@require_login
@require_game
def wrestler_detail(wrestler_name):
    game_state = get_game_state()
    wrestler = next((w for w in game_state.promotion.roster if w.name == wrestler_name), None)
    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('roster'))
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    # Pass promotion so dock works in template
    return render_template('wrestler_detail.html',
        wrestler=wrestler,
        currency=currency,
        promotion=game_state.promotion,
    )


@app.route('/release-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def release_wrestler(wrestler_name):
    """
    Release a wrestler from the roster.
    Buyout = booking_fee * remaining contract weeks * 0.5
    They become a free agent (Indy God if eligible).
    """
    game_state = get_game_state()
    wrestler = next((w for w in game_state.promotion.roster if w.name == wrestler_name), None)
    if wrestler:
        booking_fee = getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0))
        contract_length = getattr(wrestler, 'contract_length', 0)
        buyout = int(booking_fee * contract_length * 0.5)
        game_state.promotion.budget -= buyout
        game_state.promotion.roster.remove(wrestler)

        # Mark as Indy God and add to free agency
        if hasattr(game_state, 'free_agency') and game_state.free_agency:
            try:
                week = getattr(game_state.promotion, 'current_week', 0)
                year = getattr(game_state.promotion, 'current_year', 1)
                wrestler.is_signed = False
                wrestler.contract_length = 0
                if hasattr(wrestler, 'become_indy_god'):
                    wrestler.become_indy_god()
                game_state.free_agency.add_released_wrestler(wrestler, week, year)
            except Exception:
                game_state.free_agents.append(wrestler)
        else:
            wrestler.is_signed = False
            wrestler.contract_length = 0
            game_state.free_agents.append(wrestler)

        # Vacate any titles
        if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
            try:
                for champ in game_state.championship_manager.championships:
                    if champ.current_champion == wrestler.name:
                        champ.vacate(f"{wrestler.name} released")
            except Exception:
                pass

        save_game_state(game_state)
        flash(f'{wrestler.name} released. Buyout: ${buyout:,}', 'info')
    return redirect(url_for('roster'))


# ==================== TAG TEAMS / FACTIONS (Phase 1) ====================

@app.route('/groups')
@require_login
@require_game
def groups():
    """
    Tag Teams & Factions hub.
    Lists all active groups grouped by type + collapsible disbanded archive.
    """
    game_state = get_game_state()
    promotion = game_state.promotion

    # Ensure group manager exists (for old saves)
    if not game_state.group_manager:
        from classes.group import GroupManager
        game_state.group_manager = GroupManager()
        save_game_state(game_state)

    gm = game_state.group_manager

    # Active groups by type
    tag_teams = gm.get_tag_teams()
    trios = gm.get_trios()
    factions = gm.get_factions()

    # Disbanded groups (archive)
    disbanded = [g for g in gm.groups if not g.is_active]
    # Sort archive by most recently disbanded first
    disbanded.sort(key=lambda g: (g.disbanded_year, g.disbanded_week), reverse=True)

    # Counts for summary bar
    counts = gm.get_count_by_type()

    # Roster lookup for member existence checks
    roster_names = {w.name for w in promotion.roster} if promotion else set()

    return render_template('groups.html',
        promotion=promotion,
        tag_teams=tag_teams,
        trios=trios,
        factions=factions,
        disbanded_groups=disbanded,
        counts=counts,
        total_active=counts.get("total", 0),
        total_disbanded=len(disbanded),
        roster_names=roster_names,
        roster_count=len(roster_names),
        hide_base_hud=True,
    )


@app.route('/create-group', methods=['GET', 'POST'])
@require_login
@require_game
def create_group():
    """
    Create a new tag team, trio, or faction.
    GET: redirect to a picker page
    POST: full creation handler
    """
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        from classes.group import GroupManager
        game_state.group_manager = GroupManager()

    gm = game_state.group_manager

    # ===== POST: process group creation =====
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        leader_id = request.form.get('leader_id', '').strip()
        description = request.form.get('description', '').strip()
        icon = request.form.get('icon', '').strip()
        color = request.form.get('color', '').strip()

        # Collect member names — supports multi-select OR member1, member2, etc.
        member_names = request.form.getlist('members')
        if not member_names:
            # Fallback: collect numbered fields
            for i in range(1, MAX_GROUP_SIZE + 1):
                m = request.form.get(f'member{i}', '').strip()
                if m:
                    member_names.append(m)

        # De-dupe and clean
        member_names = [m.strip() for m in member_names if m.strip()]
        seen = set()
        deduped = []
        for m in member_names:
            if m not in seen:
                seen.add(m)
                deduped.append(m)
        member_names = deduped

        # Validate members exist on roster
        roster_names = {w.name for w in promotion.roster}
        invalid = [m for m in member_names if m not in roster_names]
        if invalid:
            flash(f'Not on your roster: {", ".join(invalid)}', 'error')
            return redirect(url_for('groups'))

        # Create the group via the manager
        success, msg, group = gm.create_group(
            name=name,
            member_names=member_names,
            leader_id=leader_id,
            formed_year=getattr(promotion, 'current_year', 1),
            formed_week=getattr(promotion, 'current_week', 0),
            description=description,
            icon=icon,
            color=color,
        )

        if success:
            save_game_state(game_state)
            flash(msg, 'success')

            # Inbox notification
            if hasattr(game_state, 'inbox') and game_state.inbox and group:
                try:
                    type_label = group.get_type_label()
                    members_text = ", ".join(group.get_members_ordered())
                    leader_text = ""
                    if group.is_faction() and group.leader_id:
                        leader_text = f"\n\n👑 Leader: {group.leader_id}"
                    game_state.inbox.add_message(
                        sender="Booking Office",
                        subject=f"New {type_label}: {group.name}",
                        body=(f"{group.name} has been formed as a {type_label}.\n\n"
                              f"Members: {members_text}{leader_text}"),
                        year=getattr(promotion, 'current_year', 1),
                        month=getattr(promotion, 'current_month', 1),
                        day=getattr(promotion, 'current_day', 1),
                        message_type="general",
                        icon=group.get_type_icon(),
                    )
                except Exception:
                    pass
        else:
            flash(f'Could not create group: {msg}', 'error')

        return redirect(url_for('groups'))

    # ===== GET: render picker page =====
    roster_names_set = {w.name for w in promotion.roster} if promotion else set()

    # Build available wrestlers list with overlap warnings
    available_wrestlers = []
    for w in (promotion.roster if promotion else []):
        # Check existing group memberships
        in_tag_team = False
        tag_team_name = ""
        in_faction = False
        faction_name = ""
        try:
            tag = gm.get_tag_or_trio_for_wrestler(w.name)
            if tag:
                in_tag_team = True
                tag_team_name = tag.name
            fac = gm.get_faction_for_wrestler(w.name)
            if fac:
                in_faction = True
                faction_name = fac.name
        except Exception:
            pass

        available_wrestlers.append({
            "name": w.name,
            "gender": getattr(w.gender, 'value', '') if hasattr(w, 'gender') else '',
            "popularity": getattr(w, 'popularity', 0),
            "in_tag_team": in_tag_team,
            "tag_team_name": tag_team_name,
            "in_faction": in_faction,
            "faction_name": faction_name,
        })

    # Sort by popularity (best stars first)
    available_wrestlers.sort(key=lambda x: -x.get('popularity', 0))

    return render_template('create_group.html',
        promotion=promotion,
        available_wrestlers=available_wrestlers,
        hide_base_hud=True,
    )


@app.route('/edit-group/<path:group_id>', methods=['GET', 'POST'])
@require_login
@require_game
def edit_group(group_id):
    """
    Edit an existing group.
    GET: shows the editor
    POST: handles rename + member add/remove actions
    """
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        flash('Group system not initialized!', 'error')
        return redirect(url_for('groups'))

    gm = game_state.group_manager
    group = gm.get_group(group_id)

    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups'))

    if not group.is_active:
        flash('Cannot edit a disbanded group. Reform it first.', 'warning')
        return redirect(url_for('groups'))

    # ===== POST: handle edit actions =====
    if request.method == 'POST':
        action = request.form.get('action', '').strip()

        if action == 'rename':
            new_name = request.form.get('new_name', '').strip()
            success, msg = gm.rename_group(group_id, new_name)
            flash(msg, 'success' if success else 'error')

        elif action == 'add_member':
            wrestler_name = request.form.get('wrestler_name', '').strip()
            roster_names = {w.name for w in promotion.roster}
            if wrestler_name not in roster_names:
                flash(f'{wrestler_name} is not on your roster.', 'error')
            else:
                success, msg = gm.add_member_to_group(group_id, wrestler_name)
                flash(msg, 'success' if success else 'error')

        elif action == 'remove_member':
            wrestler_name = request.form.get('wrestler_name', '').strip()
            success, msg = gm.remove_member_from_group(group_id, wrestler_name)
            flash(msg, 'success' if success else 'error')

        else:
            flash(f'Unknown action: {action}', 'error')

        save_game_state(game_state)
        # If the group auto-disbanded, send back to hub
        if not group.is_active:
            return redirect(url_for('groups'))
        return redirect(url_for('edit_group', group_id=group_id))

    # ===== GET: render editor =====
    roster_names = {w.name for w in promotion.roster} if promotion else set()

    # Build list of wrestlers available to ADD (not already in this group, respect overlap rules)
    available_to_add = []
    proposed_size = len(group.members) + 1
    is_proposed_faction = proposed_size >= 4

    for w in (promotion.roster if promotion else []):
        if w.name in group.members:
            continue
        # Check if they're in another incompatible group
        in_other = False
        other_group_name = ""
        try:
            other_groups = gm.get_groups_for_wrestler(w.name)
            for og in other_groups:
                if og.is_faction() and is_proposed_faction:
                    in_other = True
                    other_group_name = og.name
                    break
                if not og.is_faction() and not is_proposed_faction:
                    in_other = True
                    other_group_name = og.name
                    break
        except Exception:
            pass

        # Skip wrestlers in incompatible groups (can't add them anyway)
        if in_other:
            continue

        available_to_add.append({
            "name": w.name,
            "gender": getattr(w.gender, 'value', '') if hasattr(w, 'gender') else '',
            "in_other": False,
            "other_group_name": "",
        })

    available_to_add.sort(key=lambda x: x['name'])

    return render_template('edit_group.html',
        promotion=promotion,
        group=group,
        available_to_add=available_to_add,
        roster_names=roster_names,
        MAX_GROUP_SIZE=MAX_GROUP_SIZE,
        hide_base_hud=True,
    )


@app.route('/disband-group/<path:group_id>', methods=['POST'])
@require_login
@require_game
def disband_group(group_id):
    """
    Disband a group. Archives it (doesn't delete) so it can be reformed later.
    """
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        flash('Group system not initialized!', 'error')
        return redirect(url_for('groups'))

    gm = game_state.group_manager
    group = gm.get_group(group_id)

    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups'))

    reason = request.form.get('reason', 'Disbanded by management').strip()
    if not reason:
        reason = "Disbanded by management"

    group_name = group.name
    type_label = group.get_type_label()

    success, msg = gm.disband_group(
        group_id=group_id,
        reason=reason,
        year=getattr(promotion, 'current_year', 1),
        week=getattr(promotion, 'current_week', 0),
    )

    if success:
        save_game_state(game_state)
        flash(f'{group_name} has disbanded. Archived for future storylines.', 'info')

        # Inbox notification
        if hasattr(game_state, 'inbox') and game_state.inbox:
            try:
                game_state.inbox.add_message(
                    sender="Booking Office",
                    subject=f"{type_label} disbanded: {group_name}",
                    body=(f"The {type_label.lower()} '{group_name}' has been disbanded.\n\n"
                          f"Reason: {reason}\n\n"
                          f"You can reform this group at any time from the Tag Teams "
                          f"& Factions archive."),
                    year=getattr(promotion, 'current_year', 1),
                    month=getattr(promotion, 'current_month', 1),
                    day=getattr(promotion, 'current_day', 1),
                    message_type="general",
                    icon="💔",
                )
            except Exception:
                pass
    else:
        flash(f'Could not disband: {msg}', 'error')

    return redirect(url_for('groups'))


@app.route('/reform-group/<path:group_id>', methods=['POST'])
@require_login
@require_game
def reform_group(group_id):
    """
    Reform a previously disbanded group.
    Validates that all original members are still on the roster.
    Also re-checks overlap rules (in case members joined other groups since).
    """
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        flash('Group system not initialized!', 'error')
        return redirect(url_for('groups'))

    gm = game_state.group_manager
    group = gm.get_group(group_id)

    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups'))

    if group.is_active:
        flash(f'{group.name} is already active.', 'warning')
        return redirect(url_for('groups'))

    # Check all members are still on the roster
    roster_names = {w.name for w in promotion.roster}
    missing = [m for m in group.members if m not in roster_names]
    if missing:
        flash(f'Cannot reform — these members are no longer on your roster: '
              f'{", ".join(missing)}. Edit the group first or create a new one.', 'error')
        return redirect(url_for('groups'))

    # Re-check overlap rules — temporarily set inactive to check against OTHER groups
    proposed_size = len(group.members)
    for member in group.members:
        # Get all OTHER active groups containing this wrestler
        other_groups = [
            g for g in gm.get_groups_for_wrestler(member)
            if g.id != group_id
        ]
        is_proposed_faction = proposed_size >= 4
        for og in other_groups:
            if og.is_faction() and is_proposed_faction:
                flash(f'Cannot reform — {member} is already in faction "{og.name}".', 'error')
                return redirect(url_for('groups'))
            if not og.is_faction() and not is_proposed_faction:
                flash(f'Cannot reform — {member} is already in {og.group_type.value.lower()} "{og.name}".', 'error')
                return redirect(url_for('groups'))

    # All checks passed — reactivate
    group.is_active = True
    group.disbanded_year = 0
    group.disbanded_week = 0
    group.disband_reason = ""

    save_game_state(game_state)
    flash(f'♻️ {group.name} has reformed!', 'success')

    # Inbox notification
    if hasattr(game_state, 'inbox') and game_state.inbox:
        try:
            type_label = group.get_type_label()
            members_text = ", ".join(group.get_members_ordered())
            game_state.inbox.add_message(
                sender="Booking Office",
                subject=f"♻️ {group.name} has reformed!",
                body=(f"The {type_label.lower()} '{group.name}' has reunited.\n\n"
                      f"Members: {members_text}"),
                year=getattr(promotion, 'current_year', 1),
                month=getattr(promotion, 'current_month', 1),
                day=getattr(promotion, 'current_day', 1),
                message_type="general",
                icon="♻️",
            )
        except Exception:
            pass

    return redirect(url_for('groups'))


@app.route('/set-faction-leader/<path:group_id>', methods=['POST'])
@require_login
@require_game
def set_faction_leader(group_id):
    """
    Change the leader of a faction.
    Only valid for factions (4+ members).
    """
    game_state = get_game_state()

    if not game_state.group_manager:
        flash('Group system not initialized!', 'error')
        return redirect(url_for('groups'))

    gm = game_state.group_manager
    group = gm.get_group(group_id)

    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups'))

    if not group.is_active:
        flash('Cannot modify a disbanded group.', 'error')
        return redirect(url_for('groups'))

    if not group.is_faction():
        flash('Only factions have leaders (4+ members).', 'warning')
        return redirect(url_for('groups'))

    new_leader = request.form.get('leader_id', '').strip()
    if not new_leader:
        flash('No leader specified.', 'error')
        return redirect(url_for('groups'))

    success, msg = gm.set_faction_leader(group_id, new_leader)
    flash(msg, 'success' if success else 'error')

    if success:
        save_game_state(game_state)

    return redirect(url_for('groups'))

# ==================== FREE AGENTS ====================
@app.route('/free-agents')
@require_login
@require_game
def free_agents():
    game_state = get_game_state()
    progression = game_state.progression
    promotion = game_state.promotion
    limits = get_cumulative_limits(progression.level if progression else 1)
    roster_limit = limits.get("roster_limit", 5)
    current_roster = len(promotion.roster)
    can_sign = current_roster < roster_limit
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    player_level = progression.level if progression else 1
    budget = promotion.budget

    if player_level <= 5:
        allowed_tiers = ["Rookie"]
    elif player_level <= 15:
        allowed_tiers = ["Rookie", "Prospect"]
    elif player_level <= 30:
        allowed_tiers = ["Rookie", "Prospect", "Rising"]
    elif player_level <= 50:
        allowed_tiers = ["Rookie", "Prospect", "Rising", "Proven"]
    elif player_level <= 75:
        allowed_tiers = ["Rookie", "Prospect", "Rising", "Proven", "Elite"]
    else:
        allowed_tiers = ["Rookie", "Prospect", "Rising", "Proven", "Elite", "Indy God"]

    week_key = f"{promotion.current_year}-{promotion.current_week}"
    needs_refresh = (
        not hasattr(game_state, 'weekly_agent_names')
        or not game_state.weekly_agent_names
        or getattr(game_state, 'weekly_agents_week', '') != week_key
    )

    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        fa = game_state.free_agency
        try:
            all_listings = fa.get_all_listings()
        except Exception:
            all_listings = []

        eligible_listings = []
        for listing in all_listings:
            try:
                tier_value = listing.tier.value if hasattr(listing.tier, 'value') else str(listing.tier)
                if tier_value not in allowed_tiers:
                    continue
                cost = listing.signing_bonus if listing.is_exclusive_offer else listing.asking_per_show
                if cost > budget * 2 and cost > 500:
                    continue
                eligible_listings.append(listing)
            except Exception:
                continue

        if needs_refresh:
            sample_size = min(10, len(eligible_listings))
            sampled = random.sample(eligible_listings, sample_size) if eligible_listings else []
            game_state.weekly_agent_names = [l.wrestler.name for l in sampled]
            game_state.weekly_agents_week = week_key
            save_game_state(game_state)

        weekly_names = set(getattr(game_state, 'weekly_agent_names', []))
        visible_listings = [l for l in eligible_listings if l.wrestler.name in weekly_names]
        agents_with_salary = []
        for listing in visible_listings:
            try:
                w = listing.wrestler
                agents_with_salary.append({
                    "wrestler": w,
                    "asking_salary": listing.asking_per_show,
                    "signing_bonus": listing.signing_bonus,
                    "per_show_rate": listing.asking_per_show,
                    "tier": listing.tier.value if hasattr(listing.tier, 'value') else str(listing.tier),
                    "tier_name": listing.tier_name,
                    "has_contracts": getattr(listing, 'is_exclusive_offer', False),
                    "is_hot_prospect": getattr(listing, 'is_hot_prospect', False),
                    "is_indy_god": getattr(listing, 'is_indy_god', False),
                    "is_licensed": getattr(listing, 'is_licensed', False),
                    "rival_interested": getattr(listing, 'rival_interested', False),
                    "rival_name": getattr(listing, 'rival_promotion_name', ''),
                    "status_label": listing.get_status_label() if hasattr(listing, 'get_status_label') else '',
                    "weeks_remaining": listing.get_weeks_remaining() if hasattr(listing, 'get_weeks_remaining') else 0,
                })
            except Exception:
                pass
        agents_with_salary.sort(key=lambda x: -getattr(x["wrestler"], 'popularity', 0))
        return render_template('free_agents.html',
            agents=agents_with_salary,
            can_sign=can_sign,
            roster_count=current_roster,
            roster_limit=roster_limit,
            budget=budget,
            currency=currency,
            total_agents=len(agents_with_salary),
            total_pool=len(eligible_listings),
            current_week=getattr(promotion, 'current_week', 0),
            current_year=getattr(promotion, 'current_year', 1),
            player_level=player_level,
            allowed_tiers=allowed_tiers,
        )
    else:
        agents_with_salary = []
        for w in (game_state.free_agents or [])[:10]:
            ovr = getattr(w, 'overall_rating', 50)
            pop = getattr(w, 'popularity', 30)
            per_show_rate = max(50, min(50 + int(ovr * 1.3) + int(pop * 0.5), 500))
            agents_with_salary.append({
                "wrestler": w,
                "asking_salary": per_show_rate,
                "signing_bonus": 0,
                "per_show_rate": per_show_rate,
                "tier": "Rookie", "tier_name": "Free Agent",
                "has_contracts": False,
            })
        return render_template('free_agents.html',
            agents=agents_with_salary, can_sign=can_sign,
            roster_count=current_roster, roster_limit=roster_limit,
            budget=budget, currency=currency,
            total_agents=len(agents_with_salary),
            total_pool=len(game_state.free_agents or []),
            current_week=getattr(promotion, 'current_week', 0),
            current_year=getattr(promotion, 'current_year', 1),
            player_level=player_level,
            allowed_tiers=["Rookie"],
        )


@app.route('/sign-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def sign_wrestler(wrestler_name):
    game_state = get_game_state()
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level if progression else 1)
    roster_limit = limits.get("roster_limit", 5)

    if len(game_state.promotion.roster) >= roster_limit:
        flash('Roster is full!', 'error')
        return redirect(url_for('free_agents'))

    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        fa = game_state.free_agency
        try:
            success, message, wrestler, cost_paid = fa.sign_wrestler(
                wrestler_name,
                game_state.promotion.budget,
                len(game_state.promotion.roster),
                roster_limit,
            )
            if success and wrestler:
                game_state.promotion.budget -= cost_paid
                game_state.promotion.roster.append(wrestler)
                if progression:
                    try:
                        if progression.stats.get("wrestlers_signed_total", 0) == 0:
                            progression.add_xp(100, "First Wrestler Signed!")
                            flash('🎉 First Wrestler Signed! +100 XP', 'success')
                        progression.update_stat("wrestlers_signed_total")
                    except Exception:
                        pass
                save_game_state(game_state)
                flash(message, 'success')
            else:
                flash(f'Cannot sign: {message}', 'error')
        except Exception as e:
            flash(f'Signing error: {e}', 'error')
        return redirect(url_for('free_agents'))

    wrestler = next((w for w in (game_state.free_agents or []) if w.name == wrestler_name), None)
    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('free_agents'))

    ovr = getattr(wrestler, 'overall_rating', 50)
    pop = getattr(wrestler, 'popularity', 30)
    per_show_rate = 50 + int(ovr * 1.3) + int(pop * 0.5)
    per_show_rate = max(50, min(per_show_rate, 500))

    if hasattr(wrestler, 'booking_fee'):
        wrestler.booking_fee = per_show_rate
    elif hasattr(wrestler, 'salary'):
        wrestler.salary = per_show_rate
    wrestler.contract_length = 52
    wrestler.is_signed = True
    if hasattr(wrestler, 'adjust_morale'):
        wrestler.adjust_morale(15)

    game_state.promotion.roster.append(wrestler)
    game_state.free_agents.remove(wrestler)
    save_game_state(game_state)
    flash(f'{wrestler.name} hired! Per-show rate: ${per_show_rate}/show', 'success')
    return redirect(url_for('free_agents'))


# ==================== BOOK SHOW ====================
@app.route('/book-show')
@require_login
@require_game
def book_show():
    game_state = get_game_state()
    progression = game_state.progression
    promotion = game_state.promotion
    limits = get_cumulative_limits(progression.level if progression else 1)
    max_tier = limits.get("venue_tier_max", 1)
    continent = getattr(game_state, 'game_settings', {}).get("continent", "North America")

    if limits.get("can_tour_international", False):
        all_venues = get_all_venues()
    else:
        all_venues = get_venues_by_continent(continent)

    eligible_venues = [v for v in all_venues if v.tier.value <= max_tier and v.is_unlocked]

    show_all_venues = request.args.get('show_all', '0') == '1'
    recommended_min_tier = max(1, max_tier - 1)

    if show_all_venues or max_tier <= 2:
        venues = eligible_venues
    else:
        venues = [v for v in eligible_venues if v.tier.value >= recommended_min_tier]

    venues.sort(key=lambda v: v.capacity)
    hidden_venue_count = len(eligible_venues) - len(venues)

    available = [w for w in promotion.roster if not getattr(w, 'is_injured', False)]
    match_types = get_unlocked_match_types(progression.level if progression else 1)
    current_card = session.get('current_card', [])
    current_venue_id = session.get('current_venue_id')
    show_date = session.get('show_date', None)
    if not show_date:
        show_date = {'year': promotion.current_year, 'month': promotion.current_month, 'day': promotion.current_day}
        session['show_date'] = show_date

    current_venue = None
    if current_venue_id:
        venue = get_venue_by_id(current_venue_id)
        if venue:
            current_venue = venue
        else:
            for v in venues:
                if v.id == current_venue_id:
                    current_venue = v
                    break

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    show_day_name = get_day_name(get_day_of_week(show_date['year'], show_date['month'], show_date['day']))

    championships = []
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            for champ in game_state.championship_manager.get_active_championships():
                championships.append({
                    'name': champ.name,
                    'current_champion': champ.current_champion,
                    'current_champion_tag_partner': getattr(champ, 'current_champion_tag_partner', ''),
                    'is_tag_title': getattr(champ, 'is_tag_title', False) or champ.level.value == 'Tag Team Championship',
                    'rules': champ.rules.value,
                    'gender': champ.gender.value,
                    'level': champ.level.value,
                })
        except Exception:
            pass

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None

    if current_venue:
        estimated_venue_cost = current_venue.get_rental_cost(show_day_name)
        venue_day_mod = current_venue.get_day_modifier(show_day_name)
    else:
        estimated_venue_cost = 0
        venue_day_mod = {"attendance": 1.0, "cost": 1.0, "label": ""}

    estimated_salary_cost = sum(getattr(w, 'booking_fee', getattr(w, 'salary', 0)) for w in promotion.roster)
    prod_data = session.get('show_production', {})
    current_production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    estimated_production_cost = current_production.get_total_cost()

    booked_names = set()
    for match in current_card:
        for i in range(1, 31):
            name = match.get(f'wrestler{i}', '')
            if name:
                booked_names.add(name)
    available_for_booking = [w for w in available if w.name not in booked_names]

    match_type_info = get_match_type_info()
    match_categories = get_match_categories()
    show_date_string = format_date(show_date['year'], show_date['month'], show_date['day'])
    max_matches = limits.get("match_slots_weekly", 4)
    card_full = len(current_card) >= max_matches
    card_total_time = get_card_total_time(current_card)
    venue_available_time = current_venue.get_available_minutes() if current_venue else 120
    time_remaining = venue_available_time - card_total_time
    is_overrunning = time_remaining < 0

    booking_suggestions = []
    if hasattr(game_state, 'storyline_engine') and game_state.storyline_engine:
        try:
            booking_suggestions = game_state.storyline_engine.get_booking_suggestions(max_results=3)
        except Exception:
            pass

    return render_template('book_show.html',
        venues=venues, wrestlers=available_for_booking, all_wrestlers=available,
        match_types=match_types, match_type_info=match_type_info,
        match_categories=match_categories,
        current_card=current_card, current_venue=current_venue, currency=currency,
        championships=championships,
        show_date=show_date, show_date_string=show_date_string,
        show_day_name=show_day_name, venue_day_mod=venue_day_mod,
        has_booked_show=has_booked_show, estimated_venue_cost=estimated_venue_cost,
        estimated_salary_cost=estimated_salary_cost,
        estimated_production_cost=estimated_production_cost,
        can_book=len(current_card) > 0 and current_venue is not None,
        can_run=len(current_card) > 0 and current_venue is not None,
        max_matches=max_matches, card_full=card_full,
        match_time_options=MATCH_TIME_OPTIONS,
        card_total_time=card_total_time,
        venue_available_time=venue_available_time,
        time_remaining=time_remaining,
        is_overrunning=is_overrunning,
        booking_suggestions=booking_suggestions,
        show_all_venues=show_all_venues,
        hidden_venue_count=hidden_venue_count,
        max_tier=max_tier,
    )


@app.route('/select-venue/<path:venue_id>')
@require_login
@require_game
def select_venue(venue_id):
    venue = get_venue_by_id(venue_id)
    if venue:
        session['current_venue_id'] = venue_id
        session['current_card'] = []
        session['show_production'] = {}
        flash(f'Selected: {venue.name} (Max {venue.get_available_minutes()} min)', 'success')
    return redirect(url_for('book_show'))


@app.route('/add-match', methods=['POST'])
@require_login
@require_game
def add_match():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    current_card = session.get('current_card', [])
    limits = get_cumulative_limits(progression.level if progression else 1)
    max_matches = limits.get("match_slots_weekly", 4)
    if len(current_card) >= max_matches:
        flash(f'Card is full! Maximum {max_matches} matches at your level.', 'error')
        return redirect(url_for('book_show'))

    match_type = request.form.get('match_type', 'Singles')
    title_match = request.form.get('title_match', '')
    match_time = request.form.get('match_time', 'Standard')
    match_rules = request.form.get('match_rules', 'Standard')
    info = get_match_type_info().get(match_type, {"min": 2, "max": 2, "type": "singles", "intergender": False, "no_dq": False})
    num_participants = int(request.form.get('num_participants', info.get('min', 2)))
    num_participants = max(info.get('min', 2), min(num_participants, info.get('max', 2)))
    is_intergender = info.get("intergender", False) or info.get("no_dq", False)

    wrestlers = []
    for i in range(1, num_participants + 1):
        name = request.form.get(f'wrestler{i}', '')
        if name:
            wrestlers.append(name)
    if len(wrestlers) < 2:
        flash('Need at least 2 wrestlers for a match!', 'error')
        return redirect(url_for('book_show'))
    if len(wrestlers) != len(set(wrestlers)):
        flash('Cannot have the same wrestler twice in one match!', 'error')
        return redirect(url_for('book_show'))

    booked = set()
    for match in current_card:
        for key in [f'wrestler{i}' for i in range(1, 31)]:
            n = match.get(key, '')
            if n:
                booked.add(n)
    already_booked = [w for w in wrestlers if w in booked]
    if already_booked:
        flash(f'Already booked: {", ".join(already_booked)}', 'error')
        return redirect(url_for('book_show'))

    match_data = {
        'match_type': match_type, 'match_format': info.get("type", "singles"),
        'match_time': match_time, 'match_rules': match_rules,
        'is_main_event': True, 'is_title_match': bool(title_match),
        'title_name': title_match, 'num_participants': len(wrestlers),
        'is_intergender': is_intergender,
    }
    for i, name in enumerate(wrestlers, 1):
        match_data[f'wrestler{i}'] = name
    match_data['display'] = get_display_for_match(match_data)
    current_card.append(match_data)
    for i, match in enumerate(current_card):
        match['is_main_event'] = (i == len(current_card) - 1)
    session['current_card'] = current_card

    time_info = MATCH_TIME_OPTIONS.get(match_time, MATCH_TIME_OPTIONS['Standard'])
    title_text = f" for the {title_match}" if title_match else ""
    flash(f'Added: {match_data["display"]} ({match_type}, {time_info["minutes"]}min){title_text}', 'success')
    return redirect(url_for('book_show'))


@app.route('/remove-match/<int:match_index>')
@require_login
@require_game
def remove_match(match_index):
    current_card = session.get('current_card', [])
    if 0 <= match_index < len(current_card):
        current_card.pop(match_index)
        if current_card:
            for i, match in enumerate(current_card):
                match['is_main_event'] = (i == len(current_card) - 1)
        session['current_card'] = current_card
        flash('Removed match', 'info')
    return redirect(url_for('book_show'))


@app.route('/reorder-matches', methods=['POST'])
@require_login
@require_game
def reorder_matches():
    try:
        from_index = int(request.form.get('from_index', -1))
        to_slot = int(request.form.get('to_slot', -1))
    except (ValueError, TypeError):
        flash('Invalid reorder data!', 'error')
        return redirect(url_for('book_show'))
    current_card = session.get('current_card', [])
    if from_index < 0 or from_index >= len(current_card) or to_slot < 0:
        flash('Invalid!', 'error')
        return redirect(url_for('book_show'))
    match = current_card.pop(from_index)
    if to_slot >= len(current_card):
        current_card.append(match)
    else:
        current_card.insert(to_slot, match)
    for i, m in enumerate(current_card):
        m['is_main_event'] = (i == len(current_card) - 1)
    session['current_card'] = current_card
    flash('Card reordered!', 'success')
    return redirect(url_for('book_show'))


# ==================== SHOW PRODUCTION ====================
@app.route('/show-production')
@require_login
@require_game
def show_production():
    game_state = get_game_state()
    venue_id = session.get('current_venue_id')
    if not venue_id:
        flash('Select a venue first!', 'error')
        return redirect(url_for('book_show'))
    venue = get_venue_by_id(venue_id)
    if not venue:
        for v in get_venues_by_continent(getattr(game_state, 'game_settings', {}).get("continent", "North America")):
            if v.id == venue_id:
                venue = v
                break
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('book_show'))
    venue_tier = venue.tier.value
    prod_data = session.get('show_production', {})
    current_production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    summary = current_production.get_summary()
    all_options = {}
    for cat_key in ALL_PRODUCTION_OPTIONS:
        all_options[cat_key] = get_available_options(cat_key, venue_tier)
    return render_template('show_production.html',
        venue=venue, venue_tier=venue_tier, production=current_production,
        summary=summary, all_options=all_options,
        category_labels=CATEGORY_LABELS,
        budget=game_state.promotion.budget,
    )


@app.route('/update-production', methods=['POST'])
@require_login
@require_game
def update_production():
    production = ShowProduction(
        ring_id=request.form.get('ring', 'ring_none'),
        lighting_id=request.form.get('lighting', 'lighting_none'),
        camera_id=request.form.get('cameras', 'camera_none'),
        audio_id=request.form.get('audio', 'audio_none'),
        entrance_id=request.form.get('entrance', 'entrance_curtain'),
        backstage_id=request.form.get('backstage', 'backstage_none'),
        pyro_id=request.form.get('pyro', 'pyro_none'),
        commentary_id=request.form.get('commentary', 'commentary_none'),
        medical_id=request.form.get('medical', 'medical_none'),
        barricade_id=request.form.get('barricades', 'barricade_none'),
        security_id=request.form.get('security', 'security_none'),
        weapon_id=request.form.get('weapons', 'weapon_none'),
        special_fx_id=request.form.get('special_fx', 'fx_none'),
    )
    session['show_production'] = production.to_dict()
    flash(f'Production updated! Cost: ${production.get_total_cost():,} per show', 'success')
    return redirect(url_for('show_production'))


# ==================== SHOW REPORT + AI TWEETS ====================

_FAN_HANDLES = [
    "BaddestHouse78", "ColossalShow97", "MassiveLover4Life", "HacksawHouseTube",
    "SwissManager", "RingRatRandy", "SuplexCitySue", "KayfabeKing", "FrontRowFred",
    "GorillaPosition", "TurnbuckleTina", "MainEventMike", "PopcornPete",
    "IndieDarling", "SmarkSiren", "ColdOnePat", "DropkickDana", "ApronBumpAl",
]
_VERIFIED_HANDLES = ["WrestleZoneHQ", "TheDirtSheet", "SquaredCircleNow", "ProWrestlingDaily"]
_TWEET_AVATARS = ["😀", "🔥", "😎", "🤩", "😤", "🙄", "😴", "🤬", "👀", "🍿", "💀", "🧐", "🤝", "🏆"]


def generate_show_tweets(results, avg_rating, attendance, capacity, is_sellout,
                         profit, title_changes, fans_change, max_tweets=8):
    """AI-style social reactions to the show. Returns list of plain dicts (save-safe)."""
    tweets = []
    if not results:
        return tweets

    rated = [r for r in results if r.get('rating') is not None]
    best = max(rated, key=lambda r: r.get('rating', 0)) if rated else None
    worst = min(rated, key=lambda r: r.get('rating', 0)) if rated else None

    used = set()

    def handle(verified=False):
        pool = _VERIFIED_HANDLES if verified else _FAN_HANDLES
        choices = [h for h in pool if h not in used] or pool
        h = random.choice(choices)
        used.add(h)
        return h

    def add(text, sentiment, verified=False):
        tweets.append({
            "handle": handle(verified),
            "verified": verified,
            "avatar": random.choice(_TWEET_AVATARS),
            "text": text,
            "sentiment": sentiment,
        })

    for tc in (title_changes or []):
        add(f"NEW CHAMPION! {tc.get('new_champion','')} captures the "
            f"{tc.get('title','title')}! Huge moment 🏆 #NewChamp",
            "positive", verified=True)

    if best and best.get('rating', 0) >= 3.5:
        add(f"{best.get('display','The main event')} STOLE the show. "
            f"{best.get('winner','that winner')} is on another level 🔥",
            "positive")

    if worst and worst is not best and worst.get('rating', 0) < 2.5:
        add(f"Yikes… {worst.get('display','that match')} dragged badly. "
            f"Cut the time or freshen the matchup.", "negative")

    if is_sellout:
        add("SOLD OUT and the crowd was electric all night. Atmosphere = 10/10!", "positive")
    elif capacity and attendance and attendance < capacity * 0.45:
        add("Lots of empty seats tonight. Need bigger stars or better promotion.", "negative")

    if avg_rating >= 4.0:
        add("Card of the year contender. Whatever you're booking, keep doing it 👏", "positive", verified=True)
    elif avg_rating >= 3.0:
        add("Solid, watchable show. A couple of standout moments.", "neutral")
    elif avg_rating >= 2.0:
        add("Pretty mid card overall. Felt like filler in the middle.", "neutral")
    else:
        add("Rough night. This one's getting clipped, not replayed. 😬", "negative")

    if fans_change and fans_change >= 5000:
        add(f"This promotion is BUZZING right now — picked up a ton of new fans! 📈", "positive")
    elif fans_change is not None and fans_change <= 0:
        add("Losing interest in this product lately. Give us a reason to care.", "negative")

    return tweets[:max_tweets]


def build_show_breakdown(results, avg_rating, attendance, capacity, is_sellout,
                         ticket_revenue, merch_revenue, alcohol_revenue,
                         concession_revenue, vip_revenue, venue_cost,
                         production_cost, profit, fans_change, title_changes,
                         tweets, venue_name, currency, active_storylines=None):
    """Package both screens' data into one plain dict stored on game_state."""
    rated = [r for r in results if r.get('rating') is not None]
    best = max(rated, key=lambda r: r.get('rating', 0)) if rated else None
    worst = min(rated, key=lambda r: r.get('rating', 0)) if rated else None

    gross = (ticket_revenue + merch_revenue + alcohol_revenue
             + concession_revenue + vip_revenue)
    total_costs = venue_cost + production_cost

    if avg_rating >= 4.0:
        advice = "Outstanding card. Keep these pairings together and build to a blow-off."
    elif avg_rating >= 3.0:
        advice = "Solid show. Trim your lowest-rated match and give your hottest act more time."
    elif avg_rating >= 2.0:
        advice = "Mixed reaction. Pair strong workers together and shorten the weak spots."
    else:
        advice = "Tough night. Build the card around your most popular wrestlers; avoid overlong matches."

    storyline_summaries = []
    for s in (active_storylines or []):
        storyline_summaries.append({
            "title": s.get('title', s.get('name', 'Storyline')),
            "heat": s.get('heat', 0),
            "participants": s.get('participants', s.get('wrestlers', [])),
            "weeks_active": s.get('weeks_active', 0),
        })

    return {
        "venue_name": venue_name,
        "avg_rating": round(avg_rating, 2),
        "attendance": attendance,
        "capacity": capacity,
        "is_sellout": is_sellout,
        "matches": [
            {
                "display": r.get('display', ''),
                "match_type": r.get('match_type', ''),
                "rating": round(r.get('rating', 0), 2),
                "crowd": r.get('crowd', ''),
                "is_main_event": r.get('is_main_event', False),
                "is_title_match": r.get('is_title_match', False),
                "title_name": r.get('title_name', ''),
                "title_changed": r.get('title_changed', False),
                "winner": r.get('winner', ''),
            } for r in results
        ],
        "best_match": ({"display": best.get('display', ''),
                        "rating": round(best.get('rating', 0), 2)} if best else None),
        "worst_match": ({"display": worst.get('display', ''),
                         "rating": round(worst.get('rating', 0), 2)} if worst else None),
        "revenue": {"ticket": ticket_revenue, "merch": merch_revenue,
                    "alcohol": alcohol_revenue, "concession": concession_revenue,
                    "vip": vip_revenue, "gross": gross},
        "costs": {"venue": venue_cost, "production": production_cost, "total": total_costs},
        "profit": profit,
        "fans_change": fans_change,
        "title_changes": title_changes or [],
        "tweets": tweets or [],
        "storylines": storyline_summaries,
        "currency": currency,
        "advice": advice,
    }


# ==================== SAVE & RUN SHOW ====================
@app.route('/save-show', methods=['POST'])
@require_login
@require_game
def save_show():
    game_state = get_game_state()
    current_card = session.get('current_card', [])
    venue_id = session.get('current_venue_id')
    prod_data = session.get('show_production', {})
    show_date = session.get('show_date', None)
    if not current_card or not venue_id:
        flash('No show to save! Add matches and select a venue.', 'error')
        return redirect(url_for('book_show'))
    if not show_date:
        p = game_state.promotion
        show_date = {'year': p.current_year, 'month': p.current_month, 'day': p.current_day}
    game_state.booked_show = {'card': current_card, 'venue_id': venue_id, 'production': prod_data, 'show_date': show_date}
    save_game_state(game_state)
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    flash('Show booked! Go to Dashboard and click Run Show when ready.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/run-show', methods=['POST'])
@require_login
@require_game
def run_show():
    """Simulate a complete show, calculate revenue/profit, award XP/fans."""
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    booked_show = getattr(game_state, 'booked_show', None)
    if not booked_show:
        current_card = session.get('current_card', [])
        venue_id = session.get('current_venue_id')
        prod_data = session.get('show_production', {})
        show_date = session.get('show_date', None)
        if current_card and venue_id:
            booked_show = {'card': current_card, 'venue_id': venue_id, 'production': prod_data, 'show_date': show_date}

    if not booked_show:
        flash('No show booked! Book a show first.', 'error')
        return redirect(url_for('book_show'))

    card = booked_show['card']
    venue_id = booked_show['venue_id']
    show_date = booked_show.get('show_date', {'year': promotion.current_year, 'month': promotion.current_month, 'day': promotion.current_day})
    prod_data = booked_show.get('production', {})
    production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    production_cost = production.get_total_cost()
    production_quality = production.get_total_quality_bonus()
    production_fans = production.get_total_fan_bonus()

    venue = get_venue_by_id(venue_id)
    if not venue:
        for v in get_venues_by_continent(getattr(game_state, 'game_settings', {}).get("continent", "North America")):
            if v.id == venue_id:
                venue = v
                break
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('dashboard'))

    show_day_name = get_day_name(get_day_of_week(show_date['year'], show_date['month'], show_date['day']))

    match_engine = MatchEngine(promotion)
    if hasattr(game_state, 'storyline_engine') and game_state.storyline_engine:
        match_engine.storyline_engine = game_state.storyline_engine
    if hasattr(game_state, 'relationship_manager') and game_state.relationship_manager:
        match_engine.relationship_manager = game_state.relationship_manager

    results = []
    total_rating = 0.0
    five_star = 0
    four_star = 0
    title_changes = []
    total_show_time = 0

    for match_data in card:
        participants = []
        for i in range(1, 31):
            name = match_data.get(f'wrestler{i}', '')
            if name:
                for w in promotion.roster:
                    if w.name == name:
                        participants.append(w)
                        break
        if len(participants) < 2:
            continue
        w1 = participants[0]
        w2 = participants[1]
        match_time = match_data.get('match_time', 'Standard')
        time_info = MATCH_TIME_OPTIONS.get(match_time, MATCH_TIME_OPTIONS['Standard'])
        total_show_time += time_info['minutes']

        try:
            result = match_engine.simulate_match(
                wrestler1=w1, wrestler2=w2,
                match_type=match_data.get('match_type', 'Singles'),
                is_title_match=match_data.get('is_title_match', False),
                is_main_event=match_data.get('is_main_event', False),
                match_minutes=time_info['minutes'],
            )
        except TypeError:
            result = match_engine.simulate_match(
                wrestler1=w1, wrestler2=w2,
                is_title_match=match_data.get('is_title_match', False),
                is_main_event=match_data.get('is_main_event', False),
            )
        adjusted_rating = min(5.0, max(0.0, result.match_rating + (production_quality * 0.02)))

        match_format = match_data.get('match_format', 'singles')
        teams = get_match_type_info().get(match_data.get('match_type', ''), {}).get('teams', None)
        winning_team = []
        losing_team = []
        if match_format in ['multi', 'variable', 'rumble', 'gauntlet', 'referee'] and len(participants) > 2:
            weights = [getattr(p, 'popularity', 30) + getattr(p, 'overall_rating', 50) for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            actual_loser = random.choice([p for p in participants if p != actual_winner])
        elif match_format in ['tag', 'handicap', 'tag3', 'tag4', 'wargames'] and teams and len(participants) > 2:
            t1_size = teams[0]
            team1 = participants[:t1_size]
            team2 = participants[t1_size:]
            weights = [getattr(p, 'popularity', 30) + getattr(p, 'overall_rating', 50) for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        else:
            actual_winner = result.winner
            actual_loser = result.loser

        winner_display = " & ".join([p.name for p in winning_team]) if winning_team else (actual_winner.name if actual_winner else 'DRAW')
        display = match_data.get('display', f'{w1.name} vs {w2.name}')
        match_result = {
            'display': display, 'wrestler1': w1.name, 'wrestler2': w2.name,
            'all_participants': [p.name for p in participants],
            'winner': winner_display,
            'winning_team': [p.name for p in winning_team] if winning_team else [],
            'finish': result.finish_type.value if hasattr(result.finish_type, 'value') else str(result.finish_type),
            'rating': adjusted_rating,
            'crowd': result.crowd_reaction,
            'match_type': match_data.get('match_type', 'Singles'),
            'match_time': match_time, 'match_minutes': time_info['minutes'],
            'is_main_event': match_data.get('is_main_event', False),
            'is_title_match': match_data.get('is_title_match', False),
            'title_name': match_data.get('title_name', ''),
            'title_changed': False,
            'storyline_bonus': getattr(result, 'storyline_bonus', 0),
            'chemistry_bonus': getattr(result, 'chemistry_bonus', 0),
        }

        if match_data.get('is_title_match') and match_data.get('title_name') and actual_winner:
            title_name = match_data['title_name']
            if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
                try:
                    champ = game_state.championship_manager.get_championship_by_name(title_name)
                    if champ:
                        if champ.current_champion == actual_winner.name:
                            champ.record_defense(actual_loser.name if actual_loser else "")
                        else:
                            date_str = format_date(show_date['year'], show_date['month'], show_date['day'])
                            champ.award_title(actual_winner.name, date_str)
                            if hasattr(actual_winner, 'win_championship'):
                                actual_winner.win_championship()
                            match_result['title_changed'] = True
                            title_changes.append({'title': title_name, 'new_champion': actual_winner.name})
                except Exception:
                    pass

        results.append(match_result)
        total_rating += adjusted_rating
        if adjusted_rating >= 5.0:
            five_star += 1
        elif adjusted_rating >= 4.0:
            four_star += 1

        if game_state.ai_director and actual_winner and actual_loser:
            try:
                game_state.ai_director.record_match_result(actual_winner.name, actual_loser.name, adjusted_rating)
            except Exception:
                pass

    avg_rating = total_rating / len(results) if results else 0

    available_minutes = venue.get_available_minutes()
    minutes_over = total_show_time - available_minutes
    overrun_penalty = calculate_overrun_penalty(minutes_over)
    overrun_fine = overrun_penalty.get('fine', 0)
    overrun_message = overrun_penalty.get('message', '')
    if minutes_over > 0:
        try:
            venue.apply_overrun_penalty(minutes_over, getattr(promotion, 'current_week', 0))
        except Exception:
            pass
        promotion.budget -= overrun_fine

    attendance = venue.get_expected_attendance(promotion.prestige, show_day_name)
    attendance = min(attendance, venue.capacity)
    is_sellout = attendance >= venue.capacity * 0.95
    revenue_breakdown = venue.calculate_revenue(attendance, show_day_name)
    ticket_revenue = revenue_breakdown['tickets']
    merch_revenue = int(attendance * 5 * getattr(promotion, 'merchandise_modifier', 1.0))
    alcohol_revenue = revenue_breakdown.get('alcohol', 0)
    concession_revenue = revenue_breakdown.get('concessions', 0)
    vip_revenue = revenue_breakdown.get('vip', 0)
    venue_cost = venue.get_rental_cost(show_day_name)
    total_costs = venue_cost + production_cost + overrun_fine
    total_revenue = ticket_revenue + merch_revenue + alcohol_revenue + concession_revenue + vip_revenue
    profit = total_revenue - total_costs
    promotion.budget += profit
    promotion.fan_base += production_fans

    show_rewards = {'fans': {'total': 0}, 'xp': {'total': 0}}
    if progression:
        try:
            show_rewards = progression.process_show_completion(
                is_ppv=False, average_match_rating=avg_rating, attendance=attendance,
                capacity=venue.capacity, venue_prestige=venue.prestige,
                venue_tier=venue.tier.value, venue_id=venue.id,
                five_star_matches=five_star, four_star_matches=four_star,
                ticket_price=revenue_breakdown['tickets'] // max(attendance, 1),
                merchandise_modifier=getattr(promotion, 'merchandise_modifier', 1.0),
                total_matches=len(results),
            )
        except Exception:
            pass

    promotion.fan_base += show_rewards.get('fans', {}).get('total', 0)

    cal_system = getattr(game_state, 'calendar', getattr(game_state, 'calendar_system', None))
    if cal_system:
        try:
            main_event_match = results[-1].get('display', '') if results else ""
            cal_system.add_show(
                year=show_date['year'], month=show_date['month'], day=show_date['day'],
                venue=venue.name, attendance=attendance, capacity=venue.capacity,
                rating=avg_rating, profit=profit, is_sellout=is_sellout,
                main_event=main_event_match, matches_count=len(results),
            )
        except Exception:
            pass

    try:
        venue.record_event(attendance, profit)
    except Exception:
        pass

    promotion.advance_to_date(show_date['year'], show_date['month'], show_date['day'])
    promotion.advance_days(1)

    if hasattr(game_state, 'record_show_completion'):
        try:
            match_results_for_ai = [
                {
                    "wrestler_names": r.get("all_participants", []),
                    "match_display": r.get("display", ""),
                    "rating": r.get("rating", 0),
                    "winner": r.get("winner", ""),
                    "finish_type": r.get("finish", ""),
                }
                for r in results
            ]
            game_state.record_show_completion(
                avg_rating=avg_rating, attendance=attendance,
                is_sellout=is_sellout, profit=profit,
                venue_name=venue.name, match_results=match_results_for_ai,
            )
        except Exception:
            pass

    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    session['show_date'] = None

    ai_result, total_salaries = process_week_advancement(game_state)
    save_game_state(game_state)
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    # ===== Build Show Report (two screens) — additive, save-safe =====
    fans_gained = show_rewards.get('fans', {}).get('total', 0) + production_fans
    try:
        _wr = ensure_writers_room_data(game_state)
        _active_sls = [s for s in _wr.get('custom_storylines', []) if s.get('status') == 'active']
    except Exception:
        _active_sls = []
    try:
        _tweets = generate_show_tweets(
            results=results, avg_rating=avg_rating, attendance=attendance,
            capacity=venue.capacity, is_sellout=is_sellout, profit=profit,
            title_changes=title_changes, fans_change=fans_gained,
        )
    except Exception as e:
        print(f"Tweet gen error: {e}")
        _tweets = []
    game_state.last_show_breakdown = build_show_breakdown(
        results=results, avg_rating=avg_rating, attendance=attendance,
        capacity=venue.capacity, is_sellout=is_sellout,
        ticket_revenue=ticket_revenue, merch_revenue=merch_revenue,
        alcohol_revenue=alcohol_revenue, concession_revenue=concession_revenue,
        vip_revenue=vip_revenue, venue_cost=venue_cost,
        production_cost=production_cost, profit=profit,
        fans_change=fans_gained, title_changes=title_changes,
        tweets=_tweets, venue_name=venue.name, currency=currency,
        active_storylines=_active_sls,
    )
    save_game_state(game_state)

    return redirect(url_for('show_report'))

@app.route('/skip-week', methods=['POST'])
@require_login
@require_game
def skip_week():
    game_state = get_game_state()
    promotion = game_state.promotion
    promotion.advance_days(7)
    ai_result, total_salaries = process_week_advancement(game_state)
    fan_loss = int(promotion.fan_base * 0.02)
    promotion.fan_base = max(0, promotion.fan_base - fan_loss)
    save_game_state(game_state)
    flash(f'Skipped a week. Booking Fees: ${total_salaries:,}. Lost {fan_loss} fans.', 'warning')
    return redirect(url_for('dashboard'))


# ============= SHOW REPORT SCREENS =============
@app.route('/show-report')
@require_login
@require_game
def show_report():
    game_state = get_game_state()
    b = getattr(game_state, 'last_show_breakdown', None)
    if not b:
        flash('No recent show to report on.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('show_report.html', promotion=game_state.promotion,
                           b=b, hide_base_hud=True)


@app.route('/show-report/finances')
@require_login
@require_game
def show_report_finances():
    game_state = get_game_state()
    b = getattr(game_state, 'last_show_breakdown', None)
    if not b:
        flash('No recent show to report on.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('show_report_finances.html', promotion=game_state.promotion,
                           b=b, hide_base_hud=True)


@app.route('/show-report/social')
@require_login
@require_game
def show_report_social():
    game_state = get_game_state()
    b = getattr(game_state, 'last_show_breakdown', None)
    if not b:
        flash('No recent show to report on.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('show_report_social.html', promotion=game_state.promotion,
                           b=b, hide_base_hud=True)


# ==================== EVENTS ====================
@app.route('/events')
@require_login
@require_game
def events():
    game_state = get_game_state()
    ai_director = game_state.ai_director
    if not ai_director:
        return redirect(url_for('dashboard'))
    try:
        all_events = ai_director.get_active_events()
    except Exception:
        all_events = []
    return render_template('events.html', events=all_events, promotion=game_state.promotion)


@app.route('/resolve-event/<path:event_id>/<int:option_index>', methods=['POST'])
@require_login
@require_game
def resolve_event(event_id, option_index):
    game_state = get_game_state()
    ai_director = game_state.ai_director
    promotion = game_state.promotion
    if not ai_director:
        flash('AI Director not available!', 'error')
        return redirect(url_for('dashboard'))
    try:
        result = ai_director.resolve_event(event_id, option_index)
    except Exception as e:
        flash(f'Could not resolve event: {e}', 'error')
        return redirect(url_for('events'))
    if result.get('success'):
        effects = result.get('effects', {})
        # Release wrestlers
        if effects.get('release_w1') or effects.get('release'):
            event = result.get('event')
            if event:
                names = getattr(event, 'wrestlers_involved', [])
                for name in names:
                    try:
                        game_state.remove_wrestler_from_roster(name, mark_as_indy_god=False)
                    except Exception:
                        pass
        # Money effects
        if effects.get('money'):
            promotion.budget += effects['money']
        # Salary changes
        if effects.get('salary_change') or effects.get('salary_w1'):
            change = effects.get('salary_change', effects.get('salary_w1', 0))
            event = result.get('event')
            if event:
                for name in getattr(event, 'wrestlers_involved', []):
                    w = game_state.get_wrestler_by_name(name)
                    if w:
                        if hasattr(w, 'booking_fee'):
                            w.booking_fee = max(0, getattr(w, 'booking_fee', 0) + change)
                        elif hasattr(w, 'salary'):
                            w.salary = max(0, getattr(w, 'salary', 0) + change)
                        break
        # Morale effects
        if effects.get('morale') or effects.get('morale_w1'):
            change = effects.get('morale', effects.get('morale_w1', 0))
            event = result.get('event')
            if event:
                for name in getattr(event, 'wrestlers_involved', []):
                    w = game_state.get_wrestler_by_name(name)
                    if w and hasattr(w, 'adjust_morale'):
                        w.adjust_morale(change)
                        break
        if effects.get('morale_all'):
            for w in game_state.promotion.roster:
                if hasattr(w, 'adjust_morale'):
                    w.adjust_morale(effects['morale_all'])
        # Fan/prestige effects
        if effects.get('fan_bonus'):
            promotion.fan_base = max(0, promotion.fan_base + effects['fan_bonus'])
        if effects.get('prestige'):
            promotion.prestige = max(0, min(100, promotion.prestige + effects['prestige']))
        save_game_state(game_state)
        flash(result.get('message', 'Event resolved'), 'success')
    else:
        flash(result.get('message', 'Could not resolve'), 'error')
    return redirect(url_for('events'))


# ==================== CHAMPIONSHIPS ====================
@app.route('/championships')
@require_login
@require_game
def championships():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
        from classes.championship import ChampionshipManager
        game_state.championship_manager = ChampionshipManager()
        save_game_state(game_state)
    champ_manager = game_state.championship_manager
    limits = get_cumulative_limits(progression.level if progression else 1)
    max_champs = limits.get("max_championships", 0)
    active = champ_manager.get_active_championships() if champ_manager else []

    tournaments = []
    accolades = []
    next_slot_cost = 0
    try:
        if hasattr(champ_manager, 'get_active_tournaments'):
            tournaments = champ_manager.get_active_tournaments()
        if hasattr(champ_manager, 'get_planning_tournaments'):
            tournaments += champ_manager.get_planning_tournaments()
        accolades = getattr(champ_manager, 'accolades', []) or []
        if hasattr(champ_manager, 'get_next_slot_cost'):
            next_slot_cost = champ_manager.get_next_slot_cost()
    except Exception:
        pass

    return render_template('championships.html',
        promotion=promotion,
        championships=active,
        tournaments=tournaments,
        accolades=accolades,
        next_slot_cost=next_slot_cost,
        unlocked_slots=getattr(champ_manager, 'unlocked_slots', 0),
        max_slots=getattr(champ_manager, 'max_slots', 0),
        max_championships=max_champs,
        current_level=progression.level if progression else 1,
        championship_costs=CHAMPIONSHIP_COSTS,
        budget=promotion.budget,
    )


@app.route('/create-championship', methods=['GET', 'POST'])
@require_login
@require_game
def create_championship():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
        from classes.championship import ChampionshipManager
        game_state.championship_manager = ChampionshipManager()
    champ_manager = game_state.championship_manager
    if request.method == 'POST':
        name = request.form.get('name', 'Championship')
        level = request.form.get('level', 'Singles Championship')
        gender = request.form.get('gender', "Men's")
        rules = request.form.get('rules', 'Standard')
        try:
            level_enum = ChampionshipLevel(level)
            gender_enum = ChampionshipGender(gender)
            rules_enum = ChampionshipRule(rules)
        except ValueError as e:
            flash(f'Invalid selection: {e}', 'error')
            return redirect(url_for('championships'))
        costs = CHAMPIONSHIP_COSTS.get(level_enum, {})
        creation_cost = costs.get("creation_cost", 15000)
        if promotion.budget < creation_cost:
            flash(f'Cannot afford! Need ${creation_cost:,}', 'error')
            return redirect(url_for('championships'))
        try:
            championship = champ_manager.create_championship(
                name=name, level=level_enum,
                gender=gender_enum, rules=rules_enum,
            )
        except Exception as e:
            flash(f'Failed to create: {e}', 'error')
            return redirect(url_for('championships'))
        if championship:
            promotion.budget -= creation_cost
            save_game_state(game_state)
            flash(f'Created the {name}!', 'success')
        else:
            flash('Failed to create championship!', 'error')
        return redirect(url_for('championships'))
    levels = [{"value": l.value, "name": l.value, "cost": CHAMPIONSHIP_COSTS[l]["creation_cost"]} for l in ChampionshipLevel]
    genders = [g.value for g in ChampionshipGender]
    rules_list = [r.value for r in ChampionshipRule]
    return render_template('create_championship.html',
        levels=levels, genders=genders, rules=rules_list,
        budget=promotion.budget,
        slots_used=len(champ_manager.championships),
        slots_available=champ_manager.unlocked_slots,
    )


@app.route('/unlock-slot', methods=['POST'])
@require_login
@require_game
def unlock_slot():
    game_state = get_game_state()
    promotion = game_state.promotion
    champ_manager = game_state.championship_manager
    if not champ_manager:
        flash('No championship system!', 'error')
        return redirect(url_for('championships'))
    try:
        success, cost, new_total = champ_manager.unlock_slot(promotion.budget)
        if success:
            promotion.budget -= cost
            save_game_state(game_state)
            flash(f'Unlocked championship slot {new_total}! Cost: ${cost:,}', 'success')
        else:
            flash(f'Cannot unlock slot. Need ${cost:,}', 'error')
    except Exception as e:
        flash(f'Slot unlock error: {e}', 'error')
    return redirect(url_for('championships'))


@app.route('/award-title/<path:championship_id>', methods=['GET', 'POST'])
@require_login
@require_game
def award_title(championship_id):
    """
    Award a championship to:
      - 1 wrestler (singles)
      - 2 wrestlers (tag teams) — as a registered team OR any 2 individuals
      - 3 wrestlers (trios) — as a registered trio/faction OR any 3 individuals
    """
    game_state = get_game_state()
    promotion = game_state.promotion
    champ_manager = game_state.championship_manager
    if not champ_manager:
        flash('No championship system!', 'error')
        return redirect(url_for('championships'))

    championship = champ_manager.get_championship(championship_id)
    if not championship:
        flash('Championship not found!', 'error')
        return redirect(url_for('championships'))

    is_tag_title = getattr(championship, 'is_tag_title', False) or championship.level.value == 'Tag Team Championship'
    is_trios_title = getattr(championship, 'is_trios_title', False) or championship.level.value == 'Trios Championship'
    is_trophy = getattr(championship, 'is_trophy', False)

    if is_trios_title:
        required_holders = 3
    elif is_tag_title:
        required_holders = 2
    else:
        required_holders = 1

    if request.method == 'POST':
        mode = request.form.get('award_mode', 'individual').strip()
        group_id = request.form.get('group_id', '').strip()

        wrestler1 = (request.form.get('wrestler1') or request.form.get('wrestler') or '').strip()
        wrestler2 = (request.form.get('wrestler2') or request.form.get('tag_partner') or '').strip()
        wrestler3 = (request.form.get('wrestler3') or request.form.get('tag_partner_2') or '').strip()

        if not wrestler1:
            flash('Please select a primary holder!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))
        if required_holders >= 2 and not wrestler2:
            flash('This title needs 2 holders — please select the 2nd holder!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))
        if required_holders >= 3 and not wrestler3:
            flash('Trios titles need 3 holders — please select the 3rd holder!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        chosen = [wrestler1]
        if required_holders >= 2:
            chosen.append(wrestler2)
        if required_holders >= 3:
            chosen.append(wrestler3)

        if len(chosen) != len(set(chosen)):
            flash('Cannot select the same wrestler twice!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        roster_names = {w.name for w in promotion.roster}
        invalid = [w for w in chosen if w not in roster_names]
        if invalid:
            flash(f'Not on your roster: {", ".join(invalid)}', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        held_by_group_id = ""
        held_by_group_name = ""
        team_members_snapshot = []
        if mode == 'group' and group_id:
            gm = game_state.group_manager
            if gm:
                group = gm.get_group(group_id)
                if group and group.is_active:
                    invalid_members = [w for w in chosen if w not in group.members]
                    if invalid_members:
                        flash(f'These wrestlers are not in {group.name}: {", ".join(invalid_members)}', 'error')
                        return redirect(url_for('award_title', championship_id=championship_id))
                    held_by_group_id = group.id
                    held_by_group_name = group.name
                    team_members_snapshot = list(group.members)

        date_str = format_date(promotion.current_year, promotion.current_month, promotion.current_day)

        try:
            championship.award_title(
                champion_name=wrestler1,
                date=date_str,
                tag_partner=wrestler2 if required_holders >= 2 else "",
                tag_partner_2=wrestler3 if required_holders >= 3 else "",
                held_by_group_id=held_by_group_id,
                held_by_group_name=held_by_group_name,
                team_members=team_members_snapshot,
            )
        except Exception as e:
            flash(f'Could not award title: {e}', 'error')
            return redirect(url_for('championships'))

        for name in chosen:
            w = game_state.get_wrestler_by_name(name)
            if not w:
                continue
            if hasattr(w, 'win_championship'):
                try:
                    w.win_championship()
                except Exception:
                    pass
            if is_trophy and hasattr(w, 'popularity'):
                try:
                    w.popularity = min(100, getattr(w, 'popularity', 0) + 10)
                except Exception:
                    pass

        if held_by_group_id and game_state.group_manager:
            grp = game_state.group_manager.get_group(held_by_group_id)
            if grp:
                try:
                    if is_trophy:
                        grp.record_trophy_won()
                    else:
                        grp.record_title_won()
                except Exception:
                    pass

        save_game_state(game_state)

        holders_display = " & ".join(chosen)
        if held_by_group_name:
            flash(f'🏆 {holders_display} ({held_by_group_name}) are the new {championship.name}!', 'success')
        else:
            flash(f'🏆 {holders_display} {"is" if len(chosen) == 1 else "are"} the new {championship.name}!', 'success')

        if hasattr(game_state, 'inbox') and game_state.inbox:
            try:
                icon = "🏆" if is_trophy else "👑"
                subject = f"New {championship.name} {'winner' if is_trophy else 'champion'}!"
                body_lines = [f"{holders_display} {'have won' if len(chosen) > 1 else 'has won'} the {championship.name}!"]
                if held_by_group_name:
                    body_lines.append(f"\nRepresenting: {held_by_group_name}")
                if is_trophy:
                    body_lines.append(f"\n🏆 +10 popularity awarded to each holder.")
                game_state.inbox.add_message(
                    sender="Booking Office",
                    subject=subject,
                    body="\n".join(body_lines),
                    year=promotion.current_year,
                    month=promotion.current_month,
                    day=promotion.current_day,
                    message_type="general",
                    icon=icon,
                )
            except Exception:
                pass

        return redirect(url_for('championships'))

    # ===== GET: render picker =====
    eligible = [w for w in promotion.roster if not getattr(w, 'is_injured', False)]

    gender_value = championship.gender.value
    if gender_value == "Men's":
        eligible = [w for w in eligible if getattr(getattr(w, 'gender', None), 'value', '') in ['Male', 'Intergender']]
    elif gender_value == "Women's":
        eligible = [w for w in eligible if getattr(getattr(w, 'gender', None), 'value', '') in ['Female', 'Intergender']]

    eligible.sort(key=lambda w: getattr(w, 'popularity', 0), reverse=True)

    wrestler_options = []
    gm = game_state.group_manager
    for w in eligible:
        tag_or_trio_name = ""
        faction_name = ""
        try:
            if gm:
                tag = gm.get_tag_or_trio_for_wrestler(w.name)
                if tag:
                    tag_or_trio_name = tag.name
                fac = gm.get_faction_for_wrestler(w.name)
                if fac:
                    faction_name = fac.name
        except Exception:
            pass

        wrestler_options.append({
            "name": w.name,
            "gender": getattr(getattr(w, 'gender', None), 'value', '') if hasattr(w, 'gender') else '',
            "popularity": getattr(w, 'popularity', 0),
            "tag_team": tag_or_trio_name,
            "faction": faction_name,
        })

    return render_template('award_title.html',
        promotion=promotion,
        championship=championship,
        wrestlers=wrestler_options,
        is_tag_title=is_tag_title,
        is_trios_title=is_trios_title,
        is_trophy=is_trophy,
        required_holders=required_holders,
        hide_base_hud=True,
    )


@app.route('/vacate-title/<path:championship_id>', methods=['POST'])
@require_login
@require_game
def vacate_title(championship_id):
    game_state = get_game_state()
    champ_manager = game_state.championship_manager
    if champ_manager:
        championship = champ_manager.get_championship(championship_id)
        if championship:
            try:
                championship.vacate("Vacated by management")
                save_game_state(game_state)
                flash(f'{championship.name} has been vacated!', 'info')
            except Exception as e:
                flash(f'Could not vacate: {e}', 'error')
    return redirect(url_for('championships'))


# ==================== CAREER / PROFILE ====================
@app.route('/career')
@require_login
@require_game
def career():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    if progression:
        level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
        tier = get_promotion_tier(level)
        tier_name = get_tier_name(tier)
        earned_achievements = progression.get_earned_achievements() if hasattr(progression, 'get_earned_achievements') else []
        stats = progression.stats if hasattr(progression, 'stats') else {}
        total_achievements = len(progression.achievements) if hasattr(progression, 'achievements') else 0
    else:
        level, percentage, tier_name = 1, 0, "Backyard"
        earned_achievements = []
        stats = {}
        total_achievements = 0
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    return render_template('career.html',
        promotion=promotion, progression=progression,
        level=level, tier_name=tier_name,
        xp_percentage=percentage,
        stats=stats,
        achievements=earned_achievements,
        total_achievements=total_achievements,
        currency=currency,
    )


# ==================== INBOX ====================
@app.route('/inbox')
@require_login
@require_game
def inbox():
    game_state = get_game_state()
    if not game_state.inbox:
        from classes.inbox import InboxManager
        game_state.inbox = InboxManager()
        save_game_state(game_state)
    try:
        if hasattr(game_state.inbox, 'get_inbox'):
            messages = game_state.inbox.get_inbox()
        elif hasattr(game_state.inbox, 'get_all_messages'):
            messages = game_state.inbox.get_all_messages()
        else:
            messages = getattr(game_state.inbox, 'messages', [])
        unread_count = game_state.inbox.get_unread_count()
    except Exception:
        messages = []
        unread_count = 0
    return render_template('inbox.html',
        promotion=game_state.promotion,
        messages=messages,
        unread_count=unread_count,
        hide_base_hud=True,
    )


@app.route('/inbox/read/<path:msg_id>')
@require_login
@require_game
def read_message(msg_id):
    game_state = get_game_state()
    if not game_state.inbox:
        flash('No inbox!', 'error')
        return redirect(url_for('dashboard'))
    msg = game_state.inbox.get_message(msg_id)
    if not msg:
        flash('Message not found!', 'error')
        return redirect(url_for('inbox'))
    try:
        game_state.inbox.mark_read(msg_id)
    except Exception:
        try:
            msg.mark_read()
        except Exception:
            pass
    save_game_state(game_state)
    return render_template('read_message.html',
        promotion=game_state.promotion,
        message=msg,
        hide_base_hud=True,
    )


@app.route('/inbox/mark-all-read', methods=['POST'])
@require_login
@require_game
def mark_all_read():
    game_state = get_game_state()
    if game_state.inbox:
        try:
            game_state.inbox.mark_all_read()
            save_game_state(game_state)
            flash('All messages marked as read.', 'success')
        except Exception:
            pass
    return redirect(url_for('inbox'))


# ==================== CALLS ====================
@app.route('/calls')
@require_login
@require_game
def calls_app():
    game_state = get_game_state()
    if not hasattr(game_state, 'calls') or game_state.calls is None:
        try:
            from classes.calls import CallsManager
            game_state.calls = CallsManager()
            save_game_state(game_state)
        except ImportError:
            pass
    calls_data = {"incoming": [], "answered": [], "missed": []}
    contacts = []
    incoming_count = 0
    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            calls_data["incoming"] = game_state.calls.get_incoming_calls() if hasattr(game_state.calls, 'get_incoming_calls') else []
            calls_data["answered"] = (game_state.calls.get_answered_calls() if hasattr(game_state.calls, 'get_answered_calls') else [])[:10]
            calls_data["missed"] = (game_state.calls.get_missed_calls() if hasattr(game_state.calls, 'get_missed_calls') else [])[:10]
            contacts = game_state.calls.get_all_contacts() if hasattr(game_state.calls, 'get_all_contacts') else []
            incoming_count = game_state.calls.get_incoming_count() if hasattr(game_state.calls, 'get_incoming_count') else 0
        except Exception:
            pass
    can_take_shark = False
    shark_reason = ""
    active_shark_loans = []
    if hasattr(game_state, 'banking') and game_state.banking:
        try:
            can_take_shark, shark_reason = game_state.banking.can_take_loan(LoanType.LOAN_SHARK)
            active_shark_loans = game_state.banking.get_active_shark_loans() if hasattr(game_state.banking, 'get_active_shark_loans') else []
        except Exception:
            pass
    return render_template('calls.html',
        promotion=game_state.promotion,
        calls=calls_data,
        contacts=contacts,
        incoming_count=incoming_count,
        shark_options=SHARK_LOAN_OPTIONS,
        can_take_shark=can_take_shark,
        shark_reason=shark_reason,
        active_shark_loans=active_shark_loans,
        hide_base_hud=True,
    )


@app.route('/answer-call/<path:call_id>/<int:option_index>', methods=['POST'])
@require_login
@require_game
def answer_call(call_id, option_index):
    game_state = get_game_state()
    if not hasattr(game_state, 'calls') or not game_state.calls:
        flash('No calls system!', 'error')
        return redirect(url_for('calls_app'))
    try:
        result = game_state.calls.answer_call(call_id, option_index)
        if result.get('success'):
            effects = result.get('effects', {})
            if effects.get('money') and game_state.promotion:
                game_state.promotion.budget += effects['money']
            save_game_state(game_state)
            flash(result.get('message', 'Call answered'), 'success')
        else:
            flash(result.get('message', 'Error'), 'error')
    except Exception as e:
        flash(f'Call error: {e}', 'error')
    return redirect(url_for('calls_app'))


@app.route('/decline-call/<path:call_id>', methods=['POST'])
@require_login
@require_game
def decline_call(call_id):
    game_state = get_game_state()
    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            game_state.calls.decline_call(call_id)
            save_game_state(game_state)
            flash('Call declined.', 'info')
        except Exception:
            pass
    return redirect(url_for('calls_app'))


# ==================== BANKING ====================
@app.route('/banking')
@require_login
@require_game
def banking():
    game_state = get_game_state()
    if not hasattr(game_state, 'banking') or game_state.banking is None:
        from classes.banking import BankingManager
        game_state.banking = BankingManager()
        save_game_state(game_state)
    bm = game_state.banking
    try:
        can_bank, bank_reason = bm.can_take_loan(LoanType.BANK)
    except Exception:
        can_bank, bank_reason = False, "Banking unavailable"
    return render_template('banking.html',
        promotion=game_state.promotion,
        budget=game_state.promotion.budget,
        credit_score=getattr(bm, 'credit_score', 600),
        credit_rating=bm.get_credit_rating() if hasattr(bm, 'get_credit_rating') else 'Fair',
        credit_color=bm.get_credit_color() if hasattr(bm, 'get_credit_color') else '#6b7280',
        total_outstanding=bm.get_total_outstanding() if hasattr(bm, 'get_total_outstanding') else 0,
        weekly_obligations=bm.get_total_weekly_obligations() if hasattr(bm, 'get_total_weekly_obligations') else 0,
        active_loans=getattr(bm, 'active_loans', []),
        loan_history=getattr(bm, 'loan_history', []),
        bank_options=BANK_LOAN_OPTIONS,
        can_take_bank=can_bank,
        bank_reason=bank_reason,
        hide_base_hud=True,
    )


@app.route('/take-loan', methods=['POST'])
@require_login
@require_game
def take_loan():
    game_state = get_game_state()
    if not hasattr(game_state, 'banking') or game_state.banking is None:
        from classes.banking import BankingManager
        game_state.banking = BankingManager()
    bm = game_state.banking
    promotion = game_state.promotion
    loan_type_str = request.form.get('loan_type', 'bank')
    option_key = request.form.get('option_key', '')
    loan_type = LoanType.BANK if loan_type_str == 'bank' else LoanType.LOAN_SHARK
    try:
        can_take, reason = bm.can_take_loan(loan_type)
        if not can_take:
            flash(f'Cannot take loan: {reason}', 'error')
            return redirect(url_for('banking') if loan_type == LoanType.BANK else url_for('calls_app'))
        date_str = f"Y{promotion.current_year} M{promotion.current_month} D{promotion.current_day}"
        loan = bm.take_loan(loan_type, option_key, date_str)
        if loan:
            promotion.budget += loan.principal
            save_game_state(game_state)
            flash(f'${loan.principal:,} received! Weekly payments: ${loan.weekly_payment:,}', 'success')
        else:
            flash('Failed to process loan!', 'error')
    except Exception as e:
        flash(f'Loan error: {e}', 'error')
    return redirect(url_for('banking') if loan_type == LoanType.BANK else url_for('calls_app'))


# ==================== INJURY REPORT ====================
@app.route('/injury-report')
@require_login
@require_game
def injury_report():
    game_state = get_game_state()
    if not hasattr(game_state, 'injury_manager') or game_state.injury_manager is None:
        from classes.injury import InjuryManager
        game_state.injury_manager = InjuryManager()
        save_game_state(game_state)
    im = game_state.injury_manager
    return render_template('injury_report.html',
        promotion=game_state.promotion,
        active_injuries=getattr(im, 'active_injuries', []),
        injury_history=getattr(im, 'injury_history', []),
        hide_base_hud=True,
    )
# ==================== WRITERS ROOM ====================

def ensure_writers_room_data(game_state):
    if not hasattr(game_state, 'writers_room_data') or game_state.writers_room_data is None:
        game_state.writers_room_data = {}

    data = game_state.writers_room_data

    data.setdefault('my_writers', [])
    data.setdefault('available_writers', [
        {
            'id': 'writer_heyman_type',
            'name': 'Paulie Danger',
            'style': 'Long-term drama',
            'temperament': 'Temperamental genius',
            'hire_cost': 850,
            'weekly_cost': 850,
            'skill': 92,
            'description': 'Elite character work and faction drama. Expensive, but can turn a roster into stars.',
        },
        {
            'id': 'writer_russo_type',
            'name': 'Vince Crash',
            'style': 'Shock TV',
            'temperament': 'Chaotic',
            'hire_cost': 500,
            'weekly_cost': 500,
            'skill': 72,
            'description': 'Creates controversy, swerves and wild TV moments. High risk, high noise.',
        },
        {
            'id': 'writer_cornette_type',
            'name': 'Jim Classic',
            'style': 'Traditional wrestling',
            'temperament': 'Stubborn purist',
            'hire_cost': 650,
            'weekly_cost': 650,
            'skill': 84,
            'description': 'Old-school logic, promos, grudges and believable feuds.',
        },
    ])

    data.setdefault('available_freelancers', [
        {
            'id': 'freelancer_indie_angles',
            'name': 'Casey Quill',
            'style': 'Indie angles',
            'hire_cost': 300,
            'cost': 300,
            'skill': 65,
            'description': 'Cheap short-term feud pitches for small promotions.',
        },
        {
            'id': 'freelancer_horror',
            'name': 'Morgan Midnight',
            'style': 'Dark gimmicks',
            'hire_cost': 450,
            'cost': 450,
            'skill': 74,
            'description': 'Good for supernatural, mystery and betrayal stories.',
        },
        {
            'id': 'freelancer_sports',
            'name': 'Alex Ledger',
            'style': 'Sports presentation',
            'hire_cost': 400,
            'cost': 400,
            'skill': 70,
            'description': 'Tournament arcs, rankings and competitive rivalries.',
        },
    ])

    data.setdefault('marketplace_storylines', [
        {
            'id': 'market_underdog_rise',
            'title': 'The Underdog Rise',
            'name': 'The Underdog Rise',
            'cost': 500,
            'duration_weeks': 6,
            'heat': 55,
            'description': 'A low-card wrestler earns respect through surprise wins and gutsy losses.',
        },
        {
            'id': 'market_betrayal',
            'title': 'Best Friend Betrayal',
            'name': 'Best Friend Betrayal',
            'cost': 750,
            'duration_weeks': 8,
            'heat': 70,
            'description': 'A tag team or alliance collapses into a heated grudge feud.',
        },
        {
            'id': 'market_title_obsession',
            'title': 'Title Obsession',
            'name': 'Title Obsession',
            'cost': 900,
            'duration_weeks': 10,
            'heat': 78,
            'description': 'A challenger becomes consumed by the championship and crosses the line.',
        },
    ])

    data.setdefault('custom_storylines', [])
    data.setdefault('concluded_storylines', [])

    # Compatibility patch for old saved writer data missing hire_cost.
    for writer in data.get('available_writers', []):
        writer.setdefault('hire_cost', writer.get('weekly_cost', 0))
        writer.setdefault('weekly_cost', writer.get('hire_cost', 0))

    for writer in data.get('my_writers', []):
        writer.setdefault('hire_cost', writer.get('weekly_cost', 0))
        writer.setdefault('weekly_cost', writer.get('hire_cost', 0))

    for freelancer in data.get('available_freelancers', []):
        freelancer.setdefault('hire_cost', freelancer.get('cost', 0))
        freelancer.setdefault('cost', freelancer.get('hire_cost', 0))

    for story in data.get('marketplace_storylines', []):
        story.setdefault('name', story.get('title', 'Storyline Package'))
        story.setdefault('title', story.get('name', 'Storyline Package'))
        story.setdefault('quality', story.get('heat', 50))
        story.setdefault('heat', story.get('quality', 50))
        story.setdefault('duration_weeks', 6)
        story.setdefault('cost', 0)
        story.setdefault('price', story.get('cost', 0))
        story.setdefault('description', '')
        story.setdefault('genre', story.get('theme', 'General'))
        story.setdefault('difficulty', 'Normal')

    return data


def make_storyline_dict(title, wrestlers, theme, duration_weeks, source='custom', heat=45):
    return {
        'id': str(uuid.uuid4()),
        'title': title,
        'name': title,
        'wrestlers': wrestlers,
        'participants': wrestlers,
        'theme': theme,
        'description': theme,
        'duration_weeks': int(duration_weeks),
        'weeks_active': 0,
        'heat': int(heat),
        'status': 'pitched',
        'source': source,
    }


def storyline_matches_id(storyline, storyline_id):
    if isinstance(storyline, dict):
        return str(storyline.get('id', '')) == str(storyline_id)
    return str(getattr(storyline, 'id', '')) == str(storyline_id)


def get_writer_limit(game_state):
    level = game_state.progression.level if game_state.progression else 1
    if level >= 76:
        return 5
    if level >= 51:
        return 3
    if level >= 31:
        return 2
    return 1


def get_safe_ai_info(game_state):
    ai_info = {
        "mood": {
            "emoji": "🧠",
            "state": "Observing",
        },
        "personality": "AI Director",
        "creative_control": False,
        "active_events": 0,
    }

    try:
        if getattr(game_state, 'ai_director', None) and hasattr(game_state, 'get_ai_director_info'):
            loaded_ai_info = game_state.get_ai_director_info()
            if isinstance(loaded_ai_info, dict):
                ai_info.update(loaded_ai_info)
    except Exception as e:
        print(f"AI info error: {e}")

    if "mood" not in ai_info or not ai_info["mood"]:
        ai_info["mood"] = {
            "emoji": "🧠",
            "state": "Observing",
        }

    if isinstance(ai_info.get("mood"), dict):
        ai_info["mood"].setdefault("emoji", "🧠")
        ai_info["mood"].setdefault("state", "Observing")

    return ai_info


@app.route('/writers-room')
@require_login
@require_game
def writers_room():
    game_state = get_game_state()
    ensure_full_ai_systems(game_state)

    promotion = game_state.promotion
    data = ensure_writers_room_data(game_state)

    active_storylines = []
    pitched_storylines = []
    concluded_storylines = []
    booking_suggestions = []

    if getattr(game_state, 'storyline_engine', None):
        try:
            if hasattr(game_state.storyline_engine, 'get_active_storylines'):
                active_storylines = game_state.storyline_engine.get_active_storylines()

            if hasattr(game_state.storyline_engine, 'get_pitched_storylines'):
                pitched_storylines = game_state.storyline_engine.get_pitched_storylines()

            concluded_storylines = getattr(game_state.storyline_engine, 'concluded_storylines', [])[-10:]

            if hasattr(game_state.storyline_engine, 'get_booking_suggestions'):
                booking_suggestions = game_state.storyline_engine.get_booking_suggestions(max_results=5)
        except Exception as e:
            print(f"StorylineEngine writers room error: {e}")

    local_storylines = data.get('custom_storylines', [])
    active_storylines += [s for s in local_storylines if s.get('status') == 'active']
    pitched_storylines += [s for s in local_storylines if s.get('status') == 'pitched']
    concluded_storylines += data.get('concluded_storylines', [])[-10:]

    if not booking_suggestions:
        roster = [w for w in promotion.roster if not getattr(w, 'is_injured', False)]
        top_names = [
            w.name for w in sorted(
                roster,
                key=lambda x: getattr(x, 'popularity', 0),
                reverse=True
            )[:4]
        ]

        if len(top_names) >= 2:
            booking_suggestions.append({
                'title': f'{top_names[0]} vs {top_names[1]} needs a story beat',
                'description': 'Book them in a promo, tag match, or non-finish to grow rivalry heat.',
                'priority': 'High',
            })

        if len(top_names) >= 4:
            booking_suggestions.append({
                'title': 'Create a faction tension angle',
                'description': f'Use {top_names[2]} and {top_names[3]} in a loyalty test or betrayal tease.',
                'priority': 'Medium',
            })

    rival_show_preview = None
    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler and hasattr(rival_scheduler, 'get_next_rival_show_preview'):
            rival_show_preview = rival_scheduler.get_next_rival_show_preview()
    except Exception as e:
        print(f"Rival preview error: {e}")

    available_wrestlers = [
        w for w in promotion.roster
        if not getattr(w, 'is_injured', False)
    ]

    my_writers = data.get('my_writers', [])
    available_writers = data.get('available_writers', [])
    available_freelancers = data.get('available_freelancers', [])
    marketplace_storylines = data.get('marketplace_storylines', [])

    max_writers = get_writer_limit(game_state)
    total_writer_payroll = sum(int(w.get('weekly_cost', 0)) for w in my_writers)

    # ----- Writers Room 2.0 pitch-engine context (safe if module missing) -----
    if WRITERS_ROOM_2:
        pending_pitches = getattr(game_state, 'pending_pitches', []) or []
        directors = DIRECTOR_PROFILES
    else:
        pending_pitches = []
        directors = {}
    active_director = getattr(game_state, 'active_director', 'traditional')

    save_game_state(game_state)

    return render_template(
        'writers_room.html',
        promotion=promotion,
        active_storylines=active_storylines,
        pitched_storylines=pitched_storylines,
        concluded_storylines=concluded_storylines,
        booking_suggestions=booking_suggestions,
        ai_info=get_safe_ai_info(game_state),
        rival_show_preview=rival_show_preview,
        available_wrestlers=available_wrestlers,
        my_writers=my_writers,
        available_writers=available_writers,
        available_freelancers=available_freelancers,
        marketplace_storylines=marketplace_storylines,
        max_writers=max_writers,
        total_writer_payroll=total_writer_payroll,
        active_count=len(active_storylines),
        pitched_count=len(pitched_storylines),
        budget=promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        # Writers Room 2.0
        pending_pitches=pending_pitches,
        directors=directors,
        active_director=active_director,
        hide_base_hud=True,
    )


@app.route('/create-storyline', methods=['GET', 'POST'])
@require_login
@require_game
def create_storyline():
    game_state = get_game_state()
    ensure_full_ai_systems(game_state)

    data = ensure_writers_room_data(game_state)

    if request.method == 'POST':
        title = request.form.get('title', '').strip() or request.form.get('name', '').strip()
        theme = request.form.get('theme', '').strip() or request.form.get('description', '').strip()
        duration_weeks = int(request.form.get('duration_weeks', 6) or 6)

        wrestlers = request.form.getlist('wrestlers') or request.form.getlist('participants')

        if not wrestlers:
            for i in range(1, 9):
                name = request.form.get(f'wrestler{i}', '').strip()
                if name:
                    wrestlers.append(name)

        wrestlers = [w for w in wrestlers if w]

        if not title:
            flash('Storyline needs a title.', 'error')
            return redirect(url_for('writers_room'))

        if len(wrestlers) < 2:
            flash('Storyline needs at least two wrestlers.', 'error')
            return redirect(url_for('writers_room'))

        storyline = make_storyline_dict(
            title=title,
            wrestlers=wrestlers,
            theme=theme or 'Custom storyline',
            duration_weeks=duration_weeks,
            source='custom',
            heat=50,
        )

        data['custom_storylines'].append(storyline)

        save_game_state(game_state)
        flash('Storyline pitched!', 'success')
        return redirect(url_for('writers_room'))

    return render_template(
        'create_storyline.html',
        promotion=game_state.promotion,
        wrestlers=[
            w for w in game_state.promotion.roster
            if not getattr(w, 'is_injured', False)
        ],
        hide_base_hud=True,
    )


@app.route('/storyline-detail/<path:storyline_id>')
@require_login
@require_game
def storyline_detail(storyline_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)

    storyline = None

    for s in data.get('custom_storylines', []):
        if storyline_matches_id(s, storyline_id):
            storyline = s
            break

    if not storyline:
        flash('Storyline not found.', 'error')
        return redirect(url_for('writers_room'))

    return render_template(
        'storyline_detail.html',
        promotion=game_state.promotion,
        storyline=storyline,
        hide_base_hud=True,
    )


@app.route('/approve-storyline/<path:storyline_id>', methods=['POST'])
@require_login
@require_game
def approve_storyline(storyline_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)

    for s in data.get('custom_storylines', []):
        if storyline_matches_id(s, storyline_id):
            s['status'] = 'active'
            save_game_state(game_state)
            flash('Storyline approved and activated!', 'success')
            return redirect(url_for('writers_room'))

    flash('Could not find storyline to approve.', 'error')
    return redirect(url_for('writers_room'))


@app.route('/reject-storyline/<path:storyline_id>', methods=['POST'])
@require_login
@require_game
def reject_storyline(storyline_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)

    before = len(data.get('custom_storylines', []))
    data['custom_storylines'] = [
        s for s in data.get('custom_storylines', [])
        if not storyline_matches_id(s, storyline_id)
    ]

    save_game_state(game_state)

    flash('Storyline rejected.', 'info' if len(data['custom_storylines']) < before else 'warning')
    return redirect(url_for('writers_room'))


@app.route('/conclude-storyline/<path:storyline_id>', methods=['POST'])
@require_login
@require_game
def conclude_storyline(storyline_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)

    for s in list(data.get('custom_storylines', [])):
        if storyline_matches_id(s, storyline_id):
            s['status'] = 'concluded'
            data['custom_storylines'].remove(s)
            data['concluded_storylines'].append(s)
            save_game_state(game_state)
            flash('Storyline concluded.', 'success')
            return redirect(url_for('writers_room'))

    flash('Storyline not found.', 'error')
    return redirect(url_for('writers_room'))


@app.route('/hire-writer/<path:writer_id>', methods=['POST'])
@require_login
@require_game
def hire_writer(writer_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)
    promotion = game_state.promotion

    my_writers = data.get('my_writers', [])
    available_writers = data.get('available_writers', [])

    if len(my_writers) >= get_writer_limit(game_state):
        flash('Writer limit reached.', 'error')
        return redirect(url_for('writers_room'))

    writer = next((w for w in available_writers if str(w.get('id')) == str(writer_id)), None)

    if not writer:
        flash('Writer not found.', 'error')
        return redirect(url_for('writers_room'))

    signing_cost = int(writer.get('hire_cost', writer.get('weekly_cost', 0)))

    if promotion.budget < signing_cost:
        flash('Not enough money to hire this writer.', 'error')
        return redirect(url_for('writers_room'))

    promotion.budget -= signing_cost
    my_writers.append(writer)
    data['available_writers'] = [
        w for w in available_writers
        if str(w.get('id')) != str(writer_id)
    ]

    save_game_state(game_state)
    flash(f'{writer.get("name", "Writer")} hired!', 'success')
    return redirect(url_for('writers_room'))


@app.route('/hire-freelancer/<path:writer_id>', methods=['POST'])
@require_login
@require_game
def hire_freelancer(writer_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)
    promotion = game_state.promotion

    freelancer = next(
        (w for w in data.get('available_freelancers', []) if str(w.get('id')) == str(writer_id)),
        None,
    )

    if not freelancer:
        flash('Freelancer not found.', 'error')
        return redirect(url_for('writers_room'))

    cost = int(freelancer.get('hire_cost', freelancer.get('cost', 0)))

    if promotion.budget < cost:
        flash('Not enough money to hire this freelancer.', 'error')
        return redirect(url_for('writers_room'))

    promotion.budget -= cost

    pitch = make_storyline_dict(
        title=f'{freelancer.get("style", "Freelance")} Pitch',
        wrestlers=[],
        theme=freelancer.get('description', 'Freelance storyline pitch'),
        duration_weeks=4,
        source='freelancer',
        heat=int(freelancer.get('skill', 60)),
    )

    data['custom_storylines'].append(pitch)

    save_game_state(game_state)
    flash(f'{freelancer.get("name", "Freelancer")} delivered a storyline pitch.', 'success')
    return redirect(url_for('writers_room'))


@app.route('/fire-writer/<path:writer_id>', methods=['POST'])
@require_login
@require_game
def fire_writer(writer_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)

    writer = next(
        (w for w in data.get('my_writers', []) if str(w.get('id')) == str(writer_id)),
        None,
    )

    if writer:
        data['my_writers'] = [
            w for w in data.get('my_writers', [])
            if str(w.get('id')) != str(writer_id)
        ]
        data['available_writers'].append(writer)
        save_game_state(game_state)
        flash(f'{writer.get("name", "Writer")} released.', 'info')

    return redirect(url_for('writers_room'))


@app.route('/purchase-storyline/<path:item_id>', methods=['POST'])
@require_login
@require_game
def purchase_storyline(item_id):
    game_state = get_game_state()
    data = ensure_writers_room_data(game_state)
    promotion = game_state.promotion

    item = next(
        (s for s in data.get('marketplace_storylines', []) if str(s.get('id')) == str(item_id)),
        None,
    )

    if not item:
        flash('Storyline package not found.', 'error')
        return redirect(url_for('writers_room'))

    cost = int(item.get('cost', 0))

    if promotion.budget < cost:
        flash('Not enough money to buy this storyline.', 'error')
        return redirect(url_for('writers_room'))

    promotion.budget -= cost

    storyline = make_storyline_dict(
        title=item.get('title', item.get('name', 'Purchased Storyline')),
        wrestlers=[],
        theme=item.get('description', ''),
        duration_weeks=int(item.get('duration_weeks', 6)),
        source='marketplace',
        heat=int(item.get('heat', 50)),
    )

    data['custom_storylines'].append(storyline)
    data['marketplace_storylines'] = [
        s for s in data.get('marketplace_storylines', [])
        if str(s.get('id')) != str(item_id)
    ]

    save_game_state(game_state)
    flash(f'Storyline purchased: {storyline["title"]}', 'success')
    return redirect(url_for('writers_room'))


# ----- Writers Room 2.0 — Pitch Engine -----

@app.route('/writers-room/generate-pitches', methods=['POST'])
@require_login
@require_game
def writers_room_generate_pitches():
    game_state = get_game_state()
    ensure_full_ai_systems(game_state)

    if not WRITERS_ROOM_2:
        flash('Writers Room 2.0 unavailable.', 'error')
        return redirect(url_for('writers_room'))

    names = request.form.getlist('participants')
    if len(names) < 2:
        flash('Pick at least 2 wrestlers for a pitch.', 'error')
        return redirect(url_for('writers_room'))

    mode = request.form.get('mode', 'ai')
    director = request.form.get('director', getattr(game_state, 'active_director', 'traditional'))

    try:
        generate_pitches(game_state, names, mode=mode, director_key=director)
        save_game_state(game_state)
        flash('AI pitches generated! See the AI Pitches tab.', 'success')
    except Exception as e:
        flash(f'Pitch error: {e}', 'error')

    return redirect(url_for('writers_room'))


@app.route('/writers-room/accept-pitch', methods=['POST'])
@require_login
@require_game
def writers_room_accept_pitch():
    game_state = get_game_state()
    ensure_full_ai_systems(game_state)

    if not WRITERS_ROOM_2:
        flash('Writers Room 2.0 unavailable.', 'error')
        return redirect(url_for('writers_room'))

    pitch_id = request.form.get('pitch_id')
    edits = {
        'title': request.form.get('title'),
        'planned_length': int(request.form.get('planned_length', 8) or 8),
    }

    try:
        sl = accept_pitch(game_state, pitch_id, edits=edits)
        if sl:
            # Bridge into your existing dict storyline system so it appears
            # in "Active Storylines" alongside everything else.
            data = ensure_writers_room_data(game_state)
            bridged = make_storyline_dict(
                title=sl['title'],
                wrestlers=sl['participants'],
                theme=f"AI-generated {sl['type'].replace('_', ' ')} storyline",
                duration_weeks=sl['planned_length'],
                source='ai_pitch',
                heat=sl['heat'],
            )
            bridged['status'] = 'active'
            bridged['engine_id'] = sl['id']
            data['custom_storylines'].append(bridged)
            save_game_state(game_state)
            flash(f'Storyline booked: {sl["title"]}', 'success')
        else:
            flash('Could not accept pitch.', 'error')
    except Exception as e:
        flash(f'Pitch error: {e}', 'error')

    return redirect(url_for('writers_room'))


# ==================== TRAINING SCHOOL ====================
@app.route('/training-school')
@require_login
@require_game
def training_school():
    """Training School hub — landing page for all school management."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        from classes.training_school import TrainingSchool
        school = TrainingSchool()
        game_state.training_school = school
        save_game_state(game_state)

    is_founded = False
    try:
        is_founded = school.is_founded()
    except Exception:
        pass

    summary = {}
    active_trainees = []
    if is_founded:
        try:
            summary = school.get_summary()
            active_trainees = school.get_active_trainees()
        except Exception:
            pass

    applicant_count = 0
    coach_count = 0
    scheduled_shows = 0
    try:
        if game_state.trainee_pool:
            applicant_count = game_state.trainee_pool.get_applicant_count()
        if game_state.coach_manager:
            coach_count = game_state.coach_manager.get_coach_count()
        if game_state.trainee_show_manager:
            scheduled_shows = len(game_state.trainee_show_manager.get_scheduled_shows())
    except Exception:
        pass

    active_classes = 0
    raw_enrollments = getattr(game_state, 'active_enrollments', None) or []
    active_classes = sum(1 for e in raw_enrollments if e.get('is_active', True))

    next_tier_info = None
    upgrade_cost = 0
    if is_founded:
        try:
            if school.can_upgrade():
                next_tier = school.get_next_tier()
                if next_tier:
                    next_tier_info = SCHOOL_TIER_INFO.get(next_tier, {})
                    upgrade_cost = school.get_upgrade_cost()
        except Exception:
            pass

    return render_template('training_school.html',
        promotion=game_state.promotion,
        school=school,
        summary=summary,
        active_trainees=active_trainees,
        applicant_count=applicant_count,
        coach_count=coach_count,
        active_classes=active_classes,
        scheduled_shows=scheduled_shows,
        next_tier_info=next_tier_info,
        upgrade_cost=upgrade_cost,
        hide_base_hud=True,
    )


@app.route('/found-training-school', methods=['GET', 'POST'])
@require_login
@require_game
def found_training_school():
    """Found a new training school by purchasing a tier."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        from classes.training_school import TrainingSchool
        school = TrainingSchool()
        game_state.training_school = school

    if request.method == 'POST':
        school_name = request.form.get('school_name', 'Wrestling School')
        school_location = request.form.get('school_location', '')
        tier_key = request.form.get('tier', 'SCHOOL_GYM')

        try:
            tier = SchoolTier[tier_key]
        except (KeyError, ValueError):
            flash('Invalid school tier!', 'error')
            return redirect(url_for('training_school'))

        cost = SCHOOL_TIER_INFO.get(tier, {}).get("purchase_cost", 0)
        if game_state.promotion.budget < cost:
            flash(f'Cannot afford! Need ${cost:,}', 'error')
            return redirect(url_for('found_training_school'))

        try:
            success = school.found_school(
                name=school_name,
                location=school_location or game_state.promotion.location,
                tier=tier,
                week=getattr(game_state.promotion, 'current_week', 0),
                year=getattr(game_state.promotion, 'current_year', 1),
            )
            if success:
                game_state.promotion.budget -= cost
                save_game_state(game_state)
                flash(f'{school_name} founded as a {tier.value}!', 'success')
                return redirect(url_for('training_school'))
        except Exception as e:
            flash(f'Failed to found school: {e}', 'error')
            return redirect(url_for('found_training_school'))

        flash('Failed to found school!', 'error')
        return redirect(url_for('found_training_school'))

    purchase_options = []
    try:
        if hasattr(school, 'get_purchase_options'):
            purchase_options = school.get_purchase_options()
    except Exception:
        pass

    return render_template('found_school.html',
        promotion=game_state.promotion,
        purchase_options=purchase_options,
        hide_base_hud=True,
    )


@app.route('/trainee-recruitment')
@require_login
@require_game
def trainee_recruitment():
    """Trainee recruitment hub — walk-in applicants + scouting."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('Found a training school first!', 'warning')
        return redirect(url_for('training_school'))

    available_applicants = []
    scouting_options = []
    try:
        if game_state.trainee_pool:
            available_applicants = game_state.trainee_pool.get_available_applicants()
            scouting_options = game_state.trainee_pool.get_scouting_options()
    except Exception:
        pass

    walk_in_count = len(available_applicants)

    return render_template('trainee_recruitment.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary(),
        available_applicants=available_applicants,
        walk_in_count=walk_in_count,
        scouting_options=scouting_options,
        hide_base_hud=True,
    )


@app.route('/sign-applicant/<path:applicant_id>', methods=['POST'])
@require_login
@require_game
def sign_applicant(applicant_id):
    """Enroll a walk-in applicant as a trainee."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    try:
        trainee = game_state.trainee_pool.sign_applicant(applicant_id)
        if trainee:
            success, msg = school.enroll_trainee(trainee)
            if success:
                save_game_state(game_state)
                flash(f'{trainee.name} enrolled!', 'success')
            else:
                flash(msg, 'error')
        else:
            flash('Applicant not found!', 'error')
    except Exception as e:
        flash(f'Sign error: {e}', 'error')
    return redirect(url_for('trainee_recruitment'))


@app.route('/reject-applicant/<path:applicant_id>', methods=['POST'])
@require_login
@require_game
def reject_applicant(applicant_id):
    """Remove a walk-in applicant without signing them."""
    game_state = get_game_state()
    if game_state.trainee_pool:
        try:
            game_state.trainee_pool.remove_applicant(applicant_id)
            save_game_state(game_state)
        except Exception:
            pass
    return redirect(url_for('trainee_recruitment'))


@app.route('/scout-for-trainee', methods=['POST'])
@require_login
@require_game
def scout_for_trainee():
    """Spend money to actively scout a higher-quality prospect."""
    game_state = get_game_state()
    school = game_state.training_school
    tier = request.form.get('tier', 'promising')

    if not game_state.trainee_pool or not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    try:
        applicant, cost, message = game_state.trainee_pool.scout_for_prospects(
            scouting_tier=tier,
            budget=game_state.promotion.budget,
            monthly_tuition=school.get_monthly_tuition(),
        )
        if cost > 0:
            game_state.promotion.budget -= cost
        save_game_state(game_state)
        flash(message, 'success' if applicant else 'warning')
    except Exception as e:
        flash(f'Scout error: {e}', 'error')
    return redirect(url_for('trainee_recruitment'))


@app.route('/view-trainees')
@require_login
@require_game
def view_trainees():
    """List all trainees at the school."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'warning')
        return redirect(url_for('training_school'))

    trainees = getattr(school, 'trainees', [])
    active_count = 0
    graduated_count = 0
    try:
        active_count = school.get_active_trainee_count()
        graduated_count = len(school.get_graduated_trainees())
    except Exception:
        pass

    return render_template('view_trainees.html',
        promotion=game_state.promotion,
        school_summary=school.get_summary(),
        trainees=trainees,
        active_count=active_count,
        graduated_count=graduated_count,
        hide_base_hud=True,
    )


@app.route('/trainee-profile/<path:trainee_id>')
@require_login
@require_game
def trainee_profile(trainee_id):
    """View details for a single trainee."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if not trainee:
        flash('Trainee not found!', 'error')
        return redirect(url_for('view_trainees'))

    return render_template('trainee_profile.html',
        promotion=game_state.promotion,
        trainee=trainee,
        hide_base_hud=True,
    )


@app.route('/graduate-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def graduate_trainee(trainee_id):
    """Promote a graduated trainee to the main roster."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if not trainee:
        flash('Trainee not found!', 'error')
        return redirect(url_for('view_trainees'))

    try:
        wrestler_data = trainee.to_wrestler_data()

        stat_fields = ["strength", "speed", "technique", "charisma",
                       "stamina", "toughness", "mic_skills", "psychology"]
        stat_kwargs = {k: v for k, v in wrestler_data.items() if k in stat_fields}

        wrestler = Wrestler(
            name=wrestler_data["name"],
            age=wrestler_data.get("age", 22),
            gender=Gender.MALE if wrestler_data.get("gender", "Male") == "Male" else Gender.FEMALE,
            hometown=wrestler_data.get("hometown", ""),
            wrestler_level=WrestlerLevel.SHOW_READY,
            popularity=wrestler_data.get("popularity", 25),
            morale=wrestler_data.get("morale", 75),
            booking_fee=200,
            contract_type=ContractType.PER_APPEARANCE,
            **stat_kwargs,
        )

        game_state.promotion.roster.append(wrestler)
        school.add_alumni(trainee, "signed_main")
        school.remove_trainee(trainee_id, "graduated")

        for enr in (getattr(game_state, 'active_enrollments', None) or []):
            if enr.get('student_id') == trainee_id and enr.get('student_type') == 'trainee':
                enr['is_active'] = False
                enr['cancelled_reason'] = 'graduated'

        save_game_state(game_state)
        flash(f'{trainee.name} signed to main roster!', 'success')
    except Exception as e:
        flash(f'Graduation error: {e}', 'error')
    return redirect(url_for('view_trainees'))


@app.route('/release-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def release_trainee(trainee_id):
    """Release a trainee to the indies (free agent)."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if trainee:
        try:
            school.add_alumni(trainee, "released_indies")
            school.remove_trainee(trainee_id, "dropped_out")

            for enr in (getattr(game_state, 'active_enrollments', None) or []):
                if enr.get('student_id') == trainee_id and enr.get('student_type') == 'trainee':
                    enr['is_active'] = False
                    enr['cancelled_reason'] = 'released'

            save_game_state(game_state)
            flash(f'{trainee.name} released to the indies.', 'info')
        except Exception:
            pass
    return redirect(url_for('view_trainees'))


@app.route('/expel-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def expel_trainee(trainee_id):
    """Expel a trainee — removes them and damages school reputation."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if trainee:
        try:
            school.add_alumni(trainee, "expelled")
            school.remove_trainee(trainee_id, "dropped_out")
            school.modify_reputation(-5)

            for enr in (getattr(game_state, 'active_enrollments', None) or []):
                if enr.get('student_id') == trainee_id and enr.get('student_type') == 'trainee':
                    enr['is_active'] = False
                    enr['cancelled_reason'] = 'expelled'

            save_game_state(game_state)
            flash(f'{trainee.name} expelled! School reputation -5.', 'warning')
        except Exception:
            pass
    return redirect(url_for('view_trainees'))


@app.route('/roster-training')
@require_login
@require_game
def roster_training():
    """Roster Training hub — book wrestlers into classes."""
    game_state = get_game_state()
    school = game_state.training_school

    available_wrestlers = []
    for w in game_state.promotion.roster:
        if getattr(w, 'is_injured', False):
            continue
        available_wrestlers.append({
            "id": w.name,
            "name": w.name,
            "overall_rating": getattr(w, 'overall_rating', 50),
            "level_number": getattr(w, 'level_number', 1),
        })

    raw_enrollments = getattr(game_state, 'active_enrollments', None) or []
    active_enrollments = []
    enrolled_wrestler_names = set()

    for e in raw_enrollments:
        if not e.get('is_active', True):
            continue
        if e.get('student_type') != 'wrestler':
            continue

        weeks_completed = e.get('weeks_completed', 0)
        duration = max(1, e.get('duration_weeks', 4))
        progress_percent = min(100, int((weeks_completed / duration) * 100))

        active_enrollments.append({
            "id": e.get('id', ''),
            "wrestler_name": e.get('student_name', 'Unknown'),
            "class_name": e.get('class_name', 'Class'),
            "class_icon": e.get('class_icon', '💪'),
            "class_color": e.get('class_color', '#6b7280'),
            "weeks_completed": weeks_completed,
            "duration_weeks": e.get('duration_weeks', 4),
            "progress_percent": progress_percent,
            "weekly_cost": e.get('weekly_cost', 0),
            "coach_name": e.get('coach_name', ''),
        })
        enrolled_wrestler_names.add(e.get('student_id', ''))

    catalog = []
    discount_preview = {}
    max_concurrent = 1
    school_summary = {}
    recommendations = []

    try:
        if school and school.is_founded():
            catalog = get_full_catalog_for_ui(school)
            discount_preview = get_school_discount_preview(school)
            max_concurrent = school.get_max_concurrent_classes()
            school_summary = school.get_summary()

            for w_dict in available_wrestlers[:6]:
                if w_dict['name'] in enrolled_wrestler_names:
                    continue

                w_obj = next(
                    (w for w in game_state.promotion.roster if w.name == w_dict['name']),
                    None,
                )
                if not w_obj:
                    continue

                w_data = {
                    "level_number": getattr(w_obj, 'level_number', 1),
                    "wrestler_level": (
                        w_obj.wrestler_level.value
                        if hasattr(w_obj, 'wrestler_level') and w_obj.wrestler_level
                        else "Show Ready"
                    ),
                    "is_injured": False,
                    "is_trainee": False,
                    "current_training_id": None,
                    "age": getattr(w_obj, 'age', 30),
                    "strength": getattr(w_obj, 'strength', getattr(w_obj, 'power', 50)),
                    "technique": getattr(w_obj, 'technique', getattr(w_obj, 'technical', 50)),
                    "speed": getattr(w_obj, 'speed', 50),
                    "charisma": getattr(w_obj, 'charisma', 50),
                    "stamina": getattr(w_obj, 'stamina', 50),
                    "toughness": getattr(w_obj, 'toughness', 50),
                    "mic_skills": getattr(w_obj, 'mic_skills', 50),
                    "psychology": getattr(w_obj, 'psychology', 50),
                }

                try:
                    recs = get_recommended_classes_for_wrestler(w_data, max_results=1)
                    for r in recs:
                        cls = r["class"]
                        weekly = cls.get_weekly_cost_with_school(school)
                        total = cls.get_total_cost_with_school(school)
                        savings_per_week = max(0, cls.base_weekly_cost - weekly)

                        recommendations.append({
                            "wrestler_id": w_obj.name,
                            "wrestler_name": w_obj.name,
                            "reason": r["reason"],
                            "class_data": {
                                "id": cls.id,
                                "name": cls.name,
                                "icon": cls.icon,
                                "color": cls.color,
                                "weekly_cost": weekly,
                                "total_cost": total,
                                "duration_weeks": cls.duration_weeks,
                                "is_free": total == 0,
                                "has_discount": savings_per_week > 0,
                                "savings": savings_per_week,
                                "risk_summary": cls.get_risk_summary(),
                            },
                        })
                except Exception as rec_err:
                    print(f"Recommendation error for {w_obj.name}: {rec_err}")

            recommendations = recommendations[:5]
        else:
            catalog = get_full_catalog_for_ui(None)
            discount_preview = get_school_discount_preview(None)
    except Exception as e:
        print(f"roster_training catalog error: {e}")

    return render_template('roster_training.html',
        promotion=game_state.promotion,
        school_summary=school_summary,
        discount_preview=discount_preview,
        catalog=catalog,
        available_wrestlers=available_wrestlers,
        active_enrollments=active_enrollments,
        max_concurrent=max_concurrent,
        recommendations=recommendations,
        hide_base_hud=True,
    )


@app.route('/coach-management')
@require_login
@require_game
def coach_management():
    """Coach hiring + management hub."""
    game_state = get_game_state()
    school = game_state.training_school
    my_coaches = []
    available_coaches = []
    legendary_coaches = []
    payroll = {}
    max_slots = 0
    school_tier_discount = 0

    try:
        if game_state.coach_manager:
            my_coaches = game_state.coach_manager.get_all_coaches()
            payroll = game_state.coach_manager.get_payroll_summary(school)
        if game_state.coach_pool:
            available_coaches = game_state.coach_pool.get_available_coaches()
            legendary_coaches = game_state.coach_pool.get_legendary_coaches()
        if school and school.is_founded():
            max_slots = school.get_coach_slots()
            from classes.coach import SCHOOL_TIER_PAYROLL_DISCOUNT
            school_tier_discount = SCHOOL_TIER_PAYROLL_DISCOUNT.get(school.tier.value, 0)
    except Exception:
        pass

    eligible_veterans = [
        {"id": w.name, "name": w.name, "age": getattr(w, 'age', 30),
         "overall_rating": getattr(w, 'overall_rating', 50),
         "level_number": getattr(w, 'level_number', 1),
         "strength": getattr(w, 'strength', getattr(w, 'power', 50)),
         "speed": getattr(w, 'speed', 50),
         "technique": getattr(w, 'technique', getattr(w, 'technical', 50)),
         "mic_skills": getattr(w, 'mic_skills', 50),
         "psychology": getattr(w, 'psychology', 50)}
        for w in game_state.promotion.roster
        if getattr(w, 'level_number', 1) >= 8
    ]
    specialties = list(CoachSpecialty)

    return render_template('coach_management.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary() if school and school.is_founded() else {},
        my_coaches=my_coaches,
        available_coaches=available_coaches,
        legendary_coaches=legendary_coaches,
        payroll=payroll,
        max_slots=max_slots,
        school_tier_discount=school_tier_discount,
        eligible_veterans=eligible_veterans,
        specialties=specialties,
        hide_base_hud=True,
    )


@app.route('/hire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def hire_coach(coach_id):
    """Hire a coach from the pool."""
    game_state = get_game_state()
    try:
        coach = game_state.coach_pool.hire_coach(coach_id) if game_state.coach_pool else None
        if coach:
            hire_cost = coach.get_hire_cost_with_school(game_state.training_school)
            if game_state.promotion.budget < hire_cost:
                flash(f'Cannot afford! Need ${hire_cost:,}', 'error')
                return redirect(url_for('coach_management'))
            game_state.promotion.budget -= hire_cost
            game_state.coach_manager.hire_coach(coach)
            save_game_state(game_state)
            flash(f'{coach.name} hired!', 'success')
        else:
            flash('Coach not found!', 'error')
    except Exception as e:
        flash(f'Hire error: {e}', 'error')
    return redirect(url_for('coach_management'))


@app.route('/fire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def fire_coach(coach_id):
    """Fire a coach — also unassigns them from any trainees."""
    game_state = get_game_state()
    if game_state.coach_manager:
        try:
            school = game_state.training_school
            if school:
                for trainee in getattr(school, 'trainees', []):
                    if getattr(trainee, 'coach_id', '') == coach_id:
                        if hasattr(trainee, 'unassign_coach'):
                            trainee.unassign_coach()
            game_state.coach_manager.fire_coach(coach_id)
            save_game_state(game_state)
            flash('Coach released.', 'info')
        except Exception:
            pass
    return redirect(url_for('coach_management'))


@app.route('/promote-to-coach/<path:wrestler_id>', methods=['POST'])
@require_login
@require_game
def promote_to_coach(wrestler_id):
    """
    Promote a veteran roster wrestler into a player-coach (Veteran type).
    They KEEP their roster spot — can wrestle AND teach.
    """
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('Found a school first!', 'error')
        return redirect(url_for('coach_management'))

    if not game_state.coach_manager:
        flash('Coach manager not available!', 'error')
        return redirect(url_for('coach_management'))

    wrestler = next(
        (w for w in game_state.promotion.roster if w.name == wrestler_id),
        None,
    )
    if not wrestler:
        flash(f'Wrestler "{wrestler_id}" not found on roster.', 'error')
        return redirect(url_for('coach_management'))

    wrestler_level = getattr(wrestler, 'level_number', 1)
    if wrestler_level < 8:
        flash(f'{wrestler.name} is too inexperienced (Level {wrestler_level}). '
              f'Need Level 8+ Top Star tier.', 'error')
        return redirect(url_for('coach_management'))

    if game_state.coach_manager:
        existing = next(
            (c for c in game_state.coach_manager.get_all_coaches()
             if c.wrestler_id == wrestler.name or c.name == wrestler.name),
            None,
        )
        if existing:
            flash(f'{wrestler.name} is already coaching!', 'warning')
            return redirect(url_for('coach_management'))

    specialty_value = request.form.get('specialty', 'All-Around').strip()
    chosen_specialty = None
    for spec in CoachSpecialty:
        if spec.value == specialty_value or spec.name == specialty_value:
            chosen_specialty = spec
            break
    if not chosen_specialty:
        chosen_specialty = CoachSpecialty.ALL_AROUND

    spec_stat_map = {
        CoachSpecialty.STRIKING: getattr(wrestler, 'strength', 50),
        CoachSpecialty.TECHNICAL: getattr(wrestler, 'technique', getattr(wrestler, 'technical', 50)),
        CoachSpecialty.HIGH_FLYING: getattr(wrestler, 'speed', 50),
        CoachSpecialty.POWER: getattr(wrestler, 'strength', 50),
        CoachSpecialty.HARDCORE: getattr(wrestler, 'toughness', 50),
        CoachSpecialty.PROMO: getattr(wrestler, 'mic_skills', 50),
        CoachSpecialty.PSYCHOLOGY: getattr(wrestler, 'psychology', 50),
        CoachSpecialty.CONDITIONING: getattr(wrestler, 'stamina', 50),
        CoachSpecialty.ALL_AROUND: getattr(wrestler, 'overall_rating', 50),
    }
    primary_stat_value = spec_stat_map.get(chosen_specialty, 50)

    base_fee = getattr(wrestler, 'booking_fee', 200)
    weekly_cost = max(75, int(base_fee * 0.4))

    try:
        coach = game_state.coach_manager.promote_wrestler_to_coach(
            wrestler_id=wrestler.name,
            wrestler_name=wrestler.name,
            wrestler_age=getattr(wrestler, 'age', 35),
            primary_stat_value=primary_stat_value,
            specialty=chosen_specialty,
            weekly_cost=weekly_cost,
        )

        if coach:
            save_game_state(game_state)
            flash(f'🎓 {wrestler.name} is now a player-coach! '
                  f'Specialty: {chosen_specialty.value} • '
                  f'Skill: {coach.skill_rating}/100 • '
                  f'+${weekly_cost}/wk coaching fee', 'success')

            if hasattr(game_state, 'inbox') and game_state.inbox:
                try:
                    game_state.inbox.add_message(
                        sender="Training School",
                        subject=f"{wrestler.name} added to coaching staff",
                        body=(f"{wrestler.name} will continue wrestling AND start "
                              f"coaching trainees in {chosen_specialty.value}.\n\n"
                              f"Coaching skill: {coach.skill_rating}/100\n"
                              f"Additional weekly cost: ${weekly_cost:,}\n\n"
                              f"They'll be available to assign to trainees from "
                              f"the Coach Management page."),
                        year=getattr(game_state.promotion, 'current_year', 1),
                        month=getattr(game_state.promotion, 'current_month', 1),
                        day=getattr(game_state.promotion, 'current_day', 1),
                        message_type="general", icon="🎓",
                    )
                except Exception:
                    pass
        else:
            flash('Failed to promote wrestler to coach.', 'error')
    except Exception as e:
        flash(f'Promotion error: {e}', 'error')

    return redirect(url_for('coach_management'))


@app.route('/school-settings', methods=['GET'])
@require_login
@require_game
def school_settings():
    """School settings — pricing, identity, danger zone."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        return redirect(url_for('training_school'))

    summary = school.get_summary()
    recommended_tuition = school.get_recommended_tuition()

    return render_template('school_settings.html',
        promotion=game_state.promotion,
        school=school,
        summary=summary,
        recommended_tuition=recommended_tuition,
        hide_base_hud=True,
    )


@app.route('/update-school-tuition', methods=['POST'])
@require_login
@require_game
def update_school_tuition():
    """Update monthly tuition rate (within tier's min/max range)."""
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        try:
            tuition = int(request.form.get('tuition', school.get_recommended_tuition()))
            success, msg = school.set_tuition(tuition)
            save_game_state(game_state)
            flash(msg, 'success' if success else 'error')
        except Exception as e:
            flash(f'Tuition error: {e}', 'error')
    return redirect(url_for('school_settings'))


@app.route('/update-school-class-markup', methods=['POST'])
@require_login
@require_game
def update_school_class_markup():
    """Update class markup % (-50 to +100)."""
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        try:
            markup = int(request.form.get('markup', 0))
            success, msg = school.set_class_markup(markup)
            save_game_state(game_state)
            flash(msg, 'success' if success else 'error')
        except Exception as e:
            flash(f'Markup error: {e}', 'error')
    return redirect(url_for('school_settings'))


@app.route('/update-school-identity', methods=['POST'])
@require_login
@require_game
def update_school_identity():
    """Update school name + location."""
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        try:
            school.name = request.form.get('school_name', school.name)
            school.location = request.form.get('school_location', school.location)
            save_game_state(game_state)
            flash('School details updated.', 'success')
        except Exception:
            pass
    return redirect(url_for('school_settings'))


@app.route('/reset-school-pricing', methods=['POST'])
@require_login
@require_game
def reset_school_pricing():
    """Reset tuition + class markup to recommended defaults."""
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        try:
            school.current_tuition = school.get_recommended_tuition()
            school.class_markup_percent = 0
            school.rates_customized = False
            save_game_state(game_state)
            flash('Pricing reset to defaults.', 'success')
        except Exception:
            pass
    return redirect(url_for('school_settings'))


@app.route('/shutdown-school', methods=['POST'])
@require_login
@require_game
def shutdown_school():
    """Permanently shut down the training school."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school to shut down!', 'warning')
        return redirect(url_for('training_school'))

    if school.is_upgrading:
        flash('Cannot shut down during an upgrade!', 'error')
        return redirect(url_for('school_settings'))

    school_name = school.name
    trainees_released = 0
    enrollments_cancelled = 0

    try:
        for trainee in list(school.trainees):
            try:
                school.add_alumni(trainee, "school_closed",
                                  notes=f"School '{school_name}' shut down")
                school.remove_trainee(trainee.id, "dropped_out")
                trainees_released += 1
            except Exception:
                pass

        for enr in (getattr(game_state, 'active_enrollments', None) or []):
            if enr.get('is_active', True):
                enr['is_active'] = False
                enr['cancelled_reason'] = 'school_closed'
                enrollments_cancelled += 1

        school.status = SchoolStatus.SHUTDOWN
        school.tier = SchoolTier.NONE
        school.status = SchoolStatus.NOT_FOUNDED
        school.current_tuition = 0
        school.class_markup_percent = 0
        school.is_upgrading = False
        school.upgrade_target = None
        school.upgrade_weeks_remaining = 0

        if hasattr(game_state, 'inbox') and game_state.inbox:
            try:
                game_state.inbox.add_message(
                    sender="Training School",
                    subject=f"{school_name} has closed",
                    body=(f"Your school '{school_name}' has been permanently shut down.\n\n"
                          f"• {trainees_released} trainee(s) released\n"
                          f"• {enrollments_cancelled} active class(es) cancelled\n\n"
                          f"You may found a new school at any time."),
                    year=getattr(game_state.promotion, 'current_year', 1),
                    month=getattr(game_state.promotion, 'current_month', 1),
                    day=getattr(game_state.promotion, 'current_day', 1),
                    message_type="general", icon="❌",
                )
            except Exception:
                pass

        save_game_state(game_state)
        flash(
            f'{school_name} shut down. {trainees_released} trainees released, '
            f'{enrollments_cancelled} classes cancelled.',
            'info'
        )
    except Exception as e:
        flash(f'Shutdown error: {e}', 'error')

    return redirect(url_for('training_school'))


@app.route('/enroll-wrestler', methods=['POST'])
@require_login
@require_game
def enroll_wrestler():
    """Enroll a roster wrestler in a training class."""
    game_state = get_game_state()
    promotion = game_state.promotion
    school = game_state.training_school

    wrestler_id = request.form.get('wrestler_id', '').strip()
    class_id = request.form.get('class_id', '').strip()

    if not wrestler_id or not class_id:
        flash('Missing wrestler or class selection.', 'error')
        return redirect(url_for('roster_training'))

    wrestler = next((w for w in promotion.roster if w.name == wrestler_id), None)
    if not wrestler:
        flash(f'Wrestler "{wrestler_id}" not found on roster.', 'error')
        return redirect(url_for('roster_training'))

    if getattr(wrestler, 'is_injured', False):
        flash(f'{wrestler.name} is injured and cannot train.', 'error')
        return redirect(url_for('roster_training'))

    training_class = get_class(class_id)
    if not training_class:
        flash(f'Class "{class_id}" not found.', 'error')
        return redirect(url_for('roster_training'))

    w_data = {
        "level_number": getattr(wrestler, 'level_number', 1),
        "wrestler_level": (
            wrestler.wrestler_level.value
            if hasattr(wrestler, 'wrestler_level') and wrestler.wrestler_level
            else "Show Ready"
        ),
        "is_injured": False,
        "is_trainee": False,
        "current_training_id": None,
        "age": getattr(wrestler, 'age', 30),
        "strength": getattr(wrestler, 'strength', getattr(wrestler, 'power', 50)),
        "technique": getattr(wrestler, 'technique', getattr(wrestler, 'technical', 50)),
        "speed": getattr(wrestler, 'speed', 50),
        "charisma": getattr(wrestler, 'charisma', 50),
        "stamina": getattr(wrestler, 'stamina', 50),
        "toughness": getattr(wrestler, 'toughness', 50),
        "mic_skills": getattr(wrestler, 'mic_skills', 50),
        "psychology": getattr(wrestler, 'psychology', 50),
    }

    can_take, reason = can_wrestler_take_class(training_class, w_data)
    if not can_take:
        flash(f'Cannot enroll {wrestler.name}: {reason}', 'error')
        return redirect(url_for('roster_training'))

    raw_enrollments = getattr(game_state, 'active_enrollments', None) or []
    active_count = sum(1 for e in raw_enrollments if e.get('is_active', True))
    max_concurrent = school.get_max_concurrent_classes() if school and school.is_founded() else 1

    if active_count >= max_concurrent:
        flash(f'School at class capacity ({active_count}/{max_concurrent}). '
              f'Cancel an enrollment or upgrade your school.', 'error')
        return redirect(url_for('roster_training'))

    already_enrolled = any(
        e.get('is_active', True)
        and e.get('student_type') == 'wrestler'
        and e.get('student_id') == wrestler.name
        for e in raw_enrollments
    )
    if already_enrolled:
        flash(f'{wrestler.name} is already enrolled in a class.', 'error')
        return redirect(url_for('roster_training'))

    weekly_cost = training_class.get_weekly_cost_with_school(school)
    if promotion.budget < weekly_cost:
        flash(f'Cannot afford first week (${weekly_cost:,}). '
              f'Need ${weekly_cost - promotion.budget:,} more.', 'error')
        return redirect(url_for('roster_training'))

    promotion.budget -= weekly_cost

    if school and hasattr(school, 'record_class_savings'):
        try:
            school.record_class_savings(training_class.base_weekly_cost)
        except Exception:
            pass

    if not hasattr(game_state, 'active_enrollments') or game_state.active_enrollments is None:
        game_state.active_enrollments = []

    enrollment_id = str(uuid.uuid4())[:8]
    enrollment = {
        "id": enrollment_id,
        "student_type": "wrestler",
        "student_id": wrestler.name,
        "student_name": wrestler.name,
        "class_id": training_class.id,
        "class_name": training_class.name,
        "class_icon": training_class.icon,
        "class_color": training_class.color,
        "weekly_cost": weekly_cost,
        "base_weekly_cost": training_class.base_weekly_cost,
        "duration_weeks": training_class.duration_weeks,
        "weeks_completed": 1,
        "is_active": True,
        "completed": False,
        "coach_name": "",
        "year_started": getattr(promotion, 'current_year', 1),
        "week_started": getattr(promotion, 'current_week', 0),
    }
    game_state.active_enrollments.append(enrollment)

    save_game_state(game_state)
    flash(f'{wrestler.name} enrolled in {training_class.name}! '
          f'First week paid (${weekly_cost:,}). '
          f'{training_class.duration_weeks - 1} weeks remaining.', 'success')
    return redirect(url_for('roster_training'))


@app.route('/cancel-enrollment/<path:enrollment_id>', methods=['POST'])
@require_login
@require_game
def cancel_enrollment(enrollment_id):
    """Cancel an active wrestler training enrollment. No refund."""
    game_state = get_game_state()
    raw_enrollments = getattr(game_state, 'active_enrollments', None) or []

    enrollment = next(
        (e for e in raw_enrollments if e.get('id') == enrollment_id),
        None,
    )
    if not enrollment:
        flash('Enrollment not found.', 'error')
        return redirect(url_for('roster_training'))

    if not enrollment.get('is_active', True):
        flash('That enrollment is already inactive.', 'warning')
        return redirect(url_for('roster_training'))

    student_name = enrollment.get('student_name', 'Unknown')
    class_name = enrollment.get('class_name', 'Class')

    enrollment['is_active'] = False
    enrollment['cancelled_reason'] = 'manual_cancel'

    save_game_state(game_state)
    flash(f'{student_name} pulled from {class_name}. No refund.', 'info')
    return redirect(url_for('roster_training'))


@app.route('/enroll-trainee-in-class/<path:trainee_id>', methods=['GET', 'POST'])
@require_login
@require_game
def enroll_trainee_in_class(trainee_id):
    """Enroll a trainee in a school training class (free — covered by tuition)."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if not trainee:
        flash('Trainee not found!', 'error')
        return redirect(url_for('view_trainees'))

    if trainee.status != TraineeStatus.ACTIVE:
        flash(f'{trainee.name} is {trainee.status.value} and cannot enroll.', 'error')
        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    if request.method == 'POST':
        class_id = request.form.get('class_id', '').strip()
        if not class_id:
            flash('No class selected.', 'error')
            return redirect(url_for('enroll_trainee_in_class', trainee_id=trainee_id))

        training_class = get_class(class_id)
        if not training_class:
            flash(f'Class "{class_id}" not found.', 'error')
            return redirect(url_for('enroll_trainee_in_class', trainee_id=trainee_id))

        raw_enrollments = getattr(game_state, 'active_enrollments', None) or []
        active_count = sum(1 for e in raw_enrollments if e.get('is_active', True))
        max_concurrent = school.get_max_concurrent_classes()

        if active_count >= max_concurrent:
            flash(f'School at class capacity ({active_count}/{max_concurrent}).', 'error')
            return redirect(url_for('trainee_profile', trainee_id=trainee_id))

        already_enrolled = any(
            e.get('is_active', True)
            and e.get('student_type') == 'trainee'
            and e.get('student_id') == trainee_id
            for e in raw_enrollments
        )
        if already_enrolled:
            flash(f'{trainee.name} is already enrolled in a class.', 'error')
            return redirect(url_for('trainee_profile', trainee_id=trainee_id))

        if not hasattr(game_state, 'active_enrollments') or game_state.active_enrollments is None:
            game_state.active_enrollments = []

        enrollment_id = str(uuid.uuid4())[:8]
        enrollment = {
            "id": enrollment_id,
            "student_type": "trainee",
            "student_id": trainee_id,
            "student_name": trainee.name,
            "class_id": training_class.id,
            "class_name": training_class.name,
            "class_icon": training_class.icon,
            "class_color": training_class.color,
            "weekly_cost": 0,
            "base_weekly_cost": training_class.base_weekly_cost,
            "duration_weeks": training_class.duration_weeks,
            "weeks_completed": 0,
            "is_active": True,
            "completed": False,
            "coach_name": getattr(trainee, 'last_coach_name', ''),
            "year_started": getattr(game_state.promotion, 'current_year', 1),
            "week_started": getattr(game_state.promotion, 'current_week', 0),
        }
        game_state.active_enrollments.append(enrollment)

        save_game_state(game_state)
        flash(f'{trainee.name} enrolled in {training_class.name}! '
              f'Completes in {training_class.duration_weeks} weeks.', 'success')
        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    eligible_classes = []
    for cls in get_classes_for_trainees() + get_classes_for_roster():
        if not cls.intended_for_trainees and trainee.level == TraineeLevel.NEW_RECRUIT:
            continue

        t_data = {
            "level_number": 1,
            "wrestler_level": "Trainee",
            "is_injured": False,
            "is_trainee": True,
            "current_training_id": None,
            "age": trainee.age,
            "strength": trainee.strength,
            "speed": trainee.speed,
            "technique": trainee.technique,
            "charisma": trainee.charisma,
            "stamina": trainee.stamina,
            "toughness": trainee.toughness,
            "mic_skills": trainee.mic_skills,
            "psychology": trainee.psychology,
            "work_ethic": trainee.work_ethic,
        }

        can_take = True
        reason = ""

        if cls.primary_stat:
            current_value = t_data.get(cls.primary_stat, 0)
            if current_value >= STAT_CEILING_FROM_TRAINING:
                can_take = False
                reason = f"Stat already at training ceiling ({STAT_CEILING_FROM_TRAINING})"

        if can_take:
            eligible_classes.append({
                "id": cls.id,
                "name": cls.name,
                "icon": cls.icon,
                "color": cls.color,
                "description": cls.description,
                "duration_weeks": cls.duration_weeks,
                "primary_stat": cls.primary_stat,
                "secondary_stats": cls.secondary_stats,
                "injury_risk": cls.base_injury_risk_percent,
                "difficulty": cls.difficulty.value,
                "difficulty_color": cls.get_difficulty_color(),
                "category": cls.category.value,
                "is_promo": cls.is_promo_class,
                "risk_summary": cls.get_risk_summary(),
            })

    raw_enrollments = getattr(game_state, 'active_enrollments', None) or []
    active_count = sum(1 for e in raw_enrollments if e.get('is_active', True))
    max_concurrent = school.get_max_concurrent_classes()
    school_full = active_count >= max_concurrent

    already_enrolled = any(
        e.get('is_active', True)
        and e.get('student_type') == 'trainee'
        and e.get('student_id') == trainee_id
        for e in raw_enrollments
    )

    return render_template('enroll_trainee_class.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary(),
        trainee=trainee,
        eligible_classes=eligible_classes,
        active_count=active_count,
        max_concurrent=max_concurrent,
        school_full=school_full,
        already_enrolled=already_enrolled,
        hide_base_hud=True,
    )


@app.route('/assign-trainee-coach/<path:trainee_id>', methods=['GET', 'POST'])
@require_login
@require_game
def assign_trainee_coach(trainee_id):
    """Assign a personal coach to a trainee."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if not trainee:
        flash('Trainee not found!', 'error')
        return redirect(url_for('view_trainees'))

    if trainee.status != TraineeStatus.ACTIVE:
        flash(f'{trainee.name} is {trainee.status.value} and cannot be assigned a coach.', 'error')
        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    coach_manager = game_state.coach_manager
    if not coach_manager:
        flash('No coach manager available!', 'error')
        return redirect(url_for('coach_management'))

    if request.method == 'POST':
        coach_id = request.form.get('coach_id', '').strip()

        if coach_id == 'unassign':
            if trainee.has_coach_assigned and trainee.coach_id:
                coach_manager.unassign_coach(trainee.coach_id)
            success, msg = trainee.unassign_coach()
            save_game_state(game_state)
            flash(msg, 'info' if success else 'warning')
            return redirect(url_for('trainee_profile', trainee_id=trainee_id))

        if not coach_id:
            flash('No coach selected.', 'error')
            return redirect(url_for('assign_trainee_coach', trainee_id=trainee_id))

        new_coach = coach_manager.get_coach(coach_id)
        if not new_coach:
            flash('Coach not found.', 'error')
            return redirect(url_for('assign_trainee_coach', trainee_id=trainee_id))

        if trainee.has_coach_assigned and trainee.coach_id:
            old_coach_id = trainee.coach_id
            coach_manager.unassign_coach(old_coach_id)
            trainee.unassign_coach()

        success, msg = coach_manager.assign_coach_to_trainee(
            coach_id=new_coach.id,
            trainee_id=trainee.id,
            trainee_name=trainee.name,
        )
        if not success:
            flash(f'Cannot assign coach: {msg}', 'error')
            return redirect(url_for('assign_trainee_coach', trainee_id=trainee_id))

        success2, msg2 = trainee.assign_coach(
            coach_id=new_coach.id,
            coach_name=new_coach.name,
        )
        if not success2:
            coach_manager.unassign_coach(new_coach.id)
            flash(f'Cannot assign coach: {msg2}', 'error')
            return redirect(url_for('assign_trainee_coach', trainee_id=trainee_id))

        save_game_state(game_state)
        flash(f'{new_coach.name} is now coaching {trainee.name}!', 'success')
        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    all_coaches = coach_manager.get_active_coaches()

    spec_focus_stats = []
    try:
        from classes.trainee import SPECIALIZATION_INFO
        spec_focus_stats = SPECIALIZATION_INFO.get(
            trainee.specialization, {}
        ).get("stat_focus", [])
    except Exception:
        pass

    coach_options = []
    current_coach_obj = None
    if trainee.has_coach_assigned and trainee.coach_id:
        current_coach_obj = coach_manager.get_coach(trainee.coach_id)

    for c in all_coaches:
        is_best_fit = False
        try:
            from classes.coach import SPECIALTY_INFO
            coach_focus = SPECIALTY_INFO.get(c.specialty, {}).get("stat_focus", [])
            if spec_focus_stats and any(s in coach_focus for s in spec_focus_stats):
                is_best_fit = True
        except Exception:
            pass

        is_current = (current_coach_obj is not None and c.id == current_coach_obj.id)
        is_available = (c.status == CoachStatus.AVAILABLE)
        is_busy_with_other = (c.status == CoachStatus.ASSIGNED and not is_current)

        coach_options.append({
            "id": c.id,
            "name": c.name,
            "type": c.coach_type.value,
            "type_icon": c.get_type_icon(),
            "type_color": c.get_type_color(),
            "specialty": c.specialty.value,
            "specialty_icon": c.get_specialty_icon(),
            "specialty_color": c.get_specialty_color(),
            "skill_rating": c.skill_rating,
            "skill_tier": c.get_skill_tier(),
            "weekly_cost": c.get_weekly_cost_with_school(school),
            "xp_bonus": c.xp_bonus_percent,
            "injury_reduction": c.injury_risk_reduction,
            "status": c.status.value,
            "status_color": c.get_status_color(),
            "is_current": is_current,
            "is_available": is_available,
            "is_busy_with_other": is_busy_with_other,
            "currently_coaching": c.assigned_trainee_name if c.status == CoachStatus.ASSIGNED else "",
            "is_best_fit": is_best_fit,
            "is_legendary": c.is_legendary or c.coach_type == CoachType.LEGEND,
        })

    def sort_key(c):
        if c["is_current"]:
            return (0, -c["skill_rating"])
        if c["is_best_fit"] and c["is_available"]:
            return (1, -c["skill_rating"])
        if c["is_available"]:
            return (2, -c["skill_rating"])
        return (3, -c["skill_rating"])
    coach_options.sort(key=sort_key)

    return render_template('assign_coach_picker.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary() if school.is_founded() else {},
        trainee=trainee,
        coach_options=coach_options,
        current_coach=current_coach_obj,
        has_coaches=len(coach_options) > 0,
        hide_base_hud=True,
    )


@app.route('/choose-trainee-specialization/<path:trainee_id>', methods=['GET', 'POST'])
@require_login
@require_game
def choose_trainee_specialization(trainee_id):
    """Set a trainee's wrestling specialization. Locked once chosen."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if not trainee:
        flash('Trainee not found!', 'error')
        return redirect(url_for('view_trainees'))

    if trainee.status != TraineeStatus.ACTIVE:
        flash(f'{trainee.name} is {trainee.status.value} and cannot choose a specialization.', 'error')
        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    already_specialized = trainee.specialization != TraineeSpecialization.UNDECIDED

    if request.method == 'POST':
        if already_specialized:
            flash(f'{trainee.name} is already committed to {trainee.specialization.value}. '
                  f'Specialization cannot be changed.', 'warning')
            return redirect(url_for('trainee_profile', trainee_id=trainee_id))

        spec_key = request.form.get('specialization', '').strip()
        if not spec_key:
            flash('No specialization selected.', 'error')
            return redirect(url_for('choose_trainee_specialization', trainee_id=trainee_id))

        chosen_spec = None
        for spec in TraineeSpecialization:
            if spec.value == spec_key or spec.name == spec_key:
                chosen_spec = spec
                break

        if not chosen_spec or chosen_spec == TraineeSpecialization.UNDECIDED:
            flash(f'Invalid specialization: {spec_key}', 'error')
            return redirect(url_for('choose_trainee_specialization', trainee_id=trainee_id))

        try:
            trainee.assign_specialization(chosen_spec)
            save_game_state(game_state)
            flash(f'{trainee.name} is now training as a {chosen_spec.value}! '
                  f'+5 to focus stats.', 'success')
        except Exception as e:
            flash(f'Specialization error: {e}', 'error')

        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    auto_suggested = None
    try:
        scores = {
            TraineeSpecialization.STRIKER: trainee.strength + trainee.stamina,
            TraineeSpecialization.TECHNICIAN: trainee.technique + trainee.psychology,
            TraineeSpecialization.HIGH_FLYER: trainee.speed + trainee.stamina,
            TraineeSpecialization.BRAWLER: trainee.toughness + trainee.strength,
            TraineeSpecialization.POWERHOUSE: trainee.strength + trainee.toughness,
            TraineeSpecialization.ALL_ROUNDER: (trainee.technique + trainee.speed + trainee.stamina) // 2,
            TraineeSpecialization.CHARACTER: trainee.charisma + trainee.mic_skills,
        }
        auto_suggested = max(scores, key=scores.get)
    except Exception:
        pass

    from classes.trainee import SPECIALIZATION_INFO
    spec_options = []
    for spec in TraineeSpecialization:
        if spec == TraineeSpecialization.UNDECIDED:
            continue
        info = SPECIALIZATION_INFO.get(spec, {})
        focus_stats = info.get("stat_focus", [])
        current_stats = {stat: getattr(trainee, stat, 0) for stat in focus_stats}

        spec_options.append({
            "key": spec.value,
            "name": spec.value,
            "icon": info.get("icon", "❓"),
            "description": info.get("description", ""),
            "focus_stats": focus_stats,
            "current_stats": current_stats,
            "is_suggested": (spec == auto_suggested),
        })

    return render_template('choose_specialization.html',
        promotion=game_state.promotion,
        school=school,
        trainee=trainee,
        spec_options=spec_options,
        auto_suggested_name=(auto_suggested.value if auto_suggested else None),
        already_specialized=already_specialized,
        current_specialization=trainee.specialization.value,
        hide_base_hud=True,
    )


@app.route('/edit-trainee-show/<path:show_id>', methods=['GET', 'POST'])
@require_login
@require_game
def edit_trainee_show(show_id):
    """Edit a scheduled trainee show's match card."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    tsm = game_state.trainee_show_manager
    if not tsm:
        flash('No trainee show manager!', 'error')
        return redirect(url_for('training_school'))

    show = tsm.get_show(show_id)
    if not show:
        flash('Show not found!', 'error')
        return redirect(url_for('book_trainee_show'))

    from classes.trainee_show import TraineeShowStatus, TraineeMatch, TRAINEE_SHOW_INFO

    if show.status == TraineeShowStatus.COMPLETED:
        flash('Cannot edit a completed show.', 'warning')
        return redirect(url_for('book_trainee_show'))

    if request.method == 'POST':
        action = request.form.get('action', '').strip()

        if action == 'remove_match':
            try:
                match_index = int(request.form.get('match_index', -1))
            except (ValueError, TypeError):
                match_index = -1
            if show.remove_match(match_index):
                save_game_state(game_state)
                flash('Match removed.', 'info')
            else:
                flash('Could not remove match.', 'error')
            return redirect(url_for('edit_trainee_show', show_id=show.id))

        elif action == 'add_match':
            match_type = request.form.get('match_type', 'Singles').strip()
            try:
                match_minutes = int(request.form.get('match_minutes', 6))
            except (ValueError, TypeError):
                match_minutes = 6

            participants_needed = {
                'Singles': 2,
                'Triple Threat': 3,
                'Tag Team': 4,
                'Battle Royal': 4,
            }.get(match_type, 2)

            if match_type == 'Battle Royal':
                try:
                    requested = int(request.form.get('battle_royal_size', 4))
                    participants_needed = max(4, min(8, requested))
                except (ValueError, TypeError):
                    participants_needed = 4

            trainee_ids = []
            trainee_names = []
            active_trainees = school.get_active_trainees()
            trainee_lookup = {t.id: t for t in active_trainees}

            for i in range(1, participants_needed + 1):
                tid = request.form.get(f'trainee{i}', '').strip()
                if not tid:
                    continue
                trainee = trainee_lookup.get(tid)
                if not trainee:
                    flash(f'Trainee #{i} not found.', 'error')
                    return redirect(url_for('edit_trainee_show', show_id=show.id))
                if not trainee.can_wrestle_in_trainee_show():
                    flash(f'{trainee.name} cannot wrestle yet (must be Beginner+ and Active).', 'error')
                    return redirect(url_for('edit_trainee_show', show_id=show.id))
                show_info = TRAINEE_SHOW_INFO.get(show.show_type, {})
                min_level_str = show_info.get('min_level_allowed', 'Beginner')
                level_order = ['New Recruit', 'Beginner', 'Intermediate', 'Advanced', 'Graduated']
                try:
                    if level_order.index(trainee.level.value) < level_order.index(min_level_str):
                        flash(f'{trainee.name} is below required level ({min_level_str}+).', 'error')
                        return redirect(url_for('edit_trainee_show', show_id=show.id))
                except ValueError:
                    pass
                max_minutes = trainee.get_max_match_minutes()
                if match_minutes > max_minutes and max_minutes > 0:
                    flash(f'{trainee.name} can only wrestle up to {max_minutes} min at their level.', 'error')
                    return redirect(url_for('edit_trainee_show', show_id=show.id))
                trainee_ids.append(trainee.id)
                trainee_names.append(trainee.name)

            if len(trainee_ids) < 2:
                flash(f'Need at least 2 trainees (got {len(trainee_ids)}).', 'error')
                return redirect(url_for('edit_trainee_show', show_id=show.id))

            if len(trainee_ids) != len(set(trainee_ids)):
                flash('Cannot add the same trainee twice in one match.', 'error')
                return redirect(url_for('edit_trainee_show', show_id=show.id))

            already_booked = set()
            for m in show.matches:
                already_booked.update(m.trainee_ids)
            conflicts = [n for tid, n in zip(trainee_ids, trainee_names) if tid in already_booked]
            if conflicts:
                flash(f'Already booked on this show: {", ".join(conflicts)}', 'error')
                return redirect(url_for('edit_trainee_show', show_id=show.id))

            show_info = TRAINEE_SHOW_INFO.get(show.show_type, {})
            min_min = show_info.get('min_match_minutes', 4)
            max_min = show_info.get('max_match_minutes', 12)
            match_minutes = max(min_min, min(max_min, match_minutes))

            new_match = TraineeMatch(
                match_index=len(show.matches),
                trainee_ids=trainee_ids,
                trainee_names=trainee_names,
                match_type=match_type,
                match_minutes=match_minutes,
            )
            success, msg = show.add_match(new_match)
            if success:
                save_game_state(game_state)
                flash(f'Added: {" vs ".join(trainee_names)} ({match_type}, {match_minutes}min)', 'success')
            else:
                flash(msg, 'error')
            return redirect(url_for('edit_trainee_show', show_id=show.id))

        else:
            flash('Unknown action.', 'error')
            return redirect(url_for('edit_trainee_show', show_id=show.id))

    summary = show.get_summary()
    show_info = TRAINEE_SHOW_INFO.get(show.show_type, {})

    active_trainees = school.get_active_trainees()
    min_level_str = show_info.get('min_level_allowed', 'Beginner')
    level_order = ['New Recruit', 'Beginner', 'Intermediate', 'Advanced', 'Graduated']
    try:
        min_level_idx = level_order.index(min_level_str)
    except ValueError:
        min_level_idx = 0

    available_trainees_list = []
    booked_in_card = set()
    for m in show.matches:
        booked_in_card.update(m.trainee_ids)

    for t in active_trainees:
        if not t.can_wrestle_in_trainee_show():
            continue
        try:
            if level_order.index(t.level.value) < min_level_idx:
                continue
        except ValueError:
            continue
        available_trainees_list.append({
            "id": t.id,
            "name": t.name,
            "level": t.level.value,
            "level_icon": t.get_level_icon(),
            "level_color": t.get_level_color(),
            "ovr": t.get_overall_rating(),
            "max_minutes": t.get_max_match_minutes(),
            "is_booked": t.id in booked_in_card,
        })

    available_trainees_list.sort(key=lambda x: (x["is_booked"], -x["ovr"]))

    match_type_options = [
        {"name": "Singles", "participants": 2, "icon": "🤼", "description": "1v1"},
        {"name": "Tag Team", "participants": 4, "icon": "🤝", "description": "2v2"},
        {"name": "Triple Threat", "participants": 3, "icon": "⚡", "description": "3-way"},
        {"name": "Battle Royal", "participants": 4, "icon": "👑", "description": "4-8 trainees over the top rope"},
    ]

    ready, ready_msg = show.is_ready_to_run()

    return render_template('edit_trainee_show.html',
        promotion=game_state.promotion,
        school=school,
        show=show,
        summary=summary,
        show_info=show_info,
        available_trainees=available_trainees_list,
        match_type_options=match_type_options,
        ready_to_run=ready,
        ready_message=ready_msg,
        max_matches=show_info.get('max_matches', 6),
        min_matches=show_info.get('min_matches', 2),
        min_match_minutes=show_info.get('min_match_minutes', 4),
        max_match_minutes=show_info.get('max_match_minutes', 12),
        hide_base_hud=True,
    )


@app.route('/run-trainee-show/<path:show_id>', methods=['POST'])
@require_login
@require_game
def run_trainee_show(show_id):
    """Run a scheduled trainee show — simulate, award XP, apply profit + reputation."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    tsm = game_state.trainee_show_manager
    if not tsm:
        flash('No trainee show manager!', 'error')
        return redirect(url_for('book_trainee_show'))

    show = tsm.get_show(show_id)
    if not show:
        flash('Show not found!', 'error')
        return redirect(url_for('book_trainee_show'))

    from classes.trainee_show import TraineeShowStatus

    if show.status == TraineeShowStatus.COMPLETED:
        flash('Show already completed.', 'warning')
        return redirect(url_for('book_trainee_show'))

    ready, ready_msg = show.is_ready_to_run()
    if not ready:
        flash(f'Cannot run show: {ready_msg}', 'error')
        return redirect(url_for('edit_trainee_show', show_id=show.id))

    active_trainees = school.get_active_trainees()
    school_speed_mult = school.get_training_speed_multiplier()

    try:
        result = tsm.run_show(
            show_id=show.id,
            active_trainees=active_trainees,
            school_reputation=school.reputation,
            school_tier_speed_mult=school_speed_mult,
        )
    except Exception as e:
        flash(f'Show execution error: {e}', 'error')
        return redirect(url_for('edit_trainee_show', show_id=show.id))

    if not result.get('success'):
        flash(f'Show failed: {result.get("message", "Unknown error")}', 'error')
        return redirect(url_for('edit_trainee_show', show_id=show.id))

    profit = result.get('profit', 0)
    rep_change = result.get('school_rep_change', 0)
    avg_rating = result.get('avg_rating', 0.0)
    attendance = result.get('attendance', 0)

    game_state.promotion.budget += profit
    school.modify_reputation(rep_change)

    try:
        school.record_trainee_show(attendance, avg_rating)
    except Exception:
        pass

    if hasattr(game_state, 'inbox') and game_state.inbox:
        try:
            level_ups = result.get('level_ups', [])
            level_up_text = ""
            if level_ups:
                level_up_text = "\n\n📈 LEVEL UPS:\n" + "\n".join(
                    f"• {lu['trainee_name']}: {lu['event'].get('old_level', '')} → {lu['event'].get('new_level', '')}"
                    for lu in level_ups
                )

            sellout_text = " (SELLOUT!)" if result.get('is_sellout') else ""
            rep_text = f"+{rep_change} rep" if rep_change > 0 else (f"{rep_change} rep" if rep_change < 0 else "no rep change")

            game_state.inbox.add_message(
                sender="Training School",
                subject=f"{show.name} — {avg_rating:.1f}⭐",
                body=(
                    f"Trainee show complete!\n\n"
                    f"⭐ Average Rating: {avg_rating:.2f}\n"
                    f"👥 Attendance: {attendance}/{show.venue_capacity}{sellout_text}\n"
                    f"💰 Profit: ${profit:,}\n"
                    f"📈 School Reputation: {rep_text}\n"
                    f"🎓 Total XP Awarded: {result.get('total_xp_awarded', 0):,}"
                    f"{level_up_text}"
                ),
                year=getattr(game_state.promotion, 'current_year', 1),
                month=getattr(game_state.promotion, 'current_month', 1),
                day=getattr(game_state.promotion, 'current_day', 1),
                message_type="general",
                icon="🎤",
            )
        except Exception:
            pass

    save_game_state(game_state)

    summary = show.get_summary()
    return render_template('trainee_show_results.html',
        promotion=game_state.promotion,
        school=school,
        show=show,
        summary=summary,
        result=result,
        level_ups=result.get('level_ups', []),
        hide_base_hud=True,
    )


@app.route('/cancel-trainee-show/<path:show_id>', methods=['POST'])
@require_login
@require_game
def cancel_trainee_show(show_id):
    """Cancel a scheduled trainee show — refunds the venue cost."""
    game_state = get_game_state()
    tsm = game_state.trainee_show_manager
    if not tsm:
        flash('No trainee show manager!', 'error')
        return redirect(url_for('book_trainee_show'))

    show = tsm.get_show(show_id)
    if not show:
        flash('Show not found!', 'error')
        return redirect(url_for('book_trainee_show'))

    from classes.trainee_show import TraineeShowStatus

    if show.status == TraineeShowStatus.COMPLETED:
        flash('Cannot cancel a completed show.', 'warning')
        return redirect(url_for('book_trainee_show'))

    show_name = show.name
    venue_refund = show.venue_cost

    try:
        success = tsm.cancel_show(show_id)
        if not success:
            flash('Could not cancel show.', 'error')
            return redirect(url_for('book_trainee_show'))

        game_state.promotion.budget += venue_refund

        if hasattr(game_state, 'inbox') and game_state.inbox:
            try:
                game_state.inbox.add_message(
                    sender="Training School",
                    subject=f"{show_name} cancelled",
                    body=(
                        f"You cancelled {show_name}.\n\n"
                        f"💰 Venue cost refunded: ${venue_refund:,}\n\n"
                        f"Trainees will need to wait for another show opportunity."
                    ),
                    year=getattr(game_state.promotion, 'current_year', 1),
                    month=getattr(game_state.promotion, 'current_month', 1),
                    day=getattr(game_state.promotion, 'current_day', 1),
                    message_type="general",
                    icon="❌",
                )
            except Exception:
                pass

        save_game_state(game_state)
        flash(f'{show_name} cancelled. ${venue_refund:,} venue cost refunded.', 'info')
    except Exception as e:
        flash(f'Cancellation error: {e}', 'error')

    return redirect(url_for('book_trainee_show'))


# ==================== UPGRADE / ALUMNI / TRAINEE SHOWS ====================

@app.route('/upgrade-school', methods=['GET'])
@require_login
@require_game
def upgrade_school():
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        return redirect(url_for('training_school'))
    summary = school.get_summary()
    next_tier_info = None
    upgrade_cost = 0
    try:
        if school.can_upgrade():
            next_tier = school.get_next_tier()
            if next_tier:
                next_tier_info = SCHOOL_TIER_INFO.get(next_tier, {})
                upgrade_cost = school.get_upgrade_cost()
    except Exception:
        pass
    return render_template('upgrade_school.html',
        promotion=game_state.promotion,
        school=school,
        summary=summary,
        next_tier_info=next_tier_info,
        upgrade_cost=upgrade_cost,
        hide_base_hud=True,
    )


@app.route('/start-school-upgrade', methods=['POST'])
@require_login
@require_game
def start_school_upgrade():
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded() and school.can_upgrade():
        try:
            cost = school.get_upgrade_cost()
            if game_state.promotion.budget >= cost:
                game_state.promotion.budget -= cost
                success, msg = school.start_upgrade()
                save_game_state(game_state)
                flash(msg, 'success' if success else 'error')
            else:
                flash(f'Need ${cost:,} to upgrade!', 'error')
        except Exception as e:
            flash(f'Upgrade error: {e}', 'error')
    return redirect(url_for('training_school'))


@app.route('/school-alumni')
@require_login
@require_game
def school_alumni():
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        return redirect(url_for('training_school'))
    return render_template('school_alumni.html',
        promotion=game_state.promotion,
        school=school,
        alumni_count=school.get_alumni_count() if hasattr(school, 'get_alumni_count') else 0,
        alumni=getattr(school, 'alumni', []),
        hide_base_hud=True,
    )


@app.route('/trainee-shows', methods=['GET', 'POST'])
@require_login
@require_game
def book_trainee_show():
    """Trainee Shows hub — list scheduled/completed + create new shows."""
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        return redirect(url_for('training_school'))

    tsm = game_state.trainee_show_manager
    if not tsm:
        from classes.trainee_show import TraineeShowManager
        tsm = TraineeShowManager()
        game_state.trainee_show_manager = tsm

    if request.method == 'POST':
        show_type_key = request.form.get('show_type', '').strip()
        show_name = request.form.get('show_name', '').strip()
        venue_name = request.form.get('venue_name', 'School Arena').strip()

        chosen_type = None
        for st in TraineeShowType:
            if st.name == show_type_key or st.value == show_type_key:
                chosen_type = st
                break

        if not chosen_type:
            flash(f'Invalid show type: {show_type_key}', 'error')
            return redirect(url_for('book_trainee_show'))

        if not show_name:
            flash('Show name is required.', 'error')
            return redirect(url_for('book_trainee_show'))

        try:
            venue_capacity = int(request.form.get('venue_capacity', 50))
            ticket_price = int(request.form.get('ticket_price', 5))
            venue_cost = int(request.form.get('venue_cost', 100))
            day = int(request.form.get('day', game_state.promotion.current_day))
            month = int(request.form.get('month', game_state.promotion.current_month))
        except (ValueError, TypeError):
            flash('Invalid numeric values in form.', 'error')
            return redirect(url_for('book_trainee_show'))

        from classes.trainee_show import TRAINEE_SHOW_INFO
        info = TRAINEE_SHOW_INFO.get(chosen_type, {})
        if not (info.get('min_capacity', 0) <= venue_capacity <= info.get('max_capacity', 9999)):
            flash(f'Capacity must be between {info.get("min_capacity")} and {info.get("max_capacity")}.', 'error')
            return redirect(url_for('book_trainee_show'))
        if not (info.get('ticket_price_range', [1, 100])[0] <= ticket_price <= info.get('ticket_price_range', [1, 100])[1]):
            flash('Ticket price out of range for this show type.', 'error')
            return redirect(url_for('book_trainee_show'))
        if not (info.get('venue_cost_range', [1, 9999])[0] <= venue_cost <= info.get('venue_cost_range', [1, 9999])[1]):
            flash('Venue cost out of range for this show type.', 'error')
            return redirect(url_for('book_trainee_show'))

        active_trainees = school.get_active_trainees()
        can_create, reason = tsm.can_create_show(
            chosen_type, school.tier.value, school.reputation, active_trainees
        )
        if not can_create:
            flash(f'Cannot create show: {reason}', 'error')
            return redirect(url_for('book_trainee_show'))

        if game_state.promotion.budget < venue_cost:
            flash(f'Cannot afford venue cost (${venue_cost:,}). Need ${venue_cost - game_state.promotion.budget:,} more.', 'error')
            return redirect(url_for('book_trainee_show'))

        try:
            show = tsm.create_show(
                show_type=chosen_type,
                name=show_name,
                venue_name=venue_name,
                venue_capacity=venue_capacity,
                ticket_price=ticket_price,
                venue_cost=venue_cost,
                week=getattr(game_state.promotion, 'current_week', 0),
                year=int(request.form.get('year', game_state.promotion.current_year)),
                day=day,
                month=month,
            )
            if not show:
                flash('Failed to create show.', 'error')
                return redirect(url_for('book_trainee_show'))

            game_state.promotion.budget -= venue_cost

            save_game_state(game_state)
            flash(f'{show.name} booked! Now go edit the match card.', 'success')
            return redirect(url_for('edit_trainee_show', show_id=show.id))
        except Exception as e:
            flash(f'Show creation error: {e}', 'error')
            return redirect(url_for('book_trainee_show'))

    scheduled_shows = []
    completed_shows = []
    lifetime_stats = {}
    show_type_options = []
    active_trainees = []

    try:
        if tsm:
            scheduled_shows = tsm.get_scheduled_shows()
            completed_shows = tsm.get_completed_shows()
            lifetime_stats = tsm.get_lifetime_stats()
        active_trainees = school.get_active_trainees()
        if tsm:
            show_type_options = tsm.get_show_type_options(
                school_tier_name=school.tier.value,
                school_reputation=school.reputation,
                active_trainees=active_trainees,
            )
    except Exception as e:
        print(f"book_trainee_show GET error: {e}")

    return render_template('trainee_show.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary(),
        scheduled_shows=scheduled_shows,
        completed_shows=completed_shows,
        lifetime_stats=lifetime_stats,
        show_type_options=show_type_options,
        active_trainee_count=len(active_trainees),
        hide_base_hud=True,
    )


# ==================== SETTINGS ====================
@app.route('/settings')
@require_login
@require_game
def settings_page():
    game_state = get_game_state()
    ai_info = None
    try:
        if game_state.ai_director:
            ai_info = game_state.get_ai_director_info()
    except Exception:
        pass
    has_school = False
    try:
        has_school = game_state.has_training_school()
    except Exception:
        pass
    return render_template('settings.html',
        promotion=game_state.promotion,
        ai_director_info=ai_info,
        has_training_school=has_school,
        hide_base_hud=True,
    )


# ==================== SAVE / QUIT ====================
@app.route('/save-game', methods=['POST'])
@require_login
@require_game
def save_game():
    game_state = get_game_state()
    save_name = request.form.get('save_name', game_state.promotion.name if game_state.promotion else 'Save')
    save_name = save_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    filepath = f"saves/{save_name}.json"
    if game_state.save_to_file(filepath):
        flash(f'Game saved as: {save_name}', 'success')
    else:
        flash('Failed to save game!', 'error')
    return redirect(url_for('dashboard'))


@app.route('/quit')
@require_login
def quit_game():
    session_id = session.get('session_id')
    if session_id and session_id in game_sessions:
        del game_sessions[session_id]
    session.clear()
    flash('Game closed. Logged out.', 'info')
    return redirect(url_for('login'))


# ==================== API ROUTES ====================
@app.route('/api/countries/<continent>')
def api_countries(continent):
    return jsonify(get_countries(continent))


@app.route('/api/cities/<continent>/<country>')
def api_cities(continent, country):
    return jsonify(get_cities(continent, country))


# ==================== RUN ====================
if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8080))
        debug = os.environ.get('FLASK_ENV') != 'production'
        print("\n" + "=" * 50, flush=True)
        print("🎬 THE BOOKING ROOM - WEB VERSION 2.1", flush=True)
        print("=" * 50, flush=True)
        print(f"Starting server on port {port}...", flush=True)
        print(f"Open browser to: http://127.0.0.1:{port}", flush=True)
        print("=" * 50 + "\n", flush=True)
        app.run(debug=debug, host='0.0.0.0', port=port)
    except Exception as e:
        import sys
        print("=" * 60, flush=True)
        print(f"❌ STARTUP CRASHED: {e}", flush=True)
        print("=" * 60, flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        raise
