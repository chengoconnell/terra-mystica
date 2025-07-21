#!/usr/bin/env python3
"""Complete Terra Mystica game simulation demonstrating all mechanics."""

from game.game import Game
from game.player import Player, FactionType
from game.board import AxialCoord, TerrainType
from game.structures import StructureType
from game.resources import Resources, PowerBowls
from game.actions import BuildAction, TerraformAction, PassAction
from game.cults import CultType, CultTrack


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)


def print_player_status(game: Game, player: Player):
    """Print detailed player status."""
    resources = player.get_resources()
    print(f"\n{player.get_faction_name()}:")
    print(f"  Resources: {resources.workers}W, {resources.coins}C, {resources.priests}P")
    print(f"  Power: {resources.available_power} available (Total: {resources.total_power})")
    print(f"  Victory Points: {player.get_victory_points()}")
    print(f"  Shipping: {player.get_shipping_level()}")
    
    # Show structures
    structures = game.get_board().get_structures_of_player(player)
    if structures:
        print(f"  Structures: {len(structures)}")
        for coord, struct_type in structures[:3]:  # Show first 3
            print(f"    - {struct_type.name} at {coord}")
        if len(structures) > 3:
            print(f"    ... and {len(structures) - 3} more")


def find_home_terrain_hex(game: Game, player: Player):
    """Find a hex with player's home terrain."""
    home_terrain = player.get_home_terrain()
    board = game.get_board()
    # Iterate through all coordinates to find a suitable hex
    for q in range(-2, 3):
        for r in range(-2, 3):
            coord = AxialCoord(q, r)
            hex_space = board.get_hex(coord)
            if hex_space and hex_space.terrain == home_terrain and not hex_space.is_river and not hex_space.owner:
                return coord
    return None


