import sys
import os
import math
import random
import json
import socket
import threading

import tkinter as tk
from tkinter import simpledialog, messagebox

import pygame

PORT = 5555
WORLD_WIDTH = 1800
WORLD_HEIGHT = 1000

CARDS_DB = {
    "C1": {"name": "Шквал", "bullets": 4, "ammo": 5, "dmg": 0.3, "reload": 15},
    "C3": {"name": "Крупный калибр", "bullet_size": 2.0, "reload": 15},
    "C5": {"name": "Рикошетный хаос", "bounces": 2, "dmg": 1.25, "reload": 15},
    "C7": {"name": "Дробовик", "bullets": 4, "ammo": 5, "dmg": 0.4, "reload": 15},
    "C8": {"name": "Очередь", "bullets": 2, "ammo": 3, "dmg": 0.4, "reload": 15},
    "C9": {"name": "Тяжелый расчёт", "dmg": 2.0, "atk_spd": 0.4, "reload": 30},
    "C12": {"name": "Леденящие пули", "slow": 1.7, "reload": 15},
    "C13": {"name": "Мощный пробой", "dmg": 2.0, "ammo": -2, "reload": 30},
    "C16": {"name": "Защитник", "hp": 1.3, "block_cd": 0.7},
    "C22": {"name": "Разрывной снаряд", "atk_spd": 0.0, "reload": 15},
    "C23": {"name": "Сверхзвук", "bullet_speed": 3.5, "atk_spd": 0.5, "reload": 15},
    "C24": {"name": "Форсаж", "bullet_speed": 2.0, "reload_speed": 1.3},
    "C26": {"name": "Стеклянная пушка", "dmg": 2.0, "hp": 0.0, "reload": 15},
    "C27": {"name": "Ускоренный рост", "reload": 15},
    "C29": {"name": "Самонаведение", "dmg": 0.75, "atk_spd": 0.5, "reload": 15},
    "C30": {"name": "Титан", "hp": 1.8},
    "C32": {"name": "Пиявка", "vampirism": 0.75, "hp": 1.3},
    "C34": {"name": "Безумие", "bounces": 5, "dmg": 0.85, "reload": 30},
    "C36": {"name": "Паразит", "vampirism": 0.5, "hp": 1.25, "dmg": 1.25, "reload": 15},
    "C38": {"name": "Ядовитый залп", "dmg": 1.7, "reload_speed": 1.3, "bullets": -1},
    "C40": {"name": "Молниеносная перезарядка", "reload": -0.3},
    "C41": {"name": "Быстрый выстрел", "bullet_speed": 2.5, "reload": 15},
    "C46": {"name": "Точный рикошет", "bounces": 2, "atk_spd": 1.25, "reload": 15},
    "C48": {"name": "Мародер", "reload": 30},
    "C53": {"name": "Летящий скрытно", "reload": 15},
    "C54": {"name": "Пулеметный шторм", "atk_spd": 10.0, "ammo": 12, "dmg": 0.25, "reload": 15},
    "C56": {"name": "Стойкий стрелок", "hp": 1.4, "bullet_speed": 2.0, "reload": 15},
    "C59": {"name": "Тяжелый танк", "hp": 2.0, "atk_spd": 0.75, "reload": 30},
    "C60": {"name": "Умный рикошет", "bounces": 1, "dmg": 0.8, "reload": 15},
    "C61": {"name": "Жажда крови", "vampirism": 0.3},
    "C63": {"name": "Импульсный толчок", "reload": 15},
    "C64": {"name": "Часовой механизм", "dmg": 0.85, "reload": 15},
    "C66": {"name": "Трикстер", "bounces": 2, "dmg": 0.8, "reload": 30},
    "C67": {"name": "Накопление силы", "bullet_speed": 2.0, "dmg": 1.6, "atk_spd": 0.0, "reload": 30}
}

