"""
TTS module
Handles TTS engine selection, voice selection, and audio generation
"""
import os
import sys
import asyncio
import subprocess
import time
import logging
from typing import Optional

from core.config import CONFIG
from core.utils import CP, logger

# Check TTS library availability
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    print("⚠️  'edge-tts' missing. Run: pip install edge-tts")
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    print("⚠️  'pyttsx3' missing. Run: pip install pyttsx3")
    PYTTSX3_AVAILABLE = False

# Check Piper availability
try:
    piper_check = subprocess.run(['piper', '--version'], 
                                capture_output=True, 
                                text=True, 
                                timeout=5)
    PIPER_AVAILABLE = piper_check.returncode == 0
    PIPER_EXE_PATH = 'piper'  # Use PATH version
    if PIPER_AVAILABLE:
        print("✅ Piper TTS detected (PATH)")
except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
    # Fallback: check for local piper.exe
    local_piper = os.path.join(os.getcwd(), 'piper', 'piper.exe')
    if os.path.exists(local_piper):
        PIPER_AVAILABLE = True
        PIPER_EXE_PATH = local_piper
        print(f"✅ Piper TTS detected (local: {local_piper})")
    else:
        PIPER_AVAILABLE = False
        PIPER_EXE_PATH = None
        print("⚠️  'piper' not found. Install: https://github.com/rhasspy/piper")

if not EDGE_TTS_AVAILABLE and not PYTTSX3_AVAILABLE and not PIPER_AVAILABLE:
    print(CP("❌ No TTS libraries available. Install at least one.", 'red'))
    sys.exit(1)

def select_tts_engine_and_mode():
    """Select TTS engine and processing mode"""
    available = []
    if EDGE_TTS_AVAILABLE:
        available.append("1. Edge-TTS (online, high quality)")
    if PYTTSX3_AVAILABLE:
        available.append("2. pyttsx3 (offline, system voices)")
    if PIPER_AVAILABLE:
        available.append("3. Piper (offline, neural, FAST)")
    
    print("\n🎤 TTS Engine Selection:")
    for eng in available:
        print(f"   {eng}")
    
    while True:
        try:
            choice = input("\n👉 Select (1/2/3): ").strip()
            
            if choice == "1" and EDGE_TTS_AVAILABLE:
                print("\n💡 Processing Mode:")
                print("   Fast = 10 clips parallel → 5-10× faster")
                print("   Safe = 1 clip at a time → slower but ultra-safe")
                fast = input("   Use Fast mode? (y/n, default y): ").strip().lower()
                use_concurrent = fast != 'n'
                return "edge", use_concurrent
            
            elif choice == "2" and PYTTSX3_AVAILABLE:
                return "pyttsx3", False
            
            elif choice == "3" and PIPER_AVAILABLE:
                print("\n💡 Piper Features:")
                print("   • Offline (no internet)")
                print("   • Fast generation")
                print("   • Natural neural voices")
                print("   • Low resource usage")
                return "piper", False
                
        except (KeyboardInterrupt, EOFError):
            sys.exit(1)

def select_voice(engine):
    """Select voice for TTS engine"""
    if engine == "edge":
        print("\n🔊 Edge-TTS Voices:")
        voices = [
            "en-US-GuyNeural", "en-US-JennyNeural", "en-US-AriaNeural",
            "en-GB-SoniaNeural", "en-IN-NeerjaNeural", "en-AU-CeciliaNeural"
        ]
        for i, v in enumerate(voices, 1):
            print(f"   {i}. {v}")
        while True:
            try:
                choice = int(input("\n👉 Select (1-6): ")) - 1
                if 0 <= choice < len(voices):
                    return voices[choice]
            except (KeyboardInterrupt, EOFError):
                sys.exit(1)
            except:
                pass
    
    elif engine == "pyttsx3":
        print("\n🔊 pyttsx3 Voices:")
        engine_obj = pyttsx3.init()
        voices = engine_obj.getProperty('voices')
        if not voices:
            return None
        for i, voice in enumerate(voices):
            name = voice.name if hasattr(voice, 'name') else f"Voice {i+1}"
            print(f"   {i+1}. {name}")
        while True:
            try:
                choice = int(input(f"\n👉 Select (1-{len(voices)}): ")) - 1
                if 0 <= choice < len(voices):
                    return voices[choice].id
            except (KeyboardInterrupt, EOFError):
                sys.exit(1)
            except:
                pass
    
    elif engine == "piper":
        return select_piper_model()
    
    return None

