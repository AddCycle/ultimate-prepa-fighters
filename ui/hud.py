import pygame

class Hud:
    def __init__(self, health:int) -> None:
        self.health = health
        self.heart = pygame.image.load("hearts.png").convert_alpha().subsurface((0,0), (16,16))
        self.heart = pygame.transform.scale(self.heart, (64,64))
    
    def render(self, screen: pygame.surface.Surface) -> None:
        for i in range(self.health):
            screen.blit(self.heart, (0, i * 64))