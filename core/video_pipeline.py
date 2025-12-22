"""Advanced video rendering pipeline.

This module provides utilities to generate word-level caption timelines using
``faster-whisper`` and to render final videos with FFmpeg using complex filter
graphs. The resulting timeline JSON is designed to be the single source of truth
for both browser previews and backend renders.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

import tempfile
import subprocess
import gc
from contextlib import contextmanager

# Import utility function for time formatting
from core.utils import seconds_to_time_str


CAPTION_PRESETS = {
    "Modern": {
        "font": "Montserrat-Bold",
        "font_size": 70,
        "bold": True,
        "color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "shadow": 2,
        "alignment": 2,
        "margin_v_percent": 7.0,
        "margin_h_percent": 2.5,
    },
    "Classic": {
        "font": "Arial",
        "font_size": 60,
        "bold": False,
        "color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "shadow": 1,
        "alignment": 2,
        "margin_v_percent": 5.0,
        "margin_h_percent": 2.1,
    },
    "Minimal": {
        "font": "Arial",
        "font_size": 55,
        "bold": False,
        "color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "shadow": 0,
        "alignment": 2,
        "margin_v_percent": 4.0,
        "margin_h_percent": 2.0,
    },
}

def _import_fast_whisper():
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "faster-whisper is required for advanced caption generation. "
            "Install it with `pip install faster-whisper`"
        ) from exc
    return WhisperModel


def _import_ffmpeg():
    try:
        import ffmpeg  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "ffmpeg-python is required for advanced video rendering. "
            "Install it with `pip install ffmpeg-python`"
        ) from exc
    return ffmpeg


def _seconds_to_ass_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    return f"{hrs}:{mins:02}:{secs:02}.{cs:02}"


def _ass_hex_color(hex_color: str, alpha: int = 0) -> str:
    """Convert #RRGGBB to &HAABBGGRR (ASS color format)."""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) != 6:
        return "&H00FFFFFF"
    r = hex_color[0:2]
    g = hex_color[2:4]
    b = hex_color[4:6]
    return f"&H{alpha:02X}{b}{g}{r}"


def _default_caption_style(config: Dict[str, Any]) -> Dict[str, Any]:
    style = config.get("video_settings", {}).get("caption_style", {})
    
    # If a preset is specified and not fully overridden
    preset_name = style.get("preset")
    if preset_name in CAPTION_PRESETS:
        # Start with preset
        merged = CAPTION_PRESETS[preset_name].copy()
        # Overlay user config on top
        merged.update(style)
        return merged
        
    return style

def _calculate_responsive_margins(width: int, height: int, style: Dict[str, Any]) -> Dict[str, int]:
    """Calculate margins based on video resolution and style preferences."""
    margin_v_percent = float(style.get("margin_v_percent", 5.0))
    margin_h_percent = float(style.get("margin_h_percent", 2.0))
    
    margin_v = int(height * (margin_v_percent / 100))
    margin_h = int(width * (margin_h_percent / 100))
    
    return {
        "margin_v": margin_v,
        "margin_h": margin_h
    }

def _calculate_responsive_font_size(height: int, style: Dict[str, Any]) -> int:
    """Scale font size based on video height."""
    if not style.get("responsive_scaling", True):
        return int(style.get("font_size", 60))
    
    base_font_size = int(style.get("font_size", 60))
    base_height = 1080
    
    # Scale proportionally
    scaled_size = int(base_font_size * (height / base_height))
    
    # Clamp to min/max
    min_size = int(style.get("min_font_size", 40))
    max_size = int(style.get("max_font_size", 90))
    
    return max(min_size, min(max_size, scaled_size))

def _calculate_responsive_outline(height: int, style: Dict[str, Any]) -> int:
    """Scale outline thickness based on video height."""
    # Use specified outline thickness or fallback to stroke_width (legacy)
    base_outline = int(style.get("outline_thickness", style.get("stroke_width", 2)))
    if not style.get("responsive_scaling", True):
        return base_outline

    base_height = 1080
    # Scale outline proportionally
    scaled_outline = int(base_outline * (height / base_height))
    # Minimum 1px, maximum 10px
    return max(1, min(10, scaled_outline))

