#!/usr/bin/env python3
"""
Assemble narrator sprites into a standing A-pose preview.
Uses tight bounding boxes (non-transparent region) for joint alignment,
composites everything in z-order, and prints measured anchor values
to update narrator_manifest.json.

Output: narrator_tpose.png   (written to repo root)
"""

from pathlib import Path
from PIL import Image
import numpy as np

CANVAS_W, CANVAS_H = 1122, 1402
SPRITE_DIR = Path(__file__).resolve().parents[4] / "remotion-composer" / "public" / "narrator"
OUT_IMG = Path(__file__).resolve().parents[4] / "narrator_tpose.png"

JOINT_OVERLAP = 18   # px of overlap at each joint to hide gap
HEAD_TOP_Y    = 55   # px from canvas top to head artwork top
LEG_HALF_SEP  = 68   # half-separation between leg center x and canvas center

FACE_SCALE_EYES  = 0.30
FACE_SCALE_BROWS = 0.30
FACE_SCALE_MOUTH = 0.22
FACE_SCALE_GLASS = 0.25


# ─── Sprite loader ────────────────────────────────────────────────────────────

def load(name: str) -> dict:
    path = SPRITE_DIR / f"narrator_{name}.png"
    img  = Image.open(path).convert("RGBA")
    arr  = np.array(img)
    alpha = arr[:, :, 3]
    rows  = np.any(alpha > 20, axis=1)
    cols  = np.any(alpha > 20, axis=0)
    if rows.any():
        y0, y1 = int(np.where(rows)[0][0]),  int(np.where(rows)[0][-1])
        x0, x1 = int(np.where(cols)[0][0]),  int(np.where(cols)[0][-1])
    else:
        y0, y1, x0, x1 = 0, img.height-1, 0, img.width-1
    return dict(img=img, alpha=alpha, w=img.width, h=img.height,
                bx0=x0, by0=y0, bx1=x1, by1=y1,
                bcx=(x0+x1)//2, bcy=(y0+y1)//2,
                bw=x1-x0+1, bh=y1-y0+1)


def tip_right(s: dict) -> int:
    """Rightmost pixel in the first non-empty row (shoulder/joint tip)."""
    row = s["by0"]
    cols = np.where(s["alpha"][row] > 20)[0]
    return int(cols[-1]) if len(cols) else s["bx1"]


def tip_left(s: dict) -> int:
    """Leftmost pixel in the first non-empty row (shoulder/joint tip)."""
    row = s["by0"]
    cols = np.where(s["alpha"][row] > 20)[0]
    return int(cols[0]) if len(cols) else s["bx0"]


# ─── Placement helpers ────────────────────────────────────────────────────────

def place(canvas: Image.Image, s: dict, lx: int, ty: int) -> None:
    canvas.paste(s["img"], (lx, ty), s["img"])


def anchor_of(s: dict, lx: int, ty: int, pivot_x: float, pivot_y: float):
    """Return (anchor_x, anchor_y) fractions given sprite top-left position."""
    ax = (lx + s["w"] * pivot_x) / CANVAS_W
    ay = (ty + s["h"] * pivot_y) / CANVAS_H
    return round(ax, 4), round(ay, 4)


def cx_align(s: dict, cx: int) -> int:
    """Sprite left_x so its horizontal center falls on cx."""
    return cx - s["w"] // 2


def tight_top_at(s: dict, target_canvas_y: int) -> int:
    """Sprite top_y so its tight bbox top row is at target_canvas_y."""
    return target_canvas_y - s["by0"]


def tight_bottom_at(s: dict, target_canvas_y: int) -> int:
    """Sprite top_y so its tight bbox bottom row is at target_canvas_y."""
    return target_canvas_y - s["by1"]


def tight_bottom_canvas(s: dict, ty: int) -> int:
    return ty + s["by1"]


def tight_top_canvas(s: dict, ty: int) -> int:
    return ty + s["by0"]


def tight_left_canvas(s: dict, lx: int) -> int:
    return lx + s["bx0"]


def tight_right_canvas(s: dict, lx: int) -> int:
    return lx + s["bx1"]


# ─── Load sprites ─────────────────────────────────────────────────────────────

S = {k: load(k) for k in [
    "head", "torso", "waist_hips",
    "leg_left", "leg_right", "boot_left", "boot_right",
    "arm_upper_left", "arm_upper_right",
    "arm_forearm_left", "arm_forearm_right",
    "hand_left", "hand_right",
    "hair_back", "hair_bangs", "hair_curl_left", "hair_curl_right",
    "glasses_frame", "glasses_lenses",
    "eyes_open", "brows_neutral", "mouth_closed",
]}

