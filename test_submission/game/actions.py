from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Self, cast
from contextlib import contextmanager
from collections.abc import Iterator

from .coords import HexCoord
from .game_types import (
    BUILDING_COSTS,
    FACTION_HOME_TERRAIN,
    POWER_ACTION_COSTS,
    TERRAIN_CYCLE,
    ActionExecutor,
    BuildAction,
    BuildingType,
    GameAction,
    Name,
    PassAction,
    PowerAction,
    PowerActionType,
    ResourceCost,
    TerrainType,
    TransformAction,
    is_gain_spades_action,
    is_gain_workers_action,
)

if TYPE_CHECKING:
    from .board import Board
    from .game import Game
    from .player import Player


class ActionBuilder:
    """Helper class providing convenient methods for creating game actions. Validates string inputs and delegates execution to Game."""

    __is_constructing: ClassVar[bool] = False

    @staticmethod
    def _is_constructing() -> bool:
        """Check if builder is being constructed by Game."""
        return ActionBuilder.__is_constructing

    @staticmethod
    @contextmanager
    def _constructing_builder() -> Iterator[None]:
        """Context manager for construction control."""
        assert not ActionBuilder.__is_constructing
        ActionBuilder.__is_constructing = True
        try:
            yield None
        finally:
            ActionBuilder.__is_constructing = False

    __game: Game
    __player: Name

    def __new__(cls, game: Game, player: Name) -> Self:
        """Validates constructor is called by Game."""
        if not cls._is_constructing():
            raise TypeError("ActionBuilder cannot be constructed directly")

        self = super().__new__(cls)
        self.__game = game
        self.__player = player
        return self

    def transform(self, q: int, r: int, to_terrain: str) -> None:
        """Transform terrain at the specified position.
        Args:
            q: The q coordinate of the position.
            r: The r coordinate of the position.
            to_terrain: The type of terrain to transform to (e.g. "plains", "forest", "mountains")
        """
        try:
            terrain_type = TerrainType(to_terrain)
        except ValueError:
            raise ValueError(f"Invalid terrain type: {to_terrain}") from None

        action: TransformAction = {
            "action": "transform",
            "player": self.__player,
            "position": HexCoord(q, r),
            "target_terrain": terrain_type,
        }
        self.__game.execute_action(action)

    def build(self, q: int, r: int, building: str = "dwelling") -> None:
        """Build a building at the specified position.
        Args:
            q: The q coordinate of the position.
            r: The r coordinate of the position.
            building: The type of building to build (e.g. "dwelling")
        """
        try:
            building_type = BuildingType(building)
        except ValueError:
            raise ValueError(f"Invalid building type: {building}") from None

        action: BuildAction = {
            "action": "build",
            "player": self.__player,
            "position": HexCoord(q, r),
            "building_type": building_type,
        }
        self.__game.execute_action(action)

    def use_power(self, power_action: str) -> None:
        """Use a power action.
        Args:
            power_action: The type of power action to use (e.g. "gain_spades", "gain_workers")
        """
        try:
            power_type = PowerActionType(power_action)
        except ValueError:
            raise ValueError(f"Invalid power action: {power_action}") from None

        action: PowerAction = {
            "action": "power",
            "player": self.__player,
            "power_action": power_type,
        }
        self.__game.execute_action(action)

    def pass_turn(self) -> None:
        """Pass for the remainder of the round."""
        action: PassAction = {
            "action": "pass",
            "player": self.__player,
        }
        self.__game.execute_action(action)


class BaseActionExecutor(ActionExecutor):
    """
    PATTERN: Command pattern base implementation
    PATTERN: Template Method pattern for action execution
    """

    __board: Board
    __player: Player

    def __new__(cls, board: Board, player: Player) -> BaseActionExecutor:
        self = super().__new__(cls)
        self.__board = board
        self.__player = player
        return self

    @property
    def board(self) -> Board:
        return self.__board

    @property
    def player(self) -> Player:
        return self.__player

    def execute(self, action: GameAction) -> None:
        """STAGING: Validates action legality and resource availability. Execute the action after validation."""
        self._validate(action)
        cost = self.get_cost(action)

        if not self.player.can_afford(cost):
            raise ValueError(f"Insufficient resources: need {cost}")

        self.player.spend_resources(cost)
        self._perform(action)

    def _validate(self, action: GameAction) -> None:
        """Validate common action requirements."""
        if action["player"] != self.player.name:
            raise ValueError(f"Action player mismatch: {action['player']}")
        if self.player.has_passed:
            raise ValueError("Player has already passed")

    def _perform(self, action: GameAction) -> None:
        raise NotImplementedError


