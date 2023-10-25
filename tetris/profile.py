"""저장 데이터와 환경 설정 관리."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def default_bindings() -> Dict[str, int]:
    import pygame

    return {
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "rotate": pygame.K_UP,
        "down": pygame.K_DOWN,
        "hard_drop": pygame.K_SPACE,
        "hold": pygame.K_c,
        "pause": pygame.K_p,
        "restart": pygame.K_r,
        "mute": pygame.K_m,
    }


def default_settings() -> Dict[str, Any]:
    return {
        "theme": "classic",
        "mode": "marathon",
        "start_level": 1,
        "bgm_mode": "random",
        "bgm_track": "",
        "sound_enabled": True,
        "bindings": default_bindings(),
    }


def default_stats() -> Dict[str, Any]:
    return {
        "games_played": 0,
        "total_score": 0,
        "total_lines": 0,
        "total_time_ms": 0,
        "tetrises": 0,
        "t_spins": 0,
        "best_score": 0,
        "best_marathon_score": 0,
        "best_sprint_time_ms": 0,
        "best_time_attack_score": 0,
    }


def default_highscores() -> Dict[str, List[Dict[str, Any]]]:
    return {"marathon": [], "sprint": [], "time_attack": []}


def default_achievements() -> List[str]:
    return []


def default_data() -> Dict[str, Any]:
    return {
        "settings": default_settings(),
        "stats": default_stats(),
        "highscores": default_highscores(),
        "achievements": default_achievements(),
    }


@dataclass
class ProfileStore:
    path: Path
    data: Dict[str, Any] = field(default_factory=default_data)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "ProfileStore":
        path = path or cls.default_path()
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            merged = default_data()
            if isinstance(data.get("settings"), dict):
                merged["settings"].update(data["settings"])
            if isinstance(data.get("stats"), dict):
                merged["stats"].update(data["stats"])
            if isinstance(data.get("highscores"), dict):
                merged["highscores"].update(data["highscores"])
            if isinstance(data.get("achievements"), list):
                merged["achievements"] = list(data["achievements"])
            return cls(path=path, data=merged)
        return cls(path=path)

    @staticmethod
    def default_path() -> Path:
        return Path.home() / ".tetris_project" / "profile.json"

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @property
    def settings(self) -> Dict[str, Any]:
        return self.data["settings"]

    @property
    def stats(self) -> Dict[str, Any]:
        return self.data["stats"]

    @property
    def highscores(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.data["highscores"]

    @property
    def achievements(self) -> List[str]:
        return self.data["achievements"]

    def record_run(self, mode: str, score: int, lines: int, elapsed_ms: int, extras: Optional[Dict[str, Any]] = None) -> None:
        extras = extras or {}
        stats = self.stats
        stats["games_played"] += 1
        stats["total_score"] += score
        stats["total_lines"] += lines
        stats["total_time_ms"] += elapsed_ms
        stats["best_score"] = max(stats["best_score"], score)
        if mode == "marathon":
            stats["best_marathon_score"] = max(stats["best_marathon_score"], score)
        elif mode == "sprint":
            best = stats["best_sprint_time_ms"]
            stats["best_sprint_time_ms"] = elapsed_ms if best == 0 else min(best, elapsed_ms)
        elif mode == "time_attack":
            stats["best_time_attack_score"] = max(stats["best_time_attack_score"], score)
        stats["tetrises"] += extras.get("tetrises", 0)
        stats["t_spins"] += extras.get("t_spins", 0)

        self._append_highscore(mode, score, lines, elapsed_ms)
        self._unlock_achievements(score, lines, extras)

    def _append_highscore(self, mode: str, score: int, lines: int, elapsed_ms: int) -> None:
        bucket = self.highscores.setdefault(mode, [])
        bucket.append({"score": score, "lines": lines, "elapsed_ms": elapsed_ms})
        if mode == "sprint":
            bucket.sort(key=lambda item: (int(item.get("elapsed_ms", 0)), -int(item.get("score", 0))))
        else:
            bucket.sort(key=lambda item: (-int(item.get("score", 0)), int(item.get("elapsed_ms", 0))))
        del bucket[10:]

    def _unlock_achievements(self, score: int, lines: int, extras: Dict[str, Any]) -> None:
        achievements = set(self.achievements)
        if lines >= 1:
            achievements.add("FIRST LINE")
        if extras.get("tetrises", 0) > 0:
            achievements.add("FIRST TETRIS")
        if extras.get("t_spins", 0) > 0:
            achievements.add("FIRST T-SPIN")
        if self.stats["games_played"] >= 10:
            achievements.add("TEN RUNS")
        if self.stats["total_lines"] >= 100:
            achievements.add("100 LINES")
        if score >= 10000:
            achievements.add("10K SCORE")
        self.data["achievements"] = sorted(achievements)

    def cycle_theme(self, direction: int) -> str:
        from .themes import THEME_LIST

        current = self.settings.get("theme", "classic")
        slugs = [theme.slug for theme in THEME_LIST]
        index = slugs.index(current) if current in slugs else 0
        index = (index + direction) % len(slugs)
        self.settings["theme"] = slugs[index]
        return slugs[index]

    def cycle_bgm_mode(self, direction: int, tracks: List[str]) -> str:
        modes = ["random", "off"] + tracks
        current = self.settings.get("bgm_track", "") if self.settings.get("bgm_mode") == "selected" else self.settings.get("bgm_mode", "random")
        index = modes.index(current) if current in modes else 0
        index = (index + direction) % len(modes)
        choice = modes[index]
        if choice in ("random", "off"):
            self.settings["bgm_mode"] = choice
            self.settings["bgm_track"] = ""
        else:
            self.settings["bgm_mode"] = "selected"
            self.settings["bgm_track"] = choice
        return choice
