"""
Group System - Tag Teams, Trios & Factions

Smart auto-typing based on member count:
  2 members  -> Tag Team
  3 members  -> Trio
  4-8 members -> Faction (with optional leader)

Rules:
  - Unlimited groups (only constrained by roster size)
  - A wrestler can be in 1 Tag Team/Trio + 1 Faction (max overlap)
  - Faction leader gets +5% match bonus, members get +2%
  - Tag Teams: +3% chemistry bonus per match
  - Trios: +5% chemistry bonus per match
  - Auto-cleanup when wrestlers are released/retired
  - Auto-promote next leader if faction leader leaves
  - Future-ready for splits (NWO -> NWO Wolfpac storyline)
"""
import re
import uuid
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ==================== ENUMS ====================
class GroupType(Enum):
    TAG_TEAM = "Tag Team"      # Exactly 2 members
    TRIO = "Trio"              # Exactly 3 members
    FACTION = "Faction"        # 4-8 members


# ==================== CONSTANTS ====================
MIN_GROUP_SIZE = 2
MAX_GROUP_SIZE = 8

# Chemistry/stat bonuses (match rating multipliers)
TAG_TEAM_CHEMISTRY_BONUS = 0.03   # +3% to tag team matches
TRIO_CHEMISTRY_BONUS = 0.05       # +5% to trios matches
FACTION_MEMBER_BONUS = 0.02       # +2% to faction members in any match
FACTION_LEADER_BONUS = 0.05       # +5% to faction leader (additional)

# Trophy popularity bonus
TROPHY_WIN_POPULARITY = 10        # +10 popularity per holder when winning a trophy


