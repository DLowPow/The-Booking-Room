"""
Venue Data - Realistic venues with perks, restrictions, time limits, day modifiers
Organized by continent with proper capacity limits and revenue streams
"""

from classes.venue import (
    Venue, VenueTier, VenuePerk, VenueRestriction,
    VENUE_TIER_DEFAULTS, DEFAULT_DAY_MODIFIERS
)


def create_venue(
    id, name, city, tier, capacity, rental_cost, prestige,
    max_show_minutes=None, buffer_minutes=None,
    base_ticket_price=None, vip_ticket_price=0, vip_capacity_pct=0.0,
    perks=None, restrictions=None,
    alcohol_revenue_per_head=None, concession_revenue_per_head=None,
    best_days=None, worst_days=None, day_modifiers=None,
    description="", atmosphere="Standard", is_unlocked=True,
):
    """Helper to create venues with tier defaults"""
    defaults = VENUE_TIER_DEFAULTS.get(tier, {})

    venue = Venue(
        id=id, name=name, city=city, tier=tier,
        capacity=capacity, rental_cost=rental_cost, prestige=prestige,
        max_show_minutes=max_show_minutes or defaults.get("max_show_minutes", 120),
        buffer_minutes=buffer_minutes or defaults.get("buffer_minutes", 15),
        base_ticket_price=base_ticket_price or defaults.get("ticket_price_range", (10, 20))[0],
        vip_ticket_price=vip_ticket_price,
        vip_capacity_pct=vip_capacity_pct,
        alcohol_revenue_per_head=alcohol_revenue_per_head if alcohol_revenue_per_head is not None else defaults.get("alcohol_revenue_per_head", 0),
        concession_revenue_per_head=concession_revenue_per_head if concession_revenue_per_head is not None else defaults.get("concession_revenue_per_head", 5),
        perks=perks if perks is not None else defaults.get("default_perks", []),
        restrictions=restrictions if restrictions is not None else defaults.get("default_restrictions", []),
        best_days=best_days or ["Saturday", "Friday"],
        worst_days=worst_days or ["Monday", "Tuesday"],
        day_modifiers=day_modifiers or {},
        description=description, atmosphere=atmosphere,
        is_unlocked=is_unlocked,
    )
    return venue


# ==================== NORTH AMERICA ====================

