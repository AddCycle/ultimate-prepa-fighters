import pygame
import ui.renderer as renderer

class Button:
    def __init__(self, text: str, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y
        self.center = (self.x // 2, self.y // 2)
        self.text = text
        self.active: bool = False

    def render(self, screen: pygame.Surface, button_tex:pygame.surface.Surface, font: pygame.font.Font) -> None:
        color = "white"
        if self.active:
            color = "green"
        text_surface = renderer.text(self.text, color, font)
        screen.blit(button_tex.subsurface((0,0), (32,10)), self.center)
        screen.blit(text_surface, self.center)
