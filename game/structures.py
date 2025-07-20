"""Structures module - building types and upgrade paths.

This module defines the various structure types in Terra Mystica,
their costs, upgrade paths, and associated game mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set

from .resources import Resources, PowerBowls


class StructureType(Enum):
    """
    Types of structures that can be built.

    TYPE: Enum for type-safe structure identification.
    """

    DWELLING = auto()
    TRADING_HOUSE = auto()
    TEMPLE = auto()
    SANCTUARY = auto()
    STRONGHOLD = auto()


@dataclass(frozen=True)
class StructureData:
    """
    Static data about a structure type.

    TYPE: Frozen dataclass for immutable structure properties.
    """

    name: str
    power_value: int  # For calculating towns and adjacency bonuses
    base_cost: Resources  # Cost to build (not upgrade)
    income: Resources  # Income provided during income phase
    victory_points: int = 0  # VP awarded when built/upgraded
    max_per_player: Optional[int] = None  # None means unlimited


# Structure definitions
STRUCTURE_DATA: Dict[StructureType, StructureData] = {
    StructureType.DWELLING: StructureData(
        name="Dwelling",
        power_value=1,
        base_cost=Resources(workers=1, coins=2),
        income=Resources(workers=1),  # Dwellings provide worker income
        victory_points=2,
        max_per_player=None,  # Unlimited dwellings
    ),
    StructureType.TRADING_HOUSE: StructureData(
        name="Trading House",
        power_value=2,
        base_cost=Resources(workers=2, coins=3),  # Base cost before adjacency discount
        income=Resources(coins=2),  # Trading houses provide coin income
        victory_points=3,
        max_per_player=None,  # Unlimited trading houses
    ),
    StructureType.TEMPLE: StructureData(
        name="Temple",
        power_value=2,
        base_cost=Resources(workers=2, coins=5),
        income=Resources(priests=1),  # Priest income
        victory_points=3,
        max_per_player=None,  # Can have multiple temples
    ),
    StructureType.SANCTUARY: StructureData(
        name="Sanctuary",
        power_value=3,
        base_cost=Resources(workers=4, coins=6),
        income=Resources(priests=1),  # Also priest income
        victory_points=5,
        max_per_player=1,  # Only one sanctuary per player
    ),
    StructureType.STRONGHOLD: StructureData(
        name="Stronghold",
        power_value=3,
        base_cost=Resources(workers=4, coins=6),
        income=Resources(),  # Strongholds provide special abilities, not regular income
        victory_points=5,
        max_per_player=1,  # Only one stronghold per player
    ),
}


@dataclass(frozen=True)
class UpgradePath:
    """
    Represents a valid structure upgrade path.

    PATTERN: Value Object - Immutable representation of upgrade rules.
    """

    from_structure: StructureType
    to_structure: StructureType
    cost: Resources  # Additional cost beyond base building cost


# Valid upgrade paths
UPGRADE_PATHS: List[UpgradePath] = [
    # Dwelling upgrades
    UpgradePath(
        from_structure=StructureType.DWELLING,
        to_structure=StructureType.TRADING_HOUSE,
        cost=Resources(workers=2, coins=3),
    ),
    # Trading House upgrades (player chooses one path)
    UpgradePath(
        from_structure=StructureType.TRADING_HOUSE,
        to_structure=StructureType.TEMPLE,
        cost=Resources(workers=2, coins=5),
    ),
    UpgradePath(
        from_structure=StructureType.TRADING_HOUSE,
        to_structure=StructureType.STRONGHOLD,
        cost=Resources(workers=4, coins=6),
    ),
    # Temple upgrade
    UpgradePath(
        from_structure=StructureType.TEMPLE,
        to_structure=StructureType.SANCTUARY,
        cost=Resources(workers=4, coins=6),
    ),
]


def get_structure_data(structure_type: StructureType) -> StructureData:
    """Get the static data for a structure type."""
    return STRUCTURE_DATA[structure_type]


def get_upgrade_paths_from(structure_type: StructureType) -> List[StructureType]:
    """
    Get valid upgrade targets from a given structure type.

    Returns a list of structure types this can be upgraded to.
    """
    return [
        path.to_structure
        for path in UPGRADE_PATHS
        if path.from_structure == structure_type
    ]


def get_upgrade_cost(
    from_structure: StructureType, to_structure: StructureType
) -> Optional[Resources]:
    """
    Get the cost to upgrade from one structure to another.

    Returns None if the upgrade path is not valid.
    """
    for path in UPGRADE_PATHS:
        if path.from_structure == from_structure and path.to_structure == to_structure:
            return path.cost
    return None


def can_build_structure(
    structure_type: StructureType,
    existing_structures: Set[StructureType],
) -> bool:
    """
    Check if a structure type can be built given existing structures.

    This enforces max per player limits.

    Simplified from full Terra Mystica: Not checking faction-specific
    stronghold abilities or special building rules.
    """
    data = get_structure_data(structure_type)

    # Check max per player limit
    if data.max_per_player is not None:
        count = sum(1 for s in existing_structures if s == structure_type)
        if count >= data.max_per_player:
            return False

    return True


def calculate_town_power(structures: List[StructureType]) -> int:
    """
    Calculate the total power value of a group of structures.

    Used for determining if structures form a town (7+ power).
    """
    return sum(get_structure_data(s).power_value for s in structures)


def is_town(structures: List[StructureType]) -> bool:
    """
    Check if a group of connected structures forms a town.

    A town requires connected structures with total power value >= 7.

    Simplified from full Terra Mystica: Not checking for minimum
    4 structures requirement.
    """
    return calculate_town_power(structures) >= 7
