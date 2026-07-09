"""Score, level, line count, and high score persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass

from . import config


@dataclass
class ScoreManager:
    score: int = 0
    lines: int = 0
    level: int = 1
    high_score: int = 0

    LINE_POINTS = {
        1: 100,
        2: 300,
        3: 500,
        4: 800,
    }

    def __post_init__(self) -> None:
        self.high_score = self.load_high_score()

    def reset(self) -> None:
        self.score = 0
        self.lines = 0
        self.level = 1

    def add_lines(self, cleared: int) -> None:
        if cleared <= 0:
            return
        self.lines += cleared
        self.level = self.lines // config.LINES_PER_LEVEL + 1
        self.score += self.LINE_POINTS.get(cleared, 0) * self.level
        self._update_high_score()

    def add_soft_drop(self, cells: int = 1) -> None:
        self.score += max(0, cells)
        self._update_high_score()

    def add_hard_drop(self, cells: int) -> None:
        self.score += max(0, cells) * 2
        self._update_high_score()

    def fall_interval(self) -> int:
        speed = config.BASE_FALL_INTERVAL_MS - (
            (self.level - 1) * config.FALL_INTERVAL_STEP_MS
        )
        return max(config.MIN_FALL_INTERVAL_MS, speed)

    def load_high_score(self) -> int:
        try:
            with config.SCORE_FILE.open("r", encoding="utf-8") as score_file:
                data = json.load(score_file)
            return int(data.get("high_score", 0))
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
            return 0

    def save_high_score(self) -> None:
        config.SCORE_FILE.write_text(
            json.dumps({"high_score": self.high_score}, indent=2),
            encoding="utf-8",
        )

    def _update_high_score(self) -> None:
        if self.score > self.high_score:
            self.high_score = self.score
