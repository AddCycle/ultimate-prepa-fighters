# IP = "141.253.99.233"
IP = "localhost"
PORT = 5000

# window settings
SCREEN_WIDTH = 800  # temp
SCREEN_HEIGHT = 600  # temp

# game physics
GRAVITY = 1500
PLATFORM_HEIGHT = 64
GROUND_Y = SCREEN_HEIGHT - PLATFORM_HEIGHT
JUMP_SPEED = -700

# server frequency config consts
TICK_RATE = 144  # matching client FPS
SEND_RATE = 30  # initial was 30 maybe it's too much consider lowering the rate
TIMEOUT = 10  # 10sec timeout after no client ALIVE signal

FPS = TICK_RATE  # client fps
