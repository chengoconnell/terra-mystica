"""Rounds module - round and phase management.

This module manages game rounds, phases, and turn order for Terra Mystica.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Self, Tuple

from .resources import Resources, PowerBowls

if TYPE_CHECKING:
    from .game import Game, GamePhase
    from .player import Player


class RoundScoringType(Enum):
    """
    Types of round scoring bonuses.

    TYPE: Enum for round scoring conditions.

    Simplified from full Terra Mystica:
    - Limited to basic scoring conditions
    - No complex multi-condition tiles
    """

    DWELLING = auto()  # VP per dwelling built
    TRADING_HOUSE = auto()  # VP per trading house
    STRONGHOLD_SANCTUARY = auto()  # VP per stronghold/sanctuary
    SPADE = auto()  # VP per spade (terraform)
    TOWN = auto()  # VP per town founded
    CULT_ADVANCE = auto()  # VP per cult advancement


@dataclass(frozen=True)
class RoundBonus:
    """
    Bonus scoring for a specific round.

    TYPE: Immutable value object for round bonuses.
    """

    scoring_type: RoundScoringType
    victory_points: int  # VP per occurrence
    cult_bonus: Optional[Tuple[str, int]] = None  # (cult_type, steps) for cult bonuses


# Simplified round bonuses - in full game these would be randomized
ROUND_BONUSES: List[RoundBonus] = [
    RoundBonus(RoundScoringType.DWELLING, 2),
    RoundBonus(RoundScoringType.TRADING_HOUSE, 3),
    RoundBonus(RoundScoringType.SPADE, 2),
    RoundBonus(RoundScoringType.TOWN, 5),
    RoundBonus(RoundScoringType.STRONGHOLD_SANCTUARY, 5),
    RoundBonus(RoundScoringType.CULT_ADVANCE, 3),
]


class TurnOrder:
    """
    Manages player turn order within a round.

    PATTERN: Iterator - Provides controlled access to turn sequence.

    Simplified from full Terra Mystica:
    - No complex passing order bonuses
    - No first player determination via bidding
    """

    __active_players: List[Player]
    __passed_players: List[Player]
    __current_index: int

    def __new__(cls, players: List[Player]) -> TurnOrder:
        """Create a new turn order."""
        instance = super().__new__(cls)
        instance.__active_players = players.copy()
        instance.__passed_players = []
        instance.__current_index = 0
        return instance

    def get_current_player(self) -> Optional[Player]:
        """Get the current active player."""
        if not self.__active_players:
            return None
        return self.__active_players[self.__current_index]

    def advance_turn(self) -> None:
        """Move to the next player in turn order."""
        if self.__active_players:
            self.__current_index = (self.__current_index + 1) % len(
                self.__active_players
            )

    def player_pass(self, player: Player) -> None:
        """Mark a player as having passed."""
        if player in self.__active_players:
            self.__active_players.remove(player)
            self.__passed_players.append(player)

            # Adjust current index if needed
            if (
                self.__current_index >= len(self.__active_players)
                and self.__active_players
            ):
                self.__current_index = 0

    def all_passed(self) -> bool:
        """Check if all players have passed."""
        return len(self.__active_players) == 0

    def get_new_turn_order(self) -> List[Player]:
        """Get the turn order for the next round. Players who passed earlier go first."""
        return self.__passed_players + self.__active_players


class RoundManager:
    """
    Manages game rounds and phases.

    PATTERN: State - Manages round/phase transitions and turn order.
    PATTERN: Template Method - Defines round structure with phase hooks.
    """

    __game: Game
    __players: List[Player]
    __current_round: int
    __turn_order: TurnOrder
    __round_bonuses: List[RoundBonus]
    __max_rounds: int

    @classmethod
    def _create_for_game(cls, game: Game, players: List[Player]) -> Self:
        """Create a round manager instance. Private factory method for Game class."""
        obj = object.__new__(cls)
        obj.__game = game
        obj.__players = players.copy()
        obj.__current_round = 1
        obj.__turn_order = TurnOrder(players)
        obj.__round_bonuses = ROUND_BONUSES.copy()
        obj.__max_rounds = 6
        return obj

    def get_current_player(self) -> Optional[Player]:
        """Get the current active player."""
        return self.__turn_order.get_current_player()

    def get_current_round(self) -> int:
        """Get the current round number."""
        return self.__current_round

    def get_round_bonus(self) -> Optional[RoundBonus]:
        """Get the bonus scoring for the current round."""
        if 1 <= self.__current_round <= len(self.__round_bonuses):
            return self.__round_bonuses[self.__current_round - 1]
        return None

    def player_pass(self, player: Player) -> None:
        """Handle a player passing."""
        self.__turn_order.player_pass(player)

        # If all players have passed, advance to next phase
        if self.__turn_order.all_passed():
            self._advance_phase()

    def advance_turn(self) -> None:
        """Move to the next player's turn."""
        self.__turn_order.advance_turn()

    def _advance_phase(self) -> None:
        """Advance to the next game phase: Income -> Actions -> Cult Bonuses -> (next round)"""
        from .game import GamePhase

        current = self.__game.get_phase()

        if current == GamePhase.INCOME:
            self.__game._set_phase(GamePhase.ACTIONS)
            # Reset turn order for action phase
            players_order = self.__turn_order.get_new_turn_order()
            self.__turn_order = TurnOrder(players_order)
            # Reset player pass status
            for player in self.__players:
                player.reset_for_new_round()

        elif current == GamePhase.ACTIONS:
            # Round scoring removed for simplification
            self.__game._set_phase(GamePhase.CULT_BONUS)
            # Automatically advance from CULT_BONUS phase
            self._advance_phase()

        elif current == GamePhase.CULT_BONUS:
            # Advance to next round or end game
            if self.__current_round < self.__max_rounds:
                self.__current_round += 1
                self.__game._set_phase(GamePhase.INCOME)
                # Process income phase
                self._process_income_phase()
            else:
                self.__game._set_phase(GamePhase.GAME_END)
                self._process_end_game()

    def _process_income_phase(self) -> None:
        """Process income phase for all players."""
        for player in self.__players:
            income = player.get_income()
            # Convert income to resources
            resources = Resources(
                workers=income.workers,
                coins=income.coins,
                priests=income.priests,
                power_bowls=PowerBowls(),  # Default power bowls, will use gain() for power income
            )
            player.gain_resources(resources)

        # Automatically advance to ACTIONS phase after income distribution
        self._advance_phase()

    def _process_end_game(self) -> None:
        """Process end game scoring: cult tracks, largest area, and leftover coins."""
        # Cult track final scoring
        if self.__game.get_cult_board():
            cult_scoring = self.__game.get_cult_board().calculate_end_game_scoring()
            for player, vp in cult_scoring.items():
                player.gain_victory_points(vp)

        # Largest connected area scoring
        if self.__game.get_board():
            for player in self.__players:
                area_size = self.__game.get_board().calculate_largest_area(player)
                # 3 VP per structure in largest area
                player.gain_victory_points(area_size * 3)

        # Score leftover coins: 1 VP per 3 coins
        for player in self.__players:
            coins = player.get_resources().coins
            coin_vp = coins // 3
            if coin_vp > 0:
                player.gain_victory_points(coin_vp)

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.__current_round > self.__max_rounds
