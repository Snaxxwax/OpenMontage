import type { ColorState, LayoutState } from "../../types";

export interface ExpressionState {
  red: boolean;
  actionSip: boolean;
  deadpan: boolean;
  flash: boolean;
}

export function resolveExpression(
  colorState: ColorState | undefined,
  layout: LayoutState,
  sipping: boolean,
  cue: { action?: string; expression?: string },
  frame: number,
  fps: number,
): ExpressionState {
  const red       = colorState === "red" || layout === "STATE_CRITICAL_ERROR";
  const actionSip = sipping || cue.action === "sip_coffee";
  const deadpan   = cue.action === "deadpan_stare" || cue.expression === "deadpan";
  const flash     = cue.action === "glasses_flash" || (red && Math.sin((frame / fps) * 10) > 0.35);
  return { red, actionSip, deadpan, flash };
}
