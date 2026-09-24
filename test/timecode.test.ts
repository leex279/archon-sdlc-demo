import { test } from "node:test";
import assert from "node:assert/strict";
import { formatTimecode } from "../src/timecode.ts";

test("formats times under a minute", () => {
  assert.equal(formatTimecode(0), "0:00");
  assert.equal(formatTimecode(59), "0:59");
});

test("formats minutes", () => {
  assert.equal(formatTimecode(61), "1:01");
  assert.equal(formatTimecode(3599), "59:59");
});

test("formats hours", () => {
  assert.equal(formatTimecode(3725), "1:02:05");
});

test("rejects negative and fractional input", () => {
  assert.throws(() => formatTimecode(-1), RangeError);
  assert.throws(() => formatTimecode(1.5), RangeError);
});
