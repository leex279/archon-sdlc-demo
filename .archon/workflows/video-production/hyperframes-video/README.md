# hyperframes-video

> **Reference copy.** This is the custom Archon workflow shown in the second half
> of the DIY Smart Code video on Archon's SDLC workflows. It produces videos in a
> private HyperFrames video repository, so it does not run inside this demo repo:
> its scripts expect that repo's `videos/<slug>/` layout and its `scripts/*.py`
> gates. Read it as an example of a project-specific workflow with a planning
> loop, one human approval, hash-locked narration, and a production loop that
> exits only when deterministic gates are green AND a fresh reviewer says ready.

Project-specific Archon workflow for the `diy-yt-creator-hyperframes` repository.
Takes one video slug from grounded planning to a verified MP4 with QA receipts.

## Run

From the repository root (the checkout must be the video repo; scripts resolve
`videos/<slug>/` and `scripts/*.py` relative to cwd):

```bash
archon workflow run hyperframes-video --no-worktree \
  --input slug=my-video --input format=long-form \
  --input brief="Topic, angle, sources" \
  "Produce the video for my-video"
```

- Models: workflow default `sonnet` (Sonnet 5, build node); `plan-video` and `review-video` pin `fable` (Fable 5.1). Edit the `model:` lines in the yaml to change.
- `interactive: true` — the fresh launch cannot `--detach`; run it as a
  background task of your harness and resolve the one approval gate with
  `archon workflow approve <run-id>` / `reject`.
- `--no-worktree` is pinned: narration, transcript and the MP4 belong on the
  working branch.
- Resume a half-built video: add `--input accept_existing=true` to adopt an
  existing `audio/narration.wav` + `transcript.json` as the locked narration.

## Shape

```
planning (loop_group ≤3)  plan-video → preflight → approve-plan
narration (script)        TTS once, hash-locked, receipt in $ARTIFACTS_DIR
production (loop_group ≤4) produce-video → render-draft → contact-sheet → validate-video → review-video
final-render (script)
verify-and-report (script) → exits 1 on any missing artifact, failing the run
```

Gates: deterministic (`preflight`, `validate-video`, `verify-and-report`), agent
judgment on decoded pixels (`review-video`, `context: fresh`), one human gate
before money (`approve-plan`).

## Fixtures

```bash
archon workflow test hyperframes-video
```

`green` proves wiring; `preflight-red` proves the money gate is skipped on red;
`slug-invalid-exec` runs the real preflight against a path-like slug.

Known dry-run limitation (Archon 0.10.x): `loop_group.until_bash` is not
evaluated by the simulator, so the correction loop's red→retry path is proven by
a real run, not a fixture.

## Out of scope

YouTube upload, catalog `link`/`archive`, ffmpeg speed-ups, and maintenance
re-renders of published videos stay manual per the repo rules.
