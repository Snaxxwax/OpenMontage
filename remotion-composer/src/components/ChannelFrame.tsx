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

export type ChapterBeat = {
  id: string;
  title: string;
  startSeconds: number;
  endSeconds: number;
  emphasis?: "normal" | "strong" | "critical";
};

export type ChannelFrameProps = {
  beats: ChapterBeat[];
  title?: string;
  subtitle?: string;
  accentColor?: string;
  backgroundColor?: string;
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

export const ChannelFrame: React.FC<ChannelFrameProps> = memo(
  ({
    beats,
    title = "FAILURE LEDGER",
    subtitle = "A chapter-level framing system",
    accentColor = BRAND.teal,
    backgroundColor = BRAND.charcoal,
  }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const introOpacity = interpolate(
      frame,
      [0, fps * 0.6, fps * 1.8],
      [0, 1, 1],
      {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.cubic),
      }
    );

    const fadeOut = interpolate(
      frame,
      [durationInFrames - fps * 1.4, durationInFrames],
      [0, 1],
      {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }
    );

    const activeBeat =
      beats.find(
        (beat) =>
          frame >= beat.startSeconds * fps &&
          frame < beat.endSeconds * fps
      ) ?? null;

    return (
      <AbsoluteFill
        style={{
          backgroundColor,
          color: BRAND.bone,
          fontFamily: "Inter, Helvetica, Arial, sans-serif",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            opacity: 0.22,
            backgroundImage:
              "linear-gradient(rgba(245,240,225,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(245,240,225,0.035) 1px, transparent 1px)",
            backgroundSize: "96px 96px",
          }}
        />

        <div
          style={{
            position: "absolute",
            inset: 0,
            padding: "64px 76px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            opacity: clamp01(1 - fadeOut),
          }}
        >
          <header
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              borderBottom: `1px solid rgba(245,240,225,0.18)`,
              paddingBottom: 18,
              opacity: introOpacity,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 850,
                  textTransform: "uppercase",
                  letterSpacing: 0.12,
                  color: accentColor,
                }}
              >
                {title}
              </div>
              <div
                style={{
                  marginTop: 6,
                  fontSize: 22,
                  fontWeight: 600,
                  color: BRAND.bone,
                  opacity: 0.82,
                }}
              >
                {subtitle}
              </div>
            </div>
            {activeBeat && (
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  color: "rgba(245,240,225,0.52)",
                  textAlign: "right",
                }}
              >
                CHAPTER {`${beats.indexOf(activeBeat) + 1}`} / {beats.length}
              </div>
            )}
          </header>

          <section
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "40px 0",
              position: "relative",
            }}
          >
            {activeBeat && (
              <ChapterTitle
                beat={activeBeat}
                accentColor={accentColor}
                frame={frame}
                fps={fps}
              />
            )}
          </section>

          <footer
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderTop: `1px solid rgba(245,240,225,0.18)`,
              paddingTop: 18,
              opacity: introOpacity,
            }}
          >
            <div
              style={{
                display: "flex",
                gap: 14,
              }}
            >
              {beats.map((beat, index) => {
                const isActive = beat.id === activeBeat?.id;
                const accentScale = spring({
                  frame: isActive ? frame - beat.startSeconds * fps : frame,
                  fps,
                  durationInFrames: isActive ? 0.45 * fps : 0,
                  config: { damping: 28, stiffness: 150, mass: 0.85 },
                });

                return (
                  <div
                    key={beat.id}
                    style={
                      (() => {
                        const r = isActive
                          ? interpolate(accentScale, [0, 1], [
                              107,
                              parseInt(accentColor.slice(1, 3), 16),
                            ])
                          : 107;
                        const g = isActive
                          ? interpolate(accentScale, [0, 1], [
                              114,
                              parseInt(accentColor.slice(3, 5), 16),
                            ])
                          : 114;
                        const b = isActive
                          ? interpolate(accentScale, [0, 1], [
                              128,
                              parseInt(accentColor.slice(5, 7), 16),
                            ])
                          : 128;
                        const bg = isActive
                          ? `rgba(${Number(r)}, ${Number(g)}, ${Number(b)})`
                          : BRAND.grey;
                        const scaleX = isActive
                          ? Number(interpolate(accentScale, [0, 1], [0.55, 1]))
                          : 0.42;
                        return {
                          width: 64,
                          height: 3,
                          backgroundColor: bg,
                          transform: `scaleX(${scaleX})`,
                          transformOrigin: "left center",
                          opacity: isActive ? 1 : 0.35,
                        };
                      })()
                    }
                  />
                );
              })}
            </div>

            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                textTransform: "uppercase",
                color: "rgba(245,240,225,0.32)",
              }}
            >
              Modern Archivist / Failure Ledger
            </div>
          </footer>
        </div>
      </AbsoluteFill>
    );
  }
);

ChannelFrame.displayName = "ChannelFrame";

type ChapterTitleProps = {
  beat: ChapterBeat;
  accentColor: string;
  frame: number;
  fps: number;
};

const ChapterTitle: React.FC<ChapterTitleProps> = ({
  beat,
  accentColor,
  frame,
  fps,
}) => {
  const startFrame = beat.startSeconds * fps;
  const settle = spring({
    frame: frame - startFrame,
    fps,
    durationInFrames: 0.55 * fps,
    config: { damping: 20, stiffness: 110, mass: 1 },
  });

  const scale = interpolate(settle, [0, 1], [0.94, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const y = interpolate(settle, [0, 1], [18, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const opacity = interpolate(frame, [startFrame, startFrame + 0.2 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const glow = beat.emphasis === "critical" ? accentColor : "transparent";

  return (
    <div
      style={{
        textAlign: "center",
        opacity,
        transform: `translateY(${y}px) scale(${scale})`,
        transformOrigin: "center center",
      }}
    >
      <div
        style={{
          fontSize: 14,
          fontWeight: 800,
          textTransform: "uppercase",
          letterSpacing: 0.28,
          color: "rgba(245,240,225,0.58)",
          marginBottom: 24,
        }}
      >
        Chapter {beat.id}
      </div>

      <h1
        style={{
          margin: 0,
          fontSize: 86,
          lineHeight: 1.05,
          fontWeight: 900,
          color: BRAND.bone,
          maxWidth: 1280,
          textShadow: glow
            ? `0 0 34px ${glow}55, 0 0 90px ${glow}33`
            : undefined,
          letterSpacing: -0.02,
        }}
      >
        {beat.title}
      </h1>

      {beat.emphasis === "critical" && (
        <div
          style={{
            marginTop: 28,
            height: 3,
            width: 180,
            backgroundColor: accentColor,
            boxShadow: `0 0 22px ${accentColor}88`,
          }}
        />
      )}
    </div>
  );
};

export default ChannelFrame;
