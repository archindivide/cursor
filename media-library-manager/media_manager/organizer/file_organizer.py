"""File organization and naming standardization."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from ..utils.file_utils import clean_filename, get_file_extension, get_file_mtime


class FileOrganizer:
    """Organize and standardize file names and directory structure."""
    
    def __init__(self, config, logger=None):
        """
        Initialize file organizer.
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing/replacing problematic characters.
        
        Args:
            filename: Original filename
        
        Returns:
            Cleaned filename
        """
        # Remove common unwanted prefixes/suffixes
        filename = filename.strip()
        
        # Common cleanup patterns
        patterns = [
            (r'^\[.*?\]', ''),  # Remove brackets at start
            (r'\{.*?\}', ''),   # Remove curly braces
            # Don't remove parentheses yet - they contain year info
        ]
        
        for pattern, replacement in patterns:
            filename = re.sub(pattern, replacement, filename, flags=re.IGNORECASE)
        
        # Clean using existing utility
        filename = clean_filename(filename)
        
        # Normalize multiple spaces/underscores/dots
        filename = re.sub(r'[_\s\.]+', ' ', filename)
        filename = re.sub(r'[\.\s]+$', '', filename)  # Remove trailing dots/spaces
        
        return filename.strip()
    
    def extract_pattern_info(self, filename: str) -> Dict[str, str]:
        """
        Extract information from filename patterns (movies, TV shows).
        
        Args:
            filename: Filename to analyze
        
        Returns:
            Dictionary with extracted information
        """
        info = {
            'title': '',
            'year': '',
            'season': '',
            'episode': '',
            'quality': '',
            'codec': ''
        }
        
        # TV show pattern: Title.S##E## or Title S##E## or Title - S##E##
        tv_patterns = [
            r'^(.+?)[\.\s]S(\d+)E(\d+)',  # Title.S01E01 or Title S01E01
            r'^(.+?)\s*-\s*S(\d+)E(\d+)',  # Title - S01E01
        ]
        
        for tv_pattern in tv_patterns:
            match = re.match(tv_pattern, filename, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up title if it ends with dash
                title = re.sub(r'\s*-\s*$', '', title)
                info['title'] = title
                info['season'] = match.group(2)
                info['episode'] = match.group(3)
                break
        else:
            # If no TV pattern found, try movie patterns
            # Movie pattern: Title (Year) or Title.Year
            movie_pattern = r'^(.+?)\s*\((\d{4})\)'
            match = re.match(movie_pattern, filename, re.IGNORECASE)
            if match:
                info['title'] = match.group(1).strip()
                info['year'] = match.group(2)
            else:
                # Try pattern without parentheses: Title.Year
                movie_pattern2 = r'^(.+?)\.(\d{4})'
                match = re.match(movie_pattern2, filename, re.IGNORECASE)
                if match:
                    info['title'] = match.group(1).strip()
                    info['year'] = match.group(2)
                else:
                    # Try to find year anywhere in filename (but not in quality like 1080p)
                    # Only match years in a reasonable range (1880-2030)
                    year_match = re.search(r'(?<!\d)(19[89]\d|20[0-2]\d|2030)(?!\d)', filename)
                    if year_match:
                        info['year'] = year_match.group(1)
                        # Extract title before year
                        title_part = filename[:year_match.start()].strip()
                        if title_part:
                            info['title'] = title_part
        
        # Quality/resolution detection
        quality_patterns = [
            (r'2160p|4K|UHD', '4K'),
            (r'1080p|FHD|FullHD', '1080p'),
            (r'720p|HD', '720p'),
            (r'480p|SD', '480p'),
        ]
        
        for pattern, quality in quality_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                info['quality'] = quality
                break
        
        # Codec detection
        codec_patterns = [
            (r'\bHEVC\b|\bx265\b|H\.265', 'HEVC'),
            (r'\bAVC\b|\bx264\b|H\.264', 'AVC'),
            (r'\bXVID\b|DivX', 'XVID'),
        ]
        
        for pattern, codec in codec_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                info['codec'] = codec
                break
        
        return info
    
    def _detect_media_type(self, file_path: Path) -> str:
        """
        Detect media type based on filename patterns and extension.
        Returns: 'movies', 'tv_shows', 'music', 'photos', or 'unsorted'
        """
        filename = file_path.name.lower()
        extension = get_file_extension(file_path).lower()
        
        # Get supported extensions
        video_exts = self.config.get('advanced.video_extensions', [])
        audio_exts = self.config.get('advanced.audio_extensions', [])
        photo_exts = self.config.get('advanced.photo_extensions', [])
        
        # Check for TV show patterns first
        if re.search(r's\d+e\d+', filename):
            return 'tv_shows'
        
        # Check if file has a known media extension
        is_video = extension in [ext.lower() for ext in video_exts]
        is_audio = extension in [ext.lower() for ext in audio_exts]
        is_photo = extension in [ext.lower() for ext in photo_exts]
        
        if is_video:
            # Check if it could be a movie based on pattern
            pattern_info = self.extract_pattern_info(filename)
            
            # If it has a clear movie/year pattern, it's a movie
            if pattern_info.get('year'):
                return 'movies'
            
            # If it has a title that looks like a movie name, it's a movie
            if pattern_info.get('title') and len(pattern_info['title']) > 2:
                # Check for common non-movie indicators
                non_movie_patterns = [
                    r'sample', r'trailer', r'preview', r'intro', r'outro',
                    r'behind.the.scenes', r'blooper', r'featurette',
                    r'deleted.scene', r'alternate.ending'
                ]
                
                has_non_movie_pattern = any(
                    re.search(pattern, filename) for pattern in non_movie_patterns
                )
                
                if not has_non_movie_pattern:
                    return 'movies'
            
            # If it's a video file but doesn't look like a movie, put in unsorted
            return 'unsorted'
        
        elif is_audio:
            return 'music'
        elif is_photo:
            return 'photos'
        else:
            # Unknown extension - put in unsorted
            return 'unsorted'
    
    def generate_new_filename(self, file_path: Path, pattern_info: Dict = None, media_type: str = None) -> str:
        """
        Generate a new standardized filename.
        Format: Movie.Title.Year.FileType or Show.Title.S01E01.FileType
        
        Args:
            file_path: Path to file
            pattern_info: Extracted pattern information
            media_type: Type of media to determine naming strategy
        
        Returns:
            New filename (without path)
        """
        if pattern_info is None:
            pattern_info = self.extract_pattern_info(file_path.stem)
        
        extension = get_file_extension(file_path)
        
        # For unsorted files, just sanitize the original name
        if media_type == 'unsorted':
            new_name = self.sanitize_filename(file_path.stem)
            new_name = re.sub(r'\s+', '.', new_name)
            new_name = clean_filename(new_name)
            return new_name + extension
        
        # Get configuration
        naming_pattern = self.config.get('organization.naming_pattern', '{title} ({year}) [{resolution}]')
        
        # Build components for dot-separated format
        components = []
        
        # Title - replace spaces with dots
        title = pattern_info.get('title', '')
        if not title:
            title = file_path.stem
        
        # Clean title and replace spaces with dots
        title = self.sanitize_filename(title)
        title = re.sub(r'\s+', '.', title)
        components.append(title)
        
        # Year
        if pattern_info.get('year'):
            components.append(pattern_info['year'])
        
        # Season/Episode for TV shows
        if pattern_info.get('season') and pattern_info.get('episode'):
            components.append(f"S{pattern_info['season']}E{pattern_info['episode']}")
        
        # Join with dots: Title.Year or Title.S01E01
        new_name = '.'.join(components) if components else file_path.stem
        
        # Remove any leftover problematic characters
        new_name = clean_filename(new_name)
        
        return new_name + extension
    
    def find_associated_files(self, file_path: Path) -> List[Path]:
        """
        Find files associated with this media file (subtitles, NFO, etc.).
        
        Args:
            file_path: Main media file
        
        Returns:
            List of associated file paths
        """
        associated = []
        base_path = file_path.parent / file_path.stem
        
        # Common associated file extensions
        associated_exts = ['.srt', '.vtt', '.idx', '.sub', '.nfo', '.jpg', '.png']
        
        for ext in associated_exts:
            potential_file = base_path.with_suffix(ext)
            if potential_file.exists() and potential_file != file_path:
                associated.append(potential_file)
        
        return associated
    
    def plan_file_move(self, file_path: Path, target_base_dir: Path = None) -> Dict:
        """
        Plan the move/rename of a file with organized directory structure.
        
        Args:
            file_path: Current file path
            target_base_dir: Base target directory (None to use config)
        
        Returns:
            Dictionary with move plan information
        """
        # Determine media type first
        media_type = self._detect_media_type(file_path)
        
        # Extract info
        pattern_info = self.extract_pattern_info(file_path.name)
        new_name = self.generate_new_filename(file_path, pattern_info, media_type)
        
        # Determine target base directory
        if target_base_dir is None:
            # Use configured output directory or create one
            output_dir = self.config.get('organization.output_directory', 'organized_media')
            target_base_dir = Path(output_dir)
        
        # Create organized directory structure
        target_dir = self.create_directory_structure(target_base_dir, media_type, pattern_info)
        
        new_path = target_dir / new_name
        
        # Find associated files
        associated = self.find_associated_files(file_path)
        
        # Plan associated file moves
        associated_moves = []
        for assoc_file in associated:
            assoc_ext = get_file_extension(assoc_file)
            assoc_new_name = new_path.stem + assoc_ext
            assoc_new_path = target_dir / assoc_new_name
            associated_moves.append({
                'from': assoc_file,
                'to': assoc_new_path
            })
        
        return {
            'file': file_path,
            'from': file_path,
            'to': new_path,
            'associated': associated_moves,
            'changed': str(file_path) != str(new_path),
            'media_type': media_type,
            'target_dir': target_dir
        }
    
    def create_directory_structure(self, base_path: Path, media_type: str = None, pattern_info: Dict = None) -> Path:
        """
        Create organized directory structure.
        
        Args:
            base_path: Base directory
            media_type: Type of media (movie, tv, music, etc.)
            pattern_info: Extracted pattern information
        
        Returns:
            Path to created directory
        """
        if media_type is None:
            return base_path
        
        organize_by = self.config.get('organization.organize_by', 'type')
        
        if organize_by == 'none':
            return base_path
        
        # Start with base path
        new_path = base_path
        
        # Organize by media type first
        if media_type:
            new_path = new_path / media_type
        
        # Additional organization based on media type
        if media_type == 'movies':
            # For movies, just create flat structure under movies/
            # No subdirectories by year
            pass
        
        elif media_type == 'tv_shows':
            # Organize by show name for TV shows
            if pattern_info and pattern_info.get('title'):
                show_name = pattern_info['title']
                # Clean show name for directory
                show_name = self.sanitize_filename(show_name)
                show_name = re.sub(r'\s+', '.', show_name)
                new_path = new_path / show_name
                
                # Add season folder
                if pattern_info.get('season'):
                    season = f"Season {pattern_info['season']}"
                    new_path = new_path / season
        
        elif media_type == 'unsorted':
            # For unsorted files, just put them in unsorted/ folder
            # Keep original filename structure
            pass
        
        # Create directory
        new_path.mkdir(parents=True, exist_ok=True)
        
        return new_path
    
    def execute_move(self, move_plan: Dict, dry_run: bool = False) -> bool:
        """
        Execute a planned file move.
        
        Args:
            move_plan: Move plan from plan_file_move()
            dry_run: If True, don't actually move files
        
        Returns:
            True if successful
        """
        try:
            if dry_run:
                self.logger.info(f"[DRY RUN] Would move: {move_plan['from']} -> {move_plan['to']}")
                return True
            
            # Move main file
            if move_plan['changed']:
                move_plan['to'].parent.mkdir(parents=True, exist_ok=True)
                move_plan['file'].rename(move_plan['to'])
                self.logger.info(f"Moved: {move_plan['from']} -> {move_plan['to']}")
            
            # Move associated files
            for assoc in move_plan['associated']:
                assoc['to'].parent.mkdir(parents=True, exist_ok=True)
                assoc['from'].rename(assoc['to'])
                self.logger.info(f"Moved associated: {assoc['from']} -> {assoc['to']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            return False
