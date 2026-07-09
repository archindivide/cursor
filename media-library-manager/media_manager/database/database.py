"""SQLite database for tracking media library files and directories."""

import sqlite3
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class MediaDatabase:
    """SQLite database manager for media library tracking."""
    
    def __init__(self, db_path: str = None, logger=None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (defaults to media_library.db in project root)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        if db_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "media_library.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Directories table - tracks input and output directories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                directory_type TEXT NOT NULL,  -- 'input' or 'output'
                media_type TEXT,  -- 'movies', 'tv_shows', 'music', 'photos', or NULL for general
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scanned_at TIMESTAMP,
                notes TEXT
            )
        """)
        
        # Files table - tracks all files in the library
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT,  -- SHA256 hash of file (can be empty if not computed)
                original_path TEXT NOT NULL,  -- First known path
                current_path TEXT NOT NULL,  -- Current location
                filename TEXT NOT NULL,
                extension TEXT,
                media_type TEXT,  -- 'movies', 'tv_shows', 'music', 'photos'
                is_recognized BOOLEAN DEFAULT 0,  -- Matches known patterns
                file_size INTEGER,  -- Size in bytes
                mtime TIMESTAMP,  -- Modification time
                title TEXT,
                year INTEGER,
                season INTEGER,
                episode INTEGER,
                quality TEXT,
                codec TEXT,
                directory_id INTEGER,  -- Foreign key to directories
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (directory_id) REFERENCES directories(id)
            )
        """)
        
        # File movements table - tracks file location changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                from_path TEXT NOT NULL,
                to_path TEXT NOT NULL,
                movement_type TEXT DEFAULT 'organize',  -- 'organize', 'manual', 'cleanup'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # Associated files table - tracks files associated with main media files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS associated_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                main_file_id INTEGER NOT NULL,
                associated_file_id INTEGER NOT NULL,
                association_type TEXT DEFAULT 'related',  -- 'related', 'subtitle', 'metadata', 'image'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (main_file_id) REFERENCES files(id) ON DELETE CASCADE,
                FOREIGN KEY (associated_file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_current_path ON files(current_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_directory ON files(directory_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_media_type ON files(media_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directories_path ON directories(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directories_type ON directories(directory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movements_file ON file_movements(file_id)")
        
        self.conn.commit()
        self.logger.info(f"Database initialized at: {self.db_path}")
    
    def add_directory(self, path: str, directory_type: str, media_type: str = None, 
                      enabled: bool = True, notes: str = None) -> int:
        """
        Add or update a directory in the database.
        
        Args:
            path: Directory path (normalized)
            directory_type: 'input' or 'output'
            media_type: 'movies', 'tv_shows', 'music', 'photos', or None
            enabled: Whether directory is enabled
            notes: Optional notes about the directory
        
        Returns:
            Directory ID
        """
        cursor = self.conn.cursor()
        normalized_path = str(Path(path).resolve())
        
        cursor.execute("""
            INSERT OR REPLACE INTO directories (path, directory_type, media_type, enabled, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (normalized_path, directory_type, media_type, enabled, notes))
        
        self.conn.commit()
        directory_id = cursor.lastrowid
        self.logger.debug(f"Added/updated directory: {normalized_path} (type: {directory_type})")
        return directory_id
    
    def get_directory(self, path: str = None, directory_id: int = None) -> Optional[Dict]:
        """
        Get directory information.
        
        Args:
            path: Directory path (normalized)
            directory_id: Directory ID
        
        Returns:
            Directory record as dict or None
        """
        cursor = self.conn.cursor()
        
        if directory_id:
            cursor.execute("SELECT * FROM directories WHERE id = ?", (directory_id,))
        elif path:
            normalized_path = str(Path(path).resolve())
            cursor.execute("SELECT * FROM directories WHERE path = ?", (normalized_path,))
        else:
            return None
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_directories(self, directory_type: str = None, enabled: bool = None) -> List[Dict]:
        """
        List directories.
        
        Args:
            directory_type: Filter by 'input' or 'output'
            enabled: Filter by enabled status
        
        Returns:
            List of directory records
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM directories WHERE 1=1"
        params = []
        
        if directory_type:
            query += " AND directory_type = ?"
            params.append(directory_type)
        
        if enabled is not None:
            query += " AND enabled = ?"
            params.append(1 if enabled else 0)
        
        query += " ORDER BY path"
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_directory_scan_time(self, directory_id: int):
        """Update the last scanned timestamp for a directory."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE directories 
            SET last_scanned_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (directory_id,))
        self.conn.commit()
    
    def add_file(self, file_path: Path, file_hash: str = None, media_type: str = None,
                 is_recognized: bool = False, directory_id: int = None,
                 title: str = None, year: int = None, season: int = None,
                 episode: int = None, quality: str = None, codec: str = None,
                 compute_hash: bool = True) -> int:
        """
        Add or update a file in the database.
        
        Args:
            file_path: Path to file
            file_hash: SHA256 hash of file (will compute if not provided)
            media_type: Media type classification
            is_recognized: Whether file matches known patterns
            directory_id: Associated directory ID
            title: Extracted title
            year: Extracted year
            season: Season number (for TV shows)
            episode: Episode number (for TV shows)
            quality: Video quality
            codec: Video codec
        
        Returns:
            File ID
        """
        cursor = self.conn.cursor()
        
        # Compute hash if not provided and compute_hash is True
        if not file_hash and compute_hash:
            file_hash = self._compute_file_hash(file_path)
        elif not file_hash:
            # Use empty string if hash not computed and not provided
            file_hash = ''
        
        normalized_path = str(file_path.resolve())
        filename = file_path.name
        extension = file_path.suffix.lower()
        
        # Get file metadata
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except (OSError, IOError) as e:
            self.logger.warning(f"Could not stat file {file_path}: {e}")
            file_size = None
            mtime = None
        
        # Check if file already exists by hash
        cursor.execute("SELECT id, current_path FROM files WHERE file_hash = ?", (file_hash,))
        existing = cursor.fetchone()
        
        if existing:
            file_id = existing['id']
            old_path = existing['current_path']
            
            # Update file if path changed
            if old_path != normalized_path:
                cursor.execute("""
                    UPDATE files 
                    SET current_path = ?, filename = ?, extension = ?, 
                        media_type = ?, is_recognized = ?, file_size = ?, mtime = ?,
                        title = ?, year = ?, season = ?, episode = ?, quality = ?, codec = ?,
                        directory_id = ?, updated_at = CURRENT_TIMESTAMP, last_seen_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (normalized_path, filename, extension, media_type, is_recognized,
                      file_size, mtime, title, year, season, episode, quality, codec,
                      directory_id, file_id))
                
                # Record movement
                self._record_movement(file_id, old_path, normalized_path, 'organize')
            else:
                # Just update metadata
                cursor.execute("""
                    UPDATE files 
                    SET media_type = ?, is_recognized = ?, file_size = ?, mtime = ?,
                        title = ?, year = ?, season = ?, episode = ?, quality = ?, codec = ?,
                        directory_id = ?, updated_at = CURRENT_TIMESTAMP, last_seen_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (media_type, is_recognized, file_size, mtime,
                      title, year, season, episode, quality, codec, directory_id, file_id))
        else:
            # New file
            cursor.execute("""
                INSERT INTO files (
                    file_hash, original_path, current_path, filename, extension,
                    media_type, is_recognized, file_size, mtime,
                    title, year, season, episode, quality, codec, directory_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_hash, normalized_path, normalized_path, filename, extension,
                  media_type, is_recognized, file_size, mtime,
                  title, year, season, episode, quality, codec, directory_id))
            file_id = cursor.lastrowid
        
        self.conn.commit()
        return file_id
    
    def get_file(self, file_id: int = None, file_path: Path = None, file_hash: str = None) -> Optional[Dict]:
        """
        Get file information.
        
        Args:
            file_id: File ID
            file_path: File path
            file_hash: File hash
        
        Returns:
            File record as dict or None
        """
        cursor = self.conn.cursor()
        
        if file_id:
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        elif file_path:
            normalized_path = str(file_path.resolve())
            cursor.execute("SELECT * FROM files WHERE current_path = ? OR original_path = ?", 
                         (normalized_path, normalized_path))
        elif file_hash:
            cursor.execute("SELECT * FROM files WHERE file_hash = ?", (file_hash,))
        else:
            return None
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_files(self, directory_id: int = None, media_type: str = None,
                  is_recognized: bool = None, limit: int = None) -> List[Dict]:
        """
        List files in the database.
        
        Args:
            directory_id: Filter by directory
            media_type: Filter by media type
            is_recognized: Filter by recognition status
            limit: Maximum number of results
        
        Returns:
            List of file records
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM files WHERE 1=1"
        params = []
        
        if directory_id:
            query += " AND directory_id = ?"
            params.append(directory_id)
        
        if media_type:
            query += " AND media_type = ?"
            params.append(media_type)
        
        if is_recognized is not None:
            query += " AND is_recognized = ?"
            params.append(1 if is_recognized else 0)
        
        query += " ORDER BY last_seen_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def move_file(self, file_id: int, new_path: Path, movement_type: str = 'organize'):
        """
        Update file location and record movement.
        
        Args:
            file_id: File ID
            new_path: New file path
            movement_type: Type of movement ('organize', 'manual', 'cleanup')
        """
        cursor = self.conn.cursor()
        
        # Get current path
        cursor.execute("SELECT current_path FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        if not row:
            return
        
        old_path = row['current_path']
        normalized_new_path = str(new_path.resolve())
        
        # Update file location
        cursor.execute("""
            UPDATE files 
            SET current_path = ?, filename = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (normalized_new_path, new_path.name, file_id))
        
        # Record movement
        self._record_movement(file_id, old_path, normalized_new_path, movement_type)
        self.conn.commit()
    
    def _record_movement(self, file_id: int, from_path: str, to_path: str, movement_type: str):
        """Record a file movement."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO file_movements (file_id, from_path, to_path, movement_type)
            VALUES (?, ?, ?, ?)
        """, (file_id, from_path, to_path, movement_type))
    
    def get_file_movements(self, file_id: int) -> List[Dict]:
        """Get movement history for a file."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM file_movements 
            WHERE file_id = ? 
            ORDER BY created_at DESC
        """, (file_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_associated_files(self, main_file_id: int, associated_file_ids: List[int],
                            association_type: str = 'related'):
        """
        Associate files with a main file.
        
        Args:
            main_file_id: Main file ID
            associated_file_ids: List of associated file IDs
            association_type: Type of association
        """
        cursor = self.conn.cursor()
        for assoc_id in associated_file_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO associated_files 
                (main_file_id, associated_file_id, association_type)
                VALUES (?, ?, ?)
            """, (main_file_id, assoc_id, association_type))
        self.conn.commit()
    
    def get_associated_files(self, file_id: int) -> List[Dict]:
        """Get files associated with a main file."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT f.* FROM files f
            INNER JOIN associated_files af ON f.id = af.associated_file_id
            WHERE af.main_file_id = ?
        """, (file_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Count files by media type
        cursor.execute("""
            SELECT media_type, COUNT(*) as count 
            FROM files 
            GROUP BY media_type
        """)
        stats['files_by_type'] = {row['media_type'] or 'unknown': row['count'] 
                                 for row in cursor.fetchall()}
        
        # Total files
        cursor.execute("SELECT COUNT(*) as count FROM files")
        stats['total_files'] = cursor.fetchone()['count']
        
        # Recognized vs unrecognized
        cursor.execute("""
            SELECT is_recognized, COUNT(*) as count 
            FROM files 
            GROUP BY is_recognized
        """)
        stats['recognition'] = {('recognized' if row['is_recognized'] else 'unrecognized'): row['count']
                               for row in cursor.fetchall()}
        
        # Directory counts
        cursor.execute("SELECT COUNT(*) as count FROM directories")
        stats['total_directories'] = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT directory_type, COUNT(*) as count 
            FROM directories 
            GROUP BY directory_type
        """)
        stats['directories_by_type'] = {row['directory_type']: row['count'] 
                                       for row in cursor.fetchall()}
        
        # Total file size
        cursor.execute("SELECT SUM(file_size) as total_size FROM files WHERE file_size IS NOT NULL")
        result = cursor.fetchone()
        stats['total_size'] = result['total_size'] or 0
        
        return stats
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, IOError) as e:
            self.logger.error(f"Error hashing file {file_path}: {e}")
            return ''
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

