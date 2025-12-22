
import time
import os
import shutil
from pathlib import Path
from faster_whisper import WhisperModel

def benchmark_loading(model_size="small", device="cpu", compute_type="int8", root="models/test_whisper"):
    print(f"--- Benchmarking Whisper Loading ({model_size}, {device}, {compute_type}, root={root}) ---")
    
    # Ensure root exists
    os.makedirs(root, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # Simulate the logic in video_pipeline.py
        local_files_only = False
        if root and os.path.exists(root):
            if any(p.name.startswith("model") for p in Path(root).rglob("*")):
                    local_files_only = True
        
        print(f"   ℹ️  Local files only: {local_files_only}")

        if local_files_only:
                model = WhisperModel(model_size, device=device, compute_type=compute_type, cpu_threads=4, download_root=root, local_files_only=True)
        else:
                model = WhisperModel(model_size, device=device, compute_type=compute_type, cpu_threads=4, download_root=root)
                
        end_time = time.time()
        print(f"✅ Model loaded successfully in {end_time - start_time:.2f} seconds.")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")

if __name__ == "__main__":
    TEST_ROOT = "models/test_whisper"
    
    print("1. First run (should download/cache)...")
    benchmark_loading("small", "cpu", "int8", TEST_ROOT)
    
    print("\n2. Second run (should be instant from local)...")
    benchmark_loading("small", "cpu", "int8", TEST_ROOT)
