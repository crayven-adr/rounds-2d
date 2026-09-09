import sys
import os
import math
import random
import json
import socket
import threading

import tkinter as tk
from tkinter import simpledialog

import pygame

PORT = 5555
WORLD_WIDTH = 2000
WORLD_HEIGHT = 1200

# Запрашиваем IP-адрес сервера у пользователя перед запуском графики
def get_server_ip():
    root = tk.Tk()
    root.withdraw() # Скрываем главное окно
    ip = simpledialog.askstring(
        "Вход в игру", 
        "Введите IP-адрес хоста:\n(127.0.0.1 если играете один или на этом же компьютере)", 
        initialvalue="127.0.0.1"
    )
    root.destroy()
    
    if not ip:
        sys.exit() # Закрываем игру, если нажали Отмена
    return ip.strip()

SERVER_IP = get_server_ip()

CARDS = {
    "BIG_BULLETS": {"name": "Гигантские пули", "desc": "+40% урона, +50% размер"},
    "FAST_SHOOT": {"name": "Быстрая стрельба", "desc": "+45% скор. стрельбы, -20% урон"},
    "HEALTH": {"name": "Танк", "desc": "+40% HP, +20% размер"},
    "SPEED": {"name": "Спринтер", "desc": "+25% скорость"},
    "SHOTGUN": {"name": "Дробовик", "desc": "4 пули за выстрел"},
    "VAMPIRISM": {"name": "Вампиризм", "desc": "+30% отсос HP"},
    "SHIELD": {"name": "Щит", "desc": "+40 плоского HP"},
    "HEAVY_BULLETS": {"name": "Тяжелые пули", "desc": "+80% урона, медленнее полёт"},
    "SNIPER": {"name": "Снайпер", "desc": "+60% скор. пули, +50% урон"},
    "LIFESTEAL": {"name": "Жажда крови", "desc": "+50% вампиризм, -15% HP"},
    "BERSERK": {"name": "Берсерк", "desc": "+60% урон, -25% HP"}
}

pygame.init()
pygame.font.init()

screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("ROUNDS 2D")

font_main = pygame.font.SysFont("Arial", 22, bold=True)
font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_card = pygame.font.SysFont("Arial", 16, bold=True)
font_hud = pygame.font.SysFont("Arial", 14, bold=True)

cam_x = WORLD_WIDTH / 2
cam_y = WORLD_HEIGHT / 2
zoom = 0.6

game_data = {
    "players": {},
    "bullets": [],
    "platforms": [],
    "state": "WAITING",
    "round": 1,
    "loser": None,
    "winner_game": None,
    "offered_cards": [],
    "events": []
}
my_id = None
particles = []

def update_camera_transform():
    global zoom, cam_x, cam_y
    cam_x = WORLD_WIDTH / 2
    cam_y = WORLD_HEIGHT / 2
    scale_w = screen_width / WORLD_WIDTH
    scale_h = screen_height / WORLD_HEIGHT
    zoom = min(scale_w, scale_h) * 0.95

def world_to_screen(wx, wy):
    sx = (wx - cam_x) * zoom + screen_width / 2
    sy = (wy - cam_y) * zoom + screen_height / 2
    return int(sx), int(sy)

def screen_to_world(sx, sy):
    wx = (sx - screen_width / 2) / zoom + cam_x
    wy = (sy - screen_height / 2) / zoom + cam_y
    return wx, wy

def world_to_screen_dist(dist):
    return max(1, int(dist * zoom))

def add_particles(x, y, color, count=8):
    for _ in range(count):
        particles.append({
            "x": x, "y": y,
            "vx": random.uniform(-6, 6),
            "vy": random.uniform(-6, 6),
            "life": random.randint(15, 30),
            "color": color
        })

def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)

def draw_particles(surface):
    for p in particles:
        sx, sy = world_to_screen(p["x"], p["y"])
        pygame.draw.circle(surface, p["color"], (sx, sy), max(1, int(3 * zoom)))

