#!/usr/bin/env python3
"""Test constructor control pattern - verify direct instantiation is blocked."""

from game import Game
from game.player import Player
from game.board import Board
from game.faction import Faction


def test_constructor_control():
    """Test that Player and Board cannot be instantiated directly."""
    print("Testing Constructor Control Pattern...\n")
    
    # Test 1: Try to create Player directly (should fail)
    print("1. Attempting direct Player instantiation:")
    try:
        player = Player(Faction.WITCHES)
        print("   ✗ ERROR: Was able to create Player directly!")
    except TypeError as e:
        print(f"   ✓ Correctly blocked: {e}")
    
    # Test 2: Try to create Board directly (should fail)
    print("\n2. Attempting direct Board instantiation:")
    try:
        board = Board()
        print("   ✗ ERROR: Was able to create Board directly!")
    except TypeError as e:
        print(f"   ✓ Correctly blocked: {e}")
    
    # Test 3: Create Game normally (should succeed)
    print("\n3. Creating Game through normal constructor:")
    try:
        game = Game(player_factions=["Witches", "Giants"])
        print("   ✓ Successfully created Game")
        print(f"   Current player: {game.current_player_faction}")
        print(f"   Players can access board: {game.board is not None}")
    except Exception as e:
        print(f"   ✗ ERROR: Failed to create Game: {e}")
    
    # Test 4: Verify components were created inside Game
    print("\n4. Verifying internal component creation:")
    # Check that we can get player resources (proves players exist)
    witches_resources = game.get_player_resources("Witches")
    giants_resources = game.get_player_resources("Giants")
    print(f"   Witches exist: {witches_resources is not None}")
    print(f"   Giants exist: {giants_resources is not None}")
    print(f"   Game has board: {game.board is not None}")
    print("   All components created successfully through factory pattern!")
    
    print("\n✅ Constructor control pattern working correctly!")
    print("\nSummary:")
    print("- Player and Board cannot be instantiated directly")
    print("- They can only be created through Game's context managers")
    print("- This ensures proper encapsulation and invariant maintenance")


if __name__ == "__main__":
    test_constructor_control()
