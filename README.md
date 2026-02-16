# Maze Treasure Defense — Full Technical Documentation

This document explains the entire project in depth: architecture, runtime flow, each module, and every function/method.

> **Last Updated:** February 2026  
> Includes wave templates, swarm burst groups, per-tower targeting UI, sell-in-panel economy flow, speed cycling, unified status effects, and late-wave performance helpers.

---

## 1) Project Overview

`Maze Treasure Defense` is a single-process, real-time tower defense game built with **Python** and **Pygame**.

Core idea:
- Enemies spawn from lane start points.
- They pathfind to a central goal tile.
- Player places towers, traps, and sentinels to stop them.
- Every 5 waves, the map may expand with a new lane.

Primary game loop and orchestration live in `main.py`; everything else is modularized by domain (rendering, enemies, towers, traps, pathfinding, assets, constants).

---

## 2) Runtime Architecture and Data Flow

### Startup flow
1. `pygame.init()` and window creation.
2. Constants and drawing/game systems imported.
3. `create_maze()` builds the grid, spawn points, and goal.
4. Initial state variables are initialized (money, lives, wave, etc.).
5. `get_wave_selection()` captures target wave from user input popup.
6. `next_wave()` starts wave 1.

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
Game entrypoint. Owns global game state, loop timing, input handling, spawn logic, and win/loss progression.

### Functions

#### `get_wave_selection()`
**What it does**
- Runs a temporary input loop before the game starts.
- Displays `draw_wave_selection_popup(...)` and accepts numeric keyboard input.
- Returns a positive integer wave target once Enter is pressed.

**Details**
- Backspace deletes digits.
- Input capped to 3 digits.
- If the window closes, game exits immediately.

#### Wave template integration
**What it does**
- Uses `wave_templates.py` to choose enemy types by wave phase.

**Details**
- Swarm events spawn in grouped bursts (10–15).
- Enemy composition ramps by early/mid/late template pools.
- Bosses still spawn every 5th wave as final wave enemy.

#### `can_place_tower(grid, gx, gy, towers)`
**What it does**
- Validates whether a tower/sentinel can be placed at tile `(gx, gy)`.

**Rules**
- Tile must be inside grid bounds.
- Tile must be buildable (`grid[y][x] == 0`).
- No existing tower may occupy within roughly 1 tile radius of target center.

#### `can_place_trap(grid, gx, gy, towers, traps)`
**What it does**
- Validates trap placement at tile `(gx, gy)`.

**Rules**
- Tile must be inside bounds.
- Tile must be path (`grid[y][x] == 2`).
- Cannot overlap a tower.
- Cannot overlap an existing trap.

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
- Updates entities in deterministic order:
  1. enemies logic
  2. towers (and sentinel) update
  3. projectile update/cleanup
  4. traps update
  5. enemy resolution (goal reached/dead)
- Draw order:
  grid -> towers -> projectiles -> traps -> enemies -> overlays/UI.

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
  - `TOWER_COSTS`, `TRAP_COSTS`, `SENTINEL_COST`
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
Renders full-screen defeat state and two clickable text-button rects.

**Returns**
- `(play_again_rect, exit_rect)` for click handling in `main.py`.

#### `draw_boss_spawn_popup(screen, font, boss_type)`
Draws red center popup indicating boss spawn.

#### `draw_wave_selection_popup(screen, font, input_text)`
Renders startup modal for target wave numeric input.

#### `draw_pause(screen, font)`
Renders pause overlay, resume hint, and guide hint.

#### `draw_victory(screen, font)`
Renders full-screen victory state and two clickable text-button rects.

**Returns**
- `(play_again_rect, exit_rect)` for click handling in `main.py`.

#### `draw_guide(screen, font, page, scroll_offset=0)`
Draws in-game documentation overlay:
- page menu and per-page content
- custom tab strip
- clipped scrollable content area
- scrollbar with thumb
- contextual nav footer hints

**Returns**
- `max_scroll` for caller-side clamping.

#### `draw_upgrade_ui(screen, font, selected_structure, money)`
Draws floating panel near selected tower/trap/sentinel with:
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

#### `expand_paths(grid, towers, goal, spawn_points)`
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
- `get_swarm_size()`: returns swarm burst size in `[10, 15]`.
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
Implements all non-sentinel tower logic, upgrades, targeting, projectile generation, and visual range indicator.

