"""Tetromino definitions and rotation data."""

from __future__ import annotations

from dataclasses import dataclass

from . import config


# Rotation states use a 4x4 bounding box and coordinates with y growing down.
SHAPES = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
}

DEFAULT_KICKS = (
    (0, 0),
    (-1, 0),
    (1, 0),
    (0, -1),
    (-2, 0),
    (2, 0),
)

# SRS wall kicks converted to the screen coordinate system.
JLSTZ_KICKS = {
    (0, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (1, 0): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (1, 2): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (2, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (2, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (3, 2): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (3, 0): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (0, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
}

I_KICKS = {
    (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (1, 0): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    (2, 1): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (2, 3): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (3, 0): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
}


@dataclass(slots=True)
class Piece:
    """A playable tetromino with position and rotation state."""

    shape: str
    x: int = config.SPAWN_X
    y: int = config.SPAWN_Y
    rotation: int = 0

    def cells(
        self,
        x: int | None = None,
        y: int | None = None,
        rotation: int | None = None,
    ) -> list[tuple[int, int]]:
        """Return absolute board cells occupied by the piece."""
        piece_x = self.x if x is None else x
        piece_y = self.y if y is None else y
        piece_rotation = self.rotation if rotation is None else rotation % 4
        return [
            (piece_x + cell_x, piece_y + cell_y)
            for cell_x, cell_y in SHAPES[self.shape][piece_rotation]
        ]

    def reset_position(self) -> None:
        """Move the piece to the spawn area with the default rotation."""
        self.x = config.SPAWN_X
        self.y = config.SPAWN_Y
        self.rotation = 0

    def copy_for_preview(self) -> "Piece":
        """Return an unpositioned copy suitable for UI previews."""
        return Piece(self.shape, rotation=0)

    def next_rotation(self, clockwise: bool = True) -> int:
        """Return the next rotation index."""
        return (self.rotation + (1 if clockwise else -1)) % 4

    def wall_kicks(self, target_rotation: int) -> tuple[tuple[int, int], ...]:
        """Return SRS wall kick offsets for a rotation attempt."""
        if self.shape == "O":
            return ((0, 0),)

        key = (self.rotation, target_rotation % 4)
        if self.shape == "I":
            return I_KICKS.get(key, DEFAULT_KICKS)
        return JLSTZ_KICKS.get(key, DEFAULT_KICKS)

