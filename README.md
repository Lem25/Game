# Maze Treasure Defense — Full Technical Documentation

This document explains the entire project in depth: architecture, runtime flow, each module, and every function/method.

> **Last Updated:** February 2026  
> Includes wave templates, swarm burst groups, per-tower targeting UI, executioner tower, tiered economy scaling, freeze-resist scaling, main-menu guide access, and a modifiers guide tab.

---

## 1) Project Overview

`Maze Treasure Defense` is a single-process, real-time tower defense game built with **Python** and **Pygame**.

Core idea:
- Enemies spawn from lane start points.
- They pathfind to a central goal tile.
- Player places towers and traps to stop them.
- Every 5 waves, the map may expand with a new lane.

Primary game loop and orchestration live in `main.py`; gameplay helpers are split into focused modules (`economy.py`, `spawn_scaling.py`, `viewport_utils.py`, `placement_rules.py`, `wave_progression.py`, `keybind_utils.py`) to keep logic maintainable.

---

## 2) Runtime Architecture and Data Flow

### Startup flow
1. `pygame.init()` and window creation.
2. Constants and drawing/game systems imported.
3. `create_maze()` builds the grid, spawn points, and goal.
4. Initial state variables are initialized (money, lives, wave, app/menu state, etc.).
5. App starts in `main_menu` state and waits for menu input.
6. User enters wave selection, then modifier draft, then gameplay begins.

### Frame flow (`while run` in `main.py`)
1. Read inputs/events.
2. Handle pause/guide/placement/upgrade input.
3. Spawn enemies on timer.
4. Update enemies, towers, projectiles, traps.
5. Resolve death/goal outcomes (money gain, life loss).
6. Draw world + UI overlays.
7. Check victory/defeat conditions.

### Shared state objects
- `grid`: 2D tile map (`0` buildable, `1` wall, `2` path).
- `spawn_points`: list of active spawn tiles.
- `GOAL_GRID`: center goal tile.
- `towers`, `traps`, `projectiles`, `enemies`: active entity lists.
- economy state: `money`, `lives`.
- wave state: `wave`, `wave_enemies_left`, `enemy_scale`, `wave_timer`.

---

## 3) Module-by-Module Reference

## `main.py`

### Purpose
Game entrypoint. Owns global game state, loop timing, app-state transitions (menu/settings/guide/gameplay), input handling, spawn logic, and win/loss progression.

### App states (`app_state`)
- `main_menu`: start/progression/settings/guide buttons.
- `wave_select`: enter target wave.
- `modifier_draft`: pick one of three modifier cards.
- `progression`: persistent unlocks and modifier list.
- `menu_settings`: pre-run settings panel.
- `menu_guide`: full guide overlay accessible from main menu.
- `gameplay`: active run (with pause, in-run guide, and in-run settings).

### Functions

#### Wave selection flow
**What it does**
- Uses the `wave_select` app state before gameplay starts.
- Displays `draw_wave_selection_popup(...)` and accepts numeric keyboard input.
- Starts modifier draft after Enter with a valid positive target wave.

**Details**
- Backspace deletes digits.
- Input capped to 3 digits.
- Escape returns to main menu.

#### Wave template integration
**What it does**
- Uses `wave_templates.py` to choose enemy types by wave phase.

**Details**
- Swarm events spawn in grouped bursts (10–15).
- Enemy composition ramps by early/mid/late template pools.
- Bosses still spawn every 5th wave as final wave enemy.

#### `next_wave()`
**What it does**
- Advances game to the next wave and prepares spawn counts/mechanics.

**Behavior**
- Increments `wave`.
- Sets `wave_enemies_left` using phased progression (gentle early, stronger late).
- On every 5th wave:
  - Calls `expand_paths(...)` to add a new lane.
  - Removes towers that now collide with new carved path tiles.
  - Picks one spawn lane as `boss_spawn_lane`.
- Resets boss popup timer.
- Applies interval-based enemy scaling with phase-aware modifiers.

### Main loop responsibilities (non-function block)
- Handles pause states, guide navigation, placement hotkeys, and upgrade keys.
- Spawns enemies using wave-dependent spawn interval from `wave_templates.py`.
- Boss spawn logic:
  - Every 5th wave final spawn is boss.
  - Alternates minotaur and demon on 5/10 cadence.
