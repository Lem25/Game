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

def draw_ui(screen, font, money, lives, wave, wave_enemies_left, placing_tower_type, tower_costs=None, game_speed=1, selected_structure=None):
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
    
    boss_indicator = "BOSS" if wave % 5 == 0 else ""
    stats_text = f"Money: ${money}  |  Lives: {lives}  |  Wave: {wave}  |  Enemies: {wave_enemies_left}  |  Speed: {game_speed}x  |  {boss_indicator}"
    stats_surf = font.render(stats_text, True, WHITE)
    screen.blit(stats_surf, (20, box_y + 10))
    
    towers_header = font.render("TOWERS:", True, (255, 255, 100))
    screen.blit(towers_header, (20, box_y + 35))
    
    physical_cost = tower_costs.get('physical', 50)
    magic_cost = tower_costs.get('magic', 60)
    ice_cost = tower_costs.get('ice', 70)
    sentinel_cost = tower_costs.get('sentinel', 80)
    tower_types_line = f"Archer Tower ${physical_cost}  |  Magic ${magic_cost}  |  Ice ${ice_cost}  |  Sentinel ${sentinel_cost}"
    towers_surf = font.render(tower_types_line, True, WHITE)
    screen.blit(towers_surf, (20, box_y + 55))
    
    selected_labels = {
        'physical': 'ARCHER TOWER',
        'magic': 'MAGIC',
        'ice': 'ICE',
        'fire': 'FIRE',
        'spikes': 'SPIKES',
        'sentinel': 'SENTINEL',
    }
    selected_text = f"Selected: {selected_labels.get(placing_tower_type, placing_tower_type.upper())}"
    selected_surf = font.render(selected_text, True, (100, 200, 255))
    screen.blit(selected_surf, (20, box_y + 75))

    traps_header = font.render("TRAPS:", True, (255, 200, 100))
    screen.blit(traps_header, (520, box_y + 35))
    fire_cost = tower_costs.get('fire', None)
    spikes_cost = tower_costs.get('spikes', None)
    trap_info = f"Fire ${fire_cost if fire_cost is not None else 40}  |  Spikes ${spikes_cost if spikes_cost is not None else 30}"
    trap_surf = font.render(trap_info, True, WHITE)
    screen.blit(trap_surf, (520, box_y + 55))
    
    upgrade_hint = font.render("Select structure to upgrade or sell, click targeting mode, adjust speed", True, (180, 180, 180))
    screen.blit(upgrade_hint, (20, box_y + 100))

    if selected_structure and hasattr(selected_structure, 'targeting_mode'):
        label_map = {
            'first': 'First',
            'last': 'Last',
            'strongest': 'Strongest',
            'weakest': 'Weakest',
            'closest_goal': 'Closest Goal',
        }
        mode_text = font.render(f"Targeting: {label_map.get(selected_structure.targeting_mode, selected_structure.targeting_mode)}", True, (150, 220, 255))
        screen.blit(mode_text, (520, box_y + 75))

