"""Core types and enums for Terra Mystica.

This module contains fundamental types used throughout the game.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Self


class Terrain(Enum):
    """TYPE: Enum

    Represents the seven terrain types in Terra Mystica.
    The order matches the transformation cycle in the original game.
    """

    PLAINS = auto()
    SWAMP = auto()
    LAKES = auto()
    FOREST = auto()
    MOUNTAINS = auto()
    WASTELAND = auto()
    DESERT = auto()

    def transformation_cost(self, target: Terrain) -> int:
        """Calculate the cost in spades to transform from this terrain to the target terrain."""
        if self == target:
            return 0

        terrain_count = len(Terrain)
        direct_distance = abs(self.value - target.value)
        wrap_distance = terrain_count - direct_distance

        return min(direct_distance, wrap_distance)


class Resource(Enum):
    """TYPE: Enum

    Represents the resources in Terra Mystica.
    """

    WORKER = auto()
    COIN = auto()


class PowerBowls:
    """PATTERN: Encapsulated State - Manages power token distribution across bowls.

    Power tokens cycle through 3 bowls:
    - Bowl 1: Inactive tokens
    - Bowl 2: Transitioning tokens
    - Bowl 3: Active tokens (can be spent)
    """

    _bowl_1: int
    _bowl_2: int
    _bowl_3: int

    def __new__(cls, bowl_1: int = 5, bowl_2: int = 7, bowl_3: int = 0) -> Self:
        """Create a new PowerBowls instance.

        Args:
            bowl_1: Initial tokens in bowl 1 (default: 5)
            bowl_2: Initial tokens in bowl 2 (default: 7)
            bowl_3: Initial tokens in bowl 3 (default: 0)

        Raises:
            ValueError: If any bowl count is negative
        """
        if bowl_1 < 0 or bowl_2 < 0 or bowl_3 < 0:
            raise ValueError("Bowl counts cannot be negative")

        instance = object.__new__(cls)
        instance._bowl_1 = bowl_1
        instance._bowl_2 = bowl_2
        instance._bowl_3 = bowl_3
        return instance

    @property
    def bowls(self) -> tuple[int, int, int]:
        """Distribution of tokens across bowls (bowl1, bowl2, bowl3)."""
        return (self._bowl_1, self._bowl_2, self._bowl_3)

    @property
    def available_power(self) -> int:
        """Return the number of power tokens available in bowl 3."""
        return self._bowl_3

    @property
    def total_power(self) -> int:
        """Return the total number of power tokens across all bowls."""
        return self._bowl_1 + self._bowl_2 + self._bowl_3

    def gain_power(self, amount: int) -> None:
        """Gains power by moving tokens from Bowl I to II, then II to III.

        STAGING: Validates amount is non-negative and sufficient tokens available to cycle.

        Args:
            amount: Number of power tokens to gain

        Raises:
            ValueError: If amount exceeds available tokens in bowls I and II
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Amount to gain must be non-negative")

        can_move_from_1 = min(amount, self._bowl_1)
        self._bowl_1 -= can_move_from_1
        self._bowl_2 += can_move_from_1
        amount_left = amount - can_move_from_1

        if amount_left > 0:
            can_move_from_2 = min(amount_left, self._bowl_2)
            self._bowl_2 -= can_move_from_2
            self._bowl_3 += can_move_from_2
            amount_left -= can_move_from_2

        if amount_left > 0:
            raise ValueError("Not enough power tokens available to gain")

    def spend_power(self, amount: int) -> None:
        """Spends power by moving tokens from Bowl III to Bowl I.

        STAGING: Validates amount is non-negative and doesn't exceed available power in bowl 3.

        Args:
            amount: Number of power tokens to spend

        Raises:
            ValueError: If amount exceeds available tokens in bowl 3
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Amount to spend must be non-negative")

        if amount > self._bowl_3:
            raise ValueError("Not enough power tokens available to spend")

        self._bowl_3 -= amount
        self._bowl_1 += amount

    def sacrifice_power(self, amount: int) -> None:
        """Sacrifice power by moving tokens from Bowl II to Bowl III while permanently removing tokens.

        STAGING: Validates amount non-negative, sufficient tokens in bowl 2 (2*amount), and wouldn't empty bowl 2.

        For each token moved from Bowl II to Bowl III, one token is permanently removed from Bowl II.
        This allows gaining immediate power at the cost of reducing total power permanently.

        Args:
            amount: Number of power tokens to sacrifice and gain

        Raises:
            ValueError: If amount is negative, exceeds Bowl II tokens, or would leave Bowl II with 0 tokens
        """
        if amount < 0:
            raise ValueError("Amount to sacrifice must be non-negative")
        if amount > self._bowl_2:
            raise ValueError(
                f"Cannot sacrifice {amount} power: only {self._bowl_2} tokens in bowl 2"
            )
        if self._bowl_2 - (amount * 2) < 1:
            raise ValueError(
                "Cannot sacrifice power: would leave bowl 2 with less than 1 token"
            )

        # Move tokens from Bowl II to Bowl III and permanently remove the same amount from Bowl II (reducing total power)
        self._bowl_2 -= amount * 2
        self._bowl_3 += amount
