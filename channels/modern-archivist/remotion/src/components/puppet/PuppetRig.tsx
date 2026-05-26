import React from "react";
import { Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { AnyPuppetManifest, LegacyPuppetManifest, PuppetLayerEntry } from "../../types";
import type { MouthShape } from "./mouth";
import type { ExpressionState } from "./expression";
import { MOUTH_SRC } from "./mouth";
import { DEFAULT_GLASSES_ANCHOR, DEFAULT_MOUTH_ANCHOR } from "./anchors";
import { PuppetLayer } from "./PuppetLayer";
import { resolveAsset } from "../../styles";
import {
  resolvePartAtFrame,
  toCssTransform,
  pivotToOrigin,
  type PartTransform,
  type Keyframe,
} from "../../lib/transformResolver";

// ─── Action library (keyframes for each named action) ────────────────────────
// Source of truth: channels/modern-archivist/assets/character/rig/action_library.json
// Mirrored here as typed constants to avoid JSON import config requirements.

const IDLE_KEYFRAMES: Keyframe[] = [
  { frame: 0, parts: { upper_arm_r: { rot: 0, tx: 0, ty: 0 }, forearm_r: { rot: 0, tx: 0, ty: 0 }, hand_r: { rot: 0, tx: 0, ty: 0 }, mug: { rot: 0, tx: 0, ty: 0 } } },
];

const MUG_SIP_KEYFRAMES: Keyframe[] = [
  { frame: 0,  parts: { upper_arm_r: { rot: 0,   tx: 0, ty: 0 }, forearm_r: { rot: 0,   tx: 0, ty: 0 }, hand_r: { rot: 0, tx: 0, ty: 0 }, mug: { rot: 0,  tx: 0,  ty: 0  } } },
  { frame: 18, parts: { upper_arm_r: { rot: -18, tx: 0, ty: 0 }, forearm_r: { rot: -42, tx: 0, ty: 0 }, hand_r: { rot: 0, tx: 0, ty: 0 }, mug: { rot: -8, tx: -4, ty: -4 } } },
  { frame: 30, parts: { upper_arm_r: { rot: -18, tx: 0, ty: 0 }, forearm_r: { rot: -42, tx: 0, ty: 0 }, hand_r: { rot: 0, tx: 0, ty: 0 }, mug: { rot: -8, tx: -4, ty: -4 } } },
  { frame: 42, parts: { upper_arm_r: { rot: 0,   tx: 0, ty: 0 }, forearm_r: { rot: 0,   tx: 0, ty: 0 }, hand_r: { rot: 0, tx: 0, ty: 0 }, mug: { rot: 0,  tx: 0,  ty: 0  } } },
];

const ZERO_TX: PartTransform = { rot: 0, tx: 0, ty: 0, sx: 1, sy: 1 };

// ─── Rig pivots (pixel coords in 1254×1254 canvas space) ─────────────────────
// Source of truth: channels/modern-archivist/assets/character/rig/rig_spec.json
const PIVOT = {
  shoulder:  [777, 928]  as [number, number], // upper_arm_r
  elbow:     [777, 1050] as [number, number], // forearm_r
  hand:      [777, 928]  as [number, number], // hand_r
  mug:       [627, 627]  as [number, number], // mug (canvas-centered)
  head:      [627, 903]  as [number, number], // head
  glasses:   [627, 539]  as [number, number], // glasses_frame
};

// ─── Mouth display dimensions ──────────────────────────────────────────────────
const MOUTH_W = 148;
const MOUTH_H = 72;

// ─── Helpers ───────────────────────────────────────────────────────────────────
const isLegacyManifest = (manifest: AnyPuppetManifest): manifest is LegacyPuppetManifest =>
  !Array.isArray(manifest.layers);

const findLayer = (manifest: AnyPuppetManifest, id: string): PuppetLayerEntry | undefined =>
  isLegacyManifest(manifest) ? undefined : manifest.layers.find((layer) => layer.id === id);

const legacyOrV2Src = (manifest: AnyPuppetManifest, legacyKey: "body" | "mug", v2Id: string): string | undefined => {
  if (isLegacyManifest(manifest)) return manifest.layers[legacyKey];
  return findLayer(manifest, v2Id)?.src;
};

const legacyAnchor = (
  manifest: AnyPuppetManifest,
  legacyKey: "mouth" | "glasses",
  v2Id: string,
  fallback: { x: number; y: number },
): { x: number; y: number } => {
  if (isLegacyManifest(manifest)) return manifest.anchors[legacyKey] ?? fallback;
  return findLayer(manifest, v2Id)?.anchor ?? fallback;
};

// ─── Component ────────────────────────────────────────────────────────────────

interface PuppetRigProps {
  manifest: AnyPuppetManifest;
  expression: ExpressionState;
  mouthShape: MouthShape;
  isSpeaking: boolean;
  sipping: boolean;
  sippingStartFrame?: number;
  debugPuppetStatic?: boolean;
  debugDisablePuppetMouth?: boolean;
  debugDisablePuppetFilters?: boolean;
}

export const PuppetRig: React.FC<PuppetRigProps> = ({
  manifest,
  expression,
  mouthShape: mouthShapeProp,
  isSpeaking: isSpeakingProp,
  sipping,
  sippingStartFrame,
  debugPuppetStatic,
  debugDisablePuppetMouth,
  debugDisablePuppetFilters,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const mouthShape: MouthShape = (debugPuppetStatic || debugDisablePuppetMouth) ? "closed" : mouthShapeProp;
  const isSpeaking = (debugPuppetStatic || debugDisablePuppetMouth) ? false : isSpeakingProp;

  const { red, flash } = expression;
  const actionSip = debugPuppetStatic ? false : expression.actionSip;

  // ── Arm group: keyframe-driven transforms via resolver ───────────────────────
  // Local frame within the active action, clamped so it doesn't overshoot.
  const actionKeyframes = actionSip ? MUG_SIP_KEYFRAMES : IDLE_KEYFRAMES;
  const localFrame = actionSip ? Math.max(0, frame - (sippingStartFrame ?? frame)) : 0;

  const upperArmTx  = actionSip ? resolvePartAtFrame("upper_arm_r", actionKeyframes, localFrame) : ZERO_TX;
  const forearmTx   = actionSip ? resolvePartAtFrame("forearm_r",   actionKeyframes, localFrame) : ZERO_TX;
  const handTx      = actionSip ? resolvePartAtFrame("hand_r",       actionKeyframes, localFrame) : ZERO_TX;
  const mugTx       = actionSip ? resolvePartAtFrame("mug",          actionKeyframes, localFrame) : ZERO_TX;

  // ── Mouth opacity fades during sip ───────────────────────────────────────────
  const mouthOpacity = interpolate(
    frame,
    [(sippingStartFrame ?? frame) - 1, (sippingStartFrame ?? frame) + 3],
    actionSip ? [1, 0] : [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const mouthAnchor  = legacyAnchor(manifest, "mouth", `mouth_${mouthShape === "closed" ? "closed" : mouthShape}`, DEFAULT_MOUTH_ANCHOR);
  const glassesAnchor = legacyAnchor(manifest, "glasses", "glasses_frame", DEFAULT_GLASSES_ANCHOR);
  const bodySrc    = legacyOrV2Src(manifest, "body", "body");
  const mugSrc     = legacyOrV2Src(manifest, "mug", "mug");
  const shadowSrc  = findLayer(manifest, "shadow")?.src;
  const armSrc     = findLayer(manifest, "arm_right_idle")?.src;
  const handMugSrc = findLayer(manifest, "hand_mug")?.src;
  const mouthSrc   = MOUTH_SRC[mouthShape];

  const visorFill = flash
    ? "rgba(255,255,255,0.34)"
    : isSpeaking
    ? "rgba(246,244,234,0.20)"
    : "rgba(246,244,234,0.10)";

  return (
    <>
      {/* z=0 — Shadow */}
      {shadowSrc && <PuppetLayer src={resolveAsset(shadowSrc)} zIndex={0} />}

      {/* z=1 — Body portrait */}
      {bodySrc && <PuppetLayer src={resolveAsset(bodySrc)} zIndex={1} />}

      {/* z=2 — Glasses (SVG, color-state-aware) */}
      <svg
        viewBox="0 0 200 90"
        style={{
          position: "absolute",
          left:   `${glassesAnchor.x * 100 - 15}%`,
          top:    `${glassesAnchor.y * 100 - 7}%`,
          width:  "30%",
          height: "15%",
          zIndex: 2,
          overflow: "visible",
          filter: debugDisablePuppetFilters
            ? undefined
            : flash
            ? `drop-shadow(0 0 18px ${red ? "#FF3333" : "#00FFFF"})`
            : undefined,
        }}
      >
        <g fill="none" stroke={red ? "#FF3333" : "var(--accent)"} strokeWidth="7" strokeLinecap="round">
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

      {/* z=3 — Mouth phoneme */}
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
          opacity: mouthOpacity,
          mixBlendMode: "screen",
          filter: red ? "hue-rotate(330deg) saturate(1.4)" : undefined,
        }}
      />

      {/*
       * z=10–12 — Arm group: parent-child nesting for correct pivot inheritance.
       *
       * DOM hierarchy mirrors rig_spec parent chain:
       *   upper_arm_r (shoulder pivot [777,928])
       *     └─ forearm_r (elbow pivot [777,1050])
       *           ├─ mug        (z=1 within group, canvas-centered pivot)
       *           └─ hand_r     (z=2 within group, hand pivot)
       *
       * Each child's transform-origin is in its parent's post-rotation space,
       * which is exactly what CSS nested transforms provide.
       */}
      {armSrc && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            transformOrigin: pivotToOrigin(PIVOT.shoulder),
            transform: toCssTransform(upperArmTx),
            zIndex: 10,
          }}
        >
          {/* Arm layer fills the wrapper in canvas-registered space */}
          <PuppetLayer src={resolveAsset(armSrc)} />

          {/* Forearm sub-group rotates around elbow pivot */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              transformOrigin: pivotToOrigin(PIVOT.elbow),
              transform: toCssTransform(forearmTx),
            }}
          >
            {/* Mug: z=1 within forearm group (behind hand) */}
            {mugSrc && (
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                  transformOrigin: pivotToOrigin(PIVOT.mug),
                  transform: toCssTransform(mugTx),
                  zIndex: 1,
                }}
              >
                <PuppetLayer src={resolveAsset(mugSrc)} />
              </div>
            )}

            {/* Hand: z=2 within forearm group (in front of mug) */}
            {handMugSrc && (
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                  transformOrigin: pivotToOrigin(PIVOT.hand),
                  transform: toCssTransform(handTx),
                  zIndex: 2,
                }}
              >
                <PuppetLayer src={resolveAsset(handMugSrc)} />
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
