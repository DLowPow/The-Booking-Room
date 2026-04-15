"""
Game Setup System
Handles new game creation with user input
"""

from typing import Optional, Tuple
from classes.enums import Philosophy
from classes.locations import (
    LOCATIONS, 
    get_continents, 
    get_countries, 
    get_cities,
    get_currency,
    get_region_modifier,
)
from classes.philosophy import (
    get_philosophy_profile,
    display_philosophy_info,
    get_starting_budget,
)
from classes.promotion import Promotion
from systems.save_manager import GameState


def clear_screen():
    """Clear terminal screen"""
    print("\n" * 50)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def get_input(prompt: str, valid_options: list = None, allow_empty: bool = False) -> str:
    """Get validated input from user"""
    while True:
        user_input = input(prompt).strip()
        
        if not user_input and not allow_empty:
            print("❌ Please enter a value.")
            continue
        
        if valid_options:
            # Check if input is a number referring to an option
            if user_input.isdigit():
                index = int(user_input) - 1
                if 0 <= index < len(valid_options):
                    return valid_options[index]
            # Check if input matches an option directly
            elif user_input in valid_options:
                return user_input
            else:
                print(f"❌ Invalid option. Please choose from the list.")
                continue
        
        return user_input


def display_numbered_list(items: list, title: str = ""):
    """Display a numbered list of options"""
    if title:
        print(f"\n{title}")
        print("-" * 40)
    
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    print()


def setup_promoter_name() -> str:
    """Get the promoter's name"""
    print_header("🎭 CREATE YOUR PROMOTER")
    
    print("Every great promotion needs a visionary leader.")
    print("What is your name?\n")
    
    name = get_input("Promoter Name: ")
    
    print(f"\nWelcome, {name}! Let's build your wrestling empire.\n")
    input("Press Enter to continue...")
    
    return name


def setup_promotion_name() -> str:
    """Get the promotion's name"""
    print_header("🏟️ NAME YOUR PROMOTION")
    
    print("What will your wrestling promotion be called?")
    print("Choose wisely - this name will echo through history!\n")
    
    name = get_input("Promotion Name: ")
    
    print(f"\n'{name}' - A name that will strike fear into your rivals!\n")
    input("Press Enter to continue...")
    
    return name


def setup_location() -> Tuple[str, str, str]:
    """Get the promotion's location"""
    print_header("🌍 CHOOSE YOUR HOME BASE")
    
    print("Where will your promotion be headquartered?")
    print("Your location affects your market, costs, and opportunities.\n")
    
    # Select continent
    continents = get_continents()
    display_numbered_list(continents, "Select Continent:")
    continent = get_input("Enter number: ", continents)
    
    # Show region info
    region_info = get_region_modifier(continent)
    if region_info:
        print(f"\n📊 {continent}: {region_info.get('description', '')}")
    
    # Select country
    countries = get_countries(continent)
    display_numbered_list(countries, f"\nSelect Country in {continent}:")
    country = get_input("Enter number: ", countries)
    
    # Show currency
    currency_code, currency_symbol = get_currency(country)
    print(f"\n💰 Currency: {currency_code} ({currency_symbol})")
    
    # Select city
    cities = get_cities(continent, country)
    display_numbered_list(cities, f"\nSelect City in {country}:")
    city = get_input("Enter number: ", cities)
    
    print(f"\n📍 Home Base: {city}, {country}, {continent}")
    input("\nPress Enter to continue...")
    
    return continent, country, city


