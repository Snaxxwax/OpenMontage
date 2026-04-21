import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type CameraMotion =
  | "ken-burns"
  | "pan-left"
  | "pan-right"
  | "zoom-in"
  | "zoom-out"
  | "parallax";

const ANIMATION_CYCLE: CameraMotion[] = [
  "ken-burns",
  "pan-left",
  "pan-right",
  "zoom-out",
  "zoom-in",
  "parallax",
];

export interface ContinuousCameraProps {
  sceneIndex: number;
  children: React.ReactNode;
  overrideAnimation?: CameraMotion;
}

/**
 * HOC wrapper that guarantees continuous pixel motion for any child element.
 * Cycles through animation types based on sceneIndex so no two adjacent scenes
 * use the same motion without explicit override.
 *
 * Only applied when cut.continuous_camera === true in edit_decisions.
 * Existing cuts without this flag are not affected.
 *
 * The wrapper applies a CSS transform to a container div with overflow:hidden.
 * If the child already has its own transform (e.g., ImageScene), use
 * overrideAnimation to pass the desired motion to the child instead and
 * disable ContinuousCamera's own transform to prevent double-scaling.
 */
export const ContinuousCamera: React.FC<ContinuousCameraProps> = ({
  sceneIndex,
  children,
  overrideAnimation,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const animation = overrideAnimation ?? ANIMATION_CYCLE[sceneIndex % ANIMATION_CYCLE.length];
  const progress = durationInFrames > 1 ? frame / (durationInFrames - 1) : 0;

  let transform = "none";

  switch (animation) {
    case "ken-burns":
      // Slow diagonal zoom + drift — the classic documentary motion
      {
        const scale = 1 + progress * 0.12;
        const tx = interpolate(progress, [0, 1], [0, -18]);
        const ty = interpolate(progress, [0, 1], [0, -12]);
        transform = `scale(${scale}) translate(${tx}px, ${ty}px)`;
      }
      break;

    case "pan-left":
      {
        const scale = 1.08;
        const tx = interpolate(progress, [0, 1], [30, -30]);
        transform = `scale(${scale}) translateX(${tx}px)`;
      }
      break;

    case "pan-right":
      {
        const scale = 1.08;
        const tx = interpolate(progress, [0, 1], [-30, 30]);
        transform = `scale(${scale}) translateX(${tx}px)`;
      }
      break;

    case "zoom-in":
      {
        const scale = interpolate(progress, [0, 1], [1, 1.14]);
        transform = `scale(${scale})`;
      }
      break;

    case "zoom-out":
      {
        const scale = interpolate(progress, [0, 1], [1.14, 1]);
        transform = `scale(${scale})`;
      }
      break;

    case "parallax":
      {
        const scale = 1.1;
        const ty = interpolate(progress, [0, 1], [12, -12]);
        transform = `scale(${scale}) translateY(${ty}px)`;
      }
      break;
  }

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          transform,
          transformOrigin: "center center",
          willChange: "transform",
        }}
      >
        {children}
      </div>
    </div>
  );
};
