"""Board module for Terra Mystica.

This module manages the game board including terrain types and structure placement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .coordinate import Coordinate
from .core import Terrain

if TYPE_CHECKING:
    from .player import Player
    from .structures import StructureType
    from .types import HexData, AdjacencyData, BoardStateData


class Board:
    """Manages the game board state including terrain and structures.

    PATTERN: Information Expert - Board is the expert on terrain and adjacency.
    """

    _terrain: dict[Coordinate, Terrain]
    """DATASTRUCT: Dictionary mapping hex coordinates to terrain types.
    
    This spatial dictionary provides O(1) lookup for terrain at any coordinate,
    making it efficient for checking valid moves and transformations.
    """

    _structures: dict[Coordinate, Player]
    """DATASTRUCT: Dictionary mapping hex coordinates to structure owners.
    
    This ownership map allows fast lookups for adjacency checks and ensures
    only one structure per hex. The Player reference enables quick access to
    owner information for power gains and adjacency bonuses.
    """

    def __new__(cls) -> Board:
        """Create a new board with default terrain layout.

        Constructor for Board, for use by Game only.

        PATTERN: Factory Method - Board instances can only be created through
        Game's factory methods to ensure proper registration and validation.

        For our simplified version, we'll create a small hex grid with
        varied terrain types.

        Raises:
            TypeError: If attempting to construct directly outside of Game
        """
        # Check if we're allowed to construct
        from .game import Game

        if not Game._is_constructing_board():
            raise TypeError(
                "Board instances cannot be constructed directly. Use Game constructor."
            )
        self = object.__new__(cls)
        self._terrain = {}
        self._structures = {}

        # Initialize a small hex grid with varied terrain
        # Using axial coordinates (q, r) for a roughly diamond-shaped board
        self._initialize_terrain()

        return self

    def _initialize_terrain(self) -> None:
        """Initialize the board with a default terrain layout.

        Creates a small hex grid suitable for 2-4 players.
        """
        # Define a simple 5x5 hex grid centered at (0,0)
        # This gives us 19 hexes in a compact layout
        terrain_layout = [
            # Row -2
            (Coordinate(-1, -2), Terrain.MOUNTAINS),
            (Coordinate(0, -2), Terrain.FOREST),
            (Coordinate(1, -2), Terrain.LAKES),
            # Row -1
            (Coordinate(-2, -1), Terrain.WASTELAND),
            (Coordinate(-1, -1), Terrain.PLAINS),
            (Coordinate(0, -1), Terrain.SWAMP),
            (Coordinate(1, -1), Terrain.DESERT),
            # Row 0 (center)
            (Coordinate(-2, 0), Terrain.FOREST),
            (Coordinate(-1, 0), Terrain.LAKES),
            (Coordinate(0, 0), Terrain.MOUNTAINS),  # Center hex
            (Coordinate(1, 0), Terrain.PLAINS),
            (Coordinate(2, 0), Terrain.WASTELAND),
            # Row 1
            (Coordinate(-1, 1), Terrain.SWAMP),
            (Coordinate(0, 1), Terrain.DESERT),
            (Coordinate(1, 1), Terrain.FOREST),
            (Coordinate(2, 1), Terrain.LAKES),
            # Row 2
            (Coordinate(0, 2), Terrain.PLAINS),
            (Coordinate(1, 2), Terrain.WASTELAND),
            (Coordinate(2, 2), Terrain.MOUNTAINS),
        ]

        # Populate the terrain dictionary
        for coord, terrain in terrain_layout:
            self._terrain[coord] = terrain

    def get_terrain(self, coordinate: Coordinate) -> Terrain | None:
        """Get the terrain type at the specified coordinate.

        Args:
            coordinate: The coordinate to check

        Returns:
            The terrain type, or None if coordinate is not on the board
        """
        return self._terrain.get(coordinate)

    def get_structure_owner(self, coordinate: Coordinate) -> Player | None:
        """Get the player who owns a structure at this coordinate.

        Args:
            coordinate: The coordinate to check

        Returns:
            The player who owns the structure, or None if no structure exists
        """
        return self._structures.get(coordinate)

    def is_valid_coordinate(self, coordinate: Coordinate) -> bool:
        """Check if a coordinate is on the board.

        Args:
            coordinate: The coordinate to check

        Returns:
            True if the coordinate is on the board, False otherwise
        """
        return coordinate in self._terrain

    def transform_terrain(self, coordinate: Coordinate, new_terrain: Terrain) -> None:
        """Transform the terrain at the specified coordinate.

        STAGING: Validates coordinate exists on the board.

        Args:
            coordinate: Where to transform terrain
            new_terrain: The new terrain type

        Raises:
            ValueError: If coordinate is not on the board
        """
        if not self.is_valid_coordinate(coordinate):
            raise ValueError(f"Coordinate {coordinate} is not on the board")

        self._terrain[coordinate] = new_terrain

    def place_structure(self, coordinate: Coordinate, player: Player) -> None:
        """Place a structure owned by the player at the coordinate.

        STAGING: Validates coordinate exists on board and no existing structure at location.

        Args:
            coordinate: Where to place the structure
            player: The player who owns the structure

        Raises:
            ValueError: If coordinate is not on board or already has a structure
        """
        if not self.is_valid_coordinate(coordinate):
            raise ValueError(f"Coordinate {coordinate} is not on the board")

        if coordinate in self._structures:
            raise ValueError(f"Coordinate {coordinate} already has a structure")

        self._structures[coordinate] = player

    def get_adjacent_players(self, coordinate: Coordinate) -> set[Player]:
        """Get all players who have structures adjacent to this coordinate.

        Args:
            coordinate: The coordinate to check adjacency for

        Returns:
            Set of players with structures adjacent to this coordinate
        """
        adjacent_players = set()

        # Check all neighboring coordinates
        for neighbor in coordinate.neighbors():
            if owner := self._structures.get(neighbor):
                adjacent_players.add(owner)

        return adjacent_players

    def get_hex_data(self, coordinate: Coordinate) -> HexData | None:
        """Get complete hex information as a TypedDict.

        TYPE: Returns HexData for type-safe hex state representation.

        Args:
            coordinate: The coordinate to get data for

        Returns:
            HexData with complete hex state, or None if invalid coordinate
        """
        terrain = self.get_terrain(coordinate)
        if terrain is None:
            return None

        owner = self.get_structure_owner(coordinate)

        # Get structure type from owner if present
        structure_type_str: str | None = None
        if owner is not None:
            # Import here to avoid circular dependency
            from .game import Game

            if hasattr(owner, "_structures"):
                structure_type = owner._structures.get(coordinate)
                if structure_type:
                    structure_type_str = structure_type.name.lower()

        return HexData(
            coordinate=(coordinate.q, coordinate.r),
            terrain=terrain.name.lower(),  # Convert enum name to lowercase string
            owner=owner.faction.value if owner else None,
            structure=structure_type_str,
        )

    def get_adjacency_data(
        self, coordinate: Coordinate, player: Player | None = None
    ) -> AdjacencyData:
        """Get adjacency information for a coordinate.

        TYPE: Returns AdjacencyData for type-safe adjacency queries.

        Args:
            coordinate: The coordinate to check adjacency for
            player: Optional player to check if opponents are adjacent

        Returns:
            AdjacencyData with adjacency information
        """
        adjacent_players = self.get_adjacent_players(coordinate)
        adjacent_factions = [p.faction.value for p in adjacent_players]

        has_opponent = False
        if player is not None:
            has_opponent = any(p != player for p in adjacent_players)

        return AdjacencyData(
            coordinate=(coordinate.q, coordinate.r),
            adjacent_players=adjacent_factions,
            adjacent_count=len(adjacent_players),
            has_opponent=has_opponent,
        )

    def get_board_state(self) -> BoardStateData:
        """Get complete board state as a TypedDict.

        TYPE: Returns BoardStateData for type-safe board representation.

        This method provides a structured view of the entire board,
        useful for serialization, analysis, or display.

        Returns:
            BoardStateData with all hexes and aggregate information
        """
        hexes: list[HexData] = []
        terrain_counts: dict[str, int] = {}

        # Collect data for all hexes
        for coord, terrain in self._terrain.items():
            hex_data = self.get_hex_data(coord)
            if hex_data:  # Should always be true for valid coords
                hexes.append(hex_data)

                # Count terrain types
                terrain_name = terrain.name.lower()
                terrain_counts[terrain_name] = terrain_counts.get(terrain_name, 0) + 1

        # Sort hexes by coordinate for consistent ordering
        hexes.sort(key=lambda h: (h["coordinate"][0], h["coordinate"][1]))

        return BoardStateData(
            hexes=hexes,
            occupied_count=len(self._structures),
            terrain_counts=terrain_counts,
        )
