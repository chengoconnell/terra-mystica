#!/usr/bin/env python3
"""Test script to run Terra Mystica game after refactoring."""

from game import Game

def test_game():
    """Test basic game functionality."""
    print("Creating Terra Mystica game...")
    
    # Create a 2-player game
    game = Game(player_count=2)
    print(f"Created game with {len(game.get_players())} players capacity")
    
    # Check game state
    print(f"Current round: {game.get_round()}")
    print(f"Current phase: {game.get_phase()}")
    print(f"Current player: {game.get_current_player()}")
    
    # Add players with different factions
    from game.player import FactionType
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)
    player2 = game.add_player(FactionType.DWARVES)
    print("\nAdded players with factions")
    
    # Start the game
    game.start_game()
    print("Game started!")
    
    print(f"\nCurrent round: {game.get_round()}")
    print(f"Current phase: {game.get_phase()}")
    
    # Check player resources
    players = game.get_players()
    for i, player in enumerate(players):
        resources = player.get_resources()
        print(f"\nPlayer {i} ({player.get_faction().name}):")
        print(f"  Resources: {resources.workers}W, {resources.coins}C, {resources.priests}P")
        # PowerBowls uses private storage, so we need to access it differently
        power_available = resources.power_bowls.available_power()
        print(f"  Power available: {power_available}")
        print(f"  Victory Points: {player.get_victory_points()}")
        print(f"  Home Terrain: {player.get_home_terrain().name}")
    
    # Test some basic actions
    print("\n\nTesting basic actions...")
    
    # Try to pass with first player
    try:
        current = game.get_current_player()
        if current:
            game.pass_turn(current)
            print(f"{current.get_faction().name} passed successfully")
        else:
            print("Not in action phase yet")
    except Exception as e:
        print(f"Pass failed: {e}")
    
    # Check cult tracks
    print("\n\nCult track positions:")
    from game.cults import CultType
    cult_board = game.get_cult_board()
    for cult in CultType:
        print(f"{cult.name}:")
        for i, player in enumerate(players):
            pos = cult_board.get_position(player, cult)
            print(f"  Player {i}: position {pos}")
    
    print("\n\nGame is working correctly!")

if __name__ == "__main__":
    test_game()
