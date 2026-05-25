import { resolvedSpeaking, selectMouth } from "./mouth.js";
import type { WordTimestamp } from "./mouth.js";

let passed = 0;
let failed = 0;

function assert(condition: boolean, msg: string) {
  if (condition) { console.log(`  ✓ ${msg}`); passed++; }
  else { console.error(`  ✗ ${msg}`); failed++; }
}

// Test 1: no word timings + coarse speaking=false -> resolvedSpeaking returns false
assert(
  resolvedSpeaking(false, 0, 30, undefined) === false,
  "no word timings + coarse=false -> resolvedSpeaking=false"
);

// Test 2: no word timings + speaking=false + selectMouth expression="neutral" -> "closed"
assert(
  selectMouth(false, "neutral", 0, 30) === "closed",
  'no word timings + speaking=false + expression="neutral" -> "closed"'
);

// Test 3: word timing active: frame inside a word window -> resolvedSpeaking=true -> selectMouth returns open shape
const words: WordTimestamp[] = [{ start: 1.0, end: 1.5 }, { start: 2.0, end: 2.5 }];
const fps = 30;
const frameInsideWord = 35; // t = 35/30 = 1.1667s, inside [1.0, 1.5]
const isSpeakingInside = resolvedSpeaking(false, frameInsideWord, fps, words);
assert(isSpeakingInside === true, "word timing active: frame inside word window -> resolvedSpeaking=true");
const mouthInsideWord = selectMouth(isSpeakingInside, "neutral", frameInsideWord, fps);
const openShapes = ["openA", "openE", "openO", "slightOpen"];
assert(
  openShapes.includes(mouthInsideWord),
  `word timing active: selectMouth returns open shape (got "${mouthInsideWord}")`
);

// Test 4: word timing inactive: frame before any word -> resolvedSpeaking=false -> selectMouth returns "closed"
const frameBeforeWords = 10; // t = 10/30 = 0.333s, before 1.0
const isSpeakingBefore = resolvedSpeaking(false, frameBeforeWords, fps, words);
assert(isSpeakingBefore === false, "word timing inactive: frame before any word -> resolvedSpeaking=false");
assert(
  selectMouth(isSpeakingBefore, "neutral", frameBeforeWords, fps) === "closed",
  'word timing inactive: selectMouth returns "closed"'
);

// Test 5: selectMouth with speaking=false, expression="deadpan" -> "closed" (deadpan at rest = no special mouth override)
assert(
  selectMouth(false, "deadpan", 0, 30) === "closed",
  'deadpan at rest (speaking=false) -> "closed"'
);

// Test 6: skeptical at rest (speaking=false, expression="skeptical") -> "smirk"
assert(
  selectMouth(false, "skeptical", 0, 30) === "smirk",
  'skeptical at rest -> "smirk"'
);

// Test 7: flat_alarm at rest (speaking=false, expression="flat_alarm") -> "slightOpen"
assert(
  selectMouth(false, "flat_alarm", 0, 30) === "slightOpen",
  'flat_alarm at rest -> "slightOpen"'
);

// Test 8: case_closed at rest (speaking=false, expression="case_closed") -> "frown"
assert(
  selectMouth(false, "case_closed", 0, 30) === "frown",
  'case_closed at rest -> "frown"'
);

// Test 9: adjacent words with small gap < WORD_SLOP_SEC (0.05) — within slop, speaking stays true
// word1 ends at 1.5s, word2 starts at 2.0s => gap = 0.5s, well beyond slop
// But 0.05s after word1 ends is 1.55s => frame = Math.round(1.52*30) = 46 => within slop
const frameWithinSlop = 46; // t = 46/30 = 1.5333s, end + slop = 1.5 + 0.05 = 1.55s -> still within slop
const isSpeakingSlop = resolvedSpeaking(false, frameWithinSlop, fps, words);
assert(
  isSpeakingSlop === true,
  `frame within WORD_SLOP_SEC after word end -> still speaking (t=${(frameWithinSlop/fps).toFixed(3)}s, slop extends to 1.55s)`
);

// Gap beyond slop: frame = 52 => t = 52/30 = 1.733s, past slop boundary of 1.55s => not speaking
const frameInGap = 52; // t = 52/30 = 1.733s, gap > slop -> not speaking
const isSpeakingGap = resolvedSpeaking(false, frameInGap, fps, words);
assert(
  isSpeakingGap === false,
  `frame in gap beyond slop -> not speaking (t=${(frameInGap/fps).toFixed(3)}s)`
);

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
