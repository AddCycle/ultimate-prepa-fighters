import pygame
from ui.renderer import *
from ui.button import *
import sys


class Menu:
    def __init__(self, screen: pygame.Surface, title: str) -> None:
        self.screen = screen
        self.middle = (screen.get_width() // 2, screen.get_height() // 2)
        self.font = pygame.font.Font("PressStart2P.ttf", 20)
        self.title = title
        self.buttons: list[Button] = []
        self.choice = 0
        self.spacing = 50

    def addButton(self, button: Button):
        self.buttons.append(button)
        self.rearrange_buttons()

    def rearrange_buttons(self):
        total_height = len(self.buttons) * self.spacing
        start_y = self.middle[1] - total_height // 2

        for i, btn in enumerate(self.buttons):
            btn.center = (self.middle[0], start_y + i * self.spacing)

    def render(self):
        for btn in self.buttons:
            btn.render(self.screen, self.font)

    def clear(self):
        # self.buttons.clear()
        self.screen.fill("black")

    def reset_buttons(self):
        for btn in self.buttons:
            btn.active = False

    def display(self) -> int:
        selecting = True
        self.choice = 0
        choices = len(self.buttons)
        print(f"choices : {choices}")
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    break

            keys = pygame.key.get_just_pressed()
            if keys[pygame.K_DOWN]:
                self.choice = (self.choice + 1) % choices
            elif keys[pygame.K_UP]:
                self.choice = (self.choice - 1) % choices
            elif keys[pygame.K_SPACE]:
                selecting = False
                break
            elif keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()

            self.reset_buttons()
            self.buttons[self.choice].active = True

            self.screen.fill("black")

            self.render()

            render_text_at(
                self.screen,
                self.title,
                self.middle[0],
                50,
                "white",
                self.font,
            )
            pygame.display.flip()  # updating screen

        return self.choice

class PauseMenu(Menu):
    def __init__(self, screen: pygame.Surface, title: str) -> None:
        super().__init__(screen, title)
        self.addButton(Button("Resume"))
        self.addButton(Button("Quit"))

class MainMenu(Menu):
    def __init__(self, screen: pygame.Surface, title: str) -> None:
        super().__init__(screen, title)
        self.addButton(Button("PLAY"))
        self.addButton(Button("QUIT"))

class CharacterMenu(Menu):
    def __init__(self, screen: pygame.Surface, title: str) -> None:
        super().__init__(screen, title)
        self.addButton(Button("FROG"))
        self.addButton(Button("QVAL"))
        self.addButton(Button("PASS"))