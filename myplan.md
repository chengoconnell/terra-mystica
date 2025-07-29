1. Simplified Terrain & Building System 
- Only 3 terrain types, 1 building type (dwelling)
- Implement the transformation cycle (spending spades to change terrain)
- Basic adjacency rules for building

2. Power bowl system
- Simplified power system, single score instead of bowls
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
- Buildings: 2 VP per Dwelling
- Largest connected area: 18/12/6 VP for 1st/2nd/3rd

8. Power actions: 2 actions:
- Gain 2 spades (costs 4 power)
- Gain 3 workers (costs 3 power)

Module structure:
game/ ├── init.py # Exports only Game class 
      ├── types.py # TypedDicts, Enums, Protocols, type aliases 
      ├── hexgrid.py # Generic hex grid (like WithdrawableStack) 
      ├── coords.py # Coordinate systems and conversions 
      ├── power.py # Simplified power system, single score instead of bowls
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
- Phase structure (use simple turn-based play) 
- Complex scoring (just count buildings)


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

# Fluent interface pattrn

```py
# In game.py
class Game:
    def action(self, player_name: Name) -> ActionBuilder:
        """
        Create an action builder for the specified player.
        
        PATTERN: Fluent interface factory
        
        :param player_name: Name of the acting player
        :return: ActionBuilder for chaining commands
        :raises ValueError: if not player's turn
        """
        # Validate it's this player's turn
        current_player = self.__player_order[self.__state["current_player_index"]]
        if player_name != current_player:
            raise ValueError(f"Not {player_name}'s turn")
            
        # Create builder with construction control
        with ActionBuilder._constructing_builder():
            return ActionBuilder(self, player_name)

# Example usage:
game = Game([("Alice", "witches"), ("Bob", "engineers")])

# Clean, type-safe API
game.action("Alice").transform(0, 1, "forest")
game.action("Alice").build(0, 1)

game.action("Bob").use_power("gain_workers")
game.action("Bob").advance_cult()

# Direct API still works
action = {"action": "pass", "player": "Bob"}
game.execute_action(action)
```

# Observer pattern but for boards
Looking at the Terra Mystica rules, here's how the adjacency power bonus works:

## From the Rules (page 12):

**Power via Structures**
Each Structure has a Power value:
- The Stronghold and Sanctuary have a Power value of 3.
- Trading houses and Temples have a Power value of 2.
- Dwellings have a Power value of 1.

When building a Dwelling (Action #1) or upgrading a Structure (Action #4), you must inform the owners of Structures directly adjacent to your Structure that they may gain Power.

In order to determine the total number of Power an opponent may gain, add up the Power values of their Structures directly adjacent to your newly built Structure.

**The price of Power**
Unfortunately, Power gained via Structures is not free. To gain that Power, you need to lose a number of Victory points equal to one fewer than the number of Power gained.

## Observer Pattern Implementation:

```python
# In board.py
class Board:
    """
    PATTERN: Observer pattern for power gain notifications
    TYPE: Subject in observer pattern
    """
    
    def notify_building_placed(
        self, 
        position: HexCoord, 
        building_type: BuildingType,
        builder_name: Name
    ) -> None:
        """
        Notify adjacent players about building placement.
        
        PATTERN: Observer notification
        """
        # Find all adjacent opponent buildings
        power_opportunities = self._calculate_power_opportunities(
            position, builder_name
        )
        
        # Notify each affected player
        for opponent_name, power_gain in power_opportunities.items():
            player = self._get_player(opponent_name)
            # Observer decides whether to accept
            player.notify_adjacent_building(
                builder_name, position, building_type, power_gain
            )
    
    def _calculate_power_opportunities(
        self, position: HexCoord, builder_name: Name
    ) -> dict[Name, int]:
        """Calculate power gain for each adjacent opponent."""
        opportunities = {}
        
        for neighbor_pos in self.grid.get_neighbors(position):
            if neighbor_pos in self.grid:
                building = self.get_building(neighbor_pos)
                if building and building["owner"] != builder_name:
                    owner = building["owner"]
                    power_value = BUILDING_POWER_VALUES[building["type"]]
                    opportunities[owner] = opportunities.get(owner, 0) + power_value
                    
        return opportunities


# In player.py
class Player:
    """
    PATTERN: Observer in observer pattern
    TYPE: Concrete observer implementation
    """
    
    def notify_adjacent_building(
        self,
        builder: Name,
        position: HexCoord,
        building_type: BuildingType,
        power_gain: int
    ) -> bool:
        """
        Handle notification of adjacent building construction.
        
        PATTERN: Observer update method
        
        :param power_gain: Total power available from adjacent buildings
        :return: True if accepting power, False if declining
        """
        # Calculate VP cost
        vp_cost = max(0, power_gain - 1)  # First power is free
        
        # Auto-decline if would go negative VP
        if self.victory_points < vp_cost:
            return False
            
        # In simplified version, always accept if affordable
        # (In full game, this could be a strategic decision)
        if vp_cost <= self.victory_points:
            self.gain_power(power_gain)
            self.lose_victory_points(vp_cost)
            return True
            
        return False
```

## Why This is Perfect for Observer Pattern:

1. **Decoupling**: The builder doesn't need to know about other players' power systems
2. **Dynamic Subscribers**: Players automatically get notified when adjacent
3. **Individual Responses**: Each player decides independently whether to accept
4. **Event-Driven**: Building placement triggers notifications

## Simplified Version for Your Implementation:

Since you have limited lines, you could simplify:

```python
# Simplified: Always accept power if able
def notify_adjacent_building(self, power_gain: int) -> None:
    """Simplified observer: auto-accept if possible."""
    vp_cost = max(0, power_gain - 1)
    if self.victory_points >= vp_cost:
        self.gain_power(power_gain)
        self.lose_victory_points(vp_cost)
```

This demonstrates the Observer pattern while keeping the code lean. The pattern shows:
- **Subject** (Board) maintains list of adjacent structures
- **Observers** (Players) get notified of relevant events  
- **Loose Coupling** - Board doesn't know Player implementation details
- **Event Propagation** - Building action cascades to power gains

This is one of the most elegant uses of Observer pattern in board games!


## removed code
```py
# game.py
    def get_board_state(self) -> dict[str, list[tuple[int, int]]]:
        """Get positions of all buildings by player.

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
```