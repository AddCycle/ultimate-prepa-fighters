import time

class Entity:
    def __init__(self, eid: int, x: float = 0, y: float = 0, type_name="generic"):
        self.id = eid
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.type_name = type_name
        self.alive = True
        self.spawn_time = time.time()   # track creation time
        self.lifetime = 5.0             # seconds before despawn

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # gravity or slow down (optional)
        # self.vy += 200 * dt  # gravity-like effect

        # check lifetime
        if time.time() - self.spawn_time >= self.lifetime:
            self.alive = False
        age = time.time() - self.spawn_time
        if age > self.lifetime - 1.0:
            # mark fading stage (e.g. change type_name or color)
            self.type_name = "orb_fading"

    def serialize(self):
        return f"E,{self.id},{self.x},{self.y},{self.type_name},{self.vx},{self.vy}"

    @staticmethod
    def deserialize(parts):
        # parts: ["E", id, x, y, type]
        eid = int(parts[1])
        x = float(parts[2])
        y = float(parts[3])
        type_name = parts[4]
        e = Entity(eid, x, y, type_name)
        if len(parts) >= 7:
            e.vx = float(parts[5])
            e.vy = float(parts[6])
        return e