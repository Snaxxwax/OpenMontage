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
  amber: "#F59E0B",
};

export type KineticWord = {
  word: string;
  startSeconds: number;
  endSeconds: number;
  emphasis?: "normal" | "strong" | "critical" | "number";
};

export type KineticTypographyProps = {
  words: KineticWord[];
  accentColor?: string;
  backgroundColor?: string;
  fontSize?: number;
  lineHeight?: number;
  maxWidth?: number;
  revealType?: "word" | "char" | "line";
  staggerMs?: number;
  holdDuration?: number;
  textAlign?: "left" | "center" | "right";
};

type Token = {
  word: string;
  startFrame: number;
  endFrame: number;
  emphasis: "normal" | "strong" | "critical" | "number";
  index: number;
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const getEmphasisStyle = (emphasis: string, accentColor: string) => {
  switch (emphasis) {
    case "strong":
      return { fontWeight: 800, color: "#FFFFFF" };
    case "critical":
      return { fontWeight: 850, color: BRAND.criticalRed };
    case "number":
      return { fontWeight: 850, color: BRAND.amber, fontFamily: "JetBrains Mono, Fira Code, monospace" };
    default:
      return { fontWeight: 500, color: BRAND.bone };
  }
};

const wordShapePath = (revealType: "word" | "char" | "line", progress: number, word: string) => {
  if (revealType === "char") {
    return word.split("").map((_, i) => {
      const charProgress = clamp01(progress * word.length - i);
      return charProgress > 0 ? 1 : 0;
    });
  }
  return null;
};

export const KineticTypography: React.FC<KineticTypographyProps> = memo(
  ({
    words,
    accentColor = BRAND.teal,
    backgroundColor = BRAND.charcoal,
    fontSize = 54,
    lineHeight = 1.15,
    maxWidth = 1400,
    revealType = "word",
    staggerMs = 30,
    holdDuration = 0.35,
    textAlign = "center",
  }) => {
    const frame = useCurrentFrame();
    const { fps, width, height } = useVideoConfig();
    const seconds = frame / fps;

    const tokens = useMemo((): Token[] => {
      return words.map((w, index) => ({
        word: w.word,
        startFrame: Math.round(w.startSeconds * fps),
        endFrame: Math.round(w.endSeconds * fps),
        emphasis: w.emphasis ?? "normal",
        index,
      }));
    }, [words, fps]);

    return (
      <AbsoluteFill
        style={{
          backgroundColor,
          color: BRAND.bone,
          fontFamily: "Space Grotesk, Inter, Helvetica, sans-serif",
          letterSpacing: -0.02,
          overflow: "hidden",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          textAlign,
        }}
      >
        <div
          style={{
            maxWidth,
            width: "100%",
            padding: "0 60px",
            lineHeight,
            fontSize: `${fontSize}px`,
            textAlign,
          }}
        >
          {tokens.map((token) => {
            const revealStartFrame = token.startFrame;
            const revealEndFrame = revealStartFrame + Math.round((staggerMs / 1000) * fps);

            const revealProgress = spring({
              frame: frame - revealStartFrame,
              fps,
              durationInFrames: Math.round((staggerMs / 1000) * fps),
              config: { damping: 22, stiffness: 120, mass: 0.8 },
            });

            const holdProgress = interpolate(
              frame,
              [token.endFrame, token.endFrame + Math.round(holdDuration * fps)],
              [1, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );

            const exitStartFrame = token.endFrame + Math.round(holdDuration * fps);
            const exitProgress = spring({
              frame: frame - exitStartFrame,
              fps,
              durationInFrames: Math.round((staggerMs / 1000) * fps * 0.8),
              config: { damping: 26, stiffness: 140, mass: 0.7 },
            });

            const isRevealing = frame >= revealStartFrame && frame < revealEndFrame;
            const isHolding = frame >= token.startFrame && frame < exitStartFrame;
            const isExiting = frame >= exitStartFrame;

            const opacity = isRevealing
              ? revealProgress
              : isHolding
              ? 1
              : isExiting
              ? clamp01(1 - exitProgress)
              : 0;

            const scale = isRevealing
              ? interpolate(revealProgress, [0, 1], [0.88, 1], { extrapolateLeft: "clamp" })
              : isExiting
              ? interpolate(exitProgress, [0, 1], [1, 1.08], { extrapolateLeft: "clamp" })
              : 1;

            const yOffset = isRevealing
              ? interpolate(revealProgress, [0, 1], [18, 0], { extrapolateLeft: "clamp", easing: Easing.out(Easing.cubic) })
              : isExiting
              ? interpolate(exitProgress, [0, 1], [0, -14], { extrapolateLeft: "clamp", easing: Easing.in(Easing.cubic) })
              : 0;

            const emphasisStyle = getEmphasisStyle(token.emphasis, accentColor);

            if (revealType === "char") {
              return (
                <span
                  key={token.index}
                  style={{
                    display: "inline-block",
                    opacity: clamp01(opacity * 1.2),
                    transform: `translateY(${yOffset}px) scale(${scale})`,
                    filter: token.emphasis === "critical" && isHolding
                      ? `drop-shadow(0 0 8px ${BRAND.criticalRed}88)`
                      : undefined,
                  }}
                >
                  {token.word.split("").map((char, charIndex) => {
                    const charDelay = charIndex * 2;
                    const charStartFrame = revealStartFrame + Math.round((charDelay / 1000) * fps);
                    const charReveal = spring({
                      frame: frame - charStartFrame,
                      fps,
                      durationInFrames: Math.round((staggerMs / 1000) * fps * 0.6),
                      config: { damping: 24, stiffness: 130, mass: 0.7 },
                    });
                    const charOpacity = frame >= charStartFrame ? clamp01(charReveal) : 0;
                    return (
                      <span
                        key={charIndex}
                        style={{
                          display: "inline-block",
                          opacity: charOpacity,
                          transform: `translateY(${interpolate(charReveal, [0, 1], [12, 0], { extrapolateLeft: "clamp" })}px) scale(${interpolate(charReveal, [0, 1], [0.9, 1], { extrapolateLeft: "clamp" })})`,
                          color: char === " " ? "transparent" : emphasisStyle.color,
                          fontWeight: emphasisStyle.fontWeight,
                          fontFamily: emphasisStyle.fontFamily,
                        }}
                      >
                        {char}
                      </span>
                    );
                  })}
                </span>
              );
            }

            return (
              <span
                key={token.index}
                style={{
                  display: "inline-block",
                  opacity: clamp01(opacity),
                  transform: `translateY(${yOffset}px) scale(${scale})`,
                  filter: token.emphasis === "critical" && isHolding
                    ? `drop-shadow(0 0 12px ${BRAND.criticalRed}AA)`
                    : token.emphasis === "number" && isHolding
                    ? `drop-shadow(0 0 8px ${BRAND.amber}66)`
                    : undefined,
                  transition: "filter 0.2s ease",
                }}
              >
                {token.word}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }
);

KineticTypography.displayName = "KineticTypography";

export default KineticTypography;
