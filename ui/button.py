import pygame
import ui.renderer as renderer

class Button:
    def __init__(self, text: str, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y
        self.center = (self.x // 2, self.y // 2)
        self.text = text
        self.scale = 6
        self.width = 32*self.scale
        self.height = 10*self.scale
        self.active: bool = False

    def is_hovered(self, mouse_pos):
        mx, my = mouse_pos
        cx, cy = self.center
        left = cx - self.width // 2
        top = cy - self.height // 2
        return left <= mx <= left + self.width and top <= my <= top + self.height

    def render(self, screen: pygame.Surface, scale:int, button_tex:pygame.surface.Surface, font: pygame.font.Font) -> None:
        color = "white"
        if self.active:
            color = "green"
            screen.blit(button_tex.subsurface((0,20*scale), (32*scale,10*scale)), (self.center[0] - 32*scale // 4, self.center[1] - 10*scale // 4))
        else:
            screen.blit(button_tex.subsurface((0,0), (32*scale,10*scale)), (self.center[0] - 32*scale // 4, self.center[1] - 10*scale // 4))
        text_surface = renderer.text(self.text, color, font)
        screen.blit(text_surface, self.center)