# pong_server_v5.py
import socket
import threading
import json
import time
import math

HOST_IP = socket.gethostbyname(socket.gethostname())
PORT = 54321
WIDTH, HEIGHT = 640, 480
PADDLE_HEIGHT = 100
PADDLE_WIDTH = 10
BALL_RADIUS = 10

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST_IP, PORT))
clients = {}
client_addrs = {1: None, 2: None}
paddles = {1: HEIGHT//2, 2: HEIGHT//2}
ball = [WIDTH//2, HEIGHT//2]
ball_vel = [4, 4]
score = [0, 0]
game_started = False
waiting_for = 1
ENCODER = "utf-8"
BYTESIZE = 1024
TICK_RATE = 60

def reset_ball():
    global ball, ball_vel
    ball = [WIDTH//2, HEIGHT//2]
    ball_vel = [4, 4]

def reflect_ball_from_point(ball, ball_vel, point):
    dx = ball[0] - point[0]
    dy = ball[1] - point[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    nx = dx / dist
    ny = dy / dist
    dot = ball_vel[0] * nx + ball_vel[1] * ny
    ball_vel[0] -= 2 * dot * nx
    ball_vel[1] -= 2 * dot * ny
    overlap = BALL_RADIUS - dist
    if overlap > 0:
        ball[0] += nx * overlap
        ball[1] += ny * overlap

def circle_rect_collision(cx, cy, radius, rx, ry, rw, rh):
    closest_x = max(rx, min(cx, rx + rw))
    closest_y = max(ry, min(cy, ry + rh))
    distance_x = cx - closest_x
    distance_y = cy - closest_y
    return (distance_x**2 + distance_y**2) < (radius**2)

def handle_paddle_collision(ball, ball_vel, paddle_x, paddle_y):
    corners = [
        (paddle_x, paddle_y),
        (paddle_x + PADDLE_WIDTH, paddle_y),
        (paddle_x, paddle_y + PADDLE_HEIGHT),
        (paddle_x + PADDLE_WIDTH, paddle_y + PADDLE_HEIGHT)
    ]
    for cx, cy in corners:
        dist_sq = (ball[0] - cx) ** 2 + (ball[1] - cy) ** 2
        if dist_sq <= BALL_RADIUS ** 2:
            reflect_ball_from_point(ball, ball_vel, (cx, cy))
            ball_vel[0] *= 1.05
            ball_vel[1] *= 1.05
            return True
    if circle_rect_collision(ball[0], ball[1], BALL_RADIUS, paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT):
        offset = (ball[1] - (paddle_y + PADDLE_HEIGHT / 2)) / (PADDLE_HEIGHT / 2)
        ball_vel[1] += offset * 2
        ball_vel[0] *= -1
        ball_vel[0] *= 1.05
        ball_vel[1] *= 1.05
        return True
    return False

def update_ball():
    global ball, ball_vel, score, game_started, waiting_for
    ball[0] += ball_vel[0]
    ball[1] += ball_vel[1]
    if ball[1] - BALL_RADIUS <= 0 or ball[1] + BALL_RADIUS >= HEIGHT:
        ball_vel[1] *= -1

    p1x, p1y = 20, paddles[1]
    p2x, p2y = WIDTH - 30, paddles[2]
    if handle_paddle_collision(ball, ball_vel, p1x, p1y):
        ball[0] = p1x + PADDLE_WIDTH + BALL_RADIUS
    elif handle_paddle_collision(ball, ball_vel, p2x, p2y):
        ball[0] = p2x - BALL_RADIUS
    elif ball[0] - BALL_RADIUS <= 0:
        score[1] += 1
        reset_ball()
        game_started = False
        waiting_for = 1
    elif ball[0] + BALL_RADIUS >= WIDTH:
        score[0] += 1
        reset_ball()
        game_started = False
        waiting_for = 2

def handle_messages():
    global game_started, waiting_for
    while True:
        data, addr = server.recvfrom(BYTESIZE)
        msg = json.loads(data.decode(ENCODER))
        if addr not in clients:
            if 1 not in clients.values():
                clients[addr] = 1
                client_addrs[1] = addr
                server.sendto(json.dumps({"type": "welcome", "player": 1}).encode(ENCODER), addr)
            elif 2 not in clients.values():
                clients[addr] = 2
                client_addrs[2] = addr
                server.sendto(json.dumps({"type": "welcome", "player": 2}).encode(ENCODER), addr)
            else:
                continue
        player = clients[addr]
        if msg["type"] == "update":
            paddles[player] = msg["paddle_y"]
        elif msg["type"] == "start":
            if player == waiting_for and len(clients) == 2:
                game_started = True
                waiting_for = 0

def send_updates():
    while True:
        if game_started:
            update_ball()
        for player_num in [1, 2]:
            addr = client_addrs[player_num]
            if addr:
                payload = {
                    "type": "state",
                    "player": player_num,
                    "paddle_y": paddles[player_num],
                    "opponent_y": paddles[3 - player_num],
                    "ball": ball,
                    "score": score,
                    "waiting": waiting_for,
                    "players": len(clients)
                }
                server.sendto(json.dumps(payload).encode(ENCODER), addr)
        time.sleep(1 / TICK_RATE)

threading.Thread(target=handle_messages, daemon=True).start()
threading.Thread(target=send_updates, daemon=True).start()

while True:
    time.sleep(1)
