import sys
import os
import json
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from features.queue_manager import QueueManager

def test_job_order():
    print("🧪 Testing Job Processing Order...")
    qm = QueueManager()
    
    # 1. Clear queue
    with open("processing_queue.json", "w") as f:
        json.dump([], f)
    qm.reload()
    
    # 2. Add two jobs
    print("📝 Adding Job A...")
    qm.add_to_queue("_NEW_EPUBS_HERE/test_novel.epub", {"test": "A"}, title="Job A")
    time.sleep(1.1)
    print("📝 Adding Job B...")
    qm.add_to_queue("_NEW_EPUBS_HERE/test_novel.epub", {"test": "B"}, title="Job B")
    
    # 3. Claim job 1
    job1 = qm.claim_next_job()
    print(f"👷 Worker 1 claimed: {job1['title']} (Expected: Job A)")
    
    # 4. Claim job 2
    job2 = qm.claim_next_job()
    print(f"👷 Worker 2 claimed: {job2['title']} (Expected: Job B)")
    
    if job1['title'] == "Job A" and job2['title'] == "Job B":
        print("✨ SUCCESS: Jobs processed in correct FIFO order")
        return True
    else:
        print("❌ FAILURE: Incorrect processing order")
        return False

if __name__ == "__main__":
    if test_job_order():
        sys.exit(0)
    else:
        sys.exit(1)
