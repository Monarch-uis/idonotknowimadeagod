"""
Path handling utilities using pathlib.Path

Provides cross-platform path operations and validation.
"""

from pathlib import Path
from typing import Union, Optional, List
import os


PathLike = Union[str, Path]


def ensure_path(path: PathLike) -> Path:
    """
    Convert string or Path to Path object
    
    Args:
        path: String path or Path object
        
    Returns:
        Path object
    """
    if isinstance(path, str):
        return Path(path)
    return path


def ensure_dir(path: PathLike, create: bool = True) -> Path:
    """
    Ensure directory exists
    
    Args:
        path: Directory path
        create: Create directory if it doesn't exist
        
    Returns:
        Path object
    """
    dir_path = ensure_path(path)
    
    if create and not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return dir_path


def safe_path_join(*parts: PathLike) -> Path:
    """
    Safely join path components
    
    Args:
        *parts: Path components to join
        
    Returns:
        Joined Path object
    """
    if not parts:
        return Path()
    
    result = ensure_path(parts[0])
    for part in parts[1:]:
        result = result / ensure_path(part)
    
    return result


def get_file_size_mb(path: PathLike) -> float:
    """
    Get file size in megabytes
    
    Args:
        path: File path
        
    Returns:
        File size in MB
    """
    file_path = ensure_path(path)
    
    if not file_path.exists():
        return 0.0
    
    return file_path.stat().st_size / (1024 * 1024)


def find_files(
    directory: PathLike,
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    Find files matching pattern in directory
    
    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.txt", "**/*.py")
        recursive: Search recursively
        
    Returns:
        List of matching Path objects
    """
    dir_path = ensure_path(directory)
    
    if not dir_path.exists():
        return []
    
    if recursive and not pattern.startswith("**"):
        pattern = f"**/{pattern}"
    
    if recursive:
        return list(dir_path.glob(pattern))
    else:
        return list(dir_path.glob(pattern))


def normalize_path(path: PathLike) -> Path:
    """
    Normalize path for cross-platform compatibility
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized Path object
    """
    return ensure_path(path).resolve()


def get_relative_path(path: PathLike, base: PathLike) -> Path:
    """
    Get relative path from base
    
    Args:
        path: Target path
        base: Base path
        
    Returns:
        Relative Path object
    """
    path_obj = ensure_path(path).resolve()
    base_obj = ensure_path(base).resolve()
    
    try:
        return path_obj.relative_to(base_obj)
    except ValueError:
        # Paths are not relative, return absolute path
        return path_obj


def safe_remove(path: PathLike, missing_ok: bool = True) -> bool:
    """
    Safely remove a file
    
    Args:
        path: File path to remove
        missing_ok: Don't raise error if file doesn't exist
        
    Returns:
        True if file was removed, False otherwise
    """
    file_path = ensure_path(path)
    
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        elif not missing_ok:
            raise FileNotFoundError(f"File not found: {file_path}")
        return False
    except Exception:
        if not missing_ok:
            raise
        return False


def copy_file(src: PathLike, dst: PathLike, create_dirs: bool = True) -> Path:
    """
    Copy file from src to dst
    
    Args:
        src: Source file path
        dst: Destination file path
        create_dirs: Create destination directories if needed
        
    Returns:
        Destination Path object
    """
    import shutil
    
    src_path = ensure_path(src)
    dst_path = ensure_path(dst)
    
    if create_dirs:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(src_path, dst_path)
    return dst_path


def move_file(src: PathLike, dst: PathLike, create_dirs: bool = True) -> Path:
    """
    Move file from src to dst
    
    Args:
        src: Source file path
        dst: Destination file path
        create_dirs: Create destination directories if needed
        
    Returns:
        Destination Path object
    """
    import shutil
    
    src_path = ensure_path(src)
    dst_path = ensure_path(dst)
    
    if create_dirs:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.move(str(src_path), str(dst_path))
    return dst_path


def get_temp_dir(prefix: str = "epub_temp_") -> Path:
    """
    Create a temporary directory
    
    Args:
        prefix: Directory name prefix
        
    Returns:
        Path to temporary directory
    """
    import tempfile
    
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    return temp_dir


def validate_file_path(path: PathLike, must_exist: bool = False, extensions: Optional[List[str]] = None) -> bool:
    """
    Validate file path
    
    Args:
        path: File path to validate
        must_exist: File must exist
        extensions: List of valid extensions (e.g., ['.txt', '.md'])
        
    Returns:
        True if valid, False otherwise
    """
    file_path = ensure_path(path)
    
    if must_exist and not file_path.exists():
        return False
    
    if extensions:
        if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
            return False
    
    return True


# Backward compatibility helpers
def to_str(path: PathLike) -> str:
    """Convert Path to string"""
    return str(ensure_path(path))


def from_str(path_str: str) -> Path:
    """Convert string to Path"""
    return Path(path_str)