def get_server_ip():
    root = tk.Tk()
    root.withdraw()
    ip = simpledialog.askstring(
        "Вход в игру", 
        "Введите IP-адрес хоста:\n(127.0.0.1 если играете локально)", 
        initialvalue="127.0.0.1"
    )
    root.destroy()
    if not ip:
        sys.exit()
    return ip.strip()

SERVER_IP = get_server_ip()

pygame.init()
pygame.font.init()

screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("ROUNDS 2D - Physics & Halves Edition")

font_main = pygame.font.SysFont("Arial", 20, bold=True)
font_large = pygame.font.SysFont("Arial", 32, bold=True)
font_card = pygame.font.SysFont("Arial", 14, bold=True)
font_hud = pygame.font.SysFont("Arial", 12, bold=True)

cam_x = WORLD_WIDTH / 2
cam_y = WORLD_HEIGHT / 2
zoom = 0.7

game_data = {
    "players": {},
    "bullets": [],
    "platforms": [],
    "map_idx": 0,
    "state": "WAITING",
    "round": 1,
    "loser_ids": [],
    "winner_game": None,
    "offered_cards": [],
    "events": []
}
my_id = None
particles = []
selected_map_preview = 0

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
            "vx": random.uniform(-5, 5),
            "vy": random.uniform(-5, 5),
            "life": random.randint(15, 25),
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
                            if ev.get("type") in ("hit_wall", "bounce", "hit_player"):
                                add_particles(ev.get("x", 0), ev.get("y", 0), ev.get("color", (220, 220, 220)))
                            elif ev.get("type") == "death":
                                add_particles(ev.get("x", 0), ev.get("y", 0), ev.get("color", (255, 50, 50)), count=30)
        except Exception:
            break

