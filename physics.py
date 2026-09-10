# physics.py
import math
import time
from config import WORLD_WIDTH, WORLD_HEIGHT, WORLD_GRAVITY_PER_TICK

def update_player_physics(player, platforms):
    if not player["alive"]:
        return
        
    current_speed = player["speed"]
    if player.get("slow_timer", 0) > time.time():
        current_speed *= (1.0 - player.get("slow_amount", 0.0))

    player["vy"] += WORLD_GRAVITY_PER_TICK
    r = player["radius"]
    
    # Горизонтальное движение
    player["x"] += player["vx"]
    for px, py, pw, ph in platforms:
        if py <= player["y"] + r and player["y"] - r <= py + ph:
            if player["vx"] > 0 and (px <= player["x"] + r <= px + 10):
                player["x"] = px - r
                player["vx"] = 0
            elif player["vx"] < 0 and (px + pw - 10 <= player["x"] - r <= px + pw):
                player["x"] = px + pw + r
                player["vx"] = 0

    # Вертикальное движение и платформы
    prev_y = player["y"]
    player["y"] += player["vy"]
    player["on_ground"] = False

    for px, py, pw, ph in platforms:
        if px <= player["x"] + r and player["x"] - r <= px + pw:
            if player["vy"] >= 0 and (prev_y + r <= py + 12) and (player["y"] + r >= py):
                player["y"] = py - r
                player["vy"] = 0
                player["on_ground"] = True
            elif player["vy"] < 0 and (prev_y - r >= py + ph - 12) and (player["y"] - r <= py + ph):
                player["y"] = py + ph + r
                player["vy"] = 0

    # Границы арены
    if player["x"] - r < 0: 
        player["x"], player["vx"] = r, 0
    elif player["x"] + r > WORLD_WIDTH: 
        player["x"], player["vx"] = WORLD_WIDTH - r, 0
        
    if player["y"] - r < 0: 
        player["y"], player["vy"] = r, 0
    elif player["y"] + r > WORLD_HEIGHT - 40: 
        player["y"], player["vy"], player["on_ground"] = WORLD_HEIGHT - 40 - r, 0, True


def _trigger_explosion(bullet, players, events):
    """Обработка взрывного урона по области"""
    exp_radius = 120
    events.append({"type": "explosion", "x": bullet["x"], "y": bullet["y"], "radius": exp_radius})
    
    for pid, p in players.items():
        if p["alive"]:
            dist = math.hypot(p["x"] - bullet["x"], p["y"] - bullet["y"])
            if dist <= exp_radius + p["radius"]:
                p["hp"] -= bullet["dmg"]
                if p["hp"] <= 0:
                    p["alive"] = False


def update_bullets_physics(bullets, platforms, players, events):
    for b in bullets[:]:
        # 1. Самонаведение
        if b.get("homing"):
            target_p = None
            min_dist = 999999
            for pid, p in players.items():
                if p["alive"] and pid != b["owner_id"]:
                    dist = math.hypot(p["x"] - b["x"], p["y"] - b["y"])
                    if dist < min_dist:
                        min_dist = dist
                        target_p = p
            
            if target_p:
                dx = target_p["x"] - b["x"]
                dy = target_p["y"] - b["y"]
                angle_to_target = math.atan2(dy, dx)
                speed = math.hypot(b["vx"], b["vy"])
                cur_angle = math.atan2(b["vy"], b["vx"])
                diff = (angle_to_target - cur_angle + math.pi) % (2 * math.pi) - math.pi
                new_angle = cur_angle + diff * 0.15
                
                b["vx"] = math.cos(new_angle) * speed
                b["vy"] = math.sin(new_angle) * speed
        else:
            b["vy"] += WORLD_GRAVITY_PER_TICK * 0.1

        # 2. Движение по шагам
        steps = 4
        sub_vx = b["vx"] / steps
        sub_vy = b["vy"] / steps
        hit_block = False

        for _ in range(steps):
            next_x = b["x"] + sub_vx
            next_y = b["y"] + sub_vy

            for px, py, pw, ph in platforms:
                if px <= next_x <= px + pw and py <= next_y <= py + ph:
                    if b.get("bounces", 0) > 0:
                        b["bounces"] -= 1
                        if b["x"] < px or b["x"] > px + pw:
                            b["vx"] = -b["vx"]
                            sub_vx = -sub_vx
                        if b["y"] < py or b["y"] > py + ph:
                            b["vy"] = -b["vy"]
                            sub_vy = -sub_vy
                            
                        next_x = b["x"] + sub_vx
                        next_y = b["y"] + sub_vy
                    else:
                        hit_block = True
                    break

            b["x"], b["y"] = next_x, next_y
            if hit_block:
                break

        # Уничтожение пули при столкновении со стеной
        if hit_block or b["x"] < 0 or b["x"] > WORLD_WIDTH or b["y"] < 0 or b["y"] > WORLD_HEIGHT:
            if b.get("explosive"):
                _trigger_explosion(b, players, events)
            if b in bullets:
                bullets.remove(b)
            continue

        # 3. Попадание по игрокам
        for pid, p in players.items():
            if p["alive"] and pid != b["owner_id"]:
                if math.hypot(p["x"] - b["x"], p["y"] - b["y"]) < p["radius"] + b["r"]:
                    if b.get("explosive"):
                        _trigger_explosion(b, players, events)
                    else:
                        p["hp"] -= b["dmg"]
                        if b.get("slow", 0) > 0:
                            p["slow_amount"] = b["slow"]
                            p["slow_timer"] = time.time() + 2.0
                        
                        owner = players.get(b["owner_id"])
                        if owner and owner.get("vampirism", 0) > 0:
                            owner["hp"] = min(owner["max_hp"], owner["hp"] + b["dmg"] * owner["vampirism"])

                    events.append({"type": "hit_player", "x": b["x"], "y": b["y"], "color": [255, 50, 50]})
                    
                    if b in bullets:
                        bullets.remove(b)
                    if p["hp"] <= 0:
                        p["alive"] = False
                    break