def _calculate_responsive_shadow(height: int, style: Dict[str, Any]) -> int:
    base_shadow = int(style.get("shadow_depth", style.get("shadow", 0)))
    if not style.get("responsive_scaling", True):
        return base_shadow
        
    base_height = 1080
    scaled_shadow = int(base_shadow * (height / base_height))
    return max(0, min(10, scaled_shadow))



def _build_ass_header(style: Dict[str, Any], width: int = 1920, height: int = 1080) -> str:
    primary = _ass_hex_color(style.get("color", "#FFFFFF"))
    outline = _ass_hex_color(style.get("stroke_color", "#000000"))
    font = style.get("font", "Arial")
    alignment = int(style.get("alignment", 2))
    
    # Modern styling calculations
    font_size = _calculate_responsive_font_size(height, style)
    margins = _calculate_responsive_margins(width, height, style)
    outline_width = _calculate_responsive_outline(height, style)
    shadow = _calculate_responsive_shadow(height, style)
    
    # Bold support (-1 is bold in ASS, 0 is normal)
    bold = -1 if style.get("bold", False) else 0

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        (
            f"Style: Default,{font},{font_size},{primary},&H000000FF,{outline},&H00000000,"  # Secondary colour fixed
            f"{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},"
            f"{margins['margin_h']},{margins['margin_h']},{margins['margin_v']},1"
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    return "\n".join(header) + "\n"


def _write_ass_dialogue(captions: Iterable[Dict[str, Any]], style: Dict[str, Any]) -> str:
    lines = []
    for entry in captions:
        payload = entry.get("payload", {})
        text = payload.get("text", "")
        if not text:
            continue
        start = _seconds_to_ass_time(entry.get("start", 0.0))
        end = _seconds_to_ass_time(entry.get("end", entry.get("start", 0.0)))
        safe_text = (
            str(text)
            .replace("\r\n", "\n")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("\n", r"\\N")
        )
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{safe_text}")
    return "\n".join(lines) + ("\n" if lines else "")


@contextmanager
def temp_ass_file(captions: Iterable[Dict[str, Any]], config: Dict[str, Any], width: int = 1920, height: int = 1080):
    """
    Context manager for temporary ASS subtitle file
    Guarantees cleanup even if crash occurs
    """
    style = _default_caption_style(config)
    header = _build_ass_header(style, width, height)
    body = _write_ass_dialogue(captions, style)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".ass", text=True)
    path_obj = Path(tmp_path)
    
    try:
        os.close(tmp_fd)
        with open(path_obj, "w", encoding="utf-8") as handle:
            handle.write(header)
            handle.write(body)
        yield path_obj
    finally:
        try:
            if path_obj.exists():
                path_obj.unlink()
        except Exception as e:
            print(f"Warning: Could not delete temp file {path_obj}: {e}")

def _detect_gpu_device(device_pref="auto"):
    """Properly detect GPU availability"""
    if device_pref != "auto":
        return device_pref
    
    # Try CUDA
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    
    # Try MPS (Mac)
    try:
        import torch
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
    except (ImportError, AttributeError):
        pass
    
    return "cpu"


def _probe_duration(media_path: str) -> Optional[float]:
    try:
        ffmpeg = _import_ffmpeg()
        info = ffmpeg.probe(media_path)
        return float(info.get("format", {}).get("duration"))
    except Exception:
        return None