def setup_philosophy() -> Philosophy:
    """Get the promotion's philosophy"""
    print_header("🎯 CHOOSE YOUR PHILOSOPHY")
    
    print("Your philosophy defines your promotion's identity.")
    print("It affects everything from your fanbase to your finances.")
    print("\nReview each philosophy carefully:\n")
    
    philosophies = list(Philosophy)
    philosophy_names = [p.value for p in philosophies]
    
    # Display brief overview
    print("-" * 50)
    print(f"{'Philosophy':<25} {'Starting Budget':>20}")
    print("-" * 50)
    
    for phil in philosophies:
        profile = get_philosophy_profile(phil)
        print(f"{phil.value:<25} ${profile.starting_budget:>19,}")
    
    print("-" * 50)
    
    # Let user view details
    while True:
        print("\nOptions:")
        print("  1-4: View detailed info about a philosophy")
        print("  C:   Confirm selection\n")
        
        display_numbered_list(philosophy_names, "Philosophies:")
        
        choice = input("Enter number to view details (or 'C' to choose): ").strip().upper()
        
        if choice == 'C':
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(philosophies):
            selected_phil = philosophies[int(choice) - 1]
            print(display_philosophy_info(selected_phil))
            input("\nPress Enter to continue...")
        else:
            print("❌ Invalid option.")
    
    # Make final selection
    print("\nMake your final choice:")
    display_numbered_list(philosophy_names)
    
    selected_name = get_input("Enter number: ", philosophy_names)
    
    # Convert name back to enum
    for phil in philosophies:
        if phil.value == selected_name:
            selected_philosophy = phil
            break
    
    profile = get_philosophy_profile(selected_philosophy)
    print(f"\n✅ You've chosen: {selected_philosophy.value}")
    print(f"💰 Starting Budget: ${profile.starting_budget:,}")
    input("\nPress Enter to continue...")
    
    return selected_philosophy


def confirm_setup(
    promoter_name: str,
    promotion_name: str,
    continent: str,
    country: str,
    city: str,
    philosophy: Philosophy
) -> bool:
    """Display summary and confirm setup"""
    print_header("📋 CONFIRM YOUR CHOICES")
    
    profile = get_philosophy_profile(philosophy)
    currency_code, currency_symbol = get_currency(country)
    region_info = get_region_modifier(continent)
    
    print(f"  Promoter:     {promoter_name}")
    print(f"  Promotion:    {promotion_name}")
    print(f"  Location:     {city}, {country}")
    print(f"  Region:       {continent}")
    print(f"  Philosophy:   {philosophy.value}")
    print(f"  Currency:     {currency_code} ({currency_symbol})")
    print(f"  Budget:       {currency_symbol}{profile.starting_budget:,}")
    print(f"  Starting Fans: {profile.starting_fans:,}")
    print(f"  Prestige:     {profile.prestige_start}")
    
    print("\n" + "-" * 50)
    
    confirm = input("\nIs this correct? (Y/N): ").strip().upper()
    return confirm == 'Y'