NORTH_AMERICA_VENUES = [
    # TIER 1: BACKYARDS
    create_venue(
        id="na_backyard_1", name="Joey's Backyard Ring", city="Philadelphia, PA",
        tier=VenueTier.BACKYARD, capacity=40, rental_cost=50, prestige=2,
        max_show_minutes=90, base_ticket_price=5,
        perks=[VenuePerk.CHEAP_RENTAL, VenuePerk.OUTDOOR],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.SETUP_TIME_LIMITED],
        description="A backyard ring with folding chairs. The birthplace of legends... or lawsuits.",
        atmosphere="Chaotic",
    ),
    create_venue(
        id="na_backyard_2", name="Warehouse Lot", city="Detroit, MI",
        tier=VenueTier.BACKYARD, capacity=60, rental_cost=75, prestige=3,
        max_show_minutes=90, base_ticket_price=5,
        perks=[VenuePerk.CHEAP_RENTAL, VenuePerk.LATE_NIGHT],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.SETUP_TIME_LIMITED],
        description="An empty warehouse parking lot. Bring your own chairs.",
        atmosphere="Gritty",
    ),
    create_venue(
        id="na_backyard_3", name="The Barn", city="Nashville, TN",
        tier=VenueTier.BACKYARD, capacity=50, rental_cost=60, prestige=3,
        max_show_minutes=90, base_ticket_price=5,
        perks=[VenuePerk.CHEAP_RENTAL, VenuePerk.OUTDOOR, VenuePerk.PARKING_INCLUDED],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.SETUP_TIME_LIMITED],
        description="An old barn converted for wrestling. Hay bales for seating.",
        atmosphere="Rustic",
    ),

    # TIER 2: BARS AND CLUBS
    create_venue(
        id="na_bar_1", name="The Rusty Cage", city="Chicago, IL",
        tier=VenueTier.BAR_CLUB, capacity=80, rental_cost=200, prestige=8,
        max_show_minutes=120, base_ticket_price=10,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT, VenuePerk.CHEAP_RENTAL],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.NOISE_CURFEW_LATE, VenueRestriction.AGE_RESTRICTED],
        best_days=["Friday", "Saturday"], worst_days=["Monday", "Tuesday", "Sunday"],
        day_modifiers={
            "Friday": {"attendance": 1.20, "cost": 1.0, "label": "Happy Hour Crowd"},
            "Saturday": {"attendance": 1.30, "cost": 1.15, "label": "Peak Night"},
            "Sunday": {"attendance": 0.60, "cost": 0.75, "label": "Dead Night"},
        },
        alcohol_revenue_per_head=10,
        description="Dive bar with a ring in the back. Cheap drinks, loud crowd.",
        atmosphere="Rowdy",
    ),
    create_venue(
        id="na_bar_2", name="Midnight Lounge", city="Brooklyn, NY",
        tier=VenueTier.BAR_CLUB, capacity=120, rental_cost=350, prestige=12,
        max_show_minutes=120, base_ticket_price=12,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT, VenuePerk.SOUND_SYSTEM],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.NOISE_CURFEW_LATE, VenueRestriction.AGE_RESTRICTED, VenueRestriction.NO_TABLES_SPOTS],
        best_days=["Thursday", "Friday", "Saturday"],
        day_modifiers={
            "Thursday": {"attendance": 1.10, "cost": 0.90, "label": "Thirsty Thursday"},
            "Friday": {"attendance": 1.25, "cost": 1.10, "label": "Friday Night"},
            "Saturday": {"attendance": 1.30, "cost": 1.20, "label": "Saturday Night"},
        },
        alcohol_revenue_per_head=12,
        description="Trendy Brooklyn bar. Craft beer and suplexes.",
        atmosphere="Hip",
    ),
    create_venue(
        id="na_bar_3", name="Tombstone Saloon", city="Austin, TX",
        tier=VenueTier.BAR_CLUB, capacity=150, rental_cost=300, prestige=10,
        max_show_minutes=120, base_ticket_price=10,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT, VenuePerk.EARLY_OPEN, VenuePerk.PARKING_INCLUDED],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        best_days=["Friday", "Saturday"],
        day_modifiers={
            "Wednesday": {"attendance": 0.90, "cost": 0.70, "label": "Discount Night"},
        },
        alcohol_revenue_per_head=9,
        description="Western-themed saloon. Early open means cheap weekday bookings.",
        atmosphere="Wild West",
    ),
    create_venue(
        id="na_bar_4", name="The Pit", city="Los Angeles, CA",
        tier=VenueTier.BAR_CLUB, capacity=200, rental_cost=500, prestige=15,
        max_show_minutes=120, base_ticket_price=15,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT, VenuePerk.STREAMING_SETUP],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.NOISE_CURFEW_LATE, VenueRestriction.AGE_RESTRICTED],
        best_days=["Friday", "Saturday"],
        alcohol_revenue_per_head=15,
        description="Underground club. Influencers and wrestling fans collide.",
        atmosphere="Underground",
    ),

    # TIER 3: COMMUNITY CENTERS
    create_venue(
        id="na_community_1", name="Eastside Rec Center", city="Atlanta, GA",
        tier=VenueTier.COMMUNITY, capacity=200, rental_cost=400, prestige=15,
        max_show_minutes=150, base_ticket_price=12,
        perks=[VenuePerk.FAMILY_FRIENDLY, VenuePerk.PARKING_INCLUDED, VenuePerk.MERCH_TABLES],
        restrictions=[VenueRestriction.NO_BLOOD, VenueRestriction.NO_ALCOHOL, VenueRestriction.NOISE_CURFEW],
        best_days=["Saturday", "Sunday"],
        day_modifiers={
            "Saturday": {"attendance": 1.30, "cost": 1.10, "label": "Family Day"},
            "Sunday": {"attendance": 1.20, "cost": 1.00, "label": "Sunday Matinee"},
            "Wednesday": {"attendance": 0.70, "cost": 0.75, "label": "Quiet Midweek"},
        },
        description="Family-friendly rec center. No blood, no booze, no problem.",
        atmosphere="Family",
    ),
    create_venue(
        id="na_community_2", name="VFW Hall", city="Pittsburgh, PA",
        tier=VenueTier.COMMUNITY, capacity=300, rental_cost=500, prestige=18,
        max_show_minutes=150, base_ticket_price=12,
        perks=[VenuePerk.FAMILY_FRIENDLY, VenuePerk.PARKING_INCLUDED, VenuePerk.MERCH_TABLES, VenuePerk.CHEAP_RENTAL],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.NOISE_CURFEW, VenueRestriction.SHARED_SPACE],
        best_days=["Friday", "Saturday"],
        description="Veterans hall with a stage. Quick cleanup required — shared space.",
        atmosphere="Classic",
    ),
    create_venue(
        id="na_community_3", name="Civic Center Gym", city="Orlando, FL",
        tier=VenueTier.COMMUNITY, capacity=450, rental_cost=800, prestige=22,
        max_show_minutes=150, base_ticket_price=15,
        perks=[VenuePerk.FAMILY_FRIENDLY, VenuePerk.PARKING_INCLUDED, VenuePerk.MERCH_TABLES, VenuePerk.BACKSTAGE_LARGE],
        restrictions=[VenueRestriction.NO_BLOOD, VenueRestriction.NO_ALCOHOL, VenueRestriction.NOISE_CURFEW],
        best_days=["Saturday", "Sunday"],
        description="Full gymnasium with bleacher seating. Great for family shows.",
        atmosphere="Athletic",
    ),

    # TIER 4: THEATERS
    create_venue(
        id="na_theater_1", name="The Rialto Theater", city="New York, NY",
        tier=VenueTier.THEATER, capacity=800, rental_cost=2500, prestige=30,
        max_show_minutes=180, base_ticket_price=25,
        vip_ticket_price=50, vip_capacity_pct=0.10,
        perks=[VenuePerk.SOUND_SYSTEM, VenuePerk.PREMIUM_SEATING, VenuePerk.BACKSTAGE_LARGE, VenuePerk.HISTORIC],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.NO_TABLES_SPOTS],
        best_days=["Friday", "Saturday"],
        description="Historic NYC theater. Premium seating and incredible acoustics.",
        atmosphere="Prestigious",
    ),
    create_venue(
        id="na_theater_2", name="Hammerstein Ballroom", city="New York, NY",
        tier=VenueTier.THEATER, capacity=1500, rental_cost=4000, prestige=38,
        max_show_minutes=180, base_ticket_price=30,
        vip_ticket_price=65, vip_capacity_pct=0.12,
        perks=[VenuePerk.SOUND_SYSTEM, VenuePerk.PREMIUM_SEATING, VenuePerk.BACKSTAGE_LARGE, VenuePerk.TV_READY, VenuePerk.HISTORIC],
        restrictions=[],
        description="Legendary wrestling venue. ECW, ROH, and more made history here.",
        atmosphere="Legendary",
    ),
    create_venue(
        id="na_theater_3", name="The Wiltern", city="Los Angeles, CA",
        tier=VenueTier.THEATER, capacity=1850, rental_cost=4500, prestige=35,
        max_show_minutes=180, base_ticket_price=28,
        vip_ticket_price=55, vip_capacity_pct=0.10,
        perks=[VenuePerk.SOUND_SYSTEM, VenuePerk.PREMIUM_SEATING, VenuePerk.BACKSTAGE_LARGE, VenuePerk.STREAMING_SETUP],
        restrictions=[VenueRestriction.NO_PYRO],
        description="Art Deco theater in Koreatown. Beautiful backdrop for any show.",
        atmosphere="Elegant",
    ),

    # TIER 5: ARENAS
    create_venue(
        id="na_arena_1", name="The Fieldhouse", city="Indianapolis, IN",
        tier=VenueTier.ARENA, capacity=3500, rental_cost=8000, prestige=40,
        max_show_minutes=180, base_ticket_price=25,
        vip_ticket_price=60, vip_capacity_pct=0.08,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.CONCESSION_DEAL, VenuePerk.PARKING_INCLUDED],
        restrictions=[],
        description="Mid-size arena. Perfect for growing promotions.",
        atmosphere="Electric",
    ),
    create_venue(
        id="na_arena_2", name="2300 Arena", city="Philadelphia, PA",
        tier=VenueTier.ARENA, capacity=2300, rental_cost=6000, prestige=45,
        max_show_minutes=180, base_ticket_price=30,
        vip_ticket_price=75, vip_capacity_pct=0.10,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.HISTORIC],
        restrictions=[],
        description="The old ECW Arena. Wrestling history drips from every wall.",
        atmosphere="Hardcore Heritage",
    ),
    create_venue(
        id="na_arena_3", name="Civic Arena", city="Dallas, TX",
        tier=VenueTier.ARENA, capacity=6000, rental_cost=15000, prestige=50,
        max_show_minutes=180, base_ticket_price=30,
        vip_ticket_price=80, vip_capacity_pct=0.10,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.CONCESSION_DEAL],
        restrictions=[],
        description="Full production arena. Ready for TV tapings.",
        atmosphere="Professional",
    ),

    # TIER 6: LARGE ARENAS
    create_venue(
        id="na_large_1", name="Madison Square Garden", city="New York, NY",
        tier=VenueTier.LARGE_ARENA, capacity=20000, rental_cost=50000, prestige=75,
        max_show_minutes=210, base_ticket_price=45,
        vip_ticket_price=150, vip_capacity_pct=0.12,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP, VenuePerk.HISTORIC],
        restrictions=[],
        description="The World's Most Famous Arena. Enough said.",
        atmosphere="Legendary", is_unlocked=True,
    ),
    create_venue(
        id="na_large_2", name="United Center", city="Chicago, IL",
        tier=VenueTier.LARGE_ARENA, capacity=23500, rental_cost=55000, prestige=70,
        max_show_minutes=210, base_ticket_price=40,
        vip_ticket_price=130, vip_capacity_pct=0.10,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP],
        restrictions=[],
        description="Home of Bulls and Blackhawks. Massive production capability.",
        atmosphere="Grand",
    ),

    # TIER 7: STADIUMS
    create_venue(
        id="na_stadium_1", name="AT&T Stadium", city="Arlington, TX",
        tier=VenueTier.STADIUM, capacity=80000, rental_cost=200000, prestige=90,
        max_show_minutes=240, base_ticket_price=50,
        vip_ticket_price=200, vip_capacity_pct=0.08,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP, VenuePerk.CONCESSION_DEAL],
        restrictions=[],
        description="WrestleMania-level stadium. The biggest stage in wrestling.",
        atmosphere="Spectacular",
    ),
    create_venue(
        id="na_stadium_2", name="MetLife Stadium", city="East Rutherford, NJ",
        tier=VenueTier.STADIUM, capacity=82500, rental_cost=220000, prestige=92,
        max_show_minutes=240, base_ticket_price=55,
        vip_ticket_price=225, vip_capacity_pct=0.08,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP, VenuePerk.CONCESSION_DEAL],
        restrictions=[],
        description="The NY/NJ mega-stadium. Multiple WrestleManias held here.",
        atmosphere="Colossal",
    ),
]


