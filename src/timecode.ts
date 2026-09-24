/**
 * Format a whole number of seconds the way YouTube expects chapter
 * timestamps: M:SS below one hour, H:MM:SS from one hour on.
 */
export function formatTimecode(totalSeconds: number): string {
  if (!Number.isInteger(totalSeconds) || totalSeconds < 0) {
    throw new RangeError(`expected a non-negative integer, got ${totalSeconds}`);
  }
  const pad = (n: number) => String(n).padStart(2, "0");
  const seconds = totalSeconds % 60;

  if (totalSeconds > 3600) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    return `${hours}:${pad(minutes)}:${pad(seconds)}`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  return `${minutes}:${pad(seconds)}`;
}