async def test_edge_tts_connection():
    """Test Edge-TTS connection before processing"""
    print("\n🔌 Testing Edge-TTS Connection...")
    
    try:
        if not EDGE_TTS_AVAILABLE:
            return False

        import tempfile
        test_text = "Testing audio generation."
        test_file = os.path.join(tempfile.gettempdir(), "edge_tts_test.mp3")
        
        try:
            # Try to generate a test clip
            communicate = edge_tts.Communicate(test_text, "en-US-GuyNeural")
            await communicate.save(test_file)
            
            if os.path.exists(test_file):
                size = os.path.getsize(test_file)
                print(f"   ✅ Edge-TTS working! Generated {size:,} bytes")
                
                # Clean up
                try:
                    os.remove(test_file)
                except:
                    pass
                
                return True
            else:
                print(CP(f"   ❌ Edge-TTS test failed: No file generated", 'red'))
                return False
                
        except Exception as e:
            print(CP(f"   ❌ Edge-TTS test failed: {e}", 'red'))
            print("\n   💡 Possible Solutions:")
            print("      1. Check internet connection")
            print("      2. Try: pip install --upgrade edge-tts")
            print("      3. Restart your router/modem")
            print("      4. Check firewall settings")
            print("      5. Switch to pyttsx3 (offline)")
            return False
        
    except Exception as e:
        print(CP(f"   ❌ Test error: {e}", 'red'))
        return False

def get_piper_models():
    """Discover available Piper models"""
    try:
        model_paths = [
            os.path.expanduser("~/.local/share/piper/models"),
            "/usr/share/piper/models",
            "./piper_models",
            os.getcwd()  # Current directory (where your script is)
        ]
        
        models = []
        for path in model_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.onnx'):
                        full_path = os.path.join(path, file)
                        
                        # Check if .json config exists
                        json_path = full_path + '.json'
                        has_config = os.path.exists(json_path)
                        
                        models.append({
                            'name': file,
                            'path': full_path,
                            'size': os.path.getsize(full_path) / (1024*1024),
                            'has_config': has_config
                        })
                        
                        if not has_config:
                            print(f"   ⚠️  Missing config: {file}.json")
        
        return models
    except Exception as e:
        logger.warning(f"Model discovery failed: {e}")
        return []


def resolve_piper_model_path(preferred: Optional[str] = None) -> Optional[str]:
    """Resolve a Piper model path without prompting the user"""
    candidate = preferred or CONFIG["audio_settings"].get("piper_model_path")

    search_roots = [
        os.getcwd(),
        os.path.join(os.getcwd(), "piper_models"),
        os.path.expanduser("~/.local/share/piper/models"),
        os.path.join(os.getcwd(), "piper"),
    ]

    def _paths_for(name: str):
        expanded = os.path.expanduser(name)
        yield expanded
        if not os.path.isabs(expanded):
            yield os.path.abspath(expanded)
            for root in search_roots:
                yield os.path.abspath(os.path.join(root, expanded))

    if candidate:
        possible_names = [candidate]
        if not candidate.lower().endswith(".onnx"):
            possible_names.append(f"{candidate}.onnx")

        for name in possible_names:
            for path in _paths_for(name):
                if os.path.exists(path):
                    return os.path.abspath(path)

    models = get_piper_models()
    if models:
        return models[0]['path']

    return None

