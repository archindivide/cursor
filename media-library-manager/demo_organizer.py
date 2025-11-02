#!/usr/bin/env python3
"""Demonstration of the Media Library Manager file organizer."""

import sys
from pathlib import Path
from media_manager import Config, setup_logger
from media_manager.organizer.file_organizer import FileOrganizer


def demo_file_organizer():
    """Demonstrate file organizer with various examples."""
    
    # Setup
    config = Config()
    logger = setup_logger(level="INFO", console=False)
    organizer = FileOrganizer(config, logger)
    
    print("=" * 80)
    print("MEDIA LIBRARY MANAGER - FILE ORGANIZER DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demonstrates how the file organizer transforms messy filenames")
    print("into clean, standardized dot-separated names.")
    print()
    
    # Demo cases with real-world examples
    demo_files = [
        # Movies
        "[YTS] The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Movie Name (2020) [1080p] [HEVC].mkv", 
        "Bad___Title___2020___mkv___file.mkv",
        "The.Great.Movie.2021.1080p.BluRay.x264.mkv",
        "Movie-With-Dashes (2020) [4K].mkv",
        
        # TV Shows
        "Show Name - S01E01 - Episode Name.1080p.HEVC.mkv",
        "Show.Name.S01E01.1080p.HEVC.mkv",
        "Show Name S01E01 Episode Title.mkv",
        "Series.Title.S02E15.720p.x264.mkv",
        
        # Edge cases
        "No.Year.Movie.mkv",
        "Single.Word.mkv",
        "Multiple   Spaces   2020   .mkv",
    ]
    
    print("FILENAME TRANSFORMATIONS:")
    print("-" * 80)
    
    for i, filename in enumerate(demo_files, 1):
        file_path = Path(filename)
        
        # Extract pattern info
        pattern_info = organizer.extract_pattern_info(filename)
        
        # Generate new filename
        new_name = organizer.generate_new_filename(file_path, pattern_info)
        
        print(f"\n{i:2d}. {filename}")
        print(f"    -> {new_name}")
        
        # Show extracted info
        info_parts = []
        if pattern_info.get('title'):
            info_parts.append(f"Title: {pattern_info['title']}")
        if pattern_info.get('year'):
            info_parts.append(f"Year: {pattern_info['year']}")
        if pattern_info.get('season') and pattern_info.get('episode'):
            info_parts.append(f"S{pattern_info['season']}E{pattern_info['episode']}")
        if pattern_info.get('quality'):
            info_parts.append(f"Quality: {pattern_info['quality']}")
        if pattern_info.get('codec'):
            info_parts.append(f"Codec: {pattern_info['codec']}")
        
        if info_parts:
            print(f"    Info: {', '.join(info_parts)}")
    
    print("\n" + "=" * 80)
    print("KEY FEATURES DEMONSTRATED:")
    print("=" * 80)
    print("- Removes group tags: [YTS], [SomeGroup]")
    print("- Extracts year from parentheses: (2020)")
    print("- Detects TV show patterns: S01E01")
    print("- Identifies quality: 1080p, 4K, 720p")
    print("- Recognizes codecs: x264, HEVC")
    print("- Normalizes spaces and special characters")
    print("- Creates dot-separated format: Title.Year.ext")
    print("- Handles edge cases gracefully")
    
    print("\n" + "=" * 80)
    print("USAGE:")
    print("=" * 80)
    print("1. Preview changes (dry run):")
    print("   python main.py organize /path/to/media --dry-run")
    print()
    print("2. Apply changes:")
    print("   python main.py organize /path/to/media")
    print()
    print("3. The organizer will:")
    print("   - Scan for media files")
    print("   - Show what would be renamed")
    print("   - Ask for confirmation")
    print("   - Rename files and associated files (subtitles, NFO, etc.)")


if __name__ == '__main__':
    demo_file_organizer()
