import { test } from "node:test";
import assert from "node:assert/strict";
import { parseChapters, renderChapters } from "../src/chapters.ts";

test("parses and renders a chapter list", () => {
  const chapters = parseChapters("0 Intro\n\n95 Setup\n605 Demo\n");
  assert.deepEqual(chapters, [
    { start: 0, title: "Intro" },
    { start: 95, title: "Setup" },
    { start: 605, title: "Demo" },
  ]);
  assert.equal(renderChapters(chapters), "0:00 Intro\n1:35 Setup\n10:05 Demo");
});

test("rejects a line without a start time", () => {
  assert.throws(() => parseChapters("Intro"), SyntaxError);
});
