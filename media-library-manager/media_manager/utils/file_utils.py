"""File utility functions."""

import os
import hashlib
from pathlib import Path
from typing import List, Optional


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except (OSError, IOError):
        return 0


def get_file_hash(file_path: Path, algorithm: str = "md5", chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate file hash.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha256)
        chunk_size: Size of chunks to read
    
    Returns:
        Hex digest of file hash or None if error
    """
    hash_alg = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_alg.update(chunk)
        return hash_alg.hexdigest()
    except (OSError, IOError) as e:
        print(f"Error hashing file {file_path}: {e}")
        return None


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Cleaned filename
    """
    # Remove invalid characters for Windows and Unix
    invalid_chars = '<>:"/\\|?*'
    cleaned = filename
    
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip(' .')
    
    return cleaned


def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def get_file_extension(file_path: Path) -> str:
    """Get file extension (including leading dot)."""
    return file_path.suffix.lower()


def is_media_file(file_path: Path, extensions: List[str]) -> bool:
    """Check if file is a supported media file."""
    return get_file_extension(file_path) in [ext.lower() for ext in extensions]


def get_directory_size(directory: Path) -> int:
    """Calculate total size of all files in directory."""
    total_size = 0
    
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except (OSError, PermissionError):
        pass
    
    return total_size


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_file_mtime(file_path: Path) -> float:
    """Get file modification time."""
    try:
        return file_path.stat().st_mtime
    except (OSError, IOError):
        return 0


def move_file_cross_device(source: Path, destination: Path) -> bool:
    """
    Move a file, handling cross-device moves safely.
    
    On Linux/Unix, rename() only works within the same filesystem.
    For cross-device moves, this function copies then deletes the original.
    
    Args:
        source: Source file path
        destination: Destination file path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Try rename first (fast for same filesystem)
        try:
            source.rename(destination)
            return True
        except OSError as e:
            # If rename fails with cross-device error, use copy+delete
            if e.errno == 18:  # Invalid cross-device link (Errno 18)
                # Copy file
                import shutil
                shutil.copy2(source, destination)
                
                # Delete original after successful copy
                source.unlink()
                return True
            else:
                # Re-raise if it's a different error
                raise
    
    except Exception as e:
        # Log the error but return False
        import sys
        print(f"Error moving file {source} to {destination}: {e}", file=sys.stderr)
        return False