# ==================== EUROPE ====================

EUROPE_VENUES = [
    create_venue(
        id="eu_backyard_1", name="The Car Park Ring", city="London, UK",
        tier=VenueTier.BACKYARD, capacity=50, rental_cost=40, prestige=2,
        base_ticket_price=5,
        perks=[VenuePerk.CHEAP_RENTAL], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.SETUP_TIME_LIMITED],
        description="A car park with a ring. Proper British wrestling.",
    ),
    create_venue(
        id="eu_bar_1", name="The Crown & Suplex", city="London, UK",
        tier=VenueTier.BAR_CLUB, capacity=100, rental_cost=250, prestige=10,
        base_ticket_price=10,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        alcohol_revenue_per_head=12,
        description="A traditional pub with a ring in the beer garden.",
    ),
    create_venue(
        id="eu_bar_2", name="Biergarten Brawl", city="Munich, Germany",
        tier=VenueTier.BAR_CLUB, capacity=180, rental_cost=300, prestige=12,
        base_ticket_price=12,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.EARLY_OPEN, VenuePerk.OUTDOOR], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        alcohol_revenue_per_head=15,
        description="Beer garden wrestling. Early open means cheap afternoon bookings.",
    ),
    create_venue(
        id="eu_community_1", name="Camden Assembly", city="London, UK",
        tier=VenueTier.COMMUNITY, capacity=350, rental_cost=600, prestige=20,
        base_ticket_price=15,
        perks=[VenuePerk.SOUND_SYSTEM, VenuePerk.MERCH_TABLES], restrictions=[VenueRestriction.NOISE_CURFEW],
        description="Iconic Camden venue. Music meets wrestling.",
    ),
    create_venue(
        id="eu_theater_1", name="York Hall", city="London, UK",
        tier=VenueTier.THEATER, capacity=1200, rental_cost=3000, prestige=35,
        base_ticket_price=22,
        vip_ticket_price=50, vip_capacity_pct=0.08,
        perks=[VenuePerk.SOUND_SYSTEM, VenuePerk.HISTORIC, VenuePerk.BACKSTAGE_LARGE],
        restrictions=[VenueRestriction.NO_PYRO],
        description="Historic boxing and wrestling venue in Bethnal Green.",
    ),
    create_venue(
        id="eu_arena_1", name="Wembley Arena", city="London, UK",
        tier=VenueTier.ARENA, capacity=12500, rental_cost=25000, prestige=55,
        base_ticket_price=35,
        vip_ticket_price=90, vip_capacity_pct=0.10,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE],
        restrictions=[],
        description="Major London arena. AEW and WWE have packed this place.",
    ),
    create_venue(
        id="eu_stadium_1", name="Wembley Stadium", city="London, UK",
        tier=VenueTier.STADIUM, capacity=90000, rental_cost=250000, prestige=95,
        base_ticket_price=50,
        vip_ticket_price=200, vip_capacity_pct=0.08,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP, VenuePerk.CONCESSION_DEAL],
        restrictions=[],
        description="The cathedral of sport. AEW All In made history here.",
    ),
]


