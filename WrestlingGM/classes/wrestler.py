"""
Wrestler Class - Core entity for all wrestlers in the game
"""

import random
from typing import List, Optional
from classes.enums import Gender, WeightClass, WrestlingStyle, Alignment


class Wrestler:
    def __init__(
        self,
        # Identity
        name: str,
        nickname: Optional[str] = None,
        age: int = 25,
        gender: Gender = Gender.MALE,
        hometown: str = "Unknown",
        
        # Physical
        height: int = 72,  # inches
        weight: int = 220,  # pounds
        
        # Wrestling Style
        primary_style: WrestlingStyle = WrestlingStyle.ALL_ROUNDER,
        secondary_style: Optional[WrestlingStyle] = None,
        alignment: Alignment = Alignment.FACE,
        
        # Core Stats (1-100 scale)
        power: int = 50,
        speed: int = 50,
        technical: int = 50,
        stamina: int = 50,
        charisma: int = 50,
        hardcore: int = 50,
        aerial: int = 50,
        
        # Hidden Stats
        consistency: int = 50,      # How often they perform at their best
        work_ethic: int = 50,       # Affects improvement rate
        loyalty: int = 50,          # Contract negotiations
        ego: int = 50,              # Backstage issues potential
        professionalism: int = 50,  # Shows up on time, no drama
        
        # Status
        popularity: int = 50,
        momentum: int = 50,
        morale: int = 75,
        injury_prone: int = 50,     # Higher = more likely to get hurt
        fatigue: int = 0,           # 0-100, builds over time
        
        # Contract
        salary: int = 500,          # Weekly salary
        contract_length: int = 52,  # Weeks remaining
        is_exclusive: bool = True,
        
        # Special
        unique_traits: Optional[List[str]] = None,
        finisher_name: str = "Finisher",
        signature_moves: Optional[List[str]] = None,
    ):
        # Identity
        self.name = name
        self.nickname = nickname
        self.age = age
        self.gender = gender
        self.hometown = hometown
        
        # Physical
        self.height = height
        self.weight = weight
        self.weight_class = self._calculate_weight_class()
        
        # Wrestling
        self.primary_style = primary_style
        self.secondary_style = secondary_style
        self.alignment = alignment
        
        # Core Stats
        self.power = self._clamp_stat(power)
        self.speed = self._clamp_stat(speed)
        self.technical = self._clamp_stat(technical)
        self.stamina = self._clamp_stat(stamina)
        self.charisma = self._clamp_stat(charisma)
        self.hardcore = self._clamp_stat(hardcore)
        self.aerial = self._clamp_stat(aerial)
        
        # Hidden Stats
        self.consistency = self._clamp_stat(consistency)
        self.work_ethic = self._clamp_stat(work_ethic)
        self.loyalty = self._clamp_stat(loyalty)
        self.ego = self._clamp_stat(ego)
        self.professionalism = self._clamp_stat(professionalism)
        
        # Status
        self.popularity = self._clamp_stat(popularity)
        self.momentum = self._clamp_stat(momentum)
        self.morale = self._clamp_stat(morale)
        self.injury_prone = self._clamp_stat(injury_prone)
        self.fatigue = self._clamp_stat(fatigue)
        self.is_injured = False
        self.injury_weeks_remaining = 0
        self.injury_type: Optional[str] = None
        
        # Contract
        self.salary = salary
        self.contract_length = contract_length
        self.is_exclusive = is_exclusive
        self.is_signed = True
        
        # Special
        self.unique_traits = unique_traits or []
        self.finisher_name = finisher_name
        self.signature_moves = signature_moves or []
        
        # Career Tracking
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.titles_held = 0
        self.five_star_matches = 0
        
    def _clamp_stat(self, value: int) -> int:
        """Keep stats within 1-100 range"""
        return max(1, min(100, value))
    
    def _calculate_weight_class(self) -> WeightClass:
        """Determine weight class based on weight"""
        if self.weight < 200:
            return WeightClass.JUNIOR
        elif self.weight < 220:
            return WeightClass.CRUISERWEIGHT
        elif self.weight < 240:
            return WeightClass.MIDDLEWEIGHT
        elif self.weight < 265:
            return WeightClass.HEAVYWEIGHT
        else:
            return WeightClass.SUPER_HEAVYWEIGHT
    
    @property
    def overall_rating(self) -> int:
        """Calculate overall rating from core stats"""
        stats = [
            self.power,
            self.speed,
            self.technical,
            self.stamina,
            self.charisma,
            self.hardcore,
            self.aerial
        ]
        return int(sum(stats) / len(stats))
    
    @property
    def display_name(self) -> str:
        """Full display name with nickname"""
        if self.nickname:
            return f'{self.name} "{self.nickname}"'
        return self.name
    
    @property
    def win_percentage(self) -> float:
        """Calculate win percentage"""
        total = self.wins + self.losses + self.draws
        if total == 0:
            return 0.0
        return (self.wins / total) * 100
    
    def get_performance_rating(self) -> int:
        """
        Calculate tonight's performance based on stats and randomness.
        Consistency affects how close to their max they perform.
        """
        base = self.overall_rating
        
        # Consistency roll
        consistency_factor = self.consistency / 100
        variance = int((100 - self.consistency) * 0.3)
        roll = random.randint(-variance, variance)
        
        # Fatigue penalty
        fatigue_penalty = int(self.fatigue * 0.2)
        
        # Morale bonus/penalty
        morale_modifier = int((self.morale - 50) * 0.1)
        
        # Momentum bonus
        momentum_modifier = int((self.momentum - 50) * 0.15)
        
        # Injury penalty
        injury_penalty = 15 if self.is_injured else 0
        
        performance = base + roll - fatigue_penalty + morale_modifier + momentum_modifier - injury_penalty
        
        return self._clamp_stat(performance)
    
    def add_fatigue(self, amount: int):
        """Add fatigue after a match"""
        self.fatigue = self._clamp_stat(self.fatigue + amount)
    
    def rest(self, days: int = 7):
        """Recover fatigue over time"""
        recovery = days * 5
        self.fatigue = max(0, self.fatigue - recovery)
    
    def injure(self, injury_type: str, weeks: int):
        """Apply an injury to the wrestler"""
        self.is_injured = True
        self.injury_type = injury_type
        self.injury_weeks_remaining = weeks
        self.morale = max(1, self.morale - 15)
    
    def heal(self):
        """Process weekly healing"""
        if self.is_injured:
            self.injury_weeks_remaining -= 1
            if self.injury_weeks_remaining <= 0:
                self.is_injured = False
                self.injury_type = None
                self.injury_weeks_remaining = 0
    
    def adjust_momentum(self, amount: int):
        """Adjust momentum after match results"""
        self.momentum = self._clamp_stat(self.momentum + amount)
    
    def adjust_popularity(self, amount: int):
        """Adjust popularity"""
        self.popularity = self._clamp_stat(self.popularity + amount)
    
    def record_match(self, result: str):
        """Record match result: 'win', 'loss', or 'draw'"""
        if result == "win":
            self.wins += 1
            self.adjust_momentum(5)
        elif result == "loss":
            self.losses += 1
            self.adjust_momentum(-3)
        elif result == "draw":
            self.draws += 1
            self.adjust_momentum(1)
    
    def has_trait(self, trait: str) -> bool:
        """Check if wrestler has a specific trait"""
        return trait.lower() in [t.lower() for t in self.unique_traits]
    
    def add_trait(self, trait: str):
        """Add a unique trait"""
        if not self.has_trait(trait):
            self.unique_traits.append(trait)
    
    def remove_trait(self, trait: str):
        """Remove a unique trait"""
        self.unique_traits = [t for t in self.unique_traits if t.lower() != trait.lower()]
    
    def weekly_update(self):
        """Process weekly changes"""
        # Contract countdown
        if self.contract_length > 0:
            self.contract_length -= 1
        
        # Heal injuries
        self.heal()
        
        # Natural fatigue recovery
        self.rest(7)
        
        # Age-based decline (after 35)
        if self.age > 35 and random.random() < 0.05:
            stat_to_decline = random.choice(['power', 'speed', 'stamina', 'aerial'])
            current = getattr(self, stat_to_decline)
            setattr(self, stat_to_decline, max(1, current - 1))
    
    def to_dict(self) -> dict:
        """Convert wrestler to dictionary for saving"""
        return {
            "name": self.name,
            "nickname": self.nickname,
            "age": self.age,
            "gender": self.gender.value,
            "hometown": self.hometown,
            "height": self.height,
            "weight": self.weight,
            "primary_style": self.primary_style.value,
            "secondary_style": self.secondary_style.value if self.secondary_style else None,
            "alignment": self.alignment.value,
            "power": self.power,
            "speed": self.speed,
            "technical": self.technical,
            "stamina": self.stamina,
            "charisma": self.charisma,
            "hardcore": self.hardcore,
            "aerial": self.aerial,
            "consistency": self.consistency,
            "work_ethic": self.work_ethic,
            "loyalty": self.loyalty,
            "ego": self.ego,
            "professionalism": self.professionalism,
            "popularity": self.popularity,
            "momentum": self.momentum,
            "morale": self.morale,
            "injury_prone": self.injury_prone,
            "fatigue": self.fatigue,
            "salary": self.salary,
            "contract_length": self.contract_length,
            "is_exclusive": self.is_exclusive,
            "unique_traits": self.unique_traits,
            "finisher_name": self.finisher_name,
            "signature_moves": self.signature_moves,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "titles_held": self.titles_held,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Wrestler":
        """Create wrestler from dictionary"""
        wrestler = cls(
            name=data["name"],
            nickname=data.get("nickname"),
            age=data.get("age", 25),
            gender=Gender(data.get("gender", "Male")),
            hometown=data.get("hometown", "Unknown"),
            height=data.get("height", 72),
            weight=data.get("weight", 220),
            primary_style=WrestlingStyle(data.get("primary_style", "All Rounder")),
            secondary_style=WrestlingStyle(data["secondary_style"]) if data.get("secondary_style") else None,
            alignment=Alignment(data.get("alignment", "Face")),
            power=data.get("power", 50),
            speed=data.get("speed", 50),
            technical=data.get("technical", 50),
            stamina=data.get("stamina", 50),
            charisma=data.get("charisma", 50),
            hardcore=data.get("hardcore", 50),
            aerial=data.get("aerial", 50),
            consistency=data.get("consistency", 50),
            work_ethic=data.get("work_ethic", 50),
            loyalty=data.get("loyalty", 50),
            ego=data.get("ego", 50),
            professionalism=data.get("professionalism", 50),
            popularity=data.get("popularity", 50),
            momentum=data.get("momentum", 50),
            morale=data.get("morale", 75),
            injury_prone=data.get("injury_prone", 50),
            fatigue=data.get("fatigue", 0),
            salary=data.get("salary", 500),
            contract_length=data.get("contract_length", 52),
            is_exclusive=data.get("is_exclusive", True),
            unique_traits=data.get("unique_traits", []),
            finisher_name=data.get("finisher_name", "Finisher"),
            signature_moves=data.get("signature_moves", []),
        )
        wrestler.wins = data.get("wins", 0)
        wrestler.losses = data.get("losses", 0)
        wrestler.draws = data.get("draws", 0)
        wrestler.titles_held = data.get("titles_held", 0)
        return wrestler
    
    def __repr__(self) -> str:
        return f"Wrestler({self.name}, {self.overall_rating}ovr, {self.primary_style.value})"