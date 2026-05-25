"""Логика игровой механики - поле, совпадения, падения блоков"""
import random
from game_config import GRID_SIZE, COLORS


class GameBoard:
    """Класс игровой доски"""
    
    def __init__(self):
        self.grid = []
        self.blocks_cleared = 0
        self.create_grid()
        
    def create_grid(self):
        """Создать новую сетку"""
        self.grid = [[random.randint(0, 7) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.blocks_cleared = 0
        # Убедиться, что есть возможные ходы
        while not self.has_possible_moves():
            self.grid = [[random.randint(0, 7) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    def get_block(self, row, col):
        """Получить блок по координатам"""
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return self.grid[row][col]
        return -1
    
    def swap_blocks(self, pos1, pos2):
        """Обменять два блока местами"""
        y1, x1 = pos1
        y2, x2 = pos2
        if 0 <= y1 < GRID_SIZE and 0 <= x1 < GRID_SIZE and \
           0 <= y2 < GRID_SIZE and 0 <= x2 < GRID_SIZE:
            self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
    
    def find_matches(self):
        """Найти все совпадения на доске"""
        matched = set()
        
        # Проверка горизонтальных совпадений
        for y in range(GRID_SIZE):
            x = 0
            while x < GRID_SIZE - 2:
                bt = self.grid[y][x]
                if bt != -1:
                    match = [(y, x)]
                    for k in range(x + 1, GRID_SIZE):
                        if self.grid[y][k] == bt:
                            match.append((y, k))
                        else:
                            break
                    if len(match) >= 3:
                        matched.update(match)
                    x += len(match)
                else:
                    x += 1
        
        # Проверка вертикальных совпадений
        for x in range(GRID_SIZE):
            y = 0
            while y < GRID_SIZE - 2:
                bt = self.grid[y][x]
                if bt != -1:
                    match = [(y, x)]
                    for k in range(y + 1, GRID_SIZE):
                        if self.grid[k][x] == bt:
                            match.append((k, x))
                        else:
                            break
                    if len(match) >= 3:
                        matched.update(match)
                    y += len(match)
                else:
                    y += 1
        
        return list(matched)
    
    def calculate_damage(self, matches_count):
        """Рассчитать урон на основе количества совпадений"""
        if matches_count < 3:
            return 0
        elif matches_count == 3:
            return 10
        elif matches_count == 4:
            return 50
        elif matches_count == 5:
            return 100
        else:  # 6+
            return 50 * (matches_count - 4)
    
    def remove_matches(self, matched):
        """Удалить совпадённые блоки"""
        for y, x in matched:
            self.grid[y][x] = -1
        self.blocks_cleared += len(matched)
        return len(matched)
    
    def collapse_grid(self):
        """Заполнить пустые места новыми блоками"""
        columns = set()
        for x in range(GRID_SIZE):
            column = []
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] != -1:
                    column.append(self.grid[y][x])
            missing = GRID_SIZE - len(column)
            new_blocks = [random.randint(0, 7) for _ in range(missing)]
            column.extend(new_blocks)
            column.reverse()
            for y in range(GRID_SIZE):
                self.grid[y][x] = column[y]
            if missing > 0:
                columns.add(x)
        return columns
    
    def has_possible_moves(self, min_moves=1):
        """Проверить наличие возможных ходов"""
        count = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < GRID_SIZE and 0 <= nx < GRID_SIZE:
                        self.swap_blocks((y, x), (ny, nx))
                        if self.find_matches():
                            count += 1
                            self.swap_blocks((y, x), (ny, nx))
                            if count >= min_moves:
                                return True
                        else:
                            self.swap_blocks((y, x), (ny, nx))
        return False
    
    def find_possible_move(self):
        """Найти один возможный ход"""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < GRID_SIZE and 0 <= nx < GRID_SIZE:
                        self.swap_blocks((y, x), (ny, nx))
                        if self.find_matches():
                            self.swap_blocks((y, x), (ny, nx))
                            return [(y, x), (ny, nx)]
                        else:
                            self.swap_blocks((y, x), (ny, nx))
        return None
