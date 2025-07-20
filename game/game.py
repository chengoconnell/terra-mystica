"""Game facade for Terra Mystica.

This module contains the main Game class that serves as the entry point
for all game operations.
"""

from __future__ import annotations

from contextlib import contextmanager
from types import MappingProxyType

from typing import TYPE_CHECKING, Protocol, Any, TypedDict, ClassVar, Iterator

from .board import Board
from .faction import Faction
from .player import Player

from .coordinate import Coordinate
from .core import Terrain
from .structures import StructureType
from .types import GamePhase
from .validation import validate_active_player, validate_resources
from .types import (
    GameStateData,
    PlayerStateData,
    ActionResult,
    ResourceChange,
    BuildActionData,
    is_action_phase,
    is_income_phase,
    is_game_active,
)


class Game:
    """PATTERN: Facade

    Main entry point for Terra Mystica game operations. Encapsulates all game logic and state management.
    The Game class provides a simplified interface to the complex game mechanics, hiding internal implementation details from users.
    """

    __players: list[Player]
    """DATASTRUCT: Ordered list of active players in the game.
    
    This list maintains turn order and provides indexed access to player state.
    The order is significant for determining the sequence of actions within
    a round, and the list size determines valid player indices.
    """

    __current_player_index: int
    __round: int
    __is_game_over: bool
    __board: Board
    __phase: GamePhase

    # Constructor control class variables
    __is_constructing_player: ClassVar[bool] = False
    __is_constructing_board: ClassVar[bool] = False

    @staticmethod
    def _is_constructing_player() -> bool:
        """Check if Game is constructing a Player.

        TYPE: Uses static method to expose construction state for validation.
        """
        return Game.__is_constructing_player

    @staticmethod
    def _is_constructing_board() -> bool:
        """Check if Game is constructing a Board.

        TYPE: Uses static method to expose construction state for validation.
        """
        return Game.__is_constructing_board

    @staticmethod
    @contextmanager
    def __constructing_player() -> Iterator[None]:
        """Context manager for Player construction.

        PATTERN: Context Manager - ensures construction flag is properly set and cleared.
        """
        assert not Game.__is_constructing_player, "Already constructing a player"
        Game.__is_constructing_player = True
        try:
            yield None
        finally:
            Game.__is_constructing_player = False

    @staticmethod
    @contextmanager
    def __constructing_board() -> Iterator[None]:
        """Context manager for Board construction.

        PATTERN: Context Manager - ensures construction flag is properly set and cleared.
        """
        assert not Game.__is_constructing_board, "Already constructing a board"
        Game.__is_constructing_board = True
        try:
            yield None
        finally:
            Game.__is_constructing_board = False

    def __new__(cls, *, player_factions: list[str]) -> Game:
        """Create a new game with specified factions.

        STAGING: Validates player count (2-4), faction names are valid, and no duplicate factions.

        Args:
            player_factions: List of faction names (2-4 players)

        Raises:
            ValueError: If invalid number of players or unknown factions
        """
        # Validate number of players
        if not 2 <= len(player_factions) <= 4:
            raise ValueError(f"Must have 2-4 players, got {len(player_factions)}")

        # Validate faction names and convert to Faction enum
        factions: list[Faction] = []
        for faction_name in player_factions:
            try:
                faction = Faction(faction_name)
                factions.append(faction)
            except ValueError:
                valid_factions = [f.value for f in Faction]
                raise ValueError(
                    f"Unknown faction '{faction_name}'. Valid factions: {valid_factions}"
                )

        # Check for duplicate factions
        if len(set(factions)) != len(factions):
            raise ValueError("Each faction can only be used once")

        # Create the game instance
        self = object.__new__(cls)

        # Initialize players through context manager
        self.__players = []
        for faction in factions:
            with cls.__constructing_player():
                player = Player(faction)  # Only works inside context
                self.__players.append(player)

        self.__current_player_index = 0
        self.__round = 1
        self.__is_game_over = False
        self.__phase = "income"  # Games start with income phase

        # Initialize the game board through context manager
        with cls.__constructing_board():
            self.__board = Board()  # Only works inside context

        return self

    # ========== Query Methods (Read-Only) ==========
    @property
    def current_player_faction(self) -> str:
        """Get the faction name of the current player.

        Returns:
            The faction name (e.g., "Nomads", "Engineers")
        """
        return self.__players[self.__current_player_index].faction.value

    @property
    def board(self) -> Board:
        """Get the board (read-only view)."""
        return self.__board

    @property
    def current_player_resources(self) -> dict[str, int]:
        """Get the current player's resources.

        Returns:
            Dictionary with keys: "workers", "coins", "power"
        """
        player = self.__players[self.__current_player_index]
        return {
            "workers": player.resources.workers,
            "coins": player.resources.coins,
            "power": player.resources.available_power,
        }

    def get_player_resources(self, faction: str) -> dict[str, int]:
        """Get resources for a specific player by faction name.

        STAGING: Validates faction exists in current game.

        Args:
            faction: Faction name

        Returns:
            Dictionary with keys: "workers", "coins", "power"

        Raises:
            ValueError: If faction doesn't exist in this game
        """
        # Find player with matching faction
        for player in self.__players:
            if player.faction.value == faction:
                return {
                    "workers": player.resources.workers,
                    "coins": player.resources.coins,
                    "power": player.resources.available_power,
                }

        # Faction not found in this game
        active_factions = [p.faction.value for p in self.__players]
        raise ValueError(
            f"Faction '{faction}' not in this game. Active factions: {active_factions}"
        )

    @property
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.__is_game_over

    @property
    def phase(self) -> GamePhase:
        """Get the current game phase.

        TYPE: Property returning Literal type for phase validation.
        """
        return self.__phase

    def get_winner(self) -> str | None:
        """Get the winning faction name, or None if game isn't over."""
        if not self.__is_game_over:
            return None

        # Find player with highest VP
        winner = max(self.__players, key=lambda p: p.victory_points)
        return winner.faction.value

    def get_current_round(self) -> int:
        """Get the current round number (1-based)."""
        return self.__round

    def get_all_player_factions(self) -> list[str]:
        """Get list of all faction names in turn order."""
        return [player.faction.value for player in self.__players]

    def get_player_victory_points(self, faction: str) -> int:
        """Get victory points for a specific player.

        STAGING: Validates faction exists in current game.

        Args:
            faction: Faction name

        Returns:
            Current victory points for that player

        Raises:
            ValueError: If faction doesn't exist in this game
        """
        for player in self.__players:
            if player.faction.value == faction:
                return player.victory_points

        active_factions = [p.faction.value for p in self.__players]
        raise ValueError(
            f"Faction '{faction}' not in this game. Active factions: {active_factions}"
        )

    def get_player_structures(
        self, faction: str
    ) -> MappingProxyType[tuple[int, int], str]:
        """Get all structures owned by a specific player.

        STAGING: Validates faction exists in current game.

        Args:
            faction: Faction name

        Returns:
            Dictionary mapping (q, r) coordinate tuples to structure type names

        Raises:
            ValueError: If faction doesn't exist in this game
        """
        for player in self.__players:
            if player.faction.value == faction:
                structures_dict = {
                    (coord.q, coord.r): structure_type.value
                    for coord, structure_type in player.get_all_structures().items()
                }
                # Return read-only view using MappingProxyType
                return MappingProxyType(structures_dict)

        active_factions = [p.faction.value for p in self.__players]
        raise ValueError(
            f"Faction '{faction}' not in this game. Active factions: {active_factions}"
        )

    def get_terrain_at(self, q: int, r: int) -> str | None:
        """Get the terrain type at the specified coordinate.

        Args:
            q: Q coordinate
            r: R coordinate

        Returns:
            Terrain name (e.g., "Plains", "Forest") or None if out of bounds
        """
        coord = Coordinate(q, r)
        terrain = self.__board.get_terrain(coord)
        return terrain.name if terrain else None

    def get_structure_owner_at(self, q: int, r: int) -> str | None:
        """Get the faction that owns the structure at the specified coordinate.

        Args:
            q: Q coordinate
            r: R coordinate

        Returns:
            Faction name of the owner, or None if no structure
        """
        coord = Coordinate(q, r)
        owner = self.__board.get_structure_owner(coord)
        return owner.faction.value if owner else None

    def get_active_players(self) -> list[str]:
        """Get list of faction names that haven't passed this round."""
        return [
            player.faction.value for player in self.__players if not player.has_passed
        ]

    def get_game_state(self) -> GameStateData:
        """Get the current game state as a TypedDict.

        TYPE: Returns TypedDict for type-safe state representation.

        This method provides a structured, type-checked view of the game state
        that can be used for serialization, validation, or UI updates.
        """
        # Build player states using PlayerStateData
        player_states: list[PlayerStateData] = []
        for player in self.__players:
            faction_name = player.faction.value
            player_states.append(
                PlayerStateData(
                    faction=faction_name,
                    resources=self.get_player_resources(faction_name),
                    structures={
                        structure_type.value: count
                        for structure_type, count in player.get_structure_supply().items()
                    },
                    victory_points=player.victory_points,
                    has_passed=player.has_passed,
                    power_bowls=list(player.resources.power_bowls),
                )
            )

        return GameStateData(
            round=self.__round,
            current_player_index=self.__current_player_index,
            current_player_faction=self.current_player_faction,
            phase=self.__phase,
            is_game_over=self.__is_game_over,
            active_players=self.get_active_players(),
            player_count=len(self.__players),
            players=player_states,
        )

    # ========== Action Methods (Modify State) ==========

    @validate_active_player
    @validate_resources(
        workers=2, coins=1
    )  # minimum for dwelling (terraform cost added later)
    def transform_and_build(
        self, coordinate: Coordinate, target_terrain: Terrain
    ) -> None:
        """Transform terrain and build a dwelling at the specified coordinate.

        STAGING: Validates player hasn't passed (via decorator), basic resource check (via decorator), coordinate exists on board, no existing structure, target terrain matches home terrain, and full resource cost.

        Args:
            coordinate: Where to transform and build
            target_terrain: Desired terrain type

        Raises:
            ValueError: If transformation is illegal (wrong terrain, not enough resources, etc.)
        """
        current_player = self.__players[self.__current_player_index]

        # Validate coordinate is on board
        if not self.__board.is_valid_coordinate(coordinate):
            raise ValueError(f"Coordinate {coordinate} is not on the board")

        # Check if there's already a structure there
        if self.__board.get_structure_owner(coordinate):
            raise ValueError(f"Coordinate {coordinate} already has a structure")

        # Check if target terrain matches player's home terrain
        if target_terrain.name.lower() != current_player.home_terrain.lower():
            raise ValueError(
                f"Can only transform to home terrain ({current_player.home_terrain}), "
                f"not {target_terrain.name}"
            )

        # Get current terrain
        current_terrain = self.__board.get_terrain(coordinate)
        if current_terrain is None:
            raise ValueError(f"No terrain at {coordinate}")

        # Calculate terraforming cost
        terraform_cost = self.__calculate_terrain_distance(
            current_terrain, target_terrain
        )

        # Calculate total cost (terraforming + dwelling)
        # Dwelling costs: 2 workers + 1 coin
        total_workers = 2 + (terraform_cost * current_player.spade_level)
        total_coins = 1

        # Check if player can afford it
        if not current_player.resources.can_afford(
            workers=total_workers, coins=total_coins
        ):
            raise ValueError(
                f"Cannot afford transformation and building. "
                f"Need {total_workers} workers and {total_coins} coins"
            )

        # Perform the action
        # 1. Transform terrain if needed
        if current_terrain != target_terrain:
            self.__board.transform_terrain(coordinate, target_terrain)

        # 2. Build dwelling
        current_player.build_structure(coordinate, StructureType.DWELLING)
        self.__board.place_structure(coordinate, current_player)

        # 3. Spend resources
        current_player.resources.spend(workers=total_workers, coins=total_coins)

        # 4. Award VP for building (simplified: 2 VP per dwelling)
        current_player.add_victory_points(2)

    @validate_active_player
    @validate_resources(
        workers=2, coins=3
    )  # minimum cost (adjacency may reduce coins to 3)
    def upgrade_structure(self, coordinate: Coordinate) -> None:
        """Upgrade the structure at the specified coordinate (Dwelling → Trading House).

        STAGING: Validates player hasn't passed (via decorator), basic resource check (via decorator), player owns structure, structure is a dwelling, and full resource cost.

        Args:
            coordinate: Location of structure to upgrade

        Raises:
            ValueError: If upgrade is illegal (no structure, already trading house, not enough resources)
        """
        current_player = self.__players[self.__current_player_index]

        # Validate coordinate is on board
        if not self.__board.is_valid_coordinate(coordinate):
            raise ValueError(f"Coordinate {coordinate} is not on the board")

        # Check if current player owns a structure there
        structure_owner = self.__board.get_structure_owner(coordinate)
        if structure_owner != current_player:
            if structure_owner is None:
                raise ValueError(f"No structure at {coordinate} to upgrade")
            else:
                raise ValueError(f"Structure at {coordinate} belongs to another player")

        # Check what type of structure is there
        current_structure = current_player.get_structure_at(coordinate)
        if current_structure != StructureType.DWELLING:
            raise ValueError(
                f"Can only upgrade Dwellings to Trading Houses, "
                f"not {current_structure.value if current_structure else 'None'}"
            )

        # Calculate upgrade cost
        # Trading House costs: 2 workers + 6 coins (or 3 coins if adjacent to opponent)
        adjacent_players = self.__board.get_adjacent_players(coordinate)
        other_players = adjacent_players - {current_player}

        workers_cost = 2
        coins_cost = 3 if other_players else 6

        # Check if player can afford it
        if not current_player.resources.can_afford(
            workers=workers_cost, coins=coins_cost
        ):
            raise ValueError(
                f"Cannot afford upgrade. Need {workers_cost} workers and {coins_cost} coins"
            )

        # Perform the upgrade
        # 1. Upgrade the structure
        current_player.upgrade_structure(coordinate, StructureType.TRADING_HOUSE)

        # 2. Spend resources
        current_player.resources.spend(workers=workers_cost, coins=coins_cost)

        # 3. Award VP for upgrading (simplified: 3 VP per trading house)
        current_player.add_victory_points(3)

        # 4. Award power to adjacent opponents (simplified: 2 power per trading house)
        for opponent in other_players:
            opponent.resources.gain_power(2)

    @validate_active_player
    def pass_turn(self) -> None:
        """Pass for the current round. Player takes no more actions this round.

        STAGING: Validates current player hasn't already passed (via decorator) and at least one player hasn't passed.

        Raises:
            ValueError: If all players have already passed
        """
        # Check if all players have passed
        if all(player.has_passed for player in self.__players):
            raise ValueError("All players have already passed this round")

        # Mark current player as passed
        current_player = self.__players[self.__current_player_index]
        current_player.mark_passed()

        # Advance to next active player
        self.__advance_turn()

        # Check if round is over (all players passed)
        if all(player.has_passed for player in self.__players):
            self.__end_round()

    def __advance_turn(self) -> None:
        """Advance to the next player's turn.

        Note: Using double underscore for internal method.
        """
        # Find next player who hasn't passed
        original_index = self.__current_player_index

        while True:
            self.__current_player_index = (self.__current_player_index + 1) % len(
                self.__players
            )

            # If we've gone full circle, all players have passed
            if self.__current_player_index == original_index:
                break

            # If this player hasn't passed, they're the next active player
            if not self.__players[self.__current_player_index].has_passed:
                break

    def __end_round(self) -> None:
        """End the current round and prepare for the next.

        Note: Internal method called when all players have passed.
        """
        # Reset pass status for all players
        for player in self.__players:
            player.reset_pass_status()

        # Advance round counter
        self.__round += 1

        # Check end game condition (simplified: 3 rounds)
        if self.__round > 3:
            self.__is_game_over = True
            return  # Don't give income if game is over

        # Income phase for new round
        self.__phase = "income"
        self.__give_income()
        self.__phase = "action"  # Move to action phase after income

        # Reset to first player
        self.__current_player_index = 0

    def validate_action(self, action_type: str) -> ActionResult:
        """Validate if an action can be performed in the current game state.

        TYPE: Uses TypeGuard for phase checking and returns TypedDict.

        This method demonstrates advanced type features by using TypeGuards
        to check game phase and returning a structured ActionResult.
        """
        # Use TypeGuard to check if game is active
        if not is_game_active(self):
            return ActionResult(
                success=False,
                action_type="pass",
                message="Game has ended",
                resources_spent=None,
                power_gained=None,
                vp_gained=0,
            )

        # Use TypeGuard to check phase
        if action_type in ["build", "upgrade", "transform"] and not is_action_phase(
            self
        ):
            return ActionResult(
                success=False,
                action_type="build",
                message=f"Cannot perform {action_type} during {self.__phase} phase",
                resources_spent=None,
                power_gained=None,
                vp_gained=0,
            )

        return ActionResult(
            success=True,
            action_type="build",
            message="Action is valid",
            resources_spent=None,
            power_gained=None,
            vp_gained=0,
        )

    def __calculate_terrain_distance(
        self, from_terrain: Terrain, to_terrain: Terrain
    ) -> int:
        """Calculate the spade cost to transform between terrain types.

        Terrains form a cycle, so we calculate the shortest distance.

        Args:
            from_terrain: Current terrain type
            to_terrain: Target terrain type

        Returns:
            Number of spades needed (0 if same terrain)
        """
        if from_terrain == to_terrain:
            return 0

        # Define the terrain cycle (simplified)
        terrain_cycle = [
            Terrain.PLAINS,
            Terrain.SWAMP,
            Terrain.LAKES,
            Terrain.FOREST,
            Terrain.MOUNTAINS,
            Terrain.WASTELAND,
            Terrain.DESERT,
        ]

        # Find positions in cycle
        from_idx = terrain_cycle.index(from_terrain)
        to_idx = terrain_cycle.index(to_terrain)

        # Calculate shortest distance in cycle
        forward_dist = (to_idx - from_idx) % len(terrain_cycle)
        backward_dist = (from_idx - to_idx) % len(terrain_cycle)

        return min(forward_dist, backward_dist)

    def __give_income(self) -> None:
        """Distribute income to all players at the start of a round.

        Simplified income rules:
        - Each Dwelling produces 1 worker
        - Each Trading House produces 2 coins and 1 power
        - Base income: 1 worker for all players
        """
        for player in self.__players:
            # Base income
            workers_income = 1
            coins_income = 0
            power_income = 0

            # Income from structures
            for coord, structure_type in player.get_all_structures().items():
                if structure_type == StructureType.DWELLING:
                    workers_income += 1
                elif structure_type == StructureType.TRADING_HOUSE:
                    coins_income += 2
                    power_income += 1

            # Grant income
            if workers_income > 0:
                player.resources.gain(workers=workers_income)
            if coins_income > 0:
                player.resources.gain(coins=coins_income)
            if power_income > 0:
                player.resources.gain_power(power_income)
