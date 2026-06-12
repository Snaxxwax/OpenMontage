import React, { useMemo } from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ChannelFrame } from "./components/ChannelFrame";
import { MediaContainer } from "./components/MediaContainer";
import { ScrollingCodeBackdrop } from "./components/ScrollingCodeBackdrop";
import { flattenTags, getActiveColorState, getActiveMediaSequence, getActiveVisualMode, layoutForColorState } from "./state";
import { resolveAsset, stateCssVars } from "./styles";
import type { ModernArchivistEpisode } from "./types";

export const calculateModernArchivistMetadata: CalculateMetadataFunction<ModernArchivistEpisode> = async ({ props }) => ({ durationInFrames: Math.max(1, Math.ceil((props.duration_seconds || 60) * 30)) });

export const ModernArchivistComposition: React.FC<ModernArchivistEpisode> = (episode) => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig(); const time = frame / fps;
  const tags = useMemo(() => flattenTags(episode.sections), [episode.sections]);
  const visualMode = getActiveVisualMode(episode.sections, time);
  const colorState = getActiveColorState(episode.sections, time);
  const layout = layoutForColorState(colorState, visualMode);
  const mediaBase = getActiveMediaSequence(episode.sections, tags, time);
  const media = useMemo(() => {
    if (mediaBase?.kind !== "source_sequence") return mediaBase;
    return {
      ...mediaBase,
      assets: mediaBase.assets ?? episode.source_assets,
      cues: mediaBase.cues ?? episode.visual_cues,
    };
  }, [episode.source_assets, episode.visual_cues, mediaBase]);
  const audioSrc = episode.audio_src && !episode.debug_disable_audio
    ? (episode.audio_src.startsWith("/") ? resolveAsset(episode.audio_src) : staticFile(episode.audio_src))
    : null;
  return <AbsoluteFill style={{ ...stateCssVars[layout], backgroundColor: "var(--bg-color)", color: "var(--text)", overflow: "hidden", fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif", transition: "background-color 180ms linear, color 180ms linear" }}>
    {audioSrc ? <Audio src={audioSrc} /> : null}
    {!episode.debug_disable_backdrop ? <ScrollingCodeBackdrop layout={layout} /> : null}
    {!episode.debug_disable_media ? <MediaContainer layout={layout} media={media} visualMode={visualMode} /> : null}
    <ChannelFrame title={episode.title} />
  </AbsoluteFill>;
};
