import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# (kind index → color RGB)
COLORS: List[Optional[Tuple[int, int, int]]] = [
    None,
    (0,   240, 240),   # 1 I
    (240, 240,   0),   # 2 O
    (160,   0, 240),   # 3 T
    (0,   240,   0),   # 4 S
    (240,   0,   0),   # 5 Z
    (0,    80, 240),   # 6 J
    (240, 160,   0),   # 7 L
]

# 각 테트로미노 기본 모양 (0 = 빈칸, 1 = 블록)
SHAPES: List[Optional[List[List[int]]]] = [
    None,
    [[1, 1, 1, 1]],           # I
    [[1, 1], [1, 1]],          # O
    [[0, 1, 0], [1, 1, 1]],    # T
    [[0, 1, 1], [1, 1, 0]],    # S
    [[1, 1, 0], [0, 1, 1]],    # Z
    [[1, 0, 0], [1, 1, 1]],    # J
    [[0, 0, 1], [1, 1, 1]],    # L
]

COLS = 10  # board 모듈과 분리하기 위해 여기서만 사용


def _rotate(shape: List[List[int]]) -> List[List[int]]:
    rows, cols = len(shape), len(shape[0])
    return [[shape[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]


ROTATIONS: List[Optional[List[List[List[int]]]]] = [None]
for kind in range(1, 8):
    rotations = [SHAPES[kind]]
    for _ in range(3):
        rotations.append(_rotate(rotations[-1]))
    ROTATIONS.append(rotations)


@dataclass
class Piece:
    kind: Optional[int] = None
    x: int = 0
    y: int = 0
    rotation: int = 0
    shape: List[List[int]] = field(init=False)
    color: Tuple[int, int, int] = field(init=False)

    def __post_init__(self):
        if self.kind is None:
            self.kind = random.randint(1, 7)
        self.rotation %= 4
        self.shape = [row[:] for row in ROTATIONS[self.kind][self.rotation]]
        self.color = COLORS[self.kind]
        self.x = COLS // 2 - len(self.shape[0]) // 2

    @property
    def width(self) -> int:
        return len(self.shape[0])

    @property
    def height(self) -> int:
        return len(self.shape)

    def rotated(self, direction: int = 1) -> Tuple[List[List[int]], int]:
        """회전한 새 shape와 rotation 반환."""
        new_rot = (self.rotation + direction) % 4
        shape = ROTATIONS[self.kind][new_rot]
        return [row[:] for row in shape], new_rot

    def rotated_shape(self) -> List[List[int]]:
        shape, _ = self.rotated(1)
        return shape

    def clone(self) -> "Piece":
        p = Piece.__new__(Piece)
        p.kind = self.kind
        p.x = self.x
        p.y = self.y
        p.rotation = self.rotation
        p.shape = [row[:] for row in self.shape]
        p.color = self.color
        return p
