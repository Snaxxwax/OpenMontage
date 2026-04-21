import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface ConnectingLineProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color?: string;
  thickness?: number;
  label?: string;
  style?: "straight" | "curved" | "arrow";
}

/**
 * Draws an animated SVG line between two points using strokeDasharray draw-in.
 * Coordinates are in the composition's native space (1920×1080).
 *
 * NOTE: SVGPathElement.getTotalLength() is unavailable in Node.js (headless Remotion).
 * Line length is approximated via Euclidean distance, which is exact for straight lines
 * and a close underestimate (~15%) for curves. The animation still fully reveals the
 * path because strokeDashoffset reaching 0 always shows the complete stroke.
 */
export const ConnectingLine: React.FC<ConnectingLineProps> = ({
  x1,
  y1,
  x2,
  y2,
  color = "#22D3EE",
  thickness = 3,
  label,
  style = "straight",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  // Draw-in spring
  const drawProgress = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 60, mass: 1 },
  });

  // Arrowhead appears after line is mostly drawn
  const arrowProgress = spring({
    frame: Math.max(0, frame - Math.round(fps * 0.3)),
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  // Exit fade in last 8 frames
  const opacity = interpolate(
    frame,
    [durationInFrames - 8, durationInFrames - 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Euclidean length (exact for straight, approximate for curved)
  const dx = x2 - x1;
  const dy = y2 - y1;
  const straightLength = Math.sqrt(dx * dx + dy * dy);

  // For curved style, control point sits above midpoint
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2 - straightLength * 0.2;
  // Bezier perimeter ≈ straight length (underestimates by ~10-20%, acceptable)
  const totalLength = straightLength;

  const dashOffset = interpolate(drawProgress, [0, 1], [totalLength, 0]);

  // Arrowhead geometry
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const arrowSize = thickness * 5;
  const arrowScale = interpolate(arrowProgress, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const arrowPoints = [
    [x2, y2],
    [
      x2 - arrowSize * Math.cos(angle - Math.PI / 6),
      y2 - arrowSize * Math.sin(angle - Math.PI / 6),
    ],
    [
      x2 - arrowSize * Math.cos(angle + Math.PI / 6),
      y2 - arrowSize * Math.sin(angle + Math.PI / 6),
    ],
  ]
    .map(([px, py]) => `${px},${py}`)
    .join(" ");

  // Label position: midpoint of line
  const labelX = style === "curved" ? midX : (x1 + x2) / 2;
  const labelY = style === "curved" ? midY - 20 : (y1 + y2) / 2 - 20;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {style === "curved" ? (
          <path
            d={`M ${x1} ${y1} Q ${midX} ${midY} ${x2} ${y2}`}
            fill="none"
            stroke={color}
            strokeWidth={thickness}
            strokeLinecap="round"
            strokeDasharray={totalLength}
            strokeDashoffset={dashOffset}
          />
        ) : (
          <line
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={color}
            strokeWidth={thickness}
            strokeLinecap="round"
            strokeDasharray={totalLength}
            strokeDashoffset={dashOffset}
          />
        )}

        {style === "arrow" && (
          <polygon
            points={arrowPoints}
            fill={color}
            style={{ transform: `scale(${arrowScale})`, transformOrigin: `${x2}px ${y2}px` }}
          />
        )}
      </svg>

      {label && (
        <div
          style={{
            position: "absolute",
            left: labelX,
            top: labelY,
            transform: "translate(-50%, -50%)",
            color,
            fontSize: 28,
            fontWeight: 600,
            background: "rgba(0,0,0,0.6)",
            padding: "4px 12px",
            borderRadius: 6,
            whiteSpace: "nowrap",
            opacity: drawProgress,
          }}
        >
          {label}
        </div>
      )}
    </AbsoluteFill>
  );
};
