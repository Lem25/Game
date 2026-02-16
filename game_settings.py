import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).with_name('settings.json')

DEFAULT_RESOLUTION = (800, 600)
RESOLUTION_OPTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
]

DEFAULT_KEYBINDS = {
    'pause': 'escape',
    'open_guide': 'h',
    'open_settings': 'o',
    'build_physical': '1',
    'build_magic': '2',
    'build_ice': '3',
    'build_fire': '4',
    'build_spikes': '5',
    'build_sentinel': '6',
    'upgrade_path1': 'q',
    'upgrade_path2': 'e',
    'sell_structure': 'r',
    'cycle_speed': 'c',
}


def _sanitize_resolution(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return DEFAULT_RESOLUTION
    try:
        width = max(640, int(value[0]))
        height = max(480, int(value[1]))
        return (width, height)
    except Exception:
        return DEFAULT_RESOLUTION


def _sanitize_keybinds(value):
    if not isinstance(value, dict):
        return dict(DEFAULT_KEYBINDS)

    keybinds = dict(DEFAULT_KEYBINDS)
    for action, default_key in DEFAULT_KEYBINDS.items():
        bound = value.get(action, default_key)
        if isinstance(bound, str) and bound.strip():
            keybinds[action] = bound.strip().lower()
    return keybinds


def load_settings():
    if not SETTINGS_PATH.exists():
        return {'resolution': list(DEFAULT_RESOLUTION), 'keybinds': dict(DEFAULT_KEYBINDS)}

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {'resolution': list(DEFAULT_RESOLUTION), 'keybinds': dict(DEFAULT_KEYBINDS)}

    resolution = _sanitize_resolution(data.get('resolution', DEFAULT_RESOLUTION))
    keybinds = _sanitize_keybinds(data.get('keybinds', DEFAULT_KEYBINDS))
    return {'resolution': list(resolution), 'keybinds': keybinds}


def save_settings(settings):
    resolution = _sanitize_resolution(settings.get('resolution', DEFAULT_RESOLUTION))
    keybinds = _sanitize_keybinds(settings.get('keybinds', DEFAULT_KEYBINDS))
    payload = {
        'resolution': [resolution[0], resolution[1]],
        'keybinds': keybinds,
    }
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
