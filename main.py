import math
import random
import sys

import pygame

from colors import DARK_GRAY
from constants import ENEMY_STATS, FPS, GRID_H, GRID_W, HEIGHT, TILE, TOWER_COSTS, TRAP_COSTS, WIDTH, SENTINEL_COST
from drawing import (
    draw_boss_spawn_popup,
    draw_game_over,
    draw_grid,
    draw_pause,
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
from sentinel import Sentinel
from projectiles import IceLaser, ProjectilePool
from spatial import SpatialHash
from wave_templates import choose_enemy_type, get_swarm_size, get_spawn_interval

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Treasure Defense - Dynamic Random Paths!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)

def get_wave_selection():
    input_text = ""
    selecting = True
    while selecting:
        clock.tick(FPS)
        screen.fill(DARK_GRAY)
        draw_wave_selection_popup(screen, font, input_text)
        pygame.display.flip()
        
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

def can_place_tower(grid, gx, gy, towers):
    if not (0 <= gx < GRID_W and 0 <= gy < GRID_H):
        return False
    
    if grid[gy][gx] != 0:
        return False
    
    tower_exists = any(math.hypot(t.pos.x - (gx * TILE + TILE // 2), 
                                  t.pos.y - (gy * TILE + TILE // 2)) < TILE for t in towers)
    return not tower_exists


def can_place_trap(grid, gx, gy, towers, traps):
    if not (0 <= gx < GRID_W and 0 <= gy < GRID_H):
        return False
    if grid[gy][gx] != 2:
        return False
    for tower in towers:
        if int(tower.pos.x // TILE) == gx and int(tower.pos.y // TILE) == gy:
            return False
    for trap in traps:
        if trap.grid_pos == (gx, gy):
            return False
    return True


def get_structure_build_cost(structure):
    if hasattr(structure, 'build_cost') and structure.build_cost:
        return structure.build_cost
    if hasattr(structure, 'type') and structure.type in TOWER_COSTS:
        return TOWER_COSTS[structure.type]
    if hasattr(structure, 'trap_type'):
        return TRAP_COSTS.get(structure.trap_type, 0)
    if isinstance(structure, Sentinel):
        return SENTINEL_COST
    return 0

def get_structure_sell_value(structure):
    build_cost = get_structure_build_cost(structure)
    upgrade_spent = getattr(structure, 'upgrade_spent', 0)
    return int((build_cost + upgrade_spent) * 0.75)


def get_wave_enemy_count(wave, target_wave):
    effective_wave = min(wave, target_wave)

    if effective_wave <= 5:
        return 4 + effective_wave
    if effective_wave <= 14:
        return 9 + int((effective_wave - 5) * 1.5)
    return 22 + int((effective_wave - 14) * 2.0)


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
victory_play_again_rect = None
victory_exit_rect = None
game_speed = 1
projectile_pool = ProjectilePool()
spatial_index = SpatialHash()
last_interest_wave = 0
targeting_mode_rects = {}
sell_button_rect = None

def next_wave():
    global wave, wave_enemies_left, boss_spawn_lane, spawn_points
    global enemy_scale, boss_popup_counter, target_wave
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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
                if not paused:
                    show_guide = False
                    guide_page = 'menu'
                    guide_scroll = 0
            elif paused and not show_guide:
                if event.key == pygame.K_h:
                    show_guide = True
                    guide_page = 'menu'
                    guide_scroll = 0
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
                if event.key == pygame.K_1:
                    placing_tower_type = 'physical'
                elif event.key == pygame.K_2:
                    placing_tower_type = 'magic'
                elif event.key == pygame.K_3:
                    placing_tower_type = 'ice'
                elif event.key == pygame.K_4:
                    placing_tower_type = 'fire'
                elif event.key == pygame.K_5:
                    placing_tower_type = 'spikes'
                elif event.key == pygame.K_6:
                    placing_tower_type = 'sentinel'
                elif event.key == pygame.K_c:
                    game_speed = 1 if game_speed >= 3 else game_speed + 1
                elif event.key == pygame.K_q:
                    if selected_tower:
                        upgrade_name, upgrade_cost = selected_tower.get_upgrade_info(1)
                        if upgrade_name and money >= upgrade_cost and selected_tower.can_upgrade(1):
                            if selected_tower.upgrade(1):
                                money -= upgrade_cost
                                selected_tower.upgrade_spent = getattr(selected_tower, 'upgrade_spent', 0) + upgrade_cost
                elif event.key == pygame.K_e:
                    if selected_tower:
                        upgrade_name, upgrade_cost = selected_tower.get_upgrade_info(2)
                        if upgrade_name and money >= upgrade_cost and selected_tower.can_upgrade(2):
                            if selected_tower.upgrade(2):
                                money -= upgrade_cost
                                selected_tower.upgrade_spent = getattr(selected_tower, 'upgrade_spent', 0) + upgrade_cost
                elif event.key == pygame.K_r:
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
            mx, my = pygame.mouse.get_pos()
            gx, gy = mx // TILE, my // TILE
            if game_won:
                if victory_play_again_rect and victory_play_again_rect.collidepoint(mx, my):
                    run = False
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
                continue
          
            structure_placed = False

            if not game_won and placing_tower_type in ['physical', 'magic', 'ice'] and can_place_tower(grid, gx, gy, towers):
                cost = TOWER_COSTS[placing_tower_type]
                if money >= cost:
                    tower_pos = pygame.Vector2(gx * TILE + TILE // 2, gy * TILE + TILE // 2)
                    tower = Tower(tower_pos, placing_tower_type)
                    tower.upgrade_spent = 0
                    tower.build_cost = cost
                    towers.append(tower)
                    money -= cost
                    structure_placed = True
            elif not game_won and placing_tower_type == 'sentinel' and can_place_tower(grid, gx, gy, towers):
                if money >= SENTINEL_COST:
                    tower_pos = pygame.Vector2(gx * TILE + TILE // 2, gy * TILE + TILE // 2)
                    sentinel = Sentinel(tower_pos)
                    sentinel.upgrade_spent = 0
                    sentinel.build_cost = SENTINEL_COST
                    towers.append(sentinel)
                    money -= SENTINEL_COST
                    structure_placed = True
            elif not game_won and placing_tower_type in ['fire', 'spikes']:
                if can_place_trap(grid, gx, gy, towers, traps):
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

    if paused:
        for t in towers:
            t.draw(screen, selected_tower == t)
        
        for p in projectiles:
            p.draw(screen)
        
        for tr in traps:
            tr.draw(screen)
        
        for e in enemies:
            e.draw(screen)
        
        combined_costs = {**TOWER_COSTS, **TRAP_COSTS, 'sentinel': SENTINEL_COST}
        draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=combined_costs, game_speed=game_speed, selected_structure=selected_tower)
        
        if show_guide:
            max_scroll = draw_guide(screen, font, guide_page, guide_scroll)
            if guide_scroll > max_scroll:
                guide_scroll = max_scroll
        else:
            draw_pause(screen, font)
        
        if selected_tower and not show_guide:
            panel_info = draw_upgrade_ui(screen, font, selected_tower, money)
            targeting_mode_rects = panel_info.get('targeting_modes', {})
            sell_button_rect = panel_info.get('sell_rect')
        else:
            targeting_mode_rects = {}
            sell_button_rect = None
        pygame.display.flip()
        continue

    if wave_enemies_left == 0 and len(enemies) == 0 and not game_won:
        if wave > 0 and last_interest_wave != wave:
            interest = min(200, int(money * 0.05))
            money += interest
            last_interest_wave = wave

        if wave < target_wave:
            next_wave()
        elif wave == target_wave:
            game_won = True
    
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
        pygame.display.flip()
        continue

    if not paused:
        spawn_interval = get_spawn_interval(wave)
        wave_timer += dt
        if wave_enemies_left > 0 and wave_timer >= spawn_interval:
            if wave_enemies_left == 1 and wave % 5 == 0:
                etype = 'demon_boss' if wave % 10 == 0 else 'minotaur_boss'
                spawn = boss_spawn_lane
                boss_popup_counter = 60
            else:
                etype = choose_enemy_type(wave, enemies, wave_enemies_left=wave_enemies_left)
                spawn = random.choice(spawn_points)

            if etype == 'swarm' and wave_enemies_left >= 10:
                swarm_count = min(wave_enemies_left, get_swarm_size())
                for _ in range(swarm_count):
                    enemies.append(Enemy(grid, spawn, GOAL_GRID, etype, scale=enemy_scale))
                wave_enemies_left -= swarm_count
            else:
                enemies.append(Enemy(grid, spawn, GOAL_GRID, etype, scale=enemy_scale))
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


    for t in towers:
        t.draw(screen, selected_tower == t)
    
    for p in projectiles:
        p.draw(screen)
    
    for tr in traps:
        tr.draw(screen)
    
    for e in enemies:
        e.draw(screen)
    
    if boss_popup_counter > 0:
        boss_type = 'minotaur_boss' if wave % 10 != 0 else 'demon_boss'
        draw_boss_spawn_popup(screen, font, boss_type)
        boss_popup_counter -= 1
    
    combined_costs = {**TOWER_COSTS, **TRAP_COSTS, 'sentinel': SENTINEL_COST}
    draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=combined_costs, game_speed=game_speed, selected_structure=selected_tower)
    
    if selected_tower:
        panel_info = draw_upgrade_ui(screen, font, selected_tower, money)
        targeting_mode_rects = panel_info.get('targeting_modes', {})
        sell_button_rect = panel_info.get('sell_rect')
    else:
        targeting_mode_rects = {}
        sell_button_rect = None

    if lives <= 0:
        draw_game_over(screen, font)

    pygame.display.flip()

pygame.quit()
sys.exit()