# ==================== ASIA ====================

ASIA_VENUES = [
    create_venue(
        id="as_backyard_1", name="Dojo Floor", city="Tokyo, Japan",
        tier=VenueTier.BACKYARD, capacity=30, rental_cost=60, prestige=5,
        base_ticket_price=8,
        perks=[VenuePerk.CHEAP_RENTAL], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.SETUP_TIME_LIMITED],
        description="A small dojo with mats. Train here, wrestle here.",
    ),
    create_venue(
        id="as_bar_1", name="Shinjuku Fight Club", city="Tokyo, Japan",
        tier=VenueTier.BAR_CLUB, capacity=100, rental_cost=300, prestige=12,
        base_ticket_price=15,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        description="Basement bar in Shinjuku. Intimate and intense.",
    ),
    create_venue(
        id="as_community_1", name="Korakuen Hall", city="Tokyo, Japan",
        tier=VenueTier.COMMUNITY, capacity=1800, rental_cost=2000, prestige=40,
        base_ticket_price=25,
        perks=[VenuePerk.SOUND_SYSTEM, VenuePerk.MERCH_TABLES, VenuePerk.HISTORIC, VenuePerk.BACKSTAGE_LARGE],
        restrictions=[VenueRestriction.NO_PYRO],
        description="The spiritual home of Japanese wrestling. Every major promotion has wrestled here.",
        atmosphere="Sacred",
    ),
    create_venue(
        id="as_arena_1", name="Ryogoku Sumo Hall", city="Tokyo, Japan",
        tier=VenueTier.ARENA, capacity=11000, rental_cost=20000, prestige=60,
        base_ticket_price=35,
        vip_ticket_price=100, vip_capacity_pct=0.10,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.HISTORIC],
        restrictions=[],
        description="Sumo and wrestling. NJPW's home for major events.",
    ),
    create_venue(
        id="as_stadium_1", name="Tokyo Dome", city="Tokyo, Japan",
        tier=VenueTier.STADIUM, capacity=55000, rental_cost=180000, prestige=88,
        base_ticket_price=45,
        vip_ticket_price=175, vip_capacity_pct=0.08,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.VIP_LOUNGE, VenuePerk.PREMIUM_SEATING, VenuePerk.STREAMING_SETUP],
        restrictions=[],
        description="Wrestle Kingdom. The Tokyo Dome. 5 stars guaranteed (according to Dave).",
    ),
]