CX = CANVAS_W // 2   # 561

results = {}   # layer_id → (anchor_x, anchor_y)


# ─── Canvas (dark background so transparent regions are visible) ──────────────

canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (30, 30, 30, 255))

# ─── HEAD ─────────────────────────────────────────────────────────────────────
#  pivot (0.5, 1.0) → anchor = bottom-center

head = S["head"]
hx = cx_align(head, CX)
hy = tight_top_at(head, HEAD_TOP_Y)    # tight top starts at HEAD_TOP_Y

head_tight_top    = tight_top_canvas(head, hy)
head_tight_bottom = tight_bottom_canvas(head, hy)
head_tight_left   = tight_left_canvas(head, hx)
head_tight_right  = tight_right_canvas(head, hx)
head_tight_cx     = (head_tight_left + head_tight_right) // 2
head_tight_h      = head_tight_bottom - head_tight_top

results["head"] = anchor_of(head, hx, hy, 0.5, 1.0)

# ─── TORSO ────────────────────────────────────────────────────────────────────
#  pivot (0.5, 1.0)

torso = S["torso"]
torso_tight_top_target = head_tight_bottom - JOINT_OVERLAP
tx = cx_align(torso, CX)
ty = tight_top_at(torso, torso_tight_top_target)

torso_tight_top    = tight_top_canvas(torso, ty)
torso_tight_bottom = tight_bottom_canvas(torso, ty)
torso_tight_left   = tight_left_canvas(torso, tx)
torso_tight_right  = tight_right_canvas(torso, tx)

results["torso"] = anchor_of(torso, tx, ty, 0.5, 1.0)

# ─── WAIST/HIPS ───────────────────────────────────────────────────────────────
#  pivot (0.5, 1.0)

waist = S["waist_hips"]
waist_tight_top_target = torso_tight_bottom - JOINT_OVERLAP
wx = cx_align(waist, CX)
wy = tight_top_at(waist, waist_tight_top_target)

waist_tight_top    = tight_top_canvas(waist, wy)
waist_tight_bottom = tight_bottom_canvas(waist, wy)

results["waist_hips"] = anchor_of(waist, wx, wy, 0.5, 1.0)

# ─── LEGS ─────────────────────────────────────────────────────────────────────
#  pivot (0.5, 0.0)

CX_LL = CX - LEG_HALF_SEP    # center x for left leg
CX_LR = CX + LEG_HALF_SEP    # center x for right leg

leg_l = S["leg_left"]
leg_r = S["leg_right"]
leg_tight_top_target = waist_tight_bottom - JOINT_OVERLAP

ll_x = cx_align(leg_l, CX_LL)
ll_y = tight_top_at(leg_l, leg_tight_top_target)
lr_x = cx_align(leg_r, CX_LR)
lr_y = tight_top_at(leg_r, leg_tight_top_target)

ll_tight_bottom = tight_bottom_canvas(leg_l, ll_y)
lr_tight_bottom = tight_bottom_canvas(leg_r, lr_y)

results["leg_left"]  = anchor_of(leg_l, ll_x, ll_y, 0.5, 0.0)
results["leg_right"] = anchor_of(leg_r, lr_x, lr_y, 0.5, 0.0)

# ─── BOOTS ────────────────────────────────────────────────────────────────────
#  pivot (0.5, 0.0)

boot_l = S["boot_left"]
boot_r = S["boot_right"]

bl_x = cx_align(boot_l, CX_LL)
bl_y = tight_top_at(boot_l, ll_tight_bottom - JOINT_OVERLAP)
br_x = cx_align(boot_r, CX_LR)
br_y = tight_top_at(boot_r, lr_tight_bottom - JOINT_OVERLAP)

results["boot_left"]  = anchor_of(boot_l, bl_x, bl_y, 0.5, 0.0)
results["boot_right"] = anchor_of(boot_r, br_x, br_y, 0.5, 0.0)

# ─── ARMS ─────────────────────────────────────────────────────────────────────
#  pivot (0.5, 0.0) — shoulder pins to anchor

arm_ul = S["arm_upper_left"]
arm_ur = S["arm_upper_right"]


def sprite_at_content_right(s: dict, target_right: int) -> int:
    """Sprite left_x so the tight bbox right pixel lands at target_right."""
    return target_right - s["bx1"]


def sprite_at_content_left(s: dict, target_left: int) -> int:
    """Sprite left_x so the tight bbox left pixel lands at target_left."""
    return target_left - s["bx0"]


