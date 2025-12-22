"""
Queue Manager - Handle batch processing of multiple books
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

QUEUE_FILE = "processing_queue.json"

class QueueManager:
    """Manages the processing queue"""
    
    def __init__(self):
        self.queue_data = self._load_queue()
        
    def _load_queue(self) -> List[Dict]:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def _get_lock(self, timeout=10):
        """Get a platform-specific file lock"""
        import time
        lock_file = QUEUE_FILE + ".lock"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if os.name == 'nt':  # Windows
                    import msvcrt
                    # Open or create lock file and lock it
                    f = open(lock_file, 'wb')
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    return f
                else:  # Unix/Mac
                    import fcntl
                    f = open(lock_file, 'wb')
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return f
            except (IOError, OSError):
                time.sleep(0.1)
                continue
        return None

    def _release_lock(self, lock_f):
        """Release the file lock"""
        if lock_f:
            try:
                if os.name == 'nt':
                    import msvcrt
                    lock_f.seek(0)
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_f, fcntl.LOCK_UN)
            finally:
                lock_f.close()

    def save_queue(self):
        """Save queue to disk with atomic write and file locking"""
        import tempfile
        import time
        
        lock_f = self._get_lock()
        if not lock_f:
            print("⚠️  Could not acquire queue lock, retrying once...")
            time.sleep(1)
            lock_f = self._get_lock()
            
        try:
            # Write to temp file first
            dir_name = os.path.dirname(os.path.abspath(QUEUE_FILE))
            fd, temp_path = tempfile.mkstemp(suffix='.json', dir=dir_name)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.queue_data, f, indent=2)
                # Atomic rename
                os.replace(temp_path, QUEUE_FILE)
            except Exception as e:
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass
                print(f"⚠️  Queue write error: {e}")
                raise
        except Exception as e:
            print(f"⚠️  Failed to save queue: {e}")
        finally:
            if lock_f:
                self._release_lock(lock_f)

    def add_to_queue(self, epub_path: str, settings: Dict):
        """Add a job to the queue"""
        job = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "path": epub_path,
            "title": os.path.basename(epub_path),
            "settings": settings,
            "status": "pending",
            "added_at": datetime.now().isoformat()
        }
        self.queue_data.append(job)
        self.save_queue()
        return job

    def get_pending_jobs(self) -> List[Dict]:
        """Get all pending jobs"""
        return [j for j in self.queue_data if j["status"] == "pending"]

    def mark_completed(self, job_id: str, success: bool = True):
        """Mark a job as completed"""
        for job in self.queue_data:
            if job["id"] == job_id:
                job["status"] = "completed" if success else "failed"
                job["completed_at"] = datetime.now().isoformat()
                self.save_queue()
                break

    def remove_job(self, index: int) -> bool:
        """Remove job by index"""
        if 0 <= index < len(self.queue_data):
            self.queue_data.pop(index)
            self.save_queue()
            return True
        return False

    def clear_completed(self):
        """Remove all completed jobs"""
        self.queue_data = [j for j in self.queue_data if j["status"] == "pending"]
        self.save_queue()
