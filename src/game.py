"""Main game loop and orchestration."""

from __future__ import annotations

import array
import math
import random
from enum import Enum, auto

import pygame

from . import config
from .board import Board
from .piece import Piece
from .score import ScoreManager
from .ui import UI


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class AudioManager:
    """Loads replaceable audio assets and provides generated fallbacks."""

    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_channel: pygame.mixer.Channel | None = None
        self.sample_rate = 44_100
        self._initialize()

    def _initialize(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            self.enabled = pygame.mixer.get_init() is not None
        except pygame.error:
            self.enabled = False

        if not self.enabled:
            return

        fallbacks = {
            "move": ((260, 0.035, 0.28),),
            "rotate": ((460, 0.045, 0.30),),
            "drop": ((150, 0.075, 0.35),),
            "clear": ((620, 0.06, 0.30), (820, 0.08, 0.32), (1040, 0.10, 0.30)),
            "hold": ((540, 0.06, 0.26),),
            "game_over": ((520, 0.12, 0.30), (360, 0.15, 0.28), (190, 0.22, 0.28)),
            "menu": ((720, 0.05, 0.24),),
            "music_loop": (
                (220, 0.22, 0.10),
                (0, 0.05, 0.0),
                (277, 0.22, 0.10),
                (0, 0.05, 0.0),
                (330, 0.22, 0.10),
                (0, 0.05, 0.0),
                (277, 0.22, 0.08),
                (0, 0.50, 0.0),
            ),
        }

        for name, path in config.SOUND_FILES.items():
            self.sounds[name] = self._load_sound(path, fallbacks[name])
        self.sounds["music_loop"] = self._make_sound(fallbacks["music_loop"])

    def _load_sound(self, path, notes) -> pygame.mixer.Sound:
        if path.exists():
            try:
                return pygame.mixer.Sound(str(path))
            except pygame.error:
                pass
        return self._make_sound(notes)

    def _make_sound(self, notes: tuple[tuple[float, float, float], ...]) -> pygame.mixer.Sound:
        samples = array.array("h")
        for frequency, duration, volume in notes:
            frames = max(1, int(self.sample_rate * duration))
            for frame in range(frames):
                if frequency <= 0:
                    value = 0
                else:
                    envelope = min(1.0, frame / (self.sample_rate * 0.01))
                    envelope = min(envelope, (frames - frame) / (self.sample_rate * 0.02))
                    wave = math.sin((2 * math.pi * frequency * frame) / self.sample_rate)
                    value = int(32767 * volume * envelope * wave)
                samples.append(value)
                samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_music(self) -> None:
        if not self.enabled:
            return

        if config.BACKGROUND_MUSIC.exists():
            try:
                pygame.mixer.music.load(str(config.BACKGROUND_MUSIC))
                pygame.mixer.music.set_volume(0.34)
                pygame.mixer.music.play(-1)
                return
            except pygame.error:
                pass

        if self.music_channel is None or not self.music_channel.get_busy():
            self.music_channel = self.sounds["music_loop"].play(-1)
            if self.music_channel:
                self.music_channel.set_volume(0.30)

    def stop_music(self) -> None:
        if not self.enabled:
            return
        pygame.mixer.music.stop()
        if self.music_channel:
            self.music_channel.stop()


class Game:
    """Coordinates state, input, updates, and rendering."""

    def __init__(self) -> None:
        pygame.mixer.pre_init(44_100, -16, 2, 512)
        pygame.init()
        pygame.key.set_repeat(config.MOVE_REPEAT_DELAY_MS, config.MOVE_REPEAT_INTERVAL_MS)

        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption(config.WINDOW_TITLE)
        pygame.display.set_icon(self._load_icon())

        self.clock = pygame.time.Clock()
        self.board = Board()
        self.score = ScoreManager()
        self.ui = UI(self.screen)
        self.audio = AudioManager()

        self.state = GameState.MENU
        self.running = True
        self.show_fps = config.SHOW_FPS
        self.bag: list[str] = []
        self.current_piece: Piece | None = None
        self.next_piece: Piece | None = None
        self.held_piece: Piece | None = None
        self.can_hold = True
        self.fall_elapsed_ms = 0.0
        self.lock_started_at: int | None = None
        self.lock_resets = 0
        self.landing_flash_until = 0
        self.clearing_rows: list[int] = []
        self.clear_started_at = 0

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(config.FPS)
            self._handle_events()
            self._update(dt_ms)
            self._draw()
            pygame.display.flip()

        self.score.save_high_score()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event)

    def _handle_mouse(self, position: tuple[int, int]) -> None:
        if self.state == GameState.MENU:
            if self.ui.menu_buttons["play"].collidepoint(position):
                self.audio.play("menu")
                self.start_new_game()
            elif self.ui.menu_buttons["quit"].collidepoint(position):
                self._quit()
        elif self.state == GameState.PAUSED:
            if self.ui.pause_buttons["resume"].collidepoint(position):
                self.audio.play("menu")
                self.state = GameState.PLAYING
            elif self.ui.pause_buttons["restart"].collidepoint(position):
                self.audio.play("menu")
                self.start_new_game()
            elif self.ui.pause_buttons["quit"].collidepoint(position):
                self._quit()
        elif self.state == GameState.GAME_OVER:
            if self.ui.game_over_buttons["restart"].collidepoint(position):
                self.audio.play("menu")
                self.start_new_game()
            elif self.ui.game_over_buttons["menu"].collidepoint(position):
                self.audio.play("menu")
                self.state = GameState.MENU
                self.audio.stop_music()
            elif self.ui.game_over_buttons["quit"].collidepoint(position):
                self._quit()

    def _handle_key(self, event: pygame.event.Event) -> None:
        repeated = bool(getattr(event, "repeat", 0))

        if event.key == pygame.K_ESCAPE:
            self._quit()
            return
        if event.key == pygame.K_f and not repeated:
            self.show_fps = not self.show_fps
            return

        if self.state == GameState.MENU:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and not repeated:
                self.start_new_game()
            return

        if self.state == GameState.PAUSED:
            if event.key == pygame.K_p and not repeated:
                self.state = GameState.PLAYING
            elif event.key == pygame.K_r and not repeated:
                self.start_new_game()
            return

        if self.state == GameState.GAME_OVER:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and not repeated:
                self.start_new_game()
            return

        if self.state != GameState.PLAYING:
            return

        non_repeat_keys = {
            pygame.K_UP,
            pygame.K_SPACE,
            pygame.K_LSHIFT,
            pygame.K_RSHIFT,
            pygame.K_p,
        }
        if repeated and event.key in non_repeat_keys:
            return

        if event.key == pygame.K_LEFT:
            self._move_piece(dx=-1)
        elif event.key == pygame.K_RIGHT:
            self._move_piece(dx=1)
        elif event.key == pygame.K_DOWN:
            self._soft_drop()
        elif event.key == pygame.K_UP:
            self._rotate_piece()
        elif event.key == pygame.K_SPACE:
            self._hard_drop()
        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            self._hold_piece()
        elif event.key == pygame.K_p:
            self.state = GameState.PAUSED

    def _update(self, dt_ms: int) -> None:
        if self.state != GameState.PLAYING:
            return

        if self.clearing_rows:
            if pygame.time.get_ticks() - self.clear_started_at >= config.LINE_CLEAR_DURATION_MS:
                self._finish_line_clear()
            return

        if self.current_piece is None:
            return

        self.fall_elapsed_ms += dt_ms
        if self.fall_elapsed_ms >= self.score.fall_interval():
            self.fall_elapsed_ms = 0
            if not self._move_piece(dy=1, play_sound=False):
                self._start_or_finish_lock()

        self._refresh_ground_state()
        if (
            self.current_piece is not None
            and self.lock_started_at is not None
            and pygame.time.get_ticks() - self.lock_started_at >= config.LOCK_DELAY_MS
        ):
            self._lock_current_piece()

    def _draw(self) -> None:
        if self.state == GameState.MENU:
            self.ui.draw_menu(self.score.high_score)
            return

        ghost_y = None
        if self.current_piece is not None:
            ghost_y = self.board.ghost_y(self.current_piece)

        clear_progress = 0.0
        if self.clearing_rows:
            elapsed = pygame.time.get_ticks() - self.clear_started_at
            clear_progress = min(1.0, elapsed / config.LINE_CLEAR_DURATION_MS)

        landing_progress = 0.0
        if pygame.time.get_ticks() < self.landing_flash_until:
            remaining = self.landing_flash_until - pygame.time.get_ticks()
            landing_progress = remaining / config.LANDING_FLASH_MS

        self.ui.draw_game(
            self.board,
            self.current_piece,
            self.next_piece,
            self.held_piece,
            self.score,
            ghost_y,
            self.clearing_rows,
            clear_progress,
            landing_progress,
            self.show_fps,
            self.clock.get_fps(),
        )

        if self.state == GameState.PAUSED:
            self.ui.draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self.ui.draw_game_over_overlay(self.score)

    def start_new_game(self) -> None:
        self.board.reset()
        self.score.reset()
        self.bag.clear()
        self.held_piece = None
        self.current_piece = Piece(self._draw_shape())
        self.next_piece = Piece(self._draw_shape())
        self.can_hold = True
        self.fall_elapsed_ms = 0
        self.lock_started_at = None
        self.lock_resets = 0
        self.landing_flash_until = 0
        self.clearing_rows = []
        self.clear_started_at = 0
        self.state = GameState.PLAYING
        self.audio.start_music()

        if not self.board.is_valid_position(self.current_piece):
            self._game_over()

    def _draw_shape(self) -> str:
        if not self.bag:
            self.bag = list(config.TETROMINO_ORDER)
            random.shuffle(self.bag)
        return self.bag.pop()

    def _spawn_next_piece(self) -> None:
        self.current_piece = self.next_piece
        self.current_piece.reset_position()
        self.next_piece = Piece(self._draw_shape())
        self.can_hold = True
        self.fall_elapsed_ms = 0
        self.lock_started_at = None
        self.lock_resets = 0

        if not self.board.is_valid_position(self.current_piece):
            self._game_over()

    def _move_piece(self, dx: int = 0, dy: int = 0, play_sound: bool = True) -> bool:
        if self.current_piece is None or self.clearing_rows:
            return False

        new_x = self.current_piece.x + dx
        new_y = self.current_piece.y + dy
        if self.board.is_valid_position(self.current_piece, x=new_x, y=new_y):
            self.current_piece.x = new_x
            self.current_piece.y = new_y
            if play_sound and dx:
                self.audio.play("move")
            if dx:
                self._reset_lock_delay()
            self._refresh_ground_state()
            return True
        return False

    def _soft_drop(self) -> None:
        if self._move_piece(dy=1, play_sound=False):
            self.score.add_soft_drop(1)
        else:
            self._start_or_finish_lock()

    def _hard_drop(self) -> None:
        if self.current_piece is None or self.clearing_rows:
            return

        target_y = self.board.ghost_y(self.current_piece)
        distance = target_y - self.current_piece.y
        self.current_piece.y = target_y
        self.score.add_hard_drop(distance)
        self.audio.play("drop")
        self._lock_current_piece()

    def _rotate_piece(self) -> None:
        if self.current_piece is None or self.clearing_rows:
            return

        target_rotation = self.current_piece.next_rotation()
        for offset_x, offset_y in self.current_piece.wall_kicks(target_rotation):
            new_x = self.current_piece.x + offset_x
            new_y = self.current_piece.y + offset_y
            if self.board.is_valid_position(
                self.current_piece,
                x=new_x,
                y=new_y,
                rotation=target_rotation,
            ):
                self.current_piece.x = new_x
                self.current_piece.y = new_y
                self.current_piece.rotation = target_rotation
                self.audio.play("rotate")
                self._reset_lock_delay()
                self._refresh_ground_state()
                return

    def _hold_piece(self) -> None:
        if self.current_piece is None or not self.can_hold or self.clearing_rows:
            return

        self.audio.play("hold")
        current_shape = self.current_piece.shape
        if self.held_piece is None:
            self.held_piece = Piece(current_shape)
            self._spawn_next_piece()
        else:
            self.current_piece = Piece(self.held_piece.shape)
            self.held_piece = Piece(current_shape)
            if not self.board.is_valid_position(self.current_piece):
                self._game_over()

        self.can_hold = False
        self.lock_started_at = None
        self.lock_resets = 0

    def _refresh_ground_state(self) -> None:
        if self.current_piece is None:
            self.lock_started_at = None
            return

        grounded = not self.board.is_valid_position(
            self.current_piece,
            y=self.current_piece.y + 1,
        )
        if grounded and self.lock_started_at is None:
            self.lock_started_at = pygame.time.get_ticks()
            self.landing_flash_until = self.lock_started_at + config.LANDING_FLASH_MS
        elif not grounded:
            self.lock_started_at = None
            self.lock_resets = 0

    def _reset_lock_delay(self) -> None:
        if self.current_piece is None:
            return

        grounded = not self.board.is_valid_position(
            self.current_piece,
            y=self.current_piece.y + 1,
        )
        if grounded and self.lock_resets < config.MAX_LOCK_RESETS:
            self.lock_started_at = pygame.time.get_ticks()
            self.lock_resets += 1

    def _start_or_finish_lock(self) -> None:
        if self.current_piece is None:
            return

        now = pygame.time.get_ticks()
        if self.lock_started_at is None:
            self.lock_started_at = now
            self.landing_flash_until = now + config.LANDING_FLASH_MS
            return

        if now - self.lock_started_at >= config.LOCK_DELAY_MS:
            self._lock_current_piece()

    def _lock_current_piece(self) -> None:
        if self.current_piece is None:
            return

        locked_above_top = self.board.lock_piece(self.current_piece)
        self.current_piece = None
        self.lock_started_at = None
        self.lock_resets = 0

        if locked_above_top:
            self._game_over()
            return

        lines = self.board.full_lines()
        if lines:
            self.clearing_rows = lines
            self.clear_started_at = pygame.time.get_ticks()
            self.audio.play("clear")
        else:
            self._spawn_next_piece()

    def _finish_line_clear(self) -> None:
        cleared = self.board.clear_lines(self.clearing_rows)
        self.score.add_lines(cleared)
        self.clearing_rows = []
        self.clear_started_at = 0
        self._spawn_next_piece()

    def _game_over(self) -> None:
        self.state = GameState.GAME_OVER
        self.score.save_high_score()
        self.audio.play("game_over")
        self.audio.stop_music()

    def _quit(self) -> None:
        self.running = False

    def _load_icon(self) -> pygame.Surface:
        if config.ICON_PATH.exists():
            try:
                return pygame.image.load(str(config.ICON_PATH)).convert_alpha()
            except pygame.error:
                pass

        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(icon, config.COLOR_SURFACE, icon.get_rect(), border_radius=10)
        blocks = [
            (0, 0, config.PIECE_COLORS["T"]),
            (1, 0, config.PIECE_COLORS["T"]),
            (2, 0, config.PIECE_COLORS["T"]),
            (1, 1, config.PIECE_COLORS["T"]),
            (1, 2, config.PIECE_COLORS["I"]),
            (1, 3, config.PIECE_COLORS["I"]),
        ]
        for grid_x, grid_y, color in blocks:
            rect = pygame.Rect(10 + grid_x * 14, 5 + grid_y * 14, 12, 12)
            pygame.draw.rect(icon, color, rect, border_radius=3)
        return icon
