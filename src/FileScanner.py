"""
FileScanner.py
Author: Luka Chanakan Bond
Date: October 7th, 2025

Purpose:
    Interacts with the file system to scan for files in directories
"""

import os

def scanDirectory(directory: str, extensions: set[str] | None = None) -> list[str]:
    """
    Recursively scan a directory and return a list of file paths with matching extensions.

    Args:
        directory (str): Path to the root directory to scan.
        extensions (set[str], optional): Allowed file extensions.
            Defaults to common formats.

    Returns:
        list[str]: List of full paths to image files.
    """

    if extensions is None:
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic'}

    files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                files.append(os.path.join(root, file))

    return files


if __name__ == '__main__':
    pass
