#!/usr/bin/env python3
"""Test script for Terra Mystica core actions: build, terraform, upgrade."""

from game.game import Game
from game.player import Player, FactionType
from game.board import AxialCoord, TerrainType
from game.structures import StructureType
from game.resources import Resources, PowerBowls
from game.actions import BuildAction, TerraformAction, PassAction


def test_build_action():
    """Test building structures on the board."""
    print("=== Testing Build Action ===")
    
    # Create game and add players
    game = Game(player_count=2)
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)  # Home: WASTELAND
    player2 = game.add_player(FactionType.DWARVES)  # Home: MOUNTAINS
    game.start_game()
    
    print(f"Player 1 ({player1.get_faction_name()}) home terrain: {player1.get_home_terrain().name}")
    print(f"Starting resources: {player1.get_resources()}")
    
    # Find a wasteland hex (home terrain for Chaos Magicians)
    board = game._board
    wasteland_hex = None
    # Search entire board for a wasteland hex
    for hex_space in board._hexes.values():
        if hex_space.terrain == TerrainType.WASTELAND and not hex_space.is_river:
            wasteland_hex = hex_space.coord
            break
    
    if not wasteland_hex:
        print("❌ No wasteland hex found on board for testing")
        # Debug: show what terrains are available
        terrain_counts = {}
        for hex_space in board._hexes.values():
            terrain_counts[hex_space.terrain.name] = terrain_counts.get(hex_space.terrain.name, 0) + 1
        print(f"Available terrains: {terrain_counts}")
        return False
    
    print(f"\nAttempting to build dwelling at {wasteland_hex}")
    
    # Test 1: Valid build
    try:
        build_action = BuildAction(coord=wasteland_hex, structure_type=StructureType.DWELLING)
        game.execute_action(player1, build_action)
        print("✅ Successfully built dwelling")
        
        # Check structure was placed
        hex_after = board.get_hex(wasteland_hex)
        structures = board.get_structures_of_player(player1)
        if any(coord == wasteland_hex for coord, _ in structures):
            print(f"✅ Structure correctly placed at {wasteland_hex}")
        else:
            print("❌ Structure not found after building")
            return False
            
    except Exception as e:
        print(f"❌ Failed to build dwelling: {e}")
        return False
    
    # Test 2: Try to build on occupied hex (should fail)
    print("\nTesting invalid build on occupied hex...")
    # First, player2 needs to pass since it's their turn
    game.execute_action(player2, PassAction())
    # Now it's player1's turn again
    try:
        build_action2 = BuildAction(coord=wasteland_hex, structure_type=StructureType.DWELLING)
        game.execute_action(player1, build_action2)
        print("❌ Should have failed to build on occupied hex")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected: {e}")
    
    # Test 3: Build adjacent structure
    print("\nTesting adjacent build...")
    adjacent_coords = board.get_adjacent_hexes(wasteland_hex)
    built_adjacent = False
    for adj_hex in adjacent_coords:
        if adj_hex.terrain == player1.get_home_terrain() and not adj_hex.structure:
            try:
                build_action3 = BuildAction(coord=adj_hex.coord, structure_type=StructureType.DWELLING)
                game.execute_action(player1, build_action3)
                print(f"✅ Successfully built adjacent dwelling at {adj_hex.coord}")
                built_adjacent = True
                break
            except Exception as e:
                print(f"Failed to build at {adj_hex.coord}: {e}")
    
    print(f"\nResources after building: {player1.get_resources()}")
    return True


def test_terraform_action():
    """Test terraforming hexes."""
    print("\n=== Testing Terraform Action ===")
    
    # Create new game
    game = Game(player_count=2)
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)  # Home: WASTELAND
    player2 = game.add_player(FactionType.DWARVES)  # Home: MOUNTAINS
    game.start_game()
    
    # First build a dwelling to terraform from
    board = game._board
    start_hex = AxialCoord(0, 0)
    
    # Find a wasteland hex to build on
    start_hex = None
    for hex_space in board._hexes.values():
        if hex_space.terrain == TerrainType.WASTELAND and not hex_space.is_river:
            start_hex = hex_space.coord
            break
    
    if not start_hex:
        print("❌ No wasteland hex found for testing")
        return False
    
    print(f"Building initial dwelling at {start_hex}")
    build_action = BuildAction(coord=start_hex, structure_type=StructureType.DWELLING)
    game.execute_action(player1, build_action)
    
    # Find adjacent non-wasteland hex to terraform
    adjacent_hexes = board.get_adjacent_hexes(start_hex)
    target_hex = None
    for adj in adjacent_hexes:
        if adj.terrain != TerrainType.WASTELAND and not adj.is_river:
            target_hex = adj.coord
            original_terrain = adj.terrain
            break
    
    if not target_hex:
        print("❌ No suitable hex found for terraforming")
        return False
    
    print(f"\nTerraforming {target_hex} from {original_terrain.name} to WASTELAND")
    
    # Give player1 more resources for terraforming (costs 3 workers per spade)
    player1._resources = Resources(workers=10, coins=10, priests=1, power_bowls=PowerBowls((12, 0, 0)))
    print(f"Resources before terraform: {player1.get_resources()}")
    
    # Player2 needs to pass since it's their turn after the build
    game.execute_action(player2, PassAction())
    
    # Test terraforming
    try:
        terraform_action = TerraformAction(coord=target_hex)
        game.execute_action(player1, terraform_action)
        print("✅ Successfully terraformed hex")
        
        # Verify terrain changed
        hex_after = board.get_hex(target_hex)
        if hex_after.terrain == TerrainType.WASTELAND:
            print(f"✅ Terrain correctly changed to {hex_after.terrain.name}")
        else:
            print(f"❌ Terrain is {hex_after.terrain.name}, expected WASTELAND")
            return False
            
    except Exception as e:
        print(f"❌ Failed to terraform: {e}")
        return False
    
    print(f"Resources after: {player1.get_resources()}")
    
    # Test invalid terraform (non-adjacent)
    print("\nTesting invalid terraform on non-adjacent hex...")
    # Player2 passes again
    try:
        game.execute_action(player2, PassAction())
    except Exception as e:
        print(f"Warning: Could not pass for player2: {e}")
        # If player2 can't pass (maybe already passed), try with player1 anyway
    
    far_hex = AxialCoord(5, 5)
    try:
        terraform_action2 = TerraformAction(coord=far_hex)
        game.execute_action(player1, terraform_action2)
        print("❌ Should have failed to terraform non-adjacent hex")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected: {e}")
    
    return True


