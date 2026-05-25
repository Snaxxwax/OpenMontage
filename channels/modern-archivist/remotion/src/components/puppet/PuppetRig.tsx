import React from "react";
import { Img } from "remotion";
import type { PuppetManifest } from "../../types";
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
  manifest: PuppetManifest;
  expression: ExpressionState;
  mouthShape: MouthShape;
  isSpeaking: boolean;
  sipping: boolean;
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
  debugPuppetStatic,
  debugDisablePuppetMouth,
  debugDisablePuppetFilters,
}) => {
  const mouthShape: MouthShape = (debugPuppetStatic || debugDisablePuppetMouth) ? "closed" : mouthShapeProp;
  const isSpeaking = (debugPuppetStatic || debugDisablePuppetMouth) ? false : isSpeakingProp;

  const { red, flash } = expression;
  const actionSip = debugPuppetStatic ? false : expression.actionSip;

  const mouthAnchor   = manifest.anchors.mouth   ?? DEFAULT_MOUTH_ANCHOR;
  const glassesAnchor = manifest.anchors.glasses  ?? DEFAULT_GLASSES_ANCHOR;

  const mouthSrc = MOUTH_SRC[mouthShape];

  const visorFill = flash
    ? "rgba(255,255,255,0.34)"
    : isSpeaking
    ? "rgba(246,244,234,0.20)"
    : "rgba(246,244,234,0.10)";

  return (
    <>
      {/* Layer 1 — Body portrait */}
      <PuppetLayer src={resolveAsset(manifest.layers.body)} zIndex={1} />

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
        {manifest.layers.mug ? (
          <Img
            src={resolveAsset(manifest.layers.mug)}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <div style={{ width: 120, height: 96, borderRadius: 18, border: "8px solid var(--accent)" }} />
        )}
      </div>
    </>
  );
};
