"""
The Booking Room - Flask Web Application
Day 2: Show booking overhaul with dates and production
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
    ChampionshipGender, ChampionshipRule, CHAMPIONSHIP_COSTS, SLOT_COSTS
)
from systems.match_engine import MatchEngine
from systems.save_manager import GameState, SaveManager
from ai.director import AIDirector
from ai.event_generator import EventSeverity
from data.venues import get_venues_by_continent, get_all_venues
from data.free_agents import (
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

def get_week_day_name(week_number):
    """Get the show day for the current week"""
    return "Saturday"  # Default show day


def process_week_advancement(game_state):
    """Process everything that happens when a week advances"""
    promotion = game_state.promotion
    progression = game_state.progression
    ai_director = game_state.ai_director
    
    # Pay salaries
    total_salaries = sum(w.salary for w in promotion.roster)
    promotion.budget -= total_salaries
    
    # Championship maintenance
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        maintenance = game_state.championship_manager.get_total_maintenance_cost()
        promotion.budget -= maintenance
        game_state.championship_manager.weekly_update()
    
    # Update wrestlers
    for wrestler in promotion.roster:
        wrestler.weekly_update()
    
    # Process AI director
    roster_data = [
        {
            "name": w.name,
            "ego": w.ego,
            "loyalty": w.loyalty,
            "professionalism": w.professionalism,
            "morale": w.morale,
            "popularity": w.popularity,
            "salary": w.salary,
            "contract_length": w.contract_length,
            "is_injured": w.is_injured,
            "age": w.age,
            "momentum": w.momentum,
            "wins": w.wins,
            "losses": w.losses,
        }
        for w in promotion.roster
    ]
    
    ai_result = {"new_events": []}
    if ai_director:
        ai_result = ai_director.process_weekly_update(
            roster=roster_data,
            budget=promotion.budget,
            fans=promotion.fan_base,
            prestige=promotion.prestige,
            current_week=promotion.current_week,
        )
    
    # Weekly progression
    if progression:
        progression.process_weekly_update(
            active_wrestlers=len([w for w in promotion.roster if not w.is_injured]),
            total_fans=promotion.fan_base,
            current_budget=promotion.budget,
            weekly_profit=-total_salaries,
            roster_size=len(promotion.roster),
        )
    
    # Refresh free agents
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
    
    # Cap free agent pool
    max_pool = 80
    if len(game_state.free_agents) > max_pool:
        num_remove = len(game_state.free_agents) - max_pool
        for _ in range(num_remove):
            if len(game_state.free_agents) > 20:
                idx = random.randint(0, len(game_state.free_agents) - 1)
                game_state.free_agents.pop(idx)
    
    # Advance week
    promotion.advance_week()
    
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
        philosophy = request.form.get('philosophy', 'Work Rate')
        creative_control = request.form.get('creative_control') == 'on'
        cc_difficulty = request.form.get('cc_difficulty', 'Normal')
        
        game_state = GameState()
        game_state.promoter_name = promoter_name
        
        phil_enum = Philosophy.WORKRATE
        for p in Philosophy:
            if p.value == philosophy:
                phil_enum = p
                break
        
        profile = get_philosophy_profile(phil_enum)
        currency_code, currency_symbol = get_currency(country)
        
        promotion = Promotion(
            name=promotion_name,
            philosophy=phil_enum,
            owner_name=promoter_name,
            starting_budget=profile.starting_budget,
            location=f"{city}, {country}",
        )
        
        promotion.fan_base = profile.starting_fans
        promotion.prestige = profile.prestige_start
        promotion.merchandise_modifier = profile.merchandise_modifier
        
        game_state.promotion = promotion
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
        
        game_state.progression = ProgressionSystem()
        game_state.ai_director = AIDirector(
            creative_control_enabled=creative_control,
            creative_control_difficulty=cc_difficulty,
        )
        game_state.championship_manager = ChampionshipManager()
        game_state.championship_manager.setup_default_accolades()
        
        all_agents = generate_all_free_agents()
        starting_agents = []
        for tier, agents in all_agents.items():
            tier_config = TIER_CONFIG[tier]
            if tier_config["level_required"] <= 1:
                starting_agents.extend(agents)
        game_state.free_agents = starting_agents
        
        # Initialize booked show as empty
        game_state.booked_show = None
        
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        game_sessions[session_id] = game_state
        
        flash(f'{promotion_name} has been created!', 'success')
        return redirect(url_for('dashboard'))
    
    continents = get_continents()
    philosophies = [
        {
            "value": p.value,
            "name": p.value,
            "budget": get_philosophy_profile(p).starting_budget,
            "fans": get_philosophy_profile(p).starting_fans,
            "description": get_philosophy_profile(p).description,
        }
        for p in Philosophy
    ]
    
    return render_template('setup.html',
                          continents=continents,
                          philosophies=philosophies)


@app.route('/load-game/<save_name>')
@require_login
def load_game(save_name):
    game_state = GameState()
    
    if game_state.load(save_name):
        game_state.ensure_all_systems()
        
        if not hasattr(game_state, 'booked_show'):
            game_state.booked_show = None
        
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
    
    # Check if show is booked
    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    booked_show = game_state.booked_show if has_booked_show else None
    
    return render_template('dashboard.html',
                          promotion=promotion,
                          progression=progression,
                          level=level,
                          xp_percentage=percentage,
                          tier_name=get_tier_name(tier),
                          limits=limits,
                          events=events,
                          critical_events=critical_events,
                          currency=currency,
                          roster_count=len(promotion.roster),
                          injured_count=len([w for w in promotion.roster if w.is_injured]),
                          champ_count=champ_count,
                          show_day=show_day,
                          has_booked_show=has_booked_show,
                          booked_show=booked_show)


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
    
    return render_template('roster.html',
                          wrestlers=sorted_roster,
                          roster_limit=limits.get("roster_limit", 5),
                          currency=currency,
                          total_salary=sum(w.salary for w in promotion.roster))


@app.route('/wrestler/<wrestler_name>')
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
    
    return render_template('wrestler_detail.html',
                          wrestler=wrestler,
                          currency=currency)


@app.route('/release-wrestler/<wrestler_name>', methods=['POST'])
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
    
    agents_with_salary = []
    for w in game_state.free_agents:
        ovr = w.overall_rating
        if ovr >= 75:
            tier = 5
            tier_name = "⭐ Main Event"
        elif ovr >= 60:
            tier = 4
            tier_name = "🟡 Veteran"
        elif ovr >= 45:
            tier = 3
            tier_name = "🟢 Rising Star"
        elif ovr >= 35:
            tier = 2
            tier_name = "🔵 Independent"
        else:
            tier = 1
            tier_name = "⚪ Rookie"
        
        asking = w.salary if w.salary > 0 else 200 + (w.popularity * 10) + (w.overall_rating * 5)
        
        agents_with_salary.append({
            "wrestler": w,
            "asking_salary": asking,
            "signing_bonus": asking * 4,
            "tier": tier,
            "tier_name": tier_name,
        })
    
    agents_with_salary.sort(key=lambda x: (-x["tier"], -x["wrestler"].popularity))
    
    currency = game_state.game_settings.get("currency_symbol", "$")
    
    tier_info = []
    for t in range(1, 6):
        tc = TIER_CONFIG[t]
        tier_info.append({
            "tier": t,
            "name": tc["name"],
            "level_required": tc["level_required"],
            "is_unlocked": current_level >= tc["level_required"],
        })
    
    return render_template('free_agents.html',
                          agents=agents_with_salary,
                          can_sign=can_sign,
                          roster_count=current_roster,
                          roster_limit=roster_limit,
                          budget=game_state.promotion.budget,
                          currency=currency,
                          tier_info=tier_info,
                          current_level=current_level,
                          total_agents=len(game_state.free_agents))


@app.route('/sign-wrestler/<wrestler_name>', methods=['POST'])
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
    
    progression.add_xp(15, f"Signed {wrestler.name}")
    progression.update_stat("wrestlers_signed_total")
    
    save_game_state(game_state)
    flash(f'{wrestler.name} has been signed!', 'success')
    
    return redirect(url_for('free_agents'))


# ==================== BOOK SHOW (NEW FLOW) ====================

@app.route('/book-show')
@require_login
@require_game
def book_show():
    """Book a show - plan matches and production"""
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
    
    # Get current booking from session
    current_card = session.get('current_card', [])
    current_venue_id = session.get('current_venue_id')
    
    current_venue = None
    if current_venue_id:
        for v in venues:
            if v.id == current_venue_id:
                current_venue = v
                break
    
    currency = game_state.game_settings.get("currency_symbol", "$")
    show_day = game_state.game_settings.get("show_day", "Saturday")
    
    # Get championships for title match option
    championships = []
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        championships = game_state.championship_manager.get_active_championships()
    
    # Check if already booked
    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    
    # Calculate estimated costs
    estimated_venue_cost = current_venue.rental_cost if current_venue else 0
    estimated_salary_cost = sum(w.salary for w in promotion.roster)
    
    return render_template('book_show.html',
                          venues=venues,
                          wrestlers=available,
                          match_types=match_types,
                          current_card=current_card,
                          current_venue=current_venue,
                          currency=currency,
                          championships=championships,
                          show_day=show_day,
                          week=promotion.current_week,
                          year=promotion.current_year,
                          has_booked_show=has_booked_show,
                          estimated_venue_cost=estimated_venue_cost,
                          estimated_salary_cost=estimated_salary_cost,
                          can_book=len(current_card) > 0 and current_venue is not None,
                          can_run=len(current_card) > 0 and current_venue is not None)


@app.route('/select-venue/<venue_id>')
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
            flash(f'Selected: {v.name}', 'success')
            break
    
    return redirect(url_for('book_show'))


@app.route('/add-match', methods=['POST'])
@require_login
@require_game
def add_match():
    wrestler1_name = request.form.get('wrestler1')
    wrestler2_name = request.form.get('wrestler2')
    match_type = request.form.get('match_type', 'Standard')
    title_match = request.form.get('title_match', '')
    
    if wrestler1_name == wrestler2_name:
        flash('Cannot book same wrestler against themselves!', 'error')
        return redirect(url_for('book_show'))
    
    current_card = session.get('current_card', [])
    
    booked = set()
    for match in current_card:
        booked.add(match['wrestler1'])
        booked.add(match['wrestler2'])
    
    if wrestler1_name in booked or wrestler2_name in booked:
        flash('One or both wrestlers already booked!', 'error')
        return redirect(url_for('book_show'))
    
    current_card.append({
        'wrestler1': wrestler1_name,
        'wrestler2': wrestler2_name,
        'match_type': match_type,
        'is_main_event': True,
        'is_title_match': bool(title_match),
        'title_name': title_match,
    })
    
    for i, match in enumerate(current_card):
        match['is_main_event'] = (i == len(current_card) - 1)
    
    session['current_card'] = current_card
    
    title_text = f" for the {title_match}" if title_match else ""
    flash(f'Added: {wrestler1_name} vs {wrestler2_name}{title_text}', 'success')
    
    return redirect(url_for('book_show'))


@app.route('/remove-match/<int:match_index>')
@require_login
@require_game
def remove_match(match_index):
    current_card = session.get('current_card', [])
    
    if 0 <= match_index < len(current_card):
        removed = current_card.pop(match_index)
        
        if current_card:
            for i, match in enumerate(current_card):
                match['is_main_event'] = (i == len(current_card) - 1)
        
        session['current_card'] = current_card
        flash(f'Removed: {removed["wrestler1"]} vs {removed["wrestler2"]}', 'info')
    
    return redirect(url_for('book_show'))


@app.route('/save-show', methods=['POST'])
@require_login
@require_game
def save_show():
    """Save the booked show (lock it in) without running it"""
    game_state = get_game_state()
    
    current_card = session.get('current_card', [])
    venue_id = session.get('current_venue_id')
    
    if not current_card or not venue_id:
        flash('No show to save! Add matches and select a venue.', 'error')
        return redirect(url_for('book_show'))
    
    # Save the booked show to game state
    game_state.booked_show = {
        'card': current_card,
        'venue_id': venue_id,
        'week': game_state.promotion.current_week,
        'year': game_state.promotion.current_year,
        'show_day': game_state.game_settings.get("show_day", "Saturday"),
    }
    
    save_game_state(game_state)
    
    # Clear session booking (it's now saved in game state)
    session['current_card'] = []
    session['current_venue_id'] = None
    
    flash(f'Show booked for {game_state.booked_show["show_day"]}, Week {game_state.booked_show["week"]}! Go to Dashboard and click Run Show when ready.', 'success')
    
    return redirect(url_for('dashboard'))


@app.route('/run-show', methods=['POST'])
@require_login
@require_game
def run_show():
    """Run the booked show AND advance the week"""
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression
    
    # Check for booked show in game state first, then session
    booked_show = None
    if hasattr(game_state, 'booked_show') and game_state.booked_show:
        booked_show = game_state.booked_show
    
    # Fallback to session if no saved show
    if not booked_show:
        current_card = session.get('current_card', [])
        venue_id = session.get('current_venue_id')
        if current_card and venue_id:
            booked_show = {
                'card': current_card,
                'venue_id': venue_id,
            }
    
    if not booked_show:
        flash('No show booked! Book a show first.', 'error')
        return redirect(url_for('book_show'))
    
    card = booked_show['card']
    venue_id = booked_show['venue_id']
    
    # Find venue
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
    
    # Run matches
    match_engine = MatchEngine(promotion)
    results = []
    total_rating = 0.0
    five_star = 0
    four_star = 0
    title_changes = []
    
    for match_data in card:
        w1 = w2 = None
        for w in promotion.roster:
            if w.name == match_data['wrestler1']:
                w1 = w
            if w.name == match_data['wrestler2']:
                w2 = w
        
        if w1 and w2:
            result = match_engine.simulate_match(
                wrestler1=w1,
                wrestler2=w2,
                is_title_match=match_data.get('is_title_match', False),
                is_main_event=match_data.get('is_main_event', False),
            )
            
            match_result = {
                'wrestler1': w1.name,
                'wrestler2': w2.name,
                'winner': result.winner.name if result.winner else 'DRAW',
                'finish': result.finish_type.value,
                'rating': result.match_rating,
                'crowd': result.crowd_reaction,
                'is_main_event': match_data.get('is_main_event', False),
                'is_title_match': match_data.get('is_title_match', False),
                'title_name': match_data.get('title_name', ''),
                'title_changed': False,
            }
            
            # Handle title matches
            if match_data.get('is_title_match') and match_data.get('title_name') and result.winner:
                title_name = match_data['title_name']
                if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
                    champ = game_state.championship_manager.get_championship_by_name(title_name)
                    if champ:
                        if champ.current_champion == result.winner.name:
                            champ.record_defense(result.loser.name if result.loser else "")
                        else:
                            date = f"Year {promotion.current_year}, Week {promotion.current_week}"
                            champ.award_title(result.winner.name, date)
                            result.winner.titles_held += 1
                            match_result['title_changed'] = True
                            title_changes.append({
                                'title': title_name,
                                'new_champion': result.winner.name,
                            })
                            if progression:
                                progression.update_stat("title_changes")
            
            results.append(match_result)
            total_rating += result.match_rating
            
            if result.match_rating >= 5.0:
                five_star += 1
            elif result.match_rating >= 4.0:
                four_star += 1
            
            # Record for AI
            if game_state.ai_director and result.winner and result.loser:
                game_state.ai_director.record_match_result(
                    result.winner.name,
                    result.loser.name,
                    result.match_rating,
                )
    
    avg_rating = total_rating / len(results) if results else 0
    
    # Calculate attendance and financials
    attendance = venue.get_expected_attendance(promotion.prestige)
    attendance = min(attendance, venue.capacity)
    is_sellout = attendance >= venue.capacity * 0.95
    
    ticket_price = venue.get_ticket_price_range()["standard"]
    ticket_revenue = attendance * ticket_price
    merch_revenue = int(attendance * 5 * promotion.merchandise_modifier)
    venue_cost = venue.get_rental_cost()
    
    total_revenue = ticket_revenue + merch_revenue
    profit = total_revenue - venue_cost
    
    promotion.budget += profit
    
    # Process progression
    show_rewards = progression.process_show_completion(
        is_ppv=False,
        average_match_rating=avg_rating,
        attendance=attendance,
        capacity=venue.capacity,
        venue_prestige=venue.prestige,
        venue_tier=venue.tier.value,
        venue_id=venue.id,
        five_star_matches=five_star,
        four_star_matches=four_star,
        ticket_price=ticket_price,
        merchandise_modifier=promotion.merchandise_modifier,
        total_matches=len(results),
    )
    
    promotion.fan_base += show_rewards['fans']['total']
    venue.record_event(attendance, profit)
    
    # Clear the booked show
    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    
    # NOW ADVANCE THE WEEK
    ai_result, total_salaries = process_week_advancement(game_state)
    
    new_events = len(ai_result.get('new_events', []))
    
    save_game_state(game_state)
    
    currency = game_state.game_settings.get("currency_symbol", "$")
    
    return render_template('run_show.html',
                          promotion=promotion,
                          venue=venue,
                          results=results,
                          avg_rating=avg_rating,
                          attendance=attendance,
                          is_sellout=is_sellout,
                          ticket_revenue=ticket_revenue,
                          merch_revenue=merch_revenue,
                          venue_cost=venue_cost,
                          profit=profit,
                          xp_earned=show_rewards['xp']['total'],
                          fans_earned=show_rewards['fans']['total'],
                          leveled_up=show_rewards.get('leveled_up', False),
                          new_level=show_rewards.get('new_level', progression.level),
                          achievements=show_rewards.get('achievements_earned', []),
                          title_changes=title_changes,
                          currency=currency,
                          salaries_paid=total_salaries,
                          new_events=new_events,
                          new_week=promotion.current_week,
                          new_year=promotion.current_year)


@app.route('/skip-week', methods=['POST'])
@require_login
@require_game
def skip_week():
    """Skip a week without running a show (costs money, loses fans)"""
    game_state = get_game_state()
    promotion = game_state.promotion
    
    # Process week advancement without a show
    ai_result, total_salaries = process_week_advancement(game_state)
    
    # Penalty for not running a show
    fan_loss = int(promotion.fan_base * 0.02)  # Lose 2% of fans
    promotion.fan_base = max(0, promotion.fan_base - fan_loss)
    
    save_game_state(game_state)
    
    new_events = len(ai_result.get('new_events', []))
    
    flash(f'Skipped to Year {promotion.current_year}, Week {promotion.current_week}. Salaries: ${total_salaries:,}. Lost {fan_loss} fans for not running a show. {new_events} new event(s).', 'warning')
    
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


@app.route('/resolve-event/<event_id>/<int:option_index>', methods=['POST'])
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
            tournaments = []
        
        accolades = []
        try:
            accolades = champ_manager.accolades if champ_manager.accolades else []
        except Exception:
            accolades = []
        
        next_cost = 0
        try:
            next_cost = champ_manager.get_next_slot_cost()
        except Exception:
            next_cost = 0
        
        return render_template('championships.html',
                              promotion=promotion,
                              championships=active,
                              tournaments=tournaments,
                              accolades=accolades,
                              unlocked_slots=champ_manager.unlocked_slots,
                              max_slots=champ_manager.max_slots,
                              next_slot_cost=next_cost,
                              max_championships=max_champs,
                              current_level=progression.level,
                              championship_costs=CHAMPIONSHIP_COSTS,
                              budget=promotion.budget)
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
        
        can_create, message = champ_manager.can_create_championship(
            progression.level, promotion.prestige
        )
        
        if not can_create:
            flash(f'Cannot create championship: {message}', 'error')
            return redirect(url_for('championships'))
        
        costs = CHAMPIONSHIP_COSTS.get(level_enum, {})
        creation_cost = costs.get("creation_cost", 15000)
        
        if promotion.budget < creation_cost:
            flash(f'Cannot afford! Need ${creation_cost:,}', 'error')
            return redirect(url_for('championships'))
        
        championship = champ_manager.create_championship(
            name=name,
            level=level_enum,
            gender=gender_enum,
            rules=rules_enum,
        )
        
        if championship:
            promotion.budget -= creation_cost
            if progression:
                progression.update_stat("championships_created")
                progression.add_xp(100, f"Created {name}")
            save_game_state(game_state)
            flash(f'Created the {name}!', 'success')
        else:
            flash('Failed to create championship! No available slots.', 'error')
        
        return redirect(url_for('championships'))
    
    levels = [
        {"value": l.value, "name": l.value, "cost": CHAMPIONSHIP_COSTS[l]["creation_cost"]}
        for l in ChampionshipLevel
    ]
    genders = [g.value for g in ChampionshipGender]
    rules_list = [r.value for r in ChampionshipRule]
    
    return render_template('create_championship.html',
                          levels=levels,
                          genders=genders,
                          rules=rules_list,
                          budget=promotion.budget,
                          slots_used=len(champ_manager.championships),
                          slots_available=champ_manager.unlocked_slots)


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


@app.route('/award-title/<championship_id>', methods=['GET', 'POST'])
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
    
    if request.method == 'POST':
        wrestler_name = request.form.get('wrestler')
        
        if wrestler_name:
            date = f"Year {promotion.current_year}, Week {promotion.current_week}"
            championship.award_title(wrestler_name, date, "Awarded championship")
            
            for w in promotion.roster:
                if w.name == wrestler_name:
                    w.titles_held += 1
                    w.adjust_momentum(15)
                    w.morale = min(100, w.morale + 20)
                    break
            
            progression = game_state.progression
            if progression:
                progression.update_stat("title_changes")
                progression.add_xp(30, f"Crowned {wrestler_name} as {championship.name}")
            
            save_game_state(game_state)
            flash(f'{wrestler_name} is the new {championship.name}!', 'success')
            return redirect(url_for('championships'))
    
    eligible = []
    for w in promotion.roster:
        if not w.is_injured:
            try:
                gender_str = w.gender.value
                if championship.can_wrestler_compete(gender_str):
                    eligible.append(w)
            except Exception:
                eligible.append(w)
    
    eligible.sort(key=lambda w: w.popularity, reverse=True)
    
    return render_template('award_title.html',
                          championship=championship,
                          wrestlers=eligible)


@app.route('/vacate-title/<championship_id>', methods=['POST'])
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
    
    return render_template('career.html',
                          promotion=promotion,
                          progression=progression,
                          level=level,
                          tier_name=get_tier_name(tier),
                          xp_percentage=percentage,
                          stats=progression.stats,
                          achievements=earned_achievements,
                          total_achievements=len(progression.achievements),
                          currency=currency)


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
    countries = get_countries(continent)
    return jsonify(countries)


@app.route('/api/cities/<continent>/<country>')
def api_cities(continent, country):
    cities = get_cities(continent, country)
    return jsonify(cities)


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
