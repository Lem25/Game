from constants import TOWER_COSTS, TRAP_COSTS


def get_structure_build_cost(structure):
    if hasattr(structure, 'build_cost') and structure.build_cost:
        return structure.build_cost
    if hasattr(structure, 'type') and structure.type in TOWER_COSTS:
        return TOWER_COSTS[structure.type]
    if hasattr(structure, 'trap_type'):
        return TRAP_COSTS.get(structure.trap_type, 0)
    return 0


def get_structure_sell_value(structure):
    build_cost = get_structure_build_cost(structure)
    upgrade_spent = getattr(structure, 'upgrade_spent', 0)
    total_spent = max(0, build_cost + upgrade_spent)
    return max(0, int(total_spent * 0.70))


def calculate_interest(money: int) -> int:
    if money <= 500:
        rate = 0.05
    elif money <= 1200:
        rate = 0.03
    else:
        rate = 0.02
    return min(150, int(money * rate))
