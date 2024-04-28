import os
import pygame
from typing import Optional, List
from .board import ROWS, COLS
from .piece import Piece, COLORS
from .game import GameState
from .modes import MODE_LIST
from .themes import Theme, THEMES

CELL     = 30
SIDEBAR  = 190
SCREEN_W = COLS * CELL + SIDEBAR
SCREEN_H = ROWS * CELL

BG     = (0,   0,   0)
PANEL  = (10,  10,  10)
DGRAY  = (18,  18,  18)
GRAY   = (38,  38,  38)
BORDER = (110, 110, 110)
WHITE  = (240, 240, 240)
DIM    = (135, 135, 135)
GOLD   = (255, 220,   0)
GREEN  = (0,   230,  90)
CYAN   = (0,   200, 255)

_FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "PressStart2P.ttf")

# kind 인덱스 1-7, 레벨별로 순환 (10개 팔레트)
LEVEL_PALETTES = [
    [None, (  0,240,240),(240,240,  0),(160,  0,240),(  0,240,  0),(240,  0,  0),(  0, 80,240),(240,160,  0)],  # 1 클래식
    [None, (255,160,  0),(255,120, 40),(200,100,  0),(255,180, 40),(220, 80,  0),(240,140, 20),(255,200, 60)],  # 2 앰버
    [None, (  0,160,255),( 40,100,220),(  0,200,240),( 80,140,255),( 20, 80,200),(  0,180,200),(100,180,255)],  # 3 오션
    [None, (  0,200, 80),( 80,220, 40),(  0,180,100),(160,240,  0),( 20,160, 60),(  0,220,120),(120,240, 60)],  # 4 포레스트
    [None, (180,  0,240),(220, 40,200),(140,  0,200),(255,  0,200),(160, 60,240),(120,  0,160),(200, 80,255)],  # 5 퍼플
    [None, (255, 40,  0),(255,120,  0),(200, 20,  0),(255, 80, 20),(220,  0,  0),(240,100,  0),(255,200,  0)],  # 6 파이어
    [None, (160,220,255),(200,240,255),(120,200,240),(180,240,255),(140,210,240),(100,180,220),(220,245,255)],  # 7 아이스
    [None, (255,200, 20),(220,160,  0),(255,230, 60),(200,140,  0),(255,180,  0),(240,200, 40),(255,250,100)],  # 8 골드
    [None, (255,  0,128),(  0,255,128),(200,  0,255),(255,200,  0),(  0,200,255),(255, 80,200),(100,255,  0)],  # 9 네온
    [None, (220,220,220),(180,180,180),(200,200,200),(160,160,160),(240,240,240),(140,140,140),(210,210,210)],  # 10 모노
]


def _level_color(kind: int, level: int) -> tuple:
    palette = LEVEL_PALETTES[(level - 1) % len(LEVEL_PALETTES)]
    return palette[kind]


