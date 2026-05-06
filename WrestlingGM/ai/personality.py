"""
AI Personality System - 4 Director Archetypes
Each personality has unique traits, voice patterns, decision weights,
mood responses, and booking philosophy that affects every AI output.

The Showman (Russo-style): Crash TV, swerves, shock value
The Mastermind (Bischoff-style): Big money, star power, business
The Mad Scientist (Heyman-style): Extreme, cult of personality, blood feuds
The Traditionalist (Default): Logical booking, slow burns, kayfabe respect
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ==================== PERSONALITY TYPES ====================

class PersonalityType(Enum):
    SHOWMAN = "The Showman"
    MASTERMIND = "The Mastermind"
    MAD_SCIENTIST = "The Mad Scientist"
    TRADITIONALIST = "The Traditionalist"


class MoodState(Enum):
    ECSTATIC = "Ecstatic"
    HAPPY = "Happy"
    NEUTRAL = "Neutral"
    FRUSTRATED = "Frustrated"
    FURIOUS = "Furious"
    SCHEMING = "Scheming"
    DESPERATE = "Desperate"
    BORED = "Bored"


class CreativeControlLevel(Enum):
    OFF = "Off"
    LIGHT = "Light"
    HEAVY = "Heavy"
    RUSSO_MODE = "Russo Mode"


# ==================== PERSONALITY TRAITS ====================

@dataclass
class PersonalityTraits:
    """Core traits that define how the AI behaves"""
    chaos_factor: float = 0.5          # 0-1: How likely to create unexpected events
    star_focus: float = 0.5            # 0-1: How much they push top stars vs roster depth
    storyline_complexity: float = 0.5  # 0-1: Simple feuds vs elaborate multi-layer plots
    violence_preference: float = 0.5   # 0-1: Clean matches vs hardcore/blood
    swerve_frequency: float = 0.5      # 0-1: How often shocking twists happen
    respect_for_kayfabe: float = 0.5   # 0-1: Protecting the business vs breaking 4th wall
    business_savvy: float = 0.5        # 0-1: Money-driven decisions vs artistic decisions
    patience: float = 0.5             # 0-1: Quick payoffs vs slow burns
    ego: float = 0.5                  # 0-1: How much the AI inserts itself into storylines
    risk_tolerance: float = 0.5       # 0-1: Safe booking vs high-risk decisions
    loyalty_to_favorites: float = 0.5 # 0-1: How much they push their chosen ones
    comedy_tolerance: float = 0.5     # 0-1: Serious product vs entertainment/humor


# ==================== VOICE TEMPLATES ====================

@dataclass
class VoiceProfile:
    """Defines how this personality speaks across all channels"""
    greeting_style: List[str] = field(default_factory=list)
    excitement_phrases: List[str] = field(default_factory=list)
    anger_phrases: List[str] = field(default_factory=list)
    praise_phrases: List[str] = field(default_factory=list)
    criticism_phrases: List[str] = field(default_factory=list)
    booking_suggestions: List[str] = field(default_factory=list)
    match_commentary_openings: List[str] = field(default_factory=list)
    match_commentary_big_spots: List[str] = field(default_factory=list)
    match_commentary_finishes: List[str] = field(default_factory=list)
    news_headline_style: List[str] = field(default_factory=list)
    threat_phrases: List[str] = field(default_factory=list)
    compliment_phrases: List[str] = field(default_factory=list)
    prediction_phrases: List[str] = field(default_factory=list)
    catchphrases: List[str] = field(default_factory=list)
    message_sign_offs: List[str] = field(default_factory=list)
    phone_greetings: List[str] = field(default_factory=list)
    show_rating_reactions: Dict[str, List[str]] = field(default_factory=dict)


# ==================== BOOKING WEIGHTS ====================

@dataclass
class BookingWeights:
    """How this personality weighs different booking decisions"""
    title_change_chance: float = 0.15     # Base chance of title change per defense
    heel_turn_chance: float = 0.05        # Chance of suggesting a heel turn
    face_turn_chance: float = 0.03        # Chance of suggesting a face turn
    interference_chance: float = 0.10     # Chance of run-in during match
    dirty_finish_chance: float = 0.10     # Chance of DQ/countout/screwjob
    squash_match_chance: float = 0.05     # Chance of suggesting a squash
    upset_chance: float = 0.08            # Chance of lower-card beating upper-card
    injury_angle_chance: float = 0.03     # Chance of fake injury storyline
    return_surprise_chance: float = 0.02  # Chance of surprise debut/return
    faction_formation_chance: float = 0.05 # Chance of forming a stable
    betrayal_chance: float = 0.04         # Chance of tag partner/ally betrayal
    rematch_reluctance: float = 0.3       # How much they avoid repeat matches
    push_new_talent: float = 0.3          # Willingness to push unproven wrestlers
    protect_champions: float = 0.7        # How strongly they protect title holders


# ==================== 4 PERSONALITY DEFINITIONS ====================

PERSONALITIES = {
    PersonalityType.SHOWMAN: {
        "name": "The Showman",
        "real_world_inspiration": "Vince Russo",
        "description": "Crash TV incarnate. Every show needs a swerve, every match needs a twist. Ratings are everything. Logic is optional.",
        "icon": "🎬",
        "color": "#ef4444",
        "traits": PersonalityTraits(
            chaos_factor=0.9,
            star_focus=0.4,
            storyline_complexity=0.8,
            violence_preference=0.6,
            swerve_frequency=0.95,
            respect_for_kayfabe=0.2,
            business_savvy=0.5,
            patience=0.1,
            ego=0.9,
            risk_tolerance=0.95,
            loyalty_to_favorites=0.3,
            comedy_tolerance=0.8,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.35,
            heel_turn_chance=0.15,
            face_turn_chance=0.12,
            interference_chance=0.30,
            dirty_finish_chance=0.25,
            squash_match_chance=0.02,
            upset_chance=0.20,
            injury_angle_chance=0.10,
            return_surprise_chance=0.08,
            faction_formation_chance=0.12,
            betrayal_chance=0.15,
            rematch_reluctance=0.1,
            push_new_talent=0.5,
            protect_champions=0.3,
        ),
        "voice": VoiceProfile(
            greeting_style=[
                "Bro, you're not gonna BELIEVE what I've got planned!",
                "Listen, I've been thinking... and it's GOLD.",
                "Alright bro, forget everything you know about wrestling.",
                "I swear on my life, this is the greatest idea ever.",
            ],
            excitement_phrases=[
                "BRO! That's a SWERVE nobody saw coming!",
                "The ratings are gonna go through the ROOF!",
                "THIS is what wrestling is all about — SHOCK VALUE!",
                "Nobody will see this coming! NOBODY!",
                "We just broke the internet, bro!",
            ],
            anger_phrases=[
                "This is garbage, bro. We need a SWERVE!",
                "The show is dying! We need to shake things up RIGHT NOW!",
                "You're killing my creative vision here, bro!",
                "This is the most boring show I've ever seen. FIX IT.",
            ],
            praise_phrases=[
                "NOW we're talking! That's entertainment!",
                "See? When you listen to me, magic happens!",
                "That's gonna put butts in seats, bro!",
                "THAT'S how you do a wrestling show!",
            ],
            criticism_phrases=[
                "Too predictable. Where's the swerve?",
                "This match needs more DRAMA, not wrestling!",
                "Nobody cares about mat wrestling, bro!",
                "You're booking like it's 1985. Wake up!",
            ],
            booking_suggestions=[
                "What if {wrestler1} turns on {wrestler2} mid-match?",
                "Hear me out — {wrestler1} wins the title, then LOSES IT the same night!",
                "We put the title on {wrestler1}. Nobody expects it. SWERVE.",
                "Let's have EVERYONE interfere. Total chaos. Ratings gold.",
                "What if {wrestler1} reveals they've been working with {wrestler2} all along?",
                "{wrestler1} crashes through the announce table. Trust me.",
                "Pole match. Put the contract on a pole. Trust me, bro.",
            ],
            match_commentary_openings=[
                "This is gonna be INSANE, I can feel it!",
                "Forget everything you think you know about these two!",
                "Something tells me we haven't seen the last twist tonight!",
            ],
            match_commentary_big_spots=[
                "OH MY GOD! Did you see that?! NOBODY expected that!",
                "WAIT! What is happening?! This wasn't in the script!",
                "The crowd is losing their MINDS! This is MUST-SEE TV!",
            ],
            match_commentary_finishes=[
                "WHAT A SWERVE! Nobody saw that finish coming!",
                "That's the kind of moment that changes EVERYTHING!",
                "I told you! I TOLD YOU something was gonna happen!",
            ],
            news_headline_style=[
                "SHOCKING: {event} — Nobody Saw This Coming!",
                "BREAKING: Massive Swerve at {show}!",
                "EXCLUSIVE: The twist that has EVERYONE talking!",
                "YOU WON'T BELIEVE what happened at {show}!",
            ],
            catchphrases=[
                "Bro, I swear to God...",
                "That's a shoot, bro!",
                "It's all about the swerve!",
                "Ratings, bro. RATINGS.",
            ],
            message_sign_offs=[
                "Trust me on this one, bro.",
                "— The Showman",
                "P.S. This is gonna be HUGE.",
                "Let's make history tonight.",
            ],
            phone_greetings=[
                "Bro! Pick up! I've got the GREATEST idea!",
                "You sitting down? Because what I'm about to say...",
                "Don't hang up — this is career-changing stuff!",
            ],
            show_rating_reactions={
                "5_star": ["BRO! FIVE STARS! That's the greatest thing I've ever seen!"],
                "4_star": ["Now THAT'S entertainment! The people are talking!"],
                "3_star": ["Decent, but we need MORE swerves. More drama!"],
                "2_star": ["This is dying, bro. We need to blow it up. COMPLETELY."],
                "1_star": ["I'm rewriting EVERYTHING. This show needs surgery."],
            },
        ),
    },

    PersonalityType.MASTERMIND: {
        "name": "The Mastermind",
        "real_world_inspiration": "Eric Bischoff",
        "description": "It's all about the money and the big picture. Star power wins wars. Outspend, outmaneuver, and outsmart the competition.",
        "icon": "💼",
        "color": "#3b82f6",
        "traits": PersonalityTraits(
            chaos_factor=0.3,
            star_focus=0.9,
            storyline_complexity=0.5,
            violence_preference=0.3,
            swerve_frequency=0.3,
            respect_for_kayfabe=0.5,
            business_savvy=0.95,
            patience=0.6,
            ego=0.7,
            risk_tolerance=0.6,
            loyalty_to_favorites=0.8,
            comedy_tolerance=0.4,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.12,
            heel_turn_chance=0.06,
            face_turn_chance=0.04,
            interference_chance=0.15,
            dirty_finish_chance=0.08,
            squash_match_chance=0.10,
            upset_chance=0.05,
            injury_angle_chance=0.04,
            return_surprise_chance=0.06,
            faction_formation_chance=0.08,
            betrayal_chance=0.06,
            rematch_reluctance=0.5,
            push_new_talent=0.2,
            protect_champions=0.85,
        ),
        "voice": VoiceProfile(
            greeting_style=[
                "Let's talk business.",
                "I've been crunching the numbers. Listen up.",
                "Time is money. Here's what we need to do.",
                "I've got a deal that's going to change everything.",
            ],
            excitement_phrases=[
                "That's a money match right there!",
                "The buyrate is going to be MASSIVE!",
                "This is the kind of main event that sells tickets!",
                "Now THAT'S a box office attraction!",
            ],
            anger_phrases=[
                "We're hemorrhaging money. This is unacceptable.",
                "The competition is eating our lunch and you're booking THIS?",
                "This isn't a charity. We need STARS.",
                "I didn't invest in this promotion to watch it fail.",
            ],
            praise_phrases=[
                "Smart booking. The audience is buying in.",
                "That's how you build a main event scene.",
                "The numbers don't lie — this is working.",
                "Now you're thinking like a businessman.",
            ],
            criticism_phrases=[
                "Where's the star power? I see midcarders.",
                "This isn't going to sell tickets.",
                "We need a MEGASTAR, not a roster full of B-players.",
                "The competition would never book something this weak.",
            ],
            booking_suggestions=[
                "Push {wrestler1} to the moon. They're our franchise player.",
                "Sign the biggest free agent available. Outbid everyone.",
                "{wrestler1} vs {wrestler2} at the big PPV. Money match.",
                "We need a faction. {wrestler1} leading a stable = ratings.",
                "Protect {wrestler1}'s win-loss record. They're our investment.",
                "Book {wrestler1} to squash {wrestler2}. Establish dominance.",
            ],
            match_commentary_openings=[
                "This is the match that's been selling tickets all week!",
                "Two franchise players colliding — this is box office gold!",
                "The anticipation for this match has been building for weeks!",
            ],
            match_commentary_big_spots=[
                "THAT is why this person is a STAR!",
                "The crowd is on their feet! This is main event caliber!",
                "This is the moment that justifies the investment!",
            ],
            match_commentary_finishes=[
                "And THAT is why they're the top of the card!",
                "What a finish! That's the kind of moment you build a promotion around!",
                "The investment pays off! Star power wins every time!",
            ],
            news_headline_style=[
                "BUSINESS REPORT: {event} Expected to Drive Major Revenue",
                "EXCLUSIVE: Blockbuster Deal — {show} Sets Record",
                "BREAKING: Major Star {event} — Industry Shaken",
                "ANALYSIS: The Strategic Move Behind {event}",
            ],
            catchphrases=[
                "Controversy creates cash.",
                "It's not personal, it's business.",
                "The numbers don't lie.",
                "Star power sells tickets.",
            ],
            message_sign_offs=[
                "The bottom line is the bottom line.",
                "— The Mastermind",
                "Think big or go home.",
                "The competition never sleeps. Neither should we.",
            ],
            phone_greetings=[
                "I'll keep this brief. There's money to be made.",
                "I've got an offer you'd be smart to take.",
                "The competition just made a move. We need to counter.",
            ],
            show_rating_reactions={
                "5_star": ["A masterpiece. The investors will be very pleased."],
                "4_star": ["Strong numbers. But we can always push harder."],
                "3_star": ["Acceptable, but we're not maximizing our potential."],
                "2_star": ["This is costing us money. We need bigger stars."],
                "1_star": ["Unacceptable. Heads are going to roll."],
            },
        ),
    },

    PersonalityType.MAD_SCIENTIST: {
        "name": "The Mad Scientist",
        "real_world_inspiration": "Paul Heyman",
        "description": "Extreme vision. One chosen champion above all others. Violent, character-driven, cult-like devotion to the product.",
        "icon": "🩸",
        "color": "#dc2626",
        "traits": PersonalityTraits(
            chaos_factor=0.6,
            star_focus=0.7,
            storyline_complexity=0.9,
            violence_preference=0.9,
            swerve_frequency=0.5,
            respect_for_kayfabe=0.7,
            business_savvy=0.4,
            patience=0.5,
            ego=0.8,
            risk_tolerance=0.8,
            loyalty_to_favorites=0.95,
            comedy_tolerance=0.2,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.10,
            heel_turn_chance=0.08,
            face_turn_chance=0.05,
            interference_chance=0.20,
            dirty_finish_chance=0.15,
            squash_match_chance=0.08,
            upset_chance=0.10,
            injury_angle_chance=0.08,
            return_surprise_chance=0.05,
            faction_formation_chance=0.10,
            betrayal_chance=0.10,
            rematch_reluctance=0.4,
            push_new_talent=0.4,
            protect_champions=0.9,
        ),
        "voice": VoiceProfile(
            greeting_style=[
                "Ladies and gentlemen, my name is your creative director...",
                "Listen carefully, because what I'm about to say matters.",
                "The product needs to EVOLVE. Here's how.",
                "I've seen the future of this promotion. Let me show you.",
            ],
            excitement_phrases=[
                "THAT is professional wrestling at its finest!",
                "The audience just witnessed something they'll NEVER forget!",
                "THIS is the kind of moment that creates LEGENDS!",
                "Blood, sweat, and storytelling — PERFECTION!",
            ],
            anger_phrases=[
                "This product is dying and nobody cares enough to save it!",
                "We're wasting talent! These wrestlers deserve BETTER booking!",
                "I didn't build ECW from nothing to watch this mediocrity!",
                "The audience deserves more and we're FAILING them!",
            ],
            praise_phrases=[
                "Now THAT is the kind of storytelling I'm talking about!",
                "You just created a moment. A REAL moment.",
                "The audience believed every second. That's the art.",
                "Character-driven wrestling. This is what it's all about.",
            ],
            criticism_phrases=[
                "Where's the EMOTION? These characters feel hollow.",
                "This match had no story. No stakes. No reason to care.",
                "We're insulting the audience's intelligence with this booking.",
                "The violence needs PURPOSE, not just shock value.",
            ],
            booking_suggestions=[
                "{wrestler1} is THE guy. Build EVERYTHING around them.",
                "A blood feud between {wrestler1} and {wrestler2}. Make it PERSONAL.",
                "{wrestler1} needs to cut a promo that makes people FEEL something.",
                "Extreme Rules. Let them tear each other apart. Tell the story with violence.",
                "{wrestler1} doesn't need the title. They ARE the main event.",
                "Create a faction around {wrestler1}. They're the cult leader.",
            ],
            match_commentary_openings=[
                "This isn't just a match — this is a WAR with a story to tell!",
                "These two have been on a collision course for WEEKS!",
                "The personal hatred between these two is PALPABLE!",
            ],
            match_commentary_big_spots=[
                "THE VIOLENCE! The storytelling through PHYSICALITY!",
                "This is EXTREME! This is what wrestling SHOULD be!",
                "Look at the emotion! Look at the INTENSITY!",
            ],
            match_commentary_finishes=[
                "And the story reaches its climax! WHAT a conclusion!",
                "That wasn't just a match — that was a MASTERPIECE of violence and art!",
                "The chosen one prevails! As I predicted!",
            ],
            news_headline_style=[
                "EDITORIAL: {event} Proves Wrestling Can Be ART",
                "BLOOD FEUD: The Story Behind {event}",
                "EXTREME: {show} Delivers Unforgettable Brutality",
                "CHARACTER STUDY: Why {event} Matters",
            ],
            catchphrases=[
                "The cream rises to the top.",
                "Extreme isn't a gimmick — it's a philosophy.",
                "Every great champion needs a great advocate.",
                "Violence is a language. Learn to speak it.",
            ],
            message_sign_offs=[
                "The truth hurts. But it's still the truth.",
                "— The Mad Scientist",
                "Evolution is not optional.",
                "The product must be protected at all costs.",
            ],
            phone_greetings=[
                "I need your undivided attention. This is important.",
                "I've been watching the product. We need to talk.",
                "My client — I mean, our TOP STAR — needs attention.",
            ],
            show_rating_reactions={
                "5_star": ["Art. Pure art. The audience witnessed something special tonight."],
                "4_star": ["A strong show with genuine emotion. We're building something."],
                "3_star": ["There were moments, but we need more CHARACTER. More STORY."],
                "2_star": ["We're losing the audience. The product needs an extreme makeover."],
                "1_star": ["This is an embarrassment. I'd rather shut down than produce this."],
            },
        ),
    },

    PersonalityType.TRADITIONALIST: {
        "name": "The Traditionalist",
        "real_world_inspiration": "Jim Cornette / Pat Patterson",
        "description": "Logical storytelling, slow-burn feuds, and respect for the business. Wrestling comes first. Entertainment follows.",
        "icon": "📋",
        "color": "#10b981",
        "traits": PersonalityTraits(
            chaos_factor=0.15,
            star_focus=0.5,
            storyline_complexity=0.6,
            violence_preference=0.3,
            swerve_frequency=0.1,
            respect_for_kayfabe=0.95,
            business_savvy=0.6,
            patience=0.9,
            ego=0.3,
            risk_tolerance=0.2,
            loyalty_to_favorites=0.5,
            comedy_tolerance=0.3,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.08,
            heel_turn_chance=0.03,
            face_turn_chance=0.02,
            interference_chance=0.05,
            dirty_finish_chance=0.05,
            squash_match_chance=0.06,
            upset_chance=0.05,
            injury_angle_chance=0.02,
            return_surprise_chance=0.03,
            faction_formation_chance=0.04,
            betrayal_chance=0.03,
            rematch_reluctance=0.6,
            push_new_talent=0.35,
            protect_champions=0.8,
        ),
        "voice": VoiceProfile(
            greeting_style=[
                "Let's look at the booking logically.",
                "Here's what makes sense for the long-term.",
                "The audience is smart. Let's book accordingly.",
                "Good evening. I've been reviewing the card.",
            ],
            excitement_phrases=[
                "Now THAT is professional wrestling!",
                "A well-told story with a satisfying conclusion!",
                "The fundamentals were on display tonight!",
                "That's how you build a long-term feud!",
            ],
            anger_phrases=[
                "This booking makes no logical sense.",
                "We're insulting the audience's intelligence.",
                "The business didn't survive 100 years for THIS.",
                "Consistency matters. This is inconsistent.",
            ],
            praise_phrases=[
                "Logical, well-paced, and the audience bought in.",
                "THAT'S how you tell a story in the ring.",
                "The slow burn pays off. Patience wins.",
                "Clean, professional wrestling. As it should be.",
            ],
            criticism_phrases=[
                "Too many gimmicks. Let the WRESTLING speak.",
                "This hot-shotting is going to burn through our roster.",
                "Where's the logic? Why would this character do that?",
                "We're sacrificing long-term for short-term pops.",
            ],
            booking_suggestions=[
                "{wrestler1} earns the title shot through a tournament. Proper.",
                "Build {wrestler1} vs {wrestler2} slowly over 6-8 weeks.",
                "The champion defends cleanly. Protect the title's prestige.",
                "{wrestler1} works their way up the card. No shortcuts.",
                "Let {wrestler1} and {wrestler2} have a 20-minute classic.",
                "Tag team wrestling should be a feature, not an afterthought.",
            ],
            match_commentary_openings=[
                "Two competitors who've earned the right to be here tonight.",
                "This matchup has been building through weeks of logical storytelling.",
                "Let's see some good, honest professional wrestling.",
            ],
            match_commentary_big_spots=[
                "Tremendous in-ring work! The fundamentals are on display!",
                "A well-executed spot that tells the story of this match!",
                "Listen to this crowd — they're invested in the story!",
            ],
            match_commentary_finishes=[
                "And the better competitor wins tonight. As it should be.",
                "A clean finish to an excellent wrestling match!",
                "THAT is how professional wrestling is supposed to work!",
            ],
            news_headline_style=[
                "REPORT: {event} — A Return to Quality Wrestling",
                "REVIEW: {show} Delivers Consistent, Logical Booking",
                "ANALYSIS: Why {event} Is Good for the Business",
                "TRADITION: {event} Proves the Classics Still Work",
            ],
            catchphrases=[
                "Respect the business.",
                "Logic. Psychology. Storytelling.",
                "The audience is smarter than you think.",
                "Slow burn, big payoff.",
            ],
            message_sign_offs=[
                "Book with logic. The rest follows.",
                "— The Traditionalist",
                "Respect the craft.",
                "The business comes first.",
            ],
            phone_greetings=[
                "Good to hear from you. Let's discuss the booking.",
                "I've been reviewing the card. I have some thoughts.",
                "The product needs consistency. Let me explain.",
            ],
            show_rating_reactions={
                "5_star": ["A masterclass in professional wrestling. The business is alive and well."],
                "4_star": ["Strong booking. Logical, consistent, well-executed."],
                "3_star": ["Decent, but we can tighten up the storytelling."],
                "2_star": ["We're losing our way. Back to basics."],
                "1_star": ["This is an insult to the history of professional wrestling."],
            },
        ),
    },
}


# ==================== MOOD TRIGGERS ====================

MOOD_TRIGGERS = {
    "great_show": {"shift": 2, "direction": "positive"},
    "good_show": {"shift": 1, "direction": "positive"},
    "bad_show": {"shift": -1, "direction": "negative"},
    "terrible_show": {"shift": -2, "direction": "negative"},
    "sellout": {"shift": 2, "direction": "positive"},
    "five_star_match": {"shift": 3, "direction": "positive"},
    "title_change": {"shift": 1, "direction": "positive"},
    "low_attendance": {"shift": -1, "direction": "negative"},
    "wrestler_walkout": {"shift": -2, "direction": "negative"},
    "money_crisis": {"shift": -2, "direction": "negative"},
    "rival_success": {"shift": -1, "direction": "negative"},
    "fan_growth": {"shift": 1, "direction": "positive"},
    "fan_loss": {"shift": -1, "direction": "negative"},
    "injury_crisis": {"shift": -1, "direction": "negative"},
    "championship_created": {"shift": 1, "direction": "positive"},
    "loan_default": {"shift": -3, "direction": "negative"},
    "viral_moment": {"shift": 2, "direction": "positive"},
    "scandal": {"shift": -2, "direction": "negative"},
}

MOOD_SCALE = [
    MoodState.FURIOUS,      # -5 to -4
    MoodState.FRUSTRATED,   # -3 to -2
    MoodState.BORED,        # -1
    MoodState.NEUTRAL,      # 0
    MoodState.HAPPY,        # 1 to 2
    MoodState.ECSTATIC,     # 3 to 5
    MoodState.SCHEMING,     # Special: triggered by rival success
    MoodState.DESPERATE,    # Special: triggered by money crisis
]

# ==================== PERSONALITY MANAGER ====================

class PersonalityManager:
    """Manages the active AI personality, mood, and generates personality-tinted outputs"""

    def __init__(self, personality_type: PersonalityType = PersonalityType.TRADITIONALIST):
        self.personality_type = personality_type
        self.personality_data = PERSONALITIES[personality_type]
        self.traits = self.personality_data["traits"]
        self.booking_weights = self.personality_data["booking_weights"]
        self.voice = self.personality_data["voice"]
        self.mood_value: int = 0  # -5 to +5 scale
        self.mood_state: MoodState = MoodState.NEUTRAL
        self.creative_control_level: CreativeControlLevel = CreativeControlLevel.OFF
        self.memory: List[Dict] = []  # Recent events the AI remembers
        self.favorite_wrestler: str = ""  # AI's chosen one
        self.grudge_wrestler: str = ""  # AI dislikes this wrestler
        self.weeks_active: int = 0

    def get_name(self) -> str:
        return self.personality_data["name"]

    def get_icon(self) -> str:
        return self.personality_data["icon"]

    def get_color(self) -> str:
        return self.personality_data["color"]

    def get_description(self) -> str:
        return self.personality_data["description"]

    # ==================== MOOD SYSTEM ====================

    def process_mood_trigger(self, trigger: str):
        """Adjust mood based on game events"""
        trigger_data = MOOD_TRIGGERS.get(trigger)
        if not trigger_data:
            return

        shift = trigger_data["shift"]
        self.mood_value = max(-5, min(5, self.mood_value + shift))

        # Update mood state from value
        if self.mood_value >= 3:
            self.mood_state = MoodState.ECSTATIC
        elif self.mood_value >= 1:
            self.mood_state = MoodState.HAPPY
        elif self.mood_value == 0:
            self.mood_state = MoodState.NEUTRAL
        elif self.mood_value >= -1:
            self.mood_state = MoodState.BORED
        elif self.mood_value >= -3:
            self.mood_state = MoodState.FRUSTRATED
        else:
            self.mood_state = MoodState.FURIOUS

        # Special mood overrides
        if trigger == "rival_success":
            self.mood_state = MoodState.SCHEMING
        elif trigger == "money_crisis":
            self.mood_state = MoodState.DESPERATE

    def get_mood_display(self) -> Dict:
        """Get mood info for UI display"""
        mood_colors = {
            MoodState.ECSTATIC: "#10b981",
            MoodState.HAPPY: "#3b82f6",
            MoodState.NEUTRAL: "#6b7280",
            MoodState.BORED: "#9ca3af",
            MoodState.FRUSTRATED: "#f59e0b",
            MoodState.FURIOUS: "#ef4444",
            MoodState.SCHEMING: "#8b5cf6",
            MoodState.DESPERATE: "#dc2626",
        }
        mood_emojis = {
            MoodState.ECSTATIC: "🤩",
            MoodState.HAPPY: "😊",
            MoodState.NEUTRAL: "😐",
            MoodState.BORED: "😒",
            MoodState.FRUSTRATED: "😤",
            MoodState.FURIOUS: "🤬",
            MoodState.SCHEMING: "🤔",
            MoodState.DESPERATE: "😰",
        }
        return {
            "state": self.mood_state.value,
            "value": self.mood_value,
            "color": mood_colors.get(self.mood_state, "#6b7280"),
            "emoji": mood_emojis.get(self.mood_state, "😐"),
        }

    # ==================== VOICE / TEXT GENERATION ====================

    def get_random_line(self, category: str, context: Dict = None) -> str:
        """Get a random line from the voice profile for a category"""
        lines = getattr(self.voice, category, [])
        if not lines:
            return ""

        line = random.choice(lines)

        # Variable substitution
        if context:
            for key, value in context.items():
                line = line.replace(f"{{{key}}}", str(value))

        return line

    def get_greeting(self) -> str:
        return self.get_random_line("greeting_style")

    def get_excitement(self) -> str:
        return self.get_random_line("excitement_phrases")

    def get_anger(self) -> str:
        return self.get_random_line("anger_phrases")

    def get_praise(self) -> str:
        return self.get_random_line("praise_phrases")

    def get_criticism(self) -> str:
        return self.get_random_line("criticism_phrases")

    def get_catchphrase(self) -> str:
        return self.get_random_line("catchphrases")

    def get_sign_off(self) -> str:
        return self.get_random_line("message_sign_offs")

    def get_phone_greeting(self) -> str:
        return self.get_random_line("phone_greetings")

    def get_booking_suggestion(self, wrestler1: str = "", wrestler2: str = "") -> str:
        line = self.get_random_line("booking_suggestions", {
            "wrestler1": wrestler1,
            "wrestler2": wrestler2,
        })
        return line

    def get_show_reaction(self, avg_rating: float) -> str:
        """Get AI reaction to a show based on its rating"""
        if avg_rating >= 4.5:
            key = "5_star"
        elif avg_rating >= 3.5:
            key = "4_star"
        elif avg_rating >= 2.5:
            key = "3_star"
        elif avg_rating >= 1.5:
            key = "2_star"
        else:
            key = "1_star"

        reactions = self.voice.show_rating_reactions.get(key, ["No comment."])
        return random.choice(reactions)

    def get_commentary_line(self, beat_type: str) -> str:
        """Get a commentary line for live show mode"""
        if beat_type == "opening":
            return self.get_random_line("match_commentary_openings")
        elif beat_type == "big_spot":
            return self.get_random_line("match_commentary_big_spots")
        elif beat_type == "finish":
            return self.get_random_line("match_commentary_finishes")
        return ""

    def get_news_headline(self, event: str = "", show: str = "") -> str:
        return self.get_random_line("news_headline_style", {
            "event": event,
            "show": show,
        })

    # ==================== BOOKING DECISIONS ====================

    def should_trigger_swerve(self) -> bool:
        """Based on personality, should a surprise swerve happen?"""
        return random.random() < self.traits.swerve_frequency

    def should_change_title(self) -> bool:
        return random.random() < self.booking_weights.title_change_chance

    def should_trigger_heel_turn(self) -> bool:
        return random.random() < self.booking_weights.heel_turn_chance

    def should_trigger_face_turn(self) -> bool:
        return random.random() < self.booking_weights.face_turn_chance

    def should_interfere(self) -> bool:
        return random.random() < self.booking_weights.interference_chance

    def should_dirty_finish(self) -> bool:
        return random.random() < self.booking_weights.dirty_finish_chance

    def should_upset(self) -> bool:
        return random.random() < self.booking_weights.upset_chance

    def should_push_new_talent(self) -> bool:
        return random.random() < self.booking_weights.push_new_talent

    def get_chaos_factor(self) -> float:
        """Get the current chaos factor (0-1), affected by mood"""
        base = self.traits.chaos_factor
        if self.mood_state == MoodState.FURIOUS:
            base = min(1.0, base + 0.2)
        elif self.mood_state == MoodState.DESPERATE:
            base = min(1.0, base + 0.3)
        elif self.mood_state == MoodState.ECSTATIC:
            base = max(0.0, base - 0.1)
        return base

    # ==================== CREATIVE CONTROL ====================

    def set_creative_control(self, level: CreativeControlLevel):
        self.creative_control_level = level

    def should_override_booking(self) -> bool:
        """Should the AI override the player's booking decisions?"""
        if self.creative_control_level == CreativeControlLevel.OFF:
            return False
        elif self.creative_control_level == CreativeControlLevel.LIGHT:
            return random.random() < 0.1
        elif self.creative_control_level == CreativeControlLevel.HEAVY:
            return random.random() < 0.35
        elif self.creative_control_level == CreativeControlLevel.RUSSO_MODE:
            return random.random() < 0.6
        return False

    # ==================== MEMORY ====================

    def remember_event(self, event_type: str, details: Dict):
        """Store an event in the AI's memory"""
        self.memory.append({
            "type": event_type,
            "details": details,
            "week": self.weeks_active,
        })
        # Keep memory limited
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]

    def get_recent_memory(self, event_type: str = None, limit: int = 5) -> List[Dict]:
        """Retrieve recent memories, optionally filtered by type"""
        if event_type:
            filtered = [m for m in self.memory if m["type"] == event_type]
        else:
            filtered = self.memory
        return filtered[-limit:]

    def pick_favorite(self, roster: List[Dict]) -> str:
        """AI picks a favorite wrestler to push based on personality"""
        if not roster:
            return ""

        if self.traits.star_focus > 0.7:
            # Focus on most popular
            sorted_roster = sorted(roster, key=lambda w: w.get("popularity", 0), reverse=True)
        elif self.traits.loyalty_to_favorites > 0.7:
            # Stick with existing favorite if any
            if self.favorite_wrestler:
                return self.favorite_wrestler
            sorted_roster = sorted(roster, key=lambda w: w.get("popularity", 0) + w.get("wins", 0), reverse=True)
        else:
            # Random pick weighted by skill
            sorted_roster = sorted(roster, key=lambda w: w.get("popularity", 0) * 0.5 + random.randint(0, 30), reverse=True)

        if sorted_roster:
            self.favorite_wrestler = sorted_roster[0].get("name", "")
        return self.favorite_wrestler

    # ==================== WEEKLY UPDATE ====================

    def weekly_update(self):
        """Process weekly AI personality updates"""
        self.weeks_active += 1
        # Mood slowly returns to neutral
        if self.mood_value > 0:
            self.mood_value -= 1
        elif self.mood_value < 0:
            self.mood_value += 1
        if self.mood_value == 0:
            self.mood_state = MoodState.NEUTRAL

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "personality_type": self.personality_type.value,
            "mood_value": self.mood_value,
            "mood_state": self.mood_state.value,
            "creative_control_level": self.creative_control_level.value,
            "memory": self.memory[-30:],
            "favorite_wrestler": self.favorite_wrestler,
            "grudge_wrestler": self.grudge_wrestler,
            "weeks_active": self.weeks_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PersonalityManager":
        try:
            pt = PersonalityType(data.get("personality_type", "The Traditionalist"))
        except (ValueError, KeyError):
            pt = PersonalityType.TRADITIONALIST

        manager = cls(personality_type=pt)
        manager.mood_value = data.get("mood_value", 0)

        try:
            manager.mood_state = MoodState(data.get("mood_state", "Neutral"))
        except (ValueError, KeyError):
            manager.mood_state = MoodState.NEUTRAL

        try:
            manager.creative_control_level = CreativeControlLevel(data.get("creative_control_level", "Off"))
        except (ValueError, KeyError):
            manager.creative_control_level = CreativeControlLevel.OFF

        manager.memory = data.get("memory", [])
        manager.favorite_wrestler = data.get("favorite_wrestler", "")
        manager.grudge_wrestler = data.get("grudge_wrestler", "")
        manager.weeks_active = data.get("weeks_active", 0)

        return manager
