import sys
import os
import json
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from features.queue_manager import QueueManager

def test_error_handling():
    print("🧪 Testing Error Handling in Queue...")
    qm = QueueManager()
    
    # 1. Clear queue
    with open("processing_queue.json", "w") as f:
        json.dump([], f)
    qm.reload()
    
    # 2. Add an invalid job
    print("📝 Adding Invalid Job (non-existent EPUB)...")
    qm.add_to_queue("DOES_NOT_EXIST.epub", {"test": "FAIL"}, title="Failing Job")
    
    # 3. Try to process it using the worker logic
    from epub_project_manager import run_worker_mode
    
    print("👷 Starting worker to process failing job...")
    # This should call run_worker_mode which calls process_from_queue_job
    # which should fail because the file doesn't exist.
    
    # We'll use a timeout or similar if it hangs, but it should exit because queue becomes empty
    try:
        run_worker_mode()
    except Exception as e:
        print(f"⚠️ Caught exception in run_worker_mode: {e}")
    
    # 4. Check status
    qm.reload()
    job = qm.queue_data[0]
    print(f"📊 Job Status: {job['status']}")
    
    if job['status'] == "failed":
        print("✨ SUCCESS: Job correctly marked as 'failed' after error")
        return True
    else:
        print(f"❌ FAILURE: Job is {job['status']}, expected 'failed'")
        return False

if __name__ == "__main__":
    if test_error_handling():
        sys.exit(0)
    else:
        sys.exit(1)
