import socket

class Server:
    def __init__(self, port:int) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        self.socket.bind(("0.0.0.0", port))  # accepting all ips on PORT using UDP protocol