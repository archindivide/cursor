#!/usr/bin/env python3
"""Test script to demonstrate file organizer functionality."""

import sys
from pathlib import Path
from media_manager import Config, setup_logger
from media_manager.organizer.file_organizer import FileOrganizer


def test_filename_transformations():
    """Test various filename transformations."""
    
    # Setup
    config = Config()
    logger = setup_logger(level="INFO", console=False)
    organizer = FileOrganizer(config, logger)
    
    # Test cases: (input_filename, expected_output)
    test_cases = [
        # Movies
        ("[SomeGroup] Movie.Name.2020.BDRip.x264.mkv", "Movie.Name.2020.mkv"),
        ("Movie Name (2020) [1080p] [HEVC].mkv", "Movie.Name.2020.mkv"),
        ("Bad___Title___2020___mkv___file.mkv", "Bad.Title.2020.mkv"),
        ("The.Great.Movie.2021.1080p.BluRay.x264.mkv", "The.Great.Movie.2021.mkv"),
        ("Movie-With-Dashes (2020) [4K].mkv", "Movie-With-Dashes.2020.mkv"),
        
        # TV Shows
        ("Show Name - S01E01 - Episode Name.1080p.HEVC.mkv", "Show.Name.S01E01.mkv"),
        ("Show.Name.S01E01.1080p.HEVC.mkv", "Show.Name.S01E01.mkv"),
        ("Show Name S01E01 Episode Title.mkv", "Show.Name.S01E01.mkv"),
        ("Series.Title.S02E15.720p.x264.mkv", "Series.Title.S02E15.mkv"),
        
        # Edge cases
        ("No.Year.Movie.mkv", "No.Year.Movie.mkv"),
        ("", ""),
        ("Single.Word.mkv", "Single.Word.mkv"),
        ("Multiple   Spaces   2020   .mkv", "Multiple.Spaces.2020.mkv"),
    ]
    
    print("=" * 80)
    print("FILE ORGANIZER TEST - Filename Transformations")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for input_name, expected in test_cases:
        # Create a mock file path
        file_path = Path(input_name)
        
        # Extract pattern info
        pattern_info = organizer.extract_pattern_info(input_name)
        
        # Generate new filename
        actual = organizer.generate_new_filename(file_path, pattern_info)
        
        # Check result
        if actual == expected:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"Input:    {input_name}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        
        if actual != expected:
            print(f"Pattern info: {pattern_info}")
    
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 80}")
    
    return failed == 0


def test_pattern_extraction():
    """Test pattern extraction from filenames."""
    
    config = Config()
    logger = setup_logger(level="INFO", console=False)
    organizer = FileOrganizer(config, logger)
    
    test_cases = [
        # Movies
        ("Movie Name (2020) [1080p]", {
            'title': 'Movie Name',
            'year': '2020',
            'quality': '1080p',
            'season': '',
            'episode': '',
            'codec': ''
        }),
        
        # TV Shows
        ("Show Name S01E01", {
            'title': 'Show Name',
            'year': '',
            'quality': '',
            'season': '01',
            'episode': '01',
            'codec': ''
        }),
        
        # Complex case
        ("The.Great.Movie.2021.1080p.BluRay.x264", {
            'title': 'The.Great.Movie',
            'year': '2021',
            'quality': '1080p',
            'season': '',
            'episode': '',
            'codec': 'AVC'
        }),
    ]
    
    print("\n" + "=" * 80)
    print("PATTERN EXTRACTION TEST")
    print("=" * 80)
    
    for filename, expected in test_cases:
        actual = organizer.extract_pattern_info(filename)
        
        print(f"\nFilename: {filename}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        
        # Check key fields
        matches = []
        for key in ['title', 'year', 'season', 'episode', 'quality', 'codec']:
            if actual.get(key) == expected.get(key):
                matches.append(f"{key}: PASS")
            else:
                matches.append(f"{key}: FAIL ({actual.get(key)} != {expected.get(key)})")
        
        print(f"Results:  {', '.join(matches)}")


def test_sanitization():
    """Test filename sanitization."""
    
    config = Config()
    logger = setup_logger(level="INFO", console=False)
    organizer = FileOrganizer(config, logger)
    
    test_cases = [
        ("[Group] Movie Name (2020)", "Movie Name (2020)"),
        ("{Group} Movie Name", "Movie Name"),
        ("Movie___Name___2020", "Movie Name 2020"),
        ("Movie...Name....2020", "Movie Name 2020"),
        ("Movie   Name   2020", "Movie Name 2020"),
        ("Movie<>Name|2020", "Movie_Name_2020"),
    ]
    
    print("\n" + "=" * 80)
    print("SANITIZATION TEST")
    print("=" * 80)
    
    for input_name, expected in test_cases:
        actual = organizer.sanitize_filename(input_name)
        
        print(f"Input:    {input_name}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Status:   {'PASS' if actual == expected else 'FAIL'}")
        print()


def main():
    """Run all tests."""
    print("Media Library Manager - File Organizer Test Suite")
    
    # Run tests
    test_sanitization()
    test_pattern_extraction()
    success = test_filename_transformations()
    
    if success:
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
