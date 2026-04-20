"""
Main Game Loop - The core gameplay experience
Handles menus, actions, and game flow
"""

import os
import random
from typing import Dict, List, Optional, Tuple

from classes.wrestler import Wrestler
from classes.promotion import Promotion
from classes.enums import Philosophy, WrestlingStyle, Gender, Alignment
from classes.venue import Venue, VenueTier
from classes.progression import (
    ProgressionSystem, get_cumulative_limits, get_promotion_tier,
    get_tier_name, get_xp_progress
)
from systems.match_engine import MatchEngine, MatchResult
from systems.save_manager import GameState, SaveManager
from ai.director import AIDirector
from ai.event_generator import GameEvent, EventSeverity
from data.venues import get_venues_by_continent, get_venues_by_tier
from data.wrestler_generator import generate_free_agents


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def press_enter():
    """Wait for user to press enter"""
    input("\nPress Enter to continue...")


def print_header(title: str, width: int = 60):
    """Print a formatted header"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_subheader(title: str, width: int = 50):
    """Print a formatted subheader"""
    print("\n" + "-" * width)
    print(f"  {title}")
    print("-" * width)


def format_money(amount: int, symbol: str = "$") -> str:
    """Format money with commas"""
    return f"{symbol}{amount:,}"


def format_rating(rating: float) -> str:
    """Format a star rating"""
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    
    result = "★" * full_stars
    if half_star:
        result += "½"
    
    return f"{result} ({rating:.2f})"


class GameLoop:
    """
    Main game loop controller.
    Manages the flow of gameplay, menus, and actions.
    """
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.promotion = game_state.promotion
        self.progression = game_state.progression if hasattr(game_state, 'progression') else ProgressionSystem()
        
        # AI Director
        cc_enabled = game_state.game_settings.get("creative_control_enabled", False)
        cc_difficulty = game_state.game_settings.get("creative_control_difficulty", "Normal")
        self.ai_director = AIDirector(
            creative_control_enabled=cc_enabled,
            creative_control_difficulty=cc_difficulty,
        )
        
        # Match engine
        self.match_engine = MatchEngine(self.promotion)
        
        # Free agents pool
        self.free_agents: List[Wrestler] = game_state.free_agents if game_state.free_agents else []
        if not self.free_agents:
            self.free_agents = generate_free_agents(20)
        
        # Current week's show
        self.current_show_card: List[Dict] = []
        self.current_venue: Optional[Venue] = None
        
        # Running state
        self.is_running = True
        self.pending_events: List[GameEvent] = []
    
    def run(self):
        """Main game loop"""
        self.is_running = True
        
        while self.is_running:
            clear_screen()
            self._display_main_menu()
            choice = input("\nSelect option: ").strip()
            
            self._handle_main_menu(choice)
        
        print("\nThanks for playing! See you next time! 👋\n")
    
    def _display_main_menu(self):
        """Display the main game menu"""
        print_header(f"🏟️ {self.promotion.name}")
        
        # Status bar
        currency = self.game_state.game_settings.get("currency_symbol", "$")
        print(f"\n📅 Year {self.promotion.current_year}, Week {self.promotion.current_week}")
        print(f"💰 Budget: {format_money(self.promotion.budget, currency)}")
        print(f"👥 Fans: {self.promotion.fan_base:,}")
        print(f"📊 Prestige: {self.promotion.prestige}")
        print(f"🤼 Roster: {len(self.promotion.roster)} wrestlers")
        
        # Level info
        level, xp_into, xp_needed, percentage = get_xp_progress(self.progression.total_xp)
        tier = get_promotion_tier(level)
        print(f"⭐ Level {level} ({get_tier_name(tier)}) - {percentage:.0f}% to next")
        
        # Pending events warning
        critical_events = [e for e in self.ai_director.get_active_events() 
                         if e.severity in [EventSeverity.CRITICAL, EventSeverity.MAJOR]]
        if critical_events:
            print(f"\n⚠️  {len(critical_events)} urgent event(s) require attention!")
        
        # Menu options
        print("\n" + "-" * 50)
        print("\n  1. 📋 Book a Show")
        print("  2. 🤼 Roster Management")
        print("  3. ✍️  Sign Free Agents")
        print("  4. 🏟️  View Venues")
        print("  5. 📰 Events & Messages")
        print("  6. 🎯 Quests")
        print("  7. 📊 Career Overview")
        print("  8. ⏭️  Advance Week")
        print("  9. 💾 Save Game")
        print("  0. 🚪 Exit to Main Menu")
    
    def _handle_main_menu(self, choice: str):
        """Handle main menu selection"""
        handlers = {
            "1": self._book_show_menu,
            "2": self._roster_menu,
            "3": self._free_agents_menu,
            "4": self._venues_menu,
            "5": self._events_menu,
            "6": self._quests_menu,
            "7": self._career_overview,
            "8": self._advance_week,
            "9": self._save_game,
            "0": self._exit_game,
        }
        
        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            print("\n❌ Invalid option")
            press_enter()
    
    # ==================== BOOK A SHOW ====================
    
    def _book_show_menu(self):
        """Show booking menu"""
        clear_screen()
        print_header("📋 BOOK A SHOW")
        
        # Check if we have wrestlers
        available = [w for w in self.promotion.roster if not w.is_injured]
        if len(available) < 2:
            print("\n❌ You need at least 2 healthy wrestlers to book a show!")
            press_enter()
            return
        
        # Check limits
        limits = get_cumulative_limits(self.progression.level)
        
        print("\n  1. 📺 Book Weekly Show")
        if limits.get("can_run_ppv"):
            print("  2. 🎬 Book PPV Event")
        else:
            print("  2. 🔒 PPV Events (Unlock at Level 20)")
        print("  0. ↩️  Back")
        
        choice = input("\nSelect: ").strip()
        
        if choice == "1":
            self._book_weekly_show()
        elif choice == "2" and limits.get("can_run_ppv"):
            self._book_ppv()
        elif choice == "0":
            return
    
    def _book_weekly_show(self):
        """Book a weekly show"""
        clear_screen()
        print_header("📺 BOOK WEEKLY SHOW")
        
        # Select venue
        venue = self._select_venue()
        if not venue:
            return
        
        self.current_venue = venue
        self.current_show_card = []
        
        # Booking loop
        while True:
            clear_screen()
            print_header(f"📋 SHOW AT {venue.name.upper()}")
            
            # Show current card
            print(f"\n📍 Venue: {venue.name} ({venue.city})")
            print(f"👥 Capacity: {venue.capacity:,}")
            print(f"💰 Cost: {format_money(venue.rental_cost)}")
            
            self._display_current_card()
            
            print("\n" + "-" * 50)
            print("\n  1. ➕ Add Match")
            print("  2. ❌ Remove Match")
            print("  3. ▶️  Run Show")
            print("  0. ↩️  Cancel")
            
            choice = input("\nSelect: ").strip()
            
            if choice == "1":
                self._add_match_to_card()
            elif choice == "2":
                self._remove_match_from_card()
            elif choice == "3":
                if len(self.current_show_card) > 0:
                    self._run_show(is_ppv=False)
                    return
                else:
                    print("\n❌ You need at least 1 match!")
                    press_enter()
            elif choice == "0":
                return
    
    def _select_venue(self) -> Optional[Venue]:
        """Select a venue for the show"""
        clear_screen()
        print_header("🏟️ SELECT VENUE")
        
        limits = get_cumulative_limits(self.progression.level)
        max_tier = limits.get("venue_tier_max", 1)
        
        # Get available venues
        continent = self.game_state.game_settings.get("continent", "North America")
        all_venues = get_venues_by_continent(continent)
        
        # Filter by tier
        available_venues = [v for v in all_venues if v.tier.value <= max_tier and v.is_unlocked]
        
        if not available_venues:
            print("\n❌ No venues available!")
            press_enter()
            return None
        
        # Sort by capacity
        available_venues.sort(key=lambda v: v.capacity)
        
        print(f"\n{'#':<4} {'Venue':<30} {'Capacity':<10} {'Cost':<12} {'Tier'}")
        print("-" * 70)
        
        for i, venue in enumerate(available_venues[:15], 1):
            print(f"{i:<4} {venue.name:<30} {venue.capacity:<10,} {format_money(venue.rental_cost):<12} {venue.get_tier_name()}")
        
        print("\n0. Cancel")
        
        choice = input("\nSelect venue: ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_venues):
                return available_venues[idx]
        except ValueError:
            pass
        
        print("\n❌ Invalid selection")
        press_enter()
        return None
    
    def _display_current_card(self):
        """Display the current show card"""
        print_subheader("MATCH CARD")
        
        if not self.current_show_card:
            print("\n  (No matches booked yet)")
        else:
            for i, match in enumerate(self.current_show_card, 1):
                w1 = match["wrestler1"]
                w2 = match["wrestler2"]
                match_type = match.get("match_type", "Standard")
                is_title = match.get("is_title_match", False)
                
                title_marker = " 🏆" if is_title else ""
                print(f"  {i}. {w1.name} vs {w2.name} ({match_type}){title_marker}")
    
    def _add_match_to_card(self):
        """Add a match to the current card"""
        clear_screen()
        print_header("➕ ADD MATCH")
        
        # Get available wrestlers (not already booked)
        booked_names = set()
        for match in self.current_show_card:
            booked_names.add(match["wrestler1"].name)
            booked_names.add(match["wrestler2"].name)
        
        available = [w for w in self.promotion.roster 
                    if not w.is_injured and w.name not in booked_names]
        
        if len(available) < 2:
            print("\n❌ Not enough available wrestlers!")
            press_enter()
            return
        
        # Select wrestler 1
        print("\nSelect Wrestler 1:")
        w1 = self._select_wrestler(available)
        if not w1:
            return
        
        # Select wrestler 2
        available2 = [w for w in available if w.name != w1.name]
        print("\nSelect Wrestler 2:")
        w2 = self._select_wrestler(available2)
        if not w2:
            return
        
        # Select match type
        match_types = self._get_available_match_types()
        print("\nSelect Match Type:")
        for i, mt in enumerate(match_types, 1):
            print(f"  {i}. {mt}")
        
        mt_choice = input("\nSelect (1 for Standard): ").strip()
        try:
            mt_idx = int(mt_choice) - 1 if mt_choice else 0
            match_type = match_types[mt_idx] if 0 <= mt_idx < len(match_types) else "Standard"
        except ValueError:
            match_type = "Standard"
        
        # Add to card
        self.current_show_card.append({
            "wrestler1": w1,
            "wrestler2": w2,
            "match_type": match_type,
            "is_title_match": False,
            "is_main_event": False,
        })
        
        # Mark last match as main event
        if len(self.current_show_card) > 0:
            for match in self.current_show_card:
                match["is_main_event"] = False
            self.current_show_card[-1]["is_main_event"] = True
        
        print(f"\n✅ Added: {w1.name} vs {w2.name} ({match_type})")
        press_enter()
    
    def _select_wrestler(self, wrestlers: List[Wrestler]) -> Optional[Wrestler]:
        """Select a wrestler from a list"""
        print(f"\n{'#':<4} {'Name':<25} {'Pop':<6} {'Style':<15} {'W-L'}")
        print("-" * 60)
        
        for i, w in enumerate(wrestlers[:20], 1):
            record = f"{w.wins}-{w.losses}"
            print(f"{i:<4} {w.name:<25} {w.popularity:<6} {w.primary_style.value:<15} {record}")
        
        print("\n0. Cancel")
        
        choice = input("\nSelect: ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(wrestlers):
                return wrestlers[idx]
        except ValueError:
            pass
        
        return None
    
    def _get_available_match_types(self) -> List[str]:
        """Get match types available at current level"""
        from classes.progression import get_unlocked_match_types
        return get_unlocked_match_types(self.progression.level)
    
    def _remove_match_from_card(self):
        """Remove a match from the card"""
        if not self.current_show_card:
            print("\n❌ No matches to remove!")
            press_enter()
            return
        
        print("\nSelect match to remove (0 to cancel):")
        self._display_current_card()
        
        choice = input("\nSelect: ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.current_show_card):
                removed = self.current_show_card.pop(idx)
                print(f"\n✅ Removed: {removed['wrestler1'].name} vs {removed['wrestler2'].name}")
        except ValueError:
            pass
        
        press_enter()
    
    def _run_show(self, is_ppv: bool = False):
        """Run the booked show"""
        clear_screen()
        show_type = "PPV" if is_ppv else "WEEKLY SHOW"
        print_header(f"▶️ RUNNING {show_type}")
        
        venue = self.current_venue
        print(f"\n📍 {venue.name}, {venue.city}")
        print(f"👥 Capacity: {venue.capacity:,}")
        
        # Calculate attendance
        expected = venue.get_expected_attendance(
            self.promotion.prestige,
            is_ppv=is_ppv,
            card_quality=len(self.current_show_card) * 10
        )
        attendance = min(expected, venue.capacity)
        
        print(f"🎟️ Attendance: {attendance:,}")
        
        is_sellout = attendance >= venue.capacity * 0.95
        if is_sellout:
            print("🎉 SELLOUT!")
        
        # Run matches
        print_subheader("MATCH RESULTS")
        
        results: List[MatchResult] = []
        total_rating = 0.0
        five_star_count = 0
        four_star_count = 0
        
        for i, match in enumerate(self.current_show_card, 1):
            result = self.match_engine.simulate_match(
                wrestler1=match["wrestler1"],
                wrestler2=match["wrestler2"],
                is_title_match=match.get("is_title_match", False),
                is_main_event=match.get("is_main_event", False),
            )
            results.append(result)
            total_rating += result.match_rating
            
            if result.match_rating >= 5.0:
                five_star_count += 1
            elif result.match_rating >= 4.0:
                four_star_count += 1
            
            # Display result
            winner_name = result.winner.name if result.winner else "DRAW"
            me_marker = " (Main Event)" if match.get("is_main_event") else ""
            
            print(f"\n{i}. {match['wrestler1'].name} vs {match['wrestler2'].name}{me_marker}")
            print(f"   Winner: {winner_name} via {result.finish_type.value}")
            print(f"   Rating: {format_rating(result.match_rating)}")
            print(f"   Crowd: {result.crowd_reaction}/100")
        
        # Calculate show average
        avg_rating = total_rating / len(results) if results else 0
        
        print_subheader("SHOW SUMMARY")
        print(f"\n⭐ Average Match Rating: {format_rating(avg_rating)}")
        print(f"👥 Attendance: {attendance:,}")
        print(f"🎤 Crowd Reaction: {sum(r.crowd_reaction for r in results) // len(results)}/100")
        
        # Calculate financials
        ticket_price = venue.get_ticket_price_range()["standard"]
        ticket_revenue = attendance * ticket_price
        venue_cost = venue.get_rental_cost(is_ppv=is_ppv)
        merch_revenue = int(attendance * 5 * self.promotion.merchandise_modifier)
        
        total_revenue = ticket_revenue + merch_revenue
        total_cost = venue_cost
        profit = total_revenue - total_cost
        
        print_subheader("FINANCIALS")
        print(f"\n💵 Ticket Revenue: {format_money(ticket_revenue)}")
        print(f"👕 Merchandise: {format_money(merch_revenue)}")
        print(f"🏟️ Venue Cost: -{format_money(venue_cost)}")
        print(f"{'='*30}")
        profit_color = "✅" if profit >= 0 else "❌"
        print(f"{profit_color} Net Profit: {format_money(profit)}")
        
        # Apply to promotion
        self.promotion.budget += profit
        
        # Process progression
        show_rewards = self.progression.process_show_completion(
            is_ppv=is_ppv,
            average_match_rating=avg_rating,
            attendance=attendance,
            capacity=venue.capacity,
            venue_prestige=venue.prestige,
            venue_tier=venue.tier.value,
            venue_id=venue.id,
            five_star_matches=five_star_count,
            four_star_matches=four_star_count,
            ticket_price=ticket_price,
            merchandise_modifier=self.promotion.merchandise_modifier,
            total_matches=len(results),
        )
        
        print_subheader("REWARDS")
        print(f"\n⭐ XP Earned: +{show_rewards['xp']['total']}")
        print(f"👥 Fans Gained: +{show_rewards['fans']['total']}")
        
        # Apply fans
        self.promotion.fan_base += show_rewards['fans']['total']
        
        # Check for level up
        if show_rewards.get("leveled_up"):
            print(f"\n🎉 LEVEL UP! You are now Level {show_rewards['new_level']}!")
            for unlock in show_rewards.get("new_unlocks", []):
                print(f"   🔓 Unlocked: {unlock}")
        
        # Check achievements
        for achievement in show_rewards.get("achievements_earned", []):
            print(f"\n🏆 Achievement Unlocked: {achievement.name}")
        
        # Record venue history
        venue.record_event(attendance, profit)
        
        # Clear the card
        self.current_show_card = []
        self.current_venue = None
        
        press_enter()
    
    def _book_ppv(self):
        """Book a PPV event"""
        # Similar to weekly show but with more matches and higher stakes
        print("\n🎬 PPV Booking coming soon!")
        press_enter()
    
    # ==================== ROSTER MANAGEMENT ====================
    
    def _roster_menu(self):
        """Roster management menu"""
        while True:
            clear_screen()
            print_header("🤼 ROSTER MANAGEMENT")
            
            limits = get_cumulative_limits(self.progression.level)
            roster_limit = limits.get("roster_limit", 5)
            
            print(f"\n📊 Roster: {len(self.promotion.roster)}/{roster_limit}")
            print(f"💰 Weekly Salaries: {format_money(sum(w.salary for w in self.promotion.roster))}")
            
            print("\n  1. 📋 View Full Roster")
            print("  2. 👤 View Wrestler Details")
            print("  3. ❌ Release Wrestler")
            print("  0. ↩️  Back")
            
            choice = input("\nSelect: ").strip()
            
            if choice == "1":
                self._view_roster()
            elif choice == "2":
                self._view_wrestler_details()
            elif choice == "3":
                self._release_wrestler()
            elif choice == "0":
                return
    
    def _view_roster(self):
        """View the full roster"""
        clear_screen()
        print_header("📋 FULL ROSTER")
        
        if not self.promotion.roster:
            print("\n(No wrestlers signed)")
            press_enter()
            return
        
        print(f"\n{'Name':<25} {'Pop':<6} {'OVR':<5} {'Style':<15} {'Salary':<10} {'Contract'}")
        print("-" * 80)
        
        for w in sorted(self.promotion.roster, key=lambda x: x.popularity, reverse=True):
            status = "🏥" if w.is_injured else "  "
            print(f"{status}{w.name:<23} {w.popularity:<6} {w.overall_rating:<5} {w.primary_style.value:<15} {format_money(w.salary):<10} {w.contract_length}w")
        
        press_enter()
    
    def _view_wrestler_details(self):
        """View details of a specific wrestler"""
        clear_screen()
        print_header("👤 WRESTLER DETAILS")
        
        if not self.promotion.roster:
            print("\n(No wrestlers signed)")
            press_enter()
            return
        
        wrestler = self._select_wrestler(self.promotion.roster)
        if not wrestler:
            return
        
        clear_screen()
        print_header(f"👤 {wrestler.display_name}")
        
        print(f"\n📍 {wrestler.hometown}")
        print(f"📅 Age: {wrestler.age}")
        print(f"⚖️ {wrestler.weight} lbs, {wrestler.height // 12}'{wrestler.height % 12}\"")
        print(f"🎭 {wrestler.alignment.value} | {wrestler.primary_style.value}")
        
        print_subheader("STATS")
        print(f"  Power: {wrestler.power}    Speed: {wrestler.speed}")
        print(f"  Technical: {wrestler.technical}    Stamina: {wrestler.stamina}")
        print(f"  Charisma: {wrestler.charisma}    Aerial: {wrestler.aerial}")
        print(f"  Hardcore: {wrestler.hardcore}")
        print(f"\n  Overall: {wrestler.overall_rating}")
        
        print_subheader("STATUS")
        print(f"  Popularity: {wrestler.popularity}")
        print(f"  Momentum: {wrestler.momentum}")
        print(f"  Morale: {wrestler.morale}")
        if wrestler.is_injured:
            print(f"  🏥 INJURED: {wrestler.injury_type} ({wrestler.injury_weeks_remaining} weeks)")
        
        print_subheader("CONTRACT")
        print(f"  Salary: {format_money(wrestler.salary)}/week")
        print(f"  Weeks Remaining: {wrestler.contract_length}")
        
        print_subheader("RECORD")
        print(f"  Wins: {wrestler.wins} | Losses: {wrestler.losses} | Draws: {wrestler.draws}")
        print(f"  Win Rate: {wrestler.win_percentage:.1f}%")
        
        if wrestler.unique_traits:
            print_subheader("TRAITS")
            for trait in wrestler.unique_traits:
                print(f"  • {trait}")
        
        press_enter()
    
    def _release_wrestler(self):
        """Release a wrestler from the roster"""
        clear_screen()
        print_header("❌ RELEASE WRESTLER")
        
        if not self.promotion.roster:
            print("\n(No wrestlers to release)")
            press_enter()
            return
        
        wrestler = self._select_wrestler(self.promotion.roster)
        if not wrestler:
            return
        
        # Calculate buyout
        buyout = int(wrestler.salary * wrestler.contract_length * 0.5)
        
        print(f"\n⚠️ Are you sure you want to release {wrestler.name}?")
        print(f"💰 Buyout cost: {format_money(buyout)}")
        
        confirm = input("\nType 'RELEASE' to confirm: ").strip()
        
        if confirm.upper() == "RELEASE":
            self.promotion.budget -= buyout
            self.promotion.roster.remove(wrestler)
            print(f"\n✅ {wrestler.name} has been released.")
            
            # They become a free agent
            wrestler.is_signed = False
            wrestler.contract_length = 0
            self.free_agents.append(wrestler)
        else:
            print("\n❌ Release cancelled.")
        
        press_enter()
    
    # ==================== FREE AGENTS ====================
    
    def _free_agents_menu(self):
        """Free agents signing menu"""
        clear_screen()
        print_header("✍️ FREE AGENTS")
        
        limits = get_cumulative_limits(self.progression.level)
        roster_limit = limits.get("roster_limit", 5)
        current_roster = len(self.promotion.roster)
        
        if current_roster >= roster_limit:
            print(f"\n❌ Roster is full ({current_roster}/{roster_limit})")
            print(f"   Reach Level {self.progression.level + 1} to unlock more slots!")
            press_enter()
            return
        
        print(f"\n📊 Roster Space: {current_roster}/{roster_limit}")
        print(f"💰 Budget: {format_money(self.promotion.budget)}")
        
        if not self.free_agents:
            print("\n(No free agents available)")
            press_enter()
            return
        
        print(f"\n{'#':<4} {'Name':<25} {'Pop':<6} {'OVR':<5} {'Style':<15} {'Asking':<10}")
        print("-" * 70)
        
        for i, w in enumerate(self.free_agents[:15], 1):
            asking_salary = self._calculate_asking_salary(w)
            print(f"{i:<4} {w.name:<25} {w.popularity:<6} {w.overall_rating:<5} {w.primary_style.value:<15} {format_money(asking_salary)}/wk")
        
        print("\n0. Back")
        
        choice = input("\nSelect wrestler to sign: ").strip()
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.free_agents):
                self._sign_wrestler(self.free_agents[idx])
        except ValueError:
            pass
    
    def _calculate_asking_salary(self, wrestler: Wrestler) -> int:
        """Calculate what salary a free agent is asking for"""
        base = 200
        popularity_bonus = wrestler.popularity * 10
        skill_bonus = wrestler.overall_rating * 5
        
        return base + popularity_bonus + skill_bonus
    
    def _sign_wrestler(self, wrestler: Wrestler):
        """Sign a free agent"""
        asking_salary = self._calculate_asking_salary(wrestler)
        signing_bonus = asking_salary * 4  # 4 weeks signing bonus
        
        clear_screen()
        print_header(f"✍️ SIGN {wrestler.name.upper()}")
        
        print(f"\n👤 {wrestler.name}")
        print(f"⭐ Popularity: {wrestler.popularity} | Overall: {wrestler.overall_rating}")
        print(f"🎭 {wrestler.primary_style.value}")
        
        print(f"\n💰 Asking Salary: {format_money(asking_salary)}/week")
        print(f"💵 Signing Bonus: {format_money(signing_bonus)}")
        print(f"📝 Contract Length: 52 weeks")
        
        print(f"\n💰 Your Budget: {format_money(self.promotion.budget)}")
        
        if self.promotion.budget < signing_bonus:
            print("\n❌ Cannot afford signing bonus!")
            press_enter()
            return
        
        confirm = input("\nSign this wrestler? (Y/N): ").strip().upper()
        
        if confirm == "Y":
            self.promotion.budget -= signing_bonus
            wrestler.salary = asking_salary
            wrestler.contract_length = 52
            wrestler.is_signed = True
            wrestler.morale = 75
            
            self.promotion.roster.append(wrestler)
            self.free_agents.remove(wrestler)
            
            print(f"\n✅ {wrestler.name} has been signed!")
            
            # XP for signing
            self.progression.add_xp(15, f"Signed {wrestler.name}")
        else:
            print("\n❌ Signing cancelled.")
        
        press_enter()
    
    # ==================== VENUES ====================
    
    def _venues_menu(self):
        """View available venues"""
        clear_screen()
        print_header("🏟️ VENUES")
        
        limits = get_cumulative_limits(self.progression.level)
        max_tier = limits.get("venue_tier_max", 1)
        
        print(f"\n🔓 You can book up to Tier {max_tier} venues")
        
        continent = self.game_state.game_settings.get("continent", "North America")
        venues = get_venues_by_continent(continent)
        
        # Group by tier
        for tier_num in range(1, max_tier + 1):
            tier_venues = [v for v in venues if v.tier.value == tier_num]
            if tier_venues:
                print_subheader(f"TIER {tier_num} - {tier_venues[0].get_tier_name()}")
                for v in tier_venues[:5]:
                    lock = "" if v.tier.value <= max_tier else "🔒 "
                    print(f"  {lock}{v.name} ({v.city}) - Cap: {v.capacity:,}, Cost: {format_money(v.rental_cost)}")
        
        # Show locked tiers
        if max_tier < 7:
            print(f"\n🔒 Tier {max_tier + 1}+ venues locked (higher level required)")
        
        press_enter()
    
    # ==================== EVENTS ====================
    
    def _events_menu(self):
        """View and handle events"""
        while True:
            clear_screen()
            print_header("📰 EVENTS & MESSAGES")
            
            events = self.ai_director.get_active_events()
            
            if not events:
                print("\n✅ No pending events!")
                press_enter()
                return
            
            print(f"\n📋 {len(events)} pending event(s):\n")
            
            for i, event in enumerate(events, 1):
                severity_icon = {
                    EventSeverity.CRITICAL: "🚨",
                    EventSeverity.MAJOR: "⚠️",
                    EventSeverity.MODERATE: "🔶",
                    EventSeverity.MINOR: "📝",
                    EventSeverity.TRIVIAL: "💬",
                }.get(event.severity, "📋")
                
                print(f"  {i}. {severity_icon} {event.title}")
            
            print("\n  0. Back")
            
            choice = input("\nSelect event to handle: ").strip()
            
            if choice == "0":
                return
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(events):
                    self._handle_event(events[idx])
            except ValueError:
                pass
    
    def _handle_event(self, event: GameEvent):
        """Handle a specific event"""
        clear_screen()
        
        severity_text = event.severity.value.upper()
        print_header(f"{severity_text}: {event.title}")
        
        print(f"\n{event.description}")
        
        if event.wrestlers_involved:
            print(f"\n👤 Involved: {', '.join(event.wrestlers_involved)}")
        
        if event.deadline_weeks > 0:
            print(f"\n⏰ Deadline: {event.deadline_weeks} week(s)")
        
        print_subheader("OPTIONS")
        
        for i, option in enumerate(event.options, 1):
            print(f"\n  {i}. {option['text']}")
        
        print("\n  0. Decide Later")
        
        choice = input("\nYour decision: ").strip()
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(event.options):
                result = self.ai_director.resolve_event(event.id, idx)
                
                if result["success"]:
                    print(f"\n✅ {result['message']}")
                    
                    # Apply any direct effects
                    effects = result.get("effects", {})
                    
                    if effects.get("release"):
                        # Handle release
                        for name in event.wrestlers_involved:
                            for w in self.promotion.roster:
                                if w.name == name:
                                    self.promotion.roster.remove(w)
                                    print(f"   {w.name} has been released.")
                                    break
                    
                    if effects.get("money"):
                        self.promotion.budget += effects["money"]
                        print(f"   Budget: {'+' if effects['money'] > 0 else ''}{format_money(effects['money'])}")
                    
                    if effects.get("salary_change"):
                        for name in event.wrestlers_involved:
                            for w in self.promotion.roster:
                                if w.name == name:
                                    w.salary += effects["salary_change"]
                                    print(f"   {w.name}'s salary: {format_money(w.salary)}/week")
                                    break
                    
                    if effects.get("morale"):
                        for name in event.wrestlers_involved:
                            for w in self.promotion.roster:
                                if w.name == name:
                                    w.morale = max(0, min(100, w.morale + effects["morale"]))
                                    break
                else:
                    print(f"\n❌ {result['message']}")
        except ValueError:
            pass
        
        press_enter()
    
    # ==================== QUESTS ====================
    
    def _quests_menu(self):
        """View and manage quests"""
        clear_screen()
        print_header("🎯 QUESTS")
        
        quest_system = self.ai_director.quest_system
        
        # Active quests
        print_subheader("ACTIVE QUESTS")
        if quest_system.active_quests:
            for quest in quest_system.active_quests:
                progress = quest.get_progress_percentage()
                print(f"\n  📋 {quest.title}")
                print(f"     {quest.description}")
                print(f"     Progress: {progress:.0f}% | Time Left: {quest.weeks_remaining} weeks")
        else:
            print("\n  (No active quests)")
        
        # Available quests
        print_subheader("AVAILABLE QUESTS")
        if quest_system.available_quests:
            for i, quest in enumerate(quest_system.available_quests, 1):
                print(f"\n  {i}. {quest.title} [{quest.difficulty.value}]")
                print(f"     {quest.description}")
                print(f"     Rewards: {quest.xp_reward} XP")
        else:
            print("\n  (No quests available)")
        
        # Generate new quests if none available
        if not quest_system.available_quests and len(quest_system.active_quests) < 3:
            print("\n  💡 New quests will be available next week!")
        
        press_enter()
    
    # ==================== CAREER OVERVIEW ====================
    
    def _career_overview(self):
        """View career statistics and overview"""
        clear_screen()
        print_header("📊 CAREER OVERVIEW")
        
        # Promotion info
        print_subheader(f"{self.promotion.name}")
        print(f"  Philosophy: {self.promotion.philosophy.value}")
        print(f"  Location: {self.promotion.location}")
        print(f"  Owner: {self.promotion.owner_name}")
        
        # Progression
        level, xp_into, xp_needed, percentage = get_xp_progress(self.progression.total_xp)
        tier = get_promotion_tier(level)
        
        print_subheader("PROGRESSION")
        print(f"  Level: {level} / 100")
        print(f"  Tier: {get_tier_name(tier)}")
        print(f"  Total XP: {self.progression.total_xp:,}")
        print(f"  Progress to Next: {percentage:.1f}%")
        
        # Stats
        stats = self.progression.stats
        print_subheader("STATISTICS")
        print(f"  Shows Run: {stats['total_shows']}")
        print(f"  PPVs Run: {stats['total_ppvs']}")
        print(f"  5★ Matches: {stats['five_star_matches']}")
        print(f"  Total Attendance: {stats['total_attendance']:,}")
        print(f"  Sellouts: {stats['sellouts']}")
        print(f"  Weeks Played: {stats['weeks_played']}")
        
        # Achievements
        earned = self.progression.get_earned_achievements()
        total_achievements = len(self.progression.achievements)
        
        print_subheader("ACHIEVEMENTS")
        print(f"  Earned: {len(earned)} / {total_achievements}")
        
        if earned:
            print("\n  Recent:")
            for ach in earned[-5:]:
                print(f"    {ach.icon} {ach.name}")
        
        press_enter()
    
    # ==================== ADVANCE WEEK ====================
    
    def _advance_week(self):
        """Advance the game by one week"""
        clear_screen()
        print_header("⏭️ ADVANCE WEEK")
        
        print(f"\n📅 Current: Year {self.promotion.current_year}, Week {self.promotion.current_week}")
        
        # Show what will happen
        print("\nThe following will occur:")
        print("  • Weekly salaries paid")
        print("  • Wrestlers recover from fatigue")
        print("  • Injuries heal")
        print("  • Contracts count down")
        print("  • Random events may occur")
        
        confirm = input("\nAdvance to next week? (Y/N): ").strip().upper()
        
        if confirm != "Y":
            return
        
        # Process week
        print("\n⏳ Processing week...")
        
        # Pay salaries
        total_salaries = sum(w.salary for w in self.promotion.roster)
        self.promotion.budget -= total_salaries
        print(f"  💰 Salaries paid: -{format_money(total_salaries)}")
        
        # Update wrestlers
        for wrestler in self.promotion.roster:
            wrestler.weekly_update()
        
        # Check for contract expirations
        expired = [w for w in self.promotion.roster if w.contract_length <= 0]
        for w in expired:
            print(f"  📝 {w.name}'s contract has expired!")
        
        # Process AI director
        roster_data = [
            {
                "name": w.name,
                "ego": w.ego,
                "loyalty": w.loyalty,
                "professionalism": w.professionalism,
                "morale": w.morale,
                "popularity": w.popularity,
                "salary": w.salary,
                "contract_length": w.contract_length,
                "is_injured": w.is_injured,
                "age": w.age,
                "momentum": w.momentum,
                "wins": w.wins,
                "losses": w.losses,
            }
            for w in self.promotion.roster
        ]
        
        ai_result = self.ai_director.process_weekly_update(
            roster=roster_data,
            budget=self.promotion.budget,
            fans=self.promotion.fan_base,
            prestige=self.promotion.prestige,
            current_week=self.promotion.current_week,
            current_year=self.promotion.current_year,
        )
        
        # Show new events
        if ai_result["new_events"]:
            print(f"\n  📰 {len(ai_result['new_events'])} new event(s)!")
            for event in ai_result["new_events"]:
                print(f"     • {event.title}")
        
        # Weekly progression
        weekly_result = self.progression.process_weekly_update(
            active_wrestlers=len([w for w in self.promotion.roster if not w.is_injured]),
            total_fans=self.promotion.fan_base,
            current_budget=self.promotion.budget,
            weekly_profit=-total_salaries,  # Just salaries this week
            roster_size=len(self.promotion.roster),
        )
        
        print(f"  ⭐ Weekly XP: +{weekly_result['xp']}")
        
        # Generate quests if needed
        quest_system = self.ai_director.quest_system
        if len(quest_system.available_quests) < 3 and random.random() < 0.3:
            quest_system.generate_random_quests(
                current_week=self.promotion.current_week,
                fans=self.promotion.fan_base,
                budget=self.promotion.budget,
                prestige=self.promotion.prestige,
                roster=roster_data,
                count=1,
            )
            print("  🎯 New quest available!")
        
        # Advance week
        self.promotion.advance_week()
        
        print(f"\n📅 Now: Year {self.promotion.current_year}, Week {self.promotion.current_week}")
        
        press_enter()
    
    # ==================== SAVE/EXIT ====================
    
    def _save_game(self):
        """Save the current game"""
        clear_screen()
        print_header("💾 SAVE GAME")
        
        # Update game state
        self.game_state.promotion = self.promotion
        self.game_state.free_agents = self.free_agents
        
        # Add progression to game state
        if not hasattr(self.game_state, 'progression'):
            self.game_state.progression = self.progression
        
        # Add AI director
        self.game_state.ai_director = self.ai_director.to_dict()
        
        default_name = self.promotion.name.replace(" ", "_")
        save_name = input(f"Save name [{default_name}]: ").strip()
        
        if not save_name:
            save_name = default_name
        
        if self.game_state.save(save_name):
            print("\n✅ Game saved successfully!")
        else:
            print("\n❌ Failed to save game!")
        
        press_enter()
    
    def _exit_game(self):
        """Exit to main menu"""
        print("\n⚠️ Any unsaved progress will be lost!")
        confirm = input("Exit to main menu? (Y/N): ").strip().upper()
        
        if confirm == "Y":
            self.is_running = False
