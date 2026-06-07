import React, { memo, useMemo } from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const BRAND = {
  teal: "#00D4AA",
  charcoal: "#1A1A2E",
  bone: "#F5F0E1",
  grey: "#6B7280",
  criticalRed: "#DC2626",
  successGreen: "#10B981",
  amber: "#F59E0B",
};

export type DataVisualizationType = "flow" | "org" | "network";
export type DataNodeShape = "entity" | "account" | "person" | "product" | "metric";
export type DataEdgeType = "flow" | "hierarchy" | "dependency" | "influence";
export type DataLayout = "horizontal" | "vertical" | "force" | "radial";

export type DataVisualizationNode = {
  id: string;
  label: string;
  type: DataNodeShape;
  x?: number;
  y?: number;
  level?: number;
  cluster?: string;
  critical?: boolean;
};

export type DataVisualizationEdge = {
  id?: string;
  source: string;
  target: string;
  label?: string;
  value?: number;
  valueLabel?: string;
  type?: DataEdgeType;
  critical?: boolean;
};

export type DataVisualizationProps = {
  type: DataVisualizationType;
  nodes: DataVisualizationNode[];
  edges: DataVisualizationEdge[];
  title?: string;
  subtitle?: string;
  layout?: DataLayout;
  activeNodeId?: string;
  accentColor?: string;
  backgroundColor?: string;
};

type Point = { x: number; y: number };
type LayoutNode = DataVisualizationNode & Point;

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const seededNoise = (seed: string) => {
  let hash = 2166136261;
  for (let index = 0; index < seed.length; index += 1) {
    hash ^= seed.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 10000) / 10000;
};

const splitLabel = (label: string, maxChars = 16) => {
  const words = label.split(" ");
  const lines: string[] = [];
  let current = "";

  words.forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  });

  if (current) {
    lines.push(current);
  }

  return lines.slice(0, 3);
};

const getNodeSize = (type: DataNodeShape) => {
  if (type === "person") {
    return { width: 86, height: 86 };
  }
  if (type === "account" || type === "metric") {
    return { width: 118, height: 72 };
  }
  if (type === "product") {
    return { width: 112, height: 112 };
  }
  return { width: 132, height: 66 };
};

const getNodeColors = (type: DataNodeShape) => {
  if (type === "account") {
    return { fill: BRAND.teal, stroke: BRAND.charcoal, text: BRAND.charcoal };
  }
  if (type === "person") {
    return { fill: BRAND.grey, stroke: BRAND.bone, text: BRAND.bone };
  }
  if (type === "product") {
    return { fill: BRAND.amber, stroke: BRAND.charcoal, text: BRAND.charcoal };
  }
  if (type === "metric") {
    return { fill: BRAND.criticalRed, stroke: BRAND.bone, text: BRAND.bone };
  }
  return { fill: BRAND.bone, stroke: BRAND.charcoal, text: BRAND.charcoal };
};

const nodeShapePath = (type: DataNodeShape, width: number, height: number) => {
  const halfW = width / 2;
  const halfH = height / 2;

  if (type === "account") {
    return `M ${-halfW + 22} ${-halfH} L ${halfW - 22} ${-halfH} L ${halfW} 0 L ${halfW - 22} ${halfH} L ${-halfW + 22} ${halfH} L ${-halfW} 0 Z`;
  }
  if (type === "product") {
    return `M 0 ${-halfH} L ${halfW} 0 L 0 ${halfH} L ${-halfW} 0 Z`;
  }
  if (type === "metric") {
    return `M ${-halfW + 22} ${-halfH} L ${halfW - 22} ${-halfH} L ${halfW} ${-halfH + 22} L ${halfW} ${halfH - 22} L ${halfW - 22} ${halfH} L ${-halfW + 22} ${halfH} L ${-halfW} ${halfH - 22} L ${-halfW} ${-halfH + 22} Z`;
  }
  return "";
};

