"""Deterministic production gates after a draft render. Writes
$ARTIFACTS_DIR/validation-receipt.json and prints a content verdict
(`green`, `failed_gates`). A red verdict is a successful evaluation (exit 0);
exit 1 only when the gates could not run at all.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def video_dir_for(repo_root: Path, slug: str) -> Path:
    if not SLUG_PATTERN.fullmatch(slug or ""):
        raise ValueError("slug must be a non-empty lowercase hyphenated identifier")
    videos_root = (repo_root / "videos").resolve()
    video_dir = (videos_root / slug).resolve()
    video_dir.relative_to(videos_root)
    return video_dir


def python_launcher() -> list[str]:
    if sys.platform == "win32" and shutil.which("py"):
        return ["py", "-3"]
    for name in ("python3", "python"):
        if shutil.which(name):
            return [name]
    raise RuntimeError("no repository Python launcher (py/python3/python) on PATH")


def npx() -> str:
    return "npx.cmd" if sys.platform == "win32" and shutil.which("npx.cmd") else "npx"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def gate_commands(slug: str) -> list[list[str]]:
    py = python_launcher()
    video = f"videos/{slug}"
    return [
        [*py, "scripts/check-ai-disclosure.py", video],
        [*py, "scripts/check-retention-gate.py", video],
        [*py, "scripts/check-workslop.py", video],
        [*py, "scripts/check-scene-sync.py", video],
        [npx(), "hyperframes", "check", video],
        [*py, "scripts/check-static.py", f"out/{slug}.mp4"],
    ]


def evaluate(repo_root: Path, slug: str, expected_hash: str, render_path: str, artifacts: Path) -> dict:
    video_dir = video_dir_for(repo_root, slug)
    expected_hash = expected_hash.strip().lower()
    failed: list[str] = []
    narration = video_dir / "audio" / "narration.wav"
    actual_hash = hashlib.sha256(narration.read_bytes()).hexdigest() if narration.is_file() else None
    if actual_hash != expected_hash:
        failed.append("narration_sha256")

    canonical = (repo_root / "out" / f"{slug}.mp4").resolve()
    supplied = Path(render_path)
    supplied = (supplied if supplied.is_absolute() else repo_root / supplied).resolve()
    if supplied != canonical:
        failed.append("render_path_not_canonical")
    elif not canonical.is_file() or canonical.stat().st_size == 0:
        failed.append("draft_mp4_missing")

    gates = []
    details: list[str] = []
    for command in gate_commands(slug):
        completed = run(command, repo_root)
        tail = (completed.stdout + completed.stderr).strip().splitlines()[-12:]
        gates.append({"command": command, "returncode": completed.returncode, "tail": tail})
        if completed.returncode != 0:
            failed.append(" ".join(command[-3:]))
            # The next produce-video pass sees only this output, not the receipt
            # file: carry the gate's own findings (e.g. static timestamps) forward.
            details.append(f"{command[-2]}: " + " | ".join(line.strip() for line in tail[:8] if line.strip()))

    green = not failed
    result = {
        "green": green,
        "narration_sha256": expected_hash,
        "receipt_path": (artifacts / "validation-receipt.json").as_posix(),
        "failed_gates": failed,
        "failed_details": details,
        "summary": "Validation green: narration lock and every deterministic gate pass."
        if green
        else f"Validation red: {', '.join(failed)}",
    }
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "validation-receipt.json").write_text(
        json.dumps({**result, "actual_narration_sha256": actual_hash, "gates": gates}, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        result = evaluate(
            Path.cwd().resolve(),
            os.environ["INPUTS_SLUG"],
            os.environ["INPUTS_NARRATION_SHA256"],
            os.environ["INPUTS_RENDER_PATH"],
            Path(os.environ["ARTIFACTS_DIR"]).resolve(),
        )
    except Exception as exc:
        print(json.dumps({"green": False, "operational_error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
