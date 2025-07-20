"""Cult tracks module - religious advancement system.

This module manages the four cult tracks (Fire, Water, Earth, Air)
and player advancement on them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .player import Player
    from .game import Game


class CultType(Enum):
    """
    The four cult tracks.
    TYPE: Enum for type-safe cult identification.
    """

    FIRE = auto()
    WATER = auto()
    EARTH = auto()
    AIR = auto()


@dataclass
class CultPosition:
    """
    A player's position on a cult track.
    TYPE: Value object representing cult advancement state.
    """

    player: Player
    level: int  # Position on track (0-10)

    def __lt__(self, other: CultPosition) -> bool:
        """Compare positions for ordering."""
        return self.level < other.level


class CultTrack:
    """
    Individual cult track.
    PATTERN: State - Encapsulates cult track state and transitions.
    """

    __slots__ = ("_cult_type", "_positions", "_max_level")

    _cult_type: CultType
    _positions: Dict[Player, int]
    _max_level: int

    def __new__(cls, cult_type: CultType) -> CultTrack:
        """Create a new cult track."""
        instance = super().__new__(cls)
        instance._cult_type = cult_type
        instance._positions = {}
        instance._max_level = 10
        return instance

    def get_position(self, player: Player) -> int:
        """Get a player's position on this track."""
        return self._positions.get(player, 0)

    def advance(self, player: Player, steps: int) -> Tuple[int, List[Player]]:
        """Advance player on track. Returns (VP gained, players pushed down)."""
        if steps <= 0:
            return (0, [])

        current = self.get_position(player)
        new_position = min(current + steps, self._max_level)

        if new_position == current:
            return (0, [])

        # Find players that need to be pushed down
        pushed_players: List[Player] = []
        for other_player, pos in self._positions.items():
            if other_player != player and current < pos <= new_position:
                pushed_players.append(other_player)

        # Push down other players
        for other in pushed_players:
            self._positions[other] = max(0, self._positions[other] - 1)

        # Set new position
        self._positions[player] = new_position

        # Calculate victory points
        vp = self._calculate_vp_gain(current, new_position)

        return (vp, pushed_players)

    def _calculate_vp_gain(self, from_level: int, to_level: int) -> int:
        """Calculate VP: L3=1VP, L5=2VP, L7=2VP, L10=3VP"""
        vp = 0
        thresholds = [(3, 1), (5, 2), (7, 2), (10, 3)]

        for level, points in thresholds:
            if from_level < level <= to_level:
                vp += points

        return vp

    def get_rankings(self) -> List[Tuple[Player, int]]:
        """Get player rankings sorted by level (highest first)."""
        rankings = [(player, level) for player, level in self._positions.items()]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings


class CultBoard:
    """
    Manages cult tracks.
    PATTERN: Observer, Facade - Unified cult management with notifications.
    """

    __slots__ = ("_tracks", "_game")

    _tracks: Dict[CultType, CultTrack]
    _game: Game

    def __new__(cls, game: Game) -> CultBoard:
        """Create a new cult board instance."""
        instance = super().__new__(cls)
        instance._tracks = {cult_type: CultTrack(cult_type) for cult_type in CultType}
        instance._game = game
        return instance

    def advance_on_cult(
        self, player: Player, cult_type: CultType, steps: int
    ) -> Tuple[int, List[Player]]:
        """Advance player on cult track. Returns (VP gained, players pushed)."""
        track = self._tracks[cult_type]
        vp_gained, pushed = track.advance(player, steps)

        # Notify listeners (simplified - in full implementation would trigger callbacks)
        if vp_gained > 0 or pushed:
            self._notify_advancement(player, cult_type, steps, vp_gained, pushed)

        return (vp_gained, pushed)

    def get_position(self, player: Player, cult_type: CultType) -> int:
        """Get a player's position on a specific cult track."""
        return self._tracks[cult_type].get_position(player)

    def get_all_positions(self, player: Player) -> Dict[CultType, int]:
        """Get a player's positions on all cult tracks."""
        return {
            cult_type: track.get_position(player)
            for cult_type, track in self._tracks.items()
        }

    def get_rankings(self, cult_type: CultType) -> List[Tuple[Player, int]]:
        """Get rankings for a specific cult track."""
        return self._tracks[cult_type].get_rankings()

    def calculate_end_game_scoring(self) -> Dict[Player, int]:
        """End game scoring: 1st=8VP, 2nd=4VP, 3rd=2VP per track. Simplified: no tie-breaking."""
        scoring: Dict[Player, int] = {}
        position_vp = {0: 8, 1: 4, 2: 2}  # Index to VP mapping

        for cult_type in CultType:
            rankings = self.get_rankings(cult_type)

            # Award VP to top 3 positions
            for idx, (player, level) in enumerate(rankings[:3]):
                if level > 0:  # Only score if player has advanced
                    if player not in scoring:
                        scoring[player] = 0
                    scoring[player] += position_vp.get(idx, 0)

        return scoring

    def _notify_advancement(
        self,
        player: Player,
        cult_type: CultType,
        steps: int,
        vp_gained: int,
        pushed_players: List[Player],
    ) -> None:
        """Notify advancement. Placeholder for Observer pattern."""
        pass  # Would trigger callbacks in full implementation


def get_priest_cult_bonus(cult_type: CultType) -> int:
    """Get priest cult bonus. Simplified to always return 3 steps."""
    return 3
