"""
Quest System - Player goals, objectives, and rewards
Integrates with AI Director for personality-driven quest pitches
Connects to Storyline Engine, News Generator, and Achievement system
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# ==================== QUEST ENUMS ====================

class QuestType(Enum):
    BUILD_STAR = "Build Star"
    RIVALRY = "Create Rivalry"
    SELLOUT = "Sellout Venue"
    FIVE_STAR = "Five Star Match"
    FINANCIAL = "Financial Goal"
    FANS = "Fan Goal"
    TITLE_PRESTIGE = "Build Title Prestige"
    STORYLINE = "Complete Storyline"
    TV_DEAL = "Get TV Deal"
    SURVIVE = "Survive Period"
    WIN_STREAK = "Win Streak"
    SHOW_QUALITY = "Show Quality"
    HEEL_TURN = "Execute Heel Turn"
    FACE_TURN = "Execute Face Turn"
    DEFEAT_RIVAL = "Defeat Rival Promotion"


class QuestStatus(Enum):
    AVAILABLE = "Available"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    FAILED = "Failed"
    EXPIRED = "Expired"


class QuestDifficulty(Enum):
    EASY = "Easy"
    NORMAL = "Normal"
    HARD = "Hard"
    LEGENDARY = "Legendary"


class QuestSource(Enum):
    SYSTEM = "System Generated"
    AI_DIRECTOR = "AI Director Pitch"
    STORYLINE = "Storyline Linked"
    MILESTONE = "Milestone Triggered"


# ==================== QUEST CLASS ====================

@dataclass
class Quest:
    """A quest/objective for the player"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty = QuestDifficulty.NORMAL
    status: QuestStatus = QuestStatus.AVAILABLE
    source: QuestSource = QuestSource.SYSTEM

    # Requirements
    target_value: int = 0
    current_value: int = 0
    target_wrestler: str = ""
    target_venue: str = ""
    target_storyline_id: str = ""
    secondary_target: str = ""

    # Time limit
    duration_weeks: int = 12
    weeks_remaining: int = 12
    week_started: int = 0
    year_started: int = 1

    # Rewards
    xp_reward: int = 100
    money_reward: int = 0
    fans_reward: int = 0
    prestige_reward: int = 0

    # Penalties for failure
    prestige_penalty: int = 0
    fans_penalty: int = 0
    money_penalty: int = 0

    # AI integration
    ai_personality_pitch: str = ""  # The AI's voice when pitching
    ai_personality_name: str = ""

    # Tracking
    is_repeatable: bool = False
    times_completed: int = 0
    icon: str = "🎯"
    color: str = "#3b82f6"

    def start(self, current_week: int, current_year: int = 1):
        """Start the quest"""
        self.status = QuestStatus.ACTIVE
        self.week_started = current_week
        self.year_started = current_year
        self.weeks_remaining = self.duration_weeks

    def update_progress(self, new_value: int):
        """Update quest progress to absolute value"""
        self.current_value = new_value
        if self.current_value >= self.target_value:
            self.complete()

    def add_progress(self, amount: int):
        """Add to quest progress"""
        self.current_value += amount
        if self.current_value >= self.target_value:
            self.complete()

    def complete(self):
        """Mark quest as completed"""
        self.status = QuestStatus.COMPLETED
        self.times_completed += 1

    def fail(self):
        """Mark quest as failed"""
        self.status = QuestStatus.FAILED

    def tick_week(self):
        """Process a week passing"""
        if self.status == QuestStatus.ACTIVE:
            self.weeks_remaining -= 1
            if self.weeks_remaining <= 0 and self.current_value < self.target_value:
                self.fail()

    def get_progress_percentage(self) -> float:
        """Get progress as percentage (0-100)"""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def get_time_percentage(self) -> float:
        """Get time remaining as percentage"""
        if self.duration_weeks == 0:
            return 0.0
        return (self.weeks_remaining / self.duration_weeks) * 100

    def get_difficulty_color(self) -> str:
        colors = {
            QuestDifficulty.EASY: "#10b981",
            QuestDifficulty.NORMAL: "#3b82f6",
            QuestDifficulty.HARD: "#f59e0b",
            QuestDifficulty.LEGENDARY: "#dc2626",
        }
        return colors.get(self.difficulty, "#6b7280")

    def get_status_color(self) -> str:
        colors = {
            QuestStatus.AVAILABLE: "#3b82f6",
            QuestStatus.ACTIVE: "#f59e0b",
            QuestStatus.COMPLETED: "#10b981",
            QuestStatus.FAILED: "#dc2626",
            QuestStatus.EXPIRED: "#6b7280",
        }
        return colors.get(self.status, "#6b7280")

    def get_urgency(self) -> str:
        """Get urgency string based on weeks remaining"""
        if self.status != QuestStatus.ACTIVE:
            return ""
        if self.weeks_remaining <= 2:
            return "🚨 URGENT"
        if self.weeks_remaining <= 4:
            return "⚠️ Soon"
        return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "quest_type": self.quest_type.value,
            "difficulty": self.difficulty.value,
            "status": self.status.value,
            "source": self.source.value,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "target_wrestler": self.target_wrestler,
            "target_venue": self.target_venue,
            "target_storyline_id": self.target_storyline_id,
            "secondary_target": self.secondary_target,
            "duration_weeks": self.duration_weeks,
            "weeks_remaining": self.weeks_remaining,
            "week_started": self.week_started,
            "year_started": self.year_started,
            "xp_reward": self.xp_reward,
            "money_reward": self.money_reward,
            "fans_reward": self.fans_reward,
            "prestige_reward": self.prestige_reward,
            "prestige_penalty": self.prestige_penalty,
            "fans_penalty": self.fans_penalty,
            "money_penalty": self.money_penalty,
            "ai_personality_pitch": self.ai_personality_pitch,
            "ai_personality_name": self.ai_personality_name,
            "is_repeatable": self.is_repeatable,
            "times_completed": self.times_completed,
            "icon": self.icon,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        try:
            qt = QuestType(data["quest_type"])
        except (ValueError, KeyError):
            qt = QuestType.FANS
        try:
            diff = QuestDifficulty(data.get("difficulty", "Normal"))
        except ValueError:
            diff = QuestDifficulty.NORMAL
        try:
            status = QuestStatus(data.get("status", "Available"))
        except ValueError:
            status = QuestStatus.AVAILABLE
        try:
            source = QuestSource(data.get("source", "System Generated"))
        except ValueError:
            source = QuestSource.SYSTEM

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            quest_type=qt,
            difficulty=diff,
            status=status,
            source=source,
            target_value=data.get("target_value", 0),
            current_value=data.get("current_value", 0),
            target_wrestler=data.get("target_wrestler", ""),
            target_venue=data.get("target_venue", ""),
            target_storyline_id=data.get("target_storyline_id", ""),
            secondary_target=data.get("secondary_target", ""),
            duration_weeks=data.get("duration_weeks", 12),
            weeks_remaining=data.get("weeks_remaining", 12),
            week_started=data.get("week_started", 0),
            year_started=data.get("year_started", 1),
            xp_reward=data.get("xp_reward", 100),
            money_reward=data.get("money_reward", 0),
            fans_reward=data.get("fans_reward", 0),
            prestige_reward=data.get("prestige_reward", 0),
            prestige_penalty=data.get("prestige_penalty", 0),
            fans_penalty=data.get("fans_penalty", 0),
            money_penalty=data.get("money_penalty", 0),
            ai_personality_pitch=data.get("ai_personality_pitch", ""),
            ai_personality_name=data.get("ai_personality_name", ""),
            is_repeatable=data.get("is_repeatable", False),
            times_completed=data.get("times_completed", 0),
            icon=data.get("icon", "🎯"),
            color=data.get("color", "#3b82f6"),
        )


