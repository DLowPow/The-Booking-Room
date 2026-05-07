"""
The Booking Room - Flask Web Application
Wrestling GM Simulator with AI Director, Training School, Storylines,
Rival Promotions, 49 match types, iPhone UI
"""

import os
import uuid
import json
import random
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
from classes.training_school import TrainingSchool, SchoolTier, SCHOOL_TIER_INFO
from classes.coach import CoachManager, CoachSpecialty
from classes.trainee import Trainee, TraineeLevel
from classes.trainee_show import TraineeShowManager, TraineeShowType
from data.trainee_pool import TraineePool
from data.coach_pool import CoachPool
from data.training_classes import (
    get_full_catalog_for_ui, get_school_discount_preview,
    get_class, get_eligible_classes_for_wrestler, get_recommended_classes_for_wrestler,
    roll_performance, calculate_stat_gains, apply_stat_gains_with_ceiling,
    calculate_injury_risk, STAT_CEILING_FROM_TRAINING
)

# ==================== AI IMPORTS ====================
from ai.director import AIDirector, SimpleEvent
from ai.event_generator import EventGenerator, EventSeverity
from ai.voice import VoiceEngine, VoiceContext
from ai.personality import PersonalityType, CreativeControlLevel

# ==================== SYSTEMS ====================
from systems.match_engine import MatchEngine
from systems.weekly_pulse import WeeklyPulse

# ==================== DATA ====================
from data.venues import get_venues_by_continent, get_all_venues, get_venue_by_id
from data.wrestler_pool import WrestlerPool
from data.wrestler_generator import generate_free_agents, get_free_agents_for_level, get_tier_for_level, TIER_CONFIG

# ==================== SAVE MANAGER ====================
from systems.save_manager import SaveManager

# ==================== GAME STATE ====================
from classes.game_state import GameState


app = Flask(__name__)
app.secret_key = 'the_booking_room_alpha_secret_key_2024'


# ==================== ERROR HANDLING ====================

@app.errorhandler(500)
def internal_error(error):
    import traceback
    return f"<h1>500 Error</h1><pre>{traceback.format_exc()}</pre><p>{str(error)}</p>", 500

@app.errorhandler(Exception)
def handle_exception(error):
    import traceback
    return f"<h1>Error</h1><pre>{traceback.format_exc()}</pre><p>{str(error)}</p>", 500


# ==================== ACCESS CONTROL ====================

