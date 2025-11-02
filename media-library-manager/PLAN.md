# Media Library Manager - Project Plan

## Overview
A Python application that automatically organizes and cleans media libraries by:
1. **Standardizing file and folder names** (remove special characters, consistent formatting)
2. **Organizing directory structure** (group by type, genre, year, or other criteria)
3. **Removing duplicates** (hash-based detection)
4. **Generating NFO files** (for Kodi/Plex compatibility)
5. **Metadata management** (extract, fix, and enrich)

## Current Status

**✅ Phase 1 Complete**: Foundation is implemented with:
- Complete project structure
- Configuration system with YAML support
- File scanning and discovery
- Basic file hashing (MD5/SHA) for duplicates
- Logging system with file and console output
- CLI interface with Click

**✅ Phase 2 Basic**: Duplicate detection implemented:
- Hash-based duplicate finder (working)
- Duplicate preview and removal (working)

**✅ Phase 6 Complete**: File organization and naming standardization:
- Flat movie structure: `movies/Movie.Name.Year.ext`
- TV show organization: `tv_shows/Show.Name/Season X/episode.ext`
- Unsorted folder for unrecognized videos
- Smart filename sanitization and pattern extraction
- Preserves associated files (subtitles, NFO, etc.)
- Configurable output directory

**📋 Next Steps**: Metadata extraction and enrichment (Phase 3)

## Core Features

### 1. Duplicate Detection & Removal
- **File-based detection**: MD5/SHA-256 hash comparison
- **Content-based detection**: Video fingerprinting for similar content
- **Metadata-based detection**: Compare title, year, duration, resolution
- **Smart removal**: Keep highest quality/file size, preserve subtitles/torrents
- **Preview mode**: Show duplicates before deletion

### 2. Metadata Management
- **Video metadata**:
  - Extract: resolution, codec, bitrate, duration, framerate
  - Sources: embedded metadata, filename parsing, external APIs (TMDB, TVDB)
  - Enrichment: download movie/tv show info, posters, plot summaries
- **Audio metadata**:
  - ID3 tags for MP3, FLAC, OGG
  - Metadata from MusicBrainz/Discogs
- **Photo metadata**:
  - EXIF data extraction
  - Camera info, GPS coordinates, timestamps

### 3. NFO File Management
- **Generate NFO files**:
  - Movie: MovieDB format (compatible with Kodi/Plex)
  - TV Shows: episode/season NFO files
  - Music: album and track NFO files
- **Synchronize metadata**: Update NFO when media changes
- **Preserve custom edits**: Don't overwrite user-modified NFO files

### 4. File Organization
- **Smart naming**: Standardize filenames based on metadata
  - Example: `Movie Name (Year) [Resolution].mkv`
- **Directory structure**: Organize by type, genre, year, etc.
- **File type detection**: Movies vs TV shows vs music
- **Symlink management**: Create organized views without moving files

## Technical Architecture

### Core Libraries
- **Media processing**: `ffmpeg-python`, `Pillow` (PIL)
- **Metadata**: `mutagen` (audio), `python-exiv2` (photos), `tinytag`
- **Hashing**: Built-in `hashlib` for file hashing
- **API clients**: `tmdbsimple`, `tvdb_api`, `discogs_client`
- **Config**: `pyyaml` or `toml`
- **Logging**: Built-in `logging` module

### Project Structure
```
media-library-manager/
├── media_manager/
│   ├── __init__.py
│   ├── core/
│   │   ├── scanner.py          # File system scanning
│   │   ├── hasher.py           # File hashing
│   │   └── duplicate_finder.py # Duplicate detection logic
│   ├── metadata/
│   │   ├── video_metadata.py   # Video metadata extraction
│   │   ├── audio_metadata.py   # Audio metadata
│   │   ├── photo_metadata.py   # Photo EXIF data
│   │   └── api_clients.py      # External API wrappers
│   ├── nfo/
│   │   ├── generator.py        # NFO file generation
│   │   └── parser.py           # NFO file parsing
│   ├── organizer/
│   │   ├── file_organizer.py   # Rename and organize files
│   │   └── directory_structure.py # Create folder structures
│   └── utils/
│       ├── config.py           # Configuration management
│       ├── logger.py           # Logging setup
│       └── file_utils.py       # File operations
├── config/
│   ├── default_config.yaml     # Default configuration
│   └── rules.yaml              # Organization rules
├── tests/
│   └── (unit and integration tests)
├── main.py                     # CLI entry point
├── requirements.txt
├── README.md
└── PLAN.md
```

