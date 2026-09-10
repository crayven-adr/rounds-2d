# textures.py
import pygame

class TextureManager:
    def __init__(self):
        self.fonts = {}

    def init_fonts(self):
        pygame.font.init()
        self.fonts["small"] = pygame.font.SysFont("Arial", 12, bold=True)
        self.fonts["medium"] = pygame.font.SysFont("Arial", 18, bold=True)
        self.fonts["large"] = pygame.font.SysFont("Arial", 32, bold=True)

    def draw_rounded_rect(self, surface, color, rect, radius=8):
        pygame.draw.rect(surface, color, rect, border_radius=radius)