"""
Wrestling GM - Main Entry Point
Test the systems we've built
"""

from classes.enums import Gender, WrestlingStyle, Alignment, Philosophy
from classes.wrestler import Wrestler
from classes.promotion import Promotion
from classes.match_types import MatchType
from systems.match_engine import MatchEngine, quick_match


def create_test_wrestlers():
    """Create some test wrestlers"""
    
    wrestlers = [
        Wrestler(
            name="Bryan Danielson",
            nickname="The American Dragon",
            age=42,
            gender=Gender.MALE,
            hometown="Aberdeen, Washington",
            height=70,
            weight=210,
            primary_style=WrestlingStyle.TECHNICIAN,
            secondary_style=WrestlingStyle.SUBMISSION_ARTIST,
            alignment=Alignment.FACE,
            power=70,
            speed=80,
            technical=98,
            stamina=90,
            charisma=85,
            hardcore=60,
            aerial=75,
            consistency=95,
            popularity=95,
            unique_traits=["ring_general", "iron_man", "submission_specialist"],
            finisher_name="Busaiku Knee",
        ),
        Wrestler(
            name="Rey Fenix",
            nickname="The King of Dives",
            age=31,
            gender=Gender.MALE,
            hometown="Mexico City, Mexico",
            height=69,
            weight=175,
            primary_style=WrestlingStyle.LUCHADOR,
            secondary_style=WrestlingStyle.HIGH_FLYER,
            alignment=Alignment.FACE,
            power=55,
            speed=98,
            technical=80,
            stamina=85,
            charisma=75,
            hardcore=50,
            aerial=99,
            consistency=85,
            popularity=85,
            unique_traits=["spot_monkey", "ladder_match_expert"],
            finisher_name="Fire Driver",
        ),
        Wrestler(
            name="Brock Lesnar",
            nickname="The Beast",
            age=46,
            gender=Gender.MALE,
            hometown="Webster, South Dakota",
            height=75,
            weight=286,
            primary_style=WrestlingStyle.POWERHOUSE,
            alignment=Alignment.HEEL,
            power=99,
            speed=70,
            technical=80,
            stamina=75,
            charisma=80,
            hardcore=65,
            aerial=40,
            consistency=90,
            popularity=98,
            unique_traits=["showstopper", "natural_talent"],
            finisher_name="F5",
        ),
        Wrestler(
            name="Nick Gage",
            nickname="The King of Ultraviolence",
            age=43,
            gender=Gender.MALE,
            hometown="Blackwood, New Jersey",
            height=72,
            weight=220,
            primary_style=WrestlingStyle.HARDCORE,
            secondary_style=WrestlingStyle.BRAWLER,
            alignment=Alignment.FACE,
            power=75,
            speed=60,
            technical=55,
            stamina=80,
            charisma=85,
            hardcore=99,
            aerial=50,
            consistency=70,
            popularity=80,
            unique_traits=["deathmatch_king", "hardcore_legend"],
            finisher_name="Chokebreaker",
        ),
    ]
    
    return wrestlers


def main():
    """Main test function"""
    print("=" * 60)
    print("WRESTLING GM - SYSTEM TEST")
    print("=" * 60)
    
    # Create promotion
    print("\n📢 Creating Promotion...")
    promo = Promotion(
        name="All Elite Wrestling",
        philosophy=Philosophy.WORKRATE,
        owner_name="Tony Khan",
        starting_budget=500000,
    )
    print(f"Created: {promo}")
    
    # Create wrestlers
    print("\n🤼 Creating Wrestlers...")
    wrestlers = create_test_wrestlers()
    
    for wrestler in wrestlers:
        promo.sign_wrestler(wrestler)
        print(f"  - {wrestler.display_name} ({wrestler.overall_rating} OVR, {wrestler.primary_style.value})")
    
    # Create championship
    print("\n🏆 Creating Championship...")
    world_title = promo.create_championship(
        name="AEW World Championship",
        prestige=80,
    )
    promo.award_championship("AEW World Championship", wrestlers[0])
    
    # Simulate matches
    print("\n🔔 Simulating Matches...")
    engine = MatchEngine(promo)
    
    # Match 1: Standard
    print("\n--- MATCH 1: Standard Match ---")
    result1 = engine.simulate_match(
        wrestlers[0],  # Danielson
        wrestlers[1],  # Fenix
        match_type=MatchType.STANDARD,
        is_title_match=True,
    )
    print(f"Winner: {result1.winner.name if result1.winner else 'DRAW'}")
    print(f"Finish: {result1.finish_type.value}")
    print(f"Rating: {result1.match_rating} ⭐")
    print(f"Duration: {result1.duration_minutes} minutes")
    print(f"Crowd: {result1.crowd_reaction}/100")
    
    # Match 2: Big vs Small
    print("\n--- MATCH 2: Giant vs High Flyer ---")
    result2 = engine.simulate_match(
        wrestlers[2],  # Lesnar
        wrestlers[1],  # Fenix
        match_type=MatchType.STANDARD,
        is_main_event=True,
    )
    print(f"Winner: {result2.winner.name if result2.winner else 'DRAW'}")
    print(f"Finish: {result2.finish_type.value}")
    print(f"Rating: {result2.match_rating} ⭐")
    print("Highlights:")
    for h in result2.highlights[:5]:
        print(f"  • {h}")
    
    # Match 3: Deathmatch
    print("\n--- MATCH 3: Deathmatch ---")
    result3 = engine.simulate_match(
        wrestlers[3],  # Gage
        wrestlers[2],  # Lesnar
        match_type=MatchType.DEATHMATCH,
    )
    print(f"Winner: {result3.winner.name if result3.winner else 'DRAW'}")
    print(f"Rating: {result3.match_rating} ⭐")
    if result3.injuries:
        for wrestler, injury, weeks in result3.injuries:
            print(f"  🏥 INJURY: {wrestler.name} - {injury} ({weeks} weeks)")
    
    # Advance time
    print("\n📅 Advancing 4 weeks...")
    for _ in range(4):
        promo.advance_week()
    
    # Show roster status
    print("\n📋 Roster Status:")
    for wrestler in promo.roster:
        status = "🏥 INJURED" if wrestler.is_injured else "✅ Active"
        print(f"  {wrestler.name}: {wrestler.momentum} momentum, {wrestler.fatigue} fatigue, {status}")
    
    # Show finances
    print(f"\n💰 Budget: ${promo.budget:,}")
    print(f"📊 Prestige: {promo.prestige}")
    print(f"👥 Fan Base: {promo.fan_base:,}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)

"""
Wrestling GM - Main Entry Point
"""

from systems.game_setup import main_menu


def main():
    """Main entry point"""
    game_state = main_menu()
    
    if game_state:
        print("\n" + "=" * 60)
        print("GAME STARTED!")
        print("=" * 60)
        print(f"\nPromoter: {game_state.promoter_name}")
        print(f"Promotion: {game_state.promotion.name}")
        print(f"Budget: ${game_state.promotion.budget:,}")
        
        if game_state.creative_control and game_state.creative_control.enabled:
            print(f"Creative Control: ON ({game_state.creative_control.difficulty})")
        else:
            print("Creative Control: OFF")
        
        print("\n🎮 Main gameplay loop coming soon!")

"""
Wrestling GM - Main Entry Point
"""

from systems.game_setup import main_menu, create_new_game, load_existing_game
from systems.game_loop import GameLoop


def main():
    """Main entry point"""
    game_state = main_menu()
    
    if game_state:
        # Start the game loop
        game_loop = GameLoop(game_state)
        game_loop.run()
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
