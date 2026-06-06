# ai/director.py
"""
Director — The brain of the AI. personality + voice + director merged.

Contains three layers:
  1. PersonalityManager  (the 4 archetypes, mood, booking weights)
  2. VoiceEngine         (turns personality + context into text)
  3. AIDirector          (the coordinator that owns both)

EventSeverity now comes from ai.events (was ai.event_generator).
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ==========================================================================
# ==========================  PERSONALITY  =================================
# ==========================================================================

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


@dataclass
class PersonalityTraits:
    chaos_factor: float = 0.5
    star_focus: float = 0.5
    storyline_complexity: float = 0.5
    violence_preference: float = 0.5
    swerve_frequency: float = 0.5
    respect_for_kayfabe: float = 0.5
    business_savvy: float = 0.5
    patience: float = 0.5
    ego: float = 0.5
    risk_tolerance: float = 0.5
    loyalty_to_favorites: float = 0.5
    comedy_tolerance: float = 0.5


@dataclass
class VoiceProfile:
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


@dataclass
class BookingWeights:
    title_change_chance: float = 0.15
    heel_turn_chance: float = 0.05
    face_turn_chance: float = 0.03
    interference_chance: float = 0.10
    dirty_finish_chance: float = 0.10
    squash_match_chance: float = 0.05
    upset_chance: float = 0.08
    injury_angle_chance: float = 0.03
    return_surprise_chance: float = 0.02
    faction_formation_chance: float = 0.05
    betrayal_chance: float = 0.04
    rematch_reluctance: float = 0.3
    push_new_talent: float = 0.3
    protect_champions: float = 0.7


PERSONALITIES = {
    PersonalityType.SHOWMAN: {
        "name": "The Showman",
        "real_world_inspiration": "Vince Russo",
        "description": "Crash TV incarnate. Every show needs a swerve, every match needs a twist. Ratings are everything. Logic is optional.",
        "icon": "🎬",
        "color": "#ef4444",
        "traits": PersonalityTraits(
            chaos_factor=0.9, star_focus=0.4, storyline_complexity=0.8,
            violence_preference=0.6, swerve_frequency=0.95, respect_for_kayfabe=0.2,
            business_savvy=0.5, patience=0.1, ego=0.9, risk_tolerance=0.95,
            loyalty_to_favorites=0.3, comedy_tolerance=0.8,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.35, heel_turn_chance=0.15, face_turn_chance=0.12,
            interference_chance=0.30, dirty_finish_chance=0.25, squash_match_chance=0.02,
            upset_chance=0.20, injury_angle_chance=0.10, return_surprise_chance=0.08,
            faction_formation_chance=0.12, betrayal_chance=0.15, rematch_reluctance=0.1,
            push_new_talent=0.5, protect_champions=0.3,
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
                "Bro, I swear to God...", "That's a shoot, bro!",
                "It's all about the swerve!", "Ratings, bro. RATINGS.",
            ],
            message_sign_offs=[
                "Trust me on this one, bro.", "— The Showman",
                "P.S. This is gonna be HUGE.", "Let's make history tonight.",
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
            chaos_factor=0.3, star_focus=0.9, storyline_complexity=0.5,
            violence_preference=0.3, swerve_frequency=0.3, respect_for_kayfabe=0.5,
            business_savvy=0.95, patience=0.6, ego=0.7, risk_tolerance=0.6,
            loyalty_to_favorites=0.8, comedy_tolerance=0.4,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.12, heel_turn_chance=0.06, face_turn_chance=0.04,
            interference_chance=0.15, dirty_finish_chance=0.08, squash_match_chance=0.10,
            upset_chance=0.05, injury_angle_chance=0.04, return_surprise_chance=0.06,
            faction_formation_chance=0.08, betrayal_chance=0.06, rematch_reluctance=0.5,
            push_new_talent=0.2, protect_champions=0.85,
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
                "Controversy creates cash.", "It's not personal, it's business.",
                "The numbers don't lie.", "Star power sells tickets.",
            ],
            message_sign_offs=[
                "The bottom line is the bottom line.", "— The Mastermind",
                "Think big or go home.", "The competition never sleeps. Neither should we.",
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
            chaos_factor=0.6, star_focus=0.7, storyline_complexity=0.9,
            violence_preference=0.9, swerve_frequency=0.5, respect_for_kayfabe=0.7,
            business_savvy=0.4, patience=0.5, ego=0.8, risk_tolerance=0.8,
            loyalty_to_favorites=0.95, comedy_tolerance=0.2,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.10, heel_turn_chance=0.08, face_turn_chance=0.05,
            interference_chance=0.20, dirty_finish_chance=0.15, squash_match_chance=0.08,
            upset_chance=0.10, injury_angle_chance=0.08, return_surprise_chance=0.05,
            faction_formation_chance=0.10, betrayal_chance=0.10, rematch_reluctance=0.4,
            push_new_talent=0.4, protect_champions=0.9,
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
                "The truth hurts. But it's still the truth.", "— The Mad Scientist",
                "Evolution is not optional.", "The product must be protected at all costs.",
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
            chaos_factor=0.15, star_focus=0.5, storyline_complexity=0.6,
            violence_preference=0.3, swerve_frequency=0.1, respect_for_kayfabe=0.95,
            business_savvy=0.6, patience=0.9, ego=0.3, risk_tolerance=0.2,
            loyalty_to_favorites=0.5, comedy_tolerance=0.3,
        ),
        "booking_weights": BookingWeights(
            title_change_chance=0.08, heel_turn_chance=0.03, face_turn_chance=0.02,
            interference_chance=0.05, dirty_finish_chance=0.05, squash_match_chance=0.06,
            upset_chance=0.05, injury_angle_chance=0.02, return_surprise_chance=0.03,
            faction_formation_chance=0.04, betrayal_chance=0.03, rematch_reluctance=0.6,
            push_new_talent=0.35, protect_champions=0.8,
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
                "Respect the business.", "Logic. Psychology. Storytelling.",
                "The audience is smarter than you think.", "Slow burn, big payoff.",
            ],
            message_sign_offs=[
                "Book with logic. The rest follows.", "— The Traditionalist",
                "Respect the craft.", "The business comes first.",
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
    MoodState.FURIOUS, MoodState.FRUSTRATED, MoodState.BORED, MoodState.NEUTRAL,
    MoodState.HAPPY, MoodState.ECSTATIC, MoodState.SCHEMING, MoodState.DESPERATE,
]


class PersonalityManager:
    def __init__(self, personality_type: PersonalityType = PersonalityType.TRADITIONALIST):
        self.personality_type = personality_type
        self.personality_data = PERSONALITIES[personality_type]
        self.traits = self.personality_data["traits"]
        self.booking_weights = self.personality_data["booking_weights"]
        self.voice = self.personality_data["voice"]
        self.mood_value: int = 0
        self.mood_state: MoodState = MoodState.NEUTRAL
        self.creative_control_level: CreativeControlLevel = CreativeControlLevel.OFF
        self.memory: List[Dict] = []
        self.favorite_wrestler: str = ""
        self.grudge_wrestler: str = ""
        self.weeks_active: int = 0

    def get_name(self): return self.personality_data["name"]
    def get_icon(self): return self.personality_data["icon"]
    def get_color(self): return self.personality_data["color"]
    def get_description(self): return self.personality_data["description"]

    def process_mood_trigger(self, trigger: str):
        td = MOOD_TRIGGERS.get(trigger)
        if not td:
            return
        self.mood_value = max(-5, min(5, self.mood_value + td["shift"]))
        if self.mood_value >= 3: self.mood_state = MoodState.ECSTATIC
        elif self.mood_value >= 1: self.mood_state = MoodState.HAPPY
        elif self.mood_value == 0: self.mood_state = MoodState.NEUTRAL
        elif self.mood_value >= -1: self.mood_state = MoodState.BORED
        elif self.mood_value >= -3: self.mood_state = MoodState.FRUSTRATED
        else: self.mood_state = MoodState.FURIOUS
        if trigger == "rival_success": self.mood_state = MoodState.SCHEMING
        elif trigger == "money_crisis": self.mood_state = MoodState.DESPERATE

    def get_mood_display(self) -> Dict:
        mood_colors = {
            MoodState.ECSTATIC: "#10b981", MoodState.HAPPY: "#3b82f6",
            MoodState.NEUTRAL: "#6b7280", MoodState.BORED: "#9ca3af",
            MoodState.FRUSTRATED: "#f59e0b", MoodState.FURIOUS: "#ef4444",
            MoodState.SCHEMING: "#8b5cf6", MoodState.DESPERATE: "#dc2626",
        }
        mood_emojis = {
            MoodState.ECSTATIC: "🤩", MoodState.HAPPY: "😊", MoodState.NEUTRAL: "😐",
            MoodState.BORED: "😒", MoodState.FRUSTRATED: "😤", MoodState.FURIOUS: "🤬",
            MoodState.SCHEMING: "🤔", MoodState.DESPERATE: "😰",
        }
        return {
            "state": self.mood_state.value, "value": self.mood_value,
            "color": mood_colors.get(self.mood_state, "#6b7280"),
            "emoji": mood_emojis.get(self.mood_state, "😐"),
        }

    def get_random_line(self, category: str, context: Dict = None) -> str:
        lines = getattr(self.voice, category, [])
        if not lines:
            return ""
        line = random.choice(lines)
        if context:
            for key, value in context.items():
                line = line.replace(f"{{{key}}}", str(value))
        return line

    def get_greeting(self): return self.get_random_line("greeting_style")
    def get_excitement(self): return self.get_random_line("excitement_phrases")
    def get_anger(self): return self.get_random_line("anger_phrases")
    def get_praise(self): return self.get_random_line("praise_phrases")
    def get_criticism(self): return self.get_random_line("criticism_phrases")
    def get_catchphrase(self): return self.get_random_line("catchphrases")
    def get_sign_off(self): return self.get_random_line("message_sign_offs")
    def get_phone_greeting(self): return self.get_random_line("phone_greetings")

    def get_booking_suggestion(self, wrestler1="", wrestler2=""):
        return self.get_random_line("booking_suggestions",
                                    {"wrestler1": wrestler1, "wrestler2": wrestler2})

    def get_show_reaction(self, avg_rating: float) -> str:
        if avg_rating >= 4.5: key = "5_star"
        elif avg_rating >= 3.5: key = "4_star"
        elif avg_rating >= 2.5: key = "3_star"
        elif avg_rating >= 1.5: key = "2_star"
        else: key = "1_star"
        return random.choice(self.voice.show_rating_reactions.get(key, ["No comment."]))

    def get_commentary_line(self, beat_type: str) -> str:
        if beat_type == "opening": return self.get_random_line("match_commentary_openings")
        if beat_type == "big_spot": return self.get_random_line("match_commentary_big_spots")
        if beat_type == "finish": return self.get_random_line("match_commentary_finishes")
        return ""

    def get_news_headline(self, event="", show=""):
        return self.get_random_line("news_headline_style", {"event": event, "show": show})

    def should_trigger_swerve(self): return random.random() < self.traits.swerve_frequency
    def should_change_title(self): return random.random() < self.booking_weights.title_change_chance
    def should_trigger_heel_turn(self): return random.random() < self.booking_weights.heel_turn_chance
    def should_trigger_face_turn(self): return random.random() < self.booking_weights.face_turn_chance
    def should_interfere(self): return random.random() < self.booking_weights.interference_chance
    def should_dirty_finish(self): return random.random() < self.booking_weights.dirty_finish_chance
    def should_upset(self): return random.random() < self.booking_weights.upset_chance
    def should_push_new_talent(self): return random.random() < self.booking_weights.push_new_talent

    def get_chaos_factor(self) -> float:
        base = self.traits.chaos_factor
        if self.mood_state == MoodState.FURIOUS: base = min(1.0, base + 0.2)
        elif self.mood_state == MoodState.DESPERATE: base = min(1.0, base + 0.3)
        elif self.mood_state == MoodState.ECSTATIC: base = max(0.0, base - 0.1)
        return base

    def set_creative_control(self, level: CreativeControlLevel):
        self.creative_control_level = level

    def should_override_booking(self) -> bool:
        if self.creative_control_level == CreativeControlLevel.OFF: return False
        if self.creative_control_level == CreativeControlLevel.LIGHT: return random.random() < 0.1
        if self.creative_control_level == CreativeControlLevel.HEAVY: return random.random() < 0.35
        if self.creative_control_level == CreativeControlLevel.RUSSO_MODE: return random.random() < 0.6
        return False

    def remember_event(self, event_type: str, details: Dict):
        self.memory.append({"type": event_type, "details": details, "week": self.weeks_active})
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]

    def get_recent_memory(self, event_type=None, limit=5):
        filtered = [m for m in self.memory if m["type"] == event_type] if event_type else self.memory
        return filtered[-limit:]

    def pick_favorite(self, roster: List[Dict]) -> str:
        if not roster:
            return ""
        if self.traits.star_focus > 0.7:
            sorted_roster = sorted(roster, key=lambda w: w.get("popularity", 0), reverse=True)
        elif self.traits.loyalty_to_favorites > 0.7:
            if self.favorite_wrestler:
                return self.favorite_wrestler
            sorted_roster = sorted(roster, key=lambda w: w.get("popularity", 0) + w.get("wins", 0), reverse=True)
        else:
            sorted_roster = sorted(roster, key=lambda w: w.get("popularity", 0) * 0.5 + random.randint(0, 30), reverse=True)
        if sorted_roster:
            self.favorite_wrestler = sorted_roster[0].get("name", "")
        return self.favorite_wrestler

    def weekly_update(self):
        self.weeks_active += 1
        if self.mood_value > 0: self.mood_value -= 1
        elif self.mood_value < 0: self.mood_value += 1
        if self.mood_value == 0: self.mood_state = MoodState.NEUTRAL

    def to_dict(self) -> dict:
        return {
            "personality_type": self.personality_type.value,
            "mood_value": self.mood_value, "mood_state": self.mood_state.value,
            "creative_control_level": self.creative_control_level.value,
            "memory": self.memory[-30:], "favorite_wrestler": self.favorite_wrestler,
            "grudge_wrestler": self.grudge_wrestler, "weeks_active": self.weeks_active,
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
# ==========================================================================
# ============================  VOICE  ====================================
# ==========================================================================

class VoiceContext:
    def __init__(self, **kwargs):
        self.wrestler1 = kwargs.get("wrestler1", "")
        self.wrestler2 = kwargs.get("wrestler2", "")
        self.champion = kwargs.get("champion", "")
        self.challenger = kwargs.get("challenger", "")
        self.title = kwargs.get("title", "")
        self.show_name = kwargs.get("show_name", "")
        self.venue = kwargs.get("venue", "")
        self.rating = kwargs.get("rating", 0.0)
        self.attendance = kwargs.get("attendance", 0)
        self.event = kwargs.get("event", "")
        self.match_type = kwargs.get("match_type", "")
        self.winner = kwargs.get("winner", "")
        self.loser = kwargs.get("loser", "")
        self.finish = kwargs.get("finish", "")
        self.weeks = kwargs.get("weeks", 0)
        self.money = kwargs.get("money", 0)
        self.fans = kwargs.get("fans", 0)
        self.extra = kwargs.get("extra", {})

    def to_dict(self) -> Dict:
        return {
            "wrestler1": self.wrestler1, "wrestler2": self.wrestler2,
            "champion": self.champion, "challenger": self.challenger,
            "title": self.title, "show_name": self.show_name, "venue": self.venue,
            "rating": self.rating, "attendance": self.attendance, "event": self.event,
            "match_type": self.match_type, "winner": self.winner, "loser": self.loser,
            "finish": self.finish, "weeks": self.weeks, "money": self.money,
            "fans": self.fans,
        }


SHOW_RECAP_TEMPLATES = {
    "great_show": [
        "What a night at {venue}! {attendance:,} fans witnessed something special.",
        "The crowd at {venue} was electric! Average rating: {rating:.1f}⭐",
        "{venue} delivered tonight. {attendance:,} fans, {rating:.1f}⭐ average. That's how you do it.",
    ],
    "good_show": [
        "Solid night at {venue}. {attendance:,} fans saw some good wrestling.",
        "{venue} put on a decent show. {rating:.1f}⭐ average — room to grow.",
        "Not bad at {venue}. {attendance:,} in the building, respectable numbers.",
    ],
    "bad_show": [
        "Rough night at {venue}. {rating:.1f}⭐ average — we need to do better.",
        "The {venue} crowd wasn't feeling it tonight. {attendance:,} showed up but left disappointed.",
        "Below average at {venue}. {rating:.1f}⭐ — the booking needs work.",
    ],
    "terrible_show": [
        "Disaster at {venue}. {rating:.1f}⭐ average. Heads need to roll.",
        "I've seen better shows in a car park. {venue} was embarrassing tonight.",
        "{attendance:,} fans at {venue} and we gave them THAT? Unacceptable.",
    ],
}
INJURY_TEMPLATES = [
    "{wrestler1} has been injured! Diagnosis: {event}. Recovery: {weeks} weeks.",
    "BAD NEWS: {wrestler1} went down during the show. {event}. Out {weeks} weeks.",
    "Medical update: {wrestler1} suffered a {event}. Expected to miss {weeks} weeks.",
]
SIGNING_TEMPLATES = [
    "Welcome to the roster! {wrestler1} has officially signed!",
    "{wrestler1} is ALL IN! New signing confirmed.",
    "BREAKING: {wrestler1} has joined the promotion!",
]
TITLE_CHANGE_TEMPLATES = [
    "NEW CHAMPION! {winner} defeats {loser} to win the {title}!",
    "TITLE CHANGE! {winner} is the NEW {title}!",
    "AND NEW! {winner} is your {title} after defeating {loser}!",
]
TITLE_DEFENSE_TEMPLATES = [
    "{champion} retains the {title} against {challenger}!",
    "The {title} stays with {champion}! Successful defense against {challenger}.",
]
CONTRACT_WARNING_TEMPLATES = [
    "⚠️ {wrestler1}'s contract expires in {weeks} weeks!",
    "CONTRACT ALERT: {wrestler1} is approaching free agency ({weeks} weeks remaining).",
]
FINANCIAL_WARNING_TEMPLATES = [
    "⚠️ Budget is critically low! Only ${money:,} remaining.",
    "FINANCIAL WARNING: We're running out of money. ${money:,} left.",
]
MILESTONE_TEMPLATES = ["🎉 MILESTONE: {event}!", "We just hit a huge milestone — {event}!"]
FAN_GROWTH_TEMPLATES = ["📈 Fan base growing! Now at {fans:,} fans.", "The people are talking — {fans:,} fans and counting!"]
WEEKLY_SUMMARY_PARTS = {
    "opening": ["Weekly Update — Here's what happened this week.", "End of week report. Here's the rundown."],
    "salary": ["Salaries paid: ${money:,}", "Roster payroll this week: ${money:,}"],
    "loan": ["Loan payment processed: ${money:,}", "Debt repayment: ${money:,} this week"],
}


class VoiceEngine:
    """Generates text with personality flavour and context substitution."""

    def __init__(self, personality_manager: PersonalityManager):
        self.pm = personality_manager

    def generate(self, template_list, context=None, count=1):
        if not template_list:
            return [""]
        results = []
        for _ in range(count):
            template = random.choice(template_list)
            if context:
                try:
                    text = template.format(**context.to_dict())
                except (KeyError, IndexError, ValueError):
                    text = template
            else:
                text = template
            results.append(text)
        return results

    def generate_one(self, template_list, context=None):
        lines = self.generate(template_list, context, 1)
        return lines[0] if lines else ""

    def generate_show_recap(self, avg_rating, attendance, venue, profit):
        ctx = VoiceContext(rating=avg_rating, attendance=attendance, venue=venue, money=profit)
        if avg_rating >= 4.0:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["great_show"], ctx)
        elif avg_rating >= 3.0:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["good_show"], ctx)
        elif avg_rating >= 2.0:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["bad_show"], ctx)
        else:
            base = self.generate_one(SHOW_RECAP_TEMPLATES["terrible_show"], ctx)
        personality_line = self.pm.get_show_reaction(avg_rating)
        profit_line = f"\n\n💰 Profit: ${profit:,}" if profit >= 0 else f"\n\n💸 Loss: ${abs(profit):,}"
        return f"{base}\n\n{personality_line}{profit_line}"

    def generate_injury_message(self, wrestler_name, injury_type, weeks):
        return self.generate_one(INJURY_TEMPLATES, VoiceContext(wrestler1=wrestler_name, event=injury_type, weeks=weeks))

    def generate_signing_message(self, wrestler_name):
        return self.generate_one(SIGNING_TEMPLATES, VoiceContext(wrestler1=wrestler_name))

    def generate_title_change_message(self, winner, loser, title):
        return self.generate_one(TITLE_CHANGE_TEMPLATES, VoiceContext(winner=winner, loser=loser, title=title))

    def generate_title_defense_message(self, champion, challenger, title):
        return self.generate_one(TITLE_DEFENSE_TEMPLATES, VoiceContext(champion=champion, challenger=challenger, title=title))

    def generate_contract_warning(self, wrestler_name, weeks_remaining):
        return self.generate_one(CONTRACT_WARNING_TEMPLATES, VoiceContext(wrestler1=wrestler_name, weeks=weeks_remaining))

    def generate_financial_warning(self, budget):
        return self.generate_one(FINANCIAL_WARNING_TEMPLATES, VoiceContext(money=budget))

    def generate_booking_suggestion(self, wrestler1="", wrestler2=""):
        return self.pm.get_booking_suggestion(wrestler1, wrestler2)

    def generate_commentary(self, beat_type, context=None):
        base_line = self.pm.get_commentary_line(beat_type)
        if context and base_line:
            try:
                base_line = base_line.format(**context.to_dict())
            except (KeyError, IndexError, ValueError):
                pass
        return base_line

    def generate_news_headline(self, event="", show=""):
        return self.pm.get_news_headline(event, show)

    def generate_weekly_summary(self, salaries, loan_payments=0, injuries=None, contract_warnings=None):
        parts = [self.generate_one(WEEKLY_SUMMARY_PARTS["opening"]),
                 self.generate_one(WEEKLY_SUMMARY_PARTS["salary"], VoiceContext(money=salaries))]
        if loan_payments > 0:
            parts.append(self.generate_one(WEEKLY_SUMMARY_PARTS["loan"], VoiceContext(money=loan_payments)))
        if injuries:
            parts.append("\n🏥 Injuries This Week:")
            for inj in injuries:
                parts.append(f"  • {inj}")
        if contract_warnings:
            parts.append("\n📋 Contract Alerts:")
            for warn in contract_warnings:
                parts.append(f"  • {warn}")
        return "\n".join(parts)

    def generate_milestone_message(self, milestone):
        return self.generate_one(MILESTONE_TEMPLATES, VoiceContext(event=milestone))

    def generate_fan_update(self, fan_count):
        return self.generate_one(FAN_GROWTH_TEMPLATES, VoiceContext(fans=fan_count))

    def get_greeting(self): return self.pm.get_greeting()
    def get_catchphrase(self): return self.pm.get_catchphrase()
    def get_sign_off(self): return self.pm.get_sign_off()
    def get_phone_greeting(self): return self.pm.get_phone_greeting()

    def generate_mood_message(self):
        mood = self.pm.mood_state
        if mood == MoodState.ECSTATIC:
            return self.pm.get_excitement()
        if mood == MoodState.FURIOUS:
            return self.pm.get_anger()
        if mood == MoodState.FRUSTRATED:
            return self.pm.get_criticism()
        if mood == MoodState.SCHEMING:
            return f"🤔 {self.pm.get_greeting()} I've been thinking about the competition..."
        if mood == MoodState.DESPERATE:
            return f"😰 {self.pm.get_greeting()} We're in trouble. We need to make changes NOW."
        return None


# ==========================================================================
# ============================  SIMPLE EVENT  =============================
# ==========================================================================

@dataclass
class SimpleEvent:
    """Lightweight event for AI-generated scenarios."""
    id: str
    event_type: str
    severity: object
    title: str
    description: str
    wrestlers_involved: List[str] = field(default_factory=list)
    options: List[Dict] = field(default_factory=list)
    resolved: bool = False
    week_created: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "event_type": self.event_type,
            "severity": self.severity.value if hasattr(self.severity, 'value') else str(self.severity),
            "title": self.title, "description": self.description,
            "wrestlers_involved": self.wrestlers_involved, "options": self.options,
            "resolved": self.resolved, "week_created": self.week_created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleEvent":
        from ai.events import EventSeverity
        severity_map = {
            "Minor": EventSeverity.MINOR, "Moderate": EventSeverity.MODERATE,
            "Major": EventSeverity.MAJOR, "Critical": EventSeverity.CRITICAL,
        }
        return cls(
            id=data.get("id", ""), event_type=data.get("event_type", ""),
            severity=severity_map.get(data.get("severity", "Minor"), EventSeverity.MINOR),
            title=data.get("title", ""), description=data.get("description", ""),
            wrestlers_involved=data.get("wrestlers_involved", []),
            options=data.get("options", []), resolved=data.get("resolved", False),
            week_created=data.get("week_created", 0),
        )


# ==========================================================================
# ============================  AI DIRECTOR  ==============================
# ==========================================================================

class AIDirector:
    """Central AI coordinator. Owns personality + voice."""

    def __init__(self, creative_control_enabled=False,
                 creative_control_difficulty="Normal",
                 personality_type="The Traditionalist"):
        pt_map = {
            "The Showman": PersonalityType.SHOWMAN,
            "The Mastermind": PersonalityType.MASTERMIND,
            "The Mad Scientist": PersonalityType.MAD_SCIENTIST,
            "The Traditionalist": PersonalityType.TRADITIONALIST,
        }
        pt = pt_map.get(personality_type, PersonalityType.TRADITIONALIST)
        self.personality = PersonalityManager(personality_type=pt)
        self.voice = VoiceEngine(self.personality)

        self.creative_control_enabled = creative_control_enabled
        if creative_control_enabled:
            cc_map = {"Easy": CreativeControlLevel.LIGHT, "Normal": CreativeControlLevel.HEAVY,
                      "Hard": CreativeControlLevel.RUSSO_MODE}
            self.personality.set_creative_control(cc_map.get(creative_control_difficulty, CreativeControlLevel.LIGHT))
        else:
            self.personality.set_creative_control(CreativeControlLevel.OFF)

        self.weeks_active = 0
        self.shows_directed = 0
        self.last_show_rating = 0.0
        self.consecutive_bad_shows = 0
        self.consecutive_good_shows = 0
        self.active_events = []
        self.resolved_events = []
        self.event_cooldowns = {}
        self.recent_matches = []
        self.wrestler_push_list = []
        self.wrestler_depush_list = []
        self.pending_suggestions = []
        self.accepted_suggestions = 0
        self.rejected_suggestions = 0

    def process_weekly_update(self, roster, budget, fans, prestige, current_week):
        self.weeks_active += 1
        self.personality.weekly_update()
        result = {"new_events": [], "suggestions": [], "mood_change": None, "messages": []}
        self._evaluate_game_state(budget, fans, prestige, roster)
        for et in list(self.event_cooldowns.keys()):
            self.event_cooldowns[et] -= 1
            if self.event_cooldowns[et] <= 0:
                del self.event_cooldowns[et]
        if self.creative_control_enabled:
            result["new_events"] = self._generate_weekly_events(roster, budget, fans, prestige, current_week)
        if self.creative_control_enabled and roster:
            suggestions = self._generate_booking_suggestions(roster)
            result["suggestions"] = suggestions
            self.pending_suggestions.extend(suggestions)
        if roster and self.weeks_active % 4 == 0:
            self.personality.pick_favorite(roster)
        return result

    def _evaluate_game_state(self, budget, fans, prestige, roster):
        if budget < 1000:
            self.personality.process_mood_trigger("money_crisis")
        elif budget > 50000:
            self.personality.process_mood_trigger("fan_growth")
        if fans < 100:
            self.personality.process_mood_trigger("fan_loss")
        elif fans > 10000:
            self.personality.process_mood_trigger("fan_growth")
        injured = len([w for w in roster if w.get("is_injured", False)])
        if injured > len(roster) * 0.3:
            self.personality.process_mood_trigger("injury_crisis")
        if self.consecutive_bad_shows >= 3:
            self.personality.process_mood_trigger("terrible_show")
        elif self.consecutive_good_shows >= 3:
            self.personality.process_mood_trigger("great_show")

    def record_show_result(self, avg_rating, attendance, is_sellout, profit):
        self.shows_directed += 1
        self.last_show_rating = avg_rating
        if avg_rating >= 4.0:
            self.personality.process_mood_trigger("great_show")
            self.consecutive_good_shows += 1; self.consecutive_bad_shows = 0
        elif avg_rating >= 3.0:
            self.personality.process_mood_trigger("good_show")
            self.consecutive_good_shows += 1; self.consecutive_bad_shows = 0
        elif avg_rating >= 2.0:
            self.personality.process_mood_trigger("bad_show")
            self.consecutive_bad_shows += 1; self.consecutive_good_shows = 0
        else:
            self.personality.process_mood_trigger("terrible_show")
            self.consecutive_bad_shows += 1; self.consecutive_good_shows = 0
        if is_sellout:
            self.personality.process_mood_trigger("sellout")
        self.personality.remember_event("show_completed", {
            "rating": avg_rating, "attendance": attendance,
            "is_sellout": is_sellout, "profit": profit,
        })

    def record_match_result(self, winner_name, loser_name, rating):
        self.recent_matches.append({"winner": winner_name, "loser": loser_name, "rating": rating})
        if len(self.recent_matches) > 50:
            self.recent_matches = self.recent_matches[-50:]
        if rating >= 5.0:
            self.personality.process_mood_trigger("five_star_match")
        elif rating >= 4.0:
            self.personality.process_mood_trigger("good_show")

    def _generate_weekly_events(self, roster, budget, fans, prestige, current_week):
        events = []
        chaos = self.personality.get_chaos_factor()
        if random.random() > (0.1 + chaos * 0.3):
            return events
        pool = []
        if roster:
            pool.extend(["morale_issue", "viral_moment"])
        if budget < 5000:
            pool.append("financial_pressure")
        if not pool:
            return events
        event_type = random.choice(pool)
        if event_type in self.event_cooldowns:
            return events
        event = self._create_event(event_type, roster, budget, current_week)
        if event:
            events.append(event)
            self.active_events.append(event)
            self.event_cooldowns[event_type] = random.randint(2, 6)
        return events

    def _create_event(self, event_type, roster, budget, current_week):
        from ai.events import EventSeverity
        if event_type == "morale_issue" and roster:
            wrestler = random.choice(roster)
            if wrestler.get("morale", 75) < 50:
                return SimpleEvent(
                    id=f"event_{current_week}_{event_type}", event_type=event_type,
                    severity=EventSeverity.MINOR, title=f"{wrestler['name']} is unhappy",
                    description=f"{wrestler['name']} has low morale and is considering their options.",
                    wrestlers_involved=[wrestler['name']],
                    options=[
                        {"label": "Give a raise (+$100/wk)", "effects": {"salary_change": 100, "morale": 15}},
                        {"label": "Promise a push", "effects": {"morale": 10}},
                        {"label": "Ignore it", "effects": {"morale": -5}},
                    ])
        elif event_type == "viral_moment" and roster:
            wrestler = random.choice(roster)
            return SimpleEvent(
                id=f"event_{current_week}_{event_type}", event_type=event_type,
                severity=EventSeverity.MINOR, title=f"{wrestler['name']} goes viral!",
                description=f"A clip of {wrestler['name']} has gone viral! This could boost your promotion.",
                wrestlers_involved=[wrestler['name']],
                options=[{"label": "Capitalize on it!", "effects": {"morale": 10}},
                         {"label": "Ignore it", "effects": {}}])
        elif event_type == "financial_pressure":
            return SimpleEvent(
                id=f"event_{current_week}_{event_type}", event_type=event_type,
                severity=EventSeverity.MAJOR, title="Financial Warning",
                description=f"Your budget is critically low at ${budget:,}.",
                wrestlers_involved=[],
                options=[{"label": "Cut production costs", "effects": {}},
                         {"label": "Take it week by week", "effects": {}}])
        return None

    def _generate_booking_suggestions(self, roster):
        suggestions = []
        available = [w for w in roster if not w.get("is_injured", False)]
        if len(available) < 2:
            return suggestions
        w1, w2 = random.sample(available, 2)
        text = self.personality.get_booking_suggestion(wrestler1=w1["name"], wrestler2=w2["name"])
        if text:
            suggestions.append({"text": text, "wrestlers": [w1["name"], w2["name"]],
                                "personality": self.personality.get_name()})
        return suggestions

    def get_active_events(self):
        return [e for e in self.active_events if not getattr(e, 'resolved', False)]

    def resolve_event(self, event_id, option_index):
        event = next((e for e in self.active_events if e.id == event_id), None)
        if not event:
            return {"success": False, "message": "Event not found"}
        if option_index < 0 or option_index >= len(event.options):
            return {"success": False, "message": "Invalid option"}
        chosen = event.options[option_index]
        effects = chosen.get("effects", {})
        event.resolved = True
        self.active_events.remove(event)
        self.resolved_events.append(event)
        return {"success": True, "message": f"Resolved: {chosen['label']}",
                "effects": effects, "event": event}

    def generate_show_reaction(self, avg_rating):
        return self.personality.get_show_reaction(avg_rating)

    def generate_greeting(self):
        return self.personality.get_greeting()

    def generate_booking_pitch(self, wrestler1="", wrestler2=""):
        return (f"{self.personality.get_greeting()}\n\n"
                f"{self.personality.get_booking_suggestion(wrestler1, wrestler2)}\n\n"
                f"{self.personality.get_sign_off()}")

    def generate_mood_message(self):
        return self.voice.generate_mood_message()

    def get_director_info(self):
        return {
            "name": self.personality.get_name(),
            "icon": self.personality.get_icon(),
            "color": self.personality.get_color(),
            "description": self.personality.get_description(),
            "mood": self.personality.get_mood_display(),
            "favorite_wrestler": self.personality.favorite_wrestler,
            "weeks_active": self.weeks_active,
            "shows_directed": self.shows_directed,
            "creative_control": self.personality.creative_control_level.value,
            "chaos_factor": f"{self.personality.get_chaos_factor() * 100:.0f}%",
        }

    def to_dict(self):
        return {
            "personality": self.personality.to_dict(),
            "creative_control_enabled": self.creative_control_enabled,
            "weeks_active": self.weeks_active, "shows_directed": self.shows_directed,
            "last_show_rating": self.last_show_rating,
            "consecutive_bad_shows": self.consecutive_bad_shows,
            "consecutive_good_shows": self.consecutive_good_shows,
            "active_events": [e.to_dict() for e in self.active_events if hasattr(e, 'to_dict')],
            "resolved_events": [e.to_dict() for e in self.resolved_events[-20:] if hasattr(e, 'to_dict')],
            "event_cooldowns": self.event_cooldowns,
            "recent_matches": self.recent_matches[-30:],
            "wrestler_push_list": self.wrestler_push_list,
            "wrestler_depush_list": self.wrestler_depush_list,
            "accepted_suggestions": self.accepted_suggestions,
            "rejected_suggestions": self.rejected_suggestions,
        }

    @classmethod
    def from_dict(cls, data):
        director = cls(creative_control_enabled=data.get("creative_control_enabled", False))
        if "personality" in data:
            director.personality = PersonalityManager.from_dict(data["personality"])
            director.voice = VoiceEngine(director.personality)
        director.weeks_active = data.get("weeks_active", 0)
        director.shows_directed = data.get("shows_directed", 0)
        director.last_show_rating = data.get("last_show_rating", 0.0)
        director.consecutive_bad_shows = data.get("consecutive_bad_shows", 0)
        director.consecutive_good_shows = data.get("consecutive_good_shows", 0)
        director.event_cooldowns = data.get("event_cooldowns", {})
        director.recent_matches = data.get("recent_matches", [])
        director.wrestler_push_list = data.get("wrestler_push_list", [])
        director.wrestler_depush_list = data.get("wrestler_depush_list", [])
        director.accepted_suggestions = data.get("accepted_suggestions", 0)
        director.rejected_suggestions = data.get("rejected_suggestions", 0)
        for ed in data.get("active_events", []):
            try:
                director.active_events.append(SimpleEvent.from_dict(ed))
            except Exception:
                pass
        for ed in data.get("resolved_events", []):
            try:
                e = SimpleEvent.from_dict(ed)
                e.resolved = True
                director.resolved_events.append(e)
            except Exception:
                pass
        return director