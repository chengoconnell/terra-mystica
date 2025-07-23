"""Game facade and entry point for Terra Mystica.

PATTERN: Facade pattern - provides unified interface to game subsystems.
Simplified from full Terra Mystica: minimal implementation for line limits.
"""

from typing import TYPE_CHECKING, Protocol, Self, ClassVar

from .coords import HexCoord
from .types import (
    FactionType,
    Name,
    BuildingType,
    ResourceCost,
    ResourceState,
)
from .player import Player


class BoardProtocol(Protocol):
    """Minimal protocol for board stub."""

    def get_adjacent_positions(self, coord: HexCoord) -> list[HexCoord]: ...


class Game:
    """Game management facade.

    PATTERN: Facade pattern - single entry point for all game operations
    TYPE: Entry point for all game operations

    Provides the public API for Terra Mystica gameplay.
    All player actions must go through this class.
    """

    # == Construction control ==
    __is_constructing_player: ClassVar[bool] = False

    # == Instance attributes ==
    __players: dict[Name, Player]

    def __new__(cls) -> Self:
        """Create a new game instance."""
        self = super().__new__(cls)
        # Use object.__setattr__ to bypass mypy's restriction
        object.__setattr__(self, "_Game__players", {})
        # TODO: Initialize board, actions, etc.
        return self

    @property
    def board(self) -> BoardProtocol:
        """Return game board stub."""
        # TODO: Return actual Board instance
        # Stub returns object with required methods
        from .coords import HexCoord

        class BoardStub:
            def get_adjacent_positions(self, coord: HexCoord) -> list[HexCoord]:
                return []

        return BoardStub()

    @staticmethod
    def _is_constructing_player() -> bool:
        """Check if currently constructing a player."""
        return Game.__is_constructing_player

    # == Player management ==

    def create_player(self, name: Name, faction: FactionType) -> None:
        """Create a new player in the game."""
        if name in self.__players:
            raise ValueError(f"Player '{name}' already exists")

        Game.__is_constructing_player = True
        try:
            self.__players[name] = Player(self, name, faction)
        finally:
            Game.__is_constructing_player = False

    def get_player(self, name: Name) -> Player:
        """Get player by name (read-only access)."""
        if name not in self.__players:
            raise ValueError(f"Player '{name}' not found")
        return self.__players[name]

    # == Game actions (Facade API) ==

    def build_structure(
        self, player_name: Name, position: HexCoord, building_type: BuildingType
    ) -> None:
        """Build a structure for a player."""
        player = self.get_player(player_name)
        # TODO: Validate with board, check terrain, etc.
        # TODO: Apply costs
        player.add_building(position, building_type)
        # TODO: Notify observers for power gain

    def pay_resources(self, player_name: Name, cost: ResourceCost) -> None:
        """Have a player pay resources."""
        player = self.get_player(player_name)
        player.pay_cost(cost)

    def gain_resources(self, player_name: Name, gain: ResourceState) -> None:
        """Give resources to a player."""
        player = self.get_player(player_name)
        player._gain_resources(gain)

    def pass_turn(self, player_name: Name) -> None:
        """Mark a player as having passed."""
        player = self.get_player(player_name)
        player.pass_turn()
