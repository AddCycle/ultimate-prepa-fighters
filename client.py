import socket
import threading
import pygame
import time
import sys
from game.settings import *
from game.player import Player
from ui import renderer
from ui import menu

# Client pygame init
pygame.init()
pygame.display.init()
pygame.font.init()

# window setup
icon_surface = pygame.image.load("icon.png")
pygame.display.set_icon(icon_surface)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ultimate Prepa Fighters | UPF")
X = screen.get_width()
Y = screen.get_height()

# text engine setup
font = pygame.font.Font("PressStart2P.ttf", 20)


def center_text_rect(surface: pygame.Rect, y: int) -> pygame.Rect:
    surface.center = (X // 2, y)
    return surface


# sprite loading
player_sprite = pygame.image.load("icon.png").convert_alpha()
player_sprite = pygame.transform.scale(player_sprite, (64, 64))

# bg loading
bg_img = pygame.image.load("bg.png").convert_alpha()

# main menu selection
choice = menu.show_main_menu(screen, player_sprite)
if choice == 0:
    pygame.quit()
    sys.exit()

char_choice = menu.show_character_menu(screen, player_sprite)
print(f"chosen char : {char_choice}")

# getting the client/server socket/address for connecting, sending & receiving data
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_addr = (IP, PORT)

# player id & commands buffer
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
            print("Recv error:", e)
            continue

        try:
            buffer += data.decode()
        except Exception as e:
            print("Decode error:", e)
            continue

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if my_id is None and line.startswith("ID:"):
                my_id = int(line.split(":")[1])
                print(f"[CLIENT] Player ID: {my_id}")

                if my_id is not None and my_id not in all_players:
                    all_players[my_id] = Player(my_id, client_side=True)

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
                            all_players[pid] = Player(
                                pid, client_side=True
                            )  # instantiate with server ID
                        p = all_players[pid]

                        # set server-authoritative values
                        p.x, p.y = x, y
                        p.score = score
                        p.current_anim = anim

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

game_text = font.render("Welcome to UPF", False, "white", "black")
gameTextRect = game_text.get_rect()
gameTextRect.center = (X // 2, Y // 2)

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

    # input handling
    send_msg = "STOP"
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        send_msg = "LEFT"
    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        send_msg = "RIGHT"
    if just_pressed_keys[pygame.K_SPACE] or just_pressed_keys[pygame.K_UP]:
        send_msg += "|JUMP"
    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
        send_msg += "|DOWN"
    if keys[pygame.K_ESCAPE]:
        running = False

    if just_pressed_keys[pygame.K_1]:
        debug = not debug
    if keys[pygame.K_c]:
        send_msg += "|MELEE"

    # sending local data to server
    if send_msg != last_send:
        client.sendto(send_msg.encode(), server_addr)
        last_send = send_msg

    # each 5 seconds sending a hearbeat signal to server knowing client haven't lost connection
    if time.time() - last_alive > 5:
        client.sendto("ALIVE".encode(), server_addr)
        last_alive = time.time()

    # screen rendering
    screen.fill("black")  # bg
    screen.blit(game_text, gameTextRect)  # text
    pygame.draw.rect(
        screen, "purple", (0, GROUND_Y + 64, screen.get_width(), 10)
    )  # ground

    # draw bg
    renderer.draw_background(screen, bg_img)

    # trying to interpolate other players positions (for smoothing lags)
    renderer.draw_players(screen, all_players, my_id, dt, debug, font)

    pygame.display.flip()  # updating screen
    dt = clock.tick(FPS) / 1000  # delta time sync

client.sendto(
    "QUIT".encode(), server_addr
)  # sending to server a quit signal for client disconnect
print("QUIT SIGNAL SENT")
pygame.quit()  # quitting pygame subsystems
client.close()  # closing socket connection
