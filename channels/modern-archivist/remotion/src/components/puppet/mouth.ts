export type MouthShape =
  "closed" | "slightOpen" | "openA" | "openE" | "openO" | "smirk" | "frown";

export interface WordTimestamp { start: number; end: number }

const WORD_SLOP_SEC = 0.05;

export const MOUTH_SRC: Record<MouthShape, string> = {
  closed:     "modern-archivist/mouth-closed.png",
  slightOpen: "modern-archivist/mouth-slight-open.png",
  openA:      "modern-archivist/mouth-open-a.png",
  openE:      "modern-archivist/mouth-open-e.png",
  openO:      "modern-archivist/mouth-open-o.png",
  smirk:      "modern-archivist/mouth-smirk.png",
  frown:      "modern-archivist/mouth-frown.png",
};

// Phoneme cycle while speaking (~8 switches per second)
const SPEAK_CYCLE: MouthShape[] = ["openA", "openE", "openO", "slightOpen", "openA", "openO"];

export function resolvedSpeaking(
  coarse: boolean,
  frame: number,
  fps: number,
  wordTimestamps?: WordTimestamp[],
): boolean {
  if (!wordTimestamps || wordTimestamps.length === 0) return coarse;
  const t = frame / fps;
  let lo = 0;
  let hi = wordTimestamps.length - 1;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (wordTimestamps[mid].end + WORD_SLOP_SEC < t) lo = mid + 1;
    else hi = mid;
  }
  const current = wordTimestamps[lo];
  return Boolean(current && t >= current.start - WORD_SLOP_SEC && t <= current.end + WORD_SLOP_SEC);
}

export function selectMouth(
  speaking: boolean,
  expression: string,
  frame: number,
  fps: number,
): MouthShape {
  if (speaking) {
    return SPEAK_CYCLE[Math.floor((frame / fps) * 8) % SPEAK_CYCLE.length];
  }
  if (expression === "skeptical" || expression === "dry_disbelief" || expression === "dry_final") return "smirk";
  if (expression === "flat_alarm" || expression === "controlled_alarm") return "slightOpen";
  if (expression === "case_closed") return "frown";
  return "closed";
}
