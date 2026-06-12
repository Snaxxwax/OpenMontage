import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import type { MediaItem } from "../../types";
import { labelStyle, valueText } from "./mediaStyles";

const MAX_BAR_HEIGHT = 410;
const BAR_WIDTH = 108;
const CHART_TOP = 86;
const CHART_BASELINE = 520;

export const DataSequence: React.FC<{ media: Extract<MediaItem, { kind: "data_sequence" }> }> = ({ media }) => {
  const frame = useCurrentFrame();
  const data = (media.data?.length ? media.data : [
    { label: "Q1", value: 90 },
    { label: "Q2", value: 62 },
    { label: "Q3", value: 24 },
    { label: "Q4", value: 8 },
  ]).slice(0, 6);
  const values = data.map((d) => Math.max(0, Number((d as Record<string, unknown>).value ?? 50)));
  const maxValue = Math.max(1, ...values);
  const spacing = 1180 / Math.max(1, data.length);

  return <div style={{ height: "100%" }}>
    <div style={labelStyle}>DATA SEQUENCE</div>
    <div style={{ color: "var(--text)", fontSize: 64, fontWeight: 900 }}>{media.title}</div>
    <svg viewBox="0 0 1400 620" style={{ width: "100%", height: "78%" }}>
      <line x1="95" y1={CHART_BASELINE} x2="1310" y2={CHART_BASELINE} stroke="rgba(255,255,255,0.18)" strokeWidth="2" />
      {data.map((d, i) => {
        const record = d as Record<string, unknown>;
        const rawValue = values[i];
        const targetHeight = Math.max(18, (rawValue / maxValue) * MAX_BAR_HEIGHT);
        const h = interpolate(frame, [i * 8, i * 8 + 22], [0, targetHeight], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const x = 130 + i * spacing + (spacing - BAR_WIDTH) / 2;
        const label = valueText(record.label, String(i + 1));
        const unit = valueText(record.unit, "");
        return <g key={i}>
          <rect x={x} y={CHART_BASELINE - h} width={BAR_WIDTH} height={h} fill={i === data.length - 1 ? "#FF3333" : "var(--accent)"} rx="4" />
          <text x={x + BAR_WIDTH / 2} y={CHART_BASELINE - h - 22} textAnchor="middle" fill="var(--text)" fontSize="34" fontWeight={800}>{rawValue.toLocaleString()}</text>
          {unit ? <text x={x + BAR_WIDTH / 2} y={CHART_BASELINE - h + 28} textAnchor="middle" fill="rgba(255,255,255,0.72)" fontSize="24" fontWeight={700}>{unit}</text> : null}
          <text x={x + BAR_WIDTH / 2} y="570" textAnchor="middle" fill="var(--text)" fontSize="24" fontWeight={700}>{label}</text>
        </g>;
      })}
      <text x="110" y={CHART_TOP} fill="rgba(255,255,255,0.42)" fontSize="22">normalized for mixed units</text>
    </svg>
  </div>;
};
