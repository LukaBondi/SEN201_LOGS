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
        """Create the images table if it does not already exist."""
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                album TEXT,
                tags TEXT,
                filePath TEXT NOT NULL
            )
        """)
        connection.commit()
        connection.close()

    def insertImage(self, name: str, album: str, tags: str, filePath: str):
        """
        Insert a new image record into the database.

        Args:
            name (str): Name of the image.
            album (str): Album the image belongs to.
            tags (str): Tags associated with the image.
            filePath (str): Path to the actual image file.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO images (name, album, tags, filePath)
            VALUES (?, ?, ?, ?)
        """, (name, album, tags, filePath))
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
        cursor.execute("SELECT * FROM images")
        results = cursor.fetchall()
        connection.close()
        return results

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
        cursor.execute("SELECT * FROM images WHERE name = ?", (name,))
        result = cursor.fetchone()
        connection.close()
        return result

    def updateImage(self, name: str, album: str, tags: str, filePath: str):
        """
        Update metadata for an existing image.

        Args:
            name (str): Name of the image to update.
            album (str): Updated album name.
            tags (str): Updated tags.
            filePath (str): Updated file path.
        """
        connection = sqlite3.connect(self.dbPath)
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE images
            SET album = ?, tags = ?, filePath = ?
            WHERE name = ?
        """, (album, tags, filePath, name))
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
        cursor.execute("DELETE FROM images WHERE name = ?", (name,))
        connection.commit()
        connection.close()
