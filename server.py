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
                                 'w': 32, 'h': 64,
                                 'vx': 0, 'vy': 0, 'on_ground': True,
                                 'speed': rand.randint(400, 600),
                                 'last_seen': time.time(),
                                 'facing': "right",
                                 'score': 0}
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
                    player['facing'] = "left"
                elif cmd == "RIGHT":
                    player['vx'] = player['speed']
                    player['facing'] = "right"
                elif cmd == "STOP":
                    player['vx'] = 0
                elif cmd == "JUMP" and player['on_ground']: # jump
                    player['vy'] = JUMP_SPEED
                    player['on_ground'] = False
                elif cmd == "MELEE": # melee attack
                    attacker = player
                    # define hit area in front of attacker
                    melee_width = 80
                    melee_height = 64
                    facing_right = attacker.get('facing', 'right') == 'right'
                    if facing_right:
                      hit_x = attacker['x'] + attacker['w']
                    else:
                      hit_x = attacker['x'] - melee_width
                    hit_y = attacker['y']
                    hit_rect = (hit_x, hit_y, melee_width, melee_height)
    
                    # check collisions with other players
                    for other_addr, other in players.items():
                      if other_addr == addr:
                        continue  # skip self
                      ox, oy, ow, oh = other['x'], other['y'], other['w'], other['h']
                      # simple AABB collision
                      if (hit_rect[0] < ox + ow and hit_rect[0] + hit_rect[2] > ox and
                        hit_rect[1] < oy + oh and hit_rect[1] + hit_rect[3] > oy):
                          print(f"[SERVER] Player {attacker['id']} hit Player {other['id']}!")
                          other['last_hit'] = time.time()  # optional, store hit info for debug
                          attacker['score'] += 1 # incrementing the attacker score
                    # store attack info for rendering debug
                    attacker['last_melee'] = time.time()
                    attacker['melee_rect'] = hit_rect
                    print(f"player {player['id']} attacking")
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

                if 'last_melee' in p and time.time() - p['last_melee'] > 0.5:
                  del p['last_melee']
                  del p['melee_rect']
            
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

                state_parts = []
                for p in players.values():
                  part = f"{p['id']},{p['x']},{p['y']},{p['score']}"
                  if 'melee_rect' in p:
                    mx, my, mw, mh = p['melee_rect']
                    part += f",{mx},{my},{mw},{mh}"
                  state_parts.append(part)
                state = ";".join(state_parts)

                for addr in players.keys():
                    server.sendto((state + "\n").encode(), addr)
                send_dt = 0

# handling each on separate thread (optimization)
threading.Thread(target=receive_loop, daemon=True).start()
threading.Thread(target=physics_loop, daemon=True).start()

print("[SERVER] Running...")
while True:
    time.sleep(1) # keeps the main thread alive waiting