def receive_data(sock):
    global game_data, my_id
    buffer = ""
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip():
                    continue
                parsed = json.loads(line)
                if "my_id" in parsed:
                    my_id = str(parsed["my_id"])
                else:
                    game_data = parsed
                    for ev in game_data.get("events", []):
                        if isinstance(ev, dict):
                            if ev.get("type") in ("hit_wall", "hit_player"):
                                add_particles(ev.get("x", 0), ev.get("y", 0), ev.get("color", (220, 220, 220)))
                            elif ev.get("type") == "death":
                                add_particles(ev.get("x", 0), ev.get("y", 0), ev.get("color", (255, 50, 50)), count=35)
        except Exception:
            break

def main():
    global screen, screen_width, screen_height
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_IP, PORT))
    except Exception as e:
        # Выводим ошибку в графическое окно, чтобы игрок понял, что IP неверный
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("Ошибка", f"Не удалось подключиться к {SERVER_IP}\nПроверьте IP или запустите сервер.")
        root.destroy()
        return

    threading.Thread(target=receive_data, args=(sock,), daemon=True).start()
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        update_camera_transform()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                st = game_data.get("state")
                loser_id = str(game_data.get("loser")) if game_data.get("loser") is not None else None
                if st == "UPGRADE" and loser_id == my_id:
                    mx, my = event.pos
                    cards = game_data.get("offered_cards", [])
                    if isinstance(cards, list):
                        card_w, card_h = 220, 300
                        total_w = len(cards) * card_w + (len(cards) - 1) * 20
                        start_x = (screen_width - total_w) // 2
                        start_y = (screen_height - card_h) // 2

                        for i, card_id in enumerate(cards):
                            cx = start_x + i * (card_w + 20)
                            if cx <= mx <= cx + card_w and start_y <= my <= start_y + card_h:
                                try:
                                    sock.sendall((json.dumps({"card_choice": card_id}) + '\n').encode())
                                except:
                                    pass
                                break

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        wx, wy = screen_to_world(mouse_pos[0], mouse_pos[1])
        mouse_buttons = pygame.mouse.get_pressed()

        input_cmd = {
            "left": bool(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            "right": bool(keys[pygame.K_d] or keys[pygame.K_RIGHT]),
            "jump": bool(keys[pygame.K_w] or keys[pygame.K_SPACE] or keys[pygame.K_UP]),
            "shoot": bool(mouse_buttons[0]),
            "reload": bool(keys[pygame.K_r]),
            "mouse_x": wx,
            "mouse_y": wy
        }
        try:
            sock.sendall((json.dumps(input_cmd) + '\n').encode())
        except:
            pass

        update_particles()
        screen.fill((18, 20, 28))

        w_sx, w_sy = world_to_screen(0, 0)
        w_sw, w_sh = world_to_screen_dist(WORLD_WIDTH), world_to_screen_dist(WORLD_HEIGHT)
        pygame.draw.rect(screen, (30, 34, 45), (w_sx, w_sy, w_sw, w_sh))

        platforms = game_data.get("platforms", [])
        for px, py, pw, ph in platforms:
            sx, sy = world_to_screen(px, py)
            sw, sh = world_to_screen_dist(pw), world_to_screen_dist(ph)
            pygame.draw.rect(screen, (65, 75, 92), (sx, sy, sw, sh), border_radius=4)

        bullets_list = game_data.get("bullets", [])
        if isinstance(bullets_list, list):
            for b in bullets_list:
                if isinstance(b, dict):
                    sx, sy = world_to_screen(b.get("x", 0), b.get("y", 0))
                    sr = world_to_screen_dist(b.get("r", 6))
                    pygame.draw.circle(screen, (255, 230, 90), (sx, sy), max(3, sr))

        players_map = game_data.get("players", {})
        if isinstance(players_map, dict):
            for p_id_str, p in players_map.items():
                if not isinstance(p, dict) or not p.get("alive", True):
                    continue

                sx, sy = world_to_screen(p.get("x", 0), p.get("y", 0))
                sr = world_to_screen_dist(p.get("radius", 20))
                color = tuple(p.get("color", [255, 255, 255]))

                pygame.draw.circle(screen, color, (sx, sy), sr)
                pygame.draw.circle(screen, (255, 255, 255), (sx, sy), sr, 1)

                angle = p.get("aim_angle", 0)
                gun_len = sr + int(8 * zoom)
                gx = sx + int(math.cos(angle) * gun_len)
                gy = sy + int(math.sin(angle) * gun_len)
                pygame.draw.line(screen, (240, 240, 240), (sx, sy), (gx, gy), 2)

                max_hp = max(1, p.get("max_hp", 100))
                hp = p.get("hp", 100)
                hp_ratio = max(0.0, min(1.0, hp / max_hp))
                bar_w = int(36 * zoom) + 14
                bar_h = 4
                bar_x = sx - bar_w // 2
                bar_y = sy - sr - 12

                pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

                is_reloading = p.get("reloading", False)
                if is_reloading:
                    rel_txt = font_hud.render("R", True, (255, 100, 100))
                    screen.blit(rel_txt, (sx - rel_txt.get_width() // 2, bar_y - 12))
                else:
                    ammo = p.get("ammo", 6)
                    ammo_txt = font_hud.render(f"{ammo}", True, (240, 240, 240))
                    screen.blit(ammo_txt, (sx - ammo_txt.get_width() // 2, bar_y - 12))

        draw_particles(screen)

        if isinstance(players_map, dict):
            scores_str = " | ".join([f"P{pid}: {p.get('score', 0)}/7" for pid, p in players_map.items()])
            score_txt = font_main.render(scores_str, True, (255, 215, 0))
            screen.blit(score_txt, (20, 20))

        st = game_data.get("state", "WAITING")
        if st == "WAITING":
            txt = font_large.render("ОЖИДАНИЕ ИГРОКОВ (МИНИМУМ 2)...", True, (240, 240, 240))
            screen.blit(txt, (screen_width // 2 - txt.get_width() // 2, 40))
        elif st == "GAME_OVER":
            win_id = game_data.get("winner_game")
            txt = font_large.render(f"ИГРОК {win_id} ПОБЕДИЛ В ИГРЕ!", True, (50, 255, 50))
            screen.blit(txt, (screen_width // 2 - txt.get_width() // 2, screen_height // 2))
        else:
            txt = font_main.render(f"РАУНД {game_data.get('round', 1)}", True, (200, 200, 200))
            screen.blit(txt, (screen_width // 2 - txt.get_width() // 2, 10))

        if st == "UPGRADE":
            loser_id = str(game_data.get("loser")) if game_data.get("loser") is not None else None
            if loser_id == my_id:
                title = font_large.render("ВЫБЕРИТЕ КАРТУ", True, (255, 215, 0))
            else:
                title = font_large.render("ПРОИГРАВШИЙ ВЫБИРАЕТ КАРТУ...", True, (200, 200, 200))
            screen.blit(title, (screen_width // 2 - title.get_width() // 2, 50))

            if loser_id == my_id:
                cards = game_data.get("offered_cards", [])
                if isinstance(cards, list):
                    card_w, card_h = 220, 300
                    total_w = len(cards) * card_w + (len(cards) - 1) * 20
                    start_x = (screen_width - total_w) // 2
                    start_y = (screen_height - card_h) // 2

                    for i, card_id in enumerate(cards):
                        c_info = CARDS.get(card_id, {"name": card_id, "desc": ""})
                        cx = start_x + i * (card_w + 20)

                        pygame.draw.rect(screen, (35, 40, 55), (cx, start_y, card_w, card_h), border_radius=10)
                        pygame.draw.rect(screen, (255, 215, 0), (cx, start_y, card_w, card_h), 3, border_radius=10)

                        name_txt = font_card.render(c_info.get("name", card_id), True, (255, 255, 255))
                        desc_txt = font_card.render(c_info.get("desc", ""), True, (180, 190, 200))

                        screen.blit(name_txt, (cx + card_w // 2 - name_txt.get_width() // 2, start_y + 25))
                        screen.blit(desc_txt, (cx + card_w // 2 - desc_txt.get_width() // 2, start_y + 90))

        pygame.display.flip()

if __name__ == "__main__":
    main()