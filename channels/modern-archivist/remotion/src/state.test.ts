import {
  getActiveCharacterCue,
  getActiveColorState,
  getActiveLayout,
  getActiveMedia,
  getActiveMediaSequence,
  getActiveRetentionDevice,
  getActiveSection,
  getActiveVisualMode,
  isSipActive,
  isSpeaking,
  layoutForColorState,
} from "./state";
import type { AudioAmplitudeSample, EpisodeSection, ScriptTag } from "./types";

const tags: ScriptTag[] = [
  { at: 0, type: "layout", value: "STATE_MONOLOGUE" },
  { at: 4, type: "sip" },
  { at: 8, type: "media", value: { id: "code-1", kind: "code", language: "html", content: "<main />" } },
  { at: 10, type: "layout", value: "STATE_DEEP_DIVE" },
  { at: 20, type: "layout", value: "STATE_CRITICAL_ERROR" },
];

const sections: EpisodeSection[] = [
  { id: "s1", start: 0, end: 8, text: "Hook", tags: [tags[0]], visual_mode: "monologue", retention_device: "cold_open_shock", color_state: "teal", character: { visible: true, action: "glasses_flash", expression: "skeptical" } },
  { id: "s2", start: 8, end: 20, text: "Case", tags: [tags[2], tags[3]], visual_mode: "case_file", retention_device: "evidence_receipt", color_state: "teal", character: { visible: false, action: "hidden", expression: "none" }, media_overlay: { id: "case-1", kind: "case_file_sequence", title: "Case file", evidence_refs: ["source_1"] } },
  { id: "s3", start: 20, end: 28, text: "Interrupt", tags: [tags[4]], visual_mode: "critical_error", retention_device: "pattern_interrupt", color_state: "red", character: { visible: true, action: "sip_coffee", expression: "deadpan" } },
];

const amplitude: AudioAmplitudeSample[] = [
  { time: 0, volume: 0 },
  { time: 1, volume: 0.2 },
  { time: 2, volume: 0.01 },
];

function assertEqual<T>(actual: T, expected: T, message: string) {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${expected}, got ${actual}`);
  }
}

assertEqual(getActiveLayout(tags, 0), "STATE_MONOLOGUE", "initial layout");
assertEqual(getActiveLayout(tags, 12), "STATE_DEEP_DIVE", "deep dive layout");
assertEqual(getActiveLayout(tags, 24), "STATE_CRITICAL_ERROR", "critical error layout");
assertEqual(isSipActive(tags, 4.5), true, "sip active inside one-second window");
assertEqual(isSipActive(tags, 7), false, "sip inactive outside window");
assertEqual(isSpeaking(amplitude, 1.05), true, "speaking above volume threshold");
assertEqual(isSpeaking(amplitude, 2.0), false, "not speaking below volume threshold");
assertEqual(getActiveMedia(tags, 9)?.id, "code-1", "media active after media tag");
assertEqual(getActiveSection(sections, 9)?.id, "s2", "active section by time");
assertEqual(getActiveVisualMode(sections, 9), "case_file", "visual mode from section");
assertEqual(getActiveCharacterCue(sections, 9).visible, false, "hidden character cue from section");
assertEqual(getActiveCharacterCue(sections, 21).action, "sip_coffee", "character action from section");
assertEqual(getActiveRetentionDevice(sections, 2), "cold_open_shock", "retention device from section");
assertEqual(getActiveColorState(sections, 21), "red", "red critical state");
assertEqual(getActiveMediaSequence(sections, tags, 9)?.kind, "case_file_sequence", "media overlay preferred");
const typeOnlyOverlaySections: EpisodeSection[] = [{
  id: "s-type",
  start: 0,
  end: 5,
  text: "Type-only overlay",
  tags: [],
  visual_mode: "source_montage",
  media_overlay: { type: "source_montage", title: "Source packet", sources: [] },
}];
assertEqual(getActiveMediaSequence(typeOnlyOverlaySections, [], 1)?.kind, "source_montage", "type-only media overlay normalized to kind");
assertEqual(layoutForColorState("red", "critical_error"), "STATE_CRITICAL_ERROR", "layout from red state");
