"""Test the Player class implementation."""

from game.player import Player
from game.faction import Faction
from game.structures import StructureType
from game.coordinate import Coordinate


def test_player_initialization() -> None:
    """Test that players are initialized correctly per faction."""
    print("Testing Player Initialization...")
    
    # Test Witches faction
    witches_player = Player(Faction.WITCHES)
    print(f"\nWitches Player:")
    print(f"  Faction: {witches_player.faction}")
    print(f"  Home terrain: {witches_player.home_terrain}")
    print(f"  Starting VP: {witches_player.victory_points}")
    print(f"  Workers: {witches_player.resources.workers}")
    print(f"  Coins: {witches_player.resources.coins}")
    print(f"  Power distribution: {witches_player.resources.power_bowls}")
    print(f"  Shipping level: {witches_player.shipping_level}")
    print(f"  Spade level: {witches_player.spade_level}")
    
    # Test structure supply
    print(f"\n  Structure Supply:")
    for struct_type, count in witches_player.get_structure_supply().items():
        print(f"    {struct_type.name}: {count}")


def test_resource_management() -> None:
    """Test resource gain/spend operations."""
    print("\n\nTesting Resource Management...")
    player = Player(Faction.MERMAIDS)
    
    print(f"\nInitial resources:")
    print(f"  Workers: {player.resources.workers}")
    print(f"  Coins: {player.resources.coins}")
    
    # Test gaining resources
    player.resources.gain(workers=5, coins=10)
    print(f"\nAfter gaining 5 workers and 10 coins:")
    print(f"  Workers: {player.resources.workers}")
    print(f"  Coins: {player.resources.coins}")
    
    # Test spending resources
    try:
        player.resources.spend(workers=3, coins=7)
        print(f"\nAfter spending 3 workers and 7 coins:")
        print(f"  Workers: {player.resources.workers}")
        print(f"  Coins: {player.resources.coins}")
    except ValueError as e:
        print(f"  Error: {e}")


def test_victory_points() -> None:
    """Test victory point tracking."""
    print("\n\nTesting Victory Points...")
    player = Player(Faction.GIANTS)
    
    print(f"Initial VP: {player.victory_points}")
    
    player.add_victory_points(5)
    print(f"After adding 5 VP: {player.victory_points}")
    
    player.add_victory_points(-2)
    print(f"After losing 2 VP: {player.victory_points}")


def test_structure_placement() -> None:
    """Test building and tracking structures."""
    print("\n\nTesting Structure Placement...")
    player = Player(Faction.WITCHES)
    
    # Test building a dwelling
    coord1 = Coordinate(3, 4)
    try:
        player.build_structure(coord1, StructureType.DWELLING)
        print(f"\nBuilt dwelling at {coord1}")
        print(f"  Structures placed: {len(player.get_all_structures())}")
        print(f"  Dwellings remaining: {player.get_structure_supply()[StructureType.DWELLING]}")
    except (ValueError, KeyError) as e:
        print(f"  Error: {e}")
    
    # Test building on occupied space
    try:
        player.build_structure(coord1, StructureType.DWELLING)
    except ValueError as e:
        print(f"\nTrying to build on occupied space: {e}")
    
    # Test upgrading
    try:
        player.upgrade_structure(coord1, StructureType.TRADING_HOUSE)
        print(f"\nUpgraded to Trading House at {coord1}")
        print(f"  Structure at {coord1}: {player.get_structure_at(coord1)}")
        print(f"  Trading Houses remaining: {player.get_structure_supply()[StructureType.TRADING_HOUSE]}")
    except (ValueError, KeyError) as e:
        print(f"  Error: {e}")


def test_advancement_tracks() -> None:
    """Test shipping and spade advancement."""
    print("\n\nTesting Advancement Tracks...")
    player = Player(Faction.MERMAIDS)
    
    print(f"Initial shipping: {player.shipping_level}")
    print(f"Initial spade level: {player.spade_level}")
    
    # Test advancing shipping
    try:
        player.advance_shipping()
        print(f"\nAfter advancing shipping: {player.shipping_level}")
        
        # Advance to max
        player.advance_shipping()
        player.advance_shipping()
        print(f"After advancing to level 3: {player.shipping_level}")
        
        # Try to advance beyond max
        player.advance_shipping()
    except ValueError as e:
        print(f"Trying to advance beyond max: {e}")
    
    # Test spade advancement
    player2 = Player(Faction.GIANTS)
    try:
        player2.advance_spades()
        print(f"\nGiants after advancing spades: {player2.spade_level}")
        
        player2.advance_spades()
        print(f"After advancing to level 1: {player2.spade_level}")
        
        # Try to advance beyond min
        player2.advance_spades()
    except ValueError as e:
        print(f"Trying to advance beyond min: {e}")


def test_power_mechanics() -> None:
    """Test power bowl mechanics."""
    print("\n\nTesting Power Mechanics...")
    player = Player(Faction.WITCHES)
    
    print(f"Initial power: {player.resources.power_bowls}")
    print(f"Available power: {player.resources.available_power}")
    
    # Test gaining power
    player.resources.gain_power(3)
    print(f"\nAfter gaining 3 power: {player.resources.power_bowls}")
    
    # Test spending power
    try:
        if player.resources.available_power >= 2:
            player.resources.spend_power(2)
            print(f"After spending 2 power: {player.resources.power_bowls}")
    except ValueError as e:
        print(f"Error spending power: {e}")
    
    # Test power sacrifice (burn)
    try:
        before_sacrifice = player.resources.power_bowls
        player.resources.sacrifice_power(2)  # sacrifice takes an amount parameter
        after_sacrifice = player.resources.power_bowls
        print(f"\nPower before sacrifice: {before_sacrifice}")
        print(f"Power after sacrifice: {after_sacrifice}")
    except ValueError as e:
        print(f"Error sacrificing power: {e}")


if __name__ == "__main__":
    test_player_initialization()
    test_resource_management()
    test_victory_points()
    test_structure_placement()
    test_advancement_tracks()
    test_power_mechanics()
    
    print("\n\n✅ All tests completed!")
