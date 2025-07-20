"""Resource management for Terra Mystica.

This module handles the game's resource system including workers, coins,
and the unique power bowl mechanism.
"""

from __future__ import annotations

from typing import Self

from .core import Resource, PowerBowls


class Resources:
    """PATTERN: Encapsulation. The Resources class encapsulates the storage and
    logic for handling a player's resources (coins, workers, etc.), hiding the implementation details from other parts of the system.
    """

    _workers: int
    _coins: int
    _power: PowerBowls

    def __new__(
        cls, workers: int = 0, coins: int = 0, power: PowerBowls | None = None
    ) -> Self:
        """Create a new Resources instance.

        Args:
            workers: Number of workers (>= 0)
            coins: Number of coins (>= 0)
            power: Initial PowerBowls instance (default: new PowerBowls)
        Raises:
            ValueError: If workers or coins are negative
        """
        if workers < 0 or coins < 0:
            raise ValueError("Workers and coins must be non-negative")
        instance = object.__new__(cls)
        instance._workers = workers
        instance._coins = coins
        instance._power = power if power is not None else PowerBowls()
        return instance

    # ========== Query Methods (Properties) ==========

    @property
    def workers(self) -> int:
        """Number of workers available."""
        return self._workers

    @property
    def coins(self) -> int:
        """Number of coins available."""
        return self._coins

    @property
    def power_bowls(self) -> tuple[int, int, int]:
        """Power distribution across bowls (bowl1, bowl2, bowl3)."""
        return (self._power._bowl_1, self._power._bowl_2, self._power._bowl_3)

    @property
    def available_power(self) -> int:
        """Power that can be spent (in bowl 3)."""
        return self._power.available_power

    @property
    def total_power(self) -> int:
        """Total power tokens across all bowls."""
        return self._power.total_power

    def gain_power(self, amount: int) -> None:
        """Delegate power gain to the internal PowerBowls instance."""
        self._power.gain_power(amount)

    def spend_power(self, amount: int) -> None:
        """Delegate power spend to the internal PowerBowls instance."""
        self._power.spend_power(amount)

    def can_afford(self, workers: int = 0, coins: int = 0, power: int = 0) -> bool:
        """Check if the player can afford the given resources."""
        return (
            self._workers >= workers
            and self._coins >= coins
            and self._power.available_power >= power
        )

    def spend(self, workers: int = 0, coins: int = 0, power: int = 0) -> None:
        """Spend the given resources.

        STAGING: Validates sufficient workers, coins, and power available before spending.
        """
        if not self.can_afford(workers, coins, power):
            raise ValueError("Not enough resources to spend")

        self._workers -= workers
        self._coins -= coins
        self._power.spend_power(power)

    def gain(self, workers: int = 0, coins: int = 0) -> None:
        """Gain the given resources"""
        self._workers += workers
        self._coins += coins

    def sacrifice_power(self, amount: int) -> None:
        """Sacrifice power tokens to gain immediate power at the cost of permanently reducing total power.

        STAGING: Validates sufficient power tokens in bowl 2 for sacrifice (at least 2*amount).

        Args:
            amount: Number of power tokens to sacrifice

        Raises:
            ValueError: If sacrifice is not possible (insufficient tokens, would leave Bowl II empty)
        """
        self._power.sacrifice_power(amount)
