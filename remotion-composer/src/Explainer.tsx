import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/SpaceGrotesk";

// Resolve asset path — handle URLs, absolute paths (Windows/Unix), and public/ relative paths
function resolveAsset(src: string): string {
  if (src.startsWith("http://") || src.startsWith("https://") || src.startsWith("data:")) {
    return src;
  }
  // Strip any file:// prefix
  const clean = src.replace(/^file:\/\/\/?/, "");
  // Absolute paths (Unix: /foo, Windows: C:\foo or C:/foo) — convert to file:// URI
  // staticFile() only accepts relative paths within public/, so absolute paths must bypass it
  if (clean.startsWith("/") || /^[A-Za-z]:[\\/]/.test(clean)) {
    return `file:///${clean.replace(/\\/g, "/")}`;
  }
  return staticFile(clean);
}
import { TextCard } from "./components/TextCard";
import { StatCard } from "./components/StatCard";
import { CalloutBox } from "./components/CalloutBox";
import { ComparisonCard } from "./components/ComparisonCard";
import { BarChart } from "./components/charts/BarChart";
import { LineChart } from "./components/charts/LineChart";
import { PieChart } from "./components/charts/PieChart";
import { KPIGrid } from "./components/charts/KPIGrid";
import { ProgressBar } from "./components/ProgressBar";
import { CaptionOverlay, WordCaption } from "./components/CaptionOverlay";
import { SectionTitle } from "./components/SectionTitle";
import { StatReveal } from "./components/StatReveal";
import { HeroTitle } from "./components/HeroTitle";
import { AnimeScene } from "./components/AnimeScene";
import type { CameraMotion } from "./components/AnimeScene";
import { TerminalScene } from "./components/TerminalScene";
import type { TerminalStep } from "./components/TerminalScene";
import { ScreenshotScene } from "./components/ScreenshotScene";
import type { ScreenshotStep } from "./components/ScreenshotScene";
import { ProviderChip } from "./components/ProviderChip";
import type { ParticleType } from "./components/ParticleOverlay";
import { resolveTheme, type ThemeConfig, DEFAULT_THEME } from "./Root";

// Load Space Grotesk font for cinematic typography
const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});

// ---------------------------------------------------------------------------
// Animated Background — Gradient Mesh + Floating Orbs
// ---------------------------------------------------------------------------

// Parse hex color to RGB components
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const clean = hex.replace("#", "");
  const bigint = parseInt(clean.length === 3
    ? clean.split("").map(c => c + c).join("")
    : clean, 16);
  return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
}

// Detect if a color is "light" (for choosing grid/overlay treatment)
function isLightColor(hex: string): boolean {
  const { r, g, b } = hexToRgb(hex);
  return (r * 299 + g * 587 + b * 114) / 1000 > 128;
}

// Darken/lighten a color by mixing toward black or white
function shiftColor(hex: string, amount: number): string {
  const { r, g, b } = hexToRgb(hex);
  const clamp = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
  if (amount < 0) {
    // Darken
    const f = 1 + amount;
    return `rgb(${clamp(r * f)}, ${clamp(g * f)}, ${clamp(b * f)})`;
  }
  // Lighten
  return `rgb(${clamp(r + (255 - r) * amount)}, ${clamp(g + (255 - g) * amount)}, ${clamp(b + (255 - b) * amount)})`;
}

