"""Generate paid Thomas narration exactly once, then hash-lock it.

Money is spent by code, not by an AI node's judgment. Behaviour:
- narration.wav missing            -> run the repository TTS script once, lock.
- narration.wav present + receipt  -> verify hash equals receipt, pass through.
- narration.wav present, no receipt-> requires INPUTS_ACCEPT_EXISTING=true;
                                      adopts the file and writes the receipt.
Lock receipt: $ARTIFACTS_DIR/narration-lock.json. Prints `narration_sha256`.
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        repo_root = Path.cwd().resolve()
        slug = os.environ["INPUTS_SLUG"]
        fmt = os.environ.get("INPUTS_FORMAT", "long-form").strip()
        accept = os.environ.get("INPUTS_ACCEPT_EXISTING", "false").strip().lower() == "true"
        artifacts = Path(os.environ["ARTIFACTS_DIR"]).resolve()
        if fmt not in {"long-form", "shorts"}:
            raise ValueError(f"format must be long-form or shorts, got {fmt!r}")
        video_dir = video_dir_for(repo_root, slug)
        narration = video_dir / "audio" / "narration.wav"
        transcript = video_dir / "transcript.json"
        receipt_path = artifacts / "narration-lock.json"

        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            expected = str(receipt["narration_sha256"]).lower()
            if not narration.is_file():
                raise RuntimeError(f"lock receipt exists but narration is missing: {narration}")
            actual = sha256(narration)
            if actual != expected:
                raise RuntimeError(f"locked narration changed: receipt {expected}, file {actual}")
            origin = "verified against existing lock receipt"
        elif narration.is_file():
            if not accept:
                raise RuntimeError(
                    f"{narration} already exists and no lock receipt is recorded. "
                    "Rerun with --input accept_existing=true to adopt it, or remove it to regenerate."
                )
            origin = "adopted existing narration (accept_existing=true)"
        else:
            command = [*python_launcher(), "scripts/elevenlabs-tts.py", f"videos/{slug}"]
            if fmt == "shorts":
                command.append("--shorts")
            completed = subprocess.run(
                command, cwd=repo_root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", check=False,
            )
            (artifacts / "tts.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
            if completed.returncode != 0 or not narration.is_file():
                tail = (completed.stdout + completed.stderr).strip().splitlines()[-8:]
                raise RuntimeError(f"TTS failed (exit {completed.returncode}): {' | '.join(tail)}")
            origin = "generated this run"

        if not transcript.is_file() or not transcript.read_text(encoding="utf-8").strip():
            raise RuntimeError(f"transcript.json missing or empty next to narration: {transcript}")

        digest = sha256(narration)
        artifacts.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(
                {
                    "narration_sha256": digest,
                    "narration_path": narration.relative_to(repo_root).as_posix(),
                    "transcript_path": transcript.relative_to(repo_root).as_posix(),
                    "origin": origin,
                    "format": fmt,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"narration_sha256": digest, "origin": origin, "summary": f"Narration locked ({origin})."}))
        return 0
    except Exception as exc:
        print(json.dumps({"operational_error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
