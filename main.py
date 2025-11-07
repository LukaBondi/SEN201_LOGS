"""
main.py
Author: Satwik
Date: October 25, 2025

Purpose:
    Entry point for the Photo Catalog Application.
    Launches the PyQt6 GUI interface.
"""

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from gui.MainWindow import MainWindow


def resourcePath(relativePath):
    """
    Get absolute path to resource (works for dev and PyInstaller).
    
    Args:
        relativePath (str): Relative path to the resource file.
        
    Returns:
        str: Absolute path to the resource.
    """
    basePath = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(basePath, relativePath)


def main():
    """Initialize and run the Photo Catalog application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Photo Catalog")
    app.setOrganizationName("LOGS Team")
    app.setApplicationVersion("1.0.1")

    iconPath = resourcePath("assets/icon.png" if sys.platform.startswith('linux') else "assets/icon.ico")
    app.setWindowIcon(QIcon(iconPath))


    # Create and show main window
    window = MainWindow()
    window.setWindowIcon(QIcon(iconPath)) 
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
