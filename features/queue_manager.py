"""
Queue Manager - Handle batch processing of multiple books
"""
import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Initialize logger for this module
logger = logging.getLogger(__name__)

QUEUE_FILE = "processing_queue.json"

class QueueManager:
    """Manages the processing queue"""
    
    def __init__(self):
        self.queue_data = self.reload()
        
    def reload(self) -> List[Dict]:
        """Reload queue from disk to ensure we have the latest state"""
        if os.path.exists(QUEUE_FILE):
            try:
                # Use a temporary read to avoid race conditions with open()
                with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queue_data = data
                    return data
            except Exception as e:
                logger.error(f"Failed to reload queue: {e}")
                if not hasattr(self, 'queue_data'):
                    self.queue_data = []
                return self.queue_data
        self.queue_data = []
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

    def save_queue(self, existing_lock=None):
        """Save queue to disk with atomic write and file locking"""
        import tempfile
        import time
        
        lock_f = existing_lock if existing_lock else self._get_lock()
        if not lock_f:
            logger.error("❌ Could not acquire queue lock for saving.")
            return False
            
        try:
            # Write to temp file first to ensure atomic updates
            dir_name = os.path.dirname(os.path.abspath(QUEUE_FILE)) or '.'
            fd, temp_path = tempfile.mkstemp(suffix='.json', dir=dir_name)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.queue_data, f, indent=2, ensure_ascii=False)
                # Atomic rename
                os.replace(temp_path, QUEUE_FILE)
                return True
            except Exception as e:
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass
                logger.error(f"Queue write error: {e}")
                return False
        except Exception as e:
            logger.error(f"Failed to save queue: {e}")
            return False
        finally:
            if lock_f and not existing_lock:
                self._release_lock(lock_f)

    def add_to_queue(self, epub_path: str, settings: Dict, title: str = None, original_title: str = None):
        """Add a job to the queue with forced reload and locking"""
        lock_f = self._get_lock()
        if not lock_f:
            logger.error("Failed to acquire lock for adding to queue")
            return None
            
        try:
            self.reload() # Get latest state before modifying
            job = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "path": epub_path,
                "title": title if title else os.path.basename(epub_path),
                "original_title": original_title if original_title else "",
                "settings": settings,
                "status": "pending",
                "added_at": datetime.now().isoformat()
            }
            self.queue_data.append(job)
            self.save_queue(existing_lock=lock_f)
            return job
        finally:
            self._release_lock(lock_f)

    def get_pending_jobs(self) -> List[Dict]:
        """Get all pending jobs (reloads first)"""
        self.reload()
        return [j for j in self.queue_data if j["status"] == "pending"]

    def mark_completed(self, job_id: str, success: bool = True):
        """Mark a job as completed with locking and reload"""
        lock_f = self._get_lock()
        if not lock_f: return
        
        try:
            self.reload()
            for job in self.queue_data:
                if job["id"] == job_id:
                    job["status"] = "completed" if success else "failed"
                    job["completed_at"] = datetime.now().isoformat()
                    self.save_queue(existing_lock=lock_f)
                    break
        finally:
            self._release_lock(lock_f)

    def remove_job(self, index: int) -> bool:
        """Remove job by index with locking and reload"""
        lock_f = self._get_lock()
        if not lock_f: return False
        
        try:
            self.reload()
            if 0 <= index < len(self.queue_data):
                self.queue_data.pop(index)
                self.save_queue(existing_lock=lock_f)
                return True
            return False
        finally:
            self._release_lock(lock_f)

    def clear_completed(self):
        """Remove all completed jobs with locking and reload"""
        lock_f = self._get_lock()
        if not lock_f: return
        
        try:
            self.reload()
            self.queue_data = [j for j in self.queue_data if j["status"] == "pending"]
            self.save_queue(existing_lock=lock_f)
        finally:
            self._release_lock(lock_f)

    def clear_pending(self):
        """Remove all pending jobs with locking and reload (includes stale jobs)"""
        lock_f = self._get_lock()
        if not lock_f: return 0
        
        try:
            self.reload()
            # First, bring stale jobs back to 'pending' so we can clear them
            self._cleanup_stale_jobs(existing_lock=lock_f)
            
            original_count = len(self.queue_data)
            # Now clear all pending (which now includes rescued stale jobs)
            self.queue_data = [j for j in self.queue_data if j["status"] != "pending"]
            cleared_count = original_count - len(self.queue_data)
            self.save_queue(existing_lock=lock_f)
            return cleared_count
        finally:
            self._release_lock(lock_f)

    def claim_next_job(self) -> Optional[Dict]:
        """Atomically find and claim the next pending job while holding a lock."""
        import time
        lock_f = self._get_lock()
        if not lock_f:
            return None
            
        try:
            # Re-load data to ensure we have the latest state while locked
            self.reload()
            
            # CRITICAL: Automatically recover stale "processing" jobs before looking for new ones
            # This ensures that worker crashes don't leave the queue in a "jammed" state
            self._cleanup_stale_jobs(existing_lock=lock_f)
            
            for job in self.queue_data:
                if job["status"] == "pending":
                    job["status"] = "processing"
                    job["started_at"] = datetime.now().isoformat()
                    # Assign a temporary worker ID (PID)
                    job["worker_pid"] = os.getpid()
                    
                    self.save_queue(existing_lock=lock_f)
                    return job
            return None
        finally:
            self._release_lock(lock_f)

    def _cleanup_stale_jobs(self, existing_lock=None):
        """Internal helper to reset jobs that claim to be processing but have no active PID"""
        worker_pids = self.get_worker_pids()
        current_pid = os.getpid()
        modified = False
        
        for job in self.queue_data:
            if job["status"] == "processing":
                job_pid = job.get("worker_pid")
                # If the worker PID is not in our active process list and it's not US
                if not job_pid or (job_pid not in worker_pids and job_pid != current_pid):
                    logger.warning(f"Restoring stale job: {job.get('title', 'Unknown')} (PID {job_pid} not found)")
                    job["status"] = "pending" # Reset to pending for retry
                    job["worker_pid"] = None
                    job["error"] = f"Recovery: Previous worker (PID {job_pid}) crashed"
                    modified = True
        
        if modified:
            self.save_queue(existing_lock=existing_lock)
        return modified

    def get_queue_summary(self) -> Dict:
        """Get summary of queue status (reloads first)"""
        self.reload()
        pending = len([j for j in self.queue_data if j["status"] == "pending"])
        processing = len([j for j in self.queue_data if j["status"] == "processing"])
        completed = len([j for j in self.queue_data if j["status"] == "completed"])
        failed = len([j for j in self.queue_data if j["status"] == "failed"])
        return {
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "total": len(self.queue_data)
        }

    def get_worker_pids(self) -> List[int]:
        """Get list of active worker PIDs"""
        import subprocess
        import os
        
        pids = []
        try:
            current_pid = os.getpid()
            cmd = f"ps aux | grep 'epub_project_manager.py --worker' | grep -v grep"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if not line.strip(): continue
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        if pid != current_pid:
                            pids.append(pid)
                    except ValueError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to check process list: {e}")
            
        return pids

    def is_worker_running(self) -> bool:
        """Check if a worker process is currently running on the system"""
        # 1. Check OS process list first (most reliable)
        worker_pids = self.get_worker_pids()
        worker_process_found = len(worker_pids) > 0

        # 2. Check JSON state and sync
        stale_jobs_found = False
        for job in self.queue_data:
            if job["status"] == "processing":
                job_pid = job.get("worker_pid")
                # If JSON says processing but no worker process exists for THIS PID, it's stale
                if not job_pid or job_pid not in worker_pids:
                    logger.warning(f"Found stale job in queue: {job.get('title', 'Unknown')} (PID {job_pid}). Resetting to failed.")
                    job["status"] = "failed"
                    job["error"] = f"Worker (PID {job_pid}) terminated unexpectedly (stale job detected)"
                    stale_jobs_found = True
        
        if stale_jobs_found:
            self.save_queue()
            
        return worker_process_found

    def spawn_worker_terminal(self) -> bool:
        """Spawn a new terminal window running the worker process"""
        import subprocess
        import sys
        import shutil
        
        # Get the path to the main script
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        worker_script = os.path.join(script_dir, "epub_project_manager.py")
        python_exe = sys.executable
        
        worker_cmd = f'cd "{script_dir}" && "{python_exe}" "{worker_script}" --worker'
        
        # Try different terminal emulators
        terminals = [
            # GNOME Terminal
            ["gnome-terminal", "--", "bash", "-c", f'{worker_cmd}; echo ""; echo "Queue complete. Press Enter to close."; read'],
            # Konsole (KDE)
            ["konsole", "-e", "bash", "-c", f'{worker_cmd}; echo ""; echo "Queue complete. Press Enter to close."; read'],
            # XTerm (fallback)
            ["xterm", "-e", f'{worker_cmd}; echo "Queue complete. Press Enter to close."; read'],
            # XFCE Terminal
            ["xfce4-terminal", "-e", f'bash -c \'{worker_cmd}; echo "Queue complete. Press Enter."; read\''],
        ]
        
        for term_cmd in terminals:
            if shutil.which(term_cmd[0]):
                try:
                    subprocess.Popen(term_cmd, start_new_session=True)
                    print(f"   🚀 Worker terminal spawned ({term_cmd[0]})")
                    return True
                except Exception as e:
                    continue
        
        print("   ⚠️  Could not spawn worker terminal. Run manually with: --worker")
        return False
