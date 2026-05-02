"""
The Booking Room - Flask Web Application
49 match types with categories, variable participants,
no_dq = intergender, $0 start with origin stories,
10 tiers (100 levels), venue time/perks/restrictions,
match time allocation, overrun penalties, seasonal events
"""

import os
import uuid
import json
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps

from classes.wrestler import Wrestler
from classes.promotion import Promotion
from classes.enums import Philosophy, WrestlingStyle, Gender, Alignment
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
from classes.philosophy import get_philosophy_profile, PHILOSOPHY_PROFILES
from classes.championship import (
    ChampionshipManager, Championship, ChampionshipLevel,
    ChampionshipGender, ChampionshipRule, CHAMPIONSHIP_COSTS, SLOT_COSTS,
    TournamentStatus
)
from classes.production import (
    ShowProduction, get_available_options,
    RING_OPTIONS, LIGHTING_OPTIONS, CAMERA_OPTIONS,
    BACKSTAGE_OPTIONS, PYRO_OPTIONS, ENTRANCE_OPTIONS, AUDIO_OPTIONS
)
from classes.calendar_system import CalendarSystem, MONTHS, format_date, days_in_month, date_to_day_of_year
from systems.match_engine import MatchEngine
from systems.save_manager import GameState, SaveManager
from ai.director import AIDirector
from ai.event_generator import EventSeverity
from data.venues import get_venues_by_continent, get_all_venues, get_venue_by_id
from data.wrestler_generator import (
    generate_free_agents, generate_all_free_agents,
    generate_wrestler_for_tier, get_tier_for_level, TIER_CONFIG
)

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


# ==================== GAME STATE ====================

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


# ==================== DAY OF WEEK HELPER ====================

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


# ==================== SEASONAL EVENTS ====================

def get_active_seasonal_events(month, day):
    events = []
    if month == 4 and 8 <= day <= 14:
        events.append({"name": "🏟️ Mania Weekend", "description": "Fans are in town for WrestleMania! Double XP and crowd boost!", "xp_multiplier": 2.0, "attendance_multiplier": 1.5, "fan_growth_multiplier": 2.0, "color": "#f59e0b", "icon": "🏟️"})
    if month == 8 and 24 <= day <= 31:
        events.append({"name": "☀️ SummerSlam Week", "description": "Summer wrestling fever! Bonus fan growth!", "xp_multiplier": 1.5, "attendance_multiplier": 1.3, "fan_growth_multiplier": 1.5, "color": "#ef4444", "icon": "☀️"})
    if month == 1 and 15 <= day <= 21:
        events.append({"name": "👑 Rumble Season", "description": "Royal Rumble hype! Extra attendance boost!", "xp_multiplier": 1.3, "attendance_multiplier": 1.4, "fan_growth_multiplier": 1.3, "color": "#6366f1", "icon": "👑"})
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
        "Triple Threat": {"category": "Standard", "min": 3, "max": 3, "type": "multi", "label": "3-Way", "intergender": True, "no_dq": True, "description": "Three-way, no DQ by default"},
        "Fatal Four Way": {"category": "Standard", "min": 4, "max": 4, "type": "multi", "label": "4-Way", "intergender": True, "no_dq": True, "description": "Four-way, no DQ by default"},
        "5-Way Match": {"category": "Standard", "min": 5, "max": 5, "type": "multi", "label": "5-Way", "intergender": True, "no_dq": True, "description": "Five-way, no DQ"},
        "6-Way Match": {"category": "Standard", "min": 6, "max": 6, "type": "multi", "label": "6-Way", "intergender": True, "no_dq": True, "description": "Six-way, no DQ"},
        "8-Way Match": {"category": "Standard", "min": 8, "max": 8, "type": "multi", "label": "8-Way", "intergender": True, "no_dq": True, "description": "Eight-way, no DQ"},
        "Tag Team": {"category": "Tag", "min": 4, "max": 4, "type": "tag", "label": "2v2", "intergender": False, "no_dq": False, "description": "Standard tag team match", "teams": [2, 2]},
        "Mixed Tag": {"category": "Tag", "min": 4, "max": 4, "type": "tag", "label": "2v2", "intergender": True, "no_dq": False, "description": "Intergender tag team match", "teams": [2, 2]},
        "Tornado Tag": {"category": "Tag", "min": 4, "max": 4, "type": "tag", "label": "2v2 Tornado", "intergender": True, "no_dq": True, "description": "All wrestlers legal at once, no DQ", "teams": [2, 2]},
        "6-Man Tag": {"category": "Tag", "min": 6, "max": 6, "type": "tag3", "label": "3v3", "intergender": False, "no_dq": False, "description": "Three-on-three tag team", "teams": [3, 3]},
        "8-Man Tag": {"category": "Tag", "min": 8, "max": 8, "type": "tag4", "label": "4v4", "intergender": False, "no_dq": False, "description": "Four-on-four tag team", "teams": [4, 4]},
        "1-on-2 Handicap": {"category": "Tag", "min": 3, "max": 3, "type": "handicap", "label": "1v2", "intergender": False, "no_dq": False, "description": "One wrestler vs team of two", "teams": [1, 2]},
        "1-on-3 Handicap": {"category": "Tag", "min": 4, "max": 4, "type": "handicap", "label": "1v3", "intergender": False, "no_dq": False, "description": "One wrestler vs team of three", "teams": [1, 3]},
        "2-on-3 Handicap": {"category": "Tag", "min": 5, "max": 5, "type": "handicap", "label": "2v3", "intergender": False, "no_dq": False, "description": "Two vs three", "teams": [2, 3]},
        "Extreme Rules": {"category": "Hardcore", "min": 2, "max": 5, "type": "variable", "label": "No DQ", "intergender": True, "no_dq": True, "description": "No disqualification, no count-out"},
        "Falls Count Anywhere": {"category": "Hardcore", "min": 2, "max": 6, "type": "variable", "label": "FCA", "intergender": True, "no_dq": True, "description": "Pinfalls anywhere in the arena"},
        "Ladder Match": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Ladder", "intergender": True, "no_dq": True, "description": "Climb the ladder to retrieve the prize"},
        "Table Match": {"category": "Hardcore", "min": 2, "max": 6, "type": "variable", "label": "Tables", "intergender": True, "no_dq": True, "description": "Put opponent through a table to win"},
        "TLC": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "TLC", "intergender": True, "no_dq": True, "description": "Tables, Ladders and Chairs"},
        "Barbed Wire Deathmatch": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Deathmatch", "intergender": True, "no_dq": True, "description": "Ring ropes replaced with barbed wire"},
        "Exploding Barbed Wire": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Deathmatch", "intergender": True, "no_dq": True, "description": "Explosive barbed wire ropes"},
        "Landmine Deathmatch": {"category": "Hardcore", "min": 2, "max": 8, "type": "variable", "label": "Deathmatch", "intergender": True, "no_dq": True, "description": "Explosive boards surrounding the ring"},
        "Steel Cage": {"category": "Cage", "min": 2, "max": 8, "type": "variable", "label": "Cage", "intergender": True, "no_dq": True, "description": "Escape or pin inside a steel cage"},
        "Hell in a Cell": {"category": "Cage", "min": 2, "max": 6, "type": "variable", "label": "HIAC", "intergender": True, "no_dq": True, "description": "Enclosed in a massive cell structure"},
        "Elimination Chamber": {"category": "Cage", "min": 6, "max": 6, "type": "multi", "label": "Chamber", "intergender": True, "no_dq": True, "description": "Six wrestlers, pods, elimination rules"},
        "War Games": {"category": "Cage", "min": 6, "max": 8, "type": "wargames", "label": "War Games", "intergender": True, "no_dq": True, "description": "Two rings, one cage, team warfare", "teams": [3, 3]},
        "Ambulance Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Load opponent into an ambulance"},
        "Casket Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Lock opponent in a casket"},
        "Dumpster Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Throw opponent in a dumpster"},
        "I Quit": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Force opponent to say I Quit"},
        "Inferno Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Ring surrounded by fire"},
        "Iron Man": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": False, "no_dq": False, "description": "Most falls in a time limit wins"},
        "Last Man Standing": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Keep opponent down for a 10-count"},
        "Submission Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": False, "no_dq": False, "description": "Win only by submission"},
        "3 Stages of Hell": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "Best of three falls, different stipulations"},
        "Underground Match": {"category": "Specialty", "min": 2, "max": 2, "type": "singles", "label": "1v1", "intergender": True, "no_dq": True, "description": "No rules, no ring, anything goes"},
        "Bloodline Rules": {"category": "Specialty", "min": 2, "max": 8, "type": "variable", "label": "Bloodline", "intergender": True, "no_dq": True, "description": "Special tribal rules, no DQ"},
        "Brawl": {"category": "Specialty", "min": 2, "max": 4, "type": "variable", "label": "Brawl", "intergender": True, "no_dq": True, "description": "No ring, no rules, just fight"},
        "Lumberjack Match": {"category": "Specialty", "min": 2, "max": 8, "type": "variable", "label": "Lumberjack", "intergender": True, "no_dq": True, "description": "Ringside surrounded by other wrestlers"},
        "Special Guest Referee": {"category": "Specialty", "min": 3, "max": 7, "type": "referee", "label": "Guest Ref", "intergender": False, "no_dq": False, "description": "A wrestler acts as special referee"},
        "Battle Royal": {"category": "Battle Royal", "min": 4, "max": 8, "type": "rumble", "label": "Battle Royal", "intergender": True, "no_dq": True, "description": "Over the top rope elimination"},
        "Casino Battle Royale": {"category": "Battle Royal", "min": 8, "max": 21, "type": "rumble", "label": "Casino BR", "intergender": True, "no_dq": True, "description": "Timed entry battle royal"},
        "Royal Rumble": {"category": "Battle Royal", "min": 10, "max": 30, "type": "rumble", "label": "Rumble", "intergender": True, "no_dq": True, "description": "Timed entry elimination"},
        "Gauntlet Match": {"category": "Battle Royal", "min": 4, "max": 30, "type": "gauntlet", "label": "Gauntlet", "intergender": True, "no_dq": True, "description": "Sequential one-on-one matches"},
        "Gauntlet Eliminator": {"category": "Battle Royal", "min": 4, "max": 8, "type": "gauntlet", "label": "Eliminator", "intergender": True, "no_dq": True, "description": "Short format gauntlet"},
        "MMA Rules": {"category": "Combat", "min": 2, "max": 2, "type": "singles", "label": "MMA", "intergender": False, "no_dq": False, "description": "Mixed martial arts rules"},
        "Kickboxing Rules": {"category": "Combat", "min": 2, "max": 2, "type": "singles", "label": "Kickboxing", "intergender": False, "no_dq": False, "description": "Kickboxing rules, standing strikes only"},
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
        t1_size = teams[0]
        t2_size = teams[1]
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
        if len(names) <= 4:
            return " vs ".join(names)
        else:
            return f"{names[0]} vs {names[1]} + {len(names) - 2} others"
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


