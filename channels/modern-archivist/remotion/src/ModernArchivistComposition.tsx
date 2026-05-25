import React, { useMemo } from "react";
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
  const tags = useMemo(() => flattenTags(episode.sections), [episode.sections]);
  const visualMode = getActiveVisualMode(episode.sections, time);
  const colorState = getActiveColorState(episode.sections, time);
  const layout = layoutForColorState(colorState, visualMode);
  const media = getActiveMediaSequence(episode.sections, tags, time);
  const characterCue = getActiveCharacterCue(episode.sections, time);
  const speaking = isSpeaking(episode.amplitude, time);
  const sipping = isSipActive(tags, time);
  const audioSrc = episode.audio_src && !episode.debug_disable_audio
    ? (episode.audio_src.startsWith("/") ? resolveAsset(episode.audio_src) : staticFile(episode.audio_src))
    : null;
  return <AbsoluteFill style={{ ...stateCssVars[layout], backgroundColor: "var(--bg-color)", color: "var(--text)", overflow: "hidden", fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif", transition: "background-color 180ms linear, color 180ms linear" }}>
    {audioSrc ? <Audio src={audioSrc} /> : null}
    {!episode.debug_disable_backdrop ? <ScrollingCodeBackdrop layout={layout} /> : null}
    {!episode.debug_disable_media ? <MediaContainer layout={layout} media={media} visualMode={visualMode} /> : null}
    {!episode.debug_disable_puppet ? <ArchivistPuppet layout={layout} speaking={speaking} sipping={sipping} puppet={episode.puppet} cue={characterCue} colorState={colorState} wordTimestamps={episode.word_timings} debugPuppetStatic={episode.debug_puppet_static} debugDisablePuppetMouth={episode.debug_disable_puppet_mouth} debugDisablePuppetFilters={episode.debug_disable_puppet_filters} /> : null}
    <ChannelFrame title={episode.title} />
  </AbsoluteFill>;
};
