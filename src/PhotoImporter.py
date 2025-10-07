"""
photo_importer.py
Author: Satwik Singh
Date: 2025-01-09
Purpose:
    Handles importing photos into the Photo Catalog Application.
    This module reads image files from the local file system, collects metadata,
    and inserts records into the SQLite catalog database.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any


class PhotoImporter:
    """
    PhotoImporter is responsible for adding new photos to the catalog.
    It interacts with the file system, validates image paths,
    and communicates with the SQLite database via the CatalogManager.
    """

    def __init__(self, db_path: str):
        """
        Initializes the PhotoImporter.

        Args:
            db_path (str): Path to the SQLite catalog database.
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self._initialize_table()

    def _initialize_table(self) -> None:
        """Creates the catalog table if it does not exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_path TEXT UNIQUE NOT NULL,
                tags TEXT,
                description TEXT,
                date_added TEXT
            )
        """)
        self.connection.commit()

    def addPhoto(self, file_path: str, tags: List[str] = None, description: str = "") -> bool:
        """
        Adds a photo and its metadata to the catalog database.

        Args:
            file_path (str): The full path of the photo file.
            tags (List[str]): Optional list of tags for the photo.
            description (str): Optional photo description.

        Returns:
            bool: True if added successfully, False if duplicate or invalid.

        Raises:
            FileNotFoundError: If the photo does not exist at the given path.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Photo not found: {file_path}")

        name = os.path.basename(file_path)
        tag_string = ", ".join(tags) if tags else ""
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check for duplicates
        self.cursor.execute("SELECT id FROM photos WHERE file_path = ?", (file_path,))
        if self.cursor.fetchone():
            print(f"[Warning] Photo already exists in catalog: {name}")
            return False

        # Insert record
        try:
            self.cursor.execute("""
                INSERT INTO photos (name, file_path, tags, description, date_added)
                VALUES (?, ?, ?, ?, ?)
            """, (name, file_path, tag_string, description, date_added))
            self.connection.commit()
            print(f"[Info] Added photo: {name}")
            return True
        except sqlite3.Error as e:
            print(f"[Error] Database insertion failed: {e}")
            return False

    def listImportedPhotos(self) -> List[Dict[str, Any]]:
        """
        Retrieves all imported photos from the catalog.

        Returns:
            List[Dict[str, Any]]: List of photo records with metadata.
        """
        self.cursor.execute("SELECT name, file_path, tags, description, date_added FROM photos")
        records = self.cursor.fetchall()
        return [
            {
                "name": r[0],
                "file_path": r[1],
                "tags": r[2],
                "description": r[3],
                "date_added": r[4],
            }
            for r in records
        ]

    def removePhoto(self, file_path: str) -> bool:
        """
        Removes a photo from the catalog.

        Args:
            file_path (str): Path to the photo file to remove.

        Returns:
            bool: True if successfully removed, False otherwise.
        """
        self.cursor.execute("DELETE FROM photos WHERE file_path = ?", (file_path,))
        if self.cursor.rowcount > 0:
            self.connection.commit()
            print(f"[Info] Removed photo: {file_path}")
            return True
        else:
            print(f"[Warning] No record found for: {file_path}")
            return False

    def __del__(self):
        """Closes the database connection upon deletion."""
        if self.connection:
            self.connection.close()