const cubicPoint = (p0: Point, p1: Point, p2: Point, p3: Point, t: number): Point => {
  const u = 1 - t;
  return {
    x: u ** 3 * p0.x + 3 * u ** 2 * t * p1.x + 3 * u * t ** 2 * p2.x + t ** 3 * p3.x,
    y: u ** 3 * p0.y + 3 * u ** 2 * t * p1.y + 3 * u * t ** 2 * p2.y + t ** 3 * p3.y,
  };
};

const getCurve = (source: Point, target: Point, type: DataVisualizationType) => {
  if (type === "org") {
    return {
      path: `M ${source.x} ${source.y} L ${target.x} ${target.y}`,
      controls: [source, source, target, target] as [Point, Point, Point, Point],
      length: Math.hypot(target.x - source.x, target.y - source.y),
    };
  }

  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const bend = type === "flow" ? 0.34 : 0.18;
  const c1 = { x: source.x + dx * bend, y: source.y - Math.abs(dx) * 0.12 + dy * 0.08 };
  const c2 = { x: target.x - dx * bend, y: target.y + Math.abs(dx) * 0.12 - dy * 0.08 };

  return {
    path: `M ${source.x} ${source.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${target.x} ${target.y}`,
    controls: [source, c1, c2, target] as [Point, Point, Point, Point],
    length: Math.hypot(dx, dy) * 1.18,
  };
};

const layoutNodes = (
  nodes: DataVisualizationNode[],
  edges: DataVisualizationEdge[],
  type: DataVisualizationType,
  layout: DataLayout,
  width: number,
  height: number
): LayoutNode[] => {
  if (nodes.some((node) => node.x !== undefined && node.y !== undefined)) {
    return nodes.map((node) => ({
      ...node,
      x: node.x ?? width / 2,
      y: node.y ?? height / 2,
    }));
  }

  if (type === "org") {
    const vertical = layout !== "horizontal";
    const childrenByParent = new Map<string, string[]>();
    const targets = new Set(edges.map((edge) => edge.target));
    edges.forEach((edge) => {
      childrenByParent.set(edge.source, [
        ...(childrenByParent.get(edge.source) ?? []),
        edge.target,
      ]);
    });

    const rootId = nodes.find((node) => !targets.has(node.id))?.id ?? nodes[0]?.id;
    const levels = new Map<string, number>();
    const queue = rootId ? [rootId] : [];
    levels.set(rootId, 0);

    while (queue.length > 0) {
      const current = queue.shift();
      if (!current) {
        continue;
      }
      const level = levels.get(current) ?? 0;
      (childrenByParent.get(current) ?? []).forEach((child) => {
        levels.set(child, level + 1);
        queue.push(child);
      });
    }

    const groups = new Map<number, DataVisualizationNode[]>();
    nodes.forEach((node) => {
      const level = node.level ?? levels.get(node.id) ?? 0;
      groups.set(level, [...(groups.get(level) ?? []), node]);
    });

    const maxLevel = Math.max(...Array.from(groups.keys()), 0);
    return nodes.map((node) => {
      const level = node.level ?? levels.get(node.id) ?? 0;
      const siblings = groups.get(level) ?? [node];
      const siblingIndex = siblings.findIndex((sibling) => sibling.id === node.id);
      const main = maxLevel === 0 ? 0.5 : level / maxLevel;
      const cross = (siblingIndex + 1) / (siblings.length + 1);

      return {
        ...node,
        x: vertical ? 220 + cross * (width - 440) : 210 + main * (width - 420),
        y: vertical ? 170 + main * (height - 330) : 160 + cross * (height - 300),
      };
    });
  }

  if (type === "network" && layout === "radial") {
    const center = nodes.find((node) => node.critical) ?? nodes[0];
    return nodes.map((node, index) => {
      if (node.id === center.id) {
        return { ...node, x: width / 2, y: height / 2 };
      }
      const outerIndex = index - (index > nodes.findIndex((n) => n.id === center.id) ? 1 : 0);
      const angle = (outerIndex / Math.max(1, nodes.length - 1)) * Math.PI * 2 - Math.PI / 2;
      const radius = Math.min(width, height) * 0.32;
      return {
        ...node,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
      };
    });
  }

  if (type === "network") {
    const positions = nodes.map((node, index) => {
      const angle = (index / nodes.length) * Math.PI * 2;
      const radius = Math.min(width, height) * (0.22 + seededNoise(node.id) * 0.16);
      return {
        ...node,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
      };
    });

    for (let step = 0; step < 90; step += 1) {
      const deltas = positions.map(() => ({ x: 0, y: 0 }));
      for (let a = 0; a < positions.length; a += 1) {
        for (let b = a + 1; b < positions.length; b += 1) {
          const dx = positions[a].x - positions[b].x;
          const dy = positions[a].y - positions[b].y;
          const distance = Math.max(28, Math.hypot(dx, dy));
          const force = 1500 / (distance * distance);
          deltas[a].x += (dx / distance) * force;
          deltas[a].y += (dy / distance) * force;
          deltas[b].x -= (dx / distance) * force;
          deltas[b].y -= (dy / distance) * force;
        }
      }

      edges.forEach((edge) => {
        const sourceIndex = positions.findIndex((node) => node.id === edge.source);
        const targetIndex = positions.findIndex((node) => node.id === edge.target);
        if (sourceIndex === -1 || targetIndex === -1) {
          return;
        }
        const source = positions[sourceIndex];
        const target = positions[targetIndex];
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const force = (distance - 270) * 0.004;
        deltas[sourceIndex].x += (dx / distance) * force;
        deltas[sourceIndex].y += (dy / distance) * force;
        deltas[targetIndex].x -= (dx / distance) * force;
        deltas[targetIndex].y -= (dy / distance) * force;
      });

      positions.forEach((node, index) => {
        node.x = Math.max(150, Math.min(width - 150, node.x + deltas[index].x));
        node.y = Math.max(150, Math.min(height - 130, node.y + deltas[index].y));
      });
    }

    return positions;
  }

  return nodes.map((node, index) => {
    const progress = nodes.length === 1 ? 0.5 : index / (nodes.length - 1);
    const wave = Math.sin(index * 1.7) * 96;
    return {
      ...node,
      x: 170 + progress * (width - 340),
      y: height / 2 + wave,
    };
  });
};

