"""
Checkpoint Manager - Save and resume processing state
Allows recovery from crashes or interruptions
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


CHECKPOINT_FILE = "processing_checkpoint.json"


class CheckpointManager:
    """Manages processing checkpoints for crash recovery"""
    
    def __init__(self):
        self.checkpoint_data = self._load_checkpoint()
    
    def _load_checkpoint(self) -> Dict[str, Any]:
        """Load existing checkpoint if available"""
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_checkpoint(self, book_title: str, batch_info: Dict[str, Any], progress: Dict[str, Any]):
        """
        Save current processing state
        
        Args:
            book_title: Title of the book being processed
            batch_info: Current batch information
            progress: Processing progress data
        """
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "book_title": book_title,
            "batch_info": batch_info,
            "progress": progress,
            "completed_chapters": progress.get("completed_chapters", []),
            "current_batch": batch_info.get("batch_number", 0),
            "total_batches": batch_info.get("total_batches", 0)
        }
        
        try:
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
    
    def has_checkpoint(self) -> bool:
        """Check if there's a valid checkpoint"""
        return bool(self.checkpoint_data) and "book_title" in self.checkpoint_data
    
    def get_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Get the current checkpoint data"""
        return self.checkpoint_data if self.has_checkpoint() else None
    
    def clear_checkpoint(self):
        """Remove checkpoint file after successful completion"""
        if os.path.exists(CHECKPOINT_FILE):
            try:
                os.remove(CHECKPOINT_FILE)
                self.checkpoint_data = {}
            except Exception as e:
                print(f"⚠️  Failed to clear checkpoint: {e}")
    
    def display_checkpoint_info(self):
        """Display information about existing checkpoint"""
        if not self.has_checkpoint():
            return
        
        cp = self.checkpoint_data
        print("\n" + "=" * 60)
        print("📌 CHECKPOINT FOUND")
        print("=" * 60)
        print(f"\n📖 Book: {cp.get('book_title', 'Unknown')}")
        print(f"⏰ Saved: {cp.get('timestamp', 'Unknown')}")
        print(f"📊 Progress: Batch {cp.get('current_batch', 0)}/{cp.get('total_batches', 0)}")
        
        completed = cp.get('completed_chapters', [])
        if completed:
            print(f"✅ Completed Chapters: {len(completed)}")
        
        print("=" * 60)
    
    def ask_resume(self) -> bool:
        """Ask user if they want to resume from checkpoint"""
        if not self.has_checkpoint():
            return False
            
        choice = input(f"\n   {CP('👉 Resume from checkpoint?', 'cyan')} (y/n, default y): ").strip().lower()
        
        if choice == 'n':
            print("   ℹ️  Starting fresh (checkpoint will be overwritten)")
            self.clear_checkpoint()
            return False
        
        print(f"   {CP('✅ Resuming from checkpoint...', 'green')}")
        return True


def save_progress_checkpoint(book_title: str, batch_num: int, total_batches: int, completed_chapters: list):
    """Quick function to save a checkpoint"""
    manager = CheckpointManager()
    manager.save_checkpoint(
        book_title=book_title,
        batch_info={"batch_number": batch_num, "total_batches": total_batches},
        progress={"completed_chapters": completed_chapters}
    )


def get_checkpoint_if_exists() -> Optional[Dict[str, Any]]:
    """Get checkpoint data WITHOUT prompting (use for UI indicators)"""
    manager = CheckpointManager()
    if manager.has_checkpoint():
        return manager.get_checkpoint()
    return None

def ask_to_resume_checkpoint() -> Optional[Dict[str, Any]]:
    """Prompt user and return checkpoint if they want to resume"""
    manager = CheckpointManager()
    if manager.ask_resume():
        return manager.get_checkpoint()
    return None


if __name__ == "__main__":
    from core.utils import CP # Import for test mode
    # Test checkpoint system
    manager = CheckpointManager()
    # ... rest of tests