def _group_words_into_fragments(
    words: List[Dict[str, Any]],
    max_duration: float,
    max_words: int,
) -> List[Dict[str, Any]]:
    """Group words into caption fragments using ACTUAL audio timing.
    
    This function preserves the exact timing from TTS/Whisper - no estimation!
    """
    fragments: List[Dict[str, Any]] = []
    current_batch: List[Dict[str, Any]] = []
    batch_start: Optional[float] = None

    for word in words:
        if word.get("text", "").strip() == "":
            continue
        # Force float to prevent any type issues
        start = float(word.get("start", 0.0))
        end = float(word.get("end", start))

        if batch_start is None:
            batch_start = start

        projected_duration = end - batch_start
        projected_count = len(current_batch) + 1
        
        # Also detect natural pauses (>0.5s gap between words)
        has_pause = current_batch and (start - current_batch[-1]["end"] > 0.5)
        
        if (
            current_batch
            and (projected_duration > max_duration or projected_count > max_words or has_pause)
        ):
            fragments.append(
                {
                    "type": "caption_fragment",
                    "start": batch_start,
                    "end": current_batch[-1]["end"],
                    "payload": {
                        "text": " ".join(w["text"] for w in current_batch),
                        "words": current_batch,
                    },
                }
            )
            current_batch = []
            batch_start = start

        current_batch.append({
            "text": word.get("text", ""),
            "start": start,
            "end": end,
        })

    if current_batch and batch_start is not None:
        fragments.append(
            {
                "type": "caption_fragment",
                "start": batch_start,
                "end": current_batch[-1]["end"],
                "payload": {
                    "text": " ".join(w["text"] for w in current_batch),
                    "words": current_batch,
                },
            }
        )

    return fragments


