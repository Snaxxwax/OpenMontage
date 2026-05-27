#!/usr/bin/env python3
"""
Extract canvas-registered puppet layers from source PNGs.

All sources are 1254x1254 RGB with a near-white background (~246,246,246).
Outputs 1254x1254 RGBA PNGs to ../character/layers/ and
remotion-composer/public/modern-archivist/layers/.

Layers produced:
  hair_back      - hair bun + side strands (renders behind head, z=2)
  hair_front     - bangs / foreground fringe (renders over head, z=4)
  head           - face/skin only (no hair), z=3
  eye_open_l/r   - open eyes from head_neutral
  eye_closed_l/r - closed eyes from head_eyes_closed
  brow_neutral_l/r - brows from head_neutral
  body           - torso/hoodie
  arm_right_idle - arm only (no hand/mug)
  hand_mug       - hand holding mug
  mug            - the mug prop
  shadow         - drop shadow
  glasses_frame  - glasses
  lens_highlight - lens shine
"""

from pathlib import Path
import numpy as np
import cv2
from PIL import Image

ROOT = Path(__file__).parent
SRC = ROOT
LAYERS_OUT = ROOT.parent / "character" / "layers"
REMOTION_OUT = ROOT.parent.parent.parent.parent / "remotion-composer" / "public" / "modern-archivist" / "layers"
CANVAS = 1254
BG_THRESH = 28
MIN_COMPONENT = 80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_rgb(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    if img.size != (CANVAS, CANVAS):
        img = img.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    return np.array(img)


def detect_bg(arr: np.ndarray, n: int = 30) -> np.ndarray:
    corners = np.concatenate([
        arr[:n, :n].reshape(-1, 3),
        arr[:n, -n:].reshape(-1, 3),
        arr[-n:, :n].reshape(-1, 3),
        arr[-n:, -n:].reshape(-1, 3),
    ])
    return np.median(corners, axis=0)


def fg_mask(arr: np.ndarray, thresh: float = BG_THRESH, min_component: int = MIN_COMPONENT) -> np.ndarray:
    bg = detect_bg(arr)
    diff = np.linalg.norm(arr.astype(np.float32) - bg, axis=2)
    raw = (diff > thresh).astype(np.uint8)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(raw, connectivity=8)
    clean = np.zeros_like(raw)
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] >= min_component:
            clean[labels == i] = 1
    return clean.astype(bool)


def save_layer(arr_rgb: np.ndarray, mask: np.ndarray, name: str) -> dict:
    rgba = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
    rgba[:, :, :3] = arr_rgb
    rgba[:, :, 3] = (mask * 255).astype(np.uint8)

    img = Image.fromarray(rgba, "RGBA")

    fname = f"modern_archivist_{name}.png"
    for out_dir in [LAYERS_OUT, REMOTION_OUT]:
        out_dir.mkdir(parents=True, exist_ok=True)
        img.save(out_dir / fname)

    visible = int(mask.sum())
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    bbox = (int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])) if visible else None
    transparent = 1.0 - visible / (CANVAS * CANVAS)
    print(f"  {name}: visible={visible}, bbox={bbox}, transparent={transparent:.4f}")
    return {"layer": name, "visible_px": visible, "bbox": bbox}


def find_face_mask(arr: np.ndarray, fg: np.ndarray) -> np.ndarray:
    """Find largest connected skin-tone region (mid-grey)."""
    brightness = arr.mean(axis=2)
    skin = fg & (brightness > 85) & (brightness < 225)
    skin_u8 = (skin * 255).astype(np.uint8)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(skin_u8, connectivity=8)
    if num < 2:
        return skin
    largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
    return (labels == largest)


# ---------------------------------------------------------------------------
# Head neutral: hair_back, hair_front, head (face only)
# ---------------------------------------------------------------------------

def extract_head_layers():
    arr = load_rgb(SRC / "modern_archivist_head_neutral.png")
    fg = fg_mask(arr)
    brightness = arr.mean(axis=2)

    # Hair = dark foreground pixels (includes grey-blue mid-tones in hair shading)
    hair = fg & (brightness < 115)

    # Skin/face region
    face = find_face_mask(arr, fg)
    face_rows = np.where(face.any(axis=1))[0]
    face_cols = np.where(face.any(axis=0))[0]
    face_y1, face_y2 = int(face_rows[0]), int(face_rows[-1])
    face_x1, face_x2 = int(face_cols[0]), int(face_cols[-1])

    # Bangs zone: dark pixels that sit just above and at the top of the face,
    # within the face's horizontal span. These render IN FRONT of the head layer.
    bangs_y_lo = max(0, face_y1 - 60)
    bangs_y_hi = face_y1 + 110  # ~25% into the face height
    bangs_x_lo = max(0, face_x1 - 40)
    bangs_x_hi = min(CANVAS, face_x2 + 40)

    bangs_zone = np.zeros((CANVAS, CANVAS), dtype=bool)
    bangs_zone[bangs_y_lo:bangs_y_hi, bangs_x_lo:bangs_x_hi] = True

    hair_front = hair & bangs_zone
    hair_back  = hair & ~bangs_zone

    # Morphological cleanup: close small gaps in each hair layer
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    hair_back_clean  = cv2.morphologyEx(hair_back.astype(np.uint8),  cv2.MORPH_CLOSE, kernel).astype(bool)
    hair_front_clean = cv2.morphologyEx(hair_front.astype(np.uint8), cv2.MORPH_CLOSE, kernel).astype(bool)

    # Head layer = everything in fg that is NOT dark hair (skin + details)
    head_layer = fg & ~hair

    save_layer(arr, hair_back_clean,  "hair_back")
    save_layer(arr, hair_front_clean, "hair_front")
    save_layer(arr, head_layer,       "head")

    print(f"    Face bbox: x={face_x1}-{face_x2}, y={face_y1}-{face_y2}")
    print(f"    Bangs zone: x={bangs_x_lo}-{bangs_x_hi}, y={bangs_y_lo}-{bangs_y_hi}")


