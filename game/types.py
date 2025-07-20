"""Advanced type definitions for Terra Mystica.

TYPE: TypedDict for structured data validation.
TYPE: Literal types for tagged unions.
TYPE: TypeGuard for runtime type narrowing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Literal, TypeGuard

if TYPE_CHECKING:
    from .coordinate import Coordinate
    from .structures import StructureType
    from .player import Player
    from .game import Game


# Game phases using Literal types for tagged union
GamePhase = Literal["income", "action", "cleanup"]

# Action types as tagged union
ActionType = Literal["build", "upgrade", "transform", "pass", "power_action"]


class GameStateData(TypedDict):
    """TYPE: TypedDict for immutable game state representation.

    Provides type-safe dictionary structure for game state serialization
    and validation.
    """

    round: int
    current_player_index: int
    current_player_faction: str
    phase: GamePhase
    is_game_over: bool
    active_players: list[str]
    player_count: int
    players: list[PlayerStateData]


class PlayerStateData(TypedDict):
    """TYPE: TypedDict for player state representation.

    Provides structured data for individual player state.
    """

    faction: str
    resources: dict[str, int]
    structures: dict[str, int]  # structure_type -> count
    victory_points: int
    has_passed: bool
    power_bowls: list[int]  # [bowl1, bowl2, bowl3]


class ActionResult(TypedDict):
    """TYPE: TypedDict for action execution results.

    Provides structured feedback from game actions with optional fields.
    """

    success: bool
    action_type: ActionType
    message: str
    resources_spent: ResourceChange | None
    power_gained: dict[str, int] | None
    vp_gained: int


class ResourceChange(TypedDict, total=False):
    """TYPE: TypedDict with total=False for optional resource changes.

    Tracks resource deltas from game actions.
    """

    workers: int
    coins: int
    power: int


class StructureSupplyData(TypedDict):
    """TYPE: TypedDict for structure supply counts.

    Maps structure types to remaining counts in player supply.
    """

    dwelling: int
    trading_house: int
    temple: int
    sanctuary: int
    stronghold: int


class HexData(TypedDict):
    """TYPE: TypedDict for individual hex information.

    Represents the complete state of a single board hex.
    """

    coordinate: tuple[int, int]  # (q, r)
    terrain: str
    owner: str | None  # Faction name if structure present
    structure: str | None  # Structure type if present


class AdjacencyData(TypedDict):
    """TYPE: TypedDict for adjacency information.

    Tracks neighboring players and structures for a coordinate.
    """

    coordinate: tuple[int, int]
    adjacent_players: list[str]  # Faction names
    adjacent_count: int
    has_opponent: bool


class BoardStateData(TypedDict):
    """TYPE: TypedDict for complete board state.

    Provides structured representation of entire board.
    """

    hexes: list[HexData]
    occupied_count: int
    terrain_counts: dict[str, int]


class BuildActionData(TypedDict):
    """TYPE: TypedDict for build action parameters."""

    coordinate: tuple[int, int]  # (q, r)
    structure_type: str
    terrain_cost: int
    total_cost: ResourceChange


# Tagged union for game events using TypedDict
class BuildEvent(TypedDict):
    """TYPE: Tagged union member for build events."""

    type: Literal["build"]
    player: str
    coordinate: tuple[int, int]
    structure: str


class UpgradeEvent(TypedDict):
    """TYPE: Tagged union member for upgrade events."""

    type: Literal["upgrade"]
    player: str
    coordinate: tuple[int, int]
    from_structure: str
    to_structure: str
    vp_gained: int


class PassEvent(TypedDict):
    """TYPE: Tagged union member for pass events."""

    type: Literal["pass"]
    player: str
    round: int


# Union type for all game events
GameEvent = BuildEvent | UpgradeEvent | PassEvent


# Type guards for runtime type checking
def is_action_phase(game: Game) -> TypeGuard[Game]:
    """TYPE: TypeGuard for phase-specific type narrowing.

    Enables type checker to understand phase-dependent operations.
    """
    return bool(hasattr(game, "phase") and game.phase == "action")


def is_income_phase(game: Game) -> TypeGuard[Game]:
    """TYPE: TypeGuard for income phase validation."""
    return bool(hasattr(game, "phase") and game.phase == "income")


def is_game_active(game: Game) -> TypeGuard[Game]:
    """TYPE: TypeGuard for active game validation."""
    return bool(hasattr(game, "is_game_over") and not game.is_game_over)


# Type guards for event discrimination
def is_build_event(event: GameEvent) -> TypeGuard[BuildEvent]:
    """TYPE: TypeGuard for build event discrimination."""
    return event["type"] == "build"


def is_upgrade_event(event: GameEvent) -> TypeGuard[UpgradeEvent]:
    """TYPE: TypeGuard for upgrade event discrimination."""
    return event["type"] == "upgrade"


def is_pass_event(event: GameEvent) -> TypeGuard[PassEvent]:
    """TYPE: TypeGuard for pass event discrimination."""
    return event["type"] == "pass"
