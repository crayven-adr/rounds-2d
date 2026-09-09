import socket
import threading
import json
import time
import math
import random

# --- НАСТРОЙКИ СЕРВЕРА ---
SERVER_IP = "0.0.0.0"
PORT = 5555

WORLD_WIDTH = 1800
WORLD_HEIGHT = 1000
GRAVITY = 0.65
JUMP_FORCE = -17.5  # Унифицированная сила прыжка для всех карт
MOVE_SPEED = 5.5
MAX_SCORE = 10      # Всего 10 очков до победы (по 5 на каждую половину матча)
BULLET_GRAVITY = 0.2  # Возвращена гравитация для пуль

SPAWN_POINTS = [
    (150, 850), (1650, 850), (900, 500), (450, 600),
    (1350, 600), (300, 300), (1500, 300), (900, 150)
]

PLAYER_COLORS = [
    [50, 150, 255],  [255, 80, 80],   [80, 220, 100],  [255, 200, 50],
    [180, 80, 255],  [255, 130, 50],  [50, 220, 220],  [230, 100, 180]
]

# Компактные и сбалансированные арены с комфортным прыжком
MAP_LAYOUTS = [
    # Карта 1: Смешанная
    [
        (0, 950, 1800, 50), (-30, 0, 30, 1000), (1800, 0, 30, 1000), (0, -30, 1800, 30),
        (200, 780, 400, 25), (1200, 780, 400, 25), (700, 680, 400, 25),
        (100, 520, 300, 25), (1400, 520, 300, 25), (500, 380, 800, 25),
        (300, 220, 300, 25), (1200, 220, 300, 25)
    ],
    # Карта 2: Открытая
    [
        (0, 950, 1800, 50), (-30, 0, 30, 1000), (1800, 0, 30, 1000), (0, -30, 1800, 30),
        (400, 750, 1000, 25), (200, 500, 400, 25), (1200, 500, 400, 25),
        (750, 350, 300, 25), (500, 200, 800, 25)
    ],
    # Карта 3: Закрытая / Лабиринт
    [
        (0, 950, 1800, 50), (-30, 0, 30, 1000), (1800, 0, 30, 1000), (0, -30, 1800, 30),
        (150, 800, 350, 30), (1300, 800, 350, 30), (600, 750, 600, 30),
        (300, 600, 400, 25), (1100, 600, 400, 25), (750, 480, 300, 25),
        (150, 350, 500, 25), (1150, 350, 500, 25), (500, 200, 800, 25)
    ],
    # Карта 4: Башни
    [
        (0, 950, 1800, 50), (-30, 0, 30, 1000), (1800, 0, 30, 1000), (0, -30, 1800, 30),
        (250, 780, 300, 30), (1250, 780, 300, 30), (750, 650, 300, 30),
        (200, 500, 350, 30), (1250, 500, 350, 30), (700, 350, 400, 30),
        (400, 200, 300, 30), (1100, 200, 300, 30)
    ]
]

# Полная база карт улучшений (на основе предоставленного списка)[cite: 1]
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
CARDS_KEYS = list(CARDS_DB.keys())

