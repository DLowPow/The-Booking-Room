"""
The Booking Room - Flask Web Application
Complete rebuild with: Intergender matches, gender restrictions,
tag title support, match type restrictions, milestone XP,
day-based calendar, 8 wrestling styles, match slot limits
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
from classes.venue import Venue, VenueTier
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
from data.venues import get_venues_by_continent, get_all_venues
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


# ==================== MATCH TYPE HELPERS ====================

def get_match_type_info():
    return {
        "Singles": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Intergender Singles": {"participants": 2, "type": "singles", "label": "1v1", "intergender": True},
        "Tag Team": {"participants": 4, "type": "tag", "label": "2v2", "intergender": False},
        "Intergender Tag": {"participants": 4, "type": "tag", "label": "2v2", "intergender": True},
        "Triple Threat": {"participants": 3, "type": "multi", "label": "3-Way", "intergender": False},
        "Fatal Four Way": {"participants": 4, "type": "multi", "label": "4-Way", "intergender": False},
        "6-Man Tag": {"participants": 6, "type": "tag3", "label": "3v3", "intergender": False},
        "Hardcore": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Submission": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Cage": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Ladder": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Tables": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Last Man Standing": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Iron Man": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "I Quit": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "TLC": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Hell in a Cell": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Elimination Chamber": {"participants": 6, "type": "multi", "label": "6-Way", "intergender": False},
        "Battle Royal": {"participants": 8, "type": "multi", "label": "8+ Way", "intergender": False},
        "Gauntlet": {"participants": 4, "type": "multi", "label": "Gauntlet", "intergender": False},
        "War Games": {"participants": 8, "type": "tag4", "label": "4v4", "intergender": False},
        "Royal Rumble": {"participants": 8, "type": "multi", "label": "Rumble", "intergender": False},
        "Inferno": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Buried Alive": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
        "Deathmatch": {"participants": 2, "type": "singles", "label": "1v1", "intergender": False},
    }


def get_display_for_match(match_data):
    match_type = match_data.get('match_type', 'Singles')
    info = get_match_type_info().get(match_type, {"type": "singles", "participants": 2})

    if info["type"] == "singles":
        return f"{match_data.get('wrestler1', '?')} vs {match_data.get('wrestler2', '?')}"
    elif info["type"] == "tag":
        return f"{match_data.get('wrestler1', '?')} & {match_data.get('wrestler2', '?')} vs {match_data.get('wrestler3', '?')} & {match_data.get('wrestler4', '?')}"
    elif info["type"] == "tag3":
        return f"{match_data.get('wrestler1', '?')}, {match_data.get('wrestler2', '?')} & {match_data.get('wrestler3', '?')} vs {match_data.get('wrestler4', '?')}, {match_data.get('wrestler5', '?')} & {match_data.get('wrestler6', '?')}"
    elif info["type"] == "tag4":
        team1 = [match_data.get(f'wrestler{i}', '') for i in range(1, 5) if match_data.get(f'wrestler{i}')]
        team2 = [match_data.get(f'wrestler{i}', '') for i in range(5, 9) if match_data.get(f'wrestler{i}')]
        return f"{' & '.join(team1)} vs {' & '.join(team2)}"
    elif info["type"] == "multi":
        names = [match_data.get(f'wrestler{i}', '') for i in range(1, info["participants"] + 1) if match_data.get(f'wrestler{i}')]
        return " vs ".join(names)

    return f"{match_data.get('wrestler1', '?')} vs {match_data.get('wrestler2', '?')}"


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

    roster_data = [
        {
            "name": w.name, "ego": w.ego, "loyalty": w.loyalty,
            "professionalism": w.professionalism, "morale": w.morale,
            "popularity": w.popularity, "salary": w.salary,
            "contract_length": w.contract_length, "is_injured": w.is_injured,
            "age": w.age, "momentum": w.momentum, "wins": w.wins, "losses": w.losses,
        }
        for w in promotion.roster
    ]

    ai_result = {"new_events": []}
    if ai_director:
        ai_result = ai_director.process_weekly_update(
            roster=roster_data, budget=promotion.budget, fans=promotion.fan_base,
            prestige=promotion.prestige, current_week=promotion.current_week,
        )

    if progression:
        progression.process_weekly_update(
            active_wrestlers=len([w for w in promotion.roster if not w.is_injured]),
            total_fans=promotion.fan_base, current_budget=promotion.budget,
            weekly_profit=-total_salaries, roster_size=len(promotion.roster),
        )

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

        promotion = Promotion(
            name=promotion_name, philosophy=phil_enum, owner_name=promoter_name,
            starting_budget=profile.starting_budget, location=f"{city}, {country}",
        )
        promotion.fan_base = profile.starting_fans
        promotion.prestige = profile.prestige_start
        promotion.merchandise_modifier = profile.merchandise_modifier

        game_state.promotion = promotion
        game_state.game_settings = {
            "continent": continent, "country": country, "city": city,
            "currency_code": currency_code, "currency_symbol": currency_symbol,
            "creative_control_enabled": creative_control,
            "creative_control_difficulty": cc_difficulty, "show_day": "Saturday",
        }

        game_state.progression = ProgressionSystem()
        game_state.ai_director = AIDirector(
            creative_control_enabled=creative_control, creative_control_difficulty=cc_difficulty,
        )
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
            "budget": get_philosophy_profile(p).starting_budget,
            "fans": get_philosophy_profile(p).starting_fans,
            "description": get_philosophy_profile(p).description,
        }
        for p in Philosophy
    ]
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

    level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
    tier = get_promotion_tier(level)
    limits = get_cumulative_limits(level)

    events = ai_director.get_active_events() if ai_director else []
    critical_events = [e for e in events if e.severity in [EventSeverity.CRITICAL, EventSeverity.MAJOR]]

    currency = game_state.game_settings.get("currency_symbol", "$")
    show_day = game_state.game_settings.get("show_day", "Saturday")

    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        champ_count = len(game_state.championship_manager.get_active_championships())

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    booked_show = game_state.booked_show if has_booked_show else None

    return render_template('dashboard.html',
        promotion=promotion, progression=progression, level=level,
        xp_percentage=percentage, tier_name=get_tier_name(tier), limits=limits,
        events=events, critical_events=critical_events, currency=currency,
        roster_count=len(promotion.roster),
        injured_count=len([w for w in promotion.roster if w.is_injured]),
        champ_count=champ_count, show_day=show_day,
        has_booked_show=has_booked_show, booked_show=booked_show)


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

    if view_month < 1:
        view_month = 12
        view_year -= 1
    elif view_month > 12:
        view_month = 1
        view_year += 1

    month_data = cal.get_month_calendar_data(view_year, view_month)
    year_stats = cal.get_year_stats(view_year)
    recent_events = cal.get_recent_events(10)

    all_years = sorted(set(e.year for e in cal.events))
    if current_year not in all_years:
        all_years.append(current_year)
    all_years.sort()

    prev_month = view_month - 1
    prev_year = view_year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = view_month + 1
    next_year = view_year
    if next_month > 12:
        next_month = 1
        next_year += 1

    currency = game_state.game_settings.get("currency_symbol", "$")

    return render_template('calendar.html',
        promotion=promotion,
        current_year=current_year,
        current_month=current_month,
        current_day=current_day,
        view_year=view_year,
        view_month=view_month,
        month_data=month_data,
        year_stats=year_stats,
        recent_events=recent_events,
        all_years=all_years,
        months=MONTHS,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        currency=currency)


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

    current_doy = date_to_day_of_year(promotion.current_month, promotion.current_day)
    new_doy = date_to_day_of_year(month, day)

    if year < promotion.current_year:
        flash('Cannot book in the past!', 'error')
        return redirect(url_for('calendar_view'))

    if year == promotion.current_year and new_doy < current_doy:
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
    promotion = game_state.promotion
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level)
    currency = game_state.game_settings.get("currency_symbol", "$")
    sorted_roster = sorted(promotion.roster, key=lambda w: w.popularity, reverse=True)
    return render_template('roster.html', wrestlers=sorted_roster,
        roster_limit=limits.get("roster_limit", 5), currency=currency,
        total_salary=sum(w.salary for w in promotion.roster))


@app.route('/wrestler/<path:wrestler_name>')
@require_login
@require_game
def wrestler_detail(wrestler_name):
    game_state = get_game_state()
    wrestler = None
    for w in game_state.promotion.roster:
        if w.name == wrestler_name:
            wrestler = w
            break
    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('roster'))
    currency = game_state.game_settings.get("currency_symbol", "$")
    return render_template('wrestler_detail.html', wrestler=wrestler, currency=currency)


@app.route('/release-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def release_wrestler(wrestler_name):
    game_state = get_game_state()
    wrestler = None
    for w in game_state.promotion.roster:
        if w.name == wrestler_name:
            wrestler = w
            break
    if wrestler:
        buyout = int(wrestler.salary * wrestler.contract_length * 0.5)
        game_state.promotion.budget -= buyout
        game_state.promotion.roster.remove(wrestler)
        wrestler.is_signed = False
        wrestler.contract_length = 0
        game_state.free_agents.append(wrestler)
        if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
            for champ in game_state.championship_manager.championships:
                if champ.current_champion == wrestler.name:
                    champ.vacate(f"{wrestler.name} released")
        save_game_state(game_state)
        flash(f'{wrestler.name} has been released. Buyout: ${buyout:,}', 'info')
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
            game_state.weekly_agent_names = [
                w.name for w in random.sample(game_state.free_agents, available_count)
            ]
        else:
            game_state.weekly_agent_names = []
        game_state.weekly_agents_week = week_key
        save_game_state(game_state)

    weekly_names = getattr(game_state, 'weekly_agent_names', [])
    visible_agents = [w for w in game_state.free_agents if w.name in weekly_names]

    agents_with_salary = []
    for w in visible_agents:
        ovr = w.overall_rating
        if ovr >= 75:
            tier, tier_name = 5, "⭐ Main Event"
        elif ovr >= 60:
            tier, tier_name = 4, "🟡 Veteran"
        elif ovr >= 45:
            tier, tier_name = 3, "🟢 Rising Star"
        elif ovr >= 35:
            tier, tier_name = 2, "🔵 Independent"
        else:
            tier, tier_name = 1, "⚪ Rookie"
        asking = w.salary if w.salary > 0 else 200 + (w.popularity * 10) + (w.overall_rating * 5)
        agents_with_salary.append({
            "wrestler": w, "asking_salary": asking, "signing_bonus": asking * 4,
            "tier": tier, "tier_name": tier_name,
        })

    agents_with_salary.sort(key=lambda x: (-x["tier"], -x["wrestler"].popularity))
    currency = game_state.game_settings.get("currency_symbol", "$")

    tier_info = []
    for t in range(1, 6):
        tc = TIER_CONFIG[t]
        tier_info.append({
            "tier": t, "name": tc["name"], "level_required": tc["level_required"],
            "is_unlocked": current_level >= tc["level_required"],
        })

    return render_template('free_agents.html', agents=agents_with_salary, can_sign=can_sign,
        roster_count=current_roster, roster_limit=roster_limit,
        budget=game_state.promotion.budget, currency=currency,
        tier_info=tier_info, current_level=current_level,
        total_agents=len(agents_with_salary),
        total_pool=len(game_state.free_agents),
        current_week=current_week,
        current_year=current_year)


@app.route('/sign-wrestler/<path:wrestler_name>', methods=['POST'])
@require_login
@require_game
def sign_wrestler(wrestler_name):
    game_state = get_game_state()
    progression = game_state.progression
    limits = get_cumulative_limits(progression.level)
    roster_limit = limits.get("roster_limit", 5)

    if len(game_state.promotion.roster) >= roster_limit:
        flash('Roster is full!', 'error')
        return redirect(url_for('free_agents'))

    wrestler = None
    for w in game_state.free_agents:
        if w.name == wrestler_name:
            wrestler = w
            break

    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('free_agents'))

    asking_salary = wrestler.salary if wrestler.salary > 0 else 200 + (wrestler.popularity * 10) + (wrestler.overall_rating * 5)
    signing_bonus = asking_salary * 4

    if game_state.promotion.budget < signing_bonus:
        flash('Cannot afford signing bonus!', 'error')
        return redirect(url_for('free_agents'))

    game_state.promotion.budget -= signing_bonus
    wrestler.salary = asking_salary
    wrestler.contract_length = 52
    wrestler.is_signed = True
    wrestler.morale = 75
    game_state.promotion.roster.append(wrestler)
    game_state.free_agents.remove(wrestler)

    if hasattr(game_state, 'weekly_agent_names') and wrestler.name in game_state.weekly_agent_names:
        game_state.weekly_agent_names.remove(wrestler.name)

    # Only first wrestler signing gives XP (milestone)
    if progression.stats.get("wrestlers_signed_total", 0) == 0:
        progression.add_xp(100, "First Wrestler Signed!")
        flash('🎉 First Wrestler Signed Achievement! +100 XP', 'success')

    progression.update_stat("wrestlers_signed_total")
    save_game_state(game_state)
    flash(f'{wrestler.name} has been signed!', 'success')
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
        for v in venues:
            if v.id == current_venue_id:
                current_venue = v
                break

    currency = game_state.game_settings.get("currency_symbol", "$")

    # Get championships with full info for title match filtering
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

    estimated_venue_cost = current_venue.rental_cost if current_venue else 0
    estimated_salary_cost = sum(w.salary for w in promotion.roster)

    prod_data = session.get('show_production', {})
    current_production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    estimated_production_cost = current_production.get_total_cost()

    booked_names = set()
    for match in current_card:
        for i in range(1, 9):
            name = match.get(f'wrestler{i}', '')
            if name:
                booked_names.add(name)

    available_for_booking = [w for w in available if w.name not in booked_names]
    match_type_info = get_match_type_info()

    show_date_string = format_date(show_date['year'], show_date['month'], show_date['day'])

    # Match slot limits
    max_matches = limits.get("match_slots_weekly", 4)
    card_full = len(current_card) >= max_matches

    return render_template('book_show.html',
        venues=venues, wrestlers=available_for_booking, all_wrestlers=available,
        match_types=match_types, match_type_info=match_type_info,
        current_card=current_card, current_venue=current_venue, currency=currency,
        championships=championships,
        show_date=show_date,
        show_date_string=show_date_string,
        has_booked_show=has_booked_show, estimated_venue_cost=estimated_venue_cost,
        estimated_salary_cost=estimated_salary_cost,
        estimated_production_cost=estimated_production_cost,
        can_book=len(current_card) > 0 and current_venue is not None,
        can_run=len(current_card) > 0 and current_venue is not None,
        max_matches=max_matches,
        card_full=card_full)


@app.route('/select-venue/<path:venue_id>')
@require_login
@require_game
def select_venue(venue_id):
    game_state = get_game_state()
    continent = game_state.game_settings.get("continent", "North America")
    all_venues = get_venues_by_continent(continent)
    for v in all_venues:
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

    # Check match slot limit
    current_card = session.get('current_card', [])
    limits = get_cumulative_limits(progression.level)
    max_matches = limits.get("match_slots_weekly", 4)

    if len(current_card) >= max_matches:
        flash(f'Card is full! Maximum {max_matches} matches at your level.', 'error')
        return redirect(url_for('book_show'))

    match_type = request.form.get('match_type', 'Singles')
    title_match = request.form.get('title_match', '')

    info = get_match_type_info().get(match_type, {"participants": 2, "type": "singles", "intergender": False})
    num_participants = info["participants"]
    is_intergender = info.get("intergender", False)

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

    # Gender check (skip for intergender)
    if not is_intergender:
        wrestler_genders = []
        for name in wrestlers:
            for w in promotion.roster:
                if w.name == name:
                    wrestler_genders.append(w.gender.value)
                    break

        if len(set(wrestler_genders)) > 1:
            flash('Mixed genders! Use an Intergender match type for mixed gender matches.', 'error')
            return redirect(url_for('book_show'))

    booked = set()
    for match in current_card:
        for key in [f'wrestler{i}' for i in range(1, 9)]:
            n = match.get(key, '')
            if n:
                booked.add(n)

    already_booked = [w for w in wrestlers if w in booked]
    if already_booked:
        flash(f'Already booked: {", ".join(already_booked)}', 'error')
        return redirect(url_for('book_show'))

        match_rules = request.form.get('match_rules', 'Standard')

    match_data = {
        'match_type': match_type, 'match_format': info["type"],
        'match_rules': match_rules,
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

    rules_text = f" [{match_rules}]" if match_rules != "Standard" else ""
    title_text = f" for the {title_match}" if title_match else ""
    flash(f'Added: {match_data["display"]} ({match_type}){rules_text}{title_text}', 'success')
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
    """Reorder matches on the card via drag and drop"""
    new_order = request.form.get('match_order', '')

    if not new_order:
        return redirect(url_for('book_show'))

    try:
        order_indices = [int(x) for x in new_order.split(',')]
    except ValueError:
        flash('Invalid reorder data!', 'error')
        return redirect(url_for('book_show'))

    current_card = session.get('current_card', [])

    if len(order_indices) != len(current_card):
        flash('Card mismatch!', 'error')
        return redirect(url_for('book_show'))

    # Reorder
    new_card = []
    for idx in order_indices:
        if 0 <= idx < len(current_card):
            new_card.append(current_card[idx])

    # Last match is always main event
    for i, match in enumerate(new_card):
        match['is_main_event'] = (i == len(new_card) - 1)

    session['current_card'] = new_card
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

    continent = game_state.game_settings.get("continent", "North America")
    all_venues = get_venues_by_continent(continent)
    venue = None
    venue_tier = 1
    for v in all_venues:
        if v.id == venue_id:
            venue = v
            venue_tier = v.tier.value
            break

    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('book_show'))

    prod_data = session.get('show_production', {})
    current_production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()

    ring_options = get_available_options("ring", venue_tier)
    lighting_options = get_available_options("lighting", venue_tier)
    camera_options = get_available_options("cameras", venue_tier)
    backstage_options = get_available_options("backstage", venue_tier)
    pyro_options = get_available_options("pyro", venue_tier)
    entrance_options = get_available_options("entrance", venue_tier)
    audio_options = get_available_options("audio", venue_tier)

    summary = current_production.get_summary()

    return render_template('show_production.html',
        venue=venue, venue_tier=venue_tier, production=current_production,
        summary=summary, ring_options=ring_options, lighting_options=lighting_options,
        camera_options=camera_options, backstage_options=backstage_options,
        pyro_options=pyro_options, entrance_options=entrance_options,
        audio_options=audio_options, budget=game_state.promotion.budget)


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
    total_cost = production.get_total_cost()
    flash(f'Production updated! Cost: ${total_cost:,} per show', 'success')
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
        show_date = {
            'year': promotion.current_year,
            'month': promotion.current_month,
            'day': promotion.current_day,
        }

    game_state.booked_show = {
        'card': current_card,
        'venue_id': venue_id,
        'production': prod_data,
        'show_date': show_date,
    }
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
            booked_show = {
                'card': current_card, 'venue_id': venue_id,
                'production': prod_data, 'show_date': show_date,
            }

    if not booked_show:
        flash('No show booked! Book a show first.', 'error')
        return redirect(url_for('book_show'))

    card = booked_show['card']
    venue_id = booked_show['venue_id']
    show_date = booked_show.get('show_date', {
        'year': promotion.current_year,
        'month': promotion.current_month,
        'day': promotion.current_day,
    })

    prod_data = booked_show.get('production', {})
    production = ShowProduction.from_dict(prod_data) if prod_data else ShowProduction()
    production_cost = production.get_total_cost()
    production_quality = production.get_total_quality_bonus()
    production_fans = production.get_total_fan_bonus()

    continent = game_state.game_settings.get("continent", "North America")
    all_venues = get_venues_by_continent(continent)
    venue = None
    for v in all_venues:
        if v.id == venue_id:
            venue = v
            break

    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('dashboard'))

    match_engine = MatchEngine(promotion)
    results = []
    total_rating = 0.0
    five_star = 0
    four_star = 0
    title_changes = []

    for match_data in card:
        participants = []
        for i in range(1, 9):
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

        match_format = match_data.get('match_format', 'singles')
        if match_format in ['multi', 'tag', 'tag3', 'tag4'] and len(participants) > 2:
            weights = [p.popularity + p.overall_rating for p in participants]
            actual_winner = random.choices(participants, weights=weights, k=1)[0]
            losers = [p for p in participants if p != actual_winner]
            actual_loser = random.choice(losers) if losers else w2
        else:
            actual_winner = result.winner
            actual_loser = result.loser

        for p in participants:
            if p != w1 and p != w2:
                p.add_fatigue(8)

        display = match_data.get('display', f'{w1.name} vs {w2.name}')
        adjusted_rating = min(5.0, result.match_rating + (production_quality * 0.02))

        match_result = {
            'display': display, 'wrestler1': w1.name, 'wrestler2': w2.name,
            'all_participants': [p.name for p in participants],
            'winner': actual_winner.name if actual_winner else 'DRAW',
            'finish': result.finish_type.value, 'rating': adjusted_rating,
            'crowd': result.crowd_reaction,
            'match_type': match_data.get('match_type', 'Singles'),
            'is_main_event': match_data.get('is_main_event', False),
            'is_title_match': match_data.get('is_title_match', False),
            'title_name': match_data.get('title_name', ''),
            'is_intergender': match_data.get('is_intergender', False),
            'title_changed': False,
        }

        if match_data.get('is_title_match') and match_data.get('title_name') and actual_winner:
            title_name = match_data['title_name']
            if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
                champ = game_state.championship_manager.get_championship_by_name(title_name)
                if champ:
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

        if actual_winner and actual_loser:
            actual_winner.record_match("win")
            actual_loser.record_match("loss")
            if match_format == 'multi':
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
            game_state.ai_director.record_match_result(
                actual_winner.name, actual_loser.name, adjusted_rating,
            )

    avg_rating = total_rating / len(results) if results else 0

    attendance = venue.get_expected_attendance(promotion.prestige)
    attendance = min(attendance, venue.capacity)
    is_sellout = attendance >= venue.capacity * 0.95

    ticket_price = venue.get_ticket_price_range()["standard"]
    ticket_revenue = attendance * ticket_price
    merch_revenue = int(attendance * 5 * promotion.merchandise_modifier)
    venue_cost = venue.get_rental_cost()
    total_costs = venue_cost + production_cost
    total_revenue = ticket_revenue + merch_revenue
    profit = total_revenue - total_costs

    promotion.budget += profit
    promotion.fan_base += production_fans

    # First-time milestones
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
        ticket_price=ticket_price, merchandise_modifier=promotion.merchandise_modifier,
        total_matches=len(results),
    )

    promotion.fan_base += show_rewards['fans']['total']

    # Add to calendar
    if not hasattr(game_state, 'calendar_system') or game_state.calendar_system is None:
        game_state.calendar_system = CalendarSystem()

    main_event_match = ""
    if results:
        main_event_match = results[-1].get('display', '')

    game_state.calendar_system.add_show(
        year=show_date['year'],
        month=show_date['month'],
        day=show_date['day'],
        venue=venue.name,
        attendance=attendance,
        capacity=venue.capacity,
        rating=avg_rating,
        profit=profit,
        is_sellout=is_sellout,
        main_event=main_event_match,
        matches_count=len(results),
    )

    venue.record_event(attendance, profit)

    # Advance promotion to day after show
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
        venue_cost=venue_cost, production_cost=production_cost,
        profit=profit, xp_earned=show_rewards['xp']['total'],
        fans_earned=show_rewards['fans']['total'] + production_fans,
        leveled_up=show_rewards.get('leveled_up', False),
        new_level=show_rewards.get('new_level', progression.level),
        achievements=show_rewards.get('achievements_earned', []),
        title_changes=title_changes, currency=currency,
        salaries_paid=total_salaries, new_events=new_events,
        new_week=promotion.current_week, new_year=promotion.current_year,
        production_quality=production_quality, production_fans=production_fans)


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
    new_events = len(ai_result.get('new_events', []))
    flash(f'Skipped a week. Now {promotion.current_day}/{promotion.current_month}/Y{promotion.current_year}. Salaries: ${total_salaries:,}. Lost {fan_loss} fans.', 'warning')
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
    return render_template('events.html', events=all_events)


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
        if effects.get('release'):
            event = result.get('event')
            if event:
                for name in event.wrestlers_involved:
                    for w in promotion.roster[:]:
                        if w.name == name:
                            promotion.roster.remove(w)
                            break
        if effects.get('money'):
            promotion.budget += effects['money']
        if effects.get('salary_change'):
            event = result.get('event')
            if event:
                for name in event.wrestlers_involved:
                    for w in promotion.roster:
                        if w.name == name:
                            w.salary += effects['salary_change']
                            break
        if effects.get('morale'):
            event = result.get('event')
            if event:
                for name in event.wrestlers_involved:
                    for w in promotion.roster:
                        if w.name == name:
                            w.morale = max(0, min(100, w.morale + effects['morale']))
                            break
        if effects.get('fine_amount'):
            promotion.budget += effects['fine_amount']
        if effects.get('bonus'):
            promotion.budget -= effects['bonus']
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
    try:
        game_state = get_game_state()
        promotion = game_state.promotion
        progression = game_state.progression

        if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
            game_state.championship_manager = ChampionshipManager()
            game_state.championship_manager.setup_default_accolades()
            save_game_state(game_state)

        champ_manager = game_state.championship_manager
        limits = get_cumulative_limits(progression.level)
        max_champs = limits.get("max_championships", 0)

        active = champ_manager.get_active_championships() if champ_manager else []
        tournaments = []
        try:
            tournaments = champ_manager.get_active_tournaments() + champ_manager.get_planning_tournaments()
        except Exception:
            pass
        accolades = []
        try:
            accolades = champ_manager.accolades if champ_manager.accolades else []
        except Exception:
            pass
        next_cost = 0
        try:
            next_cost = champ_manager.get_next_slot_cost()
        except Exception:
            pass

        return render_template('championships.html',
            promotion=promotion, championships=active, tournaments=tournaments,
            accolades=accolades, unlocked_slots=champ_manager.unlocked_slots,
            max_slots=champ_manager.max_slots, next_slot_cost=next_cost,
            max_championships=max_champs, current_level=progression.level,
            championship_costs=CHAMPIONSHIP_COSTS, budget=promotion.budget)
    except Exception as e:
        import traceback
        return f"<h1>Championship Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", 500


@app.route('/create-championship', methods=['GET', 'POST'])
@require_login
@require_game
def create_championship():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
        game_state.championship_manager = ChampionshipManager()
        game_state.championship_manager.setup_default_accolades()

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

        can_create, message = champ_manager.can_create_championship(progression.level, promotion.prestige)
        if not can_create:
            flash(f'Cannot create championship: {message}', 'error')
            return redirect(url_for('championships'))

        costs = CHAMPIONSHIP_COSTS.get(level_enum, {})
        creation_cost = costs.get("creation_cost", 15000)
        if promotion.budget < creation_cost:
            flash(f'Cannot afford! Need ${creation_cost:,}', 'error')
            return redirect(url_for('championships'))

        championship = champ_manager.create_championship(name=name, level=level_enum, gender=gender_enum, rules=rules_enum)
        if championship:
            promotion.budget -= creation_cost
            if progression:
                if progression.stats.get("championships_created", 0) == 0:
                    progression.add_xp(200, "First Championship Created!")
                    flash('🎉 First Championship Achievement! +200 XP', 'success')
                progression.update_stat("championships_created")
            save_game_state(game_state)
            flash(f'Created the {name}!', 'success')
        else:
            flash('Failed to create championship! No available slots.', 'error')
        return redirect(url_for('championships'))

    levels = [{"value": l.value, "name": l.value, "cost": CHAMPIONSHIP_COSTS[l]["creation_cost"]} for l in ChampionshipLevel]
    genders = [g.value for g in ChampionshipGender]
    rules_list = [r.value for r in ChampionshipRule]

    return render_template('create_championship.html', levels=levels, genders=genders,
        rules=rules_list, budget=promotion.budget,
        slots_used=len(champ_manager.championships), slots_available=champ_manager.unlocked_slots)


@app.route('/unlock-slot', methods=['POST'])
@require_login
@require_game
def unlock_slot():
    game_state = get_game_state()
    promotion = game_state.promotion
    if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
        game_state.championship_manager = ChampionshipManager()
        game_state.championship_manager.setup_default_accolades()
    champ_manager = game_state.championship_manager
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
    if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
        flash('No championship system found!', 'error')
        return redirect(url_for('championships'))

    champ_manager = game_state.championship_manager
    championship = champ_manager.get_championship(championship_id)
    if not championship:
        flash('Championship not found!', 'error')
        return redirect(url_for('championships'))

    is_tag_title = championship.is_tag_title or championship.level.value == 'Tag Team Championship'

    if request.method == 'POST':
        wrestler_name = request.form.get('wrestler')
        tag_partner = request.form.get('tag_partner', '')

        if not wrestler_name:
            flash('Please select a wrestler!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        if is_tag_title and not tag_partner:
            flash('Tag titles need 2 champions! Please select a tag partner.', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        if is_tag_title and wrestler_name == tag_partner:
            flash('Cannot be your own tag partner!', 'error')
            return redirect(url_for('award_title', championship_id=championship_id))

        date_str = format_date(promotion.current_year, promotion.current_month, promotion.current_day)
        championship.award_title(wrestler_name, date_str, "Awarded championship", tag_partner=tag_partner if is_tag_title else "")

        for w in promotion.roster:
            if w.name == wrestler_name:
                w.titles_held += 1
                w.adjust_momentum(15)
                w.morale = min(100, w.morale + 20)
                break

        if is_tag_title and tag_partner:
            for w in promotion.roster:
                if w.name == tag_partner:
                    w.titles_held += 1
                    w.adjust_momentum(15)
                    w.morale = min(100, w.morale + 20)
                    break

        progression = game_state.progression
        if progression:
            if progression.stats.get("title_changes", 0) == 0:
                progression.add_xp(150, "First Champion Crowned!")
                flash('🎉 First Champion Crowned Achievement! +150 XP', 'success')
            progression.update_stat("title_changes")

        save_game_state(game_state)

        if is_tag_title:
            flash(f'{wrestler_name} & {tag_partner} are the new {championship.name}!', 'success')
        else:
            flash(f'{wrestler_name} is the new {championship.name}!', 'success')
        return redirect(url_for('championships'))

    eligible = []
    for w in promotion.roster:
        if not w.is_injured:
            try:
                if championship.can_wrestler_compete(w.gender.value):
                    eligible.append(w)
            except Exception:
                eligible.append(w)
    eligible.sort(key=lambda w: w.popularity, reverse=True)

    return render_template('award_title.html',
        championship=championship,
        wrestlers=eligible,
        is_tag_title=is_tag_title)


@app.route('/vacate-title/<path:championship_id>', methods=['POST'])
@require_login
@require_game
def vacate_title(championship_id):
    game_state = get_game_state()
    if not hasattr(game_state, 'championship_manager') or game_state.championship_manager is None:
        flash('No championship system found!', 'error')
        return redirect(url_for('championships'))
    champ_manager = game_state.championship_manager
    championship = champ_manager.get_championship(championship_id)
    if championship:
        championship.vacate("Vacated by management")
        save_game_state(game_state)
        flash(f'{championship.name} has been vacated!', 'info')
    return redirect(url_for('championships'))


# ==================== CAREER ====================

@app.route('/career')
@require_login
@require_game
def career():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
    tier = get_promotion_tier(level)
    earned_achievements = progression.get_earned_achievements()
    currency = game_state.game_settings.get("currency_symbol", "$")
    return render_template('career.html', promotion=promotion, progression=progression,
        level=level, tier_name=get_tier_name(tier), xp_percentage=percentage,
        stats=progression.stats, achievements=earned_achievements,
        total_achievements=len(progression.achievements), currency=currency)


# ==================== TUTORIAL ====================

@app.route('/tutorial')
@require_login
def tutorial():
    return render_template('tutorial.html')


# ==================== SAVE/QUIT ====================

@app.route('/save-game', methods=['POST'])
@require_login
@require_game
def save_game():
    game_state = get_game_state()
    save_name = request.form.get('save_name', game_state.promotion.name)
    save_name = save_name.replace(' ', '_')
    if game_state.save(save_name):
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
    username = session.get('username')
    logged_in = session.get('logged_in')
    session.clear()
    if username:
        session['username'] = username
    if logged_in:
        session['logged_in'] = logged_in
    flash('Game closed.', 'info')
    return redirect(url_for('index'))


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
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50 + "\n")

    app.run(debug=debug, host='0.0.0.0', port=port)
