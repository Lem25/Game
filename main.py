import math
import random
import sys

import pygame

from colors import DARK_GRAY
from constants import FPS, GRID_H, GRID_W, HEIGHT, TILE, TOWER_COSTS, TRAP_COSTS, WIDTH
from drawing import (
    draw_boss_spawn_popup,
    draw_game_over,
    draw_grid,
    draw_pause,
    draw_settings_popup,
    draw_ui,
    draw_victory,
    draw_wave_selection_popup,
    draw_upgrade_ui,
    draw_guide,
)
from enemy import Enemy, invalidate_path_cache
from maze import create_maze, expand_paths
from tower import Tower
from traps import Trap
from projectiles import IceLaser, ProjectilePool
from spatial import SpatialHash
from wave_templates import choose_enemy_type, get_spawn_interval
from game_settings import RESOLUTION_OPTIONS, load_settings, save_settings
from keybind_utils import load_keybind_maps, pretty_key_name
from economy import calculate_interest, get_structure_sell_value
from spawn_scaling import apply_spawn_scaling
from viewport_utils import get_viewport_rect, present_frame, window_to_game_pos
from placement_rules import can_place_tower, can_place_trap
from wave_progression import get_wave_enemy_count

pygame.init()
game_settings = load_settings()
current_resolution = tuple(game_settings.get('resolution', [WIDTH, HEIGHT]))
window = pygame.display.set_mode(current_resolution, pygame.RESIZABLE)
screen = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Treasure Defense - Dynamic Random Paths!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)
debug_font = pygame.font.SysFont("arial", 12)
DEBUG_LANE_OVERLAY = True
SWARM_GROUP_SIZE = 4
SWARM_SPAWN_SPACING = 0.15


def apply_resolution(new_resolution):
    global window, current_resolution, game_settings
    current_resolution = (int(new_resolution[0]), int(new_resolution[1]))
    window = pygame.display.set_mode(current_resolution, pygame.RESIZABLE)
    game_settings['resolution'] = [current_resolution[0], current_resolution[1]]
    save_settings(game_settings)


def bind_action(action, key_code):
    previous_key_code = keybind_codes.get(action, key_code)

    conflicting_action = None
    for other_action, other_key_code in keybind_codes.items():
        if other_action != action and other_key_code == key_code:
            conflicting_action = other_action
            break

    if conflicting_action is not None:
        keybind_codes[conflicting_action] = previous_key_code
        keybind_names[conflicting_action] = pygame.key.name(previous_key_code)

    keybind_codes[action] = key_code
    keybind_names[action] = pygame.key.name(key_code)
    game_settings['keybinds'] = dict(keybind_names)
    save_settings(game_settings)

def get_wave_selection():
    input_text = ""
    selecting = True
    while selecting:
        clock.tick(FPS)
        screen.fill(DARK_GRAY)
        draw_wave_selection_popup(screen, font, input_text)
        present_frame(window, screen, WIDTH, HEIGHT)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text and input_text.isdigit() and int(input_text) > 0:
                        return int(input_text)
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit() and len(input_text) < 3:
                    input_text += event.unicode
    return 50

grid, spawn_points, GOAL_GRID = create_maze()
towers = []
enemies = []
traps = []
projectiles = []
money = 400
lives = 25
wave = 0
wave_enemies_left = 0
wave_timer = 0
placing_tower_type = 'physical'
selected_tower = None
boss_spawn_lane = None
enemy_scale = 1.0
target_wave = get_wave_selection()
boss_popup_counter = 0
paused = False
show_guide = False
guide_page = 'menu'
guide_scroll = 0
game_won = False
game_over = False
victory_play_again_rect = None
victory_exit_rect = None
game_over_play_again_rect = None
game_over_exit_rect = None
game_speed = 1
projectile_pool = ProjectilePool()
spatial_index = SpatialHash()
last_interest_wave = 0
targeting_mode_rects = {}
sell_button_rect = None
pending_spawns = []
spawn_clock = 0.0
wave_swarm_spawn_count = 0
show_settings = False
settings_option_rects = []
settings_tab_rects = []
settings_tab = 'resolution'
settings_action_rects = []
awaiting_keybind_action = None
settings_scroll = 0
settings_max_scroll = 0
viewport_rect = get_viewport_rect(window, WIDTH, HEIGHT)
keybind_names, keybind_codes = load_keybind_maps(game_settings)

