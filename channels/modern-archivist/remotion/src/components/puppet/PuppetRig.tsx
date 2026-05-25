import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { AnyPuppetManifest, LegacyPuppetManifest, PuppetLayerEntry } from "../../types";
import type { MouthShape } from "./mouth";
import type { ExpressionState } from "./expression";
import { MOUTH_SRC } from "./mouth";
import { DEFAULT_GLASSES_ANCHOR, DEFAULT_MOUTH_ANCHOR } from "./anchors";
import { PuppetLayer } from "./PuppetLayer";
import { resolveAsset } from "../../styles";

// Mouth display dimensions — sized to match the portrait's face proportions
const MOUTH_W = 148;
const MOUTH_H = 72;

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

  // Fix A: Mug sip animation — Remotion spring replaces CSS transition
  const sipProgress = actionSip
    ? spring({ frame: frame - (sippingStartFrame ?? frame), fps, config: { damping: 12, stiffness: 180, mass: 0.8 } })
    : spring({ frame: (sippingStartFrame ?? 0) + 15 - frame, fps, config: { damping: 14, stiffness: 120, mass: 0.6 } });

  const mugRotate     = interpolate(sipProgress, [0, 1], [8, -28]);
  const mugTranslateX = interpolate(sipProgress, [0, 1], [0, -44]);
  const mugTranslateY = interpolate(sipProgress, [0, 1], [0, -58]);

  // Fix B: Mouth opacity — 3-frame interpolate replaces CSS transition
  const mouthOpacity = interpolate(
    frame,
    [
      (sippingStartFrame ?? frame) - 1,
      (sippingStartFrame ?? frame) + 3,
    ],
    actionSip ? [1, 0] : [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const mouthAnchor = legacyAnchor(manifest, "mouth", `mouth_${mouthShape === "closed" ? "closed" : mouthShape}`, DEFAULT_MOUTH_ANCHOR);
  const glassesAnchor = legacyAnchor(manifest, "glasses", "glasses_frame", DEFAULT_GLASSES_ANCHOR);
  const bodySrc = legacyOrV2Src(manifest, "body", "body");
  const mugSrc = legacyOrV2Src(manifest, "mug", "mug");

  const mouthSrc = MOUTH_SRC[mouthShape];

  const visorFill = flash
    ? "rgba(255,255,255,0.34)"
    : isSpeaking
    ? "rgba(246,244,234,0.20)"
    : "rgba(246,244,234,0.10)";

  return (
    <>
      {/* Layer 1 — Body portrait */}
      {bodySrc ? <PuppetLayer src={resolveAsset(bodySrc)} zIndex={1} /> : null}

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
          filter: debugDisablePuppetFilters
            ? undefined
            : flash
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
          opacity: mouthOpacity,
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
          transform: `rotate(${mugRotate}deg) translate(${mugTranslateX}px, ${mugTranslateY}px)`,
          zIndex: 4,
        }}
      >
        {mugSrc ? (
          <Img
            src={resolveAsset(mugSrc)}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <div style={{ width: 120, height: 96, borderRadius: 18, border: "8px solid var(--accent)" }} />
        )}
      </div>
    </>
  );
};