# ==================== SOUTH AMERICA ====================

SOUTH_AMERICA_VENUES = [
    create_venue(
        id="sa_backyard_1", name="La Cancha", city="Mexico City, Mexico",
        tier=VenueTier.BACKYARD, capacity=45, rental_cost=30, prestige=3,
        base_ticket_price=5,
        perks=[VenuePerk.CHEAP_RENTAL, VenuePerk.OUTDOOR], restrictions=[VenueRestriction.NO_PYRO],
        description="An outdoor court ring. Lucha starts here.",
    ),
    create_venue(
        id="sa_bar_1", name="Cantina El Luchador", city="Mexico City, Mexico",
        tier=VenueTier.BAR_CLUB, capacity=120, rental_cost=200, prestige=10,
        base_ticket_price=8,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT, VenuePerk.CHEAP_RENTAL],
        restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        alcohol_revenue_per_head=8,
        description="Lucha libre and tequila. What more do you need?",
    ),
    create_venue(
        id="sa_community_1", name="Arena Coliseo", city="Mexico City, Mexico",
        tier=VenueTier.COMMUNITY, capacity=4000, rental_cost=1500, prestige=35,
        base_ticket_price=12,
        perks=[VenuePerk.MERCH_TABLES, VenuePerk.HISTORIC, VenuePerk.BACKSTAGE_LARGE],
        restrictions=[VenueRestriction.NO_PYRO],
        description="Historic lucha libre arena. CMLL territory since 1943.",
    ),
    create_venue(
        id="sa_arena_1", name="Arena Mexico", city="Mexico City, Mexico",
        tier=VenueTier.ARENA, capacity=16500, rental_cost=18000, prestige=55,
        base_ticket_price=20,
        vip_ticket_price=60, vip_capacity_pct=0.08,
        perks=[VenuePerk.PYRO_ALLOWED, VenuePerk.TV_READY, VenuePerk.BACKSTAGE_LARGE, VenuePerk.HISTORIC],
        restrictions=[],
        description="The Cathedral of Lucha Libre. The most important wrestling venue in Mexico.",
    ),
]