DEMO_USERS = {
    "dlowpow": "BookingRoomGM26!",
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

def format_money(amount, symbol="$"):
    if amount >= 0:
        return f"{symbol}{amount:,}"
    else:
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
    """Process all weekly systems via the WeeklyPulse orchestrator"""
    promotion = game_state.promotion
    progression = game_state.progression
    week = getattr(promotion, 'current_week', 0)
    year = getattr(promotion, 'current_year', 1)

    # Run the Weekly Pulse (orchestrates ALL systems)
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
                    game_state.inbox.add_message(
                        sender="Banking", subject="Loan Payment",
                        body=msg, week=week, year=year,
                        message_type="financial", icon="🏦",
                    )
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

    return pulse_result, total_salaries


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


# ==================== MAIN ROUTES ====================

@app.route('/')
@require_login
def index():
    saves = SaveManager().list_saves()
    return render_template('index.html', saves=saves)

@app.route('/new-game', methods=['GET', 'POST'])
@require_login
def new_game():
    if request.method == 'POST':
        promoter_name = request.form.get('promoter_name', 'Player')
        promotion_name = request.form.get('promotion_name', 'My Wrestling')
        continent = request.form.get('continent', 'North America')
        country = request.form.get('country', 'United States')
        city = request.form.get('city', 'New York City')
        philosophy_value = request.form.get('philosophy', 'Strong Style')
        creative_control = request.form.get('creative_control') == 'on'
        cc_difficulty = request.form.get('cc_difficulty', 'Normal')

        # Map AI personality from CC difficulty
        ai_personality_map = {
            "Easy": "The Traditionalist",
            "Normal": "The Mastermind",
            "Hard": "The Showman",
        }
        ai_personality = ai_personality_map.get(cc_difficulty, "The Traditionalist")

        # Create game state using the new centralized system
        game_state = GameState()

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
        except Exception as e:
            print(f"Game init error (using fallback): {e}")
            # Fallback: manual initialization
            promotion = Promotion(
                name=promotion_name, philosophy=phil_enum,
                owner_name=promoter_name, starting_budget=0,
                location=f"{city}, {country}",
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
            game_state.championship_manager.setup_default_accolades()
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

            # Generate free agents
            agents = generate_free_agents(count=50, level=1)
            game_state.free_agents = agents

        # Store game settings
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
    game_state = GameState.load_from_file(f"saves/{save_name}.json")
    if game_state:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        game_sessions[session_id] = game_state
        promo_name = game_state.promotion.name if game_state.promotion else "Unknown"
        flash(f'Loaded: {promo_name}', 'success')
        return redirect(url_for('dashboard'))
    flash('Failed to load game!', 'error')
    return redirect(url_for('index'))


# ==================== DASHBOARD ====================

@app.route('/dashboard')
@require_login
@require_game
def dashboard():
    game_state = get_game_state()
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
    level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
    tier = get_promotion_tier(level)
    limits = get_cumulative_limits(level)

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

    return render_template('dashboard.html',
        promotion=promotion, progression=progression,
        level=level, xp_percentage=percentage,
        tier_name=get_tier_name(tier), limits=limits,
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
        has_training_school=game_state.has_training_school(),
        hide_base_hud=True,
    )


# ==================== ORIGIN STORY & TUTORIAL ====================

@app.route('/accept-origin-grant', methods=['POST'])
@require_login
@require_game
def accept_origin_grant():
    game_state = get_game_state()
    if hasattr(game_state, 'origin_story') and game_state.origin_story:
        if not game_state.origin_story.get('accepted', False):
            grant = game_state.origin_story['grant']
            game_state.promotion.budget += grant
            game_state.origin_story['accepted'] = True
            game_state.origin_story['delivered'] = True
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
    limits = get_cumulative_limits(game_state.progression.level)
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
    limits = get_cumulative_limits(game_state.progression.level)
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
        from classes.calendar_system import CalendarSystem
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
    return render_template('wrestler_detail.html', wrestler=wrestler, currency=currency)


@app.route('/release-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def release_wrestler(wrestler_name):
    game_state = get_game_state()
    wrestler = next((w for w in game_state.promotion.roster if w.name == wrestler_name), None)
    if wrestler:
        buyout = int(getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0)) * getattr(wrestler, 'contract_length', 0) * 0.5)
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


# ==================== FREE AGENTS ====================

@app.route('/free-agents')
@require_login
@require_game
def free_agents():
    game_state = get_game_state()
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level if progression else 1)
    roster_limit = limits.get("roster_limit", 5)
    current_roster = len(game_state.promotion.roster)
    can_sign = current_roster < roster_limit
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    # Use FreeAgencyManager if available
    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        fa = game_state.free_agency
        listings = fa.get_all_listings()
        filter_summary = fa.get_filter_summary()

        # Build agents list for template (backwards compatible)
        agents_with_salary = []
        for listing in listings:
            w = listing.wrestler
            agents_with_salary.append({
                "wrestler": w,
                "asking_salary": listing.asking_per_show,
                "signing_bonus": listing.signing_bonus,
                "per_show_rate": listing.asking_per_show,
                "tier": listing.tier.value if hasattr(listing.tier, 'value') else str(listing.tier),
                "tier_name": listing.tier_name,
                "has_contracts": listing.is_exclusive_offer,
                "is_hot_prospect": listing.is_hot_prospect,
                "is_indy_god": listing.is_indy_god,
                "is_licensed": listing.is_licensed,
                "rival_interested": listing.rival_interested,
                "rival_name": listing.rival_promotion_name,
                "status_label": listing.get_status_label(),
                "weeks_remaining": listing.get_weeks_remaining(),
            })
        agents_with_salary.sort(key=lambda x: (-getattr(x["wrestler"], 'popularity', 0),))

        return render_template('free_agents.html',
            agents=agents_with_salary,
            can_sign=can_sign,
            roster_count=current_roster,
            roster_limit=roster_limit,
            budget=game_state.promotion.budget,
            currency=currency,
            total_agents=len(agents_with_salary),
            total_pool=filter_summary.get("total", 0),
            current_week=getattr(game_state.promotion, 'current_week', 0),
            current_year=getattr(game_state.promotion, 'current_year', 1),
        )
    else:
        # Fallback: use raw free_agents list
        agents_with_salary = []
        for w in game_state.free_agents[:20]:
            per_show_rate = 50 + int(getattr(w, 'overall_rating', 50) * 1.3) + int(getattr(w, 'popularity', 30) * 0.5)
            per_show_rate = max(50, min(per_show_rate, 500))
            agents_with_salary.append({
                "wrestler": w,
                "asking_salary": per_show_rate,
                "signing_bonus": 0,
                "per_show_rate": per_show_rate,
                "tier": 1,
                "tier_name": "Free Agent",
                "has_contracts": False,
            })
        return render_template('free_agents.html',
            agents=agents_with_salary,
            can_sign=can_sign,
            roster_count=current_roster,
            roster_limit=roster_limit,
            budget=game_state.promotion.budget,
            currency=currency,
            total_agents=len(agents_with_salary),
            total_pool=len(game_state.free_agents),
            current_week=getattr(game_state.promotion, 'current_week', 0),
            current_year=getattr(game_state.promotion, 'current_year', 1),
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

    # Use FreeAgencyManager if available
    if hasattr(game_state, 'free_agency') and game_state.free_agency:
        fa = game_state.free_agency
        success, message, wrestler, cost_paid = fa.sign_wrestler(
            wrestler_name,
            game_state.promotion.budget,
            len(game_state.promotion.roster),
            roster_limit,
        )
        if success and wrestler:
            game_state.promotion.budget -= cost_paid
            game_state.promotion.roster.append(wrestler)

            # Track in progression
            if progression:
                try:
                    if progression.stats.get("wrestlers_signed_total", 0) == 0:
                        progression.add_xp(100, "First Wrestler Signed!")
                        flash('🎉 First Wrestler Signed! +100 XP', 'success')
                    progression.update_stat("wrestlers_signed_total")
                except Exception:
                    pass

            save_game_state(game_state)
            flash(f'{message}', 'success')
        else:
            flash(f'Cannot sign: {message}', 'error')
    else:
        # Fallback: sign from raw free_agents list
        wrestler = next((w for w in game_state.free_agents if w.name == wrestler_name), None)
        if not wrestler:
            flash('Wrestler not found!', 'error')
            return redirect(url_for('free_agents'))

        per_show_rate = 50 + int(getattr(wrestler, 'overall_rating', 50) * 1.3) + int(getattr(wrestler, 'popularity', 30) * 0.5)
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

    venues = [v for v in all_venues if v.tier.value <= max_tier and v.is_unlocked]
    venues.sort(key=lambda v: v.capacity)

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

    # Get storyline suggestions for booking
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

    # Check booked names
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

    # Create match engine with storyline + relationship integration
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

        result = match_engine.simulate_match(
            wrestler1=w1, wrestler2=w2,
            match_type=match_data.get('match_type', 'Singles'),
            is_title_match=match_data.get('is_title_match', False),
            is_main_event=match_data.get('is_main_event', False),
            match_minutes=time_info['minutes'],
        )

        # Apply production quality modifier
        adjusted_rating = min(5.0, max(0.0, result.match_rating + (production_quality * 0.02)))

        # Determine actual winner for multi-person matches
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
            'finish': result.finish_type.value, 'rating': adjusted_rating,
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

        # Title logic
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

        # Record match for AI Director
        if game_state.ai_director and actual_winner and actual_loser:
            try:
                game_state.ai_director.record_match_result(actual_winner.name, actual_loser.name, adjusted_rating)
            except Exception:
                pass

    avg_rating = total_rating / len(results) if results else 0

    # Time overrun
    available_minutes = venue.get_available_minutes()
    minutes_over = total_show_time - available_minutes
    overrun_penalty = calculate_overrun_penalty(minutes_over)
    overrun_fine = overrun_penalty.get('fine', 0)
    overrun_message = overrun_penalty.get('message', '')
    if minutes_over > 0:
        venue.apply_overrun_penalty(minutes_over, getattr(promotion, 'current_week', 0))
        promotion.budget -= overrun_fine

    # Revenue
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

    # Progression
    show_rewards = progression.process_show_completion(
        is_ppv=False, average_match_rating=avg_rating, attendance=attendance,
        capacity=venue.capacity, venue_prestige=venue.prestige,
        venue_tier=venue.tier.value, venue_id=venue.id,
        five_star_matches=five_star, four_star_matches=four_star,
        ticket_price=revenue_breakdown['tickets'] // max(attendance, 1),
        merchandise_modifier=getattr(promotion, 'merchandise_modifier', 1.0),
        total_matches=len(results),
    ) if progression else {'fans': {'total': 0}, 'xp': {'total': 0}}

    promotion.fan_base += show_rewards['fans']['total']

    # Calendar
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

    venue.record_event(attendance, profit)
    promotion.advance_to_date(show_date['year'], show_date['month'], show_date['day'])
    promotion.advance_days(1)

    # Record show completion for AI Director + News + Storylines
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

    # Clear show
    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    session['show_date'] = None

    # Run weekly pulse
    ai_result, total_salaries = process_week_advancement(game_state)
    save_game_state(game_state)

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    return render_template('run_show.html',
        promotion=promotion, venue=venue, results=results,
        avg_rating=avg_rating, attendance=attendance, is_sellout=is_sellout,
        ticket_revenue=ticket_revenue, merch_revenue=merch_revenue,
        alcohol_revenue=alcohol_revenue, concession_revenue=concession_revenue,
        vip_revenue=vip_revenue,
        venue_cost=venue_cost, production_cost=production_cost,
        profit=profit, xp_earned=show_rewards['xp']['total'],
        fans_earned=show_rewards['fans']['total'] + production_fans,
        leveled_up=show_rewards.get('leveled_up', False),
        new_level=show_rewards.get('new_level', progression.level if progression else 1),
        achievements=show_rewards.get('achievements_earned', []),
        title_changes=title_changes, currency=currency,
        salaries_paid=total_salaries,
        new_events=len(ai_result.get('new_events', []) if isinstance(ai_result, dict) else []),
        new_week=getattr(promotion, 'current_week', 0),
        new_year=promotion.current_year,
        production_quality=production_quality, production_fans=production_fans,
        show_day_name=show_day_name,
        total_show_time=total_show_time, available_minutes=available_minutes,
        overrun_fine=overrun_fine, overrun_message=overrun_message,
        minutes_over=minutes_over,
    )


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

# ==================== EVENTS ====================

@app.route('/events')
@require_login
@require_game
def events():
    game_state = get_game_state()
    ai_director = game_state.ai_director
    if not ai_director:
        return redirect(url_for('dashboard'))
    all_events = ai_director.get_active_events()
    return render_template('events.html', events=all_events, promotion=game_state.promotion)


@app.route('/resolve-event/<path:event_id>/<int:option_index>', methods=['POST'])
@require_login
@require_game
def resolve_event(event_id, option_index):
    game_state = get_game_state()
    ai_director = game_state.ai_director
    promotion = game_state.promotion

    result = ai_director.resolve_event(event_id, option_index)
    if result['success']:
        effects = result.get('effects', {})

        if effects.get('release_w1') or effects.get('release'):
            event = result.get('event')
            if event:
                names = getattr(event, 'wrestlers_involved', [])
                for name in names:
                    game_state.remove_wrestler_from_roster(name, mark_as_indy_god=False)

        if effects.get('money'):
            promotion.budget += effects['money']
        if effects.get('salary_change') or effects.get('salary_w1'):
            change = effects.get('salary_change', effects.get('salary_w1', 0))
            event = result.get('event')
            if event:
                for name in getattr(event, 'wrestlers_involved', []):
                    w = game_state.get_wrestler_by_name(name)
                    if w:
                        w.booking_fee = getattr(w, 'booking_fee', 0) + change
                        break
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
            for w in game_state.roster:
                if hasattr(w, 'adjust_morale'):
                    w.adjust_morale(effects['morale_all'])
        if effects.get('fan_bonus'):
            promotion.fan_base = max(0, promotion.fan_base + effects['fan_bonus'])
        if effects.get('prestige'):
            promotion.prestige = max(0, min(100, promotion.prestige + effects['prestige']))

        save_game_state(game_state)
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
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

    # Tournaments (with safe fallback)
    tournaments = []
    try:
        if hasattr(champ_manager, 'get_active_tournaments'):
            tournaments = champ_manager.get_active_tournaments()
        if hasattr(champ_manager, 'get_planning_tournaments'):
            tournaments += champ_manager.get_planning_tournaments()
    except Exception:
        pass

    # Accolades (with safe fallback)
    accolades = []
    try:
        accolades = getattr(champ_manager, 'accolades', []) or []
    except Exception:
        pass

    # Next slot cost (with safe fallback)
    next_slot_cost = 0
    try:
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

        championship = champ_manager.create_championship(name=name, level=level_enum, gender=gender_enum, rules=rules_enum)
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

    success, cost, new_total = champ_manager.unlock_slot(promotion.budget)
    if success:
        promotion.budget -= cost
        save_game_state(game_state)
        flash(f'Unlocked championship slot {new_total}! Cost: ${cost:,}', 'success')
    else:
        flash(f'Cannot unlock slot. Need ${cost:,}', 'error')
    return redirect(url_for('championships'))


@app.route('/award-title/<path:championship_id>', methods=['GET', 'POST'])
@require_login
@require_game
def award_title(championship_id):
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

    if request.method == 'POST':
        wrestler_name = request.form.get('wrestler')
        tag_partner = request.form.get('tag_partner', '')
        if not wrestler_name:
            flash('Please select a wrestler!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        date_str = format_date(promotion.current_year, promotion.current_month, promotion.current_day)
        championship.award_title(wrestler_name, date_str, tag_partner=tag_partner if is_tag_title else "")

        w = game_state.get_wrestler_by_name(wrestler_name)
        if w and hasattr(w, 'win_championship'):
            w.win_championship()

        save_game_state(game_state)
        flash(f'{wrestler_name} is the new {championship.name}!', 'success')
        return redirect(url_for('championships'))

    eligible = [w for w in game_state.roster if not getattr(w, 'is_injured', False)]
    eligible.sort(key=lambda w: getattr(w, 'popularity', 0), reverse=True)
    return render_template('award_title.html', championship=championship, wrestlers=eligible, is_tag_title=is_tag_title)


@app.route('/vacate-title/<path:championship_id>', methods=['POST'])
@require_login
@require_game
def vacate_title(championship_id):
    game_state = get_game_state()
    champ_manager = game_state.championship_manager
    if champ_manager:
        championship = champ_manager.get_championship(championship_id)
        if championship:
            championship.vacate("Vacated by management")
            save_game_state(game_state)
            flash(f'{championship.name} has been vacated!', 'info')
    return redirect(url_for('championships'))


# ==================== CAREER / PROFILE ====================

@app.route('/career')
@require_login
@require_game
def career():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
    tier = get_promotion_tier(level)
    earned_achievements = progression.get_earned_achievements() if hasattr(progression, 'get_earned_achievements') else []
    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    return render_template('career.html',
        promotion=promotion, progression=progression,
        level=level, tier_name=get_tier_name(tier),
        xp_percentage=percentage,
        stats=progression.stats if hasattr(progression, 'stats') else {},
        achievements=earned_achievements,
        total_achievements=len(progression.achievements) if hasattr(progression, 'achievements') else 0,
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

    messages = game_state.inbox.get_inbox()
    unread_count = game_state.inbox.get_unread_count()
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

    game_state.inbox.mark_read(msg_id)
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
        game_state.inbox.mark_all_read()
        save_game_state(game_state)
        flash('All messages marked as read.', 'success')
    return redirect(url_for('inbox'))


# ==================== CALLS ====================

@app.route('/calls')
@require_login
@require_game
def calls_app():
    game_state = get_game_state()

    # Ensure calls manager exists
    if not hasattr(game_state, 'calls') or game_state.calls is None:
        try:
            from classes.calls import CallsManager
            game_state.calls = CallsManager()
            save_game_state(game_state)
        except ImportError:
            pass

    # Build context for template
    calls_data = {
        "incoming": [],
        "answered": [],
        "missed": [],
    }
    contacts = []
    incoming_count = 0

    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            calls_data["incoming"] = game_state.calls.get_incoming_calls()
            calls_data["answered"] = game_state.calls.get_answered_calls()[:10]
            calls_data["missed"] = game_state.calls.get_missed_calls()[:10]
            contacts = game_state.calls.get_all_contacts()
            incoming_count = game_state.calls.get_incoming_count()
        except Exception:
            pass

    # Also include loan shark info for backwards compatibility
    shark_options = []
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

    result = game_state.calls.answer_call(call_id, option_index)
    if result.get('success'):
        effects = result.get('effects', {})
        if effects.get('money') and game_state.promotion:
            game_state.promotion.budget += effects['money']
        save_game_state(game_state)
        flash(result.get('message', 'Call answered'), 'success')
    else:
        flash(result.get('message', 'Error'), 'error')
    return redirect(url_for('calls_app'))


@app.route('/decline-call/<path:call_id>', methods=['POST'])
@require_login
@require_game
def decline_call(call_id):
    game_state = get_game_state()
    if hasattr(game_state, 'calls') and game_state.calls:
        game_state.calls.decline_call(call_id)
        save_game_state(game_state)
        flash('Call declined.', 'info')
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
    can_bank, bank_reason = bm.can_take_loan(LoanType.BANK)
    return render_template('banking.html',
        promotion=game_state.promotion,
        budget=game_state.promotion.budget,
        credit_score=bm.credit_score,
        credit_rating=bm.get_credit_rating(),
        credit_color=bm.get_credit_color(),
        total_outstanding=bm.get_total_outstanding(),
        weekly_obligations=bm.get_total_weekly_obligations(),
        active_loans=bm.active_loans,
        loan_history=bm.loan_history,
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
        active_injuries=im.active_injuries if hasattr(im, 'active_injuries') else [],
        injury_history=im.injury_history if hasattr(im, 'injury_history') else [],
        hide_base_hud=True,
    )

# ==================== WRITERS ROOM ====================

@app.route('/create-storyline', methods=['GET', 'POST'])
@require_login
@require_game
def create_storyline():
    flash('Storyline creation coming soon!', 'info')
    return redirect(url_for('writers_room'))

@app.route('/storyline-detail/<path:storyline_id>')
@require_login
@require_game
def storyline_detail(storyline_id):
    flash('Storyline details coming soon!', 'info')
    return redirect(url_for('writers_room'))

@app.route('/approve-storyline/<path:storyline_id>', methods=['POST'])
@require_login
@require_game
def approve_storyline(storyline_id):
    game_state = get_game_state()
    if hasattr(game_state, 'storyline_engine') and game_state.storyline_engine:
        try:
            game_state.storyline_engine.approve_storyline(storyline_id)
            save_game_state(game_state)
            flash('Storyline approved!', 'success')
        except Exception as e:
            flash(f'Could not approve: {e}', 'error')
    else:
        flash('Storyline system not available.', 'warning')
    return redirect(url_for('writers_room'))

@app.route('/reject-storyline/<path:storyline_id>', methods=['POST'])
@require_login
@require_game
def reject_storyline(storyline_id):
    game_state = get_game_state()
    if hasattr(game_state, 'storyline_engine') and game_state.storyline_engine:
        try:
            game_state.storyline_engine.reject_storyline(storyline_id)
            save_game_state(game_state)
            flash('Storyline passed.', 'info')
        except Exception:
            pass
    return redirect(url_for('writers_room'))

@app.route('/hire-writer/<path:writer_id>', methods=['POST'])
@require_login
@require_game
def hire_writer(writer_id):
    flash('Writer hiring coming soon!', 'info')
    return redirect(url_for('writers_room'))

@app.route('/hire-freelancer/<path:writer_id>', methods=['POST'])
@require_login
@require_game
def hire_freelancer(writer_id):
    flash('Freelancer hiring coming soon!', 'info')
    return redirect(url_for('writers_room'))

@app.route('/fire-writer/<path:writer_id>', methods=['POST'])
@require_login
@require_game
def fire_writer(writer_id):
    flash('Writer release coming soon!', 'info')
    return redirect(url_for('writers_room'))

@app.route('/purchase-storyline/<path:item_id>', methods=['POST'])
@require_login
@require_game
def purchase_storyline(item_id):
    flash('Storyline purchase coming soon!', 'info')
    return redirect(url_for('writers_room'))

# ==================== TRAINING SCHOOL ====================

@app.route('/training-school')
@require_login
@require_game
def training_school():
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        from classes.training_school import TrainingSchool
        school = TrainingSchool()
        game_state.training_school = school

    summary = school.get_summary() if school.is_founded() else {}
    active_trainees = school.get_active_trainees() if school.is_founded() else []

    # Get counts for badges
    applicant_count = game_state.trainee_pool.get_applicant_count() if game_state.trainee_pool else 0
    coach_count = game_state.coach_manager.get_coach_count() if game_state.coach_manager else 0
    active_classes = 0  # TODO: track active enrollments
    scheduled_shows = 0
    if game_state.trainee_show_manager:
        scheduled_shows = len(game_state.trainee_show_manager.get_scheduled_shows())

    # Next tier info
    next_tier_info = None
    upgrade_cost = 0
    if school.is_founded() and school.can_upgrade():
        next_tier = school.get_next_tier()
        if next_tier:
            from classes.training_school import SCHOOL_TIER_INFO
            next_tier_info = SCHOOL_TIER_INFO.get(next_tier, {})
            upgrade_cost = school.get_upgrade_cost()

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
    game_state = get_game_state()
    school = game_state.training_school

    if request.method == 'POST':
        school_name = request.form.get('school_name', 'Wrestling School')
        school_location = request.form.get('school_location', '')
        tier_key = request.form.get('tier', 'SCHOOL_GYM')

        from classes.training_school import SchoolTier, SCHOOL_TIER_INFO
        try:
            tier = SchoolTier[tier_key]
        except (KeyError, ValueError):
            flash('Invalid school tier!', 'error')
            return redirect(url_for('training_school'))

        cost = SCHOOL_TIER_INFO[tier]["purchase_cost"]
        if game_state.promotion.budget < cost:
            flash(f'Cannot afford! Need ${cost:,}', 'error')
            return redirect(url_for('found_training_school'))

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

        flash('Failed to found school!', 'error')
        return redirect(url_for('found_training_school'))

    purchase_options = school.get_purchase_options()
    return render_template('found_school.html',
        promotion=game_state.promotion,
        purchase_options=purchase_options,
        hide_base_hud=True,
    )


@app.route('/trainee-recruitment')
@require_login
@require_game
def trainee_recruitment():
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('Found a training school first!', 'warning')
        return redirect(url_for('training_school'))

    available_applicants = game_state.trainee_pool.get_available_applicants() if game_state.trainee_pool else []
    scouting_options = game_state.trainee_pool.get_scouting_options() if game_state.trainee_pool else []
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
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

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
    return redirect(url_for('trainee_recruitment'))


@app.route('/reject-applicant/<path:applicant_id>', methods=['POST'])
@require_login
@require_game
def reject_applicant(applicant_id):
    game_state = get_game_state()
    if game_state.trainee_pool:
        game_state.trainee_pool.remove_applicant(applicant_id)
        save_game_state(game_state)
    return redirect(url_for('trainee_recruitment'))


@app.route('/scout-for-trainee', methods=['POST'])
@require_login
@require_game
def scout_for_trainee():
    game_state = get_game_state()
    school = game_state.training_school
    tier = request.form.get('tier', 'promising')

    if not game_state.trainee_pool or not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    applicant, cost, message = game_state.trainee_pool.scout_for_prospects(
        scouting_tier=tier,
        budget=game_state.promotion.budget,
        monthly_tuition=school.get_monthly_tuition(),
    )
    if cost > 0:
        game_state.promotion.budget -= cost
    save_game_state(game_state)
    flash(message, 'success' if applicant else 'warning')
    return redirect(url_for('trainee_recruitment'))


@app.route('/view-trainees')
@require_login
@require_game
def view_trainees():
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        flash('No school!', 'warning')
        return redirect(url_for('training_school'))

    trainees = school.trainees
    active_count = school.get_active_trainee_count()
    graduated_count = len(school.get_graduated_trainees())

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
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if not trainee:
        flash('Trainee not found!', 'error')
        return redirect(url_for('view_trainees'))

    # Convert to wrestler and add to roster
    wrestler_data = trainee.to_wrestler_data()
    from classes.wrestler import Wrestler, Gender, WrestlingStyle, Alignment, WrestlerLevel, ContractType
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
        **{k: v for k, v in wrestler_data.items() if k in [
            "strength", "speed", "technique", "charisma",
            "stamina", "toughness", "mic_skills", "psychology",
        ]},
    )

    game_state.roster.append(wrestler)
    school.add_alumni(trainee, "signed_main")
    school.remove_trainee(trainee_id, "graduated")
    save_game_state(game_state)
    flash(f'{trainee.name} signed to main roster!', 'success')
    return redirect(url_for('view_trainees'))


@app.route('/release-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def release_trainee(trainee_id):
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if trainee:
        school.add_alumni(trainee, "released_indies")
        school.remove_trainee(trainee_id, "dropped_out")
        save_game_state(game_state)
        flash(f'{trainee.name} released to the indies.', 'info')
    return redirect(url_for('view_trainees'))


@app.route('/expel-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def expel_trainee(trainee_id):
    game_state = get_game_state()
    school = game_state.training_school
    if not school:
        flash('No school!', 'error')
        return redirect(url_for('training_school'))

    trainee = school.get_trainee(trainee_id)
    if trainee:
        school.add_alumni(trainee, "expelled")
        school.remove_trainee(trainee_id, "dropped_out")
        school.modify_reputation(-5)
        save_game_state(game_state)
        flash(f'{trainee.name} expelled! School reputation -5.', 'warning')
    return redirect(url_for('view_trainees'))


@app.route('/roster-training')
@require_login
@require_game
def roster_training():
    game_state = get_game_state()
    school = game_state.training_school

    available_wrestlers = [
        {"id": w.name, "name": w.name, "overall_rating": w.overall_rating,
         "level_number": getattr(w, 'level_number', 1)}
        for w in game_state.roster if not getattr(w, 'is_injured', False)
    ]

    catalog = get_full_catalog_for_ui(school if school and school.is_founded() else None)
    discount_preview = get_school_discount_preview(school if school and school.is_founded() else None)
    max_concurrent = school.get_max_concurrent_classes() if school and school.is_founded() else 1
    school_summary = school.get_summary() if school and school.is_founded() else {}

    return render_template('roster_training.html',
        promotion=game_state.promotion,
        school_summary=school_summary,
        discount_preview=discount_preview,
        catalog=catalog,
        available_wrestlers=available_wrestlers,
        active_enrollments=[],
        max_concurrent=max_concurrent,
        recommendations=[],
        hide_base_hud=True,
    )


@app.route('/coach-management')
@require_login
@require_game
def coach_management():
    game_state = get_game_state()
    school = game_state.training_school

    my_coaches = game_state.coach_manager.get_all_coaches() if game_state.coach_manager else []
    available_coaches = game_state.coach_pool.get_available_coaches() if game_state.coach_pool else []
    legendary_coaches = game_state.coach_pool.get_legendary_coaches() if game_state.coach_pool else []
    payroll = game_state.coach_manager.get_payroll_summary(school) if game_state.coach_manager else {}
    max_slots = school.get_coach_slots() if school and school.is_founded() else 0

    school_tier_discount = 0
    if school and school.is_founded():
        from classes.coach import SCHOOL_TIER_PAYROLL_DISCOUNT
        school_tier_discount = SCHOOL_TIER_PAYROLL_DISCOUNT.get(school.tier.value, 0)

    eligible_veterans = [
        {"id": w.name, "name": w.name, "age": getattr(w, 'age', 30),
         "overall_rating": w.overall_rating, "level_number": getattr(w, 'level_number', 1),
         "strength": getattr(w, 'power', 50), "speed": getattr(w, 'speed', 50),
         "technique": getattr(w, 'technical', 50), "mic_skills": getattr(w, 'mic_skills', 50),
         "psychology": getattr(w, 'psychology', 50)}
        for w in game_state.roster
        if getattr(w, 'level_number', 1) >= 8
    ]

    from classes.coach import CoachSpecialty
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
    game_state = get_game_state()
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
    return redirect(url_for('coach_management'))


@app.route('/fire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def fire_coach(coach_id):
    game_state = get_game_state()
    if game_state.coach_manager:
        game_state.coach_manager.fire_coach(coach_id)
        save_game_state(game_state)
        flash('Coach released.', 'info')
    return redirect(url_for('coach_management'))


@app.route('/school-settings', methods=['GET'])
@require_login
@require_game
def school_settings():
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
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        tuition = int(request.form.get('tuition', school.get_recommended_tuition()))
        success, msg = school.set_tuition(tuition)
        save_game_state(game_state)
        flash(msg, 'success' if success else 'error')
    return redirect(url_for('school_settings'))


@app.route('/update-school-class-markup', methods=['POST'])
@require_login
@require_game
def update_school_class_markup():
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        markup = int(request.form.get('markup', 0))
        success, msg = school.set_class_markup(markup)
        save_game_state(game_state)
        flash(msg, 'success' if success else 'error')
    return redirect(url_for('school_settings'))


@app.route('/update-school-identity', methods=['POST'])
@require_login
@require_game
def update_school_identity():
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        school.name = request.form.get('school_name', school.name)
        school.location = request.form.get('school_location', school.location)
        save_game_state(game_state)
        flash('School details updated.', 'success')
    return redirect(url_for('school_settings'))


@app.route('/reset-school-pricing', methods=['POST'])
@require_login
@require_game
def reset_school_pricing():
    game_state = get_game_state()
    school = game_state.training_school
    if school and school.is_founded():
        school.current_tuition = school.get_recommended_tuition()
        school.class_markup_percent = 0
        school.rates_customized = False
        save_game_state(game_state)
        flash('Pricing reset to defaults.', 'success')
    return redirect(url_for('school_settings'))


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

    if school.can_upgrade():
        next_tier = school.get_next_tier()
        if next_tier:
            from classes.training_school import SCHOOL_TIER_INFO
            next_tier_info = SCHOOL_TIER_INFO.get(next_tier, {})
            upgrade_cost = school.get_upgrade_cost()

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
        cost = school.get_upgrade_cost()
        if game_state.promotion.budget >= cost:
            game_state.promotion.budget -= cost
            success, msg = school.start_upgrade()
            save_game_state(game_state)
            flash(msg, 'success' if success else 'error')
        else:
            flash(f'Need ${cost:,} to upgrade!', 'error')
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
        alumni_count=school.get_alumni_count(),
        alumni=school.alumni,
        hide_base_hud=True,
    )


@app.route('/trainee-shows')
@require_login
@require_game
def book_trainee_show():
    game_state = get_game_state()
    school = game_state.training_school
    if not school or not school.is_founded():
        return redirect(url_for('training_school'))

    tsm = game_state.trainee_show_manager
    scheduled_shows = tsm.get_scheduled_shows() if tsm else []
    completed_shows = tsm.get_completed_shows() if tsm else []
    lifetime_stats = tsm.get_lifetime_stats() if tsm else {}

    active_trainees = school.get_active_trainees()
    active_trainee_count = len(active_trainees)

    show_type_options = []
    if tsm:
        show_type_options = tsm.get_show_type_options(
            school_tier_name=school.tier.value,
            school_reputation=school.reputation,
            active_trainees=active_trainees,
        )

    return render_template('trainee_show.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary(),
        scheduled_shows=scheduled_shows,
        completed_shows=completed_shows,
        lifetime_stats=lifetime_stats,
        show_type_options=show_type_options,
        active_trainee_count=active_trainee_count,
        hide_base_hud=True,
    )


# ==================== SETTINGS ====================

@app.route('/settings')
@require_login
@require_game
def settings_page():
    game_state = get_game_state()
    ai_info = game_state.get_ai_director_info() if game_state.ai_director else None
    return render_template('settings.html',
        promotion=game_state.promotion,
        ai_director_info=ai_info,
        has_training_school=game_state.has_training_school(),
        hide_base_hud=True,
    )


# ==================== TUTORIAL ====================

@app.route('/tutorial')
@require_login
def tutorial():
    return render_template('tutorial.html')


# ==================== SAVE / QUIT ====================

@app.route('/save-game', methods=['POST'])
@require_login
@require_game
def save_game():
    game_state = get_game_state()
    save_name = request.form.get('save_name', game_state.promotion.name if game_state.promotion else 'Save')
    save_name = save_name.replace(' ', '_')

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
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') != 'production'
    print("\n" + "=" * 50)
    print("🎬 THE BOOKING ROOM - WEB VERSION")
    print("=" * 50)
    print(f"\nStarting server on port {port}...")
    print(f"Open your browser to: http://127.0.0.1:{port}")
    print("=" * 50 + "\n")
    app.run(debug=debug, host='0.0.0.0', port=port)
