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

export type EvidenceWordTiming = {
  word: string;
  startSeconds: number;
  endSeconds: number;
};

export type EvidenceHighlightRange = {
  startWord: number;
  endWord: number;
  startSeconds?: number;
  endSeconds?: number;
  color?: string;
  critical?: boolean;
};

export type EvidenceRevealProps = {
  documentText: string;
  sourceLabel: string;
  highlightRanges: EvidenceHighlightRange[];
  wordTimings?: EvidenceWordTiming[];
  title?: string;
  documentDate?: string;
  accentColor?: string;
  backgroundColor?: string;
};

type Token = {
  value: string;
  wordIndex: number | null;
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const tokenize = (text: string): Token[] => {
  let wordIndex = 0;

  return text.split(/(\s+)/).map((value) => {
    if (/^\s+$/.test(value)) {
      return { value, wordIndex: null };
    }

    const token = { value, wordIndex };
    wordIndex += 1;
    return token;
  });
};

const getRangeTiming = (
  range: EvidenceHighlightRange,
  index: number,
  wordTimings: EvidenceWordTiming[] | undefined
) => {
  if (range.startSeconds !== undefined) {
    return {
      start: range.startSeconds,
      end: range.endSeconds ?? range.startSeconds + 1.15,
    };
  }

  const startWord = wordTimings?.[range.startWord];
  const endWord = wordTimings?.[range.endWord];

  if (startWord && endWord) {
    return {
      start: startWord.startSeconds,
      end: endWord.endSeconds,
    };
  }

  const fallbackStart = 4 + index * 1.05;
  return { start: fallbackStart, end: fallbackStart + 1 };
};

const TypewriterLabel: React.FC<{
  text: string;
  accentColor: string;
  frame: number;
  fps: number;
}> = ({ text, accentColor, frame, fps }) => {
  const startFrame = 3 * fps;
  const revealChars = Math.floor(
    interpolate(frame, [startFrame, startFrame + 0.9 * fps], [0, text.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    })
  );
  const lineProgress = interpolate(
    frame,
    [startFrame + 0.25 * fps, startFrame + 1.25 * fps],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );

  return (
    <div
      style={{
        position: "absolute",
        left: 52,
        bottom: 42,
        color: BRAND.bone,
        fontFamily: "Inter, Helvetica, Arial, sans-serif",
        letterSpacing: 0,
        opacity: interpolate(frame, [startFrame - 8, startFrame + 12], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
      }}
    >
      <div
        style={{
          fontSize: 20,
          fontWeight: 600,
          textTransform: "uppercase",
        }}
      >
        {text.slice(0, revealChars)}
        <span
          style={{
            display: revealChars >= text.length ? "none" : "inline-block",
            width: 10,
            color: accentColor,
          }}
        >
          |
        </span>
      </div>
      <div
        style={{
          width: 320,
          height: 3,
          marginTop: 10,
          transformOrigin: "left center",
          transform: `scaleX(${lineProgress})`,
          background: `linear-gradient(90deg, ${accentColor}, rgba(0, 212, 170, 0))`,
          boxShadow: `0 0 18px ${accentColor}66`,
        }}
      />
    </div>
  );
};

export const EvidenceReveal: React.FC<EvidenceRevealProps> = memo(
  ({
    documentText,
    sourceLabel,
    highlightRanges,
    wordTimings,
    title = "ARCHIVAL EXHIBIT",
    documentDate,
    accentColor = BRAND.teal,
    backgroundColor = BRAND.charcoal,
  }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const seconds = frame / fps;
    const tokens = useMemo(() => tokenize(documentText), [documentText]);

    const materialize = spring({
      frame,
      fps,
      durationInFrames: 2 * fps,
      config: { damping: 24, stiffness: 65, mass: 1.1 },
    });
    const pushProgress = interpolate(frame, [2 * fps, 4 * fps], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    });
    const documentOpacity = interpolate(materialize, [0, 0.35, 1], [0, 0.75, 1]);
    const translateZ = interpolate(materialize, [0, 1], [-200, 0]);
    const rotateX = interpolate(materialize, [0, 1], [15, 0]);
    const cameraScale = interpolate(pushProgress, [0, 1], [1, 1.15]);
    const lightSweep = interpolate(frame, [0, 2.4 * fps], [-45, 125], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });

    const highlightByWord = useMemo(() => {
      const ranges = highlightRanges.map((range, index) => ({
        ...range,
        timing: getRangeTiming(range, index, wordTimings),
      }));

      return tokens.map((token) => {
        if (token.wordIndex === null) {
          return null;
        }

        return (
          ranges.find(
            (range) =>
              token.wordIndex !== null &&
              token.wordIndex >= range.startWord &&
              token.wordIndex <= range.endWord
          ) ?? null
        );
      });
    }, [highlightRanges, tokens, wordTimings]);

    const paperStyle: CSSProperties = {
      position: "relative",
      width: 1040,
      minHeight: 630,
      padding: "72px 86px 88px",
      borderRadius: 3,
      backgroundColor: BRAND.bone,
      backgroundImage:
        "radial-gradient(circle at 18% 12%, rgba(255,255,255,0.62), transparent 18%), radial-gradient(circle at 78% 20%, rgba(26,26,46,0.045), transparent 22%), linear-gradient(115deg, rgba(255,255,255,0.42), rgba(245,240,225,0.1) 38%, rgba(82,69,47,0.12))",
      backgroundPosition: `${pushProgress * 18}px ${pushProgress * -10}px, ${pushProgress * -12}px ${pushProgress * 8}px, center`,
      boxShadow:
        "0 34px 90px rgba(0, 0, 0, 0.48), 0 12px 34px rgba(0, 0, 0, 0.32), inset 0 0 0 1px rgba(26, 26, 46, 0.12), inset 0 18px 48px rgba(255, 255, 255, 0.38), inset 0 -28px 55px rgba(26, 26, 46, 0.08)",
      overflow: "hidden",
    };

    return (
      <AbsoluteFill
        style={{
          background:
            `radial-gradient(circle at 50% 36%, rgba(0, 212, 170, 0.16), transparent 34%), linear-gradient(180deg, ${backgroundColor}, #080812)`,
          justifyContent: "center",
          alignItems: "center",
          perspective: 1200,
          fontFamily: "Inter, Helvetica, Arial, sans-serif",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            opacity: 0.22,
            backgroundImage:
              "linear-gradient(rgba(245,240,225,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(245,240,225,0.04) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            transform: `translateY(${pushProgress * -16}px)`,
          }}
        />
        <div
          style={{
            opacity: documentOpacity,
            transform: `scale(${cameraScale}) translateZ(${translateZ}px) rotateX(${rotateX}deg)`,
            transformStyle: "preserve-3d",
          }}
        >
          <article style={paperStyle}>
            <div
              style={{
                position: "absolute",
                inset: 0,
                pointerEvents: "none",
                opacity: 0.65,
                backgroundImage:
                  "radial-gradient(circle at 20% 30%, rgba(26,26,46,0.08) 0 1px, transparent 1px), radial-gradient(circle at 70% 60%, rgba(255,255,255,0.32) 0 1px, transparent 1px)",
                backgroundSize: "9px 11px, 13px 17px",
                mixBlendMode: "multiply",
                transform: `translate(${pushProgress * 8}px, ${pushProgress * -6}px)`,
              }}
            />
            <div
              style={{
                position: "absolute",
                inset: -160,
                background: `linear-gradient(${lightSweep}deg, transparent 42%, rgba(255,255,255,0.42) 50%, transparent 58%)`,
                opacity: interpolate(materialize, [0, 0.4, 1], [0, 0.8, 0.22]),
                pointerEvents: "none",
              }}
            />
            <header style={{ position: "relative", marginBottom: 34 }}>
              <div
                style={{
                  color: BRAND.grey,
                  fontSize: 15,
                  fontWeight: 800,
                  letterSpacing: 0,
                  textTransform: "uppercase",
                }}
              >
                {title}
              </div>
              {documentDate && (
                <div
                  style={{
                    color: BRAND.charcoal,
                    fontSize: 24,
                    fontWeight: 700,
                    marginTop: 8,
                    opacity: 0.72,
                  }}
                >
                  {documentDate}
                </div>
              )}
            </header>
            <main
              style={{
                position: "relative",
                color: BRAND.charcoal,
                fontFamily: "Georgia, Times New Roman, serif",
                fontSize: 36,
                lineHeight: 1.55,
                fontWeight: 500,
              }}
            >
              {tokens.map((token, index) => {
                const highlight = highlightByWord[index];
                if (!highlight || token.wordIndex === null) {
                  return <React.Fragment key={`${token.value}-${index}`}>{token.value}</React.Fragment>;
                }

                const rangeStart = highlight.timing.start * fps;
                const rangeEnd = highlight.timing.end * fps;
                const pulseIn = spring({
                  frame: frame - rangeStart,
                  fps,
                  durationInFrames: 0.28 * fps,
                  config: { damping: 18, stiffness: 145, mass: 0.8 },
                });
                const pulseOut = interpolate(frame, [rangeEnd - 0.25 * fps, rangeEnd], [1, 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.out(Easing.quad),
                });
                const active = seconds >= highlight.timing.start && seconds <= highlight.timing.end;
                const glow = active ? clamp01(pulseIn * pulseOut) : 0;
                const color = highlight.color ?? (highlight.critical ? BRAND.criticalRed : accentColor);

                return (
                  <span
                    key={`${token.value}-${index}`}
                    style={{
                      display: "inline-block",
                      padding: "0 3px",
                      borderRadius: 2,
                      transform: `scale(${1 + glow * 0.02})`,
                      backgroundColor: `${color}${Math.round(30 + glow * 80)
                        .toString(16)
                        .padStart(2, "0")}`,
                      boxShadow: `0 0 ${glow * 26}px ${color}99, inset 0 -0.18em 0 ${color}66`,
                      filter: `drop-shadow(0 0 ${glow * 10}px ${color}AA)`,
                    }}
                  >
                    {token.value}
                  </span>
                );
              })}
            </main>
          </article>
        </div>
        <TypewriterLabel text={sourceLabel} accentColor={accentColor} frame={frame} fps={fps} />
      </AbsoluteFill>
    );
  }
);

EvidenceReveal.displayName = "EvidenceReveal";

export default EvidenceReveal;
