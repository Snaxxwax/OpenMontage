import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MediaItem } from "../../types";
import { cardStyle, labelStyle, valueText } from "./mediaStyles";

export const CaseFileSequence: React.FC<{ media: Extract<MediaItem, { kind: "case_file_sequence" }> }> = ({ media }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const beats = media.beats?.length ? media.beats : [{ label: media.stamp ?? "RECEIPT", claim: media.title }, { label: "SOURCE", claim: media.evidence_refs?.join(" / ") ?? "local evidence packet" }];
  return <div style={{ height: "100%", position: "relative" }}>
    <div style={labelStyle}>CASE FILE SEQUENCE</div>
    <div style={{ color: "var(--text)", fontSize: 72, fontWeight: 900, lineHeight: 0.95, marginTop: 12 }}>{media.title}</div>
    {beats.slice(0, 4).map((beat, index) => {
      const y = interpolate(Math.min(Math.max(t - index * 1.2, 0), 1), [0, 1], [80, 0]);
      const active = Math.floor(t / 1.8) % beats.length === index;
      return <div key={index} style={{ ...cardStyle, position: "absolute", left: 70 + index * 210, top: 210 + index * 76 + y, width: 520, minHeight: 185, padding: 28, transform: `rotate(${[-3, 2, -1, 3][index] ?? 0}deg)`, outline: active ? "6px solid rgba(255,0,0,0.7)" : "none" }}>
        <div style={{ ...labelStyle, color: active ? "#FF3333" : "var(--accent)" }}>{valueText((beat as Record<string, unknown>).label, index === 0 ? "CLAIM" : "RECEIPT")}</div>
        <div style={{ color: "var(--text)", fontSize: 36, lineHeight: 1.08, marginTop: 16 }}>{valueText((beat as Record<string, unknown>).claim, valueText((beat as Record<string, unknown>).title, media.title))}</div>
      </div>;
    })}
    <div style={{ position: "absolute", bottom: 0, color: "rgba(246,244,234,0.72)", fontSize: 24 }}>Evidence refs: {(media.evidence_refs ?? ["source_pending"]).join(" · ")}</div>
  </div>;
};
