import React from "react";
import { useCurrentFrame } from "remotion";
import type { AnyPuppetManifest, PuppetActionTimeline, PuppetTimelineTrack } from "../../types";
import type { ExpressionState } from "./expression";
import type { MouthShape } from "./mouth";
import { PuppetRig } from "./PuppetRig";

interface PuppetTimelinePlayerProps {
  manifest: AnyPuppetManifest;
  timeline: PuppetActionTimeline;
  debugPuppetStatic?: boolean;
  debugDisablePuppetMouth?: boolean;
  debugDisablePuppetFilters?: boolean;
}

/** Return the last active track of a given type at the given time (highest `from` among active). */
function findActiveTrack(
  tracks: PuppetTimelineTrack[],
  type: PuppetTimelineTrack["type"],
  currentTime: number,
): PuppetTimelineTrack | undefined {
  let best: PuppetTimelineTrack | undefined;
  for (const t of tracks) {
    if (t.type !== type) continue;
    if (t.from <= currentTime && currentTime < t.to) {
      if (best === undefined || t.from > best.from) {
        best = t;
      }
    }
  }
  return best;
}

/** Map timeline mouth value (rig_spec name) to MouthShape. */
function mapMouthShape(value: string): MouthShape {
  switch (value) {
    case "closed": return "closed";
    case "rest":   return "slightOpen";
    case "aa":     return "openA";
    case "ee":     return "openE";
    case "oh":     return "openO";
    case "fv":     return "slightOpen";
    default:       return "closed";
  }
}

/** Map timeline expression value to ExpressionState (excluding actionSip — handled by action track). */
function mapExpression(value: string): Omit<ExpressionState, "actionSip"> {
  switch (value) {
    case "deadpan":
      return { red: false, deadpan: true, flash: false };
    case "alarm":
      return { red: true, deadpan: false, flash: false };
    case "neutral":
    case "skeptical":
    default:
      return { red: false, deadpan: false, flash: false };
  }
}

export const PuppetTimelinePlayer: React.FC<PuppetTimelinePlayerProps> = ({
  manifest,
  timeline,
  debugPuppetStatic,
  debugDisablePuppetMouth,
  debugDisablePuppetFilters,
}) => {
  const frame = useCurrentFrame();
  const currentTime = frame / timeline.fps;

  // Resolve active tracks
  const actionTrack     = findActiveTrack(timeline.tracks, "action",     currentTime);
  const expressionTrack = findActiveTrack(timeline.tracks, "expression", currentTime);
  const mouthTrack      = findActiveTrack(timeline.tracks, "mouth",      currentTime);

  // Action: mug_sip drives sipping + actionSip
  const isMugSip = actionTrack?.value === "mug_sip";
  const sipping  = isMugSip;
  const sippingStartFrame = isMugSip && actionTrack
    ? Math.round(actionTrack.from * timeline.fps)
    : undefined;

  // Expression: merge expression track + actionSip from action track
  const baseExpression = expressionTrack
    ? mapExpression(expressionTrack.value)
    : { red: false, deadpan: false, flash: false };

  const expression: ExpressionState = {
    ...baseExpression,
    actionSip: isMugSip,
  };

  // Mouth
  const mouthShape: MouthShape = mouthTrack ? mapMouthShape(mouthTrack.value) : "closed";
  const isSpeaking = mouthShape !== "closed";

  return (
    <PuppetRig
      manifest={manifest}
      expression={expression}
      mouthShape={mouthShape}
      isSpeaking={isSpeaking}
      sipping={sipping}
      sippingStartFrame={sippingStartFrame}
      debugPuppetStatic={debugPuppetStatic}
      debugDisablePuppetMouth={debugDisablePuppetMouth}
      debugDisablePuppetFilters={debugDisablePuppetFilters}
    />
  );
};
