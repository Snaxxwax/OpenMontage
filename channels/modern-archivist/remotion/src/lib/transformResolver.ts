/**
 * Pivot-based additive transform resolver for canvas-registered puppet layers.
 *
 * Adapted from VectorForge (RigPreview.tsx, schemas/index.ts):
 * - Additive composition: default → idle → active_action
 * - Pivot-correct transform-origin derived from rig_spec pixel coordinates
 * - Keyframe interpolation using linear lerp (GSAP replaced by plain math)
 *
 * All coordinate values are in 1254×1254 canvas pixel space.
 */

export interface PartTransform {
  rot: number; // degrees
  tx: number;  // canvas pixels
  ty: number;  // canvas pixels
  sx?: number; // scaleX (default 1)
  sy?: number; // scaleY (default 1)
}

export interface Keyframe {
  frame: number;
  parts: Record<string, Partial<PartTransform>>;
}

const ZERO: PartTransform = { rot: 0, tx: 0, ty: 0, sx: 1, sy: 1 };

/** Linear interpolation between two numbers. */
function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Resolve a part's transform at a given local frame via keyframe interpolation. */
export function resolvePartAtFrame(
  partId: string,
  keyframes: Keyframe[],
  localFrame: number,
): PartTransform {
  if (!keyframes.length) return { ...ZERO };

  const sorted = [...keyframes].sort((a, b) => a.frame - b.frame);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];

  const clampedFrame = Math.max(first.frame, Math.min(last.frame, localFrame));

  // Find surrounding pair
  let kA = first;
  let kB = last;
  for (let i = 0; i < sorted.length - 1; i++) {
    if (clampedFrame >= sorted[i].frame && clampedFrame <= sorted[i + 1].frame) {
      kA = sorted[i];
      kB = sorted[i + 1];
      break;
    }
  }

  const span = kB.frame - kA.frame;
  const t = span === 0 ? 0 : (clampedFrame - kA.frame) / span;

  const pA: PartTransform = { ...ZERO, ...kA.parts[partId] };
  const pB: PartTransform = { ...ZERO, ...kB.parts[partId] };

  return {
    rot: lerp(pA.rot, pB.rot, t),
    tx:  lerp(pA.tx,  pB.tx,  t),
    ty:  lerp(pA.ty,  pB.ty,  t),
    sx:  lerp(pA.sx ?? 1, pB.sx ?? 1, t),
    sy:  lerp(pA.sy ?? 1, pB.sy ?? 1, t),
  };
}

/**
 * Additive transform composition — from VectorForge's applyPose() merge logic.
 * Adds delta onto base: rotations and translations sum, scales multiply.
 */
export function addTransforms(base: PartTransform, delta: Partial<PartTransform>): PartTransform {
  return {
    rot: base.rot + (delta.rot ?? 0),
    tx:  base.tx  + (delta.tx  ?? 0),
    ty:  base.ty  + (delta.ty  ?? 0),
    sx:  (base.sx ?? 1) * (delta.sx ?? 1),
    sy:  (base.sy ?? 1) * (delta.sy ?? 1),
  };
}

/**
 * Convert a pixel [x, y] pivot in canvas space to a CSS transform-origin string.
 * e.g. [777, 928] on a 1254px canvas → "61.96% 74.00%"
 */
export function pivotToOrigin(pivot: [number, number], canvas = 1254): string {
  return `${((pivot[0] / canvas) * 100).toFixed(2)}% ${((pivot[1] / canvas) * 100).toFixed(2)}%`;
}

/**
 * Convert a PartTransform to a CSS transform string.
 * Rotation is applied first (at the transform-origin pivot), then translation.
 */
export function toCssTransform(t: PartTransform): string {
  const parts: string[] = [];
  if (t.rot !== 0) parts.push(`rotate(${t.rot.toFixed(3)}deg)`);
  if (t.tx !== 0 || t.ty !== 0) parts.push(`translate(${t.tx.toFixed(2)}px, ${t.ty.toFixed(2)}px)`);
  if ((t.sx ?? 1) !== 1 || (t.sy ?? 1) !== 1) parts.push(`scale(${t.sx ?? 1}, ${t.sy ?? 1})`);
  return parts.length ? parts.join(' ') : 'none';
}

/**
 * Convenience: build the style object for a canvas-registered layer div
 * with pivot-correct transform-origin and composed transform.
 */
export function layerStyle(
  pivot: [number, number],
  transform: PartTransform,
  zIndex: number,
  canvas = 1254,
): React.CSSProperties {
  return {
    position: 'absolute' as const,
    inset: 0,
    width: '100%',
    height: '100%',
    transformOrigin: pivotToOrigin(pivot, canvas),
    transform: toCssTransform(transform),
    zIndex,
  };
}

// React is referenced in the return type above; import it to satisfy TS.
import type React from 'react';