# ==================== GROUP DATACLASS ====================
@dataclass
class Group:
    """
    A unified group container for Tag Teams, Trios, and Factions.
    Type is auto-detected from member count.
    """
    id: str
    name: str
    members: List[str] = field(default_factory=list)  # Wrestler names
    leader_id: str = ""                                # Only used for factions
    formed_year: int = 1
    formed_week: int = 0

    # Stats tracking
    matches_together: int = 0
    wins_together: int = 0
    losses_together: int = 0
    titles_won_together: int = 0
    trophies_won_together: int = 0

    # Display
    description: str = ""
    color: str = "#6366f1"  # Default indigo
    icon: str = ""           # Optional emoji icon

    # Status
    is_active: bool = True
    disbanded_year: int = 0
    disbanded_week: int = 0
    disband_reason: str = ""

    # ==================== TYPE DETECTION ====================
    @property
    def group_type(self) -> GroupType:
        """Auto-detect group type from member count."""
        count = len(self.members)
        if count == 2:
            return GroupType.TAG_TEAM
        elif count == 3:
            return GroupType.TRIO
        else:
            return GroupType.FACTION

    def is_tag_team(self) -> bool:
        return len(self.members) == 2

    def is_trio(self) -> bool:
        return len(self.members) == 3

    def is_faction(self) -> bool:
        return len(self.members) >= 4

    # ==================== TYPE-SPECIFIC HELPERS ====================
    def get_type_icon(self) -> str:
        """Default icon based on group type."""
        if self.icon:
            return self.icon
        if self.is_tag_team():
            return "🤝"
        if self.is_trio():
            return "🔱"
        return "👥"

    def get_type_label(self) -> str:
        return self.group_type.value

    def get_type_color(self) -> str:
        """Default color based on type, or custom color if set."""
        if self.color != "#6366f1":
            return self.color
        if self.is_tag_team():
            return "#3b82f6"   # Blue
        if self.is_trio():
            return "#a855f7"   # Purple
        return "#f59e0b"        # Amber for factions

    # ==================== MEMBER MANAGEMENT ====================
    def has_member(self, wrestler_name: str) -> bool:
        return wrestler_name in self.members

    def add_member(self, wrestler_name: str) -> Tuple[bool, str]:
        """
        Add a member to the group.
        Returns (success, message).
        """
        if not wrestler_name:
            return (False, "No wrestler specified")
        if wrestler_name in self.members:
            return (False, f"{wrestler_name} is already in this group")
        if len(self.members) >= MAX_GROUP_SIZE:
            return (False, f"Group already at max size ({MAX_GROUP_SIZE})")

        self.members.append(wrestler_name)
        return (True, f"{wrestler_name} added to {self.name}")

    def remove_member(self, wrestler_name: str) -> Tuple[bool, str]:
        """
        Remove a member from the group.
        If the leader leaves a faction, auto-promote next member.
        Returns (success, message).
        """
        if wrestler_name not in self.members:
            return (False, f"{wrestler_name} is not in this group")

        self.members.remove(wrestler_name)

        # If the leader left, auto-promote the first remaining member
        leader_changed = False
        if self.leader_id == wrestler_name:
            self.leader_id = ""
            if self.members and self.is_faction():
                self.leader_id = self.members[0]
                leader_changed = True

        msg = f"{wrestler_name} removed from {self.name}"
        if leader_changed:
            msg += f" — {self.leader_id} promoted to leader"
        return (True, msg)

    def set_leader(self, wrestler_name: str) -> Tuple[bool, str]:
        """
        Set or change the faction leader.
        Only meaningful for factions (4+ members).
        """
        if not self.is_faction():
            return (False, "Leaders only apply to factions (4+ members)")
        if wrestler_name not in self.members:
            return (False, f"{wrestler_name} is not in this group")

        previous = self.leader_id
        self.leader_id = wrestler_name

        if previous and previous != wrestler_name:
            return (True, f"Leadership of {self.name} transferred from {previous} to {wrestler_name}")
        return (True, f"{wrestler_name} is now leading {self.name}")

    def get_leader(self) -> str:
        """Returns the leader name, or first member if no leader set."""
        if self.leader_id and self.leader_id in self.members:
            return self.leader_id
        if self.members:
            return self.members[0]
        return ""

    def get_members_ordered(self) -> List[str]:
        """
        Return members with leader first (if set), then the rest.
        Used for display in templates.
        """
        if not self.leader_id or self.leader_id not in self.members:
            return list(self.members)
        ordered = [self.leader_id]
        ordered.extend(m for m in self.members if m != self.leader_id)
        return ordered

    def get_member_count(self) -> int:
        return len(self.members)

    def is_valid(self) -> bool:
        """A group must have at least 2 members to be valid."""
        return len(self.members) >= MIN_GROUP_SIZE

    def is_at_capacity(self) -> bool:
        return len(self.members) >= MAX_GROUP_SIZE

    # ==================== STAT BONUSES ====================
    def get_chemistry_bonus(self) -> float:
        """
        Match rating bonus multiplier when ALL group members compete together.
        e.g., a tag team match where both members are from this group.
        """
        if self.is_tag_team():
            return TAG_TEAM_CHEMISTRY_BONUS
        if self.is_trio():
            return TRIO_CHEMISTRY_BONUS
        # Factions don't get chemistry bonus in matches (they're too big)
        return 0.0

    def get_member_bonus(self, wrestler_name: str) -> float:
        """
        Per-wrestler bonus when this member competes (in any match).
        Faction members get +2%, leader gets +5% (additional).
        """
        if not self.is_faction():
            return 0.0  # Tag/Trio bonuses apply to whole-team matches only
        if wrestler_name not in self.members:
            return 0.0

        bonus = FACTION_MEMBER_BONUS
        if wrestler_name == self.leader_id:
            bonus += FACTION_LEADER_BONUS
        return bonus

    # ==================== STATS TRACKING ====================
    def record_match(self, won: bool):
        """Record a match the group competed in together."""
        self.matches_together += 1
        if won:
            self.wins_together += 1
        else:
            self.losses_together += 1

    def record_title_won(self):
        self.titles_won_together += 1

    def record_trophy_won(self):
        self.trophies_won_together += 1

    def get_win_rate(self) -> float:
        if self.matches_together == 0:
            return 0.0
        return (self.wins_together / self.matches_together) * 100

    # ==================== DISPLAY ====================
    def get_display_name(self) -> str:
        """Returns name with icon prefix for UI display."""
        icon = self.get_type_icon()
        return f"{icon} {self.name}"

    def get_summary_line(self) -> str:
        """One-liner for list views."""
        return f"{self.get_display_name()} ({self.get_type_label()}, {len(self.members)} members)"

    def get_summary(self) -> Dict:
        """Compact summary for UI display."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.get_display_name(),
            "type": self.group_type.value,
            "type_icon": self.get_type_icon(),
            "type_color": self.get_type_color(),
            "member_count": len(self.members),
            "members": self.members,
            "members_ordered": self.get_members_ordered(),
            "leader": self.get_leader(),
            "leader_id": self.leader_id,
            "is_tag_team": self.is_tag_team(),
            "is_trio": self.is_trio(),
            "is_faction": self.is_faction(),
            "matches_together": self.matches_together,
            "wins_together": self.wins_together,
            "losses_together": self.losses_together,
            "win_rate": round(self.get_win_rate(), 1),
            "titles_won": self.titles_won_together,
            "trophies_won": self.trophies_won_together,
            "is_active": self.is_active,
            "formed": f"Y{self.formed_year} W{self.formed_week}",
        }

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "members": list(self.members),
            "leader_id": self.leader_id,
            "formed_year": self.formed_year,
            "formed_week": self.formed_week,
            "matches_together": self.matches_together,
            "wins_together": self.wins_together,
            "losses_together": self.losses_together,
            "titles_won_together": self.titles_won_together,
            "trophies_won_together": self.trophies_won_together,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "is_active": self.is_active,
            "disbanded_year": self.disbanded_year,
            "disbanded_week": self.disbanded_week,
            "disband_reason": self.disband_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unnamed Group"),
            members=list(data.get("members", [])),
            leader_id=data.get("leader_id", ""),
            formed_year=data.get("formed_year", 1),
            formed_week=data.get("formed_week", 0),
            matches_together=data.get("matches_together", 0),
            wins_together=data.get("wins_together", 0),
            losses_together=data.get("losses_together", 0),
            titles_won_together=data.get("titles_won_together", 0),
            trophies_won_together=data.get("trophies_won_together", 0),
            description=data.get("description", ""),
            color=data.get("color", "#6366f1"),
            icon=data.get("icon", ""),
            is_active=data.get("is_active", True),
            disbanded_year=data.get("disbanded_year", 0),
            disbanded_week=data.get("disbanded_week", 0),
            disband_reason=data.get("disband_reason", ""),
        )


# ==================== GROUP MANAGER ====================
class GroupManager:
    """
    Manages all tag teams, trios, and factions for the player's promotion.
    Enforces the 1 Tag/Trio + 1 Faction overlap rule.
    """

    def __init__(self):
        self.groups: List[Group] = []
        self.disbanded_groups: List[Group] = []  # Archive for history

    # ==================== CREATION ====================
    def create_group(
        self,
        name: str,
        member_names: List[str],
        leader_id: str = "",
        formed_year: int = 1,
        formed_week: int = 0,
        description: str = "",
        icon: str = "",
        color: str = "",
    ) -> Tuple[bool, str, Optional[Group]]:
        """
        Create a new group.
        Returns (success, message, group_or_None).
        """
        # Validate name
        if not name or not name.strip():
            return (False, "Group name is required", None)
        name = name.strip()

        # Check name uniqueness among ACTIVE groups
        for g in self.groups:
            if g.is_active and g.name.lower() == name.lower():
                return (False, f"A group named '{name}' already exists", None)

        # Validate member count
        if not member_names or len(member_names) < MIN_GROUP_SIZE:
            return (False, f"Need at least {MIN_GROUP_SIZE} members", None)
        if len(member_names) > MAX_GROUP_SIZE:
            return (False, f"Max {MAX_GROUP_SIZE} members allowed", None)

        # Check for duplicates within the proposed group
        if len(member_names) != len(set(member_names)):
            return (False, "Cannot have the same wrestler twice in one group", None)

        # Check overlap rules for each proposed member
        for member in member_names:
            can_join, reason = self.can_wrestler_join_group_size(member, len(member_names))
            if not can_join:
                return (False, f"{member}: {reason}", None)

        # Generate unique ID
        safe_name = re.sub(r'[^a-z0-9]', '', name.lower())
        group_id = f"group_{safe_name}_{uuid.uuid4().hex[:6]}"

        # Validate leader (only for factions)
        is_faction = len(member_names) >= 4
        final_leader = ""
        if is_faction:
            if leader_id and leader_id in member_names:
                final_leader = leader_id
            else:
                final_leader = member_names[0]  # Default to first member

        group = Group(
            id=group_id,
            name=name,
            members=list(member_names),
            leader_id=final_leader,
            formed_year=formed_year,
            formed_week=formed_week,
            description=description,
            icon=icon,
            color=color or "#6366f1",
        )
        self.groups.append(group)

        return (True, f"{group.get_display_name()} formed!", group)

    # ==================== OVERLAP RULES ====================
    def can_wrestler_join_group_size(
        self,
        wrestler_name: str,
        proposed_group_size: int,
    ) -> Tuple[bool, str]:
        """
        Check if a wrestler can join a NEW group of the given size.
        Rules:
          - Can be in 1 Tag/Trio (size 2 or 3) AT MOST
          - Can be in 1 Faction (size 4+) AT MOST
          - Tag/Trio + Faction overlap is allowed
        """
        is_proposed_faction = proposed_group_size >= 4

        existing_groups = self.get_groups_for_wrestler(wrestler_name)
        for g in existing_groups:
            if g.is_faction() and is_proposed_faction:
                return (False, f"already in faction '{g.name}'")
            if not g.is_faction() and not is_proposed_faction:
                return (False, f"already in {g.group_type.value.lower()} '{g.name}'")

        return (True, "")

    def get_groups_for_wrestler(self, wrestler_name: str) -> List[Group]:
        """Returns all ACTIVE groups containing this wrestler."""
        return [
            g for g in self.groups
            if g.is_active and wrestler_name in g.members
        ]

    def get_tag_or_trio_for_wrestler(self, wrestler_name: str) -> Optional[Group]:
        """Returns the wrestler's tag team or trio (if any)."""
        for g in self.get_groups_for_wrestler(wrestler_name):
            if not g.is_faction():
                return g
        return None

    def get_faction_for_wrestler(self, wrestler_name: str) -> Optional[Group]:
        """Returns the wrestler's faction (if any)."""
        for g in self.get_groups_for_wrestler(wrestler_name):
            if g.is_faction():
                return g
        return None

    # ==================== QUERIES ====================
    def get_group(self, group_id: str) -> Optional[Group]:
        for g in self.groups:
            if g.id == group_id:
                return g
        return None

    def get_group_by_name(self, name: str) -> Optional[Group]:
        for g in self.groups:
            if g.is_active and g.name.lower() == name.lower():
                return g
        return None

    def get_all_groups(self) -> List[Group]:
        """All active groups."""
        return [g for g in self.groups if g.is_active]

    def get_tag_teams(self) -> List[Group]:
        return [g for g in self.groups if g.is_active and g.is_tag_team()]

    def get_trios(self) -> List[Group]:
        return [g for g in self.groups if g.is_active and g.is_trio()]

    def get_factions(self) -> List[Group]:
        return [g for g in self.groups if g.is_active and g.is_faction()]

    def get_active_count(self) -> int:
        return sum(1 for g in self.groups if g.is_active)

    def get_count_by_type(self) -> Dict[str, int]:
        return {
            "tag_teams": len(self.get_tag_teams()),
            "trios": len(self.get_trios()),
            "factions": len(self.get_factions()),
            "total": self.get_active_count(),
        }

    # ==================== EDITS ====================
    def rename_group(self, group_id: str, new_name: str) -> Tuple[bool, str]:
        """Rename a group."""
        group = self.get_group(group_id)
        if not group:
            return (False, "Group not found")
        if not new_name or not new_name.strip():
            return (False, "Name cannot be empty")
        new_name = new_name.strip()

        # Check uniqueness
        for g in self.groups:
            if g.is_active and g.id != group_id and g.name.lower() == new_name.lower():
                return (False, f"A group named '{new_name}' already exists")

        old_name = group.name
        group.name = new_name
        return (True, f"Renamed '{old_name}' to '{new_name}'")

    def add_member_to_group(
        self,
        group_id: str,
        wrestler_name: str,
    ) -> Tuple[bool, str]:
        """Add a member to an existing group, respecting overlap rules."""
        group = self.get_group(group_id)
        if not group:
            return (False, "Group not found")
        if not group.is_active:
            return (False, "Cannot modify a disbanded group")

        # Check overlap based on what the group WILL be after adding
        new_size = len(group.members) + 1
        if new_size > MAX_GROUP_SIZE:
            return (False, f"Group already at max size ({MAX_GROUP_SIZE})")

        # Determine target group's type AFTER adding
        will_be_faction = new_size >= 4
        # Check the wrestler isn't in another group of the same general type
        for g in self.get_groups_for_wrestler(wrestler_name):
            if g.id == group_id:
                return (False, f"{wrestler_name} is already in this group")
            if g.is_faction() and will_be_faction:
                return (False, f"{wrestler_name} is already in faction '{g.name}'")
            if not g.is_faction() and not will_be_faction:
                return (False, f"{wrestler_name} is already in {g.group_type.value.lower()} '{g.name}'")

        return group.add_member(wrestler_name)

    def remove_member_from_group(
        self,
        group_id: str,
        wrestler_name: str,
    ) -> Tuple[bool, str]:
        """
        Remove a member from a group.
        If group falls below minimum size (2), auto-disband.
        """
        group = self.get_group(group_id)
        if not group:
            return (False, "Group not found")
        if not group.is_active:
            return (False, "Cannot modify a disbanded group")

        success, msg = group.remove_member(wrestler_name)
        if not success:
            return (False, msg)

        # Auto-disband if below minimum
        if not group.is_valid():
            self.disband_group(group_id, reason=f"Fell below minimum size after losing {wrestler_name}")
            return (True, f"{msg}. Group disbanded (below minimum size).")

        return (True, msg)

    def set_faction_leader(
        self,
        group_id: str,
        wrestler_name: str,
    ) -> Tuple[bool, str]:
        """Change a faction's leader."""
        group = self.get_group(group_id)
        if not group:
            return (False, "Group not found")
        if not group.is_active:
            return (False, "Cannot modify a disbanded group")
        return group.set_leader(wrestler_name)

    # ==================== DISBANDING ====================
    def disband_group(
        self,
        group_id: str,
        reason: str = "Disbanded by management",
        year: int = 0,
        week: int = 0,
    ) -> Tuple[bool, str]:
        """
        Disband a group. Moves to archive but doesn't delete (preserves history).
        """
        group = self.get_group(group_id)
        if not group:
            return (False, "Group not found")
        if not group.is_active:
            return (False, "Group is already disbanded")

        group.is_active = False
        group.disbanded_year = year
        group.disbanded_week = week
        group.disband_reason = reason

        # Move to archive (but keep in main list with is_active=False so we can still
        # find it by ID for history lookups)
        return (True, f"{group.name} has disbanded")

    # ==================== AUTO-CLEANUP ====================
    def remove_wrestler_from_all_groups(self, wrestler_name: str) -> List[str]:
        """
        Called when a wrestler is released, retired, or otherwise removed from the roster.
        Returns list of messages describing what happened.
        """
        messages = []
        affected_groups = self.get_groups_for_wrestler(wrestler_name)

        for group in affected_groups:
            success, msg = self.remove_member_from_group(group.id, wrestler_name)
            if success:
                messages.append(msg)

        return messages

    # ==================== STAT BONUS LOOKUPS ====================
    def get_chemistry_bonus_for_match(self, wrestler_names: List[str]) -> float:
        """
        Calculate the maximum chemistry bonus available for a match.
        Checks if any of the participating wrestlers form a complete tag team or trio.

        e.g., if wrestlers ["Roman", "Solo"] are in a tag team together,
        a 2v2 match featuring them gets +3% bonus.
        """
        if not wrestler_names:
            return 0.0

        wrestler_set = set(wrestler_names)

        # Check tag teams (need both members present)
        for g in self.get_tag_teams():
            if set(g.members).issubset(wrestler_set):
                return g.get_chemistry_bonus()

        # Check trios (need all 3 present)
        for g in self.get_trios():
            if set(g.members).issubset(wrestler_set):
                return g.get_chemistry_bonus()

        return 0.0

    def get_total_member_bonus(self, wrestler_name: str) -> float:
        """
        Get the total stat bonus for a single wrestler from faction membership.
        (Tag/Trio bonuses are match-wide, not per-wrestler.)
        """
        faction = self.get_faction_for_wrestler(wrestler_name)
        if not faction:
            return 0.0
        return faction.get_member_bonus(wrestler_name)

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        return {
            "groups": [g.to_dict() for g in self.groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupManager":
        manager = cls()
        for gd in data.get("groups", []):
            try:
                manager.groups.append(Group.from_dict(gd))
            except Exception as e:
                print(f"Group restore error: {e}")
        return manager
