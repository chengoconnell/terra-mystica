"""
Tests for faction abilities to verify they match Terra Mystica rules.

This test module verifies:
1. Factory pattern creates correct faction abilities
2. Each faction's abilities work as documented
3. Simplifications from full Terra Mystica are correctly implemented
"""

from types import MappingProxyType
from typing import Final

from game.faction import (
    BaseFactionAbility,
    EngineersAbility,
    FactionFactory,
    NomadsAbility,
    WitchesAbility,
)
from game.types import FactionType, ResourceCost, SpadeCount


# Test data constants
TERRAIN_COSTS: Final[dict[str, SpadeCount]] = {
    "adjacent": 1,
    "one_space": 2,
    "two_spaces": 3,
}

BUILDING_COSTS: Final[dict[str, ResourceCost]] = {
    "dwelling": {"workers": 1, "coins": 2, "power": 0, "spades": 0},
}


def test_faction_factory() -> None:
    """Test that factory creates correct faction ability instances."""
    # Test Witches
    witches = FactionFactory.create_ability(FactionType.WITCHES)
    assert isinstance(witches, WitchesAbility)
    assert isinstance(witches, BaseFactionAbility)

    # Test Engineers
    engineers = FactionFactory.create_ability(FactionType.ENGINEERS)
    assert isinstance(engineers, EngineersAbility)
    assert isinstance(engineers, BaseFactionAbility)

    # Test Nomads
    nomads = FactionFactory.create_ability(FactionType.NOMADS)
    assert isinstance(nomads, NomadsAbility)
    assert isinstance(nomads, BaseFactionAbility)

    print("✓ Factory creates correct faction instances")


def test_witches_ability() -> None:
    """
    Test Witches abilities match our simplified rules.

    In full Terra Mystica: Witches can build dwellings anywhere on forests
    without adjacency (Witches' Ride).

    Simplified: No special abilities - uses all defaults.
    """
    witches = WitchesAbility()

    # Test terrain cost modification (should be unchanged)
    for desc, base_cost in TERRAIN_COSTS.items():
        modified = witches.modify_terrain_cost(base_cost)
        assert modified == base_cost, f"Witches should not modify {desc} terrain cost"

    # Test building cost modification (should be unchanged)
    for desc, base_cost in BUILDING_COSTS.items():
        modified = witches.modify_building_cost(base_cost)
        assert modified == base_cost, f"Witches should not modify {desc} building cost"

    print("✓ Witches use default abilities (no modifications)")


def test_engineers_ability() -> None:
    """
    Test Engineers abilities match our simplified rules.

    In full Terra Mystica: Engineers have bridge-building abilities.

    Simplified: Half-cost building upgrades (workers and coins only).
    """
    engineers = EngineersAbility()

    # Test terrain cost modification (should be unchanged)
    for desc, base_cost in TERRAIN_COSTS.items():
        modified = engineers.modify_terrain_cost(base_cost)
        assert modified == base_cost, f"Engineers should not modify {desc} terrain cost"

    # Test building cost modification (should be halved for workers/coins)
    dwelling_cost = BUILDING_COSTS["dwelling"]
    modified_dwelling = engineers.modify_building_cost(dwelling_cost)
    assert modified_dwelling["workers"] == 0  # 1 // 2 = 0
    assert modified_dwelling["coins"] == 1  # 2 // 2 = 1
    assert modified_dwelling["power"] == 0  # Power not reduced
    assert modified_dwelling["spades"] == 0  # Spades not reduced

    upgrade_cost = BUILDING_COSTS["trading_house_upgrade"]
    modified_upgrade = engineers.modify_building_cost(upgrade_cost)
    assert modified_upgrade["workers"] == 1  # 2 // 2 = 1
    assert modified_upgrade["coins"] == 3  # 6 // 2 = 3
    assert modified_upgrade["power"] == 0  # Power not reduced
    assert modified_upgrade["spades"] == 0  # Spades not reduced

    print("✓ Engineers have half-cost building upgrades")


def test_nomads_ability() -> None:
    """
    Test Nomads abilities match our simplified rules.

    In full Terra Mystica: Nomads have starting advantages and terrain affinity.

    Simplified: Transform terrain costs 1 less spade (minimum 1).
    """
    nomads = NomadsAbility()

    # Test terrain cost modification (should be reduced by 1, min 1)
    assert nomads.modify_terrain_cost(1) == 1  # Can't go below 1
    assert nomads.modify_terrain_cost(2) == 1  # 2 - 1 = 1
    assert nomads.modify_terrain_cost(3) == 2  # 3 - 1 = 2

    # Test building cost modification (should be unchanged)
    for desc, base_cost in BUILDING_COSTS.items():
        modified = nomads.modify_building_cost(base_cost)
        assert modified == base_cost, f"Nomads should not modify {desc} building cost"

    print("✓ Nomads have -1 spade cost for terrain (minimum 1)")


def test_base_faction_ability() -> None:
    """Test that base faction ability provides correct defaults."""
    base = BaseFactionAbility()

    # Test all costs remain unchanged
    for desc, base_cost in TERRAIN_COSTS.items():
        modified = base.modify_terrain_cost(base_cost)
        assert modified == base_cost, f"Base should not modify {desc} terrain cost"

    for desc, base_cost in BUILDING_COSTS.items():
        modified = base.modify_building_cost(base_cost)
        assert modified == base_cost, f"Base should not modify {desc} building cost"

    print("✓ Base faction ability provides no modifications")


def test_edge_cases() -> None:
    """Test edge cases and boundary conditions."""
    # Test Engineers with zero costs
    engineers = EngineersAbility()
    zero_cost: ResourceCost = {"workers": 0, "coins": 0, "power": 0, "spades": 0}
    modified = engineers.modify_building_cost(zero_cost)
    assert all(v == 0 for v in modified.values())

    # Test Engineers with odd numbers (floor division)
    odd_cost: ResourceCost = {"workers": 3, "coins": 5, "power": 7, "spades": 9}
    modified = engineers.modify_building_cost(odd_cost)
    assert modified["workers"] == 1  # 3 // 2 = 1
    assert modified["coins"] == 2  # 5 // 2 = 2
    assert modified["power"] == 7  # Not reduced
    assert modified["spades"] == 9  # Not reduced

    # Test Nomads with very high spade costs
    nomads = NomadsAbility()
    assert nomads.modify_terrain_cost(100) == 99
    assert nomads.modify_terrain_cost(1000) == 999

    print("✓ Edge cases handled correctly")


def run_all_tests() -> None:
    """Run all faction tests."""
    print("Running faction ability tests...\n")

    test_faction_factory()
    test_witches_ability()
    test_engineers_ability()
    test_nomads_ability()
    test_base_faction_ability()
    test_edge_cases()

    print("\n✅ All faction tests passed!")
    print("\nSummary of simplifications from full Terra Mystica:")
    print("- Witches: No 'Witches Ride' ability (simplified to no special ability)")
    print("- Engineers: Half-cost buildings instead of bridge-building")
    print("- Nomads: -1 spade cost instead of complex starting advantages")


if __name__ == "__main__":
    run_all_tests()
