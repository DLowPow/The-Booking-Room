"""
AI Voice System - Personality-driven text generation
Generates context-aware dialogue for messages, commentary, news, and calls
Each personality produces unique voice across all game channels
"""

import random
from typing import Dict, List, Optional, Tuple
from ai.personality import (
    PersonalityManager, PersonalityType, MoodState,
    PERSONALITIES
)


class VoiceContext:
    """Context object passed to voice generation for variable substitution"""

    def __init__(self, **kwargs):
        self.wrestler1 = kwargs.get("wrestler1", "")
        self.wrestler2 = kwargs.get("wrestler2", "")
        self.champion = kwargs.get("champion", "")
        self.challenger = kwargs.get("challenger", "")
        self.title = kwargs.get("title", "")
        self.show_name = kwargs.get("show_name", "")
        self.venue = kwargs.get("venue", "")
        self.rating = kwargs.get("rating", 0.0)
        self.attendance = kwargs.get("attendance", 0)
        self.event = kwargs.get("event", "")
        self.match_type = kwargs.get("match_type", "")
        self.winner = kwargs.get("winner", "")
        self.loser = kwargs.get("loser", "")
        self.finish = kwargs.get("finish", "")
        self.weeks = kwargs.get("weeks", 0)
        self.money = kwargs.get("money", 0)
        self.fans = kwargs.get("fans", 0)
        self.extra = kwargs.get("extra", {})

    def to_dict(self) -> Dict:
        return {
            "wrestler1": self.wrestler1,
            "wrestler2": self.wrestler2,
            "champion": self.champion,
            "challenger": self.challenger,
            "title": self.title,
            "show_name": self.show_name,
            "venue": self.venue,
            "rating": self.rating,
            "attendance": self.attendance,
            "event": self.event,
            "match_type": self.match_type,
            "winner": self.winner,
            "loser": self.loser,
            "finish": self.finish,
            "weeks": self.weeks,
            "money": self.money,
            "fans": self.fans,
        }


# ==================== UNIVERSAL TEMPLATES ====================
# These are shared across all personalities but get tinted by mood

SHOW_RECAP_TEMPLATES = {
    "great_show": [
        "What a night at {venue}! {attendance:,} fans witnessed something special.",
        "The crowd at {venue} was electric! Average rating: {rating:.1f}⭐",
        "{venue} delivered tonight. {attendance:,} fans, {rating:.1f}⭐ average. That's how you do it.",
    ],
    "good_show": [
        "Solid night at {venue}. {attendance:,} fans saw some good wrestling.",
        "{venue} put on a decent show. {rating:.1f}⭐ average — room to grow.",
        "Not bad at {venue}. {attendance:,} in the building, respectable numbers.",
    ],
    "bad_show": [
        "Rough night at {venue}. {rating:.1f}⭐ average — we need to do better.",
        "The {venue} crowd wasn't feeling it tonight. {attendance:,} showed up but left disappointed.",
        "Below average at {venue}. {rating:.1f}⭐ — the booking needs work.",
    ],
    "terrible_show": [
        "Disaster at {venue}. {rating:.1f}⭐ average. Heads need to roll.",
        "I've seen better shows in a car park. {venue} was embarrassing tonight.",
        "{attendance:,} fans at {venue} and we gave them THAT? Unacceptable.",
    ],
}

INJURY_TEMPLATES = [
    "{wrestler1} has been injured! Diagnosis: {event}. Recovery: {weeks} weeks.",
    "BAD NEWS: {wrestler1} went down during the show. {event}. Out {weeks} weeks.",
    "Medical update: {wrestler1} suffered a {event}. Expected to miss {weeks} weeks.",
    "Injury report: {wrestler1} — {event}. Timeline: {weeks} weeks recovery.",
]

SIGNING_TEMPLATES = [
    "Welcome to the roster! {wrestler1} has officially signed!",
    "{wrestler1} is ALL IN! New signing confirmed.",
    "BREAKING: {wrestler1} has joined the promotion!",
    "The roster just got stronger — {wrestler1} is signed!",
]