# ==================== WEEK HELPER ====================

def process_week_advancement(game_state):
    promotion = game_state.promotion
    progression = game_state.progression
    ai_director = game_state.ai_director
    total_salaries = sum(w.salary for w in promotion.roster)
    promotion.budget -= total_salaries
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        maintenance = game_state.championship_manager.get_total_maintenance_cost()
        promotion.budget -= maintenance
        game_state.championship_manager.weekly_update()
    for wrestler in promotion.roster:
        wrestler.weekly_update()
    roster_data = [{"name": w.name, "ego": w.ego, "loyalty": w.loyalty, "professionalism": w.professionalism, "morale": w.morale, "popularity": w.popularity, "salary": w.salary, "contract_length": w.contract_length, "is_injured": w.is_injured, "age": w.age, "momentum": w.momentum, "wins": w.wins, "losses": w.losses} for w in promotion.roster]
    ai_result = {"new_events": []}
    if ai_director:
        ai_result = ai_director.process_weekly_update(roster=roster_data, budget=promotion.budget, fans=promotion.fan_base, prestige=promotion.prestige, current_week=promotion.current_week)
    if progression:
        progression.process_weekly_update(active_wrestlers=len([w for w in promotion.roster if not w.is_injured]), total_fans=promotion.fan_base, current_budget=promotion.budget, weekly_profit=-total_salaries, roster_size=len(promotion.roster))
    highest_tier = get_tier_for_level(progression.level if progression else 1)
    used_names = {w.name for w in game_state.free_agents}
    used_names.update({w.name for w in promotion.roster})
    num_new = random.randint(3, 6)
    for _ in range(num_new):
        available_tiers = [t for t in range(1, highest_tier + 1)]
        tier_weights = {1: 50, 2: 30, 3: 15, 4: 4, 5: 1}
        weights = [tier_weights.get(t, 10) for t in available_tiers]
        tier = random.choices(available_tiers, weights=weights, k=1)[0]
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        wrestler = generate_wrestler_for_tier(tier, gender, used_names)
        game_state.free_agents.append(wrestler)
        used_names.add(wrestler.name)
    max_pool = 80
    if len(game_state.free_agents) > max_pool:
        num_remove = len(game_state.free_agents) - max_pool
        for _ in range(num_remove):
            if len(game_state.free_agents) > 20:
                idx = random.randint(0, len(game_state.free_agents) - 1)
                game_state.free_agents.pop(idx)
    game_state.weekly_agent_names = []
    game_state.weekly_agents_week = ""
    return ai_result, total_salaries


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
    save_manager = SaveManager()
    saves = save_manager.list_saves()
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
        game_state = GameState()
        game_state.promoter_name = promoter_name
        phil_enum = Philosophy.STRONG_STYLE
        for p in Philosophy:
            if p.value == philosophy_value:
                phil_enum = p
                break
        profile = get_philosophy_profile(phil_enum)
        currency_code, currency_symbol = get_currency(country)
        promotion = Promotion(name=promotion_name, philosophy=phil_enum, owner_name=promoter_name, starting_budget=0, location=f"{city}, {country}")
        promotion.fan_base = 0
        promotion.budget = 0
        promotion.prestige = profile.prestige_start
        promotion.merchandise_modifier = profile.merchandise_modifier
        game_state.promotion = promotion
        game_state.game_settings = {"continent": continent, "country": country, "city": city, "currency_code": currency_code, "currency_symbol": currency_symbol, "creative_control_enabled": creative_control, "creative_control_difficulty": cc_difficulty, "show_day": "Saturday"}
        game_state.progression = ProgressionSystem()
        game_state.ai_director = AIDirector(creative_control_enabled=creative_control, creative_control_difficulty=cc_difficulty)
        game_state.championship_manager = ChampionshipManager()
        game_state.championship_manager.setup_default_accolades()
        game_state.calendar_system = CalendarSystem()
        all_agents = generate_all_free_agents()
        starting_agents = []
        for tier, agents in all_agents.items():
            tier_config = TIER_CONFIG[tier]
            if tier_config["level_required"] <= 1:
                starting_agents.extend(agents)
        game_state.free_agents = starting_agents
        game_state.booked_show = None
        game_state.weekly_agent_names = []
        game_state.weekly_agents_week = ""
        game_state.origin_story = {"sender": profile.origin_sender, "subject": profile.origin_subject, "message": profile.origin_message, "grant": profile.starting_grant, "delivered": False, "accepted": False}
        game_state.show_tutorial_prompt = True
        game_state.tutorial_active = False
        game_state.tutorial_step = 0
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        game_sessions[session_id] = game_state
        flash(f'{promotion_name} has been created!', 'success')
        return redirect(url_for('dashboard'))
    continents = get_continents()
    philosophies = [{"value": p.value, "name": get_philosophy_profile(p).name, "description": get_philosophy_profile(p).description, "prestige": get_philosophy_profile(p).prestige_start, "match_bonus": get_philosophy_profile(p).match_rating_bonus, "fan_growth": get_philosophy_profile(p).fan_growth_modifier, "merch": get_philosophy_profile(p).merchandise_modifier} for p in Philosophy]
    return render_template('setup.html', continents=continents, philosophies=philosophies)

