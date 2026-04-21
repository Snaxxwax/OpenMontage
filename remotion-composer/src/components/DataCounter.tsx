import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface DataCounterProps {
  from?: number;
  to: number;
  suffix?: string;
  prefix?: string;
  color?: string;
  fontSize?: number;
  position?: { x: number; y: number };
  label?: string;
}

/**
 * Floating count-up overlay. Counts from `from` to `to` with a bouncy spring.
 * Usable at any position — standalone component, not tied to a grid layout.
 */
export const DataCounter: React.FC<DataCounterProps> = ({
  from = 0,
  to,
  suffix = "",
  prefix = "",
  color = "#F59E0B",
  fontSize = 120,
  position,
  label,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  // Count-up: slightly underdamped for a satisfying snap to the final value
  const progress = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 60, mass: 1 },
  });

  // Entrance scale bounce
  const scaleProgress = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80, mass: 1 },
  });
  const scale = interpolate(scaleProgress, [0, 1], [0.7, 1]);

  // Exit fade in last 10 frames
  const opacity = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames - 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const current = Math.round(interpolate(progress, [0, 1], [from, to]));
  const formatted = new Intl.NumberFormat("en-US").format(current);

  const centerX = position ? position.x : width / 2;
  const centerY = position ? position.y : height / 2;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      <div
        style={{
          position: "absolute",
          left: centerX,
          top: centerY,
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: "center center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize,
            fontWeight: 800,
            color,
            lineHeight: 1,
            fontVariantNumeric: "tabular-nums",
            letterSpacing: "-0.02em",
            textShadow: `0 0 40px ${color}66`,
          }}
        >
          {prefix}
          {formatted}
          {suffix}
        </div>
        {label && (
          <div
            style={{
              fontSize: fontSize * 0.3,
              fontWeight: 500,
              color: "#94A3B8",
              marginTop: fontSize * 0.1,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
            }}
          >
            {label}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
