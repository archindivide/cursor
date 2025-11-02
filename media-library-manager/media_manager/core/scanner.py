"""File system scanner for media files."""

import logging
from pathlib import Path
from typing import List, Set, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from ..utils.file_utils import is_media_file, get_file_extension


class MediaScanner:
    """Scanner for discovering media files in directories."""
    
    def __init__(self, config, logger=None):
        """
        Initialize media scanner.
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.extensions = config.get_all_extensions()
        self.ignore_patterns = config.get('advanced.ignore_patterns', [])
    
    def scan_directory(self, directory: str, progress_bar: Optional[tqdm] = None) -> List[Path]:
        """
        Scan directory for media files.
        
        Args:
            directory: Directory path to scan
            progress_bar: Optional progress bar to update
        
        Returns:
            List of media file paths
        """
        media_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            self.logger.warning(f"Directory does not exist: {directory}")
            return media_files
        
        self.logger.info(f"Scanning directory: {directory}")
        
        try:
            # First, collect all files for progress tracking
            all_files = list(directory_path.rglob('*'))
            
            for file_path in all_files:
                if progress_bar:
                    progress_bar.set_description(f"Scanning: {file_path.name[:40]}")
                    progress_bar.update(1)
                
                if not file_path.is_file():
                    continue
                
                # Check if file matches ignore patterns
                if self._should_ignore(file_path):
                    continue
                
                # Check if file is a supported media file
                if is_media_file(file_path, self.extensions):
                    media_files.append(file_path)
            
            if progress_bar:
                progress_bar.close()
        
        except (OSError, PermissionError) as e:
            self.logger.error(f"Error scanning {directory}: {e}")
            if progress_bar:
                progress_bar.close()
        
        self.logger.info(f"Found {len(media_files)} media files in {directory}")
        return media_files
    
    def scan_all_media_paths(self) -> Dict[str, List[Path]]:
        """
        Scan all configured media paths.
        
        Returns:
            Dictionary mapping media type to list of file paths
        """
        all_files = {
            'movies': [],
            'tv_shows': [],
            'music': [],
            'photos': []
        }
        
        media_paths = self.config.get_media_paths()
        
        for media_type, paths in media_paths.items():
            for path in paths:
                files = self.scan_directory(path)
                all_files[media_type].extend(files)
        
        return all_files
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored based on patterns."""
        file_str = str(file_path)
        
        for pattern in self.ignore_patterns:
            # Simple pattern matching (can be enhanced with fnmatch)
            if pattern in file_str:
                return True
        
        return False
    
    def get_file_info(self, file_path: Path) -> Dict:
        """
        Get basic information about a media file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary with file information
        """
        try:
            stat = file_path.stat()
            return {
                'path': file_path,
                'name': file_path.name,
                'size': stat.st_size,
                'extension': get_file_extension(file_path),
                'mtime': stat.st_mtime,
                'media_type': self._detect_media_type(file_path)
            }
        except (OSError, IOError) as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def _detect_media_type(self, file_path: Path) -> str:
        """Detect media type based on extension."""
        extension = get_file_extension(file_path).lower()
        
        video_exts = self.config.get('advanced.video_extensions', [])
        audio_exts = self.config.get('advanced.audio_extensions', [])
        photo_exts = self.config.get('advanced.photo_extensions', [])
        
        if extension in [ext.lower() for ext in video_exts]:
            return 'video'
        elif extension in [ext.lower() for ext in audio_exts]:
            return 'audio'
        elif extension in [ext.lower() for ext in photo_exts]:
            return 'photo'
        else:
            return 'unknown'
