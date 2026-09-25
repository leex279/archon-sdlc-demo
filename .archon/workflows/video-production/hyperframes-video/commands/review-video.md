# Independently review the draft render

You are a fresh reviewer with no memory of how this video was built. Judge the decoded pixels and audio, not the source or the lint output. This node is read-only for the repository: do not edit, create, delete, or stage any file under `videos/`. Your only write is the receipt named below.

Bound inputs:

- Slug: `$INPUTS.slug`
- Format: `$INPUTS.format`
- Locked narration SHA-256: `$INPUTS.narration_sha256`
- Draft MP4: `$INPUTS.render_path`
- Contact sheets (JSON array of image paths): `$INPUTS.contact_sheets`
- Deterministic validation verdict (JSON): `$INPUTS.validation`
- Run artifacts directory: `$ARTIFACTS_DIR`

## Evidence to inspect

1. Read `videos/$INPUTS.slug/script.txt`, `transcript.json`, `kinetic-visual-plan.md`, `STORYBOARD.md`, `research/claim-ledger.md`, and the validation verdict.
2. View every contact sheet listed in `$INPUTS.contact_sheets`. Additionally extract and view single frames from the MP4 with ffmpeg at: t=0, the hook (first 3 s), every scene transition named in the storyboard, any dense UI/code moment, the CTA hold, and the final frame.
3. Compare what is visible at each timestamp to the narration active at that time (`transcript.json`) and to the claim ledger.

Lint output, exit codes, and DOM inspection are not visual evidence. If the MP4 or contact sheets are missing, unreadable, or too sparse to judge, that is itself a blocking finding.

## Judge against the repository's rules

For every finding cite the timestamp or range and the rule it breaks. At minimum check:

- every on-screen claim is supported by the narration and the source ledger; no fabricated UI or numbers;
- `AI GENERATED` badge legible top-left on the first, middle, and last frames;
- readable layout at the format's canvas; for shorts, all information inside x 60→960 / y 250→1420, top-anchored, first and last frame thumbnail-grade;
- no foreground frozen longer than 5 s; scenes hand off with no dead frames; reveals land on their spoken words rather than ahead of them;
- narration intelligible, no background music, foley under narration;
- Werbung badge present on any promo card;
- the spoken CTA, the on-screen `#cta-question`, and the `youtube-description.md` closer are the same question.

Findings must rest on what you saw. Drop anything that rests on "might".

## Receipt and verdict

Write `$ARTIFACTS_DIR/independent-review-receipt.json` containing: `ready`, `blocking_findings`, `summary`, `render_path`, `narration_sha256`, `frames_inspected` (timestamps), and `contact_sheets_inspected`.

Return the structured object:

- `ready` — true only when direct inspection found no blocking issue.
- `receipt_path` — the absolute POSIX-style path of the receipt you wrote.
- `blocking_findings` — actionable strings, each with a timestamp; empty when ready.
- `summary` — the verdict in a few sentences with the evidence behind it.
