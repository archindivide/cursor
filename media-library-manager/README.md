# Media Library Manager

A Python application that automatically organizes and maintains a media library by managing metadata, removing duplicates, and generating NFO files.

## Features

- **Cross-Platform Support**: Works on Windows, Linux, and macOS
- **File Organization & Cleaning**: Standardize file names, remove special characters, organize directory structure
- **Smart Directory Structure**: Creates organized folders by type, year, and show name
- **Unsorted Folder**: Automatically identifies and moves unrecognized files to unsorted/
- **Duplicate Detection**: Hash-based duplicate detection with smart removal
- **Smart Renaming**: Automatically rename files based on patterns (movies, TV shows, quality info)
- **Preserve Relationships**: Keep subtitles, NFO files, and other associated files together
- **Dry Run Mode**: Preview all changes before applying them
- **Metadata Management**: Extract and enrich metadata for videos, audio, and photos (future)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the application:
```bash
# Linux/macOS
cp config/default_config.yaml config/local_config.yaml

# Windows
copy config\default_config.yaml config\local_config.yaml

# Then edit config/local_config.yaml with your paths and API keys
```

## Usage

```bash
# Organize and clean up filenames with new directory structure (RECOMMENDED - start here!)
python main.py organize /path/to/media --dry-run  # Preview changes
python main.py organize /path/to/media             # Apply changes

# Organize into custom directory
python main.py organize /path/to/media --output-dir /path/to/clean/media

# Detect duplicates
python main.py detect-duplicates /path/to/media

# Remove duplicates (dry run recommended!)
python main.py remove-duplicates /path/to/media --dry-run
python main.py remove-duplicates /path/to/media

# Scan your library
python main.py scan /path/to/media
```

### Cross-Platform Examples

**Windows:**
```bash
python main.py organize "C:\Users\YourName\Videos" --dry-run
python main.py organize "D:\Movies" --output-dir "D:\Organized\Movies"
python main.py detect-duplicates "C:\Users\YourName\Videos"
```

**Linux/macOS:**
```bash
python main.py organize "/home/username/Videos" --dry-run
python main.py organize "/media/movies" --output-dir "/media/organized"
python main.py detect-duplicates "/home/username/Videos"
```

## Configuration

See `config/default_config.yaml` for configuration options.

## Project Status

See `PLAN.md` for detailed implementation plan and progress tracking.
