"""
AI Event Generator - Random events that challenge and reward the player
Backstage drama, contract disputes, viral moments, scandals, injuries
Events scale with promotion size, roster mood, and AI personality
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


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


# ==================== EVENT TEMPLATES ====================

EVENT_TEMPLATES = {
    # ===== BACKSTAGE EVENTS =====
    "backstage_fight": {
        "category": EventCategory.BACKSTAGE,
        "severity": EventSeverity.MODERATE,
        "title": "{wrestler1} and {wrestler2} got into a backstage altercation!",
        "description": "Tensions boiled over backstage. {wrestler1} and {wrestler2} had a heated confrontation that nearly turned physical.",
        "requires_wrestlers": 2,
        "min_roster": 4,
        "cooldown": 4,
        "options": [
            {"label": "Fine both wrestlers ($500 each)", "effects": {"money": -1000, "morale_all": -3}},
            {"label": "Let them settle it in the ring", "effects": {"morale_w1": 5, "morale_w2": 5, "fan_bonus": 50}},
            {"label": "Side with {wrestler1}", "effects": {"morale_w1": 10, "morale_w2": -15}},
            {"label": "Ignore it", "effects": {"morale_all": -5, "prestige": -1}},
        ],
    },
    "backstage_prank": {
        "category": EventCategory.BACKSTAGE,
        "severity": EventSeverity.MINOR,
        "title": "Backstage prank gone wrong!",
        "description": "{wrestler1} played a prank on {wrestler2} that didn't go over well. The locker room is divided.",
        "requires_wrestlers": 2,
        "min_roster": 3,
        "cooldown": 6,
        "options": [
            {"label": "Laugh it off — builds camaraderie", "effects": {"morale_all": 2}},
            {"label": "Discipline {wrestler1}", "effects": {"morale_w1": -10, "morale_w2": 5}},
            {"label": "Tell them to grow up", "effects": {"morale_all": -2}},
        ],
    },
    "locker_room_leader": {
        "category": EventCategory.BACKSTAGE,
        "severity": EventSeverity.MINOR,
        "title": "{wrestler1} is becoming a locker room leader!",
        "description": "The younger wrestlers look up to {wrestler1}. Their positive attitude is rubbing off on the entire roster.",
        "requires_wrestlers": 1,
        "min_roster": 5,
        "cooldown": 8,
        "options": [
            {"label": "Acknowledge them publicly (+morale)", "effects": {"morale_w1": 15, "morale_all": 5}},
            {"label": "Give them a raise ($200/wk)", "effects": {"salary_w1": 200, "morale_w1": 20}},
            {"label": "Keep it professional", "effects": {"morale_w1": 5}},
        ],
    },

    # ===== CONTRACT EVENTS =====
    "contract_demand": {
        "category": EventCategory.CONTRACT,
        "severity": EventSeverity.MODERATE,
        "title": "{wrestler1} is demanding a raise!",
        "description": "{wrestler1} feels they're underpaid for their contributions. They want a significant salary increase or they'll consider their options.",
        "requires_wrestlers": 1,
        "min_roster": 3,
        "cooldown": 3,
        "options": [
            {"label": "Give them a raise ($300/wk)", "effects": {"salary_w1": 300, "morale_w1": 20}},
            {"label": "Promise a title shot instead", "effects": {"morale_w1": 10}},
            {"label": "Refuse — take it or leave it", "effects": {"morale_w1": -20, "loyalty_w1": -15}},
            {"label": "Negotiate a smaller raise ($100/wk)", "effects": {"salary_w1": 100, "morale_w1": 5}},
        ],
    },
    "contract_expiring_soon": {
        "category": EventCategory.CONTRACT,
        "severity": EventSeverity.MAJOR,
        "title": "{wrestler1}'s contract expires in 4 weeks!",
        "description": "{wrestler1} has only 4 weeks left on their deal. If you don't renew, they'll hit free agency.",
        "requires_wrestlers": 1,
        "min_roster": 2,
        "cooldown": 0,
        "options": [
            {"label": "Open renewal talks now", "effects": {"morale_w1": 5}},
            {"label": "Let it play out — test their loyalty", "effects": {"morale_w1": -5}},
            {"label": "Offer a bonus to extend ($2000)", "effects": {"money": -2000, "morale_w1": 15, "contract_extend_w1": 26}},
        ],
    },

    # ===== MEDIA & VIRAL EVENTS =====
    "viral_moment": {
        "category": EventCategory.MEDIA,
        "severity": EventSeverity.MINOR,
        "title": "{wrestler1} goes viral on social media!",
        "description": "A clip of {wrestler1} has blown up online. Your promotion's name is everywhere!",
        "requires_wrestlers": 1,
        "min_roster": 2,
        "cooldown": 5,
        "options": [
            {"label": "Capitalize on it — push them!", "effects": {"morale_w1": 10, "fan_bonus": 200, "popularity_w1": 5}},
            {"label": "Post it on the promotion's page", "effects": {"fan_bonus": 100}},
            {"label": "Ignore social media", "effects": {}},
        ],
    },
    "media_interview": {
        "category": EventCategory.MEDIA,
        "severity": EventSeverity.MINOR,
        "title": "Local media wants an interview!",
        "description": "A local newspaper/podcast wants to feature your promotion. Free publicity!",
        "requires_wrestlers": 0,
        "min_roster": 0,
        "cooldown": 6,
        "options": [
            {"label": "Accept the interview", "effects": {"fan_bonus": 150, "prestige": 2}},
            {"label": "Decline — we're too busy", "effects": {}},
        ],
    },
    "podcast_appearance": {
        "category": EventCategory.MEDIA,
        "severity": EventSeverity.MINOR,
        "title": "{wrestler1} appeared on a popular podcast!",
        "description": "{wrestler1} did a shoot interview on a wrestling podcast. They talked about working for your promotion.",
        "requires_wrestlers": 1,
        "min_roster": 2,
        "cooldown": 6,
        "options": [
            {"label": "Great exposure! Thank them", "effects": {"fan_bonus": 100, "morale_w1": 5}},
            {"label": "Fine them for speaking without permission ($200)", "effects": {"money": -200, "morale_w1": -15}},
            {"label": "Whatever — free press is free press", "effects": {"fan_bonus": 50}},
        ],
    },

    # ===== FINANCIAL EVENTS =====
    "sponsor_offer": {
        "category": EventCategory.FINANCIAL,
        "severity": EventSeverity.MODERATE,
        "title": "Sponsorship offer received!",
        "description": "A local business wants to sponsor your next show. They'll pay ${amount} for ring mat branding.",
        "requires_wrestlers": 0,
        "min_roster": 0,
        "min_fans": 500,
        "cooldown": 8,
        "amount_range": [500, 3000],
        "options": [
            {"label": "Accept the sponsorship", "effects": {"money_bonus": True}},
            {"label": "Decline — we don't need sponsors", "effects": {"prestige": 1}},
        ],
    },
    "equipment_breakdown": {
        "category": EventCategory.FINANCIAL,
        "severity": EventSeverity.MINOR,
        "title": "Ring equipment needs repair!",
        "description": "Some of your ring ropes and turnbuckles are wearing out. You'll need to invest in repairs.",
        "requires_wrestlers": 0,
        "min_roster": 0,
        "cooldown": 10,
        "options": [
            {"label": "Fix it properly ($800)", "effects": {"money": -800, "quality_bonus": 2}},
            {"label": "Patch it up cheaply ($200)", "effects": {"money": -200}},
            {"label": "Ignore it — it'll be fine", "effects": {"quality_penalty": -3, "injury_risk": 5}},
        ],
    },
    "financial_pressure": {
        "category": EventCategory.FINANCIAL,
        "severity": EventSeverity.MAJOR,
        "title": "Cash flow crisis!",
        "description": "Your budget is critically low. You need to make some tough decisions.",
        "requires_wrestlers": 0,
        "min_roster": 0,
        "max_budget": 2000,
        "cooldown": 4,
        "options": [
            {"label": "Cut production costs for next show", "effects": {}},
            {"label": "Release the lowest-paid wrestler", "effects": {}},
            {"label": "Take a bank loan", "effects": {}},
            {"label": "Tough it out — book more shows", "effects": {}},
        ],
    },

    # ===== MORALE EVENTS =====
    "morale_low_complaint": {
        "category": EventCategory.MORALE,
        "severity": EventSeverity.MODERATE,
        "title": "{wrestler1} is unhappy!",
        "description": "{wrestler1} has low morale and is considering their options. They feel underutilized.",
        "requires_wrestlers": 1,
        "min_roster": 3,
        "cooldown": 3,
        "trigger_low_morale": True,
        "options": [
            {"label": "Give them a raise ($150/wk)", "effects": {"salary_w1": 150, "morale_w1": 15}},
            {"label": "Promise a push", "effects": {"morale_w1": 10}},
            {"label": "Have a heart-to-heart talk", "effects": {"morale_w1": 8}},
            {"label": "Ignore it", "effects": {"morale_w1": -10, "loyalty_w1": -10}},
        ],
    },
    "morale_high_celebration": {
        "category": EventCategory.MORALE,
        "severity": EventSeverity.MINOR,
        "title": "Locker room morale is high!",
        "description": "The roster is in great spirits after recent shows. Everyone is motivated.",
        "requires_wrestlers": 0,
        "min_roster": 3,
        "cooldown": 8,
        "trigger_high_morale": True,
        "options": [
            {"label": "Throw a team dinner ($500)", "effects": {"money": -500, "morale_all": 10}},
            {"label": "Keep the momentum going", "effects": {"morale_all": 3}},
        ],
    },
    "walkout_threat": {
        "category": EventCategory.MORALE,
        "severity": EventSeverity.CRITICAL,
        "title": "{wrestler1} is threatening to walk out!",
        "description": "{wrestler1} is fed up and threatening to leave immediately. This would breach their contract.",
        "requires_wrestlers": 1,
        "min_roster": 3,
        "cooldown": 6,
        "trigger_very_low_morale": True,
        "options": [
            {"label": "Offer a big raise ($500/wk) and apologize", "effects": {"salary_w1": 500, "morale_w1": 25}},
            {"label": "Let them go — their attitude is toxic", "effects": {"release_w1": True, "morale_all": 5}},
            {"label": "Suspend them for 4 weeks", "effects": {"morale_w1": -20, "suspend_w1": 4}},
            {"label": "Offer a title opportunity", "effects": {"morale_w1": 20}},
        ],
    },

    # ===== SCANDAL EVENTS =====
    "social_media_scandal": {
        "category": EventCategory.SCANDAL,
        "severity": EventSeverity.MAJOR,
        "title": "{wrestler1} involved in social media controversy!",
        "description": "{wrestler1} posted something controversial online. Your promotion is getting dragged into it.",
        "requires_wrestlers": 1,
        "min_roster": 2,
        "cooldown": 10,
        "options": [
            {"label": "Suspend them and issue a statement", "effects": {"morale_w1": -15, "prestige": -2, "fan_bonus": -200}},
            {"label": "Stand by them — freedom of speech", "effects": {"morale_w1": 10, "fan_bonus": -500, "prestige": -5}},
            {"label": "Release them immediately", "effects": {"release_w1": True, "prestige": -1, "fan_bonus": -100}},
            {"label": "Turn it into a storyline", "effects": {"fan_bonus": 100, "morale_w1": 5}},
        ],
    },
    "dui_arrest": {
        "category": EventCategory.SCANDAL,
        "severity": EventSeverity.CRITICAL,
        "title": "{wrestler1} arrested for DUI!",
        "description": "{wrestler1} was arrested last night. This is a PR nightmare.",
        "requires_wrestlers": 1,
        "min_roster": 3,
        "cooldown": 20,
        "options": [
            {"label": "Suspend without pay for 8 weeks", "effects": {"morale_w1": -25, "suspend_w1": 8, "prestige": -3}},
            {"label": "Release them with a public statement", "effects": {"release_w1": True, "prestige": -2}},
            {"label": "Support their recovery — pay for rehab ($3000)", "effects": {"money": -3000, "morale_w1": 20, "morale_all": 5, "prestige": 2}},
            {"label": "Ignore it — not our problem", "effects": {"prestige": -5, "fan_bonus": -300}},
        ],
    },

    # ===== OPPORTUNITY EVENTS =====
    "talent_interest": {
        "category": EventCategory.OPPORTUNITY,
        "severity": EventSeverity.MINOR,
        "title": "A talented free agent is interested!",
        "description": "Word on the street is that a quality free agent has been watching your shows and is interested in signing.",
        "requires_wrestlers": 0,
        "min_roster": 0,
        "min_prestige": 5,
        "cooldown": 6,
        "options": [
            {"label": "Reach out to them", "effects": {"new_agent": True}},
            {"label": "Wait for them to come to us", "effects": {}},
        ],
    },
    "charity_event": {
        "category": EventCategory.OPPORTUNITY,
        "severity": EventSeverity.MINOR,
        "title": "Charity event invitation!",
        "description": "A local charity wants your wrestlers to appear at a community event. Great PR opportunity.",
        "requires_wrestlers": 0,
        "min_roster": 2,
        "cooldown": 8,
        "options": [
            {"label": "Send 2 wrestlers — great PR", "effects": {"fan_bonus": 200, "prestige": 3, "morale_all": 3}},
            {"label": "Donate money instead ($500)", "effects": {"money": -500, "prestige": 2}},
            {"label": "Decline — we're too busy", "effects": {}},
        ],
    },
    "merchandise_deal": {
        "category": EventCategory.OPPORTUNITY,
        "severity": EventSeverity.MODERATE,
        "title": "Merchandise partnership offer!",
        "description": "A merch company wants to produce official merchandise for your top star.",
        "requires_wrestlers": 1,
        "min_roster": 3,
        "min_fans": 1000,
        "cooldown": 12,
        "options": [
            {"label": "Accept — extra revenue stream", "effects": {"money": 2000, "fan_bonus": 100}},
            {"label": "Negotiate better terms (+50%)", "effects": {"money": 3000}},
            {"label": "Decline — we'll handle merch ourselves", "effects": {}},
        ],
    },

    # ===== CREATIVE CHAOS (Higher chance with Creative Control) =====
    "surprise_return": {
        "category": EventCategory.CREATIVE,
        "severity": EventSeverity.MODERATE,
        "title": "A former wrestler wants to come back!",
        "description": "Someone from your past wants to return. Could be a huge pop... or a disaster.",
        "requires_wrestlers": 0,
        "min_roster": 5,
        "cooldown": 12,
        "creative_only": True,
        "options": [
            {"label": "Welcome them back!", "effects": {"fan_bonus": 300, "morale_all": 5}},
            {"label": "Decline — we've moved on", "effects": {}},
        ],
    },
    "mystery_investor": {
        "category": EventCategory.CREATIVE,
        "severity": EventSeverity.MAJOR,
        "title": "Mystery investor approaches you!",
        "description": "An anonymous wealthy individual wants to invest in your promotion. Strings attached.",
        "requires_wrestlers": 0,
        "min_roster": 0,
        "cooldown": 20,
        "creative_only": True,
        "options": [
            {"label": "Accept their money ($10,000)", "effects": {"money": 10000, "prestige": -3}},
            {"label": "Decline — we do things our way", "effects": {"prestige": 2}},
            {"label": "Investigate who they are first", "effects": {}},
        ],
    },
}


# ==================== EVENT GENERATOR CLASS ====================

class EventGenerator:
    """Generates random events based on game state, personality, and creative control"""

    def __init__(self):
        self.cooldowns: Dict[str, int] = {}
        self.events_generated: int = 0

    def generate_events(
        self,
        roster: List[Dict],
        budget: int,
        fans: int,
        prestige: int,
        current_week: int,
        chaos_factor: float = 0.3,
        creative_control_enabled: bool = False,
    ) -> List[Dict]:
        """Generate random events for this week"""
        generated = []

        # Decay cooldowns
        for event_type in list(self.cooldowns.keys()):
            self.cooldowns[event_type] -= 1
            if self.cooldowns[event_type] <= 0:
                del self.cooldowns[event_type]

        # Base event chance (higher chaos = more events)
        event_chance = 0.15 + (chaos_factor * 0.25)
        if creative_control_enabled:
            event_chance += 0.15

        # Roll for event
        if random.random() > event_chance:
            return generated

        # Build eligible event pool
        eligible = []
        for template_key, template in EVENT_TEMPLATES.items():
            # Check cooldown
            if template_key in self.cooldowns:
                continue

            # Check roster requirements
            if template.get("min_roster", 0) > len(roster):
                continue

            # Check budget requirements
            if "max_budget" in template and budget > template["max_budget"]:
                continue

            # Check fan requirements
            if template.get("min_fans", 0) > fans:
                continue

            # Check prestige requirements
            if template.get("min_prestige", 0) > prestige:
                continue

            # Check creative control requirement
            if template.get("creative_only", False) and not creative_control_enabled:
                continue

            # Check morale triggers
            if template.get("trigger_low_morale", False):
                low_morale = [w for w in roster if w.get("morale", 75) < 40]
                if not low_morale:
                    continue

            if template.get("trigger_very_low_morale", False):
                very_low = [w for w in roster if w.get("morale", 75) < 25]
                if not very_low:
                    continue

            if template.get("trigger_high_morale", False):
                avg_morale = sum(w.get("morale", 75) for w in roster) / max(len(roster), 1)
                if avg_morale < 70:
                    continue

            eligible.append(template_key)

        if not eligible:
            return generated

        # Pick a random event
        chosen_key = random.choice(eligible)
        template = EVENT_TEMPLATES[chosen_key]

        # Select wrestlers if needed
        wrestlers_involved = []
        available_wrestlers = [w for w in roster if not w.get("is_injured", False)]

        if template.get("trigger_low_morale", False):
            low_morale = [w for w in available_wrestlers if w.get("morale", 75) < 40]
            if low_morale:
                wrestlers_involved.append(random.choice(low_morale))

        elif template.get("trigger_very_low_morale", False):
            very_low = [w for w in available_wrestlers if w.get("morale", 75) < 25]
            if very_low:
                wrestlers_involved.append(random.choice(very_low))

        elif template.get("requires_wrestlers", 0) > 0:
            num_needed = template["requires_wrestlers"]
            if len(available_wrestlers) >= num_needed:
                wrestlers_involved = random.sample(available_wrestlers, num_needed)

        if template.get("requires_wrestlers", 0) > 0 and len(wrestlers_involved) < template["requires_wrestlers"]:
            return generated

        # Build event
        wrestler_names = [w["name"] for w in wrestlers_involved]
        w1_name = wrestler_names[0] if len(wrestler_names) > 0 else ""
        w2_name = wrestler_names[1] if len(wrestler_names) > 1 else ""

        # Handle sponsor amount
        amount = 0
        if "amount_range" in template:
            amount = random.randint(template["amount_range"][0], template["amount_range"][1])

        title = template["title"].format(wrestler1=w1_name, wrestler2=w2_name, amount=amount)
        description = template["description"].format(wrestler1=w1_name, wrestler2=w2_name, amount=amount)

        # Build options with wrestler name substitution
        options = []
        for opt in template["options"]:
            label = opt["label"].format(wrestler1=w1_name, wrestler2=w2_name, amount=amount)
            effects = dict(opt["effects"])

            # Replace money_bonus with actual amount for sponsors
            if effects.get("money_bonus") and amount > 0:
                effects["money"] = amount
                del effects["money_bonus"]

            options.append({"label": label, "effects": effects})

        event = {
            "id": f"event_{current_week}_{chosen_key}_{self.events_generated}",
            "template_key": chosen_key,
            "category": template["category"].value,
            "severity": template["severity"].value,
            "title": title,
            "description": description,
            "wrestlers_involved": wrestler_names,
            "options": options,
            "week": current_week,
            "amount": amount,
        }

        # Set cooldown
        self.cooldowns[chosen_key] = template.get("cooldown", 4)

        self.events_generated += 1
        generated.append(event)

        # Chance for a second event if chaos is high
        if chaos_factor > 0.7 and random.random() < 0.3:
            second_events = self.generate_events(
                roster, budget, fans, prestige, current_week,
                chaos_factor * 0.5, creative_control_enabled
            )
            generated.extend(second_events)

        return generated

    def to_dict(self) -> dict:
        return {
            "cooldowns": self.cooldowns,
            "events_generated": self.events_generated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EventGenerator":
        eg = cls()
        eg.cooldowns = data.get("cooldowns", {})
        eg.events_generated = data.get("events_generated", 0)
        return eg
