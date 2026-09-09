import socket
import threading
import json
import random

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000

clients = {}
game_state = {
    "players": {},
    "scores": {1: 0, 2: 0},
    "half_scores": {1: [0, 0], 2: [0, 0]}, # Счет по половинам (по 5 раундов)
    "current_round": 1,
    "max_rounds": 10,
    "current_map": "Arena 1",
    "maps": [
        {"name": "Arena 1", "width": 1200, "height": 800},
        {"name": "Arena 2", "width": 1400, "height": 900},
        {"name": "Arena 3", "width": 1600, "height": 1000}
    ],
    "game_over": False
}

# Генерация 67 карт (бафф + дебафф + редкость)
RARITIES = {
    "Common": {"color": "#FFFFFF", "chance": 0.5},
    "Rare": {"color": "#3498DB", "chance": 0.3},
    "Epic": {"color": "#9B59B6", "chance": 0.15},
    "Legendary": {"color": "#F1C40F", "chance": 0.05}
}

ALL_CARDS = []
card_types = [
    ("Вампиризм", "Кража HP при ударе", "Замедление бега"),
    ("Стеклянная пушка", "Урон +50%", "Макс. HP -30%"),
    ("Броненосец", "Защита +40%", "Скорость -20%"),
    ("Адреналин", "Скорость +25%", "Урон -15%"),
    ("Берсерк", "Урон при лоу ХП +100%", "Регенерация отменена"),
    ("Точный глаз", "Дальность полета пули +50%", "Скорострельность -20%"),
    ("Тяжеловес", "Отталкивание врагов +80%", "Рывок перезаряжается дольше"),
    ("Регенератор", "ХП восстанавливается со временем", "Макс. HP -10%"),
    ("Нестабильность", "Шанс крита х3", "Шанс промахнуться 10%"),
    ("Электрический шок", "Замедляет врага при попадании", "Ваш урон снижен на 5%"),
    ("Призрак", "Проход сквозь стены на 2 сек при рывке", "Урон снижен на 10%"),
    ("Гурман", "Аптечки лечат в 2 раза сильнее", "Каждый раунд отнимает 5 HP"),
    ("Магнит", "Притягивает монеты/бонусы", "Защита -10%"),
    ("Огненный след", "Оставляет огонь за собой", "Ваша скорость ниже на 10%"),
    ("Рикошет", "Пули отскакивают от стен", "Урон пуль уменьшен"),
]

# Расширяем список до 67 штук программно для примера баланса
for i in range(1, 68):
    base = card_types[(i - 1) % len(card_types)]
    r_key = random.choices(list(RARITIES.keys()), weights=[0.5, 0.3, 0.15, 0.05])[0]
    ALL_CARDS.append({
        "id": i,
        "name": f"{base[0]} #{i}",
        "buff": base[1],
        "debuff": base[2],
        "rarity": r_key,
        "color": RARITIES[r_key]["color"]
    })

def handle_client(conn, addr, player_id):
    print(f"Игрок {player_id} подключен: {addr}")
    clients[player_id] = conn
    game_state["players"][player_id] = {"x": 100 * player_id, "y": 100, "hp": 100, "cards": []}

    try:
        while True:
            data = conn.recv(2048)
            if not data:
                break
            packet = json.loads(data.decode('utf-8'))
            
            # Обновляем позицию игрока
            if "x" in packet:
                game_state["players"][player_id]["x"] = packet["x"]
                game_state["players"][player_id]["y"] = packet["y"]

            # Выбор карты
            if "pick_card" in packet:
                card_id = packet["pick_card"]
                # Находим карту и добавляем игроку, исключая повторы
                player_cards = game_state["players"][player_id]["cards"]
                if card_id not in player_cards:
                    player_cards.append(card_id)

            # Рассылаем состояние всем
            response = json.dumps(game_state)
            conn.sendall(response.encode('utf-8'))
    except Exception as e:
        print(f"Ошибка с игроком {player_id}: {e}")
    finally:
        conn.close()
        del clients[player_id]
        if player_id in game_state["players"]:
            del game_state["players"][player_id]

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(2)
    print(ет := f"Сервер запущен на {SERVER_HOST}:{SERVER_PORT}")
    
    pid = 1
    while pid <= 2:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr, pid), daemon=True).start()
        pid += 1

if __name__ == "__main__":
    start_server()