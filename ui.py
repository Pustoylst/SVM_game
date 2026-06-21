"""Отрисовка пользовательского интерфейса"""
import time
import random
import pygame
from game_config import (
    screen, SCREEN_WIDTH, SCREEN_HEIGHT, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    BOARD_WIDTH, BOARD_HEIGHT, BLOCK_SIZE, GRID_SIZE, GRID_SIZE as GRID_SIZE_IMPORT,
    COLORS, BACKGROUND_COLOR, MARGIN, counter_font, font, button_font,
    BUTTON_OFFSET_X, BUTTON_OFFSET_Y, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING
)
from game_config import DATA_DIR
import os


class GameRenderer:
    """Класс для отрисовки игры"""
    
    def __init__(self, game_board, player, boss):
        self.board = game_board
        self.player = player
        self.boss = boss
        self.selected_block = None
        self.grid_lines_surface = None
        self.create_grid_lines_surface()
        self.block_images = []
        self.background_image = None
        self.hint_move = None
        self.hint_until = 0.0
        self.help_used = False
        self.boss_phrase = None
        self.boss_phrase_until = 0.0
        self.last_boss_phrase_time = time.time()
        self.last_boss_phrase_text = None
        self.boss_phrases = [
            "Избегайте двусмысленности",
            "Я гроза гаджетников",
            "Что, опять неудача?",
            "У вас нет ничего предосудительного?",
        ]
        self.status_message = None
        self.status_message_until = 0.0
        self.load_resources()

    def show_hint(self, move, duration=3.0):
        """Показать визуальную подсказку для хода."""
        self.hint_move = move
        self.hint_until = time.time() + duration

    def clear_hint(self):
        """Скрыть подсказку."""
        self.hint_move = None
        self.hint_until = 0.0

    def set_help_used(self, used=True):
        """Отметить кнопку Help как использованную."""
        self.help_used = used

    def get_button_at_position(self, mouse_pos):
        """Вернуть индекс кнопки, если клик был по панели кнопок."""
        x, y = mouse_pos
        if x < BUTTON_OFFSET_X or x > BUTTON_OFFSET_X + BUTTON_WIDTH:
            return None

        button_data = ["Help", "Music", "Scores", "AI"]
        for idx in range(len(button_data)):
            button_y = BUTTON_OFFSET_Y + idx * (BUTTON_HEIGHT + BUTTON_SPACING)
            button_rect = pygame.Rect(BUTTON_OFFSET_X, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            if button_rect.collidepoint(x, y):
                return idx
        return None

    def is_help_button(self, mouse_pos):
        """Проверить, нажата ли кнопка Help."""
        return self.get_button_at_position(mouse_pos) == 1
        
    def create_grid_lines_surface(self):
        """Создать поверхность с линиями сетки"""
        self.grid_lines_surface = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        self.grid_lines_surface = self.grid_lines_surface.convert_alpha()
        alpha_val = int(255 * 0.2)
        line_col = (200, 200, 200, alpha_val)
        for y in range(GRID_SIZE_IMPORT):
            for x in range(GRID_SIZE_IMPORT):
                rc = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(self.grid_lines_surface, line_col, rc, 1)
    
    def load_resources(self):
        """Загрузить ресурсы (изображения и т.д.)"""
        # Попытаться загрузить изображения блоков из папки data/
        self.block_images = []
        try:
            for i in range(1, 9):
                path = os.path.join(DATA_DIR, f'block{i}.png')
                if os.path.isfile(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        img = pygame.transform.smoothscale(img, (BLOCK_SIZE, BLOCK_SIZE))
                        self.block_images.append(img)
                    except Exception:
                        # При ошибке загрузки — отказаться от изображений
                        self.block_images = []
                        break
                else:
                    # Если хотя бы одного файла нет — не использовать набор изображений
                    self.block_images = []
                    break
        except Exception:
            self.block_images = []
    
    def draw_grid(self):
        """Отрисовать основную доску с блоками"""
        for y in range(GRID_SIZE_IMPORT):
            for x in range(GRID_SIZE_IMPORT):
                block_type = self.board.get_block(y, x)
                if block_type == -1:
                    continue
                
                bx = BOARD_OFFSET_X + x * BLOCK_SIZE
                by = BOARD_OFFSET_Y + y * BLOCK_SIZE
                rect = pygame.Rect(bx, by, BLOCK_SIZE, BLOCK_SIZE)
                
                # Получить цвет блока
                if 0 <= block_type < len(COLORS):
                    color = COLORS[block_type]
                else:
                    color = (200, 200, 200)
                
                # Нарисовать блок — картинка если есть, иначе цветной прямоугольник
                if self.block_images and 0 <= block_type < len(self.block_images):
                    img = self.block_images[block_type]
                    screen.blit(img, (bx, by))
                    pygame.draw.rect(screen, (100, 100, 100), rect, 2)
                else:
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (100, 100, 100), rect, 2)
                
                # Если блок выбран, подсветить его
                if self.selected_block == (y, x):
                    pygame.draw.rect(screen, (255, 255, 255), rect, 4)
        
        # Нарисовать сетку
        screen.blit(self.grid_lines_surface, (BOARD_OFFSET_X, BOARD_OFFSET_Y))

    def draw_hint_overlay(self):
        """Подсветить блоки для подсказки без текста."""
        if not self.hint_move or time.time() > self.hint_until:
            return

        start, end = self.hint_move
        pulse = 0.5 + 0.5 * (time.time() * 4 % 1)
        alpha = int(100 + 100 * pulse)

        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)

        for cell, fill_color, border_color, border_width in (
            (start, (0, 255, 120, alpha), (255, 255, 255, 240), 4),
            (end, (255, 220, 0, alpha), (255, 255, 255, 240), 5),
        ):
            y, x = cell
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(overlay, fill_color, rect)
            pygame.draw.rect(overlay, border_color, rect, border_width)

        start_center = (
            start[1] * BLOCK_SIZE + BLOCK_SIZE // 2,
            start[0] * BLOCK_SIZE + BLOCK_SIZE // 2,
        )
        end_center = (
            end[1] * BLOCK_SIZE + BLOCK_SIZE // 2,
            end[0] * BLOCK_SIZE + BLOCK_SIZE // 2,
        )
        pygame.draw.line(overlay, (255, 255, 255, 220), start_center, end_center, 6)
        pygame.draw.circle(overlay, (255, 255, 255, 220), start_center, 10)
        pygame.draw.circle(overlay, (255, 255, 255, 220), end_center, 10)

        screen.blit(overlay, (BOARD_OFFSET_X, BOARD_OFFSET_Y))

    def draw_boss_phrase(self):
        """Показать облачко фразы босса над его панелью."""
        if not self.boss or not hasattr(self.boss, 'rect'):
            return
        now = time.time()
        # schedule phrase every 10s
        if now - self.last_boss_phrase_time >= 10 and now > self.boss_phrase_until:
            available_phrases = [p for p in self.boss_phrases if p != self.last_boss_phrase_text]
            if not available_phrases:
                available_phrases = self.boss_phrases[:]
            self.boss_phrase = random.choice(available_phrases)
            self.last_boss_phrase_text = self.boss_phrase
            self.boss_phrase_until = now + 3.0
            self.last_boss_phrase_time = now

        if not self.boss_phrase or now > self.boss_phrase_until:
            return

        # render bubble
        text_surf = button_font.render(self.boss_phrase, True, (20, 20, 20))
        pad = 10
        w = text_surf.get_width() + pad * 2
        h = text_surf.get_height() + pad * 2

        # position centered above boss panel
        bx = self.boss.rect.x + (self.boss.rect.width - w) // 2
        by = max(8, self.boss.rect.y - h - 12)

        bubble = pygame.Surface((w, h), pygame.SRCALPHA)
        bubble.fill((255, 255, 255, 240))
        pygame.draw.rect(bubble, (120, 120, 120), bubble.get_rect(), 2, border_radius=8)
        bubble.blit(text_surf, (pad, pad))

        screen.blit(bubble, (bx, by))

        # pointer triangle
        pointer_cx = bx + w // 2
        p_top = by + h
        p = [(pointer_cx - 8, p_top), (pointer_cx + 8, p_top), (pointer_cx, p_top + 10)]
        pygame.draw.polygon(screen, (255, 255, 255), p)
        pygame.draw.polygon(screen, (120, 120, 120), p, 1)
    
    def draw_battle_info(self):
        """Отрисовать информацию о боевых действиях"""
        # Информация об очищенных блоках
        info_text = f"Cleared: {self.board.blocks_cleared}"
        info_surface = counter_font.render(info_text, True, (200, 200, 200))
        info_rect = info_surface.get_rect(center=(SCREEN_WIDTH // 2, BOARD_OFFSET_Y + BOARD_HEIGHT + 20))
        screen.blit(info_surface, info_rect)
    
    def draw_title(self):
        """Отрисовать заголовок игры"""
        title_text = "SVM BATTLE"
        title_surface = font.render(title_text, True, (255, 255, 255))
        title_shadow = font.render(title_text, True, (0, 0, 0))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        shadow_rect = title_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title_surface, title_rect)

    def draw_status_message(self):
        """Отрисовать временное сообщение в верхней части экрана."""
        if not self.status_message or time.time() > self.status_message_until:
            return

        message_surface = button_font.render(self.status_message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(center=(SCREEN_WIDTH // 2, 86))
        background_rect = message_rect.inflate(24, 16)

        background_surface = pygame.Surface(background_rect.size, pygame.SRCALPHA)
        background_surface.fill((0, 0, 0, 170))
        screen.blit(background_surface, background_rect)
        pygame.draw.rect(screen, (220, 220, 220), background_rect, 2, border_radius=8)
        screen.blit(message_surface, message_rect)
    
    def draw_game(self):
        """Главная функция отрисовки всей игры"""
        screen.fill(BACKGROUND_COLOR)

        if self.hint_move and time.time() > self.hint_until:
            self.clear_hint()
        
        # Рисуем компоненты в правильном порядке
        self.draw_title()
        self.draw_status_message()
        self.draw_grid()
        self.draw_hint_overlay()
        self.player.draw()
        self.boss.draw()
        self.draw_boss_phrase()
        self.draw_battle_info()
        self.draw_buttons()
        
        pygame.display.flip()
    
    def draw_buttons(self):
        """Отрисовать кнопки"""
        button_data = [
            ("Help", 0),
            ("Music", 1),
            ("Scores", 2),
            ("AI", 3),
        ]
        
        for label, idx in button_data:
            button_y = BUTTON_OFFSET_Y + idx * (BUTTON_HEIGHT + BUTTON_SPACING)
            button_rect = pygame.Rect(BUTTON_OFFSET_X, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            is_help_used = label == "Help" and self.help_used
            button_color = (45, 45, 45) if not is_help_used else (70, 70, 70)
            border_color = (200, 200, 200) if not is_help_used else (120, 120, 120)
            text_label = label if not is_help_used else "Help (used)"
            text_color = (255, 255, 255) if not is_help_used else (180, 180, 180)

            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, border_color, button_rect, 2)
            text_surface = button_font.render(text_label, True, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)


def get_block_at_position(mouse_pos):
    """Получить координаты блока по позиции мыши"""
    x, y = mouse_pos
    if x < BOARD_OFFSET_X or x > BOARD_OFFSET_X + BOARD_WIDTH:
        return None
    if y < BOARD_OFFSET_Y or y > BOARD_OFFSET_Y + BOARD_HEIGHT:
        return None
    
    grid_x = (x - BOARD_OFFSET_X) // BLOCK_SIZE
    grid_y = (y - BOARD_OFFSET_Y) // BLOCK_SIZE
    
    if 0 <= grid_x < GRID_SIZE_IMPORT and 0 <= grid_y < GRID_SIZE_IMPORT:
        return (grid_y, grid_x)
    return None
