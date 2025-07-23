from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Self

from .power import PowerBowls
from .faction import FactionFactory
from .types import (
    BuildingType,
    BuildingData,
    FactionType,
    FactionAbility,
    PowerGainOption,
    PowerBowlState,
    PowerObserver,
    ResourceCost,
    ResourceState,
    SpadeCount,
    Name,
    VictoryPoints,
    TerrainType,
    FACTION_HOME_TERRAIN,
    DEFAULT_GAME_CONFIG,
)

if TYPE_CHECKING:
    from .game import Game
    from .coords import HexCoord


class Player(PowerObserver):
    """
    PATTERN: Observer - implements PowerObserver protocol for power gain notifications.
    TYPE: Composition over inheritance

    Manages player state including resources, power, buildings, and faction abilities.
    """

    # == Construction control ==

    __is_constructing: ClassVar[bool] = False

    @staticmethod
    def _is_constructing() -> bool:
        """Check if Game is constructing a player."""
        return Player.__is_constructing

    @staticmethod
    def _set_constructing(value: bool) -> None:
        """Set construction flag (for Game class only)."""
        Player.__is_constructing = value

    def __new__(
        cls,
        game: Game,
        name: Name,
        faction: FactionType,
    ) -> Self:
        """
        Constructor for a player, for use by Game only.

        STAGING: Validates construction is authorized by Game class.
        """
        if not Player._is_constructing():
            raise TypeError("Player instances cannot be constructed directly.")

        self = super().__new__(cls)
        self.__game = game
        self.__name = name
        self.__faction = faction

        # Initialize resources from config
        config = DEFAULT_GAME_CONFIG
        self.__workers = config.get("starting_workers", 3)
        self.__coins = config.get("starting_coins", 15)
        self.__victory_points = 20  # Start with 20 VP for power decisions

        # Initialize power bowls
        bowl_1, bowl_2 = config.get("starting_power_distribution", (5, 7))
        self.__power_bowls = PowerBowls(bowl_1, bowl_2)

        # Initialize game state
        self.__buildings = {}
        self.__has_passed = False

        # Create faction ability
        self.__ability = FactionFactory.create_ability(faction)

        return self

    __game: Game
    __name: Name
    __faction: FactionType
    __workers: int
    __coins: int
    __victory_points: VictoryPoints
    __power_bowls: PowerBowls
    __buildings: dict[HexCoord, BuildingType]
    __has_passed: bool
    __ability: FactionAbility

    # == Public read-only properties ==

    @property
    def game(self) -> Game:
        return self.__game

    @property
    def name(self) -> Name:
        return self.__name

    @property
    def faction(self) -> FactionType:
        return self.__faction

    @property
    def home_terrain(self) -> TerrainType:
        return FACTION_HOME_TERRAIN[self.__faction]

    @property
    def resources(self) -> ResourceState:
        """Current resources as read-only dict."""
        return {"workers": self.__workers, "coins": self.__coins}

    @property
    def victory_points(self) -> VictoryPoints:
        return self.__victory_points

    @property
    def power_state(self) -> PowerBowlState:
        """Current power bowl state as read-only dict."""
        return self.__power_bowls.state

    @property
    def buildings(self) -> dict[HexCoord, BuildingType]:
        """Copy of player's buildings by position."""
        return self.__buildings.copy()

    @property
    def has_passed(self) -> bool:
        return self.__has_passed

    def can_afford(self, cost: ResourceCost) -> bool:
        """Check if player can afford the given cost."""
        if cost.get("workers", 0) > self.__workers:
            return False
        if cost.get("coins", 0) > self.__coins:
            return False
        if cost.get("power", 0) > self.__power_bowls.available_power:
            return False
        return True

    def pay_cost(self, cost: ResourceCost) -> None:
        """
        Pay the given resource cost.

        STAGING: Validates sufficient resources before payment.
        """
        if not self.can_afford(cost):
            raise ValueError(f"Insufficient resources for cost: {cost}")

        self.__workers -= cost.get("workers", 0)
        self.__coins -= cost.get("coins", 0)

        if power_cost := cost.get("power", 0):
            self.__power_bowls.spend(power_cost)

    def _gain_resources(self, gain: ResourceState) -> None:
        self.__workers += gain.get("workers", 0)
        self.__coins += gain.get("coins", 0)

    def _gain_victory_points(self, points: VictoryPoints) -> None:
        self.__victory_points += points

    def _lose_victory_points(self, points: VictoryPoints) -> None:
        """
        Lose victory points (for power gain).

        STAGING: Ensures VP cannot go below 0.
        """
        self.__victory_points = max(0, self.__victory_points - points)

    # == Power management ==

    def gain_power(self, amount: int) -> None:
        """Gain power tokens through the bowl system."""
        self.__power_bowls.gain(amount)

    def calculate_adjacent_power(
        self, hex_positions: list[HexCoord]
    ) -> PowerGainOption:
        """
        Calculate potential power gain from adjacent buildings.

        TYPE: Returns structured data for power gain decision.
        """
        from .types import BUILDING_POWER_VALUES

        total_power = 0
        from_buildings: list[BuildingData] = []

        for pos in hex_positions:
            if building_type := self.__buildings.get(pos):
                power_value = BUILDING_POWER_VALUES[building_type]
                total_power += power_value
                from_buildings.append(
                    {
                        "type": building_type,
                        "owner": self.__name,
                        "position": pos,
                    }
                )

        return {
            "power_gain": total_power,
            "vp_cost": max(0, total_power - 1),
            "from_buildings": from_buildings,
        }

    # == Building management ==

    def add_building(self, position: HexCoord, building_type: BuildingType) -> None:
        """
        Record a new building for this player.

        STAGING: Validates position is not already occupied by this player.
        """
        if position in self.__buildings:
            raise ValueError(f"Player already has building at {position}")

        self.__buildings[position] = building_type

    def remove_building(self, position: HexCoord) -> BuildingType:
        """
        Remove and return building at position.

        STAGING: Validates building exists at position.
        """
        if position not in self.__buildings:
            raise ValueError(f"No building at position {position}")

        return self.__buildings.pop(position)

    def get_building_count(self, building_type: BuildingType) -> int:
        """Count buildings of a specific type."""
        return sum(1 for b in self.__buildings.values() if b == building_type)

    # == Game actions ==

    def pass_turn(self) -> None:
        """Mark player as passed."""
        self.__has_passed = True

    # == Faction abilities ==

    def modify_terrain_cost(self, base_cost: SpadeCount) -> SpadeCount:
        """Apply faction ability to terrain transformation cost."""
        return self.__ability.modify_terrain_cost(base_cost)

    def modify_building_cost(self, base_cost: ResourceCost) -> ResourceCost:
        """Apply faction ability to building cost."""
        return self.__ability.modify_building_cost(base_cost)

    # == Observer pattern implementation ==

    def notify_adjacent_building(
        self,
        builder: Name,
        position: HexCoord,
        building_type: BuildingType,
    ) -> bool:
        """
        PATTERN: Observer method for power gain notifications.

        Returns True if accepting power (and VP loss), False otherwise.
        """
        if builder == self.__name:
            return False  # No power from own buildings

        # Calculate potential power gain
        adjacent_positions = self.game.board.get_adjacent_positions(position)
        option = self.calculate_adjacent_power(adjacent_positions)

        if option["power_gain"] == 0:
            return False  # No adjacent buildings

        # Decision logic: Accept if we can afford the VP loss
        # and we need power (less than 6 in bowl III)
        can_afford_vp = self.__victory_points >= option["vp_cost"]
        need_power = self.__power_bowls.available_power < 6

        if can_afford_vp and need_power:
            self.gain_power(option["power_gain"])
            self._lose_victory_points(option["vp_cost"])
            return True

        return False