@app.route('/load-game/<path:save_name>')
@require_login
def load_game(save_name):
    game_state = GameState()
    if game_state.load(save_name):
        game_state.ensure_all_systems()
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        game_sessions[session_id] = game_state
        flash(f'Loaded: {game_state.promotion.name}', 'success')
        return redirect(url_for('dashboard'))
    else:
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
    ai_director = game_state.ai_director
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
    level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
    tier = get_promotion_tier(level)
    limits = get_cumulative_limits(level)
    events = ai_director.get_active_events() if ai_director else []
    critical_events = [e for e in events if e.severity in [EventSeverity.CRITICAL, EventSeverity.MAJOR]]
    currency = game_state.game_settings.get("currency_symbol", "$")
    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        champ_count = len(game_state.championship_manager.get_active_championships())
    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    booked_show = game_state.booked_show if has_booked_show else None
    current_month = promotion.current_month
    current_day = promotion.current_day
    current_year = promotion.current_year
    num_days = days_in_month(current_month)
    current_dow = get_day_of_week(current_year, current_month, current_day)
    start_day = current_day - current_dow
    calendar_widget_days = []
    for i in range(14):
        d = start_day + i
        m = current_month
        y = current_year
        if d < 1:
            m -= 1
            if m < 1: m = 12; y -= 1
            d = days_in_month(m) + d
        elif d > num_days:
            d = d - num_days
            m += 1
            if m > 12: m = 1; y += 1
        is_today = (d == current_day and m == current_month and y == current_year)
        is_booked = False
        if booked_show and booked_show.get('show_date'):
            sd = booked_show['show_date']
            is_booked = (sd.get('year') == y and sd.get('month') == m and sd.get('day') == d)
        has_show = False
        if hasattr(game_state, 'calendar_system') and game_state.calendar_system:
            for ev in game_state.calendar_system.events:
                if ev.year == y and ev.month == m and ev.day == d:
                    has_show = True
                    break
        is_past = (y < current_year) or (y == current_year and m < current_month) or (y == current_year and m == current_month and d < current_day)
        calendar_widget_days.append({'day': d, 'month': m, 'year': y, 'is_today': is_today, 'is_booked': is_booked, 'has_show': has_show, 'is_past': is_past})
    month_names = []
    for m_item in MONTHS:
        if isinstance(m_item, dict): month_names.append(m_item.get('name', f'Month {len(month_names)+1}'))
        else: month_names.append(str(m_item))
    current_month_name = month_names[current_month - 1] if current_month <= len(month_names) else f"Month {current_month}"
    seasonal_events = get_active_seasonal_events(current_month, current_day)
    return render_template('dashboard.html', promotion=promotion, progression=progression, level=level, xp_percentage=percentage, tier_name=get_tier_name(tier), limits=limits, events=events, critical_events=critical_events, currency=currency, roster_count=len(promotion.roster), injured_count=len([w for w in promotion.roster if w.is_injured]), champ_count=champ_count, has_booked_show=has_booked_show, booked_show=booked_show, origin_message=origin_message, show_tutorial_prompt=show_tutorial_prompt, tutorial_active=tutorial_active, tutorial_step=tutorial_step, calendar_widget_days=calendar_widget_days, current_month_name=current_month_name, seasonal_events=seasonal_events, ai_events_count=len(events), hide_base_hud=True)


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
    if hasattr(game_state, 'tutorial_active') and game_state.tutorial_active:
        game_state.tutorial_step += 1
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
    promotion = game_state.promotion
    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    booked_show = game_state.booked_show if has_booked_show else None
    return render_template('booking_room.html', promotion=promotion, has_booked_show=has_booked_show, booked_show=booked_show, hide_base_hud=True)

@app.route('/locker-room')
@require_login
@require_game
def locker_room():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level)
    return render_template('locker_room.html', promotion=promotion, roster_count=len(promotion.roster), roster_limit=limits.get("roster_limit", 5), injured_count=len([w for w in promotion.roster if w.is_injured]), hide_base_hud=True)

@app.route('/championship-hub')
@require_login
@require_game
def championship_hub():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level)
    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        champ_count = len(game_state.championship_manager.get_active_championships())
    return render_template('championship_hub.html', promotion=promotion, champ_count=champ_count, max_champs=limits.get("max_championships", 0), hide_base_hud=True)

@app.route('/settings')
@require_login
@require_game
def settings_page():
    game_state = get_game_state()
    return render_template('settings.html', promotion=game_state.promotion, hide_base_hud=True)


# ==================== CALENDAR ====================

@app.route('/calendar')
@require_login
@require_game
def calendar_view():
    game_state = get_game_state()
    promotion = game_state.promotion
    if not hasattr(game_state, 'calendar_system') or game_state.calendar_system is None:
        game_state.calendar_system = CalendarSystem()
        save_game_state(game_state)
    cal = game_state.calendar_system
    current_year = promotion.current_year
    current_month = promotion.current_month
    current_day = promotion.current_day
    view_year = int(request.args.get('year', current_year))
    view_month = int(request.args.get('month', current_month))
    if view_month < 1: view_month = 12; view_year -= 1
    elif view_month > 12: view_month = 1; view_year += 1
    num_days = days_in_month(view_month)
    total_days_before = 0
    for y in range(1, view_year):
        for m_i in range(1, 13): total_days_before += days_in_month(m_i)
    for m_i in range(1, view_month): total_days_before += days_in_month(m_i)
    first_weekday = total_days_before % 7
    day_shows = {}
    for event in cal.events:
        if event.year == view_year and event.month == view_month:
            d = event.day
            if d not in day_shows: day_shows[d] = []
            day_shows[d].append({'venue': event.venue, 'rating': event.rating, 'attendance': event.attendance, 'is_sellout': getattr(event, 'is_sellout', False), 'profit': getattr(event, 'profit', 0)})
    calendar_weeks = []
    week = [0] * 7
    day_num = 1
    for i in range(first_weekday, 7):
        if day_num <= num_days: week[i] = day_num; day_num += 1
    calendar_weeks.append(week)
    while day_num <= num_days:
        week = [0] * 7
        for i in range(7):
            if day_num <= num_days: week[i] = day_num; day_num += 1
        calendar_weeks.append(week)
    year_stats = cal.get_year_stats(view_year)
    recent_events = cal.get_recent_events(10)
    all_years = sorted(set(e.year for e in cal.events))
    if current_year not in all_years: all_years.append(current_year)
    all_years.sort()
    prev_month = view_month - 1; prev_year = view_year
    if prev_month < 1: prev_month = 12; prev_year -= 1
    next_month = view_month + 1; next_year = view_year
    if next_month > 12: next_month = 1; next_year += 1
    currency = game_state.game_settings.get("currency_symbol", "$")
    month_names = []
    for m_item in MONTHS:
        if isinstance(m_item, dict): month_names.append(m_item.get('name', f'Month {len(month_names)+1}'))
        else: month_names.append(str(m_item))
    view_month_name = month_names[view_month - 1] if view_month <= len(month_names) else f"Month {view_month}"
    current_month_name = month_names[current_month - 1] if current_month <= len(month_names) else f"Month {current_month}"
    booked_show_date = None
    if hasattr(game_state, 'booked_show') and game_state.booked_show:
        booked_show_date = game_state.booked_show.get('show_date', None)
    return render_template('calendar.html', promotion=promotion, current_year=current_year, current_month=current_month, current_day=current_day, view_year=view_year, view_month=view_month, view_month_name=view_month_name, current_month_name=current_month_name, calendar_weeks=calendar_weeks, day_shows=day_shows, num_days=num_days, year_stats=year_stats, recent_events=recent_events, all_years=all_years, months=MONTHS, month_names=month_names, prev_month=prev_month, prev_year=prev_year, next_month=next_month, next_year=next_year, currency=currency, booked_show_date=booked_show_date)