## Implementation Phases

### Phase 1: Foundation ✅ COMPLETE
- [x] Project structure setup
- [x] Configuration system
- [x] File scanning and discovery
- [x] Basic file hashing for duplicates
- [x] Logging system

### Phase 2: Duplicate Detection ✅ BASIC COMPLETE
- [x] MD5/SHA hash-based duplicate finder
- [x] Duplicate preview and removal
- [ ] Advanced duplicate detection (future)

### Phase 6: File Organization & Naming ✅ COMPLETE
- [x] Filename sanitization (remove special chars, normalize)
- [x] Smart renaming based on patterns and metadata
- [x] Directory structure creation (flat movies, organized TV shows)
- [x] Preserve file relationships (subtitles, NFO files)
- [x] Dry-run mode for preview
- [x] CLI integration with output directory options

### Phase 3: Metadata Extraction (Week 3)
- [ ] Video metadata extraction (ffmpeg)
- [ ] Audio metadata (mutagen)
- [ ] Photo EXIF extraction
- [ ] Filename parsing for metadata
- [ ] Metadata cache/database

### Phase 4: External API Integration (Week 4)
- [ ] TMDB integration for movies
- [ ] TVDB integration for TV shows
- [ ] MusicBrainz/Discogs integration
- [ ] API result caching
- [ ] Rate limiting

### Phase 5: NFO Generation (Week 5)
- [ ] NFO file format specifications
- [ ] Movie NFO generator
- [ ] TV show NFO generator
- [ ] Music NFO generator
- [ ] Update existing NFO files

### Phase 3-5: Future Enhancements
- [ ] Metadata extraction (video, audio, photo)
- [ ] External API integration (TMDB, TVDB, MusicBrainz)
- [ ] NFO file generation

### Phase 7: CLI & Polish (Week 7)
- [x] Command-line interface
- [x] Progress bars and reporting
- [x] Error handling and recovery
- [x] Documentation
- [ ] User guide

## Configuration Example

```yaml
# config/default_config.yaml
media_library:
  movie_paths:
    - "/media/movies"
  tv_show_paths:
    - "/media/tv"
  music_paths:
    - "/media/music"
  photo_paths:
    - "/media/photos"

duplicate_detection:
  enabled: true
  methods:
    - hash
    - metadata
    - fingerprint
  auto_remove: false
  keep_criteria: "highest_quality"

metadata:
  sources:
    - embedded
    - filename
    - tmdb
    - tvdb
  api_keys:
    tmdb: ""
    tvdb: ""

organization:
  naming_pattern: "{title} ({year}) [{resolution}]"
  create_subdirectories: true
  organize_by: "genre"
  
nfo:
  enabled: true
  overwrite_existing: false
  format: "kodi"
```

## CLI Commands

```bash
# Scan and show duplicates
python main.py detect-duplicates /path/to/media

# Remove duplicates (dry run)
python main.py remove-duplicates /path/to/media --dry-run

# Generate NFO files
python main.py generate-nfo /path/to/media

# Organize files
python main.py organize /path/to/media

# Full library maintenance
python main.py maintain --all
```

## Future Enhancements
- Web UI for easier management
- Integration with Plex/Jellyfin/Kodi
- Automatic subtitle downloading
- Quality upgrade detection (e.g., replace SD with HD)
- Cloud storage sync
- Multi-library support
- Scheduled maintenance tasks
- Machine learning for better duplicate detection
