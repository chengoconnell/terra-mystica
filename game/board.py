"""Board module - game board representation and hex grid management.

This module implements the hexagonal game board for Terra Mystica,
including terrain types, structure placement, and adjacency calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Self, Dict, Set, Optional, List, Tuple

if TYPE_CHECKING:
    from .game import Game
    from .player import Player
    from .structures import StructureType


class TerrainType(Enum):
    """
    The seven terrain types in Terra Mystica.

    TYPE: Enum for type-safe terrain identification.
    """

    PLAINS = auto()
    SWAMP = auto()
    LAKES = auto()
    FOREST = auto()
    MOUNTAINS = auto()
    WASTELAND = auto()
    DESERT = auto()


@dataclass(frozen=True)
class AxialCoord:
    """
    Axial coordinate system for hexagonal grid.

    DATASTRUCT: Immutable value object for hex coordinates. Uses the axial coordinate system where q is the column and r is the row (diagonal from NW to SE).
    """

    q: int  # Column
    r: int  # Row

    def neighbors(self) -> List[AxialCoord]:
        """Get all 6 neighboring hex coordinates."""
        directions = [
            AxialCoord(1, 0),  # East
            AxialCoord(1, -1),  # Northeast
            AxialCoord(0, -1),  # Northwest
            AxialCoord(-1, 0),  # West
            AxialCoord(-1, 1),  # Southwest
            AxialCoord(0, 1),  # Southeast
        ]
        return [AxialCoord(self.q + d.q, self.r + d.r) for d in directions]

    def distance_to(self, other: AxialCoord) -> int:
        """Calculate hex distance to another coordinate."""
        return (
            abs(self.q - other.q)
            + abs(self.q + self.r - other.q - other.r)
            + abs(self.r - other.r)
        ) // 2


@dataclass
class Hex:
    """
    A single hexagonal space on the board.
    """

    coord: AxialCoord
    terrain: TerrainType
    owner: Optional[Player] = None
    structure: Optional[StructureType] = None
    is_river: bool = False  # Simplified: River as hex property


class Board:
    """
    Represents the game board with hexagonal grid.

    PATTERN: Composite - Board is composed of hexagonal spaces.
    PATTERN: Repository - Provides methods to query and modify hex state.

    Simplified from full Terra Mystica:
    - Fixed small board size instead of variable setup
    - Rivers marked as hex properties instead of edges
    - No pre-printed structures or special spaces
    """

    __game: Game
    __hexes: Dict[AxialCoord, Hex]

    @classmethod
    def _create_for_game(cls, game: Game) -> Self:
        """
        Create a board instance for a game.

        This is a private factory method only for use by the Game class.
        """
        obj = object.__new__(cls)
        obj.__game = game
        obj.__hexes = {}
        obj._initialize_board()
        return obj

    def _initialize_board(self) -> None:
        """
        Initialize the board with a default layout.

        Simplified from full Terra Mystica: Using a smaller fixed layout
        with 37 hexes (similar to a radius-3 hex grid).
        """
        # Create a hexagonal board with radius 3 from center
        center = AxialCoord(0, 0)
        radius = 3

        # Generate all hexes within radius
        for q in range(-radius, radius + 1):
            for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
                coord = AxialCoord(q, r)
                # Assign terrain in a pattern (simplified from actual game)
                terrain = self._assign_terrain(q, r)
                # Mark some hexes as rivers (simplified pattern)
                is_river = (q + r) % 5 == 0 and abs(q) + abs(r) > 1

                self.__hexes[coord] = Hex(
                    coord=coord, terrain=terrain, is_river=is_river
                )

    def _assign_terrain(self, q: int, r: int) -> TerrainType:
        """
        Assign terrain types in a deterministic pattern.

        Simplified from full Terra Mystica: Using a mathematical
        pattern instead of the actual game board layout.
        """
        # Create a varied but deterministic terrain distribution
        terrain_index = (abs(q * 3 + r * 2) + abs(q - r)) % 7
        return list(TerrainType)[terrain_index]

    def get_hex(self, coord: AxialCoord) -> Optional[Hex]:
        """Get the hex at the given coordinate, or None if out of bounds."""
        return self.__hexes.get(coord)

    def get_all_hexes(self) -> List[Hex]:
        """Get all hexes on the board."""
        return list(self.__hexes.values())

    def get_adjacent_hexes(self, coord: AxialCoord) -> List[Hex]:
        """
        Get all adjacent hexes (directly neighboring).

        This handles land adjacency only. River crossings require
        shipping and are handled separately.
        """
        adjacent = []
        for neighbor_coord in coord.neighbors():
            if hex_space := self.get_hex(neighbor_coord):
                # Check if there's a river between the hexes
                if not self._is_river_between(coord, neighbor_coord):
                    adjacent.append(hex_space)
        return adjacent

    def _is_river_between(self, coord1: AxialCoord, coord2: AxialCoord) -> bool:
        """
        Check if there's a river between two adjacent hexes.

        Simplified from full Terra Mystica: Rivers are properties of hexes
        rather than edges. If either hex is a river, they're separated.
        """
        hex1 = self.get_hex(coord1)
        hex2 = self.get_hex(coord2)
        if hex1 and hex2:
            return hex1.is_river or hex2.is_river
        return False

    def get_reachable_hexes(
        self, coord: AxialCoord, shipping_level: int = 0
    ) -> Set[AxialCoord]:
        """
        Get all hexes reachable from a given hex.

        This includes direct adjacency and river crossings based on
        shipping level. Uses breadth-first search.

        Simplified from full Terra Mystica: Shipping allows crossing
        one river per shipping level in a straight line.
        """
        if self.get_hex(coord) is None:
            return set()

        reachable: Set[AxialCoord] = {coord}

        # Direct land adjacency
        for adj_hex in self.get_adjacent_hexes(coord):
            reachable.add(adj_hex.coord)

        # River crossings with shipping
        if shipping_level > 0:
            # Simplified: Can reach hexes up to shipping_level rivers away
            # in any direction (not just straight lines)
            to_check = [coord]
            rivers_crossed = 0

            while to_check and rivers_crossed < shipping_level:
                next_level = []
                for check_coord in to_check:
                    for neighbor_coord in check_coord.neighbors():
                        if neighbor_coord not in reachable:
                            if neighbor_hex := self.get_hex(neighbor_coord):
                                if self._is_river_between(check_coord, neighbor_coord):
                                    reachable.add(neighbor_coord)
                                    next_level.append(neighbor_coord)
                to_check = next_level
                if next_level:
                    rivers_crossed += 1

        return reachable

    def place_structure(
        self, coord: AxialCoord, player: Player, structure: StructureType
    ) -> None:
        """
        Place a structure on a hex.

        This method assumes validation has already been done by the
        action system. It only updates the board state.
        """
        if hex_space := self.get_hex(coord):
            hex_space.owner = player
            hex_space.structure = structure

    def terraform(self, coord: AxialCoord, new_terrain: TerrainType) -> None:
        """
        Change the terrain type of a hex.

        This method assumes validation has already been done by the
        action system. It only updates the board state.
        """
        if hex_space := self.get_hex(coord):
            hex_space.terrain = new_terrain

    def get_structures_of_player(
        self, player: Player
    ) -> List[Tuple[AxialCoord, StructureType]]:
        """Get all structures owned by a player."""
        structures = []
        for hex_space in self.__hexes.values():
            if hex_space.owner == player and hex_space.structure:
                structures.append((hex_space.coord, hex_space.structure))
        return structures

    def calculate_largest_area(self, player: Player) -> int:
        """
        Calculate the size of the largest connected area for a player.

        Connected means adjacent by land or reachable via shipping.
        Uses union-find algorithm for efficiency.

        DATASTRUCT: Union-find (disjoint set) for connected components.
        """
        # Get all structures of the player
        player_structures = self.get_structures_of_player(player)
        if not player_structures:
            return 0

        # Build adjacency considering shipping
        # Simplified: Assume player has basic shipping for scoring
        shipping_level = 1  # TODO: Get from player

        # Union-find to track connected components
        parent: Dict[AxialCoord, AxialCoord] = {}
        size: Dict[AxialCoord, int] = {}

        def find(coord: AxialCoord) -> AxialCoord:
            if coord not in parent:
                parent[coord] = coord
                size[coord] = 1
            if parent[coord] != coord:
                parent[coord] = find(parent[coord])  # Path compression
            return parent[coord]

        def union(coord1: AxialCoord, coord2: AxialCoord) -> None:
            root1, root2 = find(coord1), find(coord2)
            if root1 != root2:
                # Union by size
                if size[root1] < size[root2]:
                    root1, root2 = root2, root1
                parent[root2] = root1
                size[root1] += size[root2]

        # Initialize all player structures
        structure_coords = {coord for coord, _ in player_structures}
        for coord in structure_coords:
            find(coord)  # Initialize in union-find

        # Connect adjacent structures
        for coord in structure_coords:
            reachable = self.get_reachable_hexes(coord, shipping_level)
            for other_coord in reachable:
                if other_coord in structure_coords:
                    union(coord, other_coord)

        # Find largest component
        return max(size[find(coord)] for coord in structure_coords)

    def is_hex_reachable_by_player(
        self, coord: AxialCoord, player: Player, include_shipping: bool = True
    ) -> bool:
        """
        Check if a hex is reachable by a player.

        A hex is reachable if it's adjacent to any of the player's structures,
        either directly or via shipping range (if include_shipping is True).
        """
        player_structures = self.get_structures_of_player(player)
        if not player_structures:
            return False

        # Check direct adjacency first
        for struct_coord, _ in player_structures:
            adjacent_hexes = self.get_adjacent_hexes(struct_coord)
            if any(h.coord == coord for h in adjacent_hexes):
                return True

        # Check shipping range if enabled
        if include_shipping:
            shipping_level = player.get_shipping_level()
            if shipping_level > 0:
                for struct_coord, _ in player_structures:
                    reachable = self.get_reachable_hexes(struct_coord, shipping_level)
                    if coord in reachable:
                        return True

        return False
