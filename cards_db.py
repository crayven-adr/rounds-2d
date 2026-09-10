# cards_db.py

CARDS_DB = {
    "1": {"name": "Barrage", "short": "Залп", "desc": "+4 пуль, +5 патронов, -70% DMG, +0.25s перезарядка", "rarity": "common", "rarity_color": [180, 180, 180], "bullets": 4, "ammo": 5, "dmg_mult": 0.30, "add_reload": 0.25},
    "3": {"name": "Big Bullets", "short": "Калибр", "desc": "Увеличенный размер пуль, +0.25s перезарядка", "rarity": "common", "rarity_color": [180, 180, 180], "bullet_size": 2.0, "add_reload": 0.25},
    "5": {"name": "Bouncy", "short": "Отскок", "desc": "+2 рикошета, +25% DMG, +0.25s перезарядка", "rarity": "rare", "rarity_color": [80, 160, 255], "bounces": 2, "dmg_mult": 1.25, "add_reload": 0.25},
    "7": {"name": "Buckshot", "short": "Дробь", "desc": "+4 пуль, +5 патронов, -60% DMG, +0.25s перезарядка", "rarity": "common", "rarity_color": [180, 180, 180], "bullets": 4, "ammo": 5, "dmg_mult": 0.40, "add_reload": 0.25},
    "8": {"name": "Burst", "short": "Очередь", "desc": "+2 пуль, +3 патронов, -60% DMG, +0.25s перезарядка", "rarity": "common", "rarity_color": [180, 180, 180], "bullets": 2, "ammo": 3, "dmg_mult": 0.40, "add_reload": 0.25},
    "9": {"name": "Careful Planning", "short": "Расчет", "desc": "+100% DMG, -150% ATKSPD, +0.5s перезарядка", "rarity": "epic", "rarity_color": [160, 80, 255], "dmg_mult": 2.00, "atk_spd_mult": 0.40, "add_reload": 0.50},
    "12": {"name": "Cold Bullets", "short": "Мороз", "desc": "+70% замедление врага, +0.25s перезарядка", "rarity": "rare", "rarity_color": [80, 160, 255], "slow": 0.70, "add_reload": 0.25},
    "13": {"name": "Combine", "short": "Комбайн", "desc": "+100% DMG, -2 патрона, +0.5s перезарядка", "rarity": "epic", "rarity_color": [160, 80, 255], "dmg_mult": 2.00, "ammo": -2, "add_reload": 0.50},
    "16": {"name": "Defender", "short": "Защита", "desc": "+30% HP, -30% кулдаун блока", "rarity": "common", "rarity_color": [180, 180, 180], "hp_mult": 1.30},
    "22": {"name": "Explosive Bullet", "short": "Взрыв", "desc": "Взрыв при попадании, -100% ATKSPD, +0.25s перезарядка", "rarity": "epic", "rarity_color": [160, 80, 255], "explosive": True, "atk_spd_mult": 0.50, "add_reload": 0.25},
    "23": {"name": "Fastball", "short": "Фастбол", "desc": "+250% скорость пуль, -50% ATKSPD, +0.25s перезарядка", "rarity": "rare", "rarity_color": [80, 160, 255], "bullet_spd_mult": 3.50, "atk_spd_mult": 0.50, "add_reload": 0.25},
    "24": {"name": "Fast Forward", "short": "Ускорение", "desc": "+100% скорость пуль, +30% скорость перезарядки", "rarity": "rare", "rarity_color": [80, 160, 255], "bullet_spd_mult": 2.00, "add_reload": -0.30},
    "26": {"name": "Glass Cannon", "short": "Стекло", "desc": "+100% DMG, -100% HP (Остается 1 HP), +0.25s перезарядка", "rarity": "legendary", "rarity_color": [255, 180, 0], "dmg_mult": 2.00, "glass_cannon": True, "add_reload": 0.25},
    "29": {"name": "Homing", "short": "Наводка", "desc": "Самонаведение на цель, -25% DMG, -50% ATKSPD, +0.25s перезарядка", "rarity": "legendary", "rarity_color": [255, 180, 0], "homing": True, "dmg_mult": 0.75, "atk_spd_mult": 0.50, "add_reload": 0.25},
    "30": {"name": "Huge", "short": "Гигант", "desc": "+80% HP", "rarity": "rare", "rarity_color": [80, 160, 255], "hp_mult": 1.80},
    "32": {"name": "Leech", "short": "Пиявка", "desc": "+75% вампиризм, +30% HP", "rarity": "epic", "rarity_color": [160, 80, 255], "vampirism": 0.75, "hp_mult": 1.30},
    "34": {"name": "Mayhem", "short": "Хаос", "desc": "+5 рикошетов, -15% DMG, +0.5s перезарядка", "rarity": "rare", "rarity_color": [80, 160, 255], "bounces": 5, "dmg_mult": 0.85, "add_reload": 0.50},
    "40": {"name": "Quick Reload", "short": "Ловкость", "desc": "-70% время перезарядки", "rarity": "common", "rarity_color": [180, 180, 180], "add_reload": -0.70},
    "41": {"name": "Quick Shot", "short": "Выстрел", "desc": "+150% скорость пуль, +0.25s перезарядка", "rarity": "common", "rarity_color": [180, 180, 180], "bullet_spd_mult": 2.50, "add_reload": 0.25},
    "54": {"name": "Spray", "short": "Спрей", "desc": "+1000% ATKSPD, +12 патронов, -75% DMG, +0.25s перезарядка", "rarity": "legendary", "rarity_color": [255, 180, 0], "atk_spd_mult": 10.0, "ammo": 12, "dmg_mult": 0.25, "add_reload": 0.25},
    "59": {"name": "Tank", "short": "Танк", "desc": "+100% HP, -25% ATKSPD, +0.5s перезарядка", "rarity": "epic", "rarity_color": [160, 80, 255], "hp_mult": 2.00, "atk_spd_mult": 0.75, "add_reload": 0.50},
    "61": {"name": "Taste of Blood", "short": "Кровь", "desc": "+30% вампиризм, ускорение после попадания", "rarity": "rare", "rarity_color": [80, 160, 255], "vampirism": 0.30},
    "67": {"name": "Wind Up", "short": "Завод", "desc": "+100% скорость пуль, +60% DMG, -100% ATKSPD, +0.5s перезарядка", "rarity": "epic", "rarity_color": [160, 80, 255], "bullet_spd_mult": 2.0, "dmg_mult": 1.60, "atk_spd_mult": 0.50, "add_reload": 0.50}
}