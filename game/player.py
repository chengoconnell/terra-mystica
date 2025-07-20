"""Player module for Terra Mystica.

This module defines the Player class which manages a player's state,
including their faction, resources, structures, and victory points.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from .coordinate import Coordinate
from .core import Resource, PowerBowls
from .resources import Resources
from .structures import StructureType
from .faction import FACTION_ABILITY_MAP

if TYPE_CHECKING:
    from .faction import Faction, FactionAbility
    from .types import StructureSupplyData


class Player:
    """Encapsulates all state and logic for a single player.

    PATTERN: Information Expert - manages all player-specific state and operations.
    PATTERN: Strategy - uses FactionAbility for faction-specific behavior.
    """

    _faction: Faction
    _ability_handler: FactionAbility
    _resources: Resources
    _victory_points: int  # Track VP separately from other resources

    _structures: dict[Coordinate, StructureType]
    """DATASTRUCT: Dictionary mapping board coordinates to structure types.
    
    This ownership registry tracks all structures built by the player, enabling
    O(1) lookup for structure queries and ensuring consistent state between
    the player's records and the board's placement tracking.
    """

    _structure_supply: dict[StructureType, int]
    """DATASTRUCT: Dictionary tracking remaining buildable structures.
    
    This inventory system enforces the physical component limits of the game,
    preventing players from building more structures than available. Each
    structure type has a maximum count that decreases as structures are built.
    """

    _shipping_level: int  # Ability to cross rivers (0-3)
    _spade_level: int  # Terraforming efficiency (1-3)
    _has_passed: bool  # Track if player has passed this round

    def __new__(cls, faction: Faction) -> Player:
        """Create a new player with the given faction.

        Constructor for Player, for use by Game only.

        PATTERN: Factory Method - Player instances can only be created through
        Game's factory methods to ensure proper registration and validation.

        Args:
            faction: The faction this player is playing

        Returns:
            A new Player instance with faction-specific starting conditions

        Raises:
            TypeError: If attempting to construct directly outside of Game
        """
        # Check if we're allowed to construct
        from .game import Game

        if not Game._is_constructing_player():
            raise TypeError(
                "Player instances cannot be constructed directly. Use Game constructor."
            )

        self = object.__new__(cls)
        self._faction = faction
        self._ability_handler = FACTION_ABILITY_MAP[faction]

        # Initialize resources with faction-specific values
        initial_res = self._ability_handler.initial_resources
        workers = initial_res.get(Resource.WORKER, 0)
        coins = initial_res.get(Resource.COIN, 0)

        # Create PowerBowls from initial power distribution
        initial_power_tuple = self._ability_handler.initial_power
        power_bowls = PowerBowls(
            bowl_1=initial_power_tuple[0],
            bowl_2=0,  # All initial power starts in bowls 1 and 3
            bowl_3=initial_power_tuple[1],
        )

        self._resources = Resources(workers=workers, coins=coins, power=power_bowls)

        # Track victory points separately
        self._victory_points = 20  # All players start with 20 VP

        # Initialize structure tracking
        self._structures = {}  # No structures placed initially
        self._structure_supply = dict(self._ability_handler.initial_structure_supply)

        # Initialize advancement tracks
        self._shipping_level = 0  # Start with no shipping ability
        self._spade_level = 3  # Start at spade level 3 (standard)

        self._has_passed = False
        return self

    @property
    def faction(self) -> Faction:
        """Get the player's faction (read-only)."""
        return self._faction

    @property
    def home_terrain(self) -> str:
        """Get the player's home terrain type."""
        return self._ability_handler.home_terrain

    @property
    def resources(self) -> Resources:
        """Get the player's current resources.

        Note: Returns the actual Resources object, not a copy.
        The Resources class itself handles encapsulation.
        """
        return self._resources

    @property
    def victory_points(self) -> int:
        """Get the player's current victory points."""
        return self._victory_points

    @property
    def shipping_level(self) -> int:
        """Get the player's current shipping level (0-3)."""
        return self._shipping_level

    @property
    def spade_level(self) -> int:
        """Get the player's current spade level (1-3)."""
        return self._spade_level

    @property
    def has_passed(self) -> bool:
        """Check if the player has passed this round."""
        return self._has_passed

    def get_structure_at(self, location: Coordinate) -> StructureType | None:
        """Get the structure type at a specific location.

        Args:
            location: The coordinate to check

        Returns:
            The structure type at that location, or None if empty
        """
        return self._structures.get(location)

    def get_all_structures(self) -> dict[Coordinate, StructureType]:
        """Get all structures owned by this player.

        Returns:
            A copy of the structures dictionary to prevent external modification
        """
        return self._structures.copy()

    def get_structure_supply(self) -> dict[StructureType, int]:
        """Get the current supply of each structure type.

        Returns:
            A copy of the structure supply to prevent external modification
        """
        return self._structure_supply.copy()

    def get_structure_supply_data(self) -> StructureSupplyData:
        """Get structure supply as a TypedDict.

        TYPE: Returns StructureSupplyData for type-safe access to counts.

        This method provides a structured view of remaining structures
        that can be safely used in type-checked code.

        Returns:
            StructureSupplyData with counts for each structure type
        """
        return StructureSupplyData(
            dwelling=self._structure_supply.get(StructureType.DWELLING, 0),
            trading_house=self._structure_supply.get(StructureType.TRADING_HOUSE, 0),
            temple=self._structure_supply.get(StructureType.TEMPLE, 0),
            sanctuary=self._structure_supply.get(StructureType.SANCTUARY, 0),
            stronghold=self._structure_supply.get(StructureType.STRONGHOLD, 0),
        )

    def add_victory_points(self, points: int) -> None:
        """Add victory points to the player's total.

        Args:
            points: Number of points to add (can be negative)
        """
        self._victory_points += points

    def mark_passed(self) -> None:
        """Mark this player as having passed for the current round.

        STAGING: Validates player hasn't already passed this round.

        Raises:
            ValueError: If player has already passed
        """
        if self._has_passed:
            raise ValueError("Player has already passed this round")
        self._has_passed = True

    def reset_pass_status(self) -> None:
        """Reset the pass status for a new round."""
        self._has_passed = False

    def build_structure(
        self, location: Coordinate, structure_type: StructureType
    ) -> None:
        """Build a structure at the specified location.

        STAGING: Validates no existing structure at location and structure available in supply.

        This method assumes validation (terrain, resources, etc.) has been
        done by the Game class. It records the placement and updates supply.

        Args:
            location: Where to build the structure
            structure_type: Type of structure to build

        Raises:
            ValueError: If there's already a structure at this location
            ValueError: If no structures of this type remain in supply
        """
        if location in self._structures:
            raise ValueError(f"Already have a structure at {location}")

        if self._structure_supply.get(structure_type, 0) <= 0:
            raise ValueError(f"No {structure_type.value} left in supply")

        self._structures[location] = structure_type
        self._structure_supply[structure_type] -= 1

    def upgrade_structure(self, location: Coordinate, new_type: StructureType) -> None:
        """Upgrade a structure at the specified location.

        STAGING: Validates structure exists at location and new structure type available in supply.

        This method assumes validation (valid upgrade path, resources, etc.)
        has been done by the Game class. Returns old structure to supply.

        Args:
            location: Location of the structure to upgrade
            new_type: The new structure type

        Raises:
            ValueError: If there's no structure at this location
            ValueError: If no structures of new type remain in supply
        """
        if location not in self._structures:
            raise ValueError(f"No structure at {location} to upgrade")

        if self._structure_supply.get(new_type, 0) <= 0:
            raise ValueError(f"No {new_type.value} left in supply")

        # Return old structure to supply
        old_type = self._structures[location]
        self._structure_supply[old_type] += 1

        # Place new structure and remove from supply
        self._structures[location] = new_type
        self._structure_supply[new_type] -= 1

    def advance_shipping(self) -> None:
        """Advance shipping level by 1 (max 3).

        STAGING: Validates shipping level not already at maximum (3).

        Raises:
            ValueError: If already at max shipping level
        """
        if self._shipping_level >= 3:
            raise ValueError("Already at maximum shipping level")
        self._shipping_level += 1

    def advance_spades(self) -> None:
        """Advance spade level by 1 (min 1).

        STAGING: Validates spade level not already at minimum (1).

        Raises:
            ValueError: If already at min spade level
        """
        if self._spade_level <= 1:
            raise ValueError("Already at minimum spade level (most efficient)")
        self._spade_level -= 1  # Lower number = more efficient

    def __repr__(self) -> str:
        """String representation of the player."""
        return f"Player(faction={self._faction.value}, vp={self.victory_points}, passed={self._has_passed})"
