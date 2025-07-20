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
    structures = game._board.get_structures_of_player(player)
    if structures:
        print(f"  Structures: {len(structures)}")
        for coord, struct_type in structures[:3]:  # Show first 3
            print(f"    - {struct_type.name} at {coord}")
        if len(structures) > 3:
            print(f"    ... and {len(structures) - 3} more")


def find_home_terrain_hex(game: Game, player: Player):
    """Find a hex with player's home terrain."""
    home_terrain = player.get_home_terrain()
    for hex_space in game._board._hexes.values():
        if hex_space.terrain == home_terrain and not hex_space.is_river and not hex_space.owner:
            return hex_space.coord
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
    print(f"Game started with {len(game._players)} players")
    print(f"Current phase: {game._current_phase.name}")
    
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
        for player in game._players:
            pos = cult_board.get_position(player, cult_type)
            print(f"  {player.get_faction_name()}: {pos}")
    
    # All players have now passed, round should transition
    print_separator("END OF ROUND 1")
    
    # Check phase transition
    print(f"\nCurrent phase: {game._current_phase.name}")
    print(f"Current round: {game._round_manager._current_round}")
    
    # Show income phase
    if game._current_phase.name == "INCOME":
        print_separator("INCOME PHASE")
        for player in [player1, player2, player3]:
            print_player_status(game, player)
    
    # Fast forward through remaining rounds
    print_separator("SIMULATING REMAINING ROUNDS")
    round_count = 2
    while game._current_phase.name != "GAME_END" and round_count <= 6:
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
    print(f"Final phase: {game._current_phase.name}")
    
    if game._current_phase.name == "GAME_END":
        print("\n🏆 FINAL VICTORY POINTS:")
        scores = []
        for player in [player1, player2, player3]:
            vp = player.get_victory_points()
            scores.append((player, vp))
            print(f"{player.get_faction_name()}: {vp} VP")
            
            # Show scoring breakdown
            structures = game._board.get_structures_of_player(player)
            print(f"  - Structures built: {len(structures)}")
            
            # Show cult positions
            for track in CultTrack:
                positions = game._cult_board.get_track_positions(track)
                if player._index in positions:
                    print(f"  - {track.name} cult: position {positions[player._index]}")
        
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
