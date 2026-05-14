"""
Living World AI
Weekly heartbeat connecting wrestlers, memories, news, rivals, and inbox.
"""

import random
from ai.memory_core import MemoryCore
from ai.wrestler_mind import WrestlerMindManager


def ensure_living_world_systems(game_state):
    if not hasattr(game_state, "ai_memory") or game_state.ai_memory is None:
        game_state.ai_memory = MemoryCore()
    if not hasattr(game_state, "wrestler_minds") or game_state.wrestler_minds is None:
        game_state.wrestler_minds = WrestlerMindManager()
    if not hasattr(game_state, "living_world_history") or game_state.living_world_history is None:
        game_state.living_world_history = []
    return game_state.ai_memory, game_state.wrestler_minds


def get_booked_wrestler_names(game_state):
    booked = set()
    booked_show = getattr(game_state, "booked_show", None)
    if not booked_show:
        return booked
    card = booked_show.get("card", []) if isinstance(booked_show, dict) else []
    for match in card:
        for key, value in match.items():
            if key.startswith("wrestler") and value:
                booked.add(value)
    return booked


def add_inbox_message(game_state, subject, body, icon="🧠", message_type="ai"):
    promotion = game_state.promotion
    if hasattr(game_state, "inbox") and game_state.inbox:
        try:
            game_state.inbox.add_message(
                sender="Living World AI",
                subject=subject,
                body=body,
                year=getattr(promotion, "current_year", 1),
                month=getattr(promotion, "current_month", 1),
                day=getattr(promotion, "current_day", 1),
                message_type=message_type,
                icon=icon,
            )
            return True
        except Exception as e:
            print(f"Living World inbox error: {e}")
    return False


def generate_wrestler_news(game_state, mind_results, week, year):
    stories = []
    for result in mind_results:
        wrestler = result["wrestler"]
        frustration = result["frustration"]
        poaching_risk = result["poaching_risk"]
        if frustration >= 70:
            stories.append({
                "headline": f"Backstage Concern Growing Around {wrestler}",
                "body": f"Sources close to the locker room claim {wrestler} is becoming increasingly frustrated with their current creative direction.",
                "category": "Rumour Mill",
                "importance": "Notable",
                "sentiment": "negative",
            })
        if poaching_risk >= 70:
            stories.append({
                "headline": f"Rival Promotions Monitoring {wrestler}",
                "body": f"Industry insiders believe rival companies may be keeping a close eye on {wrestler}, especially if their current situation does not improve.",
                "category": "Contract Watch",
                "importance": "Major",
                "sentiment": "negative",
            })
    return stories


def generate_rival_noise(game_state, week, year):
    promotion = game_state.promotion
    level = getattr(game_state.progression, "level", 1) if getattr(game_state, "progression", None) else 1
    stories = []
    chance = min(45, 10 + level)
    if random.randint(1, 100) <= chance:
        rival_names = [
            "Titan Wrestling Federation",
            "Empire Pro Wrestling",
            "Global Wrestling Conglomerate",
            "Underground Wrestling Alliance",
            "Apex Wrestling Entertainment",
        ]
        rival = random.choice(rival_names)
        story_types = [
            {
                "headline": f"{rival} Runs Strong Weekend Show",
                "body": f"{rival} reportedly drew a strong crowd this week, adding pressure to smaller promotions trying to grow their audience.",
                "sentiment": "neutral",
            },
            {
                "headline": f"{rival} Looking To Expand Roster",
                "body": f"Reports suggest {rival} is preparing to scout new talent across the wrestling scene.",
                "sentiment": "negative",
            },
            {
                "headline": f"{rival} Owner Takes Shot At Rising Promotions",
                "body": f"In a recent media appearance, the owner of {rival} claimed too many new companies are trying to buy buzz instead of building stars.",
                "sentiment": "negative",
            },
        ]
        chosen = random.choice(story_types)
        chosen["category"] = "Rival Promotion"
        chosen["importance"] = "Notable"
        stories.append(chosen)
    return stories


def publish_news_to_game(game_state, stories, week, year):
    if not stories:
        return []
    if not hasattr(game_state, "news_feed") or game_state.news_feed is None:
        game_state.news_feed = []
    published = []
    for story in stories:
        article = {
            "headline": story["headline"],
            "body": story["body"],
            "category": story.get("category", "Industry News"),
            "importance": story.get("importance", "Minor"),
            "week": week,
            "year": year,
            "sentiment": story.get("sentiment", "neutral"),
            "source": "Living World AI",
            "icon": "📰",
        }
        game_state.news_feed.insert(0, article)
        published.append(article)
    game_state.news_feed = game_state.news_feed[:100]
    return published


def run_living_world_week(game_state):
    """
    Main weekly AI heartbeat.
    Safe to call from app.py during process_week_advancement.
    """
    promotion = game_state.promotion
    week = getattr(promotion, "current_week", 0)
    year = getattr(promotion, "current_year", 1)
    memory, mind_manager = ensure_living_world_systems(game_state)
    roster = getattr(promotion, "roster", [])
    booked_names = get_booked_wrestler_names(game_state)
    mind_results = mind_manager.weekly_update(roster, booked_names)
    for result in mind_results:
        if result["frustration"] >= 65:
            memory.remember(
                week=week,
                year=year,
                memory_type="wrestler_frustration",
                subject=result["wrestler"],
                description=f"{result['wrestler']} is showing frustration with current booking.",
                importance=result["frustration"],
                emotional_weight=result["frustration"],
                tags=["morale", "creative", "locker_room"],
            )
    wrestler_stories = generate_wrestler_news(game_state, mind_results, week, year)
    rival_stories = generate_rival_noise(game_state, week, year)
    all_stories = wrestler_stories + rival_stories
    published_news = publish_news_to_game(game_state, all_stories, week, year)
    high_risk = [r for r in mind_results if r.get("poaching_risk", 0) >= 70]
    for risk in high_risk[:2]:
        add_inbox_message(
            game_state,
            subject=f"Concern Around {risk['wrestler']}",
            body=(
                f"{risk['wrestler']} may be vulnerable to rival interest.\n\n"
                f"Frustration: {risk['frustration']}/100\n"
                f"Poaching Risk: {risk['poaching_risk']}/100\n\n"
                f"Consider featuring them, opening talks, or giving them a clear creative direction."
            ),
            icon="⚠️",
            message_type="ai",
        )
    summary = {
        "week": week,
        "year": year,
        "wrestler_updates": len(mind_results),
        "news_published": len(published_news),
        "high_poaching_risks": len(high_risk),
    }
    game_state.living_world_history.append(summary)
    game_state.living_world_history = game_state.living_world_history[-52:]
    return summary