def next_wave():
    global wave, wave_enemies_left, boss_spawn_lane, spawn_points
    global enemy_scale, boss_popup_counter, target_wave
    global pending_spawns, wave_swarm_spawn_count
    wave += 1

    wave_enemies_left = max(2, get_wave_enemy_count(wave, target_wave))
    
    if wave % 5 == 0:
        new_path_tiles, towers_to_remove, spawn_point = expand_paths(grid, towers, GOAL_GRID, spawn_points)
        invalidate_path_cache()
        for tower in towers_to_remove:
            if tower in towers:
                towers.remove(tower)
        
        if spawn_point and spawn_point not in spawn_points:
            spawn_points.append(spawn_point)
        boss_spawn_lane = random.choice(spawn_points)
    else:
        boss_spawn_lane = None
    
    boss_popup_counter = 0
    pending_spawns = []
    wave_swarm_spawn_count = 0

    try:
        from constants import ENEMY_SCALE_WAVE_INTERVAL, ENEMY_SCALE_INCREMENT
        if ENEMY_SCALE_WAVE_INTERVAL > 0 and wave % ENEMY_SCALE_WAVE_INTERVAL == 0:
            if wave <= 10:
                increment = max(0.04, ENEMY_SCALE_INCREMENT - 0.02)
            elif wave <= 15:
                increment = ENEMY_SCALE_INCREMENT
            else:
                increment = ENEMY_SCALE_INCREMENT + 0.02
            enemy_scale *= 1.0 + increment
    except Exception:
        pass


def reset_match_state(selected_target_wave=None):
    global grid, spawn_points, GOAL_GRID
    global towers, enemies, traps, projectiles
    global money, lives, wave, wave_enemies_left, wave_timer
    global placing_tower_type, selected_tower, boss_spawn_lane
    global enemy_scale, target_wave, boss_popup_counter
    global paused, show_guide, guide_page, guide_scroll
    global game_won, game_over, victory_play_again_rect, victory_exit_rect
    global game_over_play_again_rect, game_over_exit_rect
    global game_speed, projectile_pool, spatial_index, last_interest_wave
    global targeting_mode_rects, sell_button_rect
    global pending_spawns, spawn_clock
    global wave_swarm_spawn_count
    global show_settings, settings_option_rects, settings_tab_rects, settings_tab
    global settings_action_rects, awaiting_keybind_action, settings_scroll, settings_max_scroll

    grid, spawn_points, GOAL_GRID = create_maze()
    invalidate_path_cache()
    towers = []
    enemies = []
    traps = []
    projectiles = []

    money = 400
    lives = 25
    wave = 0
    wave_enemies_left = 0
    wave_timer = 0
    placing_tower_type = 'physical'
    selected_tower = None
    boss_spawn_lane = None
    enemy_scale = 1.0
    target_wave = selected_target_wave if selected_target_wave is not None else get_wave_selection()
    boss_popup_counter = 0
    paused = False
    show_guide = False
    guide_page = 'menu'
    guide_scroll = 0
    game_won = False
    game_over = False
    victory_play_again_rect = None
    victory_exit_rect = None
    game_over_play_again_rect = None
    game_over_exit_rect = None
    game_speed = 1
    projectile_pool = ProjectilePool()
    spatial_index = SpatialHash()
    last_interest_wave = 0
    targeting_mode_rects = {}
    sell_button_rect = None
    pending_spawns = []
    spawn_clock = 0.0
    wave_swarm_spawn_count = 0
    show_settings = False
    settings_option_rects = []
    settings_tab_rects = []
    settings_tab = 'resolution'
    settings_action_rects = []
    awaiting_keybind_action = None
    settings_scroll = 0
    settings_max_scroll = 0

    next_wave()


