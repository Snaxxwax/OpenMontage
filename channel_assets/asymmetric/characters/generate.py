"""
Generate Asymmetric brand character reference stills via local ComfyUI (SD 1.5).
Runs sequentially — one at a time on the local GPU.

Usage: python3 channel_assets/asymmetric/characters/generate.py
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from tools.graphics.comfyui_image import ComfyUIImage

OUT = Path(__file__).parent

# ── SD 1.5 workflow template (juggernaut_reborn, KSampler) ──────────────────
def make_workflow(prompt: str, negative: str, seed: int, width=512, height=768,
                  steps=20, cfg=7.5, filename_prefix="character") -> str:
    wf = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "epiCRealism_naturalSinRC1VAE.safetensors"}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]}
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["1", 1]}
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1}
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "dpm_2_ancestral",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]}
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["6", 0]}
        }
    }
    return json.dumps(wf)


NEGATIVE = (
    "face, eyes, smile, happy, text, watermark, logo, signature, blurry, "
    "low quality, deformed, ugly, cartoon, anime, bright colors, daytime, "
    "cheerful, colorful background, nsfw, "
    "near-black background, dark background, black background, deep slate, glowing"
)

# ── Character definitions ────────────────────────────────────────────────────
CHARACTERS = [
    {
        "name": "gatekeeper",
        "seed": 2847,
        "prompt": (
            "editorial print photography, figure seen from behind standing at a heavy institutional door, "
            "warm paper tones, FT magazine aesthetic, cream and warm ink palette, dark navy suit, "
            "single burnt orange light glowing from beyond the door, "
            "dramatic volumetric lighting, shadows in warm ink tones, "
            "photorealistic, editorial, 35mm film, ultra sharp"
        ),
    },
    {
        "name": "strategist",
        "seed": 5193,
        "prompt": (
            "editorial print photography, lone figure from behind standing before a large display "
            "showing network maps and data flows, warm paper tones, FT magazine aesthetic, "
            "ink blue light from the screen illuminating the figure's silhouette, "
            "cream and ink palette, dramatic edge lighting, "
            "photorealistic, editorial, 35mm film, ultra sharp"
        ),
    },
    {
        "name": "broker",
        "seed": 9031,
        "prompt": (
            "editorial print photography, figure standing at an intersection corridor, low three-quarter angle, "
            "warm paper tones, FT magazine aesthetic, burnt orange light casting long shadows in multiple directions, "
            "dark suit, warm ink shadows, mysterious institutional atmosphere, "
            "photorealistic, editorial, 35mm film, ultra sharp"
        ),
    },
    {
        "name": "extractor",
        "seed": 3764,
        "prompt": (
            "editorial print photography, figure from behind operating a large industrial valve or lever "
            "in a pipeline facility, warm paper tones, FT magazine aesthetic, "
            "deep crimson and burnt orange accent lighting from below, "
            "heavy industrial machinery, warm ink shadows, dramatic low-key lighting, "
            "photorealistic, editorial, 35mm film, ultra sharp"
        ),
    },
    {
        "name": "swarm",
        "seed": 7420,
        "prompt": (
            "editorial print photography, aerial photograph looking down at a dense crowd of uniform figures, "
            "warm paper tones, FT magazine aesthetic, burnt orange light highlighting a single cluster at the center, "
            "all others in warm ink shadow, minimal, abstract mass of people, dramatic overhead lighting, "
            "photorealistic, editorial, 35mm film, ultra sharp"
        ),
    },
]

# ── Generate ─────────────────────────────────────────────────────────────────
tool = ComfyUIImage()

for char in CHARACTERS:
    print(f"\n→ Generating: {char['name']} (seed {char['seed']})")
    out_path = OUT / f"{char['name']}.png"

    result = tool.execute({
        "prompt": char["prompt"],   # passed for logging; actual prompt is in workflow_json
        "workflow_json": make_workflow(
            prompt=char["prompt"],
            negative=NEGATIVE,
            seed=char["seed"],
            width=512,
            height=768,
            filename_prefix=char["name"],
        ),
        "output_node": "7",
        "output_path": str(out_path),
        "timeout_seconds": 300,
    })

    if result.success:
        files = result.artifacts or []
        print(f"  ✓ Saved: {[str(f) for f in files]}")
    else:
        print(f"  ✗ FAILED: {result.error}")

print("\nDone.")
