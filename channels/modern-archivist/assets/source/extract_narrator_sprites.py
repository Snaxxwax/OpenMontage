#!/usr/bin/env python3
"""Extract individual layer sprites from narrator sprite sheets.

Four source files in /home/pop/syncthing/:
  narrator_head_tilt.png  → body parts (head, torso, arms, legs, boots)
  narrator_bowing.png     → face expressions (eyes, brows, mouths)
  narrator_saluting.png   → arm gestures (point, present, mug, folder, open hand)
  narrator_clapping.png   → accessories (hair, glasses, mug, folder, papers)

Output: remotion-composer/public/narrator/ as RGBA PNGs with transparent background.
"""

from __future__ import annotations

from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image

try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

SRC_DIR = Path("/home/pop/syncthing")
OUT_DIR = Path(__file__).resolve().parents[4] / "remotion-composer" / "public" / "narrator"

# ─── Panel definitions: (source_file, row_y1, row_y2, col_x1, col_x2, output_name, label_side)
# Row/col bounds are the detected separator edges (content is inside them).
# label_side: "bottom" (default) or "top" — which side to trim the text label from.
LABEL_MARGIN_BOTTOM = 36   # for sheets with labels at bottom
LABEL_MARGIN_TOP = 52      # for narrator_bowing.png which has labels at top
BORDER_MARGIN = 4          # trim panel border edges