@app.route('/book-for-date/<int:year>/<int:month>/<int:day>')
@require_login
@require_game
def book_for_date(year, month, day):
    game_state = get_game_state()
    promotion = game_state.promotion
    if month < 1 or month > 12: flash('Invalid month!', 'error'); return redirect(url_for('calendar_view'))
    if day < 1 or day > days_in_month(month): flash('Invalid day!', 'error'); return redirect(url_for('calendar_view'))
    current_doy = date_to_day_of_year(promotion.current_month, promotion.current_day)
    new_doy = date_to_day_of_year(month, day)
    if year < promotion.current_year: flash('Cannot book in the past!', 'error'); return redirect(url_for('calendar_view'))
    if year == promotion.current_year and new_doy < current_doy: flash('Cannot book in the past!', 'error'); return redirect(url_for('calendar_view'))
    session['show_date'] = {'year': year, 'month': month, 'day': day}
    flash(f'Booking show for {format_date(year, month, day)}', 'success')
    return redirect(url_for('book_show'))


# ==================== ROSTER ====================

@app.route('/roster')
@require_login
@require_game
def roster():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level)
    currency = game_state.game_settings.get("currency_symbol", "$")
    sorted_roster = sorted(promotion.roster, key=lambda w: w.popularity, reverse=True)
    return render_template('roster.html', wrestlers=sorted_roster, roster_limit=limits.get("roster_limit", 5), currency=currency, total_salary=sum(w.salary for w in promotion.roster))

@app.route('/wrestler/<path:wrestler_name>')
@require_login
@require_game
def wrestler_detail(wrestler_name):
    game_state = get_game_state()
    wrestler = None
    for w in game_state.promotion.roster:
        if w.name == wrestler_name: wrestler = w; break
    if not wrestler: flash('Wrestler not found!', 'error'); return redirect(url_for('roster'))
    currency = game_state.game_settings.get("currency_symbol", "$")
    return render_template('wrestler_detail.html', wrestler=wrestler, currency=currency)

@app.route('/release-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def release_wrestler(wrestler_name):
    game_state = get_game_state()
    wrestler = None
    for w in game_state.promotion.roster:
        if w.name == wrestler_name: wrestler = w; break
    if wrestler:
        buyout = int(wrestler.salary * wrestler.contract_length * 0.5)
        game_state.promotion.budget -= buyout
        game_state.promotion.roster.remove(wrestler)
        wrestler.is_signed = False; wrestler.contract_length = 0
        game_state.free_agents.append(wrestler)
        if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
            for champ in game_state.championship_manager.championships:
                if champ.current_champion == wrestler.name: champ.vacate(f"{wrestler.name} released")
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
    limits = get_cumulative_limits(progression.level)
    roster_limit = limits.get("roster_limit", 5)
    current_roster = len(game_state.promotion.roster)
    can_sign = current_roster < roster_limit
    current_level = progression.level
    current_week = game_state.promotion.current_week
    current_year = game_state.promotion.current_year
    week_key = f"{current_year}-{current_week}"
    if not hasattr(game_state, 'weekly_agents_week') or game_state.weekly_agents_week != week_key:
        if game_state.free_agents:
            available_count = min(10, len(game_state.free_agents))
            game_state.weekly_agent_names = [w.name for w in random.sample(game_state.free_agents, available_count)]
        else: game_state.weekly_agent_names = []
        game_state.weekly_agents_week = week_key
        save_game_state(game_state)
    weekly_names = getattr(game_state, 'weekly_agent_names', [])
    visible_agents = [w for w in game_state.free_agents if w.name in weekly_names]
    agents_with_salary = []
    for w in visible_agents:
        ovr = w.overall_rating
        if ovr >= 75: tier, tier_name = 5, "⭐ Main Event"
        elif ovr >= 60: tier, tier_name = 4, "🟡 Veteran"
        elif ovr >= 45: tier, tier_name = 3, "🟢 Rising Star"
        elif ovr >= 35: tier, tier_name = 2, "🔵 Independent"
        else: tier, tier_name = 1, "⚪ Rookie"
        asking = w.salary if w.salary > 0 else 200 + (w.popularity * 10) + (w.overall_rating * 5)
        agents_with_salary.append({"wrestler": w, "asking_salary": asking, "signing_bonus": asking * 4, "tier": tier, "tier_name": tier_name})
    agents_with_salary.sort(key=lambda x: (-x["tier"], -x["wrestler"].popularity))
    currency = game_state.game_settings.get("currency_symbol", "$")
    tier_info = []
    for t in range(1, 6):
        tc = TIER_CONFIG[t]
        tier_info.append({"tier": t, "name": tc["name"], "level_required": tc["level_required"], "is_unlocked": current_level >= tc["level_required"]})
    return render_template('free_agents.html', agents=agents_with_salary, can_sign=can_sign, roster_count=current_roster, roster_limit=roster_limit, budget=game_state.promotion.budget, currency=currency, tier_info=tier_info, current_level=current_level, total_agents=len(agents_with_salary), total_pool=len(game_state.free_agents), current_week=current_week, current_year=current_year)

@app.route('/sign-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def sign_wrestler(wrestler_name):
    game_state = get_game_state()
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level)
    roster_limit = limits.get("roster_limit", 5)
    if len(game_state.promotion.roster) >= roster_limit: flash('Roster is full!', 'error'); return redirect(url_for('free_agents'))
    wrestler = None
    for w in game_state.free_agents:
        if w.name == wrestler_name: wrestler = w; break
    if not wrestler: flash('Wrestler not found!', 'error'); return redirect(url_for('free_agents'))
    asking_salary = wrestler.salary if wrestler.salary > 0 else 200 + (wrestler.popularity * 10) + (wrestler.overall_rating * 5)
    signing_bonus = asking_salary * 4
    if game_state.promotion.budget < signing_bonus: flash('Cannot afford signing bonus!', 'error'); return redirect(url_for('free_agents'))
    game_state.promotion.budget -= signing_bonus
    wrestler.salary = asking_salary; wrestler.contract_length = 52; wrestler.is_signed = True; wrestler.morale = 75
    game_state.promotion.roster.append(wrestler)
    game_state.free_agents.remove(wrestler)
    if hasattr(game_state, 'weekly_agent_names') and wrestler.name in game_state.weekly_agent_names:
        game_state.weekly_agent_names.remove(wrestler.name)
    if progression.stats.get("wrestlers_signed_total", 0) == 0:
        progression.add_xp(100, "First Wrestler Signed!")
        flash('🎉 First Wrestler Signed! +100 XP', 'success')
    progression.update_stat("wrestlers_signed_total")
    save_game_state(game_state)
    flash(f'{wrestler.name} signed!', 'success')
    return redirect(url_for('free_agents'))

# ==================== BOOK SHOW ====================

@app.route('/book-show')
@require_login
@require_game
def book_show():
    game_state = get_game_state()
    progression = game_state.progression
    promotion = game_state.promotion

    limits = get_cumulative_limits(progression.level)
    max_tier = limits.get("venue_tier_max", 1)

    continent = game_state.game_settings.get("continent", "North America")
    if limits.get("can_tour_international", False):
        all_venues = get_all_venues()
    else:
        all_venues = get_venues_by_continent(continent)

    venues = [v for v in all_venues if v.tier.value <= max_tier and v.is_unlocked]
    venues.sort(key=lambda v: v.capacity)

    available = [w for w in promotion.roster if not w.is_injured]
    match_types = get_unlocked_match_types(progression.level)

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
                if v.id == current_venue_id:
                    current_venue = v
                    break

    currency = game_state.game_settings.get("currency_symbol", "$")

    show_day_name = get_day_name(get_day_of_week(
        show_date['year'], show_date['month'], show_date['day']
    ))

    championships = []
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        all_champs = game_state.championship_manager.get_active_championships()
        for champ in all_champs:
            championships.append({
                'name': champ.name,
                'current_champion': champ.current_champion,
                'current_champion_tag_partner': champ.current_champion_tag_partner,
                'is_tag_title': champ.is_tag_title or champ.level.value == 'Tag Team Championship',
                'rules': champ.rules.value,
                'gender': champ.gender.value,
                'level': champ.level.value,
            })

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None

    if current_venue:
        estimated_venue_cost = current_venue.get_rental_cost(show_day_name)
        venue_day_mod = current_venue.get_day_modifier(show_day_name)
    else:
        estimated_venue_cost = 0
        venue_day_mod = {"attendance": 1.0, "cost": 1.0, "label": ""}

    estimated_salary_cost = sum(w.salary for w in promotion.roster)

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
        is_overrunning=is_overrunning)


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
    else:
        game_state = get_game_state()
        continent = game_state.game_settings.get("continent", "North America")
        for v in get_venues_by_continent(continent):
            if v.id == venue_id:
                session['current_venue_id'] = venue_id
                session['current_card'] = []
                session['show_production'] = {}
                flash(f'Selected: {v.name}', 'success')
                break
    return redirect(url_for('book_show'))


