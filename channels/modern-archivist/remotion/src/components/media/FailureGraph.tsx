import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import type { MediaItem } from "../../types";
import { labelStyle, valueText } from "./mediaStyles";
export const FailureGraph: React.FC<{ media: Extract<MediaItem, { kind: "failure_graph" }> }> = ({ media }) => {
  const frame = useCurrentFrame();
  const nodes = media.nodes?.length ? media.nodes : [{ id: "claim", label: "Claim" }, { id: "system", label: "System" }, { id: "failure", label: "Failure" }];
  const links = media.links?.length ? media.links : [{ from: 0, to: 1 }, { from: 1, to: 2 }];
  const coords = [[300, 420], [760, 260], [1220, 520], [940, 720], [480, 700]];
  return <div style={{ height: "100%" }}><div style={labelStyle}>FAILURE GRAPH</div><div style={{ color: "var(--text)", fontSize: 64, fontWeight: 900 }}>{media.title}</div><svg viewBox="0 0 1500 720" style={{ width: "100%", height: "78%" }}>
    {links.map((link, i) => { const a = coords[Number((link as Record<string, unknown>).from) || i] ?? coords[0]; const b = coords[Number((link as Record<string, unknown>).to) || i + 1] ?? coords[2]; const p = interpolate(frame, [i * 20, i * 20 + 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }); return <line key={i} x1={a[0]} y1={a[1]} x2={a[0] + (b[0]-a[0]) * p} y2={a[1] + (b[1]-a[1]) * p} stroke={i === links.length - 1 ? "#FF3333" : "var(--accent)"} strokeWidth="8" strokeLinecap="round" />; })}
    {nodes.map((node, i) => { const [x,y]=coords[i%coords.length]; return <g key={i}><circle cx={x} cy={y} r="86" fill="rgba(0,128,128,0.22)" stroke={i===nodes.length-1?"#FF3333":"var(--accent)"} strokeWidth="7"/><text x={x} y={y+8} textAnchor="middle" fill="var(--text)" fontSize="34" fontWeight="800">{valueText((node as Record<string, unknown>).label, `Node ${i+1}`)}</text></g>; })}
  </svg></div>;
};
