"""Tests for HexCoord and HexGrid with Terra Mystica game mechanics."""

from __future__ import annotations
from typing import Literal

from game.coords import HexCoord
from game.hexgrid import HexGrid


# Simple types for testing Terra Mystica mechanics
TerrainType = Literal["plains", "forest", "mountains"] 
BuildingType = Literal["dwelling", "trading_house"]


def test_hexcoord_flyweight() -> None:
    """Test that HexCoord reuses instances (flyweight pattern)."""
    coord1 = HexCoord(1, 2)
    coord2 = HexCoord(1, 2)
    coord3 = HexCoord(2, 1)
    
    # Same coordinates should return same instance
    assert coord1 is coord2
    # Different coordinates should be different instances
    assert coord1 is not coord3
    
    print("✓ Flyweight pattern working correctly")


def test_hexcoord_properties() -> None:
    """Test HexCoord coordinate properties and cube coordinates."""
    coord = HexCoord(2, -1)
    
    assert coord.q == 2
    assert coord.r == -1
    assert coord.s == -1  # s = -q - r = -2 - (-1) = -1
    
    # Test immutability (should not be able to modify)
    try:
        coord.q = 5  # type: ignore
        assert False, "Should not be able to modify q"
    except AttributeError:
        pass
    
    print("✓ HexCoord properties and immutability working")


def test_hex_neighbors() -> None:
    """Test hex neighbor calculation for adjacency rules."""
    grid: HexGrid[TerrainType] = HexGrid()
    center = HexCoord(0, 0)
    
    # Get all 6 neighbors
    neighbors = grid.get_neighbors(center)
    assert len(neighbors) == 6
    
    # Verify correct neighbor positions (E, SE, SW, W, NW, NE)
    expected = [
        HexCoord(1, 0),    # East
        HexCoord(0, 1),    # Southeast  
        HexCoord(-1, 1),   # Southwest
        HexCoord(-1, 0),   # West
        HexCoord(0, -1),   # Northwest
        HexCoord(1, -1),   # Northeast
    ]
    
    assert neighbors == expected
    print("✓ Hex neighbors calculated correctly")


def test_terra_mystica_terrain_placement() -> None:
    """Test terrain placement following Terra Mystica rules."""
    terrain_grid: HexGrid[TerrainType] = HexGrid()
    
    # Place initial terrain in a small area
    terrain_grid.set(HexCoord(0, 0), "plains")
    terrain_grid.set(HexCoord(1, 0), "forest")
    terrain_grid.set(HexCoord(0, 1), "mountains")
    terrain_grid.set(HexCoord(-1, 1), "plains")
    
    # Test retrieval
    assert terrain_grid.get(HexCoord(0, 0)) == "plains"
    assert terrain_grid.get(HexCoord(1, 0)) == "forest"
    
    # Test adjacency for terrain transformation
    center = HexCoord(0, 0)
    adjacent_terrains = terrain_grid.get_filled_neighbors(center)
    
    # Should have 3 neighbors with terrain
    assert len(adjacent_terrains) == 3
    
    # Check neighbor terrain types
    neighbor_types = {coord: terrain for coord, terrain in adjacent_terrains}
    assert neighbor_types[HexCoord(1, 0)] == "forest"
    assert neighbor_types[HexCoord(0, 1)] == "mountains"
    assert neighbor_types[HexCoord(-1, 1)] == "plains"
    
    print("✓ Terrain placement and adjacency working")


def test_building_placement_rules() -> None:
    """Test building placement following adjacency rules."""
    terrain_grid: HexGrid[TerrainType] = HexGrid()
    building_grid: HexGrid[BuildingType] = HexGrid()
    
    # Set up terrain
    terrain_grid.set(HexCoord(0, 0), "plains")
    terrain_grid.set(HexCoord(1, 0), "plains")  
    terrain_grid.set(HexCoord(0, 1), "forest")
    terrain_grid.set(HexCoord(1, 1), "plains")
    
    # Place first dwelling
    building_grid.set(HexCoord(0, 0), "dwelling")
    
    # Check valid building locations (must be adjacent to existing buildings)
    existing_building = HexCoord(0, 0)
    valid_locations = []
    
    for neighbor in terrain_grid.get_neighbors(existing_building):
        # Must be on correct terrain and not already built
        if neighbor in terrain_grid and neighbor not in building_grid:
            if terrain_grid.get(neighbor) == "plains":  # Assume plains faction
                valid_locations.append(neighbor)
    
    assert HexCoord(1, 0) in valid_locations
    assert HexCoord(1, 1) not in valid_locations  # Not adjacent
    assert HexCoord(0, 1) not in valid_locations  # Wrong terrain
    
    print("✓ Building placement rules working")


def test_distance_for_area_scoring() -> None:
    """Test distance calculation for connected area scoring."""
    grid: HexGrid[BuildingType] = HexGrid()
    
    # Place buildings in a line
    grid.set(HexCoord(0, 0), "dwelling")
    grid.set(HexCoord(1, 0), "dwelling")
    grid.set(HexCoord(2, 0), "dwelling")
    
    # Test distances
    assert grid.distance(HexCoord(0, 0), HexCoord(0, 0)) == 0
    assert grid.distance(HexCoord(0, 0), HexCoord(1, 0)) == 1
    assert grid.distance(HexCoord(0, 0), HexCoord(2, 0)) == 2
    assert grid.distance(HexCoord(0, 0), HexCoord(1, 1)) == 2
    
    print("✓ Distance calculation working")


def test_power_bowl_adjacency() -> None:
    """Test finding adjacent opponents for power gain."""
    building_grid: HexGrid[tuple[str, BuildingType]] = HexGrid()
    
    # Place player buildings
    building_grid.set(HexCoord(0, 0), ("player1", "dwelling"))
    building_grid.set(HexCoord(1, 0), ("player1", "trading_house"))
    
    # Place opponent buildings adjacent
    building_grid.set(HexCoord(0, 1), ("player2", "dwelling"))
    building_grid.set(HexCoord(-1, 0), ("player3", "dwelling"))
    
    # When player2 upgrades at (0, 1), find adjacent opponents
    upgrade_location = HexCoord(0, 1)
    adjacent_opponents = []

    for coord, (owner, building) in building_grid.get_filled_neighbors(upgrade_location):
        if owner != "player2":
            # Calculate power value (dwelling=1, trading_house=2)
            power_value = 1 if building == "dwelling" else 2
            adjacent_opponents.append((owner, coord, power_value))
    
    # Should find both player1 buildings adjacent
    assert len(adjacent_opponents) == 2
    
    # Check we found both buildings with correct power values
    found_buildings = {(owner, power) for owner, coord, power in adjacent_opponents}
    assert ("player1", 1) in found_buildings  # dwelling
    assert ("player1", 2) in found_buildings  # trading_house
    
    print("✓ Power bowl adjacency detection working")


def test_pathfinding_for_connected_areas() -> None:
    """Test pathfinding to determine connected building areas."""
    building_grid: HexGrid[str] = HexGrid()
    
    # Create two separate groups
    # Group 1
    building_grid.set(HexCoord(0, 0), "player1")
    building_grid.set(HexCoord(1, 0), "player1")
    building_grid.set(HexCoord(2, 0), "player1")
    
    # Group 2 (separated)
    building_grid.set(HexCoord(0, 2), "player1")
    building_grid.set(HexCoord(1, 2), "player1")
    
    # Check if groups are connected
    path = building_grid.find_path(
        HexCoord(0, 0), 
        HexCoord(0, 2),
        is_passable=lambda c: c in building_grid and building_grid.get(c) == "player1"
    )
    
    # Should be no path between the groups
    assert path is None
    
    # Add connecting building
    building_grid.set(HexCoord(1, 1), "player1")
    
    # Now should find a path
    path = building_grid.find_path(
        HexCoord(0, 0),
        HexCoord(0, 2), 
        is_passable=lambda c: c in building_grid and building_grid.get(c) == "player1"
    )
    
    assert path is not None
    assert len(path) >= 3  # At least start, middle, end
    
    print("✓ Pathfinding for connected areas working")


def test_range_queries_for_cult_bonuses() -> None:
    """Test range queries for area effects like cult bonuses."""
    grid: HexGrid[str] = HexGrid()
    
    # Place a temple that gives bonuses in range
    temple_location = HexCoord(0, 0)
    grid.set(temple_location, "temple")
    
    # Get all hexes within range 2 (for cult bonus effects)
    affected_hexes = grid.get_range(temple_location, 2)
    
    # Should include center + 6 at distance 1 + 12 at distance 2 = 19 total
    assert len(affected_hexes) == 19
    
    # Verify center is included
    assert temple_location in affected_hexes
    
    # Verify correct distances
    for hex_coord in affected_hexes:
        distance = grid.distance(temple_location, hex_coord) 
        assert distance <= 2
    
    print("✓ Range queries for area effects working")


def run_all_tests() -> None:
    """Run all tests."""
    print("Running HexCoord and HexGrid tests for Terra Mystica...\n")
    
    # Basic functionality
    test_hexcoord_flyweight()
    test_hexcoord_properties()
    test_hex_neighbors()
    
    # Terra Mystica specific mechanics
    test_terra_mystica_terrain_placement()
    test_building_placement_rules()
    test_distance_for_area_scoring()
    test_power_bowl_adjacency()
    test_pathfinding_for_connected_areas()
    test_range_queries_for_cult_bonuses()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_all_tests()
