import type { ColorState, EpisodeSection, LayoutState, MediaItem, RetentionDevice, ScriptTag, VisualMode } from "./types";

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

export function flattenTags(sections: { tags: ScriptTag[] }[]): ScriptTag[] {
  return sections.flatMap((section) => section.tags);
}

export function getActiveSection(sections: EpisodeSection[], time: number): EpisodeSection | undefined {
  return sections.find((section) => time >= section.start && time < section.end) ?? sections[sections.length - 1];
}

export function getActiveVisualMode(sections: EpisodeSection[], time: number): VisualMode {
  const section = getActiveSection(sections, time);
  if (section?.visual_mode) {
    return section.visual_mode;
  }
  const layout = getActiveLayout(flattenTags(sections), time);
  if (layout === "STATE_CRITICAL_ERROR") return "critical_error";
  if (layout === "STATE_DEEP_DIVE") return "case_file";
  return "monologue";
}

export function getActiveRetentionDevice(sections: EpisodeSection[], time: number): RetentionDevice | undefined {
  return getActiveSection(sections, time)?.retention_device;
}

export function getActiveColorState(sections: EpisodeSection[], time: number): ColorState {
  const section = getActiveSection(sections, time);
  if (section?.color_state) return section.color_state;
  return getActiveVisualMode(sections, time) === "critical_error" ? "red" : "teal";
}

export function getActiveMediaSequence(sections: EpisodeSection[], tags: ScriptTag[], time: number): MediaItem | undefined {
  const section = getActiveSection(sections, time);
  if (section?.media_overlay && "kind" in section.media_overlay) {
    return section.media_overlay as MediaItem;
  }
  if (section?.media_overlay && "type" in section.media_overlay) {
    const { type, ...rest } = section.media_overlay as Record<string, unknown>;
    return { ...rest, kind: type } as MediaItem;
  }
  return getActiveMedia(tags, time);
}

export function layoutForColorState(colorState: ColorState, visualMode: VisualMode): LayoutState {
  if (colorState === "red" || visualMode === "critical_error") return "STATE_CRITICAL_ERROR";
  if (visualMode === "monologue" || visualMode === "outro") return "STATE_MONOLOGUE";
  return "STATE_DEEP_DIVE";
}
