"""
Sidebar.py
Author: Satwik
Date: October 25, 2025

Purpose:
    Navigation sidebar component for the Photo Catalog Application.
    Provides navigation buttons for different views.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal


class Sidebar(QFrame):
    """
    Navigation sidebar with view switching buttons.
    
    Signals:
        viewChanged (str): Emitted when a navigation button is clicked.
    """
    
    viewChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialize the sidebar.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.navButtons = {}
        self._setupUI()
    
    def _setupUI(self):
        """Set up the sidebar UI."""
        self.setFixedWidth(180)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-right: 1px solid #504B38;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Header
        logoWidget = QWidget()
        logoWidget.setStyleSheet("background-color: #2d2d2d; padding: 20px;")
        logoLayout = QVBoxLayout(logoWidget)
        
        logoLabel = QLabel("LOGS")
        logoLabel.setStyleSheet("""
            color: #F8F3D9;
            font-size: 16pt;
            font-weight: bold;
        """)
        logoLayout.addWidget(logoLabel)
        
        catalogLabel = QLabel("CATALOG")
        catalogLabel.setStyleSheet("""
            color: #B9B28A;
            font-size: 10pt;
            font-weight: 500;
        """)
        logoLayout.addWidget(catalogLabel)
        
        layout.addWidget(logoWidget)
        
        # Navigation buttons
        self.navButtons['all_photos'] = self._createNavButton("📷 ALL PHOTOS", True)
        self.navButtons['upload'] = self._createNavButton("⬆️ UPLOAD", False)
        self.navButtons['albums'] = self._createNavButton("📁 ALBUMS", False)
        self.navButtons['favorites'] = self._createNavButton("⭐ FAVORITES", False)
        self.navButtons['tags'] = self._createNavButton("🏷️ TAGS", False)
        
        # Connect buttons
        for viewName, btn in self.navButtons.items():
            btn.clicked.connect(lambda checked=False, v=viewName: self.viewChanged.emit(v))
            layout.addWidget(btn)
        
        layout.addStretch()
    
    def _createNavButton(self, text, isActive=False):
        """
        Create a sidebar navigation button.
        
        Args:
            text (str): Button text.
            isActive (bool): Whether the button is initially active.
            
        Returns:
            QPushButton: The created button.
        """
        btn = QPushButton(text)
        btn.setFixedHeight(45)
        if isActive:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a5cb8;
                    color: white;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 10pt;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #5a6cc8;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #B9B28A;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 10pt;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    color: #F8F3D9;
                }
            """)
        return btn
    
    def setActiveView(self, viewName):
        """
        Update button styles to reflect the active view.
        
        Args:
            viewName (str): Name of the active view.
        """
        for name, btn in self.navButtons.items():
            if name == viewName:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a5cb8;
                        color: white;
                        border: none;
                        text-align: left;
                        padding-left: 20px;
                        font-size: 10pt;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #5a6cc8;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #B9B28A;
                        border: none;
                        text-align: left;
                        padding-left: 20px;
                        font-size: 10pt;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                        color: #F8F3D9;
                    }
                """)
