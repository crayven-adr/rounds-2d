# client.py
import socket
import json
import threading
import pygame
import sys
import math

from config import PORT, WORLD_WIDTH, WORLD_HEIGHT
from textures import TextureManager
from ui_drawer import draw_player_ui, draw_hud_cards

class GameClient:
    def __init__(self, host="127.0.0.1"):
        pygame.init()
        self.screen = pygame.display.set_mode((WORLD_WIDTH, WORLD_HEIGHT))
        pygame.display.set_caption(f"2D Round Fighter [{host}]")
        self.clock = pygame.time.Clock()
        
        self.tm = TextureManager()
        self.tm.init_fonts()

        self.my_id = None
        self.game_state = {}
        self.running = True
        
        # Переменные ввода
        self.input_data = {
            "left": False,
            "right": False,
            "jump": False,
            "shoot": False,
            "reload": False,
            "mouse_x": 0,
            "mouse_y": 0,
            "card_choice": None
        }

        # Сетевое подключение по IP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Подключение к серверу {host}:{PORT}...")
            self.sock.connect((host, PORT))
            print("Успешно подключено!")
        except Exception as e:
            print(f"Ошибка подключения к {host}:{PORT} -> {e}")
            sys.exit()

        threading.Thread(target=self.receive_data, daemon=True).start()

    def receive_data(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip():
                        continue
                    parsed = json.loads(line)
                    if "my_id" in parsed:
                        self.my_id = parsed["my_id"]
                    else:
                        self.game_state = parsed
            except Exception:
                break

    def handle_events(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.input_data["mouse_x"] = mouse_x
        self.input_data["mouse_y"] = mouse_y

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.input_data["left"] = True
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.input_data["right"] = True
                if event.key in (pygame.K_w, pygame.K_SPACE, pygame.K_UP):
                    self.input_data["jump"] = True
                if event.key == pygame.K_r:
                    self.input_data["reload"] = True

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.input_data["left"] = False
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.input_data["right"] = False
                if event.key in (pygame.K_w, pygame.K_SPACE, pygame.K_UP):
                    self.input_data["jump"] = False
                if event.key == pygame.K_r:
                    self.input_data["reload"] = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    state = self.game_state.get("state")
                    loser_ids = self.game_state.get("loser_ids", [])
                    
                    if state == "UPGRADE" and self.my_id in [str(lid) for lid in loser_ids]:
                        cards = self.game_state.get("offered_cards_data", [])
                        card_w, card_h = 220, 320
                        spacing = 40
                        total_w = len(cards) * card_w + (len(cards) - 1) * spacing
                        start_x = (WORLD_WIDTH - total_w) // 2
                        start_y = (WORLD_HEIGHT - card_h) // 2

                        for i, card in enumerate(cards):
                            cx = start_x + i * (card_w + spacing)
                            cy = start_y
                            if cx <= mouse_x <= cx + card_w and cy <= mouse_y <= cy + card_h:
                                self.input_data["card_choice"] = {"id": card["id"]}
                                break
                    else:
                        self.input_data["shoot"] = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.input_data["shoot"] = False

    def send_input(self):
        try:
            msg = json.dumps(self.input_data) + '\n'
            self.sock.sendall(msg.encode('utf-8'))
            if self.input_data["card_choice"]:
                self.input_data["card_choice"] = None
        except Exception:
            pass

    def draw(self):
        self.screen.fill((20, 20, 25))
        
        if not self.game_state:
            txt = self.tm.fonts["large"].render("Подключение к серверу...", True, (255, 255, 255))
            self.screen.blit(txt, (WORLD_WIDTH//2 - 150, WORLD_HEIGHT//2))
            pygame.display.flip()
            return

        state = self.game_state.get("state")

        for px, py, pw, ph in self.game_state.get("platforms", []):
            pygame.draw.rect(self.screen, (70, 75, 90), (px, py, pw, ph), border_radius=6)

        for pid, p in self.game_state.get("players", {}).items():
            if not p["alive"]:
                continue
            x, y, r = int(p["x"]), int(p["y"]), p["radius"]
            color = p["color"]
            
            pygame.draw.circle(self.screen, color, (x, y), r)
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), r, width=2)
            
            angle = p.get("aim_angle", 0)
            gun_x = x + math.cos(angle) * (r + 10)
            gun_y = y + math.sin(angle) * (r + 10)
            pygame.draw.line(self.screen, (255, 255, 255), (x, y), (gun_x, gun_y), 4)

            draw_player_ui(self.screen, p, self.tm.fonts["small"])

        for b in self.game_state.get("bullets", []):
            pygame.draw.circle(self.screen, (255, 220, 100), (int(b["x"]), int(b["y"])), b["r"])

        draw_hud_cards(self.screen, self.game_state, self.my_id, self.tm.fonts["small"])

        if state == "WAITING":
            txt = self.tm.fonts["large"].render("Ожидание второго игрока...", True, (255, 255, 255))
            self.screen.blit(txt, (WORLD_WIDTH//2 - 200, 100))

        elif state == "UPGRADE":
            cards = self.game_state.get("offered_cards_data", [])
            loser_ids = self.game_state.get("loser_ids", [])
            
            is_my_turn = str(self.my_id) in [str(lid) for lid in loser_ids]
            header_str = "Выберите карту улучшения:" if is_my_turn else "Проигравший выбирает карту..."
            
            txt = self.tm.fonts["large"].render(header_str, True, (255, 220, 80))
            self.screen.blit(txt, (WORLD_WIDTH//2 - txt.get_width()//2, 120))

            card_w, card_h = 220, 320
            spacing = 40
            total_w = len(cards) * card_w + (len(cards) - 1) * spacing
            start_x = (WORLD_WIDTH - total_w) // 2
            start_y = (WORLD_HEIGHT - card_h) // 2

            mx, my = pygame.mouse.get_pos()

            for i, card in enumerate(cards):
                cx = start_x + i * (card_w + spacing)
                cy = start_y
                
                hover = (cx <= mx <= cx + card_w and cy <= my <= cy + card_h) and is_my_turn
                bg_color = (50, 55, 70) if not hover else (70, 80, 105)

                pygame.draw.rect(self.screen, bg_color, (cx, cy, card_w, card_h), border_radius=12)
                pygame.draw.rect(self.screen, card["color"], (cx, cy, card_w, card_h), width=4, border_radius=12)

                name_txt = self.tm.fonts["medium"].render(card["name"], True, (255, 255, 255))
                self.screen.blit(name_txt, (cx + (card_w - name_txt.get_width())//2, cy + 20))

                desc_words = card["desc"].split()
                line = ""
                line_y = cy + 80
                for word in desc_words:
                    test_line = line + word + " "
                    if self.tm.fonts["small"].size(test_line)[0] < card_w - 20:
                        line = test_line
                    else:
                        d_txt = self.tm.fonts["small"].render(line, True, (200, 200, 200))
                        self.screen.blit(d_txt, (cx + 10, line_y))
                        line = word + " "
                        line_y += 22
                if line:
                    d_txt = self.tm.fonts["small"].render(line, True, (200, 200, 200))
                    self.screen.blit(d_txt, (cx + 10, line_y))

        elif state == "GAME_OVER":
            winner = self.game_state.get("winner_game")
            txt = self.tm.fonts["large"].render(f"ИГРА ОКОНЧЕНА! Победитель: Игрок {winner}", True, (80, 255, 120))
            self.screen.blit(txt, (WORLD_WIDTH//2 - txt.get_width()//2, WORLD_HEIGHT//2))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.send_input()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        self.sock.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]
    else:
        target_ip = input("Введите IP-адрес сервера (Enter для 127.0.0.1): ").strip()
        if not target_ip:
            target_ip = "127.0.0.1"

    client = GameClient(host=target_ip)
    client.run()