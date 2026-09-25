# Build or correct the composition

You are building the HyperFrames composition for one video against narration that is already locked. You run inside a bounded correction loop: the first iteration builds, later iterations correct the defects the previous validation and review named.

Bound inputs:

- Slug: `$INPUTS.slug` — project at `videos/$INPUTS.slug/`
- Format: `$INPUTS.format`
- Locked narration SHA-256: `$INPUTS.narration_sha256`
- Previous deterministic validation (empty on the first iteration): `$INPUTS.previous_validation`
- Previous independent review (empty on the first iteration): `$INPUTS.previous_review`
- Run artifacts directory: `$ARTIFACTS_DIR`

Work only inside `videos/$INPUTS.slug/`. Read `CLAUDE.md`, the `.claude/rules/*.md` it routes to, `BRIEF.md`, `script.txt`, `transcript.json`, `STORYBOARD.md`, and `kinetic-visual-plan.md` before editing. Invoke the repository's `hyperframes`, `gsap`, `gsap-timeline`, `visual-richness`, and the format-specific diy-yt-creator playbook as the composition rules.

## The narration is locked

`videos/$INPUTS.slug/audio/narration.wav` and `transcript.json` are inputs. Never delete, overwrite, retime, edit, or regenerate them for any reason — pacing, retention, layout, and review findings are fixed on the visual side only. A factual defect in the locked narration is a blocker: report it in `summary`, set `complete: false`, and stop. The workflow recomputes the hash after you return.

Background music is forbidden. Foley only where the kinetic plan assigns a semantic event, always beneath narration.

## First iteration: build

Build `index.html` (and `compositions/scene-*.html` for long-form) from the storyboard and kinetic plan with every reveal anchored to `transcript.json` word times. Apply the repository rules in full, including: the static top-left `#ai-disclosure` badge, `window.__timelines` registration with paused timelines, `class="clip"` + `data-start/duration/track-index` on every timed element, step-by-step reveals with the `tl.set` at 0 + `tl.to` pattern, no static window over 5 s, per-scene `tl.set({}, {}, DUR)` padding, local vendored GSAP, literal `font-family` names (no `var(--sans|--mono)`), topic-matching shape SVGs, Werbung badge on any promo, and the `#cta-question` element in the final phase. Finalize the chapter timestamps in `youtube-description.md` from the real `data-start` values.

## Later iterations: correct

Parse `$INPUTS.previous_validation` (failed gate names plus `failed_details`, the gate's own findings such as static-interval timestamps; the full output is in its `receipt_path`) and `$INPUTS.previous_review` (timestamped blocking findings). Fix exactly those. Do not redesign passing scenes, and do not touch narration.

## Validate before returning

Run and clear:

```
npx hyperframes lint videos/$INPUTS.slug
npx hyperframes inspect videos/$INPUTS.slug
py scripts/check-ai-disclosure.py videos/$INPUTS.slug
py scripts/check-scene-sync.py videos/$INPUTS.slug
```

Do NOT run `render`, `preview`, or any background process — the next workflow node renders the draft synchronously and builds the contact sheet from it.

## Report

Write `$ARTIFACTS_DIR/build-report.md`: what changed this iteration, which findings were addressed and how, commands run with results. No one watches this run; the report and the declared fields are the only record.

Return the structured object:

- `complete` — true only when this iteration's scoped work is done and the four commands above pass.
- `summary` — actions, evidence, or the exact blocker.
