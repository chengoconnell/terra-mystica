from __future__ import annotations
from collections.abc import Callable, Iterable, Iterator
from typing import Generic, Self, TypeVar

from .coords import HexCoord

T = TypeVar("T")


class HexGrid(Generic[T]):
    """DATASTRUCT
    TYPE: Generic parameterized container
    PATTERN: Flyweight pattern for coordinate reuse
    The grid uses axial coordinates (q, r) with flyweight pattern and can store any type T at each position.
    """

    __cells: dict[HexCoord, T]
    """The sparse storage for hex positions and their values."""

    __min_q: int
    __max_q: int
    __min_r: int
    __max_r: int
    """Boundary tracking for efficient operations."""

    def __new__(cls, positions: Iterable[tuple[HexCoord, T]] = ()) -> Self:
        """
        Constructor for the hex grid. If positions are passed, they are inserted in the order given.
        :param positions: Iterable of (coordinate, value) pairs
        """
        self = super().__new__(cls)
        self.__cells = {}
        self.__min_q = 0
        self.__max_q = 0
        self.__min_r = 0
        self.__max_r = 0

        for coord, value in positions:
            self.set(coord, value)
        return self

    def get(self, coord: HexCoord) -> T:
        """Returns the value at the given hex coordinate."""
        try:
            return self.__cells[coord]
        except KeyError:
            raise KeyError(f"No value at position: {coord!r}") from None

    def set(self, coord: HexCoord, value: T) -> None:
        """Sets the value at the given hex coordinate.Also updates the grid boundaries for efficient range queries."""
        self.__cells[coord] = value

        # Update boundaries
        if coord not in self.__cells or len(self.__cells) == 1:
            self.__min_q = min(self.__min_q, coord.q)
            self.__max_q = max(self.__max_q, coord.q)
            self.__min_r = min(self.__min_r, coord.r)
            self.__max_r = max(self.__max_r, coord.r)

    def remove(self, coord: HexCoord) -> T:
        """Removes and returns the value at the given hex coordinate."""
        try:
            value = self.__cells.pop(coord)
        except KeyError:
            raise KeyError(f"Cannot remove from empty position: {coord!r}") from None

        # Note: We don't update boundaries on removal for efficiency
        # They become conservative estimates
        return value

    def clear(self) -> None:
        """Removes all values from the grid."""
        self.__cells.clear()
        self.__min_q = 0
        self.__max_q = 0
        self.__min_r = 0
        self.__max_r = 0

    def get_neighbors(self, coord: HexCoord) -> list[HexCoord]:
        """Returns all 6 neighboring hex coordinates. Neighbors are returned in order: E, SE, SW, W, NW, NE"""
        q, r = coord.q, coord.r
        # These will reuse existing HexCoord instances via flyweight
        return [
            HexCoord(q + 1, r),  # East
            HexCoord(q, r + 1),  # Southeast
            HexCoord(q - 1, r + 1),  # Southwest
            HexCoord(q - 1, r),  # West
            HexCoord(q, r - 1),  # Northwest
            HexCoord(q + 1, r - 1),  # Northeast
        ]

    def get_filled_neighbors(self, coord: HexCoord) -> list[tuple[HexCoord, T]]:
        """Returns neighbors that have values as (coordinate, value) pairs."""
        result = []
        for neighbor in self.get_neighbors(coord):
            if neighbor in self:
                result.append((neighbor, self.__cells[neighbor]))
        return result

    def distance(self, a: HexCoord, b: HexCoord) -> int:
        """Calculates the hexagonal distance between two coordinates. Uses the hexagonal Manhattan distance formula."""
        return (abs(a.q - b.q) + abs(a.q + a.r - b.q - b.r) + abs(a.r - b.r)) // 2

    def get_range(self, center: HexCoord, radius: int) -> list[HexCoord]:
        """
        Returns all hex coordinates within the given radius of center.
        :param center: The center coordinate
        :param radius: Maximum distance from center (inclusive)
        """
        if radius < 0:
            raise ValueError(f"Radius cannot be negative: {radius}")

        if radius == 0:
            return [center]

        results = []
        # Use cube coordinates for cleaner range calculation
        for q in range(-radius, radius + 1):
            for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
                # Flyweight pattern ensures we reuse existing coords
                results.append(HexCoord(center.q + q, center.r + r))

        return results

    def get_filled_range(
        self, center: HexCoord, radius: int
    ) -> list[tuple[HexCoord, T]]:
        """Returns all filled positions within radius as (coordinate, value) pairs."""
        results = []
        for coord in self.get_range(center, radius):
            if coord in self:
                results.append((coord, self.__cells[coord]))
        return results

    def find_path(
        self,
        start: HexCoord,
        end: HexCoord,
        is_passable: Callable[[HexCoord], bool] | None = None,
    ) -> list[HexCoord] | None:
        """
        Finds the shortest path between two coordinates.
        :param start: Starting coordinate
        :param end: Target coordinate
        :param is_passable: Optional function to test if a hex can be traversed
        :return: List of coordinates from start to end, or None if no path exists
        """
        from collections import deque

        if start == end:
            return [start]

        # BFS for shortest path
        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()

            for neighbor in self.get_neighbors(current):
                if neighbor in visited:
                    continue

                if is_passable is not None and not is_passable(neighbor):
                    continue

                if neighbor == end:
                    return path + [neighbor]

                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

        return None

    def __len__(self) -> int:
        """Returns the number of filled positions in the grid."""
        return len(self.__cells)

    def __contains__(self, coord: HexCoord) -> bool:
        """
        Special method implementing containment test: coord in grid
        TYPE: Container protocol - enables 'in' operator
        """
        return coord in self.__cells

    def __iter__(self) -> Iterator[HexCoord]:
        """
        Iterates over all filled positions in the grid.
        TYPE: Iterator protocol implementation
        """
        return iter(self.__cells)

    def items(self) -> Iterator[tuple[HexCoord, T]]:
        """Iterates over all (coordinate, value) pairs in the grid. Similar to dict.items()."""
        return iter(self.__cells.items())

    def values(self) -> Iterator[T]:
        """Iterates over all values in the grid. Similar to dict.values()."""
        return iter(self.__cells.values())

    def get_bounds(self) -> tuple[HexCoord, HexCoord]:
        """Returns the bounding box of all filled positions."""
        if not self:
            raise ValueError("Cannot get bounds of empty grid")

        return (
            HexCoord(self.__min_q, self.__min_r),
            HexCoord(self.__max_q, self.__max_r),
        )
