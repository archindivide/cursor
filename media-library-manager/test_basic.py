#!/usr/bin/env python3
"""Basic test to verify the Media Library Manager setup."""

import sys
from pathlib import Path

# Import modules at the top level
from media_manager import Config, setup_logger
from media_manager.core.scanner import MediaScanner
from media_manager.core.hasher import FileHasher
from media_manager.core.duplicate_finder import DuplicateFinder
from media_manager.utils.file_utils import get_file_hash, get_file_size, format_file_size

def test_imports():
    """Test that all main modules can be imported."""
    print("Testing imports...")
    
    try:
        print("[OK] Core imports successful")
        print("[OK] Core modules imported successfully")
        print("[OK] Utility modules imported successfully")
        
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        config = Config()
        print("[OK] Configuration loaded successfully")
        
        # Test some config values
        extensions = config.get_all_extensions()
        print(f"[OK] Supported extensions: {len(extensions)}")
        
        paths = config.get_media_paths()
        print(f"[OK] Media paths configured: {len(paths)} types")
        
        return True
    except Exception as e:
        print(f"[FAIL] Configuration error: {e}")
        return False

def test_basic_operations():
    """Test basic file operations."""
    print("\nTesting basic operations...")
    
    try:
        # Test with this file
        test_file = Path(__file__)
        size = get_file_size(test_file)
        formatted = format_file_size(size)
        
        print(f"[OK] File size: {formatted}")
        return True
    except Exception as e:
        print(f"[FAIL] Operation error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Media Library Manager - Basic Setup Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_basic_operations
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    if all(results):
        print("[OK] All tests passed!")
        return 0
    else:
        print("[FAIL] Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