def generate_timeline_from_audio(
    audio_path: str,
    project_id: str,
    config: Dict[str, Any],
    model_size: str = "small",
    cpu_threads: int = 4,
    download_root: Optional[str] = None
) -> Dict[str, Any]:
    """Transcribe audio and emit a project timeline JSON structure."""
    WhisperModel = _import_fast_whisper()

    video_settings = config.get("video_settings", {})
    # Precedence: Argument override > Config > Default
    # model_size argument handles the override logic if passed (default "small" in arg matches config default roughly)
    
    compute_type = video_settings.get("caption_compute_type", "float16")
    language = video_settings.get("caption_language")
    
    # faster-whisper requires None for auto-detection, not "auto" string
    if language in (None, "", "auto", "Auto"):
        language = None
    max_fragment_duration = float(
        video_settings.get("caption_fragment_max_duration", 3.0)
    )
    max_fragment_words = int(video_settings.get("caption_fragment_max_words", 12))

    # Get device preference from config (cpu, cuda, auto, etc.)
    device_pref = video_settings.get("caption_device", "auto")
    device = _detect_gpu_device(device_pref)
    
    # Auto-adjust compute_type if it's float16 but on CPU (often slow/unsupported)
    if device == "cpu" and compute_type == "float16":
        compute_type = "int8"
        print(f"   ℹ️  Auto-switching compute_type to {compute_type} for CPU")

    import threading

    # Load Whisper model with a spinner for visual feedback
    model = None
    load_error = []

    def _load_model_thread(m_size, dev, c_type, threads, root):
        nonlocal model
        try:
            # First, check if valid model path exists in root to avoid network calls
            local_files_only = False
            if root and os.path.exists(root):
                # Simple heuristic: if likely populated, try local first
                # (Actual model validation is complex, but this prevents hang on update checks)
                if any(p.name.startswith("model") for p in Path(root).rglob("*")):
                     local_files_only = True
            
            try:
                if local_files_only:
                     print(f"   📂 Loading from local cache: {root}")
                     model = WhisperModel(m_size, device=dev, compute_type=c_type, cpu_threads=threads, download_root=root, local_files_only=True)
                else:
                     model = WhisperModel(m_size, device=dev, compute_type=c_type, cpu_threads=threads, download_root=root)
            except Exception as local_err:
                if local_files_only:
                     print(f"   ⚠️  Local load failed, retrying with network: {local_err}")
                     model = WhisperModel(m_size, device=dev, compute_type=c_type, cpu_threads=threads, download_root=root, local_files_only=False)
                else:
                    raise local_err

        except Exception as e:
            load_error.append(e)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        expand=True
    ) as progress:
        loading_task = progress.add_task(description=f"[cyan]Loading Whisper Model ({model_size}, {compute_type})...", total=None)
        
        # Start loading in background thread
        loader = threading.Thread(target=_load_model_thread, args=(model_size, device, compute_type, cpu_threads, download_root))
        loader.daemon = True
        loader.start()
        
        # Keep UI alive while loading
        while loader.is_alive():
            loader.join(0.1)
            
        if load_error:
            e = load_error[0]
            if "float16" in str(e).lower():
                fallback = "int8" if device == "cpu" else "float32"
                progress.console.print(f"   ⚠️  float16 not supported on this device. Falling back to {fallback}...")
                
                # Reset error and try again
                load_error.clear()
                loader = threading.Thread(target=_load_model_thread, args=(model_size, device, fallback, cpu_threads, download_root))
                loader.daemon = True
                loader.start()
                while loader.is_alive():
                    loader.join(0.1)
                
                if load_error:
                    raise load_error[0]
            else:
                progress.stop() # Ensure UI stops before raising
                raise e

    segments, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=True,
        word_timestamps=True,
    )

    words: List[Dict[str, Any]] = []
    
    # Use Progress bar for transcription
    total_duration = info.duration
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        expand=True
    ) as progress:
        transcribe_task = progress.add_task("[yellow]Transcribing Audio (Whisper)...", total=total_duration)
        
        for segment in segments:
            # Update progress based on segment end time
            progress.update(transcribe_task, completed=segment.end)
            
            for word in getattr(segment, "words", []):
                if word.word is None:
                    continue
                words.append(
                    {
                        "text": word.word.strip(),
                        "start": float(getattr(word, "start", 0.0) or 0.0),
                        "end": float(getattr(word, "end", 0.0) or 0.0),
                    }
                )
        
        # Ensure bar is full at the end
        progress.update(transcribe_task, completed=total_duration)

    fragments = _group_words_into_fragments(words, max_fragment_duration, max_fragment_words)
    
    # Debug output for caption generation
    print(f"   📝 Generated {len(fragments)} caption fragments from {len(words)} words")

    duration = None
    if info and getattr(info, "duration", None):
        duration = float(info.duration)
    if duration is None:
        duration = _probe_duration(audio_path)
    if duration is None:
        duration = fragments[-1]["end"] if fragments else 0.0

    timeline: List[Dict[str, Any]] = fragments

    default_effects = video_settings.get("default_effects", [])
    for effect_cfg in default_effects:
        effect_id = effect_cfg.get("effect_id", "gaussian_blur")
        start = float(effect_cfg.get("start", 0.0))
        duration_cfg = effect_cfg.get("duration")
        if duration_cfg is not None:
            end = start + float(duration_cfg)
        else:
            end = float(effect_cfg.get("end", duration))
        end = min(duration, max(start, end)) if duration else max(start, end)
        if end <= start:
            continue
        timeline.append(
            {
                "type": "visual_effect",
                "start": start,
                "end": end,
                "effect_id": effect_id,
                "params": effect_cfg.get("params", {}),
            }
        )

    # Debug: Show timeline composition
    caption_count = sum(1 for item in timeline if item.get("type") == "caption_fragment")
    effect_count = sum(1 for item in timeline if item.get("type") == "visual_effect")
    print(f"   ✅ Timeline created: {caption_count} captions, {effect_count} effects")

    return {
        "project_id": project_id,
        "media": {
            "path": str(Path(audio_path).resolve()),
            "duration": duration,
        },
        "timeline": timeline,
        "metadata": {
            "model": model_size,
            "compute_type": compute_type,
            "language": language or "auto",
        },
    }

