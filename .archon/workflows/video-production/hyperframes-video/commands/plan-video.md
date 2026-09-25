# Plan the HyperFrames video

You are planning one video in the diy-yt-creator-hyperframes repository. This node owns the planning artifacts only. It must not generate narration, render, or edit `index.html`, `compositions/`, CSS, JavaScript, or audio.

Bound inputs:

- Slug: `$INPUTS.slug` — the project directory is `videos/$INPUTS.slug/`
- Format: `$INPUTS.format` (`long-form` = 1920x1080, `shorts` = 1080x1920)
- Operator brief: `$INPUTS.brief`
- Accept existing artifacts: `$INPUTS.accept_existing`
- Revision feedback from the operator's last approval answer (empty on the first pass): `$INPUTS.revision_feedback`
- Preflight problems from the last pass (empty on the first pass; a non-empty list means the previous planning set failed a deterministic check and was never shown to the operator): `$INPUTS.preflight_problems`
- Run artifacts directory: `$ARTIFACTS_DIR`

The run's trigger message, which may add context: `$ARGUMENTS`

## 1. Load the rules before judging anything

Read, in this order:

1. `CLAUDE.md` (Key Rules) and every `.claude/rules/*.md` it routes to for source grounding, scripting, voice laws, anti-workslop, engagement CTA, AI disclosure, and the format's layout rules (`shorts-safe-zone.md` / `shorts-thumbnail-frames.md` for shorts; `scene-continuity.md`, `topic-adaptation.md` for long-form).
2. `brand-voices/thomas-tone-of-voice.md` in full.
3. `.claude/skills/diy-yt-creator/SKILL.md` and the playbook matching the chosen template.
4. `.agents/skills/kinetic-visual-architect/SKILL.md` and its `references/kinetic-visual-plan-template.md`.
5. The master catalog at `D:\Nextcloud\Obsidian\sync\smartcode\Videos\_catalog\catalog.json` — check for a prior video on the same topic and name it in `BRIEF.md` if one exists.

## 2. Ground the topic

- If `videos/$INPUTS.slug/` does not exist, create it by copying the matching template under `templates/<format>/<style>/` per `CLAUDE.md` § Adding a new video, and set `meta.json`.
- Treat `$INPUTS.brief` and `$ARGUMENTS` as operator intent, not as proof. Every factual claim in the script must trace to a primary source you read this run (URL, repo file, user-supplied screenshot). Record them in `videos/$INPUTS.slug/research/source-notes.md` and `research/claim-ledger.md`. Invent nothing.
- When `$INPUTS.accept_existing` is `true`, existing planning files are inputs to verify, not to recreate. When `$INPUTS.revision_feedback` is non-empty, it names what the operator refused last pass; address every point in it explicitly. When `$INPUTS.preflight_problems` is non-empty, fix each listed problem first; they are machine findings, not opinions.

## 3. Produce or validate the planning set

All of these must exist under `videos/$INPUTS.slug/` when you finish:

- `BRIEF.md` — scope, audience, `voice_profile: thomas`, template chosen, format, zero background music, the exact final debate CTA question, and the `adaptation:` block when the template is `editorial-cinematic`.
- `research/source-notes.md`, `research/claim-ledger.md`.
- `script.txt` — the flat spoken Thomas script. Long-form additionally writes `scripts/full-script.md` and per-scene `scripts/scene-NN-*.txt` per `phase2a-tts-script`. Apply the TTS heteronym audit (`.claude/rules/tts-pronunciation.md`), no em-dashes, no spoken word "quote", debate-sparking CTA as the last sentence.
- `STORYBOARD.md` — narration-ordered visual beats, the visual anchor per scene (real screenshots / source artifacts, never narration printed on screen), and which registry or `shared/lib` blocks each scene uses.
- `kinetic-visual-plan.md` — the complete V6.3 contract from the template: `Skill invoked: kinetic-visual-architect`, `V6.3`, `Voice profile: thomas`, `Narration lock: 100%`, `Background music: none`, and the four required H2 sections in order.
- `youtube-description.md` per `.claude/rules/youtube-metadata.md` (chapters carry placeholder timestamps; the build pass finalizes them).

Then run these yourself and fix every hit before returning:

```
py scripts/check-workslop.py videos/$INPUTS.slug
py scripts/check-retention-gate.py videos/$INPUTS.slug
py scripts/check-ai-disclosure.py videos/$INPUTS.slug
```

## 4. Stop rules

A claim you cannot source, a template that does not exist, or a brief that contradicts a repository rule is a blocker. Set `ready: false`, name the exact blocker in `summary`, and do not work around it. Do not run TTS, preview, or render under any circumstances.

## 5. Report

Write `$ARTIFACTS_DIR/plan-report.md`: template chosen, sources used, check results, open questions. No one watches this run; the report and the declared fields are the only record.

Return the structured object:

- `ready` — true only when every file above exists and all three checks pass.
- `script_path` — `videos/$INPUTS.slug/script.txt`.
- `kinetic_plan_path` — `videos/$INPUTS.slug/kinetic-visual-plan.md`.
- `summary` — what was produced and what (if anything) blocks. Never claim narration or composition work happened.