- Supports speed cycle (`C`: 1x -> 2x -> 3x -> 1x).
- Supports per-selected sell flow (button in panel and hotkey fallback).
- Uses tiered interest and spawn-time balance scaling via extracted helper modules.
- Updates entities in deterministic order:
  1. enemies logic
  2. towers update
  3. projectile update/cleanup
  4. traps update
  5. enemy resolution (goal reached/dead)
- Draw order:
  grid -> towers -> projectiles -> traps -> enemies -> overlays/UI.

---

## `keybind_utils.py`

### Purpose
Central keybind normalization and mapping helpers.

### Functions
- `normalize_key_name(name)`
- `load_keybind_maps(settings_payload)`
- `pretty_key_name(key_code)`

---

## `economy.py`

### Purpose
Central economy helpers for structure valuation and interest.

### Functions
- `get_structure_build_cost(structure)`
- `get_structure_sell_value(structure)` (70% refund)
- `calculate_interest(money)` (5%/3%/2% tiers with cap)

---

## `spawn_scaling.py`

### Purpose
Spawn-time balancing helpers for freeze resistance and swarm reward anti-farm scaling.

### Functions
- `compute_freeze_resist(wave)`
- `compute_swarm_reward(base_reward, swarm_spawn_index)`
- `apply_spawn_scaling(enemy, wave_number, swarm_spawn_index=None)`

---

## `viewport_utils.py`

### Purpose
Window scaling and coordinate conversion helpers.

### Functions
- `get_viewport_rect(surface, base_width, base_height)`
- `present_frame(window, screen, base_width, base_height)`
- `window_to_game_pos(pos, viewport, base_width, base_height)`

---

## `placement_rules.py`

### Purpose
Placement validation rules for towers and traps.

### Functions
- `can_place_tower(grid, gx, gy, towers, tile_size, grid_width, grid_height)`
- `can_place_trap(grid, gx, gy, towers, traps, grid_width, grid_height, tile_size)`

---

## `wave_progression.py`

### Purpose
Wave-size curve helper used by `main.py`.

### Functions
- `get_wave_enemy_count(wave, target_wave)`

---

## `constants.py`

### Purpose
Central balancing and configuration values.

### Contents
- Display and grid geometry:
  - `WIDTH`, `HEIGHT`, `GAME_HEIGHT`
  - `TILE`, `GRID_W`, `GRID_H`
  - Current defaults: `TILE = 40`, `GRID_W = 20`, `GRID_H = 20` (800x800 playable grid)
- Timing:
  - `FPS`
- Economy:
  - `TOWER_COSTS`, `TRAP_COSTS`
- Enemy tuning:
  - `ENEMY_STATS` (HP/speed/resists/size/reward per enemy type)
- Trap tuning:
  - `TRAP_STATS` (`fire` DPS, `spikes` damage/interval)
- Scaling:
  - `ENEMY_SCALE_WAVE_INTERVAL`, `ENEMY_SCALE_INCREMENT`

`TRAP_COSTS` is defined once (duplicate declaration removed).

---

## `colors.py`

### Purpose
Named RGB constants for drawing.

### Contents
- Basic palette constants (`BLACK`, `WHITE`, `DARK_GRAY`, etc.).
- `ENEMY_COLORS` mapping enemy type -> fallback color (used when sprite unavailable).

---

## `assets.py`

### Purpose
Robust asset loader with fallback name strategies and image scaling.

### Module-level state
- `ASSET_DIR`: absolute path to local `assets/` folder.
- `_raw`: cache dictionary for original loaded images (or `None` on load failure).
- `_FALLBACK_NAMES`: canonical logical key -> alternate filename base.
- `_EXTS`: extension probe order (`.png`, `.jpg`, `.jpeg`).

### Functions

#### `_try_candidates(name)`
**What it does**
- Generates ordered candidate base names for a logical asset key.

**Strategies**
- direct key
- alias from `_FALLBACK_NAMES`
- reversed underscore words
- `enemy_foo` <-> `foo_enemy` transformations
- `proj_foo` variant support

