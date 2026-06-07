import React from "react";
import TimelineFlythrough, {
  TimelineFlythroughProps,
} from "../components/TimelineFlythrough";

export const timelineFlythroughTestProps: TimelineFlythroughProps = {
  title: "MODERN ARCHIVIST / FAILURE LEDGER",
  subtitle: "Humane AI Pin: a launch timeline reconstructed from public evidence",
  flySpeed: 260,
  pauseDuration: 2.15,
  orbitOnPause: true,
  events: [
    {
      id: "reveal",
      date: "November 2023",
      title: "The wearable is introduced",
      description:
        "Humane frames the AI Pin as a screenless assistant, promising ambient computing worn on the body.",
      zPosition: 760,
      side: "left",
      evidenceLabel: "Launch deck",
      evidenceSource: "Product reveal coverage",
      connectionLabel: "sets expectation",
    },
    {
      id: "preorders",
      date: "Late 2023",
      title: "Preorders test the premise",
      description:
        "The $699 device and subscription model move from concept video to customer commitment.",
      zPosition: 430,
      side: "right",
      evidenceLabel: "Order page",
      evidenceSource: "Archived preorder materials",
      connectionLabel: "prices the bet",
    },
    {
      id: "review-embargo",
      date: "April 2024",
      title: "Reviews find the gap",
      description:
        "Reviewers report slow responses, heat, short battery life, and an assistant that misses routine requests.",
      zPosition: 110,
      side: "left",
      importance: "critical",
      evidenceLabel: "Review packet",
      evidenceSource: "Independent launch reviews",
      connectionLabel: "contradicts promise",
    },
    {
      id: "returns",
      date: "Summer 2024",
      title: "Returns overtake momentum",
      description:
        "Public reporting describes weak retention and a product narrative increasingly defined by refunds.",
      zPosition: -260,
      side: "right",
      importance: "critical",
      evidenceLabel: "Sales ledger",
      evidenceSource: "Business reporting and return data",
      connectionLabel: "converts hype into liability",
    },
    {
      id: "reversal",
      date: "2025",
      title: "The category is absorbed",
      description:
        "The remaining story becomes less about a device and more about what happens when a product vision outruns daily use.",
      zPosition: -650,
      side: "left",
      evidenceLabel: "Postmortem",
      evidenceSource: "Failure Ledger synthesis",
      connectionLabel: "leaves the record",
    },
  ],
};

export const TimelineFlythroughTest: React.FC<TimelineFlythroughProps> = (
  props
) => <TimelineFlythrough {...props} />;
