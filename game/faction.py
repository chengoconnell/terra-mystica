"""Faction module for Terra Mystica.

This module defines factions and their unique abilities using the Strategy pattern.
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping, Protocol

from .core import Resource
from .structures import StructureType


class Faction(Enum):
    """Available factions in the game.

    TYPE: Enum for a finite set of faction choices.
    """

    WITCHES = "Witches"
    MERMAIDS = "Mermaids"
    GIANTS = "Giants"


class FactionAbility(Protocol):
    """Protocol defining the contract for faction-specific data and logic.

    PATTERN: Strategy pattern - defines interface for interchangeable faction behaviors.
    TYPE: typing.Protocol for structural subtyping.
    """

    @property
    def home_terrain(self) -> str:
        """The faction's preferred terrain type."""
        ...

    @property
    def initial_resources(self) -> Mapping[Resource, int]:
        """Starting resources for this faction."""
        ...

    @property
    def initial_power(self) -> tuple[int, int]:
        """Initial power distribution (bowl1_and_2, bowl3)."""
        ...

    @property
    def initial_structure_supply(self) -> Mapping[StructureType, int]:
        """Number of each structure type available to build."""
        ...


class WitchesAbility:
    """Concrete strategy for the Witches faction."""

    @property
    def home_terrain(self) -> str:
        return "Forest"

    @property
    def initial_resources(self) -> Mapping[Resource, int]:
        return {Resource.COIN: 15, Resource.WORKER: 3}

    @property
    def initial_power(self) -> tuple[int, int]:
        return (5, 7)  # 5 in bowl I/II, 7 in bowl III

    @property
    def initial_structure_supply(self) -> Mapping[StructureType, int]:
        return {
            StructureType.DWELLING: 8,
            StructureType.TRADING_HOUSE: 4,
            StructureType.TEMPLE: 3,
            StructureType.SANCTUARY: 1,
            StructureType.STRONGHOLD: 1,
        }


class MermaidsAbility:
    """Concrete strategy for the Mermaids faction."""

    @property
    def home_terrain(self) -> str:
        return "Lakes"

    @property
    def initial_resources(self) -> Mapping[Resource, int]:
        return {Resource.COIN: 15, Resource.WORKER: 3}

    @property
    def initial_power(self) -> tuple[int, int]:
        return (4, 8)  # 4 in bowl I/II, 8 in bowl III

    @property
    def initial_structure_supply(self) -> Mapping[StructureType, int]:
        return {
            StructureType.DWELLING: 8,
            StructureType.TRADING_HOUSE: 4,
            StructureType.TEMPLE: 3,
            StructureType.SANCTUARY: 1,
            StructureType.STRONGHOLD: 1,
        }


class GiantsAbility:
    """Concrete strategy for the Giants faction."""

    @property
    def home_terrain(self) -> str:
        return "Wasteland"

    @property
    def initial_resources(self) -> Mapping[Resource, int]:
        return {Resource.COIN: 15, Resource.WORKER: 3}

    @property
    def initial_power(self) -> tuple[int, int]:
        return (3, 9)  # 3 in bowl I/II, 9 in bowl III

    @property
    def initial_structure_supply(self) -> Mapping[StructureType, int]:
        return {
            StructureType.DWELLING: 8,
            StructureType.TRADING_HOUSE: 4,
            StructureType.TEMPLE: 3,
            StructureType.SANCTUARY: 1,
            StructureType.STRONGHOLD: 1,
        }


# Registry mapping factions to their abilities
#
# DATASTRUCT: Strategy registry mapping faction enums to their ability implementations.
# This dictionary enables O(1) lookup of faction-specific behaviors and data,
# supporting the Strategy pattern by allowing runtime selection of faction
# abilities based on player choice.

FACTION_ABILITY_MAP: Mapping[Faction, FactionAbility] = {
    Faction.WITCHES: WitchesAbility(),
    Faction.MERMAIDS: MermaidsAbility(),
    Faction.GIANTS: GiantsAbility(),
}
