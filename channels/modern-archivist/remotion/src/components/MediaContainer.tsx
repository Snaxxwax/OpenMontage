import React from "react";
import { Img } from "remotion";
import type { LayoutState, MediaItem } from "../types";
import { resolveAsset } from "../styles";

interface MediaContainerProps {
  layout: LayoutState;
  media?: MediaItem;
}

export const MediaContainer: React.FC<MediaContainerProps> = ({ layout, media }) => {
  const visible = layout === "STATE_DEEP_DIVE" || layout === "STATE_CRITICAL_ERROR";

  return (
    <div
      style={{
        position: "absolute",
        inset: layout === "STATE_CRITICAL_ERROR" ? "80px 80px 80px 80px" : "90px 110px",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0) scale(1)" : "translateY(30px) scale(0.98)",
        transition: "opacity 420ms ease, transform 520ms cubic-bezier(0.22, 1, 0.36, 1)",
        zIndex: 5,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          height: "100%",
          border: "2px solid color-mix(in srgb, var(--accent) 70%, white 10%)",
          borderRadius: 34,
          background: "rgba(5, 11, 18, 0.82)",
          boxShadow: "0 30px 80px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.06)",
          padding: 42,
          overflow: "hidden",
          backdropFilter: "blur(8px)",
        }}
      >
        {media ? <MediaBody media={media} /> : <EmptyArchive />}
      </div>
    </div>
  );
};

const EmptyArchive: React.FC = () => (
  <div style={{ color: "var(--text)", fontSize: 54, lineHeight: 1.05, maxWidth: 1000 }}>
    <div style={{ color: "var(--accent)", fontSize: 24, letterSpacing: 8, marginBottom: 24 }}>
      ARCHIVE BUFFER
    </div>
    Waiting for evidence packet...
  </div>
);

const MediaBody: React.FC<{ media: MediaItem }> = ({ media }) => {
  if (media.kind === "code") {
    return (
      <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <Header title={media.title ?? "Code Artifact"} eyebrow={media.language ?? "source"} />
        <pre style={{ margin: 0, color: "#D7FFF7", fontSize: 44, lineHeight: 1.32, whiteSpace: "pre-wrap", fontFamily: "JetBrains Mono, Fira Code, monospace" }}>
          <code>{media.content}</code>
        </pre>
      </div>
    );
  }

  if (media.kind === "article") {
    return (
      <div>
        <Header title={media.title ?? "Article"} eyebrow={media.source ?? "source"} />
        <p style={{ color: "var(--text)", fontSize: 50, lineHeight: 1.16, maxWidth: 1400 }}>{media.body}</p>
      </div>
    );
  }

  if (media.kind === "quote") {
    return (
      <div style={{ display: "grid", placeItems: "center", height: "100%", textAlign: "center" }}>
        <blockquote style={{ color: "var(--text)", fontSize: 72, lineHeight: 1.05, margin: 0, maxWidth: 1300 }}>
          “{media.quote}”
        </blockquote>
        {media.attribution ? <div style={{ color: "var(--accent)", fontSize: 32 }}>— {media.attribution}</div> : null}
      </div>
    );
  }

  return (
    <div style={{ height: "100%", display: "grid", gridTemplateRows: "1fr auto", gap: 24 }}>
      <Img src={resolveAsset(media.src)} style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: 22 }} />
      {media.caption ? <div style={{ color: "var(--text)", fontSize: 34 }}>{media.caption}</div> : null}
    </div>
  );
};

const Header: React.FC<{ title: string; eyebrow: string }> = ({ title, eyebrow }) => (
  <div style={{ marginBottom: 32 }}>
    <div style={{ color: "var(--accent)", fontSize: 24, letterSpacing: 8, textTransform: "uppercase", marginBottom: 12 }}>{eyebrow}</div>
    <div style={{ color: "var(--text)", fontSize: 72, lineHeight: 0.95, fontWeight: 800 }}>{title}</div>
  </div>
);
