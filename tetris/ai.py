"""
tetris/ai.py — 테트리스 데모 AI (휴리스틱 기반)

타이틀 화면 데모 모드에서 사용하는 AI 플레이어.
각 피스에 대해 가능한 배치를 평가하고 최적 위치를 선택한다.

평가 기준:
  - aggregate_height : 전체 열 높이 합계 (낮을수록 좋음)
  - complete_lines   : 완성된 라인 수 (많을수록 좋음)
  - holes            : 빈 칸(구멍) 수 (적을수록 좋음)
  - bumpiness        : 인접 열 높이 차이 합 (낮을수록 좋음)

참고: Tetris AI 논문 — Dellacherie heuristic
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

# 피스 회전별 모양 (piece.py SHAPES 와 동일 구조)
from tetris.board import Board
from tetris.piece import Piece


@dataclass
class Move:
    rotation: int
    col: int
    score: float


def _col_heights(grid: List[List[int]]) -> List[int]:
    rows, cols = len(grid), len(grid[0])
    heights = []
    for c in range(cols):
        h = 0
        for r in range(rows):
            if grid[r][c]:
                h = rows - r
                break
        heights.append(h)
    return heights


def _count_holes(grid: List[List[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    holes = 0
    for c in range(cols):
        block_found = False
        for r in range(rows):
            if grid[r][c]:
                block_found = True
            elif block_found:
                holes += 1
    return holes


def _count_complete_lines(grid: List[List[int]]) -> int:
    return sum(1 for row in grid if all(row))


def _bumpiness(heights: List[int]) -> int:
    return sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))


def _evaluate(grid: List[List[int]]) -> float:
    heights = _col_heights(grid)
    agg_height   = sum(heights)
    complete     = _count_complete_lines(grid)
    holes        = _count_holes(grid)
    bumpy        = _bumpiness(heights)

    # Dellacherie 가중치
    return (
        -0.510066 * agg_height
        + 0.760666 * complete
        -0.35663  * holes
        -0.184483  * bumpy
    )


def _apply_piece(grid: List[List[int]], piece: Piece, rotation: int, col: int) -> Optional[List[List[int]]]:
    """피스를 grid에 배치해보고 결과 반환. 유효하지 않으면 None."""
    import copy
    shape = piece.rotated(rotation)
    rows_count = len(grid)
    cols_count = len(grid[0])

    # 가장 낮은 유효 행 찾기 (hard drop 시뮬레이션)
    for drop_row in range(rows_count):
        for dr, row in enumerate(shape):
            for dc, cell in enumerate(row):
                if not cell:
                    continue
                r = drop_row + dr
                c = col + dc
                if r >= rows_count or c < 0 or c >= cols_count:
                    # 이 drop_row는 유효하지 않음 — 한 행 위로
                    if drop_row == 0:
                        return None
                    drop_row -= 1
                    break
                if grid[r][c]:
                    if drop_row == 0:
                        return None
                    drop_row -= 1
                    break
            else:
                continue
            break
        else:
            # 모든 셀 유효 → 배치
            new_grid = copy.deepcopy(grid)
            for dr, row in enumerate(shape):
                for dc, cell in enumerate(row):
                    if cell:
                        new_grid[drop_row + dr][col + dc] = cell
            return new_grid
    return None


def best_move(board: Board, piece: Piece) -> Move:
    """현재 보드와 피스를 받아 최적의 (rotation, col) 반환."""
    best: Optional[Move] = None

    for rotation in range(4):
        shape = piece.rotated(rotation)
        piece_width = max(len(row) for row in shape)
        cols = len(board.grid[0])

        for col in range(-1, cols):
            result = _apply_piece(board.grid, piece, rotation, col)
            if result is None:
                continue
            score = _evaluate(result)
            if best is None or score > best.score:
                best = Move(rotation=rotation, col=col, score=score)

    return best or Move(rotation=0, col=4, score=-999.0)


def ai_actions(board: Board, piece: Piece, current_rotation: int, current_col: int) -> List[str]:
    """
    현재 피스 상태에서 목표 위치까지 필요한 액션 목록 반환.
    반환값: "rotate_cw", "move_left", "move_right", "hard_drop" 조합
    """
    target = best_move(board, piece)
    actions: List[str] = []

    rot_diff = (target.rotation - current_rotation) % 4
    for _ in range(rot_diff):
        actions.append("rotate_cw")

    col_diff = target.col - current_col
    direction = "move_right" if col_diff > 0 else "move_left"
    for _ in range(abs(col_diff)):
        actions.append(direction)

    actions.append("hard_drop")
    return actions
