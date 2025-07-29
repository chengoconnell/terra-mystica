from __future__ import annotations
from typing import TYPE_CHECKING, Self

from .coords import HexCoord
from .faction import ABILITY_CLASSES
from .power import PowerManager
from .game_types import (
    BUILDING_POWER_VALUES,
    FACTION_HOME_TERRAIN,
    FACTION_STARTING_RESOURCES,
    INCOME_FREQUENCY,
    POWER_GAIN_VP_LOSS,
    SPADE_EXCHANGE_RATE,
    BuildingType,
    FactionAbility,
    FactionType,
    Name,
    PlayerView,
    PowerObserver,
    ResourceCost,
    ResourceState,
    TerrainType,
    VictoryPoints,
)

if TYPE_CHECKING:
    from .board import Board


class Player(PowerObserver):
    """
    PATTERN: Observer - implements PowerObserver for adjacency notifications
    TYPE: Composition - has PowerManager and FactionAbility
    """

    __name: Name
    __faction: FactionType
    __faction_ability: FactionAbility
    __resources: ResourceState
    __power_manager: PowerManager
    __victory_points: VictoryPoints
    __buildings_on_board: list[HexCoord]
    __has_passed: bool
    __spades_available: int
    __board: Board
    __turn_count: int  # Track turns for income

    def __new__(cls, name: Name, faction: FactionType, board: Board) -> Self:
        self = super().__new__(cls)
        self.__name = name
        self.__faction = faction
        self.__board = board

        # Initialize faction ability using factory
        ability_class = ABILITY_CLASSES[faction]
        self.__faction_ability = ability_class()

        # Initialize resources from faction defaults
        starting_resources = FACTION_STARTING_RESOURCES[faction]
        self.__resources = starting_resources.copy()

        # Initialize other state
        self.__power_manager = PowerManager()
        self.__victory_points = 20  # Starting VP as per Terra Mystica
        self.__buildings_on_board = []
        self.__has_passed = False
        self.__spades_available = 0
        self.__turn_count = 0

        # Register as observer for power gain notifications
        board.add_observer(self)

        return self

    # Properties for read-only access

    @property
    def name(self) -> Name:
        return self.__name

    @property
    def faction(self) -> FactionType:
        return self.__faction

    @property
    def faction_ability(self) -> FactionAbility:
        return self.__faction_ability

    @property
    def resources(self) -> ResourceState:
        return self.__resources.copy()

    @property
    def workers(self) -> int:
        return self.__resources["workers"]

    @property
    def coins(self) -> int:
        return self.__resources["coins"]

    @property
    def available_power(self) -> int:
        return self.__power_manager.available_power

    @property
    def max_power(self) -> int:
        return self.__power_manager.max_power

    @property
    def victory_points(self) -> VictoryPoints:
        return self.__victory_points

    @property
    def buildings_on_board(self) -> list[HexCoord]:
        return self.__buildings_on_board.copy()

    @property
    def has_passed(self) -> bool:
        return self.__has_passed

    @property
    def spades_available(self) -> int:
        return self.__spades_available

    @property
    def home_terrain(self) -> TerrainType:
        return FACTION_HOME_TERRAIN[self.__faction]

    # Resource management

    def can_afford(self, cost: ResourceCost) -> bool:
        """Check if player can afford the given cost.

        Considers available resources and spade exchanges.
        """
        # Check direct resources
        if cost.get("workers", 0) > self.__resources["workers"]:
            return False
        if cost.get("coins", 0) > self.__resources["coins"]:
            return False
        if cost.get("power", 0) > self.available_power:
            return False

        # Check spades (considering exchanges)
        spades_needed = cost.get("spades", 0)
        if spades_needed > 0:
            spades_short = spades_needed - self.__spades_available
            if spades_short > 0:
                workers_needed = spades_short * SPADE_EXCHANGE_RATE
                if workers_needed > self.__resources["workers"] - cost.get(
                    "workers", 0
                ):
                    return False

        return True

    def spend_resources(self, cost: ResourceCost) -> None:
        """Spend resources for an action."""
        # Validate
        if not self.can_afford(cost):
            raise ValueError(f"Cannot afford cost: {cost}")

        # Spend basic resources
        self.__resources["workers"] -= cost.get("workers", 0)
        self.__resources["coins"] -= cost.get("coins", 0)

        if power_cost := cost.get("power", 0):
            self.__power_manager.spend_power(power_cost)

        # Handle spades
        if spades_needed := cost.get("spades", 0):
            if spades_needed <= self.__spades_available:
                self.__spades_available -= spades_needed
            else:
                # Need to exchange workers for spades
                spades_short = spades_needed - self.__spades_available
                workers_needed = spades_short * SPADE_EXCHANGE_RATE
                self.__resources["workers"] -= workers_needed
                self.__spades_available = 0

    def gain_resource(self, resource: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("Cannot gain negative resources")

        match resource:
            case "workers":
                self.__resources["workers"] += amount
            case "coins":
                self.__resources["coins"] += amount
            case "power":
                self.__power_manager.gain_power(amount)
            case _:
                raise ValueError(f"Unknown resource: {resource}")

    def gain_spades(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Cannot gain negative spades")
        self.__spades_available += amount

    def lose_victory_points(self, amount: VictoryPoints) -> None:
        """Lose victory points (e.g., for power gain)."""
        self.__victory_points = max(0, self.__victory_points - amount)

    def gain_victory_points(self, amount: VictoryPoints) -> None:
        if amount < 0:
            raise ValueError("Cannot gain negative VP")
        self.__victory_points += amount

    # Building management

    def add_building(self, position: HexCoord) -> None:
        self.__buildings_on_board.append(position)

    # Turn management

    def start_turn(self) -> None:
        """Called at the start of player's turn. Handles income distribution every N turns."""
        self.__turn_count += 1

        if self.__turn_count % INCOME_FREQUENCY == 0:
            self._collect_income()

    def mark_passed(self) -> None:
        """Mark player as having passed this round."""
        self.__has_passed = True

    def reset_for_new_round(self) -> None:
        """Reset round-specific state."""
        self.__has_passed = False
        self.__spades_available = 0

    def _collect_income(self) -> None:
        """Collect income from buildings. Simplified: 1 worker per dwelling."""
        dwelling_count = len(self.__buildings_on_board)
        if dwelling_count > 0:
            self.gain_resource("workers", dwelling_count)

    # PowerObserver implementation

    def notify_adjacent_building(
        self,
        builder: Name,
        position: HexCoord,
        building_type: BuildingType,
    ) -> None:
        """Handle notification of adjacent building construction.
        PATTERN: Observer pattern implementation
        Calculate power gain and decide whether to accept.
        """
        # Don't gain power from own buildings
        if builder == self.__name:
            return

        # Calculate total power gain from adjacent buildings
        power_gain = self._calculate_adjacent_power(position)

        if power_gain == 0:
            return

        # Calculate VP cost
        vp_cost = max(0, power_gain - 1) * POWER_GAIN_VP_LOSS

        # Auto-decline if it would put us at negative VP
        if vp_cost > self.__victory_points:
            return

        # Accept power if VP cost is reasonable (simplified AI)
        # In a full implementation, this would be a player decision
        if vp_cost <= 2 or power_gain >= 3:
            self.lose_victory_points(vp_cost)
            self.__power_manager.gain_power(power_gain)

    def _calculate_adjacent_power(self, new_building_pos: HexCoord) -> int:
        """Calculate power gain from owned buildings adjacent to new building."""
        total_power = 0

        for neighbor_pos in self.__board.get_valid_neighbors(new_building_pos):
            building = self.__board.get_building(neighbor_pos)
            if building and building["owner"] == self.__name:
                total_power += BUILDING_POWER_VALUES[building["type"]]

        return total_power

    # Data export

    def get_view(self) -> PlayerView:
        """Get read-only view of player data."""
        return {
            "name": self.__name,
            "faction": self.__faction,
            "resources": self.resources,  # Already returns a copy
            "power_state": {
                "current": self.available_power,
                "maximum": self.max_power,
            },
            "buildings": [
                (pos, BuildingType.DWELLING) for pos in self.__buildings_on_board
            ],
            "victory_points": self.__victory_points,
        }
