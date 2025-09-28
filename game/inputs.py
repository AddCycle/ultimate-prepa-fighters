import pygame


# handling inputs returning commands
def handle_inputs(keys, just_pressed_keys) -> str:
    send_msg = "STOP"
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        send_msg = "LEFT"
    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        send_msg = "RIGHT"
    if just_pressed_keys[pygame.K_SPACE] or just_pressed_keys[pygame.K_UP]:
        send_msg += "|JUMP"
    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
        send_msg += "|DOWN"
    if just_pressed_keys[pygame.K_c]:
        send_msg += "|MELEE"

    return send_msg
