import {
  getActiveLayout,
  getActiveMedia,
  isSipActive,
  isSpeaking,
} from "./state";
import type { AudioAmplitudeSample, ScriptTag } from "./types";

const tags: ScriptTag[] = [
  { at: 0, type: "layout", value: "STATE_MONOLOGUE" },
  { at: 4, type: "sip" },
  {
    at: 8,
    type: "media",
    value: { id: "code-1", kind: "code", language: "html", content: "<main />" },
  },
  { at: 10, type: "layout", value: "STATE_DEEP_DIVE" },
  { at: 20, type: "layout", value: "STATE_CRITICAL_ERROR" },
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
