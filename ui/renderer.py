import pygame


def text(text: str, color: str, font: pygame.font.Font) -> pygame.Surface:
    return font.render(text, True, color, "black")


def render_text_at(
    surface: pygame.Surface, txt, x, y, color, font: pygame.font.Font, bg="black"
):
    sf = font.render(txt, True, color, bg)
    rect = sf.get_rect(center=(x, y))
    surface.blit(sf, rect)


def draw_players(surface, players, player_sprite, my_id, debug=False, font=None):
    X = surface.get_width()
    y_offset = 10
    for pid, p in players.items():
        x, y = p.x, p.y
        color = "red" if pid == my_id else "blue"
        score_color = "green" if pid == my_id else "white"

        if debug:
            pygame.draw.rect(surface, color, (x, y, p.w, p.h))
        surface.blit(player_sprite, (x - player_sprite.get_width() // 4, y))
        if font:
            render_text_at(
                surface, f"Score: {p.score}", X // 2, y_offset, score_color, font
            )
        y_offset += 30

        if debug and p.melee_rect:
            mx, my, mw, mh = p.melee_rect
            pygame.draw.rect(surface, color, (mx, my, mw, mh), 2)
