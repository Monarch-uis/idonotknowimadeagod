import os
import shutil
import sys
from PIL import Image
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epub_project_manager import create_video
from core.utils import CP

def test_thumbnail_recovery():
    print(CP("\n🧪 TEST: Thumbnail Recovery from Archive", 'cyan'))
    print("=" * 60)
    
    # 1. Setup mock project structure
    test_root = "test_recovery_project"
    archive_dir = os.path.join(test_root, "cover_images")
    temp_dir = os.path.join(test_root, "temp_render_files")
    video_dir = os.path.join(test_root, "youtubevideo")
    
    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    
    # 2. Create an archived thumbnail
    # The name must be sanitized-safe version of the range
    chapter_range = "Ch 1-10"
    archive_name = "Ch 1-10.jpg"
    archive_path = os.path.join(archive_dir, archive_name)
    
    dummy_img = Image.new('RGB', (1280, 720), (0, 255, 0)) # Green
    dummy_img.save(archive_path)
    print(f"✅ Created archived thumbnail: {archive_path}")
    
    # 3. Dummy audio
    audio_path = os.path.join(test_root, "dummy_audio.mp3")
    with open(audio_path, "w") as f: f.write("dummy audio content")
    
    # 4. Target video path
    video_path = os.path.join(video_dir, "test_video.mp4")
    
    # 5. Missing thumbnail path (where it SHOULD have been)
    missing_thumb_path = os.path.join(temp_dir, "temp_thumb_0.jpg")
    
    print(f"🎬 Running create_video with MISSING path: {missing_thumb_path}")
    print(f"   But with chapter_range: {chapter_range}")
    
    # We mock everything AFTER the image recovery block to see if it continues with the correct path
    # OR we just check if it crashes with FileNotFoundError on the ARCHIVE path if we don't mock it?
    # Actually, if it finds the archive path, it will try to open it with AudioFileClip etc.
    
    detected_path = None
    
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            # Mock AudioFileClip to avoid FFmpeg dependency in this test
            with patch('epub_project_manager.AudioFileClip'):
                create_video(
                    audio_path=audio_path,
                    image_path=missing_thumb_path,
                    output_path=video_path,
                    chapter_range=chapter_range
                )
        except Exception as e:
            # We expect a crash later because of dummy audio, but we check if it got past recovery
            pass

    output = f.getvalue()
    print("\n📝 Output Capture:")
    print("-" * 30)
    print(output)
    print("-" * 30)
    
    if "Recovered from archive: Ch 1-10.jpg" in output:
        print(CP("\n✅ SUCCESS: Recovery logic found the archived thumbnail!", 'green'))
    else:
        print(CP("\n❌ FAILURE: Recovery logic did not find the archived thumbnail.", 'red'))

    # Manual Clean up
    print("\n🧹 Cleanup...")
    try:
        shutil.rmtree(test_root)
        print("✅ Test directory cleaned")
    except:
        pass

if __name__ == "__main__":
    try:
        test_thumbnail_recovery()
    except KeyboardInterrupt:
        pass
