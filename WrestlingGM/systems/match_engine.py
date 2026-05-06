"""
Match Engine - Simulates wrestling matches with full system integration
NEW: Storyline bonuses, relationship chemistry, alignment effects,
morale state impacts, Indy God bonuses, 10-stat wrestler integration,
crowd reaction modifiers, fixed __init__ syntax bug
"""

import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict


# ==================== ENUMS ====================

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


# ==================== MATCH RESULT ====================

@dataclass
class MatchResult:
    """Complete result data from a simulated match"""
    winner: object
    loser: object
    match_rating: float
    finish_type: FinishType
    crowd_reaction: int
    is_upset: bool = False
    is_title_match: bool = False
    is_main_event: bool = False
    match_type: str = "Singles"
    highlights: List[str] = field(default_factory=list)
    storyline_id: Optional[str] = None
    storyline_bonus: float = 0.0
    chemistry_bonus: float = 0.0
    crowd_reaction_bonus: float = 0.0
    morale_impact: Dict = field(default_factory=dict)


# ==================== MATCH ENGINE ====================

class MatchEngine:
    """
    Simulates wrestling matches with full integration into:
    - Storyline Engine (rating bonuses for active feuds)
    - Relationship Manager (chemistry from rivalries/tag teams)
    - New 10-stat wrestler system
    - Alignment & crowd reaction system
    - Morale state effects
    - Indy God bonuses
    """

    def __init__(self, promotion=None, storyline_engine=None, relationship_manager=None):
        self.promotion = promotion
        self.storyline_engine = storyline_engine
        self.relationship_manager = relationship_manager

    # ==================== MAIN SIMULATION ====================

    def simulate_match(
        self,
        wrestler1,
        wrestler2,
        match_type: str = "Singles",
        is_title_match: bool = False,
        is_main_event: bool = False,
        crowd_bonus: int = 0,
        match_minutes: int = 12,
    ) -> MatchResult:
        """Simulate a complete match between two wrestlers"""

        # Base skill ratings (using new 10-stat system)
        skill1 = self._calculate_wrestler_skill(wrestler1, match_type)
        skill2 = self._calculate_wrestler_skill(wrestler2, match_type)

        # Philosophy bonuses
        phil_bonus1 = self._get_philosophy_bonus(wrestler1)
        phil_bonus2 = self._get_philosophy_bonus(wrestler2)

        # Match type bonuses
        match_bonus1 = self._get_match_type_bonus(wrestler1, match_type)
        match_bonus2 = self._get_match_type_bonus(wrestler2, match_type)

        # Chemistry (from relationships + base wrestler-to-wrestler)
        chemistry = self._calculate_chemistry(wrestler1, wrestler2)

        # Storyline rating bonus
        storyline_data = self._get_storyline_data(wrestler1, wrestler2)
        storyline_bonus = storyline_data.get("bonus", 0.0)
        storyline_id = storyline_data.get("id")

        # Morale state impact
        morale_mod1 = self._get_morale_modifier(wrestler1)
        morale_mod2 = self._get_morale_modifier(wrestler2)

        # Momentum
        momentum1 = getattr(wrestler1, 'momentum', 50) / 100
        momentum2 = getattr(wrestler2, 'momentum', 50) / 100

        # Fatigue penalty
        fatigue1 = getattr(wrestler1, 'fatigue', 0) / 100
        fatigue2 = getattr(wrestler2, 'fatigue', 0) / 100

        # Match length tolerance (longer matches favor higher stamina)
        stamina_factor1 = self._get_stamina_factor(wrestler1, match_minutes)
        stamina_factor2 = self._get_stamina_factor(wrestler2, match_minutes)

        # Indy God boost
        indy_god_bonus1 = 5 if getattr(wrestler1, 'is_indy_god', False) else 0
        indy_god_bonus2 = 5 if getattr(wrestler2, 'is_indy_god', False) else 0

        # Crowd reaction power
        crowd_power1 = self._get_crowd_reaction_power(wrestler1)
        crowd_power2 = self._get_crowd_reaction_power(wrestler2)

        # Total effective skill
        effective1 = (
            skill1
            + phil_bonus1 * 10
            + match_bonus1 * 10
            + momentum1 * 5
            + morale_mod1 * 8
            - fatigue1 * 8
            + stamina_factor1
            + indy_god_bonus1
            + crowd_power1
        )
        effective2 = (
            skill2
            + phil_bonus2 * 10
            + match_bonus2 * 10
            + momentum2 * 5
            + morale_mod2 * 8
            - fatigue2 * 8
            + stamina_factor2
            + indy_god_bonus2
            + crowd_power2
        )

        # Random variance (consistency reduces variance)
        consistency1 = getattr(wrestler1, 'consistency', 50)
        consistency2 = getattr(wrestler2, 'consistency', 50)
        var_range1 = 12 - (consistency1 / 100 * 8)  # 4-12 range
        var_range2 = 12 - (consistency2 / 100 * 8)
        effective1 += random.uniform(-var_range1, var_range1)
        effective2 += random.uniform(-var_range2, var_range2)

        # Determine winner
        if effective1 > effective2:
            winner = wrestler1
            loser = wrestler2
            is_upset = self._is_upset(wrestler2, wrestler1)
        elif effective2 > effective1:
            winner = wrestler2
            loser = wrestler1
            is_upset = self._is_upset(wrestler1, wrestler2)
        else:
            winner = random.choice([wrestler1, wrestler2])
            loser = wrestler2 if winner == wrestler1 else wrestler1
            is_upset = False

        # Calculate match rating with all bonuses
        match_rating = self._calculate_match_rating(
            wrestler1, wrestler2, chemistry,
            phil_bonus1, phil_bonus2,
            match_bonus1, match_bonus2,
            is_title_match, is_main_event,
            crowd_bonus, match_type,
            storyline_bonus, match_minutes,
            morale_mod1, morale_mod2,
        )

        # Determine finish type
        finish_type = self._determine_finish(wrestler1, wrestler2, match_type)

        # Crowd reaction
        crowd_reaction = self._calculate_crowd_reaction(
            wrestler1, wrestler2, match_rating,
            is_title_match, is_main_event, is_upset,
            storyline_bonus,
        )

        # Apply post-match effects
        morale_impact = self._apply_match_effects(
            winner, loser, match_rating,
            is_title_match, is_main_event,
        )

        # Process storyline if active
        if self.storyline_engine and storyline_id:
            try:
                week = getattr(self.promotion, 'current_week', 0) if self.promotion else 0
                year = getattr(self.promotion, 'current_year', 1) if self.promotion else 1
                self.storyline_engine.process_match(
                    wrestler_names=[wrestler1.name, wrestler2.name],
                    week=week,
                    year=year,
                    match_display=f"{wrestler1.name} vs {wrestler2.name}",
                    rating=match_rating,
                    winner=winner.name,
                    finish_type=finish_type.value,
                )
            except Exception as e:
                print(f"Match engine storyline processing error: {e}")

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
            storyline_id=storyline_id,
            storyline_bonus=storyline_bonus,
            chemistry_bonus=chemistry,
            crowd_reaction_bonus=(crowd_power1 + crowd_power2) / 2,
            morale_impact=morale_impact,
        )

    # ==================== SKILL CALCULATION (NEW 10-STAT SYSTEM) ====================

    def _calculate_wrestler_skill(self, wrestler, match_type: str) -> float:
        """Calculate skill from new 10-stat wrestler system, weighted by match type"""

        # New 10 stats from rebuilt wrestler.py
        stats_to_check = [
            'power', 'speed', 'technical', 'stamina', 'charisma',
            'hardcore', 'aerial', 'mic_skills', 'psychology', 'toughness',
        ]

        # Match-type specific weighting
        weights = self._get_stat_weights_for_match(match_type)

        total = 0
        weight_sum = 0
        for stat in stats_to_check:
            val = getattr(wrestler, stat, None)
            if val is not None:
                w = weights.get(stat, 1.0)
                total += val * w
                weight_sum += w

        if weight_sum > 0:
            base = total / weight_sum
        else:
            base = getattr(wrestler, 'overall_rating', 50)

        # Popularity & reputation boost
        popularity_bonus = getattr(wrestler, 'popularity', 50) * 0.08
        reputation = getattr(wrestler, 'reputation', 0)
        reputation_bonus = min(15, reputation / 100)  # Cap at +15

        return base + popularity_bonus + reputation_bonus

    def _get_stat_weights_for_match(self, match_type: str) -> Dict[str, float]:
        """Different match types favor different stats"""
        # Default - all stats equal
        default = {stat: 1.0 for stat in [
            'power', 'speed', 'technical', 'stamina', 'charisma',
            'hardcore', 'aerial', 'mic_skills', 'psychology', 'toughness',
        ]}

        # Specific match type weightings
        if match_type in ["Submission Match", "I Quit", "MMA Rules"]:
            return {**default, 'technical': 2.0, 'psychology': 1.5, 'stamina': 1.3}
        elif match_type in ["Hardcore", "Extreme Rules", "Barbed Wire Deathmatch",
                            "Exploding Barbed Wire", "Landmine Deathmatch", "Underground Match"]:
            return {**default, 'hardcore': 2.5, 'toughness': 2.0, 'power': 1.3}
        elif match_type in ["Ladder Match", "TLC", "Cruiserweight"]:
            return {**default, 'aerial': 2.0, 'speed': 1.5, 'stamina': 1.3}
        elif match_type in ["Iron Man", "60-Minute Iron Man"]:
            return {**default, 'stamina': 2.5, 'psychology': 1.8, 'technical': 1.5}
        elif match_type in ["Steel Cage", "Hell in a Cell", "Elimination Chamber"]:
            return {**default, 'power': 1.5, 'toughness': 1.5, 'psychology': 1.3}
        elif match_type in ["Battle Royal", "Royal Rumble", "Casino Battle Royale"]:
            return {**default, 'power': 1.5, 'toughness': 1.3, 'charisma': 1.2}
        elif match_type in ["Promo Battle", "Mic Showdown"]:
            return {**default, 'mic_skills': 3.0, 'charisma': 2.0}

        return default

    # ==================== STORYLINE BONUS ====================

    def _get_storyline_data(self, wrestler1, wrestler2) -> Dict:
        """Check if there's an active storyline for this match"""
        if not self.storyline_engine:
            return {"bonus": 0.0, "id": None}

        try:
            wrestler_names = [wrestler1.name, wrestler2.name]
            storylines = self.storyline_engine.get_storylines_for_match(wrestler_names)
            if not storylines:
                return {"bonus": 0.0, "id": None}

            # Use highest-heat storyline
            best = max(storylines, key=lambda s: s.heat)
            return {
                "bonus": best.get_match_rating_bonus(),
                "id": best.id,
            }
        except Exception:
            return {"bonus": 0.0, "id": None}

    # ==================== CHEMISTRY (NEW: USES RELATIONSHIPS) ====================

    def _calculate_chemistry(self, wrestler1, wrestler2) -> float:
        """Calculate chemistry between two wrestlers using relationships + base"""
        chemistry = 0.0

        # Use Relationship Manager if available
        if self.relationship_manager:
            try:
                rel_modifier = self.relationship_manager.get_chemistry_modifier(
                    wrestler1.name, wrestler2.name
                )
                # Convert 1.0-1.4 modifier to -0.3 to +0.3 chemistry bonus
                chemistry += (rel_modifier - 1.0) * 0.5
            except Exception:
                pass

        # Skill-level similarity bonus
        ovr1 = getattr(wrestler1, 'overall_rating', 50)
        ovr2 = getattr(wrestler2, 'overall_rating', 50)
        skill_diff = abs(ovr1 - ovr2)
        if skill_diff < 10:
            chemistry += 0.15
        elif skill_diff < 20:
            chemistry += 0.05
        elif skill_diff > 40:
            chemistry -= 0.10

        # Alignment chemistry (Face vs Heel = better story)
        align1 = getattr(wrestler1, 'alignment', None)
        align2 = getattr(wrestler2, 'alignment', None)
        if align1 and align2:
            a1 = align1.value if hasattr(align1, 'value') else str(align1)
            a2 = align2.value if hasattr(align2, 'value') else str(align2)

            face_alignments = ["Face", "Mega Face"]
            heel_alignments = ["Heel", "Mega Heel"]

            face_vs_heel = (
                (a1 in face_alignments and a2 in heel_alignments) or
                (a1 in heel_alignments and a2 in face_alignments)
            )
            mega_clash = (
                (a1 == "Mega Face" and a2 == "Mega Heel") or
                (a1 == "Mega Heel" and a2 == "Mega Face")
            )

            if mega_clash:
                chemistry += 0.25  # Explosive matchup
            elif face_vs_heel:
                chemistry += 0.15
            elif a1 == a2 and a1 not in ["Tweener", "X-Factor", "Cooled Off"]:
                chemistry -= 0.05

        # Wrestling style chemistry
        style1 = getattr(wrestler1, 'primary_style', None)
        style2 = getattr(wrestler2, 'primary_style', None)
        if style1 and style2:
            s1 = style1.value if hasattr(style1, 'value') else str(style1)
            s2 = style2.value if hasattr(style2, 'value') else str(style2)
            good_combos = [
                ("Technician", "Powerhouse"), ("Luchador", "Giant"),
                ("Showman", "Technician"), ("Striker", "Luchador"),
                ("Hardcore", "Powerhouse"), ("All-Rounder", "Showman"),
                ("Technician", "Brawler"), ("High-Flyer", "Powerhouse"),
            ]
            for combo in good_combos:
                if (s1 == combo[0] and s2 == combo[1]) or (s1 == combo[1] and s2 == combo[0]):
                    chemistry += 0.10
                    break

        return max(-0.3, min(0.4, chemistry))

    # ==================== MORALE & STAMINA ====================

    def _get_morale_modifier(self, wrestler) -> float:
        """Get match rating modifier from morale state (uses new wrestler.py)"""
        if hasattr(wrestler, 'get_match_rating_modifier'):
            try:
                return wrestler.get_match_rating_modifier()
            except Exception:
                pass

        # Fallback: derive from morale value
        morale = getattr(wrestler, 'morale', 75)
        if morale >= 90:
            return 0.5
        elif morale >= 70:
            return 0.2
        elif morale >= 50:
            return 0.0
        elif morale >= 30:
            return -0.2
        elif morale >= 10:
            return -0.4
        else:
            return -0.6

    def _get_stamina_factor(self, wrestler, match_minutes: int) -> float:
        """Wrestlers with low stamina suffer in long matches"""
        stamina = getattr(wrestler, 'stamina', 50)

        if match_minutes <= 8:
            return 0  # Quick match, stamina doesn't matter
        elif match_minutes <= 15:
            # Standard match - mild penalty if low stamina
            if stamina < 40:
                return -3
            return 0
        elif match_minutes <= 25:
            # Long match - stamina matters
            if stamina < 50:
                return -8
            elif stamina >= 75:
                return 3
            return 0
        else:
            # Epic match - stamina is critical
            if stamina < 60:
                return -12
            elif stamina >= 80:
                return 5
            return 0

    def _get_crowd_reaction_power(self, wrestler) -> float:
        """Wrestlers with strong crowd reactions perform better"""
        if hasattr(wrestler, 'crowd_reaction'):
            reaction = wrestler.crowd_reaction
            reaction_value = reaction.value if hasattr(reaction, 'value') else str(reaction)

            # Mapped to performance bonuses
            if reaction_value == "Loved":
                return 5
            elif reaction_value == "Hated":
                return 4  # Heat is heat
            elif reaction_value == "Cult Following":
                return 4
            elif reaction_value == "Cheered":
                return 2
            elif reaction_value == "Booed":
                return 2
            elif reaction_value == "Respected":
                return 1
            elif reaction_value == "Mixed Reaction":
                return 0
            elif reaction_value == "Dead Silent":
                return -8

        return 0

    # ==================== UPSET DETECTION ====================

    def _is_upset(self, expected_winner, actual_winner) -> bool:
        """Detect if this is an upset based on popularity and level differences"""
        pop_diff = getattr(expected_winner, 'popularity', 50) - getattr(actual_winner, 'popularity', 50)
        level_diff = getattr(expected_winner, 'level_number', 5) - getattr(actual_winner, 'level_number', 5)

        return pop_diff > 15 or level_diff >= 3

    # ==================== PHILOSOPHY BONUS ====================

    def _get_philosophy_bonus(self, wrestler) -> float:
        """Get bonus based on promotion philosophy and wrestler style"""
        if not self.promotion:
            return 0.0
        try:
            return self.promotion.get_philosophy_style_bonus(wrestler.primary_style)
        except Exception:
            return 0.0

    # ==================== MATCH TYPE BONUS ====================

    def _get_match_type_bonus(self, wrestler, match_type: str) -> float:
        """Get bonus for wrestler based on match type and their style"""
        style_name = "All-Rounder"
        if hasattr(wrestler, 'primary_style') and wrestler.primary_style:
            style_name = wrestler.primary_style.value if hasattr(wrestler.primary_style, 'value') else str(wrestler.primary_style)

        bonuses = {
            # Standard
            "Singles": {"Technician": 0.05, "All-Rounder": 0.05},
            "Intergender Singles": {"All-Rounder": 0.05, "Showman": 0.05},
            "Triple Threat": {"All-Rounder": 0.10, "Luchador": 0.05},
            "Fatal Four Way": {"All-Rounder": 0.10, "Showman": 0.05},
            "5-Way Match": {"All-Rounder": 0.10, "Showman": 0.05},
            "6-Way Match": {"All-Rounder": 0.10, "Showman": 0.05},
            "8-Way Match": {"All-Rounder": 0.10, "Showman": 0.05},
            # Tag
            "Tag Team": {"All-Rounder": 0.05, "Technician": 0.05},
            "Mixed Tag": {"All-Rounder": 0.10, "Showman": 0.05},
            "Tornado Tag": {"Striker": 0.10, "Hardcore": 0.05, "Brawler": 0.05},
            "6-Man Tag": {"All-Rounder": 0.05, "Powerhouse": 0.05},
            "8-Man Tag": {"All-Rounder": 0.05, "Powerhouse": 0.05},
            "1-on-2 Handicap": {"Powerhouse": 0.15, "Giant": 0.10, "Striker": 0.05},
            "1-on-3 Handicap": {"Powerhouse": 0.20, "Giant": 0.15},
            "2-on-3 Handicap": {"All-Rounder": 0.10, "Striker": 0.05},
            # Hardcore
            "Extreme Rules": {"Hardcore": 0.15, "Brawler": 0.10, "Powerhouse": 0.05},
            "Falls Count Anywhere": {"Hardcore": 0.10, "Brawler": 0.10, "All-Rounder": 0.05},
            "Ladder Match": {"Luchador": 0.15, "High-Flyer": 0.15, "All-Rounder": 0.10, "Showman": 0.05},
            "Table Match": {"Powerhouse": 0.10, "Hardcore": 0.10, "Giant": 0.05},
            "TLC": {"Luchador": 0.10, "High-Flyer": 0.10, "Hardcore": 0.10, "All-Rounder": 0.05},
            "Barbed Wire Deathmatch": {"Hardcore": 0.20, "Brawler": 0.10},
            "Exploding Barbed Wire": {"Hardcore": 0.20, "Brawler": 0.10},
            "Landmine Deathmatch": {"Hardcore": 0.20, "Brawler": 0.10},
            # Cage
            "Steel Cage": {"Powerhouse": 0.10, "Technician": 0.10, "Brawler": 0.05},
            "Hell in a Cell": {"Hardcore": 0.15, "Brawler": 0.10, "Powerhouse": 0.05},
            "Elimination Chamber": {"All-Rounder": 0.10, "Technician": 0.05, "Brawler": 0.05},
            "War Games": {"Brawler": 0.10, "Powerhouse": 0.05, "All-Rounder": 0.05},
            # Specialty
            "Ambulance Match": {"Powerhouse": 0.10, "Hardcore": 0.10},
            "Casket Match": {"Powerhouse": 0.10, "Giant": 0.10},
            "Dumpster Match": {"Powerhouse": 0.10, "Hardcore": 0.05},
            "I Quit": {"Technician": 0.10, "Hardcore": 0.10, "Brawler": 0.05},
            "Inferno Match": {"Hardcore": 0.15, "Showman": 0.05},
            "Iron Man": {"Technician": 0.15, "All-Rounder": 0.10},
            "Last Man Standing": {"Powerhouse": 0.10, "Brawler": 0.10, "Hardcore": 0.05},
            "Submission Match": {"Technician": 0.20, "Brawler": 0.05},
            "3 Stages of Hell": {"All-Rounder": 0.15, "Technician": 0.10},
            "Underground Match": {"Hardcore": 0.15, "Brawler": 0.10},
            "Bloodline Rules": {"Brawler": 0.10, "Powerhouse": 0.10, "Hardcore": 0.05},
            "Brawl": {"Hardcore": 0.15, "Brawler": 0.10, "Powerhouse": 0.05},
            "Lumberjack Match": {"Showman": 0.10, "All-Rounder": 0.05},
            "Special Guest Referee": {"Showman": 0.10, "All-Rounder": 0.05},
            # Battle Royal
            "Battle Royal": {"Powerhouse": 0.10, "Giant": 0.10, "Brawler": 0.05},
            "Casino Battle Royale": {"Powerhouse": 0.10, "Giant": 0.10, "All-Rounder": 0.05},
            "Royal Rumble": {"Powerhouse": 0.10, "Giant": 0.10, "All-Rounder": 0.05},
            "Gauntlet Match": {"All-Rounder": 0.15, "Technician": 0.10},
            "Gauntlet Eliminator": {"All-Rounder": 0.10, "Brawler": 0.10},
            # Combat
            "MMA Rules": {"Striker": 0.20, "Technician": 0.10, "Brawler": 0.10},
            "Kickboxing Rules": {"Striker": 0.20, "Brawler": 0.10},
        }

        match_bonuses = bonuses.get(match_type, {})
        return match_bonuses.get(style_name, 0.0)

    # ==================== MATCH RATING ====================

    def _calculate_match_rating(
        self, wrestler1, wrestler2, chemistry,
        phil_bonus1, phil_bonus2, match_bonus1, match_bonus2,
        is_title_match, is_main_event, crowd_bonus, match_type,
        storyline_bonus, match_minutes,
        morale_mod1, morale_mod2,
    ) -> float:
        """Calculate the star rating with all bonuses applied"""
        ovr1 = getattr(wrestler1, 'overall_rating', 50)
        ovr2 = getattr(wrestler2, 'overall_rating', 50)

        # Base from wrestler quality (0-5 scale)
        avg_skill = (ovr1 + ovr2) / 2
        base_rating = (avg_skill / 100) * 3.5

        # Chemistry bonus (relationships + base)
        base_rating += chemistry * 1.5

        # Storyline bonus (heat-driven)
        base_rating += storyline_bonus

        # Philosophy bonuses
        phil_avg = (phil_bonus1 + phil_bonus2) / 2
        base_rating += phil_avg * 0.5

        # Match type bonuses
        match_avg = (match_bonus1 + match_bonus2) / 2
        base_rating += match_avg * 0.5

        # Morale state impact
        morale_avg = (morale_mod1 + morale_mod2) / 2
        base_rating += morale_avg * 0.3

        # Stipulation bonuses
        if is_title_match:
            base_rating += 0.2
        if is_main_event:
            base_rating += 0.15

        # Crowd energy
        base_rating += crowd_bonus * 0.01

        # Match length bonus (longer = better if both wrestlers can handle it)
        if match_minutes >= 15:
            stamina_avg = (getattr(wrestler1, 'stamina', 50) + getattr(wrestler2, 'stamina', 50)) / 2
            if stamina_avg >= 70:
                base_rating += 0.1
            elif stamina_avg < 50:
                base_rating -= 0.15

        # Random variance (consistency-affected)
        consistency_avg = (
            getattr(wrestler1, 'consistency', 50) + getattr(wrestler2, 'consistency', 50)
        ) / 2
        var_range = 0.4 - (consistency_avg / 100 * 0.2)  # 0.2-0.4
        base_rating += random.uniform(-var_range, var_range)

        # Popularity multiplier
        pop_avg = (
            getattr(wrestler1, 'popularity', 50) + getattr(wrestler2, 'popularity', 50)
        ) / 2
        pop_mult = 1.0 + (pop_avg - 50) * 0.003
        base_rating *= pop_mult

        # Indy God boost
        if getattr(wrestler1, 'is_indy_god', False) or getattr(wrestler2, 'is_indy_god', False):
            base_rating += 0.15

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

    # ==================== FINISH DETERMINATION ====================

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

        # Standard match finishes - based on wrestler style
        style1 = getattr(wrestler1, 'primary_style', None)
        s1 = style1.value if style1 and hasattr(style1, 'value') else "All-Rounder"

        if s1 == "Technician":
            weights = [0.4, 0.4, 0.1, 0.05, 0.05]
        elif s1 in ["Powerhouse", "Giant"]:
            weights = [0.6, 0.1, 0.1, 0.1, 0.1]
        elif s1 == "Hardcore":
            weights = [0.4, 0.1, 0.2, 0.1, 0.2]
        elif s1 in ["Luchador", "High-Flyer"]:
            weights = [0.5, 0.2, 0.1, 0.1, 0.1]
        elif s1 == "Striker":
            weights = [0.4, 0.15, 0.1, 0.1, 0.25]
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

    # ==================== CROWD REACTION ====================

    def _calculate_crowd_reaction(
        self, wrestler1, wrestler2, match_rating,
        is_title_match, is_main_event, is_upset,
        storyline_bonus,
    ) -> int:
        """Calculate crowd reaction (0-100)"""
        base = int(match_rating * 15)

        pop_avg = (
            getattr(wrestler1, 'popularity', 50) + getattr(wrestler2, 'popularity', 50)
        ) / 2
        base += int(pop_avg * 0.3)

        if is_title_match:
            base += 10
        if is_main_event:
            base += 8
        if is_upset:
            base += 12

        # Storyline crowd bonus
        base += int(storyline_bonus * 30)

        # Alignment drama (Face vs Heel = louder reactions)
        align1 = getattr(wrestler1, 'alignment', None)
        align2 = getattr(wrestler2, 'alignment', None)
        if align1 and align2:
            a1 = align1.value if hasattr(align1, 'value') else str(align1)
            a2 = align2.value if hasattr(align2, 'value') else str(align2)

            face_alignments = ["Face", "Mega Face"]
            heel_alignments = ["Heel", "Mega Heel"]

            face_vs_heel = (
                (a1 in face_alignments and a2 in heel_alignments) or
                (a1 in heel_alignments and a2 in face_alignments)
            )
            mega_clash = (
                (a1 == "Mega Face" and a2 == "Mega Heel") or
                (a1 == "Mega Heel" and a2 == "Mega Face")
            )

            if mega_clash:
                base += 15
            elif face_vs_heel:
                base += 8

        # Indy God presence boost
        if getattr(wrestler1, 'is_indy_god', False) or getattr(wrestler2, 'is_indy_god', False):
            base += 10

        # Random variance
        base += random.randint(-5, 5)

        return max(10, min(100, base))

    # ==================== POST-MATCH EFFECTS ====================

    def _apply_match_effects(
        self, winner, loser, match_rating,
        is_title_match, is_main_event,
    ) -> Dict:
        """Apply post-match effects to wrestlers and return morale impact"""
        morale_impact = {
            "winner": 0,
            "loser": 0,
        }

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

        # Winner morale boost
        if hasattr(winner, 'adjust_morale'):
            morale_gain = 2
            if match_rating >= 4.5:
                morale_gain = 8
            elif match_rating >= 4.0:
                morale_gain = 5
            elif match_rating >= 3.0:
                morale_gain = 3
            if is_title_match:
                morale_gain += 5
            winner.adjust_morale(morale_gain)
            morale_impact["winner"] = morale_gain

        # Record win on wrestler
        if hasattr(winner, 'record_match'):
            winner.record_match("win", match_rating)

        # Adjust popularity for winner
        if hasattr(winner, 'adjust_popularity'):
            pop_gain = 1
            if is_main_event:
                pop_gain += 2
            if match_rating >= 4.5:
                pop_gain += 3
            elif match_rating >= 4.0:
                pop_gain += 2
            winner.adjust_popularity(pop_gain)

        # Loser effects
        if hasattr(loser, 'adjust_momentum'):
            momentum_loss = -2
            if is_main_event:
                momentum_loss -= 2
            loser.adjust_momentum(momentum_loss)

        if hasattr(loser, 'add_fatigue'):
            loser.add_fatigue(random.randint(8, 15))

        # Loser morale impact (less severe if it was a great match)
        if hasattr(loser, 'adjust_morale'):
            morale_loss = -3
            if match_rating >= 4.5:
                morale_loss = 0  # Honored to be in a classic
            elif match_rating >= 4.0:
                morale_loss = -1
            elif match_rating < 2.0:
                morale_loss = -8
            loser.adjust_morale(morale_loss)
            morale_impact["loser"] = morale_loss

        # Record loss on wrestler
        if hasattr(loser, 'record_match'):
            loser.record_match("loss", match_rating)

        # Slight popularity loss for loser (less if good match)
        if hasattr(loser, 'adjust_popularity'):
            pop_loss = -1
            if match_rating >= 4.0:
                pop_loss = 0  # Even in defeat, looked good
            loser.adjust_popularity(pop_loss)

        # Random injury check
        if hasattr(loser, 'check_injury'):
            injury_chance = 3
            if match_rating < 2.0:
                injury_chance += 2
            loser.check_injury(injury_chance)

        return morale_impact


# ==================== CONVENIENCE FUNCTION ====================

def quick_match(wrestler1, wrestler2, match_type: str = "Singles") -> MatchResult:
    """Quick match simulation without full integration context"""
    engine = MatchEngine()
    return engine.simulate_match(wrestler1, wrestler2, match_type=match_type)