next_wave()
run = True
while run:
    raw_dt = clock.tick(FPS) / 1000.0
    dt = raw_dt * game_speed
    screen.fill(DARK_GRAY)
    draw_grid(screen, grid, GOAL_GRID)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.VIDEORESIZE:
            window = pygame.display.set_mode((max(640, event.w), max(480, event.h)), pygame.RESIZABLE)
            current_resolution = window.get_size()
            game_settings['resolution'] = [current_resolution[0], current_resolution[1]]
            save_settings(game_settings)
            viewport_rect = get_viewport_rect(window, WIDTH, HEIGHT)
        elif event.type == pygame.KEYDOWN:
            pause_key = keybind_codes.get('pause', pygame.K_ESCAPE)
            guide_key = keybind_codes.get('open_guide', pygame.K_h)
            settings_key = keybind_codes.get('open_settings', pygame.K_o)
            if paused and show_settings and awaiting_keybind_action:
                if event.key == pygame.K_ESCAPE:
                    awaiting_keybind_action = None
                else:
                    bind_action(awaiting_keybind_action, event.key)
                    awaiting_keybind_action = None
            elif event.key in (pause_key, pygame.K_ESCAPE):
                if paused and show_settings:
                    show_settings = False
                    settings_option_rects = []
                    settings_tab_rects = []
                    settings_action_rects = []
                    awaiting_keybind_action = None
                    settings_scroll = 0
                    settings_max_scroll = 0
                else:
                    paused = not paused
                    if not paused:
                        show_guide = False
                        show_settings = False
                        guide_page = 'menu'
                        guide_scroll = 0
                        awaiting_keybind_action = None
                        settings_scroll = 0
                        settings_max_scroll = 0
            elif paused and show_settings:
                if event.key == pygame.K_1:
                    settings_tab = 'resolution'
                    settings_scroll = 0
                elif event.key == pygame.K_2:
                    settings_tab = 'keybinds'
                    settings_scroll = 0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    settings_scroll = max(0, settings_scroll - 30)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    settings_scroll = min(settings_max_scroll, settings_scroll + 30)
                elif settings_tab == 'resolution':
                    for idx, res in enumerate(RESOLUTION_OPTIONS):
                        number_key = pygame.K_1 + idx
                        if event.key == number_key:
                            apply_resolution(res)
                            viewport_rect = get_viewport_rect(window, WIDTH, HEIGHT)
                            break
            elif paused and not show_guide:
                if event.key == guide_key:
                    show_guide = True
                    show_settings = False
                    guide_page = 'menu'
                    guide_scroll = 0
                elif event.key == settings_key:
                    show_settings = not show_settings
                    if show_settings:
                        show_guide = False
                        settings_tab = 'resolution'
                        awaiting_keybind_action = None
                        settings_scroll = 0
                        settings_max_scroll = 0
            elif paused and show_guide:
                if event.key == pygame.K_1:
                    guide_page = 'towers'
                    guide_scroll = 0
                elif event.key == pygame.K_2:
                    guide_page = 'traps'
                    guide_scroll = 0
                elif event.key == pygame.K_3:
                    guide_page = 'enemies'
                    guide_scroll = 0
                elif event.key == pygame.K_4:
                    guide_page = 'mechanics'
                    guide_scroll = 0
                elif event.key == pygame.K_5:
                    guide_page = 'strategy'
                    guide_scroll = 0
                elif event.key == pygame.K_6:
                    guide_page = 'keybinds'
                    guide_scroll = 0
                elif event.key == pygame.K_BACKSPACE:
                    if guide_page != 'menu':
                        guide_page = 'menu'
                        guide_scroll = 0
                    else:
                        show_guide = False
                        guide_scroll = 0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    guide_scroll = max(0, guide_scroll - 40)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    guide_scroll += 40
            elif not paused:
                if event.key == keybind_codes.get('build_physical', pygame.K_1):
                    placing_tower_type = 'physical'
                elif event.key == keybind_codes.get('build_magic', pygame.K_2):
                    placing_tower_type = 'magic'
                elif event.key == keybind_codes.get('build_ice', pygame.K_3):
                    placing_tower_type = 'ice'
                elif event.key == keybind_codes.get('build_executioner', pygame.K_6):
                    placing_tower_type = 'executioner'
                elif event.key == keybind_codes.get('build_fire', pygame.K_4):
                    placing_tower_type = 'fire'
                elif event.key == keybind_codes.get('build_spikes', pygame.K_5):
                    placing_tower_type = 'spikes'
                elif event.key == keybind_codes.get('cycle_speed', pygame.K_c):
                    game_speed = 1 if game_speed >= 3 else game_speed + 1
                elif event.key == keybind_codes.get('upgrade_path1', pygame.K_q):
                    if selected_tower:
                        upgrade_name, upgrade_cost = selected_tower.get_upgrade_info(1)
                        if upgrade_name and money >= upgrade_cost and selected_tower.can_upgrade(1):
                            if selected_tower.upgrade(1):
                                money -= upgrade_cost
                                selected_tower.upgrade_spent = getattr(selected_tower, 'upgrade_spent', 0) + upgrade_cost
                elif event.key == keybind_codes.get('upgrade_path2', pygame.K_e):
                    if selected_tower:
                        upgrade_name, upgrade_cost = selected_tower.get_upgrade_info(2)
                        if upgrade_name and money >= upgrade_cost and selected_tower.can_upgrade(2):
                            if selected_tower.upgrade(2):
                                money -= upgrade_cost
                                selected_tower.upgrade_spent = getattr(selected_tower, 'upgrade_spent', 0) + upgrade_cost
                elif event.key == keybind_codes.get('sell_structure', pygame.K_r):
                    if selected_tower:
                        money += get_structure_sell_value(selected_tower)
                        if selected_tower in towers:
                            towers.remove(selected_tower)
                        elif selected_tower in traps:
                            traps.remove(selected_tower)
                        selected_tower = None
                        targeting_mode_rects = {}
                        sell_button_rect = None
        elif event.type == pygame.MOUSEBUTTONDOWN:
            logical_pos = window_to_game_pos(event.pos, viewport_rect, WIDTH, HEIGHT)
            if logical_pos is None:
                continue
            mx, my = logical_pos
            gx, gy = mx // TILE, my // TILE
            if game_over:
                if game_over_play_again_rect and game_over_play_again_rect.collidepoint(mx, my):
                    reset_match_state()
                elif game_over_exit_rect and game_over_exit_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()
                continue
            if game_won:
                if victory_play_again_rect and victory_play_again_rect.collidepoint(mx, my):
                    reset_match_state()
                elif victory_exit_rect and victory_exit_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()
                continue

            if selected_tower and targeting_mode_rects and hasattr(selected_tower, 'targeting_mode'):
                for mode, rect in targeting_mode_rects.items():
                    if rect.collidepoint(mx, my):
                        selected_tower.targeting_mode = mode
                        break
                if any(rect.collidepoint(mx, my) for rect in targeting_mode_rects.values()):
                    continue

            if selected_tower and sell_button_rect and sell_button_rect.collidepoint(mx, my):
                money += get_structure_sell_value(selected_tower)
                if selected_tower in towers:
                    towers.remove(selected_tower)
                elif selected_tower in traps:
                    traps.remove(selected_tower)
                selected_tower = None
                targeting_mode_rects = {}
                sell_button_rect = None
                continue

            if paused:
                if show_settings:
                    for tab_rect, tab_key in settings_tab_rects:
                        if tab_rect.collidepoint(mx, my):
                            settings_tab = tab_key
                            awaiting_keybind_action = None
                            settings_scroll = 0
                            break
                    for option_rect, option_resolution in settings_option_rects:
                        if settings_tab == 'resolution' and option_rect.collidepoint(mx, my):
                            apply_resolution(option_resolution)
                            viewport_rect = get_viewport_rect(window, WIDTH, HEIGHT)
                            awaiting_keybind_action = None
                            break
                    for action_rect, action_name in settings_action_rects:
                        if settings_tab == 'keybinds' and action_rect.collidepoint(mx, my):
                            awaiting_keybind_action = action_name
                            break
                continue
          
            structure_placed = False

            if not game_won and placing_tower_type in ['physical', 'magic', 'ice', 'executioner'] and can_place_tower(grid, gx, gy, towers, TILE, GRID_W, GRID_H):
                cost = TOWER_COSTS[placing_tower_type]
                if money >= cost:
                    tower_pos = pygame.Vector2(gx * TILE + TILE // 2, gy * TILE + TILE // 2)
                    tower = Tower(tower_pos, placing_tower_type)
                    tower.upgrade_spent = 0
                    tower.build_cost = cost
                    towers.append(tower)
                    money -= cost
                    structure_placed = True
            elif not game_won and placing_tower_type in ['fire', 'spikes']:
                if can_place_trap(grid, gx, gy, towers, traps, GRID_W, GRID_H, TILE):
                    cost = TRAP_COSTS.get(placing_tower_type, 0)
                    if money >= cost:
                        trap = Trap((gx, gy), placing_tower_type)
                        trap.upgrade_spent = 0
                        trap.build_cost = cost
                        traps.append(trap)
                        money -= cost
                        structure_placed = True

            if structure_placed:
                selected_tower = None
                placing_tower_type = 'none'
                targeting_mode_rects = {}
                sell_button_rect = None
                continue
           
            selected_tower = None
            for t in towers:
                if math.hypot(t.pos.x - mx, t.pos.y - my) < t.size * 1.2:
                    selected_tower = t
                    break
            if not selected_tower:
                for tr in traps:
                    if math.hypot(tr.pos.x - mx, tr.pos.y - my) < TILE:
                        selected_tower = tr
                        break
        elif event.type == pygame.MOUSEWHEEL:
            if paused and show_guide and guide_page != 'menu':
                guide_scroll = max(0, guide_scroll - event.y * 30)
            elif paused and show_settings:
                settings_scroll = max(0, min(settings_max_scroll, settings_scroll - event.y * 30))

    if paused:
        for t in towers:
            t.draw(screen, selected_tower == t)
        
        for p in projectiles:
            p.draw(screen)
        
        for tr in traps:
            tr.draw(screen)
        
        for e in enemies:
            e.draw(screen)
        
        combined_costs = {**TOWER_COSTS, **TRAP_COSTS}
        draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=combined_costs, game_speed=game_speed, selected_structure=selected_tower)
        
        if show_guide:
            max_scroll = draw_guide(screen, font, guide_page, guide_scroll)
            if guide_scroll > max_scroll:
                guide_scroll = max_scroll
            settings_option_rects = []
            settings_tab_rects = []
            settings_action_rects = []
            settings_scroll = 0
            settings_max_scroll = 0
        elif show_settings:
            keybind_display = {action: pretty_key_name(code) for action, code in keybind_codes.items()}
            settings_panel = draw_settings_popup(
                screen,
                font,
                current_resolution,
                RESOLUTION_OPTIONS,
                settings_tab=settings_tab,
                keybind_display=keybind_display,
                waiting_action=awaiting_keybind_action,
                scroll_offset=settings_scroll,
            )
            settings_tab_rects = settings_panel.get('tabs', [])
            settings_option_rects = settings_panel.get('options', [])
            settings_action_rects = settings_panel.get('actions', [])
            settings_max_scroll = settings_panel.get('max_scroll', 0)
            if settings_scroll > settings_max_scroll:
                settings_scroll = settings_max_scroll
        else:
            draw_pause(
                screen,
                font,
                guide_key=pretty_key_name(keybind_codes.get('open_guide', pygame.K_h)),
                settings_key=pretty_key_name(keybind_codes.get('open_settings', pygame.K_o)),
            )
            settings_option_rects = []
            settings_tab_rects = []
            settings_action_rects = []
            settings_scroll = 0
            settings_max_scroll = 0
        
        if selected_tower and not show_guide and not show_settings:
            panel_info = draw_upgrade_ui(screen, font, selected_tower, money)
            targeting_mode_rects = panel_info.get('targeting_modes', {})
            sell_button_rect = panel_info.get('sell_rect')
        else:
            targeting_mode_rects = {}
            sell_button_rect = None
        viewport_rect = present_frame(window, screen, WIDTH, HEIGHT)
        continue

    if wave_enemies_left == 0 and len(enemies) == 0 and not game_won and not pending_spawns:
        if wave > 0 and last_interest_wave != wave:
            interest = calculate_interest(money)
            money += interest
            last_interest_wave = wave

        if wave < target_wave:
            next_wave()
        elif wave == target_wave:
            game_won = True
    
    if game_over:
        for t in towers:
            t.draw(screen, selected_tower == t)

        for p in projectiles:
            p.draw(screen)

        for tr in traps:
            tr.draw(screen)

        for e in enemies:
            e.draw(screen)

        game_over_play_again_rect, game_over_exit_rect = draw_game_over(screen, font)
        viewport_rect = present_frame(window, screen, WIDTH, HEIGHT)
        continue

    if game_won:
        for t in towers:
            t.draw(screen, selected_tower == t)
        
        for p in projectiles:
            p.draw(screen)
        
        for tr in traps:
            tr.draw(screen)
        
        for e in enemies:
            e.draw(screen)
        
        victory_play_again_rect, victory_exit_rect = draw_victory(screen, font)
        viewport_rect = present_frame(window, screen, WIDTH, HEIGHT)
        continue

    if not paused:
        spawn_clock += dt

        if pending_spawns:
            ready_spawns = [entry for entry in pending_spawns if entry['spawn_time'] <= spawn_clock]
            if ready_spawns:
                pending_spawns = [entry for entry in pending_spawns if entry['spawn_time'] > spawn_clock]
                for entry in ready_spawns:
                    spawn_tile = entry['spawn_point'] if entry['spawn_point'] in spawn_points else random.choice(spawn_points)
                    enemy = Enemy(grid, spawn_tile, GOAL_GRID, entry['enemy_type'], scale=enemy_scale)
                    if entry['enemy_type'] == 'swarm':
                        offset_x = random.uniform(-4.0, 4.0)
                        offset_y = random.uniform(-4.0, 4.0)
                        enemy.pos.x += offset_x
                        enemy.pos.y += offset_y
                        wave_swarm_spawn_count += 1
                        apply_spawn_scaling(enemy, wave, swarm_spawn_index=wave_swarm_spawn_count)
                    else:
                        apply_spawn_scaling(enemy, wave)
                    enemies.append(enemy)

        spawn_interval = get_spawn_interval(wave)
        wave_timer += dt
        if wave_enemies_left > 0 and wave_timer >= spawn_interval:
            if wave_enemies_left == 1 and wave % 5 == 0:
                etype = 'demon_boss' if wave % 10 == 0 else 'minotaur_boss'
                spawn = boss_spawn_lane
                boss_popup_counter = 60
            else:
                regular_budget = wave_enemies_left - 1 if wave % 5 == 0 else wave_enemies_left
                etype = choose_enemy_type(wave, enemies, wave_enemies_left=regular_budget)
                spawn = random.choice(spawn_points)

            if etype == 'swarm':
                burst_budget = wave_enemies_left - 1 if wave % 5 == 0 else wave_enemies_left
                burst_count = max(0, min(SWARM_GROUP_SIZE, burst_budget))
                if burst_count > 0:
                    for i in range(burst_count):
                        pending_spawns.append({
                            'enemy_type': 'swarm',
                            'spawn_point': spawn,
                            'spawn_time': spawn_clock + (i * SWARM_SPAWN_SPACING),
                        })
                    wave_enemies_left -= burst_count
            else:
                enemy = Enemy(grid, spawn, GOAL_GRID, etype, scale=enemy_scale)
                apply_spawn_scaling(enemy, wave)
                enemies.append(enemy)
                wave_enemies_left -= 1
            wave_timer = 0
        
        for e in enemies:
            e.logic(enemies, dt, towers=towers, spawn_points=spawn_points, goal_grid=GOAL_GRID)

        spatial_index.rebuild(enemies)

        for t in towers:
            if getattr(t, 'stun_timer', 0.0) > 0:
                t.stun_timer = max(0.0, t.stun_timer - dt)
                continue
            projectile = t.update(enemies, dt=dt, spatial_index=spatial_index, projectile_pool=projectile_pool)
            if projectile:
                if isinstance(projectile, list):
                    projectiles.extend(projectile)
                else:
                    projectiles.append(projectile)
        
        projectiles_to_remove = []
        for p in projectiles:
            if not p.update(dt, enemies):
                projectiles_to_remove.append(p)
        for p in projectiles_to_remove:
            projectiles.remove(p)
            if not isinstance(p, IceLaser):
                projectile_pool.release(p)

        for tr in traps:
            tr.update(enemies, dt)

        to_remove = []
        for e in enemies:
            if e.grid_pos() == GOAL_GRID:
                lives -= 1
                e.hp = 0
                to_remove.append(e)
            elif e.hp <= 0:
                money += int(e.reward * 1.5)
                to_remove.append(e)
        for e in to_remove:
            if e in enemies:
                enemies.remove(e)

        if lives <= 0:
            game_over = True
            game_won = False
            paused = False
            show_guide = False
            show_settings = False
            awaiting_keybind_action = None


    for t in towers:
        t.draw(screen, selected_tower == t)
    
    for p in projectiles:
        p.draw(screen)
    
    for tr in traps:
        tr.draw(screen)
    
    for e in enemies:
        e.draw(screen)

    if DEBUG_LANE_OVERLAY:
        lane_text = debug_font.render(f"Lanes: {len(spawn_points)}", True, (220, 245, 255))
        lane_bg = pygame.Surface((lane_text.get_width() + 10, lane_text.get_height() + 6), pygame.SRCALPHA)
        pygame.draw.rect(lane_bg, (10, 20, 35, 180), (0, 0, lane_bg.get_width(), lane_bg.get_height()), border_radius=4)
        screen.blit(lane_bg, (10, 10))
        screen.blit(lane_text, (15, 13))
    
    if boss_popup_counter > 0:
        boss_type = 'minotaur_boss' if wave % 10 != 0 else 'demon_boss'
        draw_boss_spawn_popup(screen, font, boss_type)
        boss_popup_counter -= 1
    
    combined_costs = {**TOWER_COSTS, **TRAP_COSTS}
    draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=combined_costs, game_speed=game_speed, selected_structure=selected_tower)
    
    if selected_tower:
        panel_info = draw_upgrade_ui(screen, font, selected_tower, money)
        targeting_mode_rects = panel_info.get('targeting_modes', {})
        sell_button_rect = panel_info.get('sell_rect')
    else:
        targeting_mode_rects = {}
        sell_button_rect = None

    viewport_rect = present_frame(window, screen, WIDTH, HEIGHT)

pygame.quit()
sys.exit()
