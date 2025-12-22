#!/usr/bin/env python3
"""Quick test script to regenerate video with Ken Burns fix"""

import os
import json
from pathlib import Path

# Paths
project_dir = Path("Novels/Active Novels/He is fighting against the Avengers in Marvel")
history_file = project_dir / ".history.json"
video_file = project_dir / "youtubevideo" / "He is fighting against the Avengers in Marvel (Ch 1-3).mp4"

# Clear history
if history_file.exists():
    history_file.unlink()
    print(f"✅ Deleted {history_file}")

# Delete old video
if video_file.exists():
    video_file.unlink()
    print(f"✅ Deleted {video_file}")

print("\n✅ Ready for regeneration!")
print("Run: python epub_project_manager.py --engine piper --voice en_US-amy-medium --preview --range 1-3")