const NodeShape: React.FC<{
  node: LayoutNode;
  progress: number;
  labelProgress: number;
  isHighlighted: boolean;
}> = ({ node, progress, labelProgress, isHighlighted }) => {
  const { width, height } = getNodeSize(node.type);
  const colors = getNodeColors(node.type);
  const label = node.label.slice(0, Math.floor(node.label.length * labelProgress));
  const lines = splitLabel(label, node.type === "person" ? 10 : 15);
  const scale = interpolate(progress, [0, 1], [0.72, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(progress, [0, 0.45, 1], [0, 0.85, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const path = nodeShapePath(node.type, width, height);

  return (
    <g
      transform={`translate(${node.x} ${node.y}) scale(${scale})`}
      opacity={opacity}
      style={{
        filter: isHighlighted
          ? `drop-shadow(0 0 18px ${BRAND.teal}) drop-shadow(0 0 34px ${BRAND.teal}55)`
          : "drop-shadow(0 16px 24px rgba(0,0,0,0.32))",
      }}
    >
      {node.type === "person" ? (
        <circle
          r={width / 2}
          fill={colors.fill}
          stroke={colors.stroke}
          strokeWidth={2}
        />
      ) : node.type === "entity" ? (
        <rect
          x={-width / 2}
          y={-height / 2}
          width={width}
          height={height}
          rx={10}
          fill={colors.fill}
          stroke={colors.stroke}
          strokeWidth={2}
        />
      ) : (
        <path d={path} fill={colors.fill} stroke={colors.stroke} strokeWidth={2} />
      )}
      {node.critical ? (
        <circle
          r={Math.max(width, height) * 0.62}
          fill="none"
          stroke={BRAND.criticalRed}
          strokeWidth={2}
          opacity={0.32}
        />
      ) : null}
      {lines.map((line, index) => (
        <text
          key={`${node.id}-${index}`}
          x={0}
          y={(index - (lines.length - 1) / 2) * 16 + 5}
          fill={colors.text}
          fontSize={node.type === "person" ? 13 : 14}
          fontWeight={850}
          textAnchor="middle"
          style={{ letterSpacing: 0 }}
        >
          {line}
        </text>
      ))}
    </g>
  );
};

export const DataVisualization: React.FC<DataVisualizationProps> = memo(
  ({
    type,
    nodes,
    edges,
    title = "FAILURE MECHANISM",
    subtitle = "Animated evidence map",
    layout,
    activeNodeId,
    accentColor = BRAND.teal,
    backgroundColor = BRAND.charcoal,
  }) => {
    const frame = useCurrentFrame();
    const { fps, width, height, durationInFrames } = useVideoConfig();
    const resolvedLayout = layout ?? (type === "network" ? "force" : type === "org" ? "vertical" : "horizontal");
    const finalNodes = useMemo(
      () => layoutNodes(nodes, edges, type, resolvedLayout, width, height),
      [edges, height, nodes, resolvedLayout, type, width]
    );
    const nodeById = useMemo(
      () => new Map(finalNodes.map((node) => [node.id, node])),
      [finalNodes]
    );
    const activeSubtree = useMemo(() => {
      if (!activeNodeId) {
        return new Set<string>();
      }
      const highlighted = new Set([activeNodeId]);
      let changed = true;
      while (changed) {
        changed = false;
        edges.forEach((edge) => {
          if (highlighted.has(edge.source) && !highlighted.has(edge.target)) {
            highlighted.add(edge.target);
            changed = true;
          }
        });
      }
      return highlighted;
    }, [activeNodeId, edges]);

    const networkSettle = type === "network"
      ? interpolate(frame, [0, 2 * fps], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.out(Easing.cubic),
        })
      : 1;

    const displayedNodes = finalNodes.map((node, index) => {
      if (type !== "network") {
        return node;
      }
      const angle = (index / Math.max(1, finalNodes.length)) * Math.PI * 2;
      const radius = Math.min(width, height) * (0.13 + seededNoise(`${node.id}-start`) * 0.18);
      const startX = width / 2 + Math.cos(angle) * radius;
      const startY = height / 2 + Math.sin(angle) * radius;
      return {
        ...node,
        x: interpolate(networkSettle, [0, 1], [startX, node.x]),
        y: interpolate(networkSettle, [0, 1], [startY, node.y]),
      };
    });
    const displayedById = new Map(displayedNodes.map((node) => [node.id, node]));

    const fadeToBlack = interpolate(
      frame,
      [durationInFrames - 0.9 * fps, durationInFrames],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    const titleOpacity = interpolate(frame, [0, 0.45 * fps, 2.4 * fps], [0, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });

    return (
      <AbsoluteFill
        style={{
          backgroundColor,
          backgroundImage:
            `radial-gradient(circle at 50% 42%, ${accentColor}20, transparent 28%), linear-gradient(180deg, ${backgroundColor}, #050508)`,
          color: BRAND.bone,
          fontFamily: "Inter, Helvetica, Arial, sans-serif",
          letterSpacing: 0,
          overflow: "hidden",
        }}
      >
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <pattern id="evidence-grid" width="64" height="64" patternUnits="userSpaceOnUse">
              <path
                d="M 64 0 L 0 0 0 64"
                fill="none"
                stroke="rgba(245,240,225,0.08)"
                strokeWidth="1"
              />
            </pattern>
            <filter id="teal-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <rect width={width} height={height} fill="url(#evidence-grid)" opacity={0.72} />
          <rect
            width={width}
            height={height}
            fill="none"
            stroke="rgba(245,240,225,0.09)"
            strokeWidth={1}
          />

          {edges.map((edge, index) => {
            const source = displayedById.get(edge.source);
            const target = displayedById.get(edge.target);
            if (!source || !target) {
              return null;
            }

            const edgeKind = edge.type ?? (type === "org" ? "hierarchy" : type === "network" ? "dependency" : "flow");
            const curve = getCurve(source, target, type);
            const drawStart = type === "network" ? 1.1 * fps : 0.65 * fps + index * 0.22 * fps;
            const drawProgress = interpolate(
              frame,
              [drawStart, drawStart + 0.8 * fps],
              [0, 1],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.out(Easing.cubic),
              }
            );
            const pulse = edge.critical ? 0.58 + Math.sin(frame * 0.24) * 0.22 : 0;
            const edgeColor = edge.critical ? BRAND.criticalRed : edgeKind === "influence" ? BRAND.amber : accentColor;
            const strokeDash =
              edgeKind === "dependency" ? "12 12" : edgeKind === "influence" ? "2 10" : undefined;
            const value = Math.max(0, edge.value ?? 0);
            const particleCount = type === "flow" ? Math.max(1, Math.min(8, Math.ceil(Math.log10(value + 10)))) : 0;
            const valueProgress = spring({
              frame: frame - drawStart - 0.35 * fps,
              fps,
              config: { damping: 24, stiffness: 90, mass: 1 },
            });
            const countedValue = Math.round(value * clamp01(valueProgress));
            const mid = cubicPoint(curve.controls[0], curve.controls[1], curve.controls[2], curve.controls[3], 0.5);

            return (
              <g key={edge.id ?? `${edge.source}-${edge.target}`}>
                <path
                  d={curve.path}
                  fill="none"
                  stroke={edgeColor}
                  strokeWidth={edgeKind === "flow" ? 3 : edgeKind === "influence" ? 1.5 : 2}
                  strokeLinecap="round"
                  strokeDasharray={strokeDash ?? curve.length}
                  strokeDashoffset={strokeDash ? 0 : curve.length * (1 - drawProgress)}
                  opacity={type === "network" ? 0.68 : 0.88}
                  filter={edge.critical || edgeKind === "influence" ? "url(#teal-glow)" : undefined}
                  style={{
                    filter: edge.critical
                      ? `drop-shadow(0 0 ${16 + pulse * 18}px ${BRAND.criticalRed})`
                      : undefined,
                  }}
                />
                {Array.from({ length: particleCount }).map((_, particleIndex) => {
                  const loop = (((frame / fps) / 3 + particleIndex / particleCount) % 1);
                  const point = cubicPoint(
                    curve.controls[0],
                    curve.controls[1],
                    curve.controls[2],
                    curve.controls[3],
                    loop
                  );
                  return (
                    <circle
                      key={particleIndex}
                      cx={point.x}
                      cy={point.y}
                      r={4}
                      fill={edge.critical ? BRAND.criticalRed : accentColor}
                      opacity={drawProgress * 0.9}
                    />
                  );
                })}
                {type === "flow" && edge.valueLabel ? (
                  <g opacity={drawProgress}>
                    <rect
                      x={mid.x - 54}
                      y={mid.y - 18}
                      width={108}
                      height={34}
                      rx={3}
                      fill="rgba(26,26,46,0.88)"
                      stroke={edgeColor}
                      strokeWidth={1}
                    />
                    <text
                      x={mid.x}
                      y={mid.y + 5}
                      fill={BRAND.bone}
                      fontSize={14}
                      fontWeight={850}
                      textAnchor="middle"
                    >
                      {edge.valueLabel.replace(/\d+(?:\.\d+)?/, String(countedValue))}
                    </text>
                  </g>
                ) : edge.label ? (
                  <text
                    x={mid.x}
                    y={mid.y - 12}
                    fill={BRAND.bone}
                    fontSize={13}
                    fontWeight={750}
                    textAnchor="middle"
                    opacity={drawProgress}
                    style={{ paintOrder: "stroke", stroke: "rgba(0,0,0,0.72)", strokeWidth: 5 }}
                  >
                    {edge.label}
                  </text>
                ) : null}
              </g>
            );
          })}

          {type === "network"
            ? displayedNodes
                .filter((node) => node.critical)
                .map((node) => {
                  const ringProgress = ((frame / fps) % 1.8) / 1.8;
                  return (
                    <g key={`${node.id}-pulse`}>
                      {[0, 0.34].map((offset) => {
                        const progress = (ringProgress + offset) % 1;
                        return (
                          <circle
                            key={offset}
                            cx={node.x}
                            cy={node.y}
                            r={72 + progress * 96}
                            fill="none"
                            stroke={BRAND.criticalRed}
                            strokeWidth={2}
                            opacity={(1 - progress) * 0.42}
                          />
                        );
                      })}
                    </g>
                  );
                })
            : null}

          {type === "network"
            ? Array.from(new Set(displayedNodes.map((node) => node.cluster).filter(Boolean))).map(
                (cluster, index) => {
                  const members = displayedNodes.filter((node) => node.cluster === cluster);
                  const center = members.reduce(
                    (sum, node) => ({ x: sum.x + node.x / members.length, y: sum.y + node.y / members.length }),
                    { x: 0, y: 0 }
                  );
                  const opacity = interpolate(
                    frame,
                    [2.0 * fps + index * 0.18 * fps, 2.6 * fps + index * 0.18 * fps],
                    [0, 1],
                    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                  );
                  return (
                    <text
                      key={cluster}
                      x={center.x}
                      y={center.y + 104}
                      fill={BRAND.grey}
                      fontSize={16}
                      fontWeight={850}
                      textAnchor="middle"
                      opacity={opacity}
                    >
                      {cluster?.toUpperCase()}
                    </text>
                  );
                }
              )
            : null}

          {displayedNodes.map((node, index) => {
            const baseDelay = type === "org"
              ? (node.level ?? 0) * 0.48 * fps + index * 0.04 * fps
              : type === "network"
                ? 0.9 * fps + index * 0.05 * fps
                : index * 0.16 * fps;
            const progress = spring({
              frame: frame - baseDelay,
              fps,
              config: { damping: 20, stiffness: 95, mass: 0.9 },
            });
            const labelProgress =
              type === "org"
                ? interpolate(frame, [baseDelay + 0.25 * fps, baseDelay + 1.15 * fps], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  })
                : clamp01(progress);
            const highlighted =
              node.critical ||
              activeSubtree.has(node.id) ||
              (type === "org" && nodeById.has(activeNodeId ?? "") && activeSubtree.has(node.id));

            return (
              <NodeShape
                key={node.id}
                node={node}
                progress={clamp01(progress)}
                labelProgress={labelProgress}
                isHighlighted={highlighted}
              />
            );
          })}
        </svg>

        <div
          style={{
            position: "absolute",
            left: 54,
            top: 42,
            opacity: titleOpacity,
          }}
        >
          <div
            style={{
              color: accentColor,
              fontSize: 18,
              fontWeight: 900,
              textTransform: "uppercase",
            }}
          >
            {title}
          </div>
          <div
            style={{
              marginTop: 8,
              color: BRAND.bone,
              fontSize: 36,
              fontWeight: 900,
              maxWidth: 980,
            }}
          >
            {subtitle}
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            right: 48,
            bottom: 38,
            color: "rgba(245,240,225,0.6)",
            fontSize: 14,
            fontWeight: 800,
            textTransform: "uppercase",
          }}
        >
          {type} / {nodes.length} nodes / {edges.length} links
        </div>

        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "black",
            opacity: fadeToBlack,
          }}
        />
      </AbsoluteFill>
    );
  }
);

DataVisualization.displayName = "DataVisualization";

export default DataVisualization;
