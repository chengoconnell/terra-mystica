"""Game facade module - the single entry point for Terra Mystica gameplay.

This module contains the Game class, which serves as the facade for all game
functionality. Users of this library should only need to instantiate Game
and interact with its public methods.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Self

from .player import FactionType

if TYPE_CHECKING:
    # Import for type hints only to avoid circular imports
    from .actions import Action
    from .board import Board
    from .cults import CultBoard
    from .player import Player
    from .rounds import RoundManager
    from .structures import StructureType


class GamePhase(Enum):
    """Current phase of the game."""

    SETUP = auto()
    INCOME = auto()
    ACTIONS = auto()
    CULT_BONUS = auto()
    CLEANUP = auto()
    GAME_END = auto()


class Game:
    """
    Main game controller and facade for Terra Mystica.

    PATTERN: Facade - Provides a unified interface to the game subsystems.
    This is the only class that users of the library should instantiate directly.
    All game functionality is accessed through this class's public methods.

    Simplified from full Terra Mystica:
    - Supports 2-4 players (full game supports 2-5)
    - Limited to 5 factions initially (full game has 14)
    - Core actions only (no favor tiles or complex bonus cards)

    Example usage:
        game = Game(player_count=3)
        player1 = game.add_player(FactionType.WITCHES)
        player2 = game.add_player(FactionType.NOMADS)
        player3 = game.add_player(FactionType.HALFLINGS)
        game.start_game()

        # Game loop
        while not game.is_finished():
            current = game.get_current_player()
            # ... player chooses action ...
            game.execute_action(current, action)
    """

    _player_count: int
    _players: list[Player]
    _board: Board | None
    _round_manager: RoundManager | None
    _cult_board: CultBoard | None
    _current_phase: GamePhase
    _is_started: bool
    _used_factions: set[FactionType]

    def __new__(cls, player_count: int) -> Self:
        """
        Create a new game instance.

        Args:
            player_count: Number of players (2-4)

        Raises:
            ValueError: If player_count is not between 2 and 4
        """
        if not 2 <= player_count <= 4:
            raise ValueError(f"Player count must be 2-4, got {player_count}")

        obj = object.__new__(cls)
        obj._player_count = player_count
        obj._players = []
        obj._board = None
        obj._round_manager = None
        obj._cult_board = None
        obj._current_phase = GamePhase.SETUP
        obj._is_started = False
        obj._used_factions = set()
        return obj

    # Factory methods for creating game components

    def add_player(self, faction: FactionType) -> Player:
        """
        Add a player to the game with the specified faction.

        PATTERN: Factory Method - Creates player instances with proper initialization.

        Args:
            faction: The faction the player will control

        Returns:
            The created Player instance

        Raises:
            ValueError: If game already started, too many players, or faction already taken
        """
        if self._is_started:
            raise ValueError("Cannot add players after game has started")

        if len(self._players) >= self._player_count:
            raise ValueError(f"Game already has {self._player_count} players")

        if faction in self._used_factions:
            raise ValueError(f"Faction {faction.name} is already taken")

        # Lazy import to avoid circular dependency
        from .player import Player

        player = Player._create_for_game(self, faction)
        self._players.append(player)
        self._used_factions.add(faction)

        return player

    # Game flow methods

    def start_game(self) -> None:
        """
        Start the game after all players have been added.

        This initializes the board, round manager, and cult board,
        then begins the first round.

        Raises:
            ValueError: If incorrect number of players or game already started
        """
        if self._is_started:
            raise ValueError("Game has already started")

        if len(self._players) != self._player_count:
            raise ValueError(
                f"Expected {self._player_count} players, "
                f"but only {len(self._players)} have been added"
            )

        # Initialize game components
        from .board import Board
        from .cults import CultBoard
        from .rounds import RoundManager

        self._board = Board._create_for_game(self)
        self._cult_board = CultBoard(self)
        self._round_manager = RoundManager._create_for_game(self, self._players)

        self._is_started = True
        self._current_phase = GamePhase.INCOME

        # Process initial income phase
        self._round_manager._process_income_phase()

    def execute_action(self, player: Player, action: Action) -> None:
        """
        Execute a player action during the action phase.

        PATTERN: Command - Actions encapsulate all validation and execution logic.

        Args:
            player: The player performing the action
            action: The action to execute

        Raises:
            ValueError: If not in action phase or not player's turn
            Exception: Any validation errors from the action
        """
        if self._current_phase != GamePhase.ACTIONS:
            raise ValueError("Actions can only be taken during the action phase")

        if not self._round_manager:
            raise ValueError("Game has not started")

        current = self._round_manager.get_current_player()
        if current != player:
            raise ValueError("Not this player's turn")

        # Validate and execute the action
        action.validate(self, player)
        action.execute(self, player)

        # Advance to next player
        self._round_manager.advance_turn()

    def pass_turn(self, player: Player) -> None:
        """
        Pass for the remainder of the round.

        Args:
            player: The player who is passing

        Raises:
            ValueError: If not player's turn or not in action phase
        """
        if self._current_phase != GamePhase.ACTIONS:
            raise ValueError("Can only pass during action phase")

        if not self._round_manager:
            raise ValueError("Game has not started")

        self._round_manager.player_pass(player)

        # Phase advancement is handled automatically by RoundManager
        pass

    # Query methods

    def get_current_player(self) -> Player | None:
        """Get the player whose turn it is, or None if not in action phase."""
        if self._current_phase != GamePhase.ACTIONS or not self._round_manager:
            return None
        return self._round_manager.get_current_player()

    def get_round(self) -> int:
        """Get the current round number (1-6)."""
        if not self._round_manager:
            return 0
        return self._round_manager.get_current_round()

    def get_phase(self) -> GamePhase:
        """Get the current game phase."""
        return self._current_phase

    def is_started(self) -> bool:
        """Check if the game has started."""
        return self._is_started

    def is_finished(self) -> bool:
        """Check if the game has ended."""
        return self._current_phase == GamePhase.GAME_END

    # Component access methods

    def get_board(self) -> Board:
        """
        Get the game board.

        Raises:
            ValueError: If game has not started
        """
        if not self._board:
            raise ValueError("Board not available until game starts")
        return self._board

    def get_cult_board(self) -> CultBoard:
        """
        Get the cult board.

        Raises:
            ValueError: If game has not started
        """
        if not self._cult_board:
            raise ValueError("Cult board not available until game starts")
        return self._cult_board

    def get_players(self) -> list[Player]:
        """Get all players in the game."""
        return self._players.copy()

    # Private helper methods

