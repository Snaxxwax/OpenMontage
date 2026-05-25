import { resolveExpression } from "./expression.js";
import type { ExpressionState } from "./expression.js";

let passed = 0;
let failed = 0;

function assert(condition: boolean, msg: string) {
  if (condition) { console.log(`  ✓ ${msg}`); passed++; }
  else { console.error(`  ✗ ${msg}`); failed++; }
}

// Test 1: default state -> all false
{
  const state: ExpressionState = resolveExpression(
    undefined,
    "STATE_MONOLOGUE",
    false,
    { action: "idle" },
    0,
    30,
  );
  assert(state.red === false,       "default: red=false");
  assert(state.actionSip === false, "default: actionSip=false");
  assert(state.deadpan === false,   "default: deadpan=false");
  assert(state.flash === false,     "default: flash=false");
}

// Test 2: colorState="red" -> red=true
{
  const state = resolveExpression("red", "STATE_MONOLOGUE", false, {}, 0, 30);
  assert(state.red === true, 'colorState="red" -> red=true');
}

// Test 3: layout="STATE_CRITICAL_ERROR" -> red=true
{
  const state = resolveExpression(undefined, "STATE_CRITICAL_ERROR", false, {}, 0, 30);
  assert(state.red === true, 'layout="STATE_CRITICAL_ERROR" -> red=true');
}

// Test 4: sipping=true -> actionSip=true
{
  const state = resolveExpression(undefined, "STATE_MONOLOGUE", true, {}, 0, 30);
  assert(state.actionSip === true, "sipping=true -> actionSip=true");
}

// Test 5: cue.action="sip_coffee" -> actionSip=true
{
  const state = resolveExpression(undefined, "STATE_MONOLOGUE", false, { action: "sip_coffee" }, 0, 30);
  assert(state.actionSip === true, 'cue.action="sip_coffee" -> actionSip=true');
}

// Test 6: cue.action="deadpan_stare" -> deadpan=true
{
  const state = resolveExpression(undefined, "STATE_MONOLOGUE", false, { action: "deadpan_stare" }, 0, 30);
  assert(state.deadpan === true, 'cue.action="deadpan_stare" -> deadpan=true');
}

// Test 7: cue.expression="deadpan" -> deadpan=true
{
  const state = resolveExpression(undefined, "STATE_MONOLOGUE", false, { expression: "deadpan" }, 0, 30);
  assert(state.deadpan === true, 'cue.expression="deadpan" -> deadpan=true');
}

// Test 8: cue.action="glasses_flash" -> flash=true
{
  const state = resolveExpression(undefined, "STATE_MONOLOGUE", false, { action: "glasses_flash" }, 0, 30);
  assert(state.flash === true, 'cue.action="glasses_flash" -> flash=true');
}

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
