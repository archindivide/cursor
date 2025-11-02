"""File organization and naming standardization."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from ..utils.file_utils import clean_filename, get_file_extension, get_file_mtime, get_file_size, move_file_cross_device


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
    
    def _detect_media_type(self, file_path: Path) -> tuple:
        """
        Detect media type based on filename patterns and extension.
        Also determines if the file is recognized (has proper pattern) or unorganized.
        
        Returns:
            Tuple of (media_type, is_recognized) where:
            - media_type: 'movies', 'tv_shows', 'music', 'photos'
            - is_recognized: True if file matches known patterns, False if unorganized
        """
        filename = file_path.name.lower()
        extension = get_file_extension(file_path).lower()
        
        # Get supported extensions
        video_exts = self.config.get('advanced.video_extensions', [])
        audio_exts = self.config.get('advanced.audio_extensions', [])
        photo_exts = self.config.get('advanced.photo_extensions', [])
        
        # Check if file has a known media extension
        is_video = extension in [ext.lower() for ext in video_exts]
        is_audio = extension in [ext.lower() for ext in audio_exts]
        is_photo = extension in [ext.lower() for ext in photo_exts]
        
        if is_video:
            # Check for TV show patterns first
            if re.search(r's\d+e\d+', filename):
                pattern_info = self.extract_pattern_info(filename)
                # TV shows with season/episode are recognized
                is_recognized = bool(pattern_info.get('season') and pattern_info.get('episode'))
                return ('tv_shows', is_recognized)
            
            # Check if it could be a movie based on pattern
            pattern_info = self.extract_pattern_info(filename)
            
            # If it has a clear movie/year pattern, it's a recognized movie
            if pattern_info.get('year'):
                return ('movies', True)
            
            # If it has a title that looks like a movie name, it's a recognized movie
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
                    return ('movies', True)
            
            # Video file but doesn't match patterns - goes to movies/unorganized
            return ('movies', False)
        
        elif is_audio:
            # Audio files go to music (no pattern matching for now, so all are unorganized)
            return ('music', False)
        elif is_photo:
            # Photo files go to photos (no pattern matching for now, so all are unorganized)
            return ('photos', False)
        else:
            # Unknown extension - default to movies/unorganized for backward compatibility
            # Or we could skip it, but let's put it somewhere
            return ('movies', False)
    
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
        
        # Get configuration
        naming_pattern = self.config.get('organization.naming_pattern', '{title} ({year}) [{resolution}]')
        
        # Build components for dot-separated format
        components = []
        
        # Title - replace spaces with dots
        title = pattern_info.get('title', '')
        if not title:
            # For unorganized files without a recognized title, use original stem (sanitized)
            title = self.sanitize_filename(file_path.stem)
            title = re.sub(r'\s+', '.', title)
            components.append(title)
            # Join with dots and clean
            new_name = '.'.join(components) if components else file_path.stem
            new_name = clean_filename(new_name)
            return new_name + extension
        
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
    
    def _is_sample_or_junk_file(self, file_path: Path) -> bool:
        """
        Determine if a file is a sample or junk file that should not be moved with the main movie.
        
        Args:
            file_path: File to check
        
        Returns:
            True if file is sample/junk, False otherwise
        """
        if not file_path.exists():
            return False
        
        filename_lower = file_path.name.lower()
        
        try:
            file_size = get_file_size(file_path)
        except (OSError, IOError):
            return False
        
        # Check for sample indicators in filename
        sample_patterns = [
            r'\bsample\b',
            r'\btrailer\b',
            r'\bpreview\b',
            r'^sample',
            r'sample\.',
            r'-sample',
        ]
        
        # Check if filename contains sample-related keywords
        is_sample_name = any(re.search(pattern, filename_lower) for pattern in sample_patterns)
        
        # Small video files (< 50MB) with sample-like names are likely samples
        if is_sample_name:
            video_exts = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
            if any(file_path.name.lower().endswith(ext) for ext in video_exts):
                if file_size < 50 * 1024 * 1024:  # Less than 50MB
                    return True
        
        # Very small video files (< 10MB) are likely samples regardless of name
        video_exts = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        if any(file_path.name.lower().endswith(ext) for ext in video_exts):
            if file_size < 10 * 1024 * 1024:  # Less than 10MB
                return True
        
        return False
    
    def _should_keep_with_main_file(self, file_path: Path) -> bool:
        """
        Determine if an associated file should be kept with the main movie file.
        Always keep images, metadata, and subtitles. When in doubt, keep files together.
        
        Args:
            file_path: Associated file to check
        
        Returns:
            True if file should be kept with main file, False otherwise
        """
        extension = get_file_extension(file_path).lower()
        filename_lower = file_path.name.lower()
        
        # Always keep images with main file
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif']
        if extension in image_exts:
            return True
        
        # Always keep metadata files with main file
        metadata_exts = ['.nfo', '.xml', '.txt']
        if extension in metadata_exts:
            return True
        
        # Always keep subtitle files with main file
        subtitle_exts = ['.srt', '.vtt', '.ass', '.ssa', '.sub', '.idx']
        if extension in subtitle_exts:
            return True
        
        # For other files, check if they're samples/junk
        # If it's clearly a sample/junk, don't move it with the main file
        if self._is_sample_or_junk_file(file_path):
            return False
        
        # When in doubt (unknown file type, not clearly junk), keep with main file
        # This is the conservative approach the user requested
        return True
    
    def find_associated_files(self, file_path: Path) -> List[Path]:
        """
        Find files associated with this media file.
        Only includes files that should be kept with the main file (images, metadata, subtitles).
        Sample and junk files are excluded.
        
        Args:
            file_path: Main media file
        
        Returns:
            List of associated file paths that should be kept with the main file
        """
        associated = []
        directory = file_path.parent
        
        # Get the main file's base name (without extension)
        main_base = file_path.stem.lower()
        
        # Common associated file patterns (poster, fanart, etc.)
        common_patterns = ['poster', 'fanart', 'banner', 'logo', 'clearart', 'thumb', 'backdrop']
        
        # Look for files in the same directory that might be associated
        for potential_file in directory.iterdir():
            if potential_file == file_path or not potential_file.is_file():
                continue
            
            potential_base = potential_file.stem.lower()
            extension = get_file_extension(potential_file).lower()
            
            # Always check if file should be kept first (fast check for images/metadata)
            if not self._should_keep_with_main_file(potential_file):
                continue
            
            # Check if file has same base name (exact match or variations)
            is_similar_name = (
                potential_base == main_base or
                potential_base.startswith(main_base + '-') or
                potential_base.startswith(main_base + '_') or
                potential_base.startswith(main_base + '.') or
                main_base.startswith(potential_base)
            )
            
            # Also check for common associated file naming patterns
            # e.g., "Movie Name-poster.jpg" or "Movie Name.fanart.jpg"
            is_common_pattern = any(
                pattern in potential_base and (main_base in potential_base or potential_base in main_base)
                for pattern in common_patterns
            )
            
            # For images and metadata in the same directory, be more lenient
            # If it's an image or metadata file, assume it's associated if name overlaps
            is_image_or_metadata = extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.nfo', '.xml']
            is_directory_match = (
                is_image_or_metadata and
                (potential_base.startswith(main_base[:10]) or main_base.startswith(potential_base[:10]))
            )
            
            # Include if it matches any of these criteria
            if is_similar_name or is_common_pattern or is_directory_match:
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
        # Determine media type and whether it's recognized
        media_type, is_recognized = self._detect_media_type(file_path)
        
        # Extract info
        pattern_info = self.extract_pattern_info(file_path.name)
        new_name = self.generate_new_filename(file_path, pattern_info, media_type)
        
        # Determine target base directory
        if target_base_dir is None:
            # Check for category-specific output directory
            output_dirs = self.config.get('organization.output_directories', {})
            category_dir = output_dirs.get(media_type, '')
            
            if category_dir and category_dir.strip():
                # Use category-specific directory
                target_base_dir = Path(category_dir)
            else:
                # Use default output directory
                output_dir = self.config.get('organization.output_directory', 'organized_media')
                target_base_dir = Path(output_dir)
        
        # Create organized directory structure
        target_dir = self.create_directory_structure(target_base_dir, media_type, pattern_info, is_recognized)
        
        new_path = target_dir / new_name
        
        # Find associated files
        associated = self.find_associated_files(file_path)
        
        # Plan associated file moves
        # Keep original filenames for associated files (don't rename them)
        associated_moves = []
        for assoc_file in associated:
            # Keep the original filename, just sanitize problematic characters
            original_name = assoc_file.name
            # Only sanitize invalid characters, don't change the name structure
            sanitized_name = clean_filename(original_name)
            assoc_new_path = target_dir / sanitized_name
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
            'is_recognized': is_recognized,
            'target_dir': target_dir
        }
    
    def create_directory_structure(self, base_path: Path, media_type: str = None, pattern_info: Dict = None, is_recognized: bool = True) -> Path:
        """
        Create organized directory structure.
        
        Args:
            base_path: Base directory (may already be category-specific)
            media_type: Type of media (movie, tv, music, etc.)
            pattern_info: Extracted pattern information
            is_recognized: Whether the file matches known patterns (False = unorganized)
        
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
        
        # Check if base_path is already a category-specific directory
        # by checking if it matches any configured category directory
        output_dirs = self.config.get('organization.output_directories', {})
        is_category_specific = False
        for category, cat_dir in output_dirs.items():
            if cat_dir and cat_dir.strip() and str(base_path) == str(Path(cat_dir)):
                is_category_specific = True
                break
        
        # Only add media_type subdirectory if base_path is not category-specific
        # and organize_by is 'type'
        if not is_category_specific and media_type and organize_by == 'type':
            new_path = new_path / media_type
        
        # Additional organization based on media type and recognition
        if media_type == 'movies':
            if is_recognized:
                # For recognized movies, create flat structure under movies/
                # No subdirectories by year
                pass
            else:
                # Unrecognized movies go to movies/unorganized/
                new_path = new_path / 'unorganized'
        
        elif media_type == 'tv_shows':
            if is_recognized and pattern_info and pattern_info.get('title'):
                # Organize by show name for recognized TV shows
                show_name = pattern_info['title']
                # Clean show name for directory
                show_name = self.sanitize_filename(show_name)
                show_name = re.sub(r'\s+', '.', show_name)
                new_path = new_path / show_name
                
                # Add season folder
                if pattern_info.get('season'):
                    season = f"Season {pattern_info['season']}"
                    new_path = new_path / season
            else:
                # Unrecognized TV shows go to tv_shows/unorganized/
                new_path = new_path / 'unorganized'
        
        elif media_type == 'music':
            if is_recognized:
                # For recognized music, flat structure (future: organize by artist/album)
                pass
            else:
                # Unrecognized music goes to music/unorganized/
                new_path = new_path / 'unorganized'
        
        elif media_type == 'photos':
            if is_recognized:
                # For recognized photos, flat structure (future: organize by date)
                pass
            else:
                # Unrecognized photos go to photos/unorganized/
                new_path = new_path / 'unorganized'
        
        # Create directory
        new_path.mkdir(parents=True, exist_ok=True)
        
        return new_path
    
    def _save_original_structure(self, target_dir: Path, file_mappings: List[Dict[str, Path]]) -> None:
        """
        Save original file structure mapping to a text file for unorganized files.
        Preserves the full original directory structure in a concise format.
        
        Args:
            target_dir: Target directory where files are being moved
            file_mappings: List of dictionaries with 'from' and 'to' keys
        """
        try:
            mapping_file = target_dir / "original_structure.txt"
            
            # Check if file exists to determine if we need a header
            file_exists = mapping_file.exists()
            
            # Append new mappings
            with open(mapping_file, 'a', encoding='utf-8') as f:
                # Add timestamp header if file is new
                if not file_exists:
                    f.write(f"Original File Structure Mapping\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write(f"{'='*80}\n\n")
                
                # Group by original directory structure
                from collections import defaultdict
                by_directory = defaultdict(list)
                
                for mapping in file_mappings:
                    original_path = mapping['from']
                    new_path = mapping['to']
                    original_dir = original_path.parent
                    by_directory[original_dir].append((original_path, new_path))
                
                # Write grouped by directory structure (concise format)
                for original_dir in sorted(by_directory.keys()):
                    f.write(f"\n{original_dir}\n")
                    
                    for original_path, new_path in sorted(by_directory[original_dir]):
                        # Show just the filename with new location
                        filename = original_path.name
                        f.write(f"  {filename} -> {new_path.name}\n")
                
                f.write("\n")
            
            self.logger.info(f"Saved original structure mapping to: {mapping_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving original structure mapping: {e}")
    
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
            
            # Track file mappings for unorganized files
            file_mappings = []
            
            # Move main file
            if move_plan['changed']:
                if move_file_cross_device(move_plan['file'], move_plan['to']):
                    self.logger.info(f"Moved: {move_plan['from']} -> {move_plan['to']}")
                    
                    # Track mapping for unorganized files (not recognized patterns)
                    if not move_plan.get('is_recognized', True):
                        file_mappings.append({
                            'from': move_plan['from'],
                            'to': move_plan['to']
                        })
                else:
                    raise Exception(f"Failed to move file: {move_plan['from']}")
            
            # Move associated files
            for assoc in move_plan['associated']:
                if move_file_cross_device(assoc['from'], assoc['to']):
                    self.logger.info(f"Moved associated: {assoc['from']} -> {assoc['to']}")
                    
                    # Track mapping for associated files of unorganized main files
                    if not move_plan.get('is_recognized', True):
                        file_mappings.append({
                            'from': assoc['from'],
                            'to': assoc['to']
                        })
                else:
                    raise Exception(f"Failed to move associated file: {assoc['from']}")
            
            # Save original structure mapping for unorganized files
            if file_mappings and not move_plan.get('is_recognized', True):
                self._save_original_structure(move_plan['target_dir'], file_mappings)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            return False
