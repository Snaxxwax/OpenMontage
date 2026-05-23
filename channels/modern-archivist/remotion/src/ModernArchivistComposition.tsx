import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ArchivistPuppet } from "./components/ArchivistPuppet";
import { ChannelFrame } from "./components/ChannelFrame";
import { MediaContainer } from "./components/MediaContainer";
import { ScrollingCodeBackdrop } from "./components/ScrollingCodeBackdrop";
import { flattenTags, getActiveLayout, getActiveMedia, isSipActive, isSpeaking } from "./state";
import { resolveAsset, stateCssVars } from "./styles";
import type { ModernArchivistEpisode } from "./types";

export const calculateModernArchivistMetadata: CalculateMetadataFunction<ModernArchivistEpisode> = async ({
  props,
}) => ({
  durationInFrames: Math.max(1, Math.ceil((props.duration_seconds || 60) * 30)),
});

export const ModernArchivistComposition: React.FC<ModernArchivistEpisode> = (episode) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;
  const tags = flattenTags(episode.sections);
  const layout = getActiveLayout(tags, time);
  const media = getActiveMedia(tags, time);
  const speaking = isSpeaking(episode.amplitude, time);
  const sipping = isSipActive(tags, time);

  return (
    <AbsoluteFill
      style={{
        ...stateCssVars[layout],
        backgroundColor: "var(--bg-color)",
        color: "var(--text)",
        overflow: "hidden",
        fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        transition: "background-color 180ms linear, color 180ms linear",
      }}
    >
      {episode.audio_src ? <Audio src={episode.audio_src.startsWith("/") ? resolveAsset(episode.audio_src) : staticFile(episode.audio_src)} /> : null}
      <ScrollingCodeBackdrop layout={layout} />
      <MediaContainer layout={layout} media={media} />
      <ArchivistPuppet layout={layout} speaking={speaking} sipping={sipping} puppet={episode.puppet} />
      <ChannelFrame title={episode.title} />
    </AbsoluteFill>
  );
};
