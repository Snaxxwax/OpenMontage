import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ArchivistPuppet } from "./components/ArchivistPuppet";
import { ChannelFrame } from "./components/ChannelFrame";
import { MediaContainer } from "./components/MediaContainer";
import { ScrollingCodeBackdrop } from "./components/ScrollingCodeBackdrop";
import { flattenTags, getActiveCharacterCue, getActiveColorState, getActiveMediaSequence, getActiveVisualMode, isSipActive, isSpeaking, layoutForColorState } from "./state";
import { resolveAsset, stateCssVars } from "./styles";
import type { ModernArchivistEpisode } from "./types";

export const calculateModernArchivistMetadata: CalculateMetadataFunction<ModernArchivistEpisode> = async ({ props }) => ({ durationInFrames: Math.max(1, Math.ceil((props.duration_seconds || 60) * 30)) });

export const ModernArchivistComposition: React.FC<ModernArchivistEpisode> = (episode) => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig(); const time = frame / fps;
  const tags = flattenTags(episode.sections);
  const visualMode = getActiveVisualMode(episode.sections, time);
  const colorState = getActiveColorState(episode.sections, time);
  const layout = layoutForColorState(colorState, visualMode);
  const media = getActiveMediaSequence(episode.sections, tags, time);
  const characterCue = getActiveCharacterCue(episode.sections, time);
  const speaking = isSpeaking(episode.amplitude, time);
  const sipping = isSipActive(tags, time);
  return <AbsoluteFill style={{ ...stateCssVars[layout], backgroundColor: "var(--bg-color)", color: "var(--text)", overflow: "hidden", fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif", transition: "background-color 180ms linear, color 180ms linear" }}>
    {episode.audio_src ? <Audio src={episode.audio_src.startsWith("/") ? resolveAsset(episode.audio_src) : staticFile(episode.audio_src)} /> : null}
    <ScrollingCodeBackdrop layout={layout} />
    <MediaContainer layout={layout} media={media} visualMode={visualMode} />
    <ArchivistPuppet layout={layout} speaking={speaking} sipping={sipping} puppet={episode.puppet} cue={characterCue} colorState={colorState} />
    <ChannelFrame title={episode.title} />
  </AbsoluteFill>;
};
