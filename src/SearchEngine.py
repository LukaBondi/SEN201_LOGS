"""
searchEngine.py
Author: Kanyanat Atsawabowornnan
Date: 2025-10-07

Purpose:
Implements the Search Engine component for the Photo Catalog Application (LOGS Project).
Allows searching photos in the catalog by title and/or tags with partial matching.
Interacts with the Metadata Manager for metadata access and the GUI Manager for display.
"""

import sqlite3


class SearchEngine:
    """
    Handles database search operations for photos by title and/or tags.

    Attributes:
        connection (sqlite3.Connection): SQLite connection object.
    """

    def __init__(self, dbPath="catalog.db"):
        """
        Initializes the search engine with a database connection.

        Args:
            dbPath (str): Path to the SQLite database file.
        """
        self.connection = sqlite3.connect(dbPath)

    def searchPhotos(self, title="", tags=""):
        """
        Searches the catalog for photos that match the title and/or tags.

        Args:
            title (str): Title to search for (partial match).
            tags (str): Comma-separated list of tags to match (≥1 match).

        Returns:
            list[tuple]: List of (id, title, tags, filepath) for matching photos.
        """
        cursor = self.connection.cursor()

        titleQuery = "1=1"
        tagQuery = "1=1"
        params = []

        if title:
            titleQuery = "title LIKE ?"
            params.append(f"%{title}%")

        if tags:
            tagList = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tagList:
                tagConditions = []
                for tag in tagList:
                    tagConditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                tagQuery = "(" + " OR ".join(tagConditions) + ")"

        query = f"""
            SELECT id, title, tags, filepath
            FROM photos
            WHERE {titleQuery} AND {tagQuery}
        """
        cursor.execute(query, params)
        return cursor.fetchall()

    def closeConnection(self):
        """Closes the SQLite database connection."""
        if self.connection:
            self.connection.close()