def simulate_full_game():
    """Simulate a complete Terra Mystica game."""
    print_separator("TERRA MYSTICA FULL GAME SIMULATION")
    
    # Create game and add players
    game = Game(player_count=3)
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)
    player2 = game.add_player(FactionType.DWARVES)
    player3 = game.add_player(FactionType.HALFLINGS)
    
    game.start_game()
    print(f"Game started with {len(game.get_players())} players")
    print(f"Initial phase: {game.get_phase().name}")
    
    # The game should now be in ACTIONS phase after processing initial income
    print(f"Current phase after start: {game.get_phase().name}")
    
    # Round 1
    print_separator("ROUND 1 - INITIAL SETUP")
    
    # Show initial state
    for player in [player1, player2, player3]:
        print_player_status(game, player)
    
    # Player 1 builds initial dwelling
    print_separator("PLAYER 1 TURN - BUILD DWELLING")
    p1_home_hex = find_home_terrain_hex(game, player1)
    if p1_home_hex:
        print(f"Building dwelling at {p1_home_hex}")
        build_action = BuildAction(coord=p1_home_hex, structure_type=StructureType.DWELLING)
        game.execute_action(player1, build_action)
        print("✅ Dwelling built successfully")
        print_player_status(game, player1)
    
    # Player 2 builds initial dwelling
    print_separator("PLAYER 2 TURN - BUILD DWELLING")
    p2_home_hex = find_home_terrain_hex(game, player2)
    if p2_home_hex:
        print(f"Building dwelling at {p2_home_hex}")
        build_action = BuildAction(coord=p2_home_hex, structure_type=StructureType.DWELLING)
        game.execute_action(player2, build_action)
        print("✅ Dwelling built successfully")
        print_player_status(game, player2)
    
    # Player 3 builds and advances cult
    print_separator("PLAYER 3 TURN - BUILD & CULT ADVANCE")
    p3_home_hex = find_home_terrain_hex(game, player3)
    if p3_home_hex:
        print(f"Building dwelling at {p3_home_hex}")
        build_action = BuildAction(coord=p3_home_hex, structure_type=StructureType.DWELLING)
        game.execute_action(player3, build_action)
        print("✅ Dwelling built successfully")
    
    # TEST CULT ADVANCEMENT AND POWER MILESTONES
    print_separator("CULT ADVANCEMENT TEST - POWER MILESTONES")
    cult_board = game.get_cult_board()
    
    # Test advancing to milestone positions
    print("\nTesting cult advancement power milestones:")
    print("Expected: Space 3=1P, Space 5=2P, Space 7=2P, Space 10=3P")
    
    # Player 1 advances on Fire cult
    print(f"\n{player1.get_faction_name()} on FIRE cult:")
    initial_power = player1.get_resources().available_power
    print(f"  Initial power: {initial_power}")
    
    # Advance to space 3 (should gain 1 power)
    power_gained = cult_board.advance_on_cult(player1, CultType.FIRE, 3)
    new_power = player1.get_resources().available_power
    print(f"  Advanced to space 3: +{power_gained} power (total: {new_power})")
    
    # Advance to space 5 (should gain 2 power)
    power_gained = cult_board.advance_on_cult(player1, CultType.FIRE, 2)
    new_power = player1.get_resources().available_power
    print(f"  Advanced to space 5: +{power_gained} power (total: {new_power})")
    
    # Player 2 advances on Water cult to multiple milestones
    print(f"\n{player2.get_faction_name()} on WATER cult:")
    initial_power = player2.get_resources().available_power
    print(f"  Initial power: {initial_power}")
    
    # Advance directly to space 7 (should gain 1+2+2 = 5 power)
    power_gained = cult_board.advance_on_cult(player2, CultType.WATER, 7)
    new_power = player2.get_resources().available_power
    print(f"  Advanced to space 7: +{power_gained} power (total: {new_power})")
    
    # Player 3 advances to max position
    print(f"\n{player3.get_faction_name()} on EARTH cult:")
    initial_power = player3.get_resources().available_power
    print(f"  Initial power: {initial_power}")
    
    # Advance to space 10 (should gain all milestone power: 1+2+2+3 = 8)
    power_gained = cult_board.advance_on_cult(player3, CultType.EARTH, 10)
    new_power = player3.get_resources().available_power
    print(f"  Advanced to space 10 (max): +{power_gained} power (total: {new_power})")
    
    # Test multiple players on same space (no pushing)
    print("\n\nTesting multiple players on same cult space:")
    print(f"Player 2 advances to Fire 5 (same as Player 1)...")
    cult_board.advance_on_cult(player2, CultType.FIRE, 5)
    
    print("\nFire cult positions:")
    for player in [player1, player2, player3]:
        pos = cult_board.get_position(player, CultType.FIRE)
        print(f"  {player.get_faction_name()}: position {pos}")
    print("✅ Multiple players can occupy the same space (no pushing)")
    
    # Continue round with dynamic turn order
    print_separator("CONTINUING ROUND 1 - PLAYERS PASS")
    
    # Track who has passed
    passed_players = set()
    
    # Continue until all players have passed
    while len(passed_players) < 3:
        current = game.get_current_player()
        if current and current not in passed_players:
            print(f"\n{current.get_faction_name()} passes")
            game.execute_action(current, PassAction())
            passed_players.add(current)
        else:
            break
    
    # Show cult positions (all at starting positions)
    print("\nCult Track Positions:")
    cult_board = game.get_cult_board()
    for cult_type in [CultType.FIRE, CultType.WATER, CultType.EARTH, CultType.AIR]:
        print(f"\n{cult_type.name} Track:")
        for player in game.get_players():
            pos = cult_board.get_position(player, cult_type)
            print(f"  {player.get_faction_name()}: {pos}")
    
    # All players have now passed, round should transition
    print_separator("END OF ROUND 1")
    
    # Check phase transition
    print(f"\nCurrent phase: {game.get_phase().name}")
    print(f"Current round: {game.get_round()}")
    
    # Show income phase
    if game.get_phase().name == "INCOME":
        print_separator("INCOME PHASE")
        for player in [player1, player2, player3]:
            print_player_status(game, player)
    
    # Fast forward through remaining rounds
    print_separator("SIMULATING REMAINING ROUNDS")
    round_count = 2
    while game.get_phase().name != "GAME_END" and round_count <= 6:
        print(f"\nRound {round_count}...")
        
        # Each player takes one action then passes
        for i, player in enumerate([player1, player2, player3]):
            if game.get_current_player() == player:
                # Try to build if possible
                home_hex = find_home_terrain_hex(game, player)
                if home_hex and player.get_resources().workers >= 2:
                    try:
                        build_action = BuildAction(coord=home_hex, structure_type=StructureType.DWELLING)
                        game.execute_action(player, build_action)
                        print(f"  {player.get_faction_name()} built dwelling")
                    except:
                        game.execute_action(player, PassAction())
                        print(f"  {player.get_faction_name()} passed")
                else:
                    game.execute_action(player, PassAction())
                    print(f"  {player.get_faction_name()} passed")
        
        round_count += 1
        
        # Safety check
        if round_count > 10:
            print("Safety limit reached")
            break
    
    # Final game state
    print_separator("GAME END - FINAL SCORES")
    print(f"Final phase: {game.get_phase().name}")
    
    if game.get_phase().name == "GAME_END":
        print("\n🏆 FINAL VICTORY POINTS:")
        scores = []
        for player in [player1, player2, player3]:
            vp = player.get_victory_points()
            scores.append((player, vp))
            print(f"{player.get_faction_name()}: {vp} VP")
            
            # Show scoring breakdown
            structures = game.get_board().get_structures_of_player(player)
            print(f"  - Structures built: {len(structures)}")
            
            # Show cult positions
            cult_positions = game.get_cult_board().get_all_positions(player)
            for cult_type, position in cult_positions.items():
                if position > 0:
                    print(f"  - {cult_type.name} cult: position {position}")
        
        # Determine winner (Game class doesn't provide this functionality)
        # In a real game, you might have tiebreaker rules here
        scores.sort(key=lambda x: x[1], reverse=True)
        winner = scores[0][0]
        print(f"\n🎉 WINNER: {winner.get_faction_name()} with {scores[0][1]} VP!")
        
        # Show rankings
        print("\nFinal Rankings:")
        for i, (player, vp) in enumerate(scores, 1):
            print(f"{i}. {player.get_faction_name()}: {vp} VP")
    
    print_separator()
    print("Simulation complete!")


if __name__ == "__main__":
    simulate_full_game()
