"""
Relationship Manager - Tracks relationships between wrestlers
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RelationshipType(Enum):
    FRIEND = "Friend"
    RIVAL = "Rival"
    ENEMY = "Enemy"
    MENTOR = "Mentor"
    PROTEGE = "Protege"
    TAG_PARTNER = "Tag Partner"
    FACTION_MATE = "Faction Mate"
    EX_TAG_PARTNER = "Ex-Tag Partner"
    EX_FACTION = "Ex-Faction"
    ROMANTIC = "Romantic"
    FAMILY = "Family"
    NEUTRAL = "Neutral"


@dataclass
class Relationship:
    """A relationship between two wrestlers"""
    wrestler1: str
    wrestler2: str
    relationship_type: RelationshipType
    intensity: int = 50  # 0-100 (how strong the relationship is)
    duration_weeks: int = 0
    origin: str = ""  # How the relationship started
    is_public: bool = False  # Is this known to fans?
    
    def to_dict(self) -> dict:
        return {
            "wrestler1": self.wrestler1,
            "wrestler2": self.wrestler2,
            "relationship_type": self.relationship_type.value,
            "intensity": self.intensity,
            "duration_weeks": self.duration_weeks,
            "origin": self.origin,
            "is_public": self.is_public,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        return cls(
            wrestler1=data["wrestler1"],
            wrestler2=data["wrestler2"],
            relationship_type=RelationshipType(data["relationship_type"]),
            intensity=data.get("intensity", 50),
            duration_weeks=data.get("duration_weeks", 0),
            origin=data.get("origin", ""),
            is_public=data.get("is_public", False),
        )


class RelationshipManager:
    """Manages all relationships between wrestlers"""
    
    def __init__(self):
        self.relationships: List[Relationship] = []
    
    def add_relationship(
        self,
        wrestler1: str,
        wrestler2: str,
        relationship_type: str,
        intensity: int = 50,
        origin: str = "",
        is_public: bool = False
    ) -> Relationship:
        """Add or update a relationship"""
        # Check if relationship exists
        existing = self.get_relationship(wrestler1, wrestler2)
        
        if existing:
            existing.relationship_type = RelationshipType(relationship_type)
            existing.intensity = intensity
            existing.origin = origin
            existing.is_public = is_public
            return existing
        
        rel = Relationship(
            wrestler1=wrestler1,
            wrestler2=wrestler2,
            relationship_type=RelationshipType(relationship_type),
            intensity=intensity,
            origin=origin,
            is_public=is_public,
        )
        self.relationships.append(rel)
        return rel
    
    def remove_relationship(self, wrestler1: str, wrestler2: str) -> bool:
        """Remove a relationship between two wrestlers"""
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel:
            self.relationships.remove(rel)
            return True
        return False
    
    def get_relationship(self, wrestler1: str, wrestler2: str) -> Optional[Relationship]:
        """Get relationship between two wrestlers"""
        for rel in self.relationships:
            if (rel.wrestler1 == wrestler1 and rel.wrestler2 == wrestler2) or \
               (rel.wrestler1 == wrestler2 and rel.wrestler2 == wrestler1):
                return rel
        return None
    
    def get_wrestler_relationships(self, wrestler_name: str) -> List[Relationship]:
        """Get all relationships for a wrestler"""
        return [
            rel for rel in self.relationships
            if rel.wrestler1 == wrestler_name or rel.wrestler2 == wrestler_name
        ]
    
    def get_relationships_by_type(
        self,
        wrestler_name: str,
        relationship_type: RelationshipType
    ) -> List[Relationship]:
        """Get all relationships of a specific type for a wrestler"""
        return [
            rel for rel in self.get_wrestler_relationships(wrestler_name)
            if rel.relationship_type == relationship_type
        ]
    
    def get_friends(self, wrestler_name: str) -> List[str]:
        """Get all friends of a wrestler"""
        friends = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.FRIEND:
                other = rel.wrestler2 if rel.wrestler1 == wrestler_name else rel.wrestler1
                friends.append(other)
        return friends
    
    def get_enemies(self, wrestler_name: str) -> List[str]:
        """Get all enemies/rivals of a wrestler"""
        enemies = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type in [RelationshipType.ENEMY, RelationshipType.RIVAL]:
                other = rel.wrestler2 if rel.wrestler1 == wrestler_name else rel.wrestler1
                enemies.append(other)
        return enemies
    
    def get_tag_partners(self, wrestler_name: str) -> List[str]:
        """Get all tag partners of a wrestler"""
        partners = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.TAG_PARTNER:
                other = rel.wrestler2 if rel.wrestler1 == wrestler_name else rel.wrestler1
                partners.append(other)
        return partners
    
    def get_faction_mates(self, wrestler_name: str) -> List[str]:
        """Get all faction mates of a wrestler"""
        mates = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.FACTION_MATE:
                other = rel.wrestler2 if rel.wrestler1 == wrestler_name else rel.wrestler1
                mates.append(other)
        return mates
    
    def get_mentors(self, wrestler_name: str) -> List[str]:
        """Get all mentors of a wrestler"""
        mentors = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.MENTOR:
                if rel.wrestler2 == wrestler_name:  # wrestler_name is the protege
                    mentors.append(rel.wrestler1)
            elif rel.relationship_type == RelationshipType.PROTEGE:
                if rel.wrestler1 == wrestler_name:  # wrestler_name is the protege
                    mentors.append(rel.wrestler2)
        return mentors
    
    def get_proteges(self, wrestler_name: str) -> List[str]:
        """Get all proteges of a wrestler"""
        proteges = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.MENTOR:
                if rel.wrestler1 == wrestler_name:  # wrestler_name is the mentor
                    proteges.append(rel.wrestler2)
            elif rel.relationship_type == RelationshipType.PROTEGE:
                if rel.wrestler2 == wrestler_name:  # wrestler_name is the mentor
                    proteges.append(rel.wrestler1)
        return proteges
    
    def are_friends(self, wrestler1: str, wrestler2: str) -> bool:
        """Check if two wrestlers are friends"""
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type == RelationshipType.FRIEND
    
    def are_enemies(self, wrestler1: str, wrestler2: str) -> bool:
        """Check if two wrestlers are enemies"""
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type in [
            RelationshipType.ENEMY, RelationshipType.RIVAL
        ]
    
    def intensify_rivalry(self, wrestler1: str, wrestler2: str, amount: int = 10):
        """Intensify a rivalry between two wrestlers"""
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]:
            rel.intensity = min(100, rel.intensity + amount)
        elif not rel:
            self.add_relationship(wrestler1, wrestler2, "Rival", amount)
    
    def cool_rivalry(self, wrestler1: str, wrestler2: str, amount: int = 10):
        """Cool down a rivalry between two wrestlers"""
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]:
            rel.intensity = max(0, rel.intensity - amount)
            if rel.intensity <= 0:
                self.relationships.remove(rel)
    
    def weekly_decay(self) -> List[Dict]:
        """Process weekly relationship changes"""
        changes = []
        
        for rel in self.relationships[:]:
            rel.duration_weeks += 1
            
            # Rivalries/enemies naturally cool off over time
            if rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]:
                if rel.intensity > 20:
                    rel.intensity -= 2
                    if rel.intensity <= 20:
                        changes.append({
                            "wrestlers": [rel.wrestler1, rel.wrestler2],
                            "change": "rivalry_cooled",
                            "message": f"The rivalry between {rel.wrestler1} and {rel.wrestler2} has cooled off.",
                        })
            
            # Friendships can decay if not maintained
            if rel.relationship_type == RelationshipType.FRIEND:
                if rel.duration_weeks > 52 and rel.intensity > 30:
                    rel.intensity -= 1
            
            # Remove dead relationships
            if rel.intensity <= 0:
                self.relationships.remove(rel)
                changes.append({
                    "wrestlers": [rel.wrestler1, rel.wrestler2],
                    "change": "relationship_ended",
                    "message": f"The {rel.relationship_type.value.lower()} relationship between {rel.wrestler1} and {rel.wrestler2} has ended.",
                })
        
        return changes
    
    def form_tag_team(self, wrestler1: str, wrestler2: str, team_name: str = ""):
        """Form a tag team"""
        self.add_relationship(
            wrestler1, wrestler2, "Tag Partner",
            intensity=75,
            origin=f"Formed tag team: {team_name}" if team_name else "Formed tag team",
            is_public=True,
        )
        # Being tag partners also makes you friends
        if not self.are_friends(wrestler1, wrestler2):
            self.add_relationship(wrestler1, wrestler2, "Friend", intensity=50)
    
    def break_up_tag_team(self, wrestler1: str, wrestler2: str, turn_enemies: bool = False):
        """Break up a tag team"""
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type == RelationshipType.TAG_PARTNER:
            rel.relationship_type = RelationshipType.EX_TAG_PARTNER
            rel.intensity = 30
            
            if turn_enemies:
                self.add_relationship(
                    wrestler1, wrestler2, "Rival",
                    intensity=70,
                    origin="Tag team breakup",
                    is_public=True,
                )
    
    def form_faction(self, members: List[str], faction_name: str = ""):
        """Form a faction"""
        origin = f"Joined faction: {faction_name}" if faction_name else "Joined faction"
        
        # All members are faction mates with each other
        for i, member1 in enumerate(members):
            for member2 in members[i+1:]:
                self.add_relationship(
                    member1, member2, "Faction Mate",
                    intensity=60,
                    origin=origin,
                    is_public=True,
                )
    
    def remove_from_faction(self, wrestler: str, turn_enemy: bool = False):
        """Remove a wrestler from their faction"""
        faction_mates = self.get_faction_mates(wrestler)
        
        for mate in faction_mates:
            rel = self.get_relationship(wrestler, mate)
            if rel:
                if turn_enemy:
                    rel.relationship_type = RelationshipType.RIVAL
                    rel.intensity = 60
                    rel.origin = "Expelled from faction"
                else:
                    rel.relationship_type = RelationshipType.EX_FACTION
                    rel.intensity = 20
    
    def get_chemistry_modifier(self, wrestler1: str, wrestler2: str) -> float:
        """Get a chemistry modifier based on relationship (for match quality)"""
        rel = self.get_relationship(wrestler1, wrestler2)
        
        if not rel:
            return 1.0
        
        modifiers = {
            RelationshipType.FRIEND: 1.1,
            RelationshipType.TAG_PARTNER: 1.15,
            RelationshipType.FACTION_MATE: 1.1,
            RelationshipType.MENTOR: 1.1,
            RelationshipType.PROTEGE: 1.1,
            RelationshipType.RIVAL: 1.2,  # Rivalries create great matches!
            RelationshipType.ENEMY: 1.15,
            RelationshipType.EX_TAG_PARTNER: 1.1,
            RelationshipType.EX_FACTION: 1.05,
            RelationshipType.FAMILY: 1.1,
        }
        
        base_modifier = modifiers.get(rel.relationship_type, 1.0)
        
        # Intensity affects the modifier
        intensity_bonus = (rel.intensity - 50) / 200  # -0.25 to +0.25
        
        return base_modifier + intensity_bonus
    
    def to_dict(self) -> dict:
        return {
            "relationships": [rel.to_dict() for rel in self.relationships]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipManager":
        manager = cls()
        for rel_data in data.get("relationships", []):
            manager.relationships.append(Relationship.from_dict(rel_data))
        return manager