def select_piper_model():
    """Interactive Piper model selection"""
    print("\n🔊 Piper Models:")
    
    models = get_piper_models()
    
    if not models:
        print("   ⚠️  No models found!")
        print("\n   📥 Download models from:")
        print("      https://github.com/rhasspy/piper/releases")
        print("\n   Recommended starter:")
        print("      • en_US-lessac-medium.onnx (Male, clear)")
        print("      • en_US-amy-medium.onnx (Female, natural)")
        print("      • en_US-joe-medium.onnx (Male, deep)")
        
        manual = input("\n   Enter model path manually (or Enter to skip): ").strip()
        if manual and os.path.exists(manual):
            return manual
        return None
    
    for i, model in enumerate(models, 1):
        quality = "high" if "high" in model['name'] else "medium" if "medium" in model['name'] else "low"
        
        # Detect gender from filename
        gender = "Female" if "female" in model['name'].lower() or "amy" in model['name'].lower() else \
                 "Male" if "male" in model['name'].lower() or "lessac" in model['name'].lower() or "joe" in model['name'].lower() or "guy" in model['name'].lower() else \
                 "Neutral"
        
        # Show warning if .json is missing
        status = "✅" if model.get('has_config', True) else "⚠️ MISSING .json"
        
        print(f"   {i}. {model['name']} {status}")
        print(f"      └─ {model['size']:.1f} MB | {gender} | Quality: {quality}")
    
    while True:
        try:
            choice = int(input(f"\n👉 Select (1-{len(models)}): ")) - 1
            if 0 <= choice < len(models):
                selected = models[choice]
                
                # Warn if config is missing
                if not selected.get('has_config', True):
                    print(f"   ⚠️  WARNING: {selected['name']}.json is missing!")
                    print(f"   This voice may not work properly.")
                    proceed = input("   Try anyway? (y/n): ").strip().lower()
                    if proceed != 'y':
                        continue
                
                print(f"   ✅ Selected: {selected['name']}")
                return selected['path']
        except (ValueError, KeyboardInterrupt):
            return None

