"""
Creative Control System
When enabled, wrestlers have agency and can cause chaos!
"""

import random
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from classes.wrestler import Wrestler
from classes.enums import Alignment


class IncidentType(Enum):
    # Money Issues
    SALARY_DEMAND = "Salary Demand"
    CONTRACT_HOLDOUT = "Contract Holdout"
    
    # Creative Disputes
    REFUSE_TO_LOSE = "Refusing to Lose"
    SHOOT_PROMO = "Shoots on Company"
    GOES_INTO_BUSINESS = "Goes Into Business For Themselves"
    REFUSES_STORYLINE = "Refuses Storyline"
    
    # Ego Problems
    DEMANDS_TITLE_SHOT = "Demands Title Shot"
    DEMANDS_MAIN_EVENT = "Demands Main Event Spot"
    BACKSTAGE_CONFRONTATION = "Backstage Confrontation"
    BURIES_OPPONENT = "Buries Opponent on Mic"
    
    # Departure Threats
    THREATENS_TO_QUIT = "Threatens to Quit"
    TALKS_TO_RIVALS = "Talking to Rival Promotions"
    NO_SHOWS = "No-Shows Event"
    WALKS_OUT = "Walks Out"
    TAKES_TITLE_TO_RIVAL = "Takes Championship to Rival"
    
    # Positive Events (rare)
    EXCEEDS_EXPECTATIONS = "Exceeds Expectations"
    MENTORS_YOUNG_TALENT = "Mentors Young Talent"
    ACCEPTS_PAYCUT = "Accepts Pay Cut for Company"
    GREAT_PROMO = "Cuts Career-Defining Promo"


class IncidentSeverity(Enum):
    MINOR = "Minor"       # Slight annoyance
    MODERATE = "Moderate" # Needs attention
    MAJOR = "Major"       # Serious problem
    CRITICAL = "Critical" # Crisis mode
    POSITIVE = "Positive" # Good thing!


@dataclass
class Incident:
    """Represents a creative control incident"""
    incident_type: IncidentType
    severity: IncidentSeverity
    wrestler: Wrestler
    target: Optional[Wrestler]  # For confrontations
    description: str
    options: List[Dict]  # Player response options
    deadline_weeks: int  # Weeks to respond before auto-resolution
    consequences: Dict   # What happens if ignored


