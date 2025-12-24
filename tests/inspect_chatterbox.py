import sys
import os

try:
    import chatterbox
    print(f"Imported chatterbox from {chatterbox.__file__}")
    print(dir(chatterbox))
except ImportError as e:
    print(f"Failed to import chatterbox: {e}")

try:
    from chatterbox import tts, tts_turbo
    print("Found submodules tts and tts_turbo")
    print(f"tts contents: {dir(tts)}")
    print(f"tts_turbo contents: {dir(tts_turbo)}")
except ImportError as e:
    print(f"Failed to import submodules: {e}")
