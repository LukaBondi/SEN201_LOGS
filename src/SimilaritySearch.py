"""
similarity_search.py
Author: Satwik Singh
Date: October 6, 2025
Purpose:
    Implements the Similarity Search module for the Photo Catalog Application.
    This module finds photos in the catalog with tags similar to a selected
    image.
"""

import sqlite3
from typing import List, Dict, Any


class SimilaritySearch:
    """
    SimilaritySearch is responsible for finding photos with overlapping tags.
    It interacts with the SQLite catalog database through simple SELECT
    queries.
    """

    def __init__(self, dbPath: str):
        """
        Initializes the SimilaritySearch module.

        Args:
            dbPath (str): Path to the SQLite catalog database.
        """
        self.dbPath = dbPath
        self.connection = sqlite3.connect(self.dbPath)
        self.cursor = self.connection.cursor()

    def _fetchTags(self, photoName: str) -> List[str]:
        """
        Retrieves the tags associated with a given photo.

        Args:
            photoName (str): Name of the reference photo.

        Returns:
            List[str]: Tags associated with that photo.

        Raises:
            ValueError: If the photo is not found in the database.
        """
        self.cursor.execute("SELECT tags FROM photos WHERE name = ?",
                          (photoName,))
        result = self.cursor.fetchone()

        if not result:
            raise ValueError(f"Photo '{photoName}' not found in catalog.")

        tags = [t.strip().lower() for t in result[0].split(",")
                if t.strip()]
        return tags

    def findSimilarPhotos(self, photoName: str) -> List[Dict[str, Any]]:
        """
        Finds photos that share one or more tags with the given photo.

        Args:
            photoName (str): Name of the reference photo.

        Returns:
            List[Dict[str, Any]]: List of photos that are similar based on
            tag overlap.
        """
        referenceTags = self._fetchTags(photoName)
        if not referenceTags:
            print(f"[Info] No tags found for {photoName}. Cannot perform "
                  f"similarity search.")
            return []

        # Build dynamic LIKE query for partial tag matching
        likeClauses = " OR ".join(["tags LIKE ?" for _ in referenceTags])
        params = [f"%{tag}%" for tag in referenceTags]

        query = f"""
            SELECT name, file_path, tags, description
            FROM photos
            WHERE ({likeClauses}) AND name != ?
        """
        params.append(photoName)
        self.cursor.execute(query, tuple(params))

        results = self.cursor.fetchall()
        similarPhotos = [
            {
                "name": r[0],
                "file_path": r[1],
                "tags": r[2],
                "description": r[3],
            }
            for r in results
        ]

        print(f"[Info] Found {len(similarPhotos)} similar photo(s) for "
              f"'{photoName}'.")
        return similarPhotos

    def findSimilarPhotosByTag(self, tag: str) -> List[tuple]:
        """
        Finds photos that contain the specified tag.

        Args:
            tag (str): Tag to search for.

        Returns:
            List[tuple]: List of photo tuples (id, name, file_path, album,
                        tags, description, date_added) matching the tag.
        """
        if not tag or not tag.strip():
            return []

        tag = tag.strip()
        query = """
            SELECT id, name, file_path, album, tags, description, date_added
            FROM photos
            WHERE tags LIKE ?
        """
        self.cursor.execute(query, (f"%{tag}%",))
        results = self.cursor.fetchall()

        print(f"[Info] Found {len(results)} photo(s) with tag '{tag}'.")
        return results

    def __del__(self):
        """Closes the database connection upon deletion."""
        if self.connection:
            self.connection.close()