#### `_load_raw(name)`
**What it does**
- Loads and caches a raw `pygame.Surface` for a logical key.

**Behavior**
- Iterates candidate names and extensions.
- Uses `pygame.image.load(...).convert_alpha()`.
- Stores result in `_raw` cache.
- Caches `None` if not found to avoid repeated disk scans.

#### `get(name, size=None)`
**What it does**
- Public accessor for image retrieval.

**Behavior**
- Returns `None` if asset not found.
- Returns copy of raw surface when `size is None`.
- If `size` is int, converts to square tuple.
- Uses smooth scaling when possible.

---

## `drawing.py`

### Purpose
All rendering utilities for map, HUD, overlays, guide, and upgrade panel.

### Functions

#### `draw_main_menu(screen, font)`
Renders the title screen and returns clickable button rects for:
- `Start Game`
- `Guide`
- `Progression`
- `Settings`

**Returns**
- `buttons` mapping for click routing in `main.py`.

#### `draw_grid(screen, grid, goal_grid)`
Draws each tile according to tile type:
- wall (`1`) with side-specific wall sprites where possible
- path (`2`) sprite/rect
- buildable ground (`0`) sprite/rect

Then draws goal gem (sprite fallback: gold circle).

#### `draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=None, game_speed=1, selected_structure=None)`
Draws bottom HUD panel:
- resources and wave data
- selected build type
- tower/trap hotkey legend with costs
- speed indicator and gameplay control hints
- selected tower targeting info when relevant

#### `draw_game_over(screen, font)`
Renders full-screen defeat state and three clickable text-button rects.

**Returns**
- `(play_again_rect, menu_rect, exit_rect)` for click handling in `main.py`.

#### `draw_boss_spawn_popup(screen, font, boss_type)`
Draws red center popup indicating boss spawn.

#### `draw_wave_selection_popup(screen, font, input_text)`
Renders startup modal for target wave numeric input.

#### `draw_pause(screen, font, guide_key='H', settings_key='O')`
Renders pause overlay, resume hint, and guide hint.

#### `draw_victory(screen, font)`
Renders full-screen victory state and three clickable text-button rects.

**Returns**
- `(play_again_rect, menu_rect, exit_rect)` for click handling in `main.py`.

#### `draw_guide(screen, font, page, scroll_offset=0)`
Draws documentation overlay (used both in paused gameplay and from main menu):
- page menu and per-page content
- custom tab strip
- clipped scrollable content area
- scrollbar with thumb
- contextual nav footer hints

**Guide pages**
- `[1]` Towers
- `[2]` Traps
- `[3]` Enemies
- `[4]` Mechanics
- `[5]` Strategy
- `[6]` Keybinds
- `[7]` Modifiers

**Returns**
- `max_scroll` for caller-side clamping.

#### `draw_upgrade_ui(screen, font, selected_structure, money, refund_rate=0.70)`
Draws floating panel near selected tower/trap with:
- path upgrades
- per-tower targeting buttons (where supported)
- sell button with current refund value

**Returns**
- panel metadata dict (`targeting_modes`, `sell_rect`) for click handling in `main.py`.

**Nested helper**
- `draw_path(path_index, key_text, level)`:
  - renders one path line with affordability coloring
  - handles `MAXED` state

---

## `maze.py`

### Purpose
Creates initial map lanes and supports dynamic lane expansion.

### Functions

#### `manhattan_distance(p1, p2)`
Simple utility returning `|x1-x2| + |y1-y2|`.

#### `create_maze()`
Builds initial `grid`, `spawn_points`, and center `goal`.

**Layout strategy**
- Border walls and interior build area.
- Carves 3 routes from three spawn points chosen from grid-relative coordinates so smaller/larger grids stay valid.
- Marks goal tile as path (`2`) so pathfinder can terminate there.

**Returns**
- `(grid, spawn_points, goal)`.

#### `expand_paths(grid, towers, spawn_points)`
Adds a new spawn lane by:
- selecting a random interior-edge tile
- finding nearest existing path tile (excluding spawn-adjacent tiles)
- carving Manhattan-style corridor to join network
- collecting towers that overlap newly carved tiles

