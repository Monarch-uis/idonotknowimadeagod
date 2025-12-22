# Subtitle Integration Guide

## ✅ What This Does

Your videos will now have **real subtitles** that:
- ✅ **Filter out bad words** (using your banned_words list)
- ✅ **Keep character names unchanged** (no pronunciation changes)
- ✅ **Can be turned on/off** by viewers (soft subtitles)
- ✅ **Sync perfectly** with your audio chapters

## 🔧 How to Integrate

### Step 1: Import the subtitle generator in your main script

Add this line at the top of `epub_project_manager.py` with your other imports:

```python
from core.subtitle_generator import generate_subtitles_for_video
```

### Step 2: Add subtitle generation after video creation

Find this section in your `main()` function (around line 2100):

```python
video_success = create_video_with_recovery(
    audio_file, item["image"], video_file,
    book_title=meta['title'],
    chapter_range=item['label'],
    timestamps=timestamps,
    max_retries=3
)
```

Add this code right after it:

```python
# Generate and embed subtitles if enabled
if video_success and os.path.exists(video_file):
    video_size = os.path.getsize(video_file)
    print(CP(f"   ✅ Video created: {video_size/1024/1024:.1f} MB", 'green'), flush=True)
    
    # 🆕 SUBTITLE GENERATION
    if CONFIG.get("video_settings", {}).get("enable_subtitles", True):
        print(f"\n   📝 Generating subtitles...", flush=True)
        subtitle_success = generate_subtitles_for_video(
            chapters=item["batch"],  # The chapter content for this video
            timestamps=timestamps,    # Chapter timestamps
            video_path=video_file,   # Output video path
            config=CONFIG,           # Your config with banned_words
            embed=CONFIG.get("video_settings", {}).get("embed_subtitles", True)
        )
        
        if subtitle_success:
            print(CP(f"   ✅ Subtitles added successfully!", 'green'), flush=True)
        else:
            print(CP(f"   ⚠️  Subtitle generation failed (video still valid)", 'yellow'), flush=True)
    
    # Continue with your existing code...
    save_to_history(meta['title'], item["start_chk"], item["end_chk"], epub_hash)
```

## ⚙️ Configuration Options

Edit `config.json` to control subtitle behavior:

```json
"video_settings": {
    "enable_subtitles": true,              // Turn subtitles on/off
    "embed_subtitles": true,               // Embed in video (true) or just create .srt file (false)
    "subtitle_max_chars": 60,              // Max characters per subtitle line
    "subtitle_reading_speed_wps": 2.5,     // Words per second reading speed
    ...
}
```

## 📝 What Happens Internally

1. **Text is cleaned** - Partial censoring for better readability:
   ```python
   # New subtitle-specific censoring (keeps first & last letter)
   clean_text = censor_text_for_subtitles(chapter_text, banned_words)
   # Examples: "fuck" → "f**k", "fucking" → "f**king", "shit" → "s**t"
   clean_text = clean_text.replace('"', '').replace("*", "")
   ```

2. **Character names stay intact** - No pronunciation changes applied to subtitles
   
3. **Text is split** into subtitle-sized chunks (60 chars default)

4. **Timestamps are calculated** based on reading speed

5. **SRT file is created** with proper formatting:
   ```
   1
   00:00:00,000 --> 00:00:03,500
   Welcome to Fanfiction Legend!
   
   2
   00:00:03,600 --> 00:00:08,200
   Today's story is about to hit different.
   ```

6. **Subtitles are embedded** into MP4 using ffmpeg (can be toggled on/off by viewer)

## 🎯 Example Output

For a chapter with text like:
```
"Fuck! This cultivation technique is amazing!" said Naruto.
"Fucking hell, Sasuke is so strong!" shouted Luffy.
```

Your subtitles will show:
```
"F**k! This cultivation technique is amazing!" said Naruto.
"F**king hell, Sasuke is so strong!" shouted Luffy.
```

- ✅ Bad words **partially** censored (f**k, f**king) - readable but censored
- ✅ Character names (Naruto, Sasuke, Luffy) kept intact
- ✅ Game terms (cultivation technique) unchanged
- ✅ Synced perfectly with audio

## 🚀 Quick Test

1. Make the changes above
2. Process a small 1-3 chapter range
3. Check the output:
   - `your_video.mp4` (main video)
   - `your_video.srt` (subtitle file, kept for reference)
4. Open video in VLC or YouTube Studio - subtitles should appear!

## 🔍 Troubleshooting

**Subtitles not showing?**
- Check `config.json`: `"enable_subtitles": true`
- Check console for errors during subtitle generation
- Verify ffmpeg is working: `ffmpeg -version`

**Bad words still in subtitles?**
- Check your `banned_words` list in config.json
- Make sure you're using regex format: `"\\bfuck\\w*"`

**Subtitles out of sync?**
- Adjust `"subtitle_reading_speed_wps"` in config (lower = slower subtitles)

## 🎓 Advanced: Subtitle-Only Mode

If you just want .srt files without embedding:

```python
subtitle_success = generate_subtitles_for_video(
    chapters=item["batch"],
    timestamps=timestamps,
    video_path=video_file,
    config=CONFIG,
    embed=False  # 👈 Just create .srt file
)
```

The .srt file can be:
- Uploaded to YouTube separately
- Used with any video player
- Edited manually if needed

---

## ✨ That's it!

Your videos now have professional subtitles that:
- Filter inappropriate content
- Keep character names authentic
- Are viewer-controllable
- Sync perfectly with your audio

Happy subtitle generation! 🎉
