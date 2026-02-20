BASE_EFFECTS = {
    "archer_damage_mult": 1.0,
    "magic_interval_mult": 1.0,
    "slow_decay_mult": 1.0,
    "start_gold_bonus": 0,
    "spike_damage_mult": 1.0,
    "burn_dot_mult": 1.0,
    "tower_range_mult": 1.0,
    "rapid_deployment": False,
    "focused_targeting_bonus": 1.0,
    "sell_refund_rate": 0.70,
    "enemy_speed_mult": 1.0,
    "enemy_reward_mult": 1.0,
    "tower_damage_mult": 1.0,
    "kill_reward_mult": 1.0,
    "interest_cap_bonus": 0,
    "interest_mult": 1.0,
    "tower_attack_interval_mult": 1.0,
}

_MODIFIER_SPECS = [
    (1, "Sharpened Arrows", "Archer Tower damage +12%.", 1, {"archer_damage_mult": 1.12}),
    (2, "Efficient Wiring", "Magic Tower attack interval -10%.", 1, {"magic_interval_mult": 0.90}),
    (3, "Cold Front", "Slow stack decay rate -25%.", 1, {"slow_decay_mult": 0.75}),
    (4, "Prepared Defenses", "Start with +60 gold.", 1, {"start_gold_bonus": 60}),
    (5, "Reinforced Triggers", "Spike Trap damage +20%.", 1, {"spike_damage_mult": 1.20}),
    (6, "Hotter Flames", "Burn DOT +20%.", 1, {"burn_dot_mult": 1.20}),
    (7, "Long Sightlines", "All towers +8% range.", 1, {"tower_range_mult": 1.08}),
    (8, "Rapid Deployment", "First tower built each wave costs -15%.", 1, {"rapid_deployment": True}),
    (9, "Focused Targeting", "Towers gain +10% damage vs Strongest target.", 1, {"focused_targeting_bonus": 1.10}),
    (10, "Efficient Salvage", "Sell refund increased to 75%.", 1, {"sell_refund_rate": 0.75}),
    (11, "Volatile Enemies", "Enemies +15% speed, rewards +25%.", 2, {"enemy_speed_mult": 1.15, "enemy_reward_mult": 1.25}),
    (12, "Glass Cannons", "Towers +20% damage, towers -15% range.", 2, {"tower_damage_mult": 1.20, "tower_range_mult": 0.85}),
    (13, "Greedy Markets", "Interest cap +50, kill rewards -10%.", 2, {"interest_cap_bonus": 50, "kill_reward_mult": 0.90}),
    (14, "Overclocked Grid", "All towers attack 15% faster, interest gains halved.", 3, {"tower_attack_interval_mult": 0.85, "interest_mult": 0.50}),
]


def _build_apply(overrides):
    def _apply(effects):
        effects.update(overrides)

    return _apply


MODIFIERS = {
    modifier_id: {
        "id": modifier_id,
        "name": name,
        "description": description,
        "tier": tier,
        "apply": _build_apply(overrides),
    }
    for modifier_id, name, description, tier, overrides in _MODIFIER_SPECS
}

def get_modifier(modifier_id: int) -> dict | None:
    return MODIFIERS.get(int(modifier_id))


def compile_run_effects(modifier_id: int | None) -> dict:
    effects = {
        "modifier_id": modifier_id,
        **BASE_EFFECTS,
    }

    modifier = get_modifier(modifier_id) if modifier_id is not None else None
    if modifier and callable(modifier.get("apply")):
        modifier["apply"](effects)

    return effects