# ==================== QUEST SYSTEM MANAGER ====================

class QuestSystem:
    """Manages all quests for the player"""

    def __init__(self):
        self.available_quests: List[Quest] = []
        self.active_quests: List[Quest] = []
        self.completed_quests: List[Quest] = []
        self.failed_quests: List[Quest] = []
        self.max_active_quests: int = 3
        self.next_id: int = 1

    def _next_quest_id(self, prefix: str = "quest") -> str:
        qid = f"{prefix}_{self.next_id}"
        self.next_id += 1
        return qid

    # ==================== QUEST GENERATION ====================

    def generate_random_quests(
        self,
        current_week: int,
        current_year: int = 1,
        fans: int = 1000,
        budget: int = 50000,
        prestige: int = 50,
        roster: List[Dict] = None,
        count: int = 3,
    ) -> List[Quest]:
        """Generate random available quests based on game state"""
        quest_types = [
            QuestType.FANS,
            QuestType.FINANCIAL,
            QuestType.FIVE_STAR,
            QuestType.SELLOUT,
            QuestType.SHOW_QUALITY,
        ]
        if roster and len(roster) > 0:
            quest_types.append(QuestType.BUILD_STAR)
            quest_types.append(QuestType.WIN_STREAK)

        generated = []
        for _ in range(count):
            quest_type = random.choice(quest_types)
            quest = self._generate_quest(
                quest_type, current_week, current_year,
                fans=fans, budget=budget, prestige=prestige, roster=roster
            )
            if quest:
                generated.append(quest)
                self.available_quests.append(quest)

        return generated

    def _generate_quest(
        self,
        quest_type: QuestType,
        current_week: int,
        current_year: int = 1,
        **context
    ) -> Optional[Quest]:
        """Generate a specific type of quest"""
        generators = {
            QuestType.FANS: self._generate_fans_quest,
            QuestType.FINANCIAL: self._generate_financial_quest,
            QuestType.FIVE_STAR: self._generate_five_star_quest,
            QuestType.SELLOUT: self._generate_sellout_quest,
            QuestType.BUILD_STAR: self._generate_build_star_quest,
            QuestType.SHOW_QUALITY: self._generate_show_quality_quest,
            QuestType.WIN_STREAK: self._generate_win_streak_quest,
            QuestType.RIVALRY: self._generate_rivalry_quest,
        }
        generator = generators.get(quest_type)
        if generator:
            return generator(current_week, current_year, context)
        return None

    def _generate_fans_quest(self, current_week: int, current_year: int, context: Dict) -> Quest:
        current_fans = context.get("fans", 1000)
        multiplier = random.uniform(1.3, 1.8)
        target = int(current_fans * multiplier)
        difficulty = QuestDifficulty.NORMAL
        if multiplier > 1.6:
            difficulty = QuestDifficulty.HARD
        elif multiplier < 1.4:
            difficulty = QuestDifficulty.EASY

        return Quest(
            id=self._next_quest_id("fans"),
            title="Grow Your Fanbase",
            description=f"Reach {target:,} fans. Put on great shows and spread the word!",
            quest_type=QuestType.FANS,
            difficulty=difficulty,
            target_value=target,
            current_value=current_fans,
            duration_weeks=12,
            weeks_remaining=12,
            xp_reward=200 + int((multiplier - 1.3) * 400),
            fans_reward=int(target * 0.1),
            is_repeatable=True,
            icon="👥",
            color="#3b82f6",
        )

    def _generate_financial_quest(self, current_week: int, current_year: int, context: Dict) -> Quest:
        current_budget = context.get("budget", 50000)
        multiplier = random.uniform(1.5, 2.5)
        target = int(current_budget * multiplier)
        difficulty = QuestDifficulty.NORMAL
        if multiplier > 2.0:
            difficulty = QuestDifficulty.HARD
        elif multiplier < 1.7:
            difficulty = QuestDifficulty.EASY

        return Quest(
            id=self._next_quest_id("money"),
            title="Build Your War Chest",
            description=f"Reach a budget of ${target:,}. Manage your finances wisely!",
            quest_type=QuestType.FINANCIAL,
            difficulty=difficulty,
            target_value=target,
            current_value=current_budget,
            duration_weeks=16,
            weeks_remaining=16,
            xp_reward=300 + int((multiplier - 1.5) * 300),
            money_reward=int(target * 0.1),
            is_repeatable=True,
            icon="💰",
            color="#10b981",
        )

    def _generate_five_star_quest(self, current_week: int, current_year: int, context: Dict) -> Quest:
        return Quest(
            id=self._next_quest_id("fivestar"),
            title="Match of the Year Candidate",
            description="Produce a 5-star match. Book the right wrestlers in the right match!",
            quest_type=QuestType.FIVE_STAR,
            difficulty=QuestDifficulty.HARD,
            target_value=1,
            current_value=0,
            duration_weeks=8,
            weeks_remaining=8,
            xp_reward=500,
            prestige_reward=10,
            fans_reward=500,
            icon="⭐",
            color="#fbbf24",
        )

    def _generate_sellout_quest(self, current_week: int, current_year: int, context: Dict) -> Quest:
        return Quest(
            id=self._next_quest_id("sellout"),
            title="Fill The House",
            description="Sell out a venue. Build hype and deliver a great card!",
            quest_type=QuestType.SELLOUT,
            difficulty=QuestDifficulty.NORMAL,
            target_value=1,
            current_value=0,
            duration_weeks=6,
            weeks_remaining=6,
            xp_reward=250,
            fans_reward=300,
            prestige_reward=5,
            is_repeatable=True,
            icon="🏟️",
            color="#8b5cf6",
        )

    def _generate_build_star_quest(self, current_week: int, current_year: int, context: Dict) -> Optional[Quest]:
        roster = context.get("roster", [])
        if not roster:
            return None
        candidates = [
            w for w in roster
            if 30 < w.get("popularity", 50) < 70
            and not w.get("is_injured")
        ]
        if not candidates:
            return None

        wrestler = random.choice(candidates)
        wrestler_name = wrestler.get("name", "Unknown")
        current_pop = wrestler.get("popularity", 50)
        target_pop = min(90, current_pop + random.randint(15, 25))

        return Quest(
            id=self._next_quest_id(f"star_{wrestler_name}"),
            title=f"Star Maker: {wrestler_name}",
            description=f"Build {wrestler_name} into a main event talent. Get their popularity to {target_pop}!",
            quest_type=QuestType.BUILD_STAR,
            difficulty=QuestDifficulty.HARD,
            target_value=target_pop,
            current_value=current_pop,
            target_wrestler=wrestler_name,
            duration_weeks=16,
            weeks_remaining=16,
            xp_reward=400,
            prestige_reward=8,
            icon="🌟",
            color="#f59e0b",
        )

    def _generate_show_quality_quest(self, current_week: int, current_year: int, context: Dict) -> Quest:
        target_rating = random.choice([3.5, 4.0, 4.5])
        difficulty = QuestDifficulty.NORMAL
        if target_rating >= 4.5:
            difficulty = QuestDifficulty.LEGENDARY
        elif target_rating >= 4.0:
            difficulty = QuestDifficulty.HARD

        return Quest(
            id=self._next_quest_id("quality"),
            title="Quality Wrestling",
            description=f"Run a show with an average match rating of {target_rating}+ stars!",
            quest_type=QuestType.SHOW_QUALITY,
            difficulty=difficulty,
            target_value=int(target_rating * 10),
            current_value=0,
            duration_weeks=4,
            weeks_remaining=4,
            xp_reward=int(200 + (target_rating - 3.5) * 300),
            prestige_reward=int(5 + (target_rating - 3.5) * 10),
            icon="📺",
            color="#a855f7",
        )

    def _generate_win_streak_quest(self, current_week: int, current_year: int, context: Dict) -> Optional[Quest]:
        roster = context.get("roster", [])
        if not roster:
            return None
        candidates = [w for w in roster if not w.get("is_injured")]
        if not candidates:
            return None

        wrestler = random.choice(candidates)
        target = random.choice([5, 8, 10])

        return Quest(
            id=self._next_quest_id(f"streak_{wrestler['name']}"),
            title=f"Win Streak: {wrestler['name']}",
            description=f"Get {wrestler['name']} to a {target}-match win streak!",
            quest_type=QuestType.WIN_STREAK,
            difficulty=QuestDifficulty.HARD if target >= 8 else QuestDifficulty.NORMAL,
            target_value=target,
            current_value=0,
            target_wrestler=wrestler["name"],
            duration_weeks=12,
            weeks_remaining=12,
            xp_reward=250 + (target * 30),
            prestige_reward=target,
            icon="🔥",
            color="#ef4444",
        )

    def _generate_rivalry_quest(self, current_week: int, current_year: int, context: Dict) -> Optional[Quest]:
        return Quest(
            id=self._next_quest_id("rivalry"),
            title="Create a Heated Rivalry",
            description="Create a storyline rivalry and build it to peak heat (80+)!",
            quest_type=QuestType.RIVALRY,
            difficulty=QuestDifficulty.HARD,
            target_value=80,
            current_value=0,
            duration_weeks=10,
            weeks_remaining=10,
            xp_reward=400,
            prestige_reward=10,
            fans_reward=300,
            icon="⚔️",
            color="#dc2626",
        )

    # ==================== AI DIRECTOR INTEGRATION ====================

    def generate_ai_pitched_quest(
        self,
        ai_director,
        current_week: int,
        current_year: int,
        roster: List[Dict],
        fans: int,
        budget: int,
    ) -> Optional[Quest]:
        """Have the AI Director pitch a quest with personality voice"""
        if not ai_director:
            return None

        if not ai_director.personality:
            return None

        personality = ai_director.personality
        personality_type_str = personality.get_name().replace("The ", "")

        # Personality-driven quest preferences
        if personality_type_str == "Showman":
            quest_types = [QuestType.SELLOUT, QuestType.FIVE_STAR, QuestType.FANS, QuestType.RIVALRY]
        elif personality_type_str == "Mastermind":
            quest_types = [QuestType.FINANCIAL, QuestType.BUILD_STAR, QuestType.FANS, QuestType.SHOW_QUALITY]
        elif personality_type_str == "Mad Scientist":
            quest_types = [QuestType.BUILD_STAR, QuestType.FIVE_STAR, QuestType.RIVALRY]
        else:  # Traditionalist
            quest_types = [QuestType.SHOW_QUALITY, QuestType.BUILD_STAR, QuestType.FINANCIAL, QuestType.WIN_STREAK]

        quest_type = random.choice(quest_types)
        quest = self._generate_quest(
            quest_type, current_week, current_year,
            fans=fans, budget=budget, roster=roster
        )

        if quest:
            quest.source = QuestSource.AI_DIRECTOR
            quest.ai_personality_name = personality.get_name()

            greeting = personality.get_greeting()
            sign_off = personality.get_sign_off()
            quest.ai_personality_pitch = f"{greeting}\n\n{quest.description}\n\n{sign_off}"

            # Add to available quests
            self.available_quests.append(quest)

        return quest

    # ==================== STORYLINE INTEGRATION ====================

    def generate_storyline_quest(
        self,
        storyline,
        current_week: int,
        current_year: int,
    ) -> Optional[Quest]:
        """Create a quest tied to an active storyline"""
        if not storyline:
            return None

        target_heat = 80
        current_heat = storyline.heat

        quest = Quest(
            id=self._next_quest_id(f"storyline_{storyline.id}"),
            title=f"Build Storyline: {storyline.name}",
            description=f"Build the {storyline.name} storyline to peak heat ({target_heat}+)!",
            quest_type=QuestType.STORYLINE,
            difficulty=QuestDifficulty.HARD,
            source=QuestSource.STORYLINE,
            target_value=target_heat,
            current_value=current_heat,
            target_storyline_id=storyline.id,
            duration_weeks=8,
            weeks_remaining=8,
            xp_reward=350,
            prestige_reward=8,
            fans_reward=200,
            icon=storyline.get_icon(),
            color=storyline.get_heat_color(),
        )

        self.available_quests.append(quest)
        return quest

    # ==================== QUEST LIFECYCLE ====================

    def accept_quest(self, quest_id: str, current_week: int, current_year: int = 1) -> bool:
        """Accept a quest from available quests"""
        if len(self.active_quests) >= self.max_active_quests:
            return False

        for quest in self.available_quests:
            if quest.id == quest_id:
                quest.start(current_week, current_year)
                self.available_quests.remove(quest)
                self.active_quests.append(quest)
                return True
        return False

    def abandon_quest(self, quest_id: str) -> bool:
        """Abandon an active quest"""
        for quest in self.active_quests:
            if quest.id == quest_id:
                quest.status = QuestStatus.FAILED
                self.active_quests.remove(quest)
                self.failed_quests.append(quest)
                return True
        return False

    def reject_available_quest(self, quest_id: str) -> bool:
        """Remove an available quest without accepting it"""
        for quest in self.available_quests:
            if quest.id == quest_id:
                self.available_quests.remove(quest)
                return True
        return False

    def check_progress(self, storyline_engine=None, **current_values) -> List[Dict]:
        """Check progress on all active quests"""
        updates = []

        for quest in self.active_quests[:]:
            old_value = quest.current_value
            old_status = quest.status

            # Update based on quest type
            if quest.quest_type == QuestType.FANS:
                quest.update_progress(current_values.get("fans", 0))
            elif quest.quest_type == QuestType.FINANCIAL:
                quest.update_progress(current_values.get("budget", 0))
            elif quest.quest_type == QuestType.SELLOUT:
                if current_values.get("had_sellout"):
                    quest.add_progress(1)
            elif quest.quest_type == QuestType.FIVE_STAR:
                if current_values.get("five_star_matches", 0) > 0:
                    quest.add_progress(current_values.get("five_star_matches", 0))
            elif quest.quest_type == QuestType.SHOW_QUALITY:
                show_rating = current_values.get("show_rating", 0)
                if show_rating * 10 >= quest.target_value:
                    quest.complete()
            elif quest.quest_type == QuestType.BUILD_STAR:
                wrestler_pop = current_values.get(f"popularity_{quest.target_wrestler}", 0)
                if wrestler_pop > 0:
                    quest.update_progress(wrestler_pop)
            elif quest.quest_type == QuestType.WIN_STREAK:
                streak = current_values.get(f"streak_{quest.target_wrestler}", 0)
                if streak > 0:
                    quest.update_progress(streak)
            elif quest.quest_type == QuestType.RIVALRY and storyline_engine:
                # Check if any active storyline has hit peak heat
                active = storyline_engine.get_active_storylines()
                if active:
                    max_heat = max(sl.heat for sl in active)
                    quest.update_progress(max_heat)
            elif quest.quest_type == QuestType.STORYLINE and storyline_engine:
                sl = storyline_engine.get_storyline(quest.target_storyline_id)
                if sl:
                    quest.update_progress(sl.heat)

            # Tick week
            quest.tick_week()

            # Record progress changes
            if quest.current_value != old_value:
                updates.append({
                    "quest_id": quest.id,
                    "quest_title": quest.title,
                    "old_value": old_value,
                    "new_value": quest.current_value,
                    "target": quest.target_value,
                    "progress": quest.get_progress_percentage(),
                })

            # Check status changes
            if quest.status != old_status:
                if quest.status == QuestStatus.COMPLETED:
                    self.active_quests.remove(quest)
                    self.completed_quests.append(quest)
                    updates.append({
                        "quest_id": quest.id,
                        "quest_title": quest.title,
                        "status": "completed",
                        "rewards": {
                            "xp": quest.xp_reward,
                            "money": quest.money_reward,
                            "fans": quest.fans_reward,
                            "prestige": quest.prestige_reward,
                        }
                    })
                elif quest.status == QuestStatus.FAILED:
                    self.active_quests.remove(quest)
                    self.failed_quests.append(quest)
                    updates.append({
                        "quest_id": quest.id,
                        "quest_title": quest.title,
                        "status": "failed",
                        "penalties": {
                            "prestige": quest.prestige_penalty,
                            "fans": quest.fans_penalty,
                            "money": quest.money_penalty,
                        }
                    })

        return updates

    # ==================== QUERIES ====================

    def get_active_quest_count(self) -> int:
        return len(self.active_quests)

    def get_available_quest_count(self) -> int:
        return len(self.available_quests)

    def can_accept_quest(self) -> bool:
        return len(self.active_quests) < self.max_active_quests

    def get_completed_count(self) -> int:
        return len(self.completed_quests)

    def get_completion_rate(self) -> float:
        total = len(self.completed_quests) + len(self.failed_quests)
        if total == 0:
            return 0.0
        return (len(self.completed_quests) / total) * 100

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        for q in self.available_quests + self.active_quests + self.completed_quests + self.failed_quests:
            if q.id == quest_id:
                return q
        return None

    def get_active_quests_for_wrestler(self, wrestler_name: str) -> List[Quest]:
        return [q for q in self.active_quests if q.target_wrestler == wrestler_name]

    def get_ai_pitched_quests(self) -> List[Quest]:
        """Get quests pitched by the AI Director"""
        return [q for q in self.available_quests if q.source == QuestSource.AI_DIRECTOR]

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "available_quests": [q.to_dict() for q in self.available_quests],
            "active_quests": [q.to_dict() for q in self.active_quests],
            "completed_quests": [q.to_dict() for q in self.completed_quests[-50:]],
            "failed_quests": [q.to_dict() for q in self.failed_quests[-50:]],
            "max_active_quests": self.max_active_quests,
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestSystem":
        system = cls()
        system.next_id = data.get("next_id", 1)
        system.max_active_quests = data.get("max_active_quests", 3)
        for q in data.get("available_quests", []):
            try:
                system.available_quests.append(Quest.from_dict(q))
            except Exception:
                pass
        for q in data.get("active_quests", []):
            try:
                system.active_quests.append(Quest.from_dict(q))
            except Exception:
                pass
        for q in data.get("completed_quests", []):
            try:
                system.completed_quests.append(Quest.from_dict(q))
            except Exception:
                pass
        for q in data.get("failed_quests", []):
            try:
                system.failed_quests.append(Quest.from_dict(q))
            except Exception:
                pass
        return system
