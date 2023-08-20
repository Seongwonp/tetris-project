"""7-bag 랜덤 테트로미노 생성."""

from __future__ import annotations

import random
from typing import List, Optional


class BagRandomizer:
    def __init__(self, rng: Optional[random.Random] = None, seed: Optional[int] = None):
        if rng is not None:
            self._rng = rng
        else:
            self._rng = random.Random(seed)
        self._bag: List[int] = []

    def _refill(self) -> None:
        self._bag = [1, 2, 3, 4, 5, 6, 7]
        self._rng.shuffle(self._bag)

    def pop(self) -> int:
        if not self._bag:
            self._refill()
        return self._bag.pop()

    def preview(self, n: int) -> List[int]:
        temp_rng = random.Random()
        temp_rng.setstate(self._rng.getstate())
        temp_bag = list(self._bag)
        if not temp_bag:
            temp_bag = [1, 2, 3, 4, 5, 6, 7]
            temp_rng.shuffle(temp_bag)

        result: List[int] = []
        while len(result) < n:
            if not temp_bag:
                temp_bag = [1, 2, 3, 4, 5, 6, 7]
                temp_rng.shuffle(temp_bag)
            result.append(temp_bag.pop())
        return result