# ---------------------------------------------------------------------------
# Eyes (open) extracted from head_neutral
# ---------------------------------------------------------------------------

def extract_open_eyes():
    arr = load_rgb(SRC / "modern_archivist_head_neutral.png")
    fg = fg_mask(arr)
    face = find_face_mask(arr, fg)
    face_rows = np.where(face.any(axis=1))[0]
    face_y1 = int(face_rows[0])
    face_cx = 534  # measured center x from analysis

    # Eyes sit roughly at 20-45% down from top of face
    face_h = int(face_rows[-1]) - face_y1
    eye_y1 = face_y1 + int(face_h * 0.18)
    eye_y2 = face_y1 + int(face_h * 0.48)

    # Left eye: right side of canvas (character's left = viewer's right)
    mid_x = face_cx
    eye_zone_l = np.zeros((CANVAS, CANVAS), dtype=bool)
    eye_zone_l[eye_y1:eye_y2, mid_x:min(CANVAS, mid_x+220)] = True

    eye_zone_r = np.zeros((CANVAS, CANVAS), dtype=bool)
    eye_zone_r[eye_y1:eye_y2, max(0, mid_x-220):mid_x] = True

    brightness = arr.mean(axis=2)
    # Eyes are darker than skin but may include whites; include fg in zone
    eye_pixels = fg & (np.arange(CANVAS)[:, None] >= eye_y1) & (np.arange(CANVAS)[:, None] <= eye_y2)

    save_layer(arr, eye_pixels & eye_zone_l, "eye_open_l")
    save_layer(arr, eye_pixels & eye_zone_r, "eye_open_r")


# ---------------------------------------------------------------------------
# Eyes (closed) from head_eyes_closed
# ---------------------------------------------------------------------------

def extract_closed_eyes():
    arr = load_rgb(SRC / "modern_archivist_head_eyes_closed.png")
    fg = fg_mask(arr)
    face = find_face_mask(arr, fg)
    face_rows = np.where(face.any(axis=1))[0]
    face_y1 = int(face_rows[0])
    face_h  = int(face_rows[-1]) - face_y1

    eye_y1 = face_y1 + int(face_h * 0.18)
    eye_y2 = face_y1 + int(face_h * 0.45)
    mid_x = 534

    eye_band = np.zeros((CANVAS, CANVAS), dtype=bool)
    eye_band[eye_y1:eye_y2, :] = True

    eye_zone_l = eye_band.copy()
    eye_zone_l[:, :mid_x] = False
    eye_zone_r = eye_band.copy()
    eye_zone_r[:, mid_x:] = False

    eye_pixels = fg & eye_band

    save_layer(arr, eye_pixels & eye_zone_l, "eye_closed_l")
    save_layer(arr, eye_pixels & eye_zone_r, "eye_closed_r")


# ---------------------------------------------------------------------------
# Brows (neutral) from head_neutral
# ---------------------------------------------------------------------------

def extract_brows_neutral():
    arr = load_rgb(SRC / "modern_archivist_head_neutral.png")
    fg = fg_mask(arr)
    face = find_face_mask(arr, fg)
    face_rows = np.where(face.any(axis=1))[0]
    face_y1 = int(face_rows[0])
    face_h  = int(face_rows[-1]) - face_y1

    # Brows sit just above the eyes, in the upper face
    brow_y1 = face_y1 - 10
    brow_y2 = face_y1 + int(face_h * 0.22)
    mid_x = 534

    brightness = arr.mean(axis=2)
    # Brows = dark pixels in the brow band (use tighter threshold than hair to avoid capturing hair mid-tones)
    brow_pixels = fg & (brightness < 80) & (np.arange(CANVAS)[:, None] >= brow_y1) & (np.arange(CANVAS)[:, None] <= brow_y2)

    brow_l_mask = brow_pixels.copy(); brow_l_mask[:, :mid_x] = False
    brow_r_mask = brow_pixels.copy(); brow_r_mask[:, mid_x:] = False

    save_layer(arr, brow_l_mask, "brow_neutral_l")
    save_layer(arr, brow_r_mask, "brow_neutral_r")


