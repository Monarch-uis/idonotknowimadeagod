# FFMPEG Installation Fix

## Problem
Your FFMPEG is missing the **libx264** codec, causing video encoding to fail with:
- `Unknown decoder 'libx264'`
- `[Errno 32] Broken pipe`

## Solution: Install Full FFMPEG with H.264 Support

### Option 1: Use Chocolatey (Recommended for Windows)

1. **Install Chocolatey** (if not already installed):
   - Open PowerShell as Administrator
   - Run:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Install FFMPEG**:
   ```powershell
   choco install ffmpeg
   ```

3. **Restart your terminal** and verify:
   ```bash
   ffmpeg -version
   ffmpeg -codecs | findstr 264
   ```

### Option 2: Manual Installation

1. **Download FFMPEG** from: https://www.gyan.dev/ffmpeg/builds/
   - Get the **"ffmpeg-release-full.7z"** (FULL build, not essentials!)

2. **Extract** to `C:\ffmpeg`

3. **Add to PATH**:
   - Press `Win + X` → System → Advanced system settings
   - Environment Variables → System Variables → Path → Edit
   - Add: `C:\ffmpeg\bin`

4. **Restart terminal** and verify:
   ```bash
   ffmpeg -version
   ffmpeg -codecs | findstr 264
   ```

### Option 3: Use imageio-ffmpeg (Python package)

This is what MoviePy tries to use automatically:

```bash
pip install --upgrade imageio-ffmpeg
```

Then test:
```python
python -c "from imageio_ffmpeg import get_ffmpeg_exe; print(get_ffmpeg_exe())"
```

## Verify Installation

Run this to check if H.264 is available:
```bash
ffmpeg -codecs | findstr 264
```

You should see:
```
DEV.LS h264    H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (decoders: h264 ... ) (encoders: libx264 libx264rgb )
```

## After Installing

1. **Close ALL terminal windows**
2. **Restart your script**
3. The video encoding should work now!

## Still Having Issues?

If the problem persists, try using a different codec in the code:
- Change `codec="libx264"` to `codec="mpeg4"` (lower quality but more compatible)
