import socket
import threading
import time
import random as rand

PORT = 5000

# game physics consts
GRAVITY = 1500
GROUND_Y = 500
JUMP_SPEED = -700
SCREEN_WIDTH = 800 # temp

# server frequency config consts
TICK_RATE = 144 # try to match client FPS
SEND_RATE = 30 # initial was 30 maybe it's too much consider lowering the rate
TIMEOUT = 10 # 10sec timeout after no client ALIVE signal

# getting server socket
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(("0.0.0.0", PORT)) # accepting all ips on PORT using UDP protocol
print(f"[SERVER] Listening on UDP port {PORT}")

players = {} # addr -> {'id','x','y','w','h','vx','vy','on_ground', 'last_seen'}
next_id = 1
lock = threading.Lock()

# recv client data function (thread)
def receive_loop():
    global next_id
    while True:
        try:
            data, addr = server.recvfrom(1024)
            data = data.decode().strip()
        except Exception as e:
            print("Recv error:", e)
            continue

        with lock:
            if addr not in players:
                pid = next_id
                next_id += 1
                players[addr] = {'id': pid, 'x': 100, 'y': GROUND_Y,
                                 'w': 64, 'h': 64,
                                 'vx': 0, 'vy': 0, 'on_ground': True,
                                 'speed': rand.randint(400, 600),
                                 'last_seen': time.time()}
                # sending player ID immediately after HELLO
                server.sendto(f"ID:{pid}\n".encode(), addr)
                print(f"[SERVER] New player {pid} from {addr}")
                print(f"[SERVER] player : {players[addr]}")

            player = players[addr]
            for cmd in data.split("|"):
                if cmd == "ALIVE":
                    player['last_seen'] = time.time()
                    print(f"[SERVER] Player {player['id']} alive")
                if cmd == "LEFT":
                    player['vx'] = -player['speed']
                elif cmd == "RIGHT":
                    player['vx'] = player['speed']
                elif cmd == "STOP":
                    player['vx'] = 0
                elif cmd == "JUMP" and player['on_ground']: # jump
                    player['vy'] = JUMP_SPEED
                    player['on_ground'] = False
                elif cmd == "QUIT": # client disconnect
                    pid = players[addr]['id']
                    print(f"[SERVER] Player {pid} quit")
                    del players[addr]
                    continue

# handling client physics (thread)
def physics_loop():
    dt = 1 / TICK_RATE
    send_dt = 0
    while True:
        time.sleep(dt)
        with lock:
            for p in players.values():

                # gravity & ground (solid)
                p['vy'] += GRAVITY * dt
                p['x'] += p['vx'] * dt
                p['y'] += p['vy'] * dt
                if p['y'] > GROUND_Y:
                    p['y'] = GROUND_Y
                    p['vy'] = 0
                    p['on_ground'] = True

                # horizontal bounds of the screen (clamp)
                if p['x'] < 0:
                  p['x'] = 0
                elif p['x'] > SCREEN_WIDTH - p['w']:
                  p['x'] = SCREEN_WIDTH - p['w']
            
            # handling client timeout (TODO : move this part)
            now = time.time()
            disconnected = [addr for addr, p in players.items() if now - p['last_seen'] > TIMEOUT]
            for addr in disconnected:
              pid = players[addr]['id']
              print(f"[SERVER] Removing inactive player {pid}")
              del players[addr]

            # broadcasting data to each player the everyone state
            send_dt += dt
            if send_dt >= 1 / SEND_RATE:
                state = ";".join(f"{p['id']},{p['x']},{p['y']}" for p in players.values())
                for addr in players.keys():
                    server.sendto((state + "\n").encode(), addr)
                send_dt = 0

# handling each on separate thread (optimization)
threading.Thread(target=receive_loop, daemon=True).start()
threading.Thread(target=physics_loop, daemon=True).start()

print("[SERVER] Running...")
while True:
    time.sleep(1) # keeps the main thread alive waiting