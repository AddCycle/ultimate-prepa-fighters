import socket
import threading
import pygame
import time

IP = "localhost"
# IP = "141.253.99.233"
PORT = 5000
FPS = 144 # clamp

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
            line, buffer = buffer.split("\n",1)
            if my_id is None and line.startswith("ID:"):
                my_id = int(line.split(":")[1])
                print(f"[CLIENT] Player ID: {my_id}")
            else:
                new_state = {}
                for p in line.split(";"):
                    if not p: continue
                    try:
                        pid, x, y = p.split(",")
                        new_state[int(pid)] = (float(x), float(y)) # recv new players positions (high frequency)
                    except Exception as e:
                        print("Parse error:", p, e)
                all_players = new_state # updating cache

# starting listening on another thread (performance optimizing)
threading.Thread(target=listen_loop, daemon=True).start()

# Client pygame main loop
pygame.init()
pygame.font.init()

# window setup
icon_surface = pygame.image.load('icon.png')
pygame.display.set_icon(icon_surface)
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Ultimate Prepa Fighters | UPF")
X = screen.get_width()
Y = screen.get_height()

# text engine setup
font = pygame.font.Font('PressStart2P.ttf', 20)
text = font.render("Welcome to UPF", False, "white", "black")
textRect = text.get_rect()
textRect.center = (X // 2, Y // 2)

# sprite loading
player_sprite = pygame.image.load('icon.png').convert_alpha()
player_sprite = pygame.transform.scale(player_sprite, (64, 64))

# setting up runtime variables
clock = pygame.time.Clock()
running = True
last_send = ""
dt = 0 # delta_time
last_alive = time.time() # for timeout/lost connnection

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
    if keys[pygame.K_ESCAPE]:
        running = False
    
    # one-time pressed keys event
    just_pressed_keys = pygame.key.get_just_pressed()
    if just_pressed_keys[pygame.K_1]:
      debug = not debug

    # sending local data to server
    if send_msg != last_send:
        client.sendto(send_msg.encode(), server_addr)
        last_send = send_msg

    # each 5 seconds sending a hearbeat signal to server knowing client haven't lost connection
    if time.time() - last_alive > 5:
      client.sendto("ALIVE".encode(), server_addr)
      last_alive = time.time()

    # screen rendering
    screen.fill("black") # bg
    screen.blit(text, textRect) # text
    pygame.draw.rect(screen, "purple", (0, 563, screen.get_width(), 500)) # ground

    # trying to interpolate other players positions (for smoothing lags)
    for pid, (x, y) in all_players.items():
        if pid in prev_positions:
            px, py = prev_positions[pid]
            x = px + (x - px) * 0.4
            y = py + (y - py) * 0.4
        prev_positions[pid] = (x, y)
        color = "red" if pid == my_id else "blue" # self in red others in blue
        if debug:
          pygame.draw.rect(screen, "red", (x, y, 64, 64))
        screen.blit(player_sprite, (x,y))

    pygame.display.flip() # updating screen
    dt = clock.tick(FPS)/1000 # delta time sync

client.sendto("QUIT".encode(), server_addr) # sending to server a quit signal for client disconnect
pygame.quit() # quitting program
client.close() # closing socket connection