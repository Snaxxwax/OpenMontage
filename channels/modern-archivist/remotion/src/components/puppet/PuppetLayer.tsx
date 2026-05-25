import React from "react";
import { Img } from "remotion";

interface PuppetLayerProps {
  src: string;
  style?: React.CSSProperties;
  zIndex?: number;
}

export const PuppetLayer: React.FC<PuppetLayerProps> = ({ src, style, zIndex = 0 }) => (
  <Img
    src={src}
    style={{
      position: "absolute",
      inset: 0,
      width: "100%",
      height: "100%",
      objectFit: "contain",
      zIndex,
      ...style,
    }}
  />
);
