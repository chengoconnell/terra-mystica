from __future__ import annotations
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Final,
    Literal,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeGuard,
)

if TYPE_CHECKING:
    from .coords import HexCoord

# TYPE: Type aliases
Name: TypeAlias = str
"""Type alias for a name."""

VictoryPoints: TypeAlias = int
"""Type alias for victory points."""

SpadeCount: TypeAlias = int
"""Type alias for number of spades."""

PowerCount: TypeAlias = int
"""Type alias for power tokens."""


# Enums
class TerrainType(Enum):
    """TYPE: Enum with restricted terrain values.
    Simplified to 3 terrain types for manageable implementation.
    """

    FOREST = "forest"
    MOUNTAINS = "mountains"
    DESERT = "desert"


class BuildingType(Enum):
    """
    TYPE: Enum for building types available in the game.
    Simplifictation - one building type for all factions, but extensible for future expansion.
    """

    DWELLING = "dwelling"


class FactionType(Enum):
    """TYPE: Enum for available factions.
    Each faction has a home terrain matching its theme.
    """

    WITCHES = "witches"  # Home: FOREST
    ENGINEERS = "engineers"  # Home: MOUNTAINS
    NOMADS = "nomads"  # Home: DESERT


class PowerActionType(Enum):
    """Power actions available to all players."""

    GAIN_SPADES = "gain_spades"  # Cost: 4 power, gain 2 spades
    GAIN_WORKERS = "gain_workers"  # Cost: 3 power, gain 2 workers


class GameState(TypedDict):
    """TYPE: TypedDict for game state tracking."""

    current_player_index: int
    current_round: int
    is_finished: bool
    winner: Name | None


# Constants
SPADE_EXCHANGE_RATE: Final[int] = 3  # workers per spade
POWER_GAIN_VP_LOSS: Final[int] = 1  # VP lost per power gained - 1
INCOME_FREQUENCY: Final[int] = 3  # turns between income

FACTION_HOME_TERRAIN: Final[dict[FactionType, TerrainType]] = {
    FactionType.WITCHES: TerrainType.FOREST,
    FactionType.ENGINEERS: TerrainType.MOUNTAINS,
    FactionType.NOMADS: TerrainType.DESERT,
}
"""Mapping of factions to their home terrain types."""

TERRAIN_CYCLE: Final[list[TerrainType]] = [
    TerrainType.MOUNTAINS,
    TerrainType.FOREST,
    TerrainType.DESERT,
]
"""Cycle of terrain types. Can be extended for additional terrains."""

BUILDING_COSTS: Final[dict[BuildingType, "ResourceCost"]] = {
    BuildingType.DWELLING: {"workers": 1, "coins": 2},
}
"""Base building costs."""

FACTION_STARTING_RESOURCES: Final[dict[FactionType, ResourceState]] = {
    FactionType.WITCHES: {"workers": 3, "coins": 15},
    FactionType.ENGINEERS: {"workers": 4, "coins": 12},  # More workers
    FactionType.NOMADS: {"workers": 2, "coins": 18},  # More coins
}
"""Starting resources for each faction."""

POWER_ACTION_COSTS: Final[dict[PowerActionType, int]] = {
    PowerActionType.GAIN_SPADES: 4,
    PowerActionType.GAIN_WORKERS: 3,
}
"""Power costs for each power action."""

BUILDING_POWER_VALUES: Final[dict[BuildingType, int]] = {
    BuildingType.DWELLING: 1,
}
"""Power values for calculating adjacency bonuses."""


# TypedDicts for data structures
class ResourceState(TypedDict):
    """TYPE: TypedDict for resource tracking."""

    workers: int
    coins: int


class ResourceCost(TypedDict, total=False):
    """TYPE: TypedDict with optional fields for costs."""

    workers: int
    coins: int
    power: int
    spades: int


class PowerState(TypedDict):
    """TYPE: TypedDict for simplified power tracking."""

    current: int
    maximum: int


class BuildingData(TypedDict):
    """TYPE: TypedDict for building data on the board."""

    type: BuildingType
    owner: Name
    position: HexCoord


class TerrainData(TypedDict):
    """TYPE: TypedDict for terrain hex data."""

    terrain_type: TerrainType
    building: BuildingData | None


class PlayerView(TypedDict):
    """TYPE: TypedDict for read-only player data."""

    name: Name
    faction: FactionType
    resources: ResourceState
    power_state: PowerState
    buildings: list[tuple[HexCoord, BuildingType]]
    victory_points: VictoryPoints


# Action types for command pattern
class TransformAction(TypedDict):
    """TYPE: TypedDict for terrain transformation action."""

    action: Literal["transform"]
    player: Name
    position: HexCoord
    target_terrain: TerrainType


class BuildAction(TypedDict):
    """TYPE: TypedDict for building construction action."""

    action: Literal["build"]
    player: Name
    position: HexCoord
    building_type: BuildingType


class PowerAction(TypedDict):
    """TYPE: TypedDict for power action."""

    action: Literal["power"]
    player: Name
    power_action: PowerActionType


class PassAction(TypedDict):
    """TYPE: TypedDict for pass action."""

    action: Literal["pass"]
    player: Name


GameAction = TransformAction | BuildAction | PowerAction | PassAction
"""TYPE: Tagged union for all possible game actions."""


# Protocols for patterns
class FactionAbility(Protocol):
    """PATTERN: Strategy pattern interface for faction abilities.
    TYPE: Protocol for structural typing.

    Each faction implements this to provide unique abilities.
    """

    def modify_terrain_cost(self, base_cost: SpadeCount) -> SpadeCount:
        """Modify the cost to transform terrain."""
        ...

    def modify_building_cost(self, base_cost: ResourceCost) -> ResourceCost:
        """Modify the cost to build."""
        ...


class ActionExecutor(Protocol):
    """PATTERN: Command pattern executor interface.
    TYPE: Protocol for action execution.
    """

    def execute(self, action: GameAction) -> None:
        """Execute the action, modifying game state."""
        ...

    def get_cost(self, action: GameAction) -> ResourceCost:
        """Calculate the cost of executing the action."""
        ...


class PowerObserver(Protocol):
    """PATTERN: Observer pattern for power gain notifications.
    TYPE: Protocol for event handling.
    """

    def notify_adjacent_building(
        self,
        builder: Name,
        position: HexCoord,
        building_type: BuildingType,
    ) -> None:
        """Handle notification of adjacent building construction."""
        ...


def is_gain_spades_action(action: PowerAction) -> TypeGuard[PowerAction]:
    return action["power_action"] == PowerActionType.GAIN_SPADES


"""TYPE: TypeGuard for gain spades action type narrowing."""


def is_gain_workers_action(action: PowerAction) -> TypeGuard[PowerAction]:
    return action["power_action"] == PowerActionType.GAIN_WORKERS


"""TYPE: TypeGuard for gain workers action type narrowing."""


# Scoring configuration
class ScoringConfig(TypedDict):
    """TYPE: TypedDict for scoring rules."""

    dwelling_points: VictoryPoints
    area_first_place: VictoryPoints
    area_second_place: VictoryPoints
    area_third_place: VictoryPoints
    coins_per_vp: int


DEFAULT_SCORING: Final[ScoringConfig] = {
    "dwelling_points": 2,
    "area_first_place": 18,
    "area_second_place": 12,
    "area_third_place": 6,
    "coins_per_vp": 3,
}
"""Standard scoring values."""
