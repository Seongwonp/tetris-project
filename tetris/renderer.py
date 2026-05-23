"""pygame 렌더링 전담 모듈."""

from pathlib import Path
from typing import Optional, List

import pygame

from .board import ROWS, COLS
from .piece import Piece
from .game import GameState
from .modes import MODE_LIST
from .themes import Theme, THEMES

CELL     = 30
SIDEBAR  = 200
SCREEN_W = COLS * CELL + SIDEBAR
SCREEN_H = ROWS * CELL

BG     = (12,  12,  22)
PANEL  = (18,  18,  32)
DGRAY  = (24,  24,  36)
GRAY   = (48,  48,  64)
BORDER = (90,  90, 130)
WHITE  = (240, 240, 240)
DIM    = (120, 120, 145)
GOLD   = (255, 215,  50)
GREEN  = (60,  230, 100)
CYAN   = (60,  200, 255)
RED    = (255,  60,  60)

_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "PressStart2P.ttf"

LEVEL_PALETTES = [
    [None, (  0,240,240),(240,240,  0),(160,  0,240),(  0,240,  0),(240,  0,  0),(  0, 80,240),(240,160,  0)],
    [None, (255,160,  0),(255,120, 40),(200,100,  0),(255,180, 40),(220, 80,  0),(240,140, 20),(255,200, 60)],
    [None, (  0,160,255),( 40,100,220),(  0,200,240),( 80,140,255),( 20, 80,200),(  0,180,200),(100,180,255)],
    [None, (  0,200, 80),( 80,220, 40),(  0,180,100),(160,240,  0),( 20,160, 60),(  0,220,120),(120,240, 60)],
    [None, (180,  0,240),(220, 40,200),(140,  0,200),(255,  0,200),(160, 60,240),(120,  0,160),(200, 80,255)],
    [None, (255, 40,  0),(255,120,  0),(200, 20,  0),(255, 80, 20),(220,  0,  0),(240,100,  0),(255,200,  0)],
    [None, (160,220,255),(200,240,255),(120,200,240),(180,240,255),(140,210,240),(100,180,220),(220,245,255)],
    [None, (255,200, 20),(220,160,  0),(255,230, 60),(200,140,  0),(255,180,  0),(240,200, 40),(255,250,100)],
    [None, (255,  0,128),(  0,255,128),(200,  0,255),(255,200,  0),(  0,200,255),(255, 80,200),(100,255,  0)],
    [None, (220,220,220),(180,180,180),(200,200,200),(160,160,160),(240,240,240),(140,140,140),(210,210,210)],
]


def _level_color(kind: int, level: int) -> tuple:
    palette = LEVEL_PALETTES[(level - 1) % len(LEVEL_PALETTES)]
    return palette[kind]


def _load_font(size: int) -> pygame.font.Font:
    if _FONT_PATH.is_file():
        try:
            return pygame.font.Font(str(_FONT_PATH), size)
        except Exception:
            pass
    for name in ("Courier New", "Courier", "Consolas", "Lucida Console", "DejaVu Sans Mono"):
        try:
            return pygame.font.SysFont(name, size + 4, bold=True)
        except Exception:
            pass
    return pygame.font.Font(None, size + 6)


