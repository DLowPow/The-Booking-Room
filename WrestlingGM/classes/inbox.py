"""
Inbox System - Player's main communication hub
Receives messages from AI Director, news, storylines, contracts, events
All messages can be tinted by AI personality voice
Supports categorization, threading, and rich metadata
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ==================== MESSAGE TYPES ====================

class MessageType(Enum):
    """Categories for inbox messages"""
    GENERAL = "general"
    AI_THOUGHT = "ai_thought"
    AI_PITCH = "ai_pitch"
    SHOW_REPORT = "show_report"
    INJURY = "injury"
    CHAMPIONSHIP = "championship"
    CONTRACT = "contract"
    CONTRACT_WARNING = "contract_warning"
    FINANCIAL = "financial"
    NEWS = "news"
    STORYLINE = "storyline"
    STORYLINE_BEAT = "storyline_beat"
    QUEST = "quest"
    EVENT = "event"
    RIVAL_RAID = "rival_raid"
    RIVAL_SIGNING = "rival_signing"
    WALKOUT = "walkout"
    TRAINEE = "trainee"
    SCHOOL_UPDATE = "school_update"
    SOCIAL_MEDIA = "social_media"
    CREATIVE = "creative"
    WEEKLY_SUMMARY = "weekly_summary"
    ACHIEVEMENT = "achievement"
    LEVEL_UP = "level_up"
    SCANDAL = "scandal"
    OPPORTUNITY = "opportunity"


class MessagePriority(Enum):
    """Priority levels for sorting and visual styling"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ==================== MESSAGE CLASS ====================

