import socket
import threading
import time


class NetworkClient:
    def __init__(self, ip, port) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = (ip, port)
        self.id = None
        self.buffer = ""
        self.players = {}
        self.lock = threading.Lock()
        self.running = True

    def start_listen(self):
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def listen_loop(self):
        while self.running:
            try:
                data, _ = self.client.recvfrom(4096)
                data = data.decode()
            except Exception as e:
                print("Recv error:", e)
                continue
            self.buffer += data
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                self.handle_line(line)

    # definitely to fix
    def handle_line(self, line):
        with self.lock:
            if self.my_id is None and line.startswith("ID:"):
                self.my_id = int(line.split(":")[1])
                print(f"[CLIENT] Player ID: {self.my_id}")
            else:
                new_state = {}
                for p in line.split(";"):
                    if not p:
                        continue
                    parts = p.split(",")
                    pid = int(parts[0])
                    x, y = float(parts[1]), float(parts[2])
                    score = int(parts[3])
                    new_state[pid] = {"pos": (x, y), "score": score}
                    if len(parts) == 8:
                        mx, my, mw, mh = map(float, parts[4:])
                        new_state[pid]["melee_rect"] = (mx, my, mw, mh)
                self.all_players = new_state

    def send(self, msg):
        self.client.sendto(msg.encode(), self.server_addr)

    def stop(self):
        self.running = False
        self.client.close()
