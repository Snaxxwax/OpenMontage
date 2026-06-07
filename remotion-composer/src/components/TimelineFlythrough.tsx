import React, { CSSProperties, memo, useMemo } from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const BRAND = {
  teal: "#00D4AA",
  charcoal: "#1A1A2E",
  bone: "#F5F0E1",
  grey: "#6B7280",
  criticalRed: "#DC2626",
};

export type TimelineEvent = {
  id: string;
  title: string;
  date: string;
  description: string;
  zPosition: number;
  side?: "left" | "right";
  importance?: "normal" | "critical";
  evidenceLabel?: string;
  evidenceSource?: string;
  connectionLabel?: string;
};

export type TimelineFlythroughProps = {
  events: TimelineEvent[];
  flySpeed?: number;
  pauseDuration?: number;
  orbitOnPause?: boolean;
  title?: string;
  subtitle?: string;
  accentColor?: string;
  backgroundColor?: string;
};

type EventTiming = {
  event: TimelineEvent;
  approachStartFrame: number;
  hitFrame: number;
  pauseEndFrame: number;
  x: number;
  y: number;
};

const APPROACH_DISTANCE = 50;
const STRING_DRAW_SECONDS = 0.5;

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const getSortedEvents = (events: TimelineEvent[]) =>
  [...events].sort((a, b) => b.zPosition - a.zPosition);

const getEventProgress = (frame: number, hitFrame: number, fps: number) =>
  clamp01(
    interpolate(frame, [hitFrame - 0.18 * fps, hitFrame + 0.42 * fps], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    })
  );

const getCameraZ = (
  timings: EventTiming[],
  frame: number,
  fps: number,
  flySpeed: number
) => {
  if (timings.length === 0) {
    return 1000 - (frame / fps) * flySpeed;
  }

  const first = timings[0];

  if (frame <= first.hitFrame) {
    return 1000 - (frame / fps) * flySpeed;
  }

  for (let index = 0; index < timings.length; index += 1) {
    const current = timings[index];
    const next = timings[index + 1];

    if (frame <= current.pauseEndFrame) {
      return current.event.zPosition;
    }

    if (!next) {
      return current.event.zPosition;
    }

    if (frame <= next.hitFrame) {
      const travelFrame = frame - current.pauseEndFrame;
      return current.event.zPosition - (travelFrame / fps) * flySpeed;
    }
  }

  const last = timings[timings.length - 1];
  return last.event.zPosition - (Math.max(0, frame - last.pauseEndFrame) / fps) * flySpeed;
};

const buildTimings = (
  events: TimelineEvent[],
  fps: number,
  flySpeed: number,
  pauseDuration: number
): EventTiming[] => {
  const pauseFrames = pauseDuration * fps;
  let carriedPauseFrames = 0;

  return getSortedEvents(events).map((event, index) => {
    const baseHitFrame = ((1000 - event.zPosition) / flySpeed) * fps;
    const hitFrame = baseHitFrame + carriedPauseFrames;
    const pauseEndFrame = hitFrame + pauseFrames;
    carriedPauseFrames += pauseFrames;

    const sideMultiplier = event.side === "right" ? 1 : event.side === "left" ? -1 : index % 2 === 0 ? -1 : 1;

    return {
      event,
      approachStartFrame: hitFrame - (APPROACH_DISTANCE / flySpeed) * fps,
      hitFrame,
      pauseEndFrame,
      x: sideMultiplier * (260 + (index % 3) * 58),
      y: ((index % 4) - 1.5) * 58,
    };
  });
};

const starBackground = (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity: 0.42,
      backgroundImage:
        "radial-gradient(circle at 12% 18%, rgba(245,240,225,0.55) 0 1px, transparent 1.5px), radial-gradient(circle at 72% 12%, rgba(0,212,170,0.46) 0 1px, transparent 1.5px), radial-gradient(circle at 88% 68%, rgba(245,240,225,0.38) 0 1px, transparent 1.5px), radial-gradient(circle at 24% 74%, rgba(245,240,225,0.32) 0 1px, transparent 1.5px), radial-gradient(circle at 54% 48%, rgba(255,255,255,0.22) 0 1px, transparent 1.5px)",
      backgroundSize: "420px 310px, 520px 390px, 470px 360px, 610px 460px, 360px 280px",
    }}
  />
);

