"""
photo_importer.py
Author: Kanyanat Atsawabowornnan
Date: October 6, 2025
Purpose:
    Handles importing photos into the Photo Catalog Application.
    This module reads image files from the local file system, collects metadata,
    and inserts records into the SQLite catalog database.
"""

import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Tuple
from catalog_database import CatalogDatabase

class PhotoImporter:
    # Import status codes
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    COPY_ERROR = "copy_error"
    UNSUPPORTED_FORMAT = "unsupported_format"
    
    def __init__(self, catalog_db: CatalogDatabase, storage_dir: str = "storage"):
        self.catalog_db = catalog_db
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.last_error = ""  # Store the last error message
    
    def _calculate_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 checksum of file content. Returns None on error."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return None
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if file is a supported image format."""
        supported_formats = {'.jpg', '.jpeg', '.png', '.svg'}
        return file_path.suffix.lower() in supported_formats
    
    def get_last_error(self) -> str:
        """Get the last error message."""
        return self.last_error
    
    def import_photo(self, original_path: Path, name: str = None, 
                    description: str = "", album: str = None, 
                    tags: List[str] = None) -> str:
        """
        Import a single photo.
        
        Returns:
            status_code - One of: SUCCESS, DUPLICATE, COPY_ERROR, UNSUPPORTED_FORMAT
            Use get_last_error() for detailed error message.
        """
        # Reset last error
        self.last_error = ""
        
        # Check supported format
        if not self._is_supported_format(original_path):
            self.last_error = f"Unsupported format: {original_path.suffix}"
            return self.UNSUPPORTED_FORMAT
        
        # Check file can be read
        checksum = self._calculate_checksum(original_path)
        if not checksum:
            self.last_error = "Cannot read file (corrupted or inaccessible)"
            return self.COPY_ERROR
        
        # Check for duplicates
        if self.catalog_db.photo_exists(checksum):
            self.last_error = "Photo already exists in catalog"
            return self.DUPLICATE
        
        # Get file info
        file_type = original_path.suffix.lower().lstrip('.')
        file_size = original_path.stat().st_size
        display_name = name or original_path.stem
        
        # Prepare albums list
        albums = [album] if album else None
        
        # 1. ADD TO DATABASE FIRST
        file_uuid = self.catalog_db.add_photo(
            original_path=original_path,
            name=display_name,
            description=description,
            albums=albums,
            tags=tags
        )
        
        if not file_uuid:
            self.last_error = "Failed to add photo to database"
            return self.COPY_ERROR
        
        # 2. COPY FILE AFTER successful database insertion
        stored_filename = f"{file_uuid}.{file_type}"
        stored_path = self.storage_dir / stored_filename
        
        try:
            shutil.copy2(original_path, stored_path)
        except (IOError, OSError):
            # If copy fails, remove from database
            self.catalog_db.delete_photo(file_uuid)
            self.last_error = "Failed to copy photo file"
            return self.COPY_ERROR
        
        # Verify the copy was successful
        if not stored_path.exists():
            # If copy verification fails, remove from database
            self.catalog_db.delete_photo(file_uuid)
            self.last_error = "Photo file corrupted during copy"
            return self.COPY_ERROR
        
        # Store UUID for success case
        self.last_error = file_uuid  # Store UUID as "error" for success case
        return self.SUCCESS
    
    def import_folder(self, folder_path: Path, album: str, description: str = "") -> List[str]:
        """
        Import all photos from a folder and all subdirectories.
        All images will have the same description and belong to the same album.
        
        Returns:
            List of successfully imported file UUIDs
        """
        imported_uuids = []
        
        # Recursively find all files in folder and subdirectories
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and self._is_supported_format(file_path):
                status = self.import_photo(
                    original_path=file_path,
                    description=description,
                    album=album
                )
                
                if status == self.SUCCESS:
                    # On success, last_error contains the UUID
                    imported_uuids.append(self.last_error)
        
        return imported_uuids
    