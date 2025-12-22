#!/usr/bin/env python3
"""
Voice Testing Tool - Test TTS voices at different speeds
Helps you choose the best voice for your audiobooks
"""

import os
import sys
import asyncio
import subprocess
import time

# Test sample
TEST_TEXT = """
Chapter One. The Beginning. 
Naruto stood at the edge of the cliff, looking down at the village below. 
The wind howled through the trees as he clenched his fists. 
This was it. The moment he had been training for his entire life.
"""

TEST_TEXT_SHORT = "Chapter One. The Beginning. This is a test of the voice quality at various speeds."

def CP(text, color='white'):
    """Color print"""
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'purple': '\033[95m',
        'white': '\033[97m',
    }
    return colors.get(color, '') + text + '\033[0m'

# ---------------------------
# PIPER VOICE TESTING
# ---------------------------
def test_piper_voices():
    """Test all available Piper voices"""
    print(CP("\n🎤 PIPER VOICE TESTING", 'cyan'))
    print("=" * 60)
    
    # Check if Piper is available
    try:
        subprocess.run(['piper', '--version'], capture_output=True, timeout=5)
    except:
        print(CP("❌ Piper not found. Please install Piper first.", 'red'))
        return
    
    # Find models
    model_paths = [
        os.path.expanduser("~/.local/share/piper/models"),
        "/usr/share/piper/models",
        "./piper_models",
        os.getcwd()
    ]
    
    models = []
    for path in model_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.onnx'):
                    models.append({
                        'name': file,
                        'path': os.path.join(path, file)
                    })
    
    if not models:
        print(CP("❌ No Piper models found!", 'red'))
        print("\n📥 Download models from:")
        print("   https://github.com/rhasspy/piper/releases")
        print("\n⭐ RECOMMENDED MODELS:")
        print("   • en_US-lessac-medium.onnx (male, clear)")
        print("   • en_US-amy-medium.onnx (female, professional)")
        print("   • en_GB-alan-medium.onnx (British male)")
        print("   • en_US-libritts_r-medium.onnx (versatile)")
        return
    
    print(f"\n✅ Found {len(models)} Piper models\n")
    
    # List models with recommendations
    for i, model in enumerate(models, 1):
        name = model['name']
        
        # Determine characteristics
        is_male = any(x in name.lower() for x in ['lessac', 'alan', 'joe', 'ryan'])
        is_female = any(x in name.lower() for x in ['amy', 'jenny', 'kathleen'])
        is_british = 'gb' in name.lower()
        quality = 'high' if 'high' in name else 'medium' if 'medium' in name else 'low'
        
        gender = "Male" if is_male else "Female" if is_female else "Neutral"
        accent = "British" if is_british else "American"
        
        print(f"{i}. {name}")
        print(f"   └─ {gender} | {accent} | Quality: {quality.title()}")
        
        # Add recommendations
        if 'lessac' in name.lower():
            print(CP("      ⭐ POPULAR - Clear male voice, great for audiobooks", 'green'))
        elif 'amy' in name.lower():
            print(CP("      ⭐ POPULAR - Professional female voice", 'green'))
        elif 'alan' in name.lower():
            print(CP("      ⭐ GOOD - British accent, authoritative", 'green'))
        print()
    
    # Test selection
    while True:
        choice = input(f"👉 Select model to test (1-{len(models)}) or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                print(f"\n🎧 Testing: {selected['name']}")
                print("=" * 60)
                
                # Test at different speeds
                speeds = [1.0, 1.5, 2.0]
                for speed in speeds:
                    print(f"\n⚡ Speed: {speed}x")
                    output = f"test_piper_{speed}x.wav"
                    
                    try:
                        cmd = [
                            'piper',
                            '--model', selected['path'],
                            '--length_scale', str(1.0 / speed),  # Speed control
                            '--output_file', output
                        ]
                        
                        subprocess.run(
                            cmd,
                            input=TEST_TEXT.encode('utf-8'),
                            capture_output=True,
                            timeout=30,
                            check=True
                        )
                        
                        if os.path.exists(output):
                            print(f"   ✅ Generated: {output}")
                            print(f"   🎵 Playing...")
                            
                            # Play the audio
                            if sys.platform == "win32":
                                os.system(f'start {output}')
                            elif sys.platform == "darwin":
                                os.system(f'afplay {output}')
                            else:
                                os.system(f'paplay {output} 2>/dev/null || aplay {output} 2>/dev/null')
                            
                            time.sleep(15)  # Give time to listen
                        else:
                            print(CP("   ❌ Generation failed", 'red'))
                    
                    except subprocess.TimeoutExpired:
                        print(CP("   ❌ Generation timeout", 'red'))
                    except Exception as e:
                        print(CP(f"   ❌ Error: {e}", 'red'))
                
                # Ask if satisfied
                print("\n" + "=" * 60)
                satisfied = input("👍 Like this voice? (y/n): ").strip().lower()
                if satisfied == 'y':
                    print(CP(f"\n✅ Great choice! Use this in config.json:", 'green'))
                    print(f'   "piper_model_path": "{selected["path"]}"')
                    print(f'\n💡 For 2x speed playback, your video player will handle that.')
                    print(f'   The voice sounds good at all speeds!')
                    return
                
                # Continue testing?
                continue_test = input("\n🔄 Test another voice? (y/n): ").strip().lower()
                if continue_test != 'y':
                    return
        
        except (ValueError, IndexError):
            print(CP("Invalid choice. Try again.", 'yellow'))

# ---------------------------
# PYTTSX3 VOICE TESTING
# ---------------------------
def test_pyttsx3_voices():
    """Test pyttsx3 voices"""
    print(CP("\n🎤 PYTTSX3 VOICE TESTING", 'cyan'))
    print("=" * 60)
    
    try:
        import pyttsx3
    except ImportError:
        print(CP("❌ pyttsx3 not installed. Run: pip install pyttsx3", 'red'))
        return
    
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    if not voices:
        print(CP("❌ No pyttsx3 voices found on your system", 'red'))
        return
    
    print(f"\n✅ Found {len(voices)} system voices\n")
    
    for i, voice in enumerate(voices, 1):
        name = voice.name if hasattr(voice, 'name') else f"Voice {i}"
        lang = voice.languages[0] if hasattr(voice, 'languages') and voice.languages else 'Unknown'
        
        is_male = any(x in name.lower() for x in ['david', 'mark', 'george', 'male', 'guy'])
        is_female = any(x in name.lower() for x in ['zira', 'susan', 'hazel', 'female'])
        gender = "Male" if is_male else "Female" if is_female else "Unknown"
        
        print(f"{i}. {name}")
        print(f"   └─ {gender} | Language: {lang}")
        print()
    
    # Test selection
    while True:
        choice = input(f"👉 Select voice to test (1-{len(voices)}) or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(voices):
                selected = voices[idx]
                print(f"\n🎧 Testing: {selected.name}")
                print("=" * 60)
                
                # Test at different speeds
                base_rate = 200
                speeds = [(1.0, base_rate), (1.5, int(base_rate * 1.5)), (2.0, base_rate * 2)]
                
                for speed_label, rate in speeds:
                    print(f"\n⚡ Speed: {speed_label}x")
                    output = f"test_pyttsx3_{speed_label}x.wav"
                    
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('voice', selected.id)
                        engine.setProperty('rate', rate)
                        engine.save_to_file(TEST_TEXT, output)
                        engine.runAndWait()
                        
                        if os.path.exists(output):
                            print(f"   ✅ Generated: {output}")
                            print(f"   🎵 Playing...")
                            
                            # Play the audio
                            if sys.platform == "win32":
                                os.system(f'start {output}')
                            elif sys.platform == "darwin":
                                os.system(f'afplay {output}')
                            else:
                                os.system(f'paplay {output} 2>/dev/null || aplay {output} 2>/dev/null')
                            
                            time.sleep(15)
                        else:
                            print(CP("   ❌ Generation failed", 'red'))
                    
                    except Exception as e:
                        print(CP(f"   ❌ Error: {e}", 'red'))
                
                # Ask if satisfied
                print("\n" + "=" * 60)
                satisfied = input("👍 Like this voice? (y/n): ").strip().lower()
                if satisfied == 'y':
                    print(CP(f"\n✅ Great choice! This voice ID:", 'green'))
                    print(f'   {selected.id}')
                    print(f'\n💡 The script will remember this choice')
                    return
                
                # Continue testing?
                continue_test = input("\n🔄 Test another voice? (y/n): ").strip().lower()
                if continue_test != 'y':
                    return
        
        except (ValueError, IndexError):
            print(CP("Invalid choice. Try again.", 'yellow'))

# ---------------------------
# EDGE-TTS VOICE TESTING
# ---------------------------
async def test_edge_single_voice(voice_name, speed_label, rate):
    """Test a single Edge-TTS voice at a specific speed"""
    try:
        import edge_tts
    except ImportError:
        return None, "edge-tts not installed"
    
    output = f"test_edge_{voice_name.split('-')[-1]}_{speed_label}x.mp3"
    
    try:
        communicate = edge_tts.Communicate(TEST_TEXT, voice_name, rate=rate)
        await communicate.save(output)
        
        if os.path.exists(output) and os.path.getsize(output) > 1000:
            return output, None
        else:
            return None, "File generation failed"
    except Exception as e:
        return None, str(e)

def test_edge_tts_voices():
    """Test Edge-TTS voices"""
    print(CP("\n🎤 EDGE-TTS VOICE TESTING", 'cyan'))
    print("=" * 60)
    
    try:
        import edge_tts
    except ImportError:
        print(CP("❌ edge-tts not installed. Run: pip install edge-tts", 'red'))
        return
    
    print(CP("\n⚠️  REMEMBER: Edge-TTS has rate limiting!", 'yellow'))
    print("   Use for testing only. Switch to Piper for production.\n")
    
    # Popular voices
    voices = [
        ("en-US-GuyNeural", "Male, American, Professional"),
        ("en-US-JennyNeural", "Female, American, Friendly"),
        ("en-US-AriaNeural", "Female, American, News-style"),
        ("en-GB-RyanNeural", "Male, British, Clear"),
        ("en-GB-SoniaNeural", "Female, British, Professional"),
        ("en-AU-WilliamNeural", "Male, Australian, Casual"),
    ]
    
    print("Popular Edge-TTS Voices:\n")
    for i, (voice_id, desc) in enumerate(voices, 1):
        print(f"{i}. {voice_id}")
        print(f"   └─ {desc}")
        print()
    
    while True:
        choice = input(f"👉 Select voice to test (1-{len(voices)}) or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(voices):
                voice_id, desc = voices[idx]
                print(f"\n🎧 Testing: {voice_id}")
                print(f"   {desc}")
                print("=" * 60)
                
                # Test at different speeds
                speeds = [(1.0, "+0%"), (1.5, "+50%"), (2.0, "+100%")]
                
                for speed_label, rate in speeds:
                    print(f"\n⚡ Speed: {speed_label}x (rate: {rate})")
                    
                    output, error = asyncio.run(test_edge_single_voice(voice_id, speed_label, rate))
                    
                    if output:
                        print(f"   ✅ Generated: {output}")
                        print(f"   🎵 Playing...")
                        
                        # Play the audio
                        if sys.platform == "win32":
                            os.system(f'start {output}')
                        elif sys.platform == "darwin":
                            os.system(f'afplay {output}')
                        else:
                            os.system(f'paplay {output} 2>/dev/null || aplay {output} 2>/dev/null')
                        
                        time.sleep(15)
                    else:
                        print(CP(f"   ❌ Error: {error}", 'red'))
                
                # Ask if satisfied
                print("\n" + "=" * 60)
                satisfied = input("👍 Like this voice? (y/n): ").strip().lower()
                if satisfied == 'y':
                    print(CP(f"\n✅ Great choice! Use this in config.json:", 'green'))
                    print(f'   "voice": "{voice_id}"')
                    print(CP(f'\n⚠️  Remember: Edge-TTS has rate limits!', 'yellow'))
                    print(f'   Consider Piper for large batches.')
                    return
                
                # Continue testing?
                continue_test = input("\n🔄 Test another voice? (y/n): ").strip().lower()
                if continue_test != 'y':
                    return
        
        except (ValueError, IndexError):
            print(CP("Invalid choice. Try again.", 'yellow'))

# ---------------------------
# MAIN MENU
# ---------------------------
def main():
    print(CP("\n" + "=" * 60, 'cyan'))
    print(CP("  🎤 TTS VOICE TESTING TOOL", 'cyan'))
    print(CP("=" * 60, 'cyan'))
    print("\nTest voices at different speeds before committing to a project!")
    print("All tests include 1.0x, 1.5x, and 2.0x speed samples.\n")
    
    while True:
        print("\n" + "=" * 60)
        print("Which TTS engine do you want to test?")
        print("=" * 60)
        print("1. Piper (offline, no limits, recommended)")
        print("2. pyttsx3 (offline, system voices)")
        print("3. Edge-TTS (online, rate limited)")
        print("4. Cleanup test files")
        print("q. Quit")
        
        choice = input("\n👉 Select: ").strip()
        
        if choice == '1':
            test_piper_voices()
        elif choice == '2':
            test_pyttsx3_voices()
        elif choice == '3':
            test_edge_tts_voices()
        elif choice == '4':
            # Cleanup
            test_files = [f for f in os.listdir('.') if f.startswith('test_')]
            if test_files:
                for f in test_files:
                    try:
                        os.remove(f)
                    except:
                        pass
                print(CP(f"\n✅ Deleted {len(test_files)} test files", 'green'))
            else:
                print("\nℹ️  No test files to cleanup")
        elif choice.lower() == 'q':
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
