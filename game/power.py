from __future__ import annotations
from typing import Final, Self

from .types import PowerBowlState


class PowerBowls:
    """
    PATTERN: State pattern for power token management
    TYPE: Encapsulated mutable state with validation

    Manages the circulation of 12 power tokens through 3 bowls:
    - Gaining power: Bowl I → Bowl II → Bowl III
    - Spending power: Bowl III → Bowl I
    - Sacrificing: Remove from Bowl II to move others to Bowl III

    The total number of tokens remains constant (except when sacrificing).
    """

    # Constants
    INITIAL_TOTAL_TOKENS: Final[int] = 12
    """Standard starting power tokens."""

    MIN_TOKENS_FOR_SACRIFICE: Final[int] = 2
    """Minimum tokens in Bowl II required to sacrifice."""

    # Private attributes
    __bowl_1: int
    __bowl_2: int
    __bowl_3: int
    __total_tokens: int

    def __new__(cls, bowl_1: int, bowl_2: int) -> Self:
        """
        Constructor for PowerBowls with initial distribution.

        STAGING: Validates token counts are non-negative and sum to 12.

        :param bowl_1: Initial tokens in Bowl I
        :param bowl_2: Initial tokens in Bowl II
        :raises ValueError: if invalid token distribution
        """
        if bowl_1 < 0 or bowl_2 < 0:
            raise ValueError("Bowl token counts cannot be negative")

        bowl_3 = 0  # Always start with empty Bowl III
        total = bowl_1 + bowl_2 + bowl_3

        if total != cls.INITIAL_TOTAL_TOKENS:
            raise ValueError(
                f"Total tokens must equal {cls.INITIAL_TOTAL_TOKENS}, got {total}"
            )

        self = super().__new__(cls)
        self.__bowl_1 = bowl_1
        self.__bowl_2 = bowl_2
        self.__bowl_3 = bowl_3
        self.__total_tokens = total

        return self

    # == Properties ==

    @property
    def state(self) -> PowerBowlState:
        """Read-only view of current bowl state."""
        return {
            "bowl_1": self.__bowl_1,
            "bowl_2": self.__bowl_2,
            "bowl_3": self.__bowl_3,
        }

    @property
    def available_power(self) -> int:
        """Power available to spend (tokens in Bowl III)."""
        return self.__bowl_3

    @property
    def total_tokens(self) -> int:
        """Total tokens in circulation (may be less than 12 after sacrificing)."""
        return self.__total_tokens

    @property
    def can_sacrifice(self) -> bool:
        """Whether sacrifice action is possible."""
        return self.__bowl_2 >= self.MIN_TOKENS_FOR_SACRIFICE

    # == Power circulation ==

    def gain(self, amount: int) -> None:
        """
        Gain power by moving tokens clockwise through bowls.

        STAGING: Validates amount is positive.

        Movement order:
        1. Bowl I → Bowl II (until Bowl I empty)
        2. Bowl II → Bowl III (until Bowl II empty)
        3. No effect if all tokens in Bowl III

        :param amount: Power to gain
        :raises ValueError: if amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot gain negative power: {amount}")

        if amount == 0:
            return

        # Phase 1: Move from Bowl I to Bowl II
        move_from_1 = min(amount, self.__bowl_1)
        if move_from_1 > 0:
            self.__bowl_1 -= move_from_1
            self.__bowl_2 += move_from_1
            amount -= move_from_1

        # Phase 2: Move from Bowl II to Bowl III
        if amount > 0:
            move_from_2 = min(amount, self.__bowl_2)
            if move_from_2 > 0:
                self.__bowl_2 -= move_from_2
                self.__bowl_3 += move_from_2
                # Any remaining amount is lost (all tokens in Bowl III)

    def spend(self, amount: int) -> None:
        """
        Spend power by moving tokens from Bowl III to Bowl I.

        STAGING: Validates sufficient power available and amount positive.

        :param amount: Power to spend
        :raises ValueError: if insufficient power or negative amount
        """
        if amount < 0:
            raise ValueError(f"Cannot spend negative power: {amount}")

        if amount == 0:
            return

        if amount > self.__bowl_3:
            raise ValueError(f"Insufficient power: need {amount}, have {self.__bowl_3}")

        self.__bowl_3 -= amount
        self.__bowl_1 += amount

    def sacrifice(self, amount: int) -> None:
        """
        Sacrifice tokens from Bowl II to immediately move others to Bowl III.

        STAGING: Validates sufficient tokens in Bowl II and amount positive.

        For each token sacrificed (removed from game), move one token
        from Bowl II to Bowl III immediately.

        :param amount: Number of tokens to sacrifice
        :raises ValueError: if insufficient tokens or invalid amount
        """
        if amount < 0:
            raise ValueError(f"Cannot sacrifice negative tokens: {amount}")

        if amount == 0:
            return

        # Need at least amount * 2 tokens in Bowl II
        # (amount to sacrifice + amount to move)
        needed_in_bowl_2 = amount * 2

        if self.__bowl_2 < needed_in_bowl_2:
            raise ValueError(
                f"Need {needed_in_bowl_2} tokens in Bowl II to sacrifice {amount}, "
                f"have {self.__bowl_2}"
            )

        # Remove tokens from game
        self.__bowl_2 -= amount
        self.__total_tokens -= amount

        # Move equal amount to Bowl III
        self.__bowl_2 -= amount
        self.__bowl_3 += amount

    # == Utility methods ==

    def get_maximum_gain_effect(self) -> int:
        """
        Calculate maximum power gain that would have any effect.

        Returns the number of tokens not in Bowl III.
        """
        return self.__bowl_1 + self.__bowl_2

    def get_sacrifice_options(self) -> list[int]:
        """
        Get list of valid sacrifice amounts.

        Returns list of token amounts that can be sacrificed.
        """
        if not self.can_sacrifice:
            return []

        # Can sacrifice from 1 up to floor(bowl_2 / 2) tokens
        max_sacrifice = self.__bowl_2 // 2
        return list(range(1, max_sacrifice + 1))

    def would_benefit_from_power(self, amount: int) -> bool:
        """
        Check if gaining power would move any tokens.

        Useful for UI/decision making.
        """
        return amount > 0 and (self.__bowl_1 > 0 or self.__bowl_2 > 0)

    def simulate_gain(self, amount: int) -> PowerBowlState:
        """
        Simulate gaining power without modifying state.

        TYPE: Pure function returning new state

        :param amount: Power to simulate gaining
        :return: New bowl state after gain
        """
        if amount < 0:
            return self.state

        # Create simulation state
        sim_bowl_1 = self.__bowl_1
        sim_bowl_2 = self.__bowl_2
        sim_bowl_3 = self.__bowl_3

        # Simulate Phase 1: Bowl I → Bowl II
        move_from_1 = min(amount, sim_bowl_1)
        if move_from_1 > 0:
            sim_bowl_1 -= move_from_1
            sim_bowl_2 += move_from_1
            amount -= move_from_1

        # Simulate Phase 2: Bowl II → Bowl III
        if amount > 0:
            move_from_2 = min(amount, sim_bowl_2)
            if move_from_2 > 0:
                sim_bowl_2 -= move_from_2
                sim_bowl_3 += move_from_2

        return {
            "bowl_1": sim_bowl_1,
            "bowl_2": sim_bowl_2,
            "bowl_3": sim_bowl_3,
        }

    # == Validation helpers ==

    def _validate_invariants(self) -> None:
        """
        Internal validation that bowl invariants hold.

        For debugging - ensures:
        - All bowl counts are non-negative
        - Total equals expected token count
        """
        assert self.__bowl_1 >= 0, f"Bowl I negative: {self.__bowl_1}"
        assert self.__bowl_2 >= 0, f"Bowl II negative: {self.__bowl_2}"
        assert self.__bowl_3 >= 0, f"Bowl III negative: {self.__bowl_3}"

        actual_total = self.__bowl_1 + self.__bowl_2 + self.__bowl_3
        assert (
            actual_total == self.__total_tokens
        ), f"Token count mismatch: {actual_total} != {self.__total_tokens}"
