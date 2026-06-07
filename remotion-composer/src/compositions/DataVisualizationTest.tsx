import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import DataVisualization, {
  DataVisualizationProps,
} from "../components/DataVisualization";

const FLOW_DURATION = 240;
const ORG_DURATION = 240;
const NETWORK_DURATION = 270;

const flowProps: DataVisualizationProps = {
  type: "flow",
  title: "MODERN ARCHIVIST / FLOW",
  subtitle: "Humane AI Pin funding, operating burn, refunds, and acquisition residue",
  layout: "horizontal",
  nodes: [
    { id: "funding", label: "$30M funding", type: "account", x: 210, y: 330 },
    { id: "humane", label: "Humane", type: "entity", x: 520, y: 330, critical: true },
    { id: "suppliers", label: "Suppliers", type: "product", x: 850, y: 205 },
    { id: "employees", label: "Employees", type: "person", x: 850, y: 455 },
    { id: "returns", label: "Returns / refunds", type: "metric", x: 1180, y: 330, critical: true },
    { id: "hp", label: "HP acquisition", type: "entity", x: 1540, y: 330 },
  ],
  edges: [
    {
      source: "funding",
      target: "humane",
      value: 30,
      valueLabel: "$30M",
      type: "flow",
    },
    {
      source: "humane",
      target: "suppliers",
      value: 12,
      valueLabel: "$12M",
      type: "flow",
    },
    {
      source: "humane",
      target: "employees",
      value: 18,
      valueLabel: "$18M",
      type: "flow",
    },
    {
      source: "suppliers",
      target: "returns",
      value: 8,
      valueLabel: "$8M",
      type: "flow",
      critical: true,
    },
    {
      source: "employees",
      target: "returns",
      value: 6,
      valueLabel: "$6M",
      type: "flow",
      critical: true,
    },
    {
      source: "returns",
      target: "hp",
      value: 16,
      valueLabel: "$16M",
      type: "flow",
    },
  ],
};

const orgProps: DataVisualizationProps = {
  type: "org",
  title: "MODERN ARCHIVIST / ORG",
  subtitle: "A launch structure cascading from founders to contractors",
  layout: "vertical",
  activeNodeId: "founders",
  nodes: [
    { id: "founders", label: "Founders", type: "person", level: 0, critical: true },
    { id: "product-vp", label: "VP Product", type: "entity", level: 1 },
    { id: "ops-vp", label: "VP Ops", type: "entity", level: 1 },
    { id: "eng-vp", label: "VP Engineering", type: "entity", level: 1 },
    { id: "product-dir", label: "Product Directors", type: "entity", level: 2 },
    { id: "supply-dir", label: "Supply Directors", type: "entity", level: 2 },
    { id: "firmware-dir", label: "Firmware Directors", type: "entity", level: 2 },
    { id: "ic-design", label: "Design ICs", type: "person", level: 3 },
    { id: "ic-qa", label: "QA ICs", type: "person", level: 3 },
    { id: "ic-field", label: "Field ICs", type: "person", level: 3 },
    { id: "contractors", label: "Contractors", type: "account", level: 4 },
  ],
  edges: [
    { source: "founders", target: "product-vp", type: "hierarchy" },
    { source: "founders", target: "ops-vp", type: "hierarchy" },
    { source: "founders", target: "eng-vp", type: "hierarchy" },
    { source: "product-vp", target: "product-dir", type: "hierarchy" },
    { source: "ops-vp", target: "supply-dir", type: "hierarchy" },
    { source: "eng-vp", target: "firmware-dir", type: "hierarchy" },
    { source: "product-dir", target: "ic-design", type: "hierarchy" },
    { source: "supply-dir", target: "ic-qa", type: "hierarchy" },
    { source: "firmware-dir", target: "ic-field", type: "hierarchy" },
    { source: "ic-design", target: "contractors", type: "hierarchy" },
    { source: "ic-qa", target: "contractors", type: "hierarchy" },
    { source: "ic-field", target: "contractors", type: "hierarchy" },
  ],
};

const networkProps: DataVisualizationProps = {
  type: "network",
  title: "MODERN ARCHIVIST / NETWORK",
  subtitle: "Dependencies around the AI Pin launch narrative",
  layout: "force",
  nodes: [
    { id: "humane", label: "Humane", type: "entity", cluster: "Company", critical: true },
    { id: "suppliers", label: "Suppliers", type: "product", cluster: "Operations" },
    { id: "reviewers", label: "Reviewers", type: "person", cluster: "Public test", critical: true },
    { id: "media", label: "Media", type: "entity", cluster: "Narrative" },
    { id: "regulators", label: "Regulators", type: "metric", cluster: "Oversight" },
    { id: "acquirers", label: "Acquirers", type: "account", cluster: "Exit" },
    { id: "customers", label: "Customers", type: "person", cluster: "Public test" },
  ],
  edges: [
    { source: "humane", target: "suppliers", type: "dependency", label: "hardware" },
    { source: "suppliers", target: "humane", type: "dependency", label: "capacity" },
    { source: "humane", target: "reviewers", type: "influence", label: "embargo" },
    { source: "reviewers", target: "media", type: "influence", label: "verdict", critical: true },
    { source: "media", target: "customers", type: "influence", label: "demand" },
    { source: "customers", target: "regulators", type: "dependency", label: "complaints" },
    { source: "humane", target: "acquirers", type: "dependency", label: "IP" },
    { source: "acquirers", target: "media", type: "influence", label: "exit story" },
    { source: "regulators", target: "humane", type: "dependency", label: "scrutiny" },
  ],
};

export const dataVisualizationTestProps = {
  flow: flowProps,
  org: orgProps,
  network: networkProps,
};

const TabBar: React.FC = () => {
  const frame = useCurrentFrame();
  const active = frame < FLOW_DURATION ? "FLOW" : frame < FLOW_DURATION + ORG_DURATION ? "ORG" : "NETWORK";

  return (
    <div
      style={{
        position: "absolute",
        left: 54,
        right: 54,
        top: 24,
        display: "flex",
        gap: 10,
        justifyContent: "center",
        zIndex: 10,
      }}
    >
      {["FLOW", "ORG", "NETWORK"].map((tab) => {
        const selected = tab === active;
        return (
          <div
            key={tab}
            style={{
              width: 136,
              height: 32,
              border: `1px solid ${selected ? "#00D4AA" : "rgba(245,240,225,0.22)"}`,
              backgroundColor: selected ? "rgba(0,212,170,0.16)" : "rgba(26,26,46,0.58)",
              color: selected ? "#F5F0E1" : "rgba(245,240,225,0.58)",
              fontSize: 13,
              fontWeight: 900,
              textAlign: "center",
              lineHeight: "32px",
              letterSpacing: 0,
            }}
          >
            {tab}
          </div>
        );
      })}
    </div>
  );
};

export const DataVisualizationTest: React.FC<typeof dataVisualizationTestProps> = ({
  flow,
  org,
  network,
}) => {
  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#1A1A2E" }}>
      <TabBar />
      <Sequence durationInFrames={FLOW_DURATION}>
        <DataVisualization {...flow} />
      </Sequence>
      <Sequence from={FLOW_DURATION} durationInFrames={ORG_DURATION}>
        <DataVisualization {...org} />
      </Sequence>
      <Sequence from={FLOW_DURATION + ORG_DURATION} durationInFrames={NETWORK_DURATION}>
        <DataVisualization {...network} />
      </Sequence>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width,
          height,
          pointerEvents: "none",
          boxShadow: "inset 0 0 160px rgba(0,0,0,0.72)",
        }}
      />
    </AbsoluteFill>
  );
};
