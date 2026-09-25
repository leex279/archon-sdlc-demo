"""Pre-TTS money gate: planning artifacts exist and the repository's own
hook-enforced checks pass BEFORE the operator is asked to approve paid narration.

Inside Claude Code these checks fire as PreToolUse hooks on the TTS command. An
Archon run has no such hook, so this node runs them explicitly. Reads
INPUTS_SLUG and INPUTS_PLAN_READY; prints one JSON object with `green`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = (
    "BRIEF.md",
    "script.txt",
    "STORYBOARD.md",
    "kinetic-visual-plan.md",
    "youtube-description.md",
    "meta.json",
    "index.html",
)
PLAN_REQUIREMENTS = (
    ("Voice profile: thomas", r"^\s*(?:voice[_ ]profile)\s*:\s*thomas\s*$"),
    ("Narration lock", r"^\s*narration lock\s*:"),
    ("Background music: none", r"^\s*background music\s*:\s*none\s*$"),
)
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def video_dir_for(repo_root: Path, slug: str) -> Path:
    if not SLUG_PATTERN.fullmatch(slug or ""):
        raise ValueError("slug must be a non-empty lowercase hyphenated identifier")
    videos_root = (repo_root / "videos").resolve()
    video_dir = (videos_root / slug).resolve()
    video_dir.relative_to(videos_root)
    return video_dir


def python_launcher() -> list[str]:
    """The repository's own Python (its check scripts import repo-local deps),
    never the uv interpreter this script happens to run under."""
    if sys.platform == "win32" and shutil.which("py"):
        return ["py", "-3"]
    for name in ("python3", "python"):
        if shutil.which(name):
            return [name]
    raise RuntimeError("no repository Python launcher (py/python3/python) on PATH")


def repo_checks(slug: str) -> list[list[str]]:
    py = python_launcher()
    video = f"videos/{slug}"
    return [
        [*py, "scripts/check-workslop.py", video],
        [*py, "scripts/check-retention-gate.py", video],
        [*py, "scripts/check-ai-disclosure.py", video],
    ]


def evaluate(repo_root: Path, slug: str, plan_ready: str) -> dict:
    video_dir = video_dir_for(repo_root, slug)
    problems: list[str] = []
    if plan_ready.strip().lower() != "true":
        problems.append("plan-video declared ready=false")
    problems.extend(f"missing {name}" for name in REQUIRED_FILES if not (video_dir / name).is_file())
    plan_path = video_dir / "kinetic-visual-plan.md"
    if plan_path.is_file():
        plan = plan_path.read_text(encoding="utf-8")
        problems.extend(
            f"kinetic-visual-plan.md lacks '{label}'"
            for label, pattern in PLAN_REQUIREMENTS
            if not re.search(pattern, plan, re.IGNORECASE | re.MULTILINE)
        )
    gates = []
    if not problems:
        for command in repo_checks(slug):
            completed = subprocess.run(
                command, cwd=repo_root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", check=False,
            )
            gates.append({"command": command, "returncode": completed.returncode})
            if completed.returncode != 0:
                tail = (completed.stdout + completed.stderr).strip().splitlines()[-6:]
                problems.append(f"{' '.join(command)} exited {completed.returncode}: {' | '.join(tail)}")
    green = not problems
    return {
        "green": green,
        "slug": slug,
        "problems": problems,
        "gates": gates,
        "summary": "Preflight green: planning set complete and pre-TTS checks pass."
        if green
        else f"Preflight red ({len(problems)}): {'; '.join(problems)}",
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        result = evaluate(Path.cwd().resolve(), os.environ["INPUTS_SLUG"], os.environ.get("INPUTS_PLAN_READY", ""))
    except Exception as exc:  # operational failure, not a red verdict
        print(json.dumps({"green": False, "operational_error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
