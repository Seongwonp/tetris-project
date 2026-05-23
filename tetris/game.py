from typing import Callable, Optional, List, Tuple

from .bag import BagRandomizer
from .board import Board, COLS, ROWS
from .config import (
    ARR_INTERVAL_MS,
    B2B_MULTIPLIER,
    COMBO_BONUS,
    DAS_DELAY_MS,
    LINE_SCORES,
    LOCK_DELAY_MS,
    NEXT_QUEUE_SIZE,
    SCORE_SPEED_STEP,
    SPEED_UP_DISPLAY_MS,
    SOFT_DROP_INTERVAL_MS,
    TSPIN_SCORES,
)
from .modes import GameMode, MARATHON
from .piece import Piece


def _fall_speed(level: int) -> int:
    return max(50, 500 - (level - 1) * 45)


SRS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}

SRS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}


def _kick_table(kind: int, from_rot: int, to_rot: int) -> List[Tuple[int, int]]:
    if kind == 2:
        return [(0, 0)]
    table = SRS_I if kind == 1 else SRS_JLSTZ
    return table.get((from_rot, to_rot), [(0, 0)])


class GameState:
    """게임 흐름 전체(낙하 타이밍, 점수, 레벨, 홀드)를 관리."""

    def __init__(self, on_sound: Optional[Callable[[str], None]] = None):
        self._on_sound = on_sound or (lambda _: None)
        self.reset()

    def reset(self, start_level: int = 1, mode: Optional[GameMode] = None, seed: Optional[int] = None) -> None:
        self.board = Board()
        self.bag = BagRandomizer(seed=seed)
        self.next_queue: List[Piece] = []
        self.piece = Piece(1)
        self.next = self.piece

        self.held: Optional[Piece] = None
        self.can_hold = True

        self.score = 0
        self.lines = 0
        self.start_level = max(1, start_level)
        self.mode = mode or MARATHON
        self.speed_bonus = 0
        self.next_speed_score = SCORE_SPEED_STEP
        self.level = self.start_level
        self.fall_speed = _fall_speed(self.level)

        self.combo = -1
        self.back_to_back = False
        self.tetrises = 0
        self.t_spins = 0

        self.last_score_delta = 0
        self.last_score_reason = ""
        self.speed_up_timer = 0
        self.elapsed_ms = 0
        self.result_reason = ""

        self.clearing_rows: List[int] = []
        self.clear_anim_timer: int = 0
        self._pending_tspin: bool = False

        self._fall_acc = 0
        self._lock_timer = 0
        self._grounded = False
        self._rotated_since_spawn = False
        self._last_kick_used = False
        self._just_locked = False
        self._contact_reset = False
        self._contact_reset_count = 0

        self._left_held = False
        self._right_held = False
        self._down_held = False
        self._horizontal_dir = 0
        self._horizontal_phase = "idle"
        self._horizontal_timer = 0
        self._soft_drop_timer = 0

        self.game_over = False
        self.paused = False

        self._fill_queue()
        self._spawn_next_piece()

    # ── 입력 ───────────────────────────────────────────────
    def press_left(self) -> None:
        if self._blocked():
            return
        self._left_held = True
        self._set_horizontal(-1, immediate=True)

    def release_left(self) -> None:
        self._left_held = False
        if self._horizontal_dir == -1:
            self._set_horizontal(1 if self._right_held else 0, immediate=True)

    def press_right(self) -> None:
        if self._blocked():
            return
        self._right_held = True
        self._set_horizontal(1, immediate=True)

    def release_right(self) -> None:
        self._right_held = False
        if self._horizontal_dir == 1:
            self._set_horizontal(-1 if self._left_held else 0, immediate=True)

    def press_down(self) -> None:
        if self._blocked():
            return
        self._down_held = True
        self.soft_drop()
        self._soft_drop_timer = 0

    def release_down(self) -> None:
        self._down_held = False
        self._soft_drop_timer = 0

    # ── 공개 액션 ─────────────────────────────────────────
    def move(self, dx: int) -> bool:
        if self._blocked():
            return False
        if self.board.is_valid(self.piece, dx=dx):
            self.piece.x += dx
            self._on_sound("move")
            self._refresh_contact()
            return True
        return False

    def rotate(self) -> bool:
        if self._blocked():
            return False

        new_shape, new_rot = self.piece.rotated(1)
        for dx, dy in _kick_table(self.piece.kind, self.piece.rotation, new_rot):
            if self.board.is_valid(self.piece, dx=dx, dy=dy, shape=new_shape):
                self.piece.shape = [row[:] for row in new_shape]
                self.piece.rotation = new_rot
                self.piece.x += dx
                self.piece.y += dy
                self._rotated_since_spawn = True
                self._last_kick_used = (dx, dy) != (0, 0)
                self._on_sound("rotate")
                self._refresh_contact()
                return True
        return False

    def soft_drop(self) -> bool:
        if self._blocked():
            return False
        if self.board.is_valid(self.piece, dy=1):
            self.piece.y += 1
            self._add_score(1, "SOFT DROP")
            self._refresh_contact()
            self._fall_acc = 0
            return True
        self._grounded = True
        return False

    def hard_drop(self) -> bool:
        if self._blocked():
            return False
        dy = 0
        while self.board.is_valid(self.piece, dy=dy + 1):
            dy += 1
        self._add_score(dy * 2, "HARD DROP")
        self.piece.y += dy
        self._on_sound("drop")
        self._lock()
        return True

    def hold(self) -> bool:
        if self._blocked() or not self.can_hold:
            return False

        current_kind = self.piece.kind
        if self.held is None:
            self.held = Piece(current_kind)
            self._spawn_next_piece()
        else:
            self.piece = Piece(self.held.kind)
            self.held = Piece(current_kind)
            self._refresh_contact()
            if not self.board.is_valid(self.piece):
                self.game_over = True
                self._on_sound("gameover")
                return False

        self.can_hold = False
        self._rotated_since_spawn = False
        return True

    def toggle_pause(self) -> None:
        if not self.game_over:
            self.paused = not self.paused

    # ── 업데이트 ───────────────────────────────────────────
    def update(self, dt: int) -> None:
        if self.game_over:
            return

        if self.speed_up_timer > 0 and not self.paused:
            self.speed_up_timer = max(0, self.speed_up_timer - dt)
        if self.paused:
            return

        self.elapsed_ms += dt
        if self.mode.time_limit_ms is not None and self.elapsed_ms >= self.mode.time_limit_ms:
            self.game_over = True
            self.result_reason = "TIME UP"
            self._on_sound("gameover")
            return

        if self.clearing_rows:
            self.clear_anim_timer -= dt
            if self.clear_anim_timer <= 0:
                cleared = self.board.clear_lines()
                self.clearing_rows = []
                self.clear_anim_timer = 0
                self._finish_lock(cleared)
            return

        self._just_locked = False
        self._contact_reset = False
        self._update_horizontal(dt)
        self._update_soft_drop(dt)
        if self.game_over or self._just_locked:
            return

        self._fall_acc += dt
        while self._fall_acc >= self.fall_speed and not self.game_over:
            self._fall_acc -= self.fall_speed
            if self.board.is_valid(self.piece, dy=1):
                self.piece.y += 1
                self._grounded = False
                self._lock_timer = 0
            else:
                self._grounded = True
                break

        if self._grounded:
            if not self._contact_reset:
                self._lock_timer += dt
            if self._lock_timer >= LOCK_DELAY_MS:
                self._lock()

    # ── 내부 헬퍼 ─────────────────────────────────────────
    def _blocked(self) -> bool:
        return self.game_over or self.paused

    def _set_horizontal(self, direction: int, immediate: bool) -> None:
        self._horizontal_dir = direction
        self._horizontal_timer = 0
        self._horizontal_phase = "delay" if direction else "idle"
        if immediate and direction:
            self.move(direction)

    def _update_horizontal(self, dt: int) -> None:
        if self._horizontal_dir == 0:
            return

        self._horizontal_timer += dt
        if self._horizontal_phase == "delay":
            if self._horizontal_timer < DAS_DELAY_MS:
                return
            self._horizontal_timer -= DAS_DELAY_MS
            self._horizontal_phase = "repeat"
            self.move(self._horizontal_dir)
            if self.game_over or self._just_locked:
                return

        while self._horizontal_phase == "repeat" and self._horizontal_timer >= ARR_INTERVAL_MS:
            self._horizontal_timer -= ARR_INTERVAL_MS
            self.move(self._horizontal_dir)
            if self.game_over or self._just_locked:
                return

    def _update_soft_drop(self, dt: int) -> None:
        if not self._down_held:
            return

        self._soft_drop_timer += dt
        while self._soft_drop_timer >= SOFT_DROP_INTERVAL_MS:
            self._soft_drop_timer -= SOFT_DROP_INTERVAL_MS
            self.soft_drop()
            if self.game_over or self._just_locked:
                return

    def _refresh_contact(self) -> None:
        self._grounded = not self.board.is_valid(self.piece, dy=1)
        if self._grounded:
            if self._contact_reset_count < 15:
                self._lock_timer = 0
                self._contact_reset_count += 1
        else:
            self._lock_timer = 0
            self._contact_reset_count = 0
        self._contact_reset = True

    def _add_score(self, amount: int, reason: str) -> None:
        if amount <= 0:
            return
        self.score += amount
        self.last_score_delta = amount
        self.last_score_reason = reason
        speed_up = False
        while self.score >= self.next_speed_score:
            self.speed_bonus += 1
            self.next_speed_score += SCORE_SPEED_STEP
            speed_up = True
        if speed_up:
            self._recalculate_speed()
            self.speed_up_timer = SPEED_UP_DISPLAY_MS

    def _recalculate_speed(self) -> None:
        base_level = self.start_level + self.lines // 10
        self.level = base_level + self.speed_bonus
        self.fall_speed = _fall_speed(self.level)

    def _is_tspin(self) -> bool:
        if self.piece.kind != 3 or not self._rotated_since_spawn:
            return False

        cx = self.piece.x + 1
        cy = self.piece.y + 1
        occupied = 0
        for ox, oy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x = cx + ox
            y = cy + oy
            if x < 0 or x >= COLS or y >= ROWS:
                occupied += 1
            elif y >= 0 and self.board.grid[y][x]:
                occupied += 1
        return occupied >= 3

    def _score_lock(self, cleared: int) -> int:
        tspin = self._is_tspin()
        if tspin:
            if cleared == 0:
                base = TSPIN_SCORES[0]
            elif cleared == 1:
                base = TSPIN_SCORES[1]
            elif cleared == 2:
                base = TSPIN_SCORES[2]
            else:
                base = TSPIN_SCORES[3]
        else:
            base = LINE_SCORES.get(cleared, 0)

        b2b_eligible = tspin or cleared == 4
        if b2b_eligible and self.back_to_back and base > 0:
            base = int(base * B2B_MULTIPLIER)

        combo_bonus = 0
        if cleared > 0:
            self.combo = 0 if self.combo < 0 else self.combo + 1
            if self.combo > 0:
                combo_bonus = self.combo * COMBO_BONUS
        else:
            self.combo = -1

        if cleared > 0:
            self.back_to_back = b2b_eligible
        elif tspin:
            self.back_to_back = True

        return (base * self.level) + combo_bonus

    def _lock(self) -> None:
        self._just_locked = True
        self._pending_tspin = self._is_tspin()
        self.board.lock(self.piece)

        self.clearing_rows = [r for r in range(ROWS) if all(self.board.grid[r])]
        if self.clearing_rows:
            self.clear_anim_timer = 350
            self._on_sound("clear")
        else:
            self._finish_lock(0)

    def _finish_lock(self, cleared: int) -> None:
        tspin = self._pending_tspin
        was_b2b = self.back_to_back
        if cleared or tspin:
            total = self._score_lock(cleared)
            if total:
                if tspin:
                    self.t_spins += 1
                    if cleared == 0:
                        reason = "T-SPIN"
                    elif cleared == 1:
                        reason = "T-SPIN SINGLE"
                    elif cleared == 2:
                        reason = "T-SPIN DOUBLE"
                    else:
                        reason = "T-SPIN TRIPLE"
                elif cleared == 4:
                    reason = "TETRIS"
                else:
                    reason = f"CLEAR x{cleared}"
                if cleared == 4:
                    self.tetrises += 1
                if self.combo > 0:
                    reason = f"{reason} COMBO {self.combo}"
                if was_b2b and (tspin or cleared == 4):
                    reason = f"{reason} B2B"
                self._add_score(total, reason)
        else:
            self.combo = -1

        self.lines += cleared
        self._recalculate_speed()
        self.can_hold = True
        if self.mode.target_lines is not None and self.lines >= self.mode.target_lines:
            self.game_over = True
            self.result_reason = "GOAL CLEAR"
            self._on_sound("gameover")
            return
        self._spawn_next_piece()

    def _fill_queue(self) -> None:
        while len(self.next_queue) < NEXT_QUEUE_SIZE:
            self.next_queue.append(Piece(self.bag.pop()))
        self.next = self.next_queue[0]

    def _spawn_next_piece(self) -> None:
        self.piece = self.next_queue.pop(0)
        self.piece.x = COLS // 2 - len(self.piece.shape[0]) // 2
        self.piece.y = 0
        self.piece.rotation = 0
        self._fill_queue()
        self._rotated_since_spawn = False
        self._last_kick_used = False
        self._contact_reset_count = 0
        self._grounded = not self.board.is_valid(self.piece, dy=1)
        self._lock_timer = 0
        self._contact_reset = False
        if not self.board.is_valid(self.piece):
            self.game_over = True
            self.result_reason = "BLOCKED SPAWN"
            self._on_sound("gameover")
