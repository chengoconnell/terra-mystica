1. Simplified Terrain & Building System 
- Only 3 terrain types, 1 building type (dwelling)
- Implement the transformation cycle (spending spades to change terrain)
- Basic adjacency rules for building

2. Power bowl system
- Implement the 3-bowl power circulation mechanic
- Power gaining from adjacent opponent building
- 2 simple power actions

3. Limited Factions
- Implement 3 factions 
- Skip strongholds and their abilities

4. Simplified resources:
- Workers, Coins, Power
- Skip Priests to reduce complexity

6. Simplified game flow:
- uses simple alternating turns instead of phases

7. Victory conditions:
- Buildings: 2 VP per Dwelling, 5 VP per Trading House 
- Cult track: 8/4/2 VP for 1st/2nd/3rd place 
- Largest connected area: 18/12/6 VP for 1st/2nd/3rd

Module structure:
game/ ├── init.py # Exports only Game class 
      ├── types.py # TypedDicts, Enums, Protocols, type aliases 
      ├── hexgrid.py # Generic hex grid (like WithdrawableStack) 
      ├── coords.py # Coordinate systems and conversions 
      ├── power.py # Power bowl system with state management 
      ├── terrain.py # Terrain transformation logic 
      ├── faction.py # Faction hierarchy with factory 
      ├── board.py # Game board using hexgrid 
      ├── actions.py # Action validation and execution 
      ├── player.py # Player data and game state 
      └── game.py # Main facade with controlled construction
      
Object-Oriented Patterns to Implement 
- Factory Pattern - For creating factions 
- Strategy Pattern - For faction-specific abilities 
- Observer Pattern - For power gaining notifications 
- Command Pattern - For executable game actions

What to Explicitly Cut 
- Shipping mechanics (use simple adjacency only) 
- All advanced buildings (Temples, Sanctuaries, Strongholds) 
- Favor tiles, Bonus cards, Town tiles 
- Priests as a resource 
- Cult tracks
- Round structure (use simple turn-based play) 
- Complex scoring (just count buildings and cult position)


Prompts
Before we implement, I want to highlight a few notes that you should always keep in mind: 
- run my py strict and black after each change
- implement code in small chunks and prompt for review
- reference @bids.py or @listings.py  or @marketplace.py  or @stacks.py  or @users.py  for example of good oop code (e.g. use private attributes)
- whenever implementing a new change think whether this would maximise marks while minimising line count
- note that we should test our code against the @terra_mystica_rules.md 


Do not implement anything. Can you also use these files as inspiration? They're an exemplar provided by the professor on how to achieve top OOP marks


```python
# game.py (preview of public API)
class Game:
    """PATTERN: Facade pattern - single entry point to the library."""
    
    # == Setup Phase ==
    
    def add_player(self, username: Username, faction: FactionType) -> Player:
        """
        Add a player to the game during setup.
        
        Returns the Player instance for inspection.
        """
        # Game controls Player construction
        Player._set_constructing(True)
        try:
            player = Player(self, username, faction)
            self.__players[username] = player
            return player
        finally:
            Player._set_constructing(False)
    
    # == Access Players ==
    
    @property
    def current_player(self) -> Player:
        """The player whose turn it is."""
        return self.__players[self.__current_username]
    
    def get_player(self, username: Username) -> Player:
        """Get a specific player by username."""
        return self.__players[username]
    
    @property
    def players(self) -> list[Player]:
        """All players in turn order."""
        return [self.__players[u] for u in self.__turn_order]
```

# Power Gain Notifications
Great question! The Observer pattern is implemented for **power gain notifications** when players build adjacent to opponents. Here's where it's implemented:

## 1. In `types.py` - The Protocol:
```python
class PowerObserver(Protocol):
    """PATTERN: Observer pattern for power gain notifications.
    TYPE: Protocol for event handling.
    """
    
    def notify_adjacent_building(
        self,
        builder: Name,
        position: HexCoord,
        building_type: BuildingType,
    ) -> bool:
        """Handle notification of adjacent building construction.
        
        Returns True if the player accepts the power (and VP loss), False if they decline.
        """
        ...
```

