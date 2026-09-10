# server.py
import socket
import json
import threading
import time
import math
import random

from config import PORT, WORLD_WIDTH, WORLD_HEIGHT, MAX_WINS, PLAYER_COLORS, MAPS
from physics import update_player_physics, update_bullets_physics
from cards import get_random_cards, ALL_CARDS

def get_local_ip():
    """Получение локального IP-адреса хоста в локальной сети"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def create_initial_player_state(pid, spawn_x, spawn_y):
    return {
        "id": str(pid),
        "x": spawn_x,
        "y": spawn_y,
        "vx": 0.0,
        "vy": 0.0,
        "radius": 20,
        "color": PLAYER_COLORS[(pid - 1) % len(PLAYER_COLORS)],
        "hp": 100,
        "max_hp": 100,
        "dmg": 15,
        "speed": 6.0,
        "alive": True,
        "wins": 0,
        "aim_angle": 0.0,
        "ammo": 6,
        "max_ammo": 6,
        "reloading": False,
        "reload_timer": 0,
        "base_reload_time": 2.0,
        "last_shot_time": 0,
        "atk_cooldown": 0.25,
        "bullets_per_shot": 1,
        "bullet_speed_mult": 1.0,
        "bullet_size_mult": 1.0,
        "bounces": 0,
        "homing": False,
        "explosive": False,
        "slow_effect": 0.0,
        "vampirism": 0.0,
        "cards": [],
        "card_icons": []
    }

class GameServer:
    def __init__(self):
        self.clients = {}
        self.inputs = {}
        self.players = {}
        self.bullets = []
        self.events = []
        
        self.current_map_idx = 0
        self.platforms = MAPS[self.current_map_idx]
        self.state = "WAITING"
        
        self.loser_ids = []
        self.offered_cards_data = []
        self.winner_game = None

    def reset_round(self):
        self.bullets.clear()
        self.events.clear()
        self.current_map_idx = random.randint(0, len(MAPS) - 1)
        self.platforms = MAPS[self.current_map_idx]
        
        spawn_positions = [
            (300, 300),
            (WORLD_WIDTH - 300, 300),
            (600, 300),
            (WORLD_WIDTH - 600, 300)
        ]
        
        for idx, (pid, p) in enumerate(self.players.items()):
            sp_x, sp_y = spawn_positions[idx % len(spawn_positions)]
            p["x"] = sp_x
            p["y"] = sp_y
            p["vx"] = 0.0
            p["vy"] = 0.0
            p["hp"] = p["max_hp"]
            p["ammo"] = p["max_ammo"]
            p["reloading"] = False
            p["alive"] = True

    def process_inputs(self):
        now = time.time()
        for pid_str, p in self.players.items():
            if not p["alive"]:
                continue
                
            inp = self.inputs.get(int(pid_str), {})
            
            vx = 0
            if inp.get("left"):
                vx -= p["speed"]
            if inp.get("right"):
                vx += p["speed"]
            p["vx"] = vx
            
            if inp.get("jump") and p.get("on_ground"):
                p["vy"] = -13.5
                p["on_ground"] = False

            mx = inp.get("mouse_x", p["x"])
            my = inp.get("mouse_y", p["y"])
            p["aim_angle"] = math.atan2(my - p["y"], mx - p["x"])

            if inp.get("reload") and not p["reloading"] and p["ammo"] < p["max_ammo"]:
                p["reloading"] = True
                p["reload_timer"] = now + p["base_reload_time"]

            if p["reloading"]:
                if now >= p["reload_timer"]:
                    p["ammo"] = p["max_ammo"]
                    p["reloading"] = False

            if inp.get("shoot") and not p["reloading"]:
                if p["ammo"] > 0:
                    if now - p["last_shot_time"] >= p.get("atk_cooldown", 0.25):
                        p["ammo"] -= 1
                        p["last_shot_time"] = now
                        self.spawn_bullets(p)
                        
                        if p["ammo"] <= 0:
                            p["reloading"] = True
                            p["reload_timer"] = now + p["base_reload_time"]

    def spawn_bullets(self, p):
        num_bullets = p.get("bullets_per_shot", 1)
        base_angle = p["aim_angle"]
        speed = 14.0 * p.get("bullet_speed_mult", 1.0)
        spread = 0.25 if num_bullets > 1 else 0.0
            
        for i in range(num_bullets):
            angle_offset = (i - (num_bullets - 1) / 2.0) * spread if num_bullets > 1 else 0.0
            final_angle = base_angle + angle_offset
            
            bullet = {
                "owner_id": p["id"],
                "x": p["x"] + math.cos(final_angle) * 25,
                "y": p["y"] + math.sin(final_angle) * 25,
                "vx": math.cos(final_angle) * speed,
                "vy": math.sin(final_angle) * speed,
                "r": int(6 * p.get("bullet_size_mult", 1.0)),
                "dmg": p["dmg"],
                "bounces": p.get("bounces", 0),
                "homing": p.get("homing", False),
                "explosive": p.get("explosive", False),
                "slow": p.get("slow_effect", 0.0)
            }
            self.bullets.append(bullet)

    def update_game_logic(self):
        if self.state == "WAITING":
            if len(self.players) >= 2:
                self.reset_round()
                self.state = "PLAYING"

        elif self.state == "PLAYING":
            self.process_inputs()
            
            for p in self.players.values():
                update_player_physics(p, self.platforms)
                
            update_bullets_physics(self.bullets, self.platforms, self.players, self.events)

            alive_players = [p for p in self.players.values() if p["alive"]]
            if len(alive_players) <= 1:
                winner = alive_players[0] if alive_players else None
                if winner:
                    winner["wins"] += 1
                    if winner["wins"] >= MAX_WINS:
                        self.winner_game = winner["id"]
                        self.state = "GAME_OVER"
                        return

                self.loser_ids = [pid for pid, p in self.players.items() if not p["alive"]]
                if not self.loser_ids and len(self.players) > 1:
                    self.loser_ids = list(self.players.keys())

                if self.loser_ids:
                    target_p = self.players[str(self.loser_ids[0])]
                    chosen_cards = get_random_cards(target_p["cards"], count=3)
                    self.offered_cards_data = [
                        {
                            "id": c["id"],
                            "name": c["name"],
                            "desc": c["desc"],
                            "color": c["color"],
                            "short": c["short"]
                        } for c in chosen_cards
                    ]
                    self.state = "UPGRADE"
                else:
                    self.reset_round()

        elif self.state == "UPGRADE":
            for lid in self.loser_ids:
                inp = self.inputs.get(int(lid), {})
                card_choice = inp.get("card_choice")
                if card_choice:
                    target_p = self.players[str(lid)]
                    cid = str(card_choice["id"])
                    
                    card_obj = next((c for c in ALL_CARDS if str(c["id"]) == cid), None)
                    if card_obj:
                        card_obj["apply"](target_p)
                        target_p["cards"].append(cid)
                        target_p["card_icons"].append({
                            "short": card_obj["short"],
                            "color": card_obj["color"]
                        })

                        inp["card_choice"] = None
                        self.reset_round()
                        self.state = "PLAYING"
                        break

    def get_state_snapshot(self):
        return {
            "state": self.state,
            "platforms": self.platforms,
            "players": self.players,
            "bullets": self.bullets,
            "events": self.events,
            "loser_ids": self.loser_ids,
            "offered_cards_data": self.offered_cards_data,
            "winner_game": self.winner_game
        }

def handle_client(sock, pid, server):
    sock.sendall((json.dumps({"my_id": str(pid)}) + '\n').encode('utf-8'))
    buffer = ""
    while True:
        try:
            data = sock.recv(2048).decode('utf-8')
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line.strip():
                    server.inputs[pid] = json.loads(line)
        except Exception:
            break

    print(f"Игрок P{pid} отключился.")
    sock.close()
    if str(pid) in server.players:
        del server.players[str(pid)]
    if pid in server.inputs:
        del server.inputs[pid]
    if pid in server.clients:
        del server.clients[pid]

def main():
    server = GameServer()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(4)
    
    local_ip = get_local_ip()
    print(f"==================================================")
    print(f" Сервер запущен на порту {PORT}.")
    print(f" Локальный IP вашего хоста: {local_ip}")
    print(f" Для подключения с другого ПК используйте: python client.py {local_ip}")
    print(f"==================================================")

    def accept_thread():
        pid_counter = 1
        while True:
            sock, addr = server_socket.accept()
            print(f"Подключился клиент {addr} -> Игрок P{pid_counter}")
            
            server.clients[pid_counter] = sock
            server.players[str(pid_counter)] = create_initial_player_state(pid_counter, 300, 300)
            
            t = threading.Thread(target=handle_client, args=(sock, pid_counter, server), daemon=True)
            t.start()
            pid_counter += 1

    threading.Thread(target=accept_thread, daemon=True).start()

    target_fps = 60
    frame_duration = 1.0 / target_fps

    while True:
        start_time = time.time()
        
        server.update_game_logic()
        
        snapshot = json.dumps(server.get_state_snapshot()) + '\n'
        encoded_snapshot = snapshot.encode('utf-8')
        
        for sock in list(server.clients.values()):
            try:
                sock.sendall(encoded_snapshot)
            except Exception:
                pass
                
        server.events.clear()

        elapsed = time.time() - start_time
        sleep_time = frame_duration - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()