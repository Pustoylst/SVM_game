import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


class _DummyDisplayInfo:
    current_w = 1280
    current_h = 720


pygame.mixer.init = lambda *args, **kwargs: None
pygame.display.Info = lambda: _DummyDisplayInfo()
pygame.display.set_mode = lambda size, flags=0: pygame.Surface(size)

from game_logic import GameBoard


def make_board(grid):
    board = GameBoard()
    board.grid = [row[:] for row in grid]
    return board


def base_grid():
    return [[(x + y) % 8 for x in range(10)] for y in range(10)]


def test_find_matches_detects_horizontal_and_vertical_lines():
    grid = base_grid()
    grid[0][0] = 3
    grid[0][1] = 3
    grid[0][2] = 3
    grid[2][4] = 6
    grid[3][4] = 6
    grid[4][4] = 6

    board = make_board(grid)

    matches = set(board.find_matches())

    assert {(0, 0), (0, 1), (0, 2)}.issubset(matches)
    assert {(2, 4), (3, 4), (4, 4)}.issubset(matches)


def test_calculate_damage_uses_expected_progression():
    board = make_board(base_grid())

    assert board.calculate_damage(2) == 0
    assert board.calculate_damage(3) == 10
    assert board.calculate_damage(4) == 50
    assert board.calculate_damage(5) == 100
    assert board.calculate_damage(7) == 150


def test_collapse_grid_fills_empty_cells():
    grid = base_grid()
    for row in grid:
        row[1] = -1
        row[3] = -1
        row[7] = -1
    board = make_board(grid)

    original_cleared = board.blocks_cleared

    import game_logic

    game_logic.random.randint = lambda a, b: 7

    columns = board.collapse_grid()

    for row in board.grid:
        assert row[1] == 7
        assert row[3] == 7
        assert row[7] == 7
    assert all(cell != -1 for row in board.grid for cell in row)
    assert columns == {1, 3, 7}
    assert board.blocks_cleared == original_cleared


def test_possible_move_finds_valid_swap():
    grid = base_grid()
    grid[0][0] = 1
    grid[0][1] = 0
    grid[0][2] = 1
    grid[1][0] = 0
    grid[1][1] = 1
    grid[1][2] = 2
    grid[2][0] = 2
    grid[2][1] = 3
    grid[2][2] = 4

    board = make_board(grid)

    move = board.find_possible_move()

    assert move is not None
    board.swap_blocks(move[0], move[1])
    assert board.find_matches()
