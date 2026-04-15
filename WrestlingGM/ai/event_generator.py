"""
Event Generator - Creates random events and incidents
Works with Creative Control and normal gameplay
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import random


class EventCategory(Enum):
    CREATIVE_CONTROL = "Creative Control"
    BUSINESS = "Business"
    ROSTER = "Roster"
    MEDIA = "Media"
    RANDOM = "Random"
    OPPORTUNITY = "Opportunity"
    CRISIS = "Crisis"


class EventSeverity(Enum):
    TRIVIAL = "Trivial"
    MINOR = "Minor"
    MODERATE = "Moderate"
    MAJOR = "Major"
    CRITICAL = "Critical"


@dataclass
class GameEvent:
    """Represents a game event that requires player attention"""
    id: str
    title: str
    category: EventCategory
    severity: EventSeverity
    description: str
    
    wrestlers_involved: List[str] = field(default_factory=list)
    options: List[Dict] = field(default_factory=list)
    deadline_weeks: int = 1
    week_created: int = 0
    is_resolved: bool = False
    resolution: str = ""
    auto_resolve_option: int = -1
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "wrestlers_involved": self.wrestlers_involved,
            "options": self.options,
            "deadline_weeks": self.deadline_weeks,
            "week_created": self.week_created,
            "is_resolved": self.is_resolved,
            "resolution": self.resolution,
            "auto_resolve_option": self.auto_resolve_option,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GameEvent":
        return cls(
            id=data["id"],
            title=data["title"],
            category=EventCategory(data["category"]),
            severity=EventSeverity(data["severity"]),
            description=data["description"],
            wrestlers_involved=data.get("wrestlers_involved", []),
            options=data.get("options", []),
            deadline_weeks=data.get("deadline_weeks", 1),
            week_created=data.get("week_created", 0),
            is_resolved=data.get("is_resolved", False),
            resolution=data.get("resolution", ""),
            auto_resolve_option=data.get("auto_resolve_option", -1),
        )


class EventGenerator:
    """
    Generates random events based on game state.
    Considers: roster personalities, finances, storylines, creative control, etc.
    """
    
    # Insults for hostile dialogue
    INSULTS = [
        "vanilla midget", "spot monkey", "green rookie", "has-been",
        "never-was", "curtain jerker", "jobber", "wannabe", "mark", "geek",
    ]
    
    # Rival promotions for dialogue
    RIVAL_PROMOTIONS = ["AEW", "WWE", "NJPW", "TNA", "ROH", "Impact", "MLW"]
    
    def __init__(
        self,
        creative_control_enabled: bool = False,
        creative_control_difficulty: str = "Normal"
    ):
        self.creative_control_enabled = creative_control_enabled
        self.cc_difficulty = creative_control_difficulty
        
        self.difficulty_mods = {
            "Easy": {"event_chance": 0.5, "positive_bias": 1.5},
            "Normal": {"event_chance": 1.0, "positive_bias": 1.0},
            "Hard": {"event_chance": 1.5, "positive_bias": 0.7},
            "Chaos": {"event_chance": 2.5, "positive_bias": 0.4},
        }
    
    def get_difficulty_mod(self, key: str) -> float:
        return self.difficulty_mods.get(self.cc_difficulty, {}).get(key, 1.0)
    
    def generate_weekly_events(
        self,
        roster: List[Dict],
        budget: int,
        fans: int,
        prestige: int,
        current_week: int,
        active_storylines: List[Dict] = None,
        recent_show_quality: float = 3.0,
    ) -> List[GameEvent]:
        """Generate events for this week based on game state"""
        events = []
        
        if self.creative_control_enabled:
            cc_events = self._generate_creative_control_events(
                roster, current_week, recent_show_quality
            )
            events.extend(cc_events)
        
        biz_events = self._generate_business_events(budget, fans, prestige, current_week)
        events.extend(biz_events)
        
        opp_events = self._generate_opportunity_events(fans, prestige, current_week)
        events.extend(opp_events)
        
        roster_events = self._generate_roster_events(roster, current_week)
        events.extend(roster_events)
        
        return events
    
    def _generate_creative_control_events(
        self,
        roster: List[Dict],
        current_week: int,
        recent_show_quality: float
    ) -> List[GameEvent]:
        """Generate Creative Control specific events"""
        events = []
        event_chance_mod = self.get_difficulty_mod("event_chance")
        
        for wrestler_data in roster:
            name = wrestler_data.get("name", "Unknown")
            
            if wrestler_data.get("is_injured"):
                continue
            
            ego = wrestler_data.get("ego", 50)
            loyalty = wrestler_data.get("loyalty", 50)
            professionalism = wrestler_data.get("professionalism", 50)
            morale = wrestler_data.get("morale", 50)
            popularity = wrestler_data.get("popularity", 50)
            
            # Calculate behavior chances
            base_chance = 0.02 * event_chance_mod
            
            # Ego-driven events
            if ego > 60 and random.random() < base_chance * (ego / 50):
                event = self._create_ego_event(wrestler_data, current_week, roster)
                if event:
                    events.append(event)
                    continue
            
            # Loyalty-driven events
            if loyalty < 40 and random.random() < base_chance * ((100 - loyalty) / 50):
                event = self._create_loyalty_event(wrestler_data, current_week)
                if event:
                    events.append(event)
                    continue
            
            # Professionalism-driven events
            if professionalism < 40 and random.random() < base_chance * ((100 - professionalism) / 50):
                event = self._create_professionalism_event(wrestler_data, current_week, roster)
                if event:
                    events.append(event)
                    continue
            
            # Morale-driven events
            if morale < 30 and random.random() < base_chance * ((100 - morale) / 50):
                event = self._create_morale_event(wrestler_data, current_week)
                if event:
                    events.append(event)
                    continue
        
        # Positive events
        positive_mod = self.get_difficulty_mod("positive_bias")
        for wrestler_data in roster:
            name = wrestler_data.get("name", "Unknown")
            professionalism = wrestler_data.get("professionalism", 50)
            loyalty = wrestler_data.get("loyalty", 50)
            
            if professionalism > 70 and random.random() < 0.02 * positive_mod:
                event = self._create_positive_event(wrestler_data, current_week, roster)
                if event:
                    events.append(event)
        
        return events
    
    def _create_ego_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create an ego-driven event"""
        name = wrestler.get("name", "Unknown")
        ego = wrestler.get("ego", 50)
        popularity = wrestler.get("popularity", 50)
        
        event_type = random.choice(["salary", "title", "refuse_lose", "main_event"])
        
        if event_type == "salary":
            return self._create_salary_demand_event(wrestler, current_week)
        elif event_type == "title":
            return self._create_demand_title_event(wrestler, current_week)
        elif event_type == "refuse_lose":
            return self._create_refuse_to_lose_event(wrestler, current_week, roster)
        elif event_type == "main_event":
            return self._create_demand_main_event(wrestler, current_week)
        
        return None
    
    def _create_loyalty_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> Optional[GameEvent]:
        """Create a loyalty-driven event"""
        return self._create_talking_to_rivals_event(wrestler, current_week)
    
    def _create_professionalism_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create a professionalism-driven event"""
        event_type = random.choice(["no_show", "drama", "business"])
        
        if event_type == "no_show":
            return self._create_no_show_event(wrestler, current_week)
        elif event_type == "drama":
            return self._create_backstage_drama_event(wrestler, current_week, roster)
        elif event_type == "business":
            return self._create_go_into_business_event(wrestler, current_week, roster)
        
        return None
    
    def _create_morale_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> Optional[GameEvent]:
        """Create a morale-driven event"""
        name = wrestler.get("name", "Unknown")
        
        return GameEvent(
            id=f"morale_{name}_{current_week}",
            title=f"😔 {name} is Unhappy",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MINOR,
            description=f"{name} has approached you expressing frustration with their current position. They feel underutilized and undervalued.",
            wrestlers_involved=[name],
            options=[
                {"text": "Promise them a push", "effects": {"morale": 15, "momentum": 10}},
                {"text": "Give them a bonus ($2,000)", "effects": {"morale": 10, "money": -2000}},
                {"text": "Have a heart-to-heart talk", "effects": {"morale": 5}},
                {"text": "Tell them to be patient", "effects": {"morale": -10}},
            ],
            deadline_weeks=2,
            week_created=current_week,
            auto_resolve_option=3,
        )
    
    def _create_positive_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create a positive event"""
        event_type = random.choice(["mentor", "exceed", "great_promo"])
        
        if event_type == "mentor":
            return self._create_mentor_event(wrestler, current_week, roster)
        elif event_type == "exceed":
            return self._create_exceed_expectations_event(wrestler, current_week)
        else:
            return self._create_great_promo_event(wrestler, current_week)
    
    def _create_salary_demand_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create a salary demand event"""
        name = wrestler.get("name", "Unknown")
        current_salary = wrestler.get("salary", 500)
        popularity = wrestler.get("popularity", 50)
        ego = wrestler.get("ego", 50)
        
        increase_percent = random.uniform(0.2, 0.5) * (1 + ego / 100)
        requested_amount = int(current_salary * (1 + increase_percent))
        
        rival = random.choice(self.RIVAL_PROMOTIONS)
        
        return GameEvent(
            id=f"salary_{name}_{current_week}",
            title=f"💰 {name} Wants a Raise",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MODERATE,
            description=f"{name} has demanded a raise to ${requested_amount:,}/week. They claim they deserve more for their contributions. They've mentioned that {rival} might be interested in their services.",
            wrestlers_involved=[name],
            options=[
                {
                    "text": f"Grant the raise (${requested_amount:,}/week)",
                    "effects": {"salary_change": requested_amount - current_salary, "morale": 15, "loyalty": 10},
                },
                {
                    "text": f"Negotiate (${int(requested_amount * 0.6):,}/week)",
                    "effects": {"salary_change": int((requested_amount - current_salary) * 0.6), "morale": 5},
                },
                {
                    "text": "Refuse the demand",
                    "effects": {"morale": -20, "loyalty": -15},
                },
                {
                    "text": "Release them",
                    "effects": {"release": True},
                },
            ],
            deadline_weeks=2,
            week_created=current_week,
            auto_resolve_option=2,
        )
    
    def _create_refuse_to_lose_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create a refuses to lose event"""
        name = wrestler.get("name", "Unknown")
        
        potential_opponents = [w for w in roster if w.get("name") != name and not w.get("is_injured")]
        if not potential_opponents:
            return None
        
        opponent = random.choice(potential_opponents)
        opponent_name = opponent.get("name", "Unknown")
        insult = random.choice(self.INSULTS)
        
        return GameEvent(
            id=f"refuse_lose_{name}_{current_week}",
            title=f"⚠️ {name} Refuses to Lose",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MAJOR,
            description=f'{name} is refusing to lose to {opponent_name} tonight. They said: "You want me to lose to that {insult}? Not happening."',
            wrestlers_involved=[name, opponent_name],
            options=[
                {
                    "text": f"Fine, {name} wins instead",
                    "effects": {"change_finish": True, "wrestler_morale": 10, "opponent_morale": -15, "ego": 5},
                },
                {
                    "text": "Book a DQ/interference finish",
                    "effects": {"compromise_finish": True, "wrestler_morale": 0, "opponent_morale": -5},
                },
                {
                    "text": "Insist they follow the script",
                    "effects": {"force_compliance": True, "morale": -20, "loyalty": -10},
                },
                {
                    "text": "Pull them from the match",
                    "effects": {"remove_from_match": True, "morale": -25, "momentum": -15},
                },
            ],
            deadline_weeks=0,
            week_created=current_week,
            auto_resolve_option=1,
        )
    
    def _create_demand_title_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create a demand title shot event"""
        name = wrestler.get("name", "Unknown")
        
        return GameEvent(
            id=f"title_demand_{name}_{current_week}",
            title=f"🏆 {name} Demands a Title Shot",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MINOR,
            description=f"{name} has approached you demanding a championship opportunity. They feel they've earned it and won't take no for an answer.",
            wrestlers_involved=[name],
            options=[
                {"text": "Book the title match", "effects": {"book_title_match": True, "morale": 20, "ego": 5}},
                {"text": "Promise a future opportunity", "effects": {"morale": 5}},
                {"text": "Explain they need to earn it", "effects": {"morale": -10}},
                {"text": "Tell them they're not ready", "effects": {"morale": -20, "loyalty": -10}},
            ],
            deadline_weeks=2,
            week_created=current_week,
            auto_resolve_option=2,
        )
    
    def _create_demand_main_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create a demand main event spot event"""
        name = wrestler.get("name", "Unknown")
        
        return GameEvent(
            id=f"main_event_{name}_{current_week}",
            title=f"⭐ {name} Demands Main Event Spot",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MINOR,
            description=f"{name} is frustrated with their position on the card. They want to be in the main event scene and are making it known.",
            wrestlers_involved=[name],
            options=[
                {"text": "Promise main event push", "effects": {"morale": 15, "momentum": 15}},
                {"text": "Explain the plan for them", "effects": {"morale": 5}},
                {"text": "Tell them to earn it", "effects": {"morale": -15}},
            ],
            deadline_weeks=2,
            week_created=current_week,
            auto_resolve_option=2,
        )
    
    def _create_talking_to_rivals_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create a talking to rivals event"""
        name = wrestler.get("name", "Unknown")
        weeks_left = wrestler.get("contract_length", 52)
        rival = random.choice(self.RIVAL_PROMOTIONS)
        
        return GameEvent(
            id=f"rival_talk_{name}_{current_week}",
            title=f"📞 {name} Talking to {rival}",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MODERATE,
            description=f"Word has reached you that {name} has been in discussions with {rival}. Their contract expires in {weeks_left} weeks.",
            wrestlers_involved=[name],
            options=[
                {
                    "text": "Offer contract extension with raise",
                    "effects": {"extend_contract": 52, "salary_increase": 0.25, "loyalty": 15},
                },
                {"text": "Have a heart-to-heart talk", "effects": {"loyalty": 5, "morale": 5}},
                {"text": "Push them stronger", "effects": {"momentum": 20, "loyalty": 10}},
                {"text": "Ignore it", "effects": {"loyalty": -10}},
            ],
            deadline_weeks=4,
            week_created=current_week,
            auto_resolve_option=3,
        )
    
    def _create_backstage_drama_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create a backstage confrontation event"""
        name = wrestler.get("name", "Unknown")
        
        potential_targets = [w for w in roster if w.get("name") != name]
        if not potential_targets:
            return None
        
        target = random.choice(potential_targets)
        target_name = target.get("name", "Unknown")
        
        reasons = [
            "over a perceived slight during last week's match",
            "about getting more TV time",
            "over comments made in an interview",
            "that's been brewing for weeks",
            "over locker room pecking order",
        ]
        
        return GameEvent(
            id=f"confrontation_{name}_{current_week}",
            title=f"😤 Backstage Confrontation",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MODERATE,
            description=f"{name} and {target_name} got into a heated argument backstage {random.choice(reasons)}.",
            wrestlers_involved=[name, target_name],
            options=[
                {"text": "Fine both wrestlers ($1,000 each)", "effects": {"fine_amount": 2000, "wrestler_morale": -10, "target_morale": -10}},
                {"text": f"Side with {name}", "effects": {"wrestler_morale": 10, "target_morale": -25}},
                {"text": f"Side with {target_name}", "effects": {"wrestler_morale": -25, "target_morale": 10}},
                {"text": "Turn it into a storyline", "effects": {"wrestler_morale": 5, "target_morale": 5, "creates_feud": True}},
            ],
            deadline_weeks=1,
            week_created=current_week,
            auto_resolve_option=0,
        )
    
    def _create_no_show_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create a no-show event"""
        name = wrestler.get("name", "Unknown")
        salary = wrestler.get("salary", 500)
        
        return GameEvent(
            id=f"no_show_{name}_{current_week}",
            title=f"❌ {name} No-Shows Event",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.MAJOR,
            description=f"{name} didn't show up to tonight's event! No call, no explanation. The card had to be restructured last minute.",
            wrestlers_involved=[name],
            options=[
                {"text": f"Fine them (${salary:,})", "effects": {"fine_amount": salary, "morale": -15}},
                {"text": "Suspend them (2 weeks)", "effects": {"suspend_weeks": 2}},
                {"text": "Fire them immediately", "effects": {"release": True}},
                {"text": "Wait for their explanation", "effects": {"roster_morale": -5}},
            ],
            deadline_weeks=1,
            week_created=current_week,
            auto_resolve_option=0,
        )
    
    def _create_go_into_business_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create a went into business for themselves event"""
        name = wrestler.get("name", "Unknown")
        salary = wrestler.get("salary", 500)
        
        potential_victims = [w for w in roster if w.get("name") != name]
        if not potential_victims:
            return None
        
        victim = random.choice(potential_victims)
        victim_name = victim.get("name", "Unknown")
        
        return GameEvent(
            id=f"business_{name}_{current_week}",
            title=f"🚨 {name} Went Into Business For Themselves!",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.CRITICAL,
            description=f"CRITICAL: {name} ignored the planned finish and pinned {victim_name} clean, completely going off script! This has embarrassed {victim_name} and thrown your storylines into chaos.",
            wrestlers_involved=[name, victim_name],
            options=[
                {"text": f"Fine them heavily (${salary * 2:,})", "effects": {"fine_amount": salary * 2, "morale": -30}},
                {"text": "Suspend without pay (4 weeks)", "effects": {"suspend_weeks": 4, "morale": -25}},
                {"text": "Fire them on the spot", "effects": {"release": True}},
                {"text": "Let it slide", "effects": {"roster_morale": -15, "ego": 10, "victim_morale": -30}},
            ],
            deadline_weeks=0,
            week_created=current_week,
            auto_resolve_option=0,
        )
    
    def _create_mentor_event(
        self,
        wrestler: Dict,
        current_week: int,
        roster: List[Dict]
    ) -> Optional[GameEvent]:
        """Create a positive mentoring event"""
        name = wrestler.get("name", "Unknown")
        
        young_wrestlers = [
            w for w in roster
            if w.get("name") != name
            and w.get("age", 30) < 28
            and w.get("popularity", 50) < 60
        ]
        
        if not young_wrestlers:
            return None
        
        protege = random.choice(young_wrestlers)
        protege_name = protege.get("name", "Unknown")
        
        return GameEvent(
            id=f"mentor_{name}_{current_week}",
            title=f"✨ {name} is Mentoring {protege_name}",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.TRIVIAL,
            description=f"Great news! {name} has taken {protege_name} under their wing and is helping them improve. The locker room atmosphere is positive.",
            wrestlers_involved=[name, protege_name],
            options=[
                {"text": "Officially recognize their leadership", "effects": {"wrestler_morale": 15, "protege_improvement": 5, "roster_morale": 5}},
                {"text": "Give them a bonus ($3,000)", "effects": {"bonus": 3000, "wrestler_morale": 10}},
                {"text": "Thank them privately", "effects": {"wrestler_morale": 5, "loyalty": 5}},
            ],
            deadline_weeks=4,
            week_created=current_week,
            auto_resolve_option=2,
        )
    
    def _create_exceed_expectations_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create an exceeds expectations event"""
        name = wrestler.get("name", "Unknown")
        
        return GameEvent(
            id=f"exceed_{name}_{current_week}",
            title=f"⭐ {name} Exceeds Expectations",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.TRIVIAL,
            description=f"{name} has been going above and beyond lately! Their work ethic and performances have been exceptional.",
            wrestlers_involved=[name],
            options=[
                {"text": "Reward with a bonus ($5,000)", "effects": {"bonus": 5000, "morale": 20, "loyalty": 15}},
                {"text": "Give them a push", "effects": {"momentum": 15, "morale": 15}},
                {"text": "Publicly praise them", "effects": {"morale": 10, "popularity": 5}},
                {"text": "Acknowledge privately", "effects": {"morale": 5}},
            ],
            deadline_weeks=4,
            week_created=current_week,
            auto_resolve_option=3,
        )
    
    def _create_great_promo_event(
        self,
        wrestler: Dict,
        current_week: int
    ) -> GameEvent:
        """Create a great promo event"""
        name = wrestler.get("name", "Unknown")
        
        return GameEvent(
            id=f"promo_{name}_{current_week}",
            title=f"🎤 {name} Cuts Amazing Promo",
            category=EventCategory.CREATIVE_CONTROL,
            severity=EventSeverity.TRIVIAL,
            description=f"{name} just delivered an incredible promo! Fans are buzzing about it online and it's generating great word of mouth.",
            wrestlers_involved=[name],
            options=[
                {"text": "Feature them more prominently", "effects": {"momentum": 20, "popularity": 10}},
                {"text": "Build a storyline around it", "effects": {"momentum": 15}},
                {"text": "Praise them backstage", "effects": {"morale": 10}},
            ],
            deadline_weeks=2,
            week_created=current_week,
            auto_resolve_option=2,
        )
    
    def _generate_business_events(
        self,
        budget: int,
        fans: int,
        prestige: int,
        current_week: int
    ) -> List[GameEvent]:
        """Generate business-related events"""
        events = []
        
        if budget < 10000 and random.random() < 0.3:
            events.append(GameEvent(
                id=f"low_budget_{current_week}",
                title="💸 Financial Warning",
                category=EventCategory.BUSINESS,
                severity=EventSeverity.MAJOR,
                description=f"Your budget is dangerously low (${budget:,}). You may need to cut costs or risk bankruptcy.",
                options=[
                    {"text": "Cut production costs", "effects": {"production_cut": True}},
                    {"text": "Release some talent", "effects": {"suggest_releases": True}},
                    {"text": "Take a loan ($50,000)", "effects": {"loan": 50000, "debt": True}},
                    {"text": "Push through", "effects": {}},
                ],
                deadline_weeks=2,
                week_created=current_week,
            ))
        
        if fans > 5000 and random.random() < 0.05:
            sponsor_amount = int(fans * random.uniform(0.5, 1.5))
            events.append(GameEvent(
                id=f"sponsor_{current_week}",
                title="🤝 Sponsorship Offer",
                category=EventCategory.OPPORTUNITY,
                severity=EventSeverity.MINOR,
                description=f"A local business wants to sponsor your promotion! They're offering ${sponsor_amount:,} for logo placement.",
                options=[
                    {"text": "Accept the deal", "effects": {"money": sponsor_amount, "prestige": -2}},
                    {"text": "Negotiate for more", "effects": {"money": int(sponsor_amount * 1.3)}},
                    {"text": "Decline", "effects": {"prestige": 2}},
                ],
                deadline_weeks=2,
                week_created=current_week,
            ))
        
        return events
    
    def _generate_opportunity_events(
        self,
        fans: int,
        prestige: int,
        current_week: int
    ) -> List[GameEvent]:
        """Generate opportunity events"""
        events = []
        
        if random.random() < 0.03:
            events.append(GameEvent(
                id=f"media_{current_week}",
                title="📰 Media Opportunity",
                category=EventCategory.MEDIA,
                severity=EventSeverity.MINOR,
                description="A wrestling podcast wants to interview you about your promotion. This could be good exposure!",
                options=[
                    {"text": "Do the interview", "effects": {"fans": 200, "prestige": 3}},
                    {"text": "Send a wrestler instead", "effects": {"fans": 100}},
                    {"text": "Decline", "effects": {}},
                ],
                deadline_weeks=1,
                week_created=current_week,
            ))
        
        if random.random() < 0.02:
            events.append(GameEvent(
                id=f"charity_{current_week}",
                title="🎗️ Charity Opportunity",
                category=EventCategory.OPPORTUNITY,
                severity=EventSeverity.MINOR,
                description="A local charity wants you to participate in a fundraiser event.",
                options=[
                    {"text": "Participate fully", "effects": {"money": -2000, "prestige": 10, "fans": 500}},
                    {"text": "Send a few wrestlers", "effects": {"money": -500, "prestige": 5, "fans": 200}},
                    {"text": "Donate money only", "effects": {"money": -1000, "prestige": 3}},
                    {"text": "Politely decline", "effects": {}},
                ],
                deadline_weeks=2,
                week_created=current_week,
            ))
        
        return events
    
    def _generate_roster_events(
        self,
        roster: List[Dict],
        current_week: int
    ) -> List[GameEvent]:
        """Generate general roster events"""
        events = []
        
        for wrestler in roster:
            name = wrestler.get("name", "Unknown")
            weeks_left = wrestler.get("contract_length", 52)
            
            if weeks_left == 8:
                events.append(GameEvent(
                    id=f"contract_warning_{name}_{current_week}",
                    title=f"📋 Contract Expiring: {name}",
                    category=EventCategory.ROSTER,
                    severity=EventSeverity.MODERATE,
                    description=f"{name}'s contract expires in 8 weeks. You should consider their future.",
                    wrestlers_involved=[name],
                    options=[
                        {"text": "Open renewal negotiations", "effects": {"negotiate_renewal": True}},
                        {"text": "Let it expire", "effects": {}},
                    ],
                    deadline_weeks=8,
                    week_created=current_week,
                ))
        
        for wrestler in roster:
            if wrestler.get("is_injured") and wrestler.get("injury_weeks_remaining") == 1:
                name = wrestler.get("name", "Unknown")
                events.append(GameEvent(
                    id=f"recovery_{name}_{current_week}",
                    title=f"🏥 {name} Ready to Return",
                    category=EventCategory.ROSTER,
                    severity=EventSeverity.TRIVIAL,
                    description=f"Good news! {name} has recovered and is cleared to compete!",
                    wrestlers_involved=[name],
                    options=[
                        {"text": "Welcome them back", "effects": {"morale": 10}},
                    ],
                    deadline_weeks=1,
                    week_created=current_week,
                ))
        
        return events
    
    def to_dict(self) -> dict:
        return {
            "creative_control_enabled": self.creative_control_enabled,
            "cc_difficulty": self.cc_difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EventGenerator":
        return cls(
            creative_control_enabled=data.get("creative_control_enabled", False),
            creative_control_difficulty=data.get("cc_difficulty", "Normal"),
        )