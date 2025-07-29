from typing import Self
from .game_types import PowerCount


class PowerManager:
    """Simplified power system - single score instead of bowls."""

    __power: PowerCount
    __max_power: PowerCount

    def __new__(cls, starting_power: PowerCount = 12) -> Self:
        self = super().__new__(cls)
        self.__power = starting_power
        self.__max_power = starting_power
        return self

    @property
    def available_power(self) -> PowerCount:
        return self.__power

    @property
    def max_power(self) -> PowerCount:
        return self.__max_power

    def gain_power(self, amount: PowerCount) -> PowerCount:
        """Gain power up to maximum. Returns actual gained."""
        old_power = self.__power
        self.__power = min(self.__power + amount, self.__max_power)
        return self.__power - old_power

    def spend_power(self, amount: PowerCount) -> None:
        """STAGING: Validates sufficient power before spending."""
        if amount > self.__power:
            raise ValueError(f"Insufficient power: {amount} > {self.__power}")
        self.__power -= amount
