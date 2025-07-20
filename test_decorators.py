"""Quick test of validation decorators"""

from game import Game

# Create a game
game = Game(player_factions=["Giants", "Witches"])

# Test 1: Try to pass twice (should fail)
print("Test 1: Pass validation")
try:
    game.pass_turn()  # First pass should work
    print("First pass successful")
    game.pass_turn()  # Second pass should fail
except ValueError as e:
    print(f"Expected error: {e}")

# Reset for next test
game = Game(player_factions=["Giants", "Witches"])

# Test 2: Try to build without enough resources
print("\nTest 2: Resource validation")
current_player = game._players[game._current_player_index]
print(f"Current resources: {current_player.resources.workers} workers, {current_player.resources.coins} coins")

# Spend most resources
current_player.resources.spend(workers=current_player.resources.workers - 1)

try:
    from game.coordinate import Coordinate
    from game.core import Terrain
    game.transform_and_build(Coordinate(0, 0), Terrain.MOUNTAINS)
except ValueError as e:
    print(f"Expected error: {e}")

print("\nDecorators working correctly!")
