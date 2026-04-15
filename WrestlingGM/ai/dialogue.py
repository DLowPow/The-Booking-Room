"""
Dialogue System - Generates contextual messages and conversations
Uses templates with variable substitution
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import random


@dataclass
class DialogueTemplate:
    """A template for generating dialogue"""
    id: str
    category: str
    mood: str  # positive, negative, neutral, any
    templates: List[str]
    variables: List[str]  # Required variables


class DialogueSystem:
    """
    Generates contextual dialogue and messages.
    Uses templates with {{variable}} substitution.
    """
    
    # ==================== WRESTLER DIALOGUE ====================
    
    SALARY_DEMAND_TEMPLATES = [
        # Polite
        "Hey boss, I've been thinking... I've been putting in solid work lately, and I feel like my pay should reflect that. What do you think about bumping me up to ${{requested_amount}} a week?",
        "I appreciate everything you've done for me, but I need to talk money. I'm looking for ${{requested_amount}} weekly. I think I've earned it.",
        
        # Assertive
        "Look, we need to talk. I've been killing it out there and my current deal doesn't cut it anymore. I want ${{requested_amount}} or we've got a problem.",
        "I've done the math. With my merch sales and the pops I get, I should be making ${{requested_amount}} at minimum. Make it happen.",
        
        # Threatening
        "I've got other offers on the table. {{rival_promotion}} is very interested. Match ${{requested_amount}} or I walk.",
        "Either you pay me what I'm worth - ${{requested_amount}} - or I start taking meetings. Your call.",
        
        # Emotional
        "I've given everything to this company! Blood, sweat, tears! And what do I get? This? I deserve ${{requested_amount}} and you know it!",
        "I can't keep doing this for pennies. My family deserves better. Please, ${{requested_amount}} would change everything.",
    ]
    
    REFUSE_TO_LOSE_TEMPLATES = [
        # Ego-driven
        "You want me to lose to {{opponent}}? Are you serious? That {{insult}} couldn't lace my boots on their best day!",
        "I'm not doing it. I'm not losing to {{opponent}}. My brand is worth more than your 'creative vision'.",
        
        # Career concern
        "Listen, if I lose clean to {{opponent}}, my stock drops. The fans won't buy me as a threat anymore. There has to be another way.",
        "I've worked too hard to lose to someone at {{opponent}}'s level. Can we at least do a DQ finish?",
        
        # Disrespectful
        "{{opponent}}? That spot monkey? I'd rather quit than make them look good.",
        "My mother hits harder than {{opponent}}. Find another jobber for your finish.",
        
        # Negotiating
        "I'll do the job, but I want something in return. Either a title shot next month or I'm not laying down.",
        "Fine, but {{opponent}} returns the favor down the line. And I want that in writing.",
    ]
    
    DEMAND_TITLE_SHOT_TEMPLATES = [
        "I've paid my dues. I've beaten everyone you put in front of me. When do I get my shot at {{championship}}?",
        "Look at the roster. Tell me one person more deserving of the {{championship}} than me. I'll wait.",
        "The fans want it. I want it. Give me {{champion}} for the {{championship}} or explain to them why not.",
        "I've been patient. Too patient. I want the {{championship}} match at the next PPV. Period.",
        "You've been dodging this conversation for weeks. I want a straight answer - when do I get {{champion}} for the belt?",
    ]
    
    THREATENS_TO_QUIT_TEMPLATES = [
        "I'm done. I'm not renewing. When my contract's up, I'm out.",
        "{{rival_promotion}} already reached out. I'm seriously considering it.",
        "Give me one reason to stay. One good reason. Because right now, I've got nothing.",
        "I've got {{weeks_remaining}} weeks left on my deal. Unless things change drastically, that's it for me here.",
        "I've loved this place, but love doesn't pay bills or win titles. I need to look out for myself.",
    ]
    
    BACKSTAGE_CONFRONTATION_TEMPLATES = [
        "{{target}}, we need to talk. NOW.",
        "You think I didn't see what you did out there, {{target}}? You tried to make me look bad!",
        "Stay out of my way, {{target}}. I'm warning you.",
        "{{target}}! You've got a lot of nerve showing your face back here after what you pulled!",
        "This ends now, {{target}}. You and me. Let's settle this right here.",
    ]
    
    POSITIVE_FEEDBACK_TEMPLATES = [
        "I just wanted to say thanks for the opportunity. I won't let you down.",
        "That match tonight? Best I've felt in years. Thank you for believing in me.",
        "The locker room feels good right now. You're doing something right, boss.",
        "I've been in this business a long time. This place? It feels like home.",
        "Whatever you need, I'm here. This company gave me a second chance and I won't forget it.",
    ]
    
    MENTOR_TEMPLATES = [
        "Hey boss, I've been working with {{protege}} lately. Kid's got potential. Maybe give them a shot?",
        "{{protege}} reminds me of myself at that age. Raw, hungry. Let me help shape them.",
        "I'd like to take {{protege}} under my wing. The business needs more people who do things the right way.",
    ]
    
    UNHAPPY_TEMPLATES = [
        "I need to be honest with you. I'm not happy with how things are going.",
        "What's the plan for me? Because right now, I feel like I'm just spinning my wheels.",
        "I came here to be a star, not to lose every week. Something needs to change.",
        "The fans are behind me, but you keep holding me back. Why?",
        "I'm trying to stay positive, but it's getting harder every week.",
    ]
    
    # ==================== MANAGEMENT MESSAGES ====================
    
    NEWS_TEMPLATES = {
        "wrestler_signed": [
            "SIGNED: {{name}} has officially joined the roster!",
            "NEW TALENT: Welcome {{name}} to the family!",
            "{{name}} has put pen to paper! They're all ours!",
        ],
        "wrestler_released": [
            "RELEASED: {{name}} has been let go from the roster.",
            "{{name}}'s time with us has come to an end.",
            "We wish {{name}} the best in their future endeavors.",
        ],
        "title_change": [
            "NEW CHAMPION! {{winner}} defeats {{loser}} to capture the {{title}}!",
            "{{winner}} is your NEW {{title}} Champion!",
            "The {{title}} has changed hands! {{winner}} dethrones {{loser}}!",
        ],
        "injury": [
            "INJURY REPORT: {{name}} has suffered a {{injury_type}}. Expected return: {{weeks}} weeks.",
            "{{name}} is injured ({{injury_type}}). They'll be out for {{weeks}} weeks.",
            "Bad news: {{name}} got hurt. {{injury_type}} - {{weeks}} weeks on the shelf.",
        ],
        "contract_expiring": [
            "ALERT: {{name}}'s contract expires in {{weeks}} weeks!",
            "Contract Warning: {{name}} - {{weeks}} weeks remaining!",
            "{{name}} is approaching free agency ({{weeks}} weeks left).",
        ],
        "milestone": [
            "MILESTONE: {{name}} has reached {{milestone}}!",
            "{{name}} achievement unlocked: {{milestone}}!",
            "Congratulations to {{name}} for {{milestone}}!",
        ],
        "show_success": [
            "Great show! The fans loved it!",
            "Another successful event in the books!",
            "The crowd went home happy tonight!",
        ],
        "show_failure": [
            "Rough night. The crowd wasn't feeling it.",
            "We need to do better. That show didn't connect.",
            "Back to the drawing board after that one.",
        ],
    }
    
    # ==================== QUEST MESSAGES ====================
    
    QUEST_TEMPLATES = {
        "build_star": {
            "title": "Star Maker",
            "description": "Build {{wrestler}} into a main event talent within {{weeks}} weeks.",
            "start": "Time to make {{wrestler}} a star. Push them to the moon!",
            "progress": "{{wrestler}} is gaining momentum. Keep it up!",
            "success": "{{wrestler}} is now a bonafide star! The investment paid off.",
            "failure": "{{wrestler}} never reached their potential. Back to the drawing board.",
        },
        "rivalry": {
            "title": "Blood Feud",
            "description": "Create a compelling rivalry between {{wrestler1}} and {{wrestler2}}.",
            "start": "Let's see if {{wrestler1}} and {{wrestler2}} can create magic.",
            "progress": "The rivalry is heating up!",
            "success": "The {{wrestler1}} vs {{wrestler2}} feud is one for the ages!",
            "failure": "The rivalry fizzled out. Fans lost interest.",
        },
        "sellout": {
            "title": "Fill The House",
            "description": "Sell out {{venue}} within the next {{weeks}} weeks.",
            "start": "Time to pack {{venue}}. Build that hype!",
            "progress": "Ticket sales are looking good!",
            "success": "SOLD OUT! {{venue}} was packed to the rafters!",
            "failure": "Empty seats at {{venue}}. Not a good look.",
        },
        "five_star": {
            "title": "Match of the Year Candidate",
            "description": "Produce a 5-star match within {{weeks}} weeks.",
            "start": "Book the right match and let them work!",
            "progress": "Some great matches, but not quite 5 stars yet.",
            "success": "FIVE STARS! A match that will be remembered forever!",
            "failure": "Good matches, but nothing legendary. The quest continues.",
        },
        "financial": {
            "title": "Money in the Bank",
            "description": "Reach a budget of ${{target}} within {{weeks}} weeks.",
            "start": "Time to get those finances in order.",
            "progress": "The money is coming in!",
            "success": "Cha-ching! The promotion is financially secure.",
            "failure": "Money's still tight. Need to tighten the belt.",
        },
    }
    
    # ==================== INSULTS ====================
    
    INSULTS = [
        "vanilla midget",
        "spot monkey",
        "green rookie",
        "has-been",
        "never-was",
        "curtain jerker",
        "jobber",
        "wannabe",
        "mark",
        "geek",
        "joke",
        "clown",
        "amateur",
    ]
    
    # ==================== RIVAL PROMOTIONS ====================
    
    RIVAL_PROMOTIONS = [
        "AEW", "WWE", "NJPW", "TNA", "ROH", "Impact",
        "MLW", "NWA", "GCW", "CMLL", "AAA",
    ]
    
    def __init__(self):
        self.message_history: List[Dict] = []
    
    def generate(
        self,
        template_category: str,
        variables: Dict,
        mood: str = "any"
    ) -> str:
        """Generate dialogue from a template category"""
        
        templates = self._get_templates(template_category)
        
        if not templates:
            return f"[No template found for: {template_category}]"
        
        template = random.choice(templates)
        
        # Add random insult if needed
        if "{{insult}}" in template:
            variables["insult"] = random.choice(self.INSULTS)
        
        # Add random rival if needed
        if "{{rival_promotion}}" in template and "rival_promotion" not in variables:
            variables["rival_promotion"] = random.choice(self.RIVAL_PROMOTIONS)
        
        # Substitute variables
        result = template
        for key, value in variables.items():
            result = result.replace("{{" + key + "}}", str(value))
        
        return result
    
    def _get_templates(self, category: str) -> List[str]:
        """Get templates for a category"""
        template_map = {
            "salary_demand": self.SALARY_DEMAND_TEMPLATES,
            "refuse_to_lose": self.REFUSE_TO_LOSE_TEMPLATES,
            "demand_title_shot": self.DEMAND_TITLE_SHOT_TEMPLATES,
            "threatens_to_quit": self.THREATENS_TO_QUIT_TEMPLATES,
            "backstage_confrontation": self.BACKSTAGE_CONFRONTATION_TEMPLATES,
            "positive_feedback": self.POSITIVE_FEEDBACK_TEMPLATES,
            "mentor": self.MENTOR_TEMPLATES,
            "unhappy": self.UNHAPPY_TEMPLATES,
        }
        return template_map.get(category, [])
    
    def generate_news(self, news_type: str, variables: Dict) -> str:
        """Generate a news message"""
        templates = self.NEWS_TEMPLATES.get(news_type, [])
        if not templates:
            return f"[News: {news_type}]"
        
        template = random.choice(templates)
        result = template
        for key, value in variables.items():
            result = result.replace("{{" + key + "}}", str(value))
        
        return result
    
    def generate_quest_text(
        self,
        quest_type: str,
        text_type: str,
        variables: Dict
    ) -> str:
        """Generate quest-related text"""
        quest_data = self.QUEST_TEMPLATES.get(quest_type, {})
        template = quest_data.get(text_type, f"[Quest {text_type}]")
        
        result = template
        for key, value in variables.items():
            result = result.replace("{{" + key + "}}", str(value))
        
        return result
    
    def generate_random_compliment(self, wrestler_name: str) -> str:
        """Generate a random compliment for a wrestler"""
        compliments = [
            f"{wrestler_name} has been a true professional.",
            f"The locker room loves {wrestler_name}.",
            f"{wrestler_name} is a natural leader.",
            f"Great attitude from {wrestler_name} lately.",
            f"{wrestler_name} always brings their A-game.",
        ]
        return random.choice(compliments)
    
    def generate_random_complaint(self, wrestler_name: str) -> str:
        """Generate a random complaint about a wrestler"""
        complaints = [
            f"{wrestler_name} has been causing problems backstage.",
            f"Some concerns about {wrestler_name}'s attitude.",
            f"{wrestler_name} seems disengaged lately.",
            f"The locker room is frustrated with {wrestler_name}.",
            f"{wrestler_name} has been difficult to work with.",
        ]
        return random.choice(complaints)
    
    def record_message(self, message_type: str, message: str, context: Dict = None):
        """Record a message for history"""
        self.message_history.append({
            "type": message_type,
            "message": message,
            "context": context or {},
        })
        
        # Keep only recent messages
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent messages"""
        return self.message_history[-count:]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            "message_history": self.message_history[-50:],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DialogueSystem":
        """Create from dictionary"""
        system = cls()
        system.message_history = data.get("message_history", [])
        return system