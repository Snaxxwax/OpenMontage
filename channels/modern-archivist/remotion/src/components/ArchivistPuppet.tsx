import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { AnyPuppetManifest, CharacterCue, ColorState, LayoutState, LegacyPuppetManifest, WordTimestamp } from "../types";
import { puppetTransform } from "../styles";
import { resolvedSpeaking, selectMouth } from "./puppet/mouth";
import { resolveExpression } from "./puppet/expression";
import { PuppetRig } from "./puppet/PuppetRig";

const fallbackPuppet: LegacyPuppetManifest = {
  version: "1.0",
  character_id: "modern_archivist",
  display_name: "The Archivist",
  temporary: false,
  layers: {
    body: "modern-archivist/archivist-body.png",
    mug:  "modern-archivist/archivist-mug.png",
  },
  anchors: {
    mouth:     { x: 0.407, y: 0.538 },
    glasses:   { x: 0.51,  y: 0.452 },
    arm_pivot: { x: 0.62,  y: 0.74 },
  },
};

interface ArchivistPuppetProps {
  layout: LayoutState;
  speaking: boolean;
  sipping: boolean;
  puppet?: AnyPuppetManifest;
  cue?: CharacterCue;
  colorState?: ColorState;
  wordTimestamps?: WordTimestamp[];
  layoutChangedAtFrame?: number;
  sippingStartFrame?: number;
  debugPuppetStatic?: boolean;
  debugDisablePuppetMouth?: boolean;
  debugDisablePuppetFilters?: boolean;
}

export const ArchivistPuppet: React.FC<ArchivistPuppetProps> = ({
  layout,
  speaking,
  sipping,
  puppet = fallbackPuppet,
  cue = { visible: true, action: "idle", expression: "neutral" },
  colorState,
  wordTimestamps,
  layoutChangedAtFrame,
  sippingStartFrame,
  debugPuppetStatic,
  debugDisablePuppetMouth,
  debugDisablePuppetFilters,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fix C: Layout fade-in — Remotion spring replaces CSS opacity transition
  const puppetOpacity = spring({
    frame: frame - (layoutChangedAtFrame ?? 0),
    fps,
    config: { damping: 20, stiffness: 200 },
  });

  const activePuppet = puppet ?? fallbackPuppet;

  if (cue.visible === false) return null;

  const expression = cue.expression ?? "neutral";
  const expressionState = resolveExpression(colorState, layout, sipping, cue, frame, fps);
  const isSpeaking = resolvedSpeaking(speaking, frame, fps, wordTimestamps);
  const mouthShape = selectMouth(isSpeaking && !expressionState.deadpan, expression, frame, fps);

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "54%",
        width: 760,
        height: 760,
        background: "transparent",
        transform: puppetTransform[layout],
        transformOrigin: "center center",
        opacity: puppetOpacity,
        zIndex: 10,
        filter: expressionState.red
          ? "drop-shadow(0 0 32px rgba(255,0,0,0.75))"
          : "drop-shadow(0 24px 42px rgba(0,0,0,0.38))",
      }}
    >
      <PuppetRig
        manifest={activePuppet}
        expression={expressionState}
        mouthShape={mouthShape}
        isSpeaking={isSpeaking}
        sipping={sipping}
        sippingStartFrame={sippingStartFrame}
        debugPuppetStatic={debugPuppetStatic}
        debugDisablePuppetMouth={debugDisablePuppetMouth}
        debugDisablePuppetFilters={debugDisablePuppetFilters}
      />
    </div>
  );
};
