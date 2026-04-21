import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface KineticHighlightProps {
  text?: string;
  color?: string;
  style?: "box" | "underline" | "circle";
  thickness?: number;
  position?: { x: number; y: number; width: number; height: number };
  fontSize?: number;
  fontWeight?: number;
}

/**
 * Draws an animated highlight shape (box, underline, or circle) over a region.
 * Uses SVG strokeDasharray draw-in driven by spring() for a kinetic feel.
 * Designed as a transparent overlay — use inside a <Sequence> timed to a beat.
 */
export const KineticHighlight: React.FC<KineticHighlightProps> = ({
  text,
  color = "#22D3EE",
  style = "underline",
  thickness = 4,
  position,
  fontSize = 64,
  fontWeight = 700,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  // Default position: centered region
  const pos = position ?? {
    x: width * 0.15,
    y: height * 0.4,
    width: width * 0.7,
    height: fontSize * 1.4,
  };

  // Draw-in spring: drives strokeDashoffset from totalLength → 0
  const drawProgress = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 60, mass: 1 },
  });

  // Exit: fade out in last 8 frames
  const opacity = interpolate(
    frame,
    [durationInFrames - 8, durationInFrames - 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Text entrance scale
  const textScale = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });
  const textOpacity = interpolate(frame, [0, 4], [0, 1], {
    extrapolateRight: "clamp",
  });

  const renderShape = () => {
    if (style === "underline") {
      const lineY = pos.y + pos.height;
      const totalLength = pos.width;
      const dashOffset = interpolate(drawProgress, [0, 1], [totalLength, 0]);
      return (
        <line
          x1={pos.x}
          y1={lineY}
          x2={pos.x + pos.width}
          y2={lineY}
          stroke={color}
          strokeWidth={thickness}
          strokeLinecap="round"
          strokeDasharray={totalLength}
          strokeDashoffset={dashOffset}
        />
      );
    }

    if (style === "box") {
      const rx = pos.width * drawProgress;
      const ry = pos.height * drawProgress;
      return (
        <rect
          x={pos.x}
          y={pos.y}
          width={rx}
          height={ry}
          fill="none"
          stroke={color}
          strokeWidth={thickness}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      );
    }

    if (style === "circle") {
      const cx = pos.x + pos.width / 2;
      const cy = pos.y + pos.height / 2;
      const rx = (pos.width / 2) * 1.1;
      const ry = (pos.height / 2) * 1.2;
      // Approximate perimeter using Ramanujan's formula
      const totalLength = Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)));
      const dashOffset = interpolate(drawProgress, [0, 1], [totalLength, 0]);
      return (
        <ellipse
          cx={cx}
          cy={cy}
          rx={rx}
          ry={ry}
          fill="none"
          stroke={color}
          strokeWidth={thickness}
          strokeLinecap="round"
          strokeDasharray={totalLength}
          strokeDashoffset={dashOffset}
        />
      );
    }

    return null;
  };

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {renderShape()}
      </svg>
      {text && (
        <div
          style={{
            position: "absolute",
            left: pos.x,
            top: pos.y,
            width: pos.width,
            height: pos.height,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize,
            fontWeight,
            color,
            transform: `scale(${textScale})`,
            transformOrigin: "center center",
            opacity: textOpacity,
            whiteSpace: "nowrap",
          }}
        >
          {text}
        </div>
      )}
    </AbsoluteFill>
  );
};
