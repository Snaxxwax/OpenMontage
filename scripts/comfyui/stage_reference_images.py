"""
Stage Modern Archivist reference images into ComfyUI's input directory.

Run before submitting any archivist ComfyUI workflow. ComfyUI LoadImage nodes
can only read from the input directory, so reference images must be copied there
first. This script is idempotent — safe to run multiple times.
"""
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMFYUI_INPUT = Path.home() / "ComfyUI" / "input" / "modern_archivist"

SOURCES = {
    "modern_archivist_arm_mug_grip.png": "channels/modern-archivist/assets/source/modern_archivist_arm_mug_grip.png",
    "modern_archivist_full_body_mug_pose.png": "channels/modern-archivist/assets/source/modern_archivist_full_body_mug_pose.png",
    "modern_archivist_mug_code.png": "channels/modern-archivist/assets/source/modern_archivist_mug_code.png",
    "modern_archivist_head_neutral.png": "channels/modern-archivist/assets/source/modern_archivist_head_neutral.png",
    "modern_archivist_torso_hoodie.png": "channels/modern-archivist/assets/source/modern_archivist_torso_hoodie.png",
}


def stage():
    COMFYUI_INPUT.mkdir(parents=True, exist_ok=True)
    staged, missing = [], []

    for dest_name, rel_src in SOURCES.items():
        src = REPO_ROOT / rel_src
        dst = COMFYUI_INPUT / dest_name
        if not src.exists():
            missing.append(str(rel_src))
            continue
        shutil.copy2(src, dst)
        staged.append(dest_name)

    for name in staged:
        print(f"[staged]  {COMFYUI_INPUT / name}")
    for path in missing:
        print(f"[missing] {path}")

    if missing:
        print(f"\n{len(missing)} source(s) not found — workflow may fail for those images.")
    else:
        print(f"\nAll {len(staged)} reference images staged to {COMFYUI_INPUT}")


if __name__ == "__main__":
    stage()
