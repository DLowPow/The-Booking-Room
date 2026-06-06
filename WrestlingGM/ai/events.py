# ai/events.py
"""
Events — Drama generation + player goals.
Consolidates: event_generator.py + quest_system.py

Two systems:
  - EventGenerator: random backstage/contract/media/scandal events
  - QuestSystem: player objectives, AI-pitched quests, storyline-linked goals

Both preserved with identical public interfaces.
EventSeverity is exported here (director.py imports it from this path-equivalent).
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==========================================================================
# ============================  EVENTS  ====================================
# ==========================================================================

class EventSeverity(Enum):
    MINOR = "Minor"
    MODERATE = "Moderate"
    MAJOR = "Major"
    CRITICAL = "Critical"


class EventCategory(Enum):
    BACKSTAGE = "Backstage"
    CONTRACT = "Contract"
    MEDIA = "Media"
    FINANCIAL = "Financial"
    MORALE = "Morale"
    INJURY = "Injury"
    SCANDAL = "Scandal"
    OPPORTUNITY = "Opportunity"
    RIVAL = "Rival Promotion"
    CREATIVE = "Creative Chaos"


EVENT_TEMPLATES = {
    "backstage_fight": {
        "category": EventCategory.BACKSTAGE, "severity": EventSeverity.MODERATE,
        "title": "{wrestler1} and {wrestler2} got into a backstage altercation!",
        "description": "Tensions boiled over backstage. {wrestler1} and {wrestler2} had a heated confrontation that nearly turned physical.",
        "requires_wrestlers": 2, "min_roster": 4, "cooldown": 4,
        "options": [
            {"label": "Fine both wrestlers ($500 each)", "effects": {"money": -1000, "morale_all": -3}},
            {"label": "Let them settle it in the ring", "effects": {"morale_w1": 5, "morale_w2": 5, "fan_bonus": 50}},
            {"label": "Side with {wrestler1}", "effects": {"morale_w1": 10, "morale_w2": -15}},
            {"label": "Ignore it", "effects": {"morale_all": -5, "prestige": -1}},
        ],
    },
    "backstage_prank": {
        "category": EventCategory.BACKSTAGE, "severity": EventSeverity.MINOR,
        "title": "Backstage prank gone wrong!",
        "description": "{wrestler1} played a prank on {wrestler2} that didn't go over well. The locker room is divided.",
        "requires_wrestlers": 2, "min_roster": 3, "cooldown": 6,
        "options": [
            {"label": "Laugh it off — builds camaraderie", "effects": {"morale_all": 2}},
            {"label": "Discipline {wrestler1}", "effects": {"morale_w1": -10, "morale_w2": 5}},
            {"label": "Tell them to grow up", "effects": {"morale_all": -2}},
        ],
    },
    "locker_room_leader": {
        "category": EventCategory.BACKSTAGE, "severity": EventSeverity.MINOR,
        "title": "{wrestler1} is becoming a locker room leader!",
        "description": "The younger wrestlers look up to {wrestler1}. Their positive attitude is rubbing off on the entire roster.",
        "requires_wrestlers": 1, "min_roster": 5, "cooldown": 8,
        "options": [
            {"label": "Acknowledge them publicly (+morale)", "effects": {"morale_w1": 15, "morale_all": 5}},
            {"label": "Give them a raise ($200/wk)", "effects": {"salary_w1": 200, "morale_w1": 20}},
            {"label": "Keep it professional", "effects": {"morale_w1": 5}},
        ],
    },
    "contract_demand": {
        "category": EventCategory.CONTRACT, "severity": EventSeverity.MODERATE,
        "title": "{wrestler1} is demanding a raise!",
        "description": "{wrestler1} feels they're underpaid for their contributions. They want a significant salary increase or they'll consider their options.",
        "requires_wrestlers": 1, "min_roster": 3, "cooldown": 3,
        "options": [
            {"label": "Give them a raise ($300/wk)", "effects": {"salary_w1": 300, "morale_w1": 20}},
            {"label": "Promise a title shot instead", "effects": {"morale_w1": 10}},
            {"label": "Refuse — take it or leave it", "effects": {"morale_w1": -20, "loyalty_w1": -15}},
            {"label": "Negotiate a smaller raise ($100/wk)", "effects": {"salary_w1": 100, "morale_w1": 5}},
        ],
    },
    "contract_expiring_soon": {
        "category": EventCategory.CONTRACT, "severity": EventSeverity.MAJOR,
        "title": "{wrestler1}'s contract expires in 4 weeks!",
        "description": "{wrestler1} has only 4 weeks left on their deal. If you don't renew, they'll hit free agency.",
        "requires_wrestlers": 1, "min_roster": 2, "cooldown": 0,
        "options": [
            {"label": "Open renewal talks now", "effects": {"morale_w1": 5}},
            {"label": "Let it play out — test their loyalty", "effects": {"morale_w1": -5}},
            {"label": "Offer a bonus to extend ($2000)", "effects": {"money": -2000, "morale_w1": 15, "contract_extend_w1": 26}},
        ],
    },
    "viral_moment": {
        "category": EventCategory.MEDIA, "severity": EventSeverity.MINOR,
        "title": "{wrestler1} goes viral on social media!",
        "description": "A clip of {wrestler1} has blown up online. Your promotion's name is everywhere!",
        "requires_wrestlers": 1, "min_roster": 2, "cooldown": 5,
        "options": [
            {"label": "Capitalize on it — push them!", "effects": {"morale_w1": 10, "fan_bonus": 200, "popularity_w1": 5}},
            {"label": "Post it on the promotion's page", "effects": {"fan_bonus": 100}},
            {"label": "Ignore social media", "effects": {}},
        ],
    },
    "media_interview": {
        "category": EventCategory.MEDIA, "severity": EventSeverity.MINOR,
        "title": "Local media wants an interview!",
        "description": "A local newspaper/podcast wants to feature your promotion. Free publicity!",
        "requires_wrestlers": 0, "min_roster": 0, "cooldown": 6,
        "options": [
            {"label": "Accept the interview", "effects": {"fan_bonus": 150, "prestige": 2}},
            {"label": "Decline — we're too busy", "effects": {}},
        ],
    },
    "podcast_appearance": {
        "category": EventCategory.MEDIA, "severity": EventSeverity.MINOR,
        "title": "{wrestler1} appeared on a popular podcast!",
        "description": "{wrestler1} did a shoot interview on a wrestling podcast. They talked about working for your promotion.",
        "requires_wrestlers": 1, "min_roster": 2, "cooldown": 6,
        "options": [
            {"label": "Great exposure! Thank them", "effects": {"fan_bonus": 100, "morale_w1": 5}},
            {"label": "Fine them for speaking without permission ($200)", "effects": {"money": -200, "morale_w1": -15}},
            {"label": "Whatever — free press is free press", "effects": {"fan_bonus": 50}},
        ],
    },
    "sponsor_offer": {
        "category": EventCategory.FINANCIAL, "severity": EventSeverity.MODERATE,
        "title": "Sponsorship offer received!",
        "description": "A local business wants to sponsor your next show. They'll pay ${amount} for ring mat branding.",
        "requires_wrestlers": 0, "min_roster": 0, "min_fans": 500, "cooldown": 8,
        "amount_range": [500, 3000],
        "options": [
            {"label": "Accept the sponsorship", "effects": {"money_bonus": True}},
            {"label": "Decline — we don't need sponsors", "effects": {"prestige": 1}},
        ],
    },
    "equipment_breakdown": {
        "category": EventCategory.FINANCIAL, "severity": EventSeverity.MINOR,
        "title": "Ring equipment needs repair!",
        "description": "Some of your ring ropes and turnbuckles are wearing out. You'll need to invest in repairs.",
        "requires_wrestlers": 0, "min_roster": 0, "cooldown": 10,
        "options": [
            {"label": "Fix it properly ($800)", "effects": {"money": -800, "quality_bonus": 2}},
            {"label": "Patch it up cheaply ($200)", "effects": {"money": -200}},
            {"label": "Ignore it — it'll be fine", "effects": {"quality_penalty": -3, "injury_risk": 5}},
        ],
    },
    "financial_pressure": {
        "category": EventCategory.FINANCIAL, "severity": EventSeverity.MAJOR,
        "title": "Cash flow crisis!",
        "description": "Your budget is critically low. You need to make some tough decisions.",
        "requires_wrestlers": 0, "min_roster": 0, "max_budget": 2000, "cooldown": 4,
        "options": [
            {"label": "Cut production costs for next show", "effects": {}},
            {"label": "Release the lowest-paid wrestler", "effects": {}},
            {"label": "Take a bank loan", "effects": {}},
            {"label": "Tough it out — book more shows", "effects": {}},
        ],
    },
    "morale_low_complaint": {
        "category": EventCategory.MORALE, "severity": EventSeverity.MODERATE,
        "title": "{wrestler1} is unhappy!",
        "description": "{wrestler1} has low morale and is considering their options. They feel underutilized.",
        "requires_wrestlers": 1, "min_roster": 3, "cooldown": 3, "trigger_low_morale": True,
        "options": [
            {"label": "Give them a raise ($150/wk)", "effects": {"salary_w1": 150, "morale_w1": 15}},
            {"label": "Promise a push", "effects": {"morale_w1": 10}},
            {"label": "Have a heart-to-heart talk", "effects": {"morale_w1": 8}},
            {"label": "Ignore it", "effects": {"morale_w1": -10, "loyalty_w1": -10}},
        ],
    },
    "morale_high_celebration": {
        "category": EventCategory.MORALE, "severity": EventSeverity.MINOR,
        "title": "Locker room morale is high!",
        "description": "The roster is in great spirits after recent shows. Everyone is motivated.",
        "requires_wrestlers": 0, "min_roster": 3, "cooldown": 8, "trigger_high_morale": True,
        "options": [
            {"label": "Throw a team dinner ($500)", "effects": {"money": -500, "morale_all": 10}},
            {"label": "Keep the momentum going", "effects": {"morale_all": 3}},
        ],
    },
    "walkout_threat": {
        "category": EventCategory.MORALE, "severity": EventSeverity.CRITICAL,
        "title": "{wrestler1} is threatening to walk out!",
        "description": "{wrestler1} is fed up and threatening to leave immediately. This would breach their contract.",
        "requires_wrestlers": 1, "min_roster": 3, "cooldown": 6, "trigger_very_low_morale": True,
        "options": [
            {"label": "Offer a big raise ($500/wk) and apologize", "effects": {"salary_w1": 500, "morale_w1": 25}},
            {"label": "Let them go — their attitude is toxic", "effects": {"release_w1": True, "morale_all": 5}},
            {"label": "Suspend them for 4 weeks", "effects": {"morale_w1": -20, "suspend_w1": 4}},
            {"label": "Offer a title opportunity", "effects": {"morale_w1": 20}},
        ],
    },
    "social_media_scandal": {
        "category": EventCategory.SCANDAL, "severity": EventSeverity.MAJOR,
        "title": "{wrestler1} involved in social media controversy!",
        "description": "{wrestler1} posted something controversial online. Your promotion is getting dragged into it.",
        "requires_wrestlers": 1, "min_roster": 2, "cooldown": 10,
        "options": [
            {"label": "Suspend them and issue a statement", "effects": {"morale_w1": -15, "prestige": -2, "fan_bonus": -200}},
            {"label": "Stand by them — freedom of speech", "effects": {"morale_w1": 10, "fan_bonus": -500, "prestige": -5}},
            {"label": "Release them immediately", "effects": {"release_w1": True, "prestige": -1, "fan_bonus": -100}},
            {"label": "Turn it into a storyline", "effects": {"fan_bonus": 100, "morale_w1": 5}},
        ],
    },
    "dui_arrest": {
        "category": EventCategory.SCANDAL, "severity": EventSeverity.CRITICAL,
        "title": "{wrestler1} arrested for DUI!",
        "description": "{wrestler1} was arrested last night. This is a PR nightmare.",
        "requires_wrestlers": 1, "min_roster": 3, "cooldown": 20,
        "options": [
            {"label": "Suspend without pay for 8 weeks", "effects": {"morale_w1": -25, "suspend_w1": 8, "prestige": -3}},
            {"label": "Release them with a public statement", "effects": {"release_w1": True, "prestige": -2}},
            {"label": "Support their recovery — pay for rehab ($3000)", "effects": {"money": -3000, "morale_w1": 20, "morale_all": 5, "prestige": 2}},
            {"label": "Ignore it — not our problem", "effects": {"prestige": -5, "fan_bonus": -300}},
        ],
    },
    "talent_interest": {
        "category": EventCategory.OPPORTUNITY, "severity": EventSeverity.MINOR,
        "title": "A talented free agent is interested!",
        "description": "Word on the street is that a quality free agent has been watching your shows and is interested in signing.",
        "requires_wrestlers": 0, "min_roster": 0, "min_prestige": 5, "cooldown": 6,
        "options": [
            {"label": "Reach out to them", "effects": {"new_agent": True}},
            {"label": "Wait for them to come to us", "effects": {}},
        ],
    },
    "charity_event": {
        "category": EventCategory.OPPORTUNITY, "severity": EventSeverity.MINOR,
        "title": "Charity event invitation!",
        "description": "A local charity wants your wrestlers to appear at a community event. Great PR opportunity.",
        "requires_wrestlers": 0, "min_roster": 2, "cooldown": 8,
        "options": [
            {"label": "Send 2 wrestlers — great PR", "effects": {"fan_bonus": 200, "prestige": 3, "morale_all": 3}},
            {"label": "Donate money instead ($500)", "effects": {"money": -500, "prestige": 2}},
            {"label": "Decline — we're too busy", "effects": {}},
        ],
    },
    "merchandise_deal": {
        "category": EventCategory.OPPORTUNITY, "severity": EventSeverity.MODERATE,
        "title": "Merchandise partnership offer!",
        "description": "A merch company wants to produce official merchandise for your top star.",
        "requires_wrestlers": 1, "min_roster": 3, "min_fans": 1000, "cooldown": 12,
        "options": [
            {"label": "Accept — extra revenue stream", "effects": {"money": 2000, "fan_bonus": 100}},
            {"label": "Negotiate better terms (+50%)", "effects": {"money": 3000}},
            {"label": "Decline — we'll handle merch ourselves", "effects": {}},
        ],
    },
    "surprise_return": {
        "category": EventCategory.CREATIVE, "severity": EventSeverity.MODERATE,
        "title": "A former wrestler wants to come back!",
        "description": "Someone from your past wants to return. Could be a huge pop... or a disaster.",
        "requires_wrestlers": 0, "min_roster": 5, "cooldown": 12, "creative_only": True,
        "options": [
            {"label": "Welcome them back!", "effects": {"fan_bonus": 300, "morale_all": 5}},
            {"label": "Decline — we've moved on", "effects": {}},
        ],
    },
    "mystery_investor": {
        "category": EventCategory.CREATIVE, "severity": EventSeverity.MAJOR,
        "title": "Mystery investor approaches you!",
        "description": "An anonymous wealthy individual wants to invest in your promotion. Strings attached.",
        "requires_wrestlers": 0, "min_roster": 0, "cooldown": 20, "creative_only": True,
        "options": [
            {"label": "Accept their money ($10,000)", "effects": {"money": 10000, "prestige": -3}},
            {"label": "Decline — we do things our way", "effects": {"prestige": 2}},
            {"label": "Investigate who they are first", "effects": {}},
        ],
    },
}


class EventGenerator:
    """Generates random events based on game state, personality, and creative control"""

    def __init__(self):
        self.cooldowns: Dict[str, int] = {}
        self.events_generated: int = 0

    def generate_events(self, roster, budget, fans, prestige, current_week,
                        chaos_factor=0.3, creative_control_enabled=False):
        generated = []

        for event_type in list(self.cooldowns.keys()):
            self.cooldowns[event_type] -= 1
            if self.cooldowns[event_type] <= 0:
                del self.cooldowns[event_type]

        event_chance = 0.15 + (chaos_factor * 0.25)
        if creative_control_enabled:
            event_chance += 0.15
        if random.random() > event_chance:
            return generated

        eligible = []
        for template_key, template in EVENT_TEMPLATES.items():
            if template_key in self.cooldowns:
                continue
            if template.get("min_roster", 0) > len(roster):
                continue
            if "max_budget" in template and budget > template["max_budget"]:
                continue
            if template.get("min_fans", 0) > fans:
                continue
            if template.get("min_prestige", 0) > prestige:
                continue
            if template.get("creative_only", False) and not creative_control_enabled:
                continue
            if template.get("trigger_low_morale", False):
                if not [w for w in roster if w.get("morale", 75) < 40]:
                    continue
            if template.get("trigger_very_low_morale", False):
                if not [w for w in roster if w.get("morale", 75) < 25]:
                    continue
            if template.get("trigger_high_morale", False):
                avg_morale = sum(w.get("morale", 75) for w in roster) / max(len(roster), 1)
                if avg_morale < 70:
                    continue
            eligible.append(template_key)

        if not eligible:
            return generated

        chosen_key = random.choice(eligible)
        template = EVENT_TEMPLATES[chosen_key]

        wrestlers_involved = []
        available_wrestlers = [w for w in roster if not w.get("is_injured", False)]

        if template.get("trigger_low_morale", False):
            low = [w for w in available_wrestlers if w.get("morale", 75) < 40]
            if low:
                wrestlers_involved.append(random.choice(low))
        elif template.get("trigger_very_low_morale", False):
            vlow = [w for w in available_wrestlers if w.get("morale", 75) < 25]
            if vlow:
                wrestlers_involved.append(random.choice(vlow))
        elif template.get("requires_wrestlers", 0) > 0:
            num_needed = template["requires_wrestlers"]
            if len(available_wrestlers) >= num_needed:
                wrestlers_involved = random.sample(available_wrestlers, num_needed)

        if template.get("requires_wrestlers", 0) > 0 and len(wrestlers_involved) < template["requires_wrestlers"]:
            return generated

        wrestler_names = [w["name"] for w in wrestlers_involved]
        w1_name = wrestler_names[0] if len(wrestler_names) > 0 else ""
        w2_name = wrestler_names[1] if len(wrestler_names) > 1 else ""

        amount = 0
        if "amount_range" in template:
            amount = random.randint(template["amount_range"][0], template["amount_range"][1])

        title = template["title"].format(wrestler1=w1_name, wrestler2=w2_name, amount=amount)
        description = template["description"].format(wrestler1=w1_name, wrestler2=w2_name, amount=amount)

        options = []
        for opt in template["options"]:
            label = opt["label"].format(wrestler1=w1_name, wrestler2=w2_name, amount=amount)
            effects = dict(opt["effects"])
            if effects.get("money_bonus") and amount > 0:
                effects["money"] = amount
                del effects["money_bonus"]
            options.append({"label": label, "effects": effects})

        event = {
            "id": f"event_{current_week}_{chosen_key}_{self.events_generated}",
            "template_key": chosen_key,
            "category": template["category"].value,
            "severity": template["severity"].value,
            "title": title, "description": description,
            "wrestlers_involved": wrestler_names,
            "options": options, "week": current_week, "amount": amount,
        }

        self.cooldowns[chosen_key] = template.get("cooldown", 4)
        self.events_generated += 1
        generated.append(event)

        if chaos_factor > 0.7 and random.random() < 0.3:
            generated.extend(self.generate_events(
                roster, budget, fans, prestige, current_week,
                chaos_factor * 0.5, creative_control_enabled))

        return generated

    def to_dict(self) -> dict:
        return {"cooldowns": self.cooldowns, "events_generated": self.events_generated}

    @classmethod
    def from_dict(cls, data: dict) -> "EventGenerator":
        eg = cls()
        eg.cooldowns = data.get("cooldowns", {})
        eg.events_generated = data.get("events_generated", 0)
        return eg


# ==========================================================================
# ============================  QUESTS  ====================================
# ==========================================================================

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


@dataclass
class Quest:
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty = QuestDifficulty.NORMAL
    status: QuestStatus = QuestStatus.AVAILABLE
    source: QuestSource = QuestSource.SYSTEM
    target_value: int = 0
    current_value: int = 0
    target_wrestler: str = ""
    target_venue: str = ""
    target_storyline_id: str = ""
    secondary_target: str = ""
    duration_weeks: int = 12
    weeks_remaining: int = 12
    week_started: int = 0
    year_started: int = 1
    xp_reward: int = 100
    money_reward: int = 0
    fans_reward: int = 0
    prestige_reward: int = 0
    prestige_penalty: int = 0
    fans_penalty: int = 0
    money_penalty: int = 0
    ai_personality_pitch: str = ""
    ai_personality_name: str = ""
    is_repeatable: bool = False
    times_completed: int = 0
    icon: str = "🎯"
    color: str = "#3b82f6"

    def start(self, current_week, current_year=1):
        self.status = QuestStatus.ACTIVE
        self.week_started = current_week
        self.year_started = current_year
        self.weeks_remaining = self.duration_weeks

    def update_progress(self, new_value):
        self.current_value = new_value
        if self.current_value >= self.target_value:
            self.complete()

    def add_progress(self, amount):
        self.current_value += amount
        if self.current_value >= self.target_value:
            self.complete()

    def complete(self):
        self.status = QuestStatus.COMPLETED
        self.times_completed += 1

    def fail(self):
        self.status = QuestStatus.FAILED

    def tick_week(self):
        if self.status == QuestStatus.ACTIVE:
            self.weeks_remaining -= 1
            if self.weeks_remaining <= 0 and self.current_value < self.target_value:
                self.fail()

    def get_progress_percentage(self) -> float:
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def get_time_percentage(self) -> float:
        if self.duration_weeks == 0:
            return 0.0
        return (self.weeks_remaining / self.duration_weeks) * 100

    def get_difficulty_color(self) -> str:
        return {
            QuestDifficulty.EASY: "#10b981", QuestDifficulty.NORMAL: "#3b82f6",
            QuestDifficulty.HARD: "#f59e0b", QuestDifficulty.LEGENDARY: "#dc2626",
        }.get(self.difficulty, "#6b7280")

    def get_status_color(self) -> str:
        return {
            QuestStatus.AVAILABLE: "#3b82f6", QuestStatus.ACTIVE: "#f59e0b",
            QuestStatus.COMPLETED: "#10b981", QuestStatus.FAILED: "#dc2626",
            QuestStatus.EXPIRED: "#6b7280",
        }.get(self.status, "#6b7280")

    def get_urgency(self) -> str:
        if self.status != QuestStatus.ACTIVE:
            return ""
        if self.weeks_remaining <= 2:
            return "🚨 URGENT"
        if self.weeks_remaining <= 4:
            return "⚠️ Soon"
        return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "quest_type": self.quest_type.value, "difficulty": self.difficulty.value,
            "status": self.status.value, "source": self.source.value,
            "target_value": self.target_value, "current_value": self.current_value,
            "target_wrestler": self.target_wrestler, "target_venue": self.target_venue,
            "target_storyline_id": self.target_storyline_id, "secondary_target": self.secondary_target,
            "duration_weeks": self.duration_weeks, "weeks_remaining": self.weeks_remaining,
            "week_started": self.week_started, "year_started": self.year_started,
            "xp_reward": self.xp_reward, "money_reward": self.money_reward,
            "fans_reward": self.fans_reward, "prestige_reward": self.prestige_reward,
            "prestige_penalty": self.prestige_penalty, "fans_penalty": self.fans_penalty,
            "money_penalty": self.money_penalty,
            "ai_personality_pitch": self.ai_personality_pitch,
            "ai_personality_name": self.ai_personality_name,
            "is_repeatable": self.is_repeatable, "times_completed": self.times_completed,
            "icon": self.icon, "color": self.color,
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
            id=data["id"], title=data["title"], description=data["description"],
            quest_type=qt, difficulty=diff, status=status, source=source,
            target_value=data.get("target_value", 0), current_value=data.get("current_value", 0),
            target_wrestler=data.get("target_wrestler", ""), target_venue=data.get("target_venue", ""),
            target_storyline_id=data.get("target_storyline_id", ""),
            secondary_target=data.get("secondary_target", ""),
            duration_weeks=data.get("duration_weeks", 12), weeks_remaining=data.get("weeks_remaining", 12),
            week_started=data.get("week_started", 0), year_started=data.get("year_started", 1),
            xp_reward=data.get("xp_reward", 100), money_reward=data.get("money_reward", 0),
            fans_reward=data.get("fans_reward", 0), prestige_reward=data.get("prestige_reward", 0),
            prestige_penalty=data.get("prestige_penalty", 0), fans_penalty=data.get("fans_penalty", 0),
            money_penalty=data.get("money_penalty", 0),
            ai_personality_pitch=data.get("ai_personality_pitch", ""),
            ai_personality_name=data.get("ai_personality_name", ""),
            is_repeatable=data.get("is_repeatable", False),
            times_completed=data.get("times_completed", 0),
            icon=data.get("icon", "🎯"), color=data.get("color", "#3b82f6"),
        )


class QuestSystem:
    def __init__(self):
        self.available_quests: List[Quest] = []
        self.active_quests: List[Quest] = []
        self.completed_quests: List[Quest] = []
        self.failed_quests: List[Quest] = []
        self.max_active_quests: int = 3
        self.next_id: int = 1

    def _next_quest_id(self, prefix="quest") -> str:
        qid = f"{prefix}_{self.next_id}"
        self.next_id += 1
        return qid

    def generate_random_quests(self, current_week, current_year=1, fans=1000,
                               budget=50000, prestige=50, roster=None, count=3):
        quest_types = [QuestType.FANS, QuestType.FINANCIAL, QuestType.FIVE_STAR,
                       QuestType.SELLOUT, QuestType.SHOW_QUALITY]
        if roster and len(roster) > 0:
            quest_types.append(QuestType.BUILD_STAR)
            quest_types.append(QuestType.WIN_STREAK)
        generated = []
        for _ in range(count):
            quest_type = random.choice(quest_types)
            quest = self._generate_quest(quest_type, current_week, current_year,
                                         fans=fans, budget=budget, prestige=prestige, roster=roster)
            if quest:
                generated.append(quest)
                self.available_quests.append(quest)
        return generated

    def _generate_quest(self, quest_type, current_week, current_year=1, **context):
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

    def _generate_fans_quest(self, current_week, current_year, context):
        current_fans = context.get("fans", 1000)
        multiplier = random.uniform(1.3, 1.8)
        target = int(current_fans * multiplier)
        difficulty = QuestDifficulty.NORMAL
        if multiplier > 1.6:
            difficulty = QuestDifficulty.HARD
        elif multiplier < 1.4:
            difficulty = QuestDifficulty.EASY
        return Quest(
            id=self._next_quest_id("fans"), title="Grow Your Fanbase",
            description=f"Reach {target:,} fans. Put on great shows and spread the word!",
            quest_type=QuestType.FANS, difficulty=difficulty,
            target_value=target, current_value=current_fans,
            duration_weeks=12, weeks_remaining=12,
            xp_reward=200 + int((multiplier - 1.3) * 400),
            fans_reward=int(target * 0.1), is_repeatable=True,
            icon="👥", color="#3b82f6",
        )

    def _generate_financial_quest(self, current_week, current_year, context):
        current_budget = context.get("budget", 50000)
        multiplier = random.uniform(1.5, 2.5)
        target = int(current_budget * multiplier)
        difficulty = QuestDifficulty.NORMAL
        if multiplier > 2.0:
            difficulty = QuestDifficulty.HARD
        elif multiplier < 1.7:
            difficulty = QuestDifficulty.EASY
        return Quest(
            id=self._next_quest_id("money"), title="Build Your War Chest",
            description=f"Reach a budget of ${target:,}. Manage your finances wisely!",
            quest_type=QuestType.FINANCIAL, difficulty=difficulty,
            target_value=target, current_value=current_budget,
            duration_weeks=16, weeks_remaining=16,
            xp_reward=300 + int((multiplier - 1.5) * 300),
            money_reward=int(target * 0.1), is_repeatable=True,
            icon="💰", color="#10b981",
        )

    def _generate_five_star_quest(self, current_week, current_year, context):
        return Quest(
            id=self._next_quest_id("fivestar"), title="Match of the Year Candidate",
            description="Produce a 5-star match. Book the right wrestlers in the right match!",
            quest_type=QuestType.FIVE_STAR, difficulty=QuestDifficulty.HARD,
            target_value=1, current_value=0, duration_weeks=8, weeks_remaining=8,
            xp_reward=500, prestige_reward=10, fans_reward=500,
            icon="⭐", color="#fbbf24",
        )

    def _generate_sellout_quest(self, current_week, current_year, context):
        return Quest(
            id=self._next_quest_id("sellout"), title="Fill The House",
            description="Sell out a venue. Build hype and deliver a great card!",
            quest_type=QuestType.SELLOUT, difficulty=QuestDifficulty.NORMAL,
            target_value=1, current_value=0, duration_weeks=6, weeks_remaining=6,
            xp_reward=250, fans_reward=300, prestige_reward=5, is_repeatable=True,
            icon="🏟️", color="#8b5cf6",
        )

    def _generate_build_star_quest(self, current_week, current_year, context):
        roster = context.get("roster", [])
        if not roster:
            return None
        candidates = [w for w in roster
                      if 30 < w.get("popularity", 50) < 70 and not w.get("is_injured")]
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
            quest_type=QuestType.BUILD_STAR, difficulty=QuestDifficulty.HARD,
            target_value=target_pop, current_value=current_pop,
            target_wrestler=wrestler_name, duration_weeks=16, weeks_remaining=16,
            xp_reward=400, prestige_reward=8, icon="🌟", color="#f59e0b",
        )

    def _generate_show_quality_quest(self, current_week, current_year, context):
        target_rating = random.choice([3.5, 4.0, 4.5])
        difficulty = QuestDifficulty.NORMAL
        if target_rating >= 4.5:
            difficulty = QuestDifficulty.LEGENDARY
        elif target_rating >= 4.0:
            difficulty = QuestDifficulty.HARD
        return Quest(
            id=self._next_quest_id("quality"), title="Quality Wrestling",
            description=f"Run a show with an average match rating of {target_rating}+ stars!",
            quest_type=QuestType.SHOW_QUALITY, difficulty=difficulty,
            target_value=int(target_rating * 10), current_value=0,
            duration_weeks=4, weeks_remaining=4,
            xp_reward=int(200 + (target_rating - 3.5) * 300),
            prestige_reward=int(5 + (target_rating - 3.5) * 10),
            icon="📺", color="#a855f7",
        )

    def _generate_win_streak_quest(self, current_week, current_year, context):
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
            target_value=target, current_value=0, target_wrestler=wrestler["name"],
            duration_weeks=12, weeks_remaining=12,
            xp_reward=250 + (target * 30), prestige_reward=target,
            icon="🔥", color="#ef4444",
        )

    def _generate_rivalry_quest(self, current_week, current_year, context):
        return Quest(
            id=self._next_quest_id("rivalry"), title="Create a Heated Rivalry",
            description="Create a storyline rivalry and build it to peak heat (80+)!",
            quest_type=QuestType.RIVALRY, difficulty=QuestDifficulty.HARD,
            target_value=80, current_value=0, duration_weeks=10, weeks_remaining=10,
            xp_reward=400, prestige_reward=10, fans_reward=300,
            icon="⚔️", color="#dc2626",
        )

    def generate_ai_pitched_quest(self, ai_director, current_week, current_year,
                                  roster, fans, budget):
        if not ai_director or not ai_director.personality:
            return None
        personality = ai_director.personality
        personality_type_str = personality.get_name().replace("The ", "")
        if personality_type_str == "Showman":
            quest_types = [QuestType.SELLOUT, QuestType.FIVE_STAR, QuestType.FANS, QuestType.RIVALRY]
        elif personality_type_str == "Mastermind":
            quest_types = [QuestType.FINANCIAL, QuestType.BUILD_STAR, QuestType.FANS, QuestType.SHOW_QUALITY]
        elif personality_type_str == "Mad Scientist":
            quest_types = [QuestType.BUILD_STAR, QuestType.FIVE_STAR, QuestType.RIVALRY]
        else:
            quest_types = [QuestType.SHOW_QUALITY, QuestType.BUILD_STAR, QuestType.FINANCIAL, QuestType.WIN_STREAK]
        quest_type = random.choice(quest_types)
        quest = self._generate_quest(quest_type, current_week, current_year,
                                     fans=fans, budget=budget, roster=roster)
        if quest:
            quest.source = QuestSource.AI_DIRECTOR
            quest.ai_personality_name = personality.get_name()
            greeting = personality.get_greeting()
            sign_off = personality.get_sign_off()
            quest.ai_personality_pitch = f"{greeting}\n\n{quest.description}\n\n{sign_off}"
            self.available_quests.append(quest)
        return quest

    def generate_storyline_quest(self, storyline, current_week, current_year):
        if not storyline:
            return None
        target_heat = 80
        current_heat = storyline.heat
        quest = Quest(
            id=self._next_quest_id(f"storyline_{storyline.id}"),
            title=f"Build Storyline: {storyline.name}",
            description=f"Build the {storyline.name} storyline to peak heat ({target_heat}+)!",
            quest_type=QuestType.STORYLINE, difficulty=QuestDifficulty.HARD,
            source=QuestSource.STORYLINE, target_value=target_heat, current_value=current_heat,
            target_storyline_id=storyline.id, duration_weeks=8, weeks_remaining=8,
            xp_reward=350, prestige_reward=8, fans_reward=200,
            icon=storyline.get_icon(), color=storyline.get_heat_color(),
        )
        self.available_quests.append(quest)
        return quest

    def accept_quest(self, quest_id, current_week, current_year=1) -> bool:
        if len(self.active_quests) >= self.max_active_quests:
            return False
        for quest in self.available_quests:
            if quest.id == quest_id:
                quest.start(current_week, current_year)
                self.available_quests.remove(quest)
                self.active_quests.append(quest)
                return True
        return False

    def abandon_quest(self, quest_id) -> bool:
        for quest in self.active_quests:
            if quest.id == quest_id:
                quest.status = QuestStatus.FAILED
                self.active_quests.remove(quest)
                self.failed_quests.append(quest)
                return True
        return False

    def reject_available_quest(self, quest_id) -> bool:
        for quest in self.available_quests:
            if quest.id == quest_id:
                self.available_quests.remove(quest)
                return True
        return False

    def check_progress(self, storyline_engine=None, **current_values):
        updates = []
        for quest in self.active_quests[:]:
            old_value = quest.current_value
            old_status = quest.status
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
                active = storyline_engine.get_active_storylines()
                if active:
                    max_heat = max(sl.heat for sl in active)
                    quest.update_progress(max_heat)
            elif quest.quest_type == QuestType.STORYLINE and storyline_engine:
                sl = storyline_engine.get_storyline(quest.target_storyline_id)
                if sl:
                    quest.update_progress(sl.heat)

            quest.tick_week()

            if quest.current_value != old_value:
                updates.append({
                    "quest_id": quest.id, "quest_title": quest.title,
                    "old_value": old_value, "new_value": quest.current_value,
                    "target": quest.target_value,
                    "progress": quest.get_progress_percentage(),
                })

            if quest.status != old_status:
                if quest.status == QuestStatus.COMPLETED:
                    self.active_quests.remove(quest)
                    self.completed_quests.append(quest)
                    updates.append({
                        "quest_id": quest.id, "quest_title": quest.title,
                        "status": "completed",
                        "rewards": {
                            "xp": quest.xp_reward, "money": quest.money_reward,
                            "fans": quest.fans_reward, "prestige": quest.prestige_reward,
                        },
                    })
                elif quest.status == QuestStatus.FAILED:
                    self.active_quests.remove(quest)
                    self.failed_quests.append(quest)
                    updates.append({
                        "quest_id": quest.id, "quest_title": quest.title,
                        "status": "failed",
                        "penalties": {
                            "prestige": quest.prestige_penalty,
                            "fans": quest.fans_penalty,
                            "money": quest.money_penalty,
                        },
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
        for q in (self.available_quests + self.active_quests
                  + self.completed_quests + self.failed_quests):
            if q.id == quest_id:
                return q
        return None

    def get_active_quests_for_wrestler(self, wrestler_name: str) -> List[Quest]:
        return [q for q in self.active_quests if q.target_wrestler == wrestler_name]

    def get_ai_pitched_quests(self) -> List[Quest]:
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