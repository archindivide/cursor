# Usage Examples

## Real-World Example: Organizing Downloads Folder

```
Input: C:\Users\archd\Downloads
Output: organized_media/

Results:
- 16 photos → organized_media/photos/
- 5 movies → organized_media/movies/
- 10 unsorted videos → organized_media/unsorted/
- 1 music file → organized_media/music/
```

### Before (Messy):
```
Downloads/
  ├── 2025-02-25 20-21-53.mkv
  ├── dipshit.mp4
  ├── Friday_Rats-1.mp4
  ├── WhatsApp-Kuva_2024-10-20_klo_18.54.04_0f1a3194.jpg
  ├── 01 Storm Of The Century Part 1 - Stephen King Mini-Series 1999 Eng Fre Ita Multi-Subs [H264-mp4].mp4
  ├── Begotten.1991.DVDRip.XviD-QiX.avi
  ├── besthd-ltroi-1080p.mkv
  └── besthd-ltroi-1080p.nfo
```

### After (Clean):
```
organized_media/
  ├── movies/
  │   ├── Begotten.1991.avi
  │   ├── 2025-02-25.20-21-53.2025.mkv
  │   ├── 01.Storm.Of.The.Century.Part.1.-.Stephen.King.Mini-Series.1999.mp4
  │   ├── 02.Storm.Of.The.Century.Part.2.-.Stephen.King.Mini-Series.1999.mp4
  │   └── 03.Storm.Of.The.Century.Part.3.-.Stephen.King.Mini-Series.1999.mp4
  ├── unsorted/
  │   ├── dipshit.mp4
  │   ├── Friday.Rats-1.mp4
  │   ├── besthd-ltroi-1080p.mkv
  │   └── besthd-ltroi-1080p.nfo
  ├── photos/
  │   └── WhatsApp-Kuva.2024.jpg
  └── music/
      └── ...mp3 files
```

## File Detection Logic

### Movies (→ `movies/`)
- Has a year in filename: `Movie (2020).mkv` → `Movie.2020.mkv`
- Has title + year: `The.Great.Movie.2021.mkv` → `The.Great.Movie.2021.mkv`
- Example: `Begotten.1991.DVDRip.avi` → `Begotten.1991.avi`

### TV Shows (→ `tv_shows/Show.Name/Season X/`)
- Has season/episode pattern: `Show S01E01.mkv` → `Show.Name/Season 01/Show.Name.S01E01.mkv`
- Example: `Breaking.Bad.S02E15.720p.mkv` → `Breaking.Bad/Season 02/Breaking.Bad.S02E15.mkv`

### Unsorted (→ `unsorted/`)
- Video without clear movie/TV pattern: `dipshit.mp4` → `unsorted/dipshit.mp4`
- Files with non-movie indicators: `sample-trailer.mkv` → `unsorted/sample.trailer.mkv`
- Example: `random-video-file.mp4` → `unsorted/random-video-file.mp4`

### Photos (→ `photos/`)
- Image files: `image.jpg`, `photo.png`, etc.

### Music (→ `music/`)
- Audio files: `song.mp3`, `album.flac`, etc.

## Common Commands

**Windows:**
```bash
# Preview your library organization
python main.py organize "C:\Downloads" --dry-run

# Organize into default location
python main.py organize "C:\Downloads"

# Organize to custom location
python main.py organize "C:\Downloads" --output-dir "D:\Media\Organized"

# Find duplicates after organization
python main.py detect-duplicates "D:\Media\Organized"

# Remove duplicates (be careful!)
python main.py remove-duplicates "D:\Media\Organized" --dry-run
python main.py remove-duplicates "D:\Media\Organized"
```

**Linux/macOS:**
```bash
# Preview your library organization
python main.py organize "/home/username/Downloads" --dry-run

# Organize into default location
python main.py organize "/home/username/Downloads"

# Organize to custom location
python main.py organize "/home/username/Downloads" --output-dir "/media/organized"

# Find duplicates after organization
python main.py detect-duplicates "/media/organized"

# Remove duplicates (be careful!)
python main.py remove-duplicates "/media/organized" --dry-run
python main.py remove-duplicates "/media/organized"
```




