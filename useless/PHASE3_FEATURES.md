# Phase 3 - Output Quality and Packaging Features

Phase 3 adds professional output quality enhancements and packaging tools.

## New Features

### 1. Thumbnail Text Overlay ✅
- **What it does**: Adds book title and chapter range text overlay on video thumbnails
- **Config**: `config.json` → `video_settings.enable_text_overlay` (default: true)
- **Settings**:
  - `text_overlay_font_size`: Font size for title text (default: 36)
  - `text_overlay_bottom_margin`: Distance from bottom (default: 40)
- **How it works**: When generating covers from EPUB or custom images, text is automatically added at the bottom with a semi-transparent background for readability

### 2. Loudness Normalization ✅
- **What it does**: Normalizes audio volume for consistent playback across videos
- **Config**: `config.json` → `audio_settings.enable_loudness_normalization` (default: false)
- **How it works**: Uses ffmpeg's `loudnorm` filter to normalize audio to industry standard levels (I=-16 LUFS)
- **Note**: Adds processing time but ensures professional audio quality

### 3. Chapter Markers in MP4 ✅
- **What it does**: Embeds chapter markers in the MP4 video file for easy navigation
- **Config**: `config.json` → `video_settings.enable_chapter_markers` (default: true)
- **How it works**: Creates chapter metadata that video players can use to skip between chapters
- **Note**: Not all players support chapter markers, but they're preserved in the file metadata

### 4. Executable Build Tools ✅
- **What it does**: Tools to package the script into a single `.exe` file
- **Files**:
  - `epub_project_manager.spec` - PyInstaller configuration
  - `build_exe.bat` - Windows batch script to build the executable
- **How to use**:
  1. Run `build_exe.bat` (it will install PyInstaller if needed)
  2. The executable will be in the `dist` folder
  3. Copy `config.json` and `background.mp3` to the same folder as the `.exe`

## Configuration Example

```json
{
    "audio_settings": {
        "enable_loudness_normalization": false
    },
    "video_settings": {
        "enable_text_overlay": true,
        "enable_chapter_markers": true,
        "text_overlay_font_size": 36,
        "text_overlay_bottom_margin": 40
    }
}
```

## Notes

- Text overlay uses system fonts (Arial on Windows) and falls back to default if not available
- Loudness normalization requires ffmpeg (already included via imageio-ffmpeg)
- Chapter markers are embedded using ffmpeg metadata format
- All features are optional and can be toggled in config.json

