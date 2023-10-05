import pygame
from typing import Optional, List
from .board import ROWS, COLS
from .piece import Piece, COLORS
from .game import GameState
from .modes import MODE_LIST
from .themes import Theme, THEMES

UI_SCALE = 1.125  # 32 -> 36


def ui(value: int) -> int:
    return int(round(value * UI_SCALE))


CELL = ui(32)
SIDEBAR = ui(210)
SCREEN_W = COLS * CELL + SIDEBAR
SCREEN_H = ROWS * CELL

BG     = (18,  18,  28)
PANEL  = (25,  25,  42)
DGRAY  = (30,  30,  38)
GRAY   = (55,  55,  70)
BORDER = (80,  80, 130)
WHITE  = (240, 240, 240)
DIM    = (130, 130, 150)
GOLD   = (255, 215,  50)
GREEN  = (80,  255, 130)
CYAN   = (80,  210, 255)


def apply_theme(theme: Theme) -> None:
    global BG, PANEL, DGRAY, GRAY, BORDER, WHITE, DIM, GOLD, GREEN, CYAN
    BG = theme.bg
    PANEL = theme.panel
    DGRAY = theme.dgray
    GRAY = theme.gray
    BORDER = theme.border
    WHITE = theme.white
    DIM = theme.dim
    GOLD = theme.gold
    GREEN = theme.green
    CYAN = theme.cyan


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_title = self._font(ui(44), bold=True)
        self.font_big   = self._font(ui(30), bold=True)
        self.font_med   = self._font(ui(18), bold=True)
        self.font_sm    = self._font(ui(13))
        self.font_tiny  = self._font(ui(11))

    # ── 메인 ──────────────────────────────────────────────
    def draw(self, state: GameState) -> None:
        self.screen.fill(BG)
        self._draw_board(state)
        self._draw_sidebar(state)
        if state.game_over:
            self._draw_overlay("GAME OVER", f"Score: {state.score:,}", "PRESS ANY KEY", (255, 70, 70))
        elif state.paused:
            self._draw_overlay("PAUSED", "", "(P) to resume", (180, 180, 255))
        pygame.display.flip()

    def draw_start(self, demo_state: GameState, start_level: int, blink_on: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_start_sidebar(start_level)
        self._draw_start_panel(start_level, blink_on)
        self._draw_start_title()
        pygame.display.flip()

    # ── 보드 영역 ─────────────────────────────────────────
    def _draw_board(self, state: GameState) -> None:
        surf = pygame.Surface((COLS * CELL, ROWS * CELL))
        surf.fill(DGRAY)

        self._draw_grid(surf)
        self._draw_locked(surf, state)
        self._draw_ghost(surf, state)
        self._draw_piece(surf, state.piece)

        self.screen.blit(surf, (0, 0))
        pygame.draw.rect(self.screen, BORDER, (0, 0, COLS * CELL, ROWS * CELL), 2)
        if state.speed_up_timer > 0:
            self._text("SPEED UP!", self.font_med, GOLD, COLS * CELL // 2, ui(36))

    def _draw_grid(self, surf: pygame.Surface) -> None:
        for r in range(ROWS + 1):
            pygame.draw.line(surf, GRAY, (0, r * CELL), (COLS * CELL, r * CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surf, GRAY, (c * CELL, 0), (c * CELL, ROWS * CELL))

    def _draw_locked(self, surf: pygame.Surface, state: GameState) -> None:
        for r in range(ROWS):
            for c in range(COLS):
                kind = state.board.is_cell_filled(r, c)
                if kind:
                    self._cell(surf, c, r, COLORS[kind])

    def _draw_ghost(self, surf: pygame.Surface, state: GameState) -> None:
        gy = state.board.ghost_y(state.piece)
        if gy == state.piece.y:
            return
        for r, row in enumerate(state.piece.shape):
            for c, v in enumerate(row):
                if v:
                    rect = pygame.Rect(
                        (state.piece.x + c) * CELL + 2,
                        (gy + r) * CELL + 2,
                        CELL - 4, CELL - 4,
                    )
                    ghost_color = tuple(max(0, x // 5) for x in state.piece.color)
                    pygame.draw.rect(surf, ghost_color, rect, width=2, border_radius=4)

    def _draw_piece(self, surf: pygame.Surface, piece: Piece) -> None:
        for r, row in enumerate(piece.shape):
            for c, v in enumerate(row):
                if v:
                    self._cell(surf, piece.x + c, piece.y + r, piece.color)

    # ── 사이드바 ──────────────────────────────────────────
    def _draw_sidebar(self, state: GameState) -> None:
        bx = COLS * CELL
        pygame.draw.rect(self.screen, PANEL, (bx, 0, SIDEBAR, SCREEN_H))
        pygame.draw.rect(self.screen, BORDER, (bx, 0, SIDEBAR, SCREEN_H), 1)

        cx = bx + SIDEBAR // 2  # 중앙 x

        # NEXT
        self._label("NEXT", cx, ui(28))
        next_queue = getattr(state, "next_queue", None) or [state.next]
        for index, piece in enumerate(next_queue[:3]):
            self._mini_board(
                cx,
                ui(50 + index * 52),
                piece,
                cell=ui(13),
                box_w=ui(100),
                box_h=ui(44),
            )

        # HOLD
        self._label("HOLD", cx, ui(218))
        dimmed = state.held is not None and not state.can_hold
        self._mini_board(cx, ui(244), state.held, dimmed=dimmed)

        # SCORE / LEVEL / LINES
        score_y = ui(326)
        self._stat("SCORE", f"{state.score:,}", cx, score_y, GOLD)
        if state.last_score_delta:
            delta = f"+{state.last_score_delta:,} {state.last_score_reason}"
            self._text(delta, self.font_tiny, DIM, cx, score_y + ui(40))
        if state.combo > 0:
            self._text(f"COMBO x{state.combo}", self.font_tiny, CYAN, cx, score_y + ui(58))
        if state.back_to_back:
            self._text("B2B", self.font_tiny, GOLD, cx, score_y + ui(76))
        self._stat("LEVEL", str(state.level),   cx, ui(386), GREEN)
        self._stat("LINES", str(state.lines),   cx, ui(444), CYAN)

        # 조작 안내
        controls = [
            ("← →",  "Move"),
            ("↑",    "Rotate"),
            ("↓",    "Soft drop"),
            ("SPACE","Hard drop"),
            ("C",    "Hold"),
            ("P",    "Pause"),
            ("R",    "Restart"),
        ]
        y = ui(506)
        for key, desc in controls:
            ks = self.font_tiny.render(key, True, (210, 210, 100))
            ds = self.font_tiny.render(desc, True, DIM)
            self.screen.blit(ks, (bx + ui(8),  y))
            self.screen.blit(ds, (bx + ui(70), y))
            y += ui(16)

    def _mini_board(self, cx: int, cy: int, piece: Optional[Piece],
                    cell: int = ui(22), dimmed: bool = False,
                    box_w: int = ui(100), box_h: int = ui(70)) -> None:
        bx = cx - box_w // 2
        pygame.draw.rect(self.screen, DGRAY, (bx, cy, box_w, box_h), border_radius=ui(6))
        if piece is None:
            return
        pw = len(piece.shape[0]) * cell
        ph = len(piece.shape)    * cell
        sx = cx - pw // 2
        sy = cy + box_h // 2 - ph // 2
        color = tuple(v // 2 for v in piece.color) if dimmed else piece.color
        hi    = tuple(min(255, int(v * 1.3)) for v in color)
        for r, row in enumerate(piece.shape):
            for c, v in enumerate(row):
                if v:
                    rect = pygame.Rect(sx + c * cell + 1, sy + r * cell + 1, cell - 2, cell - 2)
                    pygame.draw.rect(self.screen, color, rect, border_radius=ui(3))
                    pygame.draw.rect(self.screen, hi,    rect, width=2, border_radius=ui(3))

    # ── 오버레이 ──────────────────────────────────────────
    def _draw_overlay(self, title: str, sub: str, hint: str,
                      title_color: tuple) -> None:
        ov = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        self.screen.blit(ov, (0, 0))
        cx, cy = COLS * CELL // 2, ROWS * CELL // 2
        self._text(title, self.font_big,  title_color, cx, cy - ui(40))
        if sub:
            self._text(sub,   self.font_med,  WHITE,       cx, cy + ui(8))
        self._text(hint,  self.font_sm,   DIM,         cx, cy + ui(48))

    # ── 시작 화면 ─────────────────────────────────────────
    def _draw_start_panel(self, start_level: int, blink_on: bool) -> None:
        ov = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))

        panel_w = COLS * CELL - ui(60)
        panel_h = ui(210)
        panel_x = (COLS * CELL - panel_w) // 2
        panel_y = (ROWS * CELL - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=ui(12))
        pygame.draw.rect(self.screen, BORDER, panel, width=2, border_radius=ui(12))

        cx = COLS * CELL // 2
        y = panel_y + ui(46)
        if blink_on:
            self._text("PRESS ANY KEY", self.font_big, WHITE, cx, y)
        self._text("LEVEL", self.font_sm, DIM, cx, y + ui(44))
        self._text(str(start_level), self.font_med, GOLD, cx, y + ui(70))
        self._text("UP/DOWN TO CHANGE", self.font_sm, DIM, cx, y + ui(98))
        self._text("M TO MUTE", self.font_sm, DIM, cx, y + ui(126))

    def _draw_start_sidebar(self, start_level: int) -> None:
        bx = COLS * CELL
        pygame.draw.rect(self.screen, PANEL, (bx, 0, SIDEBAR, SCREEN_H))
        pygame.draw.rect(self.screen, BORDER, (bx, 0, SIDEBAR, SCREEN_H), 1)

        cx = bx + SIDEBAR // 2
        self._text("WELCOME", self.font_med, WHITE, cx, ui(34))
        self._label("LEVEL", cx, ui(74))
        self._text(str(start_level), self.font_med, GOLD, cx, ui(96))

        self._label("CONTROLS", cx, ui(150))
        controls = [
            ("← →",  "Move"),
            ("↑",    "Rotate"),
            ("↓",    "Soft drop"),
            ("SPACE","Hard drop"),
            ("C",    "Hold"),
            ("P",    "Pause"),
            ("R",    "Restart"),
        ]
        y = ui(180)
        for key, desc in controls:
            ks = self.font_tiny.render(key, True, (210, 210, 100))
            ds = self.font_tiny.render(desc, True, DIM)
            self.screen.blit(ks, (bx + ui(8),  y))
            self.screen.blit(ds, (bx + ui(70), y))
            y += ui(16)

    def _draw_start_title(self) -> None:
        cx = SCREEN_W // 2
        self._text("TETRIS", self.font_title, WHITE, cx, ui(24))

    # ── 메뉴/설정 화면 ─────────────────────────────────────
    def draw_title_menu(self, demo_state: GameState, selected: int, mode_title: str,
                        theme_title: str, bgm_title: str, blink_on: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_menu_panel(
            "TETRIS",
            [
                "ENTER TO START",
                f"MODE: {mode_title}",
                f"THEME: {theme_title}",
                f"BGM: {bgm_title}",
            ],
            ["START", "MODE", "SETTINGS", "SCORES", "QUIT"],
            selected,
            blink_on,
        )
        pygame.display.flip()

    def draw_mode_menu(self, demo_state: GameState, selected: int, start_level: int) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        items = [f"{mode.title} — {mode.description}" for mode in MODE_LIST]
        self._draw_menu_panel("MODE SELECT", [f"LEVEL: {start_level}", "ENTER to confirm"], items, selected, True)
        pygame.display.flip()

    def draw_settings_menu(self, demo_state: GameState, lines: List[str], selected: int, waiting: bool) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        hint = "PRESS A KEY" if waiting else "ENTER to edit / ESC back"
        self._draw_menu_panel("SETTINGS", [hint], lines, selected, waiting)
        pygame.display.flip()

    def draw_scores_menu(self, demo_state: GameState, top_lines: List[str], bottom_lines: List[str]) -> None:
        self.draw_info_menu(demo_state, "SCORES", top_lines, bottom_lines)

    def draw_info_menu(self, demo_state: GameState, title: str, lines: List[str], footer_lines: List[str]) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_menu_panel(title, footer_lines, lines, 999, False)
        pygame.display.flip()

    def draw_result_menu(self, demo_state: GameState, title: str, lines: List[str], options: List[str], selected: int) -> None:
        self.screen.fill(BG)
        self._draw_board(demo_state)
        self._draw_menu_panel(title, lines, options, selected, False)
        pygame.display.flip()

    def _draw_menu_panel(self, title: str, top_lines: List[str], items: List[str], selected: int, blink: bool) -> None:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        self.screen.blit(ov, (0, 0))
        panel_w = SCREEN_W - ui(70)

        # dynamic height based on content so menus adapt to different item counts / screen sizes
        title_h = self.font_title.get_height()
        sm_h = self.font_sm.get_height()
        med_h = self.font_med.get_height()
        padding_v = ui(18)

        top_lines_h = len(top_lines) * (sm_h + ui(6))
        selected_item_h = med_h + ui(8)
        normal_item_h = sm_h + ui(6)
        items_total_h = sum(selected_item_h if i == selected else normal_item_h for i in range(len(items)))

        content_h = ui(16) + title_h + ui(8) + top_lines_h + ui(8) + items_total_h + padding_v * 2
        max_panel_h = SCREEN_H - ui(110)
        panel_h = min(max_panel_h, max(ui(220), content_h))

        panel_x = ui(35)
        panel_y = (SCREEN_H - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=ui(14))
        pygame.draw.rect(self.screen, BORDER, panel, width=2, border_radius=ui(14))
        pygame.draw.rect(self.screen, (255, 255, 255), (panel_x + ui(10), panel_y + ui(10), panel_w - ui(20), panel_h - ui(20)), width=1, border_radius=ui(12))
        pygame.draw.rect(self.screen, GOLD, (panel_x, panel_y + ui(18), ui(4), panel_h - ui(36)))
        pygame.draw.rect(self.screen, CYAN, (panel_x + panel_w - ui(4), panel_y + ui(18), ui(4), panel_h - ui(36)))

        cx = SCREEN_W // 2
        y = panel_y + ui(16)

        # subtle glow behind title (centered)
        glow_w = max(ui(120), panel_w - ui(160))
        glow_h = title_h + ui(12)
        glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        for i in range(6):
            alpha = max(0, 40 - i * 6)
            rect = pygame.Rect(i * ui(2), i * ui(1), glow_w - i * ui(4), glow_h - i * ui(2))
            pygame.draw.rect(glow_surf, (GOLD[0], GOLD[1], GOLD[2], alpha), rect, border_radius=ui(20))
        self.screen.blit(glow_surf, (panel_x + (panel_w - glow_w) // 2, y - ui(6)))

        self._text(title, self.font_title, WHITE, cx, y)
        y += title_h + ui(8)

        for line in top_lines:
            fit = self._fit_text(line, self.font_sm, panel_w - ui(90))
            self._text(fit, self.font_sm, DIM, cx, y)
            y += sm_h + ui(6)
        y += ui(6)

        # compute visible window for items (paging/scroll if too many)
        avail_items_area = panel_h - (y - panel_y) - ui(56)
        slot_h = normal_item_h
        max_slots = max(1, avail_items_area // slot_h)
        if len(items) > max_slots:
            start_index = max(0, selected - max_slots // 2)
            start_index = min(start_index, len(items) - max_slots)
        else:
            start_index = 0
        end_index = min(len(items), start_index + max_slots)

        for idx in range(start_index, end_index):
            item = items[idx]
            is_sel = (idx == selected)
            color = GOLD if is_sel else WHITE
            prefix = "▶ " if is_sel else "  "
            font = self.font_sm if len(item) < 30 else self.font_tiny
            if is_sel and selected != 999:
                highlight = pygame.Rect(panel_x + ui(18), y - ui(12), panel_w - ui(36), ui(30))
                glow = pygame.Surface((highlight.width + ui(12), highlight.height + ui(8)), pygame.SRCALPHA)
                pygame.draw.rect(glow, (CYAN[0], CYAN[1], CYAN[2], 28), glow.get_rect(), border_radius=ui(12))
                self.screen.blit(glow, (highlight.x - ui(6), highlight.y - ui(4)))
                pygame.draw.rect(self.screen, (40, 40, 60), highlight, border_radius=ui(10))
                pygame.draw.rect(self.screen, GOLD, highlight, width=1, border_radius=ui(10))
            text = self._fit_text(prefix + item, font if not is_sel else self.font_med, panel_w - ui(92))
            self._text(text, font if not is_sel else self.font_med, color, cx, y)
            y += selected_item_h if is_sel else normal_item_h

        if blink:
            self._text("PRESS ANY KEY", self.font_sm, DIM, cx, panel_y + panel_h - ui(24))
        pygame.draw.line(self.screen, BORDER, (panel_x + ui(18), panel_y + ui(58)), (panel_x + panel_w - ui(18), panel_y + ui(58)), 1)

    # ── 헬퍼 ──────────────────────────────────────────────
    def _cell(self, surf: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        hi = tuple(min(255, int(v * 1.3)) for v in color)
        rect = pygame.Rect(cx * CELL + 1, cy * CELL + 1, CELL - 2, CELL - 2)
        pygame.draw.rect(surf, color, rect, border_radius=ui(4))
        pygame.draw.rect(surf, hi,    rect, width=2, border_radius=ui(4))

    def _text(self, text: str, font: pygame.font.Font,
              color: tuple, cx: int, cy: int) -> None:
        s = font.render(text, True, color)
        self.screen.blit(s, s.get_rect(center=(cx, cy)))

    def _fit_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis if text else ellipsis

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        for name in ("Avenir Next", "Helvetica Neue", "Arial", "DejaVu Sans"):
            path = pygame.font.match_font(name, bold=bold)
            if path:
                return pygame.font.Font(path, size)
        return pygame.font.Font(None, size)

    def _label(self, text: str, cx: int, cy: int) -> None:
        self._text(text, self.font_sm, DIM, cx, cy)

    def _stat(self, label: str, value: str, cx: int, y: int, vc: tuple) -> None:
        self._label(label, cx, y)
        self._text(value, self.font_med, vc, cx, y + ui(22))
