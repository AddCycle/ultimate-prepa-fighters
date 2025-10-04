class Entity:
    def __init__(self, eid: int, x: float = 0, y: float = 0, type_name="generic"):
        self.id = eid
        self.x = x
        self.y = y
        self.type_name = type_name
        self.alive = True

    def update(self, dt: float):
        pass  # later for movement or lifetime

    def serialize(self):
        return f"E,{self.id},{self.x},{self.y},{self.type_name}"

    @staticmethod
    def deserialize(parts):
        # parts: ["E", id, x, y, type]
        eid = int(parts[1])
        x = float(parts[2])
        y = float(parts[3])
        type_name = parts[4]
        return Entity(eid, x, y, type_name)