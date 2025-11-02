"""File organization and naming standardization."""

import logging
import re
import os
import shutil
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
        target_dir = self.create_directory_structure(target_base_dir, media_type, pattern_info, is_recognized, file_path)
        
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
    
    def _preserve_unorganized_structure(self, file_path: Path, base_path: Path, media_type: str) -> Path:
        """
        For unorganized files, preserve some of the original directory structure
        to keep related files together.
        
        Args:
            file_path: Original file path
            base_path: Base path for the media type
            media_type: Type of media
        
        Returns:
            Path with preserved structure
        """
        # For unorganized files, preserve the last 2-3 levels of directory structure
        # This keeps files from the same source together
        try:
            # Get relative parts of the original path
            # Try to preserve meaningful directory names (not too deep)
            source_parts = file_path.parent.parts
            
            # Only preserve if there are meaningful directory names
            # Skip very generic names like "Downloads", "Desktop", etc.
            generic_names = {'downloads', 'desktop', 'documents', 'videos', 'pictures', 'music'}
            
            preserved_parts = []
            for part in reversed(source_parts[-3:]):  # Take last 3 levels
                if part.lower() not in generic_names and len(part) > 2:
                    preserved_parts.insert(0, part)
                else:
                    break
            
            # If we have preserved parts, create structure
            if preserved_parts:
                # Sanitize directory names
                sanitized_parts = [self.sanitize_filename(part) for part in preserved_parts]
                sanitized_parts = [part.replace(' ', '.') for part in sanitized_parts if part]
                
                if sanitized_parts:
                    # Create path with preserved structure under unorganized
                    unorganized_path = base_path / media_type / 'unorganized'
                    for part in sanitized_parts[:2]:  # Limit to 2 levels max
                        unorganized_path = unorganized_path / part
                    return unorganized_path
            
        except Exception as e:
            self.logger.debug(f"Error preserving structure for {file_path}: {e}")
        
        # Default: just use unorganized folder
        return base_path / media_type / 'unorganized'
    
    def create_directory_structure(self, base_path: Path, media_type: str = None, pattern_info: Dict = None, is_recognized: bool = True, file_path: Path = None) -> Path:
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
                # Preserve some directory structure to keep files together
                if file_path:
                    preserved_path = self._preserve_unorganized_structure(file_path, base_path, media_type)
                    # Check if base_path is category-specific
                    output_dirs = self.config.get('organization.output_directories', {})
                    is_category_specific = any(
                        cat_dir and cat_dir.strip() and str(base_path) == str(Path(cat_dir))
                        for cat_dir in output_dirs.values()
                    )
                    
                    if is_category_specific:
                        # Already at category-specific path, just add unorganized
                        new_path = new_path / 'unorganized'
                        # Try to preserve structure from file_path
                        try:
                            source_parts = file_path.parent.parts[-2:]  # Last 2 levels
                            if source_parts:
                                for part in source_parts:
                                    if len(part) > 2 and part.lower() not in {'downloads', 'desktop', 'videos'}:
                                        sanitized = self.sanitize_filename(part).replace(' ', '.')
                                        new_path = new_path / sanitized
                        except Exception:
                            pass
                    else:
                        new_path = preserved_path
                else:
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
                # Preserve structure to keep files together
                if file_path:
                    preserved_path = self._preserve_unorganized_structure(file_path, base_path, media_type)
                    output_dirs = self.config.get('organization.output_directories', {})
                    is_category_specific = any(
                        cat_dir and cat_dir.strip() and str(base_path) == str(Path(cat_dir))
                        for cat_dir in output_dirs.values()
                    )
                    
                    if is_category_specific:
                        new_path = new_path / 'unorganized'
                        try:
                            source_parts = file_path.parent.parts[-2:]
                            if source_parts:
                                for part in source_parts:
                                    if len(part) > 2 and part.lower() not in {'downloads', 'desktop', 'videos'}:
                                        sanitized = self.sanitize_filename(part).replace(' ', '.')
                                        new_path = new_path / sanitized
                        except Exception:
                            pass
                    else:
                        new_path = preserved_path
                else:
                    new_path = new_path / 'unorganized'
        
        elif media_type == 'music':
            if is_recognized:
                # For recognized music, flat structure (future: organize by artist/album)
                pass
            else:
                # Unrecognized music goes to music/unorganized/
                # Preserve structure to keep files together
                if file_path:
                    preserved_path = self._preserve_unorganized_structure(file_path, base_path, media_type)
                    output_dirs = self.config.get('organization.output_directories', {})
                    is_category_specific = any(
                        cat_dir and cat_dir.strip() and str(base_path) == str(Path(cat_dir))
                        for cat_dir in output_dirs.values()
                    )
                    
                    if is_category_specific:
                        new_path = new_path / 'unorganized'
                        try:
                            source_parts = file_path.parent.parts[-2:]
                            if source_parts:
                                for part in source_parts:
                                    if len(part) > 2 and part.lower() not in {'downloads', 'desktop', 'music'}:
                                        sanitized = self.sanitize_filename(part).replace(' ', '.')
                                        new_path = new_path / sanitized
                        except Exception:
                            pass
                    else:
                        new_path = preserved_path
                else:
                    new_path = new_path / 'unorganized'
        
        elif media_type == 'photos':
            if is_recognized:
                # For recognized photos, flat structure (future: organize by date)
                pass
            else:
                # Unrecognized photos go to photos/unorganized/
                # Preserve structure to keep files together
                if file_path:
                    preserved_path = self._preserve_unorganized_structure(file_path, base_path, media_type)
                    output_dirs = self.config.get('organization.output_directories', {})
                    is_category_specific = any(
                        cat_dir and cat_dir.strip() and str(base_path) == str(Path(cat_dir))
                        for cat_dir in output_dirs.values()
                    )
                    
                    if is_category_specific:
                        new_path = new_path / 'unorganized'
                        try:
                            source_parts = file_path.parent.parts[-2:]
                            if source_parts:
                                for part in source_parts:
                                    if len(part) > 2 and part.lower() not in {'downloads', 'desktop', 'pictures', 'photos'}:
                                        sanitized = self.sanitize_filename(part).replace(' ', '.')
                                        new_path = new_path / sanitized
                        except Exception:
                            pass
                    else:
                        new_path = preserved_path
                else:
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
    
    def _cleanup_empty_directories(self, directories: List[Path], recursive: bool = True, 
                                    exclude_paths: Optional[List[Path]] = None) -> int:
        """
        Clean up empty directories after files have been moved.
        Recursively cleans up parent directories if they become empty.
        
        Args:
            directories: List of directory paths to check and clean up
            recursive: If True, also clean up parent directories that become empty
            exclude_paths: Optional list of paths to exclude from cleanup
        
        Returns:
            Number of directories removed
        """
        removed_count = 0
        removed_dirs = set()
        exclude_set = set(exclude_paths or [])
        
        # Sort directories by depth (deepest first) to avoid deleting parent before child
        directories_sorted = sorted(directories, key=lambda p: len(p.parts), reverse=True)
        
        # Helper function to check if directory should be excluded
        def should_exclude(path: Path) -> bool:
            """Check if path should be excluded from cleanup."""
            if path in exclude_set:
                return True
            # Check if any exclude path is a parent of this path
            for exclude_path in exclude_set:
                try:
                    path.relative_to(exclude_path)
                    return True
                except ValueError:
                    continue
            return False
        
        # Process each directory
        for directory in directories_sorted:
            if should_exclude(directory):
                continue
                
            # Recursively clean up this directory and its parents
            current_dir = directory
            while current_dir and current_dir.exists():
                if current_dir in removed_dirs or should_exclude(current_dir):
                    break
                
                try:
                    if current_dir.is_dir():
                        # More thorough check for empty directory
                        # On Linux, hidden files (.files) might not be caught
                        try:
                            contents = list(current_dir.iterdir())
                        except (OSError, PermissionError) as e:
                            self.logger.debug(f"Error listing directory {current_dir}: {e}")
                            break
                        
                        # Check if directory is empty
                        # On Linux, iterdir() might not show all files, so we verify by trying rmdir
                        if not contents:
                            # Directory appears empty, try to remove it
                            # rmdir() will fail if directory is not actually empty (e.g., has hidden files)
                            try:
                                current_dir.rmdir()
                                self.logger.info(f"Removed empty directory: {current_dir}")
                                removed_dirs.add(current_dir)
                                removed_count += 1
                                
                                # Continue with parent directory if recursive
                                if recursive:
                                    current_dir = current_dir.parent
                                    continue
                                else:
                                    break
                            except OSError as e:
                                # On Linux, errno 39 (ENOTEMPTY) means directory is not empty
                                # errno 16 (EBUSY) means directory is in use
                                # errno 13 (EACCES) means permission denied
                                if hasattr(e, 'errno'):
                                    if e.errno == 39:  # ENOTEMPTY
                                        # Directory has hidden files or other entries
                                        self.logger.debug(f"Directory {current_dir} is not empty (may have hidden files)")
                                        # Try to list all files including hidden
                                        try:
                                            all_contents = os.listdir(str(current_dir))
                                            if all_contents:
                                                self.logger.debug(f"Directory {current_dir} contains: {all_contents}")
                                            else:
                                                # Empty but rmdir failed - might be a mount point or special case
                                                self.logger.debug(f"Directory {current_dir} appears empty but cannot be removed")
                                        except:
                                            pass
                                    elif e.errno == 16:  # EBUSY
                                        self.logger.debug(f"Directory {current_dir} is busy (in use)")
                                    elif e.errno == 13:  # EACCES
                                        self.logger.debug(f"Permission denied removing directory {current_dir}")
                                else:
                                    self.logger.debug(f"Could not remove directory {current_dir}: {e}")
                                break
                        else:
                            # Check if only empty subdirectories remain
                            # On Linux, check for all types of entries including hidden files
                            has_files = False
                            has_dirs = False
                            
                            for item in contents:
                                try:
                                    if item.is_file():
                                        has_files = True
                                        break
                                    elif item.is_dir():
                                        has_dirs = True
                                except (OSError, PermissionError):
                                    # Skip items we can't access
                                    continue
                            
                            if not has_files:
                                # Try to remove empty subdirectories first (recursively)
                                for item in contents:
                                    try:
                                        if item.is_dir() and not should_exclude(item):
                                            # Recursively clean up subdirectory
                                            sub_removed = self._cleanup_empty_directories_recursive(item, removed_dirs, exclude_set)
                                            removed_count += sub_removed
                                    except (OSError, PermissionError) as e:
                                        self.logger.debug(f"Error processing subdirectory {item}: {e}")
                                
                                # Check again if directory is now empty
                                # Use os.listdir to catch hidden files on Linux
                                try:
                                    try:
                                        # Use os.listdir first for complete listing (catches hidden files on Linux)
                                        remaining_list = os.listdir(str(current_dir))
                                        remaining = [current_dir / item for item in remaining_list]
                                    except (OSError, PermissionError):
                                        # Fall back to iterdir if os.listdir fails
                                        remaining = list(current_dir.iterdir())
                                    
                                    if not remaining:
                                        current_dir.rmdir()
                                        self.logger.info(f"Removed empty directory: {current_dir}")
                                        removed_dirs.add(current_dir)
                                        removed_count += 1
                                        
                                        # Continue with parent directory if recursive
                                        if recursive:
                                            current_dir = current_dir.parent
                                            continue
                                        else:
                                            break
                                    else:
                                        # Directory still has contents, stop cleaning this path
                                        self.logger.debug(f"Directory {current_dir} still has {len(remaining)} items: {[r.name for r in remaining]}")
                                        break
                                except OSError as e:
                                    errno = getattr(e, 'errno', None)
                                    self.logger.debug(f"Could not remove directory {current_dir} after cleanup: {e} (errno: {errno})")
                                    break
                            else:
                                # Directory has files, stop cleaning
                                break
                    else:
                        break
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Error checking directory {current_dir}: {e}")
                    break
        
        return removed_count
    
    def _cleanup_empty_directories_recursive(self, directory: Path, removed_dirs: set, 
                                             exclude_set: set) -> int:
        """
        Helper method to recursively clean up empty subdirectories.
        
        Args:
            directory: Directory to clean up
            removed_dirs: Set of already removed directories (updated in place)
            exclude_set: Set of paths to exclude
        
        Returns:
            Number of directories removed
        """
        removed_count = 0
        
        try:
            if directory in removed_dirs:
                return removed_count
            
            # Check if should exclude
            for exclude_path in exclude_set:
                try:
                    directory.relative_to(exclude_path)
                    return removed_count
                except ValueError:
                    continue
            
            try:
                contents = list(directory.iterdir())
            except (OSError, PermissionError) as e:
                self.logger.debug(f"Error listing directory {directory}: {e}")
                return removed_count
            
            # First, recursively clean up subdirectories
            for item in contents:
                try:
                    if item.is_dir() and item not in removed_dirs:
                        sub_removed = self._cleanup_empty_directories_recursive(item, removed_dirs, exclude_set)
                        removed_count += sub_removed
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Error processing subdirectory {item}: {e}")
            
            # Check if directory is now empty
            # Use os.listdir to catch hidden files on Linux
            try:
                try:
                    # Use os.listdir for complete listing (catches hidden files)
                    remaining_list = os.listdir(str(directory))
                    remaining = [directory / item for item in remaining_list]
                except (OSError, PermissionError):
                    # Fall back to iterdir
                    remaining = list(directory.iterdir())
                
                if not remaining:
                    directory.rmdir()
                    self.logger.debug(f"Removed empty subdirectory: {directory}")
                    removed_dirs.add(directory)
                    removed_count += 1
                else:
                    self.logger.debug(f"Directory {directory} still has {len(remaining)} items after cleanup: {[r.name for r in remaining]}")
            except OSError as e:
                errno = getattr(e, 'errno', None)
                self.logger.debug(f"Could not remove directory {directory}: {e} (errno: {errno}, may not be empty or in use)")
        except (OSError, PermissionError) as e:
            self.logger.debug(f"Error cleaning subdirectory {directory}: {e}")
        
        return removed_count
    
    def _cleanup_empty_directories_in_directory(self, directory: Path, 
                                                exclude_paths: Optional[List[Path]] = None) -> int:
        """
        Comprehensively scan a directory and remove all empty directories.
        Useful when input and output are the same.
        
        Args:
            directory: Root directory to scan
            exclude_paths: Optional list of paths to exclude from cleanup
        
        Returns:
            Number of directories removed
        """
        removed_count = 0
        exclude_set = set(exclude_paths or [])
        
        # Helper to check if path should be excluded
        def should_exclude(path: Path) -> bool:
            if path in exclude_set:
                return True
            for exclude_path in exclude_set:
                try:
                    path.relative_to(exclude_path)
                    return True
                except ValueError:
                    continue
            return False
        
        # Walk directory tree bottom-up (deepest first)
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                root_path = Path(root)
                
                # Skip excluded paths
                if should_exclude(root_path):
                    continue
                
                # Skip if root path is the same as directory (don't remove root)
                if root_path == directory:
                    continue
                
                # Check if directory is empty
                try:
                    contents = list(root_path.iterdir())
                    
                    # More thorough check - verify directory is truly empty
                    # On Linux, use os.listdir to catch hidden files that iterdir() might miss
                    try:
                        all_contents = os.listdir(str(root_path))
                        is_empty = len(all_contents) == 0
                    except (OSError, PermissionError):
                        # If we can't list, check with iterdir
                        is_empty = len(contents) == 0
                        all_contents = contents
                    
                    if is_empty:
                        # Directory appears empty, try to remove it
                        try:
                            root_path.rmdir()
                            self.logger.info(f"Removed empty directory: {root_path}")
                            removed_count += 1
                        except OSError as e:
                            # On Linux, this could fail if directory is in use or has hidden files
                            errno = getattr(e, 'errno', None)
                            if errno == 39:  # ENOTEMPTY - directory not empty
                                self.logger.debug(f"Directory {root_path} is not empty (ENOTEMPTY)")
                            elif errno == 16:  # EBUSY - directory in use
                                self.logger.debug(f"Directory {root_path} is busy (EBUSY)")
                            elif errno == 13:  # EACCES - permission denied
                                self.logger.debug(f"Permission denied removing {root_path} (EACCES)")
                            else:
                                self.logger.debug(f"Could not remove directory {root_path}: {e} (errno: {errno})")
                    else:
                        # Check if only empty subdirectories remain (no files)
                        has_files = False
                        for item in contents:
                            try:
                                if item.is_file():
                                    has_files = True
                                    break
                            except (OSError, PermissionError):
                                # If we can't check, assume it might be a file
                                has_files = True
                                break
                        
                        if not has_files:
                            # Try to remove empty subdirectories recursively
                            removed_dirs = set()
                            for item in contents:
                                try:
                                    if item.is_dir() and not should_exclude(item):
                                        sub_removed = self._cleanup_empty_directories_recursive(item, removed_dirs, exclude_set)
                                        removed_count += sub_removed
                                except (OSError, PermissionError) as e:
                                    self.logger.debug(f"Error cleaning subdirectory {item}: {e}")
                            
                            # Check again if directory is now empty
                            # Use os.listdir to catch hidden files on Linux
                            try:
                                try:
                                    # Use os.listdir for complete listing
                                    remaining_list = os.listdir(str(root_path))
                                    remaining = [root_path / item for item in remaining_list]
                                except (OSError, PermissionError):
                                    # Fall back to iterdir
                                    remaining = list(root_path.iterdir())
                                
                                if not remaining:
                                    root_path.rmdir()
                                    self.logger.info(f"Removed empty directory: {root_path}")
                                    removed_count += 1
                                else:
                                    self.logger.debug(f"Directory {root_path} still has {len(remaining)} items: {[r.name for r in remaining]}")
                            except OSError as e:
                                errno = getattr(e, 'errno', None)
                                self.logger.debug(f"Could not remove directory {root_path} after subdirectory cleanup: {e} (errno: {errno})")
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Error checking directory {root_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error scanning directory for empty folders: {e}")
        
        return removed_count
    
    def _cleanup_output_directory(self, output_dir: Path) -> Dict[str, int]:
        """
        Clean up the output directory structure.
        Moves unwanted files/junk to unorganized folders instead of deleting them.
        
        Args:
            output_dir: Root output directory to clean up
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'empty_dirs_removed': 0,
            'files_moved_to_unorganized': 0,
            'dirs_moved_to_unorganized': 0
        }
        
        if not output_dir.exists():
            return stats
        
        # Files that should be moved to unorganized (not deleted)
        unorganized_file_patterns = [
            'thumbs.db',
            '.ds_store',
            'desktop.ini',
            'folder.jpg',
        ]
        
        # Directories that should be moved to unorganized
        unorganized_dir_patterns = [
            '__pycache__',
            '.git',
            '.svn',
            '.cache',
        ]
        
        # Category folders that should have their own unorganized_files
        category_folders = ['movies', 'tv_shows', 'music', 'photos']
        
        # Map of category folders to their unorganized_files directories
        category_unorganized_dirs = {}
        for category in category_folders:
            category_dir = output_dir / category
            if category_dir.exists():
                unorganized_dir = category_dir / 'unorganized_files'
                unorganized_dir.mkdir(parents=True, exist_ok=True)
                category_unorganized_dirs[category_dir] = unorganized_dir
        
        try:
            # Walk through output directory and collect files
            for root, dirs, files in os.walk(output_dir, topdown=False):
                root_path = Path(root)
                
                # Skip the unorganized_files directories themselves
                if any(unorganized_dir == root_path or unorganized_dir in root_path.parents 
                       for unorganized_dir in category_unorganized_dirs.values()):
                    continue
                
                # Determine which category folder this path belongs to
                target_unorganized_dir = None
                for category_dir, unorganized_dir in category_unorganized_dirs.items():
                    if root_path == category_dir or category_dir in root_path.parents:
                        target_unorganized_dir = unorganized_dir
                        break
                
                # If we're in a category folder, use its unorganized_files
                # Otherwise, find the closest category parent
                if not target_unorganized_dir:
                    # Check if we're in a subdirectory of a category
                    for category_dir, unorganized_dir in category_unorganized_dirs.items():
                        try:
                            root_path.relative_to(category_dir)
                            target_unorganized_dir = unorganized_dir
                            break
                        except ValueError:
                            continue
                
                # If still no category found, skip (we're outside categories or at root)
                if not target_unorganized_dir:
                    continue
                
                # Move unwanted files to unorganized
                for file_name in files:
                    file_path = root_path / file_name
                    file_lower = file_name.lower()
                    
                    # Check if it should be moved to unorganized
                    if any(pattern in file_lower for pattern in unorganized_file_patterns):
                        try:
                            # Determine the category folder this file is in
                            file_category_dir = None
                            for category_dir in category_unorganized_dirs.keys():
                                try:
                                    file_path.relative_to(category_dir)
                                    file_category_dir = category_dir
                                    break
                                except ValueError:
                                    continue
                            
                            if not file_category_dir:
                                continue
                            
                            # Create subdirectory structure in category's unorganized_files
                            relative_to_category = file_path.relative_to(file_category_dir)
                            unorganized_dir = category_unorganized_dirs[file_category_dir]
                            
                            # If file is directly in category folder, put it directly in unorganized_files
                            if relative_to_category.parent == Path('.'):
                                dest_path = unorganized_dir / file_name
                            else:
                                # Preserve subdirectory structure within unorganized_files
                                # Skip the file name itself, we only want the directory structure
                                if len(relative_to_category.parts) > 1:
                                    dest_path = unorganized_dir / relative_to_category.parent / file_name
                                else:
                                    dest_path = unorganized_dir / file_name
                            
                            # Ensure destination directory exists
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Move file
                            move_file_cross_device(file_path, dest_path)
                            self.logger.info(f"Moved file to unorganized: {file_path} -> {dest_path}")
                            stats['files_moved_to_unorganized'] += 1
                        except Exception as e:
                            self.logger.debug(f"Could not move file {file_path}: {e}")
                
                # Move unwanted directories to unorganized
                dirs_to_process = list(dirs)  # Copy list since we're modifying it
                for dir_name in dirs_to_process:
                    dir_path = root_path / dir_name
                    dir_lower = dir_name.lower()
                    
                    # Skip if it's an unorganized_files directory
                    if any(unorganized_dir == dir_path or unorganized_dir in dir_path.parents
                           for unorganized_dir in category_unorganized_dirs.values()):
                        continue
                    
                    # Check if it should be moved to unorganized
                    if any(pattern in dir_lower for pattern in unorganized_dir_patterns):
                        try:
                            # Determine which category folder this directory is in
                            dir_category_dir = None
                            for category_dir in category_unorganized_dirs.keys():
                                try:
                                    dir_path.relative_to(category_dir)
                                    dir_category_dir = category_dir
                                    break
                                except ValueError:
                                    continue
                            
                            if not dir_category_dir:
                                continue
                            
                            # Create destination path in category's unorganized_files
                            relative_to_category = dir_path.relative_to(dir_category_dir)
                            unorganized_dir = category_unorganized_dirs[dir_category_dir]
                            
                            # Preserve directory structure within unorganized_files
                            if relative_to_category.parent == Path('.'):
                                dest_path = unorganized_dir / dir_name
                            else:
                                dest_path = unorganized_dir / relative_to_category.parent / dir_name
                            
                            # Ensure parent directory exists
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Move directory
                            if dest_path.exists():
                                # If destination exists, merge contents
                                for item in dir_path.iterdir():
                                    item_dest = dest_path / item.name
                                    if item.is_file():
                                        if item_dest.exists():
                                            # Append number if file exists
                                            counter = 1
                                            stem = item_dest.stem
                                            suffix = item_dest.suffix
                                            while item_dest.exists():
                                                item_dest = dest_path / f"{stem}_{counter}{suffix}"
                                                counter += 1
                                        move_file_cross_device(item, item_dest)
                                    elif item.is_dir():
                                        if item_dest.exists():
                                            # Merge directories recursively
                                            for subitem in item.iterdir():
                                                subitem_dest = item_dest / subitem.name
                                                if subitem.is_file():
                                                    if subitem_dest.exists():
                                                        counter = 1
                                                        stem = subitem_dest.stem
                                                        suffix = subitem_dest.suffix
                                                        while subitem_dest.exists():
                                                            subitem_dest = item_dest / f"{stem}_{counter}{suffix}"
                                                            counter += 1
                                                    move_file_cross_device(subitem, subitem_dest)
                                                else:
                                                    # Recursively copy directory
                                                    if not subitem_dest.exists():
                                                        shutil.copytree(subitem, subitem_dest)
                                                    # Remove source subdirectory after copying
                                                    if item.exists():
                                                        try:
                                                            shutil.rmtree(subitem)
                                                        except OSError:
                                                            pass
                                        else:
                                            # Simple move for subdirectory
                                            item.rename(item_dest)
                                # Remove source directory if empty
                                try:
                                    if not list(dir_path.iterdir()):
                                        dir_path.rmdir()
                                except OSError:
                                    pass
                            else:
                                # Simple move - use cross-device move for safety
                                try:
                                    # Try rename first (fast)
                                    dir_path.rename(dest_path)
                                except OSError:
                                    # If rename fails (cross-device), use copy+delete
                                    shutil.copytree(dir_path, dest_path)
                                    shutil.rmtree(dir_path)
                            
                            self.logger.info(f"Moved directory to unorganized: {dir_path} -> {dest_path}")
                            stats['dirs_moved_to_unorganized'] += 1
                        except Exception as e:
                            self.logger.debug(f"Could not move directory {dir_path}: {e}")
                
                # Try to remove empty directory (but not unorganized_files directories or category folders)
                is_unorganized_dir = any(unorganized_dir == root_path or unorganized_dir in root_path.parents
                                       for unorganized_dir in category_unorganized_dirs.values())
                is_category_dir = root_path in category_unorganized_dirs.keys()
                
                if root_path != output_dir and not is_unorganized_dir and not is_category_dir:
                    try:
                        contents = list(root_path.iterdir())
                        if not contents:
                            root_path.rmdir()
                            self.logger.info(f"Removed empty output directory: {root_path}")
                            stats['empty_dirs_removed'] += 1
                    except OSError:
                        # Directory not empty or error, skip
                        pass
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up output directory: {e}")
        
        return stats
    
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
            
            # Track source directory for cleanup (if we moved from a different location)
            if move_plan['changed'] and move_plan['from'].parent != move_plan['to'].parent:
                source_dir = move_plan['from'].parent
                if source_dir.exists():
                    # Store source directory for later cleanup
                    if not hasattr(self, '_source_directories'):
                        self._source_directories = set()
                    self._source_directories.add(source_dir)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            return False