def main():
    global screen, screen_width, screen_height, selected_map_preview
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_IP, PORT))
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", f"Не удалось подключиться к {SERVER_IP}:{PORT}\n{e}")
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

            elif event.type == pygame.MOUSEBUTTONDOWN:
                st = game_data.get("state")
                loser_ids = [str(lid) for lid in game_data.get("loser_ids", [])]
                
                if st == "UPGRADE" and my_id in loser_ids:
                    mx, my = event.pos
                    cards = game_data.get("offered_cards", [])
                    if isinstance(cards, list):
                        card_w, card_h = 220, 280
                        total_w = len(cards) * card_w + (len(cards) - 1) * 20
                        start_x = (screen_width - total_w) // 2
                        start_y = (screen_height - card_h) // 2 - 40

                        for i, card_id in enumerate(cards):
                            cx = start_x + i * (card_w + 20)
                            if cx <= mx <= cx + card_w and start_y <= my <= start_y + card_h:
                                try:
                                    payload = {"card_choice": card_id, "map_choice": selected_map_preview}
                                    sock.sendall((json.dumps(payload) + '\n').encode())
                                except:
                                    pass
                                break

                    map_box_y = start_y + card_h + 30
                    total_maps = 4
                    m_width_box = 90
                    m_start_x = (screen_width - (total_maps * (m_width_box + 10))) // 2
                    for m_i in range(total_maps):
                        mx_pos = m_start_x + m_i * (m_width_box + 10)
                        if mx_pos <= mx <= mx_pos + m_width_box and map_box_y <= my <= map_box_y + 35:
                            selected_map_preview = m_i

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
        screen.fill((15, 18, 25))

        w_sx, w_sy = world_to_screen(0, 0)
        w_sw, w_sh = world_to_screen_dist(WORLD_WIDTH), world_to_screen_dist(WORLD_HEIGHT)
        pygame.draw.rect(screen, (25, 30, 40), (w_sx, w_sy, w_sw, w_sh))

        platforms = game_data.get("platforms", [])
        for px, py, pw, ph in platforms:
            sx, sy = world_to_screen(px, py)
            sw, sh = world_to_screen_dist(pw), world_to_screen_dist(ph)
            pygame.draw.rect(screen, (60, 70, 90), (sx, sy, sw, sh), border_radius=4)

        bullets_list = game_data.get("bullets", [])
        if isinstance(bullets_list, list):
            for b in bullets_list:
                if isinstance(b, dict):
                    sx, sy = world_to_screen(b.get("x", 0), b.get("y", 0))
                    sr = world_to_screen_dist(b.get("r", 6))
                    pygame.draw.circle(screen, (255, 220, 50), (sx, sy), max(3, sr))

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
            scores_str = " | ".join([f"P{pid}: {p.get('score', 0)}/10 (Пол: {p.get('half_wins', 0)}/5)" for pid, p in players_map.items()])
            score_txt = font_main.render(scores_str, True, (255, 215, 0))
            screen.blit(score_txt, (20, 20))

        st = game_data.get("state", "WAITING")
        if st == "WAITING":
            txt = font_large.render("ОЖИДАНИЕ ИГРОКОВ (ОТ 2)...", True, (240, 240, 240))
            screen.blit(txt, (screen_width // 2 - txt.get_width() // 2, 40))
        elif st == "GAME_OVER":
            win_id = game_data.get("winner_game")
            txt = font_large.render(f"ИГРОК #{win_id} ПОБЕДИЛ В МАТЧЕ!", True, (50, 255, 50))
            screen.blit(txt, (screen_width // 2 - txt.get_width() // 2, screen_height // 2))
        else:
            txt = font_main.render(f"РАУНД {game_data.get('round', 1)} | Арена #{game_data.get('map_idx', 0) + 1}", True, (200, 200, 200))
            screen.blit(txt, (screen_width // 2 - txt.get_width() // 2, 10))

        if st == "UPGRADE":
            loser_ids = [str(lid) for lid in game_data.get("loser_ids", [])]
            if my_id in loser_ids:
                title = font_large.render("ВЫБЕРИТЕ УЛУЧШЕНИЕ И АРЕНУ", True, (255, 215, 0))
                cards = game_data.get("offered_cards", [])
                if isinstance(cards, list):
                    card_w, card_h = 220, 280
                    total_w = len(cards) * card_w + (len(cards) - 1) * 20
                    start_x = (screen_width - total_w) // 2
                    start_y = (screen_height - card_h) // 2 - 40

                    for i, card_id in enumerate(cards):
                        c_info = CARDS_DB.get(card_id, {"name": card_id})
                        cx = start_x + i * (card_w + 20)

                        pygame.draw.rect(screen, (35, 42, 60), (cx, start_y, card_w, card_h), border_radius=10)
                        pygame.draw.rect(screen, (100, 150, 255), (cx, start_y, card_w, card_h), 3, border_radius=10)

                        name_txt = font_card.render(c_info.get("name", card_id), True, (255, 255, 255))
                        screen.blit(name_txt, (cx + card_w // 2 - name_txt.get_width() // 2, start_y + 35))

                    map_box_y = start_y + card_h + 20
                    select_map_label = font_card.render("Выберите арену для следующего раунда:", True, (220, 220, 220))
                    screen.blit(select_map_label, (screen_width // 2 - select_map_label.get_width() // 2, map_box_y))
                    
                    total_maps = 4
                    m_width_box = 90
                    m_start_x = (screen_width - (total_maps * (m_width_box + 10))) // 2
                    for m_i in range(total_maps):
                        mx_pos = m_start_x + m_i * (m_width_box + 10)
                        my_pos = map_box_y + 25
                        box_color = (80, 200, 100) if selected_map_preview == m_i else (45, 50, 65)
                        pygame.draw.rect(screen, box_color, (mx_pos, my_pos, m_width_box, 35), border_radius=5)
                        m_txt = font_card.render(f"Арена {m_i+1}", True, (255, 255, 255))
                        screen.blit(m_txt, (mx_pos + m_width_box // 2 - m_txt.get_width() // 2, my_pos + 9))
            else:
                title = font_large.render("ПРОИГРАВШИЕ ВЫБИРАЮТ УЛУЧШЕНИЯ...", True, (180, 180, 180))
                screen.blit(title, (screen_width // 2 - title.get_width() // 2, screen_height // 2 - 20))

        pygame.display.flip()

if __name__ == "__main__":
    main()