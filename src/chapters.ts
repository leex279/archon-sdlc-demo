import { formatTimecode } from "./timecode.ts";

export interface Chapter {
  start: number;
  title: string;
}

/** Parse lines of "<seconds> <title>" into chapters, skipping blanks. */
export function parseChapters(input: string): Chapter[] {
  return input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const match = /^(\d+)\s+(.+)$/.exec(line);
      if (!match) throw new SyntaxError(`cannot parse chapter line: "${line}"`);
      return { start: Number(match[1]), title: match[2] };
    });
}

/** Render chapters as the block YouTube reads from a video description. */
export function renderChapters(chapters: Chapter[]): string {
  return chapters.map((c) => `${formatTimecode(c.start)} ${c.title}`).join("\n");
}
