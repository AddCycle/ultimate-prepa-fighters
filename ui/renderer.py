import pygame
from game import player

def text(text: str, color: str, font: pygame.font.Font) -> pygame.Surface:
    return font.render(text, True, color, "black")

def render_text_at(
    surface: pygame.Surface, txt, x, y, color, font: pygame.font.Font, bg="black"
):
    sf = font.render(txt, True, color, bg)
    rect = sf.get_rect(center=(x, y))
    surface.blit(sf, rect)

def render_player_arrow(screen: pygame.surface.Surface, player:player.Player, arrow_sprite:pygame.surface.Surface):
    offset = player.w // 2 - arrow_sprite.get_width() // 2
    screen.blit(arrow_sprite, (player.x + offset, player.y - 30))

def draw_players(surface: pygame.Surface,players: dict[int, player.Player],my_id,dt,attack_right,attack_left,arrow_sprite,debug=False,font=None):
    X = surface.get_width()
    y_offset = 10
    for pid, p in players.items():
        p.step_animation(dt)
        x, y = p.x, p.y

        frame = p.get_current_frame()
        color = "red" if pid == my_id else "blue"
        score_color = "green" if pid == my_id else "white"
        if debug:
            pygame.draw.rect(surface, color, (x, y, p.w, p.h))

        surface.blit(frame, (x, y))
        if font:
            render_text_at(
                surface, f"Score: {p.score}", X // 2, y_offset, score_color, font
            )
        y_offset += 30

        if pid == my_id:
            render_player_arrow(surface, p, arrow_sprite)

        if debug and p.melee_rect:
            mx, my, mw, mh = p.melee_rect
            pygame.draw.rect(surface, color, (mx, my, mw, mh), 2)

        if p.melee_rect:
            mx, my, mw, mh = p.melee_rect
            attack_surface = attack_left if p.facing == "left" else attack_right
            surface.blit(attack_surface, (mx, my))


def draw_background(surface: pygame.Surface, bg_img: pygame.Surface):
    X = surface.get_width()
    surface.blit(bg_img)
