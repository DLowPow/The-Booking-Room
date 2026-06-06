# ai/output.py
"""
Output — The voice of the world.
Consolidates: commentary.py + news_generator.py

Two systems:
  - CommentaryGenerator: beat-by-beat match/show commentary
  - NewsGenerator: industry news feed (recaps, rumours, title news, etc.)

Both preserved with identical public interfaces. This is where the optional
LLM layer will later plug in to rewrite/flavour the generated text.
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==========================================================================
# ============================  COMMENTARY  ================================
# ==========================================================================

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


@dataclass
class CommentaryBeat:
    speaker: CommentarySpeaker
    text: str
    beat_type: BeatType
    timing: int = 0
    intensity: int = 50
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


@dataclass
class MatchBroadcast:
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


@dataclass
class ShowBroadcast:
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


# ---- Commentary templates -----------------------------------------------
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
POST_MATCH_TEMPLATES = [
    "{winner} celebrates as the crowd shows their appreciation!",
    "What a match! Both competitors gave it their all!",
    "{winner} stands tall, but {loser} put up one heck of a fight!",
    "That was a HELL of a contest! Both wrestlers earned respect tonight!",
]

STORYLINE_OPENING_TEMPLATES = {
    "Personal Rivalry": [
        "These two HATE each other! And tonight, it gets settled!",
        "After weeks of build, {wrestler1} and {wrestler2} finally meet!",
        "The bad blood between {wrestler1} and {wrestler2} boils over tonight!",
    ],
    "Title Chase": [
        "{challenger} has been chasing {champion} for weeks — tonight, the title is on the line!",
        "The pursuit ends here! {challenger} gets their shot at the {title}!",
    ],
    "Betrayal": [
        "Three weeks ago, {wrestler1} BETRAYED {wrestler2} — and now they meet face to face!",
        "{wrestler1} stabbed {wrestler2} in the back — now they pay the price!",
    ],
    "Mentor vs Student": [
        "The student faces the master! {wrestler1} taught {wrestler2} EVERYTHING they know!",
        "It's time for the protégé to step out of the mentor's shadow!",
    ],
    "Grudge Match": [
        "GRUDGE MATCH! These two want to HURT each other!",
        "Forget wrestling — tonight is about REVENGE!",
    ],
    "Heel Turn": [
        "Could tonight be the night {wrestler1} shows their true colors?",
        "The crowd loves {wrestler1} — but for how much longer?",
    ],
    "Underdog Story": [
        "{wrestler1} the underdog! Facing the much bigger {wrestler2}!",
        "David vs Goliath! Can {wrestler1} pull off the impossible?!",
    ],
    "Faction War": [
        "FACTION WARFARE! Both stables have skin in this game!",
        "This isn't just personal — it's about TERRITORY!",
    ],
}
STORYLINE_MID_MATCH_TEMPLATES = {
    "Personal Rivalry": [
        "You can FEEL the hatred in every strike!",
        "This isn't about winning! This is about PAIN!",
    ],
    "Betrayal": [
        "{wrestler2} has WEEKS of anger to unload! Look at the FIRE!",
        "Every shot {wrestler2} lands is for what {wrestler1} did to them!",
    ],
    "Title Chase": [
        "{challenger} can TASTE the gold! They've worked so hard for this!",
        "{champion} reminding everyone WHY they're the champion!",
    ],
    "Grudge Match": [
        "This has gone beyond wrestling! It's a STREET FIGHT!",
        "The referee has lost ALL control of this match!",
    ],
}
STORYLINE_FINISH_TEMPLATES = {
    "Personal Rivalry": [
        "{winner} gets their REVENGE! But this can't be the end!",
        "{winner} wins the battle — but the war rages on!",
    ],
    "Title Chase": [
        "{winner} CAPTURES THE GOLD! NEW CHAMPION!",
        "After all this time, {winner} achieves their dream!",
    ],
    "Betrayal": [
        "{winner} gets the LAST LAUGH! Justice served!",
        "{winner} wins... but this feud has CHANGED them!",
    ],
    "Heel Turn": [
        "WAIT! WHAT?! {winner} just attacked their own ally! HEEL TURN!",
        "TURN! TURN! {winner} just changed everything!",
    ],
}

PRE_SHOW_TEMPLATES = [
    "Welcome everyone to {show_name} live from {venue}!",
    "We are LIVE from {venue}! What a card we have for you tonight!",
    "Good evening, wrestling fans! Tonight from {venue}, anything can happen!",
    "{venue} is PACKED tonight! The atmosphere is electric!",
]
POST_SHOW_TEMPLATES = {
    "great_show": [
        "WHAT A SHOW! That was one for the history books!",
        "I'm at a LOSS for words! Incredible night of action!",
    ],
    "good_show": [
        "A great night of wrestling! Thanks for joining us!",
        "Quality action throughout! That's professional wrestling!",
    ],
    "average_show": [
        "We had some good moments tonight. Until next time!",
        "Goodnight from {venue}! See you at the next show!",
    ],
    "bad_show": [
        "Well, that's a wrap on tonight's show...",
        "We've had better nights. But the show must go on!",
    ],
}


class CommentaryGenerator:
    """Generates beat-by-beat commentary for matches and shows."""

    def __init__(self, ai_director=None, storyline_engine=None):
        self.ai_director = ai_director
        self.storyline_engine = storyline_engine

    def generate_show_broadcast(self, show_name, venue, match_results,
                                is_sellout=False, overall_rating=0.0):
        broadcast = ShowBroadcast(show_name=show_name, venue=venue,
                                  overall_rating=overall_rating, is_sellout=is_sellout)
        broadcast.pre_show = self._generate_pre_show(show_name, venue, is_sellout)
        for i, match in enumerate(match_results):
            mb = self.generate_match_broadcast(i, match, is_main_event=(i == len(match_results) - 1))
            broadcast.match_broadcasts.append(mb)
        broadcast.post_show = self._generate_post_show(venue, overall_rating)
        return broadcast

    def _generate_pre_show(self, show_name, venue, is_sellout):
        beats = []
        text = random.choice(PRE_SHOW_TEMPLATES).format(show_name=show_name, venue=venue)
        beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, text, BeatType.INTRO, 0, 60))
        if self.ai_director:
            try:
                ai_line = self.ai_director.personality.get_excitement()
                if ai_line:
                    beats.append(CommentaryBeat(CommentarySpeaker.AI_DIRECTOR, ai_line, BeatType.INTRO, 2, 70))
            except Exception:
                pass
        if is_sellout:
            beats.append(CommentaryBeat(CommentarySpeaker.COLOR,
                "And we are SOLD OUT tonight! Every seat in the house is filled!",
                BeatType.INTRO, 4, 80))
        return beats

    def _generate_post_show(self, venue, overall_rating):
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
        beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, text, BeatType.POST_MATCH, 0, 60))
        if self.ai_director:
            try:
                reaction = self.ai_director.personality.get_show_reaction(overall_rating)
                beats.append(CommentaryBeat(CommentarySpeaker.AI_DIRECTOR, reaction, BeatType.POST_MATCH, 2, 65))
            except Exception:
                pass
        return beats

    def generate_match_broadcast(self, match_index, match_data, is_main_event=False):
        match_display = match_data.get("match_display", "Match")
        wrestlers = match_data.get("wrestlers", [])
        winner = match_data.get("winner", "")
        loser = match_data.get("loser", "")
        rating = match_data.get("rating", 3.0)
        match_type = match_data.get("match_type", "Singles Match")
        finish_type = match_data.get("finish_type", "pinfall")

        broadcast = MatchBroadcast(match_index=match_index, match_display=match_display, final_rating=rating)
        wrestler_names = [w if isinstance(w, str) else w.get("name", "") for w in wrestlers]
        w1 = wrestler_names[0] if len(wrestler_names) > 0 else "Wrestler 1"
        w2 = wrestler_names[1] if len(wrestler_names) > 1 else "Wrestler 2"

        active_storyline = None
        storyline_type_str = ""
        if self.storyline_engine and len(wrestler_names) >= 2:
            try:
                storylines = self.storyline_engine.get_storylines_for_match(wrestler_names)
                if storylines:
                    active_storyline = storylines[0]
                    storyline_type_str = active_storyline.storyline_type.value
            except Exception:
                pass

        broadcast.crowd_reaction = self._determine_crowd_reaction(rating, is_main_event)
        broadcast.pre_match_hype = self._generate_pre_match_hype(match_display, w1, w2, is_main_event, active_storyline)
        broadcast.entrances = self._generate_entrances(wrestler_names, broadcast.crowd_reaction)
        broadcast.beats = self._generate_match_beats(w1, w2, winner, loser, rating, match_type, finish_type, active_storyline, is_main_event)
        broadcast.post_match = self._generate_post_match(winner, loser, rating, active_storyline, storyline_type_str)

        if active_storyline:
            broadcast.storyline_advanced = active_storyline.id
            broadcast.storyline_beat_text = self._get_storyline_beat_summary(active_storyline, winner, loser)
        return broadcast

    def _determine_crowd_reaction(self, rating, is_main_event):
        if rating >= 4.5: return CrowdReaction.THIS_IS_AWESOME
        if rating >= 4.0: return CrowdReaction.ELECTRIC if is_main_event else CrowdReaction.HOT
        if rating >= 3.0: return CrowdReaction.INVESTED
        if rating >= 2.0: return CrowdReaction.POLITE
        return CrowdReaction.DEAD_SILENT

    def _generate_pre_match_hype(self, match_display, w1, w2, is_main_event, storyline=None):
        beats = []
        if storyline:
            templates = STORYLINE_OPENING_TEMPLATES.get(storyline.storyline_type.value, [])
            if templates:
                text = random.choice(templates).format(wrestler1=w1, wrestler2=w2, challenger=w1, champion=w2, title="title")
                beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, text, BeatType.INTRO, 0, 80, True, storyline.id))
                if storyline.heat >= 60:
                    beats.append(CommentaryBeat(CommentarySpeaker.COLOR,
                        f"The heat between these two is OFF THE CHARTS! {storyline.heat}% intensity!",
                        BeatType.INTRO, 2, 75, True, storyline.id))
        else:
            text = f"And now, the MAIN EVENT! {match_display}!" if is_main_event else f"Up next: {match_display}!"
            beats.append(CommentaryBeat(CommentarySpeaker.RING_ANNOUNCER, text, BeatType.INTRO, 0, 70 if is_main_event else 50))
        return beats

    def _generate_entrances(self, wrestler_names, crowd_reaction):
        beats = []
        reaction_text = crowd_reaction.value.lower()
        for i, name in enumerate(wrestler_names[:4]):
            text = random.choice(ENTRANCE_TEMPLATES).format(wrestler=name, reaction=reaction_text)
            beats.append(CommentaryBeat(CommentarySpeaker.RING_ANNOUNCER, text, BeatType.ENTRANCE, i * 2, 55))
        return beats

    def _generate_match_beats(self, w1, w2, winner, loser, rating, match_type, finish_type, storyline=None, is_main_event=False):
        beats = []
        timing = 0
        beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, random.choice(OPENING_TEMPLATES).format(wrestler1=w1, wrestler2=w2), BeatType.OPENING, timing, 50)); timing += 30
        beats.append(CommentaryBeat(CommentarySpeaker.COLOR, random.choice(EARLY_ACTION_TEMPLATES).format(wrestler1=w1, wrestler2=w2), BeatType.EARLY_ACTION, timing, 55)); timing += 60
        beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, random.choice(MID_MATCH_TEMPLATES).format(wrestler1=w1, wrestler2=w2), BeatType.MID_MATCH, timing, 60)); timing += 60
        if storyline:
            templates = STORYLINE_MID_MATCH_TEMPLATES.get(storyline.storyline_type.value, [])
            if templates:
                text = random.choice(templates).format(wrestler1=w1, wrestler2=w2, challenger=w1, champion=w2, title="title")
                beats.append(CommentaryBeat(CommentarySpeaker.COLOR, text, BeatType.STORYLINE, timing, 80, True, storyline.id)); timing += 30
        if rating >= 3.0:
            beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, random.choice(BIG_SPOT_TEMPLATES).format(wrestler1=w1, wrestler2=w2), BeatType.BIG_SPOT, timing, 85)); timing += 30
        if rating >= 3.5:
            beats.append(CommentaryBeat(CommentarySpeaker.COLOR, random.choice(NEAR_FALL_TEMPLATES).format(wrestler1=w1, wrestler2=w2), BeatType.NEAR_FALL, timing, 88)); timing += 30
        if rating >= 4.0:
            beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, random.choice(COMEBACK_TEMPLATES).format(wrestler1=w1, wrestler2=w2), BeatType.COMEBACK, timing, 90)); timing += 30
        if rating >= 4.5:
            beats.append(CommentaryBeat(CommentarySpeaker.CROWD, "THIS IS AWESOME! THIS IS AWESOME!", BeatType.CROWD_REACTION, timing, 95)); timing += 15
        beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, random.choice(FINISH_TEMPLATES).format(winner=winner or w1, match_type=match_type), BeatType.FINISH, timing, 95))
        if storyline:
            templates = STORYLINE_FINISH_TEMPLATES.get(storyline.storyline_type.value, [])
            if templates:
                text = random.choice(templates).format(winner=winner or w1, loser=loser or w2, wrestler1=w1, wrestler2=w2, challenger=w1, champion=w2, title="title")
                beats.append(CommentaryBeat(CommentarySpeaker.COLOR, text, BeatType.FINISH, timing + 5, 90, True, storyline.id))
        return beats

    def _generate_post_match(self, winner, loser, rating, storyline=None, storyline_type_str=""):
        beats = []
        text = random.choice(POST_MATCH_TEMPLATES).format(winner=winner or "The winner", loser=loser or "The loser")
        beats.append(CommentaryBeat(CommentarySpeaker.PLAY_BY_PLAY, text, BeatType.POST_MATCH, 0, 60))
        if self.ai_director and rating >= 4.0:
            try:
                ai_line = self.ai_director.personality.get_excitement()
                if ai_line:
                    beats.append(CommentaryBeat(CommentarySpeaker.AI_DIRECTOR, ai_line, BeatType.POST_MATCH, 2, 70))
            except Exception:
                pass
        return beats

    def _get_storyline_beat_summary(self, storyline, winner, loser):
        if not storyline:
            return ""
        return (f"📖 Storyline Update: {storyline.name} | Heat: {storyline.heat}% | "
                f"Stage: {storyline.stage.value} | Winner: {winner}")

    def generate_quick_summary(self, match_data):
        winner = match_data.get("winner", "")
        loser = match_data.get("loser", "")
        rating = match_data.get("rating", 3.0)
        match_type = match_data.get("match_type", "Singles Match")
        if rating >= 4.5: rating_text = "⭐ INSTANT CLASSIC! "
        elif rating >= 4.0: rating_text = "⭐ Great match! "
        elif rating >= 3.0: rating_text = "Solid match. "
        elif rating >= 2.0: rating_text = "Decent match. "
        else: rating_text = "Disappointing. "
        return f"{rating_text}{winner} defeated {loser} in {match_type} ({rating:.1f}⭐)"


# ==========================================================================
# ============================  NEWS  =====================================
# ==========================================================================

class NewsCategory(Enum):
    BREAKING = "Breaking News"
    SHOW_RECAP = "Show Recap"
    WRESTLER_SPOTLIGHT = "Wrestler Spotlight"
    RUMOUR = "Rumour Mill"
    INDUSTRY = "Industry News"
    RIVAL_PROMOTION = "Rival Promotion"
    TITLE_NEWS = "Championship News"
    INJURY_REPORT = "Injury Report"
    SIGNING = "Signing News"
    EDITORIAL = "Editorial"
    INTERVIEW = "Interview"
    PPV_PREVIEW = "PPV Preview"
    SCANDAL = "Scandal"
    SOCIAL_MEDIA = "Social Media Buzz"
    HISTORICAL = "Looking Back"


class NewsImportance(Enum):
    MINOR = "Minor"
    NOTABLE = "Notable"
    MAJOR = "Major"
    BREAKING = "Breaking"


@dataclass
class NewsArticle:
    id: str
    headline: str
    body: str
    category: NewsCategory
    importance: NewsImportance
    week: int
    year: int
    author: str = "Wrestling News Daily"
    related_wrestlers: List[str] = field(default_factory=list)
    related_promotion: str = ""
    is_player_focused: bool = False
    sentiment: str = "neutral"
    image_emoji: str = "📰"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "headline": self.headline, "body": self.body,
            "category": self.category.value, "importance": self.importance.value,
            "week": self.week, "year": self.year, "author": self.author,
            "related_wrestlers": self.related_wrestlers,
            "related_promotion": self.related_promotion,
            "is_player_focused": self.is_player_focused, "sentiment": self.sentiment,
            "image_emoji": self.image_emoji, "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NewsArticle":
        try:
            cat = NewsCategory(data.get("category", "Industry News"))
        except ValueError:
            cat = NewsCategory.INDUSTRY
        try:
            imp = NewsImportance(data.get("importance", "Minor"))
        except ValueError:
            imp = NewsImportance.MINOR
        return cls(
            id=data.get("id", ""), headline=data.get("headline", ""),
            body=data.get("body", ""), category=cat, importance=imp,
            week=data.get("week", 0), year=data.get("year", 1),
            author=data.get("author", "Wrestling News Daily"),
            related_wrestlers=data.get("related_wrestlers", []),
            related_promotion=data.get("related_promotion", ""),
            is_player_focused=data.get("is_player_focused", False),
            sentiment=data.get("sentiment", "neutral"),
            image_emoji=data.get("image_emoji", "📰"),
            tags=data.get("tags", []),
        )


NEWS_AUTHORS = {
    "mainstream": ["Wrestling News Daily", "The Squared Circle Report", "Pro Wrestling Insider", "Ringside News", "Mat Report Weekly"],
    "tabloid": ["Wrestling Gossip", "The Backstage Buzz", "Locker Room Leak", "Hot Tag Tabloid", "Kayfabe Killers"],
    "indie": ["Indie Wrestling Beat", "The Underground Report", "Bingo Hall Times", "Suplex City Gazette"],
    "international": ["Global Grappling News", "International Wrestling Wire", "World Wrestling Today"],
    "podcast": ["Wrestling Observer Podcast", "Off The Top Rope Show", "Cheap Heat Daily"],
}

SHOW_RECAP_HEADLINES = {
    "great": ["{promotion} DELIVERS Instant Classic at {venue}!", "INSTANT CLASSIC: {promotion} Show Stuns Wrestling World", "{promotion} Continues Hot Streak with Stellar Show"],
    "good": ["{promotion} Delivers Solid Night at {venue}", "Quality Wrestling on Display at {promotion}", "Strong Night for {promotion} at {venue}"],
    "average": ["{promotion} Show Has Its Moments But Falls Short", "Mixed Reviews for {promotion}'s Latest Effort", "Inconsistent Night for {promotion}"],
    "bad": ["{promotion} Show Disappoints at {venue}", "Rough Night for {promotion} as Show Bombs", "{promotion} Show Falls Flat"],
    "terrible": ["DISASTER: {promotion} Show Branded Worst of the Year", "{promotion} Show is a TRAINWRECK", "{promotion} Hits Rock Bottom with Latest Show"],
}
WRESTLER_SPOTLIGHT_HEADLINES = [
    "Spotlight: The Rise of {wrestler}", "{wrestler} — The Future of {promotion}?",
    "{wrestler}: From Indie Darling to Main Event Player", "Why {wrestler} is Wrestling's Most Underrated Star",
    "{wrestler}'s Journey to the Top",
]
RUMOUR_HEADLINES = [
    "RUMOUR: {wrestler} Considering Departure?", "Backstage Buzz: Tension Between {wrestler1} and {wrestler2}?",
    "RUMOUR MILL: {wrestler} Linked to Surprise Return", "BUZZ: {wrestler} Reportedly Unhappy with Booking",
    "RUMOUR: {wrestler} Approaching Free Agency",
]
TITLE_HEADLINES = {
    "title_change": ["AND NEW! {winner} Captures the {title}!", "TITLE CHANGE! {winner} Defeats {loser} for {title}", "SHOCK WIN: {winner} Captures {title}"],
    "title_defense": ["{champion} Retains {title} in Hard-Fought Battle", "Still Champion: {champion} Survives {challenger}", "DEFENSE: {champion} Keeps {title} Against {challenger}"],
    "title_vacated": ["{title} VACATED — Tournament to Crown New Champion?", "BREAKING: {title} Held Up Following Controversy"],
}
INJURY_HEADLINES = [
    "INJURY REPORT: {wrestler} Sidelined with {injury}", "BAD NEWS: {wrestler} Out {weeks} Weeks with Injury",
    "{wrestler} Goes Down — Injury Diagnosis Revealed",
]
SIGNING_HEADLINES = [
    "BREAKING: {wrestler} Signs with {promotion}!", "WELCOME: {wrestler} Joins the {promotion} Roster",
    "MAJOR SIGNING: {wrestler} Inks Deal with {promotion}",
]
PPV_PREVIEW_HEADLINES = [
    "PPV PREVIEW: {promotion} Set for Massive {show_name}", "What to Expect from {promotion}'s {show_name}",
    "{show_name} Preview: Card Breakdown and Predictions",
]
INDUSTRY_HEADLINES = [
    "Industry Report: Wrestling Business Continues to Grow", "ANALYSIS: The State of Independent Wrestling",
    "Year in Review: Wrestling's Biggest Stories",
]
EDITORIAL_HEADLINES = [
    "EDITORIAL: Why {wrestler} Should Be the Top Star", "OPINION: The Problem with Modern Wrestling",
    "EDITORIAL: {promotion} Has Found Its Identity", "COLUMN: The Art of Slow-Burn Storytelling",
]
SCANDAL_HEADLINES = [
    "BREAKING: {wrestler} at Center of Controversy", "SCANDAL: {wrestler} Under Fire After Recent Incident",
    "DRAMA: {wrestler} in Hot Water Following {event}",
]
SOCIAL_MEDIA_HEADLINES = [
    "VIRAL: {wrestler}'s Tweet Has Wrestling Twitter Talking", "BUZZ: {wrestler} Trending After {event}",
    "TWITTER WAR: {wrestler1} and {wrestler2} Trade Shots Online",
]

SHOW_RECAP_BODIES = {
    "great": [
        "{promotion} put on a show for the ages tonight at {venue}. The {attendance:,} fans will be talking about this for weeks. Average match rating: {rating:.2f} stars.",
        "What can be said about {promotion}'s latest effort? This was MAGIC. {attendance:,} fans witnessed some of the best wrestling of the year. Rating: {rating:.2f}⭐.",
    ],
    "good": [
        "{promotion} delivered a quality show at {venue}. {attendance:,} fans went home happy. With a {rating:.2f}-star average, this was a solid night.",
        "Solid work from {promotion}. The {attendance:,}-strong crowd got their money's worth from a {rating:.2f}-star show.",
    ],
    "average": [
        "{promotion}'s latest show was a mixed bag. The product at {venue} left some fans wanting more. Final rating: {rating:.2f}⭐.",
        "An average night for {promotion} as the {attendance:,} fans witnessed an inconsistent show. {rating:.2f}-star rating.",
    ],
    "bad": [
        "Tough night for {promotion} as the show at {venue} failed to deliver. The {attendance:,} fans were less than impressed. Average rating: {rating:.2f} stars.",
        "{promotion} stumbled hard tonight. Almost nothing clicked at {venue}. {rating:.2f}⭐ doesn't lie.",
    ],
    "terrible": [
        "It was a disaster for {promotion} tonight. {venue} hosted one of the worst shows in recent memory. The {rating:.2f}-star rating feels generous.",
        "Where to begin with this trainwreck? {promotion}'s show at {venue} was a debacle. The {attendance:,} fans deserved better than this {rating:.2f}-star mess.",
    ],
}
RUMOUR_BODIES = [
    "Multiple sources are reporting that {wrestler} may be considering their future with {promotion}. Nothing is confirmed.",
    "Whispers from backstage suggest something is brewing involving {wrestler}. Take this with a grain of salt.",
    "Insider sources have revealed potential drama surrounding {wrestler}. The story is still developing.",
]
WRESTLER_SPOTLIGHT_BODIES = [
    "{wrestler} has been turning heads in {promotion} lately. With a record of {wins} wins, the future looks bright.",
    "There's something special about {wrestler}. They have all the tools to be a top star in {promotion}.",
    "{wrestler} continues to be one of {promotion}'s most consistent performers. The fans have noticed.",
]
INDUSTRY_BODIES = [
    "The wrestling industry continues to evolve. With more promotions emerging, the landscape has never been more competitive.",
    "Industry analysts point to several trends shaping wrestling: streaming deals, social media, and indie crossovers.",
]


class NewsGenerator:
    """AI-driven news feed generator."""

    def __init__(self, ai_director=None, storyline_engine=None):
        self.ai_director = ai_director
        self.storyline_engine = storyline_engine
        self.articles: List[NewsArticle] = []
        self.next_id: int = 1

    def _next_article_id(self) -> str:
        article_id = f"news_{self.next_id}"
        self.next_id += 1
        return article_id

    def _pick_author(self, category: NewsCategory) -> str:
        if category in [NewsCategory.RUMOUR, NewsCategory.SCANDAL, NewsCategory.SOCIAL_MEDIA]:
            return random.choice(NEWS_AUTHORS["tabloid"])
        if category == NewsCategory.RIVAL_PROMOTION:
            return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["international"])
        if category in [NewsCategory.EDITORIAL, NewsCategory.INDUSTRY]:
            return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["podcast"])
        return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["indie"])

    def generate_show_recap(self, promotion_name, venue, attendance, rating, week, year, is_sellout=False):
        if rating >= 4.5: tier, importance, sentiment, emoji = "great", NewsImportance.MAJOR, "positive", "⭐"
        elif rating >= 3.5: tier, importance, sentiment, emoji = "good", NewsImportance.NOTABLE, "positive", "📺"
        elif rating >= 2.5: tier, importance, sentiment, emoji = "average", NewsImportance.MINOR, "neutral", "📰"
        elif rating >= 1.5: tier, importance, sentiment, emoji = "bad", NewsImportance.NOTABLE, "negative", "📉"
        else: tier, importance, sentiment, emoji = "terrible", NewsImportance.MAJOR, "negative", "💀"

        headline = random.choice(SHOW_RECAP_HEADLINES[tier]).format(promotion=promotion_name, venue=venue)
        body = random.choice(SHOW_RECAP_BODIES[tier]).format(promotion=promotion_name, venue=venue, attendance=attendance, rating=rating)
        if is_sellout:
            body += f"\n\nThe show was a complete SELLOUT, with every seat filled at {venue}."
        if self.ai_director:
            try:
                ai_reaction = self.ai_director.personality.get_show_reaction(rating)
                body += f"\n\n\"{ai_reaction}\" — {self.ai_director.personality.get_name()}"
            except Exception:
                pass
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.SHOW_RECAP, importance, week, year,
            author=self._pick_author(NewsCategory.SHOW_RECAP), related_promotion=promotion_name,
            is_player_focused=True, sentiment=sentiment, image_emoji=emoji, tags=["show_recap", tier])
        self.articles.append(article)
        return article

    def generate_title_change(self, winner, loser, title, promotion_name, week, year):
        headline = random.choice(TITLE_HEADLINES["title_change"]).format(winner=winner, loser=loser, title=title)
        body = (f"In a moment that will be remembered, {winner} has captured the {title} from {loser} in {promotion_name}. "
                f"What's next for the new champion? And how will {loser} respond?")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.TITLE_NEWS, NewsImportance.MAJOR, week, year,
            author=self._pick_author(NewsCategory.TITLE_NEWS), related_wrestlers=[winner, loser],
            related_promotion=promotion_name, is_player_focused=True, sentiment="positive", image_emoji="🏆", tags=["title_change", "championship"])
        self.articles.append(article)
        return article

    def generate_title_defense(self, champion, challenger, title, promotion_name, week, year):
        headline = random.choice(TITLE_HEADLINES["title_defense"]).format(champion=champion, challenger=challenger, title=title)
        body = (f"{champion} has once again proven why they are the {title}. In a hard-fought battle against {challenger}, "
                f"the champion retained their gold and continues their reign.")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.TITLE_NEWS, NewsImportance.NOTABLE, week, year,
            author=self._pick_author(NewsCategory.TITLE_NEWS), related_wrestlers=[champion, challenger],
            related_promotion=promotion_name, is_player_focused=True, sentiment="positive", image_emoji="🏆", tags=["title_defense", "championship"])
        self.articles.append(article)
        return article

    def generate_signing_news(self, wrestler, promotion_name, week, year):
        headline = random.choice(SIGNING_HEADLINES).format(wrestler=wrestler, promotion=promotion_name)
        body = (f"{promotion_name} has officially signed {wrestler}, adding fresh talent to the roster. "
                f"Fans are speculating about who {wrestler} might face in their debut match.")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.SIGNING, NewsImportance.NOTABLE, week, year,
            author=self._pick_author(NewsCategory.SIGNING), related_wrestlers=[wrestler],
            related_promotion=promotion_name, is_player_focused=True, sentiment="positive", image_emoji="✍️", tags=["signing", "roster"])
        self.articles.append(article)
        return article

    def generate_injury_news(self, wrestler, injury, weeks, promotion_name, week, year):
        headline = random.choice(INJURY_HEADLINES).format(wrestler=wrestler, injury=injury, weeks=weeks)
        body = (f"Bad news for {promotion_name} fans: {wrestler} has suffered a {injury} and will be out for an estimated "
                f"{weeks} weeks. We wish {wrestler} a speedy recovery.")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.INJURY_REPORT, NewsImportance.NOTABLE, week, year,
            author=self._pick_author(NewsCategory.INJURY_REPORT), related_wrestlers=[wrestler],
            related_promotion=promotion_name, is_player_focused=True, sentiment="negative", image_emoji="🏥", tags=["injury", "medical"])
        self.articles.append(article)
        return article

    def generate_wrestler_spotlight(self, wrestler_data, promotion_name, week, year):
        wrestler = wrestler_data.get("name", "Wrestler")
        wins = wrestler_data.get("wins", 0)
        popularity = wrestler_data.get("popularity", 30)
        headline = random.choice(WRESTLER_SPOTLIGHT_HEADLINES).format(wrestler=wrestler, promotion=promotion_name)
        body = random.choice(WRESTLER_SPOTLIGHT_BODIES).format(wrestler=wrestler, promotion=promotion_name, wins=wins)
        if popularity >= 60:
                        body += f"\n\nWith a popularity rating of {popularity}, {wrestler} has become one of the most beloved figures in {promotion_name}."
        elif popularity >= 40:
            body += f"\n\n{wrestler} continues to build their fan base and momentum in {promotion_name}."
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.WRESTLER_SPOTLIGHT, NewsImportance.MINOR, week, year,
            author=self._pick_author(NewsCategory.WRESTLER_SPOTLIGHT), related_wrestlers=[wrestler],
            related_promotion=promotion_name, is_player_focused=True, sentiment="positive", image_emoji="🌟", tags=["spotlight", "feature"])
        self.articles.append(article)
        return article

    def generate_rumour(self, wrestlers, promotion_name, week, year, rumour_type="general"):
        if not wrestlers:
            return None
        w1 = wrestlers[0]
        w2 = wrestlers[1] if len(wrestlers) > 1 else ""
        headline = random.choice(RUMOUR_HEADLINES).format(wrestler=w1, wrestler1=w1, wrestler2=w2, promotion=promotion_name)
        body = random.choice(RUMOUR_BODIES).format(wrestler=w1, promotion=promotion_name)
        body += "\n\n*This is unconfirmed at this time. Treat as rumour only.*"
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.RUMOUR, NewsImportance.MINOR, week, year,
            author=self._pick_author(NewsCategory.RUMOUR), related_wrestlers=wrestlers[:2],
            related_promotion=promotion_name, is_player_focused=True, sentiment="neutral", image_emoji="👀", tags=["rumour", "unconfirmed"])
        self.articles.append(article)
        return article

    def generate_storyline_news(self, storyline, promotion_name, week, year):
        if not storyline or not storyline.is_active:
            return None
        participants = storyline.participants
        if len(participants) < 2:
            return None
        w1, w2 = participants[0], participants[1]
        sl_type = storyline.storyline_type.value
        headline = f"FEUD UPDATE: {w1} vs {w2} Continues to Heat Up"
        if storyline.heat >= 80:
            headline = f"PEAK HEAT: {w1} vs {w2} Reaches Boiling Point!"
        elif storyline.heat >= 60:
            headline = f"FEUD INTENSIFIES: {w1} vs {w2} Building Momentum"
        body = (f"The {sl_type} between {w1} and {w2} in {promotion_name} continues to develop. "
                f"With {len(storyline.matches_in_storyline)} matches between them so far and a heat "
                f"rating of {storyline.heat}/100, this rivalry is becoming one of the must-watch "
                f"storylines in wrestling.\n\nStage: {storyline.stage.value} | Intensity: {storyline.intensity.value}")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.BREAKING, NewsImportance.NOTABLE, week, year,
            author=self._pick_author(NewsCategory.BREAKING), related_wrestlers=[w1, w2],
            related_promotion=promotion_name, is_player_focused=True, sentiment="neutral", image_emoji="🔥",
            tags=["storyline", "feud", sl_type.lower().replace(" ", "_")])
        self.articles.append(article)
        return article

    def generate_editorial(self, topic, promotion_name, week, year, wrestler=""):
        headline = random.choice(EDITORIAL_HEADLINES).format(wrestler=wrestler or "The Top Star", promotion=promotion_name)
        bodies = [
            f"Let's be honest — {promotion_name} has been doing some interesting things lately. "
            f"Whether you love it or hate it, the booking decisions are sparking conversation. "
            f"And in wrestling, generating discussion is half the battle.",
            f"There's a reason {promotion_name} has been on people's lips this week. "
            f"From in-ring action to storyline development, they're making moves that demand attention.",
            f"The wrestling world is watching {promotion_name} closely. "
            f"With every show, they're either building toward something special or proving the cynics right.",
        ]
        body = random.choice(bodies)
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.EDITORIAL, NewsImportance.MINOR, week, year,
            author=self._pick_author(NewsCategory.EDITORIAL), related_promotion=promotion_name,
            related_wrestlers=[wrestler] if wrestler else [], is_player_focused=True,
            sentiment="neutral", image_emoji="💭", tags=["editorial", "opinion"])
        self.articles.append(article)
        return article

    def generate_industry_news(self, week, year):
        headline = random.choice(INDUSTRY_HEADLINES)
        body = random.choice(INDUSTRY_BODIES)
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.INDUSTRY, NewsImportance.MINOR, week, year,
            author=self._pick_author(NewsCategory.INDUSTRY), is_player_focused=False,
            sentiment="neutral", image_emoji="📰", tags=["industry"])
        self.articles.append(article)
        return article

    def generate_scandal(self, wrestler, event_description, promotion_name, week, year):
        headline = random.choice(SCANDAL_HEADLINES).format(wrestler=wrestler, event=event_description)
        body = (f"{promotion_name} is dealing with controversy after {wrestler} became the center of "
                f"attention for all the wrong reasons. {event_description}.\n\n"
                f"How {promotion_name} chooses to handle this could have lasting implications.")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.SCANDAL, NewsImportance.MAJOR, week, year,
            author=self._pick_author(NewsCategory.SCANDAL), related_wrestlers=[wrestler],
            related_promotion=promotion_name, is_player_focused=True, sentiment="negative", image_emoji="🚨",
            tags=["scandal", "controversy"])
        self.articles.append(article)
        return article

    def generate_social_media_buzz(self, wrestler, event_description, promotion_name, week, year):
        headline = random.choice(SOCIAL_MEDIA_HEADLINES).format(
            wrestler=wrestler, wrestler1=wrestler, wrestler2="Another Star", event=event_description)
        body = (f"Wrestling Twitter is buzzing this week thanks to {wrestler}. {event_description}. "
                f"The reaction has been swift and varied.\n\n{promotion_name} hasn't issued an official statement yet.")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.SOCIAL_MEDIA, NewsImportance.MINOR, week, year,
            author=self._pick_author(NewsCategory.SOCIAL_MEDIA), related_wrestlers=[wrestler],
            related_promotion=promotion_name, is_player_focused=True, sentiment="neutral", image_emoji="📱",
            tags=["social_media", "viral"])
        self.articles.append(article)
        return article

    def generate_ppv_preview(self, show_name, promotion_name, match_count, week, year):
        headline = random.choice(PPV_PREVIEW_HEADLINES).format(promotion=promotion_name, show_name=show_name)
        body = (f"{promotion_name} is gearing up for {show_name}, and anticipation is high. "
                f"With {match_count} matches scheduled, this PPV promises big moments.\n\n"
                f"Will championships change hands? All eyes are on {promotion_name}.")
        article = NewsArticle(self._next_article_id(), headline, body, NewsCategory.PPV_PREVIEW, NewsImportance.MAJOR, week, year,
            author=self._pick_author(NewsCategory.PPV_PREVIEW), related_promotion=promotion_name,
            is_player_focused=True, sentiment="positive", image_emoji="🎬", tags=["ppv", "preview"])
        self.articles.append(article)
        return article

    def generate_weekly_news(self, roster, promotion_name, week, year, chaos_factor=0.3):
        generated = []
        news_chance = 0.4 + (chaos_factor * 0.4)
        if roster and random.random() < news_chance * 0.3:
            popular = [w for w in roster if w.get("popularity", 0) >= 40]
            if popular:
                generated.append(self.generate_wrestler_spotlight(random.choice(popular), promotion_name, week, year))
        if roster and len(roster) >= 2 and random.random() < news_chance * 0.4:
            picked = random.sample(roster, min(2, len(roster)))
            generated.append(self.generate_rumour([w["name"] for w in picked], promotion_name, week, year))
        if self.storyline_engine:
            try:
                for sl in self.storyline_engine.get_active_storylines():
                    if sl.heat >= 50 and random.random() < news_chance * 0.3:
                        art = self.generate_storyline_news(sl, promotion_name, week, year)
                        if art:
                            generated.append(art)
            except Exception:
                pass
        if random.random() < news_chance * 0.15:
            wname = random.choice(roster)["name"] if roster else ""
            generated.append(self.generate_editorial("general", promotion_name, week, year, wname))
        if random.random() < news_chance * 0.2:
            generated.append(self.generate_industry_news(week, year))
        return generated

    # ==================== RETRIEVAL ====================

    def get_recent_articles(self, limit=20):
        return sorted(self.articles, key=lambda a: (a.year, a.week), reverse=True)[:limit]

    def get_articles_by_category(self, category, limit=10):
        filtered = [a for a in self.articles if a.category == category]
        return sorted(filtered, key=lambda a: (a.year, a.week), reverse=True)[:limit]

    def get_articles_about_wrestler(self, wrestler_name, limit=10):
        filtered = [a for a in self.articles if wrestler_name in a.related_wrestlers]
        return sorted(filtered, key=lambda a: (a.year, a.week), reverse=True)[:limit]

    def get_breaking_news(self):
        return [a for a in self.articles
                if a.importance in (NewsImportance.MAJOR, NewsImportance.BREAKING)][-10:]

    def cleanup_old_articles(self, current_week, current_year, weeks_to_keep=12):
        kept = []
        for a in self.articles:
            week_diff = (current_year - a.year) * 52 + (current_week - a.week)
            if week_diff <= weeks_to_keep:
                kept.append(a)
        self.articles = kept

    # ==================== SERIALIZATION ====================

    def to_dict(self):
        return {"articles": [a.to_dict() for a in self.articles[-100:]], "next_id": self.next_id}

    @classmethod
    def from_dict(cls, data):
        gen = cls()
        gen.next_id = data.get("next_id", 1)
        for ad in data.get("articles", []):
            try:
                gen.articles.append(NewsArticle.from_dict(ad))
            except Exception:
                pass
        return gen