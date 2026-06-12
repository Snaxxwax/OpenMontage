import React from "react";
import { Img, OffthreadVideo, Sequence, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MediaItem, SourceAsset, VisualCue } from "../../types";
import { resolveAsset } from "../../styles";
import { labelStyle, valueText } from "./mediaStyles";

type SourceSequenceMedia = Extract<MediaItem, { kind: "source_sequence" }>;

const SOURCE_DERIVED_TYPES = new Set(["video_clip", "video_frame", "webpage_screenshot", "image", "screenshot"]);

function assetStillSrc(asset?: SourceAsset): string | undefined {
  const src = asset?.asset_type === "video_clip"
    ? (asset.poster_src ?? asset.render_src ?? asset.absolute_path ?? asset.local_path)
    : (asset?.render_src ?? asset?.absolute_path ?? asset?.local_path);
  return src ? resolveAsset(src) : undefined;
}

function assetVideoSrc(asset?: SourceAsset): string | undefined {
  if (asset?.asset_type !== "video_clip" || asset.preprocessed?.remotion_safe !== true || !asset.render_src) return undefined;
  return resolveAsset(asset.render_src);
}

function assetLabel(asset?: SourceAsset): string {
  if (!asset) return "SOURCE PENDING";
  return valueText(asset.source_owner, asset.asset_id).toUpperCase();
}

function activeCue(cues: VisualCue[], time: number, range?: [number, number]): VisualCue | undefined {
  const scoped = range ? cues.filter((cue) => cue.at >= range[0] && cue.at < range[1]) : cues;
  return scoped.find((cue) => time >= cue.at && time < cue.end) ?? scoped[0];
}

function isSourceDerived(asset?: SourceAsset): boolean {
  return asset ? SOURCE_DERIVED_TYPES.has(asset.asset_type) : false;
}

function CueVisualLayer({ cue, asset, fps }: { cue: VisualCue; asset?: SourceAsset; fps: number }) {
  const stillSrc = assetStillSrc(asset);
  const videoSrc = assetVideoSrc(asset);

  return <Sequence key={`${cue.asset_id}-${cue.at}`} from={Math.round(cue.at * fps)} durationInFrames={Math.max(1, Math.round((cue.end - cue.at) * fps))}>
    {videoSrc ? <OffthreadVideo muted src={videoSrc} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "contrast(1.1) saturate(0.9) brightness(0.78)" }} /> : null}
    {!videoSrc && stillSrc ? <Img src={stillSrc} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "contrast(1.1) saturate(0.9) brightness(0.78)" }} /> : null}
  </Sequence>;
}

export const SourceSequence: React.FC<{ media: SourceSequenceMedia }> = ({ media }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;
  const cues = media.cues ?? [];
  const cue = activeCue(cues, time, media.cue_range);
  const assets = media.assets ?? [];
  const asset = assets.find((candidate) => candidate.asset_id === cue?.asset_id) ?? assets[0];
  const activeSrc = assetStillSrc(asset) || assetVideoSrc(asset);
  const localCueTime = cue ? Math.max(0, time - cue.at) : 0;
  const cueProgress = cue ? Math.min(1, Math.max(0, localCueTime / Math.max(0.1, cue.end - cue.at))) : 0;
  const push = interpolate(cueProgress, [0, 1], [1.07, 1.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const reveal = interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const treatment = valueText(cue?.visual_treatment, "source-footage-first sequence").replace(/_/g, " ");
  const overlay = valueText(cue?.overlay_text, media.title ?? "SOURCE RECEIPT");
  const attribution = asset ? `${asset.source_owner} · ${asset.asset_type.replace(/_/g, " ")}` : "source missing";
  const sourceDerived = isSourceDerived(asset);
  const scopedCues = media.cue_range ? cues.filter((candidate) => candidate.at >= media.cue_range![0] && candidate.at < media.cue_range![1]) : cues;

  return <div style={{ height: "100%", position: "relative", overflow: "hidden", borderRadius: 24, background: "#05090f" }}>
    <div style={{ position: "absolute", inset: 0, opacity: 0.28, background: "radial-gradient(circle at 32% 28%, var(--accent), transparent 34%), linear-gradient(135deg, rgba(255,255,255,0.08), transparent 52%)" }} />
    <div style={{ position: "absolute", inset: 0, transform: `scale(${push})`, transition: "transform 180ms linear", opacity: reveal }}>
      {scopedCues.map((candidate) => <CueVisualLayer key={`${candidate.asset_id}-${candidate.at}`} cue={candidate} asset={assets.find((item) => item.asset_id === candidate.asset_id)} fps={fps} />)}
      {!activeSrc ? <div style={{ width: "100%", height: "100%", display: "grid", placeItems: "center", color: "rgba(255,255,255,0.72)", fontSize: 54, fontWeight: 800 }}>MISSING SOURCE ASSET</div> : null}
    </div>

    <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg, rgba(0,0,0,0.78), transparent 58%), linear-gradient(0deg, rgba(0,0,0,0.72), transparent 42%)" }} />
    <div style={{ position: "absolute", left: 46, top: 40, display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{ ...labelStyle, margin: 0 }}>{sourceDerived ? "SOURCE-DERIVED" : "DERIVED ANALYSIS"}</div>
      <div style={{ color: "rgba(255,255,255,0.72)", fontSize: 22, letterSpacing: 3, textTransform: "uppercase" }}>{assetLabel(asset)}</div>
    </div>

    <div style={{ position: "absolute", left: 52, bottom: 64, width: "68%" }}>
      <div style={{ color: "var(--accent)", fontSize: 24, letterSpacing: 5, textTransform: "uppercase", marginBottom: 16 }}>{treatment}</div>
      <div style={{ color: "var(--text)", fontSize: 82, lineHeight: 0.9, fontWeight: 950, textTransform: "uppercase", textShadow: "0 8px 28px rgba(0,0,0,0.55)" }}>{overlay}</div>
      <div style={{ marginTop: 22, color: "rgba(255,255,255,0.76)", fontSize: 26 }}>{attribution}</div>
    </div>

    <div style={{ position: "absolute", right: 42, bottom: 44, width: 280 }}>
      <div style={{ height: 4, background: "rgba(255,255,255,0.16)", overflow: "hidden", borderRadius: 999 }}>
        <div style={{ height: "100%", width: `${Math.round(cueProgress * 100)}%`, background: "var(--accent)" }} />
      </div>
      <div style={{ marginTop: 12, color: "rgba(255,255,255,0.62)", fontSize: 20, textAlign: "right", letterSpacing: 2, textTransform: "uppercase" }}>{valueText(cue?.retention_role, "retention beat").replace(/_/g, " ")}</div>
    </div>
  </div>;
};