@app.route('/add-match', methods=['POST'])
@require_login
@require_game
def add_match():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    current_card = session.get('current_card', [])
    limits = get_cumulative_limits(progression.level)
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

    # Venue restriction check
    venue_id = session.get('current_venue_id')
    if venue_id:
        venue = get_venue_by_id(venue_id)
        if venue:
            can_host, reason = venue.can_host_match_type(match_type)
            if not can_host:
                flash(reason, 'error')
                return redirect(url_for('book_show'))

    # Championship validation
    if title_match:
        champ_manager = game_state.championship_manager
        if champ_manager:
            champ = champ_manager.get_championship_by_name(title_match)
            if champ:
                can_defend, reason = champ.can_be_defended_in(match_type, len(wrestlers))
                if not can_defend:
                    flash(f'Cannot defend {title_match}: {reason}', 'error')
                    return redirect(url_for('book_show'))
                if champ.gender.value != "Intergender":
                    for name in wrestlers:
                        for w in promotion.roster:
                            if w.name == name:
                                if not champ.can_wrestler_compete(w.gender.value):
                                    flash(f'{name} cannot compete for {title_match} (gender restriction)', 'error')
                                    return redirect(url_for('book_show'))
                                break

    # Gender check (skip for intergender / no_dq)
    if not is_intergender:
        wrestler_genders = []
        for name in wrestlers:
            for w in promotion.roster:
                if w.name == name:
                    wrestler_genders.append(w.gender.value)
                    break
        if len(set(wrestler_genders)) > 1:
            flash('Mixed genders! Use an Intergender or No DQ match type for mixed gender matches.', 'error')
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
    rules_text = f" [{match_rules}]" if match_rules != "Standard" else ""
    title_text = f" for the {title_match}" if title_match else ""
    flash(f'Added: {match_data["display"]} ({match_type}, {time_info["minutes"]}min){rules_text}{title_text}', 'success')
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
    if from_index < 0 or from_index >= len(current_card):
        flash('Invalid match!', 'error')
        return redirect(url_for('book_show'))
    if to_slot < 0:
        flash('Invalid slot!', 'error')
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
        continent = game_state.game_settings.get("continent", "North America")
        for v in get_venues_by_continent(continent):
            if v.id == venue_id:
                venue = v
                break
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('book_show'))
    venue_tier = venue.tier.value
    prod_data = session.get('show_production', {})
    current_production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    return render_template('show_production.html',
        venue=venue, venue_tier=venue_tier, production=current_production,
        summary=current_production.get_summary(),
        ring_options=get_available_options("ring", venue_tier),
        lighting_options=get_available_options("lighting", venue_tier),
        camera_options=get_available_options("cameras", venue_tier),
        backstage_options=get_available_options("backstage", venue_tier),
        pyro_options=get_available_options("pyro", venue_tier),
        entrance_options=get_available_options("entrance", venue_tier),
        audio_options=get_available_options("audio", venue_tier),
        budget=game_state.promotion.budget)


