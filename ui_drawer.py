# ui_drawer.py
import pygame
import time

def draw_player_ui(surface, player, font_small):
    x, y = int(player["x"]), int(player["y"]) - 45
    max_hp = player["max_hp"]
    current_hp = max(0, player["hp"])
    
    # 1. Полоска HP
    bar_w, bar_h = 60, 8
    pygame.draw.rect(surface, (50, 50, 50), (x - bar_w//2, y, bar_w, bar_h))
    fill_w = int((current_hp / max_hp) * bar_w)
    pygame.draw.rect(surface, (80, 220, 80), (x - bar_w//2, y, fill_w, bar_h))
    
    # 2. Полоска перезарядки / Текст патронов
    if player.get("reloading"):
        reload_bar_y = y + bar_h + 3
        now = time.time()
        reload_start = player.get("reload_timer", now) - player.get("base_reload_time", 2.0)
        total_time = player.get("base_reload_time", 2.0)
        progress = min(1.0, max(0.0, (now - reload_start) / total_time))
        
        pygame.draw.rect(surface, (40, 40, 40), (x - bar_w//2, reload_bar_y, bar_w, 5))
        pygame.draw.rect(surface, (255, 200, 50), (x - bar_w//2, reload_bar_y, int(bar_w * progress), 5))
    else:
        ammo_txt = f"{player.get('ammo', 0)}/{player.get('max_ammo', 0)}"
        txt = font_small.render(ammo_txt, True, (240, 240, 240))
        surface.blit(txt, (x - txt.get_width() // 2, y + bar_h + 2))


def draw_hud_cards(surface, game_state, my_id, font_small):
    if not game_state or not game_state.get("players"):
        return

    players = game_state["players"]
    
    my_p = players.get(str(my_id))
    if my_p:
        _render_player_card_panel(surface, f"Мои улучшения (P{my_id}):", my_p.get("card_icons", []), 20, 20, font_small)

    offset_y = 20
    for pid, p in players.items():
        if pid == str(my_id):
            continue
        icons = p.get("card_icons", [])
        if icons:
            _render_player_card_panel(surface, f"Игрок {pid}:", icons, surface.get_width() - 250, offset_y, font_small)
            offset_y += 70


def _render_player_card_panel(surface, title, icons, start_x, start_y, font_small):
    title_txt = font_small.render(title, True, (200, 200, 200))
    surface.blit(title_txt, (start_x, start_y))
    
    icon_size = 24
    for i, icon in enumerate(icons):
        ix = start_x + (i % 8) * (icon_size + 4)
        iy = start_y + 18 + (i // 8) * (icon_size + 4)
        
        pygame.draw.rect(surface, (40, 40, 50), (ix, iy, icon_size, icon_size), border_radius=4)
        pygame.draw.rect(surface, icon["color"], (ix, iy, icon_size, icon_size), width=2, border_radius=4)
        
        txt = font_small.render(icon["short"][:2], True, (255, 255, 255))
        surface.blit(txt, (ix + 3, iy + 4))