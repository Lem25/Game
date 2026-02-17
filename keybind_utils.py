import pygame

from game_settings import DEFAULT_KEYBINDS


def normalize_key_name(name):
    key_name = (name or '').strip().lower()
    if key_name.startswith('[') and key_name.endswith(']') and len(key_name) > 2:
        key_name = key_name[1:-1].strip().lower()
    return key_name


def load_keybind_maps(settings_payload):
    raw_bindings = settings_payload.get('keybinds', {})
    keybind_names = {}
    keybind_codes = {}
    for action, default_name in DEFAULT_KEYBINDS.items():
        candidate = normalize_key_name(raw_bindings.get(action, default_name)) or default_name
        try:
            key_code = pygame.key.key_code(candidate)
        except Exception:
            candidate = default_name
            key_code = pygame.key.key_code(candidate)
        keybind_names[action] = candidate
        keybind_codes[action] = key_code
    return keybind_names, keybind_codes


def pretty_key_name(key_code):
    key_name = pygame.key.name(key_code)
    if len(key_name) == 1:
        return key_name.upper()
    return key_name.replace('_', ' ').title()
