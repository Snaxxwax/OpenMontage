#!/usr/bin/env python3
import json
import pathlib

ROOT = pathlib.Path('/home/pop/repos/openmontage-asymmetric')
EPISODE_PATH = ROOT / 'projects/humane-ai-pin-autopsy/artifacts/episode.json'
RENDER_PROPS_PATH = ROOT / 'projects/humane-ai-pin-autopsy/artifacts/render_props.modern_archivist.json'

def main():
    episode = json.loads(EPISODE_PATH.read_text())
    render_props = json.loads(RENDER_PROPS_PATH.read_text())
    
    # Update episode-level fields
    render_props['duration_seconds'] = episode['duration_seconds']
    render_props['target_duration_seconds'] = episode.get('target_duration_seconds', episode['duration_seconds'])
    
    # Update sections with new timings
    for i, section in enumerate(episode['sections']):
        if i < len(render_props['sections']):
            render_props['sections'][i]['start'] = section['start']
            render_props['sections'][i]['end'] = section['end']
            render_props['sections'][i]['estimated_duration_seconds'] = round(section['end'] - section['start'], 2)
            # Also update the media_overlay timing if present
            if 'media_overlay' in render_props['sections'][i]:
                render_props['sections'][i]['media_overlay']['start'] = section['start']
                render_props['sections'][i]['media_overlay']['end'] = section['end']
    
    # Remove puppet section (since we removed puppet from pipeline)
    if 'puppet' in render_props:
        del render_props['puppet']
    
    # Update audio_src to point to the file in remotion-composer/public
    render_props['audio_src'] = 'humane-ai-pin/narration.wav'
    
    RENDER_PROPS_PATH.write_text(json.dumps(render_props, indent=2))
    print(f"Updated {RENDER_PROPS_PATH}")
    print(f"Duration: {render_props['duration_seconds']}s")
    print(f"Sections: {len(render_props['sections'])}")
    print(f"Puppet removed: {'puppet' not in render_props}")

if __name__ == '__main__':
    main()