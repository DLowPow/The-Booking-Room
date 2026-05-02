"""
Production System - Show logistics and production elements
13 categories covering every aspect of running a wrestling show
Each option has cost, quality bonus, fan bonus, and tier requirement
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==================== RING OPTIONS ====================

RING_OPTIONS = {
    "ring_none": {"name": "No Ring", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "Wrestling on the ground. Dangerous."},
    "ring_basic": {"name": "Basic Ring", "cost": 200, "quality": 2, "fans": 0, "tier": 1, "description": "Second-hand ring with worn ropes."},
    "ring_standard": {"name": "Standard Ring", "cost": 500, "quality": 5, "fans": 5, "tier": 2, "description": "Solid ring with proper turnbuckles."},
    "ring_professional": {"name": "Professional Ring", "cost": 1500, "quality": 10, "fans": 10, "tier": 3, "description": "TV-quality ring with padded corners."},
    "ring_premium": {"name": "Premium Ring", "cost": 3000, "quality": 15, "fans": 20, "tier": 4, "description": "Custom branded ring with LED apron."},
    "ring_wwe_grade": {"name": "WWE-Grade Ring", "cost": 8000, "quality": 20, "fans": 30, "tier": 5, "description": "Top-of-the-line with hydraulic setup."},
}

# ==================== LIGHTING OPTIONS ====================

LIGHTING_OPTIONS = {
    "lighting_none": {"name": "No Lighting", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "Whatever the venue has."},
    "lighting_basic": {"name": "Basic Spots", "cost": 150, "quality": 2, "fans": 0, "tier": 1, "description": "A few spotlights on the ring."},
    "lighting_standard": {"name": "Standard Rig", "cost": 600, "quality": 5, "fans": 5, "tier": 2, "description": "Full ring lighting with color gels."},
    "lighting_professional": {"name": "Pro Lighting", "cost": 2000, "quality": 10, "fans": 15, "tier": 3, "description": "Moving heads, gobos, and entrance lighting."},
    "lighting_concert": {"name": "Concert Grade", "cost": 5000, "quality": 15, "fans": 25, "tier": 4, "description": "Full concert-style rig with programmable sequences."},
    "lighting_stadium": {"name": "Stadium Production", "cost": 15000, "quality": 20, "fans": 40, "tier": 5, "description": "Arena-filling light show with follow spots."},
}

# ==================== CAMERA OPTIONS ====================

CAMERA_OPTIONS = {
    "camera_none": {"name": "No Cameras", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "No recording at all."},
    "camera_phone": {"name": "Phone Camera", "cost": 50, "quality": 1, "fans": 5, "tier": 1, "description": "Someone films on their phone for YouTube."},
    "camera_basic": {"name": "Single Camera", "cost": 300, "quality": 3, "fans": 10, "tier": 1, "description": "One fixed camera on a tripod."},
    "camera_multi": {"name": "Multi-Camera", "cost": 1200, "quality": 8, "fans": 20, "tier": 2, "description": "3 cameras with basic switching."},
    "camera_broadcast": {"name": "Broadcast Setup", "cost": 3500, "quality": 12, "fans": 30, "tier": 3, "description": "TV-quality multi-cam with replay capability."},
    "camera_tv": {"name": "Full TV Production", "cost": 8000, "quality": 18, "fans": 50, "tier": 4, "description": "Production truck, crane cam, and jib."},
    "camera_cinema": {"name": "Cinematic Production", "cost": 20000, "quality": 25, "fans": 75, "tier": 5, "description": "Film-quality cameras, steadicams, and drones."},
}

# ==================== AUDIO OPTIONS ====================

AUDIO_OPTIONS = {
    "audio_none": {"name": "No Audio", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "Just crowd noise."},
    "audio_bluetooth": {"name": "Bluetooth Speaker", "cost": 50, "quality": 1, "fans": 0, "tier": 1, "description": "A portable speaker for entrance music."},
    "audio_pa": {"name": "PA System", "cost": 400, "quality": 4, "fans": 5, "tier": 2, "description": "Venue PA with basic mixing."},
    "audio_professional": {"name": "Pro Sound", "cost": 1500, "quality": 8, "fans": 15, "tier": 3, "description": "Full PA stack with subs and monitors."},
    "audio_concert": {"name": "Concert Audio", "cost": 4000, "quality": 12, "fans": 25, "tier": 4, "description": "Line array system with in-ear monitors."},
    "audio_immersive": {"name": "Immersive Sound", "cost": 12000, "quality": 18, "fans": 40, "tier": 5, "description": "Surround sound, crowd mics, and broadcast mix."},
}

# ==================== ENTRANCE OPTIONS ====================

ENTRANCE_OPTIONS = {
    "entrance_curtain": {"name": "Curtain", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "A simple curtain to walk through."},
    "entrance_basic": {"name": "Basic Ramp", "cost": 200, "quality": 2, "fans": 5, "tier": 1, "description": "Short ramp with a backdrop."},
    "entrance_stage": {"name": "Stage Setup", "cost": 800, "quality": 5, "fans": 10, "tier": 2, "description": "Raised stage with branded backdrop."},
    "entrance_titantron": {"name": "Titantron", "cost": 3000, "quality": 10, "fans": 20, "tier": 3, "description": "Video screen with entrance videos."},
    "entrance_full": {"name": "Full Stage", "cost": 8000, "quality": 15, "fans": 35, "tier": 4, "description": "LED stage, ramp, and interactive elements."},
    "entrance_spectacular": {"name": "Spectacular Stage", "cost": 25000, "quality": 22, "fans": 60, "tier": 5, "description": "WrestleMania-level stage with moving parts."},
}

# ==================== BACKSTAGE OPTIONS ====================

BACKSTAGE_OPTIONS = {
    "backstage_none": {"name": "No Backstage", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "Wrestlers change in their cars."},
    "backstage_basic": {"name": "Basic Area", "cost": 100, "quality": 1, "fans": 0, "tier": 1, "description": "A room with chairs and a mirror."},
    "backstage_standard": {"name": "Standard Backstage", "cost": 500, "quality": 4, "fans": 0, "tier": 2, "description": "Separate locker rooms and a gorilla position."},
    "backstage_professional": {"name": "Pro Backstage", "cost": 2000, "quality": 8, "fans": 5, "tier": 3, "description": "Interview area, catering, and private rooms."},
    "backstage_premium": {"name": "Premium Backstage", "cost": 5000, "quality": 12, "fans": 10, "tier": 4, "description": "Full backstage set with cameras and monitors."},
}

# ==================== PYRO OPTIONS ====================

PYRO_OPTIONS = {
    "pyro_none": {"name": "No Pyro", "cost": 0, "quality": 0, "fans": 0, "tier": 1, "description": "No pyrotechnics."},
    "pyro_sparklers": {"name": "Sparklers", "cost": 200, "quality": 2, "fans": 10, "tier": 2, "description": "Basic cold spark fountains."},
    "pyro_basic": {"name": "Basic Pyro", "cost": 800, "quality": 5, "fans": 20, "tier": 3, "description": "Flame jets and gerbs."},
    "pyro_professional": {"name": "Pro Pyro", "cost": 3000, "quality": 10, "fans": 35, "tier": 4, "description": "Full pyro package with aerial effects."},
    "pyro_spectacular": {"name": "Spectacular Pyro", "cost": 10000, "quality": 15, "fans": 60, "tier": 5, "description": "Stadium-level pyro with firework finale."},
}

# ==================== COMMENTARY & BROADCAST ====================

COMMENTARY_OPTIONS = {
    "commentary_none": {"name": "No Commentary", "cost": 0, "quality": 0, "fans": 0, "tier": 1,
        "description": "Just the raw sounds of the ring.",
        "storyline_bonus": 0, "tv_rating_bonus": 0},
    "commentary_lone": {"name": "Lone Announcer", "cost": 150, "quality": 2, "fans": 5, "tier": 1,
        "description": "One guy with a mic at a folding table.",
        "storyline_bonus": 5, "tv_rating_bonus": 0},
    "commentary_standard": {"name": "Standard 2-Man Desk", "cost": 600, "quality": 6, "fans": 10, "tier": 2,
        "description": "Play-by-play and color with basic headsets.",
        "storyline_bonus": 10, "tv_rating_bonus": 5},
    "commentary_professional": {"name": "Professional Broadcast Team", "cost": 2500, "quality": 12, "fans": 20, "tier": 3,
        "description": "3-man booth, dedicated audio mixing, backstage interviewer.",
        "storyline_bonus": 15, "tv_rating_bonus": 10},
    "commentary_international": {"name": "International Broadcast", "cost": 8000, "quality": 18, "fans": 40, "tier": 4,
        "description": "Multiple commentary desks for different languages.",
        "storyline_bonus": 15, "tv_rating_bonus": 20, "international_fan_bonus": 25},
    "commentary_hub": {"name": "State-of-the-Art Broadcast Hub", "cost": 25000, "quality": 25, "fans": 75, "tier": 5,
        "description": "Pre-show panel, AR graphics, drone flyovers, stat overlays.",
        "storyline_bonus": 20, "tv_rating_bonus": 30, "international_fan_bonus": 50},
}

# ==================== MEDICAL & SAFETY ====================

MEDICAL_OPTIONS = {
    "medical_none": {"name": "First Aid Kit", "cost": 0, "quality": 0, "fans": 0, "tier": 1,
        "description": "Rub some dirt on it. Injuries get worse.",
        "injury_reduction": 0, "recovery_bonus": 0, "morale_bonus": 0},
    "medical_trainee": {"name": "Trainee Medic", "cost": 100, "quality": 1, "fans": 0, "tier": 1,
        "description": "Local EMT volunteer. Better than nothing.",
        "injury_reduction": 5, "recovery_bonus": 0, "morale_bonus": 2},
    "medical_paramedic": {"name": "On-Site Paramedics", "cost": 800, "quality": 3, "fans": 0, "tier": 2,
        "description": "Ambulance on standby. Reduces severe injury risk.",
        "injury_reduction": 15, "recovery_bonus": 5, "morale_bonus": 5},
    "medical_physician": {"name": "Professional Ringside Physician", "cost": 3000, "quality": 6, "fans": 0, "tier": 3,
        "description": "Dedicated doctor, can stop matches and treat cuts.",
        "injury_reduction": 30, "recovery_bonus": 10, "morale_bonus": 10},
    "medical_team": {"name": "Pro Medical & Physio Team", "cost": 8000, "quality": 10, "fans": 5, "tier": 4,
        "description": "Ice baths, taping, chiropractors backstage.",
        "injury_reduction": 50, "recovery_bonus": 20, "morale_bonus": 15},
    "medical_trauma": {"name": "Mobile Trauma Center", "cost": 20000, "quality": 15, "fans": 10, "tier": 5,
        "description": "Hospital-grade mobile unit. Near-zero catastrophic risk.",
        "injury_reduction": 80, "recovery_bonus": 35, "morale_bonus": 25},
}

# ==================== RINGSIDE & BARRICADES ====================

BARRICADE_OPTIONS = {
    "barricade_none": {"name": "No Barricades", "cost": 0, "quality": 0, "fans": 10, "tier": 1,
        "description": "Fans right against the ring. Exciting but risky.",
        "fan_incident_risk": 30, "hardcore_bonus": 5},
    "barricade_guardrails": {"name": "Metal Guardrails", "cost": 200, "quality": 2, "fans": 5, "tier": 1,
        "description": "Standard indy guardrails. Unforgiving on impact.",
        "fan_incident_risk": 15, "hardcore_bonus": 3},
    "barricade_padded": {"name": "Padded Barricades", "cost": 800, "quality": 5, "fans": 5, "tier": 2,
        "description": "Standard TV wrestling barricades. Safer for brawls.",
        "fan_incident_risk": 5, "hardcore_bonus": 0},
    "barricade_led": {"name": "Premium LED Barricades", "cost": 3500, "quality": 10, "fans": 20, "tier": 3,
        "description": "LED screens on barricades and ring apron for ads.",
        "fan_incident_risk": 3, "hardcore_bonus": 0},
    "barricade_cage": {"name": "Reinforced Cage Logistics", "cost": 10000, "quality": 15, "fans": 30, "tier": 4,
        "description": "Rigging to suspend massive cage structures safely.",
        "fan_incident_risk": 0, "hardcore_bonus": 10, "cage_match_bonus": 15},
}

# ==================== SECURITY & CROWD CONTROL ====================

SECURITY_OPTIONS = {
    "security_none": {"name": "The Locker Room", "cost": 0, "quality": 0, "fans": 0, "tier": 1,
        "description": "Wrestlers not on card act as security. Drains their stamina.",
        "prestige_bonus": 0, "incident_prevention": 0, "stamina_drain": 5},
    "security_bouncers": {"name": "Venue Bouncers", "cost": 300, "quality": 1, "fans": 0, "tier": 1,
        "description": "Local tough guys. May cause issues with rowdy fans.",
        "prestige_bonus": 2, "incident_prevention": 10, "stamina_drain": 0},
    "security_professional": {"name": "Professional Event Security", "cost": 1200, "quality": 4, "fans": 5, "tier": 2,
        "description": "Uniformed guards keeping order during walk-and-brawls.",
        "prestige_bonus": 5, "incident_prevention": 30, "stamina_drain": 0},
    "security_vip": {"name": "VIP Protection & Escorts", "cost": 4000, "quality": 8, "fans": 10, "tier": 3,
        "description": "Personal security for top stars. Boosts prestige and heel heat.",
        "prestige_bonus": 10, "incident_prevention": 50, "heel_heat_bonus": 10, "stamina_drain": 0},
    "security_elite": {"name": "Elite Crowd Management", "cost": 10000, "quality": 12, "fans": 15, "tier": 4,
        "description": "Secret Service-level. Zero chance of fan incidents.",
        "prestige_bonus": 15, "incident_prevention": 100, "stamina_drain": 0},
}

# ==================== WEAPON & PROP STASH ====================

WEAPON_OPTIONS = {
    "weapon_none": {"name": "No Weapons", "cost": 0, "quality": 0, "fans": 0, "tier": 1,
        "description": "Clean wrestling only.",
        "hardcore_bonus": 0, "injury_risk_mod": 0},
    "weapon_scavenged": {"name": "Scavenged Junk", "cost": 50, "quality": 1, "fans": 5, "tier": 1,
        "description": "Brooms, trash cans, baking sheets from out back.",
        "hardcore_bonus": 3, "injury_risk_mod": 5},
    "weapon_standard": {"name": "Standard Hardware", "cost": 400, "quality": 4, "fans": 10, "tier": 2,
        "description": "Fresh folding chairs, kendo sticks, wooden tables.",
        "hardcore_bonus": 8, "injury_risk_mod": 3},
    "weapon_custom": {"name": "Custom Gimmick Props", "cost": 1500, "quality": 8, "fans": 20, "tier": 3,
        "description": "Thumbtacks, barbed wire bats, branded guitars, reinforced ladders.",
        "hardcore_bonus": 15, "injury_risk_mod": 8},
    "weapon_breakaway": {"name": "Breakaway Stunt Props", "cost": 5000, "quality": 14, "fans": 30, "tier": 4,
        "description": "Hollywood-grade breakaway tables and pre-cut glass. Max ratings, low injury.",
        "hardcore_bonus": 20, "injury_risk_mod": -10},
}

# ==================== SPECIAL EFFECTS (NON-PYRO) ====================

SPECIAL_FX_OPTIONS = {
    "fx_none": {"name": "No Special Effects", "cost": 0, "quality": 0, "fans": 0, "tier": 1,
        "description": "No special effects.",
        "novelty_bonus": 0},
    "fx_confetti": {"name": "Confetti Cannons", "cost": 300, "quality": 2, "fans": 10, "tier": 1,
        "description": "Cheap pop for championship victories.",
        "novelty_bonus": 3},
    "fx_snow": {"name": "Snow / Bubble Machines", "cost": 800, "quality": 4, "fans": 15, "tier": 2,
        "description": "Atmospheric effects for specific entrances.",
        "novelty_bonus": 5},
    "fx_laser": {"name": "Laser Light Show", "cost": 3000, "quality": 8, "fans": 25, "tier": 3,
        "description": "Immersive lighting without fire hazards.",
        "novelty_bonus": 10},
    "fx_drone": {"name": "Drone Light Show", "cost": 12000, "quality": 15, "fans": 50, "tier": 4,
        "description": "Hundreds of drones forming your logo in the sky.",
        "novelty_bonus": 20},
    "fx_holographic": {"name": "Holographic / AR Entrances", "cost": 25000, "quality": 22, "fans": 80, "tier": 5,
        "description": "Virtual 3D models projected for the broadcast audience.",
        "novelty_bonus": 30},
}


# ==================== ALL OPTIONS REGISTRY ====================

ALL_PRODUCTION_OPTIONS = {
    "ring": RING_OPTIONS,
    "lighting": LIGHTING_OPTIONS,
    "cameras": CAMERA_OPTIONS,
    "audio": AUDIO_OPTIONS,
    "entrance": ENTRANCE_OPTIONS,
    "backstage": BACKSTAGE_OPTIONS,
    "pyro": PYRO_OPTIONS,
    "commentary": COMMENTARY_OPTIONS,
    "medical": MEDICAL_OPTIONS,
    "barricades": BARRICADE_OPTIONS,
    "security": SECURITY_OPTIONS,
    "weapons": WEAPON_OPTIONS,
    "special_fx": SPECIAL_FX_OPTIONS,
}

CATEGORY_LABELS = {
    "ring": "🥊 Ring Setup",
    "lighting": "💡 Lighting",
    "cameras": "📹 Cameras",
    "audio": "🔊 Audio",
    "entrance": "🚪 Entrance",
    "backstage": "🏠 Backstage",
    "pyro": "🔥 Pyrotechnics",
    "commentary": "🎙️ Commentary & Broadcast",
    "medical": "🏥 Medical & Safety",
    "barricades": "🛡️ Ringside & Barricades",
    "security": "🔒 Security & Crowd Control",
    "weapons": "⚔️ Weapon & Prop Stash",
    "special_fx": "✨ Special Effects",
}


def get_available_options(category: str, venue_tier: int) -> List[Dict]:
    """Get options available for a category at a given venue tier"""
    options = ALL_PRODUCTION_OPTIONS.get(category, {})
    available = []
    for opt_id, opt_data in options.items():
        if opt_data.get("tier", 1) <= venue_tier:
            available.append({
                "id": opt_id,
                "name": opt_data["name"],
                "cost": opt_data["cost"],
                "quality": opt_data.get("quality", 0),
                "fans": opt_data.get("fans", 0),
                "tier": opt_data.get("tier", 1),
                "description": opt_data.get("description", ""),
            })
    return available

<!-- Dynamic Production Categories -->
{% for cat_key, cat_label in category_labels.items() %}
{% if cat_key in all_options and all_options[cat_key] %}
<div class="app-section">
<div class="section-title">{{ cat_label }}</div>
<div class="prod-options">
{% set current_id = production.to_dict().get(cat_key ~ '_id', '') %}
{% for opt in all_options[cat_key] %}
<label class="prod-option {% if current_id == opt.id %}selected{% endif %}">
<input type="radio" name="{{ cat_key }}" value="{{ opt.id }}" {% if current_id == opt.id %}checked{% endif %}>
<div class="prod-option-info">
<span class="prod-option-name">{{ opt.name }}</span>
<span class="prod-option-desc">{{ opt.description }}</span>
</div>
<span class="prod-option-cost">${{ opt.cost | int }}</span>
</label>
{% endfor %}
</div>
</div>
{% endif %}
{% endfor %}
