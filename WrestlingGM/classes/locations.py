"""
Location data for promotions
Continent → Country → Cities
"""

LOCATIONS = {
    "North America": {
        "United States": [
            "New York City",
            "Los Angeles",
            "Chicago",
            "Houston",
            "Philadelphia",
            "Atlanta",
            "Dallas",
            "Boston",
            "Miami",
            "Las Vegas",
            "Detroit",
            "Minneapolis",
            "Seattle",
            "Denver",
            "Phoenix",
        ],
        "Canada": [
            "Toronto",
            "Montreal",
            "Vancouver",
            "Calgary",
            "Edmonton",
            "Ottawa",
            "Winnipeg",
        ],
        "Mexico": [
            "Mexico City",
            "Guadalajara",
            "Monterrey",
            "Tijuana",
            "Puebla",
            "León",
        ],
    },
    "South America": {
        "Brazil": [
            "São Paulo",
            "Rio de Janeiro",
            "Brasília",
            "Salvador",
            "Curitiba",
        ],
        "Argentina": [
            "Buenos Aires",
            "Córdoba",
            "Rosario",
            "Mendoza",
        ],
        "Chile": [
            "Santiago",
            "Valparaíso",
            "Concepción",
        ],
        "Colombia": [
            "Bogotá",
            "Medellín",
            "Cali",
        ],
    },
    "Europe": {
        "United Kingdom": [
            "London",
            "Manchester",
            "Birmingham",
            "Liverpool",
            "Glasgow",
            "Leeds",
            "Bristol",
            "Blackpool",
        ],
        "Germany": [
            "Berlin",
            "Munich",
            "Hamburg",
            "Frankfurt",
            "Oberhausen",
            "Cologne",
        ],
        "France": [
            "Paris",
            "Lyon",
            "Marseille",
            "Toulouse",
        ],
        "Spain": [
            "Madrid",
            "Barcelona",
            "Valencia",
            "Seville",
        ],
        "Italy": [
            "Rome",
            "Milan",
            "Naples",
            "Turin",
        ],
        "Ireland": [
            "Dublin",
            "Belfast",
            "Cork",
        ],
    },
    "Austral-Asia": {
        "Japan": [
            "Tokyo",
            "Osaka",
            "Nagoya",
            "Yokohama",
            "Sapporo",
            "Fukuoka",
            "Hiroshima",
            "Kobe",
        ],
        "Australia": [
            "Sydney",
            "Melbourne",
            "Brisbane",
            "Perth",
            "Adelaide",
        ],
        "New Zealand": [
            "Auckland",
            "Wellington",
            "Christchurch",
        ],
        "South Korea": [
            "Seoul",
            "Busan",
            "Incheon",
        ],
        "China": [
            "Beijing",
            "Shanghai",
            "Hong Kong",
            "Shenzhen",
            "Guangzhou",
        ],
        "India": [
            "Mumbai",
            "Delhi",
            "Bangalore",
            "Chennai",
            "Kolkata",
        ],
        "Philippines": [
            "Manila",
            "Quezon City",
            "Cebu City",
        ],
    },
    "Africa": {
        "South Africa": [
            "Johannesburg",
            "Cape Town",
            "Durban",
            "Pretoria",
        ],
        "Nigeria": [
            "Lagos",
            "Abuja",
            "Port Harcourt",
        ],
        "Egypt": [
            "Cairo",
            "Alexandria",
            "Giza",
        ],
        "Kenya": [
            "Nairobi",
            "Mombasa",
        ],
        "Morocco": [
            "Casablanca",
            "Marrakech",
            "Rabat",
        ],
    },
}


# Currency by country
CURRENCIES = {
    # North America
    "United States": ("USD", "$"),
    "Canada": ("CAD", "C$"),
    "Mexico": ("MXN", "MX$"),
    
    # South America
    "Brazil": ("BRL", "R$"),
    "Argentina": ("ARS", "AR$"),
    "Chile": ("CLP", "CLP$"),
    "Colombia": ("COP", "CO$"),
    
    # Europe
    "United Kingdom": ("GBP", "£"),
    "Germany": ("EUR", "€"),
    "France": ("EUR", "€"),
    "Spain": ("EUR", "€"),
    "Italy": ("EUR", "€"),
    "Ireland": ("EUR", "€"),
    
    # Austral-Asia
    "Japan": ("JPY", "¥"),
    "Australia": ("AUD", "A$"),
    "New Zealand": ("NZD", "NZ$"),
    "South Korea": ("KRW", "₩"),
    "China": ("CNY", "¥"),
    "India": ("INR", "₹"),
    "Philippines": ("PHP", "₱"),
    
    # Africa
    "South Africa": ("ZAR", "R"),
    "Nigeria": ("NGN", "₦"),
    "Egypt": ("EGP", "E£"),
    "Kenya": ("KES", "KSh"),
    "Morocco": ("MAD", "MAD"),
}


# Regional bonuses/modifiers
REGION_MODIFIERS = {
    "North America": {
        "tv_opportunity": 1.3,
        "merchandise_modifier": 1.2,
        "talent_pool": 1.2,
        "operating_costs": 1.2,
        "description": "High media exposure, expensive to operate",
    },
    "South America": {
        "tv_opportunity": 0.9,
        "merchandise_modifier": 0.9,
        "talent_pool": 1.0,
        "operating_costs": 0.7,
        "description": "Growing market, lower costs, passionate fans",
    },
    "Europe": {
        "tv_opportunity": 1.1,
        "merchandise_modifier": 1.1,
        "talent_pool": 1.1,
        "operating_costs": 1.1,
        "description": "Balanced market with rich wrestling history",
    },
    "Austral-Asia": {
        "tv_opportunity": 1.2,
        "merchandise_modifier": 1.3,
        "talent_pool": 1.3,
        "operating_costs": 1.0,
        "description": "Strong wrestling culture, especially Japan",
    },
    "Africa": {
        "tv_opportunity": 0.7,
        "merchandise_modifier": 0.7,
        "talent_pool": 0.8,
        "operating_costs": 0.6,
        "description": "Emerging market, untapped potential, low costs",
    },
}


def get_continents() -> list:
    """Get list of all continents"""
    return list(LOCATIONS.keys())


def get_countries(continent: str) -> list:
    """Get list of countries in a continent"""
    return list(LOCATIONS.get(continent, {}).keys())


def get_cities(continent: str, country: str) -> list:
    """Get list of cities in a country"""
    return LOCATIONS.get(continent, {}).get(country, [])


def get_currency(country: str) -> tuple:
    """Get currency code and symbol for a country"""
    return CURRENCIES.get(country, ("USD", "$"))


def get_region_modifier(continent: str) -> dict:
    """Get regional modifiers for a continent"""
    return REGION_MODIFIERS.get(continent, {})