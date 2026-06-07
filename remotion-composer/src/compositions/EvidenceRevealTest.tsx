import React from "react";
import EvidenceReveal, {
  EvidenceRevealProps,
} from "../components/EvidenceReveal";

export const evidenceRevealTestProps: EvidenceRevealProps = {
  title: "FAILURE LEDGER / EXHIBIT 04",
  documentDate: "Internal memo, March 17",
  sourceLabel: "Source: Procurement Review Board Archive",
  documentText:
    "The committee approved the revised launch schedule despite unresolved thermal failures, incomplete supplier audits, and a missing recovery plan for field units already in transit.",
  wordTimings: [
    { word: "The", startSeconds: 4.1, endSeconds: 4.22 },
    { word: "committee", startSeconds: 4.22, endSeconds: 4.58 },
    { word: "approved", startSeconds: 4.58, endSeconds: 4.92 },
    { word: "the", startSeconds: 4.92, endSeconds: 5.02 },
    { word: "revised", startSeconds: 5.02, endSeconds: 5.28 },
    { word: "launch", startSeconds: 5.28, endSeconds: 5.55 },
    { word: "schedule", startSeconds: 5.55, endSeconds: 5.9 },
    { word: "despite", startSeconds: 5.9, endSeconds: 6.22 },
    { word: "unresolved", startSeconds: 6.22, endSeconds: 6.62 },
    { word: "thermal", startSeconds: 6.62, endSeconds: 6.9 },
    { word: "failures,", startSeconds: 6.9, endSeconds: 7.26 },
    { word: "incomplete", startSeconds: 7.26, endSeconds: 7.66 },
    { word: "supplier", startSeconds: 7.66, endSeconds: 7.98 },
    { word: "audits,", startSeconds: 7.98, endSeconds: 8.28 },
    { word: "and", startSeconds: 8.28, endSeconds: 8.42 },
    { word: "a", startSeconds: 8.42, endSeconds: 8.5 },
    { word: "missing", startSeconds: 8.5, endSeconds: 8.8 },
    { word: "recovery", startSeconds: 8.8, endSeconds: 9.12 },
    { word: "plan", startSeconds: 9.12, endSeconds: 9.36 },
    { word: "for", startSeconds: 9.36, endSeconds: 9.48 },
    { word: "field", startSeconds: 9.48, endSeconds: 9.72 },
    { word: "units", startSeconds: 9.72, endSeconds: 9.96 },
    { word: "already", startSeconds: 9.96, endSeconds: 10.26 },
    { word: "in", startSeconds: 10.26, endSeconds: 10.36 },
    { word: "transit.", startSeconds: 10.36, endSeconds: 10.78 },
  ],
  highlightRanges: [
    { startWord: 4, endWord: 6 },
    { startWord: 8, endWord: 10, critical: true },
    { startWord: 11, endWord: 13 },
    { startWord: 16, endWord: 18, critical: true },
  ],
};

export const EvidenceRevealTest: React.FC<EvidenceRevealProps> = (props) => (
  <EvidenceReveal {...props} />
);
