import React from "react";
import type { MediaItem } from "../../types";
import { cardStyle } from "./mediaStyles";

type RecreatedUIMedia = Extract<MediaItem, { kind: "recreated_ui" }>;

export const RecreatedUI: React.FC<{ media: RecreatedUIMedia }> = ({ media }) => {
  const beforeAfter = media.before_after ?? [];
  return (
    <div style={{ ...cardStyle, height: "100%", display: "grid", gridTemplateRows: "auto 1fr auto", gap: 22 }}>
      <div>
        <div style={{ color: "var(--accent)", fontSize: 24, letterSpacing: 8, textTransform: "uppercase", marginBottom: 12 }}>
          RECREATED DIGITAL ARTIFACT
        </div>
        <div style={{ color: "var(--text)", fontSize: 68, lineHeight: 0.95, fontWeight: 800 }}>{media.title}</div>
        {media.url ? <div style={{ color: "rgba(215,232,230,0.62)", fontSize: 24, marginTop: 12 }}>{media.url}</div> : null}
      </div>

      <div style={{ border: "2px solid rgba(91, 241, 216, 0.32)", borderRadius: 26, background: "rgba(8,18,28,0.92)", overflow: "hidden", display: "grid", gridTemplateRows: "56px 1fr" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 22px", borderBottom: "1px solid rgba(255,255,255,0.09)", color: "rgba(215,232,230,0.7)", fontSize: 20 }}>
          <span style={{ width: 14, height: 14, borderRadius: 999, background: "#ff6b6b" }} />
          <span style={{ width: 14, height: 14, borderRadius: 999, background: "#ffd166" }} />
          <span style={{ width: 14, height: 14, borderRadius: 999, background: "#5bf1d8" }} />
          <span style={{ marginLeft: 14 }}>{media.url ?? "archived page / recreated UI"}</span>
        </div>
        <div style={{ padding: 34, display: "grid", alignContent: "center", gap: 24 }}>
          {media.claim_highlight ? (
            <div style={{ color: "var(--text)", fontSize: 54, lineHeight: 1.05, fontWeight: 800, borderLeft: "8px solid var(--accent)", paddingLeft: 24 }}>
              {media.claim_highlight}
            </div>
          ) : (
            <div style={{ color: "var(--text)", fontSize: 46, lineHeight: 1.08 }}>Recreated artifact view</div>
          )}
          {beforeAfter.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(beforeAfter.length, 3)}, 1fr)`, gap: 16 }}>
              {beforeAfter.slice(0, 3).map((item, index) => (
                <div key={index} style={{ background: "rgba(255,255,255,0.06)", borderRadius: 16, padding: 18, color: "rgba(215,232,230,0.78)", fontSize: 24 }}>
                  {String(item.label ?? item.title ?? `State ${index + 1}`)}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div style={{ color: "rgba(215,232,230,0.68)", fontSize: 22, letterSpacing: 4, textTransform: "uppercase" }}>
        Evidence refs: {(media.evidence_refs ?? []).join(", ") || "pending"}
      </div>
    </div>
  );
};
