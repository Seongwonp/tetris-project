"""간단한 리플레이 기록 저장."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReplayRecorder:
    root: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_ms: int = 0

    @classmethod
    def default_root(cls) -> Path:
        return Path.home() / ".tetris_project" / "replays"

    @classmethod
    def create(cls, metadata: Dict[str, Any], root: Optional[Path] = None) -> "ReplayRecorder":
        return cls(root=root or cls.default_root(), metadata=metadata)

    def tick(self, dt: int) -> None:
        self.elapsed_ms += dt

    def record(self, action: str, key: Optional[int] = None) -> None:
        self.events.append({"t": self.elapsed_ms, "action": action, "key": key})

    def save(self, result: Dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": self.metadata,
            "events": self.events,
            "result": result,
        }
        path = self.root / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def recent_summaries(cls, limit: int = 5, root: Optional[Path] = None) -> List[str]:
        root = root or cls.default_root()
        if not root.is_dir():
            return []
        files = sorted(root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        lines: List[str] = []
        for path in files[:limit]:
            try:
                with path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            metadata = payload.get("metadata", {})
            result = payload.get("result", {})
            mode = str(metadata.get("mode", "unknown")).upper()
            score = int(result.get("score", 0))
            lines.append(
                f"{path.stem} | {mode} | {score:,} pts | {int(result.get('lines', 0))} lines | "
                f"{int(result.get('elapsed_ms', 0)) // 1000}s"
            )
        return lines
