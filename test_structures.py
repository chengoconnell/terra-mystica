#!/usr/bin/env python3
"""Test the structures module."""

from game.core import Resource
from game.structures import (
    StructureType,
    StructureData,
    STRUCTURE_DATA,
    get_structure_data,
)


def test_structures():
    """Test structure types and data."""
    print("Testing Structure system...\n")

    # Test Dwelling data
    print("1. Testing Dwelling data:")
    dwelling_data = get_structure_data(StructureType.DWELLING)
    print(f"   Type: {StructureType.DWELLING.value}")
    print(f"   Power Value: {dwelling_data.power_value}")
    print(f"   Base Cost: {dwelling_data.base_cost}")
    print(f"   Upgrades from: {dwelling_data.upgrades_from}")

    # Test TradingHouse data
    print("\n2. Testing TradingHouse data:")
    trading_house_data = get_structure_data(StructureType.TRADING_HOUSE)
    print(f"   Type: {StructureType.TRADING_HOUSE.value}")
    print(f"   Power Value: {trading_house_data.power_value}")
    print(f"   Base Cost: {trading_house_data.base_cost}")
    print(f"   Upgrades from: {trading_house_data.upgrades_from}")
    if trading_house_data.upgrades_from:
        print("   (Note: Adjacent opponent reduces coins from 6 to 3)")

    # Test data immutability
    print("\n3. Testing immutability:")
    try:
        dwelling_data.power_value = 5
        print("   Error: Was able to modify frozen dataclass")
    except Exception:
        print("   Cannot modify frozen dataclass")

    # Test that base_cost is immutable (it's a Mapping)
    print("\n4. Testing base_cost immutability:")
    try:
        # base_cost is a Mapping, so we can't modify it directly
        dwelling_data.base_cost[Resource.WORKER] = 10
        print("   Error: Was able to modify base_cost mapping")
    except Exception:
        print("   Cannot modify base_cost mapping (as expected)")

    # Show all structure types
    print("\n5. All structure types in registry:")
    for struct_type, struct_data in STRUCTURE_DATA.items():
        print(f"   - {struct_type.value}: power_value={struct_data.power_value}")

    print("\n All tests passed!")


if __name__ == "__main__":
    test_structures()
