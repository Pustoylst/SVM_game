"""Класс персонажей для игры"""
import pygame
from game_config import (
    CHARACTER_WIDTH, CHARACTER_HEIGHT, CHARACTER_OFFSET_Y, CHARACTER_OFFSET_LEFT_X, 
    CHARACTER_OFFSET_RIGHT_X, character_font, CHARACTER_BG_COLOR, CHARACTER_BORDER_COLOR,
    PLAYER_COLOR, BOSS_COLOR, screen,
    PLAYER_CROP_OFFSET_X, PLAYER_CROP_OFFSET_Y, BOSS_CROP_OFFSET_X, BOSS_CROP_OFFSET_Y
)
from game_config import CHARACTER_SCALE_FACTOR


class Character:
    """Базовый класс персонажа"""
    
    def __init__(self, name, x, y, color, max_hp=1000, crop_offset_x=0, crop_offset_y=0):
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.max_hp = max_hp
        self.hp = max_hp
        self.width = CHARACTER_WIDTH
        self.height = CHARACTER_HEIGHT
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image_original = None
        self.image = None
        self.crop_offset_x = crop_offset_x
        self.crop_offset_y = crop_offset_y
        self._load_image_if_exists()
        
    def take_damage(self, damage):
        """Получить урон"""
        self.hp = max(0, self.hp - damage)
        
    def heal(self, amount):
        """Восстановить здоровье"""
        self.hp = min(self.max_hp, self.hp + amount)
        
    def get_hp_percent(self):
        """Получить процент здоровья"""
        if self.max_hp == 0:
            return 0
        return self.hp / self.max_hp
        
    def is_alive(self):
        """Жив ли персонаж"""
        return self.hp > 0
        
    def draw(self):
        """Отрисовать персонажа"""
        # Фон (без рамки)
        pygame.draw.rect(screen, CHARACTER_BG_COLOR, self.rect)
        
        # Область для здоровья
        hp_bar_width = self.width - 10
        hp_bar_height = 20
        hp_bar_x = self.x + 5
        hp_bar_y = self.y + 10
        
        # Фон полоски здоровья (красный)
        hp_bg_rect = pygame.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height)
        pygame.draw.rect(screen, (100, 0, 0), hp_bg_rect)
        pygame.draw.rect(screen, CHARACTER_BORDER_COLOR, hp_bg_rect, 1)
        
        # Сама полоска здоровья
        hp_percent = self.get_hp_percent()
        hp_fill_width = hp_bar_width * hp_percent
        hp_fill_rect = pygame.Rect(hp_bar_x, hp_bar_y, hp_fill_width, hp_bar_height)
        pygame.draw.rect(screen, self.color, hp_fill_rect)
        
        # Текст ХП
        hp_text = f"{int(self.hp)}/{int(self.max_hp)}"
        hp_surface = character_font.render(hp_text, True, (255, 255, 255))
        hp_text_rect = hp_surface.get_rect(center=(self.x + self.width//2, hp_bar_y + hp_bar_height//2))
        screen.blit(hp_surface, hp_text_rect)
        # Имя персонажа (рядом с ХП)
        name_surface = character_font.render(self.name, True, self.color)
        name_rect = name_surface.get_rect(center=(self.x + self.width//2, hp_bar_y + hp_bar_height + 12))
        screen.blit(name_surface, name_rect)

        # Основная область для спрайта: занимает почти всю панель под HP и именем
        sprite_top = name_rect.bottom + 6
        sprite_rect = pygame.Rect(self.x + 5, sprite_top, self.width - 10, self.height - (sprite_top - self.y) - 6)

        if sprite_rect.height < 10:
            sprite_rect.height = max(10, self.height - (hp_bar_height + 40))

        if self.image_original:
            # Масштабируем с сохранением пропорций и обрезкой (cover)
            iw, ih = self.image_original.get_width(), self.image_original.get_height()
            panel_w, panel_h = sprite_rect.width, sprite_rect.height
            # Уменьшаем целевую область спрайта на коэффициент, чтобы он точно влезал
            tw = max(1, int(panel_w * CHARACTER_SCALE_FACTOR))
            th = max(1, int(panel_h * CHARACTER_SCALE_FACTOR))
            if iw == 0 or ih == 0:
                # Защита от деления на ноль
                pygame.draw.rect(screen, self.color, sprite_rect)
            else:
                scale = max(tw / iw, th / ih)
                new_w = max(1, int(iw * scale))
                new_h = max(1, int(ih * scale))
                try:
                    scaled = pygame.transform.smoothscale(self.image_original, (new_w, new_h))
                except Exception:
                    scaled = pygame.transform.scale(self.image_original, (new_w, new_h))
                # Рендерим в отдельную поверхность уменьшенного размера и центрируем её в панели
                surf = pygame.Surface((tw, th), pygame.SRCALPHA)
                crop_x = (new_w - tw) // 2 - self.crop_offset_x
                crop_y = (new_h - th) // 2 - self.crop_offset_y
                crop_x = max(0, min(crop_x, new_w - tw))
                crop_y = max(0, min(crop_y, new_h - th))
                surf.blit(scaled, (-crop_x, -crop_y))
                blit_x = sprite_rect.x + (panel_w - tw) // 2
                blit_y = sprite_rect.y + (panel_h - th) // 2
                screen.blit(surf, (blit_x, blit_y))
        else:
            pygame.draw.rect(screen, self.color, sprite_rect)

    def _load_image_if_exists(self):
        """Попытаться загрузить изображение персонажа из папки data/ (hero/boss либо имя)."""
        from pathlib import Path
        data_dir = Path('SVM_game/data')
        if not data_dir.exists():
            return
        name_variants = []
        n = self.name.lower()
        # Обычные варианты: hero для игрока, boss для босса
        if n in ('player', 'hero'):
            name_variants.append('hero')
        if 'boss' in n:
            name_variants.append('boss')
        # Всегда проверяем само имя
        name_variants.append(n)

        exts = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']
        for base in name_variants:
            for ext in exts:
                p = data_dir / (base + ext)
                if p.is_file():
                    try:
                        img = pygame.image.load(str(p)).convert_alpha()
                        bbox = img.get_bounding_rect()
                        if bbox.width > 0 and bbox.height > 0 and bbox != img.get_rect():
                            img = img.subsurface(bbox).copy()
                        self.image_original = img
                        return
                    except Exception:
                        # Если не удалось загрузить, продолжаем искать
                        self.image_original = None
        # Если ничего не найдено — оставить None


class Player(Character):
    """Класс игрока"""
    
    def __init__(self):
        super().__init__(
            name="Player",
            x=CHARACTER_OFFSET_LEFT_X,
            y=CHARACTER_OFFSET_Y,
            color=PLAYER_COLOR,
            max_hp=1000,
            crop_offset_x=PLAYER_CROP_OFFSET_X,
            crop_offset_y=PLAYER_CROP_OFFSET_Y
        )


class Boss(Character):
    """Класс босса"""
    
    def __init__(self):
        super().__init__(
            name="Boss",
            x=CHARACTER_OFFSET_RIGHT_X,
            y=CHARACTER_OFFSET_Y,
            color=BOSS_COLOR,
            max_hp=5000,
            crop_offset_x=BOSS_CROP_OFFSET_X,
            crop_offset_y=BOSS_CROP_OFFSET_Y
        )
