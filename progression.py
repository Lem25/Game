import json
from pathlib import Path

PROGRESSION_PATH = Path(__file__).with_name("progression.json")

DEFAULT_PROGRESSION = {
    "level": 1,
    "xp": 0,
    "unlocked_modifiers": [1, 2, 3],
}

UNLOCK_BY_LEVEL = {
    2: 4,
    3: 5,
    4: 6,
    5: 7,
    6: 8,
    7: 9,
    8: 10,
    9: 11,
    10: 12,
    11: 13,
    12: 14,
}

LEGACY_MODIFIER_ID_MAP = {
    17: 13,
    23: 14,
}


def xp_to_next(level: int) -> int:
    return max(1, int(100 * (level ** 1.35)))


def _sanitize_progression(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    level = payload.get("level", DEFAULT_PROGRESSION["level"])
    xp = payload.get("xp", DEFAULT_PROGRESSION["xp"])
    unlocked_modifiers = payload.get("unlocked_modifiers", list(DEFAULT_PROGRESSION["unlocked_modifiers"]))

    try:
        level = max(1, int(level))
    except Exception:
        level = DEFAULT_PROGRESSION["level"]

    try:
        xp = max(0, int(xp))
    except Exception:
        xp = DEFAULT_PROGRESSION["xp"]

    if not isinstance(unlocked_modifiers, list):
        unlocked_modifiers = list(DEFAULT_PROGRESSION["unlocked_modifiers"])

    clean_unlocked = []
    seen = set()
    for value in unlocked_modifiers:
        try:
            mid = int(value)
        except Exception:
            continue
        mid = LEGACY_MODIFIER_ID_MAP.get(mid, mid)
        if mid > 0 and mid not in seen:
            seen.add(mid)
            clean_unlocked.append(mid)

    if not clean_unlocked:
        clean_unlocked = list(DEFAULT_PROGRESSION["unlocked_modifiers"])

    result = {
        "level": level,
        "xp": xp,
        "unlocked_modifiers": clean_unlocked,
    }
    sync_unlocks(result)
    return result


def load_progression() -> dict:
    if not PROGRESSION_PATH.exists():
        save_progression(dict(DEFAULT_PROGRESSION))
        return dict(DEFAULT_PROGRESSION)

    try:
        data = json.loads(PROGRESSION_PATH.read_text(encoding="utf-8"))
    except Exception:
        clean = dict(DEFAULT_PROGRESSION)
        save_progression(clean)
        return clean

    clean = _sanitize_progression(data)
    save_progression(clean)
    return clean


def save_progression(progression: dict) -> None:
    clean = _sanitize_progression(progression)
    PROGRESSION_PATH.write_text(json.dumps(clean, indent=2), encoding="utf-8")


def sync_unlocks(progression: dict) -> list[int]:
    unlocked = set(progression.get("unlocked_modifiers", []))
    gained = []
    level = int(progression.get("level", 1))
    for unlock_level, modifier_id in sorted(UNLOCK_BY_LEVEL.items()):
        if level >= unlock_level and modifier_id not in unlocked:
            unlocked.add(modifier_id)
            gained.append(modifier_id)

    progression["unlocked_modifiers"] = sorted(unlocked)
    return gained


def add_xp(progression: dict, amount: int) -> dict:
    amount = max(0, int(amount))
    progression["xp"] = int(progression.get("xp", 0)) + amount
    progression["level"] = max(1, int(progression.get("level", 1)))

    levels_gained = 0
    while progression["xp"] >= xp_to_next(progression["level"]):
        progression["xp"] -= xp_to_next(progression["level"])
        progression["level"] += 1
        levels_gained += 1

    newly_unlocked = sync_unlocks(progression)
    return {
        "levels_gained": levels_gained,
        "newly_unlocked": newly_unlocked,
    }
