"""
AI News Generator - Wrestling industry news feed
Headlines, show recaps, wrestler spotlights, rumours, rival promotion news
Each personality writes news with their own voice and bias
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ==================== NEWS TYPES ====================

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


# ==================== NEWS ARTICLE ====================

@dataclass
class NewsArticle:
    """A single news article in the feed"""
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
    is_player_focused: bool = False  # About player's promotion
    sentiment: str = "neutral"  # positive, neutral, negative
    image_emoji: str = "📰"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "headline": self.headline,
            "body": self.body,
            "category": self.category.value,
            "importance": self.importance.value,
            "week": self.week,
            "year": self.year,
            "author": self.author,
            "related_wrestlers": self.related_wrestlers,
            "related_promotion": self.related_promotion,
            "is_player_focused": self.is_player_focused,
            "sentiment": self.sentiment,
            "image_emoji": self.image_emoji,
            "tags": self.tags,
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
            id=data.get("id", ""),
            headline=data.get("headline", ""),
            body=data.get("body", ""),
            category=cat,
            importance=imp,
            week=data.get("week", 0),
            year=data.get("year", 1),
            author=data.get("author", "Wrestling News Daily"),
            related_wrestlers=data.get("related_wrestlers", []),
            related_promotion=data.get("related_promotion", ""),
            is_player_focused=data.get("is_player_focused", False),
            sentiment=data.get("sentiment", "neutral"),
            image_emoji=data.get("image_emoji", "📰"),
            tags=data.get("tags", []),
        )


# ==================== NEWS AUTHORS ====================

NEWS_AUTHORS = {
    "mainstream": [
        "Wrestling News Daily",
        "The Squared Circle Report",
        "Pro Wrestling Insider",
        "Ringside News",
        "Mat Report Weekly",
    ],
    "tabloid": [
        "Wrestling Gossip",
        "The Backstage Buzz",
        "Locker Room Leak",
        "Hot Tag Tabloid",
        "Kayfabe Killers",
    ],
    "indie": [
        "Indie Wrestling Beat",
        "The Underground Report",
        "Bingo Hall Times",
        "Suplex City Gazette",
    ],
    "international": [
        "Global Grappling News",
        "International Wrestling Wire",
        "World Wrestling Today",
    ],
    "podcast": [
        "Wrestling Observer Podcast",
        "Off The Top Rope Show",
        "Cheap Heat Daily",
    ],
}


# ==================== HEADLINE TEMPLATES ====================

SHOW_RECAP_HEADLINES = {
    "great": [
        "{promotion} DELIVERS Instant Classic at {venue}!",
        "INSTANT CLASSIC: {promotion} Show Stuns Wrestling World",
        "Crowd at {venue} Witnesses Something SPECIAL",
        "{promotion} Continues Hot Streak with Stellar Show",
        "Five Stars Across the Board: {promotion}'s Latest Show Reviewed",
    ],
    "good": [
        "{promotion} Delivers Solid Night at {venue}",
        "Quality Wrestling on Display at {promotion}",
        "{promotion} Show Receives Positive Reviews",
        "Strong Night for {promotion} at {venue}",
    ],
    "average": [
        "{promotion} Show Has Its Moments But Falls Short",
        "Mixed Reviews for {promotion}'s Latest Effort",
        "{promotion} Needs More to Stand Out",
        "Inconsistent Night for {promotion}",
    ],
    "bad": [
        "{promotion} Show Disappoints at {venue}",
        "Critics Slam {promotion} for Latest Show",
        "Rough Night for {promotion} as Show Bombs",
        "{promotion} Show Falls Flat",
    ],
    "terrible": [
        "DISASTER: {promotion} Show Branded Worst of the Year",
        "{promotion} Show is a TRAINWRECK",
        "Fans Demand Refunds After {promotion} Disaster",
        "{promotion} Hits Rock Bottom with Latest Show",
    ],
}

WRESTLER_SPOTLIGHT_HEADLINES = [
    "Spotlight: The Rise of {wrestler}",
    "{wrestler} — The Future of {promotion}?",
    "INTERVIEW: {wrestler} Opens Up About Their Career",
    "{wrestler}: From Indie Darling to Main Event Player",
    "Behind the Curtain: A Day in the Life of {wrestler}",
    "Why {wrestler} is Wrestling's Most Underrated Star",
    "EXCLUSIVE: {wrestler} Talks Future Plans",
    "{wrestler}'s Journey to the Top",
]

RUMOUR_HEADLINES = [
    "RUMOUR: {wrestler} Considering Departure?",
    "Backstage Buzz: Tension Between {wrestler1} and {wrestler2}?",
    "WHISPERS: Major Title Change Coming Soon?",
    "RUMOUR MILL: {wrestler} Linked to Surprise Return",
    "Sources Say: Big Changes Coming to {promotion}",
    "BUZZ: {wrestler} Reportedly Unhappy with Booking",
    "WHISPERS: New Faction Forming in {promotion}?",
    "RUMOUR: {wrestler} Approaching Free Agency",
    "BACKSTAGE: Was {wrestler}'s Loss Really Planned?",
]

TITLE_HEADLINES = {
    "title_change": [
        "AND NEW! {winner} Captures the {title}!",
        "TITLE CHANGE! {winner} Defeats {loser} for {title}",
        "HISTORY MADE: {winner} is Your New {title}",
        "End of an Era: {loser} Loses {title} to {winner}",
        "SHOCK WIN: {winner} Captures {title}",
    ],
    "title_defense": [
        "{champion} Retains {title} in Hard-Fought Battle",
        "Still Champion: {champion} Survives {challenger}",
        "{champion} Continues Dominant Reign as {title}",
        "DEFENSE: {champion} Keeps {title} Against {challenger}",
    ],
    "title_vacated": [
        "{title} VACATED — Tournament to Crown New Champion?",
        "BREAKING: {title} Held Up Following Controversy",
        "What's Next for the {title}? Title Now Vacant",
    ],
}

INJURY_HEADLINES = [
    "INJURY REPORT: {wrestler} Sidelined with {injury}",
    "BAD NEWS: {wrestler} Out {weeks} Weeks with Injury",
    "MEDICAL UPDATE: {wrestler} Suffers {injury}",
    "{wrestler} Goes Down — Injury Diagnosis Revealed",
    "Setback for {wrestler} as Injury Forces Time Off",
]

SIGNING_HEADLINES = [
    "BREAKING: {wrestler} Signs with {promotion}!",
    "WELCOME: {wrestler} Joins the {promotion} Roster",
    "SIGNING: {promotion} Adds {wrestler} to Their Ranks",
    "{wrestler} Officially With {promotion} — Effective Immediately",
    "MAJOR SIGNING: {wrestler} Inks Deal with {promotion}",
]

PPV_PREVIEW_HEADLINES = [
    "PPV PREVIEW: {promotion} Set for Massive {show_name}",
    "What to Expect from {promotion}'s {show_name}",
    "PPV PREDICTIONS: Who Wins at {show_name}?",
    "{show_name} Preview: Card Breakdown and Predictions",
    "All Eyes on {promotion} for Upcoming {show_name}",
]

INDUSTRY_HEADLINES = [
    "Industry Report: Wrestling Business Continues to Grow",
    "ANALYSIS: The State of Independent Wrestling",
    "Where Is Wrestling Heading? Industry Experts Weigh In",
    "Year in Review: Wrestling's Biggest Stories",
    "Industry Insiders Discuss Future of the Business",
]

EDITORIAL_HEADLINES = [
    "EDITORIAL: Why {wrestler} Should Be the Top Star",
    "OPINION: The Problem with Modern Wrestling",
    "EDITORIAL: {promotion} Has Found Its Identity",
    "OPINION: Why Long Title Reigns Still Matter",
    "COLUMN: The Art of Slow-Burn Storytelling",
]

SCANDAL_HEADLINES = [
    "BREAKING: {wrestler} at Center of Controversy",
    "SCANDAL: {wrestler} Under Fire After Recent Incident",
    "DRAMA: {wrestler} in Hot Water Following {event}",
    "{wrestler} Issues Statement After Backlash",
]

SOCIAL_MEDIA_HEADLINES = [
    "VIRAL: {wrestler}'s Tweet Has Wrestling Twitter Talking",
    "BUZZ: {wrestler} Trending After {event}",
    "SOCIAL MEDIA: {wrestler}'s Post Goes VIRAL",
    "TWITTER WAR: {wrestler1} and {wrestler2} Trade Shots Online",
]


# ==================== ARTICLE BODY TEMPLATES ====================

SHOW_RECAP_BODIES = {
    "great": [
        "{promotion} put on a show for the ages tonight at {venue}. From bell to bell, this was an absolute clinic in professional wrestling. The {attendance:,} fans in attendance will be talking about this one for weeks. Average match rating: {rating:.2f} stars.",
        "What can be said about {promotion}'s latest effort that hasn't already been said? This was MAGIC. {venue} was rocking from start to finish, with {attendance:,} fans witnessing some of the best wrestling of the year. Rating: {rating:.2f}⭐.",
        "If you missed {promotion} tonight, you missed something special. {attendance:,} fans packed {venue} and got everything they paid for and more. The {rating:.2f}-star average rating tells the story.",
    ],
    "good": [
        "{promotion} delivered a quality show at {venue} tonight. {attendance:,} fans saw some good wrestling and went home happy. With a {rating:.2f}-star average, this was a solid night.",
        "Solid work from {promotion} tonight. The {attendance:,}-strong crowd at {venue} got their money's worth from a {rating:.2f}-star show.",
        "{promotion} continues to build momentum with another strong outing. Tonight's show at {venue} drew {attendance:,} fans and earned a {rating:.2f}-star average rating.",
    ],
    "average": [
        "{promotion}'s latest show was a mixed bag. While there were some highlights, the overall product at {venue} left some fans wanting more. Final rating: {rating:.2f}⭐.",
        "An average night for {promotion} as the {attendance:,} fans at {venue} witnessed an inconsistent show. With a {rating:.2f}-star rating, there's clearly room for improvement.",
    ],
    "bad": [
        "Tough night for {promotion} as the show at {venue} failed to deliver. The {attendance:,} fans in attendance were less than impressed. Average rating: a disappointing {rating:.2f} stars.",
        "{promotion} stumbled hard tonight. From booking decisions to in-ring action, almost nothing clicked at {venue}. {rating:.2f}⭐ doesn't lie.",
    ],
    "terrible": [
        "It was a disaster of epic proportions for {promotion} tonight. {venue} hosted what may go down as one of the worst shows in recent memory. The {rating:.2f}-star rating somehow feels generous.",
        "Where to even begin with this trainwreck? {promotion}'s show at {venue} was an unmitigated disaster. The {attendance:,} fans deserved better than this {rating:.2f}-star debacle.",
    ],
}

RUMOUR_BODIES = [
    "Multiple sources are reporting that {wrestler} may be considering their future with {promotion}. While nothing is confirmed, the situation appears to be developing.",
    "Whispers from backstage suggest something is brewing involving {wrestler}. Take this with a grain of salt, but the rumour mill is churning.",
    "We're hearing through the grapevine that {wrestler}'s situation may be more complicated than it appears. Keep an eye on this one.",
    "Insider sources have revealed potential drama surrounding {wrestler}. The story is still developing.",
    "BREAKING: According to multiple wrestling insiders, big changes may be on the horizon. {wrestler} is reportedly at the center of it.",
]

WRESTLER_SPOTLIGHT_BODIES = [
    "{wrestler} has been turning heads in {promotion} lately. Their unique style and undeniable charisma have made them a fan favorite. With a record of {wins} wins, the future looks bright.",
    "There's something special about {wrestler}. Whether it's their in-ring work, their promo skills, or their connection with the crowd, they have all the tools to be a top star in {promotion}.",
    "Few wrestlers in {promotion} have shown the growth that {wrestler} has displayed recently. From rookie to potential main eventer, the journey has been remarkable.",
    "{wrestler} continues to be one of {promotion}'s most consistent performers. Match after match, they deliver — and the fans have noticed.",
]

INDUSTRY_BODIES = [
    "The wrestling industry continues to evolve in exciting ways. With more promotions emerging and talent moving freely, the landscape has never been more competitive.",
    "Industry analysts are pointing to several trends shaping professional wrestling. Streaming deals, social media engagement, and indie crossovers are all changing the game.",
    "What does the future of wrestling look like? Experts are divided, but one thing is clear: the next few years will be pivotal for the industry.",
]


# ==================== NEWS GENERATOR ====================

class NewsGenerator:
    """
    AI-driven news feed generator.
    Creates headlines, articles, rumours, and editorials based on game state,
    recent events, and AI Director personality.
    """

    def __init__(self, ai_director=None, storyline_engine=None):
        self.ai_director = ai_director
        self.storyline_engine = storyline_engine
        self.articles: List[NewsArticle] = []
        self.next_id: int = 1

    # ==================== ARTICLE CREATION ====================

    def _next_article_id(self) -> str:
        article_id = f"news_{self.next_id}"
        self.next_id += 1
        return article_id

    def _pick_author(self, category: NewsCategory) -> str:
        """Pick an author based on news category"""
        if category in [NewsCategory.RUMOUR, NewsCategory.SCANDAL, NewsCategory.SOCIAL_MEDIA]:
            return random.choice(NEWS_AUTHORS["tabloid"])
        elif category == NewsCategory.RIVAL_PROMOTION:
            return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["international"])
        elif category == NewsCategory.EDITORIAL:
            return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["podcast"])
        elif category == NewsCategory.INDUSTRY:
            return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["podcast"])
        else:
            return random.choice(NEWS_AUTHORS["mainstream"] + NEWS_AUTHORS["indie"])

    # ==================== SHOW RECAP NEWS ====================

    def generate_show_recap(
        self,
        promotion_name: str,
        venue: str,
        attendance: int,
        rating: float,
        week: int,
        year: int,
        is_sellout: bool = False,
    ) -> NewsArticle:
        """Generate a news article recapping a show"""

        if rating >= 4.5:
            tier = "great"
            importance = NewsImportance.MAJOR
            sentiment = "positive"
            emoji = "⭐"
        elif rating >= 3.5:
            tier = "good"
            importance = NewsImportance.NOTABLE
            sentiment = "positive"
            emoji = "📺"
        elif rating >= 2.5:
            tier = "average"
            importance = NewsImportance.MINOR
            sentiment = "neutral"
            emoji = "📰"
        elif rating >= 1.5:
            tier = "bad"
            importance = NewsImportance.NOTABLE
            sentiment = "negative"
            emoji = "📉"
        else:
            tier = "terrible"
            importance = NewsImportance.MAJOR
            sentiment = "negative"
            emoji = "💀"

        headline = random.choice(SHOW_RECAP_HEADLINES[tier]).format(
            promotion=promotion_name, venue=venue
        )

        body = random.choice(SHOW_RECAP_BODIES[tier]).format(
            promotion=promotion_name, venue=venue,
            attendance=attendance, rating=rating,
        )

        if is_sellout:
            body += f"\n\nThe show was a complete SELLOUT, with every seat filled at {venue}."

        # Add AI Director quote if available
        if self.ai_director:
            ai_reaction = self.ai_director.personality.get_show_reaction(rating)
            body += f"\n\n\"{ai_reaction}\" — {self.ai_director.personality.get_name()}"

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.SHOW_RECAP,
            importance=importance,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.SHOW_RECAP),
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment=sentiment,
            image_emoji=emoji,
            tags=["show_recap", tier],
        )
        self.articles.append(article)
        return article

    # ==================== TITLE NEWS ====================

    def generate_title_change(
        self,
        winner: str,
        loser: str,
        title: str,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate news about a title change"""
        headline = random.choice(TITLE_HEADLINES["title_change"]).format(
            winner=winner, loser=loser, title=title
        )

        body = (
            f"In a moment that will be remembered, {winner} has captured the {title} from {loser} "
            f"in {promotion_name}. This title change shakes up the championship landscape and "
            f"opens up a world of new possibilities for the division.\n\n"
            f"What's next for the new champion? And how will {loser} respond to losing the gold?"
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.TITLE_NEWS,
            importance=NewsImportance.MAJOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.TITLE_NEWS),
            related_wrestlers=[winner, loser],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="positive",
            image_emoji="🏆",
            tags=["title_change", "championship"],
        )
        self.articles.append(article)
        return article

    def generate_title_defense(
        self,
        champion: str,
        challenger: str,
        title: str,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate news about a successful title defense"""
        headline = random.choice(TITLE_HEADLINES["title_defense"]).format(
            champion=champion, challenger=challenger, title=title
        )

        body = (
            f"{champion} has once again proven why they are the {title}. In a hard-fought battle "
            f"against {challenger}, the champion retained their gold and continues their reign. "
            f"The legacy of this title continues to grow with every defense."
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.TITLE_NEWS,
            importance=NewsImportance.NOTABLE,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.TITLE_NEWS),
            related_wrestlers=[champion, challenger],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="positive",
            image_emoji="🏆",
            tags=["title_defense", "championship"],
        )
        self.articles.append(article)
        return article

    # ==================== SIGNING NEWS ====================

    def generate_signing_news(
        self,
        wrestler: str,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate news about a wrestler signing"""
        headline = random.choice(SIGNING_HEADLINES).format(
            wrestler=wrestler, promotion=promotion_name
        )

        body = (
            f"{promotion_name} has officially signed {wrestler}, adding fresh talent to the roster. "
            f"This signing represents another step forward for {promotion_name} as they continue "
            f"to build their stable of talent.\n\n"
            f"Fans are already speculating about who {wrestler} might face in their debut match."
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.SIGNING,
            importance=NewsImportance.NOTABLE,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.SIGNING),
            related_wrestlers=[wrestler],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="positive",
            image_emoji="✍️",
            tags=["signing", "roster"],
        )
        self.articles.append(article)
        return article

    # ==================== INJURY NEWS ====================

    def generate_injury_news(
        self,
        wrestler: str,
        injury: str,
        weeks: int,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate news about a wrestler injury"""
        headline = random.choice(INJURY_HEADLINES).format(
            wrestler=wrestler, injury=injury, weeks=weeks
        )

        body = (
            f"Bad news for {promotion_name} fans: {wrestler} has suffered a {injury} and will be "
            f"out of action for an estimated {weeks} weeks. The injury occurred during recent "
            f"in-ring action.\n\n"
            f"We wish {wrestler} a speedy recovery and look forward to their return to the ring."
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.INJURY_REPORT,
            importance=NewsImportance.NOTABLE,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.INJURY_REPORT),
            related_wrestlers=[wrestler],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="negative",
            image_emoji="🏥",
            tags=["injury", "medical"],
        )
        self.articles.append(article)
        return article

    # ==================== WRESTLER SPOTLIGHT ====================

    def generate_wrestler_spotlight(
        self,
        wrestler_data: Dict,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate a spotlight article on a wrestler"""
        wrestler = wrestler_data.get("name", "Wrestler")
        wins = wrestler_data.get("wins", 0)
        popularity = wrestler_data.get("popularity", 30)

        headline = random.choice(WRESTLER_SPOTLIGHT_HEADLINES).format(
            wrestler=wrestler, promotion=promotion_name
        )

        body = random.choice(WRESTLER_SPOTLIGHT_BODIES).format(
            wrestler=wrestler, promotion=promotion_name, wins=wins
        )

        if popularity >= 60:
            body += f"\n\nWith a popularity rating of {popularity}, {wrestler} has become one of the most beloved figures in {promotion_name}."
        elif popularity >= 40:
            body += f"\n\n{wrestler} continues to build their fan base and momentum in {promotion_name}."

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.WRESTLER_SPOTLIGHT,
            importance=NewsImportance.MINOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.WRESTLER_SPOTLIGHT),
            related_wrestlers=[wrestler],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="positive",
            image_emoji="🌟",
            tags=["spotlight", "feature"],
        )
        self.articles.append(article)
        return article

    # ==================== RUMOUR NEWS ====================

    def generate_rumour(
        self,
        wrestlers: List[str],
        promotion_name: str,
        week: int,
        year: int,
        rumour_type: str = "general",
    ) -> NewsArticle:
        """Generate a rumour article"""
        if not wrestlers:
            return None

        w1 = wrestlers[0]
        w2 = wrestlers[1] if len(wrestlers) > 1 else ""

        headline = random.choice(RUMOUR_HEADLINES).format(
            wrestler=w1, wrestler1=w1, wrestler2=w2, promotion=promotion_name
        )

        body = random.choice(RUMOUR_BODIES).format(
            wrestler=w1, promotion=promotion_name
        )

        body += f"\n\n*This is unconfirmed at this time. Treat as rumour only.*"

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.RUMOUR,
            importance=NewsImportance.MINOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.RUMOUR),
            related_wrestlers=wrestlers[:2],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="neutral",
            image_emoji="👀",
            tags=["rumour", "unconfirmed"],
        )
        self.articles.append(article)
        return article

    # ==================== STORYLINE NEWS ====================

    def generate_storyline_news(
        self,
        storyline,
        promotion_name: str,
        week: int,
        year: int,
    ) -> Optional[NewsArticle]:
        """Generate news about an active storyline"""
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

        body = (
            f"The {sl_type} between {w1} and {w2} in {promotion_name} continues to develop. "
            f"With {len(storyline.matches_in_storyline)} matches between them so far and a heat "
            f"rating of {storyline.heat}/100, this rivalry is becoming one of the must-watch "
            f"storylines in wrestling.\n\n"
            f"Stage: {storyline.stage.value} | Intensity: {storyline.intensity.value}"
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.BREAKING,
            importance=NewsImportance.NOTABLE,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.BREAKING),
            related_wrestlers=[w1, w2],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="neutral",
            image_emoji="🔥",
            tags=["storyline", "feud", sl_type.lower().replace(" ", "_")],
        )
        self.articles.append(article)
        return article

    # ==================== EDITORIAL ====================

    def generate_editorial(
        self,
        topic: str,
        promotion_name: str,
        week: int,
        year: int,
        wrestler: str = "",
    ) -> NewsArticle:
        """Generate an editorial/opinion piece"""
        headline = random.choice(EDITORIAL_HEADLINES).format(
            wrestler=wrestler or "The Top Star", promotion=promotion_name
        )

        bodies = [
            f"Let's be honest — {promotion_name} has been doing some interesting things lately. "
            f"Whether you love it or hate it, the booking decisions are sparking conversation. "
            f"And in wrestling, generating discussion is half the battle.",

            f"There's a reason {promotion_name} has been on people's lips this week. "
            f"From in-ring action to storyline development, they're making moves that demand attention. "
            f"Whether those moves pay off remains to be seen.",

            f"The wrestling world is watching {promotion_name} closely. "
            f"With every show, they're either building toward something special or proving "
            f"that the cynics were right. The next few weeks will tell the tale.",
        ]

        body = random.choice(bodies)

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.EDITORIAL,
            importance=NewsImportance.MINOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.EDITORIAL),
            related_promotion=promotion_name,
            related_wrestlers=[wrestler] if wrestler else [],
            is_player_focused=True,
            sentiment="neutral",
            image_emoji="💭",
            tags=["editorial", "opinion"],
        )
        self.articles.append(article)
        return article

    # ==================== INDUSTRY NEWS ====================

    def generate_industry_news(self, week: int, year: int) -> NewsArticle:
        """Generate generic industry news"""
        headline = random.choice(INDUSTRY_HEADLINES)
        body = random.choice(INDUSTRY_BODIES)

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.INDUSTRY,
            importance=NewsImportance.MINOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.INDUSTRY),
            is_player_focused=False,
            sentiment="neutral",
            image_emoji="📰",
            tags=["industry"],
        )
        self.articles.append(article)
        return article

    # ==================== SCANDAL NEWS ====================

    def generate_scandal(
        self,
        wrestler: str,
        event_description: str,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate scandal news"""
        headline = random.choice(SCANDAL_HEADLINES).format(
            wrestler=wrestler, event=event_description
        )

        body = (
            f"{promotion_name} is dealing with controversy after {wrestler} became the center of "
            f"attention for all the wrong reasons. {event_description}.\n\n"
            f"How {promotion_name} chooses to handle this situation could have lasting implications "
            f"for both {wrestler}'s career and the promotion's reputation."
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.SCANDAL,
            importance=NewsImportance.MAJOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.SCANDAL),
            related_wrestlers=[wrestler],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="negative",
            image_emoji="🚨",
            tags=["scandal", "controversy"],
        )
        self.articles.append(article)
        return article

    # ==================== SOCIAL MEDIA ====================

    def generate_social_media_buzz(
        self,
        wrestler: str,
        event_description: str,
        promotion_name: str,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate social media buzz news"""
        headline = random.choice(SOCIAL_MEDIA_HEADLINES).format(
            wrestler=wrestler, wrestler1=wrestler, wrestler2="Another Star",
            event=event_description,
        )

        body = (
            f"Wrestling Twitter is buzzing this week thanks to {wrestler}. "
            f"{event_description}. The reaction has been swift and varied, with fans "
            f"weighing in on every angle of the story.\n\n"
            f"{promotion_name} hasn't issued an official statement yet, but the social "
            f"media engagement is impossible to ignore."
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.SOCIAL_MEDIA,
            importance=NewsImportance.MINOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.SOCIAL_MEDIA),
            related_wrestlers=[wrestler],
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="neutral",
            image_emoji="📱",
            tags=["social_media", "viral"],
        )
        self.articles.append(article)
        return article

    # ==================== PPV PREVIEW ====================

    def generate_ppv_preview(
        self,
        show_name: str,
        promotion_name: str,
        match_count: int,
        week: int,
        year: int,
    ) -> NewsArticle:
        """Generate a PPV preview article"""
        headline = random.choice(PPV_PREVIEW_HEADLINES).format(
            promotion=promotion_name, show_name=show_name
        )

        body = (
            f"{promotion_name} is gearing up for {show_name}, and anticipation is high. "
            f"With {match_count} matches scheduled, this PPV promises to deliver moments "
            f"that fans will be talking about for weeks.\n\n"
            f"Will championships change hands? Will rivalries finally be settled? "
            f"All eyes are on {promotion_name} for this major event."
        )

        article = NewsArticle(
            id=self._next_article_id(),
            headline=headline,
            body=body,
            category=NewsCategory.PPV_PREVIEW,
            importance=NewsImportance.MAJOR,
            week=week,
            year=year,
            author=self._pick_author(NewsCategory.PPV_PREVIEW),
            related_promotion=promotion_name,
            is_player_focused=True,
            sentiment="positive",
            image_emoji="🎬",
            tags=["ppv", "preview"],
        )
        self.articles.append(article)
        return article

    # ==================== AI-DRIVEN WEEKLY GENERATION ====================

    def generate_weekly_news(
        self,
        roster: List[Dict],
        promotion_name: str,
        week: int,
        year: int,
        chaos_factor: float = 0.3,
    ) -> List[NewsArticle]:
        """AI generates weekly news based on roster and game state"""
        generated = []

        # Base chance of news per week
        news_chance = 0.4 + (chaos_factor * 0.4)

        # Wrestler spotlight (occasional)
        if roster and random.random() < news_chance * 0.3:
            popular_wrestlers = [w for w in roster if w.get("popularity", 0) >= 40]
            if popular_wrestlers:
                wrestler = random.choice(popular_wrestlers)
                generated.append(self.generate_wrestler_spotlight(
                    wrestler, promotion_name, week, year
                ))

        # Rumour (somewhat common)
        if roster and len(roster) >= 2 and random.random() < news_chance * 0.4:
            wrestlers_picked = random.sample(roster, min(2, len(roster)))
            wrestler_names = [w["name"] for w in wrestlers_picked]
            generated.append(self.generate_rumour(
                wrestler_names, promotion_name, week, year
            ))

        # Storyline news
        if self.storyline_engine:
            active_storylines = self.storyline_engine.get_active_storylines()
            for sl in active_storylines:
                if sl.heat >= 50 and random.random() < news_chance * 0.3:
                    article = self.generate_storyline_news(sl, promotion_name, week, year)
                    if article:
                        generated.append(article)

        # Editorial (rare)
        if random.random() < news_chance * 0.15:
            wrestler_name = ""
            if roster:
                wrestler = random.choice(roster)
                wrestler_name = wrestler["name"]
            generated.append(self.generate_editorial(
                "general", promotion_name, week, year, wrestler_name
            ))

        # Industry news (occasional)
        if random.random() < news_chance * 0.2:
            generated.append(self.generate_industry_news(week, year))

        return generated

    # ==================== ARTICLE RETRIEVAL ====================

    def get_recent_articles(self, limit: int = 20) -> List[NewsArticle]:
        """Get most recent articles"""
        sorted_articles = sorted(
            self.articles,
            key=lambda a: (a.year, a.week),
            reverse=True,
        )
        return sorted_articles[:limit]

    def get_articles_by_category(self, category: NewsCategory, limit: int = 10) -> List[NewsArticle]:
        """Get articles filtered by category"""
        filtered = [a for a in self.articles if a.category == category]
        sorted_articles = sorted(filtered, key=lambda a: (a.year, a.week), reverse=True)
        return sorted_articles[:limit]

    def get_articles_about_wrestler(self, wrestler_name: str, limit: int = 10) -> List[NewsArticle]:
        """Get articles mentioning a specific wrestler"""
        filtered = [a for a in self.articles if wrestler_name in a.related_wrestlers]
        sorted_articles = sorted(filtered, key=lambda a: (a.year, a.week), reverse=True)
        return sorted_articles[:limit]

    def get_breaking_news(self) -> List[NewsArticle]:
        """Get major/breaking news"""
        return [
            a for a in self.articles
            if a.importance in [NewsImportance.MAJOR, NewsImportance.BREAKING]
        ][-10:]

    def cleanup_old_articles(self, current_week: int, current_year: int, weeks_to_keep: int = 12):
        """Remove articles older than X weeks"""
        kept = []
        for article in self.articles:
            week_diff = (current_year - article.year) * 52 + (current_week - article.week)
            if week_diff <= weeks_to_keep:
                kept.append(article)
        self.articles = kept

    # ==================== SERIALIZATION ====================

    def to_dict(self) -> dict:
        return {
            "articles": [a.to_dict() for a in self.articles[-100:]],  # Cap at 100 articles
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NewsGenerator":
        gen = cls()
        gen.next_id = data.get("next_id", 1)
        for ad in data.get("articles", []):
            try:
                gen.articles.append(NewsArticle.from_dict(ad))
            except Exception:
                pass
        return gen
