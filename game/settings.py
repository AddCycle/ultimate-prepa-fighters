# IP = "141.253.99.233"
IP = "localhost"
PORT = 5000

# window settings
SCREEN_WIDTH = 1280  # temp
SCREEN_HEIGHT = 720  # temp

# game physics
GRAVITY = 1500
PIXEL_OFFSET = 6
PLATFORM_HEIGHT = 88 + 32 * 3 - PIXEL_OFFSET
GROUND_Y = SCREEN_HEIGHT - PLATFORM_HEIGHT
JUMP_SPEED = -700
ENTITY_RADIUS = 16
PLAYER_RADIUS = 24

# server frequency config consts
TICK_RATE = 144  # matching client FPS
SEND_RATE = 30  # initial was 30 maybe it's too much consider lowering the rate
TIMEOUT = 10  # 10sec timeout after no client ALIVE signal

# client
FPS = TICK_RATE  # client fps
MELEE_DURATION = 0.8
MELEE_DELAY_FRAMES = 7
HIT_STUN_DURATION = 0.8