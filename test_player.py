"""
Tests for player module.

Validates player mechanics including resource management, power gain,
adjacency effects, and faction abilities against simplified Terra Mystica rules.
"""

import traceback
from typing import Any
from unittest.mock import Mock, MagicMock

from game.coords import HexCoord
from game.game import Game
from game.player import Player
from game.types import (
    BuildingType,
    FactionType,
    ResourceCost,
    TerrainType,
)


def test_player_construction() -> None:
    """Test that players can only be constructed through Game class."""
    # Direct construction should fail
    try:
        Player(Mock(), "Test", FactionType.WITCHES)
        assert False, "Should not allow direct construction"
    except TypeError as e:
        assert "cannot be constructed directly" in str(e)

    # Construction through Game should work (Game sets the flag)
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        board_mock = Mock()
        board_mock.get_adjacent_positions = Mock(return_value=[])
        game_mock.board = board_mock

        player = Player(game_mock, "Test", FactionType.WITCHES)
        assert player.name == "Test"
        assert player.faction == FactionType.WITCHES
    finally:
        Player._set_constructing(False)


def test_initial_resources() -> None:
    """Test initial resource state matches rules."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.ENGINEERS)

        # From DEFAULT_GAME_CONFIG
        assert player.resources["workers"] == 3
        assert player.resources["coins"] == 15
        assert player.victory_points == 20

        # Power bowls: 5 in bowl I, 7 in bowl II
        power_state = player.power_state
        assert power_state["bowl_1"] == 5
        assert power_state["bowl_2"] == 7
        assert power_state["bowl_3"] == 0

        # No buildings initially
        assert len(player.buildings) == 0
        assert player.cult_position == 0
        assert not player.has_passed
    finally:
        Player._set_constructing(False)


def test_resource_management() -> None:
    """Test can_afford, pay_cost, and gain_resources."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.NOMADS)

        # Test can_afford
        assert player.can_afford({"workers": 2, "coins": 10})
        assert player.can_afford({"workers": 3, "coins": 15})
        assert not player.can_afford({"workers": 4, "coins": 10})
        assert not player.can_afford({"workers": 2, "coins": 20})

        # Test pay_cost
        player.pay_cost({"workers": 1, "coins": 5})
        assert player.resources["workers"] == 2
        assert player.resources["coins"] == 10

        # Test gain_resources
        player.gain_resources({"workers": 2, "coins": 7})
        assert player.resources["workers"] == 4
        assert player.resources["coins"] == 17

        # Test paying more than available raises error
        try:
            player.pay_cost({"workers": 10, "coins": 5})
            assert False, "Should raise error for insufficient resources"
        except ValueError as e:
            assert "Insufficient" in str(e)
    finally:
        Player._set_constructing(False)


def test_building_management() -> None:
    """Test adding, removing, and tracking buildings."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.WITCHES)

        # Test adding buildings
        pos1 = HexCoord(0, 0)
        pos2 = HexCoord(1, 0)
        pos3 = HexCoord(0, 1)

        player.add_building(pos1, BuildingType.DWELLING)
        player.add_building(pos2, BuildingType.DWELLING)
        player.add_building(pos3, BuildingType.TRADING_HOUSE)

        # Check buildings are tracked
        buildings = player.buildings
        assert len(buildings) == 3
        assert buildings[pos1] == BuildingType.DWELLING
        assert buildings[pos2] == BuildingType.DWELLING
        assert buildings[pos3] == BuildingType.TRADING_HOUSE

        # Test building count
        assert player.get_building_count(BuildingType.DWELLING) == 2
        assert player.get_building_count(BuildingType.TRADING_HOUSE) == 1

        # Test can't add to same position
        try:
            player.add_building(pos1, BuildingType.TRADING_HOUSE)
            assert False, "Should not allow building at same position"
        except ValueError as e:
            assert "already has building" in str(e)

        # Test removing buildings
        removed = player.remove_building(pos2)
        assert removed == BuildingType.DWELLING
        assert len(player.buildings) == 2
        assert player.get_building_count(BuildingType.DWELLING) == 1

        # Test removing from empty position
        try:
            player.remove_building(pos2)
            assert False, "Should not allow removing from empty position"
        except ValueError as e:
            assert "No building at position" in str(e)
    finally:
        Player._set_constructing(False)


def test_calculate_adjacent_power() -> None:
    """Test power calculation from adjacent buildings."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.ENGINEERS)

        # Add some buildings
        pos1 = HexCoord(0, 0)
        pos2 = HexCoord(1, 0)
        pos3 = HexCoord(0, 1)

        player.add_building(pos1, BuildingType.DWELLING)  # Power value 1
        player.add_building(pos2, BuildingType.TRADING_HOUSE)  # Power value 2

        # Test power calculation
        # Simulating that pos1 and pos2 are adjacent to some new building
        power_option = player.calculate_adjacent_power(
            [pos1, pos2, pos3]
        )  # pos3 has no building

        assert power_option["power_gain"] == 3  # 1 + 2
        assert power_option["vp_cost"] == 2  # max(0, 3 - 1)
        assert len(power_option["from_buildings"]) == 2

        # Test with no adjacent buildings
        power_option = player.calculate_adjacent_power([pos3])
        assert power_option["power_gain"] == 0
        assert power_option["vp_cost"] == 0
        assert len(power_option["from_buildings"]) == 0
    finally:
        Player._set_constructing(False)


