import React from "react";
import { Img } from "remotion";
import type { LayoutState, PuppetManifest } from "../types";
import { puppetTransform, resolveAsset } from "../styles";

interface ArchivistPuppetProps {
  layout: LayoutState;
  speaking: boolean;
  sipping: boolean;
  puppet?: PuppetManifest;
}

const fallbackPuppet: PuppetManifest = {
  version: "1.0",
  character_id: "modern_archivist",
  display_name: "The Archivist",
  temporary: true,
  layers: {
    body: "modern-archivist/archivist-body.png",
    mug: "modern-archivist/archivist-mug.png",
  },
  anchors: {
    mouth: { x: 0.51, y: 0.62 },
    glasses: { x: 0.5, y: 0.43 },
    arm_pivot: { x: 0.62, y: 0.74 },
  },
};

export const ArchivistPuppet: React.FC<ArchivistPuppetProps> = ({
  layout,
  speaking,
  sipping,
  puppet = fallbackPuppet,
}) => {
  const mouth = puppet.anchors.mouth ?? { x: 0.51, y: 0.62 };
  const glasses = puppet.anchors.glasses ?? { x: 0.5, y: 0.43 };

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "54%",
        width: 760,
        height: 760,
        transform: puppetTransform[layout],
        transformOrigin: "center center",
        transition: "transform 600ms cubic-bezier(0.22, 1, 0.36, 1)",
        zIndex: 10,
        filter: layout === "STATE_CRITICAL_ERROR" ? "drop-shadow(0 0 32px rgba(255,0,0,0.75))" : "drop-shadow(0 24px 42px rgba(0,0,0,0.38))",
      }}
    >
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

      <svg
        viewBox="0 0 200 90"
        style={{
          position: "absolute",
          left: `${glasses.x * 100 - 15}%`,
          top: `${glasses.y * 100 - 7}%`,
          width: "30%",
          height: "15%",
          zIndex: 2,
          overflow: "visible",
        }}
      >
        <g fill="none" stroke="var(--accent)" strokeWidth="7" strokeLinecap="round">
          <rect x="8" y="16" width="74" height="48" rx="18" />
          <rect x="118" y="16" width="74" height="48" rx="18" />
          <path d="M82 40 C98 30 104 30 118 40" />
          <path d="M8 36 L-20 24" />
          <path d="M192 36 L220 24" />
        </g>
        <g fill="rgba(246,244,234,0.10)">
          <rect x="12" y="20" width="66" height="40" rx="14" />
          <rect x="122" y="20" width="66" height="40" rx="14" />
        </g>
      </svg>

      <div
        style={{
          position: "absolute",
          left: `${mouth.x * 100}%`,
          top: `${mouth.y * 100}%`,
          width: speaking ? 46 : 54,
          height: speaking ? 34 : 11,
          marginLeft: -23,
          borderRadius: speaking ? "50%" : 999,
          background: speaking ? "#241116" : "#1A1014",
          border: "3px solid rgba(246,244,234,0.72)",
          transform: speaking ? "scaleY(1)" : "scaleY(0.55)",
          transition: "width 80ms linear, height 80ms linear, transform 80ms linear",
          zIndex: 3,
        }}
      />

      <div
        style={{
          position: "absolute",
          right: 92,
          bottom: 92,
          width: 180,
          height: 180,
          transformOrigin: "80% 85%",
          transform: sipping ? "rotate(-28deg) translate(-44px, -58px)" : "rotate(8deg)",
          transition: "transform 450ms cubic-bezier(0.34, 1.56, 0.64, 1)",
          zIndex: 4,
        }}
      >
        {puppet.layers.mug ? (
          <Img src={resolveAsset(puppet.layers.mug)} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
        ) : (
          <div style={{ width: 120, height: 96, borderRadius: 18, border: "8px solid var(--accent)" }} />
        )}
      </div>
    </div>
  );
};
