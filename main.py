"""Главный файл игры - Mizzz Bloxxxxx Battle Mode"""
import pygame
import sys
import time
import os
import random
from game_config import screen, clock, SCREEN_HEIGHT, SCREEN_WIDTH, play_main_theme, toggle_music, button_font, font, counter_font
from game_config import DATA_DIR
import game_config
from game_logic import GameBoard
from genetic import heuristic_value, GeneticOptimizer
from character import Player, Boss
from ui import GameRenderer, get_block_at_position


class BattleGame:
    """Главный класс игры в режиме боя"""
    
    def __init__(self):
        pygame.init()
        self.board = GameBoard()
        self.player = Player()
        self.boss = Boss()
        self.renderer = GameRenderer(self.board, self.player, self.boss)
        self.running = True
        self.start_time = time.time()
        self.selected_block = None
        self.animation_in_progress = False
        self.music_on = False
        self.help_used = False
        self.quiz_active = False
        self.quiz_question = None
        self.quiz_options = []
        self.quiz_correct_index = -1
        self.quiz_deadline = 0.0
        self.next_quiz_time = time.time() + random.randint(12, 22)
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""
        self.restart_button_rect = pygame.Rect(0, 0, 260, 64)
        self.start_music()

    def start_music(self):
        """Запустить главную тему при старте игры."""
        try:
            play_main_theme(loop=True)
            self.music_on = True
        except Exception:
            self.music_on = False
        
    def handle_click(self, pos):
        """Обработать клик мыши"""
        if self.game_over:
            if self.restart_button_rect.collidepoint(pos):
                self.reset_game()
            return

        if self.victory:
            if self.restart_button_rect.collidepoint(pos):
                self.reset_game()
            return

        if self.quiz_active:
            self.handle_quiz_click(pos)
            return

        button_index = self.renderer.get_button_at_position(pos)

        if button_index == 1:
            if self.help_used:
                self.renderer.clear_hint()
                return

            move = self.board.find_possible_move()
            if move:
                self.renderer.show_hint(move)
                self.player.take_damage(999)
                if not self.player.is_alive():
                    self.fail_game("HP игрока исчерпано")
                self.help_used = True
                self.renderer.set_help_used(True)
            else:
                self.renderer.clear_hint()
            return

        if button_index == 2:
            try:
                toggle_music()
                self.music_on = not self.music_on
            except Exception:
                self.music_on = False
            return

        # AI / show best move
        if button_index == 4:
            # try load best weights
            try:
                import os
                path = os.path.join(DATA_DIR, 'best_ga_weights.json')
                if os.path.isfile(path):
                    opt = GeneticOptimizer()
                    chrom, score = opt.load(path)
                    if chrom is None:
                        self.renderer.status_message = "No GA weights found"
                        self.renderer.status_message_until = time.time() + 3.0
                        return
                    # find best move according to heuristic
                    best_move = None
                    best_value = -1e18
                    for y in range(len(self.board.grid)):
                        for x in range(len(self.board.grid[0])):
                            for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                                ny, nx = y+dy, x+dx
                                if 0 <= ny < len(self.board.grid) and 0 <= nx < len(self.board.grid[0]):
                                    self.board.swap_blocks((y,x),(ny,nx))
                                    matches = self.board.find_matches()
                                    val = heuristic_value(self.board, matches, chrom)
                                    self.board.swap_blocks((y,x),(ny,nx))
                                    if val > best_value:
                                        best_value = val
                                        best_move = ((y,x),(ny,nx))
                    if best_move:
                        self.renderer.show_hint(best_move, duration=6.0)
                        self.renderer.status_message = "AI: best move shown"
                        self.renderer.status_message_until = time.time() + 3.0
                    else:
                        self.renderer.status_message = "AI: no move found"
                        self.renderer.status_message_until = time.time() + 3.0
                else:
                    self.renderer.status_message = "AI weights not found"
                    self.renderer.status_message_until = time.time() + 3.0
            except Exception:
                self.renderer.status_message = "AI error"
                self.renderer.status_message_until = time.time() + 3.0
            return

        block = get_block_at_position(pos)
        if block is None:
            self.selected_block = None
            self.renderer.selected_block = None
            return

        if self.selected_block is None:
            # Выбрали первый блок
            self.selected_block = block
            self.renderer.selected_block = block
        else:
            # Выбрали второй блок
            y1, x1 = self.selected_block
            y2, x2 = block

            # Проверить, соседние ли блоки
            if abs(y1 - y2) + abs(x1 - x2) == 1:
                # Попытаться поменять блоки
                self.try_swap(self.selected_block, block)

            # Сбросить выделение
            self.selected_block = None
            self.renderer.selected_block = None

    def generate_quiz(self):
        """Сгенерировать простой вопрос с тремя вариантами ответа."""
        quiz_bank = [
            {
                "question": "Интеграл: int 1 dx = ?",
                "options": ["x + C", "x^2 + C", "1/x + C"],
                "correct": 0,
            },
            {
                "question": "Интеграл: int x dx = ?",
                "options": ["x^2 + C", "x^2 / 2 + C", "2x + C"],
                "correct": 1,
            },
            {
                "question": "Интеграл: int 2x dx = ?",
                "options": ["x^2 + C", "2x^2 + C", "x + C"],
                "correct": 0,
            },
            {
                "question": "Интеграл: int 0 dx = ?",
                "options": ["0", "x + C", "C"],
                "correct": 2,
            },
            {
                "question": "Интеграл: int x^2 dx = ?",
                "options": ["x^3 / 3 + C", "x^2 / 3 + C", "3x^2 + C"],
                "correct": 0,
            },
            {
                "question": "Интеграл: int 3 dx = ?",
                "options": ["3x + C", "x^3 + C", "x / 3 + C"],
                "correct": 0,
            },
            {
                "question": "Посчитай: \u221a121 = ?",
                "options": ["10", "11", "12"],
                "correct": 1,
            },
            {
                "question": "Посчитай: \u221a144 = ?",
                "options": ["11", "12", "13"],
                "correct": 1,
            },
            {
                "question": "Посчитай: \u221a169 = ?",
                "options": ["12", "13", "14"],
                "correct": 1,
            },
            {
                "question": "Посчитай: \u221a196 = ?",
                "options": ["13", "14", "15"],
                "correct": 1,
            },
            {
                "question": "Посчитай: \u221a225 = ?",
                "options": ["14", "15", "16"],
                "correct": 1,
            },
            {
                "question": "Посчитай: \u221a256 = ?",
                "options": ["15", "16", "17"],
                "correct": 1,
            },
            {
                "question": "Предел: lim x->0 sin(x) / x = ?",
                "options": ["0", "1", "-1"],
                "correct": 1,
            },
            {
                "question": "Предел: lim x->1 (x^2 - 1) / (x - 1) = ?",
                "options": ["1", "2", "3"],
                "correct": 1,
            },
            {
                "question": "Предел: lim x->0 (1 - cos(x)) / x^2 = ?",
                "options": ["0", "1/2", "1"],
                "correct": 1,
            },
            {
                "question": "Предел: lim x->0 (e^x - 1) / x = ?",
                "options": ["0", "1", "e"],
                "correct": 1,
            },
            {
                "question": "Предел: lim x->2 (x^2 - 4) / (x - 2) = ?",
                "options": ["2", "4", "6"],
                "correct": 2,
            },
            {
                "question": "Предел: lim x->0 \u221a(1 + x) = ?",
                "options": ["0", "1", "2"],
                "correct": 1,
            },
            {
                "question": "Предел: lim x->0 (x^2 + 3x) / x = ?",
                "options": ["3", "4", "0"],
                "correct": 0,
            },
            {
                "question": "Предел: lim x->0 (sin(2x) / x) = ?",
                "options": ["1", "2", "4"],
                "correct": 1,
            },
        ]
        return random.choice(quiz_bank)

    def start_quiz(self):
        """Запустить математический вопрос."""
        quiz = self.generate_quiz()
        self.quiz_question = quiz["question"]
        self.quiz_options = quiz["options"]
        self.quiz_correct_index = quiz["correct"]
        self.quiz_deadline = time.time() + 10.0
        self.quiz_active = True

    def fail_game(self, reason):
        """Завершить игру поражением."""
        self.game_over = True
        self.game_over_reason = reason
        self.quiz_active = False
        self.quiz_question = None
        self.quiz_options = []
        self.quiz_correct_index = -1
        self.quiz_deadline = 0.0
        self.selected_block = None
        self.renderer.selected_block = None

    def reset_game(self):
        """Перезапустить бой после game over."""
        self.board = GameBoard()
        self.player = Player()
        self.boss = Boss()
        self.renderer = GameRenderer(self.board, self.player, self.boss)
        self.selected_block = None
        self.animation_in_progress = False
        self.music_on = False
        self.help_used = False
        self.quiz_active = False
        self.quiz_question = None
        self.quiz_options = []
        self.quiz_correct_index = -1
        self.quiz_deadline = 0.0
        self.next_quiz_time = time.time() + random.randint(12, 22)
        self.game_over = False
        self.game_over_reason = ""
        self.start_time = time.time()
        self.start_music()

    def handle_quiz_click(self, pos):
        """Обработать клик по вариантам ответа."""
        if not self.quiz_active or self.quiz_question is None:
            return

        option_y = SCREEN_HEIGHT // 2 - 10
        option_w = 280
        option_h = 56
        option_spacing = 18
        total_w = option_w * 3 + option_spacing * 2
        start_x = (SCREEN_WIDTH - total_w) // 2

        for index in range(3):
            rect = pygame.Rect(start_x + index * (option_w + option_spacing), option_y, option_w, option_h)
            if rect.collidepoint(pos):
                if index == self.quiz_correct_index:
                    self.quiz_active = False
                    self.quiz_question = None
                    self.quiz_options = []
                    self.quiz_correct_index = -1
                    self.quiz_deadline = 0.0
                    self.next_quiz_time = time.time() + random.randint(15, 30)
                else:
                    self.fail_game("Неверный ответ")
                return
    
    def try_swap(self, pos1, pos2):
        """Попытаться поменять блоки и найти совпадения"""
        # Поменять блоки
        self.board.swap_blocks(pos1, pos2)
        
        # Найти совпадения
        matches = self.board.find_matches()
        
        if matches:
            # Есть совпадения! Обрабатываем их
            self.process_matches(matches)
        else:
            # Нет совпадений, вернуть блоки обратно и наказать игрока
            self.board.swap_blocks(pos1, pos2)
            try:
                self.player.take_damage(500)
            except Exception:
                # На случай, если player отсутствует или метод сломан — просто пропустить
                pass
            # Если здоровье игрока исчерпано — конец игры
            if not self.player.is_alive():
                self.fail_game("HP игрока исчерпано")
    
    def process_matches(self, matches):
        """Обработать найденные совпадения"""
        if self.quiz_active:
            return

        matches_count = len(matches)
        
        # Убрать совпадённые блоки
        self.board.remove_matches(matches)
        
        # Рассчитать урон
        damage = self.board.calculate_damage(matches_count)
        
        # Нанести урон боссу
        self.boss.take_damage(damage)
        
        # Заполнить пустые места
        self.board.collapse_grid()
        
        print(f"Match! Damage to boss: {damage}, Boss HP: {int(self.boss.hp)}/{int(self.boss.max_hp)}")
    
    def check_game_state(self):
        """Проверить состояние игры"""
        if self.game_over:
            return True

        if self.quiz_active:
            if time.time() > self.quiz_deadline:
                self.fail_game("Время вышло")
                return True
            return True

        if time.time() >= self.next_quiz_time:
            self.start_quiz()
            return True

        if not self.boss.is_alive():
            # Победа над боссом — показать экран победы
            print(f"Boss defeated! You won! Time: {time.time() - self.start_time:.2f}s")
            self.victory = True
            return True
        
        if not self.board.has_possible_moves():
            print("No more moves available!")
            return False
        
        return True
    
    def handle_events(self):
        """Обработать события"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in (pygame.K_j, pygame.K_t):
                    # J/T - показать подсказку
                    move = self.board.find_possible_move()
                    if move:
                        self.renderer.show_hint(move)
                    else:
                        self.renderer.clear_hint()
    
    def run(self):
        """Главный цикл игры"""
        while self.running:
            self.handle_events()
            
            if self.game_over:
                self.draw_game_over_screen()
                pygame.display.flip()
                clock.tick(60)
                continue

            if self.victory:
                self.draw_victory_screen()
                pygame.display.flip()
                clock.tick(60)
                continue

            # Проверить состояние игры
            if not self.check_game_state():
                self.running = False
                continue

            if self.quiz_active:
                self.draw_quiz_overlay()
                pygame.display.flip()
                clock.tick(60)
                continue

            # Отрисовать
            self.renderer.draw_game()

            pygame.display.flip()

            # FPS
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

    def draw_quiz_overlay(self):
        """Нарисовать вопрос и варианты ответа поверх игры."""
        if not self.quiz_active or self.quiz_question is None:
            return

        now = time.time()
        remaining = max(0, int(self.quiz_deadline - now) + (1 if self.quiz_deadline - now > int(self.quiz_deadline - now) else 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        panel_w = min(900, SCREEN_WIDTH - 160)
        panel_h = 320
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2 - 40
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surf.fill((18, 18, 18, 245))
        pygame.draw.rect(panel_surf, (255, 255, 255), panel_surf.get_rect(), 2, border_radius=14)

        title = font.render("Вопрос преподавателя", True, (255, 230, 120))
        panel_surf.blit(title, title.get_rect(center=(panel_w // 2, 42)))

        question_surf = button_font.render(self.quiz_question, True, (240, 240, 240))
        panel_surf.blit(question_surf, question_surf.get_rect(center=(panel_w // 2, 110)))

        timer_text = f"Осталось: {remaining} c"
        timer_surf = button_font.render(timer_text, True, (255, 180, 180))
        panel_surf.blit(timer_surf, timer_surf.get_rect(center=(panel_w // 2, 150)))

        option_w = 280
        option_h = 56
        option_spacing = 18
        total_w = option_w * 3 + option_spacing * 2
        start_x = (panel_w - total_w) // 2
        option_y = 200

        for index, option_text in enumerate(self.quiz_options):
            rect = pygame.Rect(start_x + index * (option_w + option_spacing), option_y, option_w, option_h)
            pygame.draw.rect(panel_surf, (42, 42, 42), rect, border_radius=10)
            pygame.draw.rect(panel_surf, (200, 200, 200), rect, 2, border_radius=10)
            option_surf = button_font.render(option_text, True, (255, 255, 255))
            panel_surf.blit(option_surf, option_surf.get_rect(center=rect.center))

        screen.blit(panel_surf, panel_rect.topleft)

    def draw_game_over_screen(self):
        """Показать экран поражения."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        title_surf = font.render("GAME OVER", True, (255, 80, 80))
        score_surf = font.render("0 баллов", True, (255, 255, 255))
        reason_surf = button_font.render(self.game_over_reason, True, (220, 220, 220))

        self.restart_button_rect = pygame.Rect(0, 0, 260, 64)
        self.restart_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140)
        pygame.draw.rect(screen, (50, 50, 50), self.restart_button_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), self.restart_button_rect, 2, border_radius=12)
        restart_surf = button_font.render("Начать заново", True, (255, 255, 255))
        screen.blit(restart_surf, restart_surf.get_rect(center=self.restart_button_rect.center))

        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
        screen.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))
        screen.blit(reason_surf, reason_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)))

    def draw_victory_screen(self):
        """Показать экран победы."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        title_surf = font.render("ПОБЕДА", True, (120, 255, 120))
        score_surf = font.render("100 баллов", True, (255, 255, 255))

        self.restart_button_rect = pygame.Rect(0, 0, 260, 64)
        self.restart_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140)
        pygame.draw.rect(screen, (50, 50, 50), self.restart_button_rect, border_radius=12)
        pygame.draw.rect(screen, (220, 220, 220), self.restart_button_rect, 2, border_radius=12)
        restart_surf = button_font.render("Начать заново", True, (255, 255, 255))
        screen.blit(restart_surf, restart_surf.get_rect(center=self.restart_button_rect.center))

        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
        screen.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))


def main():
    """Точка входа: показать дисклеймер, меню, затем игру"""
    pygame.init()

    def show_disclaimer():
        text = (
            "Все совпадения лиц, имён, событий и прочих элементов с реальными людьми "
            "или обстоятельствами являются чистой случайностью. Любые сходства не "
            "преднамеренны и автор не имеют к этому отношения."
        )
        hint = "Нажмите любую клавишу или кликните, чтобы продолжить"

        def wrap_text(s, max_width, render_font):
            words = s.split(' ')
            lines = []
            cur = ''
            for w in words:
                test = (cur + ' ' + w).strip()
                if render_font.size(test)[0] <= max_width:
                    cur = test
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return lines

        # Centered text drawing helper
        def draw_centered_line(surface, text, render_font, x, y, max_width, color=(220,220,220)):
            surf = render_font.render(text, True, color)
            rect = surf.get_rect(center=(x + max_width // 2, y + surf.get_height() // 2))
            surface.blit(surf, rect)
            return surf.get_height()

        panel_w = min(900, SCREEN_WIDTH - 200)
        panel_h = min(420, SCREEN_HEIGHT - 200)
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2

        lines = wrap_text(text, panel_w - 80, font)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

            # Dim background
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            # Panel
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            panel_surf.fill((18, 18, 18, 240))
            pygame.draw.rect(panel_surf, (255, 255, 255), panel_surf.get_rect(), 2, border_radius=12)

            # Title
            title_surf = font.render("Дисклеймер", True, (255, 230, 120))
            panel_surf.blit(title_surf, title_surf.get_rect(center=(panel_w // 2, 48)))

            # Body (centered)
            y = 100
            text_x = 40
            text_width = panel_w - 80
            for line in lines:
                h = draw_centered_line(panel_surf, line, button_font, text_x, y, text_width)
                y += h + 8

            # Hint
            hint_surf = button_font.render(hint, True, (180, 180, 180))
            hint_rect = hint_surf.get_rect(center=(panel_w // 2, panel_h - 48))
            panel_surf.blit(hint_surf, hint_rect)

            screen.blit(panel_surf, panel_rect.topleft)
            pygame.display.flip()
            clock.tick(30)

    def show_main_menu():
        play_click_sound = None
        try:
            play_sound_path = os.path.join(DATA_DIR, 'sound1.wav')
            if os.path.isfile(play_sound_path):
                play_click_sound = pygame.mixer.Sound(play_sound_path)
                play_click_sound.set_volume(0.1)
        except Exception:
            play_click_sound = None

        play_rect = pygame.Rect(0, 0, 220, 64)
        play_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Slider: регулировка громкости музыки (в диапазоне 0.0 - 1.0)
        slider_track_w = 360
        slider_track_h = 8
        slider_x = SCREEN_WIDTH // 2 - slider_track_w // 2
        slider_y = play_rect.bottom + 100
        track_rect = pygame.Rect(slider_x, slider_y, slider_track_w, slider_track_h)
        knob_radius = 12
        knob_x = slider_x + int(game_config.MUSIC_VOLUME * slider_track_w)
        knob_y = slider_y + slider_track_h // 2
        knob_rect = pygame.Rect(knob_x - knob_radius, knob_y - knob_radius, knob_radius * 2, knob_radius * 2)
        dragging = False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Play button
                    if play_rect.collidepoint(event.pos):
                        if play_click_sound is not None:
                            try:
                                play_click_sound.play()
                            except Exception:
                                pass
                        return True

                    # Начать перетаскивание/клик по слайдеру
                    if knob_rect.collidepoint(event.pos) or track_rect.collidepoint(event.pos):
                        dragging = True
                        # Обновить громкость сразу при клике
                        rel_x = max(0, min(event.pos[0] - slider_x, slider_track_w))
                        new_v = rel_x / float(slider_track_w)
                        game_config.MUSIC_VOLUME = new_v
                        try:
                            pygame.mixer.music.set_volume(new_v)
                        except Exception:
                            pass
                        knob_rect.x = slider_x + int(new_v * slider_track_w) - knob_radius

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging = False

                if event.type == pygame.MOUSEMOTION and dragging:
                    rel_x = max(0, min(event.pos[0] - slider_x, slider_track_w))
                    new_v = rel_x / float(slider_track_w)
                    game_config.MUSIC_VOLUME = new_v
                    try:
                        pygame.mixer.music.set_volume(new_v)
                    except Exception:
                        pass
                    knob_rect.x = slider_x + int(new_v * slider_track_w) - knob_radius

            screen.fill((0, 0, 0))
            title_surf = font.render("SVM BATTLE", True, (255, 255, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)))

            pygame.draw.rect(screen, (50, 50, 50), play_rect)
            pygame.draw.rect(screen, (200, 200, 200), play_rect, 2)
            text_surface = button_font.render("Play", True, (255, 255, 255))
            screen.blit(text_surface, text_surface.get_rect(center=play_rect.center))

            # Draw volume slider
            try:
                # track
                pygame.draw.rect(screen, (80, 80, 80), track_rect, border_radius=6)
                pygame.draw.rect(screen, (200, 200, 200), track_rect, 2, border_radius=6)
                # knob
                pygame.draw.circle(screen, (220, 220, 220), knob_rect.center, knob_radius)
                pygame.draw.circle(screen, (40, 40, 40), knob_rect.center, knob_radius, 2)
                # label and percent
                label = game_config.slider_font.render("Music Volume", True, (200, 200, 200))
                screen.blit(label, (slider_x, slider_y - 28))
                pct = int(game_config.MUSIC_VOLUME * 100)
                pct_surf = game_config.slider_font.render(f"{pct}%", True, (200, 200, 200))
                screen.blit(pct_surf, (slider_x + slider_track_w + 12, slider_y - 12))
            except Exception:
                pass

            pygame.display.flip()
            clock.tick(30)

    def show_story_intro():
        story_text = (
            "Ты пришёл на экзамен к преподавателю, и никто не знает его настоящего имени. "
            "Но ты дал ему имя Марвин. Этот преподаватель ставит тебе 0 баллов за любую оплошность. "
            "И вот ты тянешь билет — на нём написано: 3 в ряд. Ты ничего не понимаешь, "
            "но преподаватель лишь усмехается и говорит: если сможешь победить меня в этой игре, "
            "то получишь 100 баллов. Но всё оказалось не так просто..."
        )

        def wrap_text(s, max_width, render_font):
            words = s.split(' ')
            lines = []
            cur = ''
            for w in words:
                test = (cur + ' ' + w).strip()
                if render_font.size(test)[0] <= max_width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return lines

        panel_margin = 40
        panel_h = max(220, SCREEN_HEIGHT // 3)
        panel_rect = pygame.Rect(
            40,
            SCREEN_HEIGHT - panel_h - 40,
            SCREEN_WIDTH - 80,
            panel_h,
        )

        boss_backdrop = Boss()

        def draw_centered_boss_sprite():
            """Показать босса в центре экрана без боевой панели."""
            if boss_backdrop.image_original:
                sprite = boss_backdrop.image_original
                max_w = int(SCREEN_WIDTH * 0.42)
                max_h = int(SCREEN_HEIGHT * 0.55)
                scale = min(max_w / sprite.get_width(), max_h / sprite.get_height())
                scale = min(scale, 1.0)
                draw_w = max(1, int(sprite.get_width() * scale))
                draw_h = max(1, int(sprite.get_height() * scale))
                rendered = pygame.transform.smoothscale(sprite, (draw_w, draw_h))
                draw_x = (SCREEN_WIDTH - draw_w) // 2
                draw_y = (SCREEN_HEIGHT - draw_h) // 2 - 10
                screen.blit(rendered, (draw_x, draw_y))
            else:
                fallback_w = int(SCREEN_WIDTH * 0.22)
                fallback_h = int(SCREEN_HEIGHT * 0.42)
                fallback_rect = pygame.Rect(0, 0, fallback_w, fallback_h)
                fallback_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)
                pygame.draw.rect(screen, boss_backdrop.color, fallback_rect, border_radius=18)

        lines = wrap_text(story_text, panel_rect.width - panel_margin * 2, counter_font)
        full_text = '\n'.join(lines)
        typed_chars = 0
        chars_per_second = 45
        finished_at = None
        waiting_for_click = False

        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and waiting_for_click and typed_chars >= len(full_text):
                    return

            if typed_chars < len(full_text):
                typed_chars = min(len(full_text), typed_chars + max(1, int(chars_per_second * dt)))
                if typed_chars >= len(full_text):
                    finished_at = time.time()
                    waiting_for_click = True
            elif finished_at is None:
                finished_at = time.time()
                waiting_for_click = True

            visible_text = full_text[:typed_chars]
            visible_lines = visible_text.split('\n')

            screen.fill((0, 0, 0))

            # Subtle atmosphere for the intro
            glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 30, 100, 50), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), SCREEN_HEIGHT // 3)
            screen.blit(glow, (0, 0))

            # Boss in the background of the story scene
            draw_centered_boss_sprite()

            panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            panel_surf.fill((10, 10, 12, 235))
            pygame.draw.rect(panel_surf, (255, 255, 255), panel_surf.get_rect(), 2, border_radius=14)

            title_surf = font.render("СЮЖЕТ", True, (255, 230, 120))
            panel_surf.blit(title_surf, title_surf.get_rect(center=(panel_rect.width // 2, 32)))

            y = 72
            left = panel_margin
            for line in visible_lines:
                if line:
                    text_surf = counter_font.render(line, True, (230, 230, 230))
                    panel_surf.blit(text_surf, (left, y))
                    y += text_surf.get_height() + 8
                else:
                    y += 18

            cursor_blink = int(time.time() * 2) % 2 == 0
            if cursor_blink and typed_chars < len(full_text):
                cursor_surf = counter_font.render("_", True, (255, 255, 255))
                panel_surf.blit(cursor_surf, (left + 10, min(y, panel_rect.height - 40)))

            if typed_chars < len(full_text):
                prompt_text = "Текст печатается..."
            else:
                prompt_text = "Левой кнопкой мыши продолжить"
            prompt_surf = button_font.render(prompt_text, True, (180, 180, 180))
            prompt_rect = prompt_surf.get_rect(center=(panel_rect.width // 2, panel_rect.height - 28))
            panel_surf.blit(prompt_surf, prompt_rect)

            screen.blit(panel_surf, panel_rect.topleft)
            pygame.display.flip()

    

    show_disclaimer()
    start = show_main_menu()
    if start:
        show_story_intro()
        game = BattleGame()
        game.run()


if __name__ == "__main__":
    main()