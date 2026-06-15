"""Главный файл игры - Mizzz Bloxxxxx Battle Mode"""
import pygame
import sys
import time
from game_config import screen, clock, SCREEN_HEIGHT, SCREEN_WIDTH, play_main_theme, toggle_music, button_font, font
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
        if self.renderer.is_help_button(pos):
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

        if self.renderer.get_button_at_position(pos) == 2:
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
            "преднамеренны — за всё отвечает генеративный ИИ, а авторы не имеют к этому отношения."
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
        play_rect = pygame.Rect(0, 0, 220, 64)
        play_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if play_rect.collidepoint(event.pos):
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

    show_disclaimer()
    start = show_main_menu()
    if start:
        game = BattleGame()
        game.run()


if __name__ == "__main__":
    main()
