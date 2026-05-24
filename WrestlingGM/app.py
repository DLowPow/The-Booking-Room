"""
The Booking Room - Flask Web Application
Wrestling GM Simulator with AI Director, Training School, Storylines,
Rival Promotions, Writers Room, 49 match types, iPhone UI
Version 2.0
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

# ==================== AI IMPORTS ====================
from ai.director import AIDirector, SimpleEvent
from ai.event_generator import EventGenerator, EventSeverity
from ai.voice import VoiceEngine, VoiceContext
from ai.personality import PersonalityType, CreativeControlLevel
from ai.rival_scheduler import RivalScheduler

# Living World is intentionally paused here.
# It will return later through Writers Room, News, and Post-Show systems.
# from ai.living_world import run_living_world_week

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

            try:
                rival_scheduler = ensure_rival_scheduler(game_state)
                if rival_scheduler:
                    rival_scheduler.complete_due_rival_shows(game_state)
            except Exception:
                pass

        flash(f'⏩ Skipped {weeks} weeks', 'success')

    elif action == 'set_level':
        target_level = int(request.form.get('level', 50))
        if progression:
            try:
                while progression.level < target_level:
                    progression.add_xp(10000, "Dev level jump")
                    if progression.level >= 100:
                        break
                flash(f'🚀 Jumped to Level {progression.level}', 'success')
            except Exception as e:
                flash(f'Level jump error: {e}', 'error')

    elif action == 'sign_rookies':
        if hasattr(game_state, 'free_agency') and game_state.free_agency:
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


def ensure_rival_scheduler(game_state):
    """Ensure RivalScheduler exists for new and old saves."""
    if not hasattr(game_state, "rival_scheduler") or game_state.rival_scheduler is None:
        try:
            game_state.rival_scheduler = RivalScheduler()
        except Exception as e:
            print(f"RivalScheduler init error: {e}")
            game_state.rival_scheduler = None

    return game_state.rival_scheduler


def format_money(amount, symbol="$"):
    if amount >= 0:
        return f"{symbol}{amount:,}"
    return f"-{symbol}{abs(amount):,}"


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
        events.append({
            "name": "Mania Weekend",
            "description": "Double XP and crowd boost!",
            "xp_multiplier": 2.0,
            "attendance_multiplier": 1.5,
            "fan_growth_multiplier": 2.0,
            "color": "#f59e0b",
            "icon": "🏟️",
        })

    if month == 8 and 24 <= day <= 31:
        events.append({
            "name": "SummerSlam Week",
            "description": "Bonus fan growth!",
            "xp_multiplier": 1.5,
            "attendance_multiplier": 1.3,
            "fan_growth_multiplier": 1.5,
            "color": "#ef4444",
            "icon": "☀️",
        })

    if month == 1 and 15 <= day <= 21:
        events.append({
            "name": "Rumble Season",
            "description": "Extra attendance boost!",
            "xp_multiplier": 1.3,
            "attendance_multiplier": 1.4,
            "fan_growth_multiplier": 1.3,
            "color": "#6366f1",
            "icon": "👑",
        })

    if month == 11 and 22 <= day <= 28:
        events.append({
            "name": "Survivor Series",
            "description": "War Games season!",
            "xp_multiplier": 1.4,
            "attendance_multiplier": 1.3,
            "fan_growth_multiplier": 1.4,
            "color": "#8b5cf6",
            "icon": "🏴",
        })

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
            categories[cat] = {
                "label": MATCH_CATEGORIES.get(cat, cat),
                "matches": [],
            }

        categories[cat]["matches"].append({
            "name": name,
            "info": info,
        })

    return categories


def get_display_for_match(match_data):
    match_type = match_data.get('match_type', 'Singles')
    info = get_match_type_info().get(match_type, {"type": "singles", "min": 2, "max": 2})
    fmt = info.get("type", "singles")
    teams = info.get("teams", None)

    if fmt == "singles":
        return f"{match_data.get('wrestler1', '?')} vs {match_data.get('wrestler2', '?')}"

    if fmt in ["tag", "handicap"] and teams:
        t1_size, t2_size = teams[0], teams[1]
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, t1_size + 1) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(t1_size + 1, t1_size + t2_size + 1) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"

    if fmt == "tag3":
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, 4) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(4, 7) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"

    if fmt == "tag4":
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, 5) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(5, 9) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"

    if fmt == "wargames":
        ts = teams[0] if teams else 3
        t1 = [match_data.get(f'wrestler{i}', '') for i in range(1, ts + 1) if match_data.get(f'wrestler{i}')]
        t2 = [match_data.get(f'wrestler{i}', '') for i in range(ts + 1, ts * 2 + 1) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(t1)} vs {' & '.join(t2)}"

    if fmt in ["multi", "variable", "rumble", "gauntlet", "referee"]:
        num = match_data.get('num_participants', info.get('min', 2))
        names = [
            match_data.get(f'wrestler{i}', '')
            for i in range(1, num + 1)
            if match_data.get(f'wrestler{i}')
        ]

        if len(names) <= 4:
            return " vs ".join(names)

        return f"{names[0]} vs {names[1]} + {len(names) - 2} others"

    names = [
        match_data.get(f'wrestler{i}', '')
        for i in range(1, 9)
        if match_data.get(f'wrestler{i}')
    ]

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
    """
    Process all weekly systems via the WeeklyPulse orchestrator.

    Living World is intentionally paused here.
    RivalScheduler is show/date based and will run from run_show/skip_week.
    """
    promotion = game_state.promotion
    progression = game_state.progression
    week = getattr(promotion, 'current_week', 0)
    year = getattr(promotion, 'current_year', 1)

    pulse_result = game_state.process_weekly_pulse(week, year)

    has_contracts = progression.level >= 31 if progression else False
    total_salaries = 0

    if has_contracts:
        total_salaries = sum(
            getattr(w, 'booking_fee', getattr(w, 'salary', 0))
            for w in promotion.roster
        )
        promotion.budget -= total_salaries

    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            game_state.championship_manager.weekly_update()
        except Exception as e:
            print(f"Championship weekly update error: {e}")

    if hasattr(game_state, 'banking') and game_state.banking:
        try:
            loan_result = game_state.banking.process_weekly_payments(promotion.budget)
            promotion.budget -= loan_result.get('total_deducted', 0)

            if hasattr(game_state, 'inbox') and game_state.inbox:
                for msg in loan_result.get('messages', []):
                    try:
                        game_state.inbox.add_message(
                            sender="Banking",
                            subject="Loan Payment",
                            body=msg,
                            year=year,
                            month=getattr(promotion, 'current_month', 1),
                            day=getattr(promotion, 'current_day', 1),
                            message_type="financial",
                            icon="🏦",
                        )
                    except Exception as e:
                        print(f"Banking inbox message error: {e}")

        except Exception as e:
            print(f"Banking weekly update error: {e}")

    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            game_state.calls.process_weekly_aging()
        except Exception as e:
            print(f"Calls weekly aging error: {e}")

    if progression:
        try:
            progression.process_weekly_update(
                active_wrestlers=len([
                    w for w in promotion.roster
                    if not getattr(w, 'is_injured', False)
                ]),
                total_fans=promotion.fan_base,
                current_budget=promotion.budget,
                weekly_profit=-total_salaries,
                roster_size=len(promotion.roster),
            )
        except Exception as e:
            print(f"Progression weekly update error: {e}")

    try:
        enrollment_result = process_class_enrollments_weekly(game_state)
        if isinstance(pulse_result, dict):
            pulse_result['enrollments'] = enrollment_result
    except Exception as e:
        print(f"Enrollment processing error: {e}")

    return pulse_result, total_salaries


# ==================== CLASS ENROLLMENT WEEKLY PROCESSOR ====================

def process_class_enrollments_weekly(game_state) -> dict:
    """
    Tick all active training class enrollments by 1 week.

    For each active enrollment:
    - Wrestlers: deducts weekly_cost from budget.
    - Trainees: train free through the school.
    - Advances weeks_completed.
    - On final week: rolls performance and applies stat gains.
    """
    enrollments = getattr(game_state, 'active_enrollments', None) or []

    if not enrollments:
        return {
            "completed": [],
            "advanced": [],
            "cancelled": [],
            "total_cost": 0,
        }

    promotion = game_state.promotion
    school = game_state.training_school

    completed = []
    advanced = []
    cancelled = []
    total_cost_this_week = 0

    for enr in enrollments:
        if not enr.get('is_active', True):
            continue

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
                            body=(
                                f"{enr.get('student_name')} was pulled from "
                                f"{enr.get('class_name')} — insufficient funds to "
                                f"cover the weekly cost of ${cost:,}."
                            ),
                            year=getattr(promotion, 'current_year', 1),
                            month=getattr(promotion, 'current_month', 1),
                            day=getattr(promotion, 'current_day', 1),
                            message_type="financial",
                            icon="⚠️",
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
                try:
                    student = school.get_trainee(enr.get('student_id'))
                except Exception:
                    student = None

            if not student:
                continue

            student_data = {}

            for stat in [
                "strength",
                "speed",
                "technique",
                "charisma",
                "stamina",
                "toughness",
                "mic_skills",
                "psychology",
                "work_ethic",
            ]:
                student_data[stat] = getattr(student, stat, 50)

            student_data["age"] = getattr(student, 'age', 30)

            try:
                performance = roll_performance(student_data, training_class)
                raw_gains = calculate_stat_gains(training_class, performance)
                actual_gains = apply_stat_gains_with_ceiling(student_data, raw_gains)

                for stat, gain in actual_gains.items():
                    if hasattr(student, stat) and gain > 0:
                        current = getattr(student, stat)
                        setattr(
                            student,
                            stat,
                            min(STAT_CEILING_FROM_TRAINING, current + gain),
                        )

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
                            body=(
                                f"Performance: {performance.value}\n"
                                f"Gains: {gain_text}"
                            ),
                            year=getattr(promotion, 'current_year', 1),
                            month=getattr(promotion, 'current_month', 1),
                            day=getattr(promotion, 'current_day', 1),
                            message_type="general",
                            icon="🎓",
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

            if game_state.promotion and promotion_initials:
                game_state.promotion.set_initials(promotion_initials)

        except Exception as e:
            print(f"Game init error using fallback: {e}")
            traceback.print_exc()

            promotion = Promotion(
                name=promotion_name,
                philosophy=phil_enum,
                owner_name=promoter_name,
                starting_budget=0,
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
            game_state.calendar_system = game_state.calendar
            game_state.inbox = InboxManager()
            game_state.calls = CallsManager()
            game_state.injury_manager = InjuryManager()
            game_state.banking = BankingManager()
            game_state.training_school = TrainingSchool()
            game_state.coach_manager = CoachManager()
            game_state.coach_pool = CoachPool()
            game_state.trainee_pool = TraineePool()
            game_state.trainee_show_manager = TraineeShowManager()
            game_state.group_manager = GroupManager()
            game_state.active_enrollments = []

            try:
                game_state.free_agency = FreeAgencyManager()
            except Exception:
                game_state.free_agency = None

            try:
                agents = generate_free_agents(count=50, level=1)
                game_state.free_agents = agents
            except Exception:
                game_state.free_agents = []

        try:
            game_state.promotion.prestige = profile.prestige_start
            game_state.promotion.merchandise_modifier = profile.merchandise_modifier
        except Exception:
            pass

        game_state.game_settings = {
            "continent": continent,
            "country": country,
            "city": city,
            "currency_code": currency_code,
            "currency_symbol": currency_symbol,
            "creative_control_enabled": creative_control,
            "creative_control_difficulty": cc_difficulty,
            "show_day": "Saturday",
        }

        game_state.origin_story = {
            "sender": profile.origin_sender,
            "subject": profile.origin_subject,
            "message": profile.origin_message,
            "grant": profile.starting_grant,
            "delivered": False,
            "accepted": False,
        }

        if game_state.inbox:
            try:
                game_state.inbox.add_message(
                    sender=profile.origin_sender,
                    subject=profile.origin_subject,
                    body=profile.origin_message,
                    year=1,
                    month=1,
                    day=1,
                    message_type="general",
                    icon="💰",
                )
            except Exception:
                pass

        game_state.show_tutorial_prompt = True
        game_state.tutorial_active = False
        game_state.tutorial_step = 0
        game_state.first_launch = True

        ensure_rival_scheduler(game_state)

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

    return render_template(
        'setup.html',
        continents=continents,
        philosophies=philosophies,
    )


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
            if hasattr(game_state, 'ensure_all_systems'):
                try:
                    game_state.ensure_all_systems()
                except Exception:
                    pass

            ensure_rival_scheduler(game_state)

            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            game_sessions[session_id] = game_state

            promo_name = game_state.promotion.name if game_state.promotion else "Unknown"
            flash(f'Loaded: {promo_name}', 'success')
            return redirect(url_for('dashboard'))

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
    promotion = game_state.promotion
    progression = game_state.progression

    try:
        ensure_rival_scheduler(game_state)
    except Exception:
        pass

    origin_message = None
    if hasattr(game_state, 'origin_story') and game_state.origin_story:
        if not game_state.origin_story.get('accepted', False):
            origin_message = game_state.origin_story

    show_tutorial_prompt = False
    if hasattr(game_state, 'show_tutorial_prompt') and game_state.show_tutorial_prompt:
        if not origin_message:
            show_tutorial_prompt = True

    tutorial_active = getattr(game_state, 'tutorial_active', False)
    tutorial_step = getattr(game_state, 'tutorial_step', 0)

    if progression:
        level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
        tier = get_promotion_tier(level)
        limits = get_cumulative_limits(level)
        tier_name = get_tier_name(tier)
    else:
        level = 1
        xp_into = 0
        xp_needed = 100
        percentage = 0
        tier = 1
        limits = get_cumulative_limits(1)
        tier_name = get_tier_name(1)

    unread_count = 0
    incoming_calls = 0

    try:
        if game_state.inbox:
            unread_count = game_state.inbox.get_unread_count()
    except Exception:
        unread_count = 0

    try:
        if game_state.calls:
            incoming_calls = game_state.calls.get_incoming_count()
    except Exception:
        incoming_calls = 0

    current_events = get_active_seasonal_events(
        getattr(promotion, 'current_month', 1),
        getattr(promotion, 'current_day', 1),
    )

    recent_show = getattr(game_state, 'last_show_result', None)

    return render_template(
        'dashboard.html',
        promotion=promotion,
        progression=progression,
        level=level,
        xp_into=xp_into,
        xp_needed=xp_needed,
        xp_percentage=percentage,
        tier=tier,
        tier_name=tier_name,
        limits=limits,
        unread_count=unread_count,
        incoming_calls=incoming_calls,
        current_events=current_events,
        recent_show=recent_show,
        origin_message=origin_message,
        show_tutorial_prompt=show_tutorial_prompt,
        tutorial_active=tutorial_active,
        tutorial_step=tutorial_step,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
    )


@app.route('/accept-origin-grant', methods=['POST'])
@require_login
@require_game
def accept_origin_grant():
    game_state = get_game_state()

    if not hasattr(game_state, 'origin_story') or not game_state.origin_story:
        flash('No grant available.', 'error')
        return redirect(url_for('dashboard'))

    if game_state.origin_story.get('accepted', False):
        flash('Grant already accepted.', 'warning')
        return redirect(url_for('dashboard'))

    grant = int(game_state.origin_story.get('grant', 0))

    game_state.promotion.budget += grant
    game_state.origin_story['accepted'] = True
    game_state.origin_grant_accepted = True
    game_state.origin_grant_amount = grant

    save_game_state(game_state)

    flash(f'Grant accepted: ${grant:,}', 'success')
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

    flash('Tutorial started.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/skip-tutorial', methods=['POST'])
@require_login
@require_game
def skip_tutorial():
    game_state = get_game_state()

    game_state.show_tutorial_prompt = False
    game_state.tutorial_active = False
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


# ==================== MAIN HUBS ====================

@app.route('/booking-room')
@require_login
@require_game
def booking_room():
    game_state = get_game_state()

    return render_template(
        'booking_room.html',
        promotion=game_state.promotion,
        booked_show=getattr(game_state, 'booked_show', None),
        last_show_result=getattr(game_state, 'last_show_result', None),
        hide_base_hud=True,
    )


@app.route('/locker-room')
@require_login
@require_game
def locker_room():
    game_state = get_game_state()

    return render_template(
        'locker_room.html',
        promotion=game_state.promotion,
        hide_base_hud=True,
    )


@app.route('/writers-room')
@require_login
@require_game
def writers_room():
    game_state = get_game_state()

    rival_show_preview = None
    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler:
            rival_show_preview = rival_scheduler.get_next_rival_show_preview()
    except Exception:
        pass

    return render_template(
        'writers_room.html',
        promotion=game_state.promotion,
        rival_show_preview=rival_show_preview,
        hide_base_hud=True,
    )


@app.route('/trophy-case')
@require_login
@require_game
def trophy_case():
    game_state = get_game_state()

    return render_template(
        'trophy_case.html',
        promotion=game_state.promotion,
        championship_manager=game_state.championship_manager,
        hide_base_hud=True,
    )


@app.route('/news')
@require_login
@require_game
def news():
    game_state = get_game_state()

    news_items = []

    try:
        if hasattr(game_state, 'news_items'):
            news_items = game_state.news_items
    except Exception:
        news_items = []

    return render_template(
        'news.html',
        promotion=game_state.promotion,
        news_items=news_items,
        hide_base_hud=True,
    )


# ==================== CALENDAR ====================

@app.route('/calendar')
@require_login
@require_game
def calendar():
    game_state = get_game_state()
    promotion = game_state.promotion

    calendar_system = getattr(game_state, 'calendar', None)
    if not calendar_system:
        calendar_system = getattr(game_state, 'calendar_system', None)

    events = []

    try:
        if calendar_system and hasattr(calendar_system, 'get_month_events'):
            events = calendar_system.get_month_events(
                promotion.current_year,
                promotion.current_month,
            )
        elif calendar_system and hasattr(calendar_system, 'events'):
            events = [
                e for e in calendar_system.events
                if getattr(e, 'year', None) == promotion.current_year
                and getattr(e, 'month', None) == promotion.current_month
            ]
    except Exception:
        events = []

    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler and hasattr(rival_scheduler, 'get_calendar_events'):
            rival_events = rival_scheduler.get_calendar_events(
                promotion.current_year,
                promotion.current_month,
            )
            events.extend(rival_events or [])
    except Exception:
        pass

    return render_template(
        'calendar.html',
        promotion=promotion,
        calendar=calendar_system,
        events=events,
        months=MONTHS,
        current_year=promotion.current_year,
        current_month=promotion.current_month,
        current_day=promotion.current_day,
        days_in_month=days_in_month(promotion.current_month),
        hide_base_hud=True,
    )

@app.route('/calendar-view')
@require_login
@require_game
def calendar_view():
    return calendar()


# ==================== ROSTER ====================

@app.route('/roster')
@require_login
@require_game
def roster():
    game_state = get_game_state()
    progression = game_state.progression

    limits = get_cumulative_limits(progression.level if progression else 1)

    sorted_roster = sorted(
        game_state.promotion.roster,
        key=lambda w: getattr(w, 'popularity', 0),
        reverse=True,
    )

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    total_salary = sum(
        getattr(w, 'booking_fee', getattr(w, 'salary', 0))
        for w in game_state.promotion.roster
    )

    return render_template(
        'roster.html',
        wrestlers=sorted_roster,
        roster_limit=limits.get("roster_limit", 5),
        currency=currency,
        total_salary=total_salary,
    )


@app.route('/wrestler/<path:wrestler_name>')
@require_login
@require_game
def wrestler_detail(wrestler_name):
    game_state = get_game_state()

    wrestler = next(
        (w for w in game_state.promotion.roster if w.name == wrestler_name),
        None,
    )

    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('roster'))

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    return render_template(
        'wrestler_detail.html',
        wrestler=wrestler,
        currency=currency,
        promotion=game_state.promotion,
    )


@app.route('/release-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def release_wrestler(wrestler_name):
    game_state = get_game_state()

    wrestler = next(
        (w for w in game_state.promotion.roster if w.name == wrestler_name),
        None,
    )

    if not wrestler:
        flash('Wrestler not found.', 'error')
        return redirect(url_for('roster'))

    booking_fee = getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0))
    contract_length = getattr(wrestler, 'contract_length', 0)
    buyout = int(booking_fee * contract_length * 0.5)

    game_state.promotion.budget -= buyout
    game_state.promotion.roster.remove(wrestler)

    wrestler.is_signed = False
    wrestler.contract_length = 0

    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        try:
            week = getattr(game_state.promotion, 'current_week', 0)
            year = getattr(game_state.promotion, 'current_year', 1)

            if hasattr(wrestler, 'become_indy_god'):
                wrestler.become_indy_god()

            game_state.free_agency.add_released_wrestler(wrestler, week, year)

        except Exception:
            game_state.free_agents.append(wrestler)
    else:
        game_state.free_agents.append(wrestler)

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


# ==================== TAG TEAMS / FACTIONS ====================

@app.route('/groups')
@require_login
@require_game
def groups():
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        game_state.group_manager = GroupManager()
        save_game_state(game_state)

    gm = game_state.group_manager

    tag_teams = gm.get_tag_teams()
    trios = gm.get_trios()
    factions = gm.get_factions()

    disbanded = [g for g in gm.groups if not g.is_active]
    disbanded.sort(
        key=lambda g: (g.disbanded_year, g.disbanded_week),
        reverse=True,
    )

    counts = gm.get_count_by_type()
    roster_names = {w.name for w in promotion.roster} if promotion else set()

    return render_template(
        'groups.html',
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
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        game_state.group_manager = GroupManager()

    gm = game_state.group_manager

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        leader_id = request.form.get('leader_id', '').strip()
        description = request.form.get('description', '').strip()
        icon = request.form.get('icon', '').strip()
        color = request.form.get('color', '').strip()

        member_names = request.form.getlist('members')

        if not member_names:
            for i in range(1, MAX_GROUP_SIZE + 1):
                member = request.form.get(f'member{i}', '').strip()
                if member:
                    member_names.append(member)

        member_names = [m.strip() for m in member_names if m.strip()]

        seen = set()
        deduped = []

        for member in member_names:
            if member not in seen:
                seen.add(member)
                deduped.append(member)

        member_names = deduped

        roster_names = {w.name for w in promotion.roster}
        invalid = [m for m in member_names if m not in roster_names]

        if invalid:
            flash(f'Not on your roster: {", ".join(invalid)}', 'error')
            return redirect(url_for('groups'))

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

            if hasattr(game_state, 'inbox') and game_state.inbox and group:
                try:
                    type_label = group.get_type_label()
                    game_state.inbox.add_message(
                        sender="Locker Room",
                        subject=f"New {type_label}: {group.name}",
                        body=(
                            f"{group.name} has officially formed.\n\n"
                            f"Members: {', '.join(group.member_names)}"
                        ),
                        year=getattr(promotion, 'current_year', 1),
                        month=getattr(promotion, 'current_month', 1),
                        day=getattr(promotion, 'current_day', 1),
                        message_type="general",
                        icon=group.icon or "🤝",
                    )
                except Exception:
                    pass
        else:
            flash(msg, 'error')

        return redirect(url_for('groups'))

    return redirect(url_for('groups'))


@app.route('/disband-group/<group_id>', methods=['POST'])
@require_login
@require_game
def disband_group(group_id):
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.group_manager:
        flash('Group system not available.', 'error')
        return redirect(url_for('groups'))

    success, msg = game_state.group_manager.disband_group(
        group_id=group_id,
        week=getattr(promotion, 'current_week', 0),
        year=getattr(promotion, 'current_year', 1),
    )

    flash(msg, 'success' if success else 'error')
    save_game_state(game_state)

    return redirect(url_for('groups'))


@app.route('/groups/<group_id>')
@require_login
@require_game
def group_detail(group_id):
    game_state = get_game_state()

    if not game_state.group_manager:
        flash('Group system not available.', 'error')
        return redirect(url_for('groups'))

    group = game_state.group_manager.get_group(group_id)

    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups'))

    roster_lookup = {
        w.name: w
        for w in game_state.promotion.roster
    }

    return render_template(
        'group_detail.html',
        promotion=game_state.promotion,
        group=group,
        roster_lookup=roster_lookup,
        hide_base_hud=True,
    )


# ==================== FREE AGENCY ====================

@app.route('/free-agents')
@require_login
@require_game
def free_agents():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    limits = get_cumulative_limits(progression.level if progression else 1)
    roster_limit = limits.get("roster_limit", 5)
    current_roster = len(promotion.roster)
    can_sign = current_roster < roster_limit

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    player_level = progression.level if progression else 1
    budget = promotion.budget

    if player_level <= 5:
        allowed_tiers = [FreeAgentTier.ROOKIE]
    elif player_level <= 15:
        allowed_tiers = [FreeAgentTier.ROOKIE, FreeAgentTier.PROSPECT]
    elif player_level <= 30:
        allowed_tiers = [FreeAgentTier.ROOKIE, FreeAgentTier.PROSPECT, FreeAgentTier.RISING]
    elif player_level <= 50:
        allowed_tiers = [
            FreeAgentTier.ROOKIE,
            FreeAgentTier.PROSPECT,
            FreeAgentTier.RISING,
            FreeAgentTier.PROVEN,
        ]
    elif player_level <= 75:
        allowed_tiers = [
            FreeAgentTier.ROOKIE,
            FreeAgentTier.PROSPECT,
            FreeAgentTier.RISING,
            FreeAgentTier.PROVEN,
            FreeAgentTier.ELITE,
        ]
    else:
        allowed_tiers = [
            FreeAgentTier.ROOKIE,
            FreeAgentTier.PROSPECT,
            FreeAgentTier.RISING,
            FreeAgentTier.PROVEN,
            FreeAgentTier.ELITE,
            FreeAgentTier.INDY_GOD,
        ]

    week_key = f"{promotion.current_year}-{promotion.current_week}"

    needs_refresh = (
        not hasattr(game_state, 'weekly_agent_names')
        or not game_state.weekly_agent_names
        or getattr(game_state, 'weekly_agents_week', '') != week_key
    )

    all_listings = []

    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        try:
            all_listings = game_state.free_agency.get_all_listings()
        except Exception:
            all_listings = []

    if not all_listings:
        fallback_agents = getattr(game_state, 'free_agents', []) or []

        all_listings = []
        for wrestler in fallback_agents:
            try:
                all_listings.append({
                    "wrestler": wrestler,
                    "tier": FreeAgentTier.ROOKIE,
                    "asking_per_show": getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 100)),
                    "signing_bonus": 0,
                    "is_exclusive_offer": False,
                    "weeks_until_expires": 0,
                    "description": "",
                })
            except Exception:
                pass

    eligible_listings = []

    for listing in all_listings:
        try:
            tier = listing.tier if hasattr(listing, 'tier') else listing.get('tier', FreeAgentTier.ROOKIE)

            if tier not in allowed_tiers:
                continue

            cost = (
                listing.signing_bonus
                if getattr(listing, 'is_exclusive_offer', False)
                else listing.asking_per_show
            ) if not isinstance(listing, dict) else (
                listing.get('signing_bonus', 0)
                if listing.get('is_exclusive_offer', False)
                else listing.get('asking_per_show', 100)
            )

            if cost > budget * 2 and cost > 500:
                continue

            eligible_listings.append(listing)

        except Exception:
            continue

    if needs_refresh:
        sample_size = min(10, len(eligible_listings))
        sampled = random.sample(eligible_listings, sample_size) if eligible_listings else []

        names = []

        for listing in sampled:
            if isinstance(listing, dict):
                names.append(listing["wrestler"].name)
            else:
                names.append(listing.wrestler.name)

        game_state.weekly_agent_names = names
        game_state.weekly_agents_week = week_key
        save_game_state(game_state)

    weekly_names = set(getattr(game_state, 'weekly_agent_names', []))

    visible_listings = []

    for listing in eligible_listings:
        try:
            wrestler = listing["wrestler"] if isinstance(listing, dict) else listing.wrestler
            if wrestler.name in weekly_names:
                visible_listings.append(listing)
        except Exception:
            pass

    agents_with_salary = []

    for listing in visible_listings:
        try:
            if isinstance(listing, dict):
                wrestler = listing["wrestler"]
                tier = listing.get("tier", FreeAgentTier.ROOKIE)
                asking = listing.get("asking_per_show", getattr(wrestler, 'booking_fee', 100))
                signing_bonus = listing.get("signing_bonus", 0)
                is_exclusive = listing.get("is_exclusive_offer", False)
                expires = listing.get("weeks_until_expires", 0)
                description = listing.get("description", "")
            else:
                wrestler = listing.wrestler
                tier = listing.tier
                asking = listing.asking_per_show
                signing_bonus = listing.signing_bonus
                is_exclusive = getattr(listing, 'is_exclusive_offer', False)
                expires = getattr(listing, 'weeks_until_expires', 0)
                description = getattr(listing, 'description', '')

            agents_with_salary.append({
                "wrestler": wrestler,
                "asking_salary": asking,
                "signing_bonus": signing_bonus,
                "per_show_rate": asking,
                "tier": tier.value if hasattr(tier, 'value') else str(tier),
                "tier_name": tier.value if hasattr(tier, 'value') else str(tier),
                "is_exclusive_offer": is_exclusive,
                "weeks_until_expires": expires,
                "description": description,
            })

        except Exception:
            continue

    return render_template(
        'free_agents.html',
        agents=agents_with_salary,
        free_agents=agents_with_salary,
        can_sign=can_sign,
        roster_limit=roster_limit,
        current_roster=current_roster,
        currency=currency,
        player_level=player_level,
        budget=budget,
        hide_base_hud=True,
    )


@app.route('/sign-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def sign_wrestler(wrestler_name):
    return sign_free_agent(wrestler_name)


@app.route('/sign-free-agent/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def sign_free_agent(wrestler_name):
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    limits = get_cumulative_limits(progression.level if progression else 1)
    roster_limit = limits.get("roster_limit", 5)

    if len(promotion.roster) >= roster_limit:
        flash('Roster limit reached!', 'error')
        return redirect(url_for('free_agents'))

    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        try:
            success, message, wrestler, cost = game_state.free_agency.sign_wrestler(
                wrestler_name,
                promotion.budget,
                len(promotion.roster),
                roster_limit,
            )

            if success and wrestler:
                promotion.budget -= cost
                promotion.roster.append(wrestler)

                try:
                    progression.add_xp(100, "Signed a wrestler")
                    progression.update_stat("wrestlers_signed_total")
                except Exception:
                    pass

                save_game_state(game_state)
                flash(message, 'success')
            else:
                flash(f'Cannot sign: {message}', 'error')

            return redirect(url_for('free_agents'))

        except Exception as e:
            flash(f'Signing error: {e}', 'error')

    wrestler = next(
        (w for w in (game_state.free_agents or []) if w.name == wrestler_name),
        None,
    )

    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('free_agents'))

    ovr = getattr(wrestler, 'overall_rating', 50)
    pop = getattr(wrestler, 'popularity', 30)

    per_show_rate = 50 + int(ovr * 1.3) + int(pop * 0.5)
    per_show_rate = max(50, min(per_show_rate, 500))

    if promotion.budget < per_show_rate:
        flash('Not enough money to hire this wrestler.', 'error')
        return redirect(url_for('free_agents'))

    promotion.budget -= per_show_rate

    if hasattr(wrestler, 'booking_fee'):
        wrestler.booking_fee = per_show_rate
    elif hasattr(wrestler, 'salary'):
        wrestler.salary = per_show_rate

    wrestler.contract_length = 52
    wrestler.is_signed = True

    if hasattr(wrestler, 'adjust_morale'):
        wrestler.adjust_morale(15)

    promotion.roster.append(wrestler)

    try:
        game_state.free_agents.remove(wrestler)
    except Exception:
        pass

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

    level = progression.level if progression else 1
    limits = get_cumulative_limits(level)
    max_tier = limits.get("venue_tier_max", 1)
    max_matches = limits.get("max_matches", 3)

    continent = getattr(game_state, 'game_settings', {}).get("continent", "North America")

    if limits.get("can_tour_international", False):
        all_venues = get_all_venues()
    else:
        all_venues = get_venues_by_continent(continent)

    venues = [
        v for v in all_venues
        if getattr(v.tier, 'value', 1) <= max_tier and getattr(v, 'is_unlocked', True)
    ]
    venues.sort(key=lambda v: getattr(v, 'capacity', 0))

    show_all_venues = request.args.get('show_all', '0') == '1'
    hidden_venue_count = len([
        v for v in all_venues
        if getattr(v.tier, 'value', 1) > max_tier
    ])

    available = [
        w for w in promotion.roster
        if not getattr(w, 'is_injured', False)
    ]

    match_types = get_unlocked_match_types(level)
    match_categories = get_match_categories()

    current_card = session.get('current_card', [])
    current_venue_id = session.get('current_venue_id')
    show_date = session.get('show_date', None)

    if not show_date:
        show_date = {
            'year': promotion.current_year,
            'month': promotion.current_month,
            'day': promotion.current_day,
        }
        session['show_date'] = show_date

    current_venue = None
    if current_venue_id:
        venue = get_venue_by_id(current_venue_id)
        if venue:
            current_venue = venue
        else:
            for v in venues:
                if getattr(v, 'id', None) == current_venue_id:
                    current_venue = v
                    break

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    show_day_name = get_day_name(
        get_day_of_week(show_date['year'], show_date['month'], show_date['day'])
    )

    venue_day_mod = DEFAULT_DAY_MODIFIERS.get(
        show_day_name,
        {"label": "", "modifier": 1.0}
    )

    championships = []
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            for champ in game_state.championship_manager.get_active_championships():
                championships.append({
                    'name': champ.name,
                    'current_champion': champ.current_champion,
                    'current_champion_tag_partner': getattr(champ, 'current_champion_tag_partner', ''),
                    'is_tag_title': getattr(champ, 'is_tag_title', False) or getattr(champ.level, 'value', '') == 'Tag Team Championship',
                    'rules': champ.rules.value if hasattr(champ.rules, 'value') else str(champ.rules),
                    'gender': champ.gender.value if hasattr(champ.gender, 'value') else str(champ.gender),
                    'level': champ.level.value if hasattr(champ.level, 'value') else str(champ.level),
                })
        except Exception:
            pass

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None

    selected_production = session.get('show_production', {})
    production_options = {}
    production_cost = 0
    production_quality = 1.0
    production_fans = 0

    try:
        production_options = get_available_options(level)
    except Exception:
        production_options = {}

    for option_id in selected_production.values():
        option = ALL_PRODUCTION_OPTIONS.get(option_id)
        if option:
            production_cost += option.cost
            production_quality += getattr(option, 'quality_modifier', 0)
            production_fans += getattr(option, 'fan_bonus', 0)

    total_show_time = get_card_total_time(current_card)

    if current_venue:
        available_minutes = getattr(current_venue, 'time_limit_minutes', 120)
        estimated_venue_cost = getattr(current_venue, 'cost', getattr(current_venue, 'rental_cost', 0))
    else:
        available_minutes = 120
        estimated_venue_cost = 0

    venue_available_time = available_minutes
    venue_time_limit = available_minutes
    time_remaining = available_minutes - total_show_time
    is_overrunning = total_show_time > available_minutes
    minutes_over = max(0, total_show_time - available_minutes)

    overrun_fine = calculate_overrun_penalty(minutes_over) if minutes_over > 0 else 0
    overrun_penalty = overrun_fine

    if minutes_over > 0:
        overrun_message = f"Over time by {minutes_over} minutes"
    else:
        overrun_message = ""

    estimated_salary_cost = 0
    booked_names = set()

    for match in current_card:
        for i in range(1, 31):
            name = match.get(f'wrestler{i}')
            if name:
                booked_names.add(name)

    for wrestler in promotion.roster:
        if wrestler.name in booked_names:
            estimated_salary_cost += getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0))

    estimated_production_cost = production_cost
    estimated_total_cost = estimated_venue_cost + estimated_salary_cost + estimated_production_cost + overrun_fine

    estimated_attendance = 0
    estimated_ticket_revenue = 0
    estimated_merch_revenue = 0
    estimated_total_revenue = 0
    estimated_profit = -estimated_total_cost

    if current_venue:
        venue_capacity = getattr(current_venue, 'capacity', 100)
        ticket_price = getattr(current_venue, 'ticket_price', 15)

        estimated_attendance = int(
            min(
                venue_capacity,
                max(
                    10,
                    promotion.fan_base * 0.08
                    + getattr(promotion, 'prestige', 1) * 20
                    + production_fans
                )
            )
        )

        estimated_ticket_revenue = estimated_attendance * ticket_price
        estimated_merch_revenue = int(
            estimated_attendance * 5 * getattr(promotion, 'merchandise_modifier', 1.0)
        )
        estimated_total_revenue = estimated_ticket_revenue + estimated_merch_revenue
        estimated_profit = estimated_total_revenue - estimated_total_cost

    rival_show_preview = None
    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler:
            rival_show_preview = rival_scheduler.get_next_rival_show_preview()
    except Exception:
        pass

    return render_template(
        'book_show.html',
        promotion=promotion,
        progression=progression,
        level=level,
        limits=limits,
        max_tier=max_tier,
        max_matches=max_matches,

        venues=venues,
        all_venues=all_venues,
        hidden_venue_count=hidden_venue_count,
        show_all_venues=show_all_venues,
        current_venue=current_venue,

        wrestlers=available,
        available_wrestlers=available,

        match_types=match_types,
        match_categories=match_categories,
        match_time_options=MATCH_TIME_OPTIONS,

        current_card=current_card,
        show_date=show_date,
        show_day_name=show_day_name,
        venue_day_mod=venue_day_mod,

        championships=championships,
        has_booked_show=has_booked_show,
        booked_show=game_state.booked_show if has_booked_show else None,

        show_production=selected_production,
        current_production=selected_production,
        production_options=production_options,
        available_production=production_options,
        category_labels=CATEGORY_LABELS,
        production_cost=production_cost,
        total_production_cost=production_cost,
        estimated_production_cost=estimated_production_cost,

        total_show_time=total_show_time,
        card_total_time=total_show_time,
        available_minutes=available_minutes,
        venue_available_time=venue_available_time,
        venue_time_limit=venue_time_limit,
        time_remaining=time_remaining,
        is_overrunning=is_overrunning,
        minutes_over=minutes_over,
        overrun_fine=overrun_fine,
        overrun_penalty=overrun_penalty,
        overrun_message=overrun_message,

        estimated_venue_cost=estimated_venue_cost,
        estimated_salary_cost=estimated_salary_cost,
        estimated_total_cost=estimated_total_cost,
        estimated_attendance=estimated_attendance,
        estimated_ticket_revenue=estimated_ticket_revenue,
        estimated_merch_revenue=estimated_merch_revenue,
        estimated_total_revenue=estimated_total_revenue,
        estimated_profit=estimated_profit,

        rival_show_preview=rival_show_preview,

        currency=currency,
        hide_base_hud=True,
    )


@app.route('/select-venue/<venue_id>', methods=['GET', 'POST'])
@require_login
@require_game
def select_venue(venue_id):
    game_state = get_game_state()
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level if progression else 1)
    max_tier = limits.get("venue_tier_max", 1)

    venue = get_venue_by_id(venue_id)

    if not venue:
        flash('Venue not found.', 'error')
        return redirect(url_for('book_show'))

    venue_tier = getattr(venue.tier, 'value', 1)

    if venue_tier > max_tier:
        flash(f'This venue unlocks at venue tier {venue_tier}.', 'error')
        return redirect(url_for('book_show'))

    session['current_venue_id'] = venue_id
    flash(f'Venue selected: {venue.name}', 'success')
    return redirect(url_for('book_show'))


@app.route('/set-show-date', methods=['POST'])
@require_login
@require_game
def set_show_date():
    game_state = get_game_state()
    promotion = game_state.promotion

    try:
        year = int(request.form.get('year', promotion.current_year))
        month = int(request.form.get('month', promotion.current_month))
        day = int(request.form.get('day', promotion.current_day))

        if month < 1 or month > 12:
            flash('Invalid month.', 'error')
            return redirect(url_for('book_show'))

        if day < 1 or day > days_in_month(month):
            flash('Invalid day.', 'error')
            return redirect(url_for('book_show'))

        session['show_date'] = {
            'year': year,
            'month': month,
            'day': day,
        }

        flash(f'Show date set to {format_date(year, month, day)}.', 'success')

    except Exception as e:
        flash(f'Date error: {e}', 'error')

    return redirect(url_for('book_show'))


@app.route('/add-match', methods=['POST'])
@require_login
@require_game
def add_match():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    limits = get_cumulative_limits(progression.level if progression else 1)
    max_matches = limits.get("max_matches", 3)

    current_card = session.get('current_card', [])

    if len(current_card) >= max_matches:
        flash(f'Match limit reached. Max matches: {max_matches}', 'error')
        return redirect(url_for('book_show'))

    match_type = request.form.get('match_type', 'Singles')
    match_info = get_match_type_info().get(match_type, get_match_type_info()['Singles'])

    try:
        num_participants = int(request.form.get('num_participants', match_info.get('min', 2)))
    except Exception:
        num_participants = match_info.get('min', 2)

    num_participants = max(match_info.get('min', 2), min(num_participants, match_info.get('max', 2)))

    match_data = {
        'match_type': match_type,
        'match_time': request.form.get('match_time', 'Standard'),
        'num_participants': num_participants,
        'is_title_match': request.form.get('is_title_match') == 'on',
        'title_match': request.form.get('is_title_match') == 'on',
        'championship_name': request.form.get('championship_name', ''),
        'story_notes': request.form.get('story_notes', ''),
        'notes': request.form.get('notes', ''),
    }

    for i in range(1, num_participants + 1):
        match_data[f'wrestler{i}'] = request.form.get(f'wrestler{i}', '')

    participants = [
        match_data.get(f'wrestler{i}', '')
        for i in range(1, num_participants + 1)
        if match_data.get(f'wrestler{i}', '')
    ]

    if len(participants) < match_info.get('min', 2):
        flash(f'{match_type} requires at least {match_info.get("min", 2)} wrestlers.', 'error')
        return redirect(url_for('book_show'))

    if len(set(participants)) != len(participants):
        flash('A wrestler cannot be booked twice in the same match.', 'error')
        return redirect(url_for('book_show'))

    roster_names = {w.name for w in promotion.roster}
    invalid = [name for name in participants if name not in roster_names]

    if invalid:
        flash(f'Invalid wrestlers: {", ".join(invalid)}', 'error')
        return redirect(url_for('book_show'))

    booked_names = set()

    for match in current_card:
        for i in range(1, 31):
            name = match.get(f'wrestler{i}', '')
            if name:
                booked_names.add(name)

    already_booked = [name for name in participants if name in booked_names]

    if already_booked:
        flash(f'Already booked tonight: {", ".join(already_booked)}', 'error')
        return redirect(url_for('book_show'))

    match_data['display'] = get_display_for_match(match_data)

    current_card.append(match_data)

    for index, match in enumerate(current_card):
        match['is_main_event'] = index == len(current_card) - 1

    session['current_card'] = current_card

    flash(f'Added match: {match_data["display"]}', 'success')
    return redirect(url_for('book_show'))


@app.route('/remove-match/<int:match_index>')
@app.route('/remove-match/<int:match_index>', methods=['POST'])
@require_login
@require_game
def remove_match(match_index):
    current_card = session.get('current_card', [])

    if 0 <= match_index < len(current_card):
        current_card.pop(match_index)

        for index, match in enumerate(current_card):
            match['is_main_event'] = index == len(current_card) - 1

        session['current_card'] = current_card
        flash('Match removed.', 'info')

    return redirect(url_for('book_show'))


@app.route('/reorder-matches', methods=['POST'])
@require_login
@require_game
def reorder_matches():
    current_card = session.get('current_card', [])

    try:
        from_index = int(request.form.get('from_index'))
        to_index = int(request.form.get('to_index'))
    except Exception:
        flash('Invalid reorder request.', 'error')
        return redirect(url_for('book_show'))

    if 0 <= from_index < len(current_card) and 0 <= to_index < len(current_card):
        match = current_card.pop(from_index)
        current_card.insert(to_index, match)

        for index, item in enumerate(current_card):
            item['is_main_event'] = index == len(current_card) - 1

        session['current_card'] = current_card
        flash('Card order updated.', 'success')

    return redirect(url_for('book_show'))


@app.route('/clear-card', methods=['POST'])
@require_login
@require_game
def clear_card():
    session['current_card'] = []
    flash('Card cleared.', 'info')
    return redirect(url_for('book_show'))


@app.route('/show-production')
@require_login
@require_game
def show_production():
    return redirect(url_for('book_show'))


@app.route('/update-production', methods=['POST'])
@app.route('/set-production', methods=['POST'])
@require_login
@require_game
def update_production():
    production = {}

    for category in CATEGORY_LABELS.keys():
        option_id = request.form.get(category)
        if option_id:
            production[category] = option_id

    session['show_production'] = production
    flash('Production updated.', 'success')
    return redirect(url_for('book_show'))


@app.route('/save-show', methods=['POST'])
@require_login
@require_game
def save_show():
    game_state = get_game_state()

    current_card = session.get('current_card', [])
    current_venue_id = session.get('current_venue_id')
    show_date = session.get('show_date')
    show_production = session.get('show_production', {})

    if not current_venue_id:
        flash('Select a venue first.', 'error')
        return redirect(url_for('book_show'))

    if not current_card:
        flash('Add at least one match.', 'error')
        return redirect(url_for('book_show'))

    venue = get_venue_by_id(current_venue_id)

    if not venue:
        flash('Venue not found.', 'error')
        return redirect(url_for('book_show'))

    if not show_date:
        promotion = game_state.promotion
        show_date = {
            'year': promotion.current_year,
            'month': promotion.current_month,
            'day': promotion.current_day,
        }

    game_state.booked_show = {
        'venue_id': current_venue_id,
        'venue_name': venue.name,
        'card': current_card,
        'show_date': show_date,
        'production': show_production,
    }

    save_game_state(game_state)
    flash('Show booked successfully.', 'success')
    return redirect(url_for('booking_room'))


@app.route('/run-show', methods=['POST'])
@require_login
@require_game
def run_show():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    booked_show = getattr(game_state, 'booked_show', None)

    if not booked_show:
        flash('No show booked.', 'error')
        return redirect(url_for('book_show'))

    venue = get_venue_by_id(booked_show.get('venue_id'))

    if not venue:
        flash('Venue not found.', 'error')
        return redirect(url_for('book_show'))

    card = booked_show.get('card', [])
    show_date = booked_show.get('show_date', {
        'year': promotion.current_year,
        'month': promotion.current_month,
        'day': promotion.current_day,
    })

    selected_production = booked_show.get('production', {})

    if not card:
        flash('Cannot run an empty show.', 'error')
        return redirect(url_for('book_show'))

    roster_lookup = {w.name: w for w in promotion.roster}

    try:
        match_engine = MatchEngine(promotion)
    except TypeError:
        match_engine = MatchEngine()

    results = []
    total_rating = 0

    for match_data in card:
        participants = []

        for i in range(1, 31):
            name = match_data.get(f'wrestler{i}', '')
            if name and name in roster_lookup:
                participants.append(roster_lookup[name])

        if len(participants) < 2:
            continue

        try:
            result = match_engine.simulate_match(
                participants,
                match_data.get('match_type', 'Singles')
            )
        except Exception:
            result = None

        if isinstance(result, dict):
            rating = float(result.get('rating', random.uniform(1.5, 4.5)))
            winner_obj = result.get('winner')
            winner = winner_obj.name if hasattr(winner_obj, 'name') else winner_obj
            if not winner:
                winner = random.choice(participants).name
            finish = result.get('finish', result.get('finish_type', 'Pinfall'))
        else:
            rating = round(random.uniform(1.5, 4.5), 2)
            winner = random.choice(participants).name
            finish = random.choice(['Pinfall', 'Submission', 'Flash Finish', 'Referee Stoppage'])

        total_rating += rating

        results.append({
            'match': match_data,
            'display': match_data.get('display', get_display_for_match(match_data)),
            'rating': round(rating, 2),
            'winner': winner,
            'finish': finish,
            'all_participants': [w.name for w in participants],
            'match_type': match_data.get('match_type', 'Singles'),
            'is_title_match': match_data.get('is_title_match') or match_data.get('title_match'),
            'championship_name': match_data.get('championship_name', ''),
        })

    avg_rating = round(total_rating / len(results), 2) if results else 1.0

    production_cost = 0
    production_quality = 1.0
    production_fans = 0

    for option_id in selected_production.values():
        option = ALL_PRODUCTION_OPTIONS.get(option_id)
        if option:
            production_cost += option.cost
            production_quality += getattr(option, 'quality_modifier', 0)
            production_fans += getattr(option, 'fan_bonus', 0)

    venue_capacity = getattr(venue, 'capacity', 100)
    ticket_price = getattr(venue, 'ticket_price', 15)
    venue_cost = getattr(venue, 'cost', getattr(venue, 'rental_cost', 0))

    show_day_name = get_day_name(
        get_day_of_week(show_date['year'], show_date['month'], show_date['day'])
    )

    day_mod = DEFAULT_DAY_MODIFIERS.get(show_day_name, {"modifier": 1.0})
    day_modifier = day_mod.get("modifier", 1.0) if isinstance(day_mod, dict) else 1.0

    base_draw = promotion.fan_base * 0.08
    rating_draw = avg_rating * 40
    prestige_draw = getattr(promotion, 'prestige', 1) * 20

    attendance = int(
        min(
            venue_capacity,
            max(
                10,
                (base_draw + rating_draw + prestige_draw + production_fans + random.randint(-30, 60)) * day_modifier
            )
        )
    )

    is_sellout = attendance >= venue_capacity

    ticket_revenue = attendance * ticket_price
    merch_revenue = int(attendance * 5 * getattr(promotion, 'merchandise_modifier', 1.0))
    alcohol_revenue = int(attendance * getattr(venue, 'alcohol_revenue_per_fan', 0))
    concession_revenue = int(attendance * getattr(venue, 'concession_revenue_per_fan', 0))
    vip_revenue = int(attendance * getattr(venue, 'vip_revenue_per_fan', 0))

    revenue = ticket_revenue + merch_revenue + alcohol_revenue + concession_revenue + vip_revenue

    used_names = set()
    wrestler_cost = 0

    for result in results:
        for name in result.get('all_participants', []):
            if name in used_names:
                continue

            wrestler = roster_lookup.get(name)
            if wrestler:
                wrestler_cost += getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0))
                used_names.add(name)

    total_show_time = get_card_total_time(card)
    available_minutes = getattr(venue, 'time_limit_minutes', 120)
    minutes_over = max(0, total_show_time - available_minutes)
    overrun_fine = calculate_overrun_penalty(minutes_over) if minutes_over > 0 else 0
    overrun_message = f"Over time by {minutes_over} minutes" if minutes_over > 0 else ""

    total_cost = venue_cost + wrestler_cost + production_cost + overrun_fine
    profit = revenue - total_cost

    promotion.budget += profit

    fan_gain = int((avg_rating * 8) + (attendance / 50) + production_fans)
    if is_sellout:
        fan_gain += 25

    promotion.fan_base += max(0, fan_gain)

    show_rewards = {"xp": {"total": 0}, "fans": {"total": fan_gain}, "leveled_up": False, "achievements_earned": []}

    if progression:
        try:
            xp_gain = int((avg_rating * 100) + (attendance / 10))
            before_level = progression.level
            progression.add_xp(xp_gain, "Show completed")
            show_rewards["xp"]["total"] = xp_gain
            show_rewards["leveled_up"] = progression.level > before_level
            show_rewards["new_level"] = progression.level
        except Exception:
            pass

    title_changes = []

    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        for result in results:
            if result.get('is_title_match') and result.get('championship_name'):
                try:
                    champ_name = result.get('championship_name')
                    winner = result.get('winner')

                    game_state.championship_manager.change_champion(
                        champ_name,
                        winner,
                        week=getattr(promotion, 'current_week', 0),
                        year=getattr(promotion, 'current_year', 1),
                    )

                    title_changes.append({
                        "championship": champ_name,
                        "new_champion": winner,
                    })
                except Exception:
                    pass

    if hasattr(game_state, 'calendar') and game_state.calendar:
        try:
            game_state.calendar.add_event(
                year=show_date.get('year', promotion.current_year),
                month=show_date.get('month', promotion.current_month),
                day=show_date.get('day', promotion.current_day),
                venue=venue.name,
                attendance=attendance,
                rating=avg_rating,
                profit=profit,
                is_sellout=is_sellout,
            )
        except TypeError:
            try:
                game_state.calendar.add_show(
                    show_date.get('year', promotion.current_year),
                    show_date.get('month', promotion.current_month),
                    show_date.get('day', promotion.current_day),
                    venue.name,
                    attendance,
                    avg_rating,
                    profit,
                    is_sellout,
                )
            except Exception:
                pass
        except Exception:
            pass

    try:
        venue.record_event(attendance, profit)
    except Exception:
        pass

    if hasattr(game_state, 'injury_manager') and game_state.injury_manager:
        try:
            for result in results:
                for wrestler_name in result.get('all_participants', []):
                    wrestler = roster_lookup.get(wrestler_name)
                    if wrestler:
                        game_state.injury_manager.check_match_injury(
                            wrestler,
                            result.get('match_type', 'Singles')
                        )
        except Exception:
            pass

    try:
        promotion.advance_to_date(
            show_date['year'],
            show_date['month'],
            show_date['day'],
        )
        promotion.advance_days(1)
    except Exception:
        pass

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
                avg_rating=avg_rating,
                attendance=attendance,
                is_sellout=is_sellout,
                profit=profit,
                venue_name=venue.name,
                match_results=match_results_for_ai,
            )
        except Exception:
            pass

    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler:
            rival_scheduler.on_player_show_completed(
                game_state,
                show_result={
                    "rating": avg_rating,
                    "attendance": attendance,
                    "profit": profit,
                    "venue": venue.name,
                    "show_date": show_date,
                    "results": results,
                },
            )
    except Exception as e:
        print(f"Rival Scheduler error: {e}")

    game_state.last_show_result = {
        'venue': venue.name,
        'show_date': show_date,
        'results': results,
        'avg_rating': avg_rating,
        'attendance': attendance,
        'is_sellout': is_sellout,
        'ticket_revenue': ticket_revenue,
        'merch_revenue': merch_revenue,
        'alcohol_revenue': alcohol_revenue,
        'concession_revenue': concession_revenue,
        'vip_revenue': vip_revenue,
        'venue_cost': venue_cost,
        'wrestler_cost': wrestler_cost,
        'production_cost': production_cost,
        'overrun_fine': overrun_fine,
        'profit': profit,
        'fan_gain': fan_gain,
    }

    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    session['show_date'] = None

    try:
        ai_result, total_salaries = process_week_advancement(game_state)
    except Exception as e:
        print(f"Weekly advancement after show error: {e}")
        ai_result, total_salaries = {}, 0

    save_game_state(game_state)

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    return render_template(
        'run_show.html',
        promotion=promotion,
        venue=venue,
        results=results,
        avg_rating=avg_rating,
        attendance=attendance,
        is_sellout=is_sellout,
        ticket_revenue=ticket_revenue,
        merch_revenue=merch_revenue,
        alcohol_revenue=alcohol_revenue,
        concession_revenue=concession_revenue,
        vip_revenue=vip_revenue,
        revenue=revenue,
        venue_cost=venue_cost,
        wrestler_cost=wrestler_cost,
        production_cost=production_cost,
        total_cost=total_cost,
        profit=profit,
        xp_earned=show_rewards.get('xp', {}).get('total', 0),
        fans_earned=show_rewards.get('fans', {}).get('total', 0),
        leveled_up=show_rewards.get('leveled_up', False),
        new_level=show_rewards.get('new_level', progression.level if progression else 1),
        achievements=show_rewards.get('achievements_earned', []),
        title_changes=title_changes,
        currency=currency,
        salaries_paid=total_salaries,
        new_events=len(ai_result.get('new_events', []) if isinstance(ai_result, dict) else []),
        new_week=getattr(promotion, 'current_week', 0),
        new_year=promotion.current_year,
        production_quality=production_quality,
        production_fans=production_fans,
        show_day_name=show_day_name,
        total_show_time=total_show_time,
        available_minutes=available_minutes,
        overrun_fine=overrun_fine,
        overrun_message=overrun_message,
        minutes_over=minutes_over,
        hide_base_hud=True,
    )


@app.route('/skip-week', methods=['POST'])
@require_login
@require_game
def skip_week():
    game_state = get_game_state()
    promotion = game_state.promotion

    promotion.advance_days(7)

    try:
        ai_result, total_salaries = process_week_advancement(game_state)
    except Exception as e:
        print(f"Weekly advancement error: {e}")
        ai_result, total_salaries = {}, 0

    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler:
            rival_scheduler.complete_due_rival_shows(game_state)
    except Exception as e:
        print(f"Rival due show error: {e}")

    fan_loss = int(promotion.fan_base * 0.02)
    promotion.fan_base = max(0, promotion.fan_base - fan_loss)

    save_game_state(game_state)

    flash(f'Skipped a week. Booking Fees: ${total_salaries:,}. Lost {fan_loss} fans.', 'warning')
    return redirect(url_for('dashboard'))


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

    return render_template(
        'events.html',
        events=all_events,
        promotion=game_state.promotion,
        hide_base_hud=True,
    )


@app.route('/resolve-event/<path:event_id>/<int:option_index>', methods=['POST'])
@app.route('/resolve-event/<path:event_id>', methods=['POST'], defaults={'option_index': 0})
@require_login
@require_game
def resolve_event(event_id, option_index=0):
    game_state = get_game_state()

    if game_state.ai_director:
        try:
            if hasattr(game_state.ai_director, 'resolve_event'):
                game_state.ai_director.resolve_event(event_id, option_index)
            flash('Event resolved.', 'success')
        except TypeError:
            try:
                game_state.ai_director.resolve_event(event_id)
                flash('Event resolved.', 'success')
            except Exception as e:
                flash(f'Could not resolve event: {e}', 'error')
        except Exception as e:
            flash(f'Could not resolve event: {e}', 'error')

    save_game_state(game_state)
    return redirect(url_for('events'))


# ==================== CHAMPIONSHIPS ====================

@app.route('/championships')
@require_login
@require_game
def championships():
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.championship_manager:
        game_state.championship_manager = ChampionshipManager()
        save_game_state(game_state)

    championships_list = []

    try:
        championships_list = game_state.championship_manager.get_active_championships()
    except Exception:
        championships_list = []

    limits = get_cumulative_limits(game_state.progression.level if game_state.progression else 1)
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    return render_template(
        'championships.html',
        promotion=promotion,
        championships=championships_list,
        championship_manager=game_state.championship_manager,
        championship_costs=CHAMPIONSHIP_COSTS,
        slot_costs=SLOT_COSTS,
        limits=limits,
        budget=promotion.budget,
        currency=currency,
        hide_base_hud=True,
    )


@app.route('/create-championship', methods=['GET', 'POST'])
@require_login
@require_game
def create_championship():
    game_state = get_game_state()
    promotion = game_state.promotion

    if not game_state.championship_manager:
        game_state.championship_manager = ChampionshipManager()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        level_value = request.form.get('level')
        gender_value = request.form.get('gender')
        rule_value = request.form.get('rule')

        try:
            level = ChampionshipLevel(level_value)
        except Exception:
            level = ChampionshipLevel.WORLD

        try:
            gender = ChampionshipGender(gender_value)
        except Exception:
            gender = ChampionshipGender.OPENWEIGHT

        try:
            rule = ChampionshipRule(rule_value)
        except Exception:
            rule = ChampionshipRule.SINGLES

        try:
            success, msg, cost = game_state.championship_manager.create_championship(
                name=name,
                level=level,
                gender=gender,
                rule=rule,
                budget=promotion.budget,
            )

            if success:
                promotion.budget -= cost
                flash(msg, 'success')
            else:
                flash(msg, 'error')

            save_game_state(game_state)

        except Exception as e:
            flash(f'Could not create championship: {e}', 'error')

        return redirect(url_for('championships'))

    return render_template(
        'create_championship.html',
        promotion=promotion,
        levels=list(ChampionshipLevel),
        genders=list(ChampionshipGender),
        rules=list(ChampionshipRule),
        championship_costs=CHAMPIONSHIP_COSTS,
        slot_costs=SLOT_COSTS,
        budget=promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/award-title/<path:championship_id>', methods=['GET', 'POST'])
@require_login
@require_game
def award_title(championship_id):
    game_state = get_game_state()
    promotion = game_state.promotion
    champ_manager = game_state.championship_manager

    if not champ_manager:
        flash('Championship system unavailable.', 'error')
        return redirect(url_for('championships'))

    championship = champ_manager.get_championship(championship_id)

    if not championship:
        flash('Championship not found.', 'error')
        return redirect(url_for('championships'))

    is_tag_title = getattr(championship, 'is_tag_title', False)

    if request.method == 'POST':
        wrestler_name = request.form.get('wrestler_name')
        partner_name = request.form.get('partner_name', '')

        try:
            if is_tag_title:
                championship.current_champion = wrestler_name
                championship.current_champion_tag_partner = partner_name
            else:
                championship.current_champion = wrestler_name

            save_game_state(game_state)
            flash(f'{championship.name} awarded to {wrestler_name}.', 'success')

        except Exception as e:
            flash(f'Could not award title: {e}', 'error')

        return redirect(url_for('championships'))

    eligible = [
        w for w in promotion.roster
        if not getattr(w, 'is_injured', False)
    ]
    eligible.sort(key=lambda w: getattr(w, 'popularity', 0), reverse=True)

    return render_template(
        'award_title.html',
        championship=championship,
        wrestlers=eligible,
        is_tag_title=is_tag_title,
        hide_base_hud=True,
    )


@app.route('/assign-champion/<path:championship_name>', methods=['POST'])
@require_login
@require_game
def assign_champion(championship_name):
    game_state = get_game_state()
    wrestler_name = request.form.get('wrestler_name')

    try:
        champ = game_state.championship_manager.get_championship(championship_name)
        if champ:
            champ.current_champion = wrestler_name
            flash(f'{wrestler_name} is now {championship_name}.', 'success')
        else:
            flash('Championship not found.', 'error')

        save_game_state(game_state)

    except Exception as e:
        flash(f'Champion assignment error: {e}', 'error')

    return redirect(url_for('championships'))


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
                flash(f'{championship.name} has been vacated.', 'info')
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
        level = 1
        xp_into = 0
        xp_needed = 100
        percentage = 0
        tier_name = "Backyard"
        earned_achievements = []
        stats = {}
        total_achievements = 0

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    return render_template(
        'career.html',
        promotion=promotion,
        progression=progression,
        level=level,
        tier_name=tier_name,
        xp_into=xp_into,
        xp_needed=xp_needed,
        xp_percentage=percentage,
        stats=stats,
        achievements=earned_achievements,
        total_achievements=total_achievements,
        currency=currency,
        hide_base_hud=True,
    )



# ==================== INBOX ====================

@app.route('/inbox')
@require_login
@require_game
def inbox():
    game_state = get_game_state()

    if not game_state.inbox:
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

    return render_template(
        'inbox.html',
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

    return render_template(
        'read_message.html',
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
    promotion = game_state.promotion

    if not hasattr(game_state, 'calls') or game_state.calls is None:
        game_state.calls = CallsManager()

    if not hasattr(game_state, 'banking') or game_state.banking is None:
        game_state.banking = BankingManager()

    calls_data = {"incoming": [], "answered": [], "missed": []}
    contacts = []
    incoming_count = 0

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

    try:
        can_take_shark, shark_reason = game_state.banking.can_take_loan(LoanType.LOAN_SHARK)
        active_shark_loans = game_state.banking.get_active_shark_loans() if hasattr(game_state.banking, 'get_active_shark_loans') else []
    except Exception:
        pass

    return render_template(
        'calls.html',
        promotion=promotion,
        calls=calls_data,
        contacts=contacts,
        incoming_count=incoming_count,
        shark_options=SHARK_LOAN_OPTIONS,
        can_take_shark=can_take_shark,
        shark_reason=shark_reason,
        active_shark_loans=active_shark_loans,
        budget=promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
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
        try:
            result = game_state.calls.answer_call(call_id, option_index, game_state)
        except TypeError:
            result = game_state.calls.answer_call(call_id, option_index)

        if isinstance(result, dict):
            success = result.get('success', True)
            message = result.get('message', 'Call answered.')

            effects = result.get('effects', {})
            if effects.get('money') and game_state.promotion:
                game_state.promotion.budget += effects['money']
        else:
            success = True
            message = 'Call answered.'

        save_game_state(game_state)
        flash(message, 'success' if success else 'error')

    except Exception as e:
        flash(f'Call error: {e}', 'error')

    return redirect(url_for('calls_app'))


@app.route('/calls/answer/<path:call_id>', methods=['POST'])
@require_login
@require_game
def answer_call_simple(call_id):
    return answer_call(call_id, 0)


@app.route('/decline-call/<path:call_id>', methods=['POST'])
@app.route('/dismiss-call/<path:call_id>', methods=['POST'])
@app.route('/calls/decline/<path:call_id>', methods=['POST'])
@require_login
@require_game
def decline_call(call_id):
    game_state = get_game_state()

    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            if hasattr(game_state.calls, 'decline_call'):
                game_state.calls.decline_call(call_id)
            elif hasattr(game_state.calls, 'dismiss_call'):
                game_state.calls.dismiss_call(call_id)
            elif hasattr(game_state.calls, 'miss_call'):
                game_state.calls.miss_call(call_id)

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
    promotion = game_state.promotion

    if not hasattr(game_state, 'banking') or game_state.banking is None:
        game_state.banking = BankingManager()
        save_game_state(game_state)

    bm = game_state.banking

    try:
        can_bank, bank_reason = bm.can_take_loan(LoanType.BANK)
    except Exception:
        can_bank, bank_reason = False, "Banking unavailable"

    try:
        can_shark, shark_reason = bm.can_take_loan(LoanType.LOAN_SHARK)
    except Exception:
        can_shark, shark_reason = False, "Loan shark unavailable"

    total_outstanding = bm.get_total_outstanding() if hasattr(bm, 'get_total_outstanding') else 0
    weekly_obligations = bm.get_total_weekly_obligations() if hasattr(bm, 'get_total_weekly_obligations') else 0

    return render_template(
        'banking.html',
        promotion=promotion,
        banking=bm,
        budget=promotion.budget,

        credit_score=getattr(bm, 'credit_score', 600),
        credit_rating=bm.get_credit_rating() if hasattr(bm, 'get_credit_rating') else 'Fair',
        credit_color=bm.get_credit_color() if hasattr(bm, 'get_credit_color') else '#6b7280',

        total_outstanding=total_outstanding,
        weekly_payments=weekly_obligations,
        weekly_obligations=weekly_obligations,

        active_loans=getattr(bm, 'active_loans', []),
        loan_history=getattr(bm, 'loan_history', []),

        bank_options=BANK_LOAN_OPTIONS,
        shark_options=SHARK_LOAN_OPTIONS,
        bank_loans=BANK_LOAN_OPTIONS,
        shark_loans=SHARK_LOAN_OPTIONS,

        can_take_bank=can_bank,
        can_bank=can_bank,
        bank_reason=bank_reason,
        can_take_shark=can_shark,
        can_shark=can_shark,
        shark_reason=shark_reason,

        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/take-loan', methods=['GET', 'POST'])
@app.route('/take-loan/<loan_type>/<loan_id>', methods=['GET', 'POST'])
@require_login
@require_game
def take_loan(loan_type=None, loan_id=None):
    game_state = get_game_state()

    if not hasattr(game_state, 'banking') or game_state.banking is None:
        game_state.banking = BankingManager()

    bm = game_state.banking
    promotion = game_state.promotion

    loan_type_str = loan_type or request.form.get('loan_type', 'bank')
    option_key = loan_id or request.form.get('option_key') or request.form.get('loan_id', '')

    if not option_key:
        flash('No loan selected.', 'error')
        return redirect(url_for('banking'))

    try:
        if str(loan_type_str).lower() in ['loan_shark', 'loanshark', 'shark']:
            loan_type_enum = LoanType.LOAN_SHARK
        else:
            loan_type_enum = LoanType.BANK

        success, msg, amount = bm.take_loan(
            loan_type_enum,
            option_key,
            promotion.budget,
        )

        if success:
            promotion.budget += amount
            save_game_state(game_state)
            flash(msg, 'success')
        else:
            flash(msg, 'error')

    except Exception as e:
        flash(f'Loan error: {e}', 'error')

    return redirect(url_for('banking'))


@app.route('/repay-loan/<path:loan_id>', methods=['POST'])
@require_login
@require_game
def repay_loan(loan_id):
    game_state = get_game_state()

    if not hasattr(game_state, 'banking') or game_state.banking is None:
        game_state.banking = BankingManager()

    try:
        success, msg, cost = game_state.banking.repay_loan(
            loan_id,
            game_state.promotion.budget,
        )

        if success:
            game_state.promotion.budget -= cost
            save_game_state(game_state)

        flash(msg, 'success' if success else 'error')

    except Exception as e:
        flash(f'Repayment error: {e}', 'error')

    return redirect(url_for('banking'))


# ==================== INJURIES ====================

@app.route('/injuries')
@require_login
@require_game
def injury_report():
    game_state = get_game_state()

    if not hasattr(game_state, 'injury_manager') or game_state.injury_manager is None:
        game_state.injury_manager = InjuryManager()
        save_game_state(game_state)

    injured = [
        w for w in game_state.promotion.roster
        if getattr(w, 'is_injured', False)
    ]

    return render_template(
        'injury_report.html',
        promotion=game_state.promotion,
        injured_wrestlers=injured,
        injury_manager=game_state.injury_manager,
        hide_base_hud=True,
    )


# ==================== TRAINING SCHOOL ====================

def ensure_training_school_systems(game_state):
    if not hasattr(game_state, 'training_school') or game_state.training_school is None:
        game_state.training_school = TrainingSchool()

    if not hasattr(game_state, 'coach_manager') or game_state.coach_manager is None:
        game_state.coach_manager = CoachManager()

    if not hasattr(game_state, 'coach_pool') or game_state.coach_pool is None:
        game_state.coach_pool = CoachPool()

    if not hasattr(game_state, 'trainee_pool') or game_state.trainee_pool is None:
        game_state.trainee_pool = TraineePool()

    if not hasattr(game_state, 'trainee_show_manager') or game_state.trainee_show_manager is None:
        game_state.trainee_show_manager = TraineeShowManager()

    if not hasattr(game_state, 'active_enrollments') or game_state.active_enrollments is None:
        game_state.active_enrollments = []

    return game_state.training_school


@app.route('/training-school')
@require_login
@require_game
def training_school():
    game_state = get_game_state()
    promotion = game_state.promotion
    school = ensure_training_school_systems(game_state)

    try:
        school_summary = school.get_summary()
    except Exception:
        school_summary = {}

    try:
        is_founded = school.is_founded()
    except Exception:
        is_founded = bool(getattr(school, 'founded', False))

    return render_template(
        'training_school.html',
        promotion=promotion,
        school=school,
        school_summary=school_summary,
        is_founded=is_founded,
        current_tier=getattr(school, 'tier', None),
        school_tiers=SchoolTier,
        school_tier_info=SCHOOL_TIER_INFO,
        budget=promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/found-training-school', methods=['GET', 'POST'])
@app.route('/found-school', methods=['GET', 'POST'])
@require_login
@require_game
def found_school():
    game_state = get_game_state()
    promotion = game_state.promotion
    school = ensure_training_school_systems(game_state)

    try:
        already_founded = school.is_founded()
    except Exception:
        already_founded = bool(getattr(school, 'founded', False))

    if request.method == 'POST':
        if already_founded:
            flash('You already own a training school.', 'warning')
            return redirect(url_for('training_school'))

        school_name = request.form.get('name', '').strip() or request.form.get('school_name', '').strip()
        if not school_name:
            school_name = f"{promotion.name} Dojo"

        tier_value = request.form.get('tier', SchoolTier.SCHOOL_GYM.value)

        try:
            selected_tier = SchoolTier(tier_value)
        except Exception:
            selected_tier = SchoolTier.SCHOOL_GYM

        tier_info = SCHOOL_TIER_INFO.get(selected_tier, {})
        setup_cost = tier_info.get('cost', 0)

        if promotion.budget < setup_cost:
            flash(f'Not enough money. Need ${setup_cost:,}.', 'error')
            return redirect(url_for('found_school'))

        try:
            promotion.budget -= setup_cost

            school.found_school(
                name=school_name,
                location=getattr(promotion, 'location', 'Unknown'),
                tier=selected_tier,
                week=getattr(promotion, 'current_week', 0),
                year=getattr(promotion, 'current_year', 1),
            )

            school.founded = True
            school.owner = promotion.name
            school.creation_cost = setup_cost

            save_game_state(game_state)
            flash(f'{school_name} founded!', 'success')
            return redirect(url_for('training_school'))

        except Exception as e:
            flash(f'Could not found school: {e}', 'error')
            return redirect(url_for('training_school'))

    available_tiers = []

    for tier, info in SCHOOL_TIER_INFO.items():
        available_tiers.append({
            'enum': tier,
            'name': info.get('name', tier.value),
            'cost': info.get('cost', 0),
            'capacity': info.get('capacity', 0),
            'weekly_cost': info.get('weekly_cost', 0),
            'description': info.get('description', ''),
            'can_afford': promotion.budget >= info.get('cost', 0),
        })

    return render_template(
        'found_school.html',
        promotion=promotion,
        school=school,
        already_founded=already_founded,
        school_tiers=SchoolTier,
        school_tier_info=SCHOOL_TIER_INFO,
        available_tiers=available_tiers,
        budget=promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/school-settings')
@require_login
@require_game
def school_settings():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    return render_template(
        'school_settings.html',
        promotion=game_state.promotion,
        school=school,
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/shutdown-school', methods=['POST'])
@require_login
@require_game
def shutdown_school():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    try:
        if hasattr(school, 'shutdown'):
            school.shutdown()
        else:
            school.founded = False
            school.status = SchoolStatus.CLOSED

        save_game_state(game_state)
        flash('Training school closed.', 'info')

    except Exception as e:
        flash(f'Shutdown error: {e}', 'error')

    return redirect(url_for('school_settings'))


@app.route('/trainees')
@require_login
@require_game
def trainees():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    try:
        trainees_list = school.get_all_trainees()
    except Exception:
        try:
            trainees_list = school.get_active_trainees()
        except Exception:
            trainees_list = getattr(school, 'trainees', [])

    try:
        applicants = game_state.trainee_pool.get_available_prospects()
    except Exception:
        applicants = getattr(game_state.trainee_pool, 'available_prospects', [])

    return render_template(
        'trainees.html',
        promotion=game_state.promotion,
        school=school,
        trainees=trainees_list,
        applicants=applicants,
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/trainee/<path:trainee_id>')
@require_login
@require_game
def trainee_profile(trainee_id):
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    trainee = None

    try:
        trainee = school.get_trainee(trainee_id)
    except Exception:
        trainee = next(
            (
                t for t in getattr(school, 'trainees', [])
                if str(getattr(t, 'id', getattr(t, 'name', ''))) == str(trainee_id)
            ),
            None,
        )

    if not trainee:
        flash('Trainee not found.', 'error')
        return redirect(url_for('trainees'))

    return render_template(
        'trainee_profile.html',
        promotion=game_state.promotion,
        school=school,
        trainee=trainee,
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/scout-trainees', methods=['GET', 'POST'])
@app.route('/scout-trainee', methods=['GET', 'POST'])
@require_login
@require_game
def scout_trainees():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)
    promotion = game_state.promotion

    if request.method == 'POST':
        try:
            tier = request.form.get('scouting_tier', 'basic')

            applicant, cost, msg = game_state.trainee_pool.scout_for_prospects(
                scouting_tier=tier,
                budget=promotion.budget,
                monthly_tuition=school.get_monthly_tuition() if hasattr(school, 'get_monthly_tuition') else 0,
            )

            if applicant:
                promotion.budget -= cost

            save_game_state(game_state)
            flash(msg, 'success' if applicant else 'warning')

        except Exception as e:
            flash(f'Scouting error: {e}', 'error')

        return redirect(url_for('scout_trainees'))

    try:
        prospects = game_state.trainee_pool.get_available_prospects()
    except Exception:
        prospects = getattr(game_state.trainee_pool, 'available_prospects', [])

    return render_template(
        'scout_trainees.html',
        promotion=promotion,
        school=school,
        prospects=prospects,
        budget=promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/enroll-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def enroll_trainee(trainee_id):
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    try:
        trainee = None

        if hasattr(game_state.trainee_pool, 'get_prospect'):
            trainee = game_state.trainee_pool.get_prospect(trainee_id)

        if not trainee:
            prospects = getattr(game_state.trainee_pool, 'available_prospects', [])
            trainee = next(
                (
                    t for t in prospects
                    if str(getattr(t, 'id', getattr(t, 'name', ''))) == str(trainee_id)
                ),
                None,
            )

        if not trainee:
            flash('Trainee not found.', 'error')
            return redirect(url_for('scout_trainees'))

        result = school.enroll_trainee(trainee)

        if isinstance(result, tuple):
            success, msg = result[0], result[1]
        else:
            success, msg = True, f'{getattr(trainee, "name", "Trainee")} enrolled!'

        save_game_state(game_state)
        flash(msg, 'success' if success else 'error')

    except Exception as e:
        flash(f'Could not enroll trainee: {e}', 'error')

    return redirect(url_for('trainees'))


@app.route('/roster-training')
@require_login
@require_game
def roster_training():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    try:
        class_catalog = get_full_catalog_for_ui()
    except Exception:
        class_catalog = []

    return render_template(
        'roster_training.html',
        promotion=game_state.promotion,
        school=school,
        wrestlers=game_state.promotion.roster,
        active_enrollments=getattr(game_state, 'active_enrollments', []),
        class_catalog=class_catalog,
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/enroll-wrestler', methods=['POST'])
@require_login
@require_game
def enroll_wrestler():
    game_state = get_game_state()
    ensure_training_school_systems(game_state)

    wrestler_name = request.form.get('wrestler_name')
    class_id = request.form.get('class_id')

    wrestler = next(
        (w for w in game_state.promotion.roster if w.name == wrestler_name),
        None,
    )

    training_class = get_class(class_id)

    if not wrestler or not training_class:
        flash('Invalid wrestler or class.', 'error')
        return redirect(url_for('roster_training'))

    enrollment = {
        'id': str(uuid.uuid4()),
        'student_type': 'wrestler',
        'student_id': wrestler.name,
        'student_name': wrestler.name,
        'class_id': class_id,
        'class_name': training_class.name,
        'duration_weeks': training_class.duration_weeks,
        'weeks_completed': 0,
        'weekly_cost': training_class.weekly_cost,
        'base_weekly_cost': training_class.weekly_cost,
        'is_active': True,
        'completed': False,
    }

    game_state.active_enrollments.append(enrollment)
    save_game_state(game_state)

    flash(f'{wrestler.name} enrolled in {training_class.name}.', 'success')
    return redirect(url_for('roster_training'))


@app.route('/enroll-trainee-in-class/<path:trainee_id>', methods=['GET', 'POST'])
@require_login
@require_game
def enroll_trainee_in_class(trainee_id):
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        training_class = get_class(class_id)

        if not training_class:
            flash('Class not found.', 'error')
            return redirect(url_for('trainee_profile', trainee_id=trainee_id))

        try:
            trainee = school.get_trainee(trainee_id)
        except Exception:
            trainee = None

        if not trainee:
            flash('Trainee not found.', 'error')
            return redirect(url_for('trainees'))

        game_state.active_enrollments.append({
            'id': str(uuid.uuid4()),
            'student_type': 'trainee',
            'student_id': trainee_id,
            'student_name': getattr(trainee, 'name', trainee_id),
            'class_id': class_id,
            'class_name': training_class.name,
            'duration_weeks': training_class.duration_weeks,
            'weeks_completed': 0,
            'weekly_cost': 0,
            'base_weekly_cost': training_class.weekly_cost,
            'is_active': True,
            'completed': False,
        })

        save_game_state(game_state)
        flash('Trainee enrolled in class.', 'success')
        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    try:
        catalog = get_classes_for_trainees()
    except Exception:
        catalog = []

    return render_template(
        'enroll_trainee_class.html',
        promotion=game_state.promotion,
        school=school,
        trainee_id=trainee_id,
        catalog=catalog,
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/cancel-enrollment/<path:enrollment_id>', methods=['POST'])
@require_login
@require_game
def cancel_enrollment(enrollment_id):
    game_state = get_game_state()
    ensure_training_school_systems(game_state)

    for enrollment in game_state.active_enrollments:
        if str(enrollment.get('id', '')) == str(enrollment_id):
            enrollment['is_active'] = False
            enrollment['cancelled_reason'] = 'manual'
            break

    save_game_state(game_state)
    flash('Enrollment cancelled.', 'info')
    return redirect(request.referrer or url_for('roster_training'))


@app.route('/coaches')
@require_login
@require_game
def coaches():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    try:
        hired_coaches = game_state.coach_manager.get_hired_coaches()
    except Exception:
        hired_coaches = getattr(game_state.coach_manager, 'coaches', [])

    try:
        available_coaches = game_state.coach_pool.get_available_coaches()
    except Exception:
        available_coaches = []

    return render_template(
        'coaches.html',
        promotion=game_state.promotion,
        school=school,
        coach_manager=game_state.coach_manager,
        hired_coaches=hired_coaches,
        available_coaches=available_coaches,
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/hire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def hire_coach(coach_id):
    game_state = get_game_state()
    ensure_training_school_systems(game_state)

    try:
        success, msg, cost = game_state.coach_manager.hire_coach(
            coach_id,
            game_state.promotion.budget,
            game_state.coach_pool,
        )

        if success:
            game_state.promotion.budget -= cost

        save_game_state(game_state)
        flash(msg, 'success' if success else 'error')

    except Exception as e:
        flash(f'Hire coach error: {e}', 'error')

    return redirect(url_for('coaches'))


@app.route('/fire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def fire_coach(coach_id):
    game_state = get_game_state()
    ensure_training_school_systems(game_state)

    try:
        success, msg = game_state.coach_manager.fire_coach(coach_id)
        save_game_state(game_state)
        flash(msg, 'success' if success else 'error')
    except Exception as e:
        flash(f'Fire coach error: {e}', 'error')

    return redirect(url_for('coaches'))


@app.route('/assign-trainee-coach/<path:trainee_id>', methods=['GET', 'POST'])
@require_login
@require_game
def assign_trainee_coach(trainee_id):
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    if request.method == 'POST':
        coach_id = request.form.get('coach_id')

        try:
            trainee = school.get_trainee(trainee_id)
            trainee.assigned_coach_id = coach_id
            save_game_state(game_state)
            flash('Coach assigned.', 'success')
        except Exception as e:
            flash(f'Coach assignment error: {e}', 'error')

        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    try:
        hired_coaches = game_state.coach_manager.get_hired_coaches()
    except Exception:
        hired_coaches = []

    return render_template(
        'assign_trainee_coach.html',
        promotion=game_state.promotion,
        school=school,
        trainee_id=trainee_id,
        coaches=hired_coaches,
        hide_base_hud=True,
    )


@app.route('/choose-trainee-specialization/<path:trainee_id>', methods=['GET', 'POST'])
@require_login
@require_game
def choose_trainee_specialization(trainee_id):
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    if request.method == 'POST':
        specialization = request.form.get('specialization')

        try:
            trainee = school.get_trainee(trainee_id)
            trainee.specialization = specialization
            save_game_state(game_state)
            flash('Specialization updated.', 'success')
        except Exception as e:
            flash(f'Specialization error: {e}', 'error')

        return redirect(url_for('trainee_profile', trainee_id=trainee_id))

    return render_template(
        'choose_trainee_specialization.html',
        promotion=game_state.promotion,
        school=school,
        trainee_id=trainee_id,
        specializations=list(TraineeSpecialization),
        hide_base_hud=True,
    )


@app.route('/trainee-show')
@require_login
@require_game
def trainee_show():
    game_state = get_game_state()
    school = ensure_training_school_systems(game_state)

    scheduled_shows = []
    completed_shows = []
    lifetime_stats = {}

    try:
        scheduled_shows = game_state.trainee_show_manager.get_scheduled_shows()
    except Exception:
        pass

    try:
        completed_shows = game_state.trainee_show_manager.get_completed_shows()
    except Exception:
        pass

    try:
        lifetime_stats = game_state.trainee_show_manager.get_lifetime_stats()
    except Exception:
        pass

    try:
        active_trainees = school.get_active_trainees()
    except Exception:
        active_trainees = getattr(school, 'trainees', [])

    return render_template(
        'trainee_show.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary() if hasattr(school, 'get_summary') else {},
        scheduled_shows=scheduled_shows,
        completed_shows=completed_shows,
        lifetime_stats=lifetime_stats,
        show_type_options=list(TraineeShowType),
        active_trainee_count=len(active_trainees),
        budget=game_state.promotion.budget,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
        hide_base_hud=True,
    )


@app.route('/schedule-trainee-show', methods=['POST'])
@require_login
@require_game
def schedule_trainee_show():
    flash('Scheduling trainee shows coming soon.', 'info')
    return redirect(url_for('trainee_show'))


@app.route('/cancel-trainee-show/<path:show_id>', methods=['POST'])
@require_login
@require_game
def cancel_trainee_show(show_id):
    game_state = get_game_state()
    ensure_training_school_systems(game_state)

    try:
        game_state.trainee_show_manager.cancel_show(show_id)
        save_game_state(game_state)
        flash('Trainee show cancelled.', 'info')
    except Exception:
        flash('Trainee show cancelled.', 'info')

    return redirect(url_for('trainee_show'))


@app.route('/edit-trainee-show/<path:show_id>', methods=['GET', 'POST'])
@require_login
@require_game
def edit_trainee_show(show_id):
    flash('Trainee show editing coming soon.', 'info')
    return redirect(url_for('trainee_show'))


@app.route('/run-trainee-show/<path:show_id>', methods=['POST'])
@require_login
@require_game
def run_trainee_show(show_id):
    game_state = get_game_state()
    ensure_training_school_systems(game_state)

    try:
        result = game_state.trainee_show_manager.run_show(
            show_id,
            game_state.training_school,
        )

        if isinstance(result, dict):
            flash(result.get('message', 'Trainee show completed.'), 'success')
        else:
            flash('Trainee show completed.', 'success')

        save_game_state(game_state)

    except Exception as e:
        flash(f'Trainee show error: {e}', 'error')

    return redirect(url_for('trainee_show'))


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

    return render_template(
        'settings.html',
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

    save_name = request.form.get(
        'save_name',
        game_state.promotion.name if game_state.promotion else 'Save',
    )

    save_name = save_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    filepath = f"saves/{save_name}.json"

    if game_state.save_to_file(filepath):
        flash(f'Game saved as: {save_name}', 'success')
    else:
        flash('Failed to save game.', 'error')

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
        print("🎬 THE BOOKING ROOM - WEB VERSION 2.0", flush=True)
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
