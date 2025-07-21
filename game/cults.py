"""Cult tracks module - religious advancement system.

This module manages the four cult tracks (Fire, Water, Earth, Air)
and player advancement on them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, List, Tuple, Protocol

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


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

    __cult_type: CultType
    __positions: Dict[Player, int]
    __max_level: int

    def __new__(cls, cult_type: CultType) -> CultTrack:
        """Create a new cult track."""
        instance = super().__new__(cls)
        instance.__cult_type = cult_type
        instance.__positions = {}
        instance.__max_level = 10
        return instance

    def get_position(self, player: Player) -> int:
        """Get a player's position on this track."""
        return self.__positions.get(player, 0)

    def advance(self, player: Player, steps: int) -> int:
        """Advance player on track. Returns Power gained.

        Per Terra Mystica rules: Multiple players can occupy same space.
        Power is gained at milestones 3/5/7/10.
        VP is only awarded at end-game based on ranking.
        """
        if steps <= 0:
            return 0

        current = self.get_position(player)
        new_position = min(current + steps, self.__max_level)

        if new_position == current:
            return 0

        # Set new position (no pushing - multiple players can share spaces)
        self.__positions[player] = new_position

        # Calculate power reward (VP only awarded at end-game)
        power = self._calculate_power_gain(current, new_position)

        return power

    def _calculate_power_gain(self, from_level: int, to_level: int) -> int:
        """Calculate Power gain per rules: L3=1P, L5=2P, L7=2P, L10=3P"""
        power = 0
        thresholds = [(3, 1), (5, 2), (7, 2), (10, 3)]

        for level, power_gain in thresholds:
            if from_level < level <= to_level:
                power += power_gain

        return power

    def get_rankings(self) -> List[Tuple[Player, int]]:
        """Get player rankings sorted by level (highest first)."""
        rankings = [(player, level) for player, level in self.__positions.items()]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings


class CultObserver(Protocol):
    """Observer for cult track events. PATTERN: Observer - Decoupled event handling."""

    def on_cult_advancement(
        self,
        player: Player,
        power_gained: int,
    ) -> None:
        """Handle cult advancement event."""
        ...


class CultBoard:
    """
    Manages cult tracks.
    PATTERN: Observer, Facade - Unified cult management with notifications.
    """

    __tracks: Dict[CultType, CultTrack]
    __game: Game
    __observers: List[CultObserver]

    def __new__(cls, game: Game) -> CultBoard:
        """Create a new cult board instance."""
        instance = super().__new__(cls)
        instance.__tracks = {cult_type: CultTrack(cult_type) for cult_type in CultType}
        instance.__game = game
        instance.__observers = []
        return instance

    def attach(self, observer: CultObserver) -> None:
        """Attach an observer to cult events."""
        if observer not in self.__observers:
            self.__observers.append(observer)

    def detach(self, observer: CultObserver) -> None:
        """Detach an observer from cult events."""
        if observer in self.__observers:
            self.__observers.remove(observer)

    def advance_on_cult(self, player: Player, cult_type: CultType, steps: int) -> int:
        """Advance player on cult track. Returns Power gained."""
        track = self.__tracks[cult_type]
        power_gained = track.advance(player, steps)

        # Notify listeners when power is gained
        if power_gained > 0:
            self._notify_advancement(player, power_gained)

        return power_gained

    def get_position(self, player: Player, cult_type: CultType) -> int:
        """Get a player's position on a specific cult track."""
        return self.__tracks[cult_type].get_position(player)

    def get_all_positions(self, player: Player) -> Dict[CultType, int]:
        """Get a player's positions on all cult tracks."""
        return {
            cult_type: track.get_position(player)
            for cult_type, track in self.__tracks.items()
        }

    def get_rankings(self, cult_type: CultType) -> List[Tuple[Player, int]]:
        """Get rankings for a specific cult track."""
        return self.__tracks[cult_type].get_rankings()

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
        power_gained: int,
    ) -> None:
        """Notify all observers of cult advancement. PATTERN: Observer notification."""
        for observer in self.__observers:
            observer.on_cult_advancement(player, power_gained)


def get_priest_cult_bonus(cult_type: CultType) -> int:
    """Get priest cult bonus. Simplified to always return 3 steps."""
    return 3


class PowerMilestoneObserver:
    """Concrete observer that grants power on cult milestones. PATTERN: Observer.
    Players gain power when reaching spaces 3/5/7/10.
    """

    def on_cult_advancement(
        self,
        player: Player,
        power_gained: int,
    ) -> None:
        """Grant power to advancing player when they reach milestones."""
        if power_gained > 0:
            player.gain_power(power_gained)
