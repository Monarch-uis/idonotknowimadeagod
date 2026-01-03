import sys
import os
import json
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from features.queue_manager import QueueManager

def test_stale_job_recovery():
    print("🧪 Testing Stale Job Recovery...")
    qm = QueueManager()
    
    # Manually inject a stale job
    stale_job = {
        "id": "STALE_TEST_999",
        "path": "_NEW_EPUBS_HERE/test_novel.epub",
        "title": "Stale Test Book",
        "status": "processing",
        "worker_pid": 999999, # Highly unlikely to exist
        "added_at": "2026-01-01T12:00:00"
    }
    
    # We need to save this to the file
    with open("processing_queue.json", "r") as f:
        queue = json.load(f)
    
    queue.append(stale_job)
    
    with open("processing_queue.json", "w") as f:
        json.dump(queue, f, indent=2)
    
    print("✅ Injected stale job (PID 999999)")
    
    # Now claim a job - this should trigger cleanup
    # We call reload first to be sure
    qm.reload()
    job = qm.claim_next_job()
    
    # Reload and check the stale job status
    qm.reload()
    found = False
    for j in qm.queue_data:
        if j["id"] == "STALE_TEST_999":
            print(f"📊 Stale job status after cleanup: {j['status']} (PID: {j.get('worker_pid')})")
            if j["status"] == "processing" and j.get("worker_pid") == os.getpid():
                print("✨ SUCCESS: Stale job was RE-CLAIMED by current process!")
            elif j["status"] == "pending":
                print("✨ SUCCESS: Stale job recovered to 'pending'")
            else:
                print(f"❌ FAILURE: Unexpected state!")
            found = True
            break
    
    if not found:
        print("❌ FAILURE: Stale job disappeared!")

if __name__ == "__main__":
    test_stale_job_recovery()