def apply_theme(theme: Theme) -> None:
    global BG, PANEL, DGRAY, GRAY, BORDER, WHITE, DIM, GOLD, GREEN, CYAN
    BG     = theme.bg
    PANEL  = theme.panel
    DGRAY  = theme.dgray
    GRAY   = theme.gray
    BORDER = theme.border
    WHITE  = theme.white
    DIM    = theme.dim
    GOLD   = theme.gold
    GREEN  = theme.green
    CYAN   = theme.cyan


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen     = screen
        self.font_title = _load_font(22)
        self.font_big   = _load_font(14)
        self.font_med   = _load_font(11)
        self.font_sm    = _load_font(9)
        self.font_tiny  = _load_font(7)
        self._scanline  = self._make_scanline_overlay()

    # ── 인게임 ──────────────────────────────────────────────
    def draw(self, state: GameState) -> None:
        self.screen.fill(BG)
        self._draw_board(state)
        self._draw_sidebar(state)
        if state.game_over:
            self._draw_overlay(
                "GAME OVER",
                f"SCORE  {state.score:,}",
                "ANY KEY TO RETRY",
                RED,
            )
        elif state.paused:
            self._draw_overlay("PAUSED", "", "P  TO RESUME", (160, 160, 255))
        self._flip()

    def draw_start(self, demo_state: GameState, start_level: int, blink_on: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_start_sidebar(start_level)
        self._draw_start_panel(start_level, blink_on)
        self._draw_start_title()
        pygame.display.flip()

    # ── 보드 ────────────────────────────────────────────────
    def _draw_board(self, state: GameState) -> None:
        surf = pygame.Surface((COLS * CELL, ROWS * CELL))
        surf.fill(DGRAY)
        self._draw_grid(surf)
        self._draw_locked(surf, state)
        self._draw_ghost(surf, state)
        self._draw_piece(surf, state.piece, state.level)
        self.screen.blit(surf, (0, 0))
        pygame.draw.rect(self.screen, BORDER, (0, 0, COLS * CELL, ROWS * CELL), 2)

        if state.speed_up_timer > 0:
            flash = (state.speed_up_timer // 120) % 2 == 0
            color = GOLD if flash else (200, 160, 0)
            self._text("SPEED UP!", self.font_med, color, COLS * CELL // 2, 20)

    def _draw_grid(self, surf: pygame.Surface) -> None:
        for r in range(ROWS + 1):
            pygame.draw.line(surf, GRAY, (0, r * CELL), (COLS * CELL, r * CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surf, GRAY, (c * CELL, 0), (c * CELL, ROWS * CELL))

    def _draw_locked(self, surf: pygame.Surface, state: GameState) -> None:
        flash_white = (
            state.clearing_rows
            and (state.clear_anim_timer // 70) % 2 == 1
        )
        for r in range(ROWS):
            for c in range(COLS):
                kind = state.board.is_cell_filled(r, c)
                if kind:
                    if r in state.clearing_rows and flash_white:
                        self._cell(surf, c, r, (255, 255, 255))
                    else:
                        self._cell(surf, c, r, _level_color(kind, state.level))

    def _draw_ghost(self, surf: pygame.Surface, state: GameState) -> None:
        gy = state.board.ghost_y(state.piece)
        if gy == state.piece.y:
            return
        base = _level_color(state.piece.kind, state.level)
        ghost_color = tuple(min(v // 4, 50) for v in base)
        for r, row in enumerate(state.piece.shape):
            for c, v in enumerate(row):
                if v:
                    rect = pygame.Rect(
                        (state.piece.x + c) * CELL + 2,
                        (gy + r) * CELL + 2,
                        CELL - 4, CELL - 4,
                    )
                    pygame.draw.rect(surf, ghost_color, rect, width=1)

    def _draw_piece(self, surf: pygame.Surface, piece: Piece, level: int = 1) -> None:
        color = _level_color(piece.kind, level)
        for r, row in enumerate(piece.shape):
            for c, v in enumerate(row):
                if v:
                    self._cell(surf, piece.x + c, piece.y + r, color)

    # ── 사이드바 ─────────────────────────────────────────────
    def _draw_sidebar(self, state: GameState) -> None:
        bx = COLS * CELL
        # Background
        pygame.draw.rect(self.screen, PANEL, (bx, 0, SIDEBAR, SCREEN_H))
        # Outer border
        pygame.draw.rect(self.screen, BORDER, (bx, 0, SIDEBAR, SCREEN_H), 1)
        # Inner accent line
        pygame.draw.rect(self.screen, GRAY, (bx + 4, 4, SIDEBAR - 8, SCREEN_H - 8), 1)

        cx = bx + SIDEBAR // 2

        th = self.font_tiny.get_height()
        mh = self.font_med.get_height()
        bigh = self.font_big.get_height()

        y = 10

        # ── NEXT ──────────────────────
        self._hlabel("NEXT", cx, y + th // 2)
        y += th + 4
        self._hsep(bx, y); y += 6
        nq = getattr(state, "next_queue", None) or [state.next]
        for piece in nq[:3]:
            self._mini_board(cx, y, piece)
            y += 52

        # ── HOLD ──────────────────────
        self._hsep(bx, y); y += 6
        self._hlabel("HOLD", cx, y + th // 2)
        y += th + 4
        dimmed = state.held is not None and not state.can_hold
        self._mini_board(cx, y, state.held, dimmed=dimmed)
        y += 52

        # ── SCORE ─────────────────────
        self._hsep(bx, y); y += 8
        self._hlabel("SCORE", cx, y + th // 2)
        y += th + 4

        score_s = self.font_big.render(f"{state.score:,}", True, GOLD)
        self.screen.blit(score_s, score_s.get_rect(center=(cx, y + bigh // 2)))
        y += bigh + 4

        # Score extras (delta / combo / B2B)
        if state.last_score_delta:
            s = self.font_tiny.render(f"+{state.last_score_delta:,}", True, GREEN)
            self.screen.blit(s, s.get_rect(center=(cx, y + th // 2)))
            y += th + 3
        if state.combo > 0:
            s = self.font_tiny.render(f"COMBO x{state.combo}", True, CYAN)
            self.screen.blit(s, s.get_rect(center=(cx, y + th // 2)))
            y += th + 3
        if state.back_to_back:
            s = self.font_tiny.render("B2B", True, GOLD)
            self.screen.blit(s, s.get_rect(center=(cx, y + th // 2)))
            y += th + 3

        # ── LEVEL ─────────────────────
        self._hsep(bx, y + 4); y += 12
        self._hlabel("LEVEL", cx, y + th // 2)
        y += th + 4
        s = self.font_med.render(str(state.level), True, GREEN)
        self.screen.blit(s, s.get_rect(center=(cx, y + mh // 2)))
        y += mh + 6

        # ── LINES ─────────────────────
        self._hsep(bx, y); y += 8
        self._hlabel("LINES", cx, y + th // 2)
        y += th + 4
        s = self.font_med.render(str(state.lines), True, CYAN)
        self.screen.blit(s, s.get_rect(center=(cx, y + mh // 2)))
        y += mh + 6

        # ── KEYS (공간이 있을 때만) ───
        controls = [("< >", "Move"), ("^", "Rot"), ("v", "Soft"),
                    ("SPC", "Hard"), ("C", "Hold"), ("P", "Pause")]
        needed = th + 6 + (th + 3) * len(controls)
        if SCREEN_H - y - 10 >= needed:
            self._hsep(bx, y); y += 6
            self._hlabel("KEYS", cx, y + th // 2)
            y += th + 4
            for key, desc in controls:
                if y + th > SCREEN_H - 6:
                    break
                ks = self.font_tiny.render(key,  True, GOLD)
                ds = self.font_tiny.render(desc, True, DIM)
                self.screen.blit(ks, (bx + 8,  y))
                self.screen.blit(ds, (bx + 62, y))
                y += th + 3

    def _mini_board(self, cx: int, cy: int, piece: Optional[Piece],
                    cell: int = 12, dimmed: bool = False,
                    box_w: int = 90, box_h: int = 44) -> None:
        bx = cx - box_w // 2
        pygame.draw.rect(self.screen, DGRAY, (bx, cy, box_w, box_h))
        pygame.draw.rect(self.screen, GRAY,  (bx, cy, box_w, box_h), 1)
        if piece is None:
            return
        pw = len(piece.shape[0]) * cell
        ph = len(piece.shape) * cell
        sx = cx - pw // 2
        sy = cy + box_h // 2 - ph // 2
        color = tuple(v // 2 for v in piece.color) if dimmed else piece.color
        for r, row in enumerate(piece.shape):
            for c, v in enumerate(row):
                if v:
                    rect = pygame.Rect(sx + c * cell + 1, sy + r * cell + 1, cell - 2, cell - 2)
                    pygame.draw.rect(self.screen, color, rect)
                    hi = tuple(min(255, x + 60) for x in color)
                    pygame.draw.line(self.screen, hi, rect.topleft, rect.topright)
                    pygame.draw.line(self.screen, hi, rect.topleft, rect.bottomleft)

    # ── 오버레이 ──────────────────────────────────────────────
    def _draw_overlay(self, title: str, sub: str, hint: str, title_color: tuple) -> None:
        ov = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        self.screen.blit(ov, (0, 0))

        cx = COLS * CELL // 2
        cy = ROWS * CELL // 2

        th = self.font_big.get_height()
        sh = self.font_sm.get_height()
        hint_h = self.font_tiny.get_height()

        total_h = th + 10 + (sh + 6 if sub else 0) + hint_h
        pw = min(COLS * CELL - 40, 260)
        ph = total_h + 40
        px = cx - pw // 2
        py = cy - ph // 2

        pygame.draw.rect(self.screen, PANEL, (px, py, pw, ph))
        pygame.draw.rect(self.screen, title_color, (px, py, pw, ph), 2)
        pygame.draw.rect(self.screen, GRAY, (px + 5, py + 5, pw - 10, ph - 10), 1)

        iy = py + 16
        ts = self.font_big.render(title, True, title_color)
        self.screen.blit(ts, ts.get_rect(center=(cx, iy + th // 2)))
        iy += th + 10

        if sub:
            ss = self.font_sm.render(sub, True, WHITE)
            self.screen.blit(ss, ss.get_rect(center=(cx, iy + sh // 2)))
            iy += sh + 6

        hs = self.font_tiny.render(hint, True, DIM)
        self.screen.blit(hs, hs.get_rect(center=(cx, iy + hint_h // 2)))

    # ── 시작화면 ──────────────────────────────────────────────
    def _draw_start_panel(self, start_level: int, blink_on: bool) -> None:
        ov = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 195))
        self.screen.blit(ov, (0, 0))
        pw, ph = 248, 176
        px = (COLS * CELL - pw) // 2
        py = (ROWS * CELL - ph) // 2
        pygame.draw.rect(self.screen, PANEL,  (px, py, pw, ph))
        pygame.draw.rect(self.screen, BORDER, (px, py, pw, ph), 2)
        pygame.draw.rect(self.screen, GRAY,   (px + 4, py + 4, pw - 8, ph - 8), 1)
        cx = COLS * CELL // 2
        y = py + 28
        if blink_on:
            self._text("PRESS ANY KEY", self.font_med, WHITE, cx, y)
        self._text("LEVEL",          self.font_sm,  DIM,  cx, y + 38)
        self._text(str(start_level), self.font_big, GOLD, cx, y + 60)
        self._text("^ / v  CHANGE", self.font_sm,  DIM,  cx, y + 92)
        self._text("M  MUTE",       self.font_sm,  DIM,  cx, y + 114)

    def _draw_start_sidebar(self, start_level: int) -> None:
        bx = COLS * CELL
        pygame.draw.rect(self.screen, PANEL,  (bx, 0, SIDEBAR, SCREEN_H))
        pygame.draw.rect(self.screen, BORDER, (bx, 0, SIDEBAR, SCREEN_H), 1)
        pygame.draw.rect(self.screen, GRAY,   (bx + 4, 4, SIDEBAR - 8, SCREEN_H - 8), 1)
        cx = bx + SIDEBAR // 2
        self._text("WELCOME",        self.font_sm,  DIM,  cx, 28)
        self._hlabel("START LEVEL",  cx, 56)
        self._text(str(start_level), self.font_big, GOLD, cx, 80)
        self._hlabel("CONTROLS",     cx, 128)
        controls = [("< >", "Move"), ("^", "Rotate"), ("v", "Soft"),
                    ("SPC", "Hard"), ("C", "Hold"), ("P", "Pause"), ("R", "Restart")]
        ky = 148
        for key, desc in controls:
            ks = self.font_tiny.render(key,  True, GOLD)
            ds = self.font_tiny.render(desc, True, DIM)
            self.screen.blit(ks, (bx + 8,  ky))
            self.screen.blit(ds, (bx + 60, ky))
            ky += 16

    def _draw_start_title(self) -> None:
        self._text("TETRIS", self.font_title, GOLD, SCREEN_W // 2, 20)

    # ── 메뉴 화면 ─────────────────────────────────────────────
    def draw_title_menu(self, demo_state: GameState, selected: int, mode_title: str,
                        theme_title: str, bgm_title: str, blink_on: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        info = f"MODE:{mode_title}  THEME:{theme_title}  BGM:{bgm_title}"
        self._draw_menu_panel(
            "TETRIS",
            [info],
            ["START", "MODE", "SETTINGS", "SCORES", "REPLAYS", "ACHIEVEMENTS", "QUIT"],
            selected, blink_on,
        )
        self._flip()

    def draw_mode_menu(self, demo_state: GameState, selected: int, start_level: int) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        items = [f"{m.title} - {m.description}" for m in MODE_LIST]
        hint = f"LEVEL:{start_level}  [< >] level  [ENTER] confirm  [ESC] back"
        self._draw_menu_panel("MODE SELECT", [hint], items, selected, False)
        self._flip()

    def draw_settings_menu(self, demo_state: GameState, lines: List[str], selected: int, waiting: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        hint = "PRESS A KEY..." if waiting else "[ENTER] edit  [ESC] back"
        self._draw_menu_panel("SETTINGS", [hint], lines, selected, waiting)
        self._flip()

    def draw_scores_menu(self, demo_state: GameState, top_lines: List[str], bottom_lines: List[str]) -> None:
        self.draw_info_menu(demo_state, "SCORES", top_lines, bottom_lines)

    def draw_info_menu(self, demo_state: GameState, title: str, lines: List[str], footer_lines: List[str]) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_menu_panel(title, footer_lines, lines, 999, False)
        self._flip()

    def draw_result_menu(self, demo_state: GameState, title: str, lines: List[str],
                         options: List[str], selected: int) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_menu_panel(title, lines, options, selected, False)
        self._flip()

    def _draw_menu_panel(self, title: str, top_lines: List[str], items: List[str],
                         selected: int, blink: bool) -> None:
        # 반투명 배경
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 220))
        self.screen.blit(ov, (0, 0))

        MX, MY = 28, 18
        px, py = MX, MY
        pw, ph = SCREEN_W - MX * 2, SCREEN_H - MY * 2

        # 패널 배경
        pygame.draw.rect(self.screen, PANEL,  (px, py, pw, ph))
        pygame.draw.rect(self.screen, BORDER, (px, py, pw, ph), 2)
        pygame.draw.rect(self.screen, GRAY,   (px + 5, py + 5, pw - 10, ph - 10), 1)

        cx = SCREEN_W // 2
        lh_title = self.font_title.get_height()
        lh_tiny  = self.font_tiny.get_height()
        lh_med   = self.font_med.get_height()
        lh_sm    = self.font_sm.get_height()

        y = py + 14

        # 타이틀
        ts = self.font_title.render(title, True, GOLD)
        self.screen.blit(ts, ts.get_rect(center=(cx, y + lh_title // 2)))
        y += lh_title + 8
        pygame.draw.line(self.screen, BORDER, (px + 10, y), (px + pw - 10, y), 1)
        y += 10

        # 상단 정보 줄
        for line in top_lines:
            line = self._fit_text(line, self.font_tiny, pw - 24)
            s = self.font_tiny.render(line, True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, y + lh_tiny // 2)))
            y += lh_tiny + 4
        y += 6

        # 하단 여백 계산
        blink_h = lh_tiny + 12 if blink else 0
        footer_y = py + ph - blink_h - 10

        # 아이템 높이 (실제 폰트 메트릭 기반)
        item_pad = 9
        item_h = lh_med + item_pad * 2

        avail_h = footer_y - y - 4
        max_vis = max(1, avail_h // item_h)

        # 스크롤 윈도우
        if len(items) > max_vis and selected < 999:
            si = max(0, min(selected - max_vis // 2, len(items) - max_vis))
        else:
            si = 0
        ei = min(len(items), si + max_vis)

        # 클리핑으로 패널 바깥 렌더링 방지
        clip = pygame.Rect(px + 6, y - 2, pw - 12, footer_y - y + 4)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip)

        iy = y
        if si > 0:
            s = self.font_tiny.render("-- more above --", True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, iy + lh_tiny // 2)))
            iy += lh_tiny + 4

        for idx in range(si, ei):
            is_sel = (idx == selected) and selected != 999
            item = items[idx]
            if is_sel:
                bar = pygame.Rect(px + 8, iy + 2, pw - 16, item_h - 4)
                pygame.draw.rect(self.screen, GRAY, bar)
                pygame.draw.rect(self.screen, GOLD, bar, 1)
                txt = self._fit_text("> " + item, self.font_med, pw - 32)
                s = self.font_med.render(txt, True, GOLD)
            else:
                txt = self._fit_text("  " + item, self.font_sm, pw - 32)
                s = self.font_sm.render(txt, True, WHITE)
            self.screen.blit(s, s.get_rect(center=(cx, iy + item_h // 2)))
            iy += item_h

        if ei < len(items):
            s = self.font_tiny.render("-- more below --", True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, iy + lh_tiny // 2)))

        self.screen.set_clip(old_clip)

        if blink:
            s = self.font_tiny.render("PRESS ANY KEY", True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, py + ph - blink_h // 2 - 4)))

    # ── 헬퍼 ────────────────────────────────────────────────
    def _make_scanline_overlay(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 2):
            pygame.draw.line(surf, (0, 0, 0, 50), (0, y), (SCREEN_W, y))
        return surf

    def _flip(self) -> None:
        self.screen.blit(self._scanline, (0, 0))
        pygame.display.flip()

    def _cell(self, surf: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        rect = pygame.Rect(cx * CELL + 1, cy * CELL + 1, CELL - 2, CELL - 2)
        pygame.draw.rect(surf, color, rect)
        hi = tuple(min(255, v + 70) for v in color)
        sh = tuple(max(0,   v - 60) for v in color)
        pygame.draw.line(surf, hi, rect.topleft,                    rect.topright,               2)
        pygame.draw.line(surf, hi, rect.topleft,                    rect.bottomleft,             2)
        pygame.draw.line(surf, sh, (rect.left,    rect.bottom - 1), (rect.right, rect.bottom - 1), 1)
        pygame.draw.line(surf, sh, (rect.right - 1, rect.top),      (rect.right - 1, rect.bottom), 1)

    def _text(self, text: str, font: pygame.font.Font, color: tuple, cx: int, cy: int) -> None:
        s = font.render(text, True, color)
        self.screen.blit(s, s.get_rect(center=(cx, cy)))

    def _fit_text(self, text: str, font: pygame.font.Font, max_w: int) -> str:
        if font.size(text)[0] <= max_w:
            return text
        while len(text) > 1 and font.size(text + "...")[0] > max_w:
            text = text[:-1]
        return (text + "...") if text else "..."

    def _hlabel(self, text: str, cx: int, cy: int) -> None:
        self._text(text, self.font_tiny, DIM, cx, cy)

    def _label(self, text: str, cx: int, cy: int) -> None:
        self._hlabel(text, cx, cy)

    def _hsep(self, bx: int, y: int) -> None:
        pygame.draw.line(self.screen, GRAY, (bx + 8, y), (bx + SIDEBAR - 8, y), 1)

    def _stat(self, label: str, value: str, cx: int, y: int, vc: tuple) -> None:
        self._hlabel(label, cx, y)
        self._text(value, self.font_med, vc, cx, y + 20)