class Player:
    def __init__(self, p_id, spawn_pos, color):
        self.id = str(p_id)
        self.spawn_x, self.spawn_y = spawn_pos
        self.color = color
        
        self.base_radius = 20
        self.radius = self.base_radius
        
        self.max_hp = 100.0
        self.hp = 100.0
        self.speed = MOVE_SPEED
        self.jump_force = JUMP_FORCE
        self.damage = 22.0
        self.bullet_size = 6
        self.bullet_speed = 22.0
        self.cooldown_max = 14
        self.cooldown_timer = 0
        self.bullets_per_shot = 1
        self.vampirism = 0.0
        self.bounces = 0

        self.max_ammo = 6
        self.ammo = 6
        self.reload_time = 75
        self.reload_timer = 0

        self.alive = True
        self.aim_angle = 0.0
        self.score = 0
        self.half_wins = 0  # Счетчик побед в текущей половине матча (до 5)
        self.cards = []

        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False

    def reset_position(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False

    def reset_for_round(self):
        self.reset_position()
        self.hp = self.max_hp
        self.alive = True
        self.ammo = self.max_ammo
        self.reload_timer = 0
        self.cooldown_timer = 0

    def apply_card(self, card_id):
        self.cards.append(card_id)
        card = CARDS_DB.get(card_id, {})
        
        if "bullets" in card:
            self.bullets_per_shot = max(1, self.bullets_per_shot + card["bullets"])
        if "ammo" in card:
            self.max_ammo = max(1, self.max_ammo + card["ammo"])
            self.ammo = self.max_ammo
        if "dmg" in card:
            self.damage *= card["dmg"]
        if "reload" in card:
            self.reload_time = max(10, int(self.reload_time + card["reload"]))
        if "bullet_size" in card:
            self.bullet_size = int(self.bullet_size * card["bullet_size"])
        if "bounces" in card:
            self.bounces += card["bounces"]
        if "hp" in card:
            if card["hp"] == 0.0:
                self.max_hp = 1.0
            else:
                self.max_hp *= card["hp"]
            self.hp = self.max_hp
        if "vampirism" in card:
            self.vampirism += card["vampirism"]
        if "bullet_speed" in card:
            self.bullet_speed *= card["bullet_speed"]

    def update_physics(self, inputs, platforms):
        if not self.alive:
            return

        dx = 0
        if inputs.get("left"):
            dx -= 1
        if inputs.get("right"):
            dx += 1
        self.vx = dx * self.speed

        if inputs.get("jump") and self.on_ground:
            self.vy = self.jump_force
            self.on_ground = False

        if inputs.get("reload") and self.ammo < self.max_ammo and self.reload_timer == 0:
            self.reload_timer = self.reload_time

        self.vy += GRAVITY
        if self.vy > 24:
            self.vy = 24

        self.x += self.vx
        for px, py, pw, ph in platforms:
            if (self.x + self.radius > px and self.x - self.radius < px + pw and
                self.y + self.radius > py and self.y - self.radius < py + ph):
                if self.vx > 0:
                    self.x = px - self.radius
                elif self.vx < 0:
                    self.x = px + pw + self.radius

        self.y += self.vy
        self.on_ground = False
        for px, py, pw, ph in platforms:
            if (self.x + self.radius > px and self.x - self.radius < px + pw and
                self.y + self.radius > py and self.y - self.radius < py + ph):
                if self.vy > 0:
                    self.y = py - self.radius
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = py + ph + self.radius
                    self.vy = 0

        mx = inputs.get("mouse_x", self.x)
        my = inputs.get("mouse_y", self.y)
        self.aim_angle = math.atan2(my - self.y, mx - self.x)

        if self.reload_timer > 0:
            self.reload_timer -= 1
            if self.reload_timer == 0:
                self.ammo = self.max_ammo

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1


class Bullet:
    def __init__(self, x, y, vx, vy, damage, owner_id, radius, vampirism, bounces):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = damage
        self.owner_id = str(owner_id)
        self.r = radius
        self.vampirism = vampirism
        self.bounces_left = bounces
        self.active = True

    def update(self, platforms):
        # Восстановлена гравитация для пуль
        self.vy += BULLET_GRAVITY
        self.x += self.vx
        self.y += self.vy

        for px, py, pw, ph in platforms:
            if px <= self.x <= px + pw and py <= self.y <= py + ph:
                if self.bounces_left > 0:
                    self.bounces_left -= 1
                    if abs(self.x - px) < 5 or abs(self.x - (px + pw)) < 5:
                        self.vx = -self.vx
                    else:
                        self.vy = -self.vy
                    self.x += self.vx * 2
                    self.y += self.vy * 2
                    return "bounce"
                else:
                    self.active = False
                    return "hit_wall"

        if self.x < 0 or self.x > WORLD_WIDTH or self.y < 0 or self.y > WORLD_HEIGHT:
            self.active = False
            return "hit_wall"

        return None


class GameServer:
    def __init__(self):
        self.players = {}
        self.bullets = []
        self.clients = {}
        self.state = "WAITING"
        self.round_num = 1
        self.loser_ids = []
        self.winner_game_id = None
        self.offered_cards = []
        self.events = []
        self.current_map_idx = 0
        self.platforms = MAP_LAYOUTS[0]
        self.lock = threading.Lock()

    def add_player(self, conn, addr):
        with self.lock:
            p_id = str(len(self.players) + 1)
            spawn_idx = (int(p_id) - 1) % len(SPAWN_POINTS)
            color_idx = (int(p_id) - 1) % len(PLAYER_COLORS)

            player = Player(p_id, SPAWN_POINTS[spawn_idx], PLAYER_COLORS[color_idx])
            self.players[p_id] = player
            self.clients[p_id] = conn
            
            conn.sendall((json.dumps({"my_id": p_id}) + '\n').encode())

            if len(self.players) >= 2 and self.state == "WAITING":
                self.start_game()

            return p_id

    def remove_player(self, p_id):
        with self.lock:
            p_id = str(p_id)
            if p_id in self.players:
                del self.players[p_id]
            if p_id in self.clients:
                del self.clients[p_id]
            if len(self.players) < 2:
                self.state = "WAITING"

    def select_map_by_index(self, idx):
        self.current_map_idx = idx % len(MAP_LAYOUTS)
        self.platforms = MAP_LAYOUTS[self.current_map_idx]

    def start_game(self):
        self.state = "PLAYING"
        self.round_num = 1
        self.select_map_by_index(random.randint(0, len(MAP_LAYOUTS) - 1))
        for p in self.players.values():
            p.score = 0
            p.half_wins = 0
            p.reset_for_round()

    def start_upgrade_phase(self, dead_p_ids):
        self.state = "UPGRADE"
        self.loser_ids = [str(pid) for pid in dead_p_ids]
        self.offered_cards = random.sample(CARDS_KEYS, min(3, len(CARDS_KEYS)))

    def process_inputs(self, p_id, inputs):
        with self.lock:
            p = self.players.get(str(p_id))
            if not p:
                return

            if self.state == "UPGRADE" and str(p_id) in self.loser_ids:
                choice = inputs.get("card_choice")
                if choice in self.offered_cards:
                    p.apply_card(choice)
                    self.loser_ids.remove(str(p_id))
                    
                    if len(self.loser_ids) == 0:
                        self.round_num += 1
                        next_map_idx = inputs.get("map_choice", random.randint(0, len(MAP_LAYOUTS) - 1))
                        self.select_map_by_index(next_map_idx)
                        self.state = "PLAYING"
                        self.offered_cards = []
                        self.bullets.clear()
                        for pl in self.players.values():
                            pl.reset_for_round()
                return

            if self.state == "PLAYING" and p.alive:
                p.update_physics(inputs, self.platforms)

                if inputs.get("shoot") and p.cooldown_timer == 0 and p.reload_timer == 0:
                    if p.ammo > 0:
                        p.ammo -= 1
                        p.cooldown_timer = p.cooldown_max
                        
                        spread = 0.22 if p.bullets_per_shot > 1 else 0.0
                        for i in range(p.bullets_per_shot):
                            offset = (i - (p.bullets_per_shot - 1) / 2) * spread
                            ang = p.aim_angle + offset
                            speed = p.bullet_speed
                            bx = p.x + math.cos(ang) * (p.radius + 10)
                            by = p.y + math.sin(ang) * (p.radius + 10)
                            b_vx = math.cos(ang) * speed
                            b_vy = math.sin(ang) * speed
                            self.bullets.append(Bullet(bx, by, b_vx, b_vy, p.damage, p.id, p.bullet_size, p.vampirism, p.bounces))

                        if p.ammo == 0:
                            p.reload_timer = p.reload_time

    def update_game_logic(self):
        with self.lock:
            self.events = []
            if self.state != "PLAYING":
                return

            for b in self.bullets[:]:
                res = b.update(self.platforms)
                if res == "hit_wall":
                    self.events.append({"type": "hit_wall", "x": b.x, "y": b.y})
                elif res == "bounce":
                    self.events.append({"type": "bounce", "x": b.x, "y": b.y})

                if not b.active:
                    if b in self.bullets:
                        self.bullets.remove(b)
                    continue

                for p_id, p in self.players.items():
                    if p_id != b.owner_id and p.alive:
                        dist = math.hypot(p.x - b.x, p.y - b.y)
                        if dist <= p.radius + b.r:
                            p.hp -= b.damage
                            b.active = False
                            if b in self.bullets:
                                self.bullets.remove(b)

                            owner = self.players.get(b.owner_id)
                            if owner and b.vampirism > 0:
                                owner.hp = min(owner.max_hp, owner.hp + b.damage * b.vampirism)

                            self.events.append({"type": "hit_player", "x": b.x, "y": b.y, "color": p.color})

                            if p.hp <= 0:
                                p.hp = 0
                                p.alive = False
                                self.events.append({"type": "death", "x": p.x, "y": p.y, "color": p.color})

                                alive_players = [pl for pl in self.players.values() if pl.alive]
                                if len(alive_players) <= 1:
                                    if len(alive_players) == 1:
                                        winner = alive_players[0]
                                        winner.score += 1
                                        winner.half_wins += 1
                                        
                                        # Возвращена логика половинчатости раундов (смена стороны / полуфинал по достижении 5 очков)
                                        if winner.half_wins >= (MAX_SCORE // 2):
                                            winner.half_wins = 0
                                            for pl in self.players.values():
                                                pl.reset_position()

                                        if winner.score >= MAX_SCORE:
                                            self.state = "GAME_OVER"
                                            self.winner_game_id = winner.id
                                            return

                                    dead_ones = [pl.id for pl in self.players.values() if not pl.alive]
                                    self.start_upgrade_phase(dead_ones)
                            break

    def get_state_json(self):
        with self.lock:
            players_dict = {}
            for p_id, p in self.players.items():
                players_dict[p_id] = {
                    "x": p.x, "y": p.y, "radius": p.radius,
                    "hp": p.hp, "max_hp": p.max_hp,
                    "color": p.color, "alive": p.alive,
                    "aim_angle": p.aim_angle,
                    "ammo": p.ammo, "max_ammo": p.max_ammo,
                    "reloading": p.reload_timer > 0,
                    "score": p.score,
                    "half_wins": p.half_wins,
                    "cards": [CARDS_DB.get(c, {}).get("name", c) for c in p.cards]
                }

            bullets_list = [{"x": b.x, "y": b.y, "r": b.r} for b in self.bullets]

            state_data = {
                "players": players_dict,
                "bullets": bullets_list,
                "platforms": self.platforms,
                "map_idx": self.current_map_idx,
                "state": self.state,
                "round": self.round_num,
                "loser_ids": self.loser_ids,
                "winner_game": self.winner_game_id,
                "offered_cards": self.offered_cards,
                "events": self.events
            }
            return json.dumps(state_data) + '\n'


def handle_client(conn, addr, server, p_id):
    buffer = ""
    while True:
        try:
            data = conn.recv(2048).decode('utf-8')
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip():
                    continue
                inputs = json.loads(line)
                server.process_inputs(p_id, inputs)
        except Exception:
            break

    server.remove_player(p_id)
    conn.close()


def main():
    server = GameServer()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, PORT))
    sock.listen(8)

    print(f"\n[СЕРВЕР ЗАПУЩЕН] Ожидание игроков на порту {PORT}...")
    
    hostname = socket.gethostname()
    try:
        local_ips = socket.gethostbyname_ex(hostname)[2]
        print("\n=== IP-АДРЕСА ДЛЯ ПОДКЛЮЧЕНИЯ ИГРОКОВ ===")
        print("-> 127.0.0.1 (локально)")
        for ip in local_ips:
            print(f"-> {ip}")
        print("=========================================\n")
    except:
        pass

    def accept_thread():
        while True:
            conn, addr = sock.accept()
            p_id = server.add_player(conn, addr)
            print(f"[ПОДКЛЮЧЕНИЕ] Игрок #{p_id} подключился с {addr}")
            threading.Thread(target=handle_client, args=(conn, addr, server, p_id), daemon=True).start()

    threading.Thread(target=accept_thread, daemon=True).start()

    clock_interval = 1.0 / 60.0
    while True:
        start_time = time.time()
        server.update_game_logic()
        state_json = server.get_state_json()

        with server.lock:
            for conn in list(server.clients.values()):
                try:
                    conn.sendall(state_json.encode('utf-8'))
                except:
                    pass

        elapsed = time.time() - start_time
        sleep_time = clock_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()