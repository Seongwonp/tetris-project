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


MARATHON = GameMode("marathon", "Marathon", "끝없이 플레이", None, None)
SPRINT_40 = GameMode("sprint", "Sprint 40", "40줄을 가장 빨리", 40, None)
TIME_ATTACK = GameMode("time_attack", "Time Attack", "2분 제한 점수전", None, 120000)

MODE_LIST: List[GameMode] = [MARATHON, SPRINT_40, TIME_ATTACK]

MODE_BY_SLUG = {mode.slug: mode for mode in MODE_LIST}

