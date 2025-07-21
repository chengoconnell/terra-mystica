"""Actions module - game actions using Command pattern.

This module implements the various actions players can take in Terra Mystica,
encapsulating game rules and validation logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Optional

from .structures import StructureType

if TYPE_CHECKING:
    from .board import AxialCoord, TerrainType
    from .game import Game
    from .player import Player


class Action(Protocol):
    """
    PATTERN: Command - Encapsulates game actions
    TYPE: Protocol defining action interface.
    """

    def validate(self, game: Game, player: Player) -> None:
        """Validate action. Raises ValueError if invalid."""
        ...

    def execute(self, game: Game, player: Player) -> None:
        """Execute action, modifying game state."""
        ...

    def describe(self) -> str:
        """Get a human-readable description of this action."""
        ...


class BaseAction(ABC):
    """
    Abstract base class for actions.
    PATTERN: Template Method - Common validation with hooks.
    """

    def validate(self, game: Game, player: Player) -> None:
        """Common validation for all actions."""
        # Check game state
        if game.get_phase().name != "ACTIONS":
            raise ValueError("Actions can only be taken during action phase")

        # Check if it's this player's turn
        current = game.get_current_player()
        if current != player:
            raise ValueError("Not this player's turn")

        # Check if player has passed
        if player.has_passed():
            raise ValueError("Player has already passed this round")

        # Subclass-specific validation
        self._validate_specific(game, player)

    @abstractmethod
    def _validate_specific(self, game: Game, player: Player) -> None:
        """Subclass-specific validation logic."""
        ...

    @abstractmethod
    def execute(self, game: Game, player: Player) -> None:
        """Execute the action."""
        ...


@dataclass
class PassAction(BaseAction):
    """Action to pass for the round."""

    def _validate_specific(self, game: Game, player: Player) -> None:
        """No additional validation needed for passing."""
        pass

    def execute(self, game: Game, player: Player) -> None:
        """Mark the player as having passed."""
        player.pass_turn()
        # Notify the round manager to check if all players have passed
        game.get_round_manager().player_pass(player)

    def describe(self) -> str:
        """Describe the pass action."""
        return "Pass for the rest of the round"


@dataclass
class BuildAction(BaseAction):
    """Build structure action."""

    coord: AxialCoord
    structure_type: StructureType

    def _validate_specific(self, game: Game, player: Player) -> None:
        """Validate the build action."""
        board = game.get_board()

        # Get the hex
        hex_space = board.get_hex(self.coord)
        if not hex_space:
            raise ValueError(f"Invalid coordinate: {self.coord}")

        # Check terrain is player's home terrain
        if hex_space.terrain != player.get_home_terrain():
            raise ValueError(
                f"Can only build on home terrain {player.get_home_terrain()}, "
                f"but hex is {hex_space.terrain}"
            )

        # Check hex is empty
        if hex_space.owner is not None:
            raise ValueError("Hex already occupied")

        # For non-dwelling structures, check upgrade path
        from .structures import StructureType as ST

        if self.structure_type != ST.DWELLING:
            raise ValueError(
                "Can only build dwellings directly. "
                "Other structures must be upgraded from existing buildings."
            )

        # Check adjacency to existing structures
        player_structures = board.get_structures_of_player(player)
        if player_structures:  # If player has structures, must be adjacent
            if not board.is_hex_reachable_by_player(self.coord, player):
                raise ValueError(
                    "New structures must be adjacent to existing structures "
                    "(directly or via shipping)"
                )

        # Check resources
        from .structures import get_structure_data

        cost = get_structure_data(self.structure_type).base_cost
        if not player.get_resources().can_afford(cost):
            raise ValueError(f"Cannot afford structure: need {cost}")

    def execute(self, game: Game, player: Player) -> None:
        """Execute the build action."""
        # Spend resources
        from .structures import get_structure_data

        data = get_structure_data(self.structure_type)
        cost = data.base_cost
        player.spend_resources(cost)

        # Place structure
        board = game.get_board()
        board.place_structure(self.coord, player, self.structure_type)

        # Award victory points
        player.gain_victory_points(data.victory_points)

        # Grant cult advancement based on terrain type
        cult_board = game.get_cult_board()
        if cult_board:
            hex_space = board.get_hex(self.coord)
            if hex_space:
                # Map terrain types to cult types (simplified)
                from .board import TerrainType
                from .cults import CultType

                terrain_cult_map = {
                    TerrainType.PLAINS: CultType.AIR,
                    TerrainType.SWAMP: CultType.WATER,
                    TerrainType.FOREST: CultType.EARTH,
                    TerrainType.MOUNTAINS: CultType.FIRE,
                    TerrainType.DESERT: CultType.FIRE,
                    TerrainType.LAKES: CultType.WATER,
                    TerrainType.WASTELAND: CultType.EARTH,
                }

                cult_type = terrain_cult_map.get(hex_space.terrain)
                if cult_type:
                    # Dwellings grant 1 step, other structures grant 2
                    steps = 1 if self.structure_type == StructureType.DWELLING else 2
                    power_gained = cult_board.advance_on_cult(player, cult_type, steps)
                    # Power is granted by the observer, no need to handle it here
                    # VP for cult tracks is only awarded at end-game

    def describe(self) -> str:
        """Describe the build action."""
        from .structures import get_structure_data

        name = get_structure_data(self.structure_type).name
        return f"Build {name} at {self.coord}"


@dataclass
class TerraformAction(BaseAction):
    """Terraform hex action. Simplified: no bonus cards or special abilities."""

    coord: AxialCoord

    def _validate_specific(self, game: Game, player: Player) -> None:
        """Validate the terraform action."""
        board = game.get_board()

        # Get the hex
        hex_space = board.get_hex(self.coord)
        if not hex_space:
            raise ValueError(f"Invalid coordinate: {self.coord}")

        # Check hex is empty
        if hex_space.owner is not None:
            raise ValueError("Cannot terraform occupied hex")

        # Check it's not already home terrain
        home_terrain = player.get_home_terrain()
        if hex_space.terrain == home_terrain:
            raise ValueError("Hex is already home terrain")

        # Calculate terraform distance
        distance = self._calculate_terraform_distance(hex_space.terrain, home_terrain)

        # Check adjacency to player's structures
        player_structures = board.get_structures_of_player(player)
        if not player_structures:
            raise ValueError("Must have at least one structure to terraform")

        # For terraforming, only check direct adjacency (no shipping)
        if not board.is_hex_reachable_by_player(
            self.coord, player, include_shipping=False
        ):
            raise ValueError("Can only terraform hexes adjacent to your structures")

        # Check resources (spade cost)
        cost = player.get_spade_cost(distance)
        if not player.get_resources().can_afford(cost):
            raise ValueError(f"Cannot afford terraforming: need {cost}")

    def _calculate_terraform_distance(
        self, from_terrain: TerrainType, to_terrain: TerrainType
    ) -> int:
        """Calculate spade distance in terrain cycle."""
        from .board import TerrainType as TT

        terrain_cycle = [
            TT.PLAINS,
            TT.SWAMP,
            TT.LAKES,
            TT.FOREST,
            TT.MOUNTAINS,
            TT.WASTELAND,
            TT.DESERT,
        ]

        from_idx = terrain_cycle.index(from_terrain)
        to_idx = terrain_cycle.index(to_terrain)

        # Calculate minimum distance in the cycle
        forward = (to_idx - from_idx) % 7
        backward = (from_idx - to_idx) % 7

        return min(forward, backward)

    def execute(self, game: Game, player: Player) -> None:
        """Execute the terraform action."""
        board = game.get_board()

        hex_space = board.get_hex(self.coord)
        if not hex_space:
            return

        # Calculate cost and spend resources
        home_terrain = player.get_home_terrain()
        distance = self._calculate_terraform_distance(hex_space.terrain, home_terrain)
        cost = player.get_spade_cost(distance)
        player.spend_resources(cost)

        # Transform the terrain
        board.terraform(self.coord, home_terrain)

        # Award 2 VP per spade
        player.gain_victory_points(2 * distance)

    def describe(self) -> str:
        """Describe the terraform action."""
        return f"Terraform hex at {self.coord}"
