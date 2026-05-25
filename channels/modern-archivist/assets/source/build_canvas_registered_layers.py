#!/usr/bin/env python3
"""
Build canvas-registered RGBA layers from the raw source PNG crops.

All source images (except torso) are 1254×1254 RGB with a near-white background.
They share the same canvas coordinate space as modern_archivist_full_body_mug_pose.png.

Strategy:
  1. Sample corners to detect background color.
  2. Threshold foreground pixels (diff from bg > THRESH).
  3. Run connected-component filtering to remove noise specks.
  4. Emit each layer as 1254×1254 RGBA with binary alpha.
"""

from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import json

ROOT = Path(__file__).parent
OUT = ROOT / "canvas_registered"
OUT.mkdir(exist_ok=True)

CANVAS = 1254
THRESH = 28          # color-distance threshold for background removal
MIN_COMPONENT = 50   # discard connected components smaller than this (noise)

TORSO_SRC = ROOT / "modern_archivist_torso_hoodie.png"

LAYERS = [
    # (output_name, source_file, z_order)
    # Torso goes behind everything
    ("torso_hoodie",          "modern_archivist_torso_hoodie.png",      10),
    # Head behind arm (character holds mug up to face/chin level)
    ("head_neutral",          "modern_archivist_head_neutral.png",       20),
    ("head_eyes_closed",      "modern_archivist_head_eyes_closed.png",   20),
    # arm_mug_grip contains both arm and mug at the correct canvas position.
    # mug_code is NOT used in the composite — its individual crop is not
    # canvas-registered (the mug is centered in the 1254×1254 frame, not at its
    # actual position in the assembled character).
    ("arm_mug_grip",          "modern_archivist_arm_mug_grip.png",       30),
    # Glasses are rendered as SVG by PuppetRig (color-state-aware teal/red) —
    # glasses_round_black is extracted as a standalone layer for reference but
    # NOT composited into the body image to avoid doubling with the SVG overlay.
    # ("glasses_round_black",   "modern_archivist_glasses_round_black.png",45),
    ("mouth_neutral",         "modern_archivist_mouth_neutral.png",       50),
    ("mouth_talk_a",          "modern_archivist_mouth_talk_a.png",       50),
    ("mouth_talk_b",          "modern_archivist_mouth_talk_b.png",       50),
]


def sample_background(arr: np.ndarray, n: int = 30) -> np.ndarray:
    """Median of corner pixels as background estimate."""
    corners = np.concatenate([
        arr[:n, :n].reshape(-1, 3),
        arr[:n, -n:].reshape(-1, 3),
        arr[-n:, :n].reshape(-1, 3),
        arr[-n:, -n:].reshape(-1, 3),
    ])
    return np.median(corners, axis=0)


def extract_foreground(arr: np.ndarray, thresh: float = THRESH) -> np.ndarray:
    """Return binary foreground mask after noise removal."""
    bg = sample_background(arr)
    diff = np.linalg.norm(arr.astype(np.float32) - bg, axis=2)
    fg = (diff > thresh).astype(np.uint8)

    # Connected-component cleanup: discard tiny specks
    num, labels, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    clean = np.zeros_like(fg)
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] >= MIN_COMPONENT:
            clean[labels == i] = 255
    return clean


def process_rgb_layer(src_path: Path) -> Image.Image:
    """Remove white background from a 1254×1254 RGB source image."""
    img = Image.open(src_path).convert("RGB")
    if img.size != (CANVAS, CANVAS):
        img = img.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)

    arr = np.array(img)
    mask = extract_foreground(arr)

    rgba = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
    rgba[:, :, :3] = arr
    rgba[:, :, 3] = mask
    return Image.fromarray(rgba, "RGBA")


def process_torso(src_path: Path) -> Image.Image:
    """Scale the 2048×2048 torso to the shared 1254×1254 canvas via RGB bg removal.

    The torso's alpha channel is all-255 (opaque white background, not transparent),
    so we use the same background-subtraction approach as the other RGB layers.
    """
    img = Image.open(src_path).convert("RGB")
    scaled = img.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    arr = np.array(scaled)
    mask = extract_foreground(arr)

    rgba = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
    rgba[:, :, :3] = arr
    rgba[:, :, 3] = mask
    return Image.fromarray(rgba, "RGBA")


def composite_all(layers_in_z_order: list[tuple[str, Image.Image]]) -> Image.Image:
    """Composite RGBA layers from bottom z to top z onto a transparent canvas."""
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    for name, img in layers_in_z_order:
        canvas = Image.alpha_composite(canvas, img)
    return canvas


def main():
    manifest = []
    by_z = []

    for out_name, src_name, z in LAYERS:
        src = ROOT / src_name
        if not src.exists():
            print(f"  SKIP {src_name} (not found)")
            continue

        if "torso" in out_name:
            layer_img = process_torso(src)
        else:
            layer_img = process_rgb_layer(src)

        out_path = OUT / f"modern_archivist_{out_name}.png"
        layer_img.save(out_path)

        # Report
        arr = np.array(layer_img)
        fg_count = int((arr[:, :, 3] > 0).sum())
        fg_rows = np.where((arr[:, :, 3] > 0).any(axis=1))[0]
        fg_cols = np.where((arr[:, :, 3] > 0).any(axis=0))[0]
        bbox = (
            [int(fg_cols[0]), int(fg_rows[0]), int(fg_cols[-1]), int(fg_rows[-1])]
            if len(fg_rows) > 0 else None
        )
        print(f"  {out_name}: fg={fg_count}px, bbox={bbox}")
        manifest.append({"layer": out_name, "z": z, "bbox": bbox, "fg_pixels": fg_count})
        by_z.append((z, out_name, layer_img))

    # Composite reference (eyes closed, mouth neutral, all layers)
    by_z.sort(key=lambda x: x[0])
    static_layers = [
        (name, img) for z, name, img in by_z
        if name not in ("head_neutral", "mouth_talk_a", "mouth_talk_b")
    ]
    composite = composite_all(static_layers)
    composite_path = OUT / "composite_eyes_closed.png"
    composite.save(composite_path)
    print(f"\nComposite (eyes closed): {composite_path}")

    # Also composite neutral (head_neutral instead of head_eyes_closed)
    neutral_layers = [
        (name, img) for z, name, img in by_z
        if name not in ("head_eyes_closed", "mouth_talk_a", "mouth_talk_b")
    ]
    composite_neutral = composite_all(neutral_layers)
    composite_neutral.save(OUT / "composite_neutral.png")

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Manifest: {OUT / 'manifest.json'}")


if __name__ == "__main__":
    main()
