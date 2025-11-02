# Quick Start Guide

## Installation

1. **Install Python dependencies:**
```bash
cd media-library-manager
pip install -r requirements.txt
```

2. **Configure the application:**

**Linux/macOS:**
```bash
cp config/default_config.yaml config/local_config.yaml
```

**Windows:**
```bash
copy config\default_config.yaml config\local_config.yaml
```

Then edit `config/local_config.yaml` and update the media paths to point to your directories:

**Windows example:**
```yaml
media_library:
  movie_paths:
    - "C:/Users/YourName/Movies"
    - "D:/Movies"
```

**Linux example:**
```yaml
media_library:
  movie_paths:
    - "/home/username/Videos/Movies"
    - "/media/movies"
```

## Basic Usage

### 1. Organize and Clean Up Files (RECOMMENDED FIRST)
```bash
# Preview what would be organized (dry run)
python main.py organize "C:/path/to/media" --dry-run

# Actually organize and create clean directory structure
python main.py organize "C:/path/to/media"

# Organize into custom directory
python main.py organize "C:/path/to/media" --output-dir "C:/path/to/clean/media"
```

### 2. Detect Duplicates
```bash
python main.py detect-duplicates "C:/path/to/media"
```

### 3. Remove Duplicates (Dry Run First!)
```bash
# Dry run to see what would be deleted
python main.py remove-duplicates "C:/path/to/media" --dry-run

# Actually remove duplicates
python main.py remove-duplicates "C:/path/to/media"
```

### 4. Scan for Media Files
```bash
python main.py scan "C:/path/to/media"
```

### 5. View Configuration
```bash
python main.py info
```

## Example Workflow

```bash
# 1. Organize and clean up filenames with new directory structure (dry run first!)
python main.py organize "D:/Movies" --dry-run

# 2. If the preview looks good, actually organize
python main.py organize "D:/Movies"

# 3. Check for duplicates after cleanup
python main.py detect-duplicates "D:/Movies"

# 4. Remove duplicates if any (dry run first!)
python main.py remove-duplicates "D:/Movies" --dry-run
python main.py remove-duplicates "D:/Movies"

# 5. Scan to see your organized library
python main.py scan "D:/Movies"
```

## Directory Structure

The organizer creates a clean, organized directory structure:

**Movies:**
```
organized_media/
  movies/
    The.Matrix.1999.mkv
    Movie.Name.2020.mkv
    Begotten.1991.mkv
```

**TV Shows:**
```
organized_media/
  tv_shows/
    Show.Name/
      Season 01/
        Show.Name.S01E01.mkv
        Show.Name.S01E02.mkv
```

**Unsorted:**
```
organized_media/
  unsorted/
    random.video.file.mp4
    sample.trailer.mkv
```

**Music:**
```
organized_media/
  music/
    Artist.-.Album.-.Song.mp3
```

## Configuration Tips

- **Output Directory**: Set `organization.output_directory` in config
- **Duplicate Detection**: Configure which method to use (hash, metadata, fingerprint)
- **Keep Criteria**: Choose what to keep (highest_quality, smallest, oldest, newest)
- **API Keys**: Add TMDB/TVDB keys for better metadata (optional)

See `config/default_config.yaml` for all options.

## Safety Features

- **Dry Run Mode**: Always test with `--dry-run` before deleting
- **Confirmation Prompts**: Built-in confirmation before deletion
- **Logging**: All actions are logged to file
- **Keep Criteria**: Smart selection of which duplicate to keep

## Next Steps

The following features are planned for future releases:
- Metadata extraction and enrichment
- NFO file generation
- File organization and renaming
- External API integration (TMDB, TVDB)

See `PLAN.md` for the full roadmap.