@dataclass
class Message:
    """A single inbox message"""
    id: str
    sender: str
    subject: str
    body: str
    icon: str = "📧"
    message_type: MessageType = MessageType.GENERAL
    priority: MessagePriority = MessagePriority.NORMAL

    # Date received
    week: int = 0
    year: int = 1
    day: int = 1
    month: int = 1
    received_at: str = ""

    # State
    is_read: bool = False
    is_starred: bool = False
    is_archived: bool = False
    is_deleted: bool = False

    # Threading
    thread_id: str = ""
    parent_id: str = ""

    # Rich metadata
    sender_color: str = ""
    sender_icon: str = ""
    related_wrestler: str = ""
    related_storyline_id: str = ""
    related_show_id: str = ""
    action_url: str = ""
    action_label: str = ""

    # AI tinted
    is_ai_tinted: bool = False
    ai_personality: str = ""

    # ==================== HELPERS ====================

    def get_priority_color(self) -> str:
        colors = {
            MessagePriority.LOW: "#6b7280",
            MessagePriority.NORMAL: "#3b82f6",
            MessagePriority.HIGH: "#f59e0b",
            MessagePriority.URGENT: "#ef4444",
        }
        return colors.get(self.priority, "#3b82f6")

    def get_type_color(self) -> str:
        colors = {
            MessageType.AI_THOUGHT: "#a855f7",
            MessageType.AI_PITCH: "#a855f7",
            MessageType.SHOW_REPORT: "#3b82f6",
            MessageType.INJURY: "#ef4444",
            MessageType.CHAMPIONSHIP: "#fbbf24",
            MessageType.CONTRACT: "#f59e0b",
            MessageType.CONTRACT_WARNING: "#f59e0b",
            MessageType.FINANCIAL: "#10b981",
            MessageType.NEWS: "#06b6d4",
            MessageType.STORYLINE: "#ec4899",
            MessageType.STORYLINE_BEAT: "#ec4899",
            MessageType.QUEST: "#8b5cf6",
            MessageType.EVENT: "#fbbf24",
            MessageType.RIVAL_RAID: "#dc2626",
            MessageType.RIVAL_SIGNING: "#dc2626",
            MessageType.WALKOUT: "#7c2d12",
            MessageType.TRAINEE: "#10b981",
            MessageType.SCHOOL_UPDATE: "#10b981",
            MessageType.SOCIAL_MEDIA: "#06b6d4",
            MessageType.CREATIVE: "#a855f7",
            MessageType.WEEKLY_SUMMARY: "#6b7280",
            MessageType.ACHIEVEMENT: "#fbbf24",
            MessageType.LEVEL_UP: "#10b981",
            MessageType.SCANDAL: "#dc2626",
            MessageType.OPPORTUNITY: "#10b981",
            MessageType.GENERAL: "#6b7280",
        }
        return colors.get(self.message_type, "#6b7280")

    def get_date_display(self) -> str:
        """Human-readable date for the inbox list"""
        return f"{self.month}/{self.day}/Y{self.year}"

    def get_preview(self, max_length: int = 80) -> str:
        """Short preview for inbox list view"""
        clean = self.body.replace("\n", " ").strip()
        if len(clean) <= max_length:
            return clean
        return clean[:max_length].rsplit(" ", 1)[0] + "..."

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "subject": self.subject,
            "body": self.body,
            "icon": self.icon,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "week": self.week,
            "year": self.year,
            "day": self.day,
            "month": self.month,
            "received_at": self.received_at,
            "is_read": self.is_read,
            "is_starred": self.is_starred,
            "is_archived": self.is_archived,
            "is_deleted": self.is_deleted,
            "thread_id": self.thread_id,
            "parent_id": self.parent_id,
            "sender_color": self.sender_color,
            "sender_icon": self.sender_icon,
            "related_wrestler": self.related_wrestler,
            "related_storyline_id": self.related_storyline_id,
            "related_show_id": self.related_show_id,
            "action_url": self.action_url,
            "action_label": self.action_label,
            "is_ai_tinted": self.is_ai_tinted,
            "ai_personality": self.ai_personality,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        try:
            mt = MessageType(data.get("message_type", "general"))
        except (ValueError, KeyError):
            mt = MessageType.GENERAL

        try:
            pr = MessagePriority(data.get("priority", "normal"))
        except (ValueError, KeyError):
            pr = MessagePriority.NORMAL

        return cls(
            id=data.get("id", ""),
            sender=data.get("sender", "System"),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            icon=data.get("icon", "📧"),
            message_type=mt,
            priority=pr,
            week=data.get("week", 0),
            year=data.get("year", 1),
            day=data.get("day", 1),
            month=data.get("month", 1),
            received_at=data.get("received_at", ""),
            is_read=data.get("is_read", False),
            is_starred=data.get("is_starred", False),
            is_archived=data.get("is_archived", False),
            is_deleted=data.get("is_deleted", False),
            thread_id=data.get("thread_id", ""),
            parent_id=data.get("parent_id", ""),
            sender_color=data.get("sender_color", ""),
            sender_icon=data.get("sender_icon", ""),
            related_wrestler=data.get("related_wrestler", ""),
            related_storyline_id=data.get("related_storyline_id", ""),
            related_show_id=data.get("related_show_id", ""),
            action_url=data.get("action_url", ""),
            action_label=data.get("action_label", ""),
            is_ai_tinted=data.get("is_ai_tinted", False),
            ai_personality=data.get("ai_personality", ""),
        )


# ==================== INBOX MANAGER ====================

