# pong_client_v5.py
import socket
import threading
import json
import pygame
import tkinter as tk
from tkinter import simpledialog

SERVER_PORT = 54321
ENCODER = "utf-8"
BYTESIZE = 1024

WIDTH, HEIGHT = 640, 480
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_RADIUS = 10

NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 0, 255)
BLACK = (0, 0, 0)

tk_root = tk.Tk()
tk_root.withdraw()
SERVER_IP = simpledialog.askstring("Połączenie z serwerem", "Podaj adres IP serwera:")
if not SERVER_IP:
    print("Nie podano adresu IP – wychodzę.")
    exit()

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(1.0)
client.bind(("", 0))
server_addr = (SERVER_IP, SERVER_PORT)

try:
    client.sendto(json.dumps({"type": "connect"}).encode(ENCODER), server_addr)
    data, _ = client.recvfrom(BYTESIZE)
    welcome = json.loads(data.decode(ENCODER))
    player = welcome["player"]
except socket.timeout:
    print("Brak odpowiedzi od serwera. Zamykanie klienta.")
    exit()

pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON UDP PONG")
clock = pygame.time.Clock()

my_paddle_y = HEIGHT // 2
opponent_y = HEIGHT // 2
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_trail = []
score = [0, 0]
waiting = 1
players_connected = 1
running = True

def draw_glow_rect(surface, color, rect, glow_radius=4):
    glow_color = [min(255, c + 100) for c in color]
    for i in range(glow_radius, 0, -1):
        pygame.draw.rect(surface, glow_color, rect.inflate(i * 2, i * 2), border_radius=4)
    pygame.draw.rect(surface, color, rect)

def draw_glow_circle(surface, color, pos, radius, glow_radius=4):
    glow_color = [min(255, c + 100) for c in color]
    for i in range(glow_radius, 0, -1):
        pygame.draw.circle(surface, glow_color, pos, radius + i)
    pygame.draw.circle(surface, color, pos, radius)

def send_position():
    msg = {"type": "update", "paddle_y": my_paddle_y}
    client.sendto(json.dumps(msg).encode(ENCODER), server_addr)

def send_start():
    msg = {"type": "start"}
    client.sendto(json.dumps(msg).encode(ENCODER), server_addr)

def receive_loop():
    global opponent_y, ball_pos, score, waiting, players_connected
    while running:
        try:
            data, _ = client.recvfrom(BYTESIZE)
            msg = json.loads(data.decode(ENCODER))
            if msg["type"] == "state":
                if msg["player"] == player:
                    opponent_y = msg["opponent_y"]
                    ball_pos[:] = msg["ball"]
                    score[:] = msg["score"]
                    waiting = msg.get("waiting", 0)
                    players_connected = msg.get("players", 1)
        except:
            pass

threading.Thread(target=receive_loop, daemon=True).start()

while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if waiting == player:
                send_start()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        my_paddle_y -= 5
    if keys[pygame.K_DOWN]:
        my_paddle_y += 5
    my_paddle_y = max(0, min(HEIGHT - PADDLE_HEIGHT, my_paddle_y))
    send_position()

    win.fill(BLACK)
    for y in range(HEIGHT):
        fade = int(20 + (y / HEIGHT) * 30)
        pygame.draw.line(win, (fade, fade, fade + 10), (0, y), (WIDTH, y))

    ball_trail.append(tuple(ball_pos))
    if len(ball_trail) > 10:
        ball_trail.pop(0)
    for i, pos in enumerate(ball_trail):
        alpha = int(255 * (i + 1) / len(ball_trail))
        radius = int(BALL_RADIUS * (i + 1) / len(ball_trail))
        color = (NEON_PINK[0], NEON_PINK[1], NEON_PINK[2], alpha)
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (int(pos[0]), int(pos[1])), radius)
        win.blit(s, (0, 0))

    my_x = 20 if player == 1 else WIDTH - 30
    opp_x = WIDTH - 30 if player == 1 else 20
    draw_glow_rect(win, NEON_BLUE, pygame.Rect(my_x, my_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
    draw_glow_rect(win, NEON_PINK, pygame.Rect(opp_x, opponent_y, PADDLE_WIDTH, PADDLE_HEIGHT))
    draw_glow_circle(win, NEON_PINK, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

    font = pygame.font.SysFont("Courier New", 36, bold=True)
    score_text = font.render(f"{score[0]} : {score[1]}", True, NEON_BLUE)
    win.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))

    if players_connected < 2:
        msg = "Oczekiwanie na gracza nr 2..."
    elif waiting == player:
        msg = "Naciśnij ENTER, by rozpocząć"
    else:
        msg = ""
    if msg:
        txt_surf = pygame.font.SysFont("Courier New", 24, bold=True).render(msg, True, NEON_PINK)
        win.blit(txt_surf, (WIDTH // 2 - txt_surf.get_width() // 2, 60))

    pygame.display.flip()

pygame.quit()
client.close()
