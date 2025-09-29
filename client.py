import socket
import threading
import pygame
import time
import sys
from game.settings import *
from game.player import Player
from ui import renderer, menu, button
from game import inputs, game_logic_client

# Client pygame init
pygame.mixer.init()  # music
pygame.display.init()  # video
pygame.font.init()  # font
pygame.init()

# window setup
icon_surface = pygame.image.load("icon.png")
pygame.display.set_icon(icon_surface)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultimate Prepa Fighters | UPF")
X = screen.get_width()
Y = screen.get_height()

# text engine setup
font = pygame.font.Font("PressStart2P.ttf", 20)

# sprite loading
attack_surface_right = pygame.image.load("attack_sprite.png").convert_alpha()
attack_surface_left = pygame.transform.flip(
    attack_surface_right, True, False
).convert_alpha()

# icon loading
player_sprite = icon_surface.convert_alpha()
player_sprite = pygame.transform.scale(player_sprite, (64, 64))

# bg loading
bg_img = pygame.image.load("bg.png").convert_alpha()

# pause menu
pause_menu = menu.Menu(screen, "PAUSE")
pause_menu.addButton(button.Button("Resume"))
pause_menu.addButton(button.Button("Quit"))

# main menu selection
current_menu = menu.Menu(screen, "Ultimate Prepa Fighters")
current_menu.addButton(button.Button("PLAY"))
current_menu.addButton(button.Button("QUIT"))
choice = current_menu.display()
if choice == 1:
    pygame.quit()
    sys.exit()

# character menu selection
current_menu.title = "Choose your character"
current_menu.addButton(button.Button("FROG"))
current_menu.addButton(button.Button("QVAL"))
current_menu.addButton(button.Button("PASS"))
char_choice = current_menu.display()

# network udp client socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_addr = (IP, PORT)

# client player id & commands buffer
my_id = None
buffer = ""

# all players local cache for real-time rendering
all_players: dict[int, Player] = {}
prev_positions = {}

# dev mode (showing collisions...)
debug = False

# inital message to query a player id from server
client.sendto("HELLO".encode(), server_addr)

# after getting char_choice in client
client.sendto(f"CHAR:{char_choice}".encode(), server_addr)

# listen thread (listen all server data)
def listen_loop():
    global my_id, buffer, all_players
    while True:
        try:
            data, _ = client.recvfrom(4096)
        except Exception as e:
            print("listen_loop, Recv error:", e)
            continue

        try:
            buffer += data.decode()
        except Exception as e:
            print("[CLIENT]: listen_loop: Decode error:", e)
            continue

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if my_id is None and line.startswith("ID:"):
                my_id = int(line.split(":")[1])
                print(f"[CLIENT] Player ID: {my_id}")

                if my_id is not None and my_id not in all_players:
                    all_players[my_id] = Player(my_id)

                all_players[my_id].char_choice = char_choice
                sprite_map = {0: "frog.png", 1: "qval.png", 2: "pass.png"}
                all_players[my_id].load_sprites(sprite_map[char_choice])
                continue
            else:
                for p in line.split(";"):
                    if not p:
                        continue
                    if p.startswith("QUIT:"):
                        removed_ids = p.split(":")[1].split(",")
                        for rid in removed_ids:
                            if rid:
                                rid_int = int(rid)
                                if rid_int in all_players:
                                    del all_players[rid_int]
                        continue  # skip normal player updates for QUIT line
                    try:
                        # received players data parsing
                        parts = p.split(",")
                        pid = int(parts[0])
                        x, y = float(parts[1]), float(parts[2])
                        score = int(parts[3])
                        anim = parts[4]

                        # create or update Player object based on server data
                        if pid not in all_players:
                            all_players[pid] = Player(pid)  # instantiate with server ID
                        p = all_players[pid]

                        # set server-authoritative values
                        p.x, p.y = x, y
                        p.score = score

                        # setting the new animation to the beginning
                        if p.current_anim != anim:
                            p.current_anim = anim
                            p.anim_frame = 0
                            p.anim_timer = 0.0

                        if "_left" in anim:
                            p.facing = "left"
                        elif "_right" in anim:
                            p.facing = "right"

                        if len(parts) >= 6:
                            server_char_choice = int(parts[5])
                            if p.char_choice != server_char_choice:
                                p.char_choice = server_char_choice
                                if p.id == my_id:
                                    pass
                                else:
                                    sprite_map = {
                                        0: "frog.png",
                                        1: "qval.png",
                                        2: "pass.png",
                                    }
                                    p.load_sprites(sprite_map[server_char_choice])

                        if len(parts) == 10:
                            mx, my, mw, mh = map(float, parts[6:])
                            p.melee_rect = (mx, my, mw, mh)
                        else:
                            p.melee_rect = None
                    except Exception as e:
                        print("Parse error:", p, e)

# starting listening on another thread (performance optimizing)
threading.Thread(target=listen_loop, daemon=True).start()

# setting up runtime variables
clock = pygame.time.Clock()
running = True
last_send = ""
dt = 0  # delta_time
last_alive = time.time()  # for timeout/lost connnection


# each 5 seconds sending a hearbeat signal to server knowing client haven't lost connection
def heartbeat_loop():
    global last_alive, running
    while running:
        if time.time() - last_alive > 5:
            client.sendto("ALIVE".encode(), server_addr)
            last_alive = time.time()
        time.sleep(0.1)


# sending heartbeat (another thread)
threading.Thread(target=heartbeat_loop, daemon=True).start()


# game loop
while running:
    # when quitting window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # keydown event handling
    keys = pygame.key.get_pressed()
    # one-time pressed keys event
    just_pressed_keys = pygame.key.get_just_pressed()

    # command handling
    send_msg = inputs.handle_inputs(keys, just_pressed_keys)

    if keys[pygame.K_ESCAPE]:
        pause_choice = pause_menu.display()
        print(pause_choice)
        if pause_choice == 1:
            running = False

    if just_pressed_keys[pygame.K_1]:
        debug = not debug

    # sending local data to server
    if send_msg != last_send:
        client.sendto(send_msg.encode(), server_addr)
        last_send = send_msg

    # draw black
    screen.fill("black")
    # draw bg
    renderer.draw_background(screen, bg_img)

    # floor
    if debug:
        pygame.draw.rect(
            screen, "purple", (0, GROUND_Y + 32 * 3, screen.get_width(), 10)
        )  # ground

    # trying to interpolate other players positions (for smoothing lags)
    renderer.draw_players(
        screen,
        all_players,
        my_id,
        dt,
        attack_surface_right,
        attack_surface_left,
        debug,
        font,
    )

    pygame.display.flip()  # updating screen
    dt = clock.tick(FPS) / 1000  # delta time sync

client.sendto(
    "QUIT".encode(), server_addr
)  # sending to server a quit signal for client disconnect

pygame.quit()  # quitting pygame subsystems
client.close()  # closing socket connection
sys.exit()  # exiting the program