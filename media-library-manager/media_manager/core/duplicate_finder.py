"""Duplicate detection and removal logic."""

import logging
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from ..utils.file_utils import get_file_size, format_file_size


class DuplicateFinder:
    """Find and manage duplicate files."""
    
    def __init__(self, config, logger=None):
        """
        Initialize duplicate finder.
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.keep_criteria = config.get('duplicate_detection.keep_criteria', 'highest_quality')
    
    def select_file_to_keep(self, file_paths: List[Path]) -> Path:
        """
        Select which file to keep from a list of duplicates.
        
        Args:
            file_paths: List of duplicate file paths
        
        Returns:
            Path to file that should be kept
        """
        if not file_paths:
            return None
        
        if len(file_paths) == 1:
            return file_paths[0]
        
        # Get file information
        file_info = []
        for file_path in file_paths:
            try:
                size = get_file_size(file_path)
                mtime = file_path.stat().st_mtime
                file_info.append({
                    'path': file_path,
                    'size': size,
                    'mtime': mtime
                })
            except (OSError, IOError) as e:
                self.logger.error(f"Error getting info for {file_path}: {e}")
        
        if not file_info:
            return file_paths[0]
        
        # Apply keep criteria
        if self.keep_criteria == 'highest_quality':
            # Keep largest file (assumes larger = higher quality)
            file_info.sort(key=lambda x: x['size'], reverse=True)
        elif self.keep_criteria == 'smallest':
            file_info.sort(key=lambda x: x['size'])
        elif self.keep_criteria == 'oldest':
            file_info.sort(key=lambda x: x['mtime'])
        elif self.keep_criteria == 'newest':
            file_info.sort(key=lambda x: x['mtime'], reverse=True)
        else:
            # Default: keep first one
            return file_info[0]['path']
        
        return file_info[0]['path']
    
    def organize_duplicates(self, duplicates: Dict[str, List[Path]]) -> Dict[str, Dict]:
        """
        Organize duplicate groups and select files to keep.
        
        Args:
            duplicates: Dictionary mapping hash to list of file paths
        
        Returns:
            Dictionary with keep and remove information
        """
        organized = {}
        
        for file_hash, file_paths in duplicates.items():
            if len(file_paths) < 2:
                continue
            
            keep_file = self.select_file_to_keep(file_paths)
            remove_files = [f for f in file_paths if f != keep_file]
            
            organized[file_hash] = {
                'keep': keep_file,
                'remove': remove_files,
                'count': len(file_paths)
            }
        
        return organized
    
    def calculate_space_savings(self, duplicates: Dict[str, Dict]) -> int:
        """
        Calculate how much space would be saved by removing duplicates.
        
        Args:
            duplicates: Organized duplicate information
        
        Returns:
            Total bytes that would be saved
        """
        total_size = 0
        
        for info in duplicates.values():
            for file_path in info['remove']:
                total_size += get_file_size(file_path)
        
        return total_size
    
    def format_duplicate_report(self, duplicates: Dict[str, List[Path]]) -> str:
        """
        Format duplicate information for display (concise format).
        
        Args:
            duplicates: Dictionary of duplicate groups
        
        Returns:
            Formatted report string
        """
        report = []
        report.append(f"\nFound {len(duplicates)} groups of duplicate files\n")
        
        organized = self.organize_duplicates(duplicates)
        total_space = self.calculate_space_savings(organized)
        total_to_remove = sum(len(info['remove']) for info in organized.values())
        
        for i, (file_hash, info) in enumerate(organized.items(), 1):
            group_space = sum(get_file_size(f) for f in info['remove'])
            
            # Concise format: show keep file and count of duplicates
            report.append(f"Group {i}: {info['keep'].name} ({info['count']} copies, {format_file_size(group_space)} to save)")
            
            # Only show remove list if there are few files
            if len(info['remove']) <= 3:
                for file_path in info['remove']:
                    report.append(f"  - {file_path.name}")
        
        report.append(f"\n{'='*60}")
        report.append(f"Total: {total_to_remove} duplicate files to remove")
        report.append(f"Space savings: {format_file_size(total_space)}")
        report.append(f"{'='*60}\n")
        
        return '\n'.join(report)
