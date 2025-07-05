import socket
import threading
import json
import pygame

SERVER_IP = input("Podaj adres IP serwera: ")
PORT = 54321
WIDTH, HEIGHT = 640, 480

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("", 0))

pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

paddle_y = HEIGHT // 2
state = None
player = None

def receive():
    global state, player
    while True:
        data, _ = client.recvfrom(1024)
        msg = json.loads(data.decode())
        if "player" in msg and "paddles" not in msg:
            player = msg["player"]
            print("Jesteś graczem", player)
        else:
            state = msg

threading.Thread(target=receive, daemon=True).start()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        paddle_y -= 5
    if keys[pygame.K_DOWN]:
        paddle_y += 5
    paddle_y = max(0, min(HEIGHT-100, paddle_y))
    if player:
        client.sendto(str(paddle_y).encode(), (SERVER_IP, PORT))

    win.fill((0,0,0))
    if not state:
        font = pygame.font.SysFont(None, 36)
        txt = "Oczekiwanie na drugiego gracza..." if player else "Czekam na rejestrację..."
        win.blit(font.render(txt, True, (255,255,255)), (100, HEIGHT//2))
    else:
        pygame.draw.rect(win, (255,255,255), (20, state["paddles"][1], 10, 100))
        pygame.draw.rect(win, (255,255,255), (WIDTH-30, state["paddles"][2], 10, 100))
        pygame.draw.circle(win, (255,0,0), (int(state["ball"][0]), int(state["ball"][1])), 10)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client.close()
