import socket
import threading
import json
import time

HOST = socket.gethostbyname(socket.gethostname())
PORT = 54321
WIDTH, HEIGHT = 640, 480

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
clients = {}
state = {
    "paddles": {1: HEIGHT//2, 2: HEIGHT//2},
    "ball": [WIDTH//2, HEIGHT//2],
    "ball_vel": [4, 4]
}

def update():
    while True:
        if len(clients) == 2:
            state["ball"][0] += state["ball_vel"][0]
            state["ball"][1] += state["ball_vel"][1]
            if state["ball"][1] <= 0 or state["ball"][1] >= HEIGHT:
                state["ball_vel"][1] *= -1
            for p, addr in clients.items():
                payload = {"player": p, **state}
                server.sendto(json.dumps(payload).encode(), addr)
        time.sleep(1/60)

threading.Thread(target=update, daemon=True).start()

while True:
    data, addr = server.recvfrom(1024)
    if addr not in clients.values() and len(clients) < 2:
        player_num = 1 if 1 not in clients else 2
        clients[player_num] = addr
        server.sendto(json.dumps({"player": player_num}).encode(), addr)
    else:
        player = [k for k, v in clients.items() if v == addr][0]
        state["paddles"][player] = int(data.decode())