# ---------------------------------------------------------------------------
# Body from torso_hoodie (canvas-registered with head_neutral)
# ---------------------------------------------------------------------------
# torso_hoodie.png is 2048×2048; load_rgb() resizes it to 1254×1254.
# After resize, the torso occupies roughly y=645–1253 on the shared canvas.
# full_body_mug_pose.png is a DIFFERENT canvas registration (face at y≈302)
# and must NOT be used as the body source.

def extract_body():
    arr = load_rgb(SRC / "modern_archivist_torso_hoodie.png")
    fg = fg_mask(arr)

    # torso_hoodie contains only the torso; no head cutoff needed.
    save_layer(arr, fg, "body")


# ---------------------------------------------------------------------------
# Arm + hand + mug from arm_mug_grip (all canvas-registered)
# ---------------------------------------------------------------------------
# arm_mug_grip.png: canvas-registered, arm+hand+mug at x=84-445, y=501-1220
# mug_code.png is NOT canvas-registered (mug centered at face position, not at
# the arm's actual canvas position) — do NOT use it as the mug layer source.
#
# Puppet z-order: arm_right_idle(z=10) → mug(z=11) → hand_mug(z=12)
# Splits from arm_mug_grip:
#   arm_right_idle  = sleeve pixels (y >= 720)
#   mug             = dark pixels in upper grip zone (y < 720, brightness < 90)
#   hand_mug        = remaining pixels in upper grip zone (y < 720, brightness >= 90)

def extract_arm_layers():
    # Use a tighter threshold (40) for arm to avoid background-fringe near-white pixels.
    arm_arr = load_rgb(SRC / "modern_archivist_arm_mug_grip.png")
    arm_fg = fg_mask(arm_arr, thresh=40)

    # Erode mask by 1px to remove antialiasing fringe at background boundary.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    arm_fg_clean = cv2.erode(arm_fg.astype(np.uint8), kernel, iterations=1).astype(bool)

    brightness = arm_arr.mean(axis=2)
    row_idx = np.arange(CANVAS)[:, None]  # (1254, 1) for broadcasting

    # Arm = sleeve portion (below wrist split)
    arm_mask = arm_fg_clean & (row_idx >= 720)

    # Mug = dark pixels in the upper grip zone (the dark navy mug body)
    mug_mask = arm_fg_clean & (row_idx < 720) & (brightness < 90)

    # Hand = remaining fg pixels in the upper grip zone (sleeve/skin around mug)
    hand_mask = arm_fg_clean & (row_idx < 720) & (brightness >= 90)

    save_layer(arm_arr, arm_mask,  "arm_right_idle")
    save_layer(arm_arr, mug_mask,  "mug")
    save_layer(arm_arr, hand_mask, "hand_mug")


# ---------------------------------------------------------------------------
# Shadow: synthesized ellipse (no shadow layer in source images)
# ---------------------------------------------------------------------------

def extract_shadow():
    # Drop-shadow ellipse at the base of the character
    arr = load_rgb(SRC / "modern_archivist_full_body_mug_pose.png")
    shadow_mask = np.zeros((CANVAS, CANVAS), dtype=bool)
    cy, cx, ry, rx = 1210, 627, 30, 300
    yy, xx = np.ogrid[:CANVAS, :CANVAS]
    shadow_mask = ((yy - cy)**2 / ry**2 + (xx - cx)**2 / rx**2) <= 1.0
    save_layer(arr, shadow_mask, "shadow")


# ---------------------------------------------------------------------------
# Glasses from glasses_round_black
# ---------------------------------------------------------------------------

def extract_glasses():
    arr = load_rgb(SRC / "modern_archivist_glasses_round_black.png")
    fg = fg_mask(arr)
    brightness = arr.mean(axis=2)

    # Glasses frame = dark pixels
    frame_mask = fg & (brightness < 90)
    # Lens highlight = bright pixels within glasses zone (inside lens)
    lens_zone = fg & (brightness > 200) & (np.arange(CANVAS)[:, None] > 350) & (np.arange(CANVAS)[:, None] < 700)

    save_layer(arr, frame_mask, "glasses_frame")
    save_layer(arr, lens_zone,  "lens_highlight")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Extracting puppet layers from source PNGs...")
    print()

    print("Head layers (hair_back, hair_front, head):")
    extract_head_layers()
    print()

    print("Open eyes (eye_open_l, eye_open_r):")
    extract_open_eyes()
    print()

    print("Closed eyes (eye_closed_l, eye_closed_r):")
    extract_closed_eyes()
    print()

    print("Neutral brows (brow_neutral_l, brow_neutral_r):")
    extract_brows_neutral()
    print()

    print("Body:")
    extract_body()
    print()

    print("Arm / hand / mug:")
    extract_arm_layers()
    print()

    print("Shadow:")
    extract_shadow()
    print()

    print("Glasses:")
    extract_glasses()
    print()

    print("Done. Layers written to character/layers/ and remotion-composer/public/.")


if __name__ == "__main__":
    main()
