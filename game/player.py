import time
import random
import pygame
from game.settings import *


class Player:
    def __init__(self, pid, client_side=False) -> None:
        self.id = pid
        self.char_choice: int | None = None
        self.x: float = 100
        self.y: float = GROUND_Y
        self.scale = 3
        # temp for testing too much
        self.w = 32 * self.scale
        self.h = 32 * self.scale
        self.vx: float = 0
        self.vy: float = 0
        # track of jumps
        self.on_ground = True
        self.max_jumps = 5
        self.jump_count = 0

        self.speed = random.randint(400, 600)
        self.facing = "right"  # remembers last facing direction
        self.score = 0
        self.last_seen = time.time()
        self.last_melee: float = 0.0
        self.melee_rect: tuple[float, float, float, float] | None = None

        # animation state
        self.animations: dict[str, list[pygame.Surface]] = {}
        self.current_anim = "idle_right"
        self.anim_frame = 0
        self.anim_timer = 0.0

        # if client_side:
        #     self.load_sprites("qval.png")
        # quit signal
        self.quit = False

    def alive(self):
        """Send an ALIVE signal to server to prevent disconnect."""
        self.last_seen = time.time()
        print(f"Player {self.id} alive")

    def jump(self):
        """-- previously : Perform a jump if on ground.
        -- now : Perform a jump if allowed (supports double jump)."""
        if self.jump_count < self.max_jumps:
            self.vy = JUMP_SPEED
            self.on_ground = False
            self.jump_count += 1

    def update(self, dt):
        # gravity & motion
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # ground collision
        if self.y > GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
            self.jump_count = 0  # resetting jumps

        # horizontal bounds
        if self.x < 0:
            self.x = 0
        elif self.x > SCREEN_WIDTH - self.w:
            self.x = SCREEN_WIDTH - self.w

        # melee duration timeout
        if self.last_melee > 0 and time.time() - self.last_melee > MELEE_DURATION:
            self.last_melee = 0.0
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
        melee_width = self.w
        melee_height = self.h
        facing_right = self.facing == "right"
        hit_x = self.x + self.w if facing_right else self.x - melee_width
        hit_y = self.y
        self.melee_rect = (hit_x, hit_y, melee_width, melee_height)
        self.last_melee = time.time()

    def load_sprites(self, sheet_path="frog.png"):
        sheet = pygame.image.load(sheet_path).convert_alpha()
        frame_width, frame_height = 32, 32
        sheet_width, sheet_height = sheet.get_size()
        print(f"sheet size : {sheet.get_size()}")

        cols = sheet_width // frame_width  # 12
        rows = sheet_height // frame_height  # 8

        # Map each row to an animation name
        row_mapping = {
            0: "idle_right",
            1: "idle_left",
            2: "run_right",
            3: "run_left",
            4: "jump_right",
            5: "jump_left",
            6: "fall_right",
            7: "fall_left",
            8: "melee_right",
            9: "melee_left",
            10: "doublejump_right",
            11: "doublejump_left",
        }

        self.animations = {name: [] for name in row_mapping.values()}

        for row in range(rows):
            anim_name = row_mapping.get(row)
            if anim_name is None:
                continue

            for col in range(cols):
                x = col * frame_width
                y = row * frame_height
                rect = pygame.Rect(x, y, frame_width, frame_height)

                if rect.right <= sheet_width and rect.bottom <= sheet_height:
                    frame = sheet.subsurface(rect)
                    frame = pygame.transform.scale_by(frame, self.scale)
                    self.animations[anim_name].append(frame)

    def decide_animation(self):
        """Server-side: decides which animation should be active."""
        facing = self.facing  # use last known direction

        if self.last_melee > 0 and time.time() - self.last_melee < MELEE_DURATION:
            new_anim = f"melee_{facing}"
        elif self.vy < 0:
            if self.jump_count != 0 and self.jump_count % 2 == 0:
                new_anim = f"doublejump_{facing}"
            else:
                new_anim = f"jump_{facing}"
        elif self.vy > 0:
            new_anim = f"fall_{facing}"
        elif abs(self.vx) > 0:
            new_anim = f"run_{facing}"
        else:
            new_anim = f"idle_{facing}"

        # reset frame if animation changed
        if new_anim != self.current_anim:
            self.current_anim = new_anim
            self.anim_frame = 0
            self.anim_timer = 0.0

        return self.current_anim

    def get_current_frame(self):
        frames = self.animations.get(self.current_anim, [])
        if not frames:
            # nothing loaded: return a transparent dummy surface instead of crashing
            return pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        return frames[self.anim_frame % len(frames)]

    def step_animation(self, dt):
        """Client-side: advances frames for the current_anim decided by server."""
        frames = self.animations.get(self.current_anim, [])
        if not frames:
            return

        self.anim_timer += dt
        if self.anim_timer > 0.1:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % len(frames)