## 2. In `player.py` - The Observer:
```python
class Player(PowerObserver):
    """
    PATTERN: Observer - implements PowerObserver protocol for power gain notifications.
    """
    
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
        
        # Calculate potential power gain from adjacent buildings
        adjacent_positions = self.game.board.get_adjacent_positions(position)
        option = self.calculate_adjacent_power(adjacent_positions)
        
        if option["power_gain"] == 0:
            return False  # No adjacent buildings
        
        # Decision logic: Accept if we can afford the VP loss
        can_afford_vp = self.__victory_points >= option["vp_cost"]
        need_power = self.__power_bowls.available_power < 6
        
        if can_afford_vp and need_power:
            self._gain_power(option["power_gain"])
            self._lose_victory_points(option["vp_cost"])
            return True
        
        return False
```

## 3. In `game.py` - The Subject/Notifier:
```python
def build_dwelling(self, player_name: Name, position: HexCoord) -> None:
    """Build a dwelling at the specified position."""
    # ... validation and building ...
    
    # Notify observers (adjacent players) for power gain
    self.__handle_power_gain(player_name, position, BuildingType.DWELLING)

def __handle_power_gain(
    self,
    builder_name: Name,
    position: HexCoord,
    building_type: BuildingType,
) -> None:
    """
    Handle power gain for adjacent players.
    
    PATTERN: Observer pattern notification.
    """
    adjacent_positions = self.__board.get_adjacent_positions(position)
    
    for player in self.__players.values():
        if player.name == builder_name:
            continue  # No power from own buildings
        
        # Check if player has buildings adjacent
        player_positions = {pos for pos, _ in player.get_buildings_list()}
        adjacent_owned = [
            pos for pos in adjacent_positions if pos in player_positions
        ]
        
        if adjacent_owned:
            # Notify player of opportunity (Observer pattern)
            accepted = player.notify_adjacent_building(
                builder_name, position, building_type
            )
```

## The Pattern Flow:

1. **Event**: Player builds a structure
2. **Subject**: Game identifies which players have adjacent buildings
3. **Notification**: Game calls `notify_adjacent_building()` on each affected player
4. **Observer Decision**: Each player decides whether to accept power (and lose VP)
5. **Response**: Player returns True/False, and Game logs the decision

This is a classic Observer pattern where:
- **Subject**: Game (manages building placement)
- **Observers**: Players (interested in adjacent building events)
- **Event**: Building construction/upgrade
- **Notification Method**: `notify_adjacent_building()`

The pattern is already properly implemented in your code! It's one of the core mechanics from Terra Mystica - when someone builds next to you, you can gain power but must pay victory points.


# Cult Track
You're right to catch that TODO - it's another case where I was adding complexity from the full Terra Mystica rules. According to your simplified plan:

**Your Plan Says:**
- **One cult track** (not four)
- **Simple advancement mechanics**
- **Cult track: 8/4/2 VP for 1st/2nd/3rd place** (scored at game end only)

So the cult track in your simplified game:
1. **No power gains** during advancement
2. **Only scores at game end** based on relative positions
3. **Simple advancement** - pay 1 worker, move up 1 space

## The Clean Implementation:

```python
# In AdvanceCultCommand
def execute(self) -> None:
    """Advance on cult track."""
    player = self._get_player()
    
    # Pay cost
    cost = self.get_cost()
    player.pay_cost(cost)
    
    # Advance on track
    player.advance_cult(1)
    # That's it! No power gains in simplified game
```

## Cult Scoring (in game.py at game end):

```python
def __calculate_final_scores(self) -> dict[Name, VictoryPoints]:
    """Calculate final scores for all players."""
    # ... other scoring ...
    
    # Cult track scoring - sort players by position
    cult_positions = [
        (name, self.__players[name].cult_position)
        for name in self.__turn_order
    ]
    cult_positions.sort(key=lambda x: x[1], reverse=True)
    
    # Award points for top 3 positions
    scoring_map = {0: 8, 1: 4, 2: 2}  # 1st/2nd/3rd place
    
    for rank, (player_name, position) in enumerate(cult_positions[:3]):
        if position > 0:  # Must have advanced at least once
            scores[player_name] += scoring_map.get(rank, 0)
```