TITLE_CHANGE_TEMPLATES = [
    "NEW CHAMPION! {winner} defeats {loser} to win the {title}!",
    "TITLE CHANGE! {winner} is the NEW {title}!",
    "History made! {winner} captures the {title} from {loser}!",
    "AND NEW! {winner} is your {title} after defeating {loser}!",
]

TITLE_DEFENSE_TEMPLATES = [
    "{champion} retains the {title} against {challenger}!",
    "The {title} stays with {champion}! Successful defense against {challenger}.",
    "{champion} proves why they're champion — {title} retained!",
]

CONTRACT_WARNING_TEMPLATES = [
    "⚠️ {wrestler1}'s contract expires in {weeks} weeks!",
    "CONTRACT ALERT: {wrestler1} is approaching free agency ({weeks} weeks remaining).",
    "Heads up — {wrestler1} will be a free agent in {weeks} weeks unless renewed.",
]

FINANCIAL_WARNING_TEMPLATES = [
    "⚠️ Budget is critically low! Only ${money:,} remaining.",
    "FINANCIAL WARNING: We're running out of money. ${money:,} left.",
    "The accountant is panicking. ${money:,} in the bank. Cut costs NOW.",
]

MILESTONE_TEMPLATES = [
    "🎉 MILESTONE: {event}!",
    "We just hit a huge milestone — {event}!",
    "History! {event}. The hard work is paying off.",
]

FAN_GROWTH_TEMPLATES = [
    "📈 Fan base growing! Now at {fans:,} fans.",
    "The people are talking — {fans:,} fans and counting!",
    "Momentum is building. {fans:,} fans behind us now.",
]

WEEKLY_SUMMARY_PARTS = {
    "opening": [
        "Weekly Update — Here's what happened this week.",
        "End of week report. Here's the rundown.",
        "This week in wrestling — your summary.",
    ],
    "salary": [
        "Salaries paid: ${money:,}",
        "Roster payroll this week: ${money:,}",
        "Weekly wages: ${money:,} deducted",
    ],
    "loan": [
        "Loan payment processed: ${money:,}",
        "Debt repayment: ${money:,} this week",
    ],
}


