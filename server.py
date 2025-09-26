import socket
import threading
import time
from game.settings import *
from game.player import Player

# server socket udp
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(("0.0.0.0", PORT))  # accepting all ips on PORT using UDP protocol
print(f"[SERVER] IP : {IP}")
print(f"[SERVER] Listening on UDP port {PORT}")

players: dict[str, Player] = {}  # dict of "addr":Player
next_id = 0
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

                # sending player id -> client
                server.sendto(f"ID:{pid}\n".encode(), addr)
                print(f"[SERVER] New player {pid} from {addr[0]}:{addr[1]}")

            player = players[addr]

            # receiving character choice <- client
            if data.startswith("CHAR:"):
                try:
                    choice = int(data.split(":")[1])
                    player.char_choice = choice
                    print(f"[SERVER] Player {player.id} chose character {choice}")
                except Exception as e:
                    print("Invalid CHAR message:", data, e)
            else:
                # handling messages <- client
                for cmd in data.split("|"):
                    if cmd == "ALIVE":
                        player.alive()
                    elif cmd == "QUIT":
                        pid = player.id
                        print(f"[SERVER] Player {pid} quit")
                        player.quit = True
                        continue
                    else:
                        # player inputs
                        player.handle_input(cmd)
                        # check collisions with other players
                        if (
                            cmd == "MELEE" and player.melee_rect
                        ):  # only if player is attacking
                            mx, my, mw, mh = player.melee_rect
                            for other_addr, other in players.items():
                                if other_addr == addr:
                                    continue
                                ox, oy, ow, oh = other.x, other.y, other.w, other.h
                                if (
                                    mx < ox + ow
                                    and mx + mw > ox
                                    and my < oy + oh
                                    and my + mh > oy
                                ):
                                    print(
                                        f"[SERVER] Player {player.id} hit Player {other.id}!"
                                    )
                                    # TODO : instead of a score, just decrease life points from other.health
                                    other.last_hit = time.time()  # hit animation
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
                p.current_anim = p.decide_animation()
            now = time.time()
            disconnected = [
                addr
                for addr, p in players.items()
                if now - p.last_seen > TIMEOUT or getattr(p, "quit", False)
            ]
            for addr in disconnected:
                pid = players[addr].id
                print(f"[SERVER] Removing inactive player {pid}")
                quit_msg = f"QUIT:{pid}\n"
                for other_addr in players.keys():
                    if other_addr != addr:
                        server.sendto(quit_msg.encode(), other_addr)
                del players[addr]

            # broadcasting data to each player the everyone state
            send_dt += dt
            if send_dt >= 1 / SEND_RATE:

                state_parts = []
                for p in players.values():
                    part = (
                        f"{p.id},{p.x},{p.y},{p.score},{p.current_anim},{p.char_choice}"
                    )
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
