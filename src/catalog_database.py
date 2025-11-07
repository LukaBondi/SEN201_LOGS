"""
database_manager.py
Author: Chayenchanadhip Sevikul
Date: 2025-10-06

Purpose:
    This module manages a SQLite database for the photo catalog app.
    It handles database initialization, schema creation, and provides CRUD
    operations for photo metadata including:
    - Photo names, descriptions, and file information
    - Album organization and categorization  
    - Tag-based classification and filtering
    - File UUID references and duplicate detection
"""

import sqlite3
import uuid
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any

class CatalogDatabase:
    def __init__(self, db_path: str = "data/photos.db", storage_dir: str = "storage"):
        self.db_path = db_path
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self._init_database()
        except sqlite3.Error:
            self.conn = None
    
    def _init_database(self):
        """Initialize database with embedded schema"""
        try:
            schema_sql = """
            -- Photos table - core image metadata
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_uuid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                original_filename TEXT,
                description TEXT,
                file_type TEXT,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                favorite BOOLEAN DEFAULT FALSE,
                checksum TEXT UNIQUE
            );
            
            -- Albums table - for organizing photos
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );
            
            -- Tags table - for categorizing photos
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            
            -- Many-to-many: Photos can be in multiple albums
            CREATE TABLE IF NOT EXISTS photo_albums (
                photo_id INTEGER,
                album_id INTEGER,
                PRIMARY KEY (photo_id, album_id),
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
            );
            
            -- Many-to-many: Photos can have multiple tags
            CREATE TABLE IF NOT EXISTS photo_tags (
                photo_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (photo_id, tag_id),
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            
            -- Indexes for fast searching
            CREATE INDEX IF NOT EXISTS idx_photos_name ON photos(name);
            CREATE INDEX IF NOT EXISTS idx_photos_date_added ON photos(date_added);
            CREATE INDEX IF NOT EXISTS idx_photos_checksum ON photos(checksum);
            CREATE INDEX IF NOT EXISTS idx_albums_name ON albums(name);
            CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
            CREATE INDEX IF NOT EXISTS idx_photo_tags_tag_id ON photo_tags(tag_id);
            CREATE INDEX IF NOT EXISTS idx_photo_tags_photo_id ON photo_tags(photo_id);
            """
            
            cursor = self.conn.cursor()
            cursor.executescript(schema_sql)
            self.conn.commit()
            
            # Migration: Add original_filename column if it doesn't exist
            try:
                cursor.execute("PRAGMA table_info(photos)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'original_filename' not in columns:
                    cursor.execute("ALTER TABLE photos ADD COLUMN original_filename TEXT")
                    # Populate original_filename with current name for existing records
                    cursor.execute("UPDATE photos SET original_filename = name WHERE original_filename IS NULL")
                    self.conn.commit()
            except sqlite3.Error:
                pass
            
            return True
        except sqlite3.Error:
            return False
    
    def _calculate_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 checksum of file content"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return None
    
    # --- Photo Operations ---
    def add_photo(self, original_path: Path, name: str = None, description: str = "",
                  albums: List[str] = None, tags: List[str] = None) -> Optional[str]:
        """Add a photo to the catalog with metadata. Returns UUID or None on error."""
        if not original_path.exists():
            return None
        
        try:
            # Calculate checksum and check for duplicates
            checksum = self._calculate_checksum(original_path)
            if not checksum or self._photo_exists(checksum):
                return None  # Duplicate found or checksum failed
            
            # Generate UUID and file info
            file_uuid = str(uuid.uuid4())
            file_type = original_path.suffix.lower().lstrip('.')
            file_size = original_path.stat().st_size
            display_name = name or original_path.stem
            original_filename = original_path.name  # Store the original filename
            
            # Copy file to storage
            stored_path = self.storage_dir / f"{file_uuid}.{file_type}"
            shutil.copy2(original_path, stored_path)
            
            # Insert into database
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO photos (file_uuid, name, original_filename, description, file_type, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_uuid, display_name, original_filename, description, file_type, file_size, checksum))
            
            photo_id = cursor.lastrowid
            
            # Add to albums and tags
            if albums:
                for album_name in albums:
                    self._add_photo_to_album(photo_id, album_name)
            
            if tags:
                for tag_name in tags:
                    self._add_tag_to_photo(photo_id, tag_name)
            
            self.conn.commit()
            return file_uuid
            
        except (sqlite3.Error, IOError, OSError):
            return None
    
    def _photo_exists(self, checksum: str) -> bool:
        """Check if photo already exists by checksum"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM photos WHERE checksum = ?", (checksum,))
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False
    
    def _add_photo_to_album(self, photo_id: int, album_name: str) -> bool:
        """Add photo to album (creates album if needed). Returns success."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO albums (name) VALUES (?)", (album_name,))
            cursor.execute("""
                INSERT OR IGNORE INTO photo_albums (photo_id, album_id)
                SELECT ?, id FROM albums WHERE name = ?
            """, (photo_id, album_name))
            return True
        except sqlite3.Error:
            return False
    
    def _add_tag_to_photo(self, photo_id: int, tag_name: str) -> bool:
        """Add tag to photo (creates tag if needed). Returns success."""
        try:
            # Normalize tag name to lowercase to prevent duplicates with different cases
            tag_name = tag_name.strip().lower()
            if not tag_name:
                return False
            
            cursor = self.conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            cursor.execute("""
                INSERT OR IGNORE INTO photo_tags (photo_id, tag_id)
                SELECT ?, id FROM tags WHERE name = ?
            """, (photo_id, tag_name))
            return True
        except sqlite3.Error:
            return False
    
    def delete_photo(self, file_uuid: str) -> bool:
        """Delete a photo by UUID. Returns success."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM photos WHERE file_uuid = ?", (file_uuid,))
            deleted = cursor.rowcount > 0
            self.conn.commit()
            
            # Also delete the physical file
            if deleted:
                self._delete_photo_file(file_uuid)
            
            return deleted
        except sqlite3.Error:
            return False
    
    def _delete_photo_file(self, file_uuid: str) -> bool:
        """Delete physical photo file. Returns success."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_type FROM photos WHERE file_uuid = ?", (file_uuid,))
            result = cursor.fetchone()
            if result:
                file_path = self.storage_dir / f"{file_uuid}.{result['file_type']}"
                file_path.unlink(missing_ok=True)
                return True
            return False
        except sqlite3.Error:
            return False
    
    def update_photo(self, file_uuid: str, name: str = None, description: str = None,
                    favorite: bool = None) -> bool:
        """Update photo metadata. Returns success."""
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if favorite is not None:
                updates.append("favorite = ?")
                params.append(favorite)
            
            if not updates:
                return False
                
            params.append(file_uuid)
            cursor = self.conn.cursor()
            cursor.execute(f"UPDATE photos SET {', '.join(updates)} WHERE file_uuid = ?", params)
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def get_photo_path(self, file_uuid: str) -> Optional[Path]:
        """Get full file path from UUID. Returns Path or None."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_type FROM photos WHERE file_uuid = ?", (file_uuid,))
            result = cursor.fetchone()
            if result:
                return self.storage_dir / f"{file_uuid}.{result['file_type']}"
            return None
        except sqlite3.Error:
            return None

    # --- Album Management ---
    def create_album(self, name: str, description: str = "") -> bool:
        """Create a new album. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO albums (name, description) VALUES (?, ?)", 
                          (name, description))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Album already exists
        except sqlite3.Error:
            return False

    def update_album(self, old_name: str, new_name: str, description: str = None) -> bool:
        """Update album name and/or description. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            
            if description is not None:
                cursor.execute("""
                    UPDATE albums 
                    SET name = ?, description = ? 
                    WHERE name = ?
                """, (new_name, description, old_name))
            else:
                cursor.execute("""
                    UPDATE albums 
                    SET name = ? 
                    WHERE name = ?
                """, (new_name, old_name))
            
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False  # New name already exists
        except sqlite3.Error:
            return False

    def delete_album(self, album_name: str) -> bool:
        """Delete an album and remove all photo associations. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM albums WHERE name = ?", (album_name,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_all_albums(self) -> List[Dict]:
        """Get all albums. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM albums ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    # --- Tag Management ---
    def create_tag(self, tag_name: str) -> bool:
        """Create a new tag. Returns True if successful."""
        try:
            # Normalize tag name to lowercase to prevent duplicates with different cases
            tag_name = tag_name.strip().lower()
            if not tag_name:
                return False
            
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Tag already exists
        except sqlite3.Error:
            return False

    def update_tag(self, old_name: str, new_name: str) -> bool:
        """Update tag name. Returns True if successful."""
        try:
            # Normalize both tag names to lowercase
            old_name = old_name.strip().lower()
            new_name = new_name.strip().lower()
            if not old_name or not new_name:
                return False
            
            cursor = self.conn.cursor()
            cursor.execute("UPDATE tags SET name = ? WHERE name = ?", (new_name, old_name))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False  # New name already exists
        except sqlite3.Error:
            return False

    def delete_tag(self, tag_name: str) -> bool:
        """Delete a tag and remove all photo associations. Returns True if successful."""
        try:
            # Normalize tag name to lowercase
            tag_name = tag_name.strip().lower()
            if not tag_name:
                return False
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tags WHERE name = ?", (tag_name,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_all_tags(self) -> List[Dict]:
        """Get all tags. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tags ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    # --- Photo-Tag Relationship Management ---
    def add_tag_to_photo(self, file_uuid: str, tag_name: str) -> bool:
        """Add tag to photo (creates tag if needed). Returns True if successful."""
        try:
            # Normalize tag name to lowercase to prevent duplicates with different cases
            tag_name = tag_name.strip().lower()
            if not tag_name:
                return False
            
            # Ensure tag exists
            self.create_tag(tag_name)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO photo_tags (photo_id, tag_id)
                SELECT photos.id, tags.id 
                FROM photos, tags 
                WHERE photos.file_uuid = ? AND tags.name = ?
            """, (file_uuid, tag_name))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def remove_tag_from_photo(self, file_uuid: str, tag_name: str) -> bool:
        """Remove tag from photo. Returns True if successful."""
        try:
            # Normalize tag name to lowercase
            tag_name = tag_name.strip().lower()
            if not tag_name:
                return False
            
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM photo_tags 
                WHERE photo_id = (SELECT id FROM photos WHERE file_uuid = ?)
                AND tag_id = (SELECT id FROM tags WHERE name = ?)
            """, (file_uuid, tag_name))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def add_photo_to_album(self, file_uuid: str, album_name: str) -> bool:
        """Add photo to album (creates album if needed). Returns True if successful."""
        try:
            # Ensure album exists
            self.create_album(album_name)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO photo_albums (photo_id, album_id)
                SELECT photos.id, albums.id 
                FROM photos, albums 
                WHERE photos.file_uuid = ? AND albums.name = ?
            """, (file_uuid, album_name))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def remove_photo_from_album(self, file_uuid: str, album_name: str) -> bool:
        """Remove photo from album. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM photo_albums 
                WHERE photo_id = (SELECT id FROM photos WHERE file_uuid = ?)
                AND album_id = (SELECT id FROM albums WHERE name = ?)
            """, (file_uuid, album_name))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    # --- Search Operations ---
    def search_photos_by_name(self, query: str, sort_by: str = "name") -> List[Dict]:
        """Search photos by name with sorting. Returns empty list on error."""
        try:
            valid_sorts = {"name", "date_added"}
            sort_by = sort_by if sort_by in valid_sorts else "name"
            order_dir = "DESC" if sort_by == "date_added" else "ASC"
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT * FROM photos 
                WHERE name LIKE ? 
                ORDER BY {sort_by} {order_dir}
            """, (f"%{query}%",))
            
            photos = [dict(row) for row in cursor.fetchall()]
            for photo in photos:
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
            return photos
        except sqlite3.Error:
            return []
    
    def search_albums_by_name(self, query: str) -> List[Dict]:
        """Search albums by name. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM albums WHERE name LIKE ? ORDER BY name", (f"%{query}%",))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def search_tags_by_name(self, query: str) -> List[Dict]:
        """Search tags by name. Returns empty list on error."""
        try:
            # Normalize query to lowercase for case-insensitive search
            query = query.strip().lower()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tags WHERE name LIKE ? ORDER BY name", (f"%{query}%",))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def search_photos_by_tags(self, tags: List[str], require_all: bool = True) -> List[Dict]:
        """Search photos by tags (AND or OR logic). Returns empty list on error."""
        if not tags:
            return []
        
        try:
            # Normalize all tag names to lowercase
            tags = [tag.strip().lower() for tag in tags if tag.strip()]
            if not tags:
                return []
            
            placeholders = ','.join(['?'] * len(tags))
            
            if require_all:
                # AND logic - must have ALL tags
                query = f"""
                    SELECT p.* FROM photos p
                    WHERE p.id IN (
                        SELECT pt.photo_id FROM photo_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE t.name IN ({placeholders})
                        GROUP BY pt.photo_id
                        HAVING COUNT(DISTINCT t.name) = ?
                    )
                """
                params = tags + [len(tags)]
            else:
                # OR logic - must have ANY tag
                query = f"""
                    SELECT DISTINCT p.* FROM photos p
                    JOIN photo_tags pt ON p.id = pt.photo_id
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                """
                params = tags
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            photos = [dict(row) for row in cursor.fetchall()]
            for photo in photos:
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
            return photos
        except sqlite3.Error:
            return []
    
    def get_album_photos(self, album_name: str) -> List[Dict]:
        """Get all photos in an album with tags. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT p.* FROM photos p
                JOIN photo_albums pa ON p.id = pa.photo_id
                JOIN albums a ON pa.album_id = a.id
                WHERE a.name = ?
                ORDER BY p.date_added DESC
            """, (album_name,))
            
            photos = [dict(row) for row in cursor.fetchall()]
            for photo in photos:
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
                # Get tags for this photo and join them as comma-separated string
                tags_list = self.get_photo_tags(photo['file_uuid'])
                photo['tags'] = ', '.join(tags_list) if tags_list else ''
            return photos
        except sqlite3.Error:
            return []

    def photo_in_album(self, file_uuid: str, album_name: str) -> bool:
        """Return True if the photo (UUID) is already in the given album."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 1 FROM photo_albums pa
                JOIN photos p ON pa.photo_id = p.id
                JOIN albums a ON pa.album_id = a.id
                WHERE p.file_uuid = ? AND a.name = ?
            """, (file_uuid, album_name))
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def get_photos_not_in_album(self, album_name: str) -> List[Dict]:
        """Get all photos that are NOT already in the specified album with tags."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT p.* FROM photos p
                WHERE p.id NOT IN (
                    SELECT pa.photo_id FROM photo_albums pa
                    JOIN albums a ON pa.album_id = a.id
                    WHERE a.name = ?
                )
                ORDER BY p.date_added DESC
            """, (album_name,))
            photos = [dict(row) for row in cursor.fetchall()]
            for photo in photos:
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
                # Get tags for this photo and join them as comma-separated string
                tags_list = self.get_photo_tags(photo['file_uuid'])
                photo['tags'] = ', '.join(tags_list) if tags_list else ''
            return photos
        except sqlite3.Error:
            return []
    
    # --- Tag Management ---
    def get_photo_tags(self, file_uuid: str) -> List[str]:
        """Get all tags for a photo. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN photo_tags pt ON t.id = pt.tag_id
                JOIN photos p ON pt.photo_id = p.id
                WHERE p.file_uuid = ?
            """, (file_uuid,))
            return [row['name'] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    # --- Utility Methods ---
    def get_photo_by_uuid(self, file_uuid: str) -> Optional[Dict]:
        """Get a single photo by UUID with full path and tags. Returns None if not found."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM photos WHERE file_uuid = ?", (file_uuid,))
            row = cursor.fetchone()
            if row:
                photo = dict(row)
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
                photo['file_path'] = photo['full_path']  # Add file_path alias for compatibility
                # Get tags for this photo and join them as comma-separated string
                tags_list = self.get_photo_tags(photo['file_uuid'])
                photo['tags'] = ', '.join(tags_list) if tags_list else ''
                return photo
            return None
        except sqlite3.Error:
            return None

    def get_all_photos(self) -> List[Dict]:
        """Get all photos with full paths and tags. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM photos ORDER BY date_added DESC")
            
            photos = [dict(row) for row in cursor.fetchall()]
            for photo in photos:
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
                # Get tags for this photo and join them as comma-separated string
                tags_list = self.get_photo_tags(photo['file_uuid'])
                photo['tags'] = ', '.join(tags_list) if tags_list else ''
            return photos
        except sqlite3.Error:
            return []

    def get_photo_albums(self, file_uuid: str) -> List[str]:
        """Return list of album names a photo belongs to."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT a.name FROM albums a
                JOIN photo_albums pa ON a.id = pa.album_id
                JOIN photos p ON pa.photo_id = p.id
                WHERE p.file_uuid = ?
                ORDER BY a.name
            """, (file_uuid,))
            return [row['name'] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_favorite_photos(self) -> List[Dict]:
        """Get only photos marked as favorites with tags. Returns empty list on error."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM photos WHERE favorite = 1 ORDER BY date_added DESC")
            photos = [dict(row) for row in cursor.fetchall()]
            for photo in photos:
                photo['full_path'] = str(self.get_photo_path(photo['file_uuid']))
                # Get tags for this photo and join them as comma-separated string
                tags_list = self.get_photo_tags(photo['file_uuid'])
                photo['tags'] = ', '.join(tags_list) if tags_list else ''
            return photos
        except sqlite3.Error:
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics. Returns empty dict on error."""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM photos")
            total_photos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM albums")
            total_albums = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tags")
            total_tags = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM photos WHERE favorite = 1")
            favorite_photos = cursor.fetchone()[0]
            
            return {
                "total_photos": total_photos,
                "total_albums": total_albums,
                "total_tags": total_tags,
                "favorite_photos": favorite_photos
            }
        except sqlite3.Error:
            return {}
    
    def close(self):
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
        except sqlite3.Error:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()