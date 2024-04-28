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
        piece.x, piece.y = 3, 0
        self.assertTrue(self.board.is_valid(piece))

    def test_piece_invalid_out_of_bounds_left(self):
        piece = Piece(1)  # I 피스 (4칸 너비)
        piece.x, piece.y = -5, 0
        self.assertFalse(self.board.is_valid(piece))

    def test_piece_invalid_out_of_bounds_right(self):
        piece = Piece(1)  # I 피스 (4칸 너비)
        piece.x, piece.y = 8, 0  # x=8 + width=4 → col 11 > 10
        self.assertFalse(self.board.is_valid(piece))

    def test_piece_invalid_below_floor(self):
        piece = Piece(2)  # O 피스 (2x2)
        piece.x, piece.y = 4, 20
        self.assertFalse(self.board.is_valid(piece))

    def test_clear_full_line(self):
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
        piece = Piece(2)  # O 피스 (2x2)
        piece.x, piece.y = 4, 0
        ghost = self.board.ghost_y(piece)
        self.assertEqual(ghost, 18)  # rows=20, O피스 높이=2 → 바닥 y=18

    def test_lock_piece(self):
        piece = Piece(2)  # O 피스 (2x2)
        piece.x, piece.y = 4, 18
        self.board.lock(piece)
        self.assertNotEqual(self.board.grid[18][4], 0)
        self.assertNotEqual(self.board.grid[19][4], 0)


if __name__ == "__main__":
    unittest.main()
