"""합성 사운드 효과 모듈 (numpy + pygame)."""

import math
import random
from typing import Optional, List
from pathlib import Path
import pygame


def _synth(freq: float, duration_ms: int, volume: float = 0.3) -> Optional[pygame.mixer.Sound]:
    """사인파 기반 단음 생성."""
    try:
        import numpy as np
        sr = 44100
        frames = int(sr * duration_ms / 1000)
        t = np.arange(frames) / sr
        fade = 1 - t / t[-1]
        wave = (volume * 32767 * fade * np.sin(2 * math.pi * freq * t)).astype(np.int16)
        stereo = np.column_stack([wave, wave])
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None


class SoundManager:
    """게임 이벤트에 맞는 효과음을 재생."""

    def __init__(self):
        self._sfx: dict[str, Optional[pygame.mixer.Sound]] = {}
        self._enabled = True
        self._bgm_files = self._find_bgm_files()
        self._bgm_mode = "random"
        self._bgm_track = ""
        self._load()

    def _load(self) -> None:
        self._sfx = {
            "move":     _synth(300,  40, 0.15),
            "rotate":   _synth(500,  55, 0.20),
            "drop":     _synth(150,  80, 0.30),
            "clear":    _synth(880, 140, 0.40),
            "gameover": _synth(100, 400, 0.50),
        }

    def _find_bgm_files(self) -> List[Path]:
        root = Path(__file__).resolve().parents[1]
        candidates = [
            "03. A-Type Music (Korobeiniki).mp3",
            "04. B-Type Music.mp3",
            "05. C-Type Music.mp3",
            "01. Title.mp3",
            "bgm.ogg",
            "bgm.mp3",
        ]
        files = []
        for name in candidates:
            path = root / name
            if path.is_file():
                files.append(path)
        return files

    def track_names(self) -> List[str]:
        return [path.name for path in self._bgm_files]

    def set_preferences(self, enabled: bool, bgm_mode: str, bgm_track: str, restart_bgm: bool = True) -> None:
        self._enabled = enabled
        self._bgm_mode = bgm_mode
        self._bgm_track = bgm_track
        if not self._enabled or self._bgm_mode == "off":
            self.stop_bgm()
        else:
            self.play_bgm(restart=restart_bgm)

    def play(self, name: str) -> None:
        if not self._enabled:
            return
        snd = self._sfx.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def play_bgm(self, restart: bool = False) -> None:
        if not self._enabled or not self._bgm_files:
            return
        if restart and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if restart or not pygame.mixer.music.get_busy():
            if self._bgm_mode == "selected" and self._bgm_track:
                matches = [path for path in self._bgm_files if path.name == self._bgm_track]
                path = matches[0] if matches else random.choice(self._bgm_files)
            elif self._bgm_mode == "off":
                return
            else:
                path = random.choice(self._bgm_files)
            try:
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(0.35)
                pygame.mixer.music.play(-1)
            except pygame.error as exc:
                print(f"[BGM] load failed: {exc}")

    def stop_bgm(self) -> None:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def toggle(self) -> bool:
        self._enabled = not self._enabled
        if not self._enabled:
            self.stop_bgm()
        else:
            self.play_bgm(restart=True)
        return self._enabled
