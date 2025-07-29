from __future__ import annotations
from typing import Self


from .coords import HexCoord
from .hexgrid import HexGrid
from .game_types import (
    BuildingData,
    BuildingType,
    Name,
    PowerObserver,
    TerrainData,
    TerrainType,
)


class Board:
    """
    PATTERN: Observer - for building placement notifications
    PATTERN: Facade - wraps HexGrid for game-specific operations
    TYPE: Composition over inheritance - Board has a HexGrid
    """

    __grid: HexGrid[TerrainData]
    __observers: list[PowerObserver]

    def __new__(cls) -> Self:
        self = super().__new__(cls)
        self.__grid = HexGrid[TerrainData]()
        self.__observers = []
        self._initialize_map()
        return self

    def _initialize_map(self) -> None:
        """Create a small hex map with varied terrain.

        Creates a 4x4 hex grid with a balanced mix of terrain types.
        Pattern creates interesting adjacencies for gameplay.
        """
        # Define a 4x4 hex grid pattern
        # Using axial coordinates (q, r)
        terrain_pattern = [
            # Row 0: r=0
            ((0, 0), TerrainType.FOREST),
            ((1, 0), TerrainType.MOUNTAINS),
            ((2, 0), TerrainType.DESERT),
            ((3, 0), TerrainType.FOREST),
            # Row 1: r=1 (offset)
            ((-1, 1), TerrainType.MOUNTAINS),
            ((0, 1), TerrainType.DESERT),
            ((1, 1), TerrainType.FOREST),
            ((2, 1), TerrainType.MOUNTAINS),
            # Row 2: r=2
            ((-1, 2), TerrainType.DESERT),
            ((0, 2), TerrainType.FOREST),
            ((1, 2), TerrainType.MOUNTAINS),
            ((2, 2), TerrainType.DESERT),
            # Row 3: r=3 (offset)
            ((-2, 3), TerrainType.FOREST),
            ((-1, 3), TerrainType.MOUNTAINS),
            ((0, 3), TerrainType.DESERT),
            ((1, 3), TerrainType.FOREST),
        ]

        for (q, r), terrain_type in terrain_pattern:
            coord = HexCoord(q, r)
            terrain_data: TerrainData = {"terrain_type": terrain_type, "building": None}
            self.__grid.set(coord, terrain_data)

    # Core terrain and building management

    def _get_terrain_data(self, coord: HexCoord) -> TerrainData:
        """Get terrain data at coordinate with helpful error message.

        :raises ValueError: if coordinate is outside the board
        """
        try:
            return self.__grid.get(coord)
        except KeyError:
            raise ValueError(
                f"Coordinate (q={coord.q}, r={coord.r}) is outside the board"
            ) from None

    def get_terrain(self, coord: HexCoord) -> TerrainType:
        """Get terrain type at the given coordinate."""
        terrain_data = self._get_terrain_data(coord)
        return terrain_data["terrain_type"]

    def set_terrain(self, coord: HexCoord, terrain: TerrainType) -> None:
        """Set terrain type at the given coordinate."""
        terrain_data = self._get_terrain_data(coord)
        terrain_data["terrain_type"] = terrain
        self.__grid.set(coord, terrain_data)

    def get_building(self, coord: HexCoord) -> BuildingData | None:
        """Get building at the given coordinate, or None if empty."""
        terrain_data = self._get_terrain_data(coord)
        return terrain_data["building"]

    def set_building(
        self, coord: HexCoord, building_type: BuildingType, owner: Name
    ) -> None:
        """Place a building at the given coordinate.
        :raises ValueError: if coordinate is outside the board
        :raises ValueError: if position already has a building
        """
        terrain_data = self._get_terrain_data(coord)
        if terrain_data["building"] is not None:
            raise ValueError(f"Position already has building: {coord}")

        building: BuildingData = {
            "type": building_type,
            "owner": owner,
            "position": coord,
        }
        terrain_data["building"] = building
        self.__grid.set(coord, terrain_data)

    # Observer pattern for power gaining

    def add_observer(self, observer: PowerObserver) -> None:
        """Register an observer for building placement notifications."""
        if observer not in self.__observers:
            self.__observers.append(observer)

    def remove_observer(self, observer: PowerObserver) -> None:
        """Unregister an observer."""
        self.__observers.remove(observer)

    def notify_building_placed(
        self, coord: HexCoord, building_type: BuildingType, owner: Name
    ) -> None:
        """
        Notify all observers about a new building placement.
        Calculates power gain opportunities for adjacent opponents.
        """
        # Get all adjacent buildings owned by other players
        adjacent_buildings = self.get_adjacent_opponent_buildings(coord, owner)

        if not adjacent_buildings:
            return  # No adjacent opponents

        # Group buildings by owner
        buildings_by_owner: dict[Name, list[BuildingData]] = {}
        for building in adjacent_buildings:
            buildings_by_owner.setdefault(building["owner"], []).append(building)

        # Notify each affected observer
        for observer in self.__observers:
            # Let the observer determine if they own any of these buildings
            # and decide whether to accept power
            observer.notify_adjacent_building(owner, coord, building_type)

    # Game-specific queries

    def has_position(self, coord: HexCoord) -> bool:
        """Check if coordinate exists on the board."""
        return coord in self.__grid

    def get_valid_neighbors(self, coord: HexCoord) -> list[HexCoord]:
        """Get only neighboring coordinates that exist on the board."""
        return [n for n in self.__grid.get_neighbors(coord) if n in self.__grid]

    def get_adjacent_opponent_buildings(
        self, coord: HexCoord, player: Name
    ) -> list[BuildingData]:
        """Get all buildings adjacent to coord owned by other players.
        Used for power gain calculations.
        """
        adjacent_buildings = []

        for neighbor in self.get_valid_neighbors(coord):
            building = self.get_building(neighbor)
            if building and building["owner"] != player:
                adjacent_buildings.append(building)

        return adjacent_buildings

    def find_connected_buildings(self, player: Name) -> list[set[HexCoord]]:
        """Find all groups of connected buildings for a player."""
        player_buildings: set[HexCoord] = set()
        for coord in self.__grid:
            building = self.get_building(coord)
            if building and building["owner"] == player:
                player_buildings.add(coord)

        if not player_buildings:
            return []

        # Find connected components using BFS
        visited: set[HexCoord] = set()
        components: list[set[HexCoord]] = []

        for start in player_buildings:
            if start in visited:
                continue

            # BFS to find all connected buildings
            component: set[HexCoord] = set()
            queue = [start]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                component.add(current)

                # Check all neighbors
                for neighbor in self.get_valid_neighbors(current):
                    if neighbor in player_buildings and neighbor not in visited:
                        queue.append(neighbor)

            components.append(component)

        return components

    def get_largest_connected_area(self, player: Name) -> int:
        """Get the size of the player's largest connected building group. Used for area scoring at game end."""
        components = self.find_connected_buildings(player)
        return max(len(comp) for comp in components) if components else 0

    def get_all_positions(self) -> list[HexCoord]:
        """Get all valid positions on the board."""
        return list(self.__grid)

    def get_empty_positions(self) -> list[HexCoord]:
        """Get all positions without buildings."""
        empty = []
        for coord in self.__grid:
            if self.get_building(coord) is None:
                empty.append(coord)
        return empty

    def get_positions_with_terrain(self, terrain: TerrainType) -> list[HexCoord]:
        """Get all positions with the specified terrain type."""
        positions = []
        for coord in self.__grid:
            if self.get_terrain(coord) == terrain:
                positions.append(coord)
        return positions

    def __len__(self) -> int:
        """Number of positions on the board."""
        return len(self.__grid)
