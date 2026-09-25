"""Decode visual evidence from the draft MP4 for the independent reviewer.

Writes two contact sheets (one frame every 5 s, and one every 2 s over the
first 60 s) plus first/last single frames under $ARTIFACTS_DIR/qa/. Evidence
is produced by code so the reviewer judges real pixels, never lint text.
Prints `sheets` (JSON array of paths) and `frames`.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def duration_of(mp4: Path, cwd: Path) -> float:
    completed = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(mp4)], cwd)
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {completed.stderr.strip()}")
    return float(json.loads(completed.stdout)["format"]["duration"])


def sheet(mp4: Path, out: Path, every: float, span: float | None, cols: int, cwd: Path) -> Path:
    total = span if span is not None else duration_of(mp4, cwd)
    frames = max(1, math.ceil(total / every))
    rows = max(1, math.ceil(frames / cols))
    vf = f"fps=1/{every},scale=480:-1,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}"
    command = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(mp4)]
    if span is not None:
        command += ["-t", str(span)]
    command += ["-vf", vf, "-frames:v", "1", "-q:v", "3", str(out)]
    completed = run(command, cwd)
    if completed.returncode != 0 or not out.is_file() or out.stat().st_size == 0:
        # drawtext needs a font; retry without the timestamp burn-in rather than fail the round
        vf_plain = vf.replace(vf[vf.index(",drawtext"):vf.index(",tile")], "")
        command[command.index("-vf") + 1] = vf_plain
        completed = run(command, cwd)
        if completed.returncode != 0 or not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError(f"contact sheet failed: {completed.stderr.strip()[-400:]}")
    return out


def frame(mp4: Path, out: Path, t: float, cwd: Path) -> Path:
    completed = run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4), "-frames:v", "1", "-q:v", "2", str(out)], cwd)
    if completed.returncode != 0 or not out.is_file():
        raise RuntimeError(f"frame extract at {t}s failed: {completed.stderr.strip()[-300:]}")
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        repo_root = Path.cwd().resolve()
        slug = os.environ["INPUTS_SLUG"]
        mp4 = (repo_root / os.environ["INPUTS_RENDER_PATH"]).resolve()
        if not mp4.is_file():
            raise FileNotFoundError(f"render not found: {mp4}")
        qa = Path(os.environ["ARTIFACTS_DIR"]).resolve() / "qa"
        qa.mkdir(parents=True, exist_ok=True)
        # Clear evidence from a previous iteration so the reviewer never grades stale pixels.
        for old in qa.glob("*"):
            old.unlink()
        total = duration_of(mp4, repo_root)
        sheets = [
            sheet(mp4, qa / f"contact-sheet-{slug}-full.jpg", 5.0, None, 6, repo_root),
            sheet(mp4, qa / f"contact-sheet-{slug}-hook.jpg", 2.0, min(60.0, total), 6, repo_root),
        ]
        frames = [
            frame(mp4, qa / "frame-first.jpg", 0.0, repo_root),
            frame(mp4, qa / "frame-last.jpg", max(0.0, total - 0.1), repo_root),
        ]
        rel = lambda p: p.as_posix()
        print(json.dumps({"sheets": [rel(p) for p in sheets], "frames": [rel(p) for p in frames], "duration": total}))
        return 0
    except Exception as exc:
        print(json.dumps({"operational_error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
