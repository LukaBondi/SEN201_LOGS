"""
DatabaseManager.py
Author: Chayenchanadhip Sevikul
Date: 2025-10-06

Purpose:
    This module manages a SQLite database that stores image metadata.
    It handles database initialization, table creation, and provides
    basic query functionality for image data including:
    - Name
    - Album
    - Tags
    - File path
"""

import sqlite3
from typing import List, Tuple, Optional


class DatabaseManager:
    """
    Handles SQLite database operations for image metadata.
    """

    def __init__(self, dbPath: str = "photo_catalog.db"):
        """
        Initialize the DatabaseManager and ensure the table exists.

        Args:
            dbPath (str): Path to the SQLite database file.
        """
        self.dbPath = dbPath
        self._createTable()

    def _createTable(self):
        """Create the photos table if it does not already exist."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_path TEXT UNIQUE NOT NULL,
                album TEXT,
                tags TEXT,
                description TEXT,
                date_added TEXT
            )
        """)
        # Ensure migration for older DBs: check for missing columns and add them if needed
        try:
            cursor.execute("PRAGMA table_info(photos)")
            cols = [row[1] for row in cursor.fetchall()]
            # Add 'album' column if it's missing in older DBs
            if 'album' not in cols:
                cursor.execute("ALTER TABLE photos ADD COLUMN album TEXT DEFAULT ''")
            # Add 'favorite' column if it's missing (added later in history)
            if 'favorite' not in cols:
                cursor.execute("ALTER TABLE photos ADD COLUMN favorite INTEGER DEFAULT 0")
        except Exception:
            # In case PRAGMA or ALTER TABLE fails (e.g., locked DB), continue gracefully
            pass
        # Ensure tags master table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                name TEXT PRIMARY KEY
            )
            """
        )
        connection.commit()
        connection.close()

    def insertImage(self, name: str, filePath: str, album: str = "",
                    tags: str = "", description: str = "", dateAdded: str = ""):
        """
        Insert a new image record into the database.

        Args:
            name (str): Name of the image.
            filePath (str): Path to the actual image file.
            album (str): Album the image belongs to.
            tags (str): Tags associated with the image.
            description (str): Description of the image.
            dateAdded (str): Date when the image was added.
        """
        from datetime import datetime
        if not dateAdded:
            dateAdded = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO photos (name, file_path, album, tags, description, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, filePath, album, tags, description, dateAdded))
        connection.commit()
        connection.close()

    def getAllImages(self) -> List[Tuple]:
        """
        Retrieve all image metadata from the database.

        Returns:
            List[Tuple]: A list of all image metadata records.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM photos")
        results = cursor.fetchall()
        connection.close()
        return results

    def getFavorites(self) -> List[Tuple]:
        """Return all photos marked as favorite."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM photos WHERE favorite = 1")
            results = cursor.fetchall()
        except sqlite3.OperationalError:
            # Column may not exist on older DBs; treat as empty
            results = []
        connection.close()
        return results

    def setFavoriteById(self, photoId: int, isFavorite: bool) -> None:
        """Mark a photo as favorite (1) or not (0) by id."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE photos SET favorite = ? WHERE id = ?", (1 if isFavorite else 0, photoId))
            connection.commit()
        finally:
            connection.close()

    def getImageByName(self, name: str) -> Optional[Tuple]:
        """
        Retrieve a single image record by name.

        Args:
            name (str): Name of the image to search for.

        Returns:
            Optional[Tuple]: The image record if found, else None.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM photos WHERE name = ?", (name,))
        result = cursor.fetchone()
        connection.close()
        return result

    # --- Tags master helpers ---
    def getAllTags(self) -> List[str]:
        """Return all tag names from the tags master table."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE")
        rows = cursor.fetchall()
        connection.close()
        return [r[0] for r in rows]

    def createTag(self, tag: str) -> None:
        """Create a tag in the tags master table (no-op if exists)."""
        tag = (tag or '').strip()
        if not tag:
            return
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (tag,))
            connection.commit()
        finally:
            connection.close()

    def deleteTag(self, tag: str) -> None:
        """Delete a tag from the tags table and remove it from all photos."""
        tag = (tag or '').strip()
        if not tag:
            return
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM tags WHERE name = ?", (tag,))
            # Remove from photos.tags strings
            cursor.execute("SELECT id, tags FROM photos WHERE tags IS NOT NULL AND tags != ''")
            rows = cursor.fetchall()
            for pid, tags_str in rows:
                parts = [t.strip() for t in tags_str.split(',') if t.strip()]
                new_parts = [t for t in parts if t.lower() != tag.lower()]
                if new_parts != parts:
                    new_tags = ", ".join(new_parts)
                    cursor.execute("UPDATE photos SET tags = ? WHERE id = ?", (new_tags, pid))
            connection.commit()
        finally:
            connection.close()

    # --- Photo tag helpers ---
    def updatePhotoTags(self, photoId: int, tags: str) -> None:
        """Update tags for a specific photo by id."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("UPDATE photos SET tags = ? WHERE id = ?", (tags, photoId))
        connection.commit()
        connection.close()

    def updatePhotoTagsByPath(self, filePath: str, tags: str) -> None:
        """Update tags for a specific photo by file path."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("UPDATE photos SET tags = ? WHERE file_path = ?", (tags, filePath))
        connection.commit()
        connection.close()

    def getImageByFilePath(self, filePath: str) -> Optional[Tuple]:
        """Retrieve a single image record by file path."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM photos WHERE file_path = ?", (filePath,))
        result = cursor.fetchone()
        connection.close()
        return result

    def updateImage(self, name: str, filePath: str, album: str = "",
                    tags: str = "", description: str = ""):
        """
        Update metadata for an existing image.

        Args:
            name (str): Name of the image to update.
            filePath (str): Updated file path.
            album (str): Updated album name.
            tags (str): Updated tags.
            description (str): Updated description.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE photos
            SET file_path = ?, album = ?, tags = ?, description = ?
            WHERE name = ?
        """, (filePath, album, tags, description, name))
        connection.commit()
        connection.close()

    def deleteImage(self, name: str):
        """
        Delete an image record from the database by name.

        Args:
            name (str): Name of the image to delete.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM photos WHERE name = ?", (name,))
        connection.commit()
        connection.close()

    def getAllAlbums(self) -> List[str]:
        """
        Get a list of all unique album names in the database.

        Returns:
            List[str]: List of album names.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT DISTINCT album FROM photos
            WHERE album IS NOT NULL AND album != ''
            ORDER BY album
        """)
        results = cursor.fetchall()
        connection.close()
        return [r[0] for r in results]

    def getPhotosByAlbum(self, album: str) -> List[Tuple]:
        """
        Retrieve all photos belonging to a specific album.

        Args:
            album (str): Name of the album.

        Returns:
            List[Tuple]: List of photo records in the album.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM photos WHERE album = ?", (album,))
        results = cursor.fetchall()
        connection.close()
        return results

    def renameAlbum(self, oldName: str, newName: str):
        """
        Rename an album by updating all photos in that album.

        Args:
            oldName (str): Current album name.
            newName (str): New album name.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("UPDATE photos SET album = ? WHERE album = ?",
                      (newName, oldName))
        connection.commit()
        connection.close()

    def deleteAlbum(self, album: str):
        """
        Remove album assignment from all photos (sets album to empty string).

        Args:
            album (str): Name of the album to delete.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("UPDATE photos SET album = '' WHERE album = ?",
                      (album,))
        connection.commit()
        connection.close()

    def setFavoriteByPath(self, filePath: str, isFavorite: bool) -> None:
        """Mark a photo as favorite using its file path."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE photos SET favorite = ? WHERE file_path = ?", (1 if isFavorite else 0, filePath))
            connection.commit()
        finally:
            connection.close()