import pygame
from constants import WIDTH, HEIGHT, TILE, GRID_W, GRID_H, GAME_HEIGHT
from colors import BLACK, WHITE, LIGHT_GREEN, DARK_GREEN, GOLD
from assets import get as get_asset

def draw_grid(screen, grid, goal_grid):
    tile_path = get_asset('tile_path', TILE)
    tile_grass = get_asset('tile_grass', TILE)
    tile_wall = get_asset('tile_wall', TILE)
    wall_left = get_asset('wall_left', TILE)
    wall_right = get_asset('wall_right', TILE)
    for y in range(GRID_H):
        for x in range(GRID_W):
            pos = (x * TILE, y * TILE)
            if grid[y][x] == 1:
                if x == 0 and wall_left:
                    screen.blit(wall_left, pos)
                elif x == GRID_W - 1 and wall_right:
                    screen.blit(wall_right, pos)
                elif tile_wall:
                    if x == 0:
                        screen.blit(pygame.transform.rotate(tile_wall, 90), pos)
                    elif x == GRID_W - 1:
                        screen.blit(pygame.transform.rotate(tile_wall, -90), pos)
                    else:
                        screen.blit(tile_wall, pos)
                else:
                    pygame.draw.rect(screen, BLACK, (pos[0], pos[1], TILE, TILE))
            elif grid[y][x] == 2:
                if tile_path:
                    screen.blit(tile_path, pos)
                else:
                    pygame.draw.rect(screen, WHITE, (pos[0], pos[1], TILE, TILE))
                    pygame.draw.rect(screen, (200, 200, 200), (pos[0], pos[1], TILE, TILE), 1)
            else:
                if tile_grass:
                    screen.blit(tile_grass, pos)
                else:
                    pygame.draw.rect(screen, LIGHT_GREEN, (pos[0], pos[1], TILE, TILE))
                    pygame.draw.rect(screen, DARK_GREEN, (pos[0], pos[1], TILE, TILE), 1)
    
    tx = goal_grid[0] * TILE + TILE // 2
    ty = goal_grid[1] * TILE + TILE // 2
    gem = get_asset('goal_gem', TILE)
    if gem:
        screen.blit(gem, (tx - TILE // 2, ty - TILE // 2))
    else:
        pygame.draw.circle(screen, GOLD, (tx, ty), TILE)
        pygame.draw.circle(screen, BLACK, (tx, ty), TILE, 2)

def draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=None):
    if tower_costs is None:
        tower_costs = {}
    
    box_height = HEIGHT - GAME_HEIGHT
    box_y = GAME_HEIGHT
    box_x = 0
    box_width = WIDTH
    
    ui_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    pygame.draw.rect(ui_surface, (0, 0, 0, 200), (0, 0, box_width, box_height))
    pygame.draw.rect(ui_surface, (255, 255, 255, 150), (0, 0, box_width, box_height), 2)
    screen.blit(ui_surface, (box_x, box_y))
    
    boss_indicator = "BOSS" if wave in [5, 10] else ""
    stats_text = f"Money: ${money}  |  Lives: {lives}  |  Wave: {wave}  |  Enemies: {wave_enemies_left}  |  {boss_indicator}"
    stats_surf = font.render(stats_text, True, WHITE)
    screen.blit(stats_surf, (20, box_y + 10))
    
    towers_header = font.render("TOWER TYPES:", True, (255, 255, 100))
    screen.blit(towers_header, (20, box_y + 35))
    
    physical_cost = tower_costs.get('physical', 50)
    magic_cost = tower_costs.get('magic', 60)
    tower_types_line = f"[1] Physical ${physical_cost}  |  [2] Magic ${magic_cost}  |  [5] Ice ${tower_costs.get('ice', 70)}"
    towers_surf = font.render(tower_types_line, True, WHITE)
    screen.blit(towers_surf, (20, box_y + 55))
    
    selected_text = f"Selected: {placing_tower_type.upper()}"
    selected_surf = font.render(selected_text, True, (100, 200, 255))
    screen.blit(selected_surf, (20, box_y + 75))

    traps_header = font.render("TRAPS:", True, (255, 200, 100))
    screen.blit(traps_header, (420, box_y + 35))
    fire_cost = tower_costs.get('fire', None)
    spikes_cost = tower_costs.get('spikes', None)
    trap_info = f"[3] Fire ${fire_cost if fire_cost is not None else 40}  |  [4] Spikes ${spikes_cost if spikes_cost is not None else 30}"
    trap_surf = font.render(trap_info, True, WHITE)
    screen.blit(trap_surf, (420, box_y + 55))

def draw_game_over(screen, font):
    go_text = font.render("GAME OVER! Press Ctrl+C to restart.", True, (255, 50, 50))
    screen.blit(go_text, (WIDTH // 2 - 200, HEIGHT // 2 - 100))

def draw_boss_spawn_popup(screen, font, boss_type):
    popup_width = 300
    popup_height = 100
    popup_x = (WIDTH - popup_width) // 2
    popup_y = (HEIGHT - popup_height) // 2
    
    popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    pygame.draw.rect(popup_surface, (0, 0, 0, 200), (0, 0, popup_width, popup_height))
    pygame.draw.rect(popup_surface, (255, 0, 0, 255), (0, 0, popup_width, popup_height), 3)
    
    text = font.render(f"{boss_type.upper()} HAS SPAWNED!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(popup_width // 2, popup_height // 2))
    popup_surface.blit(text, (text_rect.x, text_rect.y + 15))
    
    screen.blit(popup_surface, (popup_x, popup_y))

def draw_wave_selection_popup(screen, font, input_text):
    popup_width = 400
    popup_height = 150
    popup_x = (WIDTH - popup_width) // 2
    popup_y = (HEIGHT - popup_height) // 2
    
    popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    pygame.draw.rect(popup_surface, (0, 0, 0, 200), (0, 0, popup_width, popup_height))
    pygame.draw.rect(popup_surface, (255, 255, 255, 150), (0, 0, popup_width, popup_height), 2)
    
    title = font.render("Select Target Wave", True, WHITE)
    title_rect = title.get_rect(center=(popup_width // 2, 20))
    popup_surface.blit(title, title_rect)
    
    instruction = font.render("Enter wave number and press ENTER", True, (200, 200, 200))
    inst_rect = instruction.get_rect(center=(popup_width // 2, 50))
    popup_surface.blit(instruction, inst_rect)
    
    input_display = font.render(f"Wave: {input_text}_", True, (100, 200, 255))
    input_rect = input_display.get_rect(center=(popup_width // 2, 90))
    popup_surface.blit(input_display, input_rect)
    
    screen.blit(popup_surface, (popup_x, popup_y))

def draw_pause(screen, font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, WIDTH, HEIGHT))
    screen.blit(overlay, (0, 0))
    
    pause_text = font.render("PAUSED", True, (255, 255, 0))
    pause_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
    screen.blit(pause_text, pause_rect)
    
    resume_text = font.render("Press ESC to Resume", True, WHITE)
    resume_rect = resume_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
    screen.blit(resume_text, resume_rect)

def draw_victory(screen, font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 100, 0, 200), (0, 0, WIDTH, HEIGHT))
    screen.blit(overlay, (0, 0))
    
    victory_text = font.render("VICTORY!", True, (0, 255, 0))
    victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
    screen.blit(victory_text, victory_rect)
    
    play_again_text = font.render("Play Again", True, WHITE)
    play_again_rect = play_again_text.get_rect(center=(WIDTH // 2 - 100, HEIGHT // 2 + 50))
    pygame.draw.rect(screen, (0, 150, 0), play_again_rect.inflate(20, 10), 2)
    screen.blit(play_again_text, play_again_rect)
    
    exit_text = font.render("Exit", True, WHITE)
    exit_rect = exit_text.get_rect(center=(WIDTH // 2 + 100, HEIGHT // 2 + 50))
    pygame.draw.rect(screen, (150, 0, 0), exit_rect.inflate(20, 10), 2)
    screen.blit(exit_text, exit_rect)
    
    return play_again_rect, exit_rect
