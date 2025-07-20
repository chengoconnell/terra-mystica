"""Player module - manages player state, resources, and faction.

This module implements player management including resources, faction abilities,
and tracking of player progression in Terra Mystica.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Self, Protocol, Dict

from .board import TerrainType
from .resources import Resources, PowerBowls

if TYPE_CHECKING:
    from .game import Game


class FactionType(Enum):
    """
    The factions available in the game.

    TYPE: Enum for type-safe faction identification.

    Simplified from full Terra Mystica: Starting with 3 core factions
    instead of all 14. Each faction has unique abilities and home terrain.
    """

    # Wasteland factions
    CHAOS_MAGICIANS = auto()
    # Mountain factions
    DWARVES = auto()
    # Plains factions
    HALFLINGS = auto()


@dataclass
class FactionData:
    """
    Static data about a faction.

    TYPE: Data class bundling faction properties.
    """

    name: str
    home_terrain: TerrainType
    starting_resources: Resources
    special_ability: str
    # Simplified: Omitting exchange rates, stronghold abilities, etc.


# Faction definitions
FACTION_DATA: Dict[FactionType, FactionData] = {
    FactionType.CHAOS_MAGICIANS: FactionData(
        name="Chaos Magicians",
        home_terrain=TerrainType.WASTELAND,
        starting_resources=Resources(
            workers=4,
            coins=15,
            priests=0,
            power_bowls=PowerBowls((5, 7, 0)),  # 5 in Bowl I, 7 in Bowl II
        ),
        special_ability="Can use double spades on one action",
    ),
    FactionType.DWARVES: FactionData(
        name="Dwarves",
        home_terrain=TerrainType.MOUNTAINS,
        starting_resources=Resources(
            workers=3,
            coins=15,
            priests=0,
            power_bowls=PowerBowls((5, 7, 0)),
        ),
        special_ability="Tunneling: Can build through mountains",
    ),
    FactionType.HALFLINGS: FactionData(
        name="Halflings",
        home_terrain=TerrainType.PLAINS,
        starting_resources=Resources(
            workers=3,
            coins=15,
            priests=0,
            power_bowls=PowerBowls((5, 7, 0)),
        ),
        special_ability="Gain 1 additional spade per spade action",
    ),
}


class Player:
    """
    Represents a player in the game.

    PATTERN: Part of the Facade pattern - created and managed by Game class.
    PATTERN: Context for Strategy pattern - holds faction-specific behavior.

    Players should not be instantiated directly by library users.
    All player interaction happens through the Game facade.

    Simplified from full Terra Mystica:
    - No favor tiles or bonus cards
    - Basic terraforming and shipping tracks
    - Simplified power actions
    """

    _game: Game
    _faction: FactionType
    _resources: Resources
    _terraforming_level: int  # 0-3, reduces spade cost
    _shipping_level: int  # 0-3, allows river crossing
    _victory_points: int
    _passed: bool  # Whether player has passed this round

    @classmethod
    def _create_for_game(cls, game: Game, faction: FactionType) -> Self:
        """
        Create a player instance for a game.

        This is a private factory method only for use by the Game class.
        """
        obj = object.__new__(cls)
        obj._game = game
        obj._faction = faction

        # Initialize with faction starting resources
        faction_data = FACTION_DATA[faction]
        obj._resources = faction_data.starting_resources

        # Starting track levels
        obj._terraforming_level = 0
        obj._shipping_level = 0
        obj._victory_points = 20  # Standard starting VP
        obj._passed = False

        return obj

    def get_faction(self) -> FactionType:
        """Get the player's faction."""
        return self._faction

    def get_faction_name(self) -> str:
        """Get the faction's display name."""
        return FACTION_DATA[self._faction].name

    def get_home_terrain(self) -> TerrainType:
        """Get the faction's home terrain type."""
        return FACTION_DATA[self._faction].home_terrain

    def get_resources(self) -> Resources:
        """Get a copy of the player's current resources."""
        return self._resources

    def get_victory_points(self) -> int:
        """Get the player's current victory points."""
        return self._victory_points

    def get_terraforming_level(self) -> int:
        """Get the player's terraforming track level (0-3)."""
        return self._terraforming_level

    def get_shipping_level(self) -> int:
        """Get the player's shipping track level (0-3)."""
        return self._shipping_level

    def get_spade_cost(self, distance: int) -> Resources:
        """
        Calculate the cost to terraform based on distance.

        Distance is the number of terrain steps (1-3).
        Terraforming track reduces the cost.
        """
        if distance < 1 or distance > 3:
            raise ValueError(f"Invalid terraform distance: {distance}")

        # Base cost: 3 workers per spade
        # Each terraforming level reduces cost by 1 worker
        workers_per_spade = max(1, 3 - self._terraforming_level)
        total_workers = workers_per_spade * distance

        return Resources(workers=total_workers)

    def has_passed(self) -> bool:
        """Check if the player has passed this round."""
        return self._passed

    def pass_turn(self) -> None:
        """Mark the player as having passed for this round."""
        self._passed = True

    def reset_for_new_round(self) -> None:
        """Reset player state for a new round."""
        self._passed = False

    def spend_resources(self, cost: Resources) -> None:
        """
        Spend resources from the player's pool.

        Raises:
            ValueError: If player cannot afford the cost
        """
        self._resources = self._resources.subtract(cost)

    def gain_resources(self, income: Resources) -> None:
        """Add resources to the player's pool."""
        self._resources = self._resources.add(income)

    def gain_power(self, amount: int) -> None:
        """
        Gain power tokens following bowl progression rules.

        Power tokens move from Bowl I → II → III.
        """
        self._resources = self._resources.gain_power(amount)

    def gain_victory_points(self, points: int) -> None:
        """Add victory points to the player's total."""
        if points < 0:
            raise ValueError(f"Cannot gain negative victory points: {points}")
        self._victory_points += points

    def advance_terraforming(self) -> None:
        """
        Advance on the terraforming track.

        Simplified from full Terra Mystica: Just tracks 0-3 levels.
        """
        if self._terraforming_level >= 3:
            raise ValueError("Terraforming already at maximum level")
        self._terraforming_level += 1

    def advance_shipping(self) -> None:
        """
        Advance on the shipping track.

        Simplified from full Terra Mystica: Just tracks 0-3 levels.
        """
        if self._shipping_level >= 3:
            raise ValueError("Shipping already at maximum level")
        self._shipping_level += 1

    def get_income(self) -> Resources:
        """
        Calculate the player's income for the income phase.

        Simplified from full Terra Mystica: Basic income based on
        structures, no bonus cards or favor tiles.
        """
        # Base income
        workers = 1  # Base worker income
        coins = 0
        priests = 0
        power = 0

        # TODO: Add income from structures on board
        # Each trading house gives +2 coins
        # Each temple gives +1 priest
        # Stronghold gives faction-specific income

        # Create power bowls for income (power starts in bowl I)
        power_bowls = PowerBowls((power, 0, 0)) if power > 0 else PowerBowls()

        return Resources(
            workers=workers,
            coins=coins,
            priests=priests,
            power_bowls=power_bowls,
        )