**Returns**
- `(path_tiles, towers_to_remove, new_spawn)`
- if expansion fails: `([], [], None)`

### Constants
- `GOAL_GRID` is exported as center tile shortcut.

---

## `pathfinding.py`

### Purpose
A* implementation for enemy navigation on path tiles.

### Functions

#### `astar(grid, start, goal)`
Computes shortest route from `start` to `goal` using:
- 4-direction neighbors only
- Manhattan heuristic
- only traversable tiles where `grid[y][x] == 2`

**Internal helper**
- `heuristic(a, b)` nested function.

**Returns**
- list of tiles from start->goal (inclusive) or empty list if unreachable.

---

## `wave_templates.py`

### Purpose
Owns wave-phase composition, swarm burst sizing, and spawn-interval pacing.

### Functions
- `get_wave_template(wave)`: returns pool + swarm chance + boss flag.
- `choose_enemy_type(wave, enemies_alive, wave_enemies_left=None)`: chooses enemy type with swarm constraints.
- `get_spawn_interval(wave)`: returns per-wave spawn cadence for smoother difficulty ramp.

---

## `status_effects.py`

### Purpose
Unified status-effect model used by enemies.

### Class: `StatusEffect`
- fields: `type`, `duration`, `strength`
- helper behavior: ticking + active-state checks

---

## `spatial.py`

### Purpose
Spatial hash bucket helper used to speed up enemy lookup for targeting/AoE.

---

## `enemy.py`

### Purpose
Defines enemy entity model, movement, resist-based damage handling, and special AI behaviors for all enemy/boss types.

### Class: `Enemy`

#### `__init__(self, grid, spawn, goal, enemy_type, scale=1.0)`
Initializes:
- combat stats from `ENEMY_STATS` with optional scale factor
- per-type special state (dodge, shield, phases, cooldowns)
- pathing state and lane tracking
- status effect state (slow/freeze/burn/impale)

Calls `self.repath()` at end.

#### `repath(self)`
Runs `astar(...)` from current tile to goal and caches route.
Skips first node because it is current tile.

#### `grid_pos(self)`
Returns current tile coordinate from pixel position.

#### `logic(self, enemies, dt, towers=None, spawn_points=None, goal_grid=None)`
Main per-frame behavior:
1. Updates status effects (slow / frozen / impale / burn).
2. Applies health-threshold behaviors.
3. Applies boss/special behavior.
4. Repaths if needed.
5. Resolves freeze application and unfreeze/immunity behavior.
6. Moves toward current waypoint using `dt`-scaled movement.
7. Triggers healer chain-heal timer.

#### `take_damage(self, incoming_dmg, dmg_type, source='generic', resist_override=None)`
Unified damage intake:
- mage can block projectile hits
- assassin can dodge
- applies resist or override resist
- applies shield absorption first
- subtracts resulting HP

**Returns**
- `True` if hit landed, `False` if blocked/dodged.

#### `_apply_health_behaviors(self, enemies)`
Threshold-driven non-boss and phase transitions:
- fighter one-time shield
- assassin emergency teleport/buff
- tank bulwark resist boost
- minotaur phase 2 transition

#### `_apply_boss_behaviors(self, enemies, towers, spawn_points, goal_grid, dt)`
Boss active skills:
- minotaur periodic nearest-tower stun in radius
- demon phase 1 lane tower swap
- demon phase 2 summon minions at 50% HP
- demon phase 3 beneficial teleport at 25% HP

#### `_chain_heal_lane(self, enemies)`
Healer support skill:
- selects same-lane wounded allies
- sorts by lowest health ratio then distance
- heals up to 3 targets.

#### `_swap_lane_towers(self, towers, spawn_points)`
Demon utility:
- picks 2 lanes
- assigns towers to nearest lane center
- pairwise swaps positions between lanes
- updates `grid_pos` for objects that expose it

**Nested helpers**
- `lane_center(tile)`
- `nearest_lane(tower)`

#### `_spawn_demon_minions(self, enemies)`
Spawns 4 scaled minions at demon current tile.

