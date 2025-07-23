from .types import (
    FactionAbility,
    FactionType,
    ResourceCost,
    SpadeCount,
)


class BaseFactionAbility(FactionAbility):
    """
    TYPE: Concrete base class implementing FactionAbility protocol.
    Base implementation of faction abilities with defaults.
    """

    def modify_terrain_cost(self, base_cost: SpadeCount) -> SpadeCount:
        """Default: no modification."""
        return base_cost

    def modify_building_cost(self, base_cost: ResourceCost) -> ResourceCost:
        """Default: no modification."""
        return base_cost


class WitchesAbility(BaseFactionAbility):
    """
    PATTERN: Strategy pattern implementation for Witches.
    Simplified from full Terra Mystica: Witches have no special abilities.
    """

    pass  # Uses default implementations from BaseFactionAbility


class EngineersAbility(BaseFactionAbility):
    """
    PATTERN: Strategy pattern implementation for Engineers.
    Engineers: Simplifictation - build at half cost
    """

    def modify_building_cost(self, base_cost: ResourceCost) -> ResourceCost:
        return {
            "workers": base_cost.get("workers", 0) // 2,
            "coins": base_cost.get("coins", 0) // 2,
            "power": base_cost.get("power", 0),  # Power costs not reduced
            "spades": base_cost.get("spades", 0),  # Spade costs not reduced
        }


class NomadsAbility(BaseFactionAbility):
    """
    PATTERN: Strategy pattern implementation for Nomads.
    Nomads: Simplification - transform terrain costs 1 less spade (minimum 1)
    """

    def modify_terrain_cost(self, base_cost: SpadeCount) -> SpadeCount:
        """Reduce terrain transformation cost by 1."""
        return max(1, base_cost - 1)


class FactionFactory:
    """
    PATTERN: Factory pattern for creating faction abilities
    TYPE: Static factory methods
    """

    @staticmethod
    def create_ability(faction_type: FactionType) -> FactionAbility:
        """Create the appropriate faction ability instance."""
        match faction_type:
            case FactionType.WITCHES:
                return WitchesAbility()
            case FactionType.ENGINEERS:
                return EngineersAbility()
            case FactionType.NOMADS:
                return NomadsAbility()