class CreativeControlSystem:
    """
    Manages all creative control incidents and wrestler agency.
    Only active when Creative Control mode is enabled.
    """
    
    def __init__(self, enabled: bool = False, difficulty: str = "Normal"):
        self.enabled = enabled
        self.difficulty = difficulty
        self.active_incidents: List[Incident] = []
        self.incident_history: List[Dict] = []
        
        # Difficulty modifiers
        self.difficulty_modifiers = {
            "Easy": {
                "incident_chance": 0.5,
                "severity_modifier": 0.7,
                "positive_chance": 1.5,
            },
            "Normal": {
                "incident_chance": 1.0,
                "severity_modifier": 1.0,
                "positive_chance": 1.0,
            },
            "Hard": {
                "incident_chance": 1.5,
                "severity_modifier": 1.3,
                "positive_chance": 0.7,
            },
            "Chaos": {
                "incident_chance": 2.0,
                "severity_modifier": 1.5,
                "positive_chance": 0.5,
            },
        }
    
    def get_modifier(self, key: str) -> float:
        """Get difficulty modifier"""
        mods = self.difficulty_modifiers.get(self.difficulty, {})
        return mods.get(key, 1.0)
    
    def check_for_incidents(self, roster: List[Wrestler], week: int) -> List[Incident]:
        """
        Check roster for potential incidents this week.
        Called during weekly update.
        """
        if not self.enabled:
            return []
        
        new_incidents = []
        
        for wrestler in roster:
            if wrestler.is_injured:
                continue  # Injured wrestlers cause fewer problems
            
            incident = self._evaluate_wrestler(wrestler, roster, week)
            if incident:
                new_incidents.append(incident)
                self.active_incidents.append(incident)
        
        return new_incidents
    
    def _evaluate_wrestler(
        self, 
        wrestler: Wrestler, 
        roster: List[Wrestler],
        week: int
    ) -> Optional[Incident]:
        """Evaluate if a wrestler causes an incident this week"""
        
        # Base chance modified by difficulty
        base_chance = 0.03 * self.get_modifier("incident_chance")  # 3% base
        
        # Wrestler personality modifiers
        ego_factor = wrestler.ego / 100
        loyalty_factor = (100 - wrestler.loyalty) / 100
        prof_factor = (100 - wrestler.professionalism) / 100
        morale_factor = (100 - wrestler.morale) / 100
        
        # High popularity wrestlers are more likely to cause trouble
        popularity_factor = wrestler.popularity / 200  # 0 to 0.5
        
        # Calculate final chance
        incident_chance = base_chance * (
            1 + ego_factor + loyalty_factor + prof_factor + morale_factor + popularity_factor
        )
        
        # Stars cause more problems
        if wrestler.popularity > 80:
            incident_chance *= 1.3
        if wrestler.popularity > 90:
            incident_chance *= 1.2
        
        # Low momentum wrestlers get frustrated
        if wrestler.momentum < 30:
            incident_chance *= 1.4
        
        # Contract running out
        if wrestler.contract_length < 8:
            incident_chance *= 1.5
        
        # Roll the dice
        if random.random() > incident_chance:
            return None
        
        # Determine incident type
        return self._generate_incident(wrestler, roster)
    
    def _generate_incident(
        self, 
        wrestler: Wrestler, 
        roster: List[Wrestler]
    ) -> Incident:
        """Generate a specific incident for a wrestler"""
        
        # Weight incidents based on wrestler personality
        weighted_incidents = []
        
        # High ego incidents
        if wrestler.ego > 60:
            weighted_incidents.extend([
                (IncidentType.DEMANDS_TITLE_SHOT, 3),
                (IncidentType.DEMANDS_MAIN_EVENT, 3),
                (IncidentType.REFUSE_TO_LOSE, 2),
                (IncidentType.BURIES_OPPONENT, 2),
            ])
        
        # Low loyalty incidents
        if wrestler.loyalty < 50:
            weighted_incidents.extend([
                (IncidentType.TALKS_TO_RIVALS, 3),
                (IncidentType.THREATENS_TO_QUIT, 2),
                (IncidentType.WALKS_OUT, 1),
            ])
        
        # Low professionalism
        if wrestler.professionalism < 50:
            weighted_incidents.extend([
                (IncidentType.NO_SHOWS, 2),
                (IncidentType.SHOOT_PROMO, 2),
                (IncidentType.GOES_INTO_BUSINESS, 2),
            ])
        
        # Money issues (everyone can have these)
        weighted_incidents.extend([
            (IncidentType.SALARY_DEMAND, 2),
            (IncidentType.CONTRACT_HOLDOUT, 1),
        ])
        
        # Low morale
        if wrestler.morale < 40:
            weighted_incidents.extend([
                (IncidentType.REFUSES_STORYLINE, 2),
                (IncidentType.THREATENS_TO_QUIT, 2),
            ])
        
        # Positive incidents (modified by loyalty and professionalism)
        positive_chance = (wrestler.loyalty + wrestler.professionalism) / 200
        positive_chance *= self.get_modifier("positive_chance")
        
        if random.random() < positive_chance:
            weighted_incidents = [
                (IncidentType.EXCEEDS_EXPECTATIONS, 3),
                (IncidentType.MENTORS_YOUNG_TALENT, 2),
                (IncidentType.ACCEPTS_PAYCUT, 1),
                (IncidentType.GREAT_PROMO, 2),
            ]
        
        # Default fallback
        if not weighted_incidents:
            weighted_incidents = [
                (IncidentType.SALARY_DEMAND, 1),
                (IncidentType.BACKSTAGE_CONFRONTATION, 1),
            ]
        
        # Weighted random selection
        total_weight = sum(w for _, w in weighted_incidents)
        roll = random.uniform(0, total_weight)
        
        current = 0
        selected_type = weighted_incidents[0][0]
        for incident_type, weight in weighted_incidents:
            current += weight
            if roll <= current:
                selected_type = incident_type
                break
        
        # Generate the full incident
        return self._create_incident(selected_type, wrestler, roster)
    
    def _create_incident(
        self,
        incident_type: IncidentType,
        wrestler: Wrestler,
        roster: List[Wrestler]
    ) -> Incident:
        """Create a complete incident with options and consequences"""
        
        # Get a potential target for confrontations
        target = None
        if incident_type in [
            IncidentType.BACKSTAGE_CONFRONTATION,
            IncidentType.REFUSE_TO_LOSE,
            IncidentType.BURIES_OPPONENT,
        ]:
            potential_targets = [w for w in roster if w != wrestler and not w.is_injured]
            if potential_targets:
                target = random.choice(potential_targets)
        
        # Build incident based on type
        incident_data = self._get_incident_data(incident_type, wrestler, target)
        
        return Incident(
            incident_type=incident_type,
            severity=incident_data["severity"],
            wrestler=wrestler,
            target=target,
            description=incident_data["description"],
            options=incident_data["options"],
            deadline_weeks=incident_data["deadline"],
            consequences=incident_data["consequences"],
        )
    
    def _get_incident_data(
        self,
        incident_type: IncidentType,
        wrestler: Wrestler,
        target: Optional[Wrestler]
    ) -> Dict:
        """Get full incident data based on type"""
        
        # Calculate salary demand amount
        salary_increase = int(wrestler.salary * random.uniform(0.2, 0.5))
        
        incidents = {
            IncidentType.SALARY_DEMAND: {
                "severity": IncidentSeverity.MODERATE,
                "description": f"{wrestler.name} is demanding a raise of ${salary_increase:,}/week, "
                              f"claiming they deserve more for their contributions.",
                "options": [
                    {
                        "text": f"Grant the raise (${salary_increase:,}/week)",
                        "effect": "salary_increase",
                        "value": salary_increase,
                        "morale_change": 15,
                        "loyalty_change": 10,
                    },
                    {
                        "text": "Negotiate (50% of demand)",
                        "effect": "salary_increase",
                        "value": salary_increase // 2,
                        "morale_change": 5,
                        "loyalty_change": 0,
                    },
                    {
                        "text": "Refuse the demand",
                        "effect": "none",
                        "morale_change": -20,
                        "loyalty_change": -15,
                    },
                    {
                        "text": "Release them immediately",
                        "effect": "release",
                        "morale_change": 0,
                        "loyalty_change": 0,
                    },
                ],
                "deadline": 2,
                "consequences": {
                    "morale_loss": 25,
                    "loyalty_loss": 20,
                    "possible_quit": True,
                },
            },
            
            IncidentType.REFUSE_TO_LOSE: {
                "severity": IncidentSeverity.MAJOR,
                "description": f"{wrestler.name} is refusing to lose to "
                              f"{target.name if target else 'their scheduled opponent'} tonight. "
                              f"They believe it would damage their credibility.",
                "options": [
                    {
                        "text": "Change the finish (they win)",
                        "effect": "change_finish",
                        "morale_change": 10,
                        "target_morale_change": -15,
                        "ego_change": 5,
                    },
                    {
                        "text": "Book a DQ/interference finish",
                        "effect": "compromise_finish",
                        "morale_change": 0,
                        "target_morale_change": -5,
                    },
                    {
                        "text": "Insist they follow the script",
                        "effect": "force_compliance",
                        "morale_change": -20,
                        "loyalty_change": -10,
                        "possible_shoot": True,
                    },
                    {
                        "text": "Pull them from the match",
                        "effect": "remove_from_match",
                        "morale_change": -25,
                        "momentum_change": -15,
                    },
                ],
                "deadline": 0,  # Immediate
                "consequences": {
                    "possible_shoot": True,
                    "ruins_storyline": True,
                },
            },
            
            IncidentType.GOES_INTO_BUSINESS: {
                "severity": IncidentSeverity.CRITICAL,
                "description": f"{wrestler.name} went into business for themselves during the match! "
                              f"They ignored the planned finish and pinned "
                              f"{target.name if target else 'their opponent'} clean.",
                "options": [
                    {
                        "text": "Fine them heavily (2 weeks salary)",
                        "effect": "fine",
                        "value": wrestler.salary * 2,
                        "morale_change": -30,
                    },
                    {
                        "text": "Suspend without pay (4 weeks)",
                        "effect": "suspend",
                        "value": 4,
                        "morale_change": -25,
                    },
                    {
                        "text": "Fire them on the spot",
                        "effect": "release",
                    },
                    {
                        "text": "Let it slide (preserve relationship)",
                        "effect": "none",
                        "roster_morale_change": -10,
                        "ego_change": 10,
                    },
                ],
                "deadline": 0,
                "consequences": {
                    "storyline_ruined": True,
                    "target_momentum_loss": 20,
                },
            },
            
            IncidentType.TALKS_TO_RIVALS: {
                "severity": IncidentSeverity.MODERATE,
                "description": f"Word has reached you that {wrestler.name} has been in contact "
                              f"with rival promotions. They may be testing their market value.",
                "options": [
                    {
                        "text": "Offer a contract extension with raise",
                        "effect": "extend_contract",
                        "salary_increase": int(wrestler.salary * 0.25),
                        "contract_add": 52,
                        "loyalty_change": 15,
                    },
                    {
                        "text": "Have a heart-to-heart talk",
                        "effect": "talk",
                        "loyalty_change": 5,
                        "morale_change": 5,
                    },
                    {
                        "text": "Push them stronger (main event)",
                        "effect": "push",
                        "momentum_change": 20,
                        "loyalty_change": 10,
                    },
                    {
                        "text": "Ignore it (their contract is binding)",
                        "effect": "none",
                        "loyalty_change": -10,
                    },
                ],
                "deadline": 4,
                "consequences": {
                    "possible_quit": True,
                    "loyalty_decay": 5,
                },
            },
            
            IncidentType.TAKES_TITLE_TO_RIVAL: {
                "severity": IncidentSeverity.CRITICAL,
                "description": f"CRISIS: {wrestler.name} has left the company and taken the championship "
                              f"to a rival promotion! This is a PR nightmare!",
                "options": [
                    {
                        "text": "Take legal action (expensive)",
                        "effect": "legal",
                        "cost": 50000,
                        "prestige_change": -5,
                    },
                    {
                        "text": "Crown a new champion immediately",
                        "effect": "new_champion",
                        "prestige_change": -15,
                    },
                    {
                        "text": "Create a new championship",
                        "effect": "new_title",
                        "prestige_change": -10,
                        "cost": 10000,
                    },
                ],
                "deadline": 0,
                "consequences": {
                    "title_vacated": True,
                    "prestige_loss": 25,
                    "fan_loss": 500,
                },
            },
            
            IncidentType.DEMANDS_TITLE_SHOT: {
                "severity": IncidentSeverity.MINOR,
                "description": f"{wrestler.name} has approached you demanding a championship opportunity. "
                              f"They feel they've earned it.",
                "options": [
                    {
                        "text": "Book the title match",
                        "effect": "book_title_match",
                        "morale_change": 20,
                        "ego_change": 5,
                    },
                    {
                        "text": "Promise a future opportunity",
                        "effect": "promise",
                        "morale_change": 5,
                    },
                    {
                        "text": "Explain they need to earn it",
                        "effect": "deny",
                        "morale_change": -10,
                    },
                    {
                        "text": "Tell them they're not ready",
                        "effect": "deny_harsh",
                        "morale_change": -20,
                        "loyalty_change": -10,
                    },
                ],
                "deadline": 2,
                "consequences": {
                    "morale_loss": 15,
                },
            },
            
            IncidentType.BACKSTAGE_CONFRONTATION: {
                "severity": IncidentSeverity.MODERATE,
                "description": f"Tensions boiled over backstage! {wrestler.name} and "
                              f"{target.name if target else 'another wrestler'} got into a heated "
                              f"confrontation that nearly turned physical.",
                "options": [
                    {
                        "text": "Fine both wrestlers",
                        "effect": "fine_both",
                        "value": 1000,
                        "morale_change": -10,
                        "target_morale_change": -10,
                    },
                    {
                        "text": "Side with {wrestler.name}",
                        "effect": "side_wrestler",
                        "morale_change": 10,
                        "target_morale_change": -25,
                    },
                    {
                        "text": f"Side with {target.name if target else 'the other wrestler'}",
                        "effect": "side_target",
                        "morale_change": -25,
                        "target_morale_change": 10,
                    },
                    {
                        "text": "Turn it into a storyline",
                        "effect": "storyline",
                        "morale_change": 5,
                        "target_morale_change": 5,
                        "creates_feud": True,
                    },
                ],
                "deadline": 1,
                "consequences": {
                    "ongoing_heat": True,
                },
            },
            
            IncidentType.NO_SHOWS: {
                "severity": IncidentSeverity.MAJOR,
                "description": f"{wrestler.name} didn't show up to tonight's event! "
                              f"No call, no explanation. The card had to be restructured.",
                "options": [
                    {
                        "text": "Fine them (1 week salary)",
                        "effect": "fine",
                        "value": wrestler.salary,
                        "morale_change": -15,
                    },
                    {
                        "text": "Suspend them (2 weeks)",
                        "effect": "suspend",
                        "value": 2,
                    },
                    {
                        "text": "Fire them immediately",
                        "effect": "release",
                    },
                    {
                        "text": "Wait for their explanation",
                        "effect": "wait",
                        "roster_morale_change": -5,
                    },
                ],
                "deadline": 1,
                "consequences": {
                    "show_quality_penalty": True,
                },
            },
            
            IncidentType.SHOOT_PROMO: {
                "severity": IncidentSeverity.MAJOR,
                "description": f"{wrestler.name} went off-script during their promo and shot on "
                              f"the company! They aired legitimate grievances on live TV.",
                "options": [
                    {
                        "text": "Embrace it (worked shoot angle)",
                        "effect": "embrace",
                        "publicity_boost": 20,
                        "controversy": True,
                    },
                    {
                        "text": "Suspend them publicly",
                        "effect": "suspend",
                        "value": 2,
                        "publicity_boost": 10,
                    },
                    {
                        "text": "Handle it privately (fine)",
                        "effect": "fine",
                        "value": wrestler.salary,
                        "morale_change": -15,
                    },
                    {
                        "text": "Fire them (send a message)",
                        "effect": "release",
                        "roster_morale_change": -10,
                    },
                ],
                "deadline": 0,
                "consequences": {
                    "media_attention": True,
                },
            },
            
            # POSITIVE INCIDENTS
            IncidentType.EXCEEDS_EXPECTATIONS: {
                "severity": IncidentSeverity.POSITIVE,
                "description": f"{wrestler.name} has been going above and beyond lately! "
                              f"Their work ethic and performances have been exceptional.",
                "options": [
                    {
                        "text": "Reward with a bonus",
                        "effect": "bonus",
                        "value": 5000,
                        "morale_change": 20,
                        "loyalty_change": 15,
                    },
                    {
                        "text": "Give them a push",
                        "effect": "push",
                        "momentum_change": 15,
                        "morale_change": 15,
                    },
                    {
                        "text": "Publicly praise them",
                        "effect": "praise",
                        "morale_change": 10,
                        "popularity_change": 5,
                    },
                    {
                        "text": "Acknowledge privately",
                        "effect": "none",
                        "morale_change": 5,
                    },
                ],
                "deadline": 4,
                "consequences": {},
            },
            
            IncidentType.MENTORS_YOUNG_TALENT: {
                "severity": IncidentSeverity.POSITIVE,
                "description": f"{wrestler.name} has taken younger talent under their wing. "
                              f"The locker room atmosphere has improved.",
                "options": [
                    {
                        "text": "Officially recognize their leadership",
                        "effect": "leadership_role",
                        "morale_change": 15,
                        "roster_morale_change": 10,
                    },
                    {
                        "text": "Bonus for extra effort",
                        "effect": "bonus",
                        "value": 3000,
                        "morale_change": 10,
                    },
                    {
                        "text": "Thank them personally",
                        "effect": "none",
                        "morale_change": 5,
                        "loyalty_change": 5,
                    },
                ],
                "deadline": 4,
                "consequences": {},
            },
            
            IncidentType.GREAT_PROMO: {
                "severity": IncidentSeverity.POSITIVE,
                "description": f"{wrestler.name} just delivered an incredible promo! "
                              f"Fans are buzzing about it online.",
                "options": [
                    {
                        "text": "Feature them more prominently",
                        "effect": "push",
                        "momentum_change": 20,
                        "popularity_change": 10,
                    },
                    {
                        "text": "Build a storyline around it",
                        "effect": "storyline",
                        "momentum_change": 15,
                    },
                    {
                        "text": "Praise them backstage",
                        "effect": "none",
                        "morale_change": 10,
                    },
                ],
                "deadline": 2,
                "consequences": {},
            },
        }
        
        return incidents.get(incident_type, {
            "severity": IncidentSeverity.MINOR,
            "description": f"Something happened with {wrestler.name}.",
            "options": [{"text": "Acknowledge", "effect": "none"}],
            "deadline": 1,
            "consequences": {},
        })
    
    def resolve_incident(
        self, 
        incident: Incident, 
        option_index: int,
        promotion
    ) -> Dict:
        """
        Resolve an incident with the chosen option.
        Returns a summary of what happened.
        """
        if option_index >= len(incident.options):
            option_index = 0
        
        option = incident.options[option_index]
        results = {
            "option_chosen": option["text"],
            "effects_applied": [],
        }
        
        wrestler = incident.wrestler
        target = incident.target
        
        # Apply morale change
        if "morale_change" in option:
            wrestler.morale = max(1, min(100, wrestler.morale + option["morale_change"]))
            results["effects_applied"].append(
                f"{wrestler.name} morale: {option['morale_change']:+d}"
            )
        
        # Apply loyalty change
        if "loyalty_change" in option:
            wrestler.loyalty = max(1, min(100, wrestler.loyalty + option["loyalty_change"]))
            results["effects_applied"].append(
                f"{wrestler.name} loyalty: {option['loyalty_change']:+d}"
            )
        
        # Apply ego change
        if "ego_change" in option:
            wrestler.ego = max(1, min(100, wrestler.ego + option["ego_change"]))
            results["effects_applied"].append(
                f"{wrestler.name} ego: {option['ego_change']:+d}"
            )
        
        # Apply momentum change
        if "momentum_change" in option:
            wrestler.adjust_momentum(option["momentum_change"])
            results["effects_applied"].append(
                f"{wrestler.name} momentum: {option['momentum_change']:+d}"
            )
        
        # Apply popularity change
        if "popularity_change" in option:
            wrestler.adjust_popularity(option["popularity_change"])
            results["effects_applied"].append(
                f"{wrestler.name} popularity: {option['popularity_change']:+d}"
            )
        
        # Apply target changes
        if target:
            if "target_morale_change" in option:
                target.morale = max(1, min(100, target.morale + option["target_morale_change"]))
                results["effects_applied"].append(
                    f"{target.name} morale: {option['target_morale_change']:+d}"
                )
        
        # Apply salary changes
        if option.get("effect") == "salary_increase" and "value" in option:
            wrestler.salary += option["value"]
            results["effects_applied"].append(
                f"{wrestler.name} salary increased by ${option['value']:,}/week"
            )
        
        # Apply fines
        if option.get("effect") == "fine" and "value" in option:
            promotion.budget += option["value"]  # Fine goes to company
            results["effects_applied"].append(
                f"{wrestler.name} fined ${option['value']:,}"
            )
        
        # Apply suspension
        if option.get("effect") == "suspend" and "value" in option:
            # Simulate suspension by making them unavailable
            wrestler.is_injured = True
            wrestler.injury_type = "Suspended"
            wrestler.injury_weeks_remaining = option["value"]
            results["effects_applied"].append(
                f"{wrestler.name} suspended for {option['value']} weeks"
            )
        
        # Apply release
        if option.get("effect") == "release":
            # This will need to be handled by promotion
            results["wrestler_released"] = True
            results["effects_applied"].append(
                f"{wrestler.name} has been released!"
            )
        
        # Apply roster morale changes
        if "roster_morale_change" in option:
            for w in promotion.roster:
                if w != wrestler:
                    w.morale = max(1, min(100, w.morale + option["roster_morale_change"]))
            results["effects_applied"].append(
                f"Roster morale: {option['roster_morale_change']:+d}"
            )
        
        # Apply costs
        if "cost" in option:
            promotion.budget -= option["cost"]
            results["effects_applied"].append(f"Cost: ${option['cost']:,}")
        
        # Apply bonuses (wrestler gets money, company pays)
        if option.get("effect") == "bonus" and "value" in option:
            promotion.budget -= option["value"]
            results["effects_applied"].append(
                f"Paid ${option['value']:,} bonus to {wrestler.name}"
            )
        
        # Record in history
        self.incident_history.append({
            "type": incident.incident_type.value,
            "wrestler": wrestler.name,
            "target": target.name if target else None,
            "resolution": option["text"],
            "severity": incident.severity.value,
        })
        
        # Remove from active
        if incident in self.active_incidents:
            self.active_incidents.remove(incident)
        
        return results
    
    def auto_resolve_expired(self, promotion) -> List[Dict]:
        """Auto-resolve incidents that have expired"""
        results = []
        
        for incident in self.active_incidents[:]:  # Copy list for iteration
            incident.deadline_weeks -= 1
            
            if incident.deadline_weeks < 0:
                # Apply consequences
                result = {
                    "incident": incident.incident_type.value,
                    "wrestler": incident.wrestler.name,
                    "auto_resolved": True,
                    "consequences": [],
                }
                
                consequences = incident.consequences
                wrestler = incident.wrestler
                
                if consequences.get("morale_loss"):
                    wrestler.morale = max(1, wrestler.morale - consequences["morale_loss"])
                    result["consequences"].append(f"Morale -{consequences['morale_loss']}")
                
                if consequences.get("loyalty_loss"):
                    wrestler.loyalty = max(1, wrestler.loyalty - consequences["loyalty_loss"])
                    result["consequences"].append(f"Loyalty -{consequences['loyalty_loss']}")
                
                if consequences.get("possible_quit") and random.random() < 0.3:
                    result["wrestler_quit"] = True
                    result["consequences"].append("WRESTLER QUIT!")
                
                results.append(result)
                self.active_incidents.remove(incident)
        
        return results
    
    def display_incident(self, incident: Incident) -> str:
        """Get formatted display string for an incident"""
        severity_icons = {
            IncidentSeverity.MINOR: "⚠️",
            IncidentSeverity.MODERATE: "🔶",
            IncidentSeverity.MAJOR: "🔴",
            IncidentSeverity.CRITICAL: "🚨",
            IncidentSeverity.POSITIVE: "✨",
        }
        
        lines = [
            f"\n{'='*60}",
            f"{severity_icons.get(incident.severity, '❓')} {incident.severity.value.upper()}: "
            f"{incident.incident_type.value}",
            f"{'='*60}",
            f"\n{incident.description}\n",
        ]
        
        if incident.deadline_weeks > 0:
            lines.append(f"⏰ Response needed within {incident.deadline_weeks} week(s)\n")
        else:
            lines.append("⏰ IMMEDIATE RESPONSE REQUIRED\n")
        
        lines.append("Options:")
        for i, option in enumerate(incident.options, 1):
            lines.append(f"  {i}. {option['text']}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            "enabled": self.enabled,
            "difficulty": self.difficulty,
            "incident_history": self.incident_history,
            # Active incidents need special handling
            "active_incidents_count": len(self.active_incidents),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CreativeControlSystem":
        """Create from dictionary"""
        system = cls(
            enabled=data.get("enabled", False),
            difficulty=data.get("difficulty", "Normal"),
        )
        system.incident_history = data.get("incident_history", [])
        return system