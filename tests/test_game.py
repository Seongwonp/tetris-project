import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tetris.bag import BagRandomizer
from tetris.board import COLS, ROWS
from tetris.game import GameState
from tetris.piece import Piece


def _empty_grid():
    return [[0] * COLS for _ in range(ROWS)]


def _set_piece(state: GameState, kind: int, x: int, y: int, rotation: int = 0):
    piece = Piece(kind)
    if rotation:
        shape, rot = piece.rotated(rotation)
        piece.shape = shape
        piece.rotation = rot
    piece.x = x
    piece.y = y
    state.piece = piece
    return piece


class BagTests(unittest.TestCase):
    def test_7_bag_cycles_unique(self):
        bag = BagRandomizer(random.Random(0))
        first = [bag.pop() for _ in range(7)]
        second = [bag.pop() for _ in range(7)]
        self.assertEqual(set(first), set(range(1, 8)))
        self.assertEqual(set(second), set(range(1, 8)))


class GameStateTests(unittest.TestCase):
    def test_next_queue_has_three_pieces(self):
        state = GameState(on_sound=lambda _: None)
        self.assertEqual(len(state.next_queue), 3)
        self.assertIs(state.next, state.next_queue[0])

    def test_line_clear_scores_and_combo(self):
        state = GameState(on_sound=lambda _: None)
        state.board.grid = _empty_grid()
        state.board.grid[ROWS - 1][:6] = [1] * 6
        _set_piece(state, 1, 6, ROWS - 1)
        state._lock()
        state.update(400)  # advance past clear animation

        self.assertEqual(state.score, 100)
        self.assertEqual(state.lines, 1)
        self.assertEqual(state.combo, 0)

        state.board.grid = _empty_grid()
        state.board.grid[ROWS - 1][:6] = [1] * 6
        _set_piece(state, 1, 6, ROWS - 1)
        state._lock()
        state.update(400)

        self.assertEqual(state.score, 250)
        self.assertEqual(state.lines, 2)
        self.assertEqual(state.combo, 1)

    def test_back_to_back_tetris_multiplier(self):
        state = GameState(on_sound=lambda _: None)
        state.back_to_back = True
        state.board.grid = _empty_grid()
        for row in range(ROWS - 4, ROWS):
            state.board.grid[row][:9] = [1] * 9

        _set_piece(state, 1, 9, ROWS - 4, rotation=1)
        state._lock()
        state.update(400)  # advance past clear animation

        self.assertEqual(state.score, 1200)
        self.assertEqual(state.lines, 4)

    def test_tspin_scores_without_line_clear(self):
        state = GameState(on_sound=lambda _: None)
        state.board.grid = _empty_grid()
        state.board.grid[17][4] = 1
        state.board.grid[17][6] = 1
        state.board.grid[19][4] = 1
        _set_piece(state, 3, 4, 17)
        state._rotated_since_spawn = True
        state._lock()

        self.assertEqual(state.score, 400)
        self.assertEqual(state.lines, 0)

    def test_grounded_piece_can_move_during_lock_delay(self):
        # lock delay 동안 이동/회전이 가능하고 타이머가 리셋되어야 함
        state = GameState(on_sound=lambda _: None)
        _set_piece(state, 1, 3, ROWS - 1)  # I-피스, 바닥 행
        state._grounded = True
        state._lock_timer = 300  # lock delay 진행 중
        x_before = state.piece.x

        result = state.move(-1)
        self.assertTrue(result)
        self.assertEqual(state.piece.x, x_before - 1)
        self.assertEqual(state._lock_timer, 0)  # 이동 시 타이머 리셋


if __name__ == "__main__":
    unittest.main()