PANELS = [
    # ── narrator_head_tilt.png ──────────────────────────────────────────────
    # Row 1 (y=48-392): HEAD, TORSO, WAIST/HIPS, LEFT UPPER ARM
    ("narrator_head_tilt", 48,  392,  66,  348, "narrator_head",           "head"),
    ("narrator_head_tilt", 48,  392, 375,  708, "narrator_torso"),
    ("narrator_head_tilt", 48,  392, 737, 1025, "narrator_waist_hips"),
    ("narrator_head_tilt", 48,  392, 1060, 1377, "narrator_arm_upper_left"),
    # Row 2 (y=451-695): LEFT FOREARM, LEFT HAND, RIGHT UPPER ARM, RIGHT FOREARM, RIGHT HAND
    ("narrator_head_tilt", 451, 695,  66,  298, "narrator_arm_forearm_left"),
    ("narrator_head_tilt", 451, 695, 340,  549, "narrator_hand_left"),
    ("narrator_head_tilt", 451, 695, 588,  844, "narrator_arm_upper_right"),
    ("narrator_head_tilt", 451, 695, 887, 1113, "narrator_arm_forearm_right"),
    ("narrator_head_tilt", 451, 695, 1154, 1377, "narrator_hand_right"),
    # Row 3 (y=758-1056): LEFT LEG, RIGHT LEG, LEFT BOOT, RIGHT BOOT
    ("narrator_head_tilt", 758, 1056,  66,  329, "narrator_leg_left"),
    ("narrator_head_tilt", 758, 1056, 387,  667, "narrator_leg_right"),
    ("narrator_head_tilt", 758, 1056, 720, 1025, "narrator_boot_left"),
    ("narrator_head_tilt", 758, 1056, 1071, 1377, "narrator_boot_right"),

    # ── narrator_bowing.png ─────────────────────────────────────────────────
    # Labels are at the TOP of each panel in this sheet.
    # Row 1 (y=38-243): EYES OPEN FRONT, EYES HALF-LID FRONT, EYES CLOSED
    ("narrator_bowing",  38, 243,  34,  510, "narrator_eyes_open",       "top"),
    ("narrator_bowing",  38, 243, 529,  985, "narrator_eyes_half_lid",   "top"),
    ("narrator_bowing",  38, 243, 1004, 1429, "narrator_eyes_closed",    "top"),
    # Row 2 (y=269-443): EYES LOOK LEFT, EYES LOOK RIGHT
    ("narrator_bowing", 269, 443,  34,  720, "narrator_eyes_look_left",  "top"),
    ("narrator_bowing", 269, 443, 740, 1428, "narrator_eyes_look_right", "top"),
    # Row 3 (y=473-651): BROWS NEUTRAL, BROWS SKEPTICAL, BROWS FURROWED
    ("narrator_bowing", 473, 651,  35,  496, "narrator_brows_neutral",   "top"),
    ("narrator_bowing", 473, 651, 518,  962, "narrator_brows_skeptical", "top"),
    ("narrator_bowing", 473, 651, 983, 1428, "narrator_brows_furrowed",  "top"),
    # Row 4 (y=681-844): MOUTH CLOSED, MOUTH SMALL OPEN, MOUTH OPEN
    ("narrator_bowing", 681, 844,  35,  496, "narrator_mouth_closed",     "top"),
    ("narrator_bowing", 681, 844, 518,  962, "narrator_mouth_small_open", "top"),
    ("narrator_bowing", 681, 844, 983, 1428, "narrator_mouth_open",       "top"),
    # Row 5 (y=873-1048): MOUTH WIDE OPEN, MOUTH O, MOUTH FLAT, MOUTH SMIRK
    ("narrator_bowing", 873, 1048,  35,  384, "narrator_mouth_wide_open", "top"),
    ("narrator_bowing", 873, 1048, 409,  708, "narrator_mouth_o",         "top"),
    ("narrator_bowing", 873, 1048, 733, 1066, "narrator_mouth_flat",      "top"),
    ("narrator_bowing", 873, 1048, 1091, 1428, "narrator_mouth_smirk",    "top"),

    # ── narrator_saluting.png ───────────────────────────────────────────────
    # Row 1 (y=20-221): LEFT POINT, RIGHT POINT
    ("narrator_saluting",  20, 221,  34,  704, "narrator_arm_point_left"),
    ("narrator_saluting",  20, 221, 739, 1408, "narrator_arm_point_right"),
    # Row 2 (y=238-433): LEFT PRESENT, RIGHT PRESENT
    ("narrator_saluting", 238, 433,  34,  704, "narrator_arm_present_left"),
    ("narrator_saluting", 238, 433, 739, 1408, "narrator_arm_present_right"),
    # Row 3 (y=441-647): LEFT MUG HOLD, CENTER TWO-HAND MUG HOLD, RIGHT MUG HOLD
    ("narrator_saluting", 441, 647,  35,  489, "narrator_arm_mug_left"),
    ("narrator_saluting", 441, 647, 518,  920, "narrator_arm_mug_both"),
    ("narrator_saluting", 441, 647, 950, 1408, "narrator_arm_mug_right"),
    # Row 4 (y=659-888): LEFT FOLDER HOLD, RIGHT FOLDER HOLD
    ("narrator_saluting", 659, 888,  35,  704, "narrator_arm_folder_left"),
    ("narrator_saluting", 659, 888, 739, 1407, "narrator_arm_folder_right"),
    # Row 5 (y=897-1064): LEFT OPEN HAND, RIGHT OPEN HAND
    ("narrator_saluting", 897, 1064,  35,  703, "narrator_arm_open_left"),
    ("narrator_saluting", 897, 1064, 739, 1407, "narrator_arm_open_right"),

    # ── narrator_clapping.png ───────────────────────────────────────────────
    # Row 1: hair — use rembg for fine strand edges
    ("narrator_clapping",  25, 478,  34,  407, "narrator_hair_back",       "rembg"),
    ("narrator_clapping",  25, 478, 428,  775, "narrator_hair_bangs",      "rembg"),
    ("narrator_clapping",  25, 478, 795, 1084, "narrator_hair_curl_left",  "rembg"),
    ("narrator_clapping",  25, 478, 1105, 1410, "narrator_hair_curl_right","rembg"),
    # Row 2 (y=500-713): GLASSES FRAME, GLASSES LENSES
    ("narrator_clapping", 500, 713,  34,  709, "narrator_glasses_frame"),
    ("narrator_clapping", 500, 713, 733, 1410, "narrator_glasses_lenses"),
    # Row 3 (y=737-1045): MUG, MANILA FOLDER, PAPERS
    ("narrator_clapping", 737, 1045,  34,  462, "narrator_prop_mug"),
    ("narrator_clapping", 737, 1045, 483,  936, "narrator_prop_folder"),
    ("narrator_clapping", 737, 1045, 958, 1410, "narrator_prop_papers"),
]


