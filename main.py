"""Главный файл игры - Mizzz Bloxxxxx Battle Mode"""
import pygame
import sys
import time
import os
from game_config import screen, clock, SCREEN_HEIGHT, SCREEN_WIDTH, play_main_theme, toggle_music, button_font, font, counter_font
from game_config import DATA_DIR
from game_logic import GameBoard
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
        button_index = self.renderer.get_button_at_position(pos)

        if button_index == 1:
            if self.help_used:
                self.renderer.clear_hint()
                return

            move = self.board.find_possible_move()
            if move:
                self.renderer.show_hint(move)
                self.player.take_damage(999)
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
            # Нет совпадений, вернуть блоки обратно
            self.board.swap_blocks(pos1, pos2)
    
    def process_matches(self, matches):
        """Обработать найденные совпадения"""
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
        if not self.boss.is_alive():
            print(f"Boss defeated! You won! Time: {time.time() - self.start_time:.2f}s")
            return False
        
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
            
            # Проверить состояние игры
            if not self.check_game_state():
                self.running = False
            
            # Отрисовать
            self.renderer.draw_game()
            
            # FPS
            clock.tick(60)
        
        pygame.quit()
        sys.exit()


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
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if play_rect.collidepoint(event.pos):
                        if play_click_sound is not None:
                            try:
                                play_click_sound.play()
                            except Exception:
                                pass
                        return True

            screen.fill((0, 0, 0))
            title_surf = font.render("SVM BATTLE", True, (255, 255, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)))

            pygame.draw.rect(screen, (50, 50, 50), play_rect)
            pygame.draw.rect(screen, (200, 200, 200), play_rect, 2)
            text_surface = button_font.render("Play", True, (255, 255, 255))
            screen.blit(text_surface, text_surface.get_rect(center=play_rect.center))

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
