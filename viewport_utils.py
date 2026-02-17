import pygame


def get_viewport_rect(surface, base_width, base_height):
    window_w, window_h = surface.get_size()
    scale = min(window_w / base_width, window_h / base_height)
    viewport_w = max(1, int(base_width * scale))
    viewport_h = max(1, int(base_height * scale))
    viewport_x = (window_w - viewport_w) // 2
    viewport_y = (window_h - viewport_h) // 2
    return pygame.Rect(viewport_x, viewport_y, viewport_w, viewport_h)


def present_frame(window, screen, base_width, base_height):
    viewport = get_viewport_rect(window, base_width, base_height)
    window.fill((0, 0, 0))
    if viewport.size == (base_width, base_height):
        window.blit(screen, viewport.topleft)
    else:
        scaled = pygame.transform.smoothscale(screen, viewport.size)
        window.blit(scaled, viewport.topleft)
    pygame.display.flip()
    return viewport


def window_to_game_pos(pos, viewport, base_width, base_height):
    x, y = pos
    if not viewport.collidepoint(x, y):
        return None
    rel_x = (x - viewport.x) / viewport.width
    rel_y = (y - viewport.y) / viewport.height
    gx = int(rel_x * base_width)
    gy = int(rel_y * base_height)
    gx = max(0, min(base_width - 1, gx))
    gy = max(0, min(base_height - 1, gy))
    return gx, gy
