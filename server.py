import socket
import threading
import time
import random as rand
from game.settings import *
from game.player import Player


# getting server socket
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(("0.0.0.0", PORT))  # accepting all ips on PORT using UDP protocol
print(f"[SERVER] Listening on UDP port {PORT}")

players: dict[str, Player] = {}  # dict of "addr":Player
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
                players[addr] = Player(pid)
                # sending player ID immediately after HELLO
                server.sendto(f"ID:{pid}\n".encode(), addr)
                print(f"[SERVER] New player {pid} from {addr}")
                print(f"[SERVER] player : {players[addr]}")

            player = players[addr]
            for cmd in data.split("|"):
                if cmd == "ALIVE":
                    player.alive()
                elif cmd == "QUIT":
                    pid = player.id
                    print(f"[SERVER] Player {pid} quit")
                    del players[addr]
                    continue
                else:
                    player.handle_input(cmd)
                    # check collisions with other players
            if player.melee_rect:  # only if player is attacking
                mx, my, mw, mh = player.melee_rect
                for other_addr, other in players.items():
                    if other_addr == addr:
                        continue
                    ox, oy, ow, oh = other.x, other.y, other.w, other.h
                    if mx < ox + ow and mx + mw > ox and my < oy + oh and my + mh > oy:
                        print(f"[SERVER] Player {player.id} hit Player {other.id}!")
                        other.last_melee = time.time()  # optional
                        player.score += 1


# handling client physics (thread)
def physics_loop():
    dt = 1 / TICK_RATE
    send_dt = 0
    while True:
        time.sleep(dt)
        with lock:
            for p in players.values():
                p.update(dt)
            # handling client timeout (TODO : move this part)
            now = time.time()
            disconnected = [
                addr for addr, p in players.items() if now - p.last_seen > TIMEOUT
            ]
            for addr in disconnected:
                pid = players[addr].id
                print(f"[SERVER] Removing inactive player {pid}")
                del players[addr]

            # broadcasting data to each player the everyone state
            send_dt += dt
            if send_dt >= 1 / SEND_RATE:

                state_parts = []
                for p in players.values():
                    part = f"{p.id},{p.x},{p.y},{p.score}"
                    if p.melee_rect:
                        mx, my, mw, mh = p.melee_rect
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
    time.sleep(1)  # keeps the main thread alive waiting
