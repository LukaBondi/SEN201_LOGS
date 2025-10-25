"""
main.py
Author: LOGS Team
Date: October 25, 2025

Purpose:
    Entry point for the Photo Catalog Application.
    Launches the PyQt6 GUI interface.
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.MainWindow import MainWindow


def main():
    """Initialize and run the Photo Catalog application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Photo Catalog")
    app.setOrganizationName("LOGS Team")
    app.setApplicationVersion("1.0.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