def generate_timeline_from_words(
    audio_path: str,
    project_id: str,
    words: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate timeline JSON directly from provided word timings (bypass Whisper)."""
    
    video_settings = config.get("video_settings", {})
    max_fragment_duration = float(
        video_settings.get("caption_fragment_max_duration", 3.0)
    )
    max_fragment_words = int(video_settings.get("caption_fragment_max_words", 12))

    # Group words into fragments
    fragments = _group_words_into_fragments(words, max_fragment_duration, max_fragment_words)
    print(f"   📝 Generated {len(fragments)} caption fragments from {len(words)} input words")

    duration = _probe_duration(audio_path)
    if duration is None:
        duration = fragments[-1]["end"] if fragments else 0.0

    timeline: List[Dict[str, Any]] = fragments

    default_effects = video_settings.get("default_effects", [])
    for effect_cfg in default_effects:
        effect_id = effect_cfg.get("effect_id", "gaussian_blur")
        start = float(effect_cfg.get("start", 0.0))
        duration_cfg = effect_cfg.get("duration")
        if duration_cfg is not None:
            end = start + float(duration_cfg)
        else:
            end = float(effect_cfg.get("end", duration))
        end = min(duration, max(start, end)) if duration else max(start, end)
        if end <= start:
            continue
        timeline.append(
            {
                "type": "visual_effect",
                "start": start,
                "end": end,
                "effect_id": effect_id,
                "params": effect_cfg.get("params", {}),
            }
        )

    return {
        "project_id": project_id,
        "media": {
            "path": str(Path(audio_path).resolve()),
            "duration": duration,
        },
        "timeline": timeline,
        "metadata": {
            "source": "tts_timing",
        },
    }


def _build_video_stream(stream, fps, ass_path, effects):
    """Helper to build the video filter graph with effects and subtitles"""
    for effect in effects:
        start = float(effect.get("start", 0.0))
        end = float(effect.get("end", start))
        params = effect.get("params", {})
        enable_expr = f"between(t,{start},{end})"
        effect_id = effect.get("effect_id", "gaussian_blur")

        if effect_id == "gaussian_blur":
            sigma = float(params.get("sigma", 5))
            stream = stream.filter(
                "boxblur",
                luma_radius=max(1, int(sigma)),
                luma_power=1,
                enable=enable_expr,
            )
        elif effect_id == "grayscale":
            stream = stream.filter("hue", s=0, enable=enable_expr)
        elif effect_id == "brightness":
            value = float(params.get("value", 0.1))
            stream = stream.filter("eq", brightness=value, enable=enable_expr)
        else:
            print(f"   ⚠️  Unknown effect '{effect_id}', skipping")

    stream = stream.filter("fps", fps)
    stream = stream.filter("format", "yuv420p")

    if ass_path is not None:
        # Windows path escaping for FFmpeg filter syntax
        # FFmpeg requires: backslashes escaped as \\ and colons as \:
        escaped_path = str(ass_path).replace("\\", "/")  # Use forward slashes (works on Windows)
        escaped_path = escaped_path.replace(":", r"\:")  # Escape colons for filter syntax
        stream = stream.filter("subtitles", escaped_path)
        
    return stream

def _escape_ffmpeg_path(path: str | Path) -> str:
    """
    Harden Windows path escaping for FFmpeg filters (subtitles, movie, etc).
    Uses forward slashes and escapes colons/quotes.
    """
    p = str(path).replace("\\", "/")
    # FFmpeg filter syntax: escape colon after drive letter (e.g., C\:), single quotes, and commas
    p = p.replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")
    return p

def render_video_with_timeline(
    image_path: str,
    audio_path: str,
    timeline_data: Dict[str, Any],
    output_path: str,
    config: Dict[str, Any],
    quality_settings: Optional[Dict[str, Any]] = None,
    export_timeline_json: bool = True,
) -> None:
    """Render a video using FFmpeg subprocess based on the shared timeline JSON.
    
    Uses direct subprocess call instead of ffmpeg-python for better Windows
    compatibility with subtitle path escaping and memory safety.
    """
    import subprocess
    import gc
    
    image_path = str(image_path)
    audio_path = str(audio_path)
    output_path = str(output_path)
    quality_settings = quality_settings or {}
    captions = [item for item in timeline_data.get("timeline", []) if item.get("type") == "caption_fragment"]
    
    project_duration = float(
        timeline_data.get("media", {}).get("duration") or _probe_duration(audio_path) or 0.0
    )

    print(f"   🎬 Rendering video (Duration: {seconds_to_time_str(project_duration)})", flush=True)
    
    fps = int(config.get("video_settings", {}).get("preview_fps", 30))
    crf = str(quality_settings.get("crf", 23))
    # Preference: use rendering_preset if defined, otherwise fallback to quality_settings
    preset = config.get("video_settings", {}).get("rendering_preset", quality_settings.get("preset", "medium"))
    audio_bitrate = config.get("audio_settings", {}).get("export_bitrate", "192k")
    
    enable_dynamic = config.get("video_settings", {}).get("enable_dynamic_background", True)

    # Get FFmpeg path
    ffmpeg_exe = "ffmpeg"
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg_exe = get_ffmpeg_exe()
    except ImportError:
        pass

    def run_ffmpeg_render(vf_filter: str, filter_complex: Optional[str] = None):
        """Run FFmpeg with explicit command line and log to file to prevent memory spikes."""
        log_file = Path(output_path).with_suffix(".ffmpeg.log")
        
        # Windows startupinfo to hide console window
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        cmd = [
            ffmpeg_exe,
            "-y",
            "-loop", "1",
            "-framerate", str(fps),
            "-i", image_path,
            "-i", audio_path,
        ]
        
        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a"])
        else:
            cmd.extend(["-vf", vf_filter])
            
        cmd.extend([
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", crf,
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-shortest",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
        ])
        
        if project_duration:
            cmd.extend(["-t", str(project_duration)])
        
        if not filter_complex:
             cmd.append(output_path)
        else:
             # Already mapped
             cmd.append(output_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            expand=True
        ) as progress:
            description = f"[cyan]FFmpeg Rendering ({preset}, CRF {crf})..."
            render_task = progress.add_task(description=description, total=project_duration)
            
            with open(log_file, "w") as log_handle:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_handle,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Regex to find time=HH:MM:SS.ms
                time_regex = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")
                
                for line in process.stderr:
                    log_handle.write(line)
                    match = time_regex.search(line)
                    if match:
                        hours, minutes, seconds, ms = map(int, match.groups())
                        current_time = hours * 3600 + minutes * 60 + seconds + ms / 100
                        progress.update(render_task, completed=current_time)
                
                process.wait()
                result_returncode = process.returncode
        
        if result_returncode != 0:
            print(f"   ❌ FFmpeg failed (code {result_returncode}). Check logs for details.")
            raise RuntimeError(f"FFmpeg failed with code {result_returncode}")
        
        print(f"   ✅ FFmpeg render complete")
        try:
            if log_file.exists():
                log_file.unlink()
        except:
            pass

    # Export timeline BEFORE rendering
    if export_timeline_json:
        timeline_path = Path(output_path).with_suffix(".timeline.json")
        try:
            with open(timeline_path, "w", encoding="utf-8") as handle:
                json.dump(timeline_data, handle, indent=2)
            print(f"   ✅ Timeline exported: {timeline_path.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to export timeline: {e}")

    try:
        # Prepare filter setup
        current_preset = config.get("video_settings", {}).get("current_quality_preset", "Balanced")
        presets = config.get("video_settings", {}).get("quality_presets", {})
        
        target_height = 720
        target_width = 1280
        if current_preset in presets:
            target_height = int(presets[current_preset].get("height", 720))
            target_width = int(target_width * 16 / 9) if target_height == 720 else int(target_height * 16 / 9)
            # Standard 16:9
            if target_height == 480: target_width = 854
            elif target_height == 720: target_width = 1280
            elif target_height == 1080: target_width = 1920

        print(f"   📐 Resolution: {target_width}x{target_height} | Dynamic: {enable_dynamic}")

        with temp_ass_file(captions, config, width=target_width, height=target_height) as ass_path:
            ass_path_escaped = _escape_ffmpeg_path(ass_path)
            
            if enable_dynamic:
                style = config.get("video_settings", {}).get("background_animation_style", "pulse")
                
                # Filter building components
                # [0:v] is the input cover image
                
                if style == "pulse":
                    # Breathing pulse effect
                    # Background: blurred, oversized, subtle pulse
                    bg_logic = (
                        f"scale={target_width*1.2}:-1,boxblur=20:5, "
                        f"scale='iw*(1+0.03*sin(t/2))':-1, "
                        f"crop={target_width}:{target_height}[bg]"
                    )
                    # Foreground: sharp, floating pulse
                    fg_logic = (
                        f"[0:v]scale=-1:{int(target_height*0.85)}, "
                        f"scale='iw*(1+0.02*sin(t/2.5))':-1[fg]"
                    )
                elif style == "ken_burns":
                    # Ken Burns: Slow zoom using zoompan filter (proper method)
                    # Research: crop with dynamic dimensions causes "Failed to configure input pad" errors
                    # zoompan is specifically designed for Ken Burns effects
                    # zoom: 1.0 (no zoom) to 1.15 (15% zoom in) over duration
                    # Formula: z='min(zoom+0.0002,1.15)' for gradual zoom
                    fps = 12  # Match video FPS
                    bg_logic = (
                        f"scale={target_width*1.5}:-1,boxblur=20:5, "
                        f"crop={target_width}:{target_height}:'(iw-ow)/2':'(ih-oh)/2'[bg]"
                    )
                    # Foreground: Use zoompan for smooth Ken Burns zoom
                    # d=1 means evaluate expression for each frame
                    # s=WxH sets output size
                    # z='min(zoom+0.0002,1.15)' creates gradual zoom from 1.0 to 1.15
                    fg_scale = int(target_height * 0.85)
                    fg_logic = (
                        f"[0:v]zoompan=z='min(zoom+0.0002,1.15)':d=1:s={target_width}x{target_height}:fps={fps}, "
                        f"scale=-1:{fg_scale}[fg]"
                    )
                else:
                    # Default static layout
                    bg_logic = f"scale={target_width}:{target_height},boxblur=20:5[bg]"
                    fg_logic = f"[0:v]scale=-1:{int(target_height*0.85)}[fg]"

                filter_complex = (
                    f"[0:v]{bg_logic}; "
                    f"{fg_logic}; "
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles='{ass_path_escaped}'[v]"
                )
                run_ffmpeg_render("", filter_complex=filter_complex)
            else:
                vf_filter = f"fps={fps},scale={target_width}:{target_height},format=yuv420p,subtitles='{ass_path_escaped}'"
                run_ffmpeg_render(vf_filter)
            
    finally:
        # Explicit resource release
        gc.collect()

def check_dependencies() -> bool:
    """Check if critical dependencies (ffmpeg, faster-whisper) are available."""
    print("   🔍 Checking video dependencies...")
    missing = []
    
    # Windows startupinfo to hide console window
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # Check FFmpeg
    try:
        _import_ffmpeg()
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, startupinfo=startupinfo)
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                from imageio_ffmpeg import get_ffmpeg_exe
                exe = get_ffmpeg_exe()
                subprocess.run([exe, '-version'], capture_output=True, check=True, startupinfo=startupinfo)
            except:
                missing.append("ffmpeg (executable not found)")
    except RuntimeError:
        missing.append("ffmpeg-python (pip package)")
    except Exception as e:
        missing.append(f"ffmpeg check failed: {e}")

    # Check Faster-Whisper
    try:
        _import_fast_whisper()
    except RuntimeError:
        missing.append("faster-whisper (pip package)")
    except Exception as e:
        missing.append(f"faster-whisper check failed: {e}")

    if missing:
        print(f"   ❌ Missing dependencies: {', '.join(missing)}")
        return False
    
    print("   ✅ Video dependencies OK")
    return True


__all__ = [
    "generate_timeline_from_audio",
    "render_video_with_timeline",
    "check_dependencies",
]
