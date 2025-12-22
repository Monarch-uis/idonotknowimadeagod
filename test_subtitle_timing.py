#!/usr/bin/env python3
"""
Quick test to verify subtitle timing accuracy
Run this to check if your subtitles match audio duration
"""

import os
import sys
from pathlib import Path

def parse_ass_file(ass_path):
    """Parse ASS subtitle file and extract timing info"""
    if not os.path.exists(ass_path):
        return None
    
    caption_times = []
    with open(ass_path, 'r', encoding='utf-8') as f:
        in_events = False
        for line in f:
            line = line.strip()
            
            if line == '[Events]':
                in_events = True
                continue
            
            if in_events and line.startswith('Dialogue:'):
                # Format: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
                parts = line.split(',', 9)
                if len(parts) >= 3:
                    start_str = parts[1].strip()
                    end_str = parts[2].strip()
                    
                    # Convert H:MM:SS.CS to seconds
                    def time_to_seconds(time_str):
                        h, m, s = time_str.split(':')
                        s, cs = s.split('.')
                        return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100
                    
                    try:
                        start = time_to_seconds(start_str)
                        end = time_to_seconds(end_str)
                        caption_times.append((start, end))
                    except:
                        continue
    
    return caption_times

def get_audio_duration(audio_path):
    """Get audio file duration using moviepy"""
    try:
        from moviepy.editor import AudioFileClip
        clip = AudioFileClip(audio_path)
        duration = clip.duration
        clip.close()
        return duration
    except:
        return None

def analyze_timing(audio_path, subtitle_path):
    """Analyze subtitle timing accuracy"""
    print("\n" + "="*60)
    print("🔍 SUBTITLE TIMING ANALYSIS")
    print("="*60)
    
    # Get audio duration
    print(f"\n📂 Files:")
    print(f"   Audio: {os.path.basename(audio_path)}")
    print(f"   Subtitles: {os.path.basename(subtitle_path)}")
    
    audio_duration = get_audio_duration(audio_path)
    if audio_duration is None:
        print("\n❌ Error: Could not read audio file")
        return False
    
    # Parse subtitles
    caption_times = parse_ass_file(subtitle_path)
    if not caption_times:
        print("\n❌ Error: Could not parse subtitle file")
        return False
    
    # Calculate metrics
    first_caption_start = caption_times[0][0]
    last_caption_end = caption_times[-1][1]
    total_caption_span = last_caption_end - first_caption_start
    
    print(f"\n⏱️  Timing Analysis:")
    print(f"   Audio duration:     {audio_duration:.2f}s")
    print(f"   First caption:      {first_caption_start:.2f}s")
    print(f"   Last caption:       {last_caption_end:.2f}s")
    print(f"   Caption span:       {total_caption_span:.2f}s")
    print(f"   Caption count:      {len(caption_times)}")
    
    # Check for gaps
    gaps = []
    for i in range(len(caption_times) - 1):
        current_end = caption_times[i][1]
        next_start = caption_times[i + 1][0]
        gap = next_start - current_end
        if gap > 0.5:  # Gaps larger than 0.5s
            gaps.append((i, gap))
    
    if gaps:
        print(f"\n⚠️  Large gaps found: {len(gaps)}")
        print("   (Gaps >0.5s between captions)")
        for idx, gap in gaps[:5]:
            print(f"      Caption {idx+1}→{idx+2}: {gap:.2f}s gap")
        if len(gaps) > 5:
            print(f"      ... and {len(gaps)-5} more")
    
    # Calculate accuracy
    time_diff = abs(audio_duration - last_caption_end)
    coverage = (total_caption_span / audio_duration) * 100 if audio_duration > 0 else 0
    
    print(f"\n📊 Accuracy Metrics:")
    print(f"   Time difference:    {time_diff:.2f}s")
    print(f"   Coverage:           {coverage:.1f}%")
    
    # Verdict
    print(f"\n" + "="*60)
    if time_diff < 1.0 and coverage > 95:
        print("✅ EXCELLENT: Timing is accurate!")
        print("   Subtitles match audio duration perfectly")
        return True
    elif time_diff < 2.0 and coverage > 90:
        print("⚠️  GOOD: Minor timing differences detected")
        print("   Acceptable for most use cases")
        return True
    else:
        print("❌ POOR: Significant timing issues detected")
        print("   Subtitles may drift out of sync")
        return False

def find_video_files(directory):
    """Find audio/subtitle pairs in directory"""
    pairs = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp3'):
                audio_path = os.path.join(root, file)
                ass_path = audio_path.replace('.mp3', '.ass')
                if os.path.exists(ass_path):
                    pairs.append((audio_path, ass_path))
    return pairs

def main():
    """Main test function"""
    print("\n🎬 SUBTITLE TIMING VERIFICATION TOOL")
    print("="*60)
    
    # Check if files were provided as arguments
    if len(sys.argv) >= 3:
        audio_path = sys.argv[1]
        subtitle_path = sys.argv[2]
        
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return
        
        if not os.path.exists(subtitle_path):
            print(f"❌ Subtitle file not found: {subtitle_path}")
            return
        
        analyze_timing(audio_path, subtitle_path)
        return
    
    # Otherwise, search in current directory and Novels folder
    print("\n🔍 Searching for video files...")
    
    search_paths = [
        os.getcwd(),
        os.path.join(os.getcwd(), "Novels"),
        os.path.join(os.getcwd(), "Novels", "Active Novels"),
    ]
    
    all_pairs = []
    for search_path in search_paths:
        if os.path.exists(search_path):
            pairs = find_video_files(search_path)
            all_pairs.extend(pairs)
    
    if not all_pairs:
        print("\n❌ No audio/subtitle pairs found!")
        print("\nUsage:")
        print("  python test_subtitle_timing.py <audio.mp3> <subtitles.ass>")
        print("\nOr place this script in your project folder and run it to auto-detect files.")
        return
    
    print(f"\n✅ Found {len(all_pairs)} audio/subtitle pairs\n")
    
    # Analyze each pair
    results = []
    for i, (audio_path, subtitle_path) in enumerate(all_pairs[:5], 1):  # Limit to 5
        print(f"\n{'='*60}")
        print(f"📹 Video {i}/{min(len(all_pairs), 5)}")
        result = analyze_timing(audio_path, subtitle_path)
        results.append(result)
        
        if i < min(len(all_pairs), 5):
            input("\nPress Enter to check next video...")
    
    # Summary
    if len(all_pairs) > 5:
        print(f"\n\nℹ️  Showing first 5 of {len(all_pairs)} videos")
    
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All videos have accurate subtitle timing!")
    elif passed > total / 2:
        print("\n✅ Most videos have good timing")
    else:
        print("\n⚠️  Many videos have timing issues")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")