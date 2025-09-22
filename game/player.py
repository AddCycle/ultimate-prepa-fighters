import time
import random
from game.settings import *


class Player:
    def __init__(self, pid) -> None:
        self.id = pid
        self.x: float = 100
        self.y: float = GROUND_Y
        self.w = 32
        self.h = 64
        self.vx: float = 0
        self.vy: float = 0
        self.on_ground = True
        self.speed = random.randint(400, 600)
        self.facing = "right"
        self.score = 0
        self.last_seen = time.time()
        self.last_melee: float = -1
        self.melee_rect: tuple[float, float, float, float] | None = (0, 0, 0, 0)

    def alive(self):
        """Send an ALIVE Signal to server to prevent disconnect."""
        self.last_seen = time.time()

    def jump(self):
        """Perform a jump if on ground."""
        if self.on_ground:
            self.vy = JUMP_SPEED
            self.on_ground = False

    def update(self, dt):
        # gravity & ground (solid)
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # ground collision
        if self.y > GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True

        # horizontal bounds of the screen (clamself)
        if self.x < 0:
            self.x = 0
        elif self.x > SCREEN_WIDTH - self.w:
            self.x = SCREEN_WIDTH - self.w

        if time.time() - self.last_melee > 0.5:
            self.last_melee = -1
            self.melee_rect = None

    def handle_input(self, cmd: str):
        """Apply a single command from the client."""
        if cmd == "LEFT":
            self.vx = -self.speed
            self.facing = "left"
        elif cmd == "RIGHT":
            self.vx = self.speed
            self.facing = "right"
        elif cmd == "STOP":
            self.vx = 0
        elif cmd == "JUMP":
            self.jump()
        elif cmd == "DOWN":
            self.vy = -JUMP_SPEED
        elif cmd == "MELEE":
            self.perform_melee()

    def perform_melee(self):
        """Compute melee attack; sets self.melee_rect."""
        melee_width = 80
        melee_height = 64
        facing_right = self.facing == "right"
        hit_x = self.x + self.w if facing_right else self.x - melee_width
        hit_y = self.y
        self.melee_rect = (hit_x, hit_y, melee_width, melee_height)
        self.last_melee = time.time()
