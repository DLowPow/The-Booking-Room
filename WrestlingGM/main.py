"""
The Booking Room - Main Entry Point
For terminal/console testing
For web version, run app.py instead
"""

from systems.game_setup import main_menu
from systems.game_loop import GameLoop


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("🚪 THE BOOKING ROOM")
    print("=" * 60)
    print("\nFor the web version, run: python app.py")
    print("This is the terminal/test version.\n")
    
    game_state = main_menu()
    
    if game_state:
        # Start the game loop
        game_loop = GameLoop(game_state)
        game_loop.run()
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
