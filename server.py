import socket
import threading
import json
import time
import math
import random

# --- НАСТРОЙКИ СЕРВЕРА ---
SERVER_IP = "0.0.0.0"
PORT = 5555

WORLD_WIDTH = 2000
WORLD_HEIGHT = 1200
GRAVITY = 0.65
JUMP_FORCE = -25.0
MOVE_SPEED = 8.5
MAX_SCORE = 7
BULLET_GRAVITY = 0.15 

SPAWN_POINTS = [
    (150, 1050), (1850, 1050), (1000, 550), (500, 700),
    (1500, 700), (300, 350), (1700, 350), (1000, 200)
]

PLAYER_COLORS = [
    [50, 150, 255],  [255, 80, 80],   [80, 220, 100],  [255, 200, 50],
    [180, 80, 255],  [255, 130, 50],  [50, 220, 220],  [230, 100, 180]
]

MAP_LAYOUTS = [
    [
        (0, 1150, 2000, 50), (-30, 0, 30, 1200), (2000, 0, 30, 1200), (0, -30, 2000, 30),
        (200, 1000, 350, 25), (1450, 1000, 350, 25), (700, 950, 600, 25),
        (100, 800, 300, 25), (1600, 800, 300, 25), (550, 750, 300, 25),
        (1150, 750, 300, 25), (800, 600, 400, 25), (250, 380, 400, 25),
        (1350, 380, 400, 25), (650, 220, 700, 25)
    ],
    [
        (0, 1150, 2000, 50), (-30, 0, 30, 1200), (2000, 0, 30, 1200), (0, -30, 2000, 30),
        (100, 950, 500, 30), (1400, 950, 500, 30), (750, 850, 500, 30),
        (300, 700, 400, 30), (1300, 700, 400, 30), (100, 500, 400, 30),
        (1500, 500, 400, 30), (600, 400, 800, 30), (850, 200, 300, 30)
    ],
    [
        (0, 1150, 2000, 50), (-30, 0, 30, 1200), (2000, 0, 30, 1200), (0, -30, 2000, 30),
        (400, 850, 300, 300), (1300, 850, 300, 300), (850, 950, 300, 25),
        (200, 650, 350, 25), (1450, 650, 350, 25), (700, 550, 600, 30),
        (400, 350, 300, 25), (1300, 350, 300, 25), (850, 250, 300, 25)
    ]
]

CARDS_KEYS = [
    "BIG_BULLETS", "FAST_SHOOT", "HEALTH", "SPEED", "SHOTGUN", "VAMPIRISM",
    "SHIELD", "HEAVY_BULLETS", "SNIPER", "LIFESTEAL", "BERSERK"
]


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
        self.bullet_speed = 24.0
        self.cooldown_max = 14
        self.cooldown_timer = 0
        self.bullets_per_shot = 1
        self.vampirism = 0.0

        self.max_ammo = 6
        self.ammo = 6
        self.reload_time = 80
        self.reload_timer = 0

        self.alive = True
        self.aim_angle = 0.0
        self.score = 0
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
        if card_id == "BIG_BULLETS":
            self.damage *= 1.4
            self.bullet_size = int(self.bullet_size * 1.5)
        elif card_id == "FAST_SHOOT":
            self.cooldown_max = max(4, int(self.cooldown_max * 0.55))
            self.damage *= 0.8
        elif card_id == "HEALTH":
            self.max_hp *= 1.4
            self.radius = int(self.base_radius * 1.2)
        elif card_id == "SPEED":
            self.speed *= 1.25
        elif card_id == "SHOTGUN":
            self.bullets_per_shot = 4
            self.damage *= 0.5
            self.max_ammo = 4
        elif card_id == "VAMPIRISM":
            self.vampirism += 0.3
        elif card_id == "SHIELD":
            self.max_hp += 40.0
        elif card_id == "HEAVY_BULLETS":
            self.damage *= 1.8
            self.bullet_speed *= 0.7
        elif card_id == "SNIPER":
            self.bullet_speed *= 1.6
            self.damage *= 1.5
            self.cooldown_max = int(self.cooldown_max * 1.5)
        elif card_id == "LIFESTEAL":
            self.vampirism += 0.5
            self.max_hp *= 0.85
        elif card_id == "BERSERK":
            self.damage *= 1.6
            self.speed *= 1.2
            self.max_hp *= 0.75

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
        if self.vy > 26:
            self.vy = 26

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
    def __init__(self, x, y, vx, vy, damage, owner_id, radius, vampirism):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = damage
        self.owner_id = str(owner_id)
        self.r = radius
        self.vampirism = vampirism
        self.active = True

    def update(self, platforms):
        self.vy += BULLET_GRAVITY

        self.x += self.vx
        self.y += self.vy

        for px, py, pw, ph in platforms:
            if px <= self.x <= px + pw and py <= self.y <= py + ph:
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
        self.loser_id = None
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

    def select_random_map(self):
        self.current_map_idx = random.randint(0, len(MAP_LAYOUTS) - 1)
        self.platforms = MAP_LAYOUTS[self.current_map_idx]

    def start_game(self):
        self.state = "PLAYING"
        self.round_num = 1
        self.select_random_map()
        for p in self.players.values():
            p.score = 0
            p.reset_for_round()

    def start_upgrade_phase(self, loser_id):
        self.state = "UPGRADE"
        self.loser_id = str(loser_id)
        self.offered_cards = random.sample(CARDS_KEYS, min(3, len(CARDS_KEYS)))

    def process_inputs(self, p_id, inputs):
        with self.lock:
            p = self.players.get(str(p_id))
            if not p:
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
                            self.bullets.append(Bullet(bx, by, b_vx, b_vy, p.damage, p.id, p.bullet_size, p.vampirism))

                        if p.ammo == 0:
                            p.reload_timer = p.reload_time

            elif self.state == "UPGRADE" and str(self.loser_id) == str(p_id):
                choice = inputs.get("card_choice")
                if choice in self.offered_cards:
                    p.apply_card(choice)
                    self.round_num += 1
                    self.select_random_map() 
                    self.state = "PLAYING"
                    self.loser_id = None
                    self.offered_cards = []
                    self.bullets.clear()
                    for pl in self.players.values():
                        pl.reset_for_round()

    def update_game_logic(self):
        with self.lock:
            self.events = []
            if self.state != "PLAYING":
                return

            for b in self.bullets[:]:
                res = b.update(self.platforms)
                if res == "hit_wall":
                    self.events.append({"type": "hit_wall", "x": b.x, "y": b.y})

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
                                        if winner.score >= MAX_SCORE:
                                            self.state = "GAME_OVER"
                                            self.winner_game_id = winner.id
                                            return

                                    self.start_upgrade_phase(p.id)
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
                    "score": p.score
                }

            bullets_list = [{"x": b.x, "y": b.y, "r": b.r} for b in self.bullets]

            state_data = {
                "players": players_dict,
                "bullets": bullets_list,
                "platforms": self.platforms,
                "state": self.state,
                "round": self.round_num,
                "loser": self.loser_id,
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
    
    # Автоматическое определение IP для раздачи друзьям
    hostname = socket.gethostname()
    try:
        local_ips = socket.gethostbyname_ex(hostname)[2]
        print("\n=== ВАШИ IP-АДРЕСА ДЛЯ ПОДКЛЮЧЕНИЯ ДРУЗЕЙ ===")
        print("-> 127.0.0.1 (только для вас на этом компьютере)")
        for ip in local_ips:
            print(f"-> {ip} (для тех, кто с вами в локальной сети или Radmin/Hamachi)")
        print("=============================================\n")
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