const AnimatedBackground: React.FC<{ theme: ThemeConfig }> = ({ theme }) => {
  // Flat near-black fill — systemic-pulse brand: no animated orbs, no gradients.
  // Static grid at 2% opacity gives documentary texture without GPU cost.
  const bg = theme.backgroundColor;
  return (
    <AbsoluteFill style={{ background: bg }}>
      {/* Static grid — 2% opacity, zero animation cost */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Types — aligned with edit_decisions artifact schema
// ---------------------------------------------------------------------------

interface Cut {
  id: string;
  source: string;
  in_seconds: number;
  out_seconds: number;
  layer?: string;
  type?: string;
  // Component-specific props
  text?: string;
  stat?: string;
  subtitle?: string;
  callout_type?: "info" | "warning" | "tip" | "quote";
  title?: string;
  // Video source trim — seek to this point in the source before playback.
  // Defaults to 0 (play from beginning). Use this instead of in_seconds for source trimming.
  source_in_seconds?: number;
  // Comparison props
  leftLabel?: string;
  rightLabel?: string;
  leftValue?: string;
  rightValue?: string;
  // Chart props
  chartData?: any[];
  chartSeries?: any[];
  chartColors?: string[];
  chartAnimation?: string;
  donut?: boolean;
  centerLabel?: string;
  centerValue?: string;
  showGrid?: boolean;
  showValues?: boolean;
  showLegend?: boolean;
  showMarkers?: boolean;
  xLabel?: string;
  yLabel?: string;
  columns?: 2 | 3 | 4;
  // Progress bar props
  progress?: number;
  progressLabel?: string;
  progressColor?: string;
  progressAnimation?: string;
  progressSegments?: any[];
  // Hero title props (when used as scene, not overlay)
  heroSubtitle?: string;
  // Styling overrides
  backgroundColor?: string;
  backgroundImage?: string; // AI-generated or stock image rendered behind the component
  backgroundVideo?: string; // Video clip rendered behind the component (takes priority over backgroundImage)
  backgroundVideoStart?: number; // Seek position in seconds for background video (default 0)
  backgroundOverlay?: number; // Opacity of dark overlay on backgroundImage/backgroundVideo (0-1, default 0.55)
  color?: string;
  accentColor?: string;
  fontSize?: number;
  // Animation & transitions
  animation?: string;
  transition_in?: string;
  transition_out?: string;
  reason?: string;
  transform?: {
    animation?: string;
    scale?: number;
    position?: string | { x: number; y: number };
  };
  // Anime scene props (type: "anime_scene")
  images?: string[];
  particles?: ParticleType;
  particleColor?: string;
  particleCount?: number;
  particleIntensity?: number;
  vignette?: boolean;
  lightingFrom?: string;
  lightingTo?: string;
  // Terminal scene props (type: "terminal_scene")
  steps?: TerminalStep[];
  terminalTitle?: string;
  prompt?: string;
  // Screenshot scene props (type: "screenshot_scene")
  screenshotSteps?: ScreenshotStep[];
  screenshotSize?: { width: number; height: number };
  cursorStartAt?: [number, number];
}

interface Overlay {
  type: "section_title" | "stat_reveal" | "hero_title" | "provider_chip";
  in_seconds: number;
  out_seconds: number;
  text?: string;
  subtitle?: string;
  accentColor?: string;
  position?: string;
  // provider_chip
  providers?: string[];
  cycleSeconds?: number;
  label?: string;
}

interface AudioLayer {
  src: string;
  volume?: number;
}

interface AudioConfig {
  narration?: AudioLayer;
  music?: AudioLayer & {
    fadeInSeconds?: number;
    fadeOutSeconds?: number;
    /** Start playback from this offset in seconds (skip quiet intros).
     *  Use the audio_energy tool to find the optimal offset. */
    offsetSeconds?: number;
    /** Loop the music if it's shorter than the video duration. */
    loop?: boolean;
  };
}

export interface ExplainerProps {
  [key: string]: unknown;
  cuts: Cut[];
  overlays?: Overlay[];
  captions?: WordCaption[];
  audio?: AudioConfig;
}

// ---------------------------------------------------------------------------
// Image Extensions
// ---------------------------------------------------------------------------

const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"];
const VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".avi", ".mkv"];

function isImage(source: string): boolean {
  const lower = source.toLowerCase();
  return IMAGE_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function isVideo(source: string): boolean {
  const lower = source.toLowerCase();
  return VIDEO_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function isRouteSpec(source: string): boolean {
  return source.toLowerCase().endsWith(".json");
}

// ---------------------------------------------------------------------------
// Cinematic vignette overlay
// ---------------------------------------------------------------------------

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.6) 100%)",
      pointerEvents: "none",
    }}
  />
);

// ---------------------------------------------------------------------------
// Enhanced Image Scene — spring physics, parallax, variety
// ---------------------------------------------------------------------------

const ImageScene: React.FC<{ src: string; animation?: string }> = ({
  src,
  animation,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Smooth spring fade-in
  const fadeIn = spring({ frame, fps, config: { damping: 18, stiffness: 80 } });

  // Fade-out for crossfade effect
  const fadeOutStart = durationInFrames - 8;
  const fadeOut = interpolate(frame, [fadeOutStart, durationInFrames], [1, 0.3], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  let scale = 1;
  let translateX = 0;
  let translateY = 0;
  const anim = animation || "zoom-in";

  // Progress with easing — smoother than linear
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (anim === "zoom-in") {
    scale = 1 + progress * 0.18;
  } else if (anim === "zoom-out") {
    scale = 1.18 - progress * 0.18;
  } else if (anim === "pan-left") {
    translateX = interpolate(progress, [0, 1], [40, -40]);
    scale = 1.15;
  } else if (anim === "pan-right") {
    translateX = interpolate(progress, [0, 1], [-40, 40]);
    scale = 1.15;
  } else if (anim === "ken-burns" || anim === "ken-burns-slow-zoom") {
    // Cinematic Ken Burns: gentle zoom + diagonal drift
    scale = 1 + progress * 0.22;
    translateX = interpolate(progress, [0, 1], [0, -25]);
    translateY = interpolate(progress, [0, 1], [0, -15]);
  } else if (anim === "parallax") {
    // Subtle parallax — foreground moves faster
    translateY = interpolate(progress, [0, 1], [15, -15]);
    scale = 1.1;
  }
  // "static" or "none" → just display

  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#0F172A" }}>
      <Img
        src={resolveAsset(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity: fadeIn * fadeOut,
          transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
          willChange: "transform, opacity",
        }}
      />
      <Vignette />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Enhanced Video Scene
// ---------------------------------------------------------------------------

const VideoScene: React.FC<{ src: string; startFrom?: number; animation?: string }> = ({
  src,
  startFrom = 0,
  animation,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // "hard" animation = no fade in or out — true hard cut at scene boundaries
  const hardCut = animation === "hard" || animation === "hard_cut";
  const fadeIn = hardCut ? 1 : spring({ frame, fps, config: { damping: 20 } });
  const fadeOutStart = durationInFrames - 8;
  const fadeOut = hardCut ? 1 : interpolate(frame, [fadeOutStart, durationInFrames], [1, 0.3], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "#0F172A" }}>
      <OffthreadVideo
        src={resolveAsset(src)}
        startFrom={Math.round(startFrom * fps)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity: fadeIn * fadeOut,
        }}
        muted
      />
      <Vignette />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Route Scene — Asymmetric app-store documentary grammar
// ---------------------------------------------------------------------------

const RouteScene: React.FC<{ cut: Cut; theme: ThemeConfig }> = ({ cut, theme }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const phase = Math.floor(progress * 6);
  const routeDraw = interpolate(frame, [0, Math.max(1, durationInFrames * 0.42)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const pulse = (frame % Math.round(fps * 1.2)) / Math.round(fps * 1.2);
  const impact = spring({ frame: frame - Math.round(durationInFrames * 0.18), fps, config: { damping: 14, stiffness: 130 } });

  const reason = cut.reason || cut.transform?.animation || cut.id;
  const sceneLabel = cut.id.replace("cut-", "SCENE ");
  const payoffMatch = reason.match(/(THE ROUTE IS THE PRODUCT|THE ROUTE TO USERS IS THE LEVER)/i);
  const exactPayoff = payoffMatch?.[1]?.toUpperCase();
  const isPayoff = Boolean(exactPayoff);
  const beatAction = reason.match(
    /story beat:\s*(Reveal|Collapse|Compare|Prove|Route|Lock|Show consequence):?\s*([^.;]*)/i,
  );
  const action = beatAction?.[1]?.toUpperCase() || (cut.title || cut.id).toUpperCase();
  const actionDetail = beatAction?.[2] || "";
  const stateLabel =
    /developer|pulse|straight route|direct route/i.test(actionDetail)
      ? "DIRECT ROUTE APPEARS"
      : /gate|permission|review|warning|pay/i.test(actionDetail)
        ? "GATE DROPS"
        : /toll|fee|commission|payment/i.test(actionDetail)
          ? "TOLL APPEARS"
          : /collapse|compress|squeeze/i.test(actionDetail)
            ? "ROUTE COMPRESSES"
            : /compare|fork|alternative/i.test(actionDetail)
              ? "ROUTES SPLIT"
              : /lock|blocked|stop/i.test(actionDetail)
                ? "ROUTE LOCKS"
                : "ROUTE CHANGES STATE";
  const beatText = `${action}: ${stateLabel}`;
  const amber = cut.accentColor || theme.accentColor || "#FFB84D";
  const route = theme.primaryColor || "#39A7FF";
  const bg = "#071018";
  const text = "#F7FAFC";

  const nodes = [
    { x: 210, y: 565, label: "DEV" },
    { x: 520, y: phase >= 1 ? 450 : 565, label: phase >= 1 ? "REVIEW" : "APP" },
    { x: 850, y: phase >= 2 ? 642 : 520, label: phase >= 2 ? "PAY" : "STORE" },
    { x: 1190, y: phase >= 3 ? 430 : 565, label: phase >= 3 ? "WARN" : "TRUST" },
    { x: 1590, y: 560, label: "USER" },
  ];

  const path = `M ${nodes[0].x} ${nodes[0].y} C 390 ${nodes[0].y - 180}, 440 ${nodes[1].y}, ${nodes[1].x} ${nodes[1].y} S 690 ${nodes[2].y}, ${nodes[2].x} ${nodes[2].y} S 1030 ${nodes[3].y}, ${nodes[3].x} ${nodes[3].y} S 1400 ${nodes[4].y}, ${nodes[4].x} ${nodes[4].y}`;
  const altOpacity = interpolate(progress, [0.34, 0.48, 0.86], [0, 0.85, 0.35], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const gateScale = 0.9 + Math.sin(frame / 9) * 0.035;
  const cameraScale = 1 + Math.sin(progress * Math.PI) * 0.035;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 48%, rgba(57,167,255,0.12), transparent 34%), linear-gradient(135deg, ${bg}, #0B1722 52%, #05080D)`,
        color: text,
        overflow: "hidden",
        fontFamily: theme.headingFont,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          transform: `translateY(${(frame % 72) * -0.16}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 58,
          top: 48,
          fontSize: 24,
          letterSpacing: 0,
          color: "rgba(247,250,252,0.66)",
          fontWeight: 700,
        }}
      >
        ASYMMETRIC / ROUTE TO USERS
      </div>
      <div
        style={{
          position: "absolute",
          right: 64,
          top: 50,
          fontSize: 22,
          color: "rgba(247,250,252,0.52)",
          fontFamily: theme.monoFont,
        }}
      >
        {sceneLabel}
      </div>

      <svg
        viewBox="0 0 1920 1080"
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${cameraScale})`,
          transformOrigin: "50% 54%",
        }}
      >
        <defs>
          <filter id={`glow-${cut.id}`} x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="8" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <marker id={`arrow-${cut.id}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill={route} />
          </marker>
        </defs>

        <path d={path} fill="none" stroke="rgba(255,255,255,0.13)" strokeWidth="18" strokeLinecap="round" />
        <path
          d={path}
          fill="none"
          stroke={route}
          strokeWidth="9"
          strokeLinecap="round"
          markerEnd={`url(#arrow-${cut.id})`}
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - routeDraw}
          filter={`url(#glow-${cut.id})`}
        />

        <path
          d="M 450 740 C 650 890, 1120 850, 1450 715"
          fill="none"
          stroke={amber}
          strokeWidth="5"
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray="0.025 0.025"
          strokeDashoffset={1 - routeDraw}
          opacity={altOpacity}
        />

        {nodes.map((node, i) => {
          const appear = interpolate(progress, [i * 0.08, i * 0.08 + 0.12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const isControl = i > 0 && i < nodes.length - 1;
          return (
            <g key={node.label} opacity={appear}>
              <circle
                cx={node.x}
                cy={node.y}
                r={isControl ? 54 * gateScale : 46}
                fill={isControl ? "rgba(255,184,77,0.13)" : "rgba(57,167,255,0.16)"}
                stroke={isControl ? amber : route}
                strokeWidth={4}
              />
              {isControl && (
                <rect
                  x={node.x - 34}
                  y={node.y - 48}
                  width={68}
                  height={96}
                  rx={10}
                  fill="rgba(7,16,24,0.92)"
                  stroke={amber}
                  strokeWidth={3}
                />
              )}
              <text x={node.x} y={node.y + (isControl ? 86 : 78)} textAnchor="middle" fill={text} fontSize="25" fontWeight="700">
                {node.label}
              </text>
            </g>
          );
        })}

        <circle
          cx={210 + pulse * 1380}
          cy={565 + Math.sin(pulse * Math.PI * 2 + phase) * 72}
          r={18 + impact * 8}
          fill={text}
          opacity={0.88}
          filter={`url(#glow-${cut.id})`}
        />
      </svg>

      <div
        style={{
          position: "absolute",
          left: 150,
          right: 150,
          ...(isPayoff ? { bottom: 360 } : { top: 168 }),
          fontSize: isPayoff ? 76 : 30,
          lineHeight: 1.05,
          fontWeight: 800,
          textAlign: "center",
          color: text,
          textShadow: "0 0 28px rgba(57,167,255,0.34)",
          opacity: interpolate(progress, [0.08, 0.22], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {isPayoff ? exactPayoff || "THE ROUTE TO USERS IS THE LEVER" : beatText}
      </div>

      <div
        style={{
          position: "absolute",
          left: 140,
          right: 140,
          bottom: 54,
          height: 5,
          background: "rgba(255,255,255,0.10)",
          borderRadius: 999,
          overflow: "hidden",
        }}
      >
        <div style={{ width: `${progress * 100}%`, height: "100%", background: `linear-gradient(90deg, ${route}, ${amber})` }} />
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Scene renderer — maps cut type / source to the right component
// ---------------------------------------------------------------------------

// Background image layer — renders an AI-generated/stock image behind data components
const BackgroundImageLayer: React.FC<{
  src: string;
  overlayOpacity?: number;
  children: React.ReactNode;
}> = ({ src, overlayOpacity = 0.55, children }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Subtle ken-burns on the background
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bgScale = 1 + progress * 0.08;

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {/* Background image with subtle zoom */}
      <Img
        src={resolveAsset(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${bgScale})`,
          willChange: "transform",
        }}
      />
      {/* Dark overlay for readability */}
      <AbsoluteFill
        style={{
          background: `rgba(15, 23, 42, ${overlayOpacity})`,
        }}
      />
      {/* Component content on top */}
      {children}
    </AbsoluteFill>
  );
};

// Background video layer — plays a looping video behind component content with dark overlay
const BackgroundVideoLayer: React.FC<{
  src: string;
  startFrom?: number;
  overlayOpacity?: number;
  children: React.ReactNode;
}> = ({ src, startFrom = 0, overlayOpacity = 0.55, children }) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {/* Background video */}
      <OffthreadVideo
        src={resolveAsset(src)}
        startFrom={Math.round(startFrom * fps)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
        muted
      />
      {/* Dark overlay for readability */}
      <AbsoluteFill
        style={{
          background: `rgba(15, 23, 42, ${overlayOpacity})`,
        }}
      />
      {/* Component content on top */}
      {children}
    </AbsoluteFill>
  );
};

const SceneRenderer: React.FC<{ cut: Cut; theme: ThemeConfig }> = ({ cut, theme }) => {
  // Wrap component with background video or image if specified
  const maybeWrapWithBg = (element: React.ReactElement) => {
    if (cut.backgroundVideo) {
      return (
        <BackgroundVideoLayer
          src={cut.backgroundVideo}
          startFrom={cut.backgroundVideoStart ?? 0}
          overlayOpacity={cut.backgroundOverlay ?? 0.55}
        >
          {element}
        </BackgroundVideoLayer>
      );
    }
    if (cut.backgroundImage) {
      return (
        <BackgroundImageLayer
          src={cut.backgroundImage}
          overlayOpacity={cut.backgroundOverlay ?? 0.55}
        >
          {element}
        </BackgroundImageLayer>
      );
    }
    return element;
  };

  // Resolve the scene element based on cut type, then wrap with backgroundImage if set
  // Use transparent bg so the animated gradient background shows through
  // When no explicit backgroundColor on the cut, inherit from theme
  const rawBg = (cut.backgroundImage || cut.backgroundVideo) ? "transparent" : (cut.backgroundColor || theme.surfaceColor);
  const bgColor = (rawBg === theme.backgroundColor || rawBg === "#0F172A" || rawBg === "#0f172a") ? "transparent" : rawBg;
  const textColor = cut.color || theme.textColor;
  const accent = cut.accentColor || theme.accentColor;

  // Explicit component types — use theme-derived defaults for colors
  if (cut.type === "text_card" && cut.text) {
    return maybeWrapWithBg(
      <TextCard text={cut.text} fontSize={cut.fontSize} color={textColor} backgroundColor={bgColor} />
    );
  }
  if (cut.type === "stat_card" && cut.stat) {
    return maybeWrapWithBg(
      <StatCard stat={cut.stat} subtitle={cut.subtitle} accentColor={accent} backgroundColor={bgColor} />
    );
  }
  if (cut.type === "callout" && cut.text) {
    return maybeWrapWithBg(
      <CalloutBox
        text={cut.text} type={cut.callout_type} title={cut.title}
        borderColor={accent} backgroundColor={cut.backgroundColor || theme.surfaceColor}
        textColor={textColor} containerBackgroundColor={bgColor}
      />
    );
  }
  if (cut.type === "comparison" && cut.leftLabel && cut.rightLabel && cut.leftValue && cut.rightValue) {
    return maybeWrapWithBg(
      <ComparisonCard
        leftLabel={cut.leftLabel} rightLabel={cut.rightLabel}
        leftValue={cut.leftValue} rightValue={cut.rightValue}
        title={cut.title} backgroundColor={bgColor} textColor={textColor}
      />
    );
  }
  if (cut.type === "hero_title" && cut.text) {
    return maybeWrapWithBg(
      <HeroTitle title={cut.text} subtitle={cut.heroSubtitle || cut.subtitle} />
    );
  }
  if (cut.type === "terminal_scene" && cut.steps) {
    return maybeWrapWithBg(
      <TerminalScene
        title={cut.terminalTitle || "Terminal"}
        steps={cut.steps as TerminalStep[]}
        prompt={cut.prompt}
        accentColor={accent}
        backgroundColor={bgColor || theme.backgroundColor}
      />
    );
  }
  if (cut.type === "screenshot_scene" && cut.backgroundImage && cut.screenshotSteps) {
    return (
      <ScreenshotScene
        backgroundImage={cut.backgroundImage}
        backgroundSize={cut.screenshotSize}
        steps={cut.screenshotSteps as ScreenshotStep[]}
        accentColor={accent}
        cursorStartAt={cut.cursorStartAt}
      />
    );
  }

  // --- Chart types — use theme.chartColors as default palette ---
  if (cut.type === "bar_chart" && cut.chartData) {
    return maybeWrapWithBg(
      <BarChart
        data={cut.chartData} title={cut.title} colors={cut.chartColors || theme.chartColors}
        animationStyle={(cut.chartAnimation as any) || "grow-up"}
        showGrid={cut.showGrid} showValues={cut.showValues} backgroundColor={bgColor}
      />
    );
  }
  if (cut.type === "line_chart" && cut.chartSeries) {
    return maybeWrapWithBg(
      <LineChart
        series={cut.chartSeries} title={cut.title} colors={cut.chartColors || theme.chartColors}
        animationStyle={(cut.chartAnimation as any) || "draw"}
        showGrid={cut.showGrid} showMarkers={cut.showMarkers} showLegend={cut.showLegend}
        xLabel={cut.xLabel} yLabel={cut.yLabel} backgroundColor={bgColor}
      />
    );
  }
  if (cut.type === "pie_chart" && cut.chartData) {
    return maybeWrapWithBg(
      <PieChart
        data={cut.chartData} title={cut.title} colors={cut.chartColors || theme.chartColors}
        animationStyle={(cut.chartAnimation as any) || "expand"}
        donut={cut.donut} centerLabel={cut.centerLabel} centerValue={cut.centerValue}
        showLegend={cut.showLegend} backgroundColor={bgColor}
      />
    );
  }
  if (cut.type === "kpi_grid" && cut.chartData) {
    return maybeWrapWithBg(
      <KPIGrid
        metrics={cut.chartData} title={cut.title} columns={cut.columns}
        colors={cut.chartColors || theme.chartColors} animationStyle={(cut.chartAnimation as any) || "count-up"}
        backgroundColor={bgColor}
      />
    );
  }
  if (cut.type === "progress_bar" && cut.progress !== undefined) {
    return maybeWrapWithBg(
      <AbsoluteFill
        style={{
          background: bgColor || theme.surfaceColor,
          display: "flex", alignItems: "center", justifyContent: "center",
          padding: "80px 120px",
        }}
      >
        {cut.title && (
          <div style={{
            position: "absolute", top: 120, fontSize: 48, fontWeight: 700,
            color: textColor, textAlign: "center", width: "100%",
          }}>
            {cut.title}
          </div>
        )}
        <ProgressBar
          progress={cut.progress} label={cut.progressLabel}
          color={cut.progressColor || accent}
          animationStyle={(cut.progressAnimation as any) || "fill"}
          segments={cut.progressSegments} backgroundColor={cut.backgroundColor || theme.surfaceColor}
        />
      </AbsoluteFill>
    );
  }

  // --- Anime scene (multi-image crossfade + particles) ---
  if (cut.type === "anime_scene" && cut.images && cut.images.length > 0) {
    return (
      <AnimeScene
        images={cut.images}
        animation={(cut.animation as CameraMotion) || "ken-burns"}
        particles={cut.particles}
        particleColor={cut.particleColor}
        particleCount={cut.particleCount}
        particleIntensity={cut.particleIntensity}
        backgroundColor={cut.backgroundColor}
        vignette={cut.vignette ?? true}
        lightingFrom={cut.lightingFrom}
        lightingTo={cut.lightingTo}
        sceneDurationSeconds={cut.out_seconds - cut.in_seconds}
      />
    );
  }

  // --- Media types (image / video fallback) ---
  const animation = cut.animation || cut.transform?.animation;

  if ((cut.type === "route_scene" || (cut.source && isRouteSpec(cut.source)))) {
    return maybeWrapWithBg(<RouteScene cut={cut} theme={theme} />);
  }

  if (cut.source && isImage(cut.source)) {
    return maybeWrapWithBg(<ImageScene src={cut.source} animation={animation} />);
  }

  if (cut.source && isVideo(cut.source)) {
    return maybeWrapWithBg(<VideoScene src={cut.source} startFrom={cut.source_in_seconds ?? 0} animation={animation} />);
  }

  // Final fallback — try as image if source exists, otherwise show text_card
  if (cut.source) {
    return maybeWrapWithBg(<ImageScene src={cut.source} animation={animation} />);
  }

  // No source, no type — render as text card with cut id as fallback
  return <TextCard text={cut.text || cut.id} color={textColor} backgroundColor={bgColor} />;
};

// ---------------------------------------------------------------------------
// Overlay renderer
// ---------------------------------------------------------------------------

const OverlayRenderer: React.FC<{ overlay: Overlay }> = ({ overlay }) => {
  if (overlay.type === "section_title") {
    return (
      <SectionTitle
        title={overlay.text || ""}
        subtitle={overlay.subtitle}
        accentColor={overlay.accentColor}
        position={(overlay.position as any) || "top-left"}
      />
    );
  }
  if (overlay.type === "stat_reveal") {
    return (
      <StatReveal
        stat={overlay.text || ""}
        label={overlay.subtitle}
        accentColor={overlay.accentColor}
        position={(overlay.position as any) || "bottom-right"}
      />
    );
  }
  if (overlay.type === "hero_title") {
    return <HeroTitle title={overlay.text || ""} subtitle={overlay.subtitle} />;
  }
  if (overlay.type === "provider_chip" && overlay.providers) {
    return (
      <ProviderChip
        providers={overlay.providers as string[]}
        cycleSeconds={overlay.cycleSeconds}
        position={(overlay.position as any) || "bottom-right"}
        accentColor={overlay.accentColor}
        label={overlay.label}
      />
    );
  }
  return null;
};

// ---------------------------------------------------------------------------
// Main composition
// ---------------------------------------------------------------------------

export const Explainer: React.FC<ExplainerProps> = (props) => {
  const { cuts, overlays, captions, audio } = props;
  const { fps, durationInFrames } = useVideoConfig();

  // Resolve theme from props — playbook name, theme name, or custom themeConfig
  const theme = resolveTheme(props as Record<string, unknown>);

  return (
    <AbsoluteFill style={{ background: theme.backgroundColor, fontFamily: theme.headingFont || fontFamily }}>
      {/* Layer 0: Animated gradient background — driven by theme */}
      <AnimatedBackground theme={theme} />

      {/* Layer 1: Visual scenes */}
      {cuts.map((cut) => {
        const from = Math.round(cut.in_seconds * fps);
        const duration = Math.round((cut.out_seconds - cut.in_seconds) * fps);

        return (
          <Sequence key={cut.id} from={from} durationInFrames={duration}>
            <SceneRenderer cut={cut} theme={theme} />
          </Sequence>
        );
      })}

      {/* Layer 2: Overlays (section titles, stat reveals, hero titles) */}
      {overlays?.map((overlay, i) => {
        const from = Math.round(overlay.in_seconds * fps);
        const duration = Math.round(
          (overlay.out_seconds - overlay.in_seconds) * fps
        );

        return (
          <Sequence key={`overlay-${i}`} from={from} durationInFrames={duration}>
            <OverlayRenderer overlay={overlay} />
          </Sequence>
        );
      })}

      {/* Layer 3: Captions (word-by-word highlight) */}
      {captions && captions.length > 0 && (
        <CaptionOverlay
          words={captions}
          wordsPerPage={6}
          fontSize={42}
          highlightColor={theme.captionHighlightColor}
          backgroundColor={theme.captionBackgroundColor}
        />
      )}

      {/* Layer 4: Audio — narration */}
      {audio?.narration?.src && (
        <Audio src={resolveAsset(audio.narration.src)} volume={audio.narration.volume ?? 1} />
      )}

      {/* Layer 4: Audio — music with offset, fade in/out, and optional loop */}
      {audio?.music?.src && (
        <Audio
          src={resolveAsset(audio.music.src)}
          startFrom={Math.round((audio.music.offsetSeconds ?? 0) * fps)}
          loop={audio.music.loop ?? false}
          loopVolumeCurveBehavior="repeat"
          volume={(f) => {
            const baseVol = audio.music!.volume ?? 0.1;
            const fadeInDur = (audio.music!.fadeInSeconds ?? 2) * fps;
            const fadeOutDur = (audio.music!.fadeOutSeconds ?? 3) * fps;
            const totalFrames = durationInFrames;

            // Fade in
            const fadeIn = interpolate(f, [0, fadeInDur], [0, baseVol], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            // Fade out
            const fadeOut = interpolate(
              f,
              [totalFrames - fadeOutDur, totalFrames],
              [baseVol, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            return Math.min(fadeIn, fadeOut);
          }}
        />
      )}
    </AbsoluteFill>
  );
};