async def gen_single_clip_edge_with_retry(text, filename, voice, speed, max_retries=7, delay=5, silent=False):
    """Generate Edge-TTS audio with retry logic and timing capture"""
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1 and not silent:
                print(f"\n   🔄 Retry {attempt-1}/{max_retries-1}...", end='', flush=True)
            
            communicate = edge_tts.Communicate(text, voice, rate=speed)
            
            # Use stream() to capture timing data
            subs = []
            sentences = []
            
            with open(filename, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # Structure: {'offset': 123, 'duration': 456, 'text': 'word'}
                        # offset/duration are in 100ns units (ticks)
                        start = chunk["offset"] / 1e7
                        duration = chunk["duration"] / 1e7
                        subs.append({
                            'start': start,
                            'end': start + duration,
                            'text': chunk["text"]
                        })
                    elif chunk["type"] == "SentenceBoundary":
                        # Capture sentences as fallback
                        start = chunk["offset"] / 1e7
                        duration = chunk["duration"] / 1e7
                        sentences.append({
                            'start': start,
                            'end': start + duration,
                            'text': chunk["text"]
                        })

            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                if attempt > 1 and not silent:
                    print(" ✅", flush=True)
                
                # Use words if available, otherwise sentences (fallback)
                final_timing = subs
                if not subs and sentences:
                    # print(f"   ⚠️  Using sentence-level timing (WordBoundary missing)", flush=True)
                    final_timing = sentences
                
                return True, None, {'events': final_timing, 'is_high_precision': True}
            else:
                raise Exception("Empty audio file")
        
        except Exception as e:
            if attempt < max_retries:
                if not silent:
                    print(f"   ❌ {str(e)[:40]}", flush=True)
                    print(f"   ⏳ Waiting {delay}s...", flush=True)
                await asyncio.sleep(delay)
                continue
            else:
                return False, str(e), None
    
    return False, "Max retries reached", None

def gen_single_clip_pyttsx3_with_retry(text, filename, voice_id, speed_rate, max_retries=7, delay=5):
    """Generate pyttsx3 audio with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"\n   🔄 Retry {attempt-1}/{max_retries-1}...", end='', flush=True)
            
            engine = pyttsx3.init()
            if voice_id:
                engine.setProperty('voice', voice_id)
            
            base_rate = 200
            rate_adjust = 1.0
            if speed_rate.startswith("+"):
                rate_adjust = 1 + (int(speed_rate.strip("%+")) / 100)
            elif speed_rate.startswith("-"):
                rate_adjust = 1 - (int(speed_rate.strip("%-")) / 100)
            
            engine.setProperty('rate', base_rate * rate_adjust)
            engine.save_to_file(text, filename)
            engine.runAndWait()
            
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                return True, None, {'events': None, 'is_high_precision': False}
            else:
                raise Exception("Empty audio file")
        
        except Exception as e:
            if attempt < max_retries:
                print(f"   ❌ {str(e)[:40]}", flush=True)
                time.sleep(delay)
                continue
            else:
                return False, str(e), None
    
    return False, "Max retries reached", None

def gen_single_clip_piper_with_retry(text, filename, model_path, max_retries=7, delay=5, silent=False):
    """Generate Piper audio with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1 and not silent:
                print(f"\n   🔄 Retry {attempt-1}/{max_retries-1}...", end='', flush=True)
            
            piper_exe = PIPER_EXE_PATH if PIPER_EXE_PATH else 'piper'
            piper_cmd = [
                piper_exe,
                '--model', model_path,
                '--output_file', filename
            ]
            
            config = CONFIG["audio_settings"]
            if config.get("piper_speaker_id"):
                piper_cmd.extend(['--speaker', str(config["piper_speaker_id"])])
            if config.get("piper_noise_scale"):
                piper_cmd.extend(['--noise_scale', str(config["piper_noise_scale"])])
            if config.get("piper_length_scale"):
                piper_cmd.extend(['--length_scale', str(config["piper_length_scale"])])
            
            # Windows optimization: prevent console popup
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            process = subprocess.run(
                piper_cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=300,
                check=True,
                startupinfo=startupinfo
            )
            
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                if attempt > 1 and not silent:
                    print(" ✅", flush=True)
                
                # Fast Duration Detection (ffprobe > moviepy)
                duration = 0.0
                try:
                    probe_exe = 'ffprobe'
                    try:
                        from imageio_ffmpeg import get_ffmpeg_exe
                        probe_exe = get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
                    except:
                        pass
                        
                    p_cmd = [probe_exe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename]
                    p_result = subprocess.run(p_cmd, capture_output=True, text=True, startupinfo=startupinfo)
                    if p_result.returncode == 0:
                        duration = float(p_result.stdout.strip())
                except Exception:
                    duration = os.path.getsize(filename) / 16000.0
                
                # Estimate word timing (Linear Distribution)
                words = text.split()
                estimated_subs = []
                if words and duration > 0:
                    word_duration = duration / len(words)
                    current_time = 0.0
                    for word in words:
                        estimated_subs.append({
                            'start': current_time,
                            'end': current_time + word_duration,
                            'text': word
                        })
                        current_time += word_duration
                
                return True, None, {'events': estimated_subs, 'is_high_precision': False}
            else:
                raise Exception("Empty audio file")
        
        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                if not silent:
                    print(f"   ❌ Timeout", flush=True)
                    print(f"   ⏳ Waiting {delay}s...", flush=True)
                time.sleep(delay)
                continue
            else:
                return False, "Generation timeout", None
        
        except subprocess.CalledProcessError as e:
            if attempt < max_retries:
                if not silent:
                    error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
                    print(f"   ❌ Piper error: {error_msg[:100]}", flush=True)
                    print(f"   ⏳ Waiting {delay}s...", flush=True)
                time.sleep(delay)
                continue
            else:
                return False, f"Piper error: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}", None
    
    return False, "Max retries reached", None