#### `_teleport_to_beneficial_point(self, goal_grid)`
Finds forward path candidates that are closer in remaining path length but still not too near goal.
Teleports to one of later better candidates.

**Returns**
- `True` if teleported, otherwise `False`.

#### `add_slow(self, amount)`
Adds slow through the status-effect framework unless freeze immunity is active.

#### `draw(self, screen)`
Draws sprite or fallback circle, plus:
- freeze/slow clarity effects (outline, tint, particles/crack, meter)
- compact HP bar.

---

## `tower.py`

### Purpose
Implements tower logic, upgrades, targeting, projectile generation, and visual range indicator.

### Class: `Tower`

#### `__init__(self, pos, ttype)`
Initializes base type data:
- tower category (`physical`, `magic`, `ice`, `executioner`)
- base damage/range/color/name
- cooldown and size
- upgrade-path state and feature flags

#### `get_upgrade_info(self, path)`
Returns next upgrade tuple `(name, cost)` for chosen path.
If no upgrade available: `(None, 0)`.

#### `can_upgrade(self, path)`
Enforces two-tier and path-lock rule:
- can only level a path if opposite path is still 0.

#### `upgrade(self, path)`
Applies feature unlocks and stat changes for selected path.

**Returns**
- `True` if upgraded, `False` if invalid.

#### `in_range(self, enemy)`
Range check helper based on Euclidean distance.

#### `update(self, enemies, dt=1.0 / 60.0, spatial_index=None, projectile_pool=None)`
Main tower behavior:
- handles cooldown
- ice mode: manages persistent `IceLaser` links and AoE slow/freeze options
- magic pull mode applies continuous attraction
- magic AoE mode fires target selected by tower priority mode
- physical volley mode emits multi-projectile list
- default emits single projectile

Supports optional spatial query acceleration and projectile pooling.

**Returns**
- `None`, one projectile, or list of projectiles.

#### `draw(self, screen, selected=False)`
Draws tower sprite/fallback circle and optional translucent range circle when selected.

Ice sprite key typo was fixed to `tower_ice`.

---

## `traps.py`

### Purpose
Implements path-placed trap entities with continuous/triggered effects and branching upgrades.

### Class: `Trap`

#### `__init__(self, grid_pos, trap_type)`
Initializes trap tile placement, base stats from `TRAP_STATS`, and upgrade flags.

#### `get_upgrade_info(self, path)`
Returns next upgrade tuple `(name, cost)` for trap and path.

#### `can_upgrade(self, path)`
Path-lock validation (same rule as towers).

#### `upgrade(self, path)`
Applies upgrade effects:
- fire: aura size and burn spread (`Detonate` is currently a named tier without extra behavior logic)
- spikes: bleed, impale, cluster, quake

#### `_apply_damage(self, enemy, amount, dmg_type, source)`
Compatibility damage adapter:
- prefers `enemy.take_damage(...)`
- fallback to direct HP subtraction.

#### `_update_fire(self, enemies, dt)`
Continuous fire aura logic by Chebyshev tile distance from trap:
- center highest damage
- surrounding rings lower multipliers
- optional burn spread splash to nearby enemies.

#### `_update_spikes_trigger(self, enemies, affected)`
Triggered spike hit processing:
- direct spike damage to enemies on tile
- optional bleed/impale flags
- optional quake and cluster extra AoE effects

#### `update(self, enemies)`
Main trap tick:
- derives fixed dt via `1/FPS`
- fire trap applies continuous aura each frame
- spike trap accumulates timer and triggers on interval when occupied

#### `draw(self, screen)`
Draws trap sprite or fallback rectangle on tile.

---

## `projectiles.py`

### Purpose
Projectile and beam implementations used by towers.

### Class: `Projectile`

#### `__init__(self, start_pos, target_enemy, dmg, dmg_type, tower_type, tower=None)`
Initializes homing projectile state, speed, bounce/chain flags from source tower, and sprite.

#### `update(self, dt, enemies=None)`
Moves projectile toward target and resolves impact:
- on hit: damage via enemy damage model
- supports armor pierce override
- shatter bonus vs frozen targets
- optional chain hits and AoE splash
- optional bounce retargeting to nearby unhit enemies

