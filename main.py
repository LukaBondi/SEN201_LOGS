"""
main.py
Author: Satwik
Date: October 25, 2025

Purpose:
    Entry point for the Photo Catalog Application.
    Launches the PyQt6 GUI interface.
"""

import os, sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.MainWindow import MainWindow

def resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller)"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def main():
    """Initialize and run the Photo Catalog application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Photo Catalog")
    app.setOrganizationName("LOGS Team")
    app.setApplicationVersion("1.0.1")

    icon_path = resource_path("assets/icon.png" if sys.platform.startswith('linux') else "assets/icon.ico")
    app.setWindowIcon(QIcon(icon_path))


    # Create and show main window
    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path)) 
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
