"""
Living World Memory Core
Tracks important moments so the AI can learn from the save over time.
"""

from dataclasses import dataclass, field
from typing import List, Any
import uuid


@dataclass
class AIMemory:
    id: str
    week: int
    year: int
    memory_type: str
    subject: str
    description: str
    importance: int = 50
    emotional_weight: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            week=data.get("week", 0),
            year=data.get("year", 1),
            memory_type=data.get("memory_type", "general"),
            subject=data.get("subject", ""),
            description=data.get("description", ""),
            importance=data.get("importance", 50),
            emotional_weight=data.get("emotional_weight", 0),
            tags=data.get("tags", []),
        )


class MemoryCore:
    def __init__(self):
        self.memories: List[AIMemory] = []

    def remember(self, week, year, memory_type, subject, description,
                 importance=50, emotional_weight=0, tags=None):
        memory = AIMemory(
            id=str(uuid.uuid4()),
            week=week,
            year=year,
            memory_type=memory_type,
            subject=subject,
            description=description,
            importance=importance,
            emotional_weight=emotional_weight,
            tags=tags or [],
        )
        self.memories.append(memory)
        self.memories = self.memories[-300:]
        return memory

    def get_recent(self, limit=10):
        return self.memories[-limit:]

    def get_for_subject(self, subject, limit=10):
        results = [m for m in self.memories if m.subject == subject]
        return results[-limit:]

    def to_dict(self):
        return {"memories": [m.to_dict() for m in self.memories]}

    @classmethod
    def from_dict(cls, data):
        core = cls()
        for item in data.get("memories", []):
            core.memories.append(AIMemory.from_dict(item))
        return core