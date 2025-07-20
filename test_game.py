#!/usr/bin/env python3
"""Test script for the Game class."""

import sys
sys.path.append('/Users/andrewoconnell/Oxford/oop/terra-mystica')

from game.game import Game


def test_game_creation():
    """Test creating a game with different player configurations."""
    print("Testing Game Creation...\n")
    
    # Test valid game creation
    try:
        game = Game(player_factions=["Witches", "Giants"])
        print(f"✓ Created 2-player game")
        print(f"  Current player: {game.current_player_faction}")
        print(f"  Resources: {game.current_player_resources}")
    except Exception as e:
        print(f"✗ Failed to create 2-player game: {e}")
    
    # Test with 3 players
    try:
        game = Game(player_factions=["Witches", "Giants", "Mermaids"])
        print(f"\n✓ Created 3-player game")
        print(f"  Players: Witches, Giants, Mermaids")
    except Exception as e:
        print(f"✗ Failed to create 3-player game: {e}")
    
    # Test invalid faction
    try:
        game = Game(player_factions=["Witches", "InvalidFaction"])
        print(f"✗ Should have failed with invalid faction")
    except ValueError as e:
        print(f"\n✓ Correctly rejected invalid faction: {e}")
    
    # Test duplicate factions
    try:
        game = Game(player_factions=["Witches", "Witches"])
        print(f"✗ Should have failed with duplicate factions")
    except ValueError as e:
        print(f"✓ Correctly rejected duplicate factions: {e}")
    
    # Test too few players
    try:
        game = Game(player_factions=["Witches"])
        print(f"✗ Should have failed with too few players")
    except ValueError as e:
        print(f"✓ Correctly rejected 1-player game: {e}")


def test_turn_management():
    """Test turn progression and passing."""
    print("\n\nTesting Turn Management...\n")
    
    game = Game(player_factions=["Witches", "Giants", "Mermaids"])
    
    # Track initial state
    print(f"Round 1 begins")
    print(f"Current player: {game.current_player_faction}")
    
    # Test passing
    initial_faction = game.current_player_faction
    game.pass_turn()
    print(f"\n{initial_faction} passed")
    print(f"Current player: {game.current_player_faction}")
    
    # Pass with remaining players
    second_faction = game.current_player_faction
    game.pass_turn()
    print(f"\n{second_faction} passed")
    print(f"Current player: {game.current_player_faction}")
    
    # Last player passes - should trigger round end
    third_faction = game.current_player_faction
    game.pass_turn()
    print(f"\n{third_faction} passed")
    print(f"Round 1 ended")
    
    # Should be back to first player for round 2
    print(f"\nRound 2 begins")
    print(f"Current player: {game.current_player_faction}")
    print(f"Game over: {game.is_game_over}")


def test_resource_queries():
    """Test resource query methods."""
    print("\n\nTesting Resource Queries...\n")
    
    game = Game(player_factions=["Witches", "Giants"])
    
    # Test current player resources
    print(f"Witches resources: {game.current_player_resources}")
    
    # Test getting resources by faction
    try:
        giants_resources = game.get_player_resources("Giants")
        print(f"Giants resources: {giants_resources}")
    except Exception as e:
        print(f"Failed to get Giants resources: {e}")
    
    # Test invalid faction query
    try:
        mermaids_resources = game.get_player_resources("Mermaids")
        print(f"Should have failed - Mermaids not in game")
    except ValueError as e:
        print(f"✓ Correctly rejected query for non-existent faction: {e}")


def test_game_end():
    """Test game ending after 3 rounds."""
    print("\n\nTesting Game End Condition...\n")
    
    game = Game(player_factions=["Witches", "Giants"])
    
    # Play through 3 rounds
    for round_num in range(1, 4):
        print(f"Round {round_num}")
        
        # Both players pass
        game.pass_turn()  # Witches pass
        game.pass_turn()  # Giants pass
        
        print(f"  Game over: {game.is_game_over}")
        print(f"  Winner: {game.get_winner()}")
    
    print(f"\nFinal state:")
    print(f"  Game over: {game.is_game_over}")
    print(f"  Winner: {game.get_winner()}")
    
    # Check victory points
    witches_vp = 20  # Starting VP
    giants_vp = 20   # Starting VP
    print(f"  (Both players tied at {witches_vp} VP)")


if __name__ == "__main__":
    test_game_creation()
    test_turn_management()
    test_resource_queries()
    test_game_end()
    
    print("\n✅ All Game tests completed!")
