# cards.py
import random
from cards_db import CARDS_DB

def apply_card_stats(p, stats):
    """Применение эффектов карты к параметрам игрока"""
    if "dmg_mult" in stats:
        p["dmg"] = max(1, p["dmg"] * stats["dmg_mult"])
        
    if "ammo" in stats:
        p["max_ammo"] = max(1, p["max_ammo"] + stats["ammo"])
        p["ammo"] = min(p["ammo"], p["max_ammo"])

    if "add_reload" in stats:
        p["base_reload_time"] = max(0.2, p["base_reload_time"] + stats["add_reload"])

    if "atk_spd_mult" in stats:
        p["atk_cooldown"] = max(0.05, p.get("atk_cooldown", 0.2) / stats["atk_spd_mult"])

    if "hp_mult" in stats:
        p["max_hp"] = int(p["max_hp"] * stats["hp_mult"])
        p["hp"] = p["max_hp"]

    if stats.get("glass_cannon"):
        p["max_hp"] = 1
        p["hp"] = 1

    if "bullets" in stats:
        p["bullets_per_shot"] = p.get("bullets_per_shot", 1) + stats["bullets"]
        
    if "bullet_size" in stats:
        p["bullet_size_mult"] = p.get("bullet_size_mult", 1.0) * stats["bullet_size"]

    if "bullet_spd_mult" in stats:
        p["bullet_speed_mult"] = p.get("bullet_speed_mult", 1.0) * stats["bullet_spd_mult"]

    if "bounces" in stats:
        p["bounces"] = p.get("bounces", 0) + stats["bounces"]

    if stats.get("homing"):
        p["homing"] = True

    if stats.get("explosive"):
        p["explosive"] = True

    if "slow" in stats:
        p["slow_effect"] = max(p.get("slow_effect", 0.0), stats["slow"])

    if "vampirism" in stats:
        p["vampirism"] = p.get("vampirism", 0.0) + stats["vampirism"]

ALL_CARDS = []
for cid, info in CARDS_DB.items():
    card_obj = {
        "id": cid,
        "name": info["name"],
        "desc": info["desc"],
        "color": info["rarity_color"],
        "short": info["short"],
        "stats": info,
        "apply": lambda p, stats=info: apply_card_stats(p, stats)
    }
    ALL_CARDS.append(card_obj)

def get_random_cards(player_card_ids, count=3):
    """Выдача случайных карт, исключая ранее выбранные данным игроком"""
    available = [c for c in ALL_CARDS if c["id"] not in player_card_ids]
    if not available:
        return []
    return random.sample(available, min(count, len(available)))