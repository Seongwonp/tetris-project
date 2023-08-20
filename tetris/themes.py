"""렌더링 테마 정의."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Theme:
    slug: str
    title: str
    bg: tuple
    panel: tuple
    dgray: tuple
    gray: tuple
    border: tuple
    white: tuple
    dim: tuple
    gold: tuple
    green: tuple
    cyan: tuple


CLASSIC = Theme("classic", "Classic", (18, 18, 28), (25, 25, 42), (30, 30, 38), (55, 55, 70), (80, 80, 130), (240, 240, 240), (130, 130, 150), (255, 215, 50), (80, 255, 130), (80, 210, 255))
NEON = Theme("neon", "Neon", (10, 10, 18), (16, 12, 32), (18, 18, 24), (48, 48, 64), (120, 70, 220), (250, 250, 255), (160, 160, 190), (255, 90, 210), (100, 255, 170), (90, 220, 255))
SUNSET = Theme("sunset", "Sunset", (28, 14, 18), (50, 24, 32), (36, 18, 24), (76, 42, 54), (200, 104, 88), (255, 245, 235), (210, 170, 160), (255, 190, 90), (120, 230, 160), (110, 190, 255))
MONO = Theme("mono", "Mono", (18, 18, 18), (28, 28, 28), (34, 34, 34), (60, 60, 60), (180, 180, 180), (240, 240, 240), (160, 160, 160), (220, 220, 220), (200, 200, 200), (180, 180, 180))

THEMES: Dict[str, Theme] = {theme.slug: theme for theme in [CLASSIC, NEON, SUNSET, MONO]}
THEME_LIST: List[Theme] = list(THEMES.values())

