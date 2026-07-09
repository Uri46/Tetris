"""Rendering helpers for menus, panels, board, and overlays."""

from __future__ import annotations

import math

import pygame

from . import config
from .piece import Piece, SHAPES
from .score import ScoreManager


class UI:
    """All drawing code for the game."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = self._font(70, bold=True)
        self.font_large = self._font(42, bold=True)
        self.font_medium = self._font(26, bold=True)
        self.font_body = self._font(20)
        self.font_small = self._font(15)

        self.menu_buttons = {
            "play": pygame.Rect(config.WINDOW_WIDTH // 2 - 110, 415, 220, 56),
            "quit": pygame.Rect(config.WINDOW_WIDTH // 2 - 110, 485, 220, 50),
        }
        self.pause_buttons = {
            "resume": pygame.Rect(config.WINDOW_WIDTH // 2 - 120, 315, 240, 52),
            "restart": pygame.Rect(config.WINDOW_WIDTH // 2 - 120, 380, 240, 52),
            "quit": pygame.Rect(config.WINDOW_WIDTH // 2 - 120, 445, 240, 52),
        }
        self.game_over_buttons = {
            "restart": pygame.Rect(config.WINDOW_WIDTH // 2 - 120, 402, 240, 52),
            "menu": pygame.Rect(config.WINDOW_WIDTH // 2 - 120, 467, 240, 52),
            "quit": pygame.Rect(config.WINDOW_WIDTH // 2 - 120, 532, 240, 52),
        }

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        font_name = pygame.font.match_font("segoeui") or pygame.font.get_default_font()
        font = pygame.font.Font(font_name, size)
        font.set_bold(bold)
        return font

    def draw_background(self) -> None:
        self.screen.fill(config.COLOR_BACKGROUND)
        ticks = pygame.time.get_ticks() / 1000

        for x in range(-80, config.WINDOW_WIDTH, 40):
            offset = int((math.sin(ticks * 0.45 + x * 0.01) + 1) * 6)
            pygame.draw.line(
                self.screen,
                config.COLOR_BACKGROUND_GRID,
                (x + offset, 0),
                (x + 120 + offset, config.WINDOW_HEIGHT),
                1,
            )

    def draw_game(
        self,
        board,
        current_piece: Piece | None,
        next_piece: Piece | None,
        held_piece: Piece | None,
        score: ScoreManager,
        ghost_y: int | None,
        clearing_rows: list[int],
        clear_progress: float,
        landing_progress: float,
        show_fps: bool,
        fps: float,
    ) -> None:
        self.draw_background()
        self._draw_board_frame()
        self._draw_locked_cells(board)

        if current_piece and ghost_y is not None:
            self._draw_piece(current_piece, ghost_y=ghost_y, ghost=True)
            self._draw_piece(current_piece, landing_progress=landing_progress)

        if clearing_rows:
            self._draw_line_clear_animation(clearing_rows, clear_progress)

        self._draw_board_grid()
        self._draw_side_panel(score, next_piece, held_piece)

        if show_fps:
            fps_text = self.font_small.render(f"FPS {fps:.0f}", True, config.COLOR_TEXT_MUTED)
            self.screen.blit(fps_text, (18, config.WINDOW_HEIGHT - 28))

    def draw_menu(self, high_score: int) -> None:
        self.draw_background()
        ticks = pygame.time.get_ticks() / 1000
        title_y = 165 + int(math.sin(ticks * 1.8) * 5)

        self._draw_center_text(
            "TETRIS",
            self.font_title,
            config.COLOR_TEXT,
            title_y,
            shadow=True,
        )
        self._draw_center_text(
            "Profesional",
            self.font_medium,
            config.COLOR_ACCENT,
            title_y + 78,
        )
        self._draw_center_text(
            f"Récord {high_score}",
            self.font_body,
            config.COLOR_TEXT_MUTED,
            title_y + 128,
        )

        mouse = pygame.mouse.get_pos()
        self._draw_button("Jugar", self.menu_buttons["play"], mouse, primary=True)
        self._draw_button("Salir", self.menu_buttons["quit"], mouse, primary=False)
        self._draw_falling_preview()

    def draw_pause_overlay(self) -> None:
        self._dim_screen(190)
        self._draw_center_text("Pausa", self.font_large, config.COLOR_TEXT, 240, shadow=True)

        mouse = pygame.mouse.get_pos()
        self._draw_button("Continuar", self.pause_buttons["resume"], mouse, primary=True)
        self._draw_button("Reiniciar", self.pause_buttons["restart"], mouse, primary=False)
        self._draw_button("Salir", self.pause_buttons["quit"], mouse, primary=False)

    def draw_game_over_overlay(self, score: ScoreManager) -> None:
        self._dim_screen(210)
        self._draw_center_text(
            "Game Over",
            self.font_large,
            config.COLOR_DANGER,
            230,
            shadow=True,
        )
        self._draw_center_text(
            f"Puntaje {score.score}",
            self.font_medium,
            config.COLOR_TEXT,
            292,
        )
        self._draw_center_text(
            f"Récord {score.high_score}",
            self.font_body,
            config.COLOR_TEXT_MUTED,
            332,
        )

        mouse = pygame.mouse.get_pos()
        self._draw_button("Reintentar", self.game_over_buttons["restart"], mouse, primary=True)
        self._draw_button("Menú", self.game_over_buttons["menu"], mouse, primary=False)
        self._draw_button("Salir", self.game_over_buttons["quit"], mouse, primary=False)

    def _draw_board_frame(self) -> None:
        frame = pygame.Rect(
            config.BOARD_X - 10,
            config.BOARD_Y - 10,
            config.BOARD_WIDTH + 20,
            config.BOARD_HEIGHT + 20,
        )
        self._draw_shadow(frame, radius=8)
        pygame.draw.rect(self.screen, config.COLOR_SURFACE_DARK, frame, border_radius=8)
        pygame.draw.rect(self.screen, config.COLOR_BORDER, frame, 1, border_radius=8)

        board_rect = pygame.Rect(
            config.BOARD_X,
            config.BOARD_Y,
            config.BOARD_WIDTH,
            config.BOARD_HEIGHT,
        )
        pygame.draw.rect(self.screen, (9, 12, 19), board_rect)

    def _draw_locked_cells(self, board) -> None:
        for row_index, row in enumerate(board.grid):
            for col_index, shape in enumerate(row):
                if shape:
                    self._draw_cell(col_index, row_index, config.PIECE_COLORS[shape])

    def _draw_piece(
        self,
        piece: Piece,
        ghost_y: int | None = None,
        ghost: bool = False,
        landing_progress: float = 0,
    ) -> None:
        y = piece.y if ghost_y is None else ghost_y
        color = config.PIECE_COLORS[piece.shape]
        for cell_x, cell_y in piece.cells(y=y):
            if cell_y < 0:
                continue
            if ghost:
                self._draw_ghost_cell(cell_x, cell_y)
            else:
                if landing_progress > 0:
                    self._draw_landing_cell(cell_x, cell_y, landing_progress)
                self._draw_cell(cell_x, cell_y, color)

    def _draw_cell(self, grid_x: int, grid_y: int, color: tuple[int, int, int]) -> None:
        x = config.BOARD_X + grid_x * config.CELL_SIZE
        y = config.BOARD_Y + grid_y * config.CELL_SIZE
        rect = pygame.Rect(x + 2, y + 2, config.CELL_SIZE - 4, config.CELL_SIZE - 4)
        shadow = rect.move(2, 2)

        pygame.draw.rect(self.screen, (0, 0, 0), shadow, border_radius=4)
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        highlight = (
            min(255, color[0] + 45),
            min(255, color[1] + 45),
            min(255, color[2] + 45),
        )
        pygame.draw.line(self.screen, highlight, rect.topleft, rect.topright, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1, border_radius=4)

    def _draw_ghost_cell(self, grid_x: int, grid_y: int) -> None:
        x = config.BOARD_X + grid_x * config.CELL_SIZE
        y = config.BOARD_Y + grid_y * config.CELL_SIZE
        rect = pygame.Rect(x + 4, y + 4, config.CELL_SIZE - 8, config.CELL_SIZE - 8)
        pygame.draw.rect(self.screen, config.COLOR_GHOST, rect, 2, border_radius=4)

    def _draw_landing_cell(self, grid_x: int, grid_y: int, progress: float) -> None:
        x = config.BOARD_X + grid_x * config.CELL_SIZE
        y = config.BOARD_Y + grid_y * config.CELL_SIZE
        alpha = int(130 * progress)
        surface = pygame.Surface((config.CELL_SIZE + 10, config.CELL_SIZE + 10), pygame.SRCALPHA)
        pygame.draw.rect(
            surface,
            (*config.COLOR_WARNING, alpha),
            pygame.Rect(0, 0, config.CELL_SIZE + 10, config.CELL_SIZE + 10),
            2,
            border_radius=6,
        )
        self.screen.blit(surface, (x - 5, y - 5))

    def _draw_line_clear_animation(self, rows: list[int], progress: float) -> None:
        pulse = math.sin(progress * math.pi)
        for row in rows:
            y = config.BOARD_Y + row * config.CELL_SIZE
            overlay = pygame.Surface((config.BOARD_WIDTH, config.CELL_SIZE), pygame.SRCALPHA)
            overlay.fill((*config.COLOR_ACCENT, int(70 + 135 * pulse)))
            self.screen.blit(overlay, (config.BOARD_X, y))

            center_width = int(config.BOARD_WIDTH * progress)
            center_rect = pygame.Rect(
                config.BOARD_X + (config.BOARD_WIDTH - center_width) // 2,
                y + 4,
                center_width,
                config.CELL_SIZE - 8,
            )
            pygame.draw.rect(self.screen, config.COLOR_TEXT, center_rect, border_radius=4)

    def _draw_board_grid(self) -> None:
        for x in range(config.GRID_WIDTH + 1):
            start_x = config.BOARD_X + x * config.CELL_SIZE
            pygame.draw.line(
                self.screen,
                (25, 31, 44),
                (start_x, config.BOARD_Y),
                (start_x, config.BOARD_Y + config.BOARD_HEIGHT),
                1,
            )
        for y in range(config.GRID_HEIGHT + 1):
            start_y = config.BOARD_Y + y * config.CELL_SIZE
            pygame.draw.line(
                self.screen,
                (25, 31, 44),
                (config.BOARD_X, start_y),
                (config.BOARD_X + config.BOARD_WIDTH, start_y),
                1,
            )

        outline = pygame.Rect(
            config.BOARD_X,
            config.BOARD_Y,
            config.BOARD_WIDTH,
            config.BOARD_HEIGHT,
        )
        pygame.draw.rect(self.screen, config.COLOR_BORDER, outline, 2)

    def _draw_side_panel(
        self,
        score: ScoreManager,
        next_piece: Piece | None,
        held_piece: Piece | None,
    ) -> None:
        panel = pygame.Rect(
            config.SIDE_PANEL_X,
            config.SIDE_PANEL_Y,
            config.SIDE_PANEL_WIDTH,
            config.SIDE_PANEL_HEIGHT,
        )
        self._draw_shadow(panel, radius=8)
        pygame.draw.rect(self.screen, config.COLOR_SURFACE, panel, border_radius=8)
        pygame.draw.rect(self.screen, config.COLOR_BORDER, panel, 1, border_radius=8)

        y = panel.y + 24
        self._draw_stat("Puntaje", str(score.score), y)
        y += 76
        self._draw_stat("Nivel", str(score.level), y)
        y += 76
        self._draw_stat("Líneas", str(score.lines), y)
        y += 76
        self._draw_stat("Récord", str(score.high_score), y)
        y += 90

        self._draw_mini_piece("Próxima", next_piece, pygame.Rect(panel.x + 24, y, 202, 106))
        y += 128
        self._draw_mini_piece("Hold", held_piece, pygame.Rect(panel.x + 24, y, 202, 106))

    def _draw_stat(self, label: str, value: str, y: int) -> None:
        rect = pygame.Rect(config.SIDE_PANEL_X + 20, y, config.SIDE_PANEL_WIDTH - 40, 58)
        pygame.draw.rect(self.screen, config.COLOR_SURFACE_DARK, rect, border_radius=8)
        pygame.draw.rect(self.screen, (45, 55, 73), rect, 1, border_radius=8)

        label_surface = self.font_small.render(label.upper(), True, config.COLOR_TEXT_MUTED)
        value_surface = self.font_medium.render(value, True, config.COLOR_TEXT)
        self.screen.blit(label_surface, (rect.x + 14, rect.y + 8))
        self.screen.blit(value_surface, (rect.x + 14, rect.y + 25))

    def _draw_mini_piece(self, label: str, piece: Piece | None, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, config.COLOR_SURFACE_DARK, rect, border_radius=8)
        pygame.draw.rect(self.screen, (45, 55, 73), rect, 1, border_radius=8)
        label_surface = self.font_small.render(label.upper(), True, config.COLOR_TEXT_MUTED)
        self.screen.blit(label_surface, (rect.x + 14, rect.y + 10))

        if piece is None:
            empty = self.font_body.render("-", True, config.COLOR_TEXT_MUTED)
            self.screen.blit(empty, empty.get_rect(center=(rect.centerx, rect.centery + 10)))
            return

        cells = SHAPES[piece.shape][0]
        min_x = min(cell[0] for cell in cells)
        max_x = max(cell[0] for cell in cells)
        min_y = min(cell[1] for cell in cells)
        max_y = max(cell[1] for cell in cells)
        cell_size = 20
        piece_width = (max_x - min_x + 1) * cell_size
        piece_height = (max_y - min_y + 1) * cell_size
        start_x = rect.centerx - piece_width // 2
        start_y = rect.y + 58 - piece_height // 2 + 18

        color = config.PIECE_COLORS[piece.shape]
        for cell_x, cell_y in cells:
            block = pygame.Rect(
                start_x + (cell_x - min_x) * cell_size,
                start_y + (cell_y - min_y) * cell_size,
                cell_size - 2,
                cell_size - 2,
            )
            pygame.draw.rect(self.screen, color, block, border_radius=4)
            pygame.draw.rect(self.screen, (255, 255, 255), block, 1, border_radius=4)

    def _draw_falling_preview(self) -> None:
        cells = [
            ("I", 118, 120, 0),
            ("T", 770, 155, 0.7),
            ("S", 130, 520, 1.4),
            ("L", 790, 505, 2.1),
        ]
        ticks = pygame.time.get_ticks() / 1000
        for shape, x, y, phase in cells:
            offset = int((ticks * 28 + phase * 40) % 90)
            color = config.PIECE_COLORS[shape]
            for cell_x, cell_y in SHAPES[shape][0]:
                rect = pygame.Rect(
                    x + cell_x * 18,
                    y + ((offset + cell_y * 18) % 120),
                    16,
                    16,
                )
                pygame.draw.rect(self.screen, color, rect, border_radius=3)

    def _draw_button(
        self,
        text: str,
        rect: pygame.Rect,
        mouse: tuple[int, int],
        primary: bool,
    ) -> None:
        hover = rect.collidepoint(mouse)
        if primary:
            color = config.COLOR_ACCENT_DARK if hover else config.COLOR_ACCENT
            text_color = (4, 13, 18)
        else:
            color = config.COLOR_SURFACE_LIGHT if hover else config.COLOR_SURFACE
            text_color = config.COLOR_TEXT

        self._draw_shadow(rect, radius=8)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1, border_radius=8)

        label = self.font_body.render(text, True, text_color)
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_center_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        y: int,
        shadow: bool = False,
    ) -> None:
        if shadow:
            shadow_surface = font.render(text, True, config.COLOR_SHADOW)
            shadow_rect = shadow_surface.get_rect(center=(config.WINDOW_WIDTH // 2 + 3, y + 4))
            self.screen.blit(shadow_surface, shadow_rect)
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(config.WINDOW_WIDTH // 2, y))
        self.screen.blit(surface, rect)

    def _dim_screen(self, alpha: int) -> None:
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_shadow(self, rect: pygame.Rect, radius: int) -> None:
        shadow_rect = rect.move(5, 7)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (0, 0, 0, 90),
            shadow_surface.get_rect(),
            border_radius=radius,
        )
        self.screen.blit(shadow_surface, shadow_rect.topleft)
