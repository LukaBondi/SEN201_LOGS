"""
similarity_search.py
Author: Satwik Singh
Date: October 6, 2025
Purpose:
    Implements the Similarity Search module for the Photo Catalog Application.
    This module finds photos in the catalog with tags similar to a selected image.
"""

import sqlite3
from typing import List, Dict, Any


class SimilaritySearch:
    """
    SimilaritySearch is responsible for finding photos with overlapping tags.
    It interacts with the SQLite catalog database through simple SELECT queries.
    """

    def __init__(self, db_path: str):
        """
        Initializes the SimilaritySearch module.

        Args:
            db_path (str): Path to the SQLite catalog database.
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def _fetchTags(self, photo_name: str) -> List[str]:
        """
        Retrieves the tags associated with a given photo.

        Args:
            photo_name (str): Name of the reference photo.

        Returns:
            List[str]: Tags associated with that photo.

        Raises:
            ValueError: If the photo is not found in the database.
        """
        self.cursor.execute("SELECT tags FROM photos WHERE name = ?", (photo_name,))
        result = self.cursor.fetchone()

        if not result:
            raise ValueError(f"Photo '{photo_name}' not found in catalog.")

        tags = [t.strip().lower() for t in result[0].split(",") if t.strip()]
        return tags

    def findSimilarPhotos(self, photo_name: str) -> List[Dict[str, Any]]:
        """
        Finds photos that share one or more tags with the given photo.

        Args:
            photo_name (str): Name of the reference photo.

        Returns:
            List[Dict[str, Any]]: List of photos that are similar based on tag overlap.
        """
        reference_tags = self._fetchTags(photo_name)
        if not reference_tags:
            print(f"[Info] No tags found for {photo_name}. Cannot perform similarity search.")
            return []

        # Build dynamic LIKE query for partial tag matching
        like_clauses = " OR ".join(["tags LIKE ?" for _ in reference_tags])
        params = [f"%{tag}%" for tag in reference_tags]

        query = f"""
            SELECT name, file_path, tags, description
            FROM photos
            WHERE ({like_clauses}) AND name != ?
        """
        params.append(photo_name)
        self.cursor.execute(query, tuple(params))

        results = self.cursor.fetchall()
        similar_photos = [
            {
                "name": r[0],
                "file_path": r[1],
                "tags": r[2],
                "description": r[3],
            }
            for r in results
        ]

        print(f"[Info] Found {len(similar_photos)} similar photo(s) for '{photo_name}'.")
        return similar_photos

    def __del__(self):
        """Closes the database connection upon deletion."""
        if self.connection:
            self.connection.close()
