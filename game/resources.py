"""Resources module - immutable value objects for game resources.

This module defines the resource system used throughout Terra Mystica,
including workers, coins, priests, and the unique power bowl mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


class Resources:
    """TYPE: Immutable value object for resources. Simplified: no conversion tracking."""

    __workers: int = 0
    __coins: int = 0
    __priests: int = 0
    __power_bowls: PowerBowls

    def __new__(
        cls,
        workers: int = 0,
        coins: int = 0,
        priests: int = 0,
        power_bowls: PowerBowls | None = None,
    ) -> Self:
        self = super().__new__(cls)
        self.__workers = max(0, workers)
        self.__coins = max(0, coins)
        self.__priests = max(0, priests)
        self.__power_bowls = power_bowls or PowerBowls()
        return self

    @property
    def workers(self) -> int:
        return self.__workers

    @property
    def coins(self) -> int:
        return self.__coins

    @property
    def priests(self) -> int:
        return self.__priests

    @property
    def power_bowls(self) -> PowerBowls:
        return self.__power_bowls

    @property
    def total_power(self) -> int:
        return 12  # Fixed total in simplified version

    @property
    def available_power(self) -> int:
        return self.__power_bowls.available_power()

    def can_afford(self, cost: Resources) -> bool:
        """Check if can afford cost. Power checked from Bowl III only."""
        return (
            self.__workers >= cost.workers
            and self.__coins >= cost.coins
            and self.__priests >= cost.priests
            and self.__power_bowls.available_power() >= cost.available_power
        )

    def subtract(self, cost: Resources) -> Resources:
        """Return new Resources with cost subtracted. Power spent from Bowl III."""
        if not self.can_afford(cost):
            raise ValueError(f"Cannot afford cost. Have: {self}, Need: {cost}")

        new_bowls = self.__power_bowls
        if cost.available_power > 0:
            new_bowls = self.__power_bowls.spend(cost.available_power)

        return Resources(
            self.__workers - cost.workers,
            self.__coins - cost.coins,
            self.__priests - cost.priests,
            new_bowls,
        )

    def add(self, income: Resources) -> Resources:
        """Return new Resources with income added. Power follows bowl progression."""
        new_workers = self.__workers + income.workers
        new_coins = self.__coins + income.coins
        new_priests = self.__priests + income.priests

        # Power follows bowl progression
        new_bowls = self.__power_bowls
        if income.total_power > 0:
            new_bowls = self.__power_bowls.gain(income.total_power)

        return Resources(
            workers=new_workers,
            coins=new_coins,
            priests=new_priests,
            power_bowls=new_bowls,
        )

    def gain_power(self, amount: int) -> Resources:
        """Return new Resources with power gained. Tokens move I→II→III."""
        if amount < 0:
            raise ValueError(f"Cannot gain negative power: {amount}")

        new_bowls = self.__power_bowls.gain(amount)
        return Resources(
            workers=self.__workers,
            coins=self.__coins,
            priests=self.__priests,
            power_bowls=new_bowls,
        )


class PowerBowls:
    __slots__ = ("_PowerBowls__tokens",)
    __tokens: tuple[int, int, int]  # Bowls I, II, III

    def __new__(cls, tokens: tuple[int, int, int] = (12, 0, 0)) -> Self:
        if sum(tokens) != 12 or any(t < 0 for t in tokens):
            raise ValueError("Invalid power token distribution")
        self = super().__new__(cls)
        self.__tokens = tokens
        return self

    def gain(self, amount: int) -> PowerBowls:
        """Move tokens clockwise through bowls"""
        bowl1, bowl2, bowl3 = self.__tokens

        # First move from bowl 1 to 2
        move_1_to_2 = min(amount, bowl1)
        bowl1 -= move_1_to_2
        bowl2 += move_1_to_2
        amount -= move_1_to_2

        # Then move from bowl 2 to 3
        move_2_to_3 = min(amount, bowl2)
        bowl2 -= move_2_to_3
        bowl3 += move_2_to_3

        return PowerBowls((bowl1, bowl2, bowl3))

    def spend(self, amount: int) -> PowerBowls:
        """Move tokens from bowl 3 to bowl 1"""
        bowl1, bowl2, bowl3 = self.__tokens
        if bowl3 < amount:
            raise ValueError(f"Insufficient power: have {bowl3}, need {amount}")
        return PowerBowls((bowl1 + amount, bowl2, bowl3 - amount))

    def available_power(self) -> int:
        """Power available for spending (bowl 3)"""
        return self.__tokens[2]