# ==================== OCEANIA ====================

OCEANIA_VENUES = [
    create_venue(
        id="oc_backyard_1", name="The Outback Ring", city="Melbourne, Australia",
        tier=VenueTier.BACKYARD, capacity=40, rental_cost=50, prestige=2,
        base_ticket_price=8,
        perks=[VenuePerk.CHEAP_RENTAL, VenuePerk.OUTDOOR], restrictions=[VenueRestriction.NO_PYRO],
        description="A ring in someone's backyard. Aussie wrestling starts here.",
    ),
    create_venue(
        id="oc_bar_1", name="The Bottleshop Brawl", city="Sydney, Australia",
        tier=VenueTier.BAR_CLUB, capacity=100, rental_cost=250, prestige=10,
        base_ticket_price=12,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.LATE_NIGHT], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        alcohol_revenue_per_head=12,
        description="Pub wrestling down under. Cold beers and hot action.",
    ),
    create_venue(
        id="oc_community_1", name="Melbourne Town Hall", city="Melbourne, Australia",
        tier=VenueTier.COMMUNITY, capacity=500, rental_cost=800, prestige=20,
        base_ticket_price=15,
        perks=[VenuePerk.FAMILY_FRIENDLY, VenuePerk.HISTORIC], restrictions=[VenueRestriction.NO_BLOOD, VenueRestriction.NOISE_CURFEW],
        description="Heritage-listed town hall. Family-friendly shows only.",
    ),
]


# ==================== AFRICA ====================

AFRICA_VENUES = [
    create_venue(
        id="af_backyard_1", name="The Sandlot", city="Lagos, Nigeria",
        tier=VenueTier.BACKYARD, capacity=60, rental_cost=30, prestige=2,
        base_ticket_price=5,
        perks=[VenuePerk.CHEAP_RENTAL, VenuePerk.OUTDOOR], restrictions=[VenueRestriction.NO_PYRO],
        description="Open-air wrestling on sandy ground. Pure passion.",
    ),
    create_venue(
        id="af_bar_1", name="The Shebeen Ring", city="Johannesburg, South Africa",
        tier=VenueTier.BAR_CLUB, capacity=80, rental_cost=150, prestige=8,
        base_ticket_price=8,
        perks=[VenuePerk.ALCOHOL_SALES, VenuePerk.CHEAP_RENTAL], restrictions=[VenueRestriction.NO_PYRO, VenueRestriction.AGE_RESTRICTED],
        description="Township bar with wrestling. Community spirit is everything.",
    ),
    create_venue(
        id="af_community_1", name="Cape Town City Hall", city="Cape Town, South Africa",
        tier=VenueTier.COMMUNITY, capacity=300, rental_cost=500, prestige=18,
        base_ticket_price=12,
        perks=[VenuePerk.FAMILY_FRIENDLY, VenuePerk.HISTORIC], restrictions=[VenueRestriction.NO_BLOOD, VenueRestriction.NOISE_CURFEW],
        description="Historic city hall. Great acoustics for crowd noise.",
    ),
]


# ==================== VENUE LOOKUP ====================

ALL_VENUES = {
    "North America": NORTH_AMERICA_VENUES,
    "Europe": EUROPE_VENUES,
    "Asia": ASIA_VENUES,
    "South America": SOUTH_AMERICA_VENUES,
    "Oceania": OCEANIA_VENUES,
    "Africa": AFRICA_VENUES,
}


def get_venues_by_continent(continent: str):
    return ALL_VENUES.get(continent, NORTH_AMERICA_VENUES)


def get_all_venues():
    all_v = []
    for venues in ALL_VENUES.values():
        all_v.extend(venues)
    return all_v


def get_venue_by_id(venue_id: str):
    for venue in get_all_venues():
        if venue.id == venue_id:
            return venue
    return None
