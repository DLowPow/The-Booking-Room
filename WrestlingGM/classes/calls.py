"""
Calls System - Player's phone calls hub
Receives calls from AI Director, Loan Shark, sponsors, agents, wrestlers
All calls can be tinted by AI personality voice
Supports contacts list, missed calls, call history, response options
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ==================== CALL TYPES ====================

class CallType(Enum):
    """Categories for incoming calls"""
    GENERAL = "general"
    AI_DIRECTOR = "ai_director"
    AI_PITCH = "ai_pitch"
    AI_DEMAND = "ai_demand"
    LOAN_SHARK = "loan_shark"
    LOAN_SHARK_THREAT = "loan_shark_threat"
    BANK = "bank"
    SPONSOR = "sponsor"
    AGENT = "agent"
    WRESTLER = "wrestler"
    JOURNALIST = "journalist"
    RIVAL_PROMOTER = "rival_promoter"
    LAWYER = "lawyer"
    VENUE = "venue"
    SCANDAL = "scandal"
    EMERGENCY = "emergency"
    MYSTERIOUS = "mysterious"


class CallStatus(Enum):
    """State of a call"""
    INCOMING = "incoming"      # Just arrived, not yet answered
    ANSWERED = "answered"      # Player accepted and resolved
    DECLINED = "declined"      # Player rejected
    MISSED = "missed"          # Expired without answer
    IN_PROGRESS = "in_progress"  # Currently being viewed


class CallPriority(Enum):
    """Urgency levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ==================== CONTACT DATA ====================

# Default contacts that always exist
DEFAULT_CONTACTS = {
    "loan_shark": {
        "name": "Loan Shark",
        "subtitle": "Tony 'The Wallet' Castellano",
        "icon": "💰",
        "color": "#dc2626",
        "always_available": True,
        "description": "No questions asked, but consequences are brutal.",
    },
    "bank": {
        "name": "Capital Bank",
        "subtitle": "Loan Officer",
        "icon": "🏦",
        "color": "#10b981",
        "always_available": True,
        "description": "Legitimate loans for verified businesses.",
    },
    "ai_director": {
        "name": "AI Director",
        "subtitle": "Your Creative Partner",
        "icon": "🎬",
        "color": "#8b5cf6",
        "always_available": True,
        "description": "Calls when they have ideas or demands.",
    },
}


# ==================== CALL CLASS ====================

