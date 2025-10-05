import pygame
import socket
from game.player import Player
from game.entity import Entity
from game import inputs
from ui import renderer,menu,hud
from game.settings import *

class GameClient:
    def __init__(self, screen:pygame.surface.Surface, server_addr, char_choice, pause_menu, id) -> None:
        self.my_id = id
        self.screen = screen
        self.server_addr = server_addr
        self.char_choice = char_choice
        self.running = True
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.last_send = ""
        self.debug = False
        self.font = pygame.Font("PressStart2P.ttf")
        self.pause_menu: menu.Menu = pause_menu
        self.hud: hud.Hud = hud.Hud(HEALTH)
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print("[INFO] Joystick connected:", self.joystick.get_name())
        else:
            self.joystick = None
            print("[INFO] No joystick detected.")
    
    def handle_events(self, events: list[pygame.Event]):
        # when quitting window
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self, all_players: dict[int, Player], client: socket.socket, events: list[pygame.Event]):
        # hotplug for joysticks
        for e in events:
            if e.type == pygame.JOYDEVICEADDED:
                self.joystick = pygame.joystick.Joystick(e.device_index)
                self.joystick.init()
                print("Joystick added:", self.joystick.get_name())

            elif e.type == pygame.JOYDEVICEREMOVED:
                print("Joystick removed.")
                self.joystick = None

        # keydown event handling
        keys = pygame.key.get_pressed()
        
        # one-time pressed keys event
        just_pressed_keys = pygame.key.get_just_pressed()

        # command handling
        send_msg = inputs.handle_inputs(keys, just_pressed_keys, self.joystick, events)
        # sending local data to server
        if send_msg != self.last_send:
            client.sendto(send_msg.encode(), self.server_addr)
            self.last_send = send_msg

        if keys[pygame.K_ESCAPE]:
            pause_choice = self.pause_menu.display()
            if pause_choice == 1:
                self.running = False

        if just_pressed_keys[pygame.K_1]:
            self.debug = not self.debug
    
    def render(self, all_players, all_entities, bg_img, attack_surface_right, attack_surface_left, arrow_sprite):
        # draw black
        self.screen.fill("black")
        # draw bg
        renderer.draw_background(self.screen, bg_img)

        # floor
        if self.debug:
            pygame.draw.rect(
                self.screen, "purple", (0, GROUND_Y + 32 * 3, self.screen.get_width(), 10)
            )  # ground

        # trying to interpolate other players positions (for smoothing lags)
        renderer.draw_players(
            self.screen,
            all_players,
            self.my_id,
            self.dt,
            attack_surface_right,
            attack_surface_left,
            arrow_sprite,
            self.debug,
            self.font,
        )

        # draw entities
        for e in all_entities.values():
            color = "yellow" if e.type_name == "orb" else "orange"
            pygame.draw.circle(self.screen, color, (int(e.x), int(e.y)), 10)

        # hud
        self.hud.render(self.screen)

        pygame.display.flip()  # updating screen
    
    def run(self, all_players: dict[int, Player], all_entities: dict[int, Entity], client:socket.socket, bg_img, attack_surface_right, attack_surface_left, arrow_sprite):
        while self.running:
            events = pygame.event.get()
            # window quit
            self.handle_events(events)

            self.update(all_players, client, events)

            # rendering
            self.render(all_players, all_entities, bg_img, attack_surface_right, attack_surface_left, arrow_sprite)

            self.dt = self.clock.tick(FPS) / 1000

def handle_server_message(line: str, all_players: dict[int, Player], all_entities: dict[int, Entity], my_id: int | None, char_choice: int):
    if my_id is None and line.startswith("ID:"):
        pid = int(line.split(":")[1])
        print(f"[CLIENT] Player ID: {pid}")

        all_players[pid] = Player(pid)
        all_players[pid].char_choice = char_choice
        sprite_map = {0: "frog.png", 1: "qval.png", 2: "pass.png"}
        all_players[pid].load_sprites(sprite_map[char_choice])
        return pid # update client id


    if line.startswith("QUIT:"):
        removed_ids = line.split(":")[1].split(",")
        for rid in removed_ids:
            if rid:
                rid_int = int(rid)
                if rid_int in all_players:
                    del all_players[rid_int]
        return my_id

    if line.startswith("KILL:"):
        reid = int(line.split(":")[1])
        if reid in all_entities:
            del all_entities[reid]
            print(f"[CLIENT] Entity {reid} removed")

    if line.startswith("SCORE:"):
        pl, sc = line.split(":")[1].split(",")
        if pl in all_players:
            all_players[int(pl)].score = int(sc)
            print(f"[CLIENT] Score update for player {int(pl)}...")

    for p in line.split(";"):
        if not p:
            continue

        parts = p.split(",")
        try:
            if (parts[0] == "P"):
                # received players data parsing
                pid = int(parts[1])
                x, y = float(parts[2]), float(parts[3])
                score = int(parts[4])
                anim = parts[5]

                # create or update Player object based on server data
                if pid not in all_players:
                    all_players[pid] = Player(pid)  # instantiate with server ID
                update_player(all_players[pid], x, y, score, anim, char_choice, parts, my_id)
            elif (parts[0] == "E"):
                eid = int(parts[1])
                if eid not in all_entities:
                    all_entities[eid] = Entity.deserialize(parts)
                else:
                    e = all_entities[eid]
                    e.x = float(parts[2])
                    e.y = float(parts[3])
                    e.type_name = parts[4]
                    e.vx = int(parts[5])
                    e.vy = int(parts[6])
        except Exception as e:
            print("Parse error:", p, e)
    return my_id

def update_player(player: Player, x,y,score, anim, server_char_choice, parts, my_id):
    # set server-authoritative values
    player.x, player.y = x, y
    player.score = score

    # setting the new animation to the beginning
    if player.current_anim != anim:
        player.current_anim = anim
        player.anim_frame = 0
        player.anim_timer = 0.0

    if "_left" in anim:
        player.facing = "left"
    elif "_right" in anim:
        player.facing = "right"

    if len(parts) >= 7:
        server_char_choice = int(parts[6])
        if player.char_choice != server_char_choice:
            player.char_choice = server_char_choice
            if player.id == my_id:
                pass
            else:
                sprite_map = {
                    0: "frog.png",
                    1: "qval.png",
                    2: "pass.png",
                }
                player.load_sprites(sprite_map[server_char_choice])

    if len(parts) >= 11:
        mx, my, mw, mh = map(float, parts[7:])
        player.melee_rect = (mx, my, mw, mh)
    else:
        player.melee_rect = None