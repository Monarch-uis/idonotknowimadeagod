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

def handle_queue_menu(qm: QueueManager, process_callback: Callable, add_job_callback: Callable):
    """
    Handle the batch queue menu (Aligned with human-centric documentation)
    
    Args:
        qm: QueueManager instance
        process_callback: Function to call when processing is requested
        add_job_callback: Function to call to add a new book
    """
    while True:
        try:
            summary = qm.get_queue_summary()
            
            print("\n" + "═"*50)
            print(CP("📋 QUEUE MANAGER", 'purple'))
            print("═"*50)
            print("Current queue status:")
            print(f"  • {CP('Pending:', 'yellow')}   {summary['pending']} book(s)")
            print(f"  • {CP('Processing:', 'cyan')} {summary['processing']}")
            print(f"  • {CP('Completed:', 'green')}  {summary['completed']}")
            print(f"  • {CP('Failed:', 'red')}     {summary['failed']}")
            print()
            print("Options:")
            print(f"  {CP('1.', 'cyan')} Add new book to queue")
            print(f"  {CP('2.', 'cyan')} View pending jobs")
            print(f"  {CP('3.', 'cyan')} Start processing queue")
            print(f"  {CP('4.', 'cyan')} Clear completed jobs")
            print(f"  {CP('5.', 'cyan')} Remove a job from queue")
            print(f"  {CP('6.', 'cyan')} Back to main menu")
            
            choice = input(f"\n   {CP('👉 Select (1-6):', 'cyan')} ").strip()
            
            if choice == '1':
                add_job_callback()
            elif choice == '2':
                jobs = qm.get_pending_jobs()
                print("\n" + "═"*50)
                print(f"Pending jobs in queue:")
                print("═"*50)
                if not jobs:
                    print("   (Queue is empty)")
                else:
                    for i, job in enumerate(jobs):
                        print(f"{i+1}. {job['title']}")
                        s = job['settings']
                        # Try to get chapter range from settings
                        rb = s.get('raw_batches', [])
                        range_str = f"{len(rb)} batches" if rb else "Full book"
                        print(f"   Chapters: {range_str} | Engine: {s.get('engine', 'N/A')} | Quality: {s.get('quality_preset', 'N/A')}")
                        print(f"   Added: {job['added_at']}")
                        print()
                input("\nPress Enter to continue...")
            elif choice == '3':
                if summary['pending'] == 0:
                    print(CP("\n   ⚠️  No pending jobs to process!", 'yellow'))
                    time.sleep(1)
                    continue
                    
                # Ask how to process
                print(f"\n   How would you like to process?")
                print(f"   [1] Process in THIS window")
                print(f"   [2] Spawn worker in NEW window (Recommended)")
                
                p_choice = input(f"\n   👉 Select (1/2, default 2): ").strip()
                
                if p_choice == '1':
                    process_callback(qm)
                else:
                    if qm.spawn_worker_terminal():
                        print(CP("\n   ✅ Worker started in new terminal. You can close this window.", 'green'))
                        time.sleep(2)
                    else:
                        # Fallback to local if spawn failed
                        process_callback(qm)
            elif choice == '4':
                qm.clear_completed()
                print(CP("\n   ✅ Completed jobs cleared", 'green'))
                time.sleep(1)
            elif choice == '5':
                jobs = qm.get_pending_jobs()
                if not jobs:
                    print(CP("\n   ⚠️  No jobs to remove", 'yellow'))
                    time.sleep(1)
                    continue
                
                print("\n   Enter job number to remove:")
                for i, job in enumerate(jobs):
                    print(f"   [{i+1}] {job['title']}")
                
                try:
                    idx_str = input("\n   👉 Job #: ").strip()
                    if idx_str:
                        idx = int(idx_str) - 1
                        # Map index back to real queue index
                        # qm.remove_job(idx) usually handles this by reloading?
                        # Wait, qm.remove_job uses absolute index. 
                        # Pending jobs might be at different indices if there are completed ones.
                        # reload and find by ID is safer.
                        target_id = jobs[idx]['id']
                        
                        # Find absolute index
                        qm.reload()
                        abs_idx = -1
                        for i, j in enumerate(qm.queue_data):
                            if j['id'] == target_id:
                                abs_idx = i
                                break
                        
                        if abs_idx != -1:
                            confirm = input(f"   Remove job: {jobs[idx]['title']}? (y/n): ").lower()
                            if confirm == 'y':
                                qm.remove_job(abs_idx)
                                print(CP("   ✅ Job removed", 'green'))
                            else:
                                print("   ❌ Cancelled")
                        else:
                             print("   ❌ Job not found in queue")
                    time.sleep(1)
                except:
                    print("   ❌ Invalid selection")
                    time.sleep(1)
            elif choice == '6' or choice.lower() == 'b':
                break
        except Exception as e:
            print(CP(f"\n   ❌ Menu Error: {e}", 'red'))
            time.sleep(2)