def remove_background(img_rgba: np.ndarray, bg_threshold: int = 230,
                      fringe_passes: int = 3) -> np.ndarray:
    """Flood-fill from all 4 corners to mark near-white background as transparent.

    Pass 1: BFS from corners — removes all connected near-white background.
    Pass 2: fringe erosion — any pixel adjacent to a transparent pixel where all
            channels >= fringe_threshold also becomes transparent. Repeated for
            fringe_passes iterations to eat through anti-aliasing halo.
    """
    h, w = img_rgba.shape[:2]
    rgb = img_rgba[:, :, :3]
    is_bg = np.all(rgb >= bg_threshold, axis=2)

    visited = np.zeros((h, w), dtype=bool)
    transparent = np.zeros((h, w), dtype=bool)
    queue = deque()

    def enqueue_if_bg(r, c):
        if 0 <= r < h and 0 <= c < w and not visited[r, c] and is_bg[r, c]:
            visited[r, c] = True
            queue.append((r, c))

    # Seed from entire perimeter so one dark corner doesn't block the fill
    for c in range(w):
        enqueue_if_bg(0, c)
        enqueue_if_bg(h - 1, c)
    for r in range(1, h - 1):
        enqueue_if_bg(r, 0)
        enqueue_if_bg(r, w - 1)

    while queue:
        r, c = queue.popleft()
        transparent[r, c] = True
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            enqueue_if_bg(r + dr, c + dc)

    # Pass 2: fringe erosion — expand transparent into light adjacent pixels
    fringe_threshold = 210
    is_fringe = np.all(rgb >= fringe_threshold, axis=2)
    for _ in range(fringe_passes):
        # Find all opaque fringe pixels adjacent to a transparent pixel
        t = transparent
        neighbours = (
            np.roll(t, 1, axis=0) | np.roll(t, -1, axis=0) |
            np.roll(t, 1, axis=1) | np.roll(t, -1, axis=1)
        )
        new_transparent = neighbours & is_fringe & ~t
        if not new_transparent.any():
            break
        transparent |= new_transparent

    result = img_rgba.copy()
    result[transparent, 3] = 0
    return result


def extract_panel(src_path: Path, y1: int, y2: int, x1: int, x2: int,
                  label_side: str = "bottom") -> Image.Image:
    img = Image.open(src_path).convert("RGB")
    bm = BORDER_MARGIN
    use_rembg = label_side == "rembg"
    # For rembg sprites the label is at the bottom (clapping sheet)
    if label_side == "top":
        crop = img.crop((x1 + bm, y1 + LABEL_MARGIN_TOP, x2 - bm, y2 - bm))
    else:
        crop = img.crop((x1 + bm, y1 + bm, x2 - bm, y2 - LABEL_MARGIN_BOTTOM))

    if use_rembg and HAS_REMBG:
        result = rembg_remove(crop).convert("RGBA")
        # Remove semi-transparent white bleed rembg leaves around dark-content edges.
        arr = np.array(result)
        fringe = (arr[:, :, 3] > 0) & (arr[:, :, 3] < 255) & (arr[:, :, :3].mean(axis=2) > 180)
        arr[fringe, 3] = 0
        return Image.fromarray(arr, "RGBA")

    arr = np.array(crop)
    rgba = np.dstack([arr, np.full((arr.shape[0], arr.shape[1]), 255, dtype=np.uint8)])

    if label_side == "head":
        rgba = remove_background(rgba)
        # Additional global pass: remove achromatic bright pixels (hair interior gaps).
        # Safe because skin is warm-toned (R-B > 20); achromatic = grey/white background.
        rc = rgba[:, :, 0].astype(int)
        gc = rgba[:, :, 1].astype(int)
        bc = rgba[:, :, 2].astype(int)
        bright = rgba[:, :, :3].mean(axis=2)
        achromatic_bg = (bright > 180) & ((rc - bc) <= 20) & ((rc - gc) <= 12)
        rgba[achromatic_bg, 3] = 0
    else:
        rgba = remove_background(rgba)

    return Image.fromarray(rgba, "RGBA")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for entry in PANELS:
        label_side = entry[6] if len(entry) > 6 else "bottom"
        src_name, y1, y2, x1, x2, out_name = entry[:6]
        src_path = SRC_DIR / f"{src_name}.png"
        if not src_path.exists():
            print(f"  MISSING: {src_path}")
            continue

        out_path = OUT_DIR / f"{out_name}.png"
        img = extract_panel(src_path, y1, y2, x1, x2, label_side)
        img.save(out_path)
        w, h = img.size
        alpha = np.array(img)[:, :, 3]
        pct_transparent = 100 * (alpha == 0).mean()
        print(f"  {out_name}.png  {w}×{h}  {pct_transparent:.0f}% transparent")

    print(f"\nDone. Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
