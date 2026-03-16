"""
TTS module
Handles TTS engine selection, voice selection, and audio generation
"""
import os
# Force HuggingFace Hub into offline mode for all local TTS engines (Pocket, Kokoro)
# This prevents any network calls. Edge-TTS is unaffected (it uses its own API).
os.environ["HF_HUB_OFFLINE"] = "1"
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
    # Fallback: check for local binaries
    local_piper_dir = os.path.join(os.getcwd(), 'piper')
    local_piper_linux = os.path.join(local_piper_dir, 'piper')
    local_piper_windows = os.path.join(local_piper_dir, 'piper.exe')
    
    if os.name != 'nt' and os.path.exists(local_piper_linux):
        PIPER_AVAILABLE = True
        PIPER_EXE_PATH = local_piper_linux
        # Ensure executable
        try: os.chmod(PIPER_EXE_PATH, 0o755)
        except OSError: pass  # Permission may already be set
        print(f"✅ Piper TTS detected (local Linux: {local_piper_linux})")
    elif os.path.exists(local_piper_windows):
        PIPER_AVAILABLE = True
        PIPER_EXE_PATH = local_piper_windows
        print(f"✅ Piper TTS detected (local Windows: {local_piper_windows})")
    else:
        PIPER_AVAILABLE = False
        PIPER_EXE_PATH = None
        print("⚠️  'piper' not found. Install: https://github.com/rhasspy/piper")

# Check Chatterbox availability
try:
    from core.tts_chatterbox import ChatterboxTTSClient
    CHATTERBOX_AVAILABLE = True
    print("✅ Chatterbox TTS available (Premium)")
except ImportError:
    CHATTERBOX_AVAILABLE = False
    print("⚠️  Chatterbox TTS not available.")
except Exception as e:
    CHATTERBOX_AVAILABLE = False
    print(f"⚠️  Chatterbox TTS import error: {e}")

# Check Pocket TTS availability
try:
    from pocket_tts import TTSModel
    POCKET_AVAILABLE = True
    print("✅ Pocket TTS available")
except ImportError:
    POCKET_AVAILABLE = False
    print("⚠️  'pocket-tts' missing. Run: pip install pocket-tts")

# Check Kokoro TTS availability
try:
    from kokoro import KPipeline
    KOKORO_AVAILABLE = True
    print("✅ Kokoro TTS available (offline)")
except ImportError:
    KOKORO_AVAILABLE = False
    print("⚠️  'kokoro' missing. Run: pip install kokoro soundfile")

if not EDGE_TTS_AVAILABLE and not PYTTSX3_AVAILABLE and not PIPER_AVAILABLE and not POCKET_AVAILABLE and not KOKORO_AVAILABLE:
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
    if CHATTERBOX_AVAILABLE:
        available.append("4. Chatterbox Turbo (premium, expressive, SLOW)")
    if POCKET_AVAILABLE:
        available.append("5. Pocket TTS (offline, fast, CPU-efficient)")
    if KOKORO_AVAILABLE:
        available.append("6. Kokoro (offline, 82M, high-quality)")
    
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
                print("\n💡 Piper enabled (Sequential Safe Mode)")
                # Force sequential mode to avoid process pool failures
                return "piper", False

            elif choice == "4" and CHATTERBOX_AVAILABLE:
                print("\n💡 Chatterbox Features:")
                print("   • Expressive (laughs, sighs)")
                print("   • Voice cloning capable")
                print("   • Quality > Speed")
                return "chatterbox", False
                
            elif choice == "5" and POCKET_AVAILABLE:
                print("\n💡 Pocket TTS enabled (Sequential Mode)")
                return "pocket", False

            elif choice == "6" and KOKORO_AVAILABLE:
                print("\n💡 Kokoro TTS enabled (Sequential Mode)")
                return "kokoro", False
                
        except (KeyboardInterrupt, EOFError):
            sys.exit(1)

