"""
Quest System - Side quests and objectives for players
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import random


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


@dataclass
class Quest:
    """A quest/objective for the player"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty = QuestDifficulty.NORMAL
    status: QuestStatus = QuestStatus.AVAILABLE
    
    # Requirements
    target_value: int = 0
    current_value: int = 0
    target_wrestler: str = ""
    target_venue: str = ""
    secondary_target: str = ""
    
    # Time limit
    duration_weeks: int = 12
    weeks_remaining: int = 12
    week_started: int = 0
    
    # Rewards
    xp_reward: int = 100
    money_reward: int = 0
    fans_reward: int = 0
    prestige_reward: int = 0
    
    # Penalties for failure
    prestige_penalty: int = 0
    fans_penalty: int = 0
    
    # Tracking
    is_repeatable: bool = False
    times_completed: int = 0
    
    def start(self, current_week: int):
        """Start the quest"""
        self.status = QuestStatus.ACTIVE
        self.week_started = current_week
        self.weeks_remaining = self.duration_weeks
    
    def update_progress(self, new_value: int):
        """Update quest progress"""
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
        """Get progress as percentage"""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)
    
    def get_time_percentage(self) -> float:
        """Get time remaining as percentage"""
        if self.duration_weeks == 0:
            return 0.0
        return (self.weeks_remaining / self.duration_weeks) * 100
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "quest_type": self.quest_type.value,
            "difficulty": self.difficulty.value,
            "status": self.status.value,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "target_wrestler": self.target_wrestler,
            "target_venue": self.target_venue,
            "secondary_target": self.secondary_target,
            "duration_weeks": self.duration_weeks,
            "weeks_remaining": self.weeks_remaining,
            "week_started": self.week_started,
            "xp_reward": self.xp_reward,
            "money_reward": self.money_reward,
            "fans_reward": self.fans_reward,
            "prestige_reward": self.prestige_reward,
            "prestige_penalty": self.prestige_penalty,
            "fans_penalty": self.fans_penalty,
            "is_repeatable": self.is_repeatable,
            "times_completed": self.times_completed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            quest_type=QuestType(data["quest_type"]),
            difficulty=QuestDifficulty(data.get("difficulty", "Normal")),
            status=QuestStatus(data.get("status", "Available")),
            target_value=data.get("target_value", 0),
            current_value=data.get("current_value", 0),
            target_wrestler=data.get("target_wrestler", ""),
            target_venue=data.get("target_venue", ""),
            secondary_target=data.get("secondary_target", ""),
            duration_weeks=data.get("duration_weeks", 12),
            weeks_remaining=data.get("weeks_remaining", 12),
            week_started=data.get("week_started", 0),
            xp_reward=data.get("xp_reward", 100),
            money_reward=data.get("money_reward", 0),
            fans_reward=data.get("fans_reward", 0),
            prestige_reward=data.get("prestige_reward", 0),
            prestige_penalty=data.get("prestige_penalty", 0),
            fans_penalty=data.get("fans_penalty", 0),
            is_repeatable=data.get("is_repeatable", False),
            times_completed=data.get("times_completed", 0),
        )


