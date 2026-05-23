#!/usr/bin/env python3
"""Generate Modern Archivist / Failure Ledger source assets using OpenAI Images API.

Outputs are reference/source sheets for Krita cleanup and Remotion integration,
not final cut-out puppet layers.
"""
import base64
import json
import os
import pathlib
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "channels" / "modern-archivist" / "assets" / "source"
OUT_DIR = ASSET_DIR / "openai_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    raise SystemExit("OPENAI_API_KEY is not set")

MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
ENDPOINT = "https://api.openai.com/v1/images/edits"

REFS = [
    ASSET_DIR / "modern_archivist_full_body_mug_pose.png",
    ASSET_DIR / "modern_archivist_head_neutral.png",
    ASSET_DIR / "modern_archivist_mug_code.png",
]
for p in REFS:
    if not p.exists():
        raise SystemExit(f"missing reference image: {p}")

STYLE = """
Preserve the provided character design exactly: wavy medium-brown hair, round black glasses,
large expressive eyes, neutral tired archivist expression, dark hoodie, black coffee mug with code symbol,
flat 2.5D vector/anime hybrid look, clean readable shapes, crisp edges, no photorealism.
Channel tone: dark forensic documentary, corporate autopsy, evidence archive, dry and deadpan.
Use transparent background when the asset is a sheet of parts. Do not add logos, watermarks, text labels, or captions.
Keep elements cleanly separated with negative space so they can be cut apart in Krita.
""".strip()

JOBS = [
    {
        "filename": "modern_archivist_expression_sheet_openai.png",
        "background": "transparent",
        "prompt": STYLE + "\n\nCreate a 3x3 expression reference sheet for the same Archivist character. Bust/head only. Expressions: neutral, skeptical, tired, annoyed, eyes closed sigh, half-lidded deadpan, slight smirk, concerned, critical-error red-lit stare. Keep the same face, hair, glasses, and drawing style. Separate each head with whitespace. Transparent background.",
    },
    {
        "filename": "modern_archivist_mouth_phoneme_sheet_openai.png",
        "background": "transparent",
        "prompt": STYLE + "\n\nCreate a clean mouth phoneme asset sheet matching the provided character. Mouth only, no full face. Include 8 separated mouth shapes: closed, slight open, A, E, O, wide, frown, smirk. Same line weight and color style as the source. Transparent background. No labels.",
    },
    {
        "filename": "modern_archivist_arm_mug_pose_sheet_openai.png",
        "background": "transparent",
        "prompt": STYLE + "\n\nCreate a puppet pose reference sheet for the Archivist's right arm, hand, and black code mug. Include 5 separated pose elements: idle hand, mug grip low, mug halfway up, sip pose, lowered mug after sip. Preserve hoodie sleeve color and mug design. Transparent background. Clean separation for layer cutting. No labels.",
    },
    {
        "filename": "failure_ledger_props_sheet_openai.png",
        "background": "transparent",
        "prompt": STYLE + "\n\nCreate a reusable prop sheet for the channel in the same flat 2.5D vector style: red filing stamp, bankruptcy folder, SEC filing page, court exhibit binder, evidence box, old CRT monitor, server rack, stock ticker strip, shredded document pile, desk lamp. Isolated elements, transparent background, no labels, no real company logos.",
    },
    {
        "filename": "failure_ledger_archive_room_background_openai.png",
        "background": "opaque",
        "prompt": STYLE + "\n\nCreate a 16:9 dark archive-room background plate for The Failure Ledger. Moody desk, filing cabinets, shelves, evidence boxes, soft monitor glow, corporate forensics aesthetic. No people. No text. Flat 2.5D vector/anime hybrid, clean geometry, suitable as a Remotion background layer.",
    },
    {
        "filename": "failure_ledger_thumbnail_style_sheet_openai.png",
        "background": "opaque",
        "prompt": STYLE + "\n\nCreate a thumbnail style concept sheet with four clean, high-contrast compositions for a corporate failure documentary channel. Use abstract evidence visuals only: falling red chart, redacted filing, court stamp, broken product silhouette, glowing spreadsheet, archive desk. No real logos and no readable text. Dark premium YouTube documentary aesthetic.",
    },
]

headers = {"Authorization": f"Bearer {API_KEY}"}
manifest = {
    "model": MODEL,
    "endpoint": ENDPOINT,
    "reference_images": [str(p) for p in REFS],
    "outputs": [],
}

for idx, job in enumerate(JOBS, start=1):
    out = OUT_DIR / job["filename"]
    if out.exists() and out.stat().st_size > 0:
        print(f"SKIP existing {out}")
        manifest["outputs"].append({"file": str(out), "status": "existing"})
        continue
    print(f"[{idx}/{len(JOBS)}] generating {out.name}", flush=True)
    files = []
    opened = []
    try:
        for ref in REFS:
            fh = open(ref, "rb")
            opened.append(fh)
            files.append(("image[]", (ref.name, fh, "image/png")))
        data = {
            "model": MODEL,
            "prompt": job["prompt"],
            "size": "1024x1024",
            "quality": "medium",
            "n": "1",
        }
        if job.get("background") == "transparent":
            data["background"] = "transparent"
        resp = requests.post(ENDPOINT, headers=headers, data=data, files=files, timeout=300)
        if resp.status_code >= 400:
            print(resp.text, file=sys.stderr)
            raise RuntimeError(f"OpenAI API error {resp.status_code} for {out.name}")
        payload = resp.json()
        b64 = payload["data"][0].get("b64_json")
        if not b64:
            raise RuntimeError(f"No b64_json in response for {out.name}: {payload}")
        out.write_bytes(base64.b64decode(b64))
        manifest["outputs"].append({"file": str(out), "status": "generated", "bytes": out.stat().st_size})
        print(f"WROTE {out} ({out.stat().st_size} bytes)", flush=True)
    finally:
        for fh in opened:
            fh.close()
    time.sleep(2)

manifest_path = OUT_DIR / "openai_generation_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