class TransformExecutor(BaseActionExecutor):
    def get_cost(self, action: GameAction) -> ResourceCost:
        """Calculate spades needed for transformation."""
        action = cast(TransformAction, action)
        target = action["target_terrain"]
        coord = action["position"]
        current = self.board.get_terrain(coord)
        base_spades = self._calculate_distance(current, target)

        # Apply faction ability
        ability = self.player.faction_ability
        spades = ability.modify_terrain_cost(base_spades)

        return {"spades": spades}

    def _validate(self, action: GameAction) -> None:
        super()._validate(action)
        action = cast(TransformAction, action)

        target = action["target_terrain"]
        coord = action["position"]

        # Check position exists
        if not self.board.has_position(coord):
            raise ValueError(f"Invalid position: {action['position']}")

        # Check not already target terrain
        current = self.board.get_terrain(coord)
        if current == target:
            raise ValueError(f"Already {target.value} terrain")

        # Check no building present
        if self.board.get_building(coord) is not None:
            raise ValueError("Cannot transform terrain that has a building")

        # Check adjacency to player's buildings
        if not self._is_adjacent_to_player_building(coord):
            raise ValueError("Must be adjacent to your buildings")

    def _perform(self, action: GameAction) -> None:
        action = cast(TransformAction, action)
        coord = action["position"]
        self.board.set_terrain(coord, action["target_terrain"])

    def _calculate_distance(
        self, from_terrain: TerrainType, to_terrain: TerrainType
    ) -> int:
        """Calculate spades needed between terrain types."""
        if from_terrain == to_terrain:
            return 0

        cycle = TERRAIN_CYCLE
        from_idx = cycle.index(from_terrain)
        to_idx = cycle.index(to_terrain)
        forward = (to_idx - from_idx) % len(cycle)
        backward = (from_idx - to_idx) % len(cycle)

        return min(forward, backward)

    def _is_adjacent_to_player_building(self, coord: HexCoord) -> bool:
        """Check if position is adjacent to player's buildings."""
        for neighbor_coord in self.board.get_valid_neighbors(coord):
            building = self.board.get_building(neighbor_coord)
            if building and building["owner"] == self.player.name:
                return True
        return False


class BuildExecutor(BaseActionExecutor):
    def get_cost(self, action: GameAction) -> ResourceCost:
        """Get building cost with faction modifications."""
        action = cast(BuildAction, action)
        building_type = action["building_type"]
        base_cost = BUILDING_COSTS[building_type].copy()

        # Apply faction ability
        ability = self.player.faction_ability
        return ability.modify_building_cost(base_cost)

    def _validate(self, action: GameAction) -> None:
        """STAGING:Validate building placement. Validates terrain, ownership, and placement rules."""
        super()._validate(action)
        action = cast(BuildAction, action)
        building_type = action["building_type"]
        coord = action["position"]

        # Check position exists
        if not self.board.has_position(coord):
            raise ValueError(f"Invalid position: {action['position']}")

        # Check correct terrain
        terrain = self.board.get_terrain(coord)
        home_terrain = FACTION_HOME_TERRAIN[self.player.faction]
        if terrain != home_terrain:
            raise ValueError(f"Can only build on {home_terrain.value}")

        # Check no existing building
        if self.board.get_building(coord) is not None:
            raise ValueError("Position already has building")

        # Only dwellings can be built directly
        if building_type != BuildingType.DWELLING:
            raise ValueError("Can only build dwellings directly")

        # Check adjacency (except first building)
        if not self._is_adjacent_or_first_building(coord):
            raise ValueError("Dwelling must be adjacent to your buildings")

    def _perform(self, action: GameAction) -> None:
        action = cast(BuildAction, action)
        building_type = action["building_type"]
        coord = action["position"]

        # Place building
        self.board.set_building(coord, building_type, self.player.name)
        self.player.add_building(coord)

        # Award VP for building
        self.player.gain_victory_points(2)

        # Notify adjacent players for power gain
        self._notify_neighbors(coord, building_type)

    def _is_adjacent_or_first_building(self, coord: HexCoord) -> bool:
        """Check if this is first building or adjacent to player's buildings."""
        # First building is always allowed
        if not self.player.buildings_on_board:
            return True

        # Otherwise must be adjacent
        for neighbor_coord in self.board.get_valid_neighbors(coord):
            building = self.board.get_building(neighbor_coord)
            if building and building["owner"] == self.player.name:
                return True
        return False

    def _notify_neighbors(self, coord: HexCoord, building_type: BuildingType) -> None:
        """Notify neighbors about new building for power gain."""
        # This will be handled by board's observer pattern
        self.board.notify_building_placed(coord, building_type, self.player.name)


class PowerActionExecutor(BaseActionExecutor):
    def get_cost(self, action: GameAction) -> ResourceCost:
        """Get power cost for action."""
        action = cast(PowerAction, action)
        power_type = action["power_action"]
        return {"power": POWER_ACTION_COSTS[power_type]}

    def _perform(self, action: GameAction) -> None:
        """Execute power action effects."""
        action = cast(PowerAction, action)
        if is_gain_spades_action(action):
            self.player.gain_spades(2)
        elif is_gain_workers_action(action):
            self.player.gain_resource("workers", 2)


class PassExecutor(BaseActionExecutor):
    def get_cost(self, action: GameAction) -> ResourceCost:
        """Passing is free."""
        return {}

    def _perform(self, action: GameAction) -> None:
        """Mark player as passed."""
        self.player.mark_passed()


class ActionFactory:
    """
    PATTERN: Factory pattern for creating action executors
    TYPE: Static factory methods
    """

    @staticmethod
    def create_executor(
        action: GameAction, board: Board, player: Player
    ) -> ActionExecutor:
        match action["action"]:
            case "transform":
                return TransformExecutor(board, player)
            case "build":
                return BuildExecutor(board, player)
            case "power":
                return PowerActionExecutor(board, player)
            case "pass":
                return PassExecutor(board, player)
