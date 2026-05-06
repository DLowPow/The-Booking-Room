"""
Weekly Pulse - The Master Orchestrator
The heartbeat of The Booking Room. Called every time the player advances a week
or runs a show. Coordinates ALL systems to keep the wrestling world alive.

This is what makes the world feel ALIVE:
  - AI Director processes mood and generates events
  - Storylines decay and AI proposes new ones
  - Rival promotions run shows, sign talent, raid your roster
  - Training school operates (trainees, coaches, applicants, payroll)
  - News feed populates with weekly articles
  - Quests check progress and award rewards
  - Free agency refreshes
  - Wrestler morale shifts based on bookings
  - Contracts decay, warnings issued
  - Relationship dynamics evolve
"""

import random
from typing import Dict, List, Optional
from datetime import datetime


class WeeklyPulse:
    """
    The master weekly orchestrator.
    Single entry point: pulse.run() processes the entire game world for one week.
    """

    def __init__(self, game_state):
        self.gs = game_state
        self.events_this_week: List[Dict] = []
        self.messages_added: int = 0

    # ==================== MAIN ENTRY POINT ====================

    def run(self, current_week: int, current_year: int) -> Dict:
        """
        Master weekly update. Called by app.py when advancing time.
        Returns a comprehensive result dict for UI feedback.
        """
        result = {
            "week": current_week,
            "year": current_year,
            "ai_events": [],
            "ai_suggestions": [],
            "storyline_updates": [],
            "storyline_beats": [],
            "news_articles": [],
            "rival_activity": {},
            "training_school": {},
            "trainee_applicants": [],
            "coach_pool_refresh": [],
            "quest_updates": [],
            "relationship_changes": [],
            "wrestler_updates": [],
            "free_agent_refresh": [],
            "contract_warnings": [],
            "messages_added": 0,
            "money_changes": {"income": 0, "expenses": 0, "net": 0},
            "highlights": [],  # Notable events for end-of-week summary
        }

        roster_dicts = self._get_roster_dicts()
        budget = getattr(self.gs.promotion, "budget", 0) if self.gs.promotion else 0
        fans = getattr(self.gs.promotion, "fan_base", 0) if self.gs.promotion else 0
        prestige = getattr(self.gs.promotion, "prestige", 1) if self.gs.promotion else 1

        # ===== 1. AI DIRECTOR WEEKLY UPDATE =====
        self._process_ai_director(result, roster_dicts, budget, fans, prestige, current_week)

        # ===== 2. STORYLINE ENGINE =====
        self._process_storylines(result, roster_dicts, current_week, current_year)

        # ===== 3. NEWS GENERATOR =====
        self._process_news(result, roster_dicts, current_week, current_year)

        # ===== 4. RIVAL PROMOTIONS =====
        self._process_rivals(result, roster_dicts, current_week, current_year)

        # ===== 5. TRAINING SCHOOL =====
        self._process_training_school(result, current_week, current_year)

        # ===== 6. QUEST SYSTEM =====
        self._process_quests(result, fans, budget)

        # ===== 7. RELATIONSHIPS =====
        self._process_relationships(result)

        # ===== 8. WRESTLER WEEKLY UPDATES =====
        self._process_wrestlers(result, current_week)

        # ===== 9. FREE AGENT POOL REFRESH =====
        self._process_free_agents(result)

        # ===== 10. INJURY HEALING =====
        self._process_injuries(result)

        # ===== 11. CONTRACT WARNINGS =====
        self._check_contracts(result, current_week)

        # ===== 12. INBOX DELIVERY =====
        self._deliver_inbox_messages(result, current_week, current_year)

        # ===== 13. BUILD HIGHLIGHTS SUMMARY =====
        self._build_highlights(result)

        return result

    # ==================== HELPER: GET ROSTER AS DICTS ====================

    def _get_roster_dicts(self) -> List[Dict]:
        """Convert roster to dict format for AI consumption"""
        if not self.gs or not self.gs.roster:
            return []
        try:
            return self.gs.get_roster_as_dicts()
        except Exception:
            return []

    # ==================== 1. AI DIRECTOR ====================

    def _process_ai_director(self, result, roster_dicts, budget, fans, prestige, current_week):
        if not self.gs.ai_director:
            return

        try:
            ai_result = self.gs.ai_director.process_weekly_update(
                roster=roster_dicts,
                budget=budget,
                fans=fans,
                prestige=prestige,
                current_week=current_week,
            )
            result["ai_events"] = ai_result.get("new_events", [])
            result["ai_suggestions"] = ai_result.get("suggestions", [])

            # Generate AI mood message if noteworthy
            mood_msg = self.gs.ai_director.generate_mood_message()
            if mood_msg and self.gs.inbox:
                try:
                    self.gs.inbox.add_message(
                        sender=self.gs.ai_director.personality.get_name(),
                        subject="Quick Thought",
                        body=mood_msg,
                        icon=self.gs.ai_director.personality.get_icon(),
                        message_type="ai_thought",
                    )
                    self.messages_added += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"[Pulse] AI Director error: {e}")

    # ==================== 2. STORYLINES ====================

    def _process_storylines(self, result, roster_dicts, current_week, current_year):
        if not self.gs.storyline_engine:
            return

        try:
            # Apply weekly heat decay to all active storylines
            self.gs.storyline_engine.weekly_update()

            # AI auto-proposes new storylines based on personality
            if self.gs.ai_director and roster_dicts:
                chaos = self.gs.ai_director.personality.get_chaos_factor()
                personality_name = self.gs.ai_director.personality.get_name()

                new_storyline = self.gs.storyline_engine.ai_propose_storyline(
                    roster=roster_dicts,
                    ai_personality_name=personality_name,
                    chaos_factor=chaos,
                    week=current_week,
                    year=current_year,
                )
                if new_storyline:
                    result["storyline_updates"].append({
                        "type": "proposed",
                        "storyline_id": new_storyline.id,
                        "name": new_storyline.name,
                        "participants": new_storyline.participants,
                        "icon": new_storyline.get_icon(),
                    })
                    result["highlights"].append(
                        f"📖 New storyline pitched: {new_storyline.name}"
                    )

            # Auto-advance storyline beats (drama between matches)
            if self.gs.ai_director:
                chaos = self.gs.ai_director.personality.get_chaos_factor()
                beats = self.gs.storyline_engine.ai_advance_storylines(
                    week=current_week,
                    year=current_year,
                    chaos_factor=chaos,
                )
                result["storyline_beats"] = beats

                # Send beats as inbox messages
                if beats and self.gs.inbox:
                    for beat in beats[:3]:  # Cap at 3 per week to avoid spam
                        try:
                            self.gs.inbox.add_message(
                                sender="Backstage Report",
                                subject=f"📖 {beat.get('storyline_name', 'Storyline Update')}",
                                body=beat.get("description", ""),
                                icon="📖",
                                message_type="storyline_beat",
                            )
                            self.messages_added += 1
                        except Exception:
                            pass
        except Exception as e:
            print(f"[Pulse] Storyline error: {e}")

    # ==================== 3. NEWS ====================

    def _process_news(self, result, roster_dicts, current_week, current_year):
        if not self.gs.news_generator or not self.gs.promotion:
            return

        try:
            chaos = (
                self.gs.ai_director.personality.get_chaos_factor()
                if self.gs.ai_director else 0.3
            )
            articles = self.gs.news_generator.generate_weekly_news(
                roster=roster_dicts,
                promotion_name=self.gs.promotion.name,
                week=current_week,
                year=current_year,
                chaos_factor=chaos,
            )
            result["news_articles"] = [a.headline for a in articles] if articles else []

            if articles:
                result["highlights"].append(
                    f"📰 {len(articles)} new article{'s' if len(articles) > 1 else ''} in the news"
                )
        except Exception as e:
            print(f"[Pulse] News generator error: {e}")

    # ==================== 4. RIVAL PROMOTIONS ====================

    def _process_rivals(self, result, roster_dicts, current_week, current_year):
        if not self.gs.rival_promotions:
            return

        try:
            free_agent_dicts = []
            for w in self.gs.free_agents:
                try:
                    if hasattr(w, "to_dict"):
                        free_agent_dicts.append(w.to_dict())
                except Exception:
                    pass

            prestige = getattr(self.gs.promotion, "prestige", 1) if self.gs.promotion else 1
            fans = getattr(self.gs.promotion, "fan_base", 0) if self.gs.promotion else 0

            rival_result = self.gs.rival_promotions.process_weekly_operations(
                current_week=current_week,
                current_year=current_year,
                player_roster=roster_dicts,
                player_free_agents=free_agent_dicts,
                player_prestige=prestige,
                player_fans=fans,
            )
            result["rival_activity"] = rival_result

            # Build highlights from rival activity
            if rival_result.get("shows_run"):
                result["highlights"].append(
                    f"🏟️ {len(rival_result['shows_run'])} rival show{'s' if len(rival_result['shows_run']) > 1 else ''} ran this week"
                )

            if rival_result.get("raids"):
                for raid in rival_result["raids"]:
                    raid_data = raid.get("raid", {})
                    rival_name = raid.get("rival_name", "A rival")
                    wrestler_name = raid_data.wrestler_name if hasattr(raid_data, "wrestler_name") else "your wrestler"
                    result["highlights"].append(
                        f"🚨 {rival_name} POACHED {wrestler_name} from your roster!"
                    )
                    # Send urgent inbox message
                    if self.gs.inbox:
                        try:
                            self.gs.inbox.add_message(
                                sender="Industry Insider",
                                subject=f"🚨 ROSTER RAID: {wrestler_name} signed by {rival_name}",
                                body=f"BREAKING: {rival_name} has signed {wrestler_name} away from your promotion. They've been removed from your roster.",
                                icon="🚨",
                                message_type="rival_raid",
                            )
                            self.messages_added += 1
                        except Exception:
                            pass

            if rival_result.get("signings"):
                for sign in rival_result["signings"]:
                    sign_data = sign.get("signing", {})
                    rival_name = sign.get("rival_name", "A rival")
                    wrestler_name = sign_data.wrestler_name if hasattr(sign_data, "wrestler_name") else "a free agent"
                    result["highlights"].append(
                        f"📝 {rival_name} signed {wrestler_name} from free agency"
                    )

            # Maybe create a new rival as the industry evolves
            try:
                from ai.rival_promotions import RivalSize

                player_level = self.gs.progression.level if self.gs.progression else 1
                if player_level <= 10:
                    player_size = RivalSize.BACKYARD
                elif player_level <= 30:
                    player_size = RivalSize.INDIE
                elif player_level <= 50:
                    player_size = RivalSize.REGIONAL
                elif player_level <= 70:
                    player_size = RivalSize.NATIONAL
                elif player_level <= 90:
                    player_size = RivalSize.MAJOR
                else:
                    player_size = RivalSize.GLOBAL

                new_rival = self.gs.rival_promotions.maybe_create_new_rival(
                    current_week=current_week,
                    player_size=player_size,
                )
                if new_rival:
                    result["highlights"].append(
                        f"🆕 New rival promotion emerged: {new_rival.name}"
                    )
            except Exception:
                pass

        except Exception as e:
            print(f"[Pulse] Rival promotions error: {e}")

    # ==================== 5. TRAINING SCHOOL ====================

    def _process_training_school(self, result, current_week, current_year):
        if not self.gs.training_school or not self.gs.training_school.is_founded():
            return

        try:
            # Process school weekly update (trainees, classes, monthly tuition)
            had_trainee_show = False  # TODO: detect if a trainee show ran this week
            school_result = self.gs.training_school.weekly_update(
                coach_manager=self.gs.coach_manager,
                had_trainee_show=had_trainee_show,
                current_week=current_week,
            )
            result["training_school"] = school_result

            # Refresh trainee applicants
            if self.gs.trainee_pool:
                new_applicants = self.gs.trainee_pool.generate_weekly_applicants(
                    school_reputation=self.gs.training_school.reputation,
                    school_capacity=self.gs.training_school.get_capacity(),
                    current_trainees=self.gs.training_school.get_trainee_count(),
                    monthly_tuition=self.gs.training_school.get_monthly_tuition(),
                    week=current_week,
                    year=current_year,
                )
                result["trainee_applicants"] = new_applicants

                if new_applicants:
                    result["highlights"].append(
                        f"🎓 {len(new_applicants)} new trainee applicant{'s' if len(new_applicants) > 1 else ''} arrived"
                    )

            # Refresh coach pool
            if self.gs.coach_pool:
                new_coaches = self.gs.coach_pool.generate_weekly_coach_pool(
                    school_reputation=self.gs.training_school.reputation,
                    current_pool_size=self.gs.coach_pool.get_pool_count(),
                )
                result["coach_pool_refresh"] = new_coaches

            # Process coach payroll
            if self.gs.coach_manager:
                coach_result = self.gs.coach_manager.process_weekly_update(
                    school=self.gs.training_school,
                )
                paid = coach_result.get("total_paid", 0)
                if paid > 0 and self.gs.promotion:
                    self.gs.promotion.budget = max(0, self.gs.promotion.budget - paid)
                    result["money_changes"]["expenses"] += paid

            # Highlight graduations
            if school_result.get("graduations"):
                for grad in school_result["graduations"]:
                    result["highlights"].append(
                        f"🎓 {grad['name']} GRADUATED from your school!"
                    )

            # Highlight dropouts
            if school_result.get("dropouts"):
                for drop in school_result["dropouts"]:
                    result["highlights"].append(
                        f"😞 Trainee {drop['name']} dropped out"
                    )

            # Monthly tuition processing
            if school_result.get("monthly_processed"):
                income = school_result.get("tuition_collected", 0)
                expenses = school_result.get("overhead_paid", 0)
                if income > 0 and self.gs.promotion:
                    self.gs.promotion.budget += income
                    result["money_changes"]["income"] += income
                if expenses > 0 and self.gs.promotion:
                    self.gs.promotion.budget = max(0, self.gs.promotion.budget - expenses)
                    result["money_changes"]["expenses"] += expenses

        except Exception as e:
            print(f"[Pulse] Training school error: {e}")

    # ==================== 6. QUESTS ====================

    def _process_quests(self, result, fans, budget):
        if not self.gs.quest_system:
            return

        try:
            quest_updates = self.gs.quest_system.check_progress(
                storyline_engine=self.gs.storyline_engine,
                fans=fans,
                budget=budget,
            )
            result["quest_updates"] = quest_updates

            # Highlight completed quests
            for update in quest_updates:
                if update.get("status") == "completed":
                    result["highlights"].append(
                        f"✅ Quest completed: {update.get('quest_title', 'Unknown')}"
                    )
                    # Apply rewards
                    rewards = update.get("rewards", {})
                    if self.gs.promotion:
                        self.gs.promotion.budget += rewards.get("money", 0)
                        self.gs.promotion.fan_base += rewards.get("fans", 0)
                        self.gs.promotion.prestige += rewards.get("prestige", 0)
                elif update.get("status") == "failed":
                    result["highlights"].append(
                        f"❌ Quest failed: {update.get('quest_title', 'Unknown')}"
                    )
        except Exception as e:
            print(f"[Pulse] Quest system error: {e}")

    # ==================== 7. RELATIONSHIPS ====================

    def _process_relationships(self, result):
        if not self.gs.relationship_manager:
            return

        try:
            rel_changes = self.gs.relationship_manager.weekly_decay()
            result["relationship_changes"] = rel_changes

            # Highlight major relationship changes
            for change in rel_changes:
                if change.get("change") in ["relationship_ended", "rivalry_cooled"]:
                    result["highlights"].append(
                        change.get("message", "A relationship changed.")
                    )
        except Exception as e:
            print(f"[Pulse] Relationship manager error: {e}")

    # ==================== 8. WRESTLER WEEKLY UPDATES ====================

    def _process_wrestlers(self, result, current_week):
        if not self.gs.roster:
            return

        walkouts = []

        for wrestler in self.gs.roster[:]:
            try:
                if hasattr(wrestler, "weekly_update"):
                    update = wrestler.weekly_update()

                    if update.get("level_up"):
                        result["highlights"].append(
                            f"⭐ {wrestler.name} leveled up to {update['level_up']['new_level']}!"
                        )
                        result["wrestler_updates"].append({
                            "name": wrestler.name,
                            "type": "level_up",
                            "details": update["level_up"],
                        })

                    if update.get("walked_out"):
                        walkouts.append(wrestler)
                        result["highlights"].append(
                            f"🚪 {wrestler.name} walked out of the promotion!"
                        )
            except Exception as e:
                print(f"[Pulse] Wrestler update error for {wrestler.name}: {e}")

        # Process walkouts
        for w in walkouts:
            try:
                self.gs.remove_wrestler_from_roster(w.name, mark_as_indy_god=False)
                # Send inbox message
                if self.gs.inbox:
                    try:
                        self.gs.inbox.add_message(
                            sender="HR Department",
                            subject=f"🚪 {w.name} has walked out!",
                            body=f"{w.name}'s morale was too low and they've quit the promotion. They are no longer on your roster.",
                            icon="🚪",
                            message_type="walkout",
                        )
                        self.messages_added += 1
                    except Exception:
                        pass
            except Exception:
                pass

    # ==================== 9. FREE AGENT REFRESH ====================

    def _process_free_agents(self, result):
        try:
            from data.wrestler_pool import WrestlerPool

            # Maintain free agent pool of 60-100 agents
            current_count = len(self.gs.free_agents) if self.gs.free_agents else 0
            if current_count < 60:
                # Need to create a temporary pool to generate new agents
                temp_pool = WrestlerPool()
                # Pass already-used names to avoid duplicates
                if self.gs.free_agents:
                    for fa in self.gs.free_agents:
                        if hasattr(fa, "name"):
                            temp_pool.used_names.add(fa.name)
                if self.gs.roster:
                    for r in self.gs.roster:
                        if hasattr(r, "name"):
                            temp_pool.used_names.add(r.name)

                new_agents = temp_pool.generate_weekly_refresh(
                    current_pool_size=current_count,
                    target_pool_size=80,
                )
                if new_agents:
                    self.gs.free_agents.extend(new_agents)
                    result["free_agent_refresh"] = [w.name for w in new_agents]
                    result["highlights"].append(
                        f"🤼 {len(new_agents)} new free agent{'s' if len(new_agents) > 1 else ''} on the market"
                    )
        except Exception as e:
            print(f"[Pulse] Free agent refresh error: {e}")

    # ==================== 10. INJURY HEALING ====================

    def _process_injuries(self, result):
        if not self.gs.injury_manager:
            return

        try:
            self.gs.injury_manager.process_weekly_healing(self.gs.roster)
        except Exception as e:
            print(f"[Pulse] Injury healing error: {e}")

    # ==================== 11. CONTRACT WARNINGS ====================

    def _check_contracts(self, result, current_week):
        if not self.gs.roster:
            return

        try:
            for wrestler in self.gs.roster:
                if hasattr(wrestler, "is_contract_expiring") and wrestler.is_contract_expiring(weeks_warning=4):
                    weeks_left = getattr(wrestler, "contract_length", 0)
                    if weeks_left == 4 or weeks_left == 2 or weeks_left == 1:
                        result["contract_warnings"].append({
                            "name": wrestler.name,
                            "weeks_left": weeks_left,
                        })
                        # Send inbox warning
                        if self.gs.inbox:
                            try:
                                self.gs.inbox.add_message(
                                    sender="Contract Office",
                                    subject=f"⚠️ {wrestler.name} contract expiring in {weeks_left} weeks",
                                    body=f"{wrestler.name}'s contract expires in {weeks_left} weeks. Negotiate a renewal or risk losing them to free agency.",
                                    icon="📋",
                                    message_type="contract_warning",
                                )
                                self.messages_added += 1
                            except Exception:
                                pass
        except Exception as e:
            print(f"[Pulse] Contract check error: {e}")

    # ==================== 12. INBOX DELIVERY ====================

    def _deliver_inbox_messages(self, result, current_week, current_year):
        """Final tally of messages added this week"""
        result["messages_added"] = self.messages_added

    # ==================== 13. HIGHLIGHTS SUMMARY ====================

    def _build_highlights(self, result):
        """Build a final highlights summary for the week"""
        # Calculate net money change
        result["money_changes"]["net"] = (
            result["money_changes"]["income"] - result["money_changes"]["expenses"]
        )

        # If no highlights, add a quiet week message
        if not result["highlights"]:
            result["highlights"].append("📅 A quiet week. Time to make some moves!")

        # Cap highlights at 10 to keep UI manageable
        if len(result["highlights"]) > 10:
            extra = len(result["highlights"]) - 9
            result["highlights"] = result["highlights"][:9]
            result["highlights"].append(f"... and {extra} more events this week")
