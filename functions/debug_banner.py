
print("Step 1: Imports")
import os
import sys
import time
# Try imports one by one
try:
    print("Importing moviepy...")
    from moviepy.editor import AudioFileClip
    print("MoviePy imported.")
except Exception as e:
    print(f"MoviePy failed: {e}")

print("Step 2: Rainbow Banner")

def CP(text, color='white'):
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'purple': '\033[95m',
        'white': '\033[97m',
    }
    end = '\033[0m'
    return colors.get(color, '') + text + end

def print_rainbow_banner():
    lines = [
        "    ███████╗ █████╗ ███╗   ██╗███████╗██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗",
        "    ██╔════╝██╔══██╗████╗  ██║██╔════╝██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║",
        "    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
        "                            LEGEND AUTOMATION"
    ]
    colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
    
    os.system("") # Enable processing
    
    print()
    for i, line in enumerate(lines):
        print(colors[i % len(colors)] + line + '\033[0m')

print_rainbow_banner()
print("Banner printed. Waiting 5s...")
time.sleep(5)
print("Done.")
