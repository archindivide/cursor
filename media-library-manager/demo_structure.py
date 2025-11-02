#!/usr/bin/env python3
"""Demonstration of the Media Library Manager with organized directory structure."""

import sys
from pathlib import Path
from media_manager import Config, setup_logger
from media_manager.organizer.file_organizer import FileOrganizer


def demo_directory_structure():
    """Demonstrate the new organized directory structure."""
    
    # Setup
    config = Config()
    logger = setup_logger(level="INFO", console=False)
    organizer = FileOrganizer(config, logger)
    
    print("=" * 80)
    print("MEDIA LIBRARY MANAGER - ORGANIZED DIRECTORY STRUCTURE")
    print("=" * 80)
    print()
    print("This demonstrates how files are organized into a clean directory structure")
    print("instead of just renaming files in place.")
    print()
    
    # Demo files with various patterns
    demo_files = [
        # Movies
        "[YTS] The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Movie Name (2020) [1080p] [HEVC].mkv", 
        "The.Great.Movie.2021.1080p.BluRay.x264.mkv",
        "Action.Movie.2015.720p.x264.mkv",
        
        # TV Shows
        "Show Name - S01E01 - Episode Name.1080p.HEVC.mkv",
        "Show.Name.S01E02.1080p.HEVC.mkv",
        "Series.Title.S02E15.720p.x264.mkv",
        "Another.Show.S01E05.1080p.mkv",
        
        # Unsorted files (videos that don't match patterns)
        "random-video-file.mp4",
        "sample-trailer.mkv",
        "intro-video.mp4",
        "some-random-file.wmv",
        
        # Music
        "Artist - Album - Song.mp3",
        "Music.File.flac",
    ]
    
    # Create output directory
    output_dir = Path("demo_organized")
    
    print("ORGANIZED DIRECTORY STRUCTURE:")
    print("-" * 80)
    print(f"Output Directory: {output_dir.absolute()}")
    print()
    
    # Group files by media type for display
    media_groups = {}
    
    for filename in demo_files:
        file_path = Path(filename)
        
        # Plan the move
        move_plan = organizer.plan_file_move(file_path, output_dir)
        
        media_type = move_plan['media_type']
        if media_type not in media_groups:
            media_groups[media_type] = []
        
        media_groups[media_type].append(move_plan)
    
    # Display the structure
    for media_type, plans in media_groups.items():
        print(f"{media_type.upper()}:")
        print("-" * 40)
        
        for plan in plans:
            print(f"  {plan['from'].name}")
            print(f"    -> {plan['to']}")
            
            # Show associated files if any
            if plan['associated']:
                print("    Associated files:")
                for assoc in plan['associated']:
                    print(f"      {assoc['from'].name} -> {assoc['to']}")
            print()
    
    print("=" * 80)
    print("DIRECTORY STRUCTURE EXPLANATION:")
    print("=" * 80)
    print()
    print("MOVIES:")
    print("  organized_media/")
    print("    movies/")
    print("      The.Matrix.1999.mkv")
    print("      Movie.Name.2020.mkv")
    print("      The.Great.Movie.2021.mkv")
    print("      Action.Movie.2015.mkv")
    print()
    print("TV SHOWS:")
    print("  organized_media/")
    print("    tv_shows/")
    print("      Show.Name/")
    print("        Season 1/")
    print("          Show.Name.S01E01.mkv")
    print("          Show.Name.S01E02.mkv")
    print("      Series.Title/")
    print("        Season 2/")
    print("          Series.Title.S02E15.mkv")
    print()
    print("UNSORTED:")
    print("  organized_media/")
    print("    unsorted/")
    print("      random.video.file.mp4")
    print("      sample.trailer.mkv")
    print("      intro.video.mp4")
    print()
    print("MUSIC:")
    print("  organized_media/")
    print("    music/")
    print("      Artist.-.Album.-.Song.mp3")
    print("      Music.File.flac")
    print()
    print("KEY FEATURES:")
    print("- Creates new organized structure (doesn't modify original)")
    print("- Flat movie structure: all movies in movies/ folder")
    print("- TV shows organized by show name and season")
    print("- Unsorted folder for unrecognized videos")
    print("- Preserves associated files (subtitles, NFO, etc.)")
    print("- Clean dot-separated filenames")
    print("- Configurable output directory")
    
    print("\n" + "=" * 80)
    print("USAGE:")
    print("=" * 80)
    print("1. Preview the new structure:")
    print("   python main.py organize /path/to/messy/media --dry-run")
    print()
    print("2. Organize into default directory:")
    print("   python main.py organize /path/to/messy/media")
    print()
    print("3. Organize into custom directory:")
    print("   python main.py organize /path/to/messy/media --output-dir /path/to/clean/media")
    print()
    print("4. Configure output directory in config:")
    print("   Edit config/local_config.yaml:")
    print("   organization:")
    print("     output_directory: '/path/to/your/clean/media'")


if __name__ == '__main__':
    demo_directory_structure()