class InboxManager:
    """
    Central inbox manager.
    Receives messages from all game systems (AI Director, news, events, etc.)
    Provides filtering, sorting, threading, and stats.
    """

    def __init__(self):
        self.messages: List[Message] = []
        self.next_id_num: int = 1
        self.lifetime_received: int = 0
        self.lifetime_read: int = 0

    def _next_message_id(self, prefix: str = "msg") -> str:
        msg_id = f"{prefix}_{self.next_id_num}"
        self.next_id_num += 1
        return msg_id

    # ==================== ADD MESSAGES ====================

    def add_message(
        self,
        sender: str,
        subject: str,
        body: str,
        icon: str = "📧",
        message_type: str = "general",
        priority: str = "normal",
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
        related_wrestler: str = "",
        related_storyline_id: str = "",
        related_show_id: str = "",
        action_url: str = "",
        action_label: str = "",
        sender_color: str = "",
        sender_icon: str = "",
        is_ai_tinted: bool = False,
        ai_personality: str = "",
        thread_id: str = "",
        parent_id: str = "",
    ) -> Message:
        """Add a message to the inbox"""

        try:
            mt = MessageType(message_type)
        except (ValueError, KeyError):
            mt = MessageType.GENERAL

        try:
            pr = MessagePriority(priority)
        except (ValueError, KeyError):
            pr = MessagePriority.NORMAL

        message = Message(
            id=self._next_message_id(),
            sender=sender,
            subject=subject,
            body=body,
            icon=icon,
            message_type=mt,
            priority=pr,
            week=week,
            year=year,
            day=day,
            month=month,
            received_at=datetime.now().isoformat(),
            related_wrestler=related_wrestler,
            related_storyline_id=related_storyline_id,
            related_show_id=related_show_id,
            action_url=action_url,
            action_label=action_label,
            sender_color=sender_color,
            sender_icon=sender_icon,
            is_ai_tinted=is_ai_tinted,
            ai_personality=ai_personality,
            thread_id=thread_id,
            parent_id=parent_id,
        )

        self.messages.append(message)
        self.lifetime_received += 1
        return message

    def add_from_voice_engine(
        self,
        message_data: dict,
        week: int = 0,
        year: int = 1,
        day: int = 1,
        month: int = 1,
        ai_personality: str = "",
        related_wrestler: str = "",
        action_url: str = "",
        action_label: str = "",
    ) -> Message:
        """
        Add a message built by VoiceEngine.build_inbox_message().
        Convenience wrapper that handles all the dict unpacking.
        """
        return self.add_message(
            sender=message_data.get("sender", "System"),
            subject=message_data.get("subject", ""),
            body=message_data.get("body", ""),
            icon=message_data.get("icon", "📧"),
            message_type=message_data.get("message_type", "general"),
            priority=message_data.get("priority", "normal"),
            week=week,
            year=year,
            day=day,
            month=month,
            related_wrestler=related_wrestler,
            action_url=action_url,
            action_label=action_label,
            is_ai_tinted=bool(ai_personality),
            ai_personality=ai_personality,
        )

    # ==================== MESSAGE STATE ====================

    def mark_read(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg and not msg.is_read:
            msg.is_read = True
            self.lifetime_read += 1
            return True
        return False

    def mark_unread(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg and msg.is_read:
            msg.is_read = False
            return True
        return False

    def mark_all_read(self) -> int:
        """Mark all unread messages as read. Returns count."""
        count = 0
        for msg in self.messages:
            if not msg.is_read and not msg.is_deleted:
                msg.is_read = True
                count += 1
                self.lifetime_read += 1
        return count

    def toggle_star(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg:
            msg.is_starred = not msg.is_starred
            return True
        return False

    def archive_message(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg:
            msg.is_archived = True
            return True
        return False

    def unarchive_message(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg:
            msg.is_archived = False
            return True
        return False

    def delete_message(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg:
            msg.is_deleted = True
            return True
        return False

    def restore_message(self, message_id: str) -> bool:
        msg = self.get_message(message_id)
        if msg and msg.is_deleted:
            msg.is_deleted = False
            return True
        return False

    def permanently_delete(self, message_id: str) -> bool:
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                self.messages.pop(i)
                return True
        return False

    def empty_trash(self) -> int:
        """Permanently delete all trashed messages. Returns count."""
        before = len(self.messages)
        self.messages = [m for m in self.messages if not m.is_deleted]
        return before - len(self.messages)

    # ==================== QUERIES ====================

    def get_message(self, message_id: str) -> Optional[Message]:
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        return None

    def get_all_messages(self, include_archived: bool = False, include_deleted: bool = False) -> List[Message]:
        """Get all messages, optionally filtering archived/deleted"""
        result = self.messages
        if not include_archived:
            result = [m for m in result if not m.is_archived]
        if not include_deleted:
            result = [m for m in result if not m.is_deleted]
        return result

    def get_inbox(self) -> List[Message]:
        """Get active inbox (not archived, not deleted), newest first"""
        active = [m for m in self.messages if not m.is_archived and not m.is_deleted]
        return sorted(active, key=lambda m: (m.year, m.month, m.day, m.id), reverse=True)

    def get_unread(self) -> List[Message]:
        return [m for m in self.get_inbox() if not m.is_read]

    def get_starred(self) -> List[Message]:
        return [m for m in self.messages if m.is_starred and not m.is_deleted]

    def get_archived(self) -> List[Message]:
        return [m for m in self.messages if m.is_archived and not m.is_deleted]

    def get_trash(self) -> List[Message]:
        return [m for m in self.messages if m.is_deleted]

    def get_by_type(self, message_type: MessageType) -> List[Message]:
        return [m for m in self.get_inbox() if m.message_type == message_type]

    def get_by_priority(self, priority: MessagePriority) -> List[Message]:
        return [m for m in self.get_inbox() if m.priority == priority]

    def get_urgent(self) -> List[Message]:
        return self.get_by_priority(MessagePriority.URGENT)

    def get_for_wrestler(self, wrestler_name: str) -> List[Message]:
        return [m for m in self.messages if m.related_wrestler == wrestler_name]

    def get_for_storyline(self, storyline_id: str) -> List[Message]:
        return [m for m in self.messages if m.related_storyline_id == storyline_id]

    def get_thread(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread, sorted oldest first"""
        thread_msgs = [m for m in self.messages if m.thread_id == thread_id and not m.is_deleted]
        return sorted(thread_msgs, key=lambda m: (m.year, m.month, m.day, m.id))

    def get_recent(self, limit: int = 10) -> List[Message]:
        return self.get_inbox()[:limit]

    def get_ai_messages(self) -> List[Message]:
        """Get messages from the AI Director"""
        return [m for m in self.get_inbox() if m.is_ai_tinted]

    # ==================== STATS ====================

    def get_unread_count(self) -> int:
        return len(self.get_unread())

    def get_urgent_count(self) -> int:
        return len([m for m in self.get_inbox() if m.priority == MessagePriority.URGENT and not m.is_read])

    def get_total_count(self) -> int:
        return len(self.get_inbox())

    def get_starred_count(self) -> int:
        return len(self.get_starred())

    def get_message_counts_by_type(self) -> Dict[str, int]:
        """Count of unread messages per type for UI badges"""
        counts = {}
        for msg in self.get_unread():
            type_value = msg.message_type.value
            counts[type_value] = counts.get(type_value, 0) + 1
        return counts

    def get_inbox_summary(self) -> Dict:
        """Full summary stats for UI display"""
        return {
            "total": self.get_total_count(),
            "unread": self.get_unread_count(),
            "urgent": self.get_urgent_count(),
            "starred": self.get_starred_count(),
            "archived": len(self.get_archived()),
            "trash": len(self.get_trash()),
            "ai_messages": len(self.get_ai_messages()),
            "lifetime_received": self.lifetime_received,
            "lifetime_read": self.lifetime_read,
            "by_type": self.get_message_counts_by_type(),
        }

    # ==================== CLEANUP ====================

    def cleanup_old_messages(self, current_week: int, current_year: int, weeks_to_keep: int = 26):
        """Auto-archive messages older than X weeks (default 6 months)"""
        archived_count = 0
        for msg in self.messages:
            if msg.is_archived or msg.is_deleted:
                continue

            # Calculate age in weeks
            week_diff = (current_year - msg.year) * 52 + (current_week - msg.week)
            if week_diff > weeks_to_keep:
                msg.is_archived = True
                archived_count += 1

        return archived_count

    def cap_message_count(self, max_messages: int = 500):
        """Prevent inbox from growing too large by removing oldest deleted messages"""
        if len(self.messages) <= max_messages:
            return

        # Remove deleted messages first
        deleted = [m for m in self.messages if m.is_deleted]
        if deleted:
            # Sort by oldest first
            deleted.sort(key=lambda m: (m.year, m.month, m.day))
            to_remove = len(self.messages) - max_messages
            for msg in deleted[:to_remove]:
                self.messages.remove(msg)

        # If still too many, remove oldest archived
        if len(self.messages) > max_messages:
            archived = [m for m in self.messages if m.is_archived]
            archived.sort(key=lambda m: (m.year, m.month, m.day))
            to_remove = len(self.messages) - max_messages
            for msg in archived[:to_remove]:
                self.messages.remove(msg)

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "messages": [m.to_dict() for m in self.messages],
            "next_id_num": self.next_id_num,
            "lifetime_received": self.lifetime_received,
            "lifetime_read": self.lifetime_read,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InboxManager":
        manager = cls()
        manager.next_id_num = data.get("next_id_num", 1)
        manager.lifetime_received = data.get("lifetime_received", 0)
        manager.lifetime_read = data.get("lifetime_read", 0)
        for md in data.get("messages", []):
            try:
                manager.messages.append(Message.from_dict(md))
            except Exception as e:
                print(f"Error loading message: {e}")
        return manager
