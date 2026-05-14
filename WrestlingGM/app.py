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
from ai.rival_scheduler import RivalScheduler  # <-- CPU rival introduction and scheduling

# Living World is intentionally not run weekly yet.
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

DEV_USERNAMES = {"dlowpow"}

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

# ==================== WEEKLY PULSE HELPER ====================

def process_week_advancement(game_state):
    """
    Process weekly systems.

    RivalScheduler is show-based and should not spam weekly inbox messages.
    Living World AI will return later through Writers Room, News, and Post-Show systems.
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

    # Do not call run_living_world_week here.
    # The CPU rival now reacts through show completion via RivalScheduler.

    return pulse_result, total_salaries

# ==================== CLASS ENROLLMENT WEEKLY PROCESSOR ====================
def process_class_enrollments_weekly(game_state) -> dict:
    """
    Tick all active training class enrollments by 1 week.
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
                student = school.get_trainee(enr.get('student_id'))

            if not student:
                continue

            student_data = {}
            for stat in [
                "strength", "speed", "technique", "charisma",
                "stamina", "toughness", "mic_skills",
                "psychology", "work_ethic"
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
        level, percentage, tier_name = 1, 0, "Backyard"
        limits = get_cumulative_limits(1)

    events = []
    critical_events = []
    if game_state.ai_director:
        try:
            events = game_state.ai_director.get_active_events()
            critical_events = [
                e for e in events
                if hasattr(e, 'severity')
                and e.severity in [EventSeverity.CRITICAL, EventSeverity.MAJOR]
            ]
        except Exception:
            pass

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            champ_count = len(game_state.championship_manager.get_active_championships())
        except Exception:
            pass

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None
    booked_show = game_state.booked_show if has_booked_show else None

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
            is_booked = (
                sd.get('year') == y
                and sd.get('month') == m
                and sd.get('day') == d
            )

        has_show = False
        if cal_system and hasattr(cal_system, 'events'):
            has_show = any(
                ev.year == y and ev.month == m and ev.day == d
                for ev in cal_system.events
            )

        has_rival_show = False
        try:
            rival_scheduler = ensure_rival_scheduler(game_state)
            if rival_scheduler:
                has_rival_show = any(
                    ev.get("year") == y
                    and ev.get("month") == m
                    and ev.get("day") == d
                    for ev in rival_scheduler.get_calendar_events()
                )
        except Exception:
            has_rival_show = False

        is_past = (
            y < current_year
            or (y == current_year and m < current_month)
            or (y == current_year and m == current_month and d < current_day)
        )

        day_events = get_active_seasonal_events(m, d)

        calendar_widget_days.append({
            'day': d,
            'month': m,
            'year': y,
            'is_today': is_today,
            'is_booked': is_booked,
            'has_show': has_show or has_rival_show,
            'has_rival_show': has_rival_show,
            'is_past': is_past,
            'is_event': len(day_events) > 0,
            'event_name': day_events[0]['name'] if day_events else '',
            'event_color': day_events[0]['color'] if day_events else '',
        })

    month_names = [
        m_item.get('name', f'Month {i}') if isinstance(m_item, dict) else str(m_item)
        for i, m_item in enumerate(MONTHS, 1)
    ]

    current_month_name = (
        month_names[current_month - 1]
        if current_month <= len(month_names)
        else f"Month {current_month}"
    )

    seasonal_events = get_active_seasonal_events(current_month, current_day)

    unread_count = 0
    if hasattr(game_state, 'inbox') and game_state.inbox:
        try:
            unread_count = game_state.inbox.get_unread_count()
        except Exception:
            pass

    incoming_calls = 0
    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            incoming_calls = game_state.calls.get_incoming_count()
        except Exception:
            pass

    has_training_school = False
    try:
        has_training_school = game_state.has_training_school()
    except Exception:
        pass

    return render_template(
        'dashboard.html',
        promotion=promotion,
        progression=progression,
        level=level,
        xp_percentage=percentage,
        tier_name=tier_name,
        limits=limits,
        events=events,
        critical_events=critical_events,
        currency=currency,
        roster_count=len(promotion.roster),
        injured_count=len([
            w for w in promotion.roster
            if getattr(w, 'is_injured', False)
        ]),
        champ_count=champ_count,
        has_booked_show=has_booked_show,
        booked_show=booked_show,
        origin_message=origin_message,
        show_tutorial_prompt=show_tutorial_prompt,
        tutorial_active=tutorial_active,
        tutorial_step=tutorial_step,
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
    has_booked_show = (
        hasattr(game_state, 'booked_show')
        and game_state.booked_show is not None
    )

    return render_template(
        'booking_room.html',
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
    limits = get_cumulative_limits(
        game_state.progression.level if game_state.progression else 1
    )

    return render_template(
        'locker_room.html',
        promotion=game_state.promotion,
        roster_count=len(game_state.promotion.roster),
        roster_limit=limits.get("roster_limit", 5),
        injured_count=len([
            w for w in game_state.promotion.roster
            if getattr(w, 'is_injured', False)
        ]),
        hide_base_hud=True,
    )


@app.route('/championship-hub')
@require_login
@require_game
def championship_hub():
    game_state = get_game_state()
    limits = get_cumulative_limits(
        game_state.progression.level if game_state.progression else 1
    )

    champ_count = 0
    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        try:
            champ_count = len(game_state.championship_manager.get_active_championships())
        except Exception:
            pass

    return render_template(
        'championship_hub.html',
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

    total_days_before = (
        sum(days_in_month(mi) for y in range(1, view_year) for mi in range(1, 13))
        + sum(days_in_month(mi) for mi in range(1, view_month))
    )

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
                    'is_rival': False,
                    'rival_name': '',
                    'completed': True,
                    'icon': '🎟️',
                    'color': '#22c55e',
                })

    try:
        rival_scheduler = ensure_rival_scheduler(game_state)

        if rival_scheduler:
            for event in rival_scheduler.get_calendar_events():
                if event.get("year") == view_year and event.get("month") == view_month:
                    d = event.get("day")

                    if d not in day_shows:
                        day_shows[d] = []

                    day_shows[d].append({
                        "venue": event.get("venue", "Unknown Venue"),
                        "rating": event.get("rating", 0),
                        "attendance": event.get("attendance", 0),
                        "is_sellout": False,
                        "profit": 0,
                        "is_rival": True,
                        "rival_name": event.get("title", "Rival Show"),
                        "completed": event.get("completed", False),
                        "icon": event.get("icon", "⚔️"),
                        "color": event.get("color", "#ef4444"),
                    })

    except Exception as e:
        print(f"Rival calendar event error: {e}")

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

    year_stats = (
        cal_system.get_year_stats(view_year)
        if hasattr(cal_system, 'get_year_stats')
        else {}
    )

    prev_month, prev_year = (
        (view_month - 1, view_year)
        if view_month > 1
        else (12, view_year - 1)
    )

    next_month, next_year = (
        (view_month + 1, view_year)
        if view_month < 12
        else (1, view_year + 1)
    )

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    month_names = [
        m.get('name', f'Month {i}') if isinstance(m, dict) else str(m)
        for i, m in enumerate(MONTHS, 1)
    ]

    view_month_name = (
        month_names[view_month - 1]
        if view_month <= len(month_names)
        else f"Month {view_month}"
    )

    current_month_name = (
        month_names[current_month - 1]
        if current_month <= len(month_names)
        else f"Month {current_month}"
    )

    booked_show_date = None
    if hasattr(game_state, 'booked_show') and game_state.booked_show:
        booked_show_date = game_state.booked_show.get('show_date', None)

    return render_template(
        'calendar.html',
        promotion=promotion,
        current_year=current_year,
        current_month=current_month,
        current_day=current_day,
        view_year=view_year,
        view_month=view_month,
        view_month_name=view_month_name,
        current_month_name=current_month_name,
        calendar_weeks=calendar_weeks,
        day_shows=day_shows,
        num_days=num_days,
        year_stats=year_stats,
        months=MONTHS,
        month_names=month_names,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        currency=currency,
        booked_show_date=booked_show_date,
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

    if (
        year < promotion.current_year
        or (
            year == promotion.current_year
            and date_to_day_of_year(month, day)
            < date_to_day_of_year(promotion.current_month, promotion.current_day)
        )
    ):
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

    sorted_roster = sorted(
        game_state.promotion.roster,
        key=lambda w: getattr(w, 'popularity', 0),
        reverse=True,
    )

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    total_fees = sum(
        getattr(w, 'booking_fee', getattr(w, 'salary', 0))
        for w in game_state.promotion.roster
    )

    return render_template(
        'roster.html',
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
    """
    Release a wrestler from the roster.
    Buyout = booking_fee * remaining contract weeks * 0.5.
    Released wrestlers are pushed toward free agency where possible.
    """
    game_state = get_game_state()
    wrestler = next(
        (w for w in game_state.promotion.roster if w.name == wrestler_name),
        None,
    )

    if wrestler:
        booking_fee = getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0))
        contract_length = getattr(wrestler, 'contract_length', 0)
        buyout = int(booking_fee * contract_length * 0.5)

        game_state.promotion.budget -= buyout
        game_state.promotion.roster.remove(wrestler)

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
                wrestler.is_signed = False
                wrestler.contract_length = 0
                game_state.free_agents.append(wrestler)

        else:
            wrestler.is_signed = False
            wrestler.contract_length = 0
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
    """
    Tag Teams & Factions hub.
    Lists all active groups grouped by type and disbanded archive.
    """
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
    """
    Create a new tag team, trio, or faction.
    """
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

    eligible_listings = []

    for listing in all_listings:
        try:
            if listing.tier not in allowed_tiers:
                continue

            cost = (
                listing.signing_bonus
                if getattr(listing, 'is_exclusive_offer', False)
                else listing.asking_per_show
            )

            if cost > budget * 2 and cost > 500:
                continue

            eligible_listings.append(listing)

        except Exception:
            continue

    if needs_refresh:
        sample_size = min(10, len(eligible_listings))
        sampled = random.sample(eligible_listings, sample_size) if eligible_listings else []

        game_state.weekly_agent_names = [
            listing.wrestler.name
            for listing in sampled
        ]
        game_state.weekly_agents_week = week_key
        save_game_state(game_state)

    weekly_names = set(getattr(game_state, 'weekly_agent_names', []))

    visible_listings = [
        listing for listing in eligible_listings
        if listing.wrestler.name in weekly_names
    ]

    agents_with_salary = []

    for listing in visible_listings:
        try:
            wrestler = listing.wrestler

            agents_with_salary.append({
                "wrestler": wrestler,
                "asking_salary": listing.asking_per_show,
                "signing_bonus": listing.signing_bonus,
                "per_show_rate": listing.asking_per_show,
                "tier": listing.tier.value if hasattr(listing.tier, 'value') else str(listing.tier),
                "tier_name": listing.tier.value if hasattr(listing.tier, 'value') else str(listing.tier),
                "is_exclusive_offer": getattr(listing, 'is_exclusive_offer', False),
                "weeks_until_expires": getattr(listing, 'weeks_until_expires', 0),
                "description": getattr(listing, 'description', ''),
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
            success, msg, wrestler, cost = game_state.free_agency.sign_wrestler(
                wrestler_name,
                promotion.budget,
                len(promotion.roster),
                roster_limit,
            )

            if success and wrestler:
                promotion.budget -= cost
                promotion.roster.append(wrestler)
                save_game_state(game_state)
                flash(msg, 'success')
            else:
                flash(msg, 'error')

            return redirect(url_for('free_agents'))

        except Exception as e:
            flash(f'Free agency error: {e}', 'error')
            return redirect(url_for('free_agents'))

    wrestler = next(
        (w for w in game_state.free_agents if w.name == wrestler_name),
        None,
    )

    if not wrestler:
        flash('Wrestler not found!', 'error')
        return redirect(url_for('free_agents'))

    per_show_rate = getattr(wrestler, 'asking_per_show', getattr(wrestler, 'booking_fee', 100))

    if promotion.budget < per_show_rate:
        flash('Not enough money to hire this wrestler!', 'error')
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
    game_state.free_agents.remove(wrestler)

    save_game_state(game_state)
    flash(f'{wrestler.name} hired! Per-show rate: ${per_show_rate}/show', 'success')
    return redirect(url_for('free_agents'))

# ==================== BOOK SHOW ====================
@app.route('/book-show')
@require_login
@require_game
def book_show():
    """
    Main show booking hub.
    Includes venue selection, match card editor, production options,
    and RivalScheduler preview support.
    """
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

    eligible_venues = [
        v for v in all_venues
        if v.tier.value <= max_tier and v.is_unlocked
    ]

    show_all_venues = request.args.get('show_all', '0') == '1'
    recommended_min_tier = max(1, max_tier - 1)

    if show_all_venues or max_tier <= 2:
        venues = eligible_venues
    else:
        venues = [v for v in eligible_venues if v.tier.value >= recommended_min_tier]

    venues.sort(key=lambda v: v.capacity)
    hidden_venue_count = len(eligible_venues) - len(venues)

    available = [
        w for w in promotion.roster
        if not getattr(w, 'is_injured', False)
    ]

    match_types = get_unlocked_match_types(progression.level if progression else 1)
    current_card = session.get('current_card', [])
    current_venue_id = session.get('current_venue_id')
    show_date = session.get('show_date')

    if not show_date:
        show_date = {
            'year': promotion.current_year,
            'month': promotion.current_month,
            'day': promotion.current_day,
        }
        session['show_date'] = show_date

    current_venue = None
    if current_venue_id:
        current_venue = get_venue_by_id(current_venue_id)
        if not current_venue:
            for venue in venues:
                if venue.id == current_venue_id:
                    current_venue = venue
                    break

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")
    show_day_name = get_day_name(
        get_day_of_week(show_date['year'], show_date['month'], show_date['day'])
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
                    'rules': getattr(champ.rules, 'value', champ.rules),
                    'gender': getattr(champ.gender, 'value', champ.gender),
                    'level': getattr(champ.level, 'value', champ.level),
                })
        except Exception:
            championships = []

    has_booked_show = hasattr(game_state, 'booked_show') and game_state.booked_show is not None

    current_production = session.get('show_production', {})
    production_options = {}
    production_cost = 0

    try:
        player_level = progression.level if progression else 1
        production_options = get_available_options(player_level)
        for option_id in current_production.values():
            option = ALL_PRODUCTION_OPTIONS.get(option_id)
            if option:
                production_cost += option.cost
    except Exception:
        production_options = {}
        production_cost = 0

    card_total_time = get_card_total_time(current_card)
    selected_match_type = request.args.get('match_type', 'Singles')
    match_info = get_match_type_info().get(selected_match_type, get_match_type_info()["Singles"])
    match_categories = get_match_categories()

    rival_show_preview = None
    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler:
            rival_show_preview = rival_scheduler.get_next_rival_show_preview()
    except Exception as e:
        print(f"Rival preview error: {e}")
        rival_show_preview = None

    return render_template(
        'book_show.html',
        promotion=promotion,
        progression=progression,
        venues=venues,
        eligible_venue_count=len(eligible_venues),
        hidden_venue_count=hidden_venue_count,
        show_all_venues=show_all_venues,
        current_venue=current_venue,
        available_wrestlers=available,
        match_types=match_types,
        match_categories=match_categories,
        selected_match_type=selected_match_type,
        selected_match_info=match_info,
        current_card=current_card,
        current_production=current_production,
        production_options=production_options,
        production_cost=production_cost,
        category_labels=CATEGORY_LABELS,
        match_time_options=MATCH_TIME_OPTIONS,
        card_total_time=card_total_time,
        show_date=show_date,
        show_day_name=show_day_name,
        championships=championships,
        has_booked_show=has_booked_show,
        booked_show=game_state.booked_show if has_booked_show else None,
        rival_show_preview=rival_show_preview,
        currency=currency,
        limits=limits,
        hide_base_hud=True,
    )


@app.route('/select-venue/<venue_id>', methods=['POST'])
@require_login
@require_game
def select_venue(venue_id):
    session['current_venue_id'] = venue_id
    flash('Venue selected!', 'success')
    return redirect(url_for('book_show'))


@app.route('/set-show-date', methods=['POST'])
@require_login
@require_game
def set_show_date():
    year = int(request.form.get('year', 1))
    month = int(request.form.get('month', 1))
    day = int(request.form.get('day', 1))

    session['show_date'] = {
        'year': year,
        'month': month,
        'day': day,
    }

    flash(f'Show date set to {format_date(year, month, day)}', 'success')
    return redirect(url_for('book_show'))


@app.route('/set-production', methods=['POST'])
@require_login
@require_game
def set_production():
    production = session.get('show_production', {})

    for category in CATEGORY_LABELS.keys():
        value = request.form.get(category)
        if value:
            production[category] = value
        elif category in production:
            del production[category]

    session['show_production'] = production
    flash('Production options updated!', 'success')
    return redirect(url_for('book_show'))


@app.route('/add-match', methods=['POST'])
@require_login
@require_game
def add_match():
    game_state = get_game_state()
    promotion = game_state.promotion

    match_type = request.form.get('match_type', 'Singles')
    info = get_match_type_info().get(match_type, get_match_type_info()["Singles"])

    num_participants = int(request.form.get('num_participants', info.get('min', 2)))
    num_participants = max(info.get('min', 2), min(num_participants, info.get('max', 2)))

    match_data = {
        'match_type': match_type,
        'num_participants': num_participants,
        'match_time': request.form.get('match_time', 'Standard'),
        'is_title_match': request.form.get('is_title_match') == 'on',
        'championship_name': request.form.get('championship_name', ''),
        'notes': request.form.get('notes', ''),
    }

    for i in range(1, num_participants + 1):
        match_data[f'wrestler{i}'] = request.form.get(f'wrestler{i}', '')

    participants = [
        match_data.get(f'wrestler{i}', '')
        for i in range(1, num_participants + 1)
        if match_data.get(f'wrestler{i}', '')
    ]

    if len(participants) < info.get('min', 2):
        flash(f'{match_type} needs at least {info.get("min", 2)} participants.', 'error')
        return redirect(url_for('book_show', match_type=match_type))

    if len(set(participants)) != len(participants):
        flash('A wrestler cannot be selected twice in the same match.', 'error')
        return redirect(url_for('book_show', match_type=match_type))

    roster_names = {w.name for w in promotion.roster}
    invalid = [p for p in participants if p not in roster_names]

    if invalid:
        flash(f'Invalid wrestlers: {", ".join(invalid)}', 'error')
        return redirect(url_for('book_show', match_type=match_type))

    match_data['display'] = get_display_for_match(match_data)

    current_card = session.get('current_card', [])
    current_card.append(match_data)
    session['current_card'] = current_card

    flash(f'Match added: {match_data["display"]}', 'success')
    return redirect(url_for('book_show'))


@app.route('/remove-match/<int:index>', methods=['POST'])
@require_login
@require_game
def remove_match(index):
    current_card = session.get('current_card', [])

    if 0 <= index < len(current_card):
        removed = current_card.pop(index)
        session['current_card'] = current_card
        flash(f'Removed: {removed.get("display", "Match")}', 'info')

    return redirect(url_for('book_show'))


@app.route('/clear-card', methods=['POST'])
@require_login
@require_game
def clear_card():
    session['current_card'] = []
    flash('Match card cleared.', 'info')
    return redirect(url_for('book_show'))


@app.route('/book-current-show', methods=['POST'])
@require_login
@require_game
def book_current_show():
    game_state = get_game_state()

    venue_id = session.get('current_venue_id')
    current_card = session.get('current_card', [])
    show_date = session.get('show_date')
    production = session.get('show_production', {})

    if not venue_id:
        flash('Select a venue before booking the show.', 'error')
        return redirect(url_for('book_show'))

    if not current_card:
        flash('Add at least one match before booking the show.', 'error')
        return redirect(url_for('book_show'))

    venue = get_venue_by_id(venue_id)
    if not venue:
        flash('Selected venue could not be found.', 'error')
        return redirect(url_for('book_show'))

    if not show_date:
        show_date = {
            'year': game_state.promotion.current_year,
            'month': game_state.promotion.current_month,
            'day': game_state.promotion.current_day,
        }

    game_state.booked_show = {
        'venue_id': venue_id,
        'venue_name': venue.name,
        'show_date': show_date,
        'card': current_card,
        'production': production,
    }

    save_game_state(game_state)

    flash('Show booked successfully!', 'success')
    return redirect(url_for('booking_room'))


@app.route('/cancel-booked-show', methods=['POST'])
@require_login
@require_game
def cancel_booked_show():
    game_state = get_game_state()
    game_state.booked_show = None
    save_game_state(game_state)
    flash('Booked show cancelled.', 'info')
    return redirect(url_for('booking_room'))


@app.route('/run-show', methods=['POST'])
@require_login
@require_game
def run_show():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    booked_show = getattr(game_state, 'booked_show', None)

    if booked_show:
        venue_id = booked_show.get('venue_id')
        card = booked_show.get('card', [])
        show_date = booked_show.get('show_date', {
            'year': promotion.current_year,
            'month': promotion.current_month,
            'day': promotion.current_day,
        })
        production = booked_show.get('production', {})
    else:
        venue_id = session.get('current_venue_id')
        card = session.get('current_card', [])
        show_date = session.get('show_date', {
            'year': promotion.current_year,
            'month': promotion.current_month,
            'day': promotion.current_day,
        })
        production = session.get('show_production', {})

    if not venue_id:
        flash('No venue selected!', 'error')
        return redirect(url_for('book_show'))

    if not card:
        flash('You need at least one match on the card!', 'error')
        return redirect(url_for('book_show'))

    venue = get_venue_by_id(venue_id)
    if not venue:
        flash('Venue not found!', 'error')
        return redirect(url_for('book_show'))

    production_cost = 0
    production_rating_bonus = 0
    production_attendance_bonus = 0

    for option_id in production.values():
        option = ALL_PRODUCTION_OPTIONS.get(option_id)
        if option:
            production_cost += option.cost
            production_rating_bonus += getattr(option, 'rating_bonus', 0)
            production_attendance_bonus += getattr(option, 'attendance_bonus', 0)

    match_engine = MatchEngine()
    results = []
    total_rating = 0

    roster_lookup = {w.name: w for w in promotion.roster}

    for match in card:
        participants = []

        for i in range(1, int(match.get('num_participants', 2)) + 1):
            name = match.get(f'wrestler{i}')
            if name and name in roster_lookup:
                participants.append(roster_lookup[name])

        if len(participants) < 2:
            continue

        time_option = match.get('match_time', 'Standard')
        time_modifier = get_time_quality_modifier(time_option)

        try:
            result = match_engine.simulate_match(
                participants=participants,
                match_type=match.get('match_type', 'Singles'),
                promotion=promotion,
            )
        except TypeError:
            result = match_engine.simulate_match(
                participants,
                match.get('match_type', 'Singles'),
                promotion,
            )
        except Exception:
            result = {
                "rating": round(random.uniform(1.5, 4.0), 2),
                "winner": random.choice(participants).name,
                "finish": "Pinfall",
            }

        rating = float(result.get('rating', random.uniform(1.5, 4.0)))
        rating = max(0.5, min(5.0, rating + time_modifier + production_rating_bonus))

        result['rating'] = rating
        result['display'] = match.get('display', get_display_for_match(match))
        result['match_type'] = match.get('match_type', 'Singles')
        result['match_time'] = time_option
        result['all_participants'] = [w.name for w in participants]
        result['is_title_match'] = match.get('is_title_match', False)
        result['championship_name'] = match.get('championship_name', '')

        results.append(result)
        total_rating += rating

        for wrestler in participants:
            try:
                if hasattr(wrestler, 'matches_worked'):
                    wrestler.matches_worked += 1
                if hasattr(wrestler, 'adjust_morale'):
                    wrestler.adjust_morale(1)
            except Exception:
                pass

    if not results:
        flash('No valid matches could be run.', 'error')
        return redirect(url_for('book_show'))

    avg_rating = total_rating / len(results)

    card_total_time = get_card_total_time(card)
    overrun_penalty = calculate_overrun_penalty(card_total_time, venue)
    avg_rating = max(0.5, min(5.0, avg_rating - overrun_penalty))

    base_attendance = int(venue.capacity * random.uniform(0.35, 0.85))
    fan_modifier = min(2.0, max(0.25, promotion.fan_base / max(venue.capacity, 1)))
    prestige_modifier = 1 + (getattr(promotion, 'prestige', 0) / 200)
    rating_modifier = 0.75 + (avg_rating / 5)

    attendance = int(base_attendance * fan_modifier * prestige_modifier * rating_modifier)
    attendance = int(attendance * (1 + production_attendance_bonus))
    attendance = max(0, min(attendance, venue.capacity))

    is_sellout = attendance >= venue.capacity

    ticket_price = getattr(venue, 'ticket_price', 10)
    ticket_revenue = int(attendance * ticket_price)
    merch_revenue = int(attendance * 5 * getattr(promotion, 'merchandise_modifier', 1.0))
    venue_cost = getattr(venue, 'cost', getattr(venue, 'rental_cost', 0))

    wrestler_cost = 0
    used_wrestlers = set()
    for match in card:
        for i in range(1, int(match.get('num_participants', 2)) + 1):
            name = match.get(f'wrestler{i}')
            if name and name in roster_lookup and name not in used_wrestlers:
                used_wrestlers.add(name)
                wrestler = roster_lookup[name]
                wrestler_cost += getattr(wrestler, 'booking_fee', getattr(wrestler, 'salary', 0))

    total_cost = venue_cost + production_cost + wrestler_cost
    revenue = ticket_revenue + merch_revenue
    profit = revenue - total_cost

    promotion.budget += profit

    fan_gain = int((avg_rating * 20) + (attendance / 50))
    if is_sellout:
        fan_gain += int(venue.capacity * 0.05)

    promotion.fan_base += max(0, fan_gain)
    promotion.prestige = min(100, getattr(promotion, 'prestige', 0) + (avg_rating * 0.1))

    xp_gain = int((avg_rating * 100) + (attendance / 10))
    if progression:
        try:
            progression.add_xp(xp_gain, "Show completed")
        except Exception:
            pass

    if hasattr(game_state, 'championship_manager') and game_state.championship_manager:
        for result in results:
            if result.get('is_title_match') and result.get('championship_name'):
                try:
                    winner = result.get('winner')
                    game_state.championship_manager.change_champion(
                        result.get('championship_name'),
                        winner,
                        week=getattr(promotion, 'current_week', 0),
                        year=getattr(promotion, 'current_year', 1),
                    )
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

    if hasattr(game_state, 'injury_manager') and game_state.injury_manager:
        try:
            for result in results:
                for wrestler_name in result.get('all_participants', []):
                    wrestler = roster_lookup.get(wrestler_name)
                    if wrestler:
                        game_state.injury_manager.check_match_injury(wrestler, result.get('match_type', 'Singles'))
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

    # Rival Scheduler - scripted CPU rival intro and future rival calendar
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
                },
            )
    except Exception as e:
        print(f"Rival Scheduler error: {e}")

    try:
        promotion.current_year = show_date.get('year', promotion.current_year)
        promotion.current_month = show_date.get('month', promotion.current_month)
        promotion.current_day = show_date.get('day', promotion.current_day)
    except Exception:
        pass

    game_state.booked_show = None
    session['current_card'] = []
    session['current_venue_id'] = None
    session['show_production'] = {}
    session['show_date'] = None

    save_game_state(game_state)

    return render_template(
        'show_results.html',
        promotion=promotion,
        venue=venue,
        results=results,
        avg_rating=avg_rating,
        attendance=attendance,
        is_sellout=is_sellout,
        ticket_revenue=ticket_revenue,
        merch_revenue=merch_revenue,
        revenue=revenue,
        venue_cost=venue_cost,
        wrestler_cost=wrestler_cost,
        production_cost=production_cost,
        total_cost=total_cost,
        profit=profit,
        fan_gain=fan_gain,
        xp_gain=xp_gain,
        show_date=show_date,
        currency=getattr(game_state, 'game_settings', {}).get("currency_symbol", "$"),
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
        pulse_result, total_salaries = process_week_advancement(game_state)
    except Exception as e:
        print(f"Weekly advancement error: {e}")
        pulse_result, total_salaries = {}, 0

    try:
        rival_scheduler = ensure_rival_scheduler(game_state)
        if rival_scheduler:
            rival_scheduler.complete_due_rival_shows(game_state)
    except Exception as e:
        print(f"Rival due show error: {e}")

    save_game_state(game_state)
    flash('Advanced one week.', 'success')
    return redirect(url_for('dashboard'))


# ==================== EVENTS ====================
@app.route('/events')
@require_login
@require_game
def events():
    game_state = get_game_state()
    active_events = []

    if game_state.ai_director:
        try:
            active_events = game_state.ai_director.get_active_events()
        except Exception:
            active_events = []

    return render_template(
        'events.html',
        promotion=game_state.promotion,
        events=active_events,
        hide_base_hud=True,
    )


@app.route('/resolve-event/<event_id>', methods=['POST'])
@require_login
@require_game
def resolve_event(event_id):
    game_state = get_game_state()

    if game_state.ai_director:
        try:
            game_state.ai_director.resolve_event(event_id)
            flash('Event resolved.', 'success')
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
        promotion=game_state.promotion,
        championships=championships_list,
        championship_costs=CHAMPIONSHIP_COSTS,
        slot_costs=SLOT_COSTS,
        limits=limits,
        currency=currency,
        hide_base_hud=True,
    )


@app.route('/create-championship', methods=['GET', 'POST'])
@require_login
@require_game
def create_championship():
    game_state = get_game_state()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        level = request.form.get('level', ChampionshipLevel.WORLD.value)
        gender = request.form.get('gender', ChampionshipGender.ANY.value)
        rules = request.form.get('rules', ChampionshipRule.SINGLES.value)

        try:
            level_enum = ChampionshipLevel(level)
        except Exception:
            level_enum = ChampionshipLevel.WORLD

        try:
            gender_enum = ChampionshipGender(gender)
        except Exception:
            gender_enum = ChampionshipGender.ANY

        try:
            rules_enum = ChampionshipRule(rules)
        except Exception:
            rules_enum = ChampionshipRule.SINGLES

        cost = CHAMPIONSHIP_COSTS.get(level_enum, 0)

        if game_state.promotion.budget < cost:
            flash('Not enough money to create this championship.', 'error')
            return redirect(url_for('championships'))

        try:
            champ = Championship(
                name=name,
                level=level_enum,
                gender=gender_enum,
                rules=rules_enum,
            )
            game_state.championship_manager.championships.append(champ)
            game_state.promotion.budget -= cost
            save_game_state(game_state)
            flash(f'{name} created!', 'success')
        except Exception as e:
            flash(f'Could not create championship: {e}', 'error')

        return redirect(url_for('championships'))

    return redirect(url_for('championships'))


@app.route('/vacate-championship/<path:championship_name>', methods=['POST'])
@require_login
@require_game
def vacate_championship(championship_name):
    game_state = get_game_state()

    try:
        for champ in game_state.championship_manager.championships:
            if champ.name == championship_name:
                champ.vacate("Vacated by promoter")
                flash(f'{championship_name} vacated.', 'info')
                break
    except Exception:
        flash('Could not vacate championship.', 'error')

    save_game_state(game_state)
    return redirect(url_for('championships'))


# ==================== CAREER ====================
@app.route('/career')
@require_login
@require_game
def career():
    game_state = get_game_state()
    promotion = game_state.promotion
    progression = game_state.progression

    if progression:
        level, xp_into, xp_needed, percentage = get_xp_progress(progression.total_xp)
        tier_name = get_tier_name(get_promotion_tier(level))
        earned_achievements = progression.get_earned_achievements() if hasattr(progression, 'get_earned_achievements') else []
        stats = progression.stats if hasattr(progression, 'stats') else {}
        total_achievements = len(progression.achievements) if hasattr(progression, 'achievements') else 0
    else:
        level, percentage, tier_name = 1, 0, "Backyard"
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

    if not hasattr(game_state, 'calls') or game_state.calls is None:
        game_state.calls = CallsManager()
        save_game_state(game_state)

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

    if hasattr(game_state, 'banking') and game_state.banking:
        try:
            can_take_shark, shark_reason = game_state.banking.can_take_loan(LoanType.LOAN_SHARK)
            active_shark_loans = game_state.banking.get_active_shark_loans() if hasattr(game_state.banking, 'get_active_shark_loans') else []
        except Exception:
            pass

    return render_template(
        'calls.html',
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


@app.route('/calls/answer/<path:call_id>', methods=['POST'])
@require_login
@require_game
def answer_call(call_id):
    game_state = get_game_state()

    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            game_state.calls.answer_call(call_id)
            save_game_state(game_state)
            flash('Call answered.', 'success')
        except Exception as e:
            flash(f'Could not answer call: {e}', 'error')

    return redirect(url_for('calls_app'))


@app.route('/calls/decline/<path:call_id>', methods=['POST'])
@require_login
@require_game
def decline_call(call_id):
    game_state = get_game_state()

    if hasattr(game_state, 'calls') and game_state.calls:
        try:
            game_state.calls.decline_call(call_id)
            save_game_state(game_state)
            flash('Call declined.', 'info')
        except Exception as e:
            flash(f'Could not decline call: {e}', 'error')

    return redirect(url_for('calls_app'))


# ==================== BANKING ====================
@app.route('/banking')
@require_login
@require_game
def banking():
    game_state = get_game_state()

    if not hasattr(game_state, 'banking') or game_state.banking is None:
        game_state.banking = BankingManager()
        save_game_state(game_state)

    bank_loans = BANK_LOAN_OPTIONS
    shark_loans = SHARK_LOAN_OPTIONS
    active_loans = []

    try:
        active_loans = game_state.banking.get_active_loans()
    except Exception:
        active_loans = getattr(game_state.banking, 'active_loans', [])

    currency = getattr(game_state, 'game_settings', {}).get("currency_symbol", "$")

    return render_template(
        'banking.html',
        promotion=game_state.promotion,
        banking=game_state.banking,
        bank_loans=bank_loans,
        shark_loans=shark_loans,
        active_loans=active_loans,
        currency=currency,
        hide_base_hud=True,
    )


@app.route('/take-loan/<loan_type>/<loan_id>', methods=['POST'])
@require_login
@require_game
def take_loan(loan_type, loan_id):
    game_state = get_game_state()

    if not hasattr(game_state, 'banking') or game_state.banking is None:
        game_state.banking = BankingManager()

    try:
        loan_type_enum = LoanType(loan_type)
    except Exception:
        loan_type_enum = LoanType.BANK

    try:
        success, msg, amount = game_state.banking.take_loan(
            loan_type_enum,
            loan_id,
            game_state.promotion.budget,
        )

        if success:
            game_state.promotion.budget += amount
            save_game_state(game_state)
            flash(msg, 'success')
        else:
            flash(msg, 'error')
    except Exception as e:
        flash(f'Loan error: {e}', 'error')

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
        'injuries.html',
        promotion=game_state.promotion,
        injured_wrestlers=injured,
        injury_manager=game_state.injury_manager,
        hide_base_hud=True,
    )


# ==================== WRITERS ROOM ====================
@app.route('/writers-room')
@require_login
@require_game
def writers_room():
    game_state = get_game_state()

    active_storylines = []
    pitched_storylines = []
    concluded_storylines = []
    booking_suggestions = []
    available_wrestlers = game_state.promotion.roster
    my_writers = []
    available_writers = []
    available_freelancers = []
    marketplace_storylines = []
    max_writers = 0
    total_writer_payroll = 0
    ai_info = None

    try:
        if hasattr(game_state, 'storyline_engine') and game_state.storyline_engine:
            active_storylines = getattr(game_state.storyline_engine, 'active_storylines', [])
            pitched_storylines = getattr(game_state.storyline_engine, 'pitched_storylines', [])
            concluded_storylines = getattr(game_state.storyline_engine, 'concluded_storylines', [])
    except Exception:
        pass

    try:
        if game_state.ai_director:
            ai_info = game_state.get_ai_director_info()
    except Exception:
        pass

    return render_template(
        'writers_room.html',
        promotion=game_state.promotion,
        active_storylines=active_storylines,
        pitched_storylines=pitched_storylines,
        concluded_storylines=concluded_storylines,
        booking_suggestions=booking_suggestions,
        ai_info=ai_info,
        available_wrestlers=available_wrestlers,
        my_writers=my_writers,
        available_writers=available_writers,
        available_freelancers=available_freelancers,
        marketplace_storylines=marketplace_storylines,
        max_writers=max_writers,
        total_writer_payroll=total_writer_payroll,
        active_count=len(active_storylines),
        pitched_count=len(pitched_storylines),
        hide_base_hud=True,
    )


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
            if hasattr(game_state.storyline_engine, 'approve_storyline'):
                game_state.storyline_engine.approve_storyline(storyline_id)
                save_game_state(game_state)
                flash('Storyline approved!', 'success')
        except Exception as e:
            flash(f'Could not approve: {e}', 'error')

    return redirect(url_for('writers_room'))


@app.route('/reject-storyline/<path:storyline_id>', methods=['POST'])
@require_login
@require_game
def reject_storyline(storyline_id):
    game_state = get_game_state()

    if hasattr(game_state, 'storyline_engine') and game_state.storyline_engine:
        try:
            if hasattr(game_state.storyline_engine, 'reject_storyline'):
                game_state.storyline_engine.reject_storyline(storyline_id)
                save_game_state(game_state)
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
    flash('Writer management coming soon!', 'info')
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
        school = TrainingSchool()
        game_state.training_school = school
        save_game_state(game_state)

    return render_template(
        'training_school.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary() if hasattr(school, 'get_summary') else {},
        hide_base_hud=True,
    )


@app.route('/found-school', methods=['GET', 'POST'])
@require_login
@require_game
def found_school():
    game_state = get_game_state()
    school = game_state.training_school

    if not school:
        school = TrainingSchool()
        game_state.training_school = school

    if request.method == 'POST':
        name = request.form.get('name', 'Training School')
        tier_value = request.form.get('tier', SchoolTier.SCHOOL_GYM.value)

        try:
            tier = SchoolTier(tier_value)
        except Exception:
            tier = SchoolTier.SCHOOL_GYM

        try:
            school.found_school(
                name=name,
                location=game_state.promotion.location,
                tier=tier,
                week=getattr(game_state.promotion, 'current_week', 0),
                year=getattr(game_state.promotion, 'current_year', 1),
            )
            save_game_state(game_state)
            flash('Training school founded!', 'success')
        except Exception as e:
            flash(f'Could not found school: {e}', 'error')

        return redirect(url_for('training_school'))

    return render_template(
        'found_school.html',
        promotion=game_state.promotion,
        school=school,
        school_tiers=SchoolTier,
        school_tier_info=SCHOOL_TIER_INFO,
        hide_base_hud=True,
    )


@app.route('/school-settings')
@require_login
@require_game
def school_settings():
    game_state = get_game_state()

    return render_template(
        'school_settings.html',
        promotion=game_state.promotion,
        school=game_state.training_school,
        hide_base_hud=True,
    )


@app.route('/shutdown-school', methods=['POST'])
@require_login
@require_game
def shutdown_school():
    flash('School shutdown coming soon.', 'info')
    return redirect(url_for('school_settings'))


@app.route('/trainees')
@require_login
@require_game
def trainees():
    game_state = get_game_state()
    school = game_state.training_school

    trainees_list = []
    if school:
        try:
            trainees_list = school.get_all_trainees()
        except Exception:
            trainees_list = getattr(school, 'trainees', [])

    return render_template(
        'trainees.html',
        promotion=game_state.promotion,
        school=school,
        trainees=trainees_list,
        hide_base_hud=True,
    )


@app.route('/trainee/<path:trainee_id>')
@require_login
@require_game
def trainee_profile(trainee_id):
    game_state = get_game_state()
    school = game_state.training_school

    trainee = None
    if school:
        try:
            trainee = school.get_trainee(trainee_id)
        except Exception:
            trainee = next(
                (t for t in getattr(school, 'trainees', []) if getattr(t, 'id', getattr(t, 'name', '')) == trainee_id),
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
        hide_base_hud=True,
    )


@app.route('/scout-trainees', methods=['GET', 'POST'])
@require_login
@require_game
def scout_trainees():
    game_state = get_game_state()

    if not game_state.trainee_pool:
        game_state.trainee_pool = TraineePool()

    prospects = []

    try:
        if hasattr(game_state.trainee_pool, 'get_available_prospects'):
            prospects = game_state.trainee_pool.get_available_prospects()
    except Exception:
        prospects = []

    return render_template(
        'scout_trainees.html',
        promotion=game_state.promotion,
        school=game_state.training_school,
        prospects=prospects,
        hide_base_hud=True,
    )


@app.route('/enroll-trainee/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def enroll_trainee(trainee_id):
    game_state = get_game_state()
    school = game_state.training_school

    if not school:
        flash('You need a training school first.', 'error')
        return redirect(url_for('training_school'))

    try:
        trainee = None

        if game_state.trainee_pool and hasattr(game_state.trainee_pool, 'get_prospect'):
            trainee = game_state.trainee_pool.get_prospect(trainee_id)

        if trainee and hasattr(school, 'enroll_trainee'):
            school.enroll_trainee(trainee)
            save_game_state(game_state)
            flash(f'{getattr(trainee, "name", "Trainee")} enrolled!', 'success')
        else:
            flash('Trainee enrollment coming soon.', 'info')
    except Exception as e:
        flash(f'Could not enroll trainee: {e}', 'error')

    return redirect(url_for('trainees'))


@app.route('/roster-training')
@require_login
@require_game
def roster_training():
    game_state = get_game_state()

    return render_template(
        'roster_training.html',
        promotion=game_state.promotion,
        school=game_state.training_school,
        wrestlers=game_state.promotion.roster,
        active_enrollments=getattr(game_state, 'active_enrollments', []),
        class_catalog=get_full_catalog_for_ui(),
        hide_base_hud=True,
    )


@app.route('/enroll-wrestler', methods=['POST'])
@require_login
@require_game
def enroll_wrestler():
    flash('Roster class enrollment coming soon.', 'info')
    return redirect(url_for('roster_training'))


@app.route('/enroll-trainee-in-class/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def enroll_trainee_in_class(trainee_id):
    flash('Trainee class enrollment coming soon.', 'info')
    return redirect(url_for('trainee_profile', trainee_id=trainee_id))


@app.route('/cancel-enrollment/<path:enrollment_id>', methods=['POST'])
@require_login
@require_game
def cancel_enrollment(enrollment_id):
    game_state = get_game_state()
    enrollments = getattr(game_state, 'active_enrollments', [])

    for enrollment in enrollments:
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

    if not game_state.coach_manager:
        game_state.coach_manager = CoachManager()

    available_coaches = []
    hired_coaches = []

    try:
        hired_coaches = game_state.coach_manager.get_hired_coaches()
    except Exception:
        hired_coaches = getattr(game_state.coach_manager, 'coaches', [])

    try:
        if game_state.coach_pool and hasattr(game_state.coach_pool, 'get_available_coaches'):
            available_coaches = game_state.coach_pool.get_available_coaches()
    except Exception:
        available_coaches = []

    return render_template(
        'coaches.html',
        promotion=game_state.promotion,
        school=game_state.training_school,
        coach_manager=game_state.coach_manager,
        hired_coaches=hired_coaches,
        available_coaches=available_coaches,
        hide_base_hud=True,
    )


@app.route('/hire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def hire_coach(coach_id):
    flash('Coach hiring coming soon.', 'info')
    return redirect(url_for('coaches'))


@app.route('/fire-coach/<path:coach_id>', methods=['POST'])
@require_login
@require_game
def fire_coach(coach_id):
    flash('Coach firing coming soon.', 'info')
    return redirect(url_for('coaches'))


@app.route('/assign-trainee-coach/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def assign_trainee_coach(trainee_id):
    flash('Coach assignment coming soon.', 'info')
    return redirect(url_for('trainee_profile', trainee_id=trainee_id))


@app.route('/choose-trainee-specialization/<path:trainee_id>', methods=['POST'])
@require_login
@require_game
def choose_trainee_specialization(trainee_id):
    flash('Trainee specialization coming soon.', 'info')
    return redirect(url_for('trainee_profile', trainee_id=trainee_id))


@app.route('/trainee-show')
@require_login
@require_game
def trainee_show():
    game_state = get_game_state()
    school = game_state.training_school

    if not game_state.trainee_show_manager:
        game_state.trainee_show_manager = TraineeShowManager()

    scheduled_shows = []
    completed_shows = []
    lifetime_stats = {}
    show_type_options = list(TraineeShowType)
    active_trainees = []

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
        active_trainees = school.get_active_trainees() if school else []
    except Exception:
        active_trainees = []

    return render_template(
        'trainee_show.html',
        promotion=game_state.promotion,
        school=school,
        school_summary=school.get_summary() if school and hasattr(school, 'get_summary') else {},
        scheduled_shows=scheduled_shows,
        completed_shows=completed_shows,
        lifetime_stats=lifetime_stats,
        show_type_options=show_type_options,
        active_trainee_count=len(active_trainees),
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
    flash('Running trainee shows coming soon.', 'info')
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