@dataclass
class Call:
    """A single phone call (incoming or completed)"""
    id: str
    caller_name: str
    caller_subtitle: str
    subject: str
    body: str
    icon: str = "📞"
    color: str = "#3b82f6"
    call_type: CallType = CallType.GENERAL
    status: CallStatus = CallStatus.INCOMING
    priority: CallPriority = CallPriority.NORMAL

    # Date received
    week: int = 0
    year: int = 1
    day: int = 1
    month: int = 1
    received_at: str = ""

    # Expiry
    expires_in_weeks: int = 2
    weeks_pending: int = 0

    # Response options (player choices)
    options: List[Dict] = field(default_factory=list)
    chosen_option_index: int = -1
    chosen_option_label: str = ""

    # Effects on game state (filled when option chosen)
    applied_effects: Dict = field(default_factory=dict)

    # Rich metadata
    related_wrestler: str = ""
    related_storyline_id: str = ""
    contact_id: str = ""  # Maps to DEFAULT_CONTACTS

    # AI integration
    is_ai_tinted: bool = False
    ai_personality: str = ""

    # ==================== HELPERS ====================

    def is_expired(self) -> bool:
        return self.status == CallStatus.INCOMING and self.weeks_pending >= self.expires_in_weeks

    def get_priority_color(self) -> str:
        colors = {
            CallPriority.LOW: "#6b7280",
            CallPriority.NORMAL: "#3b82f6",
            CallPriority.HIGH: "#f59e0b",
            CallPriority.URGENT: "#ef4444",
        }
        return colors.get(self.priority, "#3b82f6")

    def get_status_color(self) -> str:
        colors = {
            CallStatus.INCOMING: "#3b82f6",
            CallStatus.ANSWERED: "#10b981",
            CallStatus.DECLINED: "#6b7280",
            CallStatus.MISSED: "#ef4444",
            CallStatus.IN_PROGRESS: "#f59e0b",
        }
        return colors.get(self.status, "#6b7280")

    def get_type_icon(self) -> str:
        if self.icon and self.icon != "📞":
            return self.icon
        type_icons = {
            CallType.AI_DIRECTOR: "🎬",
            CallType.AI_PITCH: "💡",
            CallType.AI_DEMAND: "❗",
            CallType.LOAN_SHARK: "💰",
            CallType.LOAN_SHARK_THREAT: "💢",
            CallType.BANK: "🏦",
            CallType.SPONSOR: "🤝",
            CallType.AGENT: "📋",
            CallType.WRESTLER: "🤼",
            CallType.JOURNALIST: "📰",
            CallType.RIVAL_PROMOTER: "⚔️",
            CallType.LAWYER: "⚖️",
            CallType.VENUE: "🏟️",
            CallType.SCANDAL: "🚨",
            CallType.EMERGENCY: "🆘",
            CallType.MYSTERIOUS: "❓",
        }
        return type_icons.get(self.call_type, "📞")

    def get_date_display(self) -> str:
        return f"{self.month}/{self.day}/Y{self.year}"

    def get_preview(self, max_length: int = 80) -> str:
        clean = self.body.replace("\n", " ").strip()
        if len(clean) <= max_length:
            return clean
        return clean[:max_length].rsplit(" ", 1)[0] + "..."

    def get_urgency_text(self) -> str:
        if self.status != CallStatus.INCOMING:
            return ""
        if self.weeks_pending >= self.expires_in_weeks - 1:
            return "🚨 EXPIRES THIS WEEK"
        weeks_left = self.expires_in_weeks - self.weeks_pending
        return f"⏰ {weeks_left} week{'s' if weeks_left != 1 else ''} to respond"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "caller_name": self.caller_name,
            "caller_subtitle": self.caller_subtitle,
            "subject": self.subject,
            "body": self.body,
            "icon": self.icon,
            "color": self.color,
            "call_type": self.call_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "week": self.week,
            "year": self.year,
            "day": self.day,
            "month": self.month,
            "received_at": self.received_at,
            "expires_in_weeks": self.expires_in_weeks,
            "weeks_pending": self.weeks_pending,
            "options": self.options,
            "chosen_option_index": self.chosen_option_index,
            "chosen_option_label": self.chosen_option_label,
            "applied_effects": self.applied_effects,
            "related_wrestler": self.related_wrestler,
            "related_storyline_id": self.related_storyline_id,
            "contact_id": self.contact_id,
            "is_ai_tinted": self.is_ai_tinted,
            "ai_personality": self.ai_personality,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Call":
        try:
            ct = CallType(data.get("call_type", "general"))
        except (ValueError, KeyError):
            ct = CallType.GENERAL

        try:
            st = CallStatus(data.get("status", "incoming"))
        except (ValueError, KeyError):
            st = CallStatus.INCOMING

        try:
            pr = CallPriority(data.get("priority", "normal"))
        except (ValueError, KeyError):
            pr = CallPriority.NORMAL

        return cls(
            id=data.get("id", ""),
            caller_name=data.get("caller_name", "Unknown"),
            caller_subtitle=data.get("caller_subtitle", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            icon=data.get("icon", "📞"),
            color=data.get("color", "#3b82f6"),
            call_type=ct,
            status=st,
            priority=pr,
            week=data.get("week", 0),
            year=data.get("year", 1),
            day=data.get("day", 1),
            month=data.get("month", 1),
            received_at=data.get("received_at", ""),
            expires_in_weeks=data.get("expires_in_weeks", 2),
            weeks_pending=data.get("weeks_pending", 0),
            options=data.get("options", []),
            chosen_option_index=data.get("chosen_option_index", -1),
            chosen_option_label=data.get("chosen_option_label", ""),
            applied_effects=data.get("applied_effects", {}),
            related_wrestler=data.get("related_wrestler", ""),
            related_storyline_id=data.get("related_storyline_id", ""),
            contact_id=data.get("contact_id", ""),
            is_ai_tinted=data.get("is_ai_tinted", False),
            ai_personality=data.get("ai_personality", ""),
        )


# ==================== CALLS MANAGER ====================

class CallsManager:
    """
    Central calls manager.
    Handles incoming calls, contact list, call history, weekly expiration.
    """

    def __init__(self):
        self.calls: List[Call] = []
        self.contacts: Dict[str, Dict] = dict(DEFAULT_CONTACTS)  # contact_id -> contact_data
        self.next_id_num: int = 1
        self.lifetime_received: int = 0
        self.lifetime_answered: int = 0
        self.lifetime_declined: int = 0
        self.lifetime_missed: int = 0

    def _next_call_id(self, prefix: str = "call") -> str:
        cid = f"{prefix}_{self.next_id_num}"
        self.next_id_num += 1
        return cid

    # ==================== ADD CALLS ====================

    def add_call(
        self,
        caller_name: str,
        subject: str,
        body: str,
        caller_subtitle: str = "",
        icon: str = "📞",
        color: str = "#3b82f6",
        call_type: str = "general",
        priority: str = "normal",
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
        expires_in_weeks: int = 2,
        options: List[Dict] = None,
        related_wrestler: str = "",
        related_storyline_id: str = "",
        contact_id: str = "",
        is_ai_tinted: bool = False,
        ai_personality: str = "",
    ) -> Call:
        """Add a call to the queue"""

        try:
            ct = CallType(call_type)
        except (ValueError, KeyError):
            ct = CallType.GENERAL

        try:
            pr = CallPriority(priority)
        except (ValueError, KeyError):
            pr = CallPriority.NORMAL

        call = Call(
            id=self._next_call_id(),
            caller_name=caller_name,
            caller_subtitle=caller_subtitle,
            subject=subject,
            body=body,
            icon=icon,
            color=color,
            call_type=ct,
            status=CallStatus.INCOMING,
            priority=pr,
            week=week,
            year=year,
            day=day,
            month=month,
            received_at=datetime.now().isoformat(),
            expires_in_weeks=expires_in_weeks,
            weeks_pending=0,
            options=options or [],
            related_wrestler=related_wrestler,
            related_storyline_id=related_storyline_id,
            contact_id=contact_id,
            is_ai_tinted=is_ai_tinted,
            ai_personality=ai_personality,
        )

        self.calls.append(call)
        self.lifetime_received += 1
        return call

    def add_ai_director_call(
        self,
        ai_director,
        subject: str,
        body: str,
        options: List[Dict] = None,
        priority: str = "normal",
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
        related_wrestler: str = "",
        related_storyline_id: str = "",
    ) -> Call:
        """
        Convenience method: add a call from the AI Director with personality voice.
        Automatically uses personality name, icon, and color.
        """
        if not ai_director or not hasattr(ai_director, "personality"):
            return self.add_call(
                caller_name="AI Director",
                subject=subject,
                body=body,
                options=options,
                priority=priority,
                week=week, year=year, day=day, month=month,
            )

        personality = ai_director.personality
        return self.add_call(
            caller_name=personality.get_name(),
            caller_subtitle="AI Creative Director",
            subject=subject,
            body=body,
            icon=personality.get_icon(),
            color=personality.get_color(),
            call_type="ai_director",
            priority=priority,
            week=week, year=year, day=day, month=month,
            options=options,
            contact_id="ai_director",
            is_ai_tinted=True,
            ai_personality=personality.get_name(),
            related_wrestler=related_wrestler,
            related_storyline_id=related_storyline_id,
        )

    def add_loan_shark_call(
        self,
        subject: str,
        body: str,
        options: List[Dict] = None,
        is_threat: bool = False,
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
    ) -> Call:
        """Convenience method: add a Loan Shark call"""
        contact = self.contacts.get("loan_shark", {})
        return self.add_call(
            caller_name=contact.get("name", "Loan Shark"),
            caller_subtitle=contact.get("subtitle", "Tony 'The Wallet' Castellano"),
            subject=subject,
            body=body,
            icon=contact.get("icon", "💰"),
            color=contact.get("color", "#dc2626"),
            call_type="loan_shark_threat" if is_threat else "loan_shark",
            priority="urgent" if is_threat else "high",
            week=week, year=year, day=day, month=month,
            options=options,
            contact_id="loan_shark",
            expires_in_weeks=1 if is_threat else 2,
        )

    def add_sponsor_call(
        self,
        sponsor_name: str,
        subject: str,
        body: str,
        amount: int = 0,
        options: List[Dict] = None,
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
    ) -> Call:
        """Convenience method: add a sponsor offer call"""
        return self.add_call(
            caller_name=sponsor_name,
            caller_subtitle=f"Sponsorship Offer: ${amount:,}",
            subject=subject,
            body=body,
            icon="🤝",
            color="#10b981",
            call_type="sponsor",
            priority="normal",
            week=week, year=year, day=day, month=month,
            options=options,
            expires_in_weeks=2,
        )

    def add_emergency_call(
        self,
        caller_name: str,
        subject: str,
        body: str,
        options: List[Dict] = None,
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
        related_wrestler: str = "",
    ) -> Call:
        """Convenience method: add a crisis/emergency call"""
        return self.add_call(
            caller_name=caller_name,
            caller_subtitle="URGENT",
            subject=subject,
            body=body,
            icon="🆘",
            color="#dc2626",
            call_type="emergency",
            priority="urgent",
            week=week, year=year, day=day, month=month,
            options=options,
            related_wrestler=related_wrestler,
            expires_in_weeks=1,
        )

    # ==================== CALL ACTIONS ====================

    def answer_call(self, call_id: str, option_index: int = 0) -> Dict:
        """
        Player answers a call and chooses an option.
        Returns the chosen option's effects for the app to apply.
        """
        call = self.get_call(call_id)
        if not call:
            return {"success": False, "message": "Call not found", "effects": {}}

        if call.status != CallStatus.INCOMING:
            return {"success": False, "message": "Call already handled", "effects": {}}

        if option_index < 0 or option_index >= len(call.options):
            return {"success": False, "message": "Invalid option", "effects": {}}

        chosen = call.options[option_index]
        effects = chosen.get("effects", {})

        call.status = CallStatus.ANSWERED
        call.chosen_option_index = option_index
        call.chosen_option_label = chosen.get("label", "")
        call.applied_effects = effects

        self.lifetime_answered += 1

        return {
            "success": True,
            "message": f"Answered: {chosen.get('label', '')}",
            "effects": effects,
            "call": call,
        }

    def decline_call(self, call_id: str) -> bool:
        """Player declines/ignores a call"""
        call = self.get_call(call_id)
        if call and call.status == CallStatus.INCOMING:
            call.status = CallStatus.DECLINED
            self.lifetime_declined += 1
            return True
        return False

    def delete_call(self, call_id: str) -> bool:
        """Permanently delete a call"""
        for i, call in enumerate(self.calls):
            if call.id == call_id:
                self.calls.pop(i)
                return True
        return False

    # ==================== WEEKLY PROCESSING ====================

    def process_weekly_aging(self) -> List[Call]:
        """
        Age all incoming calls by 1 week. Auto-miss expired calls.
        Returns list of newly missed calls.
        """
        missed = []
        for call in self.calls:
            if call.status != CallStatus.INCOMING:
                continue
            call.weeks_pending += 1
            if call.weeks_pending >= call.expires_in_weeks:
                call.status = CallStatus.MISSED
                self.lifetime_missed += 1
                missed.append(call)
        return missed

    # ==================== QUERIES ====================

    def get_call(self, call_id: str) -> Optional[Call]:
        for call in self.calls:
            if call.id == call_id:
                return call
        return None

    def get_all_calls(self) -> List[Call]:
        """Get all calls, newest first"""
        return sorted(self.calls, key=lambda c: (c.year, c.month, c.day, c.id), reverse=True)

    def get_incoming_calls(self) -> List[Call]:
        """Active incoming calls awaiting response"""
        return [c for c in self.get_all_calls() if c.status == CallStatus.INCOMING]

    def get_answered_calls(self) -> List[Call]:
        return [c for c in self.get_all_calls() if c.status == CallStatus.ANSWERED]

    def get_missed_calls(self) -> List[Call]:
        return [c for c in self.get_all_calls() if c.status == CallStatus.MISSED]

    def get_declined_calls(self) -> List[Call]:
        return [c for c in self.get_all_calls() if c.status == CallStatus.DECLINED]

    def get_calls_by_type(self, call_type: CallType) -> List[Call]:
        return [c for c in self.get_all_calls() if c.call_type == call_type]

    def get_urgent_calls(self) -> List[Call]:
        """Get incoming calls marked urgent"""
        return [c for c in self.get_incoming_calls() if c.priority == CallPriority.URGENT]

    def get_ai_director_calls(self) -> List[Call]:
        return [c for c in self.get_all_calls() if c.is_ai_tinted]

    def get_calls_for_wrestler(self, wrestler_name: str) -> List[Call]:
        return [c for c in self.get_all_calls() if c.related_wrestler == wrestler_name]

    def get_calls_for_storyline(self, storyline_id: str) -> List[Call]:
        return [c for c in self.get_all_calls() if c.related_storyline_id == storyline_id]

    def get_recent(self, limit: int = 10) -> List[Call]:
        return self.get_all_calls()[:limit]

    # ==================== STATS ====================

    def get_incoming_count(self) -> int:
        return len(self.get_incoming_calls())

    def get_urgent_count(self) -> int:
        return len(self.get_urgent_calls())

    def get_total_count(self) -> int:
        return len(self.calls)

    def get_calls_summary(self) -> Dict:
        """Full summary stats for UI display"""
        return {
            "total": self.get_total_count(),
            "incoming": self.get_incoming_count(),
            "urgent": self.get_urgent_count(),
            "answered": len(self.get_answered_calls()),
            "missed": len(self.get_missed_calls()),
            "declined": len(self.get_declined_calls()),
            "ai_calls": len(self.get_ai_director_calls()),
            "lifetime_received": self.lifetime_received,
            "lifetime_answered": self.lifetime_answered,
            "lifetime_declined": self.lifetime_declined,
            "lifetime_missed": self.lifetime_missed,
        }

    # ==================== CONTACTS ====================

    def get_contact(self, contact_id: str) -> Optional[Dict]:
        return self.contacts.get(contact_id)

    def get_all_contacts(self) -> List[Dict]:
        """Get all contacts as a list with their IDs included"""
        result = []
        for contact_id, data in self.contacts.items():
            entry = dict(data)
            entry["id"] = contact_id
            result.append(entry)
        return result

    def add_contact(self, contact_id: str, contact_data: Dict):
        """Add a new contact (e.g. when player meets a sponsor)"""
        self.contacts[contact_id] = contact_data

    def remove_contact(self, contact_id: str) -> bool:
        if contact_id in self.contacts and not DEFAULT_CONTACTS.get(contact_id, {}).get("always_available"):
            del self.contacts[contact_id]
            return True
        return False

    # ==================== CLEANUP ====================

    def cleanup_old_calls(self, current_week: int, current_year: int, weeks_to_keep: int = 26):
        """Remove calls older than X weeks (default 6 months)"""
        kept = []
        for call in self.calls:
            week_diff = (current_year - call.year) * 52 + (current_week - call.week)
            if week_diff <= weeks_to_keep:
                kept.append(call)
        self.calls = kept

    def cap_call_count(self, max_calls: int = 100):
        """Prevent calls from growing too large by removing oldest"""
        if len(self.calls) <= max_calls:
            return
        # Sort by oldest first, remove oldest until under cap
        self.calls.sort(key=lambda c: (c.year, c.month, c.day))
        excess = len(self.calls) - max_calls
        self.calls = self.calls[excess:]

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "calls": [c.to_dict() for c in self.calls],
            "contacts": self.contacts,
            "next_id_num": self.next_id_num,
            "lifetime_received": self.lifetime_received,
            "lifetime_answered": self.lifetime_answered,
            "lifetime_declined": self.lifetime_declined,
            "lifetime_missed": self.lifetime_missed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CallsManager":
        manager = cls()
        manager.next_id_num = data.get("next_id_num", 1)
        manager.lifetime_received = data.get("lifetime_received", 0)
        manager.lifetime_answered = data.get("lifetime_answered", 0)
        manager.lifetime_declined = data.get("lifetime_declined", 0)
        manager.lifetime_missed = data.get("lifetime_missed", 0)

        # Restore contacts (merge with defaults)
        saved_contacts = data.get("contacts", {})
        for contact_id, contact_data in saved_contacts.items():
            manager.contacts[contact_id] = contact_data

        # Restore calls
        for cd in data.get("calls", []):
            try:
                manager.calls.append(Call.from_dict(cd))
            except Exception as e:
                print(f"Error loading call: {e}")

        return manager
