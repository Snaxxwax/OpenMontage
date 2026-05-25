import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { CharacterCue, ColorState, LayoutState, PuppetManifest, WordTimestamp } from "../types";
import { puppetTransform } from "../styles";
import { resolvedSpeaking, selectMouth } from "./puppet/mouth";
import { resolveExpression } from "./puppet/expression";
import { PuppetRig } from "./puppet/PuppetRig";

const fallbackPuppet: PuppetManifest = {
  version: "1.0",
  character_id: "modern_archivist",
  display_name: "The Archivist",
  temporary: false,
  layers: {
    body: "modern-archivist/archivist-body.png",
    mug:  "modern-archivist/archivist-mug.png",
  },
  anchors: {
    mouth:     { x: 0.51, y: 0.62 },
    glasses:   { x: 0.50, y: 0.43 },
    arm_pivot: { x: 0.62, y: 0.74 },
  },
};

interface ArchivistPuppetProps {
  layout: LayoutState;
  speaking: boolean;
  sipping: boolean;
  puppet?: PuppetManifest;
  cue?: CharacterCue;
  colorState?: ColorState;
  wordTimestamps?: WordTimestamp[];
}

export const ArchivistPuppet: React.FC<ArchivistPuppetProps> = ({
  layout,
  speaking,
  sipping,
  puppet = fallbackPuppet,
  cue = { visible: true, action: "idle", expression: "neutral" },
  colorState,
  wordTimestamps,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

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
        transition: "transform 600ms cubic-bezier(0.22, 1, 0.36, 1), opacity 260ms ease",
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
        expressionName={expression}
        sipping={sipping}
      />
    </div>
  );
};
