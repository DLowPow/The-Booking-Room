"""
AI Commentary System - Live Show Beat-by-Beat Commentary
Generates dynamic commentary for matches with personality voice
Pivots to storyline scripts when active rivalries are detected
Powers the Watch Live Show feature
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ==================== COMMENTARY TYPES ====================

class CommentarySpeaker(Enum):
    PLAY_BY_PLAY = "Play-by-Play"
    COLOR = "Color Commentary"
    BACKSTAGE = "Backstage"
    RING_ANNOUNCER = "Ring Announcer"
    AI_DIRECTOR = "AI Director"
    CROWD = "Crowd Reaction"


class BeatType(Enum):
    INTRO = "intro"
    ENTRANCE = "entrance"
    OPENING = "opening"
    EARLY_ACTION = "early_action"
    MID_MATCH = "mid_match"
    BIG_SPOT = "big_spot"
    NEAR_FALL = "near_fall"
    COMEBACK = "comeback"
    INTERFERENCE = "interference"
    STORYLINE = "storyline"
    FINISH = "finish"
    POST_MATCH = "post_match"
    CROWD_REACTION = "crowd_reaction"


class CrowdReaction(Enum):
    DEAD_SILENT = "Dead Silent"
    POLITE = "Polite Applause"
    INVESTED = "Invested"
    HOT = "Hot Crowd"
    ELECTRIC = "Electric Atmosphere"
    HOSTILE = "Hostile"
    THIS_IS_AWESOME = "This Is Awesome!"
    ONE_MORE_TIME = "One More Time!"


# ==================== COMMENTARY BEAT ====================

@dataclass
class CommentaryBeat:
    """A single commentary moment in a match"""
    speaker: CommentarySpeaker
    text: str
    beat_type: BeatType
    timing: int = 0  # Seconds into match
    intensity: int = 50  # 0-100, affects display style
    is_storyline: bool = False
    storyline_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker.value,
            "text": self.text,
            "beat_type": self.beat_type.value,
            "timing": self.timing,
            "intensity": self.intensity,
            "is_storyline": self.is_storyline,
            "storyline_id": self.storyline_id,
        }


# ==================== MATCH BROADCAST ====================

@dataclass
class MatchBroadcast:
    """Complete commentary feed for a single match"""
    match_index: int
    match_display: str
    pre_match_hype: List[CommentaryBeat] = field(default_factory=list)
    entrances: List[CommentaryBeat] = field(default_factory=list)
    beats: List[CommentaryBeat] = field(default_factory=list)
    post_match: List[CommentaryBeat] = field(default_factory=list)
    storyline_advanced: Optional[str] = None
    storyline_beat_text: str = ""
    crowd_reaction: CrowdReaction = CrowdReaction.INVESTED
    final_rating: float = 0.0

    def get_all_beats(self) -> List[CommentaryBeat]:
        """Get all beats in order for playback"""
        return self.pre_match_hype + self.entrances + self.beats + self.post_match

    def to_dict(self) -> dict:
        return {
            "match_index": self.match_index,
            "match_display": self.match_display,
            "pre_match_hype": [b.to_dict() for b in self.pre_match_hype],
            "entrances": [b.to_dict() for b in self.entrances],
            "beats": [b.to_dict() for b in self.beats],
            "post_match": [b.to_dict() for b in self.post_match],
            "storyline_advanced": self.storyline_advanced,
            "storyline_beat_text": self.storyline_beat_text,
            "crowd_reaction": self.crowd_reaction.value,
            "final_rating": self.final_rating,
        }


# ==================== SHOW BROADCAST ====================

@dataclass
class ShowBroadcast:
    """Complete commentary feed for an entire show"""
    show_name: str
    venue: str
    pre_show: List[CommentaryBeat] = field(default_factory=list)
    match_broadcasts: List[MatchBroadcast] = field(default_factory=list)
    backstage_segments: List[CommentaryBeat] = field(default_factory=list)
    post_show: List[CommentaryBeat] = field(default_factory=list)
    overall_rating: float = 0.0
    is_sellout: bool = False

    def to_dict(self) -> dict:
        return {
            "show_name": self.show_name,
            "venue": self.venue,
            "pre_show": [b.to_dict() for b in self.pre_show],
            "match_broadcasts": [m.to_dict() for m in self.match_broadcasts],
            "backstage_segments": [b.to_dict() for b in self.backstage_segments],
            "post_show": [b.to_dict() for b in self.post_show],
            "overall_rating": self.overall_rating,
            "is_sellout": self.is_sellout,
        }


# ==================== GENERIC COMMENTARY TEMPLATES ====================

ENTRANCE_TEMPLATES = [
    "Here comes {wrestler}, making their way to the ring!",
    "The crowd reacts as {wrestler}'s music hits!",
    "{wrestler} is here, and they look focused tonight!",
    "Listen to that reaction for {wrestler}!",
    "{wrestler} steps through the curtain to a {reaction} response!",
]

OPENING_TEMPLATES = [
    "And we are underway! {wrestler1} and {wrestler2} circle each other!",
    "The bell rings! These two are ready to throw down!",
    "Here we go! Lock-up to start the match!",
    "Tentative start as {wrestler1} and {wrestler2} feel each other out!",
    "Quick action right out of the gate!",
]

EARLY_ACTION_TEMPLATES = [
    "Both competitors trading holds, looking for an opening!",
    "{wrestler1} works the arm, controlling the early pace!",
    "Quick exchange of strikes! Both wrestlers showing their skills!",
    "Some chain wrestling here in the early going!",
    "The crowd is into this one already!",
]

MID_MATCH_TEMPLATES = [
    "{wrestler1} is in control now, working over {wrestler2}!",
    "{wrestler2} fighting from underneath, the crowd behind them!",
    "What a sequence! These two are putting on a show!",
    "Back and forth action! Neither wrestler giving an inch!",
    "{wrestler1} with a tactical approach, slowing things down!",
    "The pace picks up! This is what they came to see!",
]

BIG_SPOT_TEMPLATES = [
    "OH MY! {wrestler1} just CRUSHED {wrestler2} with that move!",
    "WHAT A MOVE! The crowd is on their feet!",
    "INCREDIBLE! Did you see that?!",
    "MASSIVE move from {wrestler1}! That had to hurt!",
    "Bone-jarring impact! {wrestler2} is rocked!",
    "BIG SHOT from {wrestler1}! This could be it!",
]

NEAR_FALL_TEMPLATES = [
    "ONE! TWO! NO! {wrestler2} kicks out!",
    "SO CLOSE! That was almost it!",
    "How did {wrestler2} survive that?!",
    "The crowd thought it was over! What a kick out!",
    "ONE! TWO! THR— NO! Shoulder up!",
    "I can't believe {wrestler2} is still in this!",
]

COMEBACK_TEMPLATES = [
    "{wrestler2} fighting back! The crowd is going WILD!",
    "Here comes the comeback! {wrestler2} unloading!",
    "{wrestler2} catching fire! Building momentum!",
    "The crowd is FEEDING {wrestler2}! What a rally!",
    "{wrestler2} won't quit! Look at this fire!",
]

FINISH_TEMPLATES = [
    "ONE! TWO! THREE! {winner} wins it!",
    "It's over! {winner} gets the victory!",
    "{winner} captures the win in {match_type}!",
    "And there it is! {winner} stands tall!",
    "{winner} picks up the W in a hard-fought battle!",
]

CLEAN_FINISH_TEMPLATES = [
    "A clean finish! {winner} earned every bit of that win!",
    "{winner} wins it cleanly in the middle of the ring!",
    "No controversy here — {winner} is the better competitor tonight!",
]

DIRTY_FINISH_TEMPLATES = [
    "Wait a minute! {winner} had their feet on the ropes!",
    "That's not how this should end! Controversial finish!",
    "{winner} stole one tonight! The referee didn't see it!",
    "A tainted victory for {winner}!",
]

POST_MATCH_TEMPLATES = [
    "{winner} celebrates as the crowd shows their appreciation!",
    "What a match! Both competitors gave it their all!",
    "{winner} stands tall, but {loser} put up one heck of a fight!",
    "That was a HELL of a contest! Both wrestlers earned respect tonight!",
]


# ==================== STORYLINE-SPECIFIC TEMPLATES ====================

STORYLINE_OPENING_TEMPLATES = {
    "Personal Rivalry": [
        "These two HATE each other! And tonight, it gets settled!",
        "After weeks of build, {wrestler1} and {wrestler2} finally meet!",
        "The bad blood between {wrestler1} and {wrestler2} boils over tonight!",
        "Personal issues drove this feud — and now they collide!",
    ],
    "Title Chase": [
        "{challenger} has been chasing {champion} for weeks — tonight, the title is on the line!",
        "The pursuit ends here! {challenger} gets their shot at the {title}!",
        "{challenger}'s title journey culminates RIGHT NOW!",
    ],
    "Betrayal": [
        "Three weeks ago, {wrestler1} BETRAYED {wrestler2} — and now they meet face to face!",
        "The betrayal that ROCKED our locker room! Tonight, {wrestler2} gets their hands on {wrestler1}!",
        "{wrestler1} stabbed {wrestler2} in the back — now they pay the price!",
    ],
    "Mentor vs Student": [
        "The student faces the master! {wrestler1} taught {wrestler2} EVERYTHING they know!",
        "It's time for the protégé to step out of the mentor's shadow!",
        "{wrestler1} created {wrestler2} — but tonight, they want to surpass their teacher!",
    ],
    "Grudge Match": [
        "GRUDGE MATCH! No referees can stop this! These two want to HURT each other!",
        "The hatred is REAL! {wrestler1} and {wrestler2} have ONE thing on their minds!",
        "Forget wrestling — tonight is about REVENGE!",
    ],
    "Heel Turn": [
        "Could tonight be the night {wrestler1} shows their true colors?",
        "Something feels different about {wrestler1} tonight... pay attention!",
        "The crowd loves {wrestler1} — but for how much longer?",
    ],
    "Underdog Story": [
        "{wrestler1} the underdog! Facing the much bigger {wrestler2}!",
        "Nobody gives {wrestler1} a chance tonight — but they don't know that!",
        "David vs Goliath! Can {wrestler1} pull off the impossible?!",
    ],
    "Faction War": [
        "FACTION WARFARE! Both stables have skin in this game!",
        "This isn't just personal — it's about TERRITORY!",
        "The eyes of every faction member are on this match!",
    ],
}

STORYLINE_MID_MATCH_TEMPLATES = {
    "Personal Rivalry": [
        "You can FEEL the hatred in every strike!",
        "{wrestler1} isn't wrestling — they're trying to HURT {wrestler2}!",
        "This isn't about winning! This is about PAIN!",
    ],
    "Betrayal": [
        "{wrestler2} has THREE WEEKS of anger to unload! Look at the FIRE!",
        "Every shot {wrestler2} lands is for what {wrestler1} did to them!",
        "{wrestler2} mocking {wrestler1}! Twisting the knife!",
    ],
    "Title Chase": [
        "{challenger} can TASTE the gold! They've worked so hard for this!",
        "{champion} reminding everyone WHY they're the champion!",
        "The {title} is right there! Both warriors fighting for legacy!",
    ],
    "Grudge Match": [
        "This has gone beyond wrestling! It's a STREET FIGHT!",
        "{wrestler1} doesn't care about rules anymore!",
        "The referee has lost ALL control of this match!",
    ],
}

STORYLINE_FINISH_TEMPLATES = {
    "Personal Rivalry": [
        "{winner} gets their REVENGE! But this can't be the end!",
        "It's over... but the war between these two will continue!",
        "{winner} wins the battle — but the war rages on!",
    ],
    "Title Chase": [
        "{winner} CAPTURES THE GOLD! The chase is over! NEW CHAMPION!",
        "After all this time, {winner} achieves their dream!",
        "{winner} loses tonight — but the hunt isn't over!",
    ],
    "Betrayal": [
        "{winner} gets the LAST LAUGH! Justice served!",
        "Wait — {winner} is laughing on the mat! This isn't over!",
        "{winner} wins... but at what cost? This feud has CHANGED them!",
    ],
    "Heel Turn": [
        "WAIT! WHAT?! {winner} just attacked their own ally! HEEL TURN!",
        "{winner} has SHOWN THEIR TRUE COLORS! The crowd is in SHOCK!",
        "TURN! TURN! {winner} just changed everything we thought we knew!",
    ],
}


# ==================== PRE-SHOW & POST-SHOW TEMPLATES ====================

PRE_SHOW_TEMPLATES = [
    "Welcome everyone to {show_name} live from {venue}!",
    "We are LIVE from {venue}! What a card we have for you tonight!",
    "Good evening, wrestling fans! Tonight from {venue}, anything can happen!",
    "{venue} is PACKED tonight! The atmosphere is electric!",
]

POST_SHOW_TEMPLATES = {
    "great_show": [
        "WHAT A SHOW! That was one for the history books!",
        "We may have just witnessed the greatest show this venue has ever seen!",
        "I'm at a LOSS for words! Incredible night of action!",
        "If you weren't here tonight, you missed something SPECIAL!",
    ],
    "good_show": [
        "A great night of wrestling! Thanks for joining us!",
        "Solid show from top to bottom! See you next time!",
        "Quality action throughout! That's professional wrestling!",
    ],
    "average_show": [
        "We had some good moments tonight. Until next time!",
        "Goodnight from {venue}! See you at the next show!",
        "Thanks for watching! Drive home safely!",
    ],
    "bad_show": [
        "Well, that's a wrap on tonight's show...",
        "We've had better nights. But the show must go on!",
        "Thanks for sticking with us through tonight's show...",
    ],
}


# ==================== BACKSTAGE SEGMENT TEMPLATES ====================

BACKSTAGE_SEGMENT_TEMPLATES = [
    "We're getting word of an incident in the back!",
    "Cameras are catching something happening backstage!",
    "Let's go to our backstage interviewer!",
    "Something is happening in the parking lot!",
    "Tension brewing in the locker room!",
]


# ==================== COMMENTARY GENERATOR ====================

class CommentaryGenerator:
    """
    Generates beat-by-beat commentary for matches and shows.
    Pulls from generic templates AND personality voice from AI Director.
    Pivots to storyline-specific scripts when rivalries are detected.
    """

    def __init__(self, ai_director=None, storyline_engine=None):
        self.ai_director = ai_director
        self.storyline_engine = storyline_engine

    # ==================== SHOW BROADCAST GENERATION ====================

    def generate_show_broadcast(
        self,
        show_name: str,
        venue: str,
        match_results: List[Dict],
        is_sellout: bool = False,
        overall_rating: float = 0.0,
    ) -> ShowBroadcast:
        """Generate complete broadcast for a show"""
        broadcast = ShowBroadcast(
            show_name=show_name,
            venue=venue,
            overall_rating=overall_rating,
            is_sellout=is_sellout,
        )

        # Pre-show
        broadcast.pre_show = self._generate_pre_show(show_name, venue, is_sellout)

        # Match broadcasts
        for i, match in enumerate(match_results):
            mb = self.generate_match_broadcast(i, match, is_main_event=(i == len(match_results) - 1))
            broadcast.match_broadcasts.append(mb)

        # Post-show
        broadcast.post_show = self._generate_post_show(venue, overall_rating)

        return broadcast

    def _generate_pre_show(self, show_name: str, venue: str, is_sellout: bool) -> List[CommentaryBeat]:
        """Generate pre-show hype"""
        beats = []

        # Welcome line
        template = random.choice(PRE_SHOW_TEMPLATES)
        text = template.format(show_name=show_name, venue=venue)
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.PLAY_BY_PLAY,
            text=text,
            beat_type=BeatType.INTRO,
            timing=0,
            intensity=60,
        ))

        # AI Director excitement (if applicable)
        if self.ai_director:
            ai_line = self.ai_director.personality.get_excitement()
            if ai_line:
                beats.append(CommentaryBeat(
                    speaker=CommentarySpeaker.AI_DIRECTOR,
                    text=ai_line,
                    beat_type=BeatType.INTRO,
                    timing=2,
                    intensity=70,
                ))

        # Sellout call
        if is_sellout:
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.COLOR,
                text="And we are SOLD OUT tonight! Every seat in the house is filled!",
                beat_type=BeatType.INTRO,
                timing=4,
                intensity=80,
            ))

        return beats

    def _generate_post_show(self, venue: str, overall_rating: float) -> List[CommentaryBeat]:
        """Generate post-show wrap-up"""
        beats = []

        if overall_rating >= 4.0:
            templates = POST_SHOW_TEMPLATES["great_show"]
        elif overall_rating >= 3.0:
            templates = POST_SHOW_TEMPLATES["good_show"]
        elif overall_rating >= 2.0:
            templates = POST_SHOW_TEMPLATES["average_show"]
        else:
            templates = POST_SHOW_TEMPLATES["bad_show"]

        text = random.choice(templates).format(venue=venue)
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.PLAY_BY_PLAY,
            text=text,
            beat_type=BeatType.POST_MATCH,
            timing=0,
            intensity=60,
        ))

        # AI Director sign-off
        if self.ai_director:
            reaction = self.ai_director.personality.get_show_reaction(overall_rating)
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.AI_DIRECTOR,
                text=reaction,
                beat_type=BeatType.POST_MATCH,
                timing=2,
                intensity=65,
            ))

        return beats

    # ==================== MATCH BROADCAST GENERATION ====================

    def generate_match_broadcast(
        self,
        match_index: int,
        match_data: Dict,
        is_main_event: bool = False,
    ) -> MatchBroadcast:
        """Generate full commentary feed for a single match"""

        match_display = match_data.get("match_display", "Match")
        wrestlers = match_data.get("wrestlers", [])
        winner = match_data.get("winner", "")
        loser = match_data.get("loser", "")
        rating = match_data.get("rating", 3.0)
        match_type = match_data.get("match_type", "Singles Match")
        finish_type = match_data.get("finish_type", "pinfall")

        broadcast = MatchBroadcast(
            match_index=match_index,
            match_display=match_display,
            final_rating=rating,
        )

        # Get wrestler names
        wrestler_names = [w if isinstance(w, str) else w.get("name", "") for w in wrestlers]
        w1 = wrestler_names[0] if len(wrestler_names) > 0 else "Wrestler 1"
        w2 = wrestler_names[1] if len(wrestler_names) > 1 else "Wrestler 2"

        # Check for active storyline
        active_storyline = None
        storyline_type_str = ""
        if self.storyline_engine and len(wrestler_names) >= 2:
            storylines = self.storyline_engine.get_storylines_for_match(wrestler_names)
            if storylines:
                active_storyline = storylines[0]
                storyline_type_str = active_storyline.storyline_type.value

        # Determine crowd reaction based on rating
        broadcast.crowd_reaction = self._determine_crowd_reaction(rating, is_main_event)

        # === PRE-MATCH HYPE ===
        broadcast.pre_match_hype = self._generate_pre_match_hype(
            match_display, w1, w2, is_main_event, active_storyline
        )

        # === ENTRANCES ===
        broadcast.entrances = self._generate_entrances(wrestler_names, broadcast.crowd_reaction)

        # === MATCH BEATS ===
        broadcast.beats = self._generate_match_beats(
            w1, w2, winner, loser, rating, match_type, finish_type, active_storyline, is_main_event
        )

        # === POST-MATCH ===
        broadcast.post_match = self._generate_post_match(
            winner, loser, rating, active_storyline, storyline_type_str
        )

        # Mark storyline progression
        if active_storyline:
            broadcast.storyline_advanced = active_storyline.id
            broadcast.storyline_beat_text = self._get_storyline_beat_summary(
                active_storyline, winner, loser
            )

        return broadcast

    def _determine_crowd_reaction(self, rating: float, is_main_event: bool) -> CrowdReaction:
        """Determine how the crowd is reacting"""
        if rating >= 4.5:
            return CrowdReaction.THIS_IS_AWESOME
        elif rating >= 4.0:
            return CrowdReaction.ELECTRIC if is_main_event else CrowdReaction.HOT
        elif rating >= 3.0:
            return CrowdReaction.INVESTED
        elif rating >= 2.0:
            return CrowdReaction.POLITE
        else:
            return CrowdReaction.DEAD_SILENT

    def _generate_pre_match_hype(
        self, match_display: str, w1: str, w2: str,
        is_main_event: bool, storyline=None
    ) -> List[CommentaryBeat]:
        """Generate pre-match commentary"""
        beats = []

        # Storyline-driven opening
        if storyline:
            storyline_type = storyline.storyline_type.value
            templates = STORYLINE_OPENING_TEMPLATES.get(storyline_type, [])
            if templates:
                template = random.choice(templates)
                text = template.format(
                    wrestler1=w1, wrestler2=w2,
                    challenger=w1, champion=w2, title="title"
                )
                beats.append(CommentaryBeat(
                    speaker=CommentarySpeaker.PLAY_BY_PLAY,
                    text=text,
                    beat_type=BeatType.INTRO,
                    timing=0,
                    intensity=80,
                    is_storyline=True,
                    storyline_id=storyline.id,
                ))

                # Heat-based intensity line
                if storyline.heat >= 60:
                    beats.append(CommentaryBeat(
                        speaker=CommentarySpeaker.COLOR,
                        text=f"The heat between these two is OFF THE CHARTS! {storyline.heat}% intensity!",
                        beat_type=BeatType.INTRO,
                        timing=2,
                        intensity=75,
                        is_storyline=True,
                        storyline_id=storyline.id,
                    ))
        else:
            # Generic match intro
            text = f"Up next: {match_display}!"
            if is_main_event:
                text = f"And now, the MAIN EVENT! {match_display}!"
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.RING_ANNOUNCER,
                text=text,
                beat_type=BeatType.INTRO,
                timing=0,
                intensity=70 if is_main_event else 50,
            ))

        return beats

    def _generate_entrances(self, wrestler_names: List[str], crowd_reaction: CrowdReaction) -> List[CommentaryBeat]:
        """Generate entrance commentary"""
        beats = []
        reaction_text = crowd_reaction.value.lower()

        for i, name in enumerate(wrestler_names[:4]):  # Max 4 entrances
            template = random.choice(ENTRANCE_TEMPLATES)
            text = template.format(wrestler=name, reaction=reaction_text)
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.RING_ANNOUNCER,
                text=text,
                beat_type=BeatType.ENTRANCE,
                timing=i * 2,
                intensity=55,
            ))

        return beats

    def _generate_match_beats(
        self, w1: str, w2: str, winner: str, loser: str,
        rating: float, match_type: str, finish_type: str,
        storyline=None, is_main_event: bool = False
    ) -> List[CommentaryBeat]:
        """Generate the main match commentary beats"""
        beats = []
        timing = 0

        # OPENING
        template = random.choice(OPENING_TEMPLATES)
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.PLAY_BY_PLAY,
            text=template.format(wrestler1=w1, wrestler2=w2),
            beat_type=BeatType.OPENING,
            timing=timing,
            intensity=50,
        ))
        timing += 30

        # EARLY ACTION
        template = random.choice(EARLY_ACTION_TEMPLATES)
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.COLOR,
            text=template.format(wrestler1=w1, wrestler2=w2),
            beat_type=BeatType.EARLY_ACTION,
            timing=timing,
            intensity=55,
        ))
        timing += 60

        # MID-MATCH
        template = random.choice(MID_MATCH_TEMPLATES)
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.PLAY_BY_PLAY,
            text=template.format(wrestler1=w1, wrestler2=w2),
            beat_type=BeatType.MID_MATCH,
            timing=timing,
            intensity=60,
        ))
        timing += 60

        # STORYLINE BEAT (if applicable)
        if storyline:
            storyline_type = storyline.storyline_type.value
            templates = STORYLINE_MID_MATCH_TEMPLATES.get(storyline_type, [])
            if templates:
                template = random.choice(templates)
                text = template.format(
                    wrestler1=w1, wrestler2=w2,
                    challenger=w1, champion=w2, title="title"
                )
                beats.append(CommentaryBeat(
                    speaker=CommentarySpeaker.COLOR,
                    text=text,
                    beat_type=BeatType.STORYLINE,
                    timing=timing,
                    intensity=80,
                    is_storyline=True,
                    storyline_id=storyline.id,
                ))
                timing += 30

        # BIG SPOT (if rating is good enough)
        if rating >= 3.0:
            template = random.choice(BIG_SPOT_TEMPLATES)
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.PLAY_BY_PLAY,
                text=template.format(wrestler1=w1, wrestler2=w2),
                beat_type=BeatType.BIG_SPOT,
                timing=timing,
                intensity=85,
            ))
            timing += 30

        # NEAR FALL (if rating is good)
        if rating >= 3.5:
            template = random.choice(NEAR_FALL_TEMPLATES)
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.COLOR,
                text=template.format(wrestler1=w1, wrestler2=w2),
                beat_type=BeatType.NEAR_FALL,
                timing=timing,
                intensity=88,
            ))
            timing += 30

        # COMEBACK (for great matches)
        if rating >= 4.0:
            template = random.choice(COMEBACK_TEMPLATES)
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.PLAY_BY_PLAY,
                text=template.format(wrestler1=w1, wrestler2=w2),
                beat_type=BeatType.COMEBACK,
                timing=timing,
                intensity=90,
            ))
            timing += 30

        # ANOTHER NEAR FALL for 5-star matches
        if rating >= 4.5:
            beats.append(CommentaryBeat(
                speaker=CommentarySpeaker.CROWD,
                text="THIS IS AWESOME! THIS IS AWESOME!",
                beat_type=BeatType.CROWD_REACTION,
                timing=timing,
                intensity=95,
            ))
            timing += 15

        # FINISH
        template = random.choice(FINISH_TEMPLATES)
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.PLAY_BY_PLAY,
            text=template.format(winner=winner or w1, match_type=match_type),
            beat_type=BeatType.FINISH,
            timing=timing,
            intensity=95,
        ))

        # Storyline finish line (if applicable)
        if storyline:
            storyline_type = storyline.storyline_type.value
            templates = STORYLINE_FINISH_TEMPLATES.get(storyline_type, [])
            if templates:
                template = random.choice(templates)
                text = template.format(
                    winner=winner or w1, loser=loser or w2,
                    wrestler1=w1, wrestler2=w2,
                    challenger=w1, champion=w2, title="title"
                )
                beats.append(CommentaryBeat(
                    speaker=CommentarySpeaker.COLOR,
                    text=text,
                    beat_type=BeatType.FINISH,
                    timing=timing + 5,
                    intensity=90,
                    is_storyline=True,
                    storyline_id=storyline.id,
                ))

        return beats

    def _generate_post_match(
        self, winner: str, loser: str, rating: float,
        storyline=None, storyline_type_str: str = ""
    ) -> List[CommentaryBeat]:
        """Generate post-match commentary"""
        beats = []

        # Generic post-match
        template = random.choice(POST_MATCH_TEMPLATES)
        text = template.format(winner=winner or "The winner", loser=loser or "The loser")
        beats.append(CommentaryBeat(
            speaker=CommentarySpeaker.PLAY_BY_PLAY,
            text=text,
            beat_type=BeatType.POST_MATCH,
            timing=0,
            intensity=60,
        ))

        # AI Director reaction (if applicable)
        if self.ai_director and rating >= 4.0:
            ai_line = self.ai_director.personality.get_excitement()
            if ai_line:
                beats.append(CommentaryBeat(
                    speaker=CommentarySpeaker.AI_DIRECTOR,
                    text=ai_line,
                    beat_type=BeatType.POST_MATCH,
                    timing=2,
                    intensity=70,
                ))

        return beats

    def _get_storyline_beat_summary(self, storyline, winner: str, loser: str) -> str:
        """Get a summary of how this match advanced the storyline"""
        if not storyline:
            return ""

        return (
            f"📖 Storyline Update: {storyline.name} | "
            f"Heat: {storyline.heat}% | Stage: {storyline.stage.value} | "
            f"Winner: {winner}"
        )

    # ==================== QUICK SUMMARY MODE ====================

    def generate_quick_summary(self, match_data: Dict) -> str:
        """Generate a brief 2-3 line summary instead of full commentary"""
        winner = match_data.get("winner", "")
        loser = match_data.get("loser", "")
        rating = match_data.get("rating", 3.0)
        match_type = match_data.get("match_type", "Singles Match")

        rating_text = ""
        if rating >= 4.5:
            rating_text = "⭐ INSTANT CLASSIC! "
        elif rating >= 4.0:
            rating_text = "⭐ Great match! "
        elif rating >= 3.0:
            rating_text = "Solid match. "
        elif rating >= 2.0:
            rating_text = "Decent match. "
        else:
            rating_text = "Disappointing. "

        return f"{rating_text}{winner} defeated {loser} in {match_type} ({rating:.1f}⭐)"
