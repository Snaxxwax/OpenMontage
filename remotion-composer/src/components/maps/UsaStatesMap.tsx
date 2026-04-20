import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {ComposableMap, Geographies, Geography} from "react-simple-maps";
import usStatesTopology from "us-atlas/states-10m.json";

interface UsaStatesMapProps {
  title?: string;
  subtitle?: string;
  stateValues?: Record<string, number>;
  highlightedStateIds?: string[];
  colorStops?: string[];
  backgroundColor?: string;
  defaultFill?: string;
  borderColor?: string;
  textColor?: string;
  mutedTextColor?: string;
}

const lerpHex = (from: string, to: string, t: number) => {
  const parse = (value: string) => {
    const hex = value.replace("#", "");
    const normalized = hex.length === 3 ? hex.split("").map((c) => c + c).join("") : hex;
    const num = Number.parseInt(normalized, 16);
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255] as const;
  };
  const [r1, g1, b1] = parse(from);
  const [r2, g2, b2] = parse(to);
  const mix = (a: number, b: number) => Math.round(a + (b - a) * t);
  return `rgb(${mix(r1, r2)}, ${mix(g1, g2)}, ${mix(b1, b2)})`;
};

const mapValueToColor = (value: number, min: number, max: number, stops: string[]) => {
  if (max <= min) {
    return stops[stops.length - 1] ?? "#3ECFB2";
  }
  const progress = Math.max(0, Math.min(1, (value - min) / (max - min)));
  if (stops.length <= 1) {
    return stops[0] ?? "#3ECFB2";
  }
  const segments = stops.length - 1;
  const scaled = progress * segments;
  const index = Math.min(Math.floor(scaled), segments - 1);
  const localT = scaled - index;
  return lerpHex(stops[index]!, stops[index + 1]!, localT);
};

export const UsaStatesMap: React.FC<UsaStatesMapProps> = ({
  title,
  subtitle,
  stateValues = {},
  highlightedStateIds = [],
  colorStops = ["#E8EAED", "#3ECFB2", "#FF2D6B"],
  backgroundColor = "#0F1623",
  defaultFill = "#1C2333",
  borderColor = "rgba(232, 234, 237, 0.18)",
  textColor = "#E8EAED",
  mutedTextColor = "#5A6478",
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const fadeIn = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = fadeIn * fadeOut;

  const values = Object.values(stateValues);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const highlighted = new Set(highlightedStateIds.map(String));

  return (
    <AbsoluteFill style={{background: backgroundColor}}>
      <svg viewBox="0 0 1920 1080" style={{width: "100%", height: "100%"}}>
        {title ? (
          <text
            x={960}
            y={92}
            textAnchor="middle"
            fill={textColor}
            fontSize={54}
            fontWeight={800}
            opacity={opacity}
            style={{letterSpacing: "-0.02em"}}
          >
            {title}
          </text>
        ) : null}
        {subtitle ? (
          <text
            x={960}
            y={146}
            textAnchor="middle"
            fill={mutedTextColor}
            fontSize={26}
            fontWeight={500}
            opacity={opacity}
          >
            {subtitle}
          </text>
        ) : null}
        <foreignObject x="120" y="200" width="1680" height="760">
          <div style={{width: "100%", height: "100%", opacity}}>
            <ComposableMap
              projection="geoAlbersUsa"
              width={1680}
              height={760}
              style={{width: "100%", height: "100%"}}
            >
              <Geographies geography={usStatesTopology as object}>
                {({geographies}: {geographies: any[]}) =>
                  geographies.map((geo: any) => {
                    const id = String(geo.id);
                    const rawValue = stateValues[id];
                    const isHighlighted = highlighted.has(id);
                    const fill =
                      rawValue === undefined
                        ? defaultFill
                        : mapValueToColor(rawValue, min, max, colorStops);
                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        style={{
                          default: {
                            fill,
                            stroke: borderColor,
                            strokeWidth: isHighlighted ? 2.4 : 0.9,
                            outline: "none",
                            filter: isHighlighted
                              ? "drop-shadow(0 0 10px rgba(255, 45, 107, 0.28))"
                              : "none",
                          },
                          hover: {fill, stroke: borderColor, outline: "none"},
                          pressed: {fill, stroke: borderColor, outline: "none"},
                        }}
                      />
                    );
                  })
                }
              </Geographies>
            </ComposableMap>
          </div>
        </foreignObject>
      </svg>
    </AbsoluteFill>
  );
};
