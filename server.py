import socket
import threading
import json
import time

HOST = socket.gethostbyname(socket.gethostname())
PORT = 54321
WIDTH, HEIGHT = 640, 480

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
clients = []

state = {"paddles": [HEIGHT//2, HEIGHT//2], "ball": [WIDTH//2, HEIGHT//2], "ball_vel": [4, 4]}

def update():
    while True:
        state["ball"][0] += state["ball_vel"][0]
        state["ball"][1] += state["ball_vel"][1]
        if state["ball"][1] <= 0 or state["ball"][1] >= HEIGHT:
            state["ball_vel"][1] *= -1
        for c in clients:
            server.sendto(json.dumps(state).encode(), c)
        time.sleep(1/60)

threading.Thread(target=update, daemon=True).start()

while True:
    data, addr = server.recvfrom(1024)
    if addr not in clients:
        clients.append(addr)
    paddle_y = int(data.decode())
    idx = clients.index(addr)
    state["paddles"][idx] = paddle_y