def _load_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font(_FONT_PATH, size)
    except Exception:
        return pygame.font.Font(None, size * 2)


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
        self.font_title = _load_font(24)
        self.font_big   = _load_font(16)
        self.font_med   = _load_font(12)
        self.font_sm    = _load_font(10)
        self.font_tiny  = _load_font(8)
        self._scanline  = self._make_scanline_overlay()

    # ── 인게임 ─────────────────────────────────────────────
    def draw(self, state: GameState) -> None:
        self.screen.fill(BG)
        self._draw_board(state)
        self._draw_sidebar(state)
        if state.game_over:
            self._draw_overlay("GAME OVER", f"SCORE: {state.score:06d}", "PRESS ANY KEY", (255, 60, 60))
        elif state.paused:
            self._draw_overlay("PAUSED", "", "(P) RESUME", (160, 160, 255))
        self._flip()

    def draw_start(self, demo_state: GameState, start_level: int, blink_on: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_start_sidebar(start_level)
        self._draw_start_panel(start_level, blink_on)
        self._draw_start_title()
        pygame.display.flip()

    # ── 보드 ───────────────────────────────────────────────
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
            self._text("SPEED UP!", self.font_med, GOLD, COLS * CELL // 2, 22)

    def _draw_grid(self, surf: pygame.Surface) -> None:
        for r in range(ROWS + 1):
            pygame.draw.line(surf, GRAY, (0, r * CELL), (COLS * CELL, r * CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surf, GRAY, (c * CELL, 0), (c * CELL, ROWS * CELL))

    def _draw_locked(self, surf: pygame.Surface, state: GameState) -> None:
        # 라인 클리어 애니메이션: 350ms 동안 지우는 줄이 흰색으로 깜빡임
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
        ghost_color = tuple(min(v // 4, 45) for v in base)
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

    # ── 사이드바 ────────────────────────────────────────────
    def _draw_sidebar(self, state: GameState) -> None:
        bx = COLS * CELL
        pygame.draw.rect(self.screen, PANEL,  (bx, 0, SIDEBAR, SCREEN_H))
        pygame.draw.rect(self.screen, BORDER, (bx, 0, SIDEBAR, SCREEN_H), 1)
        pygame.draw.rect(self.screen, GRAY,   (bx + 3, 3, SIDEBAR - 6, SCREEN_H - 6), 1)
        cx = bx + SIDEBAR // 2

        self._hlabel("NEXT", cx, 14)
        self._hsep(bx, 26)
        nq = getattr(state, "next_queue", None) or [state.next]
        for i, piece in enumerate(nq[:3]):
            self._mini_board(cx, 32 + i * 54, piece)

        self._hsep(bx, 196)
        self._hlabel("HOLD", cx, 206)
        dimmed = state.held is not None and not state.can_hold
        self._mini_board(cx, 216, state.held, dimmed=dimmed)

        self._hsep(bx, 274)
        y = 284
        self._stat("SCORE", f"{state.score:06d}", cx, y, GOLD)
        ey = y + 34
        if state.last_score_delta:
            self._text(f"+{state.last_score_delta:,}", self.font_tiny, GREEN, cx, ey)
            ey += 14
        if state.combo > 0:
            self._text(f"COMBO x{state.combo}", self.font_tiny, CYAN, cx, ey)
            ey += 14
        if state.back_to_back:
            self._text("B2B", self.font_tiny, GOLD, cx, ey)

        self._hsep(bx, 360)
        self._stat("LEVEL", str(state.level), cx, 370, GREEN)
        self._hsep(bx, 410)
        self._stat("LINES", str(state.lines), cx, 420, CYAN)

        self._hsep(bx, 462)
        self._hlabel("KEYS", cx, 472)
        controls = [("< >", "Move"), ("^", "Rotate"), ("v", "Soft"),
                    ("SPC", "Hard"), ("C", "Hold"), ("P", "Pause")]
        ky = 484
        for key, desc in controls:
            ks = self.font_tiny.render(key,  True, GOLD)
            ds = self.font_tiny.render(desc, True, DIM)
            self.screen.blit(ks, (bx + 6,  ky))
            self.screen.blit(ds, (bx + 58, ky))
            ky += 16

    def _mini_board(self, cx: int, cy: int, piece: Optional[Piece],
                    cell: int = 12, dimmed: bool = False,
                    box_w: int = 88, box_h: int = 46) -> None:
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

    # ── 오버레이 ────────────────────────────────────────────
    def _draw_overlay(self, title: str, sub: str, hint: str, title_color: tuple) -> None:
        ov = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.screen.blit(ov, (0, 0))
        cx, cy = COLS * CELL // 2, ROWS * CELL // 2
        self._text(title, self.font_big,  title_color, cx, cy - 36)
        if sub:
            self._text(sub,  self.font_med, WHITE,      cx, cy + 4)
        self._text(hint, self.font_sm,   DIM,          cx, cy + 38)

    # ── 시작화면 ────────────────────────────────────────────
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
        self._text("LEVEL",             self.font_sm,  DIM,  cx, y + 38)
        self._text(str(start_level),    self.font_big, GOLD, cx, y + 60)
        self._text("^ / v  CHANGE",    self.font_sm,  DIM,  cx, y + 92)
        self._text("M  MUTE",          self.font_sm,  DIM,  cx, y + 114)

    def _draw_start_sidebar(self, start_level: int) -> None:
        bx = COLS * CELL
        pygame.draw.rect(self.screen, PANEL,  (bx, 0, SIDEBAR, SCREEN_H))
        pygame.draw.rect(self.screen, BORDER, (bx, 0, SIDEBAR, SCREEN_H), 1)
        pygame.draw.rect(self.screen, GRAY,   (bx + 3, 3, SIDEBAR - 6, SCREEN_H - 6), 1)
        cx = bx + SIDEBAR // 2
        self._text("WELCOME",        self.font_sm,  DIM,  cx, 28)
        self._hlabel("START LEVEL",  cx, 58)
        self._text(str(start_level), self.font_big, GOLD, cx, 82)
        self._hlabel("CONTROLS",     cx, 130)
        controls = [("< >", "Move"), ("^", "Rotate"), ("v", "Soft"),
                    ("SPC", "Hard"), ("C", "Hold"), ("P", "Pause"), ("R", "Restart")]
        ky = 152
        for key, desc in controls:
            ks = self.font_tiny.render(key,  True, GOLD)
            ds = self.font_tiny.render(desc, True, DIM)
            self.screen.blit(ks, (bx + 6,  ky))
            self.screen.blit(ds, (bx + 58, ky))
            ky += 16

    def _draw_start_title(self) -> None:
        self._text("TETRIS", self.font_title, GOLD, SCREEN_W // 2, 20)

    # ── 메뉴 화면 ───────────────────────────────────────────
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
        hint = f"LEVEL:{start_level}  [< >] change level  [ENTER] confirm  [ESC] back"
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
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 215))
        self.screen.blit(ov, (0, 0))

        MX, MY = 26, 16
        px, py = MX, MY
        pw, ph = SCREEN_W - MX * 2, SCREEN_H - MY * 2
        pygame.draw.rect(self.screen, PANEL,  (px, py, pw, ph))
        pygame.draw.rect(self.screen, BORDER, (px, py, pw, ph), 2)
        pygame.draw.rect(self.screen, GRAY,   (px + 4, py + 4, pw - 8, ph - 8), 1)

        cx = SCREEN_W // 2
        y  = py + 12

        ts = self.font_title.render(title, True, GOLD)
        self.screen.blit(ts, ts.get_rect(center=(cx, y + ts.get_height() // 2)))
        y += ts.get_height() + 6

        pygame.draw.line(self.screen, BORDER, (px + 8, y), (px + pw - 8, y), 1)
        y += 8

        for line in top_lines:
            s = self.font_tiny.render(line, True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, y + s.get_height() // 2)))
            y += s.get_height() + 4
        y += 4

        footer_h  = 20 if blink else 4
        item_area_end = py + ph - footer_h
        item_h    = self.font_med.get_height() + 8
        max_vis   = max(1, (item_area_end - y) // item_h)

        if len(items) > max_vis and selected < 999:
            si = max(0, selected - max_vis // 2)
            si = min(si, len(items) - max_vis)
        else:
            si = 0
        ei = min(len(items), si + max_vis)

        if si > 0:
            s = self.font_tiny.render("-- more above --", True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, y + s.get_height() // 2)))
            y += s.get_height() + 2

        for idx in range(si, ei):
            is_sel = (idx == selected) and selected != 999
            item   = items[idx]
            if is_sel:
                bar = pygame.Rect(px + 8, y - 2, pw - 16, item_h - 2)
                pygame.draw.rect(self.screen, GRAY, bar)
                pygame.draw.rect(self.screen, GOLD, bar, 1)
                txt = self._fit_text("> " + item, self.font_med, pw - 26)
                s   = self.font_med.render(txt, True, GOLD)
            else:
                txt = self._fit_text("  " + item, self.font_sm, pw - 26)
                s   = self.font_sm.render(txt, True, WHITE)
            self.screen.blit(s, s.get_rect(center=(cx, y + item_h // 2 - 1)))
            y += item_h

        if ei < len(items):
            s = self.font_tiny.render("-- more below --", True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, y + s.get_height() // 2)))

        if blink:
            s = self.font_tiny.render("PRESS ANY KEY", True, DIM)
            self.screen.blit(s, s.get_rect(center=(cx, py + ph - 12)))

    # ── 헬퍼 ───────────────────────────────────────────────
    def _make_scanline_overlay(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 2):
            pygame.draw.line(surf, (0, 0, 0, 55), (0, y), (SCREEN_W, y))
        return surf

    def _flip(self) -> None:
        self.screen.blit(self._scanline, (0, 0))
        pygame.display.flip()

    def _cell(self, surf: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        rect = pygame.Rect(cx * CELL + 1, cy * CELL + 1, CELL - 2, CELL - 2)
        pygame.draw.rect(surf, color, rect)
        hi = tuple(min(255, v + 70) for v in color)
        sh = tuple(max(0,   v - 60) for v in color)
        pygame.draw.line(surf, hi, rect.topleft,                   rect.topright,              2)
        pygame.draw.line(surf, hi, rect.topleft,                   rect.bottomleft,            2)
        pygame.draw.line(surf, sh, (rect.left,   rect.bottom - 1), (rect.right, rect.bottom - 1), 1)
        pygame.draw.line(surf, sh, (rect.right - 1, rect.top),     (rect.right - 1, rect.bottom), 1)

    def _text(self, text: str, font: pygame.font.Font, color: tuple, cx: int, cy: int) -> None:
        s = font.render(text, True, color)
        self.screen.blit(s, s.get_rect(center=(cx, cy)))

    def _fit_text(self, text: str, font: pygame.font.Font, max_w: int) -> str:
        if font.size(text)[0] <= max_w:
            return text
        while text and font.size(text + "...")[0] > max_w:
            text = text[:-1]
        return (text + "...") if text else "..."

    def _hlabel(self, text: str, cx: int, cy: int) -> None:
        self._text(text, self.font_tiny, DIM, cx, cy)

    def _label(self, text: str, cx: int, cy: int) -> None:
        self._hlabel(text, cx, cy)

    def _hsep(self, bx: int, y: int) -> None:
        pygame.draw.line(self.screen, GRAY, (bx + 6, y), (bx + SIDEBAR - 6, y), 1)

    def _stat(self, label: str, value: str, cx: int, y: int, vc: tuple) -> None:
        self._hlabel(label, cx, y)
        self._text(value, self.font_med, vc, cx, y + 20)
