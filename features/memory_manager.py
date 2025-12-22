"""
Memory Manager - Optimize RAM usage for low-spec systems
Monitors available memory and adjusts processing strategies
"""
import os
import gc
import platform
import subprocess
from typing import Tuple, Optional

class MemoryManager:
    """Manages system memory to prevent crashes on low-ram devices"""
    
    def __init__(self, low_memory_threshold_mb: int = 2000):
        self.threshold_mb = low_memory_threshold_mb
        self.os_type = platform.system()
    
    def get_free_memory_mb(self) -> int:
        """Get available system memory in MB"""
        try:
            if self.os_type == "Windows":
                # Use wmic to get free physical memory
                cmd = "wmic os get FreePhysicalMemory /Value"
                output = subprocess.check_output(cmd, shell=True).decode().strip()
                # Output format: FreePhysicalMemory=1234567 (in KB)
                kb = int(output.split("=")[1])
                return kb // 1024
            elif self.os_type == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if "MemAvailable" in line:
                            # MemAvailable:    123456 kB
                            parts = line.split()
                            return int(parts[1]) // 1024
            return 4096  # Default fallback if detection fails
        except:
            return 4096 # Assume enough if we can't check
            
    def check_memory(self) -> Tuple[bool, str]:
        """
        Check if memory is low
        Returns: (is_low, status_message)
        """
        free_mb = self.get_free_memory_mb()
        is_low = free_mb < self.threshold_mb
        
        status = f"RAM: {free_mb}MB Free"
        if is_low:
            status += " (LOW - Optimizing)"
        return is_low, status
        
    def aggressive_cleanup(self):
        """Perform aggressive memory cleanup"""
        # Force Python Garbage Collection
        gc.collect()
        
        # On Windows, we can't easily force OS to drop caches without admin,
        # but GC is usually enough for Python apps.
        pass

    def should_reduce_concurrency(self) -> bool:
        """Return True if we should disable concurrent processing"""
        is_low, _ = self.check_memory()
        return is_low

# Global instance
memory_manager = MemoryManager()

def check_memory_status() -> str:
    """Quick check for display"""
    return memory_manager.check_memory()[1]

def optimize_memory():
    """Run optimization"""
    memory_manager.aggressive_cleanup()

def is_low_memory() -> bool:
    """Check if we are in low memory state"""
    return memory_manager.check_memory()[0]