export const TimelineFlythrough: React.FC<TimelineFlythroughProps> = memo(
  ({
    events,
    flySpeed = 260,
    pauseDuration = 2.2,
    orbitOnPause = true,
    title = "FAILURE LEDGER",
    subtitle = "A TIMELINE OF CONFIDENCE COLLAPSING INTO EVIDENCE",
    accentColor = BRAND.teal,
    backgroundColor = BRAND.charcoal,
  }) => {
    const frame = useCurrentFrame();
    const { fps, width, height, durationInFrames } = useVideoConfig();
    const timings = useMemo(
      () => buildTimings(events, fps, flySpeed, pauseDuration),
      [events, flySpeed, fps, pauseDuration]
    );
    const cameraZ = getCameraZ(timings, frame, fps, flySpeed);
    const activeTiming =
      timings.find((timing) => frame >= timing.hitFrame && frame <= timing.pauseEndFrame) ??
      null;
    const activePauseProgress = activeTiming
      ? clamp01((frame - activeTiming.hitFrame) / (pauseDuration * fps))
      : 0;
    const activeOrbit = activeTiming && orbitOnPause ? activePauseProgress * 360 : 0;
    const introOpacity = interpolate(frame, [0, fps * 0.5, fps * 2.2], [0, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
    const fadeToBlack = interpolate(
      frame,
      [durationInFrames - fps * 1.5, durationInFrames],
      [0, 1],
      {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }
    );
    const sceneStyle: CSSProperties = {
      position: "absolute",
      left: "50%",
      top: "50%",
      width: 1,
      height: 1,
      transformStyle: "preserve-3d",
      transform: `translate3d(-50%, -50%, ${-cameraZ}px) rotateY(${-activeOrbit}deg)`,
    };

    return (
      <AbsoluteFill
        style={{
          overflow: "hidden",
          backgroundColor,
          backgroundImage:
            "radial-gradient(circle at 50% 42%, rgba(0, 212, 170, 0.16), transparent 24%), radial-gradient(circle at 50% 54%, #25253d 0%, #10101d 46%, #030306 100%)",
          color: BRAND.bone,
          fontFamily: "Inter, Helvetica, Arial, sans-serif",
          letterSpacing: 0,
          perspective: 1200,
        }}
      >
        {starBackground}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(90deg, rgba(0,0,0,0.62), transparent 24%, transparent 76%, rgba(0,0,0,0.62)), radial-gradient(circle at center, transparent 50%, rgba(0,0,0,0.54))",
          }}
        />

        <div style={sceneStyle}>
          <svg
            width={width}
            height={height}
            viewBox={`${-width / 2} ${-height / 2} ${width} ${height}`}
            style={{
              position: "absolute",
              left: -width / 2,
              top: -height / 2,
              overflow: "visible",
              transformStyle: "preserve-3d",
            }}
          >
            {timings.slice(1).map((timing, index) => {
              const previous = timings[index];
              const drawProgress = interpolate(
                frame,
                [
                  timing.approachStartFrame,
                  timing.approachStartFrame + STRING_DRAW_SECONDS * fps,
                ],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.out(Easing.cubic),
                }
              );
              const pathLength = Math.hypot(timing.x - previous.x, timing.y - previous.y) + 320;
              const path = `M ${previous.x} ${previous.y} C ${previous.x * 0.35} ${previous.y - 120}, ${timing.x * 0.35} ${timing.y + 120}, ${timing.x} ${timing.y}`;
              const labelOpacity = interpolate(
                frame,
                [timing.hitFrame + 0.16 * fps, timing.hitFrame + 0.48 * fps],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }
              );
              const midX = (previous.x + timing.x) / 2;
              const midY = (previous.y + timing.y) / 2;

              return (
                <g key={`${previous.event.id}-${timing.event.id}`}>
                  <path
                    d={path}
                    fill="none"
                    stroke={BRAND.criticalRed}
                    strokeWidth={4}
                    strokeLinecap="round"
                    strokeDasharray={pathLength}
                    strokeDashoffset={pathLength * (1 - drawProgress)}
                    opacity={0.82}
                    style={{
                      filter: "drop-shadow(0 0 10px rgba(220,38,38,0.56))",
                    }}
                  />
                  <text
                    x={midX}
                    y={midY - 20}
                    fill={BRAND.bone}
                    fontSize={18}
                    fontWeight={700}
                    textAnchor="middle"
                    opacity={labelOpacity}
                    style={{
                      paintOrder: "stroke",
                      stroke: "rgba(0,0,0,0.72)",
                      strokeWidth: 6,
                    }}
                  >
                    {timing.event.connectionLabel ?? "escalates"}
                  </text>
                </g>
              );
            })}
          </svg>

          {timings.map((timing) => {
            const { event } = timing;
            const hitProgress = getEventProgress(frame, timing.hitFrame, fps);
            const approachProgress = interpolate(
              frame,
              [timing.approachStartFrame, timing.hitFrame],
              [0, 1],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.out(Easing.cubic),
              }
            );
            const pulse = 1 + Math.sin(frame * 0.38) * 0.16 * approachProgress;
            const isCritical = event.importance === "critical";
            const evidenceScale = spring({
              frame: frame - timing.hitFrame,
              fps,
              durationInFrames: 0.62 * fps,
              config: { damping: 18, stiffness: 92, mass: 0.9 },
            });
            const textOpacity = interpolate(
              frame,
              [timing.hitFrame + 0.34 * fps, timing.hitFrame + 0.78 * fps],
              [0, 1],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }
            );
            const descriptionOpacity = interpolate(
              frame,
              [timing.hitFrame + 0.58 * fps, timing.hitFrame + 1.02 * fps],
              [0, 1],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }
            );

            return (
              <div
                key={event.id}
                style={{
                  position: "absolute",
                  left: timing.x,
                  top: timing.y,
                  width: 1,
                  height: 1,
                  transformStyle: "preserve-3d",
                  transform: `translateZ(${event.zPosition}px)`,
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    left: -22,
                    top: -22,
                    width: 44,
                    height: 44,
                    clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
                    backgroundColor: isCritical ? BRAND.criticalRed : accentColor,
                    transform: `scale(${pulse})`,
                    boxShadow: `0 0 24px ${isCritical ? BRAND.criticalRed : accentColor}`,
                    opacity: interpolate(approachProgress, [0, 0.24, 1], [0.45, 0.85, 1]),
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: -74,
                    top: -74,
                    width: 148,
                    height: 148,
                    border: `1px solid ${isCritical ? BRAND.criticalRed : accentColor}`,
                    borderRadius: "50%",
                    opacity: approachProgress * 0.45,
                    transform: `scale(${0.65 + approachProgress * 0.65})`,
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: event.side === "right" ? 64 : -424,
                    top: -118,
                    width: 360,
                    minHeight: 236,
                    padding: "22px 24px",
                    border: `1px solid rgba(245,240,225,${0.12 + hitProgress * 0.28})`,
                    background:
                      "linear-gradient(135deg, rgba(26,26,46,0.94), rgba(5,5,10,0.9))",
                    boxShadow:
                      "0 28px 64px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.04)",
                    transform: `scale(${interpolate(evidenceScale, [0, 1], [0.72, 1])}) translateY(${interpolate(hitProgress, [0, 1], [18, 0])}px)`,
                    transformOrigin: event.side === "right" ? "left center" : "right center",
                    opacity: hitProgress,
                  }}
                >
                  <div
                    style={{
                      height: 86,
                      marginBottom: 18,
                      border: `1px solid ${isCritical ? BRAND.criticalRed : accentColor}66`,
                      background:
                        "repeating-linear-gradient(0deg, rgba(245,240,225,0.08), rgba(245,240,225,0.08) 1px, transparent 1px, transparent 9px), linear-gradient(135deg, rgba(0,212,170,0.16), rgba(220,38,38,0.12))",
                      position: "relative",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        left: 18,
                        top: 18,
                        width: 52,
                        height: 52,
                        border: `2px solid ${isCritical ? BRAND.criticalRed : accentColor}`,
                        transform: "rotate(45deg)",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        right: 18,
                        bottom: 14,
                        color: BRAND.bone,
                        fontSize: 14,
                        fontWeight: 800,
                        textTransform: "uppercase",
                      }}
                    >
                      {event.evidenceLabel ?? "Evidence"}
                    </div>
                  </div>
                  <div
                    style={{
                      color: isCritical ? BRAND.criticalRed : accentColor,
                      fontSize: 16,
                      fontWeight: 800,
                      textTransform: "uppercase",
                      opacity: textOpacity,
                    }}
                  >
                    {event.date}
                  </div>
                  <div
                    style={{
                      marginTop: 8,
                      color: BRAND.bone,
                      fontSize: 30,
                      lineHeight: 1.04,
                      fontWeight: 850,
                      opacity: textOpacity,
                    }}
                  >
                    {event.title}
                  </div>
                  <div
                    style={{
                      marginTop: 14,
                      color: "rgba(245,240,225,0.78)",
                      fontSize: 17,
                      lineHeight: 1.38,
                      opacity: descriptionOpacity,
                    }}
                  >
                    {event.description}
                  </div>
                  <div
                    style={{
                      marginTop: 18,
                      color: BRAND.grey,
                      fontSize: 13,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      opacity: descriptionOpacity,
                    }}
                  >
                    {event.evidenceSource ?? "Archive index"}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            position: "absolute",
            left: 58,
            top: 48,
            opacity: introOpacity,
          }}
        >
          <div
            style={{
              color: accentColor,
              fontSize: 19,
              fontWeight: 850,
              textTransform: "uppercase",
            }}
          >
            {title}
          </div>
          <div
            style={{
              marginTop: 8,
              color: BRAND.bone,
              fontSize: 38,
              fontWeight: 850,
              maxWidth: 860,
            }}
          >
            {subtitle}
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            left: 58,
            bottom: 44,
            color: "rgba(245,240,225,0.62)",
            fontSize: 15,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          Camera Z {Math.round(cameraZ)} / {timings.length} exhibits indexed
        </div>

        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "black",
            opacity: fadeToBlack,
          }}
        />
      </AbsoluteFill>
    );
  }
);

TimelineFlythrough.displayName = "TimelineFlythrough";

export default TimelineFlythrough;