def test_adjacency_and_shipping():
    """Test adjacency and shipping range validation."""
    print("\n=== Testing Adjacency and Shipping ===")
    
    # Create new game
    game = Game(player_count=2)
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)  # Home: WASTELAND
    player2 = game.add_player(FactionType.DWARVES)  # Home: MOUNTAINS
    game.start_game()
    
    board = game._board
    
    # Find a wasteland hex to build initial dwelling
    start_hex = None
    for hex_space in board._hexes.values():
        if hex_space.terrain == TerrainType.WASTELAND and not hex_space.is_river:
            start_hex = hex_space.coord
            break
    
    if not start_hex:
        print("❌ No wasteland hex found for testing")
        return False
    
    print(f"Building initial dwelling at {start_hex}")
    build_action = BuildAction(coord=start_hex, structure_type=StructureType.DWELLING)
    game.execute_action(player1, build_action)
    
    # Test shipping range (no shipping by default)
    print("\nTesting shipping range...")
    print(f"Player shipping level: {player1.get_shipping_level()}")
    
    # Find a non-adjacent hex within shipping range
    non_adjacent_coords = []
    for q in range(-3, 4):
        for r in range(-3, 4):
            coord = AxialCoord(q, r)
            if board.get_hex(coord) and coord.distance_to(start_hex) == 2:
                non_adjacent_coords.append(coord)
    
    if non_adjacent_coords:
        # Find a suitable target hex with correct terrain
        target = None
        for coord in non_adjacent_coords:
            hex_space = board.get_hex(coord)
            if hex_space and hex_space.terrain == TerrainType.WASTELAND and not hex_space.is_river:
                target = coord
                break
        
        if target:
            print(f"\nTrying to build at distance 2 hex {target} (requires shipping)...")
            # Player2 needs to pass first
            game.execute_action(player2, PassAction())
            
            try:
                build_action2 = BuildAction(coord=target, structure_type=StructureType.DWELLING)
                game.execute_action(player1, build_action2)
                print("❌ Should have failed without shipping")
                return False
            except ValueError as e:
                print(f"✅ Correctly rejected: {e}")
        else:
            print("\n⚠️  No suitable distant wasteland hex found for shipping test")
    
    return True


def test_resource_validation():
    """Test that actions fail when resources are insufficient."""
    print("\n=== Testing Resource Validation ===")
    
    # Create game with minimal resources
    game = Game(player_count=2)
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)
    player2 = game.add_player(FactionType.DWARVES)
    game.start_game()
    
    # Spend most resources
    current = player1.get_resources()
    player1.spend_resources(Resources(
        workers=max(0, current.workers - 1),
        coins=max(0, current.coins - 1),
        priests=current.priests
    ))
    
    print(f"Resources after spending: {player1.get_resources()}")
    
    # Find a wasteland hex for testing
    board = game._board
    wasteland_hex = None
    for hex_space in board._hexes.values():
        if hex_space.terrain == TerrainType.WASTELAND and not hex_space.is_river:
            wasteland_hex = hex_space.coord
            break
    
    if not wasteland_hex:
        print("❌ No wasteland hex found for testing")
        return False
    
    # Try to build without enough resources
    print("\nTrying to build without sufficient resources...")
    try:
        build_action = BuildAction(coord=wasteland_hex, structure_type=StructureType.DWELLING)
        game.execute_action(player1, build_action)
        print("❌ Should have failed due to insufficient resources")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected: {e}")
    
    return True


def run_all_tests():
    """Run all core action tests."""
    print("Terra Mystica Core Actions Test Suite")
    print("=" * 50)
    
    tests = [
        ("Build Action", test_build_action),
        ("Terraform Action", test_terraform_action),
        ("Adjacency and Shipping", test_adjacency_and_shipping),
        ("Resource Validation", test_resource_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    all_passed = run_all_tests()
    exit(0 if all_passed else 1)
