import math
import random
import sys

import pygame

from colors import DARK_GRAY
from constants import ENEMY_STATS, FPS, GRID_H, GRID_W, HEIGHT, TILE, TOWER_COSTS, TRAP_COSTS, WIDTH
from drawing import (
    draw_boss_spawn_popup,
    draw_game_over,
    draw_grid,
    draw_pause,
    draw_ui,
    draw_victory,
    draw_wave_selection_popup,
)
from enemy import Enemy
from maze import create_maze, expand_paths
from tower import Tower
from traps import Trap

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

def get_enemy_type_for_wave(wave):
    pools = [
        ['fighter'],
        ['fighter', 'fighter', 'assassin'],
        ['fighter', 'assassin', 'mage'],
        ['fighter', 'tank', 'mage', 'assassin'],
        list(ENEMY_STATS.keys()) + list(ENEMY_STATS.keys()),
    ]
    pool = pools[min(wave - 1, len(pools) - 1)]
    pool = [e for e in pool if e not in ['mini_boss', 'minotaur_boss', 'demon_boss']]
    etype = random.choice(pool) if pool else 'fighter'
    
    if etype == 'healer' and len(enemies) == 0:
        etype = random.choice([e for e in pool if e != 'healer']) if pool else 'fighter'
    
    return etype

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


grid, spawn_points, GOAL_GRID = create_maze()
towers = []
enemies = []
traps = []
projectiles = []
money = 300
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
game_won = False
victory_play_again_rect = None
victory_exit_rect = None

def next_wave():
    global wave, wave_enemies_left, boss_spawn_lane, spawn_points
    global enemy_scale, boss_popup_counter, target_wave
    wave += 1
    
    if wave <= target_wave:
        wave_enemies_left = max(2, int(5 * (1.5 ** (wave / 5.0))))
    else:
        wave_enemies_left = max(2, int(5 * (1.5 ** (target_wave / 5.0))))
    
    if wave % 5 == 0:
        new_path_tiles, towers_to_remove, spawn_point = expand_paths(grid, towers, GOAL_GRID, spawn_points)
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
            enemy_scale *= 1.0 + ENEMY_SCALE_INCREMENT
    except Exception:
        pass


next_wave()
run = True
while run:
    dt = clock.tick(FPS) / 1000.0
    screen.fill(DARK_GRAY)
    draw_grid(screen, grid, GOAL_GRID)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
            elif not paused:
                if event.key == pygame.K_1:
                    placing_tower_type = 'physical'
                elif event.key == pygame.K_2:
                    placing_tower_type = 'magic'
                elif event.key == pygame.K_3:
                    placing_tower_type = 'fire'
                elif event.key == pygame.K_4:
                    placing_tower_type = 'spikes'
                elif event.key == pygame.K_5:
                    placing_tower_type = 'ice'
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

            if paused:
                continue
          
            if not game_won and placing_tower_type in ['physical', 'magic', 'ice'] and can_place_tower(grid, gx, gy, towers):
                cost = TOWER_COSTS[placing_tower_type]
                if money >= cost:
                    tower_pos = pygame.Vector2(gx * TILE + TILE // 2, gy * TILE + TILE // 2)
                    towers.append(Tower(tower_pos, placing_tower_type))
                    money -= cost
            elif not game_won and placing_tower_type in ['fire', 'spikes']:
                if can_place_trap(grid, gx, gy, towers, traps):
                    cost = TRAP_COSTS.get(placing_tower_type, 0)
                    if money >= cost:
                        traps.append(Trap((gx, gy), placing_tower_type))
                        money -= cost
           
            selected_tower = None
            for t in towers:
                if math.hypot(t.pos.x - mx, t.pos.y - my) < t.size * 1.2:
                    selected_tower = t
                    break

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
        draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=combined_costs)
        draw_pause(screen, font)
        pygame.display.flip()
        continue

    if wave < target_wave and wave_enemies_left == 0 and len(enemies) == 0:
        next_wave()
    
    if wave == target_wave and wave_enemies_left == 0 and len(enemies) == 0:
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
        wave_timer += 1
        if wave_enemies_left > 0 and wave_timer > 90:
            if wave_enemies_left == 1 and wave % 5 == 0:
                etype = 'demon_boss' if wave % 10 == 0 else 'minotaur_boss'
                spawn = boss_spawn_lane
                boss_popup_counter = 60
            else:
                etype = get_enemy_type_for_wave(wave)
                spawn = random.choice(spawn_points)
            
            try:
                enemies.append(Enemy(grid, spawn, GOAL_GRID, etype, scale=enemy_scale))
            except TypeError:
                enemies.append(Enemy(grid, spawn, GOAL_GRID, etype))
            
            wave_enemies_left -= 1
            wave_timer = 0
        
        for e in enemies:
            e.logic(enemies)

        for t in towers:
            projectile = t.update(enemies)
            if projectile:
                projectiles.append(projectile)
        
        projectiles_to_remove = []
        for p in projectiles:
            if not p.update(dt):
                projectiles_to_remove.append(p)
        for p in projectiles_to_remove:
            projectiles.remove(p)

        for tr in traps:
            tr.update(enemies)

        to_remove = []
        for e in enemies:
            if e.grid_pos() == GOAL_GRID:
                lives -= 1
                to_remove.append(e)
            elif e.hp <= 0:
                money += e.reward
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
    
    combined_costs = {**TOWER_COSTS, **TRAP_COSTS}
    draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=combined_costs)

    if lives <= 0:
        draw_game_over(screen, font)

    pygame.display.flip()

pygame.quit()
sys.exit()
