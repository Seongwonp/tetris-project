"""Tetris – pygame 기반 테트리스 게임 패키지."""

from .piece import Piece, COLORS, SHAPES
from .bag import BagRandomizer
from .modes import GameMode
from .profile import ProfileStore
from .board import Board
from .game import GameState
# Renderer imports pygame and is optional for non-graphical tests/environments.
# Import lazily and tolerate environments without pygame (CI).
try:
    from .renderer import Renderer  # type: ignore
except Exception:
    Renderer = None  # type: ignore


__all__ = ["Piece", "COLORS", "SHAPES", "BagRandomizer", "GameMode", "ProfileStore", "Board", "GameState", "Renderer"]