### Class: `Tower`

#### `__init__(self, pos, ttype)`
Initializes base type data:
- tower category (`physical`, `magic`, `ice`)
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
Path-lock validation (same rule as towers/sentinel).

#### `upgrade(self, path)`
Applies upgrade effects:
- fire: aura size, burn spread, explode on kill, revive flag
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

#### `_update_spikes_bleed(self, enemies, dt)`
Maintains bleed DoT on tracked enemy IDs.
Auto-cleans dead/missing targets.

#### `_update_spikes_trigger(self, enemies, affected)`
Triggered spike hit processing:
- direct spike damage to enemies on tile
- optional bleed/impale flags
- optional explosion on kill (if enabled)
- optional quake and cluster extra AoE effects

#### `update(self, enemies)`
Main trap tick:
- derives fixed dt via `1/FPS`
- fire trap applies continuous aura each frame
- spike trap accumulates timer and triggers on interval when occupied

#### `draw(self, screen)`
Draws trap sprite or fallback rectangle on tile.

---

## `sentinel.py`

### Purpose
Defines a support tower that creates temporary barriers and utility control effects.

### Class: `Sentinel`

#### `__init__(self, pos)`
Initializes tile anchor, barrier duration/cooldown/range, and upgrade flags.

**Current baseline**
- barrier duration: `6.0s`
- barrier cooldown: `10.0s`

#### `get_upgrade_info(self, path)`
Returns next sentinel upgrade tuple `(name, cost)`.

#### `can_upgrade(self, path)`
Path-lock validation.

#### `upgrade(self, path)`
Applies sentinel path effects:
- Path 1: longer barrier/range, then reflect DoT (`15 DPS`, magic)
- Path 2: pulse knockback enable, then overload AoE on barrier expiry (`150` damage)

#### `_apply_damage(self, enemy, amount, dmg_type)`
Damage adapter (`take_damage` preferred).

#### `_deactivate_barrier(self)`
Turns barrier off and starts cooldown.

#### `_handle_barrier_expire(self, enemies)`
Runs overload AoE on expiry (if enabled), then deactivates.

#### `_handle_barrier_block(self, enemies, dt)`
If enemies occupy sentinel tile:
- pushes them backward along radial direction
- applies strong slow each tick via enemy slow system (`add_slow(2.5)`)
- applies reflect DoT when unlocked.

#### `_handle_pulse(self, enemies)`
On pulse interval, knockbacks nearby enemies in radius.

#### `_try_activate_barrier(self, enemies)`
If not on cooldown, activates barrier when enemy enters range.

#### `update(self, enemies, dt)`
Main sentinel state machine:
- cooldown decay
- active barrier timing and behavior
- activation checks while idle

#### `draw(self, screen, selected=False)`
Renders sentinel body, optional range, active barrier tile overlay, pulse ring, and timer/cooldown labels.

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

- `main.py` calls `Enemy.logic(...)`, `Tower.update(...)`, `Sentinel.update(...)`, `Trap.update(...)`, and projectile updates every frame.
- `Enemy.repath()` calls `pathfinding.astar(...)` against maze/path data.
- `drawing.py` is pure render layer (no state mutation except local UI rect outputs).
- `assets.py` is shared by drawing, enemies, towers, traps, and projectiles for sprite lookup.
- Balance is centralized in `constants.py`; behavior rules are distributed across entity modules.

---

## 5) Input, Economy, and Progression Reference

### Input map
- `1..6`: choose build type
- mouse click: place/select
- `Q`, `E`: apply path upgrades to selected structure
- `C`: cycle game speed (`1x -> 2x -> 3x -> 1x`)
- tower menu click: set targeting mode for selected tower only
- tower menu click or `R`: sell selected structure
- `ESC`: pause/resume
- paused + `H`: open guide
- paused + `O`: open settings
- victory/game-over screen: click `Play Again` or `Exit`

### Economy
- start money: `400`
- start lives: `25`
- kill reward: `int(enemy.reward * 1.5)`
- wave completion interest: `5%` of current gold, capped at `200`
- sell refund: `75%` of (build cost + spent upgrades)

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
