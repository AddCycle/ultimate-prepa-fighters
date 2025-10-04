import pygame


# handling inputs returning commands
def handle_inputs(keys, just_pressed_keys, joystick: pygame.joystick.JoystickType, events: list[pygame.Event]) -> str:
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

        y_axis = joystick.get_axis(1)  # usually left stick horizontal
        if y_axis > 0.3:
            send_msg += "|DOWN"
    
    if just_pressed_keys[pygame.K_SPACE] or just_pressed_keys[pygame.K_UP]:
        send_msg += "|JUMP"
    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
        send_msg += "|DOWN"
    if just_pressed_keys[pygame.K_c]:
        send_msg += "|MELEE"
    
    for e in events:
        if e.type == pygame.JOYBUTTONDOWN:
            if e.button == 0:  # A / Cross
                send_msg += "|JUMP"
            elif e.button == 1:  # B / Circle
                send_msg += "|MELEE"
        elif e.type == pygame.JOYAXISMOTION:
            print("Axis", e.axis, e.value)
    
    # for e in events:
    #     # if e.type == pygame.JOYAXISMOTION: print('Axis', e.axis, e.value)
    #     # elif e.type == pygame.JOYBUTTONDOWN: print('Button', e.button, 'down')
    #     # elif e.type == pygame.JOYBUTTONUP: print('Button', e.button, 'up')
    #     if e.type == pygame.JOYHATMOTION:
    #         hx, hy = e.value
    #         if hx == -1: send_msg = "LEFT"
    #         elif hx == 1: send_msg = "RIGHT"
    #         if hy == 1: send_msg += "|JUMP"
    #         elif hy == -1: send_msg += "|DOWN"

    return send_msg
