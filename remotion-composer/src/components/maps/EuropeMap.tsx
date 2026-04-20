import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {ComposableMap, Geographies, Geography} from "react-simple-maps";
import europeTopology from "world-atlas/countries-110m.json";

interface EuropeMapProps {
  title?: string;
  subtitle?: string;
  countryValues?: Record<string, number>;
  highlightedCountryNames?: string[];
  colorStops?: string[];
  backgroundColor?: string;
  defaultFill?: string;
  borderColor?: string;
  textColor?: string;
  mutedTextColor?: string;
}

const EUROPE_COUNTRIES = new Set([
  "albania", "andorra", "austria", "belarus", "belgium", "bosnia and herzegovina",
  "bulgaria", "croatia", "czech republic", "czechia", "denmark", "estonia", "finland",
  "france", "germany", "greece", "hungary", "iceland", "ireland", "italy", "kosovo",
  "latvia", "liechtenstein", "lithuania", "luxembourg", "malta", "moldova", "monaco",
  "montenegro", "netherlands", "north macedonia", "norway", "poland", "portugal",
  "romania", "russia", "san marino", "serbia", "slovakia", "slovenia", "spain",
  "sweden", "switzerland", "ukraine", "united kingdom", "vatican city", "vatican",
]);

const normalizeName = (value: string) =>
  value
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();

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

export const EuropeMap: React.FC<EuropeMapProps> = ({
  title,
  subtitle,
  countryValues = {},
  highlightedCountryNames = [],
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

  const normalizedCountryValues = Object.fromEntries(
    Object.entries(countryValues).map(([key, value]) => [normalizeName(key), value]),
  );
  const highlighted = new Set(highlightedCountryNames.map(normalizeName));
  const values = Object.values(normalizedCountryValues);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;

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
        <foreignObject x="140" y="180" width="1640" height="780">
          <div style={{width: "100%", height: "100%", opacity}}>
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{center: [18, 55], scale: 720}}
              width={1640}
              height={780}
              style={{width: "100%", height: "100%"}}
            >
              <Geographies geography={europeTopology as object}>
                {({geographies}: {geographies: any[]}) =>
                  geographies
                    .filter((geo) => {
                      const name = normalizeName(String(geo.properties?.name ?? ""));
                      return EUROPE_COUNTRIES.has(name);
                    })
                    .map((geo: any) => {
                      const name = normalizeName(String(geo.properties?.name ?? ""));
                      const rawValue = normalizedCountryValues[name];
                      const isHighlighted = highlighted.has(name);
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
