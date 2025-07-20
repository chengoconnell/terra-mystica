#!/usr/bin/env python3
"""Test script to verify Terra Mystica game ends properly after 6 rounds."""

from game import Game
from game.player import FactionType
from game.resources import Resources


def test_endgame():
    """Test that the game ends properly and calculates final scores."""
    print("Testing Terra Mystica end-game mechanics...")
    
    # Create game with 2 players
    game = Game(player_count=2)
    
    # Add players
    player1 = game.add_player(FactionType.CHAOS_MAGICIANS)
    player2 = game.add_player(FactionType.DWARVES)
    
    # Start the game
    game.start_game()
    print(f"Game started. Current round: {game.get_round()}")
    
    # Simulate 6 rounds by having players pass each round
    for round_num in range(1, 7):
        print(f"\n--- Round {round_num} ---")
        print(f"Phase: {game.get_phase().name}")
        
        # Each round, both players just pass
        # This will advance through all phases
        passes = 0
        max_passes = 20  # Safety limit
        
        while game.get_round() == round_num and passes < max_passes:
            current_player = game.get_current_player()
            if current_player:
                print(f"Player {current_player.get_faction().name} passing...")
                game.pass_turn(current_player)
            passes += 1
            
        print(f"Round {round_num} complete. Current phase: {game.get_phase().name}")
    
    # Check that game has ended
    print(f"\n--- Game End Check ---")
    print(f"Current round: {game.get_round()}")
    print(f"Current phase: {game.get_phase().name}")
    print(f"Is game over: {game._round_manager.is_game_over() if game._round_manager else 'No round manager'}")
    
    # Show final scores
    print(f"\n--- Final Scores ---")
    players = game.get_players()
    for i, player in enumerate(players):
        resources = player.get_resources()
        vp = player.get_victory_points()
        print(f"\nPlayer {i} ({player.get_faction().name}):")
        print(f"  Victory Points: {vp}")
        print(f"  Leftover coins: {resources.coins} (worth {resources.coins // 3} VP)")
        print(f"  Workers: {resources.workers}")
        print(f"  Priests: {resources.priests}")
        print(f"  Power: {resources.power_bowls.available_power()}")
        
        # Check cult positions
        if game._cult_board:
            from game.cults import CultType
            print(f"  Cult positions:")
            for cult in CultType:
                position = game._cult_board.get_position(player, cult)
                print(f"    {cult.name}: {position}")
    
    # Verify the game phase is GAME_END
    from game.game import GamePhase
    if game.get_phase() == GamePhase.GAME_END:
        print("\n✅ Game ended successfully!")
    else:
        print(f"\n❌ Game did not end properly. Phase is {game.get_phase().name}")
    
    return game.get_phase() == GamePhase.GAME_END


if __name__ == "__main__":
    success = test_endgame()
    if success:
        print("\nAll end-game tests passed!")
    else:
        print("\nEnd-game test failed!")
        exit(1)
