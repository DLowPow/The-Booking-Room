"""
Production System - Show logistics and production elements
Tiered by venue size with realistic pricing
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


class ProductionCategory(Enum):
    RING = "Ring Setup"
    LIGHTING = "Lighting"
    CAMERAS = "Camera Crew"
    BACKSTAGE = "Backstage"
    PYRO = "Pyrotechnics"
    ENTRANCE = "Entrance Setup"
    AUDIO = "Audio & Music"


# ==================== RING TYPES ====================

@dataclass
class RingOption:
    """A ring setup option"""
    id: str
    name: str
    description: str
    cost: int
    min_venue_tier: int = 1
    
    # Match quality effects
    match_quality_bonus: int = 0
    injury_risk_modifier: float = 1.0  # 1.0 = normal, higher = more injuries
    
    # Style bonuses/penalties
    lucha_modifier: float = 1.0  # How good for lucha/high flying
    hardcore_modifier: float = 1.0  # How good for hardcore
    technical_modifier: float = 1.0  # How good for technical
    power_modifier: float = 1.0  # How good for power moves
    
    # Special
    is_special: bool = False
    fan_novelty_bonus: int = 0  # Extra fans from novelty


RING_OPTIONS = {
    "boxing_ring": RingOption(
        id="boxing_ring",
        name="Boxing Ring",
        description="A standard boxing ring. Hard canvas, thin ropes. Not ideal for wrestling but cheap.",
        cost=100,
        min_venue_tier=1,
        match_quality_bonus=-3,
        injury_risk_modifier=1.4,
        lucha_modifier=0.5,
        hardcore_modifier=1.2,
        technical_modifier=0.8,
        power_modifier=1.0,
    ),
    "wrestling_ring_basic": RingOption(
        id="wrestling_ring_basic",
        name="Basic Wrestling Ring (16ft)",
        description="A small, basic wrestling ring. Gets the job done but nothing special.",
        cost=300,
        min_venue_tier=1,
        match_quality_bonus=0,
        injury_risk_modifier=1.1,
        lucha_modifier=0.8,
        hardcore_modifier=1.0,
        technical_modifier=1.0,
        power_modifier=0.9,
    ),
    "wrestling_ring_standard": RingOption(
        id="wrestling_ring_standard",
        name="Standard Wrestling Ring (18ft)",
        description="A proper 18-foot wrestling ring. Industry standard size.",
        cost=600,
        min_venue_tier=1,
        match_quality_bonus=3,
        injury_risk_modifier=1.0,
        lucha_modifier=1.0,
        hardcore_modifier=1.0,
        technical_modifier=1.0,
        power_modifier=1.0,
    ),
    "wrestling_ring_pro": RingOption(
        id="wrestling_ring_pro",
        name="Professional Wrestling Ring (20ft)",
        description="A premium 20-foot ring with quality ropes and padding. Used by major promotions.",
        cost=1500,
        min_venue_tier=2,
        match_quality_bonus=6,
        injury_risk_modifier=0.9,
        lucha_modifier=1.1,
        hardcore_modifier=1.0,
        technical_modifier=1.1,
        power_modifier=1.1,
    ),
    "wrestling_ring_elite": RingOption(
        id="wrestling_ring_elite",
        name="Elite Wrestling Ring (20ft)",
        description="Top-of-the-line ring with LED apron, premium canvas, and superior bump protection.",
        cost=5000,
        min_venue_tier=3,
        match_quality_bonus=10,
        injury_risk_modifier=0.8,
        lucha_modifier=1.2,
        hardcore_modifier=0.9,
        technical_modifier=1.2,
        power_modifier=1.1,
    ),
    "six_sided_ring": RingOption(
        id="six_sided_ring",
        name="Six-Sided Ring",
        description="The iconic 6-sided ring! Unique look that fans love. Changes match dynamics significantly.",
        cost=2000,
        min_venue_tier=2,
        match_quality_bonus=5,
        injury_risk_modifier=1.05,
        lucha_modifier=1.3,
        hardcore_modifier=0.8,
        technical_modifier=0.9,
        power_modifier=0.9,
        is_special=True,
        fan_novelty_bonus=50,
    ),
}


# ==================== PRODUCTION ITEMS ====================

@dataclass
class ProductionItem:
    """A production element for shows"""
    id: str
    name: str
    category: ProductionCategory
    description: str
    cost: int  # Per show cost
    min_venue_tier: int = 1
    
    # Effects
    show_quality_bonus: int = 0
    fan_excitement_bonus: int = 0
    prestige_bonus: int = 0
    
    # Requirements
    requires: List[str] = field(default_factory=list)  # IDs of required items


# ==================== LIGHTING ====================

LIGHTING_OPTIONS = {
    # Tier 1
    "lighting_none": ProductionItem(
        id="lighting_none",
        name="House Lights Only",
        category=ProductionCategory.LIGHTING,
        description="Just the venue's existing lights. Cheap but looks amateur.",
        cost=0,
        min_venue_tier=1,
        show_quality_bonus=0,
        fan_excitement_bonus=0,
    ),
    "lighting_basic": ProductionItem(
        id="lighting_basic",
        name="Basic Spotlight",
        category=ProductionCategory.LIGHTING,
        description="A single spotlight on the ring. Better than nothing.",
        cost=50,
        min_venue_tier=1,
        show_quality_bonus=1,
        fan_excitement_bonus=2,
    ),
    "lighting_standard": ProductionItem(
        id="lighting_standard",
        name="Standard Show Lighting",
        category=ProductionCategory.LIGHTING,
        description="Ring lights, entrance way lighting, and basic color washes.",
        cost=200,
        min_venue_tier=1,
        show_quality_bonus=3,
        fan_excitement_bonus=5,
    ),
    # Tier 2
    "lighting_pro": ProductionItem(
        id="lighting_pro",
        name="Professional Lighting Rig",
        category=ProductionCategory.LIGHTING,
        description="Moving head lights, color themes per wrestler, entrance effects.",
        cost=800,
        min_venue_tier=2,
        show_quality_bonus=5,
        fan_excitement_bonus=10,
        prestige_bonus=2,
    ),
    # Tier 3
    "lighting_concert": ProductionItem(
        id="lighting_concert",
        name="Concert-Grade Lighting",
        category=ProductionCategory.LIGHTING,
        description="Full intelligent lighting rig with DMX control. Looks like a major show.",
        cost=3000,
        min_venue_tier=3,
        show_quality_bonus=8,
        fan_excitement_bonus=15,
        prestige_bonus=5,
    ),
    # Tier 4
    "lighting_arena": ProductionItem(
        id="lighting_arena",
        name="Arena Lighting System",
        category=ProductionCategory.LIGHTING,
        description="Full arena production with lasers, strobes, and atmospheric effects.",
        cost=8000,
        min_venue_tier=4,
        show_quality_bonus=12,
        fan_excitement_bonus=20,
        prestige_bonus=8,
    ),
    # Tier 5+
    "lighting_stadium": ProductionItem(
        id="lighting_stadium",
        name="Stadium Spectacular",
        category=ProductionCategory.LIGHTING,
        description="Hollywood-level lighting design. Every entrance is a movie moment.",
        cost=25000,
        min_venue_tier=5,
        show_quality_bonus=18,
        fan_excitement_bonus=30,
        prestige_bonus=12,
    ),
}


# ==================== CAMERAS ====================

CAMERA_OPTIONS = {
    "camera_none": ProductionItem(
        id="camera_none",
        name="No Cameras",
        category=ProductionCategory.CAMERAS,
        description="No recording. This show exists only in memory.",
        cost=0,
        min_venue_tier=1,
    ),
    "camera_phone": ProductionItem(
        id="camera_phone",
        name="Phone/Handheld Recording",
        category=ProductionCategory.CAMERAS,
        description="Someone with a phone or cheap camera. For social media clips.",
        cost=50,
        min_venue_tier=1,
        show_quality_bonus=1,
        fan_excitement_bonus=3,
    ),
    "camera_single": ProductionItem(
        id="camera_single",
        name="Single Camera Setup",
        category=ProductionCategory.CAMERAS,
        description="One proper camera on a tripod. Hard cam view.",
        cost=200,
        min_venue_tier=1,
        show_quality_bonus=2,
        fan_excitement_bonus=5,
    ),
    "camera_multi": ProductionItem(
        id="camera_multi",
        name="Multi-Camera (3 cameras)",
        category=ProductionCategory.CAMERAS,
        description="Hard cam, ringside, and roaming camera. Real production value.",
        cost=1000,
        min_venue_tier=2,
        show_quality_bonus=5,
        fan_excitement_bonus=10,
        prestige_bonus=3,
    ),
    "camera_broadcast": ProductionItem(
        id="camera_broadcast",
        name="Broadcast Package (6+ cameras)",
        category=ProductionCategory.CAMERAS,
        description="Full broadcast setup with crane, steadicam, and replay system.",
        cost=5000,
        min_venue_tier=3,
        show_quality_bonus=10,
        fan_excitement_bonus=15,
        prestige_bonus=6,
    ),
    "camera_premium": ProductionItem(
        id="camera_premium",
        name="Premium Broadcast (10+ cameras)",
        category=ProductionCategory.CAMERAS,
        description="Multiple angles, slow-mo replay, picture-in-picture. TV quality.",
        cost=12000,
        min_venue_tier=4,
        show_quality_bonus=15,
        fan_excitement_bonus=20,
        prestige_bonus=10,
    ),
    "camera_cinematic": ProductionItem(
        id="camera_cinematic",
        name="Cinematic Production (20+ cameras)",
        category=ProductionCategory.CAMERAS,
        description="Drones, spidercam, jib arms, 4K everywhere. Movie-quality production.",
        cost=35000,
        min_venue_tier=5,
        show_quality_bonus=20,
        fan_excitement_bonus=30,
        prestige_bonus=15,
    ),
}


# ==================== BACKSTAGE ====================

BACKSTAGE_OPTIONS = {
    "backstage_none": ProductionItem(
        id="backstage_none",
        name="No Backstage Setup",
        category=ProductionCategory.BACKSTAGE,
        description="Wrestlers change in bathrooms or their cars. Not professional.",
        cost=0,
        min_venue_tier=1,
        show_quality_bonus=-2,
    ),
    "backstage_basic": ProductionItem(
        id="backstage_basic",
        name="Basic Changing Area",
        category=ProductionCategory.BACKSTAGE,
        description="A curtained off area with some chairs. Minimal but functional.",
        cost=100,
        min_venue_tier=1,
        show_quality_bonus=0,
    ),
    "backstage_standard": ProductionItem(
        id="backstage_standard",
        name="Standard Backstage",
        category=ProductionCategory.BACKSTAGE,
        description="Proper changing rooms, gorilla position, and a monitor for wrestlers to watch.",
        cost=400,
        min_venue_tier=1,
        show_quality_bonus=2,
        fan_excitement_bonus=2,
    ),
    "backstage_catering": ProductionItem(
        id="backstage_catering",
        name="Backstage with Catering",
        category=ProductionCategory.BACKSTAGE,
        description="Full backstage area with food and drinks. Keeps the roster happy.",
        cost=1000,
        min_venue_tier=2,
        show_quality_bonus=3,
        fan_excitement_bonus=3,
    ),
    "backstage_pro": ProductionItem(
        id="backstage_pro",
        name="Professional Backstage",
        category=ProductionCategory.BACKSTAGE,
        description="Full catering, gorilla position with monitors, hair & makeup station, medical room.",
        cost=3000,
        min_venue_tier=3,
        show_quality_bonus=5,
        fan_excitement_bonus=5,
        prestige_bonus=3,
    ),
    "backstage_premium": ProductionItem(
        id="backstage_premium",
        name="Premium Backstage Suite",
        category=ProductionCategory.BACKSTAGE,
        description="Private dressing rooms, full catering, medical team, gear designers, hair & makeup, green room.",
        cost=8000,
        min_venue_tier=4,
        show_quality_bonus=8,
        fan_excitement_bonus=8,
        prestige_bonus=5,
    ),
    "backstage_elite": ProductionItem(
        id="backstage_elite",
        name="Elite Production Complex",
        category=ProductionCategory.BACKSTAGE,
        description="WWE-level backstage: interview areas, multiple dressing rooms, full medical, promo studio, everything.",
        cost=20000,
        min_venue_tier=5,
        show_quality_bonus=12,
        fan_excitement_bonus=12,
        prestige_bonus=8,
    ),
}


# ==================== PYRO ====================

PYRO_OPTIONS = {
    "pyro_none": ProductionItem(
        id="pyro_none",
        name="No Pyro",
        category=ProductionCategory.PYRO,
        description="No pyrotechnics. Safe and cheap.",
        cost=0,
        min_venue_tier=1,
    ),
    "pyro_fog": ProductionItem(
        id="pyro_fog",
        name="Fog Machines",
        category=ProductionCategory.PYRO,
        description="Atmospheric fog for entrances. Cheap but effective mood setter.",
        cost=100,
        min_venue_tier=1,
        fan_excitement_bonus=5,
    ),
    "pyro_sparklers": ProductionItem(
        id="pyro_sparklers",
        name="Sparklers & Cold Sparks",
        category=ProductionCategory.PYRO,
        description="Cold spark fountains for entrances. Safe enough for small venues.",
        cost=400,
        min_venue_tier=2,
        fan_excitement_bonus=10,
        prestige_bonus=2,
    ),
    "pyro_basic": ProductionItem(
        id="pyro_basic",
        name="Basic Pyro Package",
        category=ProductionCategory.PYRO,
        description="Flash pots, gerbs, and single-shot mortars. Real pyro.",
        cost=1500,
        min_venue_tier=3,
        fan_excitement_bonus=18,
        prestige_bonus=4,
        show_quality_bonus=3,
    ),
    "pyro_standard": ProductionItem(
        id="pyro_standard",
        name="Standard Pyro Show",
        category=ProductionCategory.PYRO,
        description="Flame bars, waterfalls, comets, and timed sequences for key moments.",
        cost=5000,
        min_venue_tier=4,
        fan_excitement_bonus=25,
        prestige_bonus=8,
        show_quality_bonus=5,
    ),
    "pyro_spectacular": ProductionItem(
        id="pyro_spectacular",
        name="Spectacular Pyro Display",
        category=ProductionCategory.PYRO,
        description="Full fireworks display with mortars, mines, cakes, and perfectly choreographed sequences.",
        cost=15000,
        min_venue_tier=5,
        fan_excitement_bonus=40,
        prestige_bonus=12,
        show_quality_bonus=8,
    ),
    "pyro_wrestlemania": ProductionItem(
        id="pyro_wrestlemania",
        name="WrestleMania-Level Pyro",
        category=ProductionCategory.PYRO,
        description="The biggest pyro display in wrestling. Fireworks that rival New Year's Eve.",
        cost=50000,
        min_venue_tier=6,
        fan_excitement_bonus=60,
        prestige_bonus=20,
        show_quality_bonus=12,
    ),
}


# ==================== ENTRANCE ====================

ENTRANCE_OPTIONS = {
    "entrance_curtain": ProductionItem(
        id="entrance_curtain",
        name="Curtain Only",
        category=ProductionCategory.ENTRANCE,
        description="A simple curtain wrestlers walk through. As basic as it gets.",
        cost=50,
        min_venue_tier=1,
        show_quality_bonus=0,
    ),
    "entrance_banner": ProductionItem(
        id="entrance_banner",
        name="Branded Backdrop",
        category=ProductionCategory.ENTRANCE,
        description="A printed banner or backdrop with your promotion logo.",
        cost=200,
        min_venue_tier=1,
        show_quality_bonus=1,
        fan_excitement_bonus=3,
        prestige_bonus=1,
    ),
    "entrance_ramp": ProductionItem(
        id="entrance_ramp",
        name="Entrance Ramp",
        category=ProductionCategory.ENTRANCE,
        description="A proper entrance ramp from stage to ring.",
        cost=800,
        min_venue_tier=2,
        show_quality_bonus=3,
        fan_excitement_bonus=8,
        prestige_bonus=2,
    ),
    "entrance_stage": ProductionItem(
        id="entrance_stage",
        name="Stage & Ramp Setup",
        category=ProductionCategory.ENTRANCE,
        description="Elevated stage with LED screen, ramp, and branded set pieces.",
        cost=3000,
        min_venue_tier=3,
        show_quality_bonus=6,
        fan_excitement_bonus=15,
        prestige_bonus=5,
    ),
    "entrance_premium": ProductionItem(
        id="entrance_premium",
        name="Premium Entrance Set",
        category=ProductionCategory.ENTRANCE,
        description="Custom themed stage with multiple screens, moving parts, and wrestler-specific effects.",
        cost=10000,
        min_venue_tier=4,
        show_quality_bonus=10,
        fan_excitement_bonus=22,
        prestige_bonus=8,
    ),
    "entrance_spectacular": ProductionItem(
        id="entrance_spectacular",
        name="Spectacular Entrance Complex",
        category=ProductionCategory.ENTRANCE,
        description="Multi-level stage with lifts, vehicles, theatrical elements. Every entrance is a spectacle.",
        cost=30000,
        min_venue_tier=5,
        show_quality_bonus=15,
        fan_excitement_bonus=35,
        prestige_bonus=12,
    ),
}


# ==================== AUDIO ====================

AUDIO_OPTIONS = {
    "audio_bluetooth": ProductionItem(
        id="audio_bluetooth",
        name="Bluetooth Speaker",
        category=ProductionCategory.AUDIO,
        description="A portable bluetooth speaker for entrance music. Barely audible.",
        cost=0,
        min_venue_tier=1,
        show_quality_bonus=-1,
    ),
    "audio_pa_basic": ProductionItem(
        id="audio_pa_basic",
        name="Basic PA System",
        category=ProductionCategory.AUDIO,
        description="Simple PA speakers and a microphone. Gets the job done.",
        cost=150,
        min_venue_tier=1,
        show_quality_bonus=1,
        fan_excitement_bonus=3,
    ),
    "audio_pa_pro": ProductionItem(
        id="audio_pa_pro",
        name="Professional PA",
        category=ProductionCategory.AUDIO,
        description="Quality speakers, mixing board, wireless mics, and proper entrance music playback.",
        cost=600,
        min_venue_tier=2,
        show_quality_bonus=3,
        fan_excitement_bonus=6,
        prestige_bonus=2,
    ),
    "audio_broadcast": ProductionItem(
        id="audio_broadcast",
        name="Broadcast Audio Suite",
        category=ProductionCategory.AUDIO,
        description="Full audio setup with commentary desk, ring mics, and professional mixing.",
        cost=2500,
        min_venue_tier=3,
        show_quality_bonus=6,
        fan_excitement_bonus=10,
        prestige_bonus=4,
    ),
    "audio_arena": ProductionItem(
        id="audio_arena",
        name="Arena Sound System",
        category=ProductionCategory.AUDIO,
        description="Concert-quality surround sound. Every theme song hits different.",
        cost=8000,
        min_venue_tier=4,
        show_quality_bonus=10,
        fan_excitement_bonus=15,
        prestige_bonus=6,
    ),
    "audio_stadium": ProductionItem(
        id="audio_stadium",
        name="Stadium Sound Experience",
        category=ProductionCategory.AUDIO,
        description="Massive stadium PA with subwoofers that shake the building. Entrances give you chills.",
        cost=20000,
        min_venue_tier=5,
        show_quality_bonus=14,
        fan_excitement_bonus=22,
        prestige_bonus=10,
    ),
}


# ==================== PRODUCTION LOADOUT ====================

@dataclass
class ShowProduction:
    """Complete production setup for a show"""
    ring_id: str = "wrestling_ring_basic"
    lighting_id: str = "lighting_none"
    camera_id: str = "camera_none"
    backstage_id: str = "backstage_none"
    pyro_id: str = "pyro_none"
    entrance_id: str = "entrance_curtain"
    audio_id: str = "audio_bluetooth"
    
    def get_ring(self) -> RingOption:
        return RING_OPTIONS.get(self.ring_id, RING_OPTIONS["wrestling_ring_basic"])
    
    def get_lighting(self) -> ProductionItem:
        return LIGHTING_OPTIONS.get(self.lighting_id, LIGHTING_OPTIONS["lighting_none"])
    
    def get_cameras(self) -> ProductionItem:
        return CAMERA_OPTIONS.get(self.camera_id, CAMERA_OPTIONS["camera_none"])
    
    def get_backstage(self) -> ProductionItem:
        return BACKSTAGE_OPTIONS.get(self.backstage_id, BACKSTAGE_OPTIONS["backstage_none"])
    
    def get_pyro(self) -> ProductionItem:
        return PYRO_OPTIONS.get(self.pyro_id, PYRO_OPTIONS["pyro_none"])
    
    def get_entrance(self) -> ProductionItem:
        return ENTRANCE_OPTIONS.get(self.entrance_id, ENTRANCE_OPTIONS["entrance_curtain"])
    
    def get_audio(self) -> ProductionItem:
        return AUDIO_OPTIONS.get(self.audio_id, AUDIO_OPTIONS["audio_bluetooth"])
    
    def get_total_cost(self) -> int:
        total = self.get_ring().cost
        total += self.get_lighting().cost
        total += self.get_cameras().cost
        total += self.get_backstage().cost
        total += self.get_pyro().cost
        total += self.get_entrance().cost
        total += self.get_audio().cost
        return total
    
    def get_total_quality_bonus(self) -> int:
        total = self.get_ring().match_quality_bonus
        total += self.get_lighting().show_quality_bonus
        total += self.get_cameras().show_quality_bonus
        total += self.get_backstage().show_quality_bonus
        total += self.get_pyro().show_quality_bonus
        total += self.get_entrance().show_quality_bonus
        total += self.get_audio().show_quality_bonus
        return total
    
    def get_total_fan_bonus(self) -> int:
        total = self.get_ring().fan_novelty_bonus
        total += self.get_lighting().fan_excitement_bonus
        total += self.get_cameras().fan_excitement_bonus
        total += self.get_backstage().fan_excitement_bonus
        total += self.get_pyro().fan_excitement_bonus
        total += self.get_entrance().fan_excitement_bonus
        total += self.get_audio().fan_excitement_bonus
        return total
    
    def get_total_prestige_bonus(self) -> int:
        total = 0
        total += self.get_lighting().prestige_bonus
        total += self.get_cameras().prestige_bonus
        total += self.get_backstage().prestige_bonus
        total += self.get_pyro().prestige_bonus
        total += self.get_entrance().prestige_bonus
        total += self.get_audio().prestige_bonus
        return total
    
    def get_injury_modifier(self) -> float:
        return self.get_ring().injury_risk_modifier
    
    def get_summary(self) -> Dict:
        return {
            "ring": self.get_ring().name,
            "lighting": self.get_lighting().name,
            "cameras": self.get_cameras().name,
            "backstage": self.get_backstage().name,
            "pyro": self.get_pyro().name,
            "entrance": self.get_entrance().name,
            "audio": self.get_audio().name,
            "total_cost": self.get_total_cost(),
            "quality_bonus": self.get_total_quality_bonus(),
            "fan_bonus": self.get_total_fan_bonus(),
            "prestige_bonus": self.get_total_prestige_bonus(),
            "injury_modifier": self.get_injury_modifier(),
        }
    
    def to_dict(self) -> dict:
        return {
            "ring_id": self.ring_id,
            "lighting_id": self.lighting_id,
            "camera_id": self.camera_id,
            "backstage_id": self.backstage_id,
            "pyro_id": self.pyro_id,
            "entrance_id": self.entrance_id,
            "audio_id": self.audio_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ShowProduction":
        return cls(
            ring_id=data.get("ring_id", "wrestling_ring_basic"),
            lighting_id=data.get("lighting_id", "lighting_none"),
            camera_id=data.get("camera_id", "camera_none"),
            backstage_id=data.get("backstage_id", "backstage_none"),
            pyro_id=data.get("pyro_id", "pyro_none"),
            entrance_id=data.get("entrance_id", "entrance_curtain"),
            audio_id=data.get("audio_id", "audio_bluetooth"),
        )


def get_available_options(category: str, venue_tier: int) -> list:
    """Get all options available for a venue tier"""
    option_maps = {
        "ring": RING_OPTIONS,
        "lighting": LIGHTING_OPTIONS,
        "cameras": CAMERA_OPTIONS,
        "backstage": BACKSTAGE_OPTIONS,
        "pyro": PYRO_OPTIONS,
        "entrance": ENTRANCE_OPTIONS,
        "audio": AUDIO_OPTIONS,
    }
    
    options = option_maps.get(category, {})
    available = []
    
    for opt_id, opt in options.items():
        if isinstance(opt, RingOption):
            min_tier = opt.min_venue_tier
        else:
            min_tier = opt.min_venue_tier
        
        available.append({
            "id": opt_id,
            "name": opt.name,
            "description": opt.description,
            "cost": opt.cost,
            "min_venue_tier": min_tier,
            "is_locked": venue_tier < min_tier,
            "quality_bonus": opt.match_quality_bonus if isinstance(opt, RingOption) else opt.show_quality_bonus,
            "fan_bonus": opt.fan_novelty_bonus if isinstance(opt, RingOption) else opt.fan_excitement_bonus,
            "prestige_bonus": 0 if isinstance(opt, RingOption) else opt.prestige_bonus,
        })
    
    return available