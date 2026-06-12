import React from "react";
import { Img } from "remotion";
import type { LayoutState, MediaItem, VisualMode } from "../types";
import { resolveAsset } from "../styles";
import { CaseFileSequence } from "./media/CaseFileSequence";
import { CinematicMetaphor } from "./media/CinematicMetaphor";
import { CodeWalkthrough } from "./media/CodeWalkthrough";
import { DataSequence } from "./media/DataSequence";
import { FailureGraph } from "./media/FailureGraph";
import { KineticTypography } from "./media/KineticTypography";
import { RecreatedUI } from "./media/RecreatedUI";
import { SourceMontage } from "./media/SourceMontage";
import { SourceSequence } from "./media/SourceSequence";

interface MediaContainerProps { layout: LayoutState; media?: MediaItem; visualMode?: VisualMode; }

export const MediaContainer: React.FC<MediaContainerProps> = ({ layout, media, visualMode }) => {
  const visible = layout === "STATE_DEEP_DIVE" || layout === "STATE_CRITICAL_ERROR" || Boolean(media);
  return <div style={{ position: "absolute", inset: layout === "STATE_CRITICAL_ERROR" ? "80px 80px 80px 80px" : "90px 110px", opacity: visible ? 1 : 0, transform: visible ? "translateY(0) scale(1)" : "translateY(30px) scale(0.98)", transition: "opacity 420ms ease, transform 520ms cubic-bezier(0.22, 1, 0.36, 1)", zIndex: 5, pointerEvents: "none" }}>
    <div style={{ height: "100%", border: "2px solid color-mix(in srgb, var(--accent) 70%, white 10%)", borderRadius: 34, background: "rgba(5, 11, 18, 0.82)", boxShadow: "0 30px 80px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.06)", padding: 42, overflow: "hidden", backdropFilter: "blur(8px)" }}>
      {media ? <MediaBody media={media} /> : <EmptyArchive visualMode={visualMode} />}
    </div>
  </div>;
};

const EmptyArchive: React.FC<{ visualMode?: VisualMode }> = ({ visualMode }) => <div style={{ color: "var(--text)", fontSize: 54, lineHeight: 1.05, maxWidth: 1000 }}><div style={{ color: "var(--accent)", fontSize: 24, letterSpacing: 8, marginBottom: 24 }}>ARCHIVE BUFFER</div>Waiting for {visualMode ?? "evidence"} packet...</div>;

const MediaBody: React.FC<{ media: MediaItem }> = ({ media }) => {
  if (media.kind === "case_file_sequence") return <CaseFileSequence media={media} />;
  if (media.kind === "cinematic_metaphor") return <CinematicMetaphor media={media} />;
  if (media.kind === "failure_graph") return <FailureGraph media={media} />;
  if (media.kind === "kinetic_typography") return <KineticTypography media={media} />;
  if (media.kind === "data_sequence") return <DataSequence media={media} />;
  if (media.kind === "code_walkthrough") return <CodeWalkthrough media={media} />;
  if (media.kind === "source_montage") return <SourceMontage media={media} />;
  if (media.kind === "source_sequence") return <SourceSequence media={media} />;
  if (media.kind === "recreated_ui") return <RecreatedUI media={media} />;
  if (media.kind === "code") return <CodeWalkthrough media={{ ...media, kind: "code_walkthrough", title: media.title ?? "Code Artifact" }} />;
  if (media.kind === "article") return <div><Header title={media.title ?? "Article"} eyebrow={media.source ?? "source"} /><p style={{ color: "var(--text)", fontSize: 50, lineHeight: 1.16, maxWidth: 1400 }}>{media.body}</p></div>;
  if (media.kind === "quote") return <KineticTypography media={{ id: media.id, kind: "kinetic_typography", text: media.quote, attribution: media.attribution, evidence_refs: media.evidence_refs }} />;
  return <div style={{ height: "100%", display: "grid", gridTemplateRows: "1fr auto", gap: 24 }}><Img src={resolveAsset(media.src)} style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: 22 }} />{media.caption ? <div style={{ color: "var(--text)", fontSize: 34 }}>{media.caption}</div> : null}</div>;
};

const Header: React.FC<{ title: string; eyebrow: string }> = ({ title, eyebrow }) => <div style={{ marginBottom: 32 }}><div style={{ color: "var(--accent)", fontSize: 24, letterSpacing: 8, textTransform: "uppercase", marginBottom: 12 }}>{eyebrow}</div><div style={{ color: "var(--text)", fontSize: 72, lineHeight: 0.95, fontWeight: 800 }}>{title}</div></div>;
