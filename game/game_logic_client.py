from game.player import Player

def handle_server_message(line: str, all_players: dict[int, Player], my_id: int | None, char_choice: int):
    if my_id is None and line.startswith("ID:"):
        pid = int(line.split(":")[1])
        print(f"[CLIENT] Player ID: {pid}")

        all_players[pid] = Player(pid)
        all_players[pid].char_choice = char_choice
        sprite_map = {0: "frog.png", 1: "qval.png", 2: "pass.png"}
        all_players[pid].load_sprites(sprite_map[char_choice])
        return pid # update client id


    if line.startswith("QUIT:"):
        removed_ids = line.split(":")[1].split(",")
        for rid in removed_ids:
            if rid:
                rid_int = int(rid)
                if rid_int in all_players:
                    del all_players[rid_int]
        return my_id

    for p in line.split(";"):
        if not p:
            continue

        parts = p.split(",")
        try:
            # received players data parsing
            pid = int(parts[0])
            x, y = float(parts[1]), float(parts[2])
            score = int(parts[3])
            anim = parts[4]

            # create or update Player object based on server data
            if pid not in all_players:
                all_players[pid] = Player(pid)  # instantiate with server ID
            update_player(all_players[pid], x, y, score, anim, char_choice, parts, my_id)
        except Exception as e:
            print("Parse error:", p, e)
    return my_id

def update_player(player: Player, x,y,score, anim, server_char_choice, parts, my_id):
    # set server-authoritative values
    player.x, player.y = x, y
    player.score = score

    # setting the new animation to the beginning
    if player.current_anim != anim:
        player.current_anim = anim
        player.anim_frame = 0
        player.anim_timer = 0.0

    if "_left" in anim:
        player.facing = "left"
    elif "_right" in anim:
        player.facing = "right"

    if len(parts) >= 6:
        server_char_choice = int(parts[5])
        if player.char_choice != server_char_choice:
            player.char_choice = server_char_choice
            if player.id == my_id:
                pass
            else:
                sprite_map = {
                    0: "frog.png",
                    1: "qval.png",
                    2: "pass.png",
                }
                player.load_sprites(sprite_map[server_char_choice])

    if len(parts) == 10:
        mx, my, mw, mh = map(float, parts[6:])
        player.melee_rect = (mx, my, mw, mh)
    else:
        player.melee_rect = None