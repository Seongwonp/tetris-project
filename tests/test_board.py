import unittest
from tetris.board import Board
from tetris.piece import Piece


class TestBoard(unittest.TestCase):

    def setUp(self):
        self.board = Board()

    def test_initial_board_empty(self):
        for row in self.board.grid:
            self.assertTrue(all(cell == 0 for cell in row))

    def test_board_dimensions(self):
        self.assertEqual(len(self.board.grid), 20)
        self.assertEqual(len(self.board.grid[0]), 10)

    def test_piece_valid_at_spawn(self):
        piece = Piece(1)  # I 피스
        self.assertTrue(self.board.is_valid(piece.shape, 0, 3))

    def test_piece_invalid_out_of_bounds_left(self):
        piece = Piece(1)
        self.assertFalse(self.board.is_valid(piece.shape, 0, -5))

    def test_piece_invalid_out_of_bounds_right(self):
        piece = Piece(1)
        self.assertFalse(self.board.is_valid(piece.shape, 0, 8))

    def test_piece_invalid_below_floor(self):
        piece = Piece(2)  # O 피스
        self.assertFalse(self.board.is_valid(piece.shape, 20, 4))

    def test_clear_full_line(self):
        # 맨 아래 줄 전부 채우기
        for c in range(10):
            self.board.grid[19][c] = 1
        cleared = self.board.clear_lines()
        self.assertEqual(cleared, 1)
        for c in range(10):
            self.assertEqual(self.board.grid[19][c], 0)

    def test_clear_multiple_lines(self):
        for r in range(18, 20):
            for c in range(10):
                self.board.grid[r][c] = 1
        cleared = self.board.clear_lines()
        self.assertEqual(cleared, 2)

    def test_no_clear_incomplete_line(self):
        for c in range(9):  # 9칸만 채움
            self.board.grid[19][c] = 1
        cleared = self.board.clear_lines()
        self.assertEqual(cleared, 0)

    def test_ghost_y_empty_board(self):
        piece = Piece(2)  # O 피스
        ghost = self.board.ghost_y(piece.shape, 0, 4)
        self.assertEqual(ghost, 18)  # 바닥에서 2칸 위

    def test_lock_piece(self):
        piece = Piece(2)  # O 피스 (2x2)
        self.board.lock(piece.shape, 18, 4)
        self.assertNotEqual(self.board.grid[18][4], 0)
        self.assertNotEqual(self.board.grid[19][4], 0)


if __name__ == "__main__":
    unittest.main()