**Returns**
- `True` while projectile remains active
- `False` when projectile should be removed.

#### `_chain_to_nearby(self, enemies, count)`
Applies reduced chain damage to nearby enemies and optionally spreads slow status.

#### `draw(self, screen)`
Draws rotated sprite toward travel angle or fallback circle.

### Class: `IceLaser`

#### `__init__(self, tower, target_enemy, freeze_delay=1.0)`
Initializes persistent beam lock from ice tower to target.

#### `update(self, dt, enemies=None)`
Maintains beam while target alive/in range:
- applies initial slow once
- after `freeze_delay`, applies heavy slow burst and resets timer
- immediately deactivates when beam is flagged inactive

**Returns**
- `True` if still active, else `False`.

#### `draw(self, screen)`
Draws beam line and endpoint glow marker.

---

## 4) Cross-Module Interaction Summary

- `main.py` calls `Enemy.logic(...)`, `Tower.update(...)`, `Trap.update(...)`, and projectile updates every frame.
- `Enemy.repath()` calls `pathfinding.astar(...)` against maze/path data.
- `drawing.py` is pure render layer (no state mutation except local UI rect outputs).
- `assets.py` is shared by drawing, enemies, towers, traps, and projectiles for sprite lookup.
- Balance is centralized in `constants.py`; behavior rules are distributed across entity modules.

---

## 5) Input, Economy, and Progression Reference

### Input map
- `1`: Archer tower, `2`: Magic tower, `3`: Ice tower
- `4`: Fire trap, `5`: Spike trap, `6`: Executioner tower
- mouse click: place/select
- `Q`, `E`: apply path upgrades to selected structure
- `C`: cycle game speed (`1x -> 2x -> 3x -> 1x`)
- tower menu click: set targeting mode for selected tower only
- tower menu click or `R`: sell selected structure
- `ESC`: pause/resume
- paused + `H`: open guide
- while guide is open: `1..7` switch pages, `UP/DOWN` (or wheel) scroll, `BACKSPACE` back/close
- paused + `O`: open settings
- victory/game-over screen: click `Play Again`, `Main Menu`, or `Exit`

### Main menu navigation
- `Start Game` -> wave selection -> modifier draft -> gameplay.
- `Guide` -> opens `menu_guide` state with the same page system (`1..7`) and scrolling controls.
- `Progression` -> shows level/XP and unlocked modifiers.
- `Settings` -> resolution + keybind tabs.

### Modifier system (run-affecting)
- Each run offers 3 random modifiers from unlocked pool; pick exactly 1.
- Chosen modifier persists for the full run and can alter economy/combat pacing.
- Modifier definitions live in `modifiers.py`; active effect bundle is produced by `compile_run_effects(...)`.

Current modifiers:
- Tier 1: Sharpened Arrows, Efficient Wiring, Cold Front, Prepared Defenses, Reinforced Triggers, Hotter Flames, Long Sightlines, Rapid Deployment, Focused Targeting, Efficient Salvage.
- Tier 2: Volatile Enemies, Glass Cannons, Greedy Markets.
- Tier 3: Overclocked Grid.

### Economy
- start money: `400`
- start lives: `25`
- kill reward: `int(enemy.reward * 1.5)`
- wave completion interest: tiered (`5%` up to 500, `3%` up to 1200, then `2%`), capped at `150`
- sell refund: default `70%` of (build cost + spent upgrades), adjustable by run modifiers

### Progression
- wave enemy count follows phased curve (early/mid/late)
- every 5 waves: lane expansion + boss final spawn
- every configured interval (default 5): phase-aware enemy scaling
- wave templates control composition, swarm probability, and spawn interval

---

## 6) Known Implementation Notes

- `main.py` keeps a deliberate single-loop/stateful orchestration style.
- Some trap feature flags are scaffolding for future expansion (e.g., revive flow behavior).
- Gameplay speed now affects simulation correctly for movement/updates using `dt`.

---

## 7) Suggested Next Documentation Additions

- Add a `CHANGELOG.md` for balance updates.
- Add a compact `API.md` if you want this README shortened for players.
- Add diagram(s) of update order and entity interaction.
