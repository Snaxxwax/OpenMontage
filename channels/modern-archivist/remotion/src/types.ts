export type LayoutState =
  | "STATE_MONOLOGUE"
  | "STATE_DEEP_DIVE"
  | "STATE_CRITICAL_ERROR";

export type NarrativePhase =
  | "hook"
  | "context"
  | "deep_dive"
  | "pattern_interrupt"
  | "why_it_matters"
  | "outro";

export type RetentionDevice =
  | "cold_open_shock"
  | "mystery_gap"
  | "contradiction_reveal"
  | "compression_montage"
  | "pattern_interrupt"
  | "comic_release"
  | "stakes_escalation"
  | "visual_reset"
  | "act_break"
  | "payoff"
  | "evidence_receipt"
  | "mechanism_explanation";

export type VisualMode =
  | "monologue"
  | "case_file"
  | "cinematic_metaphor"
  | "failure_graph"
  | "code_walkthrough"
  | "data_sequence"
  | "critical_error"
  | "outro";

export type SectionLayout =
  | "anchor_center"
  | "media_full"
  | "split_screen_left"
  | "split_screen_right"
  | "evidence_board"
  | "quote_card"
  | "timeline"
  | "code_walkthrough"
  | "data_chart";

export type ColorState = "teal" | "red";

export type EvidenceRole =
  | "primary_evidence"
  | "secondary_evidence"
  | "derived_analysis"
  | "illustrative_only"
  | "brand_interstitial";

export interface CharacterCue {
  visible: boolean;
  action?: "hidden" | "idle" | "sip_coffee" | "deadpan_stare" | "glasses_flash" | string;
  expression?: "none" | "neutral" | "deadpan" | "skeptical" | "alarm" | string;
}

export interface MotionPlanStep {
  at_seconds: number;
  action: string;
  target?: string;
  label?: string;
}

export interface Provenance {
  source_id?: string;
  url?: string;
  publisher?: string;
  retrieved_at?: string;
  license?: string;
  note?: string;
}

interface MediaBase {
  id: string;
  kind: string;
  title?: string;
  evidence_role?: EvidenceRole;
  evidence_refs?: string[];
  provenance?: Provenance;
  motion_plan?: MotionPlanStep[];
  description?: string;
}

export type MediaItem =
  | (MediaBase & { kind: "code"; language?: string; content: string })
  | (MediaBase & { kind: "article"; source?: string; body: string; highlightTerms?: string[] })
  | (MediaBase & { kind: "quote"; quote: string; attribution?: string })
  | (MediaBase & { kind: "image"; src: string; caption?: string })
  | (MediaBase & { kind: "case_file_sequence"; title: string; beats?: Array<Record<string, unknown>>; stamp?: string })
  | (MediaBase & { kind: "cinematic_metaphor"; title: string; evidence_role: "illustrative_only"; mood?: string; asset_src?: string; label?: string })
  | (MediaBase & { kind: "failure_graph"; title: string; nodes?: Array<Record<string, unknown>>; links?: Array<Record<string, unknown>> })
  | (MediaBase & { kind: "kinetic_typography"; text?: string; phrases?: string[]; variant?: "glitch_slam" | "highlight_sweep" | "word_reveal" | string; attribution?: string })
  | (MediaBase & { kind: "data_sequence"; title: string; chart_type?: "line" | "bar" | string; data?: Array<Record<string, unknown>> })
  | (MediaBase & { kind: "code_walkthrough"; language?: string; filename?: string; content: string; highlights?: Array<Record<string, unknown>> })
  | (MediaBase & { kind: "source_montage"; title: string; sources?: Array<Record<string, unknown>> });

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
  narration?: string;
  tags: ScriptTag[];
  narrative_phase?: NarrativePhase;
  retention_device?: RetentionDevice;
  visual_mode?: VisualMode;
  layout?: SectionLayout;
  color_state?: ColorState;
  character?: CharacterCue;
  evidence_refs?: string[];
  evidence_role?: EvidenceRole;
  media_overlay?: MediaItem | Record<string, unknown>;
  estimated_duration_seconds?: number;
}

export interface AudioAmplitudeSample {
  time: number;
  volume: number;
}

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
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
  word_timings?: WordTimestamp[];
  puppet?: PuppetManifest;
  debug_disable_backdrop?: boolean;
  debug_disable_puppet?: boolean;
  debug_disable_media?: boolean;
  debug_disable_audio?: boolean;
}
