import time
from game.player import Player
from game.settings import *
from network.network import Server

# handle all commands <- client
def handle_command(players: dict[str, Player], player: Player, cmd):
    if cmd == "ALIVE":
        player.alive()
    elif cmd == "QUIT":
        pid = player.id
        player.quit = True
        print(f"[SERVER] Player {pid} quit")
    else:
        # player inputs
        player.handle_input(cmd)
        # check collisions with other players
        # FIXME : moved this from to constantly check hitboxes inside update_players
        # if (
        #     cmd == "MELEE" and player.melee_rect
        # ):  # only if player is attacking
        #     check_melee(players, player)

def update_players(players: dict[str, Player]):
    for player in players.values():
        if player.melee_rect:  # only if hitbox exists
            check_melee(players, player)

# apply melee results to players
def check_melee(players: dict[str, Player], player: Player):
    if not player.melee_rect:
        return

    mx, my, mw, mh = player.melee_rect # type: ignore
    now = time.time()
    for other in players.values():
        if other.id == player.id:
            continue  # skip self

        # skip if other is still in hit animation (invincible)
        if other.last_hit > 0 and now - other.last_hit < HIT_STUN_DURATION:
            continue

        ox, oy, ow, oh = other.x, other.y, other.w, other.h
        if (mx < ox + ow and mx + mw > ox and my < oy + oh and my + mh > oy):
            print(f"[SERVER] Player {player.id} hit Player {other.id}!")
            other.last_hit = now # start hit animation / invincibility
            # TODO : instead of a score, just decrease life points from other.health
            player.score += 1
            print("player score")

def cleanup_players(players: dict[str, Player], server: Server):
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
                server.socket.sendto(quit_msg.encode(), other_addr)
        del players[addr]

def broadcast_state(players: dict[str, Player], server: Server):
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
        server.socket.sendto((state + "\n").encode(), addr)