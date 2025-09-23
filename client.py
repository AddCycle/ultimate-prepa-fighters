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

# main menu selection
choice = menu.show_main_menu(screen, player_sprite)
if choice == 0:
    pygame.quit()
    sys.exit()

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
            else:
                for p in line.split(";"):
                    if not p:
                        continue
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
                        if len(parts) == 9:
                            mx, my, mw, mh = map(float, parts[5:])
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
    send_msg = "STOP"
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        send_msg = "LEFT"
    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        send_msg = "RIGHT"
    if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
        send_msg += "|JUMP"
    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
        send_msg += "|DOWN"
    if keys[pygame.K_ESCAPE]:
        running = False

    # one-time pressed keys event
    just_pressed_keys = pygame.key.get_just_pressed()
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

    # trying to interpolate other players positions (for smoothing lags)
    renderer.draw_players(screen, all_players, player_sprite, my_id, dt, debug, font)

    pygame.display.flip()  # updating screen
    dt = clock.tick(FPS) / 1000  # delta time sync

client.sendto(
    "QUIT".encode(), server_addr
)  # sending to server a quit signal for client disconnect
pygame.quit()  # quitting pygame subsystems
client.close()  # closing socket connection
