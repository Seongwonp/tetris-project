"""게임 모드 정의."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class GameMode:
    slug: str
    title: str
    description: str
    target_lines: Optional[int] = None
    time_limit_ms: Optional[int] = None


MARATHON = GameMode("marathon", "Marathon", "Endless, no time limit", None, None)
SPRINT_40 = GameMode("sprint", "Sprint 40", "Clear 40 lines fast", 40, None)
TIME_ATTACK = GameMode("time_attack", "Time Attack", "Max score in 2 min", None, 120000)

MODE_LIST: List[GameMode] = [MARATHON, SPRINT_40, TIME_ATTACK]

MODE_BY_SLUG = {mode.slug: mode for mode in MODE_LIST}

