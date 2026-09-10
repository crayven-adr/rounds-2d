# player_stats.py
from cards_db import CARDS_DB

def create_default_player(player_id, color):
    return {
        "id": player_id,
        "x": 300 + int(player_id) * 200, "y": 400,
        "vx": 0, "vy": 0, "radius": 20,
        "hp": 100, "max_hp": 100, "alive": True, "score": 0,
        "color": color, "aim_angle": 0,
        "cards": [], "card_icons": [],
        "bullets": 1, "bounces": 0, "max_ammo": 6, "ammo": 6,
        "reloading": False, "reload_timer": 0, "base_reload_time": 2.0,
        "dmg": 1.0, "bullet_speed": 1.0, "atk_spd": 1.0, "vampirism": 0.0,
        "homing": False, "on_ground": False, "last_shot": 0
    }

def apply_card(player, card_id):
    card = CARDS_DB.get(card_id)
    if not card:
        return
    
    player["cards"].append(card_id)
    player["card_icons"].append({
        "id": card_id,
        "short": card["short"],
        "color": card["rarity_color"],
        "rarity": card["rarity"]
    })
    
    if "bullets" in card: player["bullets"] = max(1, player["bullets"] + card["bullets"])
    if "bounces" in card: player["bounces"] += card["bounces"]
    if "ammo" in card:
        player["max_ammo"] = max(1, player["max_ammo"] + card["ammo"])
        player["ammo"] = player["max_ammo"]
        
    if "add_reload" in card:
        player["base_reload_time"] = max(0.3, player["base_reload_time"] + card["add_reload"])
        
    if "dmg_mult" in card: player["dmg"] *= card["dmg_mult"]
    if "atk_spd_mult" in card: player["atk_spd"] *= card["atk_spd_mult"]
    if "bullet_spd_mult" in card: player["bullet_speed"] *= card["bullet_spd_mult"]
    
    if "hp_mult" in card:
        player["max_hp"] *= card["hp_mult"]
        player["hp"] = player["max_hp"]
        
    if card.get("glass_cannon"):
        player["max_hp"] = 1
        player["hp"] = 1
        
    if card.get("homing"): player["homing"] = True
    if "vampirism" in card: player["vampirism"] += card["vampirism"]