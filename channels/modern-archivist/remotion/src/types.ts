export type LayoutState =
  | "STATE_MONOLOGUE"
  | "STATE_DEEP_DIVE"
  | "STATE_CRITICAL_ERROR";

export type MediaItem =
  | {
      id: string;
      kind: "code";
      title?: string;
      language?: string;
      content: string;
    }
  | {
      id: string;
      kind: "article";
      title?: string;
      source?: string;
      body: string;
      highlightTerms?: string[];
    }
  | {
      id: string;
      kind: "quote";
      quote: string;
      attribution?: string;
    }
  | {
      id: string;
      kind: "image";
      src: string;
      caption?: string;
    };

export type ScriptTag =
  | { at: number; type: "layout"; value: LayoutState }
  | { at: number; type: "sip" }
  | { at: number; type: "media"; value: MediaItem }
  | { at: number; type: "emphasis"; value?: string };

export interface EpisodeSection {
  id: string;
  start: number;
  end: number;
  text: string;
  tags: ScriptTag[];
}

export interface AudioAmplitudeSample {
  time: number;
  volume: number;
}

export interface PuppetManifest {
  version: string;
  character_id: string;
  display_name?: string;
  temporary?: boolean;
  layers: {
    body: string;
    mug?: string;
  };
  anchors: {
    mouth?: { x: number; y: number };
    glasses?: { x: number; y: number };
    arm_pivot?: { x: number; y: number };
  };
}

export interface ModernArchivistEpisode extends Record<string, unknown> {
  episode_id: string;
  title: string;
  duration_seconds: number;
  audio_src?: string;
  sections: EpisodeSection[];
  amplitude?: AudioAmplitudeSample[];
  puppet?: PuppetManifest;
}
