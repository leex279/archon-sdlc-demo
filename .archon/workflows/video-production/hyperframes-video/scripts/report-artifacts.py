"""Terminal verdict from artifacts on disk, never from run status.

Checks: narration hash equals the lock receipt, transcript present, final MP4
decodes, validation receipt green, review receipt ready, at least one contact
sheet exists, youtube-description.md exists. Writes
$ARTIFACTS_DIR/final-artifact-report.json and prints `succeeded` — the
run's verdict. A red verdict exits 1 so the run FAILS rather than
completing without a deliverable; the reasons are in the report file.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
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


def read_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def mp4_decodes(mp4: Path, cwd: Path) -> bool:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(mp4)],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if completed.returncode != 0:
        return False
    try:
        payload = json.loads(completed.stdout)
        return float(payload["format"]["duration"]) > 0 and {"video", "audio"} <= {s.get("codec_type") for s in payload["streams"]}
    except (KeyError, TypeError, ValueError):
        return False


def evaluate(repo_root: Path, slug: str, expected_hash: str, render_path: str, artifacts: Path) -> dict:
    video_dir = video_dir_for(repo_root, slug)
    expected_hash = expected_hash.strip().lower()
    reasons: list[str] = []

    narration = video_dir / "audio" / "narration.wav"
    actual_hash = hashlib.sha256(narration.read_bytes()).hexdigest() if narration.is_file() else None
    lock = read_json(artifacts / "narration-lock.json") or {}
    locked_hash = str(lock.get("narration_sha256", "")).lower()
    if not (actual_hash and actual_hash == expected_hash == locked_hash):
        reasons.append("narration_lock_mismatch")

    if not (video_dir / "transcript.json").is_file():
        reasons.append("transcript_missing")
    if not (video_dir / "youtube-description.md").is_file():
        reasons.append("youtube_description_missing")

    final_mp4 = (repo_root / render_path).resolve()
    if final_mp4 != (repo_root / "out" / f"{slug}.mp4").resolve():
        reasons.append("render_path_not_canonical")
    elif not final_mp4.is_file():
        reasons.append("final_mp4_missing")
    elif not mp4_decodes(final_mp4, repo_root):
        reasons.append("final_mp4_decode_failed")

    validation = read_json(artifacts / "validation-receipt.json")
    if not (validation and validation.get("green") is True):
        reasons.append("validation_not_green")
    review = read_json(artifacts / "independent-review-receipt.json")
    if not (review and review.get("ready") is True):
        reasons.append("independent_review_not_ready")

    sheets = sorted(p.as_posix() for p in (artifacts / "qa").glob("contact-sheet-*.jpg") if p.stat().st_size > 0) if (artifacts / "qa").is_dir() else []
    if not sheets:
        reasons.append("contact_sheet_missing")

    succeeded = not reasons
    result = {
        "succeeded": succeeded,
        "mp4_path": f"out/{slug}.mp4",
        "validation_receipt": (artifacts / "validation-receipt.json").as_posix(),
        "review_receipt": (artifacts / "independent-review-receipt.json").as_posix(),
        "contact_sheets": sheets,
        "summary": f"Video {slug} verified: final MP4, locked narration, green validation, ready review, contact sheets."
        if succeeded
        else f"Artifact verification failed: {', '.join(reasons)}",
    }
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "final-artifact-report.json").write_text(
        json.dumps({**result, "actual_narration_sha256": actual_hash, "locked_narration_sha256": locked_hash or None, "reasons": reasons}, indent=2) + "\n",
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
            os.environ.get("INPUTS_RENDER_PATH", f"out/{os.environ['INPUTS_SLUG']}.mp4"),
            Path(os.environ["ARTIFACTS_DIR"]).resolve(),
        )
    except Exception as exc:
        print(json.dumps({"succeeded": False, "operational_error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    if not result["succeeded"]:
        print(f"verify-and-report: {result['summary']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
