import pygame

# handling inputs returning commands
def handle_inputs(keys, just_pressed_keys, joystick: pygame.joystick.JoystickType | None, events: list[pygame.Event]) -> str:
    send_msg = "STOP"
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        send_msg = "LEFT"
    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        send_msg = "RIGHT"
    
    if joystick:
        x_axis = joystick.get_axis(0)  # usually left stick horizontal
        if x_axis < -0.3:
            send_msg = "LEFT"
        elif x_axis > 0.3:
            send_msg = "RIGHT"

        y_axis = joystick.get_axis(1)  # usually left stick vertical
        if y_axis > 0.3:
            send_msg += "|DOWN"
    
    if just_pressed_keys[pygame.K_SPACE] or just_pressed_keys[pygame.K_UP]:
        send_msg += "|JUMP"
    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
        send_msg += "|DOWN"
    if just_pressed_keys[pygame.K_c]:
        send_msg += "|MELEE"
    if just_pressed_keys[pygame.K_e]:
        send_msg += "|FIRE"
    
    for e in events:
        if e.type == pygame.JOYBUTTONDOWN:
            print(f"pressed button : {e.button}")
            if e.button == 0:  # A / Cross
                send_msg += "|JUMP"
            elif e.button == 1:  # B / Circle
                send_msg += "|MELEE"
            elif e.button == 2:  # X / Projectile
                send_msg += "|FIRE"
        elif e.type == pygame.JOYAXISMOTION:
            print("Axis", e.axis, e.value)
    
    return send_msg