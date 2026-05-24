import React from "react";
import { Img, useCurrentFrame, useVideoConfig } from "remotion";
import type { CharacterCue, ColorState, LayoutState, PuppetManifest } from "../types";
import { puppetTransform, resolveAsset } from "../styles";

// ─── Mouth asset map ──────────────────────────────────────────────────────────

const MOUTH_SRC = {
  closed:     "modern-archivist/mouth-closed.png",
  slightOpen: "modern-archivist/mouth-slight-open.png",
  openA:      "modern-archivist/mouth-open-a.png",
  openE:      "modern-archivist/mouth-open-e.png",
  openO:      "modern-archivist/mouth-open-o.png",
  smirk:      "modern-archivist/mouth-smirk.png",
  frown:      "modern-archivist/mouth-frown.png",
} as const;

type MouthShape = keyof typeof MOUTH_SRC;

export type WordTimestamp = { word: string; start: number; end: number };

// Phoneme cycle while speaking (~8 switches per second)
const SPEAK_CYCLE: MouthShape[] = ["openA", "openE", "openO", "slightOpen", "openA", "openO"];

// Pad word boundaries slightly so the mouth doesn't snap shut between words
const WORD_SLOP_SEC = 0.05;

function resolvedSpeaking(
  coarse: boolean,
  frame: number,
  fps: number,
  wordTimestamps?: WordTimestamp[],
): boolean {
  if (!wordTimestamps || wordTimestamps.length === 0) return coarse;
  const t = frame / fps;
  return wordTimestamps.some(w => t >= w.start - WORD_SLOP_SEC && t <= w.end + WORD_SLOP_SEC);
}

function selectMouth(speaking: boolean, expression: string, frame: number, fps: number): MouthShape {
  if (speaking) {
    return SPEAK_CYCLE[Math.floor((frame / fps) * 8) % SPEAK_CYCLE.length];
  }
  if (expression === "skeptical" || expression === "dry_disbelief" || expression === "dry_final") return "smirk";
  if (expression === "flat_alarm" || expression === "controlled_alarm") return "slightOpen";
  if (expression === "case_closed") return "frown";
  return "closed";
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

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

// ─── Component ────────────────────────────────────────────────────────────────

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

  if (cue.visible === false) return null;

  const mouthAnchor   = puppet.anchors.mouth     ?? { x: 0.51, y: 0.62 };
  const glassesAnchor = puppet.anchors.glasses   ?? { x: 0.50, y: 0.43 };

  const red       = colorState === "red" || layout === "STATE_CRITICAL_ERROR";
  const actionSip = sipping || cue.action === "sip_coffee";
  const deadpan   = cue.action === "deadpan_stare" || cue.expression === "deadpan";
  const flash     = cue.action === "glasses_flash" || (red && Math.sin((frame / fps) * 10) > 0.35);
  const expression = cue.expression ?? "neutral";

  const isSpeaking = resolvedSpeaking(speaking, frame, fps, wordTimestamps);
  const mouthShape = selectMouth(isSpeaking && !deadpan, expression, frame, fps);
  const mouthSrc   = MOUTH_SRC[mouthShape];

  const visorFill = flash
    ? "rgba(255,255,255,0.34)"
    : isSpeaking
    ? "rgba(246,244,234,0.20)"
    : "rgba(246,244,234,0.10)";

  // Mouth display dimensions — sized to match the portrait's face proportions
  const MOUTH_W = 148;
  const MOUTH_H = 72;

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
        filter: red
          ? "drop-shadow(0 0 32px rgba(255,0,0,0.75))"
          : "drop-shadow(0 24px 42px rgba(0,0,0,0.38))",
      }}
    >
      {/* Layer 1 — Body portrait */}
      <Img
        src={resolveAsset(puppet.layers.body)}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "contain",
          zIndex: 1,
        }}
      />

      {/* Layer 2 — Glasses (SVG for flash/color animation) */}
      <svg
        viewBox="0 0 200 90"
        style={{
          position: "absolute",
          left:  `${glassesAnchor.x * 100 - 15}%`,
          top:   `${glassesAnchor.y * 100 - 7}%`,
          width: "30%",
          height: "15%",
          zIndex: 2,
          overflow: "visible",
          filter: flash
            ? `drop-shadow(0 0 18px ${red ? "#FF3333" : "#00FFFF"})`
            : undefined,
        }}
      >
        <g
          fill="none"
          stroke={red ? "#FF3333" : "var(--accent)"}
          strokeWidth="7"
          strokeLinecap="round"
        >
          <rect x="8"   y="16" width="74" height="48" rx="18" />
          <rect x="118" y="16" width="74" height="48" rx="18" />
          <path d="M82 40 C98 30 104 30 118 40" />
          <path d="M8 36 L-20 24" />
          <path d="M192 36 L220 24" />
        </g>
        <g fill={visorFill}>
          <rect x="12"  y="20" width="66" height="40" rx="14" />
          <rect x="122" y="20" width="66" height="40" rx="14" />
        </g>
      </svg>

      {/* Layer 3 — Mouth phoneme PNG */}
      <Img
        src={resolveAsset(mouthSrc)}
        style={{
          position: "absolute",
          left:      `${mouthAnchor.x * 100}%`,
          top:       `${mouthAnchor.y * 100}%`,
          width:     MOUTH_W,
          height:    MOUTH_H,
          transform: "translate(-50%, -50%)",
          objectFit: "contain",
          zIndex: 3,
          opacity: actionSip ? 0 : 1,
          transition: "opacity 100ms ease",
          // Blend the cream-toned mouth assets into the dark portrait
          mixBlendMode: "screen",
          filter: red ? "hue-rotate(330deg) saturate(1.4)" : undefined,
        }}
      />

      {/* Layer 4 — Mug with sip pivot animation */}
      <div
        style={{
          position: "absolute",
          right: 92,
          bottom: 92,
          width: 180,
          height: 180,
          transformOrigin: "80% 85%",
          transform: actionSip
            ? "rotate(-28deg) translate(-44px, -58px)"
            : "rotate(8deg)",
          transition: "transform 450ms cubic-bezier(0.34, 1.56, 0.64, 1)",
          zIndex: 4,
        }}
      >
        {puppet.layers.mug ? (
          <Img
            src={resolveAsset(puppet.layers.mug)}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <div style={{ width: 120, height: 96, borderRadius: 18, border: "8px solid var(--accent)" }} />
        )}
      </div>
    </div>
  );
};
