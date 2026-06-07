import type { CSSProperties } from "react";
import { staticFile } from "remotion";
import type { LayoutState } from "./types";

export const stateCssVars: Record<LayoutState, CSSProperties> = {
  STATE_MONOLOGUE: {
    "--bg-color": "#2F4F4F",
    "--accent": "#008080",
    "--text": "#F6F4EA",
  } as CSSProperties,
  STATE_DEEP_DIVE: {
    "--bg-color": "#101820",
    "--accent": "#008080",
    "--text": "#F6F4EA",
  } as CSSProperties,
  STATE_CRITICAL_ERROR: {
    "--bg-color": "#8B0000",
    "--accent": "#FF0000",
    "--text": "#FFF7F7",
  } as CSSProperties,
};

export function resolveAsset(src: string): string {
  if (src.startsWith("http://") || src.startsWith("https://") || src.startsWith("data:")) {
    return src;
  }
  const clean = src.replace(/^file:\/\/\/?/, "").replace(/\\/g, "/");
  if (clean.startsWith("/") || /^[A-Za-z]:\//.test(clean)) {
    return `file://${clean}`;
  }
  return staticFile(clean);
}
