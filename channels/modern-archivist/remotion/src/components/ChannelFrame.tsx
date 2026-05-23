import React from "react";

export const ChannelFrame: React.FC<{ title: string }> = ({ title }) => (
  <>
    <div
      style={{
        position: "absolute",
        top: 34,
        left: 48,
        zIndex: 30,
        color: "var(--text)",
        fontSize: 26,
        letterSpacing: 6,
        textTransform: "uppercase",
        opacity: 0.88,
      }}
    >
      The Modern Archivist
    </div>
    <div
      style={{
        position: "absolute",
        bottom: 34,
        left: 48,
        right: 48,
        zIndex: 30,
        display: "flex",
        justifyContent: "space-between",
        color: "var(--text)",
        fontSize: 24,
        opacity: 0.72,
      }}
    >
      <span>{title}</span>
      <span style={{ color: "var(--accent)" }}>DOM ONLY / ARCHIVE MODE</span>
    </div>
  </>
);
