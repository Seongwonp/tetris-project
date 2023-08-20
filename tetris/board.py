from typing import List, Tuple
from .piece import Piece

ROWS = 20
COLS = 10


class Board:
    """게임 그리드 상태와 충돌/줄제거 로직을 담당."""

    def __init__(self):
        self.grid: List[List[int]] = [[0] * COLS for _ in range(ROWS)]

    def is_valid(self, piece: Piece, dx: int = 0, dy: int = 0,
                 shape: List[List[int]] = None) -> bool:
        """piece + 오프셋(dx, dy)이 보드 범위 내에 있고 다른 블록과 겹치지 않으면 True."""
        s = shape if shape is not None else piece.shape
        for r, row in enumerate(s):
            for c, cell in enumerate(row):
                if not cell:
                    continue
                nx = piece.x + c + dx
                ny = piece.y + r + dy
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return False
                if ny >= 0 and self.grid[ny][nx]:
                    return False
        return True

    def lock(self, piece: Piece) -> None:
        """piece를 그리드에 고정."""
        for r, row in enumerate(piece.shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + r][piece.x + c] = piece.kind

    def clear_lines(self) -> int:
        """완성된 줄을 제거하고 개수를 반환."""
        full_rows = [row for row in self.grid if all(row)]
        if not full_rows:
            return 0
        remaining = [row for row in self.grid if not all(row)]
        cleared = len(full_rows)
        self.grid = [[0] * COLS for _ in range(cleared)] + remaining
        return cleared

    def ghost_y(self, piece: Piece) -> int:
        """piece가 바닥까지 떨어졌을 때의 y 좌표 반환."""
        dy = 0
        while self.is_valid(piece, dy=dy + 1):
            dy += 1
        return piece.y + dy

    def is_cell_filled(self, row: int, col: int) -> int:
        """(row, col) 셀의 kind 값 반환 (0이면 비어 있음)."""
        return self.grid[row][col]