class QuestSystem:
    """Manages all quests for the player"""
    
    def __init__(self):
        self.available_quests: List[Quest] = []
        self.active_quests: List[Quest] = []
        self.completed_quests: List[Quest] = []
        self.failed_quests: List[Quest] = []
        self.max_active_quests: int = 3
    
    def generate_random_quests(
        self,
        current_week: int,
        fans: int = 1000,
        budget: int = 50000,
        prestige: int = 50,
        roster: List[Dict] = None,
        count: int = 3
    ) -> List[Quest]:
        """Generate random available quests"""
        quest_types = [
            QuestType.FANS,
            QuestType.FINANCIAL,
            QuestType.FIVE_STAR,
            QuestType.SELLOUT,
            QuestType.SHOW_QUALITY,
        ]
        
        if roster and len(roster) > 0:
            quest_types.append(QuestType.BUILD_STAR)
        
        generated = []
        
        for _ in range(count):
            quest_type = random.choice(quest_types)
            quest = self._generate_quest(
                quest_type, current_week,
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
        }
        
        generator = generators.get(quest_type)
        if generator:
            return generator(current_week, context)
        return None
    
    def _generate_fans_quest(self, current_week: int, context: Dict) -> Quest:
        """Generate a fans quest"""
        current_fans = context.get("fans", 1000)
        multiplier = random.uniform(1.3, 1.8)
        target = int(current_fans * multiplier)
        
        difficulty = QuestDifficulty.NORMAL
        if multiplier > 1.6:
            difficulty = QuestDifficulty.HARD
        elif multiplier < 1.4:
            difficulty = QuestDifficulty.EASY
        
        return Quest(
            id=f"fans_{current_week}_{random.randint(1000, 9999)}",
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
        )
    
    def _generate_financial_quest(self, current_week: int, context: Dict) -> Quest:
        """Generate a financial quest"""
        current_budget = context.get("budget", 50000)
        multiplier = random.uniform(1.5, 2.5)
        target = int(current_budget * multiplier)
        
        difficulty = QuestDifficulty.NORMAL
        if multiplier > 2.0:
            difficulty = QuestDifficulty.HARD
        elif multiplier < 1.7:
            difficulty = QuestDifficulty.EASY
        
        return Quest(
            id=f"money_{current_week}_{random.randint(1000, 9999)}",
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
        )
    
    def _generate_five_star_quest(self, current_week: int, context: Dict) -> Quest:
        """Generate a five star match quest"""
        return Quest(
            id=f"fivestar_{current_week}_{random.randint(1000, 9999)}",
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
        )
    
    def _generate_sellout_quest(self, current_week: int, context: Dict) -> Quest:
        """Generate a sellout quest"""
        return Quest(
            id=f"sellout_{current_week}_{random.randint(1000, 9999)}",
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
        )
    
    def _generate_build_star_quest(self, current_week: int, context: Dict) -> Optional[Quest]:
        """Generate a build a star quest"""
        roster = context.get("roster", [])
        if not roster:
            return None
        
        # Find a mid-card wrestler to push
        candidates = [
            w for w in roster
            if w.get("popularity", 50) < 70
            and w.get("popularity", 50) > 30
            and not w.get("is_injured")
        ]
        
        if not candidates:
            return None
        
        wrestler = random.choice(candidates)
        wrestler_name = wrestler.get("name", "Unknown")
        current_pop = wrestler.get("popularity", 50)
        target_pop = min(90, current_pop + random.randint(15, 25))
        
        return Quest(
            id=f"star_{wrestler_name}_{current_week}_{random.randint(1000, 9999)}",
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
        )
    
    def _generate_show_quality_quest(self, current_week: int, context: Dict) -> Quest:
        """Generate a show quality quest"""
        target_rating = random.choice([3.5, 4.0, 4.5])
        
        difficulty = QuestDifficulty.NORMAL
        if target_rating >= 4.5:
            difficulty = QuestDifficulty.LEGENDARY
        elif target_rating >= 4.0:
            difficulty = QuestDifficulty.HARD
        
        return Quest(
            id=f"quality_{current_week}_{random.randint(1000, 9999)}",
            title="Quality Wrestling",
            description=f"Run a show with an average match rating of {target_rating}+ stars!",
            quest_type=QuestType.SHOW_QUALITY,
            difficulty=difficulty,
            target_value=int(target_rating * 10),  # Store as integer (35, 40, 45)
            current_value=0,
            duration_weeks=4,
            weeks_remaining=4,
            xp_reward=int(200 + (target_rating - 3.5) * 300),
            prestige_reward=int(5 + (target_rating - 3.5) * 10),
        )
    
    def accept_quest(self, quest_id: str, current_week: int) -> bool:
        """Accept a quest from available quests"""
        if len(self.active_quests) >= self.max_active_quests:
            return False
        
        for quest in self.available_quests:
            if quest.id == quest_id:
                quest.start(current_week)
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
    
    def check_progress(self, **current_values) -> List[Dict]:
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
            
            # Tick week
            quest.tick_week()
            
            # Record updates
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
                        }
                    })
        
        return updates
    
    def get_active_quest_count(self) -> int:
        """Get number of active quests"""
        return len(self.active_quests)
    
    def can_accept_quest(self) -> bool:
        """Check if player can accept more quests"""
        return len(self.active_quests) < self.max_active_quests
    
    def get_completed_count(self) -> int:
        """Get total completed quests"""
        return len(self.completed_quests)
    
    def get_completion_rate(self) -> float:
        """Get quest completion rate"""
        total = len(self.completed_quests) + len(self.failed_quests)
        if total == 0:
            return 0.0
        return (len(self.completed_quests) / total) * 100
    
    def to_dict(self) -> dict:
        return {
            "available_quests": [q.to_dict() for q in self.available_quests],
            "active_quests": [q.to_dict() for q in self.active_quests],
            "completed_quests": [q.to_dict() for q in self.completed_quests[-50:]],
            "failed_quests": [q.to_dict() for q in self.failed_quests[-50:]],
            "max_active_quests": self.max_active_quests,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuestSystem":
        system = cls()
        system.available_quests = [Quest.from_dict(q) for q in data.get("available_quests", [])]
        system.active_quests = [Quest.from_dict(q) for q in data.get("active_quests", [])]
        system.completed_quests = [Quest.from_dict(q) for q in data.get("completed_quests", [])]
        system.failed_quests = [Quest.from_dict(q) for q in data.get("failed_quests", [])]
        system.max_active_quests = data.get("max_active_quests", 3)
        return system