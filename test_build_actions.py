#!/usr/bin/env python3
"""Test script for Game build and upgrade actions."""

from game import Game
from game.coordinate import Coordinate
from game.core import Terrain

def test_build_actions():
    """Test building and upgrading structures in the game."""
    print("Testing Build and Upgrade Actions...\n")
    
    # Create a 2-player game
    game = Game(player_factions=["Witches", "Giants"])
    
    # Show initial board state
    print("Initial board terrain (sample):")
    sample_coords = [
        Coordinate(0, 0),   # Mountains (center)
        Coordinate(1, 0),   # Plains
        Coordinate(0, 1),   # Desert
        Coordinate(-1, 0),  # Lakes
    ]
    for coord in sample_coords:
        terrain = game.board.get_terrain(coord)
        print(f"  {coord}: {terrain.value if terrain else 'None'}")
    
    print(f"\nCurrent player: {game.current_player_faction}")
    print(f"Resources: {game.current_player_resources}")
    print(f"Home terrain: Forest")
    
    # Test 1: Transform and build on existing Forest terrain
    print("\n1. Build Dwelling on existing Forest:")
    # Build at (-2, 0) which is Forest and has Wasteland neighbor at (-2, -1)
    target_coord = Coordinate(-2, 0)  # Forest
    try:
        # No transformation needed - already Forest
        # Cost: 2 workers + 1 coin
        print(f"  Building on {target_coord} (already Forest)")
        print(f"  Expected cost: 2 workers + 1 coin")
        
        game.transform_and_build(target_coord, Terrain.FOREST)
        print("  ✓ Success!")
        print(f"  New resources: {game.current_player_resources}")
        print(f"  Structure placed at: {target_coord}")
        
    except ValueError as e:
        print(f"  ✗ Error: {e}")
    
    # Test 2: Try to build on already occupied space
    print("\n2. Try to build on occupied coordinate:")
    try:
        game.transform_and_build(target_coord, Terrain.SWAMP)
        print("  ✗ Should have failed!")
    except ValueError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Pass turn to Giants
    print("\n  Witches pass their turn...")
    game.pass_turn()
    print(f"  Current player is now: {game.current_player_faction}")
    
    print(f"\n3. Giants turn")
    print(f"Current player: {game.current_player_faction}")
    print(f"Resources: {game.current_player_resources}")
    print(f"Home terrain: Wasteland")
    
    # Giants build on Wasteland adjacent to Witches
    giant_coord = Coordinate(-2, -1)  # Wasteland, adjacent to Witches at (-2, 0)
    try:
        print(f"\n  Building on existing Wasteland at {giant_coord}")
        print(f"  Expected cost: 2 workers + 1 coin")
        print(f"  This is adjacent to Witches' dwelling at {target_coord}")
        game.transform_and_build(giant_coord, Terrain.WASTELAND)
        print("  ✓ Success!")
        print(f"  New resources: {game.current_player_resources}")
    except ValueError as e:
        print(f"  ✗ Error: {e}")
    
    # Pass turn - Giants pass to end the round
    print("\n  Giants pass their turn...")
    game.pass_turn()
    print(f"  Round ended. New round begins.")
    print(f"  Current player: {game.current_player_faction}")
    
    # Test 4: Upgrade structure
    print(f"\n4. Witches upgrade Dwelling to Trading House:")
    print(f"Current player: {game.current_player_faction}")
    print(f"Resources: {game.current_player_resources}")
    
    try:
        # Adjacent to Giants, so discount applies: 2 workers + 3 coins
        print(f"  Upgrading dwelling at {target_coord}")
        print(f"  Expected cost: 2 workers + 3 coins (adjacent to Giants)")
        
        game.upgrade_structure(target_coord)
        print("  ✓ Success!")
        print(f"  New resources: {game.current_player_resources}")
        
        # Check Giants' power gain using public API
        giants_resources = game.get_player_resources("Giants")
        print(f"\n  Giants power after upgrade: {giants_resources['power']}")
        print(f"  (Giants gained 2 power from adjacent upgrade)")
        
    except ValueError as e:
        print(f"  ✗ Error: {e}")
    
    # Test 5: Try to upgrade non-existent structure
    print("\n5. Try to upgrade non-existent structure:")
    empty_coord = Coordinate(0, -1)  # Swamp, no structure
    try:
        game.upgrade_structure(empty_coord)
        print("  ✗ Should have failed!")
    except ValueError as e:
        print(f"  ✓ Correctly rejected: {e}")
    
    # Test 6: Transform non-adjacent terrain and build
    print("\n6. Witches transform Plains to Forest and build:")
    plains_coord = Coordinate(1, 0)  # Plains
    try:
        # Plains -> Forest is 3 steps in terrain cycle
        # Cost: 3 spades * 3 (spade level) + 2 workers + 1 coin = 11 workers + 1 coin
        print(f"  Transforming {plains_coord} from Plains to Forest")
        print(f"  Expected cost: 11 workers + 1 coin")
        
        # Need to be Witches' turn
        if game.current_player_faction != "Witches":
            print("  Switching back to Witches...")
            game.pass_turn()  # Giants pass
            print(f"  Current player: {game.current_player_faction}")
        
        print(f"  Current resources: {game.current_player_resources}")
        
        game.transform_and_build(plains_coord, Terrain.FOREST)
        print("  ✓ Success!")
        print(f"  New resources: {game.current_player_resources}")
    except ValueError as e:
        print(f"  ✗ Error: {e}")
    
    print("\n✅ Build and upgrade tests completed!")

if __name__ == "__main__":
    test_build_actions()
