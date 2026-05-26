"""Конфигурация и константы игры"""
import pygame
import os

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Экран
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Mizzz Bloxxxxx - Battle Mode")

clock = pygame.time.Clock()

# Игровое поле
GRID_SIZE = 10
MARGIN = 10
TITLE_HEIGHT = 100
COUNTER_HEIGHT = 50
CHARACTER_MARGIN = 20
# Коэффициент уменьшения спрайтов внутри панели (1.0 = без изменения)
CHARACTER_SCALE_FACTOR = 0.9
# Смещение окна обрезки спрайта внутри панели (пиксели после масштабирования)
# Плюс по X двигает персонажа правее в панели, плюс по Y - ниже.
PLAYER_CROP_OFFSET_X = 50
PLAYER_CROP_OFFSET_Y = 0
BOSS_CROP_OFFSET_X = 40
BOSS_CROP_OFFSET_Y = 0

# Слайдеры
SLIDER_WIDTH = 20
SLIDER_HEIGHT = 150
SLIDER_SPACING = 10

# Кнопки
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
BUTTON_SPACING = 10

# Шрифты
font = pygame.font.SysFont(None, 48)
counter_font = pygame.font.SysFont(None, 36)
slider_font = pygame.font.SysFont(None, 24)
button_font = pygame.font.SysFont(None, 30)
character_font = pygame.font.SysFont(None, 28)

# Метки слайдеров
slider_labels = ['Satuation', 'Brightness', 'Contrast', 'Colormap', 'BG Brightness', 'Transparence']
label_widths = [slider_font.size(lbl)[0] for lbl in slider_labels]
max_label_width = max(label_widths)
SLIDER_OFFSET_X = MARGIN + max_label_width + 5

# Размер блока и распределение пространства между панелями персонажей и доской
available_width = SCREEN_WIDTH - 2*MARGIN - SLIDER_OFFSET_X - SLIDER_WIDTH - SLIDER_SPACING
available_height = SCREEN_HEIGHT - TITLE_HEIGHT - COUNTER_HEIGHT - 2*MARGIN

# Выделяем 2 колонки для персонажей + GRID_SIZE колонок для доски
BLOCK_SIZE = int(min(
    available_width / (GRID_SIZE + 2),
    available_height / GRID_SIZE
))

BOARD_WIDTH = GRID_SIZE * BLOCK_SIZE
BOARD_HEIGHT = GRID_SIZE * BLOCK_SIZE
TOTAL_CONTENT_HEIGHT = TITLE_HEIGHT + BOARD_HEIGHT + COUNTER_HEIGHT + 2*MARGIN

# Ширина боковых панелей определяется как остаток от доступной ширины
CHARACTER_WIDTH = int((available_width - BOARD_WIDTH) / 2 - CHARACTER_MARGIN)
if CHARACTER_WIDTH < 120:
    CHARACTER_WIDTH = 120

# Высота панели персонажа совпадает с высотой доски
CHARACTER_HEIGHT = BOARD_HEIGHT

BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_WIDTH - CHARACTER_WIDTH*2 - CHARACTER_MARGIN*2) // 2 + CHARACTER_WIDTH + CHARACTER_MARGIN
BOARD_OFFSET_Y = (SCREEN_HEIGHT - TOTAL_CONTENT_HEIGHT) // 2 + TITLE_HEIGHT + MARGIN

# Позиции персонажей
CHARACTER_OFFSET_LEFT_X = BOARD_OFFSET_X - CHARACTER_WIDTH - CHARACTER_MARGIN
CHARACTER_OFFSET_RIGHT_X = BOARD_OFFSET_X + BOARD_WIDTH + CHARACTER_MARGIN + 20
CHARACTER_OFFSET_Y = BOARD_OFFSET_Y

SLIDER_OFFSET_Y = BOARD_OFFSET_Y

BUTTON_OFFSET_X = SCREEN_WIDTH - MARGIN - BUTTON_WIDTH
BUTTON_OFFSET_Y = MARGIN

BACKGROUND_COLOR = (0, 0, 0)

# Цвета блоков
COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 165, 0),
    (128, 0, 128),
    (0, 255, 255),
    (255, 192, 203)
]

# Цвета персонажей
PLAYER_COLOR = (100, 200, 100)  # Зелёный
BOSS_COLOR = (200, 50, 50)      # Красный
CHARACTER_BG_COLOR = (30, 30, 30)
CHARACTER_BORDER_COLOR = (150, 150, 150)

# Директория данных
DATA_DIR = 'SVM_game/data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

TOP5_FILE = os.path.join(DATA_DIR, 'top5.txt')