def create_new_game() -> Optional[GameState]:
    """
    Run the complete new game setup flow.
    Returns a GameState object or None if cancelled.
    """
    print_header("🎮 WRESTLING GM - NEW GAME")
    
    print("Welcome to Wrestling GM!")
    print("You're about to create your own wrestling promotion.")
    print("Make smart choices and build a wrestling empire!\n")
    
    input("Press Enter to begin setup...")
    
    while True:
        # Step 1: Promoter Name
        clear_screen()
        promoter_name = setup_promoter_name()
        
        # Step 2: Promotion Name
        clear_screen()
        promotion_name = setup_promotion_name()
        
        # Step 3: Location
        clear_screen()
        continent, country, city = setup_location()
        
        # Step 4: Philosophy
        clear_screen()
        philosophy = setup_philosophy()
        
        # Confirm
        clear_screen()
        if confirm_setup(promoter_name, promotion_name, continent, country, city, philosophy):
            break
        else:
            print("\nLet's start over...")
            input("Press Enter to restart setup...")
    
    # Create the game state
    print_header("🚀 CREATING YOUR PROMOTION")
    
    profile = get_philosophy_profile(philosophy)
    currency_code, currency_symbol = get_currency(country)
    region_info = get_region_modifier(continent)
    
    # Create promotion with all modifiers applied
    promotion = Promotion(
        name=promotion_name,
        philosophy=philosophy,
        owner_name=promoter_name,
        starting_budget=profile.starting_budget,
        location=f"{city}, {country}",
    )
    
    # Apply philosophy modifiers
    promotion.fan_base = profile.starting_fans
    promotion.prestige = profile.prestige_start
    promotion.merchandise_modifier = profile.merchandise_modifier
    
    # Store additional data
    promotion.continent = continent
    promotion.country = country
    promotion.city = city
    promotion.currency_code = currency_code
    promotion.currency_symbol = currency_symbol
    
    # Apply region modifiers
    if region_info:
        promotion.tv_modifier = region_info.get('tv_opportunity', 1.0)
        promotion.talent_pool_modifier = region_info.get('talent_pool', 1.0)
        promotion.operating_cost_modifier = region_info.get('operating_costs', 1.0)
    
    # Create game state
    game_state = GameState()
    game_state.promoter_name = promoter_name
    game_state.promotion = promotion
    game_state.game_settings = {
        "continent": continent,
        "country": country,
        "city": city,
        "currency_code": currency_code,
        "currency_symbol": currency_symbol,
    }
    
    print("✅ Promotion created successfully!\n")
    print(f"   {promotion_name}")
    print(f"   Based in {city}, {country}")
    print(f"   Philosophy: {philosophy.value}")
    print(f"   Budget: {currency_symbol}{profile.starting_budget:,}")
    print(f"   Fans: {profile.starting_fans:,}")
    
    # Prompt to save
    print("\n" + "-" * 50)
    save_now = input("\nWould you like to save your game? (Y/N): ").strip().upper()
    
    if save_now == 'Y':
        save_name = input("Enter save name: ").strip()
        if not save_name:
            save_name = promotion_name
        game_state.save(save_name)
    
    print("\n🎉 Setup complete! Your journey begins now!")
    input("\nPress Enter to continue...")
    
    return game_state


def load_existing_game() -> Optional[GameState]:
    """
    Load an existing game from save files.
    Returns a GameState object or None if cancelled/failed.
    """
    print_header("📂 LOAD GAME")
    
    game_state = GameState()
    saves = game_state.list_saves()
    
    if not saves:
        print("No save files found.")
        input("\nPress Enter to go back...")
        return None
    
    print("Available save files:\n")
    print(f"{'#':<4} {'Save Name':<20} {'Promotion':<20} {'Week':<10} {'Date':<20}")
    print("-" * 74)
    
    for i, save in enumerate(saves, 1):
        week_info = f"Y{save.get('year', 1)}:W{save.get('week', 1)}"
        date = save.get('save_date', 'Unknown')[:10]
        print(f"{i:<4} {save['save_name']:<20} {save['promotion_name']:<20} {week_info:<10} {date:<20}")
    
    print("-" * 74)
    print("\nEnter 0 to cancel.")
    
    while True:
        choice = input("\nSelect save to load: ").strip()
        
        if choice == '0':
            return None
        
        if choice.isdigit() and 1 <= int(choice) <= len(saves):
            selected_save = saves[int(choice) - 1]
            break
        else:
            print("❌ Invalid selection.")
    
    # Load the save
    if game_state.load(selected_save['save_name']):
        print(f"\n✅ Loaded: {selected_save['promotion_name']}")
        print(f"   Year {selected_save.get('year', 1)}, Week {selected_save.get('week', 1)}")
        input("\nPress Enter to continue...")
        return game_state
    else:
        print("❌ Failed to load save file.")
        input("\nPress Enter to go back...")
        return None


def main_menu() -> Optional[GameState]:
    """
    Display main menu and handle selection.
    Returns a GameState to play with, or None to exit.
    """
    while True:
        clear_screen()
        print_header("🏆 WRESTLING GM 🏆")
        
        print("       The Ultimate Wrestling Management Simulation\n")
        print("-" * 60)
        print("\n  1. 🆕 New Game")
        print("  2. 📂 Load Game")
        print("  3. ❌ Exit")
        print("\n" + "-" * 60)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            game_state = create_new_game()
            if game_state:
                return game_state
        elif choice == '2':
            game_state = load_existing_game()
            if game_state:
                return game_state
        elif choice == '3':
            print("\nThanks for playing! Goodbye! 👋\n")
            return None
        else:
            print("❌ Invalid option.")
            input("Press Enter to continue...")

            # Add this import at the top