def sprite_at_content_cx(s: dict, cx: int) -> int:
    """Sprite left_x so the tight bbox center x lands at cx."""
    return cx - (s["bx0"] + s["bw"] // 2)


# Find shoulder_y: first canvas row where the jacket widens to true shoulder width.
# The collar is narrow (~6px); the shoulder socket is where it first crosses
# SHOULDER_MIN_WIDTH. This is where the arm tip should connect.
SHOULDER_MIN_WIDTH = 130  # px
ARM_SHOULDER_GAP   = 4    # px of gap between arm tip and jacket edge at shoulder

shoulder_y            = torso_tight_top + 8  # fallback
torso_left_at_shldr  = torso_tight_left
torso_right_at_shldr = torso_tight_right

torso_alpha = torso["alpha"]
for row_off in range(0, torso["bh"]):
    row = torso["by0"] + row_off
    cols = np.where(torso_alpha[row] > 20)[0]
    if len(cols) and (int(cols[-1]) - int(cols[0])) >= SHOULDER_MIN_WIDTH:
        shoulder_y            = ty + row
        torso_left_at_shldr  = tx + int(cols[0])
        torso_right_at_shldr = tx + int(cols[-1])
        break

# Place arm tip so its rightmost pixel at the tip row sits ARM_SHOULDER_GAP
# px to the left of the jacket's left edge at shoulder_y (and symmetrically right).
aul_x = (torso_left_at_shldr - ARM_SHOULDER_GAP) - tip_right(arm_ul)
aul_y = shoulder_y - arm_ul["by0"]

aur_x = (torso_right_at_shldr + ARM_SHOULDER_GAP) - tip_left(arm_ur)
aur_y = shoulder_y - arm_ur["by0"]

# Content center X drives forearm and hand (straight vertical hang)
CONTENT_CX_L = aul_x + arm_ul["bx0"] + arm_ul["bw"] // 2
CONTENT_CX_R = aur_x + arm_ur["bx0"] + arm_ur["bw"] // 2

aul_tight_bottom = tight_bottom_canvas(arm_ul, aul_y)
aur_tight_bottom = tight_bottom_canvas(arm_ur, aur_y)

results["arm_upper_left"]  = anchor_of(arm_ul, aul_x, aul_y, 0.5, 0.0)
results["arm_upper_right"] = anchor_of(arm_ur, aur_x, aur_y, 0.5, 0.0)

# Forearms — content center aligned to upper arm
afl = S["arm_forearm_left"]
afr = S["arm_forearm_right"]

afl_x = sprite_at_content_cx(afl, CONTENT_CX_L)
afl_y = tight_top_at(afl, aul_tight_bottom - JOINT_OVERLAP)
afr_x = sprite_at_content_cx(afr, CONTENT_CX_R)
afr_y = tight_top_at(afr, aur_tight_bottom - JOINT_OVERLAP)

afl_tight_bottom = tight_bottom_canvas(afl, afl_y)
afr_tight_bottom = tight_bottom_canvas(afr, afr_y)

results["arm_forearm_left"]  = anchor_of(afl, afl_x, afl_y, 0.5, 0.0)
results["arm_forearm_right"] = anchor_of(afr, afr_x, afr_y, 0.5, 0.0)

# Hands — content center aligned to upper arm
hl = S["hand_left"]
hr = S["hand_right"]

hl_x = sprite_at_content_cx(hl, CONTENT_CX_L)
hl_y = tight_top_at(hl, afl_tight_bottom - JOINT_OVERLAP)
hr_x = sprite_at_content_cx(hr, CONTENT_CX_R)
hr_y = tight_top_at(hr, afr_tight_bottom - JOINT_OVERLAP)

results["hand_left"]  = anchor_of(hl, hl_x, hl_y, 0.5, 0.0)
results["hand_right"] = anchor_of(hr, hr_x, hr_y, 0.5, 0.0)

# ─── HAIR (center pivot, co-registered to head) ───────────────────────────────
hair_back  = S["hair_back"]
hair_bangs = S["hair_bangs"]
hair_cl    = S["hair_curl_left"]
hair_cr    = S["hair_curl_right"]

# Align hair tight-center to head tight-center (x and y)
def hair_align(hs, h_sprite_lx, h_sprite_ty, h_spr):
    head_tight_cx_canvas = h_sprite_lx + h_spr["bcx"]
    head_tight_cy_canvas = h_sprite_ty  + h_spr["bcy"]
    hx_placed = head_tight_cx_canvas - hs["bcx"]
    hy_placed = head_tight_cy_canvas - hs["bcy"]
    return int(hx_placed), int(hy_placed)

hbk_x, hbk_y   = hair_align(hair_back,  hx, hy, head)
hbng_x, hbng_y = hair_align(hair_bangs, hx, hy, head)
hcl_x, hcl_y   = hair_align(hair_cl,    hx, hy, head)
hcr_x, hcr_y   = hair_align(hair_cr,    hx, hy, head)

# Shift curls outward slightly
hcl_x -= 20
hcr_x += 20

results["hair_back"]       = anchor_of(hair_back,  hbk_x,  hbk_y,  0.5, 0.5)
results["hair_bangs"]      = anchor_of(hair_bangs, hbng_x, hbng_y, 0.5, 0.5)
results["hair_curl_left"]  = anchor_of(hair_cl,    hcl_x,  hcl_y,  0.5, 0.5)
results["hair_curl_right"] = anchor_of(hair_cr,    hcr_x,  hcr_y,  0.5, 0.5)

# ─── FACE OVERLAYS (scaled down, center pivot) ────────────────────────────────

def face_layer(key: str, scale: float, frac_y: float):
    """
    Place a face overlay (eyes/brows/mouth/glasses) scaled to `scale`,
    centered at (head_tight_cx, head_tight_top + head_tight_h * frac_y).
    Returns anchor (x, y) for manifest.
    """
    s = S[key]
    dw = max(1, int(s["w"] * scale))
    dh = max(1, int(s["h"] * scale))
    cy = head_tight_top + int(head_tight_h * frac_y)
    px = head_tight_cx - dw // 2
    py = cy - dh // 2
    scaled = s["img"].resize((dw, dh), Image.LANCZOS)
    canvas.paste(scaled, (px, py), scaled)
    # anchor = canvas fraction of center
    return round(head_tight_cx / CANVAS_W, 4), round(cy / CANVAS_H, 4)

# ─── COMPOSITE (z-ordered) ────────────────────────────────────────────────────

# z=5:  hair_back
place(canvas, hair_back, hbk_x, hbk_y)
# z=10: legs
place(canvas, leg_l, ll_x, ll_y)
place(canvas, leg_r, lr_x, lr_y)
# z=15: boots
place(canvas, boot_l, bl_x, bl_y)
place(canvas, boot_r, br_x, br_y)
# z=20: waist
place(canvas, waist, wx, wy)
# z=22-24: right arm (behind torso)
place(canvas, arm_ur, aur_x, aur_y)
place(canvas, afr,    afr_x, afr_y)
place(canvas, hr,     hr_x,  hr_y)
# z=25: torso
place(canvas, torso, tx, ty)
# z=27-29: left arm (in front)
place(canvas, arm_ul, aul_x, aul_y)
place(canvas, afl,    afl_x, afl_y)
place(canvas, hl,     hl_x,  hl_y)
# z=40: head
place(canvas, head, hx, hy)
# z=45: hair front
place(canvas, hair_bangs, hbng_x, hbng_y)
place(canvas, hair_cl,    hcl_x,  hcl_y)
place(canvas, hair_cr,    hcr_x,  hcr_y)

# z=48-49: glasses (behind eyes so lenses are visible through frames)
gfx, gfy = face_layer("glasses_lenses", FACE_SCALE_GLASS, 0.40)
gfx2, gfy2 = face_layer("glasses_frame", FACE_SCALE_GLASS, 0.40)

# z=50-60: face features
ex, ey   = face_layer("eyes_open",    FACE_SCALE_EYES,  0.40)
bx, by_  = face_layer("brows_neutral", FACE_SCALE_BROWS, 0.26)
mx, my_  = face_layer("mouth_closed", FACE_SCALE_MOUTH, 0.68)

results["glasses_lenses"] = (round(gfx,  4), round(gfy,  4))
results["glasses_frame"]  = (round(gfx2, 4), round(gfy2, 4))
results["eyes_*"]         = (round(ex,   4), round(ey,   4))
results["brows_*"]        = (round(bx,   4), round(by_,  4))
results["mouths_*"]       = (round(mx,   4), round(my_,  4))

canvas.save(str(OUT_IMG))
print(f"Saved: {OUT_IMG}")

print("\n── Measured anchors (paste into narrator_manifest.json) ──")
print(f"{'layer':<22}  anchor_x   anchor_y")
print("─" * 48)
for k, v in results.items():
    print(f"  {k:<20}  {v[0]:.4f}     {v[1]:.4f}")
