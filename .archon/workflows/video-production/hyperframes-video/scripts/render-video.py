"""Run one governed HyperFrames render synchronously and verify the MP4.

Uses the repository orchestrator (`scripts/build.py render`) so its own gates
(retention artifact, AI disclosure, lint, post-render static check) apply. The
canonical output of build.py is <repo>/out/<slug>.mp4. Verifies: narration hash
unchanged before and after, MP4 refreshed, ffprobe shows video+audio, full
decode succeeds. Prints `complete`, `narration_sha256`, `render_path`.
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


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(path: Path):
    if not path.is_file():
        return None
    st = path.stat()
    return st.st_size, st.st_mtime_ns


def probe_ok(completed: subprocess.CompletedProcess) -> bool:
    if completed.returncode != 0:
        return False
    try:
        payload = json.loads(completed.stdout)
        duration = float(payload["format"]["duration"])
        types = {s.get("codec_type") for s in payload["streams"]}
    except (KeyError, TypeError, ValueError):
        return False
    return duration > 0 and {"video", "audio"} <= types


def evaluate(repo_root: Path, slug: str, mode: str, expected_hash: str, artifacts: Path) -> dict:
    if mode not in {"draft", "final"}:
        raise ValueError("mode must be draft or final")
    video_dir = video_dir_for(repo_root, slug)
    narration = video_dir / "audio" / "narration.wav"
    if not narration.is_file():
        raise FileNotFoundError(f"locked narration is missing: {narration}")
    expected_hash = expected_hash.strip().lower()
    if sha256(narration) != expected_hash:
        raise RuntimeError("narration hash differs from the lock before render; refusing to render")

    output = repo_root / "out" / f"{slug}.mp4"
    before = signature(output)
    command = [*python_launcher(), "scripts/build.py", "render", f"videos/{slug}"]
    if mode == "draft":
        command += ["--quality", "draft"]
    completed = run(command, repo_root)
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / f"render-{mode}.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
    combined = completed.stdout + completed.stderr
    # A draft render that trips ONLY the post-render static gate is still a
    # usable draft: the MP4 exists and validate-video re-runs check-static, so
    # the finding reaches produce-video through the loop instead of killing it.
    # The launcher chain (uv -> py -> build.py) does not reliably preserve
    # build.py's exit 2, so key on the gate's own message plus a refreshed MP4.
    static_only = (
        mode == "draft"
        and completed.returncode != 0
        and "Static gate FAILED" in combined
        and signature(output) not in (None, before)
    )
    if completed.returncode != 0 and not static_only:
        tail = combined.strip().splitlines()[-10:]
        raise RuntimeError(f"{mode} render exited {completed.returncode}: {' | '.join(tail)}")
    if signature(output) in (None, before):
        raise RuntimeError(f"{mode} render did not refresh {output}")
    if not probe_ok(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(output)], repo_root)):
        raise RuntimeError(f"{mode} render MP4 lacks a decodable video+audio pair: {output}")
    decode = run(["ffmpeg", "-nostdin", "-xerror", "-v", "error", "-i", str(output), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], repo_root)
    if decode.returncode != 0:
        raise RuntimeError(f"{mode} render failed full decode: {decode.stderr.strip()[-400:]}")
    if sha256(narration) != expected_hash:
        raise RuntimeError("narration hash changed during render")
    return {
        "complete": True,
        "narration_sha256": expected_hash,
        "render_path": f"out/{slug}.mp4",
        "static_gate_failed": static_only,
        "summary": f"{mode.capitalize()} render completed; MP4 refreshed and fully decodes."
        + (" Static gate FAILED; validate-video reports the intervals." if static_only else ""),
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        result = evaluate(
            Path.cwd().resolve(),
            os.environ["INPUTS_SLUG"],
            os.environ["INPUTS_MODE"],
            os.environ["INPUTS_NARRATION_SHA256"],
            Path(os.environ["ARTIFACTS_DIR"]).resolve(),
        )
    except Exception as exc:
        print(json.dumps({"complete": False, "operational_error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
