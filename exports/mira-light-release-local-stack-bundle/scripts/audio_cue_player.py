#!/usr/bin/env python3
"""Small audio cue helper for release booth scenes.

This helper intentionally keeps the integration simple:

- resolve an asset from `assets/audio`
- tolerate the legacy `dance.mp3` cue name by falling back to `dance.wav`
- prefer local OS players instead of adding a Python audio dependency
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any


DEFAULT_AUDIO_ROOT = Path(__file__).resolve().parent.parent / "assets" / "audio"
FALLBACK_SUFFIXES = (".wav", ".mp3", ".m4a", ".aac", ".aiff")
PLAYER_SPECS = (
    ("afplay", ["afplay"]),
    ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error"]),
    ("mpg123", ["mpg123", "-q"]),
    ("paplay", ["paplay"]),
    ("aplay", ["aplay", "-q"]),
)


class AudioCuePlayer:
    """Resolve and play release audio cues without extra Python dependencies."""

    def __init__(
        self,
        cue_root: Path | str = DEFAULT_AUDIO_ROOT,
        *,
        dry_run: bool = False,
        player_command: str | None = None,
    ) -> None:
        self.cue_root = Path(cue_root)
        self.dry_run = dry_run
        self.player_command = (player_command or os.environ.get("MIRA_LIGHT_AUDIO_PLAYER") or "").strip()

    def resolve_asset(self, cue_name: str) -> Path | None:
        candidate = Path(cue_name)
        direct_candidates: list[Path] = []

        if candidate.is_absolute():
            direct_candidates.append(candidate)
        else:
            direct_candidates.append(self.cue_root / candidate)

        for item in direct_candidates:
            if item.exists():
                return item.resolve()

        stem = candidate.stem if candidate.suffix else candidate.name
        relative_parent = candidate.parent if str(candidate.parent) != "." else Path()
        for suffix in FALLBACK_SUFFIXES:
            alt = self.cue_root / relative_parent / f"{stem}{suffix}"
            if alt.exists():
                return alt.resolve()

        return None

    def detect_player(self) -> list[str] | None:
        if self.player_command:
            argv = shlex.split(self.player_command)
            if not argv:
                return None
            executable = argv[0]
            if os.path.isabs(executable) or shutil.which(executable):
                return argv
            return None

        for executable, argv in PLAYER_SPECS:
            if shutil.which(executable):
                return list(argv)
        return None

    def play(self, cue_name: str, *, blocking: bool = False) -> dict[str, Any]:
        resolved = self.resolve_asset(cue_name)
        result: dict[str, Any] = {
            "ok": False,
            "cue": cue_name,
            "dryRun": self.dry_run,
            "blocking": blocking,
            "cueRoot": str(self.cue_root),
            "resolvedAsset": str(resolved) if resolved else None,
        }

        if resolved is None:
            result["reason"] = "asset_not_found"
            return result

        if self.dry_run:
            result["ok"] = True
            result["reason"] = "dry_run"
            return result

        player_argv = self.detect_player()
        if not player_argv:
            result["reason"] = "player_not_found"
            return result

        argv = [*player_argv, str(resolved)]
        result["player"] = player_argv[0]

        try:
            if blocking:
                completed = subprocess.run(
                    argv,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                result["ok"] = completed.returncode == 0
                result["exitCode"] = completed.returncode
                if not result["ok"]:
                    result["reason"] = "player_failed"
                return result

            proc = subprocess.Popen(
                argv,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            result["ok"] = True
            result["pid"] = proc.pid
            result["reason"] = "spawned"
            return result
        except OSError as exc:
            result["reason"] = "spawn_failed"
            result["error"] = str(exc)
            return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Play a local Mira Light release audio cue.")
    parser.add_argument("cue", help="Cue name such as dance.mp3 or a direct asset path.")
    parser.add_argument("--cue-root", default=str(DEFAULT_AUDIO_ROOT), help="Root directory that stores cue assets.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve the cue without actually playing it.")
    parser.add_argument("--blocking", action="store_true", help="Wait for playback to finish before exiting.")
    args = parser.parse_args()

    player = AudioCuePlayer(
        cue_root=args.cue_root,
        dry_run=args.dry_run,
    )
    result = player.play(args.cue, blocking=args.blocking)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