@app.route('/update-production', methods=['POST'])
@require_login
@require_game
def update_production():
    production = ShowProduction(
        ring_id=request.form.get('ring', 'wrestling_ring_basic'),
        lighting_id=request.form.get('lighting', 'lighting_none'),
        camera_id=request.form.get('cameras', 'camera_none'),
        backstage_id=request.form.get('backstage', 'backstage_none'),
        pyro_id=request.form.get('pyro', 'pyro_none'),
        entrance_id=request.form.get('entrance', 'entrance_curtain'),
        audio_id=request.form.get('audio', 'audio_bluetooth'),
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
        promotion = game_state.promotion
        show_date = {'year': promotion.current_year, 'month': promotion.current_month, 'day': promotion.current_day}
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

    booked_show = None
    if hasattr(game_state, 'booked_show') and game_state.booked_show:
        booked_show = game_state.booked_show
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
        continent = game_state.game_settings.get("continent", "North America")
        for v in get_venues_by_continent(continent):
            if v.id == venue_id:
                venue = v
                break
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('dashboard'))

    show_day_name = get_day_name(get_day_of_week(show_date['year'], show_date['month'], show_date['day']))

    match_engine = MatchEngine(promotion)
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

        result = match_engine.simulate_match(
            wrestler1=w1, wrestler2=w2,
            is_title_match=match_data.get('is_title_match', False),
            is_main_event=match_data.get('is_main_event', False),
        )

        match_time = match_data.get('match_time', 'Standard')
        time_info = MATCH_TIME_OPTIONS.get(match_time, MATCH_TIME_OPTIONS['Standard'])
        total_show_time += time_info['minutes']

        avg_skill = sum(p.overall_rating for p in participants) / len(participants)
        time_quality_mod = get_time_quality_modifier(match_time, avg_skill)

        match_format = match_data.get('match_format', 'singles')
        winning_team = []
        losing_team = []
        teams = get_match_type_info().get(match_data.get('match_type', ''), {}).get('teams', None)

        if match_format in ['multi', 'variable', 'rumble', 'gauntlet', 'referee'] and len(participants) > 2:
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            losers = [p for p in participants if p != actual_winner]
            actual_loser = random.choice(losers) if losers else w2
        elif match_format in ['tag', 'handicap'] and teams and len(participants) > 2:
            t1_size = teams[0]
            team1 = participants[:t1_size]
            team2 = participants[t1_size:]
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        elif match_format == 'tag3':
            team1 = participants[:3]
            team2 = participants[3:]
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        elif match_format == 'tag4':
            team1 = participants[:4]
            team2 = participants[4:]
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        elif match_format == 'wargames':
            ts = teams[0] if teams else 3
            team1 = participants[:ts]
            team2 = participants[ts:]
            weights = [p.popularity + p.overall_rating for p in participants]
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

        for p in participants:
            if p != w1 and p != w2:
                p.add_fatigue(time_info.get('fatigue', 8))

        display = match_data.get('display', f'{w1.name} vs {w2.name}')
        adjusted_rating = min(5.0, result.match_rating + (production_quality * 0.02) + time_quality_mod)
        adjusted_rating = max(0.0, adjusted_rating)

        if winning_team:
            winner_display = " & ".join([p.name for p in winning_team])
        else:
            winner_display = actual_winner.name if actual_winner else 'DRAW'

        match_result = {
            'display': display, 'wrestler1': w1.name, 'wrestler2': w2.name,
            'all_participants': [p.name for p in participants],
            'winner': winner_display,
            'winning_team': [p.name for p in winning_team] if winning_team else [],
            'finish': result.finish_type.value, 'rating': adjusted_rating,
            'crowd': result.crowd_reaction,
            'match_type': match_data.get('match_type', 'Singles'),
            'match_time': match_time, 'match_minutes': time_info['minutes'],
            'match_rules': match_data.get('match_rules', 'Standard'),
            'is_main_event': match_data.get('is_main_event', False),
            'is_title_match': match_data.get('is_title_match', False),
            'title_name': match_data.get('title_name', ''),
            'is_intergender': match_data.get('is_intergender', False),
            'title_changed': False,
        }

        # Title logic
        if match_data.get('is_title_match') and match_data.get('title_name') and actual_winner:
            title_name = match_data['title_name']
            if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
                champ = game_state.championship_manager.get_championship_by_name(title_name)
                if champ:
                    is_tag = champ.is_tag_title or champ.level.value == 'Tag Team Championship'
                    if is_tag and winning_team:
                        winning_names = {p.name for p in winning_team}
                        champ_names = {champ.current_champion, champ.current_champion_tag_partner}
                        champ_names.discard("")
                        if winning_names == champ_names:
                            loser_names = " & ".join([p.name for p in losing_team]) if losing_team else ""
                            champ.record_defense(loser_names)
                        else:
                            date_str = format_date(show_date['year'], show_date['month'], show_date['day'])
                            tag_partner = winning_team[1].name if len(winning_team) > 1 else ""
                            champ.award_title(winning_team[0].name, date_str, tag_partner=tag_partner)
                            for p in winning_team:
                                p.titles_held += 1
                            match_result['title_changed'] = True
                            title_changes.append({'title': title_name, 'new_champion': winner_display})
                            if progression and progression.stats.get("title_changes", 0) == 0:
                                progression.add_xp(150, "First Champion Crowned!")
                            if progression:
                                progression.update_stat("title_changes")
                    else:
                        if champ.current_champion == actual_winner.name:
                            champ.record_defense(actual_loser.name if actual_loser else "")
                        else:
                            date_str = format_date(show_date['year'], show_date['month'], show_date['day'])
                            champ.award_title(actual_winner.name, date_str)
                            actual_winner.titles_held += 1
                            match_result['title_changed'] = True
                            title_changes.append({'title': title_name, 'new_champion': actual_winner.name})
                            if progression and progression.stats.get("title_changes", 0) == 0:
                                progression.add_xp(150, "First Champion Crowned!")
                            if progression:
                                progression.update_stat("title_changes")

        # Record wins/losses
        if winning_team:
            for p in winning_team:
                p.record_match("win")
            for p in losing_team:
                p.record_match("loss")
        elif actual_winner and actual_loser:
            actual_winner.record_match("win")
            actual_loser.record_match("loss")
            if match_format in ['multi', 'variable', 'rumble', 'gauntlet']:
                for p in participants:
                    if p != actual_winner and p != actual_loser:
                        p.record_match("loss")

        results.append(match_result)
        total_rating += adjusted_rating
        if adjusted_rating >= 5.0:
            five_star += 1
        elif adjusted_rating >= 4.0:
            four_star += 1
        if game_state.ai_director and actual_winner and actual_loser:
            game_state.ai_director.record_match_result(actual_winner.name, actual_loser.name, adjusted_rating)

    avg_rating = total_rating / len(results) if results else 0

    # Overrun check
    available_minutes = venue.get_available_minutes()
    minutes_over = total_show_time - available_minutes
    overrun_penalty = calculate_overrun_penalty(minutes_over)
    overrun_fine = overrun_penalty.get('fine', 0)
    overrun_message = overrun_penalty.get('message', '')
    if minutes_over > 0:
        venue.apply_overrun_penalty(minutes_over, promotion.current_week)
        promotion.budget -= overrun_fine
        promotion.prestige = max(0, promotion.prestige - overrun_penalty.get('prestige_loss', 0))
        if overrun_penalty.get('fan_loss', 0) > 0:
            promotion.fan_base = max(0, promotion.fan_base - overrun_penalty['fan_loss'])

    attendance = venue.get_expected_attendance(promotion.prestige, show_day_name)
    attendance = min(attendance, venue.capacity)
    is_sellout = attendance >= venue.capacity * 0.95

    revenue_breakdown = venue.calculate_revenue(attendance, show_day_name)
    ticket_revenue = revenue_breakdown['tickets']
    merch_revenue = int(attendance * 5 * promotion.merchandise_modifier)
    alcohol_revenue = revenue_breakdown.get('alcohol', 0)
    concession_revenue = revenue_breakdown.get('concessions', 0)
    vip_revenue = revenue_breakdown.get('vip', 0)

    venue_cost = venue.get_rental_cost(show_day_name)
    total_costs = venue_cost + production_cost + overrun_fine
    total_revenue = ticket_revenue + merch_revenue + alcohol_revenue + concession_revenue + vip_revenue
    profit = total_revenue - total_costs

    promotion.budget += profit
    promotion.fan_base += production_fans

    milestone_msgs = []
    if progression:
        if progression.stats.get("total_shows", 0) == 0 and progression.stats.get("total_ppvs", 0) == 0:
            progression.add_xp(200, "First Show Ever!")
            milestone_msgs.append('🎉 First Show Achievement! +200 XP')
        if is_sellout and progression.stats.get("sellouts", 0) == 0:
            progression.add_xp(250, "First Sellout!")
            milestone_msgs.append('🎉 First Sellout Achievement! +250 XP')
        if five_star > 0 and progression.stats.get("five_star_matches", 0) == 0:
            progression.add_xp(300, "First Five Star Match!")
            milestone_msgs.append('🎉 First 5-Star Match! +300 XP')

    show_rewards = progression.process_show_completion(
        is_ppv=False, average_match_rating=avg_rating, attendance=attendance,
        capacity=venue.capacity, venue_prestige=venue.prestige,
        venue_tier=venue.tier.value, venue_id=venue.id,
        five_star_matches=five_star, four_star_matches=four_star,
        ticket_price=revenue_breakdown['tickets'] // max(attendance, 1),
        merchandise_modifier=promotion.merchandise_modifier,
        total_matches=len(results),
    )

    promotion.fan_base += show_rewards['fans']['total']

    if not hasattr(game_state, 'calendar_system') or game_state.calendar_system is None:
        game_state.calendar_system = CalendarSystem()

    main_event_match = results[-1].get('display', '') if results else ""
    game_state.calendar_system.add_show(
        year=show_date['year'], month=show_date['month'], day=show_date['day'],
        venue=venue.name, attendance=attendance, capacity=venue.capacity,
        rating=avg_rating, profit=profit, is_sellout=is_sellout,
        main_event=main_event_match, matches_count=len(results),
    )

    venue.record_event(attendance, profit)
    promotion.advance_to_date(show_date['year'], show_date['month'], show_date['day'])
    promotion.advance_days(1)

    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    session['show_date'] = None

    ai_result, total_salaries = process_week_advancement(game_state)
    new_events = len(ai_result.get('new_events', []))
    save_game_state(game_state)
    currency = game_state.game_settings.get("currency_symbol", "$")

    for msg in milestone_msgs:
        flash(msg, 'success')

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
        new_level=show_rewards.get('new_level', progression.level),
        achievements=show_rewards.get('achievements_earned', []),
        title_changes=title_changes, currency=currency,
        salaries_paid=total_salaries, new_events=new_events,
        new_week=promotion.current_week, new_year=promotion.current_year,
        production_quality=production_quality, production_fans=production_fans,
        show_day_name=show_day_name,
        total_show_time=total_show_time,
        available_minutes=available_minutes,
        overrun_fine=overrun_fine, overrun_message=overrun_message,
        minutes_over=minutes_over)


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
    flash(f'Skipped a week. Now {promotion.current_day}/{promotion.current_month}/Y{promotion.current_year}. Salaries: ${total_salaries:,}. Lost {fan_loss} fans.', 'warning')
    return redirect(url_for('dashboard'))

# ==================== BOOK SHOW ====================

