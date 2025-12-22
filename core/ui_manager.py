"""
UI Manager Module
Handles all user interaction, menus, and banners.
"""
import os
import sys
import time
import json
from typing import Callable, Optional

from core.utils import CP, beep_notification
from core.config import CONFIG, CONFIG_FILE, logger
from features.queue_manager import QueueManager

def save_global_config():
    """Save global config to file"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(CONFIG, f, indent=4)
        print(CP("   💾 Settings saved", 'green'))
    except Exception as e:
        logger.error(f"Config save failed: {e}")

def print_rainbow_banner():
    """Display epic rainbow banner"""
    lines = [
        "    ███████╗ █████╗ ███╗   ██╗███████╗██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗",
        "    ██╔════╝██╔══██╗████╗  ██║██╔════╝██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║",
        "    █████╗  ███████║██╔██╗ ██║█████╗  ██║██║        ██║   ██║██║   ██║██╔██╗ ██║",
        "    ██╔══╝  ██╔══██║██║╚██╗██║██╔══╝  ██║██║        ██║   ██║██║   ██║██║╚██╗██║",
        "    ██║     ██║  ██║██║ ╚████║██║     ██║╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║",
        "    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
        "                            LEGEND AUTOMATION"
    ]
    colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
    
    print()
    for i, line in enumerate(lines):
        print(colors[i % len(colors)] + line + '\033[0m')
    print(CP("                        Config via config.json", 'cyan'))
    print(CP("=" * 78, 'cyan'))

def handle_video_quality_menu():
    """Handle video quality selection"""
    while True:
        current = CONFIG["video_settings"].get("current_quality_preset", "Balanced")
        presets = CONFIG["video_settings"].get("quality_presets", {})
        
        print("\n" + "="*50)
        print(f"⚙️  VIDEO QUALITY SETTINGS (Current: {CP(current, 'cyan')})")
        print("="*50)
        
        display_order = ["Fast", "Balanced", "High"]
        
        for i, name in enumerate(display_order):
            if name in presets:
                p = presets[name]
                mark = "✅" if name == current else "  "
                print(f"   [{i+1}] {mark} {name:<10} ({p['height']}p, CRF {p['crf']}, {p['preset']})")
        
        print("-" * 50)
        print(f"{CP('[B]', 'cyan')} Back to Main Menu")
        
        choice = input("\n👉 Select option: ").strip().upper()
        
        if choice == 'B':
            break
        
        try:
            val = int(choice)
            if 1 <= val <= len(display_order):
                selected_name = display_order[val-1]
                if selected_name in presets:
                    CONFIG["video_settings"]["current_quality_preset"] = selected_name
                    print(f"   ✅ Quality set to: {selected_name}")
                    save_global_config()
                else:
                     print("   ❌ Preset not configured")
        except:
            pass

def handle_queue_menu(qm: QueueManager, process_callback: Callable):
    """
    Handle the batch queue menu
    
    Args:
        qm: QueueManager instance
        process_callback: Function to call when processing is requested
    """
    while True:
        jobs = qm.get_pending_jobs()
        print("\n" + "="*50)
        print(f"📋 BATCH PROCESSING QUEUE ({len(jobs)} pending)")
        print("="*50)
        
        if not jobs:
            print("   (Queue is empty)")
        
        for i, job in enumerate(jobs):
            print(f"   [{i+1}] {job['title']}")
            print(f"       Added: {job['added_at']}")
            print(f"       Engine: {job['settings'].get('engine', 'N/A')} | Voice: {job['settings'].get('voice', 'N/A')}")
            
        print("-" * 50)
        print(f"{CP('[P]', 'green')} Process Queue Now")
        print(f"{CP('[C]', 'red')} Clear Completed")
        print(f"{CP('[D]', 'yellow')} Delete Job")
        print(f"{CP('[B]', 'cyan')} Back to Main Menu")
        
        choice = input("\n👉 Select option: ").strip().upper()
        
        if choice == 'B':
            break
        elif choice == 'P':
            if not jobs:
                print("   ⚠️  Queue is empty!")
                continue
            # Call the callback
            process_callback(qm)
        elif choice == 'C':
            qm.clear_completed()
            print("   ✅ Completed jobs cleared")
        elif choice == 'D':
            try:
                idx = int(input("   Enter job number to delete: ")) - 1
                if qm.remove_job(idx):
                    print("   ✅ Job removed")
                else:
                    print("   ❌ Invalid job number")
            except:
                pass
