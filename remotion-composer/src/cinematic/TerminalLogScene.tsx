import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TerminalLogEntry } from "./types";

interface TerminalLogSceneProps {
  entries: TerminalLogEntry[];
  flash?: boolean;
  stationId?: string;
}

const BG = "#080810";
const COLOR_CREW = "#8fbc8f";
const COLOR_AUTO = "#b8c8d4";
const COLOR_GAP = "#2a2a3a";
const COLOR_LABEL_CREW = "#4a7a4a";
const COLOR_LABEL_AUTO = "#5a7888";
const COLOR_HEADER = "#3a4a54";
const COLOR_PROMPT = "#4a6070";

function formatDay(day: number | null): string {
  if (day === null) return "";
  return `DAY ${String(day).padStart(3, " ")}`;
}

function typeLabel(type: "crew" | "autonomous" | "gap"): string {
  if (type === "crew") return "CREW";
  if (type === "autonomous") return "AUTO";
  return "";
}

export const TerminalLogScene: React.FC<TerminalLogSceneProps> = ({
  entries,
  flash = false,
  stationId = "ABYSS-7",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const totalEntries = entries.length;
  // How many frames to reveal each entry. Flash mode: all entries in first half.
  const framesPerEntry = flash
    ? Math.max(2, Math.floor((durationInFrames * 0.5) / totalEntries))
    : Math.max(8, Math.floor((durationInFrames * 0.85) / totalEntries));

  // Start offset for flash mode: show entries starting from the middle
  const flashOffset = flash ? Math.floor(totalEntries * 0.45) : 0;
  const startFrame = flash ? 0 : 18; // header appears at frame 0 for flash

  // Header fade in
  const headerOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Scan line pulse (subtle, periodic)
  const scanOpacity = 0.025 + 0.01 * Math.sin(frame * 0.18);

  // Which entries are visible at this frame
  const visibleEntries: { entry: TerminalLogEntry; opacity: number }[] = [];
  for (let i = 0; i < totalEntries; i++) {
    const idx = flash ? (flashOffset + i) % totalEntries : i;
    const entryStartFrame = startFrame + i * framesPerEntry;
    const op = interpolate(frame, [entryStartFrame, entryStartFrame + 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    if (op > 0) {
      visibleEntries.push({ entry: entries[idx], opacity: op });
    }
  }

  // Cursor blink after last entry appears
  const lastEntryFrame = startFrame + (totalEntries - 1) * framesPerEntry + 8;
  const cursorVisible = frame >= lastEntryFrame;
  const cursorBlink =
    cursorVisible && Math.floor((frame - lastEntryFrame) / 8) % 2 === 0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        fontFamily: "'Courier New', 'Lucida Console', monospace",
        overflow: "hidden",
      }}
    >
      {/* Scanline overlay */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(180deg, rgba(255,255,255,0.018) 0px, rgba(255,255,255,0.018) 1px, transparent 2px, transparent 5px)",
          opacity: scanOpacity,
          pointerEvents: "none",
        }}
      />

      {/* Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.6) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Terminal content */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          padding: "2.6vh 3vw",
          opacity: headerOpacity,
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1.4vh",
            paddingBottom: "0.65vh",
            borderBottom: `1px solid ${COLOR_HEADER}`,
          }}
        >
          <span
            style={{
              color: COLOR_HEADER,
              fontSize: "0.75vw",
              letterSpacing: "0.18em",
              textTransform: "uppercase",
            }}
          >
            STATION {stationId} // ACTIVITY LOG
          </span>
          <span
            style={{
              color: COLOR_HEADER,
              fontSize: "0.75vw",
              letterSpacing: "0.12em",
            }}
          >
            READ-ONLY
          </span>
        </div>

        {/* Log entries */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.5vh" }}>
          {visibleEntries.map(({ entry, opacity }, i) => {
            if (entry.type === "gap") {
              return (
                <div
                  key={i}
                  style={{
                    opacity,
                    color: COLOR_GAP,
                    fontSize: "0.85vw",
                    letterSpacing: "0.04em",
                    padding: "0.55vh 0",
                    borderTop: `1px solid ${COLOR_GAP}`,
                    borderBottom: `1px solid ${COLOR_GAP}`,
                    textAlign: "center",
                  }}
                >
                  {entry.text}
                </div>
              );
            }

            const isCrew = entry.type === "crew";
            const textColor = isCrew ? COLOR_CREW : COLOR_AUTO;
            const labelColor = isCrew ? COLOR_LABEL_CREW : COLOR_LABEL_AUTO;

            return (
              <div
                key={i}
                style={{
                  opacity,
                  display: "flex",
                  alignItems: "baseline",
                  gap: "0.55vw",
                  fontSize: "1.05vw",
                  lineHeight: 1.55,
                }}
              >
                <span
                  style={{
                    color: COLOR_PROMPT,
                    fontSize: "0.8vw",
                    letterSpacing: "0.06em",
                    minWidth: "3.5vw",
                    flexShrink: 0,
                  }}
                >
                  {formatDay(entry.day)}
                </span>
                <span
                  style={{
                    color: labelColor,
                    fontSize: "0.72vw",
                    letterSpacing: "0.10em",
                    minWidth: "2.2vw",
                    flexShrink: 0,
                  }}
                >
                  [{typeLabel(entry.type)}]
                </span>
                <span style={{ color: textColor, letterSpacing: "0.02em" }}>
                  {entry.text}
                </span>
              </div>
            );
          })}

          {/* Cursor */}
          {cursorVisible && (
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: "0.55vw",
                fontSize: "1.05vw",
                opacity: cursorBlink ? 0.9 : 0,
              }}
            >
              <span style={{ color: COLOR_PROMPT, fontSize: "0.8vw", minWidth: "3.5vw" }} />
              <span style={{ color: COLOR_LABEL_AUTO, fontSize: "0.72vw", minWidth: "2.2vw" }} />
              <span style={{ color: COLOR_AUTO }}>█</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            marginTop: "1vh",
            paddingTop: "0.5vh",
            borderTop: `1px solid ${COLOR_HEADER}`,
            display: "flex",
            justifyContent: "space-between",
            color: COLOR_HEADER,
            fontSize: "0.65vw",
            letterSpacing: "0.12em",
          }}
        >
          <span>AUTONOMOUS LOGGING ACTIVE</span>
          <span>LAST SURFACE CONTACT: DAY 011</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
