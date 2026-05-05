import pytest
import subprocess
import shutil
from pathlib import Path
from tools.video.source_commentary_render_adapter import SourceCommentaryRenderAdapter
from tools.video.video_compose import VideoCompose

def is_remotion_available():
    """Check if npx is available and remotion-composer/node_modules exists."""
    if not shutil.which("npx"):
        return False
    composer_dir = Path(__file__).resolve().parent.parent.parent / "remotion-composer"
    node_modules = composer_dir / "node_modules"
    return node_modules.exists()

@pytest.mark.skipif(not is_remotion_available(), reason="Remotion/npx not available")
def test_source_commentary_render_poc(tmp_path):
    # 1. Generate a tiny deterministic local MP4 with ffmpeg
    # 2 seconds of a red background with a timestamp overlay
    input_clip = tmp_path / "fixture_clip.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=640x360:d=2",
        "-vf", "drawtext=text='%{pts\\:hms}':fontcolor=white:fontsize=24:x=(w-tw)/2:y=(h-th)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(input_clip)
    ], check=True, capture_output=True)
    
    # 2. Create a minimal source_commentary_edit_plan with one source_clip
    project_id = "poc-test"
    plan = {
        "version": "1.0",
        "project_id": project_id,
        "timeline": [
            {
                "clip_type": "source_clip",
                "receipt_id": "rcpt-poc",
                "claim_id": "claim-poc",
                "local_clip_path": str(input_clip),
                "duration_seconds": 2.0,
                "source_label_plan": {
                    "text": "POC SOURCE LABEL",
                    "position": "top-left"
                }
            }
        ]
    }
    
    # 3. Run source_commentary_render_adapter
    adapter = SourceCommentaryRenderAdapter()
    adapter_result = adapter.execute({
        "project_id": project_id,
        "source_commentary_edit_plan": plan,
        "render_runtime": "remotion"
    })
    assert adapter_result.success is True
    
    edit_decisions = adapter_result.data["edit_decisions"]
    asset_manifest = adapter_result.data["asset_manifest"]
    
    # 4. Call existing video_compose with render_runtime="remotion"
    output_path = tmp_path / "poc_output.mp4"
    composer = VideoCompose()
    render_result = composer.execute({
        "operation": "render",
        "edit_decisions": edit_decisions,
        "asset_manifest": asset_manifest,
        "output_path": str(output_path),
        # Ensure we don't try to run final review if it requires more setup
        "options": {"subtitle_burn": False}
    })
    
    # Check if it failed due to missing remotion installation even if npx exists
    if not render_result.success:
        pytest.fail(f"VideoCompose render failed: {render_result.error}")
        
    # 5. Verify output MP4 exists and has nonzero size
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    print(f"POC Render successful: {output_path}")
