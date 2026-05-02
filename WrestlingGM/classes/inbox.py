"""
Inbox System - Persistent message history
All messages received during the game are stored here
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Message:
    id: str
    sender: str
    subject: str
    body: str
    date: str = ""
    year: int = 1
    month: int = 1
    day: int = 1
    is_read: bool = False
    message_type: str = "general"
    has_attachment: bool = False
    attachment_type: str = ""
    attachment_value: int = 0
    attachment_accepted: bool = False
    icon: str = "📧"

    def mark_read(self):
        self.is_read = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "subject": self.subject,
            "body": self.body,
            "date": self.date,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "is_read": self.is_read,
            "message_type": self.message_type,
            "has_attachment": self.has_attachment,
            "attachment_type": self.attachment_type,
            "attachment_value": self.attachment_value,
            "attachment_accepted": self.attachment_accepted,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            id=data.get("id", ""),
            sender=data.get("sender", "Unknown"),
            subject=data.get("subject", "No Subject"),
            body=data.get("body", ""),
            date=data.get("date", ""),
            year=data.get("year", 1),
            month=data.get("month", 1),
            day=data.get("day", 1),
            is_read=data.get("is_read", False),
            message_type=data.get("message_type", "general"),
            has_attachment=data.get("has_attachment", False),
            attachment_type=data.get("attachment_type", ""),
            attachment_value=data.get("attachment_value", 0),
            attachment_accepted=data.get("attachment_accepted", False),
            icon=data.get("icon", "📧"),
        )


class InboxManager:
    def __init__(self):
        self.messages: List[Message] = []
        self.next_id: int = 1

    def add_message(
        self, sender: str, subject: str, body: str,
        year: int = 1, month: int = 1, day: int = 1,
        message_type: str = "general", icon: str = "📧",
        has_attachment: bool = False, attachment_type: str = "",
        attachment_value: int = 0,
    ) -> Message:
        msg = Message(
            id=f"msg_{self.next_id}",
            sender=sender,
            subject=subject,
            body=body,
            date=f"Y{year} M{month} D{day}",
            year=year, month=month, day=day,
            message_type=message_type,
            icon=icon,
            has_attachment=has_attachment,
            attachment_type=attachment_type,
            attachment_value=attachment_value,
        )
        self.messages.insert(0, msg)
        self.next_id += 1
        return msg

    def get_message(self, msg_id: str) -> Optional[Message]:
        for msg in self.messages:
            if msg.id == msg_id:
                return msg
        return None

    def get_all_messages(self) -> List[Message]:
        return self.messages

    def get_unread_messages(self) -> List[Message]:
        return [m for m in self.messages if not m.is_read]

    def get_unread_count(self) -> int:
        return len(self.get_unread_messages())

    def mark_read(self, msg_id: str):
        msg = self.get_message(msg_id)
        if msg:
            msg.is_read = True

    def mark_all_read(self):
        for msg in self.messages:
            msg.is_read = True

    def to_dict(self) -> dict:
        return {
            "messages": [m.to_dict() for m in self.messages],
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InboxManager":
        inbox = cls()
        inbox.next_id = data.get("next_id", 1)
        for md in data.get("messages", []):
            inbox.messages.append(Message.from_dict(md))
        return inbox
