from __future__ import annotations
from typing import ClassVar, Self, final
from weakref import WeakValueDictionary


@final
class HexCoord:
    """
    PATTERN: Flyweight pattern. Ensures only one instance exists per coordinate.
    Immutable hexagonal coordinate using axial system (q, r).
    """

    __instances: ClassVar[WeakValueDictionary[tuple[int, int], HexCoord]] = (
        WeakValueDictionary()
    )
    # Flyweight pool for coordinate instances."""

    __slots__ = ("__q", "__r", "__weakref__")
    # TYPE: __slots__ restricts instance attributes to only these names. For memory efficiency and to prevent dynamic attributes.

    __q: int
    __r: int

    def __new__(cls, q: int, r: int) -> Self:
        """Factory constructor implementing flyweight pattern. Returns existing instance if coordinates already exist."""
        key = (q, r)
        instance = HexCoord.__instances.get(key)

        if instance is None:
            instance = super().__new__(cls)
            instance.__q = q
            instance.__r = r
            HexCoord.__instances[key] = instance

        return instance

    @property
    def q(self) -> int:
        """The q component of axial coordinates."""
        return self.__q

    @property
    def r(self) -> int:
        """The r component of axial coordinates."""
        return self.__r

    def __eq__(self, other: object) -> bool:
        """Equality based on coordinates."""
        if not isinstance(other, HexCoord):
            return NotImplemented
        return self.__q == other.__q and self.__r == other.__r

    def __hash__(self) -> int:
        """Hash based on coordinates for use in sets and dicts."""
        return hash((self.__q, self.__r))
