import socket
import threading
import pygame
import time
import sys
from game.settings import *

# Client pygame init
pygame.init()
pygame.display.init()
pygame.font.init()

# window setup
icon_surface = pygame.image.load("icon.png")
pygame.display.set_icon(icon_surface)
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Ultimate Prepa Fighters | UPF")
X = screen.get_width()
Y = screen.get_height()

# text engine setup
font = pygame.font.Font("PressStart2P.ttf", 20)


def center_text_rect(surface: pygame.Rect, y: int) -> pygame.Rect:
    surface.center = (X // 2, y)
    return surface


def text(text: str, color: str) -> pygame.Surface:
    return font.render(text, True, color, "black")


def render_text_at(
    surface: pygame.Surface, text: str, x: int, y: int, color: str, bg="black"
) -> None:
    sf = font.render(text, True, color, "black")
    rect = sf.get_rect()
    rect.center = (x, y)
    surface.blit(sf, rect)


quit_text = text("QUIT", "white")
connect_text = text("CONNECT", "white")

# sprite loading
player_sprite = pygame.image.load("icon.png").convert_alpha()
player_sprite = pygame.transform.scale(player_sprite, (64, 64))

selecting = True
choice = -1

# main MENU
while selecting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            break

    keys = pygame.key.get_just_pressed()
    if keys[pygame.K_DOWN]:
        choice = 0
        quit_text = text("QUIT", "green")
        connect_text = text("CONNECT", "white")
    elif keys[pygame.K_UP]:
        choice = 1
        quit_text = text("QUIT", "white")
        connect_text = text("CONNECT", "green")
    elif keys[pygame.K_SPACE]:
        selecting = False
        break

    render_text_at(screen, "Ultimate Prepa Fighters", X // 2, 50, "white")
    screen.blit(connect_text, center_text_rect(connect_text.get_rect(), Y // 2))
    screen.blit(quit_text, center_text_rect(quit_text.get_rect(), Y // 2 + 200))
    screen.blit(player_sprite, (X // 2, 100))
    pygame.display.flip()  # updating screen

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
all_players = {}
prev_positions = {}

# dev mode (showing collisions...)
debug = False

# inital message to query a player id
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
                new_state = {}
                for p in line.split(";"):
                    if not p:
                        continue
                    try:
                        # received players data parsing
                        parts = p.split(",")
                        pid = int(parts[0])
                        x, y = float(parts[1]), float(parts[2])
                        score = int(parts[3])
                        new_state[pid] = {"pos": (x, y), "score": score}
                        if len(parts) == 8:  # has melee rect
                            mx, my, mw, mh = map(float, parts[4:])
                            new_state[pid]["melee_rect"] = (mx, my, mw, mh)
                        # pid, x, y = p.split(",")
                        # new_state[int(pid)] = (float(x), float(y)) # recv new players positions (high frequency)
                    except Exception as e:
                        print("Parse error:", p, e)
                all_players = new_state  # updating cache


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
    pygame.draw.rect(screen, "purple", (0, 563, screen.get_width(), 500))  # ground

    # trying to interpolate other players positions (for smoothing lags)
    y_offset = 10
    for pid, data in all_players.items():
        x, y = data["pos"]

        if pid in prev_positions:
            px, py = prev_positions[pid]
            x = px + (x - px) * 0.4
            y = py + (y - py) * 0.4
        prev_positions[pid] = (x, y)

        color = "red" if pid == my_id else "blue"  # self in red, others in blue
        score_color = (
            "green" if pid == my_id else "white"
        )  # self in red, others in blue
        if debug:
            pygame.draw.rect(screen, color, (x, y, 32, 64))

        # render sprite (fix width call)
        screen.blit(player_sprite, (x - (player_sprite.get_width() // 4), y))
        render_text_at(
            screen, "Score: " + str(data["score"]), X // 2, y_offset, score_color
        )
        y_offset += 30

        # debug: melee rect
        if debug and "melee_rect" in data:
            hx, hy, hw, hh = data["melee_rect"]
            pygame.draw.rect(screen, color, (hx, hy, hw, hh), 2)

    pygame.display.flip()  # updating screen
    dt = clock.tick(FPS) / 1000  # delta time sync

client.sendto(
    "QUIT".encode(), server_addr
)  # sending to server a quit signal for client disconnect
pygame.quit()  # quitting pygame subsystems
client.close()  # closing socket connection
