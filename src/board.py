"""Board state, collision checks, and line clearing."""

from __future__ import annotations

from . import config
from .piece import Piece


class Board:
    """A 10x20 Tetris board."""

    def __init__(self) -> None:
        self.width = config.GRID_WIDTH
        self.height = config.GRID_HEIGHT
        self.grid: list[list[str | None]] = []
        self.reset()

    def reset(self) -> None:
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]

    def is_valid_position(
        self,
        piece: Piece,
        x: int | None = None,
        y: int | None = None,
        rotation: int | None = None,
    ) -> bool:
        """Return True if a piece position is inside the board and unoccupied."""
        for cell_x, cell_y in piece.cells(x=x, y=y, rotation=rotation):
            if cell_x < 0 or cell_x >= self.width:
                return False
            if cell_y >= self.height:
                return False
            if cell_y >= 0 and self.grid[cell_y][cell_x] is not None:
                return False
        return True

    def lock_piece(self, piece: Piece) -> bool:
        """
        Merge a piece into the grid.

        Returns True when any block locks above the visible board, which means
        the game is over.
        """
        locked_above_top = False
        for cell_x, cell_y in piece.cells():
            if cell_y < 0:
                locked_above_top = True
                continue
            if 0 <= cell_y < self.height:
                self.grid[cell_y][cell_x] = piece.shape
        return locked_above_top

    def full_lines(self) -> list[int]:
        return [
            row_index
            for row_index, row in enumerate(self.grid)
            if all(cell is not None for cell in row)
        ]

    def clear_lines(self, rows_to_clear: list[int]) -> int:
        if not rows_to_clear:
            return 0

        rows = set(rows_to_clear)
        self.grid = [
            row for row_index, row in enumerate(self.grid) if row_index not in rows
        ]

        for _ in rows_to_clear:
            self.grid.insert(0, [None for _ in range(self.width)])

        return len(rows_to_clear)

    def ghost_y(self, piece: Piece) -> int:
        """Return the y-position where the piece would land on hard drop."""
        ghost_y = piece.y
        while self.is_valid_position(piece, y=ghost_y + 1):
            ghost_y += 1
        return ghost_y

