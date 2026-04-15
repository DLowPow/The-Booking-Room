"""
Match Engine - Simulates wrestling matches
"""

import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from classes.enums import WrestlingStyle, Philosophy, MatchType
from classes.wrestler import Wrestler
from classes.promotion import Promotion
from systems.chemistry import get_chemistry


class MatchFinish(Enum):
    PINFALL = "Pinfall"
    SUBMISSION = "Submission"
    COUNTOUT = "Count Out"
    DQ = "Disqualification"
    KO = "Knockout"
    LADDER_RETRIEVAL = "Retrieved the Prize"
    ESCAPE = "Cage Escape"
    TIME_LIMIT_DRAW = "Time Limit Draw"


@dataclass
class MatchResult:
    """Contains all information about a completed match"""
    winner: Optional[Wrestler]
    loser: Optional[Wrestler]
    is_draw: bool
    finish_type: MatchFinish
    match_rating: float  # Star rating (0.0 - 5.0)
    crowd_reaction: int  # 1-100
    highlights: List[str]
    injuries: List[Tuple[Wrestler, str, int]]  # (wrestler, injury_type, weeks)
    momentum_changes: Dict[str, int]  # wrestler_name -> change
    duration_minutes: int


class MatchEngine:
    """Handles all match simulation logic"""
    
    # Trait bonuses
    TRAIT_BONUSES = {
        "iron_man": {"stamina_bonus": 15, "match_types": [MatchType.IRON_MAN]},
        "spot_monkey": {"aerial_bonus": 10, "risk_increase": 1.3},
        "ring_general": {"consistency_bonus": 20, "psychology_bonus": 15},
        "promo_god": {"charisma_bonus": 20},
        "submission_specialist": {"submission_chance": 1.5, "match_types": [MatchType.SUBMISSION]},
        "hardcore_legend": {"hardcore_bonus": 15, "match_types": [MatchType.DEATHMATCH]},
        "giant_killer": {"vs_bigger_bonus": 20},
        "underdog": {"when_losing_bonus": 15},
        "veteran_presence": {"helps_younger_bonus": 10},
        "natural_talent": {"all_stats_bonus": 5},
        "glass_cannon": {"offense_bonus": 15, "injury_risk": 1.5},
        "technician_supreme": {"technical_bonus": 15},
        "showstopper": {"main_event_bonus": 20},
        "tag_specialist": {"tag_match_bonus": 20},
        "ladder_match_expert": {"ladder_bonus": 25},
        "deathmatch_king": {"deathmatch_bonus": 30},
    }
    
    # Match type fatigue costs
    MATCH_FATIGUE = {
        MatchType.STANDARD: 10,
        MatchType.IRON_MAN: 30,
        MatchType.SUBMISSION: 15,
        MatchType.LADDER: 25,
        MatchType.CAGE: 20,
        MatchType.DEATHMATCH: 35,
        MatchType.TABLES: 20,
        MatchType.BATTLE_ROYAL: 15,
        MatchType.TAG_TEAM: 8,
    }
    
    # Injury types and durations
    INJURIES = [
        ("Minor Bruising", 1, 2),
        ("Muscle Strain", 2, 4),
        ("Concussion", 3, 6),
        ("Back Injury", 4, 8),
        ("Knee Injury", 6, 12),
        ("Shoulder Injury", 4, 10),
        ("Neck Injury", 8, 16),
        ("Broken Bone", 12, 24),
    ]
    
    def __init__(self, promotion: Optional[Promotion] = None):
        self.promotion = promotion
        self.philosophy = promotion.philosophy if promotion else Philosophy.SPORTS_ENTERTAINMENT
    
    def simulate_match(
        self,
        wrestler1: Wrestler,
        wrestler2: Wrestler,
        match_type: MatchType = MatchType.STANDARD,
        is_title_match: bool = False,
        is_main_event: bool = False,
        predetermined_winner: Optional[Wrestler] = None,
        time_limit: int = 30,
    ) -> MatchResult:
        """
        Simulate a complete match between two wrestlers.
        Returns a MatchResult with all details.
        """
        highlights = []
        injuries = []
        momentum_changes = {}
        
        # Get performance ratings for tonight
        perf1 = wrestler1.get_performance_rating()
        perf2 = wrestler2.get_performance_rating()
        
        highlights.append(f"{wrestler1.name} performing at {perf1} tonight")
        highlights.append(f"{wrestler2.name} performing at {perf2} tonight")
        
        # Apply chemistry bonus
        chemistry = get_chemistry(wrestler1.primary_style, wrestler2.primary_style)
        highlights.append(f"Style chemistry: {chemistry:.2f}x")
        
        # Apply philosophy bonus
        phil_bonus1 = self._get_philosophy_bonus(wrestler1)
        phil_bonus2 = self._get_philosophy_bonus(wrestler2)
        
        # Apply match type bonuses
        match_bonus1 = self._get_match_type_bonus(wrestler1, match_type)
        match_bonus2 = self._get_match_type_bonus(wrestler2, match_type)
        
        # Apply trait bonuses
        trait_bonus1 = self._get_trait_bonus(wrestler1, match_type, wrestler2, is_main_event)
        trait_bonus2 = self._get_trait_bonus(wrestler2, match_type, wrestler1, is_main_event)
        
        # Calculate final match scores
        final_score1 = perf1 * phil_bonus1 * match_bonus1 * trait_bonus1
        final_score2 = perf2 * phil_bonus2 * match_bonus2 * trait_bonus2
        
        # Determine winner
        if predetermined_winner:
            winner = predetermined_winner
            loser = wrestler2 if winner == wrestler1 else wrestler1
            is_draw = False
        else:
            winner, loser, is_draw = self._determine_winner(
                wrestler1, wrestler2, final_score1, final_score2
            )
        
        # Calculate match quality
        base_quality = (perf1 + perf2) / 2
        chemistry_quality = base_quality * chemistry
        
        # Bonuses for special situations
        if is_main_event:
            chemistry_quality *= 1.1
            highlights.append("Main event bonus applied!")
        if is_title_match:
            chemistry_quality *= 1.05
            highlights.append("Title match intensity!")
        
        # Convert to star rating (0-5)
        match_rating = self._calculate_star_rating(chemistry_quality)
        
        # Calculate crowd reaction
        crowd_reaction = self._calculate_crowd_reaction(
            wrestler1, wrestler2, match_rating, is_main_event
        )
        
        # Determine finish type
        finish_type = self._determine_finish(match_type, winner, is_draw)
        
        # Calculate match duration
        duration = self._calculate_duration(match_type, time_limit, match_rating)
        
        # Check for injuries
        injuries = self._check_for_injuries(
            [wrestler1, wrestler2], match_type
        )
        
        # Apply fatigue
        fatigue = self.MATCH_FATIGUE.get(match_type, 10)
        if is_main_event:
            fatigue = int(fatigue * 1.3)
        wrestler1.add_fatigue(fatigue)
        wrestler2.add_fatigue(fatigue)
        
        # Calculate momentum changes
        if not is_draw:
            if match_rating >= 4.0:
                momentum_changes[winner.name] = 10
                momentum_changes[loser.name] = -2  # Good match softens loss
            elif match_rating >= 3.0:
                momentum_changes[winner.name] = 7
                momentum_changes[loser.name] = -4
            else:
                momentum_changes[winner.name] = 5
                momentum_changes[loser.name] = -5
            
            if is_title_match:
                momentum_changes[winner.name] += 5
        else:
            momentum_changes[wrestler1.name] = 2
            momentum_changes[wrestler2.name] = 2
        
        # Record match results
        if not is_draw:
            winner.record_match("win")
            loser.record_match("loss")
        else:
            wrestler1.record_match("draw")
            wrestler2.record_match("draw")
        
        # Apply momentum changes
        for wrestler_name, change in momentum_changes.items():
            wrestler = wrestler1 if wrestler1.name == wrestler_name else wrestler2
            wrestler.adjust_momentum(change)
        
        # Apply injuries
        for wrestler, injury_type, weeks in injuries:
            wrestler.injure(injury_type, weeks)
            highlights.append(f"⚠️ {wrestler.name} injured: {injury_type} ({weeks} weeks)")
        
        # Track 5 star matches
        if match_rating >= 5.0:
            wrestler1.five_star_matches += 1
            wrestler2.five_star_matches += 1
            highlights.append("⭐⭐⭐⭐⭐ FIVE STAR MATCH!")
        
        return MatchResult(
            winner=winner,
            loser=loser,
            is_draw=is_draw,
            finish_type=finish_type,
            match_rating=match_rating,
            crowd_reaction=crowd_reaction,
            highlights=highlights,
            injuries=injuries,
            momentum_changes=momentum_changes,
            duration_minutes=duration,
        )
    
    def _get_philosophy_bonus(self, wrestler: Wrestler) -> float:
        """Get philosophy-based style bonus"""
        if self.promotion:
            return self.promotion.get_philosophy_style_bonus(wrestler.primary_style)
        return 1.0
    
    def _get_match_type_bonus(self, wrestler: Wrestler, match_type: MatchType) -> float:
        """Get bonus for wrestler in specific match type"""
        from classes.match_types import MATCH_TYPE_BONUSES
        
        bonuses = MATCH_TYPE_BONUSES.get(match_type, {})
        return bonuses.get(wrestler.primary_style, 1.0)
    
    def _get_trait_bonus(
        self,
        wrestler: Wrestler,
        match_type: MatchType,
        opponent: Wrestler,
        is_main_event: bool
    ) -> float:
        """Calculate total bonus from wrestler's unique traits"""
        bonus = 1.0
        
        for trait in wrestler.unique_traits:
            trait_lower = trait.lower().replace(" ", "_")
            trait_data = self.TRAIT_BONUSES.get(trait_lower, {})
            
            # Match type specific bonuses
            if match_type in trait_data.get("match_types", []):
                bonus *= 1.2
            
            # Situational bonuses
            if trait_lower == "giant_killer" and opponent.weight > wrestler.weight + 50:
                bonus *= 1.15
            elif trait_lower == "showstopper" and is_main_event:
                bonus *= 1.15
            elif trait_lower == "natural_talent":
                bonus *= 1.05
        
        return bonus
    
    def _determine_winner(
        self,
        wrestler1: Wrestler,
        wrestler2: Wrestler,
        score1: float,
        score2: float
    ) -> Tuple[Optional[Wrestler], Optional[Wrestler], bool]:
        """Determine match winner based on scores with randomness"""
        
        total = score1 + score2
        win_chance1 = score1 / total
        
        # Add some randomness (upsets can happen)
        roll = random.random()
        
        # Check for draw (rare)
        if abs(score1 - score2) < 5 and random.random() < 0.05:
            return None, None, True
        
        if roll < win_chance1:
            return wrestler1, wrestler2, False
        else:
            return wrestler2, wrestler1, False
    
    def _calculate_star_rating(self, quality_score: float) -> float:
        """Convert quality score to 0-5 star rating"""
        # Quality score is roughly 0-100
        # Map to 0-5 stars with diminishing returns at high end
        
        if quality_score >= 95:
            stars = 5.0
        elif quality_score >= 90:
            stars = 4.75
        elif quality_score >= 85:
            stars = 4.5
        elif quality_score >= 80:
            stars = 4.0
        elif quality_score >= 70:
            stars = 3.5
        elif quality_score >= 60:
            stars = 3.0
        elif quality_score >= 50:
            stars = 2.5
        elif quality_score >= 40:
            stars = 2.0
        elif quality_score >= 30:
            stars = 1.5
        elif quality_score >= 20:
            stars = 1.0
        else:
            stars = 0.5
        
        # Add small random variance
        variance = random.uniform(-0.25, 0.25)
        stars = max(0.0, min(5.0, stars + variance))
        
        return round(stars * 4) / 4  # Round to nearest 0.25
    
    def _calculate_crowd_reaction(
        self,
        wrestler1: Wrestler,
        wrestler2: Wrestler,
        match_rating: float,
        is_main_event: bool
    ) -> int:
        """Calculate crowd reaction (1-100)"""
        # Base on popularity and match quality
        base = (wrestler1.popularity + wrestler2.popularity) / 2
        quality_bonus = match_rating * 10
        
        reaction = base + quality_bonus
        
        if is_main_event:
            reaction += 10
        
        # Face vs Heel bonus
        if wrestler1.alignment != wrestler2.alignment:
            reaction += 5
        
        return max(1, min(100, int(reaction)))
    
    def _determine_finish(
        self,
        match_type: MatchType,
        winner: Optional[Wrestler],
        is_draw: bool
    ) -> MatchFinish:
        """Determine how the match ended"""
        if is_draw:
            return MatchFinish.TIME_LIMIT_DRAW
        
        if match_type == MatchType.SUBMISSION:
            return MatchFinish.SUBMISSION
        elif match_type == MatchType.LADDER:
            return MatchFinish.LADDER_RETRIEVAL
        elif match_type == MatchType.CAGE:
            if random.random() < 0.5:
                return MatchFinish.ESCAPE
            return MatchFinish.PINFALL
        else:
            # Standard finish distribution
            roll = random.random()
            if roll < 0.7:
                return MatchFinish.PINFALL
            elif roll < 0.9:
                return MatchFinish.SUBMISSION
            elif roll < 0.95:
                return MatchFinish.COUNTOUT
            else:
                return MatchFinish.DQ
    
    def _calculate_duration(
        self,
        match_type: MatchType,
        time_limit: int,
        match_rating: float
    ) -> int:
        """Calculate match duration in minutes"""
        base_time = {
            MatchType.STANDARD: 12,
            MatchType.IRON_MAN: 60,
            MatchType.SUBMISSION: 15,
            MatchType.LADDER: 20,
            MatchType.CAGE: 18,
            MatchType.DEATHMATCH: 15,
            MatchType.TABLES: 10,
            MatchType.BATTLE_ROYAL: 25,
            MatchType.TAG_TEAM: 15,
        }
        
        base = base_time.get(match_type, 12)
        
        # Better matches tend to go longer
        quality_modifier = 1.0 + (match_rating - 2.5) * 0.1
        
        duration = int(base * quality_modifier)
        duration += random.randint(-3, 5)
        
        return max(3, min(time_limit, duration))
    
    def _check_for_injuries(
        self,
        wrestlers: List[Wrestler],
        match_type: MatchType
    ) -> List[Tuple[Wrestler, str, int]]:
        """Check if any wrestlers got injured"""
        injuries = []
        
        # Higher risk match types
        risk_modifier = {
            MatchType.STANDARD: 1.0,
            MatchType.IRON_MAN: 1.3,
            MatchType.SUBMISSION: 1.1,
            MatchType.LADDER: 2.0,
            MatchType.CAGE: 1.5,
            MatchType.DEATHMATCH: 2.5,
            MatchType.TABLES: 1.8,
            MatchType.BATTLE_ROYAL: 1.2,
            MatchType.TAG_TEAM: 0.8,
        }
        
        base_risk = 0.03  # 3% base chance
        type_risk = risk_modifier.get(match_type, 1.0)
        
        for wrestler in wrestlers:
            # Factor in injury prone stat
            wrestler_risk = base_risk * type_risk * (wrestler.injury_prone / 50)
            
            # Check for spot monkey trait (higher risk)
            if wrestler.has_trait("spot_monkey"):
                wrestler_risk *= 1.3
            if wrestler.has_trait("glass_cannon"):
                wrestler_risk *= 1.5
            
            if random.random() < wrestler_risk:
                # Determine injury severity
                severity_roll = random.random()
                if severity_roll < 0.5:
                    injury_pool = self.INJURIES[:3]  # Minor
                elif severity_roll < 0.85:
                    injury_pool = self.INJURIES[3:6]  # Moderate
                else:
                    injury_pool = self.INJURIES[6:]  # Severe
                
                injury_name, min_weeks, max_weeks = random.choice(injury_pool)
                weeks = random.randint(min_weeks, max_weeks)
                injuries.append((wrestler, injury_name, weeks))
        
        return injuries
    
    def simulate_quick_match(
        self,
        wrestler1: Wrestler,
        wrestler2: Wrestler
    ) -> str:
        """Quick simulation returning just a summary string"""
        result = self.simulate_match(wrestler1, wrestler2)
        
        if result.is_draw:
            return f"{wrestler1.name} vs {wrestler2.name}: DRAW ({result.match_rating}⭐)"
        else:
            return f"{result.winner.name} def. {result.loser.name} via {result.finish_type.value} ({result.match_rating}⭐)"


# Convenience function for quick testing
def quick_match(w1: Wrestler, w2: Wrestler, promo: Optional[Promotion] = None) -> MatchResult:
    """Quick helper to run a match"""
    engine = MatchEngine(promo)
    return engine.simulate_match(w1, w2)