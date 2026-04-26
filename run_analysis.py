
import json
import sys
from tools.analysis.video_analyzer import VideoAnalyzer

analyzer = VideoAnalyzer()
result = analyzer.execute({
    "source": "reference_short_h264.mp4",
    "analysis_depth": "standard",
    "max_keyframes": 20
})

if result.success:
    print(json.dumps(result.data, indent=2))
else:
    print(f"Error: {result.error}")
    sys.exit(1)