@app.route('/book-show')
@require_login
@require_game
def book_show():
    game_state = get_game_state()
    progression = game_state.progression
    promotion = game_state.promotion

    limits = get_cumulative_limits(progression.level)
    max_tier = limits.get("venue_tier_max", 1)

    continent = game_state.game_settings.get("continent", "North America")
    if limits.get("can_tour_international", False):
        all_venues = get_all_venues()
    else:
        all_venues = get_venues_by_continent(continent)

    venues = [v for v in all_venues if v.tier.value <= max_tier and v.is_unlocked]
    venues.sort(key=lambda v: v.capacity)

    available = [w for w in promotion.roster if not w.is_injured]
    match_types = get_unlocked_match_types(progression.level)

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
                if v.id == current_venue_id:
                    current_venue = v
                    break

    currency = game_state.game_settings.get("currency_symbol", "$")

    show_day_name = get_day_name(get_day_of_week(
        show_date['year'], show_date['month'], show_date['day']
    ))

    championships = []
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        all_champs = game_state.championship_manager.get_active_championships()
        for champ in all_champs:
            championships.append({
                'name': champ.name,
                'current_champion': champ.current_champion,
                'current_champion_tag_partner': champ.current_champion_tag_partner,
                'is_tag_title': champ.is_tag_title or champ.level.value == 'Tag Team Championship',
                'rules': champ.rules.value,
                'gender': champ.gender.value,
                'level': champ.level.value,
            })

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None

    if current_venue:
        estimated_venue_cost = current_venue.get_rental_cost(show_day_name)
        venue_day_mod = current_venue.get_day_modifier(show_day_name)
    else:
        estimated_venue_cost = 0
        venue_day_mod = {"attendance": 1.0, "cost": 1.0, "label": ""}

    estimated_salary_cost = sum(w.salary for w in promotion.roster)

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
        is_overrunning=is_overrunning)


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
    else:
        game_state = get_game_state()
        continent = game_state.game_settings.get("continent", "North America")
        for v in get_venues_by_continent(continent):
            if v.id == venue_id:
                session['current_venue_id'] = venue_id
                session['current_card'] = []
                session['show_production'] = {}
                flash(f'Selected: {v.name}', 'success')
                break
    return redirect(url_for('book_show'))


@app.route('/add-match', methods=['POST'])
@require_login
@require_game
def add_match():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    current_card = session.get('current_card', [])
    limits = get_cumulative_limits(progression.level)
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

    # Venue restriction check
    venue_id = session.get('current_venue_id')
    if venue_id:
        venue = get_venue_by_id(venue_id)
        if venue:
            can_host, reason = venue.can_host_match_type(match_type)
            if not can_host:
                flash(reason, 'error')
                return redirect(url_for('book_show'))

    # Championship validation
    if title_match:
        champ_manager = game_state.championship_manager
        if champ_manager:
            champ = champ_manager.get_championship_by_name(title_match)
            if champ:
                can_defend, reason = champ.can_be_defended_in(match_type, len(wrestlers))
                if not can_defend:
                    flash(f'Cannot defend {title_match}: {reason}', 'error')
                    return redirect(url_for('book_show'))
                if champ.gender.value != "Intergender":
                    for name in wrestlers:
                        for w in promotion.roster:
                            if w.name == name:
                                if not champ.can_wrestler_compete(w.gender.value):
                                    flash(f'{name} cannot compete for {title_match} (gender restriction)', 'error')
                                    return redirect(url_for('book_show'))
                                break

    # Gender check (skip for intergender / no_dq)
    if not is_intergender:
        wrestler_genders = []
        for name in wrestlers:
            for w in promotion.roster:
                if w.name == name:
                    wrestler_genders.append(w.gender.value)
                    break
        if len(set(wrestler_genders)) > 1:
            flash('Mixed genders! Use an Intergender or No DQ match type for mixed gender matches.', 'error')
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
    rules_text = f" [{match_rules}]" if match_rules != "Standard" else ""
    title_text = f" for the {title_match}" if title_match else ""
    flash(f'Added: {match_data["display"]} ({match_type}, {time_info["minutes"]}min){rules_text}{title_text}', 'success')
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
    if from_index < 0 or from_index >= len(current_card):
        flash('Invalid match!', 'error')
        return redirect(url_for('book_show'))
    if to_slot < 0:
        flash('Invalid slot!', 'error')
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
        continent = game_state.game_settings.get("continent", "North America")
        for v in get_venues_by_continent(continent):
            if v.id == venue_id:
                venue = v
                break
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('book_show'))
    venue_tier = venue.tier.value
    prod_data = session.get('show_production', {})
    current_production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    return render_template('show_production.html',
        venue=venue, venue_tier=venue_tier, production=current_production,
        summary=current_production.get_summary(),
        ring_options=get_available_options("ring", venue_tier),
        lighting_options=get_available_options("lighting", venue_tier),
        camera_options=get_available_options("cameras", venue_tier),
        backstage_options=get_available_options("backstage", venue_tier),
        pyro_options=get_available_options("pyro", venue_tier),
        entrance_options=get_available_options("entrance", venue_tier),
        audio_options=get_available_options("audio", venue_tier),
        budget=game_state.promotion.budget)


