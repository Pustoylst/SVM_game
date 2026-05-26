"""Отрисовка пользовательского интерфейса"""
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
        self.load_resources()
        
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
    
    def draw_game(self):
        """Главная функция отрисовки всей игры"""
        screen.fill(BACKGROUND_COLOR)
        
        # Рисуем компоненты в правильном порядке
        self.draw_title()
        self.draw_grid()
        self.player.draw()
        self.boss.draw()
        self.draw_battle_info()
        self.draw_buttons()
        
        pygame.display.flip()
    
    def draw_buttons(self):
        """Отрисовать кнопки"""
        button_data = [
            ("Tip", 0),
            ("Help", 1),
            ("Music", 2),
            ("Scores", 3),
        ]
        
        for label, idx in button_data:
            button_y = BUTTON_OFFSET_Y + idx * (BUTTON_HEIGHT + BUTTON_SPACING)
            button_rect = pygame.Rect(BUTTON_OFFSET_X, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(screen, (50, 50, 50), button_rect)
            pygame.draw.rect(screen, (200, 200, 200), button_rect, 2)
            text_surface = button_font.render(label, True, (255, 255, 255))
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
