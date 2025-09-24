import pygame
from ui.renderer import *
import sys


def show_main_menu(screen: pygame.Surface, player_sprite):
    X, Y = screen.get_width(), screen.get_height()
    font = pygame.font.Font("PressStart2P.ttf", 20)
    quit_text = text("QUIT", "white", font)
    connect_text = text("PLAY", "white", font)
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
            connect_text = text("PLAY", "white", font)
        elif keys[pygame.K_UP]:
            choice = 1
            quit_text = text("QUIT", "white", font)
            connect_text = text("PLAY", "green", font)
        elif keys[pygame.K_SPACE]:
            selecting = False
            break

        render_text_at(screen, "Ultimate Prepa Fighters", X // 2, 50, "white", font)
        screen.blit(connect_text, connect_text.get_rect(center=(X // 2, Y // 2)))
        screen.blit(quit_text, quit_text.get_rect(center=(X // 2, Y // 2 + 200)))
        screen.blit(player_sprite, (X // 2, 100))
        pygame.display.flip()  # updating screen

    return choice


def show_character_menu(screen: pygame.Surface, player_sprite):
    X, Y = screen.get_width(), screen.get_height()
    font = pygame.font.Font("PressStart2P.ttf", 20)
    choices = 3
    frog_text = text("FROG", "white", font)
    qval_text = text("QVAL", "white", font)
    pass_text = text("PASS", "white", font)

    def highlight_text(choice: int):
        nonlocal frog_text, qval_text, pass_text
        if choice == 0:
            frog_text = text("FROG", "green", font)
        elif choice == 1:
            qval_text = text("QVAL", "green", font)
        else:
            pass_text = text("PASS", "green", font)

    def reset():
        nonlocal frog_text, qval_text, pass_text
        frog_text = text("FROG", "white", font)
        qval_text = text("QVAL", "white", font)
        pass_text = text("PASS", "white", font)

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
            if choice < choices - 1:
                choice += 1
            reset()
            highlight_text(choice)
        elif keys[pygame.K_UP]:
            if choice > 0:
                choice -= 1
            reset()
            highlight_text(choice)
        elif keys[pygame.K_SPACE]:
            selecting = False
            break
        elif keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

        render_text_at(screen, "Select your character", X // 2, 50, "white", font)
        screen.blit(frog_text, frog_text.get_rect(center=(X // 2, Y // 2)))
        screen.blit(qval_text, qval_text.get_rect(center=(X // 2, Y // 2 + 100)))
        screen.blit(pass_text, pass_text.get_rect(center=(X // 2, Y // 2 + 200)))
        screen.blit(player_sprite, (X // 2, 100))
        pygame.display.flip()  # updating screen

    return choice
