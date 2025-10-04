import threading
import time
import random
from game.settings import *
from game.player import Player
from game.entity import Entity
from network import network
from game import game_logic

# server socket udp
server = network.Server(PORT)
print(f"[SERVER] IP : {IP}")
print(f"[SERVER] Listening on UDP port {PORT}")

players: dict[str, Player] = {}  # dict of "addr":Player
next_id = 0

entities: dict[int, Entity] = {}
next_entity_id = 1000  # avoid collision with player ids & restart server if too many ids
max_entities = 100

last_spawn_time = 0
spawn_interval = 10  # seconds

lock = threading.Lock()

# recv client data function (thread)
def receive_loop():
    global next_id
    while True:
        try:
            data, addr = server.socket.recvfrom(1024)
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
                server.socket.sendto(f"ID:{pid}\n".encode(), addr)
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
                    game_logic.handle_command(players, player, cmd)

# handling client physics (thread)
def physics_loop():
    global next_entity_id, last_spawn_time, spawn_interval
    dt = 1 / TICK_RATE
    send_dt = 0
    while True:
        time.sleep(dt)
        with lock:
            for p in players.values():
                p.update(dt)
                p.current_anim = p.decide_animation()
            
            game_logic.cleanup_players(players, server)
            game_logic.update_players(players) # for collisions

            # broadcasting data to each player the everyone state
            send_dt += dt
            if send_dt >= 1 / SEND_RATE:
                game_logic.broadcast_state(players, server, entities)
                send_dt = 0
            
            # entities (test) FIXME
            now = time.time()
            if now - last_spawn_time >= spawn_interval and len(entities) < max_entities:
                x = random.randint(100, 700)
                y = random.randint(100, 400)
                e = Entity(next_entity_id, x, y, "orb")
                entities[e.id] = e
                next_entity_id += 1
                last_spawn_time = now
                print(f"[SERVER] Spawned entity {e.id} at ({x}, {y})")


# handling each on separate thread (optimization)
threading.Thread(target=receive_loop, daemon=True).start()
threading.Thread(target=physics_loop, daemon=True).start()

print("[SERVER] Running...")
while True:
    time.sleep(1)  # keeps the main thread alive waiting