def draw_game_over(screen, font):
    screen.fill((100, 0, 0))

    game_over_text = font.render("GAME OVER", True, (255, 80, 80))
    game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
    screen.blit(game_over_text, game_over_rect)

    play_again_text = font.render("Play Again", True, WHITE)
    play_again_rect = play_again_text.get_rect(center=(WIDTH // 2 - 100, HEIGHT // 2 + 50))
    pygame.draw.rect(screen, (180, 80, 80), play_again_rect.inflate(20, 10), 2)
    screen.blit(play_again_text, play_again_rect)

    exit_text = font.render("Exit", True, WHITE)
    exit_rect = exit_text.get_rect(center=(WIDTH // 2 + 100, HEIGHT // 2 + 50))
    pygame.draw.rect(screen, (150, 0, 0), exit_rect.inflate(20, 10), 2)
    screen.blit(exit_text, exit_rect)

    return play_again_rect, exit_rect

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

def draw_pause(screen, font, guide_key='H', settings_key='O'):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, WIDTH, HEIGHT))
    screen.blit(overlay, (0, 0))
    
    pause_text = font.render("PAUSED", True, (255, 255, 0))
    pause_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    screen.blit(pause_text, pause_rect)
    
    resume_text = font.render("Press ESC to Resume", True, WHITE)
    resume_rect = resume_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
    screen.blit(resume_text, resume_rect)
    
    guide_text = font.render(f"Press [{guide_key}] for Game Guide", True, (100, 255, 100))
    guide_rect = guide_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    screen.blit(guide_text, guide_rect)

    settings_text = font.render(f"Press [{settings_key}] for Settings", True, (100, 200, 255))
    settings_rect = settings_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    screen.blit(settings_text, settings_rect)


def draw_settings_popup(
    screen,
    font,
    current_resolution,
    resolution_options,
    settings_tab='resolution',
    keybind_display=None,
    waiting_action=None,
):
    popup_width = 520
    popup_height = 420
    popup_x = (WIDTH - popup_width) // 2
    popup_y = (HEIGHT - popup_height) // 2

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 160), (0, 0, WIDTH, HEIGHT))
    screen.blit(overlay, (0, 0))

    popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    pygame.draw.rect(popup_surface, (15, 20, 30, 245), (0, 0, popup_width, popup_height))
    pygame.draw.rect(popup_surface, (120, 180, 255, 220), (0, 0, popup_width, popup_height), 2)

    title = font.render("SETTINGS", True, (255, 255, 120))
    popup_surface.blit(title, (popup_width // 2 - title.get_width() // 2, 20))

    hint = font.render("[1] Resolution  |  [2] Keybinds  |  ESC closes settings", True, (190, 190, 190))
    popup_surface.blit(hint, (popup_width // 2 - hint.get_width() // 2, 52))

    tab_defs = [
        ('resolution', '[1] Resolution'),
        ('keybinds', '[2] Keybinds'),
    ]
    tab_rects = []
    tab_y = 86
    tab_x = 40
    for tab_key, tab_label in tab_defs:
        tab_rect = pygame.Rect(tab_x, tab_y, 210, 34)
        is_active = settings_tab == tab_key
        fill_color = (45, 70, 105, 235) if is_active else (35, 45, 65, 220)
        border_color = (130, 210, 255) if is_active else (95, 120, 165)
        pygame.draw.rect(popup_surface, fill_color, tab_rect)
        pygame.draw.rect(popup_surface, border_color, tab_rect, 2)
        tab_text = font.render(tab_label, True, (220, 240, 255) if is_active else (180, 190, 210))
        popup_surface.blit(tab_text, (tab_rect.x + 14, tab_rect.y + 8))
        tab_rects.append((pygame.Rect(popup_x + tab_rect.x, popup_y + tab_rect.y, tab_rect.width, tab_rect.height), tab_key))
        tab_x += 230

    option_rects = []
    keybind_action_rects = []
    if settings_tab == 'resolution':
        tab_hint = font.render("Click a resolution option to apply", True, (185, 210, 235))
        popup_surface.blit(tab_hint, (popup_width // 2 - tab_hint.get_width() // 2, 132))

        y = 168
        for idx, res in enumerate(resolution_options):
            label = f"{idx + 1}. {res[0]} x {res[1]}"
            is_current = tuple(current_resolution) == tuple(res)
            text_color = (120, 255, 120) if is_current else (230, 230, 230)
            text = font.render(label, True, text_color)

            row_rect = pygame.Rect(60, y - 4, popup_width - 120, 38)
            border = (80, 220, 120) if is_current else (90, 120, 170)
            pygame.draw.rect(popup_surface, (30, 35, 50, 220), row_rect)
            pygame.draw.rect(popup_surface, border, row_rect, 2)
            popup_surface.blit(text, (row_rect.x + 14, row_rect.y + 8))

            option_rects.append((pygame.Rect(popup_x + row_rect.x, popup_y + row_rect.y, row_rect.width, row_rect.height), res))
            y += 42
    else:
        keybind_display = keybind_display or {}
        action_rows = [
            ('pause', 'Pause / Resume'),
            ('open_guide', 'Open Guide'),
            ('open_settings', 'Open Settings'),
            ('build_physical', 'Build Archer Tower'),
            ('build_magic', 'Build Magic Tower'),
            ('build_ice', 'Build Ice Tower'),
            ('build_fire', 'Build Fire Trap'),
            ('build_spikes', 'Build Spike Trap'),
            ('build_sentinel', 'Build Sentinel'),
            ('upgrade_path1', 'Upgrade Path 1'),
            ('upgrade_path2', 'Upgrade Path 2'),
            ('sell_structure', 'Sell Structure'),
            ('cycle_speed', 'Cycle Game Speed'),
        ]

        if waiting_action:
            waiting_name = next((label for action, label in action_rows if action == waiting_action), waiting_action)
            tab_hint = font.render(f"Press a key for: {waiting_name} (ESC cancels)", True, (255, 220, 120))
        else:
            tab_hint = font.render("Click action row to change keybind", True, (185, 210, 235))
        popup_surface.blit(tab_hint, (popup_width // 2 - tab_hint.get_width() // 2, 132))

        y = 166
        for action, label in action_rows:
            row_rect = pygame.Rect(44, y, popup_width - 88, 26)
            is_waiting = waiting_action == action
            border = (255, 210, 120) if is_waiting else (90, 120, 170)
            fill = (45, 35, 25, 230) if is_waiting else (30, 35, 50, 220)
            pygame.draw.rect(popup_surface, fill, row_rect)
            pygame.draw.rect(popup_surface, border, row_rect, 2)

            key_text_value = keybind_display.get(action, '-')
            label_text = font.render(label, True, (230, 230, 230))
            key_text = font.render(f"[{key_text_value}]", True, (120, 255, 120) if not is_waiting else (255, 220, 120))
            popup_surface.blit(label_text, (row_rect.x + 10, row_rect.y + 4))
            popup_surface.blit(key_text, (row_rect.right - key_text.get_width() - 10, row_rect.y + 4))

            keybind_action_rects.append((pygame.Rect(popup_x + row_rect.x, popup_y + row_rect.y, row_rect.width, row_rect.height), action))
            y += 29

    screen.blit(popup_surface, (popup_x, popup_y))
    return {'tabs': tab_rects, 'options': option_rects, 'actions': keybind_action_rects}

def draw_victory(screen, font):
    screen.fill((0, 100, 0))
    
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

def draw_guide(screen, font, page, scroll_offset=0):
    guide_width = 700
    guide_height = 650
    guide_x = (WIDTH - guide_width) // 2
    guide_y = 75

    guide_surf = pygame.Surface((guide_width, guide_height), pygame.SRCALPHA)
    pygame.draw.rect(guide_surf, (20, 20, 40, 240), (0, 0, guide_width, guide_height))
    pygame.draw.rect(guide_surf, (100, 150, 255, 200), (0, 0, guide_width, guide_height), 3)

    max_scroll = 0

    if page == 'menu':
        title = font.render("GAME GUIDE", True, (255, 255, 100))
        guide_surf.blit(title, (guide_width // 2 - 50, 20))

        sections = [
            "[1] Towers & Upgrades",
            "[2] Traps & Sentinels",
            "[3] Enemies & Bosses",
            "[4] Game Mechanics",
            "[5] Strategy Tips",
            "[6] Keybinds"
        ]

        y_offset = 80
        for i, section in enumerate(sections):
            text = font.render(section, True, (100, 255, 100))
            guide_surf.blit(text, (50, y_offset + i * 40))
    else:
        page_items = [
            ('towers', '1:Towers'),
            ('traps', '2:Traps'),
            ('enemies', '3:Enemies'),
            ('mechanics', '4:Mechanics'),
            ('strategy', '5:Strategy'),
            ('keybinds', '6:Keybinds'),
        ]

        page_titles = {
            'towers': "TOWERS & UPGRADES",
            'traps': "TRAPS & DEFENSE",
            'enemies': "ENEMIES & BOSSES",
            'mechanics': "GAME MECHANICS",
            'strategy': "STRATEGY TIPS",
            'keybinds': "KEYBINDS",
        }
        title = font.render(page_titles.get(page, "GAME GUIDE"), True, (255, 255, 100))
        guide_surf.blit(title, (20, 40))

        page_font = pygame.font.SysFont("arial", 11)
        padding_x = 8
        item_height = 18
        spacing = 6
        current_x = 12
        bar_y = 10
        for key, label in page_items:
            text_surf = page_font.render(label, True, WHITE)
            item_width = text_surf.get_width() + padding_x * 2
            is_active = (page == key)
            if is_active:
                bg_color = (100, 150, 255)
                border_color = (200, 220, 255)
                text_color = (255, 255, 255)
            else:
                bg_color = (40, 40, 60)
                border_color = (90, 90, 120)
                text_color = (190, 190, 210)

            pygame.draw.rect(guide_surf, bg_color, (current_x, bar_y, item_width, item_height), border_radius=4)
            pygame.draw.rect(guide_surf, border_color, (current_x, bar_y, item_width, item_height), 1, border_radius=4)
            label_surf = page_font.render(label, True, text_color)
            guide_surf.blit(label_surf, (current_x + padding_x, bar_y + 2))
            current_x += item_width + spacing

        content = []
        line_height = 24
        content_font = pygame.font.SysFont("arial", 13)

        if page == 'towers':
            content = [
                "ARCHER TOWER - $60",
                "  Path 1: Sniper ($120) -> Elite ($240)",
                "    Sniper: +Range, +Damage | Elite: Ignores 60% armor",
                "  Path 2: Volley ($110) -> Bounce ($220)",
                "    Volley: 4 arrows | Bounce: Arrows bounce once",
                "",
                "MAGIC TOWER - $70",
                "  Path 1: Bolt ($140) -> Arc ($280)",
                "    Bolt: Chain to 3 enemies | Arc: Chain 4 + spread effects",
                "  Path 2: Nova ($160) -> Vortex ($320)",
                "    Nova: AoE damage | Vortex: Pull enemies + bigger AoE",
                "",
                "ICE TOWER - $80",
                "  Path 1: Glacial ($130) -> Shatter ($260)",
                "    Glacial: Faster freeze pulses | Shatter: +70% dmg to frozen",
                "  Path 2: Blizzard ($150) -> Absolute Zero ($300)",
                "    Blizzard: Slow all enemies in range | Absolute Zero: Focus hard-freeze",
                "",
                "SENTINEL TOWER - $90",
                "  Auto-activates barrier when enemies approach (6s, 10s CD)",
                "  Path 1: Barrier ($100) -> Reflect ($200)",
                "    Barrier: 8s duration | Reflect: 15 DPS to blocked enemies",
                "  Path 2: Pulse ($110) -> Overload ($220)",
                "    Pulse: Stronger repel | Overload: Explode for 150 AoE"
            ]
            line_height = 24
            content_font = pygame.font.SysFont("arial", 13)
        elif page == 'traps':
            content = [
                "FIRE TRAP - $45 (Place on path)",
                "  Continuous damage in 3x3 area, strongest at center",
                "  Path 1: Inferno ($80) -> Phoenix ($180)",
                "    Inferno: Bigger aura, +DPS | Phoenix: Revive on destroy",
                "  Path 2: Oil Slick ($90) -> Detonate ($200)",
                "    Oil Slick: Burn spreads | Detonate: Explode on kill (40 AoE)",
                "",
                "SPIKE TRAP - $35 (Place on path)",
                "  Damages enemies on tile every 1 second",
                "  Path 1: Barbed ($70) -> Impale ($160)",
                "    Barbed: Bleed DoT (5 DPS) | Impale: Hold enemy 2s",
                "  Path 2: Cluster ($80) -> Quake ($170)",
                "    Cluster: Multi-traps | Quake: AoE on trigger",
                "",
                "TIP: Traps placed on enemy paths deal damage automatically!",
                "Combine with towers for maximum efficiency."
            ]
            line_height = 30
            content_font = font
        elif page == 'enemies':
            content = [
                "REGULAR ENEMIES:",
                "  Fighter - Physical reduction, gains 30% HP shield at 50% HP (once)",
                "  Mage - Magic reduction, blocks first 3 projectiles",
                "  Assassin - 20% dodge that falls on each dodge",
                "    At 30% HP: teleports to nearest healer (once)",
                "    If no healer: 50% dodge and +20% move speed",
                "  Tank - Heavy all-around resist, doubles resist at 30% HP",
                "  Swarm - Very low HP, high speed, spawns in tight burst groups",
                "  Healer - Neutral resist, chain-heals 13% HP to up to 3 lane allies",
                "",
                "BOSSES (Spawn every 5 waves):",
                "  Minotaur Boss - Massive physical armor tank",
                "    Phase 1: walks and periodically stuns towers",
                "    Phase 2 (<30% HP): loses all resists, becomes extremely fast",
                "  Demon Boss - Huge magic resist",
                "    Phase 1: swaps towers between two lanes",
                "    Phase 2 (~50% HP): spawns minions",
                "    Phase 3 (~25% HP): teleports to beneficial path point (>=5 tiles from end)",
                "",
                "REWARDS:",
                "  Kill any enemy: 1.5x their base reward",
                "  Example: Tank ($24) gives $36 on kill",
                "  Enemies scale with wave count for harder challenges",
                "",
                "ENEMY ABILITIES:",
                "  - Projectiles are reduced by type resistances",
                "  - Bosses use phase-based mechanics",
                "  - All enemies gain HP scaling on higher waves"
            ]
            line_height = 26
            content_font = pygame.font.SysFont("arial", 13)
        elif page == 'mechanics':
            content = [
                "PLACING STRUCTURES:",
                "  Grid: 20x20 tiles, 40px per tile",
                "  Towers: Place on floor tiles",
                "  Traps: Place on path tiles",
                "  Sentinel: Place on floor tiles, auto-activates near enemies",
                "",
                "UPGRADES:",
                "  Click any tower/trap and choose one upgrade path",
                "  Once you pick a path, you can't upgrade the other!",
                "  Each path has 2 tiers with powerful abilities",
                "",
                "MATCH END:",
                "  Victory and Game Over both show Play Again / Exit buttons",
                "",
                "DAMAGE TYPES:",
                "  Physical - Reduced by physical resistance",
                "  Magic - Reduced by magic resistance",
                "  Ice - Applies slow stacks, freezes at 10 stacks",
                "",
                "STATUS EFFECTS:",
                "  Slow: Reduces movement speed (8% per stack)",
                "  Frozen: Enemy can't move (10+ slow stacks for 3s)",
                "  Bleed: Damage over time from Barbed spikes",
                "  Burn: Fire damage spreads with Oil Slick upgrade",
                "  Impale: Enemy held in place for 2 seconds"
            ]
            line_height = 24
            content_font = pygame.font.SysFont("arial", 13)
        elif page == 'keybinds':
            content = [
                "GAMEPLAY KEYBINDS:",
                "  [1] Archer Tower build mode",
                "  [2] Magic Tower build mode",
                "  [3] Ice Tower build mode",
                "  [4] Fire Trap build mode",
                "  [5] Spike Trap build mode",
                "  [6] Sentinel build mode",
                "",
                "SELECTED STRUCTURE:",
                "  [Q] Upgrade Path 1",
                "  [E] Upgrade Path 2",
                "  [R] Sell structure",
                "",
                "GLOBAL CONTROLS:",
                "  [C] Change game speed",
                "  [ESC] Pause / Resume",
                "  [O] Open settings (while paused)",
                "",
                "GUIDE CONTROLS (Paused):",
                "  [H] Open guide",
                "  [1-6] Open guide pages",
                "  [UP]/[DOWN] or Wheel: Scroll",
                "  [BACKSPACE] Back to guide menu / close guide"
            ]
            line_height = 24
            content_font = pygame.font.SysFont("arial", 13)
        elif page == 'strategy':
            content = [
                "  - Mix damage types to handle resistant enemies",
                "  - Ice towers slow, letting others deal more damage",
                "  - Place traps at choke points for max efficiency",
                "  - Save money for upgrades - they're very powerful!",
                "  - Sentinels block paths temporarily for emergency defense"
            ]
            line_height = 34
            content_font = pygame.font.SysFont("arial", 15)

        content_area = pygame.Rect(20, 80, guide_width - 40, guide_height - 130)
        pygame.draw.rect(guide_surf, (30, 30, 55, 255), content_area)
        pygame.draw.rect(guide_surf, (70, 90, 130, 255), content_area, 1)

        content_total_height = max(0, len(content) * line_height)
        max_scroll = max(0, content_total_height - content_area.height)
        scroll_offset = max(0, min(scroll_offset, max_scroll))

        clip_rect = guide_surf.get_clip()
        guide_surf.set_clip(content_area)

        y_offset = content_area.y - scroll_offset
        for line in content:
            if y_offset + line_height >= content_area.y and y_offset <= content_area.bottom:
                if page == 'enemies':
                    if line.endswith(":"):
                        color = (255, 200, 100)
                    elif line.startswith("  ") and "HP" in line:
                        color = (150, 255, 150)
                    else:
                        color = WHITE
                elif page in ('towers', 'traps'):
                    color = (255, 200, 100) if line and not line.startswith(" ") else WHITE
                elif page == 'strategy':
                    color = (150, 255, 200)
                else:
                    color = (255, 200, 100) if line.endswith(":") else WHITE

                text = content_font.render(line, True, color)
                guide_surf.blit(text, (content_area.x, y_offset))
            y_offset += line_height

        guide_surf.set_clip(clip_rect)

        if max_scroll > 0:
            track_rect = pygame.Rect(content_area.right - 6, content_area.y + 4, 4, content_area.height - 8)
            pygame.draw.rect(guide_surf, (60, 70, 90), track_rect, border_radius=2)

            thumb_height = max(24, int(track_rect.height * (content_area.height / content_total_height)))
            thumb_travel = track_rect.height - thumb_height
            thumb_y = track_rect.y + int((scroll_offset / max_scroll) * thumb_travel)
            thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
            pygame.draw.rect(guide_surf, (150, 180, 255), thumb_rect, border_radius=2)

    tiny_font = pygame.font.SysFont("arial", 12)
    if page == 'menu':
        nav_text = tiny_font.render("[1-6] Select  |  [BACKSPACE] Close  |  [ESC] Resume", True, (180, 180, 180))
    else:
        nav_text = tiny_font.render("[Wheel/UP/DOWN] Scroll  |  [BACKSPACE] Menu  |  [ESC] Resume", True, (180, 180, 180))
    nav_rect = nav_text.get_rect(bottomright=(guide_width - 12, guide_height - 10))
    guide_surf.blit(nav_text, nav_rect)

    screen.blit(guide_surf, (guide_x, guide_y))
    return max_scroll
def draw_upgrade_ui(screen, font, selected_structure, money):
    if not selected_structure:
        return {'targeting_modes': {}, 'sell_rect': None}

    panel_width = 250
    panel_height = 250 if hasattr(selected_structure, 'targeting_mode') else 210
    panel_x = selected_structure.pos.x + 30
    panel_y = selected_structure.pos.y - panel_height // 2

    if panel_x + panel_width > WIDTH:
        panel_x = selected_structure.pos.x - panel_width - 30
    if panel_y < 0:
        panel_y = 0
    if panel_y + panel_height > GAME_HEIGHT:
        panel_y = GAME_HEIGHT - panel_height

    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (20, 20, 40, 230), (0, 0, panel_width, panel_height))
    pygame.draw.rect(panel_surface, (100, 150, 255, 255), (0, 0, panel_width, panel_height), 2)

    name_text = font.render(selected_structure.name, True, (255, 255, 100))
    panel_surface.blit(name_text, (10, 10))

    y_offset = 40

    def draw_path(path_index, key_text, level):
        nonlocal y_offset
        upgrade_name, upgrade_cost = selected_structure.get_upgrade_info(path_index)
        if upgrade_name:
            can_afford = money >= upgrade_cost
            color = (100, 255, 100) if can_afford else (150, 150, 150)
            upgrade_text = font.render(f"[{key_text}] {upgrade_name} - ${upgrade_cost}", True, color)
            panel_surface.blit(upgrade_text, (10, y_offset))
            if level > 0:
                level_text = font.render(f"  Level: {level}/2", True, (200, 200, 200))
                panel_surface.blit(level_text, (15, y_offset + 20))
            y_offset += 50
        elif level >= 2:
            maxed_text = font.render(f"Path {path_index}: MAXED", True, (255, 215, 0))
            panel_surface.blit(maxed_text, (10, y_offset))

    path1_level = getattr(selected_structure, 'path1_level', 0)
    path2_level = getattr(selected_structure, 'path2_level', 0)

    if path1_level > 0:
        draw_path(1, 'Q', path1_level)
    elif path2_level > 0:
        draw_path(2, 'E', path2_level)
    else:
        draw_path(1, 'Q', path1_level)
        draw_path(2, 'E', path2_level)

    targeting_mode_rects = {}
    if hasattr(selected_structure, 'targeting_mode'):
        label_map = {
            'first': 'First',
            'last': 'Last',
            'strongest': 'Strong',
            'weakest': 'Weak',
            'closest_goal': 'Goal',
        }
        modes = ['first', 'last', 'strongest', 'weakest', 'closest_goal']
        title = font.render('Targeting:', True, (180, 220, 255))
        panel_surface.blit(title, (10, 150))

        btn_y = 172
        btn_w = 44
        btn_h = 22
        spacing = 4
        for idx, mode in enumerate(modes):
            x = 10 + idx * (btn_w + spacing)
            rect = pygame.Rect(x, btn_y, btn_w, btn_h)
            is_active = selected_structure.targeting_mode == mode
            bg = (90, 150, 240) if is_active else (50, 60, 90)
            border = (180, 220, 255) if is_active else (120, 130, 160)
            pygame.draw.rect(panel_surface, bg, rect, border_radius=4)
            pygame.draw.rect(panel_surface, border, rect, 1, border_radius=4)

            label = font.render(label_map[mode], True, (255, 255, 255))
            label_rect = label.get_rect(center=rect.center)
            panel_surface.blit(label, label_rect)
            targeting_mode_rects[mode] = pygame.Rect(panel_x + rect.x, panel_y + rect.y, rect.w, rect.h)

    build_cost = getattr(selected_structure, 'build_cost', 0)
    upgrade_spent = getattr(selected_structure, 'upgrade_spent', 0)
    sell_value = int((build_cost + upgrade_spent) * 0.75)
    sell_btn_rect = pygame.Rect(10, panel_height - 34, panel_width - 20, 24)
    pygame.draw.rect(panel_surface, (70, 120, 80), sell_btn_rect, border_radius=4)
    pygame.draw.rect(panel_surface, (120, 190, 130), sell_btn_rect, 1, border_radius=4)
    sell_text = font.render(f"Sell: ${sell_value}", True, (255, 255, 255))
    panel_surface.blit(sell_text, sell_text.get_rect(center=sell_btn_rect.center))
    
    screen.blit(panel_surface, (panel_x, panel_y))
    return {
        'targeting_modes': targeting_mode_rects,
        'sell_rect': pygame.Rect(panel_x + sell_btn_rect.x, panel_y + sell_btn_rect.y, sell_btn_rect.w, sell_btn_rect.h),
    }