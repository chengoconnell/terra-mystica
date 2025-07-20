"""Structure types for Terra Mystica.

This module defines structure types using a data-driven approach with
enums and dataclasses, separating type identification from static data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Mapping

from .core import Resource


class StructureType(Enum):
    """Type: An enumeration of all possible structure types in the game."""

    DWELLING = "Dwelling"
    TRADING_HOUSE = "Trading House"
    TEMPLE = "Temple"
    SANCTUARY = "Sanctuary"
    STRONGHOLD = "Stronghold"


@dataclass(frozen=True)
class StructureData:
    """Type: An immutable dataclass to hold the static properties of a structure.

    This is a Value Object. Its identity is defined by its data.
    """

    power_value: int
    base_cost: Mapping[Resource, int]
    # The structure this one is upgraded from, if any.
    upgrades_from: StructureType | None = None


# =============================================================================
# The Structure Registry
# =============================================================================

# This dictionary acts as a central, immutable source of truth for all
# structure data, mapping the enum to its corresponding data object.
#
# DATASTRUCT: Registry pattern mapping structure types to their static data.
# This immutable dictionary serves as a centralized lookup table for structure
# properties, separating data from behavior. The registry pattern allows easy
# extension of structure types and ensures consistent access to structure
# metadata throughout the game engine.

STRUCTURE_DATA: Final[Mapping[StructureType, StructureData]] = {
    StructureType.DWELLING: StructureData(
        power_value=1,
        base_cost={Resource.WORKER: 1, Resource.COIN: 2},
    ),
    StructureType.TRADING_HOUSE: StructureData(
        power_value=2,
        # The base cost is 6 coins, as per the rulebook (p. 11).
        # The discount to 3 coins is a conditional rule handled by the
        # game logic, not a property of the structure itself.
        base_cost={Resource.WORKER: 2, Resource.COIN: 6},
        upgrades_from=StructureType.DWELLING,
    ),
    StructureType.TEMPLE: StructureData(
        power_value=2,
        base_cost={Resource.WORKER: 2, Resource.COIN: 5},
        upgrades_from=StructureType.TRADING_HOUSE,
    ),
    StructureType.SANCTUARY: StructureData(
        power_value=3,
        base_cost={Resource.WORKER: 4, Resource.COIN: 10},
        upgrades_from=StructureType.TEMPLE,
    ),
    StructureType.STRONGHOLD: StructureData(
        power_value=3,
        # Note: The cost for the Stronghold is faction-specific.
        # This base_cost would be overridden by faction-specific data.
        base_cost={Resource.WORKER: 4, Resource.COIN: 10},
        upgrades_from=StructureType.TRADING_HOUSE,
    ),
}


def get_structure_data(structure_type: StructureType) -> StructureData:
    """Get the static data for a structure type.

    Args:
        structure_type: The type of structure to get data for

    Returns:
        The static data for that structure type

    Raises:
        KeyError: If structure type not found in registry

    PATTERN: Registry. The STRUCTURE_DATA dictionary acts as a central,
         immutable registry to look up data for any given StructureType.
    """
    data = STRUCTURE_DATA[structure_type]
    assert isinstance(data, StructureData)
    return data
