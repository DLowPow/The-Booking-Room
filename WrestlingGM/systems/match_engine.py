"""
Match Engine - Simulates wrestling matches
Supports 49 match types, 8 wrestling styles, 4 philosophies
No dependency on classes/match_types.py (deleted)
"""

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class FinishType(Enum):
    PINFALL = "Pinfall"
    SUBMISSION = "Submission"
    COUNTOUT = "Count-Out"
    DQ = "Disqualification"
    KO = "Knockout"
    ESCAPE = "Escape"
    RETRIEVE = "Retrieved Item"
    LAST_ELIMINATION = "Last Elimination"
    STOPPAGE = "Referee Stoppage"
    DRAW = "Draw"
    TIME_LIMIT = "Time Limit Draw"


@dataclass
class MatchResult:
    winner: object
    loser: object
    match_rating: float
    finish_type: FinishType
    crowd_reaction: int
    is_upset: bool = False
    is_title_match: bool = False
    is_main_event: bool = False
    match_type: str = "Singles"
    highlights: list = None

    def __post_init__(self):
        if self.highlights is None:
            self.highlights = []


class MatchEngine:
    """Simulates wrestling matches with style-based bonuses"""

    def __init__(self, promotion=None):
        self.promotion = promotion

    def simulate_match(
        self,
        wrestler1,
        wrestler2,
        match_type: str = "Singles",
        is_title_match: bool = False,
        is_main_event: bool = False,
        crowd_bonus: int = 0,
    ) -> MatchResult:
        """Simulate a match between two wrestlers"""

        # Base skill ratings
        skill1 = self._calculate_wrestler_skill(wrestler1)
        skill2 = self._calculate_wrestler_skill(wrestler2)

        # Philosophy bonuses
        phil_bonus1 = self._get_philosophy_bonus(wrestler1)
        phil_bonus2 = self._get_philosophy_bonus(wrestler2)

        # Match type bonuses
        match_bonus1 = self._get_match_type_bonus(wrestler1, match_type)
        match_bonus2 = self._get_match_type_bonus(wrestler2, match_type)

        # Chemistry bonus
        chemistry = self._calculate_chemistry(wrestler1, wrestler2)

        # Momentum and morale
        momentum1 = getattr(wrestler1, 'momentum', 50) / 100
        momentum2 = getattr(wrestler2, 'momentum', 50) / 100
        morale1 = getattr(wrestler1, 'morale', 75) / 100
        morale2 = getattr(wrestler2, 'morale', 75) / 100

        # Fatigue penalty
        fatigue1 = getattr(wrestler1, 'fatigue', 0) / 100
        fatigue2 = getattr(wrestler2, 'fatigue', 0) / 100

        # Total effective skill
        effective1 = (
            skill1
            + phil_bonus1 * 10
            + match_bonus1 * 10
            + momentum1 * 5
            + morale1 * 5
            - fatigue1 * 8
        )
        effective2 = (
            skill2
            + phil_bonus2 * 10
            + match_bonus2 * 10
            + momentum2 * 5
            + morale2 * 5
            - fatigue2 * 8
        )

        # Random variance
        variance1 = random.uniform(-8, 8)
        variance2 = random.uniform(-8, 8)
        effective1 += variance1
        effective2 += variance2

        # Determine winner
        if effective1 > effective2:
            winner = wrestler1
            loser = wrestler2
            is_upset = wrestler2.popularity > wrestler1.popularity + 15
        elif effective2 > effective1:
            winner = wrestler2
            loser = wrestler1
            is_upset = wrestler1.popularity > wrestler2.popularity + 15
        else:
            winner = random.choice([wrestler1, wrestler2])
            loser = wrestler2 if winner == wrestler1 else wrestler1
            is_upset = False

        # Calculate match rating
        match_rating = self._calculate_match_rating(
            wrestler1, wrestler2, chemistry,
            phil_bonus1, phil_bonus2,
            match_bonus1, match_bonus2,
            is_title_match, is_main_event,
            crowd_bonus, match_type,
        )

        # Determine finish type
        finish_type = self._determine_finish(wrestler1, wrestler2, match_type)

        # Crowd reaction
        crowd_reaction = self._calculate_crowd_reaction(
            wrestler1, wrestler2, match_rating,
            is_title_match, is_main_event, is_upset,
        )

        # Apply match effects
        self._apply_match_effects(winner, loser, match_rating, is_title_match, is_main_event)

        return MatchResult(
            winner=winner,
            loser=loser,
            match_rating=match_rating,
            finish_type=finish_type,
            crowd_reaction=crowd_reaction,
            is_upset=is_upset,
            is_title_match=is_title_match,
            is_main_event=is_main_event,
            match_type=match_type,
        )

    def _calculate_wrestler_skill(self, wrestler) -> float:
        """Calculate base skill from wrestler attributes"""
        attrs = []
        for attr in ['striking', 'grappling', 'aerial', 'charisma', 'stamina',
                      'technical', 'power', 'speed']:
            val = getattr(wrestler, attr, None)
            if val is not None:
                attrs.append(val)

        if attrs:
            base = sum(attrs) / len(attrs)
        else:
            base = getattr(wrestler, 'overall_rating', 50)

        popularity_bonus = getattr(wrestler, 'popularity', 50) * 0.1
        return base + popularity_bonus

    def _get_philosophy_bonus(self, wrestler) -> float:
        """Get bonus based on promotion philosophy and wrestler style"""
        if not self.promotion:
            return 0.0
        try:
            return self.promotion.get_philosophy_style_bonus(wrestler.primary_style)
        except Exception:
            return 0.0

    def _get_match_type_bonus(self, wrestler, match_type: str) -> float:
        """Get bonus for wrestler based on match type and their style"""
        style_name = "All Rounder"
        if hasattr(wrestler, 'primary_style') and wrestler.primary_style:
            style_name = wrestler.primary_style.value if hasattr(wrestler.primary_style, 'value') else str(wrestler.primary_style)

        bonuses = {
            # Standard
            "Singles": {"Technician": 0.05, "All Rounder": 0.05},
            "Intergender Singles": {"All Rounder": 0.05, "Showman": 0.05},
            "Triple Threat": {"All Rounder": 0.10, "Luchador": 0.05},
            "Fatal Four Way": {"All Rounder": 0.10, "Showman": 0.05},
            "5-Way Match": {"All Rounder": 0.10, "Showman": 0.05},
            "6-Way Match": {"All Rounder": 0.10, "Showman": 0.05},
            "8-Way Match": {"All Rounder": 0.10, "Showman": 0.05},

            # Tag
            "Tag Team": {"All Rounder": 0.05, "Technician": 0.05},
            "Mixed Tag": {"All Rounder": 0.10, "Showman": 0.05},
            "Tornado Tag": {"Fighter": 0.10, "Hardcore": 0.05},
            "6-Man Tag": {"All Rounder": 0.05, "Powerhouse": 0.05},
            "8-Man Tag": {"All Rounder": 0.05, "Powerhouse": 0.05},
            "1-on-2 Handicap": {"Powerhouse": 0.15, "Giant": 0.10, "Fighter": 0.05},
            "1-on-3 Handicap": {"Powerhouse": 0.20, "Giant": 0.15},
            "2-on-3 Handicap": {"All Rounder": 0.10, "Fighter": 0.05},

            # Hardcore
            "Extreme Rules": {"Hardcore": 0.15, "Fighter": 0.10, "Powerhouse": 0.05},
            "Falls Count Anywhere": {"Hardcore": 0.10, "Fighter": 0.10, "All Rounder": 0.05},
            "Ladder Match": {"Luchador": 0.15, "All Rounder": 0.10, "Showman": 0.05},
            "Table Match": {"Powerhouse": 0.10, "Hardcore": 0.10, "Giant": 0.05},
            "TLC": {"Luchador": 0.10, "Hardcore": 0.10, "All Rounder": 0.05},
            "Barbed Wire Deathmatch": {"Hardcore": 0.20, "Fighter": 0.10},
            "Exploding Barbed Wire": {"Hardcore": 0.20, "Fighter": 0.10},
            "Landmine Deathmatch": {"Hardcore": 0.20, "Fighter": 0.10},

            # Cage
            "Steel Cage": {"Powerhouse": 0.10, "Technician": 0.10, "Fighter": 0.05},
            "Hell in a Cell": {"Hardcore": 0.15, "Fighter": 0.10, "Powerhouse": 0.05},
            "Elimination Chamber": {"All Rounder": 0.10, "Technician": 0.05, "Fighter": 0.05},
            "War Games": {"Fighter": 0.10, "Powerhouse": 0.05, "All Rounder": 0.05},

            # Specialty
            "Ambulance Match": {"Powerhouse": 0.10, "Hardcore": 0.10},
            "Casket Match": {"Powerhouse": 0.10, "Giant": 0.10},
            "Dumpster Match": {"Powerhouse": 0.10, "Hardcore": 0.05},
            "I Quit": {"Technician": 0.10, "Hardcore": 0.10, "Fighter": 0.05},
            "Inferno Match": {"Hardcore": 0.15, "Showman": 0.05},
            "Iron Man": {"Technician": 0.15, "All Rounder": 0.10},
            "Last Man Standing": {"Powerhouse": 0.10, "Fighter": 0.10, "Hardcore": 0.05},
            "Submission Match": {"Technician": 0.20, "Fighter": 0.05},
            "3 Stages of Hell": {"All Rounder": 0.15, "Technician": 0.10},
            "Underground Match": {"Hardcore": 0.15, "Fighter": 0.10},
            "Bloodline Rules": {"Fighter": 0.10, "Powerhouse": 0.10, "Hardcore": 0.05},
            "Brawl": {"Hardcore": 0.15, "Fighter": 0.10, "Powerhouse": 0.05},
            "Lumberjack Match": {"Showman": 0.10, "All Rounder": 0.05},
            "Special Guest Referee": {"Showman": 0.10, "All Rounder": 0.05},

            # Battle Royal
            "Battle Royal": {"Powerhouse": 0.10, "Giant": 0.10, "Fighter": 0.05},
            "Casino Battle Royale": {"Powerhouse": 0.10, "Giant": 0.10, "All Rounder": 0.05},
            "Royal Rumble": {"Powerhouse": 0.10, "Giant": 0.10, "All Rounder": 0.05},
            "Gauntlet Match": {"All Rounder": 0.15, "Technician": 0.10},
            "Gauntlet Eliminator": {"All Rounder": 0.10, "Fighter": 0.10},

            # Combat
            "MMA Rules": {"Fighter": 0.20, "Technician": 0.10},
            "Kickboxing Rules": {"Fighter": 0.20},
        }

        match_bonuses = bonuses.get(match_type, {})
        return match_bonuses.get(style_name, 0.0)

    def _calculate_chemistry(self, wrestler1, wrestler2) -> float:
        """Calculate chemistry between two wrestlers"""
        chemistry = 0.0

        # Similar skill levels create better matches
        ovr1 = getattr(wrestler1, 'overall_rating', 50)
        ovr2 = getattr(wrestler2, 'overall_rating', 50)
        skill_diff = abs(ovr1 - ovr2)
        if skill_diff < 10:
            chemistry += 0.15
        elif skill_diff < 20:
            chemistry += 0.05
        elif skill_diff > 40:
            chemistry -= 0.10

        # Opposite alignments create better stories
        align1 = getattr(wrestler1, 'alignment', None)
        align2 = getattr(wrestler2, 'alignment', None)
        if align1 and align2:
            a1 = align1.value if hasattr(align1, 'value') else str(align1)
            a2 = align2.value if hasattr(align2, 'value') else str(align2)
            if (a1 == 'Face' and a2 == 'Heel') or (a1 == 'Heel' and a2 == 'Face'):
                chemistry += 0.15
            elif a1 == a2:
                chemistry -= 0.05

        # Complementary styles
        style1 = getattr(wrestler1, 'primary_style', None)
        style2 = getattr(wrestler2, 'primary_style', None)
        if style1 and style2:
            s1 = style1.value if hasattr(style1, 'value') else str(style1)
            s2 = style2.value if hasattr(style2, 'value') else str(style2)
            good_combos = [
                ("Technician", "Powerhouse"), ("Luchador", "Giant"),
                ("Showman", "Technician"), ("Fighter", "Luchador"),
                ("Hardcore", "Powerhouse"), ("All Rounder", "Showman"),
            ]
            for combo in good_combos:
                if (s1 == combo[0] and s2 == combo[1]) or (s1 == combo[1] and s2 == combo[0]):
                    chemistry += 0.10
                    break

        return max(-0.3, min(0.3, chemistry))

    def _calculate_match_rating(
        self, wrestler1, wrestler2, chemistry,
        phil_bonus1, phil_bonus2, match_bonus1, match_bonus2,
        is_title_match, is_main_event, crowd_bonus, match_type,
    ) -> float:
        """Calculate the star rating for a match"""

        ovr1 = getattr(wrestler1, 'overall_rating', 50)
        ovr2 = getattr(wrestler2, 'overall_rating', 50)

        # Base from wrestler quality (0-5 scale)
        avg_skill = (ovr1 + ovr2) / 2
        base_rating = (avg_skill / 100) * 3.5

        # Chemistry bonus
        base_rating += chemistry * 1.5

        # Philosophy bonuses
        phil_avg = (phil_bonus1 + phil_bonus2) / 2
        base_rating += phil_avg * 0.5

        # Match type bonuses
        match_avg = (match_bonus1 + match_bonus2) / 2
        base_rating += match_avg * 0.5

        # Stipulation bonuses
        if is_title_match:
            base_rating += 0.2
        if is_main_event:
            base_rating += 0.15

        # Crowd energy
        base_rating += crowd_bonus * 0.01

        # Random variance
        variance = random.uniform(-0.3, 0.3)
        base_rating += variance

        # Popularity multiplier
        pop_avg = (getattr(wrestler1, 'popularity', 50) + getattr(wrestler2, 'popularity', 50)) / 2
        pop_mult = 1.0 + (pop_avg - 50) * 0.003
        base_rating *= pop_mult

        # Match type ceiling adjustments
        high_ceiling_types = [
            "Iron Man", "3 Stages of Hell", "Hell in a Cell",
            "Elimination Chamber", "War Games", "TLC", "Ladder Match",
        ]
        low_ceiling_types = [
            "Battle Royal", "Casino Battle Royale", "Royal Rumble",
            "Gauntlet Match", "Lumberjack Match",
        ]
        if match_type in high_ceiling_types:
            base_rating += 0.15
        elif match_type in low_ceiling_types:
            base_rating -= 0.10

        return max(0.5, min(5.0, round(base_rating, 2)))

    def _determine_finish(self, wrestler1, wrestler2, match_type: str) -> FinishType:
        """Determine how the match ends based on match type"""

        # Match-type specific finishes
        submission_types = ["Submission Match", "I Quit", "MMA Rules"]
        if match_type in submission_types:
            return FinishType.SUBMISSION

        cage_types = ["Steel Cage"]
        if match_type in cage_types:
            return random.choice([FinishType.PINFALL, FinishType.ESCAPE, FinishType.SUBMISSION])

        ladder_types = ["Ladder Match", "TLC"]
        if match_type in ladder_types:
            return FinishType.RETRIEVE

        elimination_types = [
            "Battle Royal", "Casino Battle Royale", "Royal Rumble",
            "Elimination Chamber", "War Games",
        ]
        if match_type in elimination_types:
            return FinishType.LAST_ELIMINATION

        ko_types = ["Kickboxing Rules", "MMA Rules", "Last Man Standing"]
        if match_type in ko_types:
            return random.choice([FinishType.KO, FinishType.STOPPAGE])

        no_dq_types = [
            "Extreme Rules", "Falls Count Anywhere", "Tornado Tag",
            "Barbed Wire Deathmatch", "Exploding Barbed Wire", "Landmine Deathmatch",
            "Hell in a Cell", "Ambulance Match", "Casket Match", "Dumpster Match",
            "Inferno Match", "Underground Match", "Brawl", "Bloodline Rules",
            "3 Stages of Hell", "Table Match",
        ]
        if match_type in no_dq_types:
            return random.choice([FinishType.PINFALL, FinishType.KO, FinishType.SUBMISSION])

        iron_man_types = ["Iron Man"]
        if match_type in iron_man_types:
            if random.random() < 0.1:
                return FinishType.TIME_LIMIT
            return random.choice([FinishType.PINFALL, FinishType.SUBMISSION])

        # Standard match finishes
        style1 = getattr(wrestler1, 'primary_style', None)
        s1 = style1.value if style1 and hasattr(style1, 'value') else "All Rounder"

        if s1 == "Technician":
            weights = [0.4, 0.4, 0.1, 0.05, 0.05]
        elif s1 in ["Powerhouse", "Giant"]:
            weights = [0.6, 0.1, 0.1, 0.1, 0.1]
        elif s1 == "Hardcore":
            weights = [0.4, 0.1, 0.2, 0.1, 0.2]
        elif s1 == "Luchador":
            weights = [0.5, 0.2, 0.1, 0.1, 0.1]
        else:
            weights = [0.5, 0.2, 0.1, 0.1, 0.1]

        finishes = [
            FinishType.PINFALL,
            FinishType.SUBMISSION,
            FinishType.COUNTOUT,
            FinishType.DQ,
            FinishType.KO,
        ]

        return random.choices(finishes, weights=weights, k=1)[0]

    def _calculate_crowd_reaction(
        self, wrestler1, wrestler2, match_rating,
        is_title_match, is_main_event, is_upset,
    ) -> int:
        """Calculate crowd reaction (0-100)"""

        base = int(match_rating * 15)

        pop_avg = (getattr(wrestler1, 'popularity', 50) + getattr(wrestler2, 'popularity', 50)) / 2
        base += int(pop_avg * 0.3)

        if is_title_match:
            base += 10
        if is_main_event:
            base += 8
        if is_upset:
            base += 12

        # Alignment drama
        align1 = getattr(wrestler1, 'alignment', None)
        align2 = getattr(wrestler2, 'alignment', None)
        if align1 and align2:
            a1 = align1.value if hasattr(align1, 'value') else str(align1)
            a2 = align2.value if hasattr(align2, 'value') else str(align2)
            if (a1 == 'Face' and a2 == 'Heel') or (a1 == 'Heel' and a2 == 'Face'):
                base += 8

        base += random.randint(-5, 5)

        return max(10, min(100, base))

    def _apply_match_effects(self, winner, loser, match_rating, is_title_match, is_main_event):
        """Apply post-match effects to wrestlers"""

        # Winner effects
        if hasattr(winner, 'adjust_momentum'):
            momentum_gain = 3
            if is_main_event:
                momentum_gain += 3
            if is_title_match:
                momentum_gain += 5
            if match_rating >= 4.0:
                momentum_gain += 3
            winner.adjust_momentum(momentum_gain)

        if hasattr(winner, 'add_fatigue'):
            winner.add_fatigue(random.randint(5, 12))

        # Loser effects
        if hasattr(loser, 'adjust_momentum'):
            momentum_loss = -2
            if is_main_event:
                momentum_loss -= 2
            loser.adjust_momentum(momentum_loss)

        if hasattr(loser, 'add_fatigue'):
            loser.add_fatigue(random.randint(8, 15))

        # Random injury check
        if hasattr(loser, 'check_injury'):
            injury_chance = 3
            if match_rating < 2.0:
                injury_chance += 2
            loser.check_injury(injury_chance)


def quick_match(wrestler1, wrestler2, match_type="Singles") -> MatchResult:
    """Quick match simulation without promotion context"""
    engine = MatchEngine()
    return engine.simulate_match(wrestler1, wrestler2, match_type=match_type)