So we should **remove that TODO** - the cult track is just:
- Pay 1 worker to advance 1 space
- Score 8/4/2 VP at game end for top 3 players
- No intermediate benefits

This keeps it simple and saves code!

# Removal of commands
Looking at our commands and game design, we can eliminate several commands that don't add value to our OOP design:

## Commands to Remove:

### 1. **PassCommand** - Completely unnecessary
```python
class PassCommand(GameCommand):
    def validate_and_execute(self) -> None:
        """Always valid - Game handles pass logic."""
        pass  # Does literally nothing!
```
This is a no-op command. The `Game` class already handles all pass logic directly. Creating a command object that does nothing doesn't demonstrate any OOP principles.

### 2. **PowerCommand** - Just resource conversion
The power actions in our simplified game just convert power → workers. This doesn't add interesting game mechanics or OOP design value. Instead, we could:
- Keep the power bowl system (that's unique and interesting)
- Remove power "actions" 
- Let players convert power → coins directly as a simple exchange (like the exemplar's conversions)

### 3. **CultCommand** - Too simple
Paying 1 worker to advance 1 space is trivial. We could either:
- Remove the cult track entirely (saves more lines)
- OR make cult advancement automatic (e.g., gain cult when building)

## Refined Implementation:

```python
"""
Command pattern for core game actions only.

PATTERN: Command pattern for transform and build actions.
TYPE: Focused implementation with only essential commands.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

from .coords import HexCoord
from .types import (
    BuildingType,
    ResourceCost,
    TerrainType,
    BUILDING_COSTS,
    SPADE_EXCHANGE_RATE,
)

if TYPE_CHECKING:
    from .game import Game
    from .player import Player
    from .board import Board


class GameCommand(ABC):
    """
    PATTERN: Command pattern base for game actions.
    
    Only implements commands that add meaningful game logic.
    """

    def __new__(cls, game: Game, player_name: str) -> Self:
        """Validate command creation."""
        from .game import Game
        
        if not isinstance(game, Game):
            raise TypeError("Commands must be created by Game")
        
        self = super().__new__(cls)
        self._game = game
        self._player_name = player_name
        return self

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command with integrated validation.
        
        STAGING: Raises ValueError if validation fails.
        """
        ...

    def _player(self) -> Player:
        return self._game._get_player_internal(self._player_name)

    def _board(self) -> Board:
        return self._game._get_board()


class TransformCommand(GameCommand):
    """
    Transform terrain - core mechanic showing command pattern.
    
    Encapsulates terrain transformation logic including:
    - Distance calculation
    - Faction ability application  
    - Resource cost calculation
    """

    def __new__(
        cls, game: Game, player: str, pos: HexCoord, terrain: TerrainType
    ) -> Self:
        self = super().__new__(cls, game, player)
        self._pos = pos
        self._terrain = terrain
        return self

    def execute(self) -> None:
        """
        STAGING: Validates position, adjacency, and resources.
        """
        board = self._board()
        player = self._player()
        
        # Validate position
        if not board.is_valid_position(self._pos):
            raise ValueError("Invalid position")
        if board.has_building(self._pos):
            raise ValueError("Position occupied")
        
        current = board.get_terrain(self._pos)
        if current == self._terrain:
            raise ValueError("Already target terrain")
        
        # Validate adjacency
        if not board.is_adjacent_to_player(self._pos, player):
            raise ValueError("Must be adjacent to your buildings")
        
        # Calculate cost with faction ability
        tm = self._game._get_terrain_manager()
        base_spades = tm.calculate_distance(current, self._terrain)
        spades = player.get_modify_terrain_cost(base_spades)
        cost = {"workers": spades * SPADE_EXCHANGE_RATE}
        
        # Validate affordability
        if not player.can_afford(cost):
            raise ValueError(f"Need {cost['workers']} workers")
        
        # Execute
        player.pay_cost(cost)
        board.set_terrain(self._pos, self._terrain)


class BuildingCommand(GameCommand):
    """
    Build or upgrade buildings - core mechanic with strategy pattern.
    
    Handles both dwelling construction and upgrades with:
    - Terrain validation
    - Adjacency rules
    - Faction cost modifications
    - Adjacency discounts
    """

    def __new__(
        cls, game: Game, player: str, pos: HexCoord, upgrade: bool = False
    ) -> Self:
        self = super().__new__(cls, game, player)
        self._pos = pos
        self._upgrade = upgrade
        return self

    def execute(self) -> None:
        """
        STAGING: Validates and executes build or upgrade.
        """
        if self._upgrade:
            self._execute_upgrade()
        else:
            self._execute_build()

    def _execute_build(self) -> None:
        """Build a new dwelling."""
        board = self._board()
        player = self._player()
        
        # Validate terrain and position
        if board.get_terrain(self._pos) != player.home_terrain:
            raise ValueError("Must build on home terrain")
        if board.has_building(self._pos):
            raise ValueError("Position occupied")
        
        # Validate adjacency (unless first building)
        if player.get_buildings_list():
            if not board.is_adjacent_to_player(self._pos, player):
                raise ValueError("Must be adjacent to your buildings")
        
        # Apply faction ability to cost
        base = BUILDING_COSTS[BuildingType.DWELLING]
        cost = player.get_modify_building_cost(base)
        
        if not player.can_afford(cost):
            raise ValueError(f"Need {cost} to build")
        
        # Execute
        player.pay_cost(cost)
        board.place_building(self._pos, BuildingType.DWELLING, self._player_name)
        player.add_building(self._pos, BuildingType.DWELLING)

    def _execute_upgrade(self) -> None:
        """Upgrade dwelling to trading house."""
        board = self._board()
        player = self._player()
        
        # Validate building exists and is dwelling
        building = player.get_building_at(self._pos)
        if building != BuildingType.DWELLING:
            raise ValueError("Can only upgrade dwellings")
        
        # Calculate cost with faction ability
        base = BUILDING_COSTS[BuildingType.TRADING_HOUSE]
        cost = player.get_modify_building_cost(base)
        
        # Apply adjacency discount
        if board.has_adjacent_opponent_building(self._pos, self._player_name):
            cost["coins"] = cost.get("coins", 0) // 2
        
        if not player.can_afford(cost):
            raise ValueError(f"Need {cost} to upgrade")
        
        # Execute
        player.pay_cost(cost)
        player.remove_building(self._pos)
        player.add_building(self._pos, BuildingType.TRADING_HOUSE)
        board.place_building(
            self._pos, BuildingType.TRADING_HOUSE, self._player_name
        )
```

And in `game.py`, simplify the API:

```python
# Remove these methods:
# - use_power_action() 
# - advance_on_cult_track()

# Simplify pass to not use command:
def pass_turn(self, player_name: Name) -> None:
    """Pass for the round - no command needed."""
    self.__validate_turn(player_name)
    
    if player_name in self.__passed_players:
        raise ValueError(f"{player_name} already passed")
    
    self.__passed_players.add(player_name)
    self.end_turn()

# Add simple conversion instead of power actions:
def convert_resources(
    self, 
    player_name: Name, 
    from_resource: str, 
    to_resource: str,
    amount: int
) -> None:
    """Simple resource conversion following game rules."""
    self.__validate_turn(player_name)
    # e.g., 3 power → 1 worker, 1 power → 1 coin
```

This approach:
1. **Saves ~250 lines** from actions.py
2. **Focuses on core mechanics** that demonstrate OOP
3. **Keeps interesting patterns**: Command pattern with real logic
4. **Removes trivial commands** that don't add design value
5. **Simplifies Game API** by removing unnecessary methods

The remaining commands (Transform and Building) are substantial enough to demonstrate the command pattern properly while being essential to the game mechanics.