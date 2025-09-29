import socket
import threading
import pygame
import time
import sys
from game.settings import *
from game.player import Player
from ui import renderer, menu, button
from game import inputs, game_logic_client
from game.game_logic_client import GameClient

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

# setting up runtime variables
running = True
last_alive = time.time()  # for timeout/lost connnection

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
    global my_id, buffer, all_players, last_alive
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
            my_id = game_logic_client.handle_server_message(line, all_players, my_id, char_choice)

# starting listening on another thread (performance optimizing)
threading.Thread(target=listen_loop, daemon=True).start()

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

# GameClient instance
game = GameClient(screen, server_addr, char_choice, pause_menu)
game.run(all_players, my_id, client, bg_img, attack_surface_right, attack_surface_left) # game loop

client.sendto(
    "QUIT".encode(), server_addr
)  # sending to server a quit signal for client disconnect

pygame.quit()  # quitting pygame subsystems
client.close()  # closing socket connection
sys.exit()  # exiting the program