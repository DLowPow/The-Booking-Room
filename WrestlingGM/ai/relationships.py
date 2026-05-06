"""
Relationship Manager - Wrestler-to-wrestler dynamics
Tracks friendships, rivalries, mentors, tag teams, factions, families
Bridges to Storyline Engine for storyline suggestions
Provides chemistry modifiers for match quality
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# ==================== RELATIONSHIP ENUMS ====================

class RelationshipType(Enum):
    FRIEND = "Friend"
    BEST_FRIEND = "Best Friend"
    RIVAL = "Rival"
    ENEMY = "Enemy"
    MENTOR = "Mentor"
    PROTEGE = "Protege"
    TAG_PARTNER = "Tag Partner"
    FACTION_MATE = "Faction Mate"
    EX_TAG_PARTNER = "Ex-Tag Partner"
    EX_FACTION = "Ex-Faction"
    ROMANTIC = "Romantic"
    EX_ROMANTIC = "Ex-Romantic"
    FAMILY = "Family"
    NEUTRAL = "Neutral"


class RelationshipStatus(Enum):
    ACTIVE = "Active"
    DECLINING = "Declining"
    STRAINED = "Strained"
    BROKEN = "Broken"


# ==================== RELATIONSHIP DATA CLASS ====================

@dataclass
class Relationship:
    """A relationship between two wrestlers"""
    wrestler1: str
    wrestler2: str
    relationship_type: RelationshipType
    intensity: int = 50  # 0-100
    duration_weeks: int = 0
    origin: str = ""
    is_public: bool = False  # Known to fans?
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    notable_events: List[str] = field(default_factory=list)

    def get_intensity_color(self) -> str:
        if self.intensity >= 80:
            return "#dc2626"
        if self.intensity >= 60:
            return "#f59e0b"
        if self.intensity >= 40:
            return "#3b82f6"
        if self.intensity >= 20:
            return "#6b7280"
        return "#4b5563"

    def get_type_color(self) -> str:
        colors = {
            RelationshipType.FRIEND: "#3b82f6",
            RelationshipType.BEST_FRIEND: "#10b981",
            RelationshipType.RIVAL: "#f59e0b",
            RelationshipType.ENEMY: "#dc2626",
            RelationshipType.MENTOR: "#8b5cf6",
            RelationshipType.PROTEGE: "#a78bfa",
            RelationshipType.TAG_PARTNER: "#10b981",
            RelationshipType.FACTION_MATE: "#06b6d4",
            RelationshipType.EX_TAG_PARTNER: "#6b7280",
            RelationshipType.EX_FACTION: "#6b7280",
            RelationshipType.ROMANTIC: "#ec4899",
            RelationshipType.EX_ROMANTIC: "#9d174d",
            RelationshipType.FAMILY: "#fbbf24",
            RelationshipType.NEUTRAL: "#9ca3af",
        }
        return colors.get(self.relationship_type, "#9ca3af")

    def get_type_icon(self) -> str:
        icons = {
            RelationshipType.FRIEND: "🤝",
            RelationshipType.BEST_FRIEND: "💛",
            RelationshipType.RIVAL: "⚔️",
            RelationshipType.ENEMY: "💢",
            RelationshipType.MENTOR: "🎓",
            RelationshipType.PROTEGE: "📚",
            RelationshipType.TAG_PARTNER: "🤜🤛",
            RelationshipType.FACTION_MATE: "👥",
            RelationshipType.EX_TAG_PARTNER: "💔",
            RelationshipType.EX_FACTION: "🚪",
            RelationshipType.ROMANTIC: "💕",
            RelationshipType.EX_ROMANTIC: "💔",
            RelationshipType.FAMILY: "👨‍👩‍👧",
            RelationshipType.NEUTRAL: "—",
        }
        return icons.get(self.relationship_type, "—")

    def add_notable_event(self, event: str):
        """Add a notable event to this relationship's history"""
        self.notable_events.append(event)
        if len(self.notable_events) > 20:
            self.notable_events = self.notable_events[-20:]

    def to_dict(self) -> dict:
        return {
            "wrestler1": self.wrestler1,
            "wrestler2": self.wrestler2,
            "relationship_type": self.relationship_type.value,
            "intensity": self.intensity,
            "duration_weeks": self.duration_weeks,
            "origin": self.origin,
            "is_public": self.is_public,
            "status": self.status.value,
            "notable_events": self.notable_events,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        try:
            rt = RelationshipType(data["relationship_type"])
        except (ValueError, KeyError):
            rt = RelationshipType.NEUTRAL
        try:
            status = RelationshipStatus(data.get("status", "Active"))
        except ValueError:
            status = RelationshipStatus.ACTIVE

        return cls(
            wrestler1=data["wrestler1"],
            wrestler2=data["wrestler2"],
            relationship_type=rt,
            intensity=data.get("intensity", 50),
            duration_weeks=data.get("duration_weeks", 0),
            origin=data.get("origin", ""),
            is_public=data.get("is_public", False),
            status=status,
            notable_events=data.get("notable_events", []),
        )


# ==================== RELATIONSHIP MANAGER ====================

class RelationshipManager:
    """Manages all wrestler-to-wrestler relationships"""

    def __init__(self):
        self.relationships: List[Relationship] = []

    # ==================== ADD/REMOVE/QUERY ====================

    def add_relationship(
        self,
        wrestler1: str,
        wrestler2: str,
        relationship_type: str,
        intensity: int = 50,
        origin: str = "",
        is_public: bool = False,
    ) -> Relationship:
        """Add or update a relationship"""
        existing = self.get_relationship(wrestler1, wrestler2)
        if existing:
            try:
                existing.relationship_type = RelationshipType(relationship_type)
            except ValueError:
                existing.relationship_type = RelationshipType.NEUTRAL
            existing.intensity = intensity
            existing.origin = origin
            existing.is_public = is_public
            return existing

        try:
            rt = RelationshipType(relationship_type)
        except ValueError:
            rt = RelationshipType.NEUTRAL

        rel = Relationship(
            wrestler1=wrestler1,
            wrestler2=wrestler2,
            relationship_type=rt,
            intensity=intensity,
            origin=origin,
            is_public=is_public,
        )
        self.relationships.append(rel)
        return rel

    def remove_relationship(self, wrestler1: str, wrestler2: str) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel:
            self.relationships.remove(rel)
            return True
        return False

    def get_relationship(self, wrestler1: str, wrestler2: str) -> Optional[Relationship]:
        for rel in self.relationships:
            if (rel.wrestler1 == wrestler1 and rel.wrestler2 == wrestler2) or \
               (rel.wrestler1 == wrestler2 and rel.wrestler2 == wrestler1):
                return rel
        return None

    def get_wrestler_relationships(self, wrestler_name: str) -> List[Relationship]:
        return [
            rel for rel in self.relationships
            if rel.wrestler1 == wrestler_name or rel.wrestler2 == wrestler_name
        ]

    def get_relationships_by_type(
        self,
        wrestler_name: str,
        relationship_type: RelationshipType,
    ) -> List[Relationship]:
        return [
            rel for rel in self.get_wrestler_relationships(wrestler_name)
            if rel.relationship_type == relationship_type
        ]

    def get_other_wrestler(self, rel: Relationship, wrestler_name: str) -> str:
        return rel.wrestler2 if rel.wrestler1 == wrestler_name else rel.wrestler1

    # ==================== TYPED QUERIES ====================

    def get_friends(self, wrestler_name: str) -> List[str]:
        friends = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type in [RelationshipType.FRIEND, RelationshipType.BEST_FRIEND]:
                friends.append(self.get_other_wrestler(rel, wrestler_name))
        return friends

    def get_enemies(self, wrestler_name: str) -> List[str]:
        enemies = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type in [RelationshipType.ENEMY, RelationshipType.RIVAL]:
                enemies.append(self.get_other_wrestler(rel, wrestler_name))
        return enemies

    def get_tag_partners(self, wrestler_name: str) -> List[str]:
        partners = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.TAG_PARTNER:
                partners.append(self.get_other_wrestler(rel, wrestler_name))
        return partners

    def get_faction_mates(self, wrestler_name: str) -> List[str]:
        mates = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.FACTION_MATE:
                mates.append(self.get_other_wrestler(rel, wrestler_name))
        return mates

    def get_mentors(self, wrestler_name: str) -> List[str]:
        mentors = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.MENTOR and rel.wrestler2 == wrestler_name:
                mentors.append(rel.wrestler1)
            elif rel.relationship_type == RelationshipType.PROTEGE and rel.wrestler1 == wrestler_name:
                mentors.append(rel.wrestler2)
        return mentors

    def get_proteges(self, wrestler_name: str) -> List[str]:
        proteges = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.MENTOR and rel.wrestler1 == wrestler_name:
                proteges.append(rel.wrestler2)
            elif rel.relationship_type == RelationshipType.PROTEGE and rel.wrestler2 == wrestler_name:
                proteges.append(rel.wrestler1)
        return proteges

    def get_family_members(self, wrestler_name: str) -> List[str]:
        family = []
        for rel in self.get_wrestler_relationships(wrestler_name):
            if rel.relationship_type == RelationshipType.FAMILY:
                family.append(self.get_other_wrestler(rel, wrestler_name))
        return family

    # ==================== STATE CHECKS ====================

    def are_friends(self, wrestler1: str, wrestler2: str) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type in [
            RelationshipType.FRIEND, RelationshipType.BEST_FRIEND,
        ]

    def are_enemies(self, wrestler1: str, wrestler2: str) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type in [
            RelationshipType.ENEMY, RelationshipType.RIVAL,
        ]

    def are_tag_partners(self, wrestler1: str, wrestler2: str) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type == RelationshipType.TAG_PARTNER

    def are_faction_mates(self, wrestler1: str, wrestler2: str) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type == RelationshipType.FACTION_MATE

    def are_family(self, wrestler1: str, wrestler2: str) -> bool:
        rel = self.get_relationship(wrestler1, wrestler2)
        return rel is not None and rel.relationship_type == RelationshipType.FAMILY

    # ==================== INTENSITY MANAGEMENT ====================

    def intensify_rivalry(self, wrestler1: str, wrestler2: str, amount: int = 10):
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]:
            rel.intensity = min(100, rel.intensity + amount)
        elif not rel:
            self.add_relationship(wrestler1, wrestler2, "Rival", amount)

    def cool_rivalry(self, wrestler1: str, wrestler2: str, amount: int = 10):
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]:
            rel.intensity = max(0, rel.intensity - amount)
            if rel.intensity <= 0:
                self.relationships.remove(rel)

    def strengthen_friendship(self, wrestler1: str, wrestler2: str, amount: int = 5):
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type in [RelationshipType.FRIEND, RelationshipType.BEST_FRIEND]:
            rel.intensity = min(100, rel.intensity + amount)
            if rel.intensity >= 85 and rel.relationship_type == RelationshipType.FRIEND:
                rel.relationship_type = RelationshipType.BEST_FRIEND
        elif not rel:
            self.add_relationship(wrestler1, wrestler2, "Friend", 50 + amount)

    # ==================== WEEKLY DECAY ====================

    def weekly_decay(self) -> List[Dict]:
        """Process weekly relationship changes"""
        changes = []
        for rel in self.relationships[:]:
            rel.duration_weeks += 1

            # Rivalries cool naturally
            if rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]:
                if rel.intensity > 20:
                    rel.intensity -= 2
                    if rel.intensity <= 20:
                        rel.status = RelationshipStatus.DECLINING
                        changes.append({
                            "wrestlers": [rel.wrestler1, rel.wrestler2],
                            "change": "rivalry_cooled",
                            "message": f"The rivalry between {rel.wrestler1} and {rel.wrestler2} has cooled off.",
                        })

            # Friendships can decay if not maintained
            elif rel.relationship_type in [RelationshipType.FRIEND, RelationshipType.BEST_FRIEND]:
                if rel.duration_weeks > 52 and rel.intensity > 30:
                    rel.intensity -= 1

            # Tag teams strengthen over time (up to a cap)
            elif rel.relationship_type == RelationshipType.TAG_PARTNER:
                if rel.intensity < 90 and rel.duration_weeks % 4 == 0:
                    rel.intensity = min(90, rel.intensity + 1)

            # Romantic relationships have natural fluctuation
            elif rel.relationship_type == RelationshipType.ROMANTIC:
                fluctuation = random.choice([-2, -1, 0, 0, 1, 2])
                rel.intensity = max(0, min(100, rel.intensity + fluctuation))

            # Update status based on intensity
            if rel.intensity >= 70:
                rel.status = RelationshipStatus.ACTIVE
            elif rel.intensity >= 40:
                rel.status = RelationshipStatus.ACTIVE
            elif rel.intensity >= 20:
                rel.status = RelationshipStatus.DECLINING
            elif rel.intensity > 0:
                rel.status = RelationshipStatus.STRAINED
            else:
                rel.status = RelationshipStatus.BROKEN

            # Remove dead relationships
            if rel.intensity <= 0:
                self.relationships.remove(rel)
                changes.append({
                    "wrestlers": [rel.wrestler1, rel.wrestler2],
                    "change": "relationship_ended",
                    "message": f"The {rel.relationship_type.value.lower()} relationship between {rel.wrestler1} and {rel.wrestler2} has ended.",
                })

        return changes

    # ==================== TAG TEAMS ====================

    def form_tag_team(self, wrestler1: str, wrestler2: str, team_name: str = ""):
        """Form a tag team between two wrestlers"""
        rel = self.add_relationship(
            wrestler1, wrestler2, "Tag Partner",
            intensity=75,
            origin=f"Formed tag team: {team_name}" if team_name else "Formed tag team",
            is_public=True,
        )
        if team_name:
            rel.add_notable_event(f"Formed tag team '{team_name}'")

        # Tag partners often become friends
        if not self.are_friends(wrestler1, wrestler2):
            existing = self.get_relationship(wrestler1, wrestler2)
            # Don't override the tag partner relationship — just track the bond
            if existing and existing.relationship_type == RelationshipType.TAG_PARTNER:
                existing.add_notable_event("Strong bond developing")

    def break_up_tag_team(self, wrestler1: str, wrestler2: str, turn_enemies: bool = False):
        """Break up a tag team"""
        rel = self.get_relationship(wrestler1, wrestler2)
        if rel and rel.relationship_type == RelationshipType.TAG_PARTNER:
            if turn_enemies:
                rel.relationship_type = RelationshipType.RIVAL
                rel.intensity = 70
                rel.origin = "Tag team breakup turned bitter"
                rel.add_notable_event("Tag team broke up — became enemies")
                rel.is_public = True
            else:
                rel.relationship_type = RelationshipType.EX_TAG_PARTNER
                rel.intensity = 30
                rel.add_notable_event("Tag team amicably split")

    # ==================== FACTIONS ====================

    def form_faction(self, members: List[str], faction_name: str = ""):
        """Form a faction with multiple members"""
        origin = f"Joined faction: {faction_name}" if faction_name else "Joined faction"

        # All members are faction mates with each other
        for i, member1 in enumerate(members):
            for member2 in members[i + 1:]:
                rel = self.add_relationship(
                    member1, member2, "Faction Mate",
                    intensity=60,
                    origin=origin,
                    is_public=True,
                )
                if faction_name:
                    rel.add_notable_event(f"Founding member of '{faction_name}'")

    def remove_from_faction(self, wrestler: str, turn_enemy: bool = False):
        """Remove a wrestler from their faction"""
        faction_mates = self.get_faction_mates(wrestler)
        for mate in faction_mates:
            rel = self.get_relationship(wrestler, mate)
            if rel:
                if turn_enemy:
                    rel.relationship_type = RelationshipType.RIVAL
                    rel.intensity = 65
                    rel.origin = "Expelled from faction"
                    rel.add_notable_event(f"{wrestler} was kicked out — became enemies")
                else:
                    rel.relationship_type = RelationshipType.EX_FACTION
                    rel.intensity = 25
                    rel.add_notable_event(f"{wrestler} left the faction")

    # ==================== MENTOR / PROTÉGÉ ====================

    def establish_mentorship(self, mentor: str, protege: str):
        """Establish a mentor/protégé relationship"""
        rel = self.add_relationship(
            mentor, protege, "Mentor",
            intensity=70,
            origin=f"{mentor} is training {protege}",
            is_public=False,
        )
        rel.add_notable_event(f"{mentor} took {protege} under their wing")

    def graduate_protege(self, mentor: str, protege: str, on_good_terms: bool = True):
        """End a mentor/protégé relationship — protégé moves on"""
        rel = self.get_relationship(mentor, protege)
        if rel and rel.relationship_type in [RelationshipType.MENTOR, RelationshipType.PROTEGE]:
            if on_good_terms:
                rel.relationship_type = RelationshipType.FRIEND
                rel.intensity = 60
                rel.add_notable_event("Mentorship graduated to friendship")
            else:
                rel.relationship_type = RelationshipType.RIVAL
                rel.intensity = 75
                rel.add_notable_event("Student surpassed master — became rivals")

    # ==================== STORYLINE ENGINE BRIDGE ====================

    def suggest_storyline_pairs(self, min_intensity: int = 50) -> List[Dict]:
        """
        Suggest wrestler pairs with strong existing relationships for storylines.
        The Storyline Engine can use these to propose richer feuds.
        """
        suggestions = []

        for rel in self.relationships:
            if rel.intensity < min_intensity:
                continue

            suggestion = {
                "wrestler1": rel.wrestler1,
                "wrestler2": rel.wrestler2,
                "relationship_type": rel.relationship_type.value,
                "intensity": rel.intensity,
                "is_public": rel.is_public,
                "duration_weeks": rel.duration_weeks,
                "suggested_storyline": None,
                "reasoning": "",
            }

            # Map relationships to ideal storyline types
            if rel.relationship_type == RelationshipType.RIVAL:
                suggestion["suggested_storyline"] = "Personal Rivalry"
                suggestion["reasoning"] = "Existing rivalry — storyline writes itself."
            elif rel.relationship_type == RelationshipType.ENEMY:
                suggestion["suggested_storyline"] = "Grudge Match"
                suggestion["reasoning"] = "Deep hatred — perfect for a grudge."
            elif rel.relationship_type == RelationshipType.TAG_PARTNER and rel.intensity >= 70:
                suggestion["suggested_storyline"] = "Betrayal"
                suggestion["reasoning"] = "Strong tag bond — set up a shocking betrayal."
            elif rel.relationship_type == RelationshipType.BEST_FRIEND:
                suggestion["suggested_storyline"] = "Betrayal"
                suggestion["reasoning"] = "Best friends — betrayal would be devastating."
            elif rel.relationship_type == RelationshipType.MENTOR:
                suggestion["suggested_storyline"] = "Mentor vs Student"
                suggestion["reasoning"] = "Mentor/protégé dynamic — passing of the torch."
            elif rel.relationship_type == RelationshipType.PROTEGE:
                suggestion["suggested_storyline"] = "Mentor vs Student"
                suggestion["reasoning"] = "Student wants to surpass their teacher."
            elif rel.relationship_type == RelationshipType.EX_TAG_PARTNER:
                suggestion["suggested_storyline"] = "Personal Rivalry"
                suggestion["reasoning"] = "Former partners — unfinished business."
            elif rel.relationship_type == RelationshipType.EX_FACTION:
                suggestion["suggested_storyline"] = "Grudge Match"
                suggestion["reasoning"] = "Former faction member — bad blood remains."
            elif rel.relationship_type == RelationshipType.FAMILY:
                suggestion["suggested_storyline"] = "Legacy"
                suggestion["reasoning"] = "Family ties — legacy storyline potential."
            elif rel.relationship_type == RelationshipType.FACTION_MATE:
                suggestion["suggested_storyline"] = "Faction War"
                suggestion["reasoning"] = "Faction members — set up internal conflict."
            elif rel.relationship_type == RelationshipType.ROMANTIC:
                suggestion["suggested_storyline"] = "Love Triangle"
                suggestion["reasoning"] = "Romantic angle — perfect for triangle drama."
            elif rel.relationship_type == RelationshipType.EX_ROMANTIC:
                suggestion["suggested_storyline"] = "Personal Rivalry"
                suggestion["reasoning"] = "Past romance — fuel for personal feud."

            if suggestion["suggested_storyline"]:
                suggestions.append(suggestion)

        # Sort by intensity (highest first)
        suggestions.sort(key=lambda s: -s["intensity"])
        return suggestions

    def get_chemistry_modifier(self, wrestler1: str, wrestler2: str) -> float:
        """
        Get chemistry modifier for match quality calculation.
        Used by the match engine to apply rating bonuses.
        """
        rel = self.get_relationship(wrestler1, wrestler2)
        if not rel:
            return 1.0

        modifiers = {
            RelationshipType.FRIEND: 1.10,
            RelationshipType.BEST_FRIEND: 1.15,
            RelationshipType.TAG_PARTNER: 1.20,
            RelationshipType.FACTION_MATE: 1.10,
            RelationshipType.MENTOR: 1.12,
            RelationshipType.PROTEGE: 1.12,
            RelationshipType.RIVAL: 1.25,        # Rivalries create great matches!
            RelationshipType.ENEMY: 1.20,
            RelationshipType.EX_TAG_PARTNER: 1.15,
            RelationshipType.EX_FACTION: 1.10,
            RelationshipType.FAMILY: 1.10,
            RelationshipType.ROMANTIC: 1.05,
            RelationshipType.EX_ROMANTIC: 1.18,  # Drama!
            RelationshipType.NEUTRAL: 1.0,
        }

        base_modifier = modifiers.get(rel.relationship_type, 1.0)

        # Intensity affects the modifier (-0.25 to +0.25 swing)
        intensity_bonus = (rel.intensity - 50) / 200
        return base_modifier + intensity_bonus

    # ==================== STATS / SUMMARIES ====================

    def get_relationship_count(self) -> int:
        """Total number of tracked relationships"""
        return len(self.relationships)

    def get_relationship_summary(self, wrestler_name: str) -> Dict:
        """Get a summary of all relationships for a wrestler"""
        all_rels = self.get_wrestler_relationships(wrestler_name)
        return {
            "total": len(all_rels),
            "friends": len(self.get_friends(wrestler_name)),
            "enemies": len(self.get_enemies(wrestler_name)),
            "tag_partners": len(self.get_tag_partners(wrestler_name)),
            "faction_mates": len(self.get_faction_mates(wrestler_name)),
            "mentors": len(self.get_mentors(wrestler_name)),
            "proteges": len(self.get_proteges(wrestler_name)),
            "family": len(self.get_family_members(wrestler_name)),
        }

    def get_strongest_bonds(self, limit: int = 10) -> List[Relationship]:
        """Get the strongest relationships in the promotion (highest intensity)"""
        sorted_rels = sorted(self.relationships, key=lambda r: -r.intensity)
        return sorted_rels[:limit]

    def get_hottest_rivalries(self, limit: int = 10) -> List[Relationship]:
        """Get the most intense rivalries currently active"""
        rivalries = [
            r for r in self.relationships
            if r.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]
        ]
        rivalries.sort(key=lambda r: -r.intensity)
        return rivalries[:limit]

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "relationships": [rel.to_dict() for rel in self.relationships],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipManager":
        manager = cls()
        for rel_data in data.get("relationships", []):
            try:
                manager.relationships.append(Relationship.from_dict(rel_data))
            except Exception:
                pass
        return manager