class VoiceEngine:
    """Generates text with personality flavour and context substitution"""

    def __init__(self, personality_manager: PersonalityManager):
        self.pm = personality_manager

    def generate(self, template_list: List[str], context: VoiceContext = None, count: int = 1) -> List[str]:
        """Pick random templates and fill with context variables"""
        if not template_list:
            return [""]

        results = []
        for _ in range(count):
            template = random.choice(template_list)
            if context:
                try:
                    text = template.format(**context.to_dict())
                except (KeyError, IndexError, ValueError):
                    text = template
            else:
                text = template
            results.append(text)

        return results

    def generate_one(self, template_list: List[str], context: VoiceContext = None) -> str:
        """Generate a single line from templates"""
        lines = self.generate(template_list, context, 1)
        return lines[0] if lines else ""

    # ==================== SHOW RECAPS ====================

    def generate_show_recap(self, avg_rating: float, attendance: int, venue: str, profit: int) -> str:
        """Generate a show recap message with personality tint"""
        ctx = VoiceContext(
            rating=avg_rating, attendance=attendance,
            venue=venue, money=profit,
        )

        if avg_rating >= 4.0:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["great_show"], ctx)
            personality_line = self.pm.get_show_reaction(avg_rating)
        elif avg_rating >= 3.0:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["good_show"], ctx)
            personality_line = self.pm.get_show_reaction(avg_rating)
        elif avg_rating >= 2.0:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["bad_show"], ctx)
            personality_line = self.pm.get_show_reaction(avg_rating)
        else:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["terrible_show"], ctx)
            personality_line = self.pm.get_show_reaction(avg_rating)

        profit_line = f"\n\n💰 Profit: ${profit:,}" if profit >= 0 else f"\n\n💸 Loss: ${abs(profit):,}"

        return f"{base}\n\n{personality_line}{profit_line}"

    # ==================== INJURY MESSAGES ====================

    def generate_injury_message(self, wrestler_name: str, injury_type: str, weeks: int) -> str:
        ctx = VoiceContext(wrestler1=wrestler_name, event=injury_type, weeks=weeks)
        return self.generate_one(INJURY_TEMPLATES, ctx)

    # ==================== SIGNING MESSAGES ====================

    def generate_signing_message(self, wrestler_name: str) -> str:
        ctx = VoiceContext(wrestler1=wrestler_name)
        return self.generate_one(SIGNING_TEMPLATES, ctx)

    # ==================== TITLE MESSAGES ====================

    def generate_title_change_message(self, winner: str, loser: str, title: str) -> str:
        ctx = VoiceContext(winner=winner, loser=loser, title=title)
        return self.generate_one(TITLE_CHANGE_TEMPLATES, ctx)

    def generate_title_defense_message(self, champion: str, challenger: str, title: str) -> str:
        ctx = VoiceContext(champion=champion, challenger=challenger, title=title)
        return self.generate_one(TITLE_DEFENSE_TEMPLATES, ctx)

    # ==================== CONTRACT WARNINGS ====================

    def generate_contract_warning(self, wrestler_name: str, weeks_remaining: int) -> str:
        ctx = VoiceContext(wrestler1=wrestler_name, weeks=weeks_remaining)
        return self.generate_one(CONTRACT_WARNING_TEMPLATES, ctx)

    # ==================== FINANCIAL WARNINGS ====================

    def generate_financial_warning(self, budget: int) -> str:
        ctx = VoiceContext(money=budget)
        return self.generate_one(FINANCIAL_WARNING_TEMPLATES, ctx)

    # ==================== BOOKING SUGGESTIONS ====================

    def generate_booking_suggestion(self, wrestler1: str = "", wrestler2: str = "") -> str:
        """Get a personality-tinted booking suggestion"""
        return self.pm.get_booking_suggestion(wrestler1, wrestler2)

    # ==================== COMMENTARY LINES ====================

    def generate_commentary(self, beat_type: str, context: VoiceContext = None) -> str:
        """Generate commentary for live show mode"""
        base_line = self.pm.get_commentary_line(beat_type)

        if context and base_line:
            try:
                base_line = base_line.format(**context.to_dict())
            except (KeyError, IndexError, ValueError):
                pass

        return base_line

    # ==================== NEWS HEADLINES ====================

    def generate_news_headline(self, event: str = "", show: str = "") -> str:
        return self.pm.get_news_headline(event, show)

    # ==================== WEEKLY SUMMARY ====================

    def generate_weekly_summary(self, salaries: int, loan_payments: int = 0,
                                 injuries: List[str] = None,
                                 contract_warnings: List[str] = None) -> str:
        """Generate a weekly summary message"""
        ctx_salary = VoiceContext(money=salaries)
        ctx_loan = VoiceContext(money=loan_payments)

        parts = []
        parts.append(self.generate_one(WEEKLY_SUMMARY_PARTS["opening"]))
        parts.append(self.generate_one(WEEKLY_SUMMARY_PARTS["salary"], ctx_salary))

        if loan_payments > 0:
            parts.append(self.generate_one(WEEKLY_SUMMARY_PARTS["loan"], ctx_loan))

        if injuries:
            parts.append("\n🏥 Injuries This Week:")
            for inj in injuries:
                parts.append(f"  • {inj}")

        if contract_warnings:
            parts.append("\n📋 Contract Alerts:")
            for warn in contract_warnings:
                parts.append(f"  • {warn}")

        return "\n".join(parts)

    # ==================== MILESTONE MESSAGES ====================

    def generate_milestone_message(self, milestone: str) -> str:
        ctx = VoiceContext(event=milestone)
        return self.generate_one(MILESTONE_TEMPLATES, ctx)

    # ==================== FAN GROWTH ====================

    def generate_fan_update(self, fan_count: int) -> str:
        ctx = VoiceContext(fans=fan_count)
        return self.generate_one(FAN_GROWTH_TEMPLATES, ctx)

    # ==================== PERSONALITY-SPECIFIC GREETINGS ====================

    def get_greeting(self) -> str:
        return self.pm.get_greeting()

    def get_catchphrase(self) -> str:
        return self.pm.get_catchphrase()

    def get_sign_off(self) -> str:
        return self.pm.get_sign_off()

    def get_phone_greeting(self) -> str:
        return self.pm.get_phone_greeting()

    # ==================== MOOD-AWARE GENERATION ====================

    def generate_mood_message(self) -> Optional[str]:
        """Generate a message based on current AI mood (if noteworthy)"""
        mood = self.pm.mood_state

        if mood == MoodState.ECSTATIC:
            return self.pm.get_excitement()
        elif mood == MoodState.FURIOUS:
            return self.pm.get_anger()
        elif mood == MoodState.FRUSTRATED:
            return self.pm.get_criticism()
        elif mood == MoodState.SCHEMING:
            return f"🤔 {self.pm.get_greeting()} I've been thinking about the competition..."
        elif mood == MoodState.DESPERATE:
            return f"😰 {self.pm.get_greeting()} We're in trouble. We need to make changes NOW."

        return None

    # ==================== COMBINED MESSAGE BUILDER ====================

    def build_inbox_message(self, message_type: str, context: VoiceContext = None, **kwargs) -> Dict:
        """Build a complete inbox message with personality voice"""

        if message_type == "show_recap":
            body = self.generate_show_recap(
                kwargs.get("avg_rating", 0),
                kwargs.get("attendance", 0),
                kwargs.get("venue", ""),
                kwargs.get("profit", 0),
            )
            return {
                "sender": self.pm.get_name(),
                "subject": f"Show Report — {kwargs.get('venue', 'Show')}",
                "body": body,
                "icon": "📺",
                "message_type": "show_report",
            }

        elif message_type == "injury":
            body = self.generate_injury_message(
                kwargs.get("wrestler_name", ""),
                kwargs.get("injury_type", ""),
                kwargs.get("weeks", 0),
            )
            return {
                "sender": "Medical Team",
                "subject": f"Injury: {kwargs.get('wrestler_name', '')}",
                "body": body,
                "icon": "🏥",
                "message_type": "injury",
            }

        elif message_type == "title_change":
            body = self.generate_title_change_message(
                kwargs.get("winner", ""),
                kwargs.get("loser", ""),
                kwargs.get("title", ""),
            )
            return {
                "sender": "Championship Committee",
                "subject": f"Title Change: {kwargs.get('title', '')}",
                "body": body,
                "icon": "🏆",
                "message_type": "championship",
            }

        elif message_type == "contract_warning":
            body = self.generate_contract_warning(
                kwargs.get("wrestler_name", ""),
                kwargs.get("weeks", 0),
            )
            return {
                "sender": "Contract Office",
                "subject": f"Contract Alert: {kwargs.get('wrestler_name', '')}",
                "body": body,
                "icon": "📋",
                "message_type": "contract",
            }

        elif message_type == "financial_warning":
            body = self.generate_financial_warning(kwargs.get("budget", 0))
            return {
                "sender": "Accounting",
                "subject": "⚠️ Financial Warning",
                "body": body,
                "icon": "💸",
                "message_type": "financial",
            }

        elif message_type == "booking_suggestion":
            body = self.generate_booking_suggestion(
                kwargs.get("wrestler1", ""),
                kwargs.get("wrestler2", ""),
            )
            greeting = self.get_greeting()
            sign_off = self.get_sign_off()
            return {
                "sender": self.pm.get_name(),
                "subject": "Creative Pitch",
                "body": f"{greeting}\n\n{body}\n\n{sign_off}",
                "icon": self.pm.get_icon(),
                "message_type": "creative",
            }

        elif message_type == "weekly_summary":
            body = self.generate_weekly_summary(
                kwargs.get("salaries", 0),
                kwargs.get("loan_payments", 0),
                kwargs.get("injuries", []),
                kwargs.get("contract_warnings", []),
            )
            return {
                "sender": "Weekly Report",
                "subject": "End of Week Summary",
                "body": body,
                "icon": "📊",
                "message_type": "weekly_summary",
            }

        return {
            "sender": "System",
            "subject": "Notification",
            "body": str(kwargs),
            "icon": "📧",
            "message_type": "general",
        }