def preview_voice(engine, voice_id):
    """Generate and play a short voice preview (~10 seconds)"""
    import os
    import subprocess
    import tempfile
    
    text = "This is a preview of my voice. I can narrate your audiobooks with high quality and natural intonation. Let's make something great together."
    tmp_wav = os.path.join(tempfile.gettempdir(), f"preview_{engine}_{voice_id}.wav")
    
    print(f"\n   ⏳ Generating ~10s preview for '{voice_id}' (please wait)...")
    success = False
    
    if engine == "pocket":
        success, _, _ = gen_single_clip_pocket_with_retry(text, tmp_wav, voice_id, max_retries=1, delay=1, silent=True)
    elif engine == "kokoro":
        success, _, _ = gen_single_clip_kokoro_with_retry(text, tmp_wav, voice_id, max_retries=1, delay=1, silent=True)
        
    if success and os.path.exists(tmp_wav):
        print("   🔊 Playing preview...")
        try:
            # Try ffplay first
            subprocess.run(["ffplay", "-nodisp", "-autoexit", tmp_wav], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            try:
                # Fallback to aplay (ALSA player on Linux)
                subprocess.run(["aplay", "-q", tmp_wav], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print("   ❌ Could not play audio (ffplay/aplay not found)")
        try:
            os.remove(tmp_wav)
        except OSError:
            pass
    else:
        print("   ❌ Failed to generate preview")

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
            except ValueError:
                pass  # Invalid input, loop again
    
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
            except ValueError:
                pass  # Invalid input, loop again
    
    elif engine == "piper":
        return select_piper_model()
    
    elif engine == "pocket":
        print("\n🔊 Pocket TTS Voices:")
        voices = [
            ("Alba (Female, Default)", "alba"),
            ("Fantine (Female)", "fantine"),
            ("Marius (Male)", "marius"),
            ("Javert (Male)", "javert")
        ]
        for i, (name, _) in enumerate(voices, 1):
            print(f"   {i}. {name}")
        print("\n   💡 Tip: Type 'p' followed by the number (e.g. 'p1') to preview a voice!")
        
        while True:
            try:
                choice = input(f"\n👉 Select (1-{len(voices)}, default 1): ").strip().lower()
                if not choice:
                    return voices[0][1]
                
                is_preview = choice.startswith('p')
                if is_preview:
                    choice = choice[1:]
                    
                if not choice.isdigit():
                    continue
                    
                idx = int(choice) - 1
                if 0 <= idx < len(voices):
                    selected_voice = voices[idx][1]
                    if is_preview:
                        preview_voice("pocket", selected_voice)
                    else:
                        return selected_voice
            except (KeyboardInterrupt, EOFError):
                sys.exit(1)
            except ValueError:
                pass

    elif engine == "kokoro":
        print("\n🔊 Kokoro Houses (Voices):")
        voices = [
            ("Heart (American Female, Default)", "af_heart", "a"),
            ("Emma (British Female)", "bf_emma", "b"),
            ("Adam (American Male)", "am_adam", "a"),
            ("Michael (American Male)", "am_michael", "a"),
            ("George (British Male)", "bm_george", "b")
        ]
        for i, (name, _, _) in enumerate(voices, 1):
            print(f"   {i}. {name}")
        print("\n   💡 Tip: Type 'p' followed by the number (e.g. 'p1') to preview a voice!")
        
        while True:
            try:
                choice = input(f"\n👉 Select (1-{len(voices)}, default 1): ").strip().lower()
                if not choice:
                    CONFIG["audio_settings"]["kokoro_lang_code"] = voices[0][2]
                    return voices[0][1] # af_heart
                    
                is_preview = choice.startswith('p')
                if is_preview:
                    choice = choice[1:]
                    
                if not choice.isdigit():
                    continue
                    
                idx = int(choice) - 1
                if 0 <= idx < len(voices):
                    selected_voice = voices[idx][1]
                    selected_lang = voices[idx][2]
                    
                    if is_preview:
                        old_lang = CONFIG["audio_settings"].get("kokoro_lang_code", "a")
                        CONFIG["audio_settings"]["kokoro_lang_code"] = selected_lang
                        preview_voice("kokoro", selected_voice)
                        CONFIG["audio_settings"]["kokoro_lang_code"] = old_lang
                    else:
                        CONFIG["audio_settings"]["kokoro_lang_code"] = selected_lang
                        return selected_voice
            except (KeyboardInterrupt, EOFError):
                sys.exit(1)
            except ValueError:
                pass
    
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
                except OSError:
                    pass  # Cleanup is non-critical
                
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
                
            # Environment setup for Linux shared libraries
            env = os.environ.copy()
            if os.name != 'nt' and PIPER_EXE_PATH and os.path.isabs(PIPER_EXE_PATH):
                piper_dir = os.path.dirname(PIPER_EXE_PATH)
                if 'LD_LIBRARY_PATH' in env:
                    env['LD_LIBRARY_PATH'] = f"{piper_dir}:{env['LD_LIBRARY_PATH']}"
                else:
                    env['LD_LIBRARY_PATH'] = piper_dir

            process = subprocess.run(
                piper_cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=300,
                check=True,
                startupinfo=startupinfo,
                env=env
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
                    except Exception:
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

import threading
_pocket_local = threading.local()
_pocket_lock = threading.Lock()

def get_pocket_model():
    """Retrieve or initialize thread-local Pocket TTS model safely"""
    if getattr(_pocket_local, 'model', None) is None:
        import torch
        from pocket_tts import TTSModel
        
        # Option 2: Optimize CPU Threads for Ryzen 5600GT (6 cores)
        # Safe to set per-thread initialization, it sets global PyTorch threads
        torch.set_num_threads(6)
        
        # Option 1 failed: lsd_decode_steps must be > 0. Reverting to default (1).
        with _pocket_lock:
            _pocket_local.model = TTSModel.load_model()
            
    return _pocket_local.model

def gen_single_clip_pocket_with_retry(text, filename, voice_id="en", max_retries=7, delay=5, silent=False):
    """Generate Pocket TTS audio with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1 and not silent:
                print(f"\n   🔄 Retry {attempt-1}/{max_retries-1}...", end='', flush=True)
            
            import scipy.io.wavfile
            import torch
            import numpy as np
            import re
            
            model = get_pocket_model()
            
            # Parse voice
            v_id = voice_id if voice_id else "alba"
            if v_id == "en" or v_id == "":
                v_id = "alba"
                
            voice_state = model.get_state_for_audio_prompt(v_id)
            
            # Smart chunking to avoid "Maximum generation length reached" bug
            # Pocket TTS has a known bug with long text — we must keep chunks short.
            # Step 1: Split on sentence boundaries (.!?;:)
            raw_chunks = re.split(r'(?<=[.!?;:])\s+', text.strip())
            
            # Step 2: Sub-split any chunk still over the limit on commas/dashes
            MAX_CHUNK_CHARS = 100
            chunks = []
            for chunk in raw_chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                if len(chunk) <= MAX_CHUNK_CHARS:
                    chunks.append(chunk)
                else:
                    # Split on commas, dashes, and em-dashes
                    sub_parts = re.split(r'[,\-—]\s*', chunk)
                    current = ""
                    for part in sub_parts:
                        if current and len(current) + len(part) > MAX_CHUNK_CHARS:
                            chunks.append(current.strip())
                            current = part
                        else:
                            current = f"{current} {part}" if current else part
                    if current.strip():
                        chunks.append(current.strip())
            
            # Step 3: Hard fallback — if any chunk is STILL too long (no punctuation),
            # split by word count
            MAX_WORDS_PER_CHUNK = 15
            final_chunks = []
            for chunk in chunks:
                words_in_chunk = chunk.split()
                if len(words_in_chunk) > MAX_WORDS_PER_CHUNK:
                    for i in range(0, len(words_in_chunk), MAX_WORDS_PER_CHUNK):
                        segment = " ".join(words_in_chunk[i:i + MAX_WORDS_PER_CHUNK])
                        if segment:
                            final_chunks.append(segment)
                else:
                    final_chunks.append(chunk)
            
            chunks = final_chunks if final_chunks else [text]
            
            # Generate audio for each chunk and concatenate
            audio_chunks = []
            for chunk in chunks:
                chunk_audio = model.generate_audio(voice_state, chunk)
                chunk_np = chunk_audio.cpu().numpy()
                if chunk_np.shape[0] == 1:
                    chunk_np = chunk_np[0]
                elif chunk_np.ndim > 1:
                    chunk_np = chunk_np.T
                audio_chunks.append(chunk_np)
            
            if not audio_chunks:
                raise Exception("No audio chunks generated")
            
            full_audio = np.concatenate(audio_chunks)
            scipy.io.wavfile.write(filename, model.sample_rate, full_audio)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                if attempt > 1 and not silent:
                    print(" ✅", flush=True)
                
                # Estimate word timing (Linear Distribution)
                duration = len(full_audio) / model.sample_rate
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
                
        except Exception as e:
            import traceback
            full_trace = traceback.format_exc()
            if attempt < max_retries:
                if not silent:
                    print(f"\n   ❌ Pocket-TTS error: {str(e)[:40]}", flush=True)
                    print(f"   [DEBUG TRACE]: {full_trace}", flush=True)
                    print(f"   ⏳ Waiting {delay}s...", flush=True)
                import time
                time.sleep(delay)
                continue
            else:
                return False, f"Pocket-TTS error: {str(e)}\nTrace: {full_trace}", None
                
    return False, "Max retries reached", None

def gen_single_clip_chatterbox(text, filename):
    """Generate audio using Chatterbox Turbo"""
    try:
        from core.tts_chatterbox import ChatterboxTTSClient
        client = ChatterboxTTSClient()
        client.generate_audio(text, filename)
        
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            # Estimate duration for subtitles
            duration = os.path.getsize(filename) / 32000.0 # Approx 16bit 16khz mono
            
            # Simple word distribution
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
             return False, "Empty audio generated", None

    except Exception as e:
        return False, str(e), None

# ------ Kokoro TTS ------
import threading
_kokoro_local = threading.local()
_kokoro_lock = threading.Lock()

def get_kokoro_pipeline():
    """Retrieve or initialize thread-local Kokoro pipeline, re-initializing if lang_code changes"""
    import torch
    lang_code = CONFIG["audio_settings"].get("kokoro_lang_code", "a")
    curr_lang = getattr(_kokoro_local, 'lang_code', None)
    
    if getattr(_kokoro_local, 'pipeline', None) is None or curr_lang != lang_code:
        from kokoro import KPipeline
        # Optimize CPU: use all 6 cores of Ryzen 5600GT
        torch.set_num_threads(6)
        with _kokoro_lock:
            _kokoro_local.pipeline = KPipeline(lang_code=lang_code, repo_id='hexgrad/Kokoro-82M')
            _kokoro_local.lang_code = lang_code
    return _kokoro_local.pipeline

def gen_single_clip_kokoro_with_retry(text, filename, voice_id="af_heart", max_retries=7, delay=5, silent=False):
    """Generate Kokoro TTS audio with retry logic"""
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1 and not silent:
                print(f"\n   🔄 Retry {attempt-1}/{max_retries-1}...", end='', flush=True)
            
            import soundfile as sf
            import numpy as np
            
            pipeline = get_kokoro_pipeline()
            v_id = voice_id if voice_id else "af_heart"
            
            import torch
            
            # Generate all chunks with inference_mode (no gradients = ~30-50% faster)
            audio_chunks = []
            with torch.inference_mode():
                for i, (gs, ps, audio) in enumerate(pipeline(text, voice=v_id, speed=1)):
                    audio_chunks.append(audio)
            
            if not audio_chunks:
                raise Exception("No audio chunks generated")
            
            full_audio = np.concatenate(audio_chunks)
            sf.write(filename, full_audio, 24000)
            
            if os.path.exists(filename) and os.path.getsize(filename) > 1000:
                if attempt > 1 and not silent:
                    print(" ✅", flush=True)
                
                # Estimate word timing (Linear Distribution)
                duration = len(full_audio) / 24000.0
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
                
        except Exception as e:
            import traceback
            full_trace = traceback.format_exc()
            if attempt < max_retries:
                if not silent:
                    print(f"\n   ❌ Kokoro error: {str(e)[:40]}", flush=True)
                    print(f"   [DEBUG TRACE]: {full_trace}", flush=True)
                    print(f"   ⏳ Waiting {delay}s...", flush=True)
                import time
                time.sleep(delay)
                continue
            else:
                return False, f"Kokoro error: {str(e)}\nTrace: {full_trace}", None
                
    return False, "Max retries reached", None
