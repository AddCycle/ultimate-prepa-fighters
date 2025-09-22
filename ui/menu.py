import pygame
from ui.renderer import *


def show_main_menu(screen: pygame.Surface, player_sprite):
    X, Y = screen.get_width(), screen.get_height()
    font = pygame.font.Font("PressStart2P.ttf", 20)
    quit_text = text("QUIT", "white", font)
    connect_text = text("CONNECT", "white", font)
    selecting = True
    choice = -1
    # main MENU
    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break

        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_DOWN]:
            choice = 0
            quit_text = text("QUIT", "green", font)
            connect_text = text("CONNECT", "white", font)
        elif keys[pygame.K_UP]:
            choice = 1
            quit_text = text("QUIT", "white", font)
            connect_text = text("CONNECT", "green", font)
        elif keys[pygame.K_SPACE]:
            selecting = False
            break

        render_text_at(screen, "Ultimate Prepa Fighters", X // 2, 50, "white", font)
        screen.blit(connect_text, connect_text.get_rect(center=(X // 2, Y // 2)))
        screen.blit(quit_text, quit_text.get_rect(center=(X // 2, Y // 2 + 200)))
        screen.blit(player_sprite, (X // 2, 100))
        pygame.display.flip()  # updating screen

    return choice
