import type { AudioAmplitudeSample, LayoutState, MediaItem, ScriptTag } from "./types";

export const DEFAULT_LAYOUT: LayoutState = "STATE_MONOLOGUE";

export function getActiveLayout(tags: ScriptTag[], time: number): LayoutState {
  const active = tags
    .filter((tag): tag is Extract<ScriptTag, { type: "layout" }> => tag.type === "layout")
    .filter((tag) => tag.at <= time)
    .sort((a, b) => b.at - a.at);

  return active[0]?.value ?? DEFAULT_LAYOUT;
}

export function getActiveMedia(tags: ScriptTag[], time: number): MediaItem | undefined {
  const active = tags
    .filter((tag): tag is Extract<ScriptTag, { type: "media" }> => tag.type === "media")
    .filter((tag) => tag.at <= time)
    .sort((a, b) => b.at - a.at);

  return active[0]?.value;
}

export function isSipActive(tags: ScriptTag[], time: number, durationSeconds = 1.1): boolean {
  return tags.some((tag) => tag.type === "sip" && time >= tag.at && time <= tag.at + durationSeconds);
}

export function isSpeaking(
  amplitude: AudioAmplitudeSample[] | undefined,
  time: number,
  threshold = 0.08,
): boolean {
  if (!amplitude || amplitude.length === 0) {
    return false;
  }

  const nearest = amplitude.reduce((best, sample) =>
    Math.abs(sample.time - time) < Math.abs(best.time - time) ? sample : best,
  );

  return nearest.volume > threshold;
}

export function flattenTags(sections: { tags: ScriptTag[] }[]): ScriptTag[] {
  return sections.flatMap((section) => section.tags);
}