from systems.creative_control import CreativeControlSystem

# Add this new function after setup_philosophy()

def setup_creative_control() -> Tuple[bool, str]:
    """Get creative control settings"""
    print_header("🎭 CREATIVE CONTROL")
    
    print("Creative Control adds wrestler agency to your game.")
    print("When enabled, wrestlers can:")
    print("")
    print("  • Demand raises and title shots")
    print("  • Refuse to lose matches")
    print("  • Go into business for themselves")
    print("  • Start backstage drama")
    print("  • Talk to rival promotions")
    print("  • Walk out with your championship!")
    print("")
    print("This creates a more challenging and unpredictable experience.")
    print("-" * 60)
    
    # Enable/Disable choice
    print("\nEnable Creative Control?")
    print("  1. Yes - I want the chaos!")
    print("  2. No  - I prefer full control")
    
    while True:
        choice = input("\nSelect (1 or 2): ").strip()
        if choice == "1":
            enabled = True
            break
        elif choice == "2":
            enabled = False
            break
        else:
            print("❌ Please enter 1 or 2")
    
    difficulty = "Normal"
    
    if enabled:
        print("\n" + "-" * 60)
        print("\nSelect Difficulty:")
        print("")
        print("  1. 😊 Easy   - Fewer incidents, more positive events")
        print("  2. 😐 Normal - Balanced experience")
        print("  3. 😰 Hard   - Frequent incidents, egos run wild")
        print("  4. 🔥 Chaos  - Constant drama, good luck!")
        
        difficulties = ["Easy", "Normal", "Hard", "Chaos"]
        
        while True:
            choice = input("\nSelect (1-4): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= 4:
                difficulty = difficulties[int(choice) - 1]
                break
            else:
                print("❌ Please enter 1-4")
        
        print(f"\n✅ Creative Control: ENABLED ({difficulty})")
        print("\nPrepare for drama! 🎭")
    else:
        print("\n✅ Creative Control: DISABLED")
        print("\nYou have complete control over your roster.")
    
    input("\nPress Enter to continue...")
    
    return enabled, difficulty


# Update the create_new_game() function - add after philosophy selection:

def create_new_game() -> Optional[GameState]:
    """
    Run the complete new game setup flow.
    Returns a GameState object or None if cancelled.
    """
    print_header("🎮 WRESTLING GM - NEW GAME")
    
    print("Welcome to Wrestling GM!")
    print("You're about to create your own wrestling promotion.")
    print("Make smart choices and build a wrestling empire!\n")
    
    input("Press Enter to begin setup...")
    
    while True:
        # Step 1: Promoter Name
        clear_screen()
        promoter_name = setup_promoter_name()
        
        # Step 2: Promotion Name
        clear_screen()
        promotion_name = setup_promotion_name()
        
        # Step 3: Location
        clear_screen()
        continent, country, city = setup_location()
        
        # Step 4: Philosophy
        clear_screen()
        philosophy = setup_philosophy()
        
        # Step 5: Creative Control (NEW!)
        clear_screen()
        cc_enabled, cc_difficulty = setup_creative_control()
        
        # Confirm
        clear_screen()
        if confirm_setup_with_cc(
            promoter_name, promotion_name, continent, country, city, 
            philosophy, cc_enabled, cc_difficulty
        ):
            break
        else:
            print("\nLet's start over...")
            input("Press Enter to restart setup...")
    
    # Create the game state
    print_header("🚀 CREATING YOUR PROMOTION")
    
    profile = get_philosophy_profile(philosophy)
    currency_code, currency_symbol = get_currency(country)
    region_info = get_region_modifier(continent)
    
    # Create promotion with all modifiers applied
    promotion = Promotion(
        name=promotion_name,
        philosophy=philosophy,
        owner_name=promoter_name,
        starting_budget=profile.starting_budget,
        location=f"{city}, {country}",
    )
    
    # Apply philosophy modifiers
    promotion.fan_base = profile.starting_fans
    promotion.prestige = profile.prestige_start
    promotion.merchandise_modifier = profile.merchandise_modifier
    
    # Store additional data
    promotion.continent = continent
    promotion.country = country
    promotion.city = city
    promotion.currency_code = currency_code
    promotion.currency_symbol = currency_symbol
    
    # Apply region modifiers
    if region_info:
        promotion.tv_modifier = region_info.get('tv_opportunity', 1.0)
        promotion.talent_pool_modifier = region_info.get('talent_pool', 1.0)
        promotion.operating_cost_modifier = region_info.get('operating_costs', 1.0)
    
    # Create Creative Control system (NEW!)
    creative_control = CreativeControlSystem(
        enabled=cc_enabled,
        difficulty=cc_difficulty
    )
    
    # Create game state
    game_state = GameState()
    game_state.promoter_name = promoter_name
    game_state.promotion = promotion
    game_state.creative_control = creative_control  # NEW!
    game_state.game_settings = {
        "continent": continent,
        "country": country,
        "city": city,
        "currency_code": currency_code,
        "currency_symbol": currency_symbol,
        "creative_control_enabled": cc_enabled,
        "creative_control_difficulty": cc_difficulty,
    }
    
    print("✅ Promotion created successfully!\n")
    print(f"   {promotion_name}")
    print(f"   Based in {city}, {country}")
    print(f"   Philosophy: {philosophy.value}")
    print(f"   Budget: {currency_symbol}{profile.starting_budget:,}")
    print(f"   Fans: {profile.starting_fans:,}")
    print(f"   Creative Control: {'ON (' + cc_difficulty + ')' if cc_enabled else 'OFF'}")
    
    # Prompt to save
    print("\n" + "-" * 50)
    save_now = input("\nWould you like to save your game? (Y/N): ").strip().upper()
    
    if save_now == 'Y':
        save_name = input("Enter save name: ").strip()
        if not save_name:
            save_name = promotion_name
        game_state.save(save_name)
    
    print("\n🎉 Setup complete! Your journey begins now!")
    input("\nPress Enter to continue...")
    
    return game_state


def confirm_setup_with_cc(
    promoter_name: str,
    promotion_name: str,
    continent: str,
    country: str,
    city: str,
    philosophy: Philosophy,
    cc_enabled: bool,
    cc_difficulty: str
) -> bool:
    """Display summary and confirm setup (with Creative Control)"""
    print_header("📋 CONFIRM YOUR CHOICES")
    
    profile = get_philosophy_profile(philosophy)
    currency_code, currency_symbol = get_currency(country)
    
    print(f"  Promoter:          {promoter_name}")
    print(f"  Promotion:         {promotion_name}")
    print(f"  Location:          {city}, {country}")
    print(f"  Region:            {continent}")
    print(f"  Philosophy:        {philosophy.value}")
    print(f"  Currency:          {currency_code} ({currency_symbol})")
    print(f"  Budget:            {currency_symbol}{profile.starting_budget:,}")
    print(f"  Starting Fans:     {profile.starting_fans:,}")
    print(f"  Prestige:          {profile.prestige_start}")
    print(f"  Creative Control:  {'ON (' + cc_difficulty + ')' if cc_enabled else 'OFF'}")
    
    print("\n" + "-" * 50)
    
    confirm = input("\nIs this correct? (Y/N): ").strip().upper()
    return confirm == 'Y'


# Allow running this file directly for testing
if __name__ == "__main__":
    game = main_menu()
    if game:
        print(f"\nGame loaded: {game.promotion.name}")
        print(f"Budget: {game.promotion.budget:,}")