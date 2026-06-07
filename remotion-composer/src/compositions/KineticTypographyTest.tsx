import React from "react";
import KineticTypography, { KineticTypographyProps } from "../components/KineticTypography";

export const kineticTypographyTestProps: KineticTypographyProps = {
  fontSize: 58,
  lineHeight: 1.1,
  maxWidth: 1320,
  revealType: "word",
  staggerMs: 35,
  holdDuration: 0.3,
  words: [
    { word: "HOW ", startSeconds: 0.5, endSeconds: 3.0 },
    { word: "HUMANE ", startSeconds: 0.7, endSeconds: 3.0, emphasis: "strong" },
    { word: "BURNED ", startSeconds: 0.9, endSeconds: 3.0, emphasis: "critical" },
    { word: "$230M ", startSeconds: 1.1, endSeconds: 3.0, emphasis: "number" },
    { word: "IN ", startSeconds: 1.4, endSeconds: 3.0 },
    { word: "13 ", startSeconds: 1.6, endSeconds: 3.0, emphasis: "number" },
    { word: "MONTHS", startSeconds: 1.8, endSeconds: 3.0, emphasis: "strong" },
    { word: ".", startSeconds: 2.0, endSeconds: 3.0 },
    { word: "THE ", startSeconds: 3.5, endSeconds: 6.0 },
    { word: "PROMISE ", startSeconds: 3.7, endSeconds: 6.0, emphasis: "strong" },
    { word: "WAS ", startSeconds: 3.9, endSeconds: 6.0 },
    { word: "AMBIENT ", startSeconds: 4.1, endSeconds: 6.0, emphasis: "strong" },
    { word: "COMPUTING ", startSeconds: 4.3, endSeconds: 6.0 },
    { word: "WORN ", startSeconds: 4.5, endSeconds: 6.0 },
    { word: "ON ", startSeconds: 4.7, endSeconds: 6.0 },
    { word: "THE ", startSeconds: 4.8, endSeconds: 6.0 },
    { word: "BODY", startSeconds: 5.0, endSeconds: 6.0, emphasis: "strong" },
    { word: ".", startSeconds: 5.2, endSeconds: 6.0 },
    { word: "THE ", startSeconds: 6.5, endSeconds: 9.0 },
    { word: "REALITY ", startSeconds: 6.7, endSeconds: 9.0, emphasis: "critical" },
    { word: "WAS ", startSeconds: 6.9, endSeconds: 9.0 },
    { word: "THERMAL ", startSeconds: 7.1, endSeconds: 9.0, emphasis: "critical" },
    { word: "FAILURE ", startSeconds: 7.3, endSeconds: 9.0, emphasis: "critical" },
    { word: "AND ", startSeconds: 7.5, endSeconds: 9.0 },
    { word: "A ", startSeconds: 7.6, endSeconds: 9.0 },
    { word: "DEVICE ", startSeconds: 7.8, endSeconds: 9.0 },
    { word: "THAT ", startSeconds: 8.0, endSeconds: 9.0 },
    { word: "NEEDED ", startSeconds: 8.2, endSeconds: 9.0 },
    { word: "YOUR ", startSeconds: 8.4, endSeconds: 9.0 },
    { word: "PHONE", startSeconds: 8.6, endSeconds: 9.0, emphasis: "critical" },
    { word: ".", startSeconds: 8.8, endSeconds: 9.0 },
  ],
};

export const KineticTypographyTest: React.FC<KineticTypographyProps> = (props) => (
  <KineticTypography {...props} />
);
