"""File hashing for duplicate detection."""

import logging
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.file_utils import get_file_hash, get_file_size


class FileHasher:
    """Handle file hashing operations for duplicate detection."""
    
    def __init__(self, config, logger=None):
        """
        Initialize file hasher.
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.algorithm = config.get('advanced.hash_algorithm', 'md5')
        self.chunk_size = config.get('advanced.chunk_size', 8192)
        self.max_workers = config.get('advanced.max_workers', 4)
    
    def hash_file(self, file_path: Path) -> Optional[str]:
        """
        Calculate hash for a single file.
        
        Args:
            file_path: Path to file
        
        Returns:
            File hash or None if error
        """
        return get_file_hash(file_path, self.algorithm, self.chunk_size)
    
    def hash_files(self, file_paths: list) -> Dict[Path, str]:
        """
        Calculate hashes for multiple files in parallel.
        
        Args:
            file_paths: List of file paths
        
        Returns:
            Dictionary mapping file path to hash
        """
        hash_map = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all hash jobs
            future_to_file = {
                executor.submit(self.hash_file, file_path): file_path
                for file_path in file_paths
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    hash_value = future.result()
                    if hash_value:
                        hash_map[file_path] = hash_value
                except Exception as e:
                    self.logger.error(f"Error hashing {file_path}: {e}")
        
        return hash_map
    
    def find_hash_duplicates(self, files: list) -> Dict[str, list]:
        """
        Find duplicate files based on hash.
        
        Args:
            files: List of file paths
        
        Returns:
            Dictionary mapping hash to list of duplicate file paths
        """
        self.logger.info(f"Hashing {len(files)} files for duplicate detection...")
        hash_map = self.hash_files(files)
        
        # Group files by hash
        hash_to_files = {}
        for file_path, file_hash in hash_map.items():
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(file_path)
        
        # Find duplicates (hash values with multiple files)
        duplicates = {
            file_hash: files for file_hash, files in hash_to_files.items()
            if len(files) > 1
        }
        
        self.logger.info(f"Found {len(duplicates)} groups of duplicate files")
        return duplicates
    
    def get_file_signature(self, file_path: Path) -> Dict:
        """
        Get file signature (hash + metadata).
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary with file signature
        """
        return {
            'path': file_path,
            'hash': self.hash_file(file_path),
            'size': get_file_size(file_path)
        }