def test_power_gain_and_vp_loss() -> None:
    """Test power gain mechanics and VP cost."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.NOMADS)

        # Initial state
        assert player.victory_points == 20

        # Test gaining power (mocked PowerBowls)
        player.gain_power(3)
        # Power bowls state would change, but we're testing the interface

        # Test losing VP
        player.lose_victory_points(2)
        assert player.victory_points == 18

        # Test VP can't go below 0
        player.lose_victory_points(20)
        assert player.victory_points == 0

        # Test gaining VP
        player.gain_victory_points(5)
        assert player.victory_points == 5
    finally:
        Player._set_constructing(False)


def test_notify_adjacent_building() -> None:
    """Test Observer pattern for power gain from opponent buildings."""
    Player._set_constructing(True)
    try:
        # Create game mock with board
        game_mock = Mock(spec=Game)
        board_mock = Mock()
        game_mock.board = board_mock

        # Create two players
        player1 = Player(game_mock, "Player1", FactionType.WITCHES)
        player2 = Player(game_mock, "Player2", FactionType.ENGINEERS)

        # Player1 has buildings that will be adjacent
        pos1 = HexCoord(0, 0)
        pos2 = HexCoord(1, 0)
        player1.add_building(pos1, BuildingType.DWELLING)  # Power 1
        player1.add_building(pos2, BuildingType.TRADING_HOUSE)  # Power 2

        # Mock board to return player1's positions as adjacent
        new_pos = HexCoord(1, 1)
        board_mock.get_adjacent_positions.return_value = [pos1, pos2]

        # Test notification when player2 builds
        # Player1 has enough VP (20) and needs power (has 0 in bowl III)
        accepted = player1.notify_adjacent_building(
            "Player2", new_pos, BuildingType.DWELLING
        )

        assert accepted  # Should accept power
        assert player1.victory_points == 18  # Lost 2 VP (3 power - 1)

        # Test not accepting from own buildings
        accepted = player1.notify_adjacent_building(
            "Player1", new_pos, BuildingType.DWELLING
        )
        assert not accepted  # No power from own buildings

        # Test with no adjacent buildings
        board_mock.get_adjacent_positions.return_value = []
        accepted = player1.notify_adjacent_building(
            "Player2", HexCoord(5, 5), BuildingType.DWELLING
        )
        assert not accepted  # No adjacent buildings
    finally:
        Player._set_constructing(False)


def test_faction_ability_integration() -> None:
    """Test faction abilities modify costs correctly."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)

        # Test Engineers - half cost building upgrade
        engineer = Player(game_mock, "Eng", FactionType.ENGINEERS)
        base_cost: ResourceCost = {"workers": 2, "coins": 6}
        modified = engineer.modify_building_cost(base_cost)
        assert modified["workers"] == 1  # Halved
        assert modified["coins"] == 3  # Halved

        # Test Nomads - reduce terrain cost by 1 (minimum 1)
        nomad = Player(game_mock, "Nom", FactionType.NOMADS)
        assert nomad.modify_terrain_cost(3) == 2
        assert nomad.modify_terrain_cost(2) == 1
        assert nomad.modify_terrain_cost(1) == 1  # Minimum is 1
        assert nomad.modify_terrain_cost(0) == 1  # Even 0 becomes 1

        # Test Witches - no special ability
        witch = Player(game_mock, "Wit", FactionType.WITCHES)
        assert witch.modify_building_cost(base_cost) == base_cost
        assert witch.modify_terrain_cost(3) == 3
    finally:
        Player._set_constructing(False)


def test_cult_track() -> None:
    """Test cult track advancement."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.NOMADS)

        # Initial position
        assert player.cult_position == 0

        # Advance on track
        player.advance_cult(3)
        assert player.cult_position == 3

        player.advance_cult(5)
        assert player.cult_position == 8

        # Test maximum position (from config)
        player.advance_cult(10)
        assert player.cult_position == 10  # Capped at max
    finally:
        Player._set_constructing(False)


def test_end_turn() -> None:
    """Test passing mechanism."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)
        player = Player(game_mock, "Test", FactionType.WITCHES)

        assert not player.has_passed
        player.end_turn()
        assert player.has_passed
    finally:
        Player._set_constructing(False)


def test_home_terrain() -> None:
    """Test faction home terrain mapping."""
    Player._set_constructing(True)
    try:
        game_mock = Mock(spec=Game)

        # Test each faction's home terrain
        witch = Player(game_mock, "W", FactionType.WITCHES)
        assert witch.home_terrain == TerrainType.FOREST

        engineer = Player(game_mock, "E", FactionType.ENGINEERS)
        assert engineer.home_terrain == TerrainType.MOUNTAINS

        nomad = Player(game_mock, "N", FactionType.NOMADS)
        assert nomad.home_terrain == TerrainType.DESERT
    finally:
        Player._set_constructing(False)


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_player_construction,
        test_initial_resources,
        test_resource_management,
        test_building_management,
        test_calculate_adjacent_power,
        test_power_gain_and_vp_loss,
        test_notify_adjacent_building,
        test_faction_ability_integration,
        test_cult_track,
        test_end_turn,
        test_home_terrain,
    ]
    
    print("Running player tests...")
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