@app.route('/update-production', methods=['POST'])
@require_login
@require_game
def update_production():
    production = ShowProduction(
        ring_id=request.form.get('ring', 'wrestling_ring_basic'),
        lighting_id=request.form.get('lighting', 'lighting_none'),
        camera_id=request.form.get('cameras', 'camera_none'),
        backstage_id=request.form.get('backstage', 'backstage_none'),
        pyro_id=request.form.get('pyro', 'pyro_none'),
        entrance_id=request.form.get('entrance', 'entrance_curtain'),
        audio_id=request.form.get('audio', 'audio_bluetooth'),
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
        promotion = game_state.promotion
        show_date = {'year': promotion.current_year, 'month': promotion.current_month, 'day': promotion.current_day}
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

    booked_show = None
    if hasattr(game_state, 'booked_show') and game_state.booked_show:
        booked_show = game_state.booked_show
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
        continent = game_state.game_settings.get("continent", "North America")
        for v in get_venues_by_continent(continent):
            if v.id == venue_id:
                venue = v
                break
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('dashboard'))

    show_day_name = get_day_name(get_day_of_week(show_date['year'], show_date['month'], show_date['day']))

    match_engine = MatchEngine(promotion)
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

        result = match_engine.simulate_match(
            wrestler1=w1, wrestler2=w2,
            is_title_match=match_data.get('is_title_match', False),
            is_main_event=match_data.get('is_main_event', False),
        )

        match_time = match_data.get('match_time', 'Standard')
        time_info = MATCH_TIME_OPTIONS.get(match_time, MATCH_TIME_OPTIONS['Standard'])
        total_show_time += time_info['minutes']

        avg_skill = sum(p.overall_rating for p in participants) / len(participants)
        time_quality_mod = get_time_quality_modifier(match_time, avg_skill)

        match_format = match_data.get('match_format', 'singles')
        winning_team = []
        losing_team = []
        teams = get_match_type_info().get(match_data.get('match_type', ''), {}).get('teams', None)

        if match_format in ['multi', 'variable', 'rumble', 'gauntlet', 'referee'] and len(participants) > 2:
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            losers = [p for p in participants if p != actual_winner]
            actual_loser = random.choice(losers) if losers else w2
        elif match_format in ['tag', 'handicap'] and teams and len(participants) > 2:
            t1_size = teams[0]
            team1 = participants[:t1_size]
            team2 = participants[t1_size:]
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        elif match_format == 'tag3':
            team1 = participants[:3]
            team2 = participants[3:]
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        elif match_format == 'tag4':
            team1 = participants[:4]
            team2 = participants[4:]
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            if actual_winner in team1:
                winning_team, losing_team = team1, team2
            else:
                winning_team, losing_team = team2, team1
            actual_winner = winning_team[0]
            actual_loser = losing_team[0]
        elif match_format == 'wargames':
            ts = teams[0] if teams else 3
            team1 = participants[:ts]
            team2 = participants[ts:]
            weights = [p.popularity + p.overall_rating for p in participants]
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

        for p in participants:
            if p != w1 and p != w2:
                p.add_fatigue(time_info.get('fatigue', 8))

        display = match_data.get('display', f'{w1.name} vs {w2.name}')
        adjusted_rating = min(5.0, result.match_rating + (production_quality * 0.02) + time_quality_mod)
        adjusted_rating = max(0.0, adjusted_rating)

        if winning_team:
            winner_display = " & ".join([p.name for p in winning_team])
        else:
            winner_display = actual_winner.name if actual_winner else 'DRAW'

        match_result = {
            'display': display, 'wrestler1': w1.name, 'wrestler2': w2.name,
            'all_participants': [p.name for p in participants],
            'winner': winner_display,
            'winning_team': [p.name for p in winning_team] if winning_team else [],
            'finish': result.finish_type.value, 'rating': adjusted_rating,
            'crowd': result.crowd_reaction,
            'match_type': match_data.get('match_type', 'Singles'),
            'match_time': match_time, 'match_minutes': time_info['minutes'],
            'match_rules': match_data.get('match_rules', 'Standard'),
            'is_main_event': match_data.get('is_main_event', False),
            'is_title_match': match_data.get('is_title_match', False),
            'title_name': match_data.get('title_name', ''),
            'is_intergender': match_data.get('is_intergender', False),
            'title_changed': False,
        }

        # Title logic
        if match_data.get('is_title_match') and match_data.get('title_name') and actual_winner:
            title_name = match_data['title_name']
            if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
                champ = game_state.championship_manager.get_championship_by_name(title_name)
                if champ:
                    is_tag = champ.is_tag_title or champ.level.value == 'Tag Team Championship'
                    if is_tag and winning_team:
                        winning_names = {p.name for p in winning_team}
                        champ_names = {champ.current_champion, champ.current_champion_tag_partner}
                        champ_names.discard("")
                        if winning_names == champ_names:
                            loser_names = " & ".join([p.name for p in losing_team]) if losing_team else ""
                            champ.record_defense(loser_names)
                        else:
                            date_str = format_date(show_date['year'], show_date['month'], show_date['day'])
                            tag_partner = winning_team[1].name if len(winning_team) > 1 else ""
                            champ.award_title(winning_team[0].name, date_str, tag_partner=tag_partner)
                            for p in winning_team:
                                p.titles_held += 1
                            match_result['title_changed'] = True
                            title_changes.append({'title': title_name, 'new_champion': winner_display})
                            if progression and progression.stats.get("title_changes", 0) == 0:
                                progression.add_xp(150, "First Champion Crowned!")
                            if progression:
                                progression.update_stat("title_changes")
                    else:
                        if champ.current_champion == actual_winner.name:
                            champ.record_defense(actual_loser.name if actual_loser else "")
                        else:
                            date_str = format_date(show_date['year'], show_date['month'], show_date['day'])
                            champ.award_title(actual_winner.name, date_str)
                            actual_winner.titles_held += 1
                            match_result['title_changed'] = True
                            title_changes.append({'title': title_name, 'new_champion': actual_winner.name})
                            if progression and progression.stats.get("title_changes", 0) == 0:
                                progression.add_xp(150, "First Champion Crowned!")
                            if progression:
                                progression.update_stat("title_changes")

        # Record wins/losses
        if winning_team:
            for p in winning_team:
                p.record_match("win")
            for p in losing_team:
                p.record_match("loss")
        elif actual_winner and actual_loser:
            actual_winner.record_match("win")
            actual_loser.record_match("loss")
            if match_format in ['multi', 'variable', 'rumble', 'gauntlet']:
                for p in participants:
                    if p != actual_winner and p != actual_loser:
                        p.record_match("loss")

        results.append(match_result)
        total_rating += adjusted_rating
        if adjusted_rating >= 5.0:
            five_star += 1
        elif adjusted_rating >= 4.0:
            four_star += 1
        if game_state.ai_director and actual_winner and actual_loser:
            game_state.ai_director.record_match_result(actual_winner.name, actual_loser.name, adjusted_rating)

    avg_rating = total_rating / len(results) if results else 0

    # Overrun check
    available_minutes = venue.get_available_minutes()
    minutes_over = total_show_time - available_minutes
    overrun_penalty = calculate_overrun_penalty(minutes_over)
    overrun_fine = overrun_penalty.get('fine', 0)
    overrun_message = overrun_penalty.get('message', '')
    if minutes_over > 0:
        venue.apply_overrun_penalty(minutes_over, promotion.current_week)
        promotion.budget -= overrun_fine
        promotion.prestige = max(0, promotion.prestige - overrun_penalty.get('prestige_loss', 0))
        if overrun_penalty.get('fan_loss', 0) > 0:
            promotion.fan_base = max(0, promotion.fan_base - overrun_penalty['fan_loss'])

    attendance = venue.get_expected_attendance(promotion.prestige, show_day_name)
    attendance = min(attendance, venue.capacity)
    is_sellout = attendance >= venue.capacity * 0.95

    revenue_breakdown = venue.calculate_revenue(attendance, show_day_name)
    ticket_revenue = revenue_breakdown['tickets']
    merch_revenue = int(attendance * 5 * promotion.merchandise_modifier)
    alcohol_revenue = revenue_breakdown.get('alcohol', 0)
    concession_revenue = revenue_breakdown.get('concessions', 0)
    vip_revenue = revenue_breakdown.get('vip', 0)

    venue_cost = venue.get_rental_cost(show_day_name)
    total_costs = venue_cost + production_cost + overrun_fine
    total_revenue = ticket_revenue + merch_revenue + alcohol_revenue + concession_revenue + vip_revenue
    profit = total_revenue - total_costs

    promotion.budget += profit
    promotion.fan_base += production_fans

    milestone_msgs = []
    if progression:
        if progression.stats.get("total_shows", 0) == 0 and progression.stats.get("total_ppvs", 0) == 0:
            progression.add_xp(200, "First Show Ever!")
            milestone_msgs.append('🎉 First Show Achievement! +200 XP')
        if is_sellout and progression.stats.get("sellouts", 0) == 0:
            progression.add_xp(250, "First Sellout!")
            milestone_msgs.append('🎉 First Sellout Achievement! +250 XP')
        if five_star > 0 and progression.stats.get("five_star_matches", 0) == 0:
            progression.add_xp(300, "First Five Star Match!")
            milestone_msgs.append('🎉 First 5-Star Match! +300 XP')

    show_rewards = progression.process_show_completion(
        is_ppv=False, average_match_rating=avg_rating, attendance=attendance,
        capacity=venue.capacity, venue_prestige=venue.prestige,
        venue_tier=venue.tier.value, venue_id=venue.id,
        five_star_matches=five_star, four_star_matches=four_star,
        ticket_price=revenue_breakdown['tickets'] // max(attendance, 1),
        merchandise_modifier=promotion.merchandise_modifier,
        total_matches=len(results),
    )

    promotion.fan_base += show_rewards['fans']['total']

    if not hasattr(game_state, 'calendar_system') or game_state.calendar_system is None:
        game_state.calendar_system = CalendarSystem()

    main_event_match = results[-1].get('display', '') if results else ""
    game_state.calendar_system.add_show(
        year=show_date['year'], month=show_date['month'], day=show_date['day'],
        venue=venue.name, attendance=attendance, capacity=venue.capacity,
        rating=avg_rating, profit=profit, is_sellout=is_sellout,
        main_event=main_event_match, matches_count=len(results),
    )

    venue.record_event(attendance, profit)
    promotion.advance_to_date(show_date['year'], show_date['month'], show_date['day'])
    promotion.advance_days(1)

    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    session['show_date'] = None

    ai_result, total_salaries = process_week_advancement(game_state)
    new_events = len(ai_result.get('new_events', []))
    save_game_state(game_state)
    currency = game_state.game_settings.get("currency_symbol", "$")

    for msg in milestone_msgs:
        flash(msg, 'success')

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
        new_level=show_rewards.get('new_level', progression.level),
        achievements=show_rewards.get('achievements_earned', []),
        title_changes=title_changes, currency=currency,
        salaries_paid=total_salaries, new_events=new_events,
        new_week=promotion.current_week, new_year=promotion.current_year,
        production_quality=production_quality, production_fans=production_fans,
        show_day_name=show_day_name,
        total_show_time=total_show_time,
        available_minutes=available_minutes,
        overrun_fine=overrun_fine, overrun_message=overrun_message,
        minutes_over=minutes_over)


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
    flash(f'Skipped a week. Now {promotion.current_day}/{promotion.current_month}/Y{promotion.current_year}. Salaries: ${total_salaries:,}. Lost {fan_loss} fans.', 'warning')
    return redirect(url_for('dashboard'))
