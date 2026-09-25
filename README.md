# archon-sdlc-demo

A tiny CLI that turns chapter start times into YouTube chapter timestamps.

```bash
printf '0 Intro\n95 Setup\n3725 Wrap-up\n' | npm run -s chapters
# 0:00 Intro
# 1:35 Setup
# 1:02:05 Wrap-up
```

Input is one chapter per line: `<start in whole seconds> <title>`.

Requires Node 22.6+ (runs TypeScript directly with `--experimental-strip-types`).

## Development

```bash
npm test
```

This repository is the demo target for a DIY Smart Code video about Archon's
SDLC workflows.

## Workflows shown in the video

- **Run 1 — `archon-ship`** (ships with Archon 0.10.x, the maintained SDLC pack)
  took issue #1 to pull request #2.
- **Run 2 — `hyperframes-video`**, a custom workflow for producing videos. A
  reference copy lives in
  [`.archon/workflows/video-production/hyperframes-video/`](.archon/workflows/video-production/hyperframes-video/).

