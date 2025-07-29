from __future__ import annotations
from typing import Self

from .actions import ActionBuilder, ActionFactory
from .board import Board
from .player import Player
from .game_types import (
    DEFAULT_SCORING,
    FactionType,
    GameAction,
    GameState,
    Name,
    PlayerView,
    VictoryPoints,
)


class Game:
    """PATTERN: Facade - Single entry point for all game functionality"""

    __board: Board
    __players: list[Player]
    __player_map: dict[Name, Player]
    __active_players: set[Name]
    __pass_order: list[Name]  # Track order of passing for next round
    __game_state: GameState
    __max_turns: int
    __max_rounds: int
    __action_builders: dict[Name, ActionBuilder]

    def __new__(cls, max_rounds: int = 10) -> Self:
        """Create a new game instance. Simplification: no phases, just rounds. In each round, players can take one action"""
        if max_rounds <= 0:
            raise ValueError("Max turns must be positive")

        self = super().__new__(cls)
        self.__board = Board()
        self.__players = []
        self.__player_map = {}
        self.__active_players = set()
        self.__pass_order = []
        self.__game_state = {
            "current_player_index": 0,
            "current_round": 1,
            "is_finished": False,
            "winner": None,
        }
        self.__max_rounds = max_rounds
        self.__action_builders = {}
        return self

    # Player management

    def add_player(self, name: str, faction: str) -> ActionBuilder:
        """Add a player to the game. Returns ActionBuilder for this player.
        STAGING: Validates that the game has not yet started.
        """
        if self.__game_state["current_round"] > 1:
            raise ValueError("Cannot add players after game starts")

        if name in self.__player_map:
            raise ValueError(f"Player already exists: {name}")

        try:
            faction_type = FactionType(faction)
        except ValueError:
            raise ValueError(f"Invalid faction: {faction}") from None

        # Check faction not already taken
        for player in self.__players:
            if player.faction == faction_type:
                raise ValueError(f"Faction already taken: {faction}")

        # Create player
        player = Player(name, faction_type, self.__board)
        self.__players.append(player)
        self.__player_map[name] = player
        self.__active_players.add(name)  # New player is active

        # Create action builder for player
        with ActionBuilder._constructing_builder():
            builder = ActionBuilder(self, name)
            self.__action_builders[name] = builder

        return builder

    def get_player_action(self, name: str) -> ActionBuilder:
        """Get action builder for a player, used for executing player actions."""
        if name not in self.__action_builders:
            raise KeyError(f"Unknown player: {name}")
        return self.__action_builders[name]

    @property
    def players(self) -> list[str]:
        """List of player names in turn order."""
        return [p.name for p in self.__players]

    @property
    def current_player(self) -> str:
        """Name of the current player."""
        if self.__game_state["is_finished"]:
            raise ValueError("Game is finished")
        if not self.__players:
            raise ValueError("No players in game")

        idx = self.__game_state["current_player_index"]
        return self.__players[idx].name

    @property
    def is_finished(self) -> bool:
        """Whether the game has ended."""
        return self.__game_state["is_finished"]

    @property
    def current_round(self) -> int:
        return self.__game_state["current_round"]

    @property
    def rounds_remaining(self) -> int:
        return max(0, self.__max_rounds - self.__game_state["current_round"])

    # Action execution

    def execute_action(self, action: GameAction) -> None:
        """Execute a game action.
        PATTERN: Command pattern execution
        STAGING: Validates player turn and game not finished.
        """
        if self.__game_state["is_finished"]:
            raise ValueError("Game is finished")

        if len(self.__players) < 2 or len(self.__players) > 3:
            raise ValueError(
                "Need 2 or 3 players to start"
            )  # Since we only have 3 factions

        current = self.__players[self.__game_state["current_player_index"]]
        if action["player"] not in self.__active_players:
            raise ValueError(
                f"{action['player']} has passed for the rest of the round, it's {current.name}'s turn"
            )
        if action["player"] != current.name:
            raise ValueError(
                f"Not {action['player']}'s turn, it's {current.name}'s turn"
            )

        # Create and execute action
        executor = ActionFactory.create_executor(action, self.__board, current)
        executor.execute(action)

        # Handle passing
        if action["action"] == "pass":
            self._handle_pass(current.name)
        else:
            # Check for forced pass (no valid actions)
            if not self._has_valid_actions(current):
                current.mark_passed()
                self._handle_pass(current.name)

        if not self.__game_state["is_finished"]:
            if len(self.__active_players) == 0:
                # All passed - start new round
                self._start_new_round()
            else:
                # Continue to next active player
                self._advance_to_next_active_player()

    def _handle_pass(self, player_name: Name) -> None:
        """Handle a player passing."""
        self.__active_players.discard(player_name)
        self.__pass_order.append(player_name)

    def _advance_to_next_active_player(self) -> None:
        """Find and activate the next player who hasn't passed."""
        player_count = len(self.__players)
        if player_count == 0:
            return

        # Start from current position
        current_idx = self.__game_state["current_player_index"]

        # Look for next active player
        for _ in range(player_count):
            current_idx = (current_idx + 1) % player_count
            player = self.__players[current_idx]

            if player.name in self.__active_players:
                self.__game_state["current_player_index"] = current_idx
                player.start_turn()
                return

        # Shouldn't reach here if active_players is tracked correctly
        raise RuntimeError("No active players found but round hasn't ended")

    def _start_new_round(self) -> None:
        """Reset for a new round."""
        self.__game_state["current_round"] += 1

        # Check end game
        if self.__game_state["current_round"] >= self.__max_rounds:
            self._end_game()
            return

        for player in self.__players:
            player.reset_for_new_round()

        # Reactivate all players
        self.__active_players = {p.name for p in self.__players}

        # Determine turn order based on pass order
        if self.__pass_order:
            # First player to pass gets first turn next round
            first_player_name = self.__pass_order[0]
            # Find their index
            for i, player in enumerate(self.__players):
                if player.name == first_player_name:
                    self.__game_state["current_player_index"] = i
                    break
        else:
            # No one passed (shouldn't happen), keep same order
            self.__game_state["current_player_index"] = 0

        # Clear pass order for next round
        self.__pass_order.clear()

        # Start the first player's turn
        if self.__players:
            current = self.__players[self.__game_state["current_player_index"]]
            current.start_turn()

    def _has_valid_actions(self, player: Player) -> bool:
        """Check if player has any valid actions. Simplified: just check if they have resources for anything."""
        # Can always pass
        if player.has_passed:
            return False

        # Check for any affordable action
        has_workers = player.workers > 0
        has_coins = player.coins > 0
        has_power = player.available_power >= 3

        return has_workers or has_coins or has_power

    def _end_game(self) -> None:
        """End the game and determine winner."""
        self.__game_state["is_finished"] = True

        # Calculate final scores
        scores = self._calculate_final_scores()

        # Determine winner
        if scores:
            winner_name = max(scores.items(), key=lambda item: item[1])[0]
            self.__game_state["winner"] = winner_name

    def _calculate_final_scores(self) -> dict[Name, VictoryPoints]:
        """Calculate final victory points for all players."""
        scores: dict[Name, VictoryPoints] = {}
        scoring = DEFAULT_SCORING

        for player in self.__players:
            # Base VP
            vp = player.victory_points

            # Remaining resources to VP
            total_coins = player.coins + player.workers  # 1:1 conversion
            vp += total_coins // scoring["coins_per_vp"]
            scores[player.name] = vp

        # Area scoring
        area_sizes = [
            (p.name, self.__board.get_largest_connected_area(p.name))
            for p in self.__players
        ]
        area_sizes.sort(key=lambda x: x[1], reverse=True)

        # Award area bonuses
        if len(area_sizes) >= 1 and area_sizes[0][1] > 0:
            scores[area_sizes[0][0]] += scoring["area_first_place"]
        if len(area_sizes) >= 2 and area_sizes[1][1] > 0:
            scores[area_sizes[1][0]] += scoring["area_second_place"]
        if len(area_sizes) >= 3 and area_sizes[2][1] > 0:
            scores[area_sizes[2][0]] += scoring["area_third_place"]

        return scores

    # Game state queries

    def get_player_view(self, name: str) -> PlayerView:
        """Get read-only view of player state."""
        if name not in self.__player_map:
            raise KeyError(f"Unknown player: {name}")
        return self.__player_map[name].get_view()

    def get_final_scores(self) -> dict[str, int] | None:
        """Get final scores if game is finished."""
        if not self.__game_state["is_finished"]:
            return None
        return self._calculate_final_scores()

    def get_winner(self) -> str | None:
        """Get winner name if game is finished."""
        return self.__game_state["winner"]

    def get_board_state(self) -> dict[str, list[tuple[int, int]]]:
        """
        Get positions of all buildings by player.
        Returns dict mapping player names to lists of (q, r) coordinates.
        """
        positions_by_player: dict[str, list[tuple[int, int]]] = {}

        for coord in self.__board.get_all_positions():
            building = self.__board.get_building(coord)
            if building:
                owner = building["owner"]
                if owner not in positions_by_player:
                    positions_by_player[owner] = []
                positions_by_player[owner].append((coord.q, coord.r))

        return positions_by_player
