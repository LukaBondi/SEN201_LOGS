"""
PhotoCard.py
Author: Luka Bond
Date: October 25, 2025

Purpose:
    Photo card widget component for displaying photo thumbnails in grid views.
"""

import os
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QWidget, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


class PhotoCard(QFrame):
    """
    A card widget displaying a photo thumbnail with metadata.
    
    Signals:
        photoClicked (object): Emitted when the card is clicked.
        deleteRequested (str): Emitted when delete button is clicked (file_uuid).
    """
    
    photoClicked = pyqtSignal(object)
    deleteRequested = pyqtSignal(str)  # Emits file_uuid
    
    def __init__(self, photo, parent=None):
        """
        Initialize the photo card.
        
        Args:
            photo: Photo data (tuple or dict).
            parent: Parent widget.
        """
        super().__init__(parent)
        self.photo = photo
        self._parsePhotoData()
        self.is_selectable = False
        self.is_selected = False
        self._setupUI()
    
    def _parsePhotoData(self):
        """Parse photo data from tuple or dict format."""
        # Schema: (id, name, file_path, album, tags, description, date_added)
        if isinstance(self.photo, tuple):
            self.file_path = self.photo[2] if len(self.photo) > 2 else ''
            self.file_uuid = self.photo[0] if len(self.photo) > 0 else ''  # id is file_uuid
            self.name = self.photo[1] if len(self.photo) > 1 else os.path.basename(self.file_path)
            self.tags = self.photo[4] if len(self.photo) > 4 else ''
        else:
            self.file_path = self.photo.get('full_path', self.photo.get('file_path', ''))
            self.file_uuid = self.photo.get('file_uuid', '')
            self.name = self.photo.get('name', os.path.basename(self.file_path))
            self.tags = self.photo.get('tags', '')
    
    def _setupUI(self):
        """Set up the card UI."""
        self.setFixedSize(280, 220)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #EBE5C2;
            }
            QFrame:hover {
                border: 2px solid #B9B28A;
            }
        """)
        # Selection styling (applies when card is selected)
        self._selected_style = "border: 2px solid #2A7AE2; background-color: #E8F0FF;"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar with delete button (overlay)
        topBar = QWidget()
        topBarLayout = QHBoxLayout(topBar)
        topBarLayout.setContentsMargins(8, 8, 8, 0)
        topBarLayout.addStretch()
        
        self.deleteBtn = QPushButton("🗑 Delete")
        self.deleteBtn.setFixedHeight(24)
        self.deleteBtn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                padding: 2px 8px; 
                font-size: 8pt; 
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        self.deleteBtn.clicked.connect(self._onDeleteClicked)
        topBarLayout.addWidget(self.deleteBtn)
        layout.addWidget(topBar)
        
        # Photo thumbnail
        photoLabel = QLabel()
        photoLabel.setFixedSize(280, 180)
        photoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photoLabel.setStyleSheet("background-color: #f5f5f5; border-radius: 8px 8px 0 0;")
        
        if self.file_path and isinstance(self.file_path, str) and os.path.exists(self.file_path):
            pixmap = QPixmap(self.file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    280, 180, 
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                    Qt.TransformationMode.SmoothTransformation
                )
                photoLabel.setPixmap(scaled_pixmap)
                photoLabel.setScaledContents(True)
            else:
                photoLabel.setText("📷")
                photoLabel.setStyleSheet("background-color: #EBE5C2; font-size: 48pt;")
        else:
            photoLabel.setText("❌")
            photoLabel.setStyleSheet("background-color: #EBE5C2; font-size: 48pt; color: #B9B28A;")
        
        layout.addWidget(photoLabel)
        
    # Photo info
        infoWidget = QWidget()
        infoWidget.setFixedHeight(40)
        infoWidget.setStyleSheet("background-color: white; border-radius: 0 0 8px 8px;")
        infoLayout = QVBoxLayout(infoWidget)
        infoLayout.setContentsMargins(10, 10, 10, 10)
        infoLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        nameLabel = QLabel(self.name[:25] + "..." if len(self.name) > 25 else self.name)
        nameLabel.setStyleSheet("color: #504B38; font-weight: 600; font-size: 9pt;")
        infoLayout.addWidget(nameLabel)

        layout.addWidget(infoWidget)
    
    def _onDeleteClicked(self):
        """Handle delete button click."""
        if not self.file_path:
            QMessageBox.warning(
                self, 
                "Delete", 
                "Missing file path for this photo."
            )
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Photo",
            f"Remove '{os.path.basename(self.file_path)}' from catalog? "
            "This will not delete the file from disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.deleteRequested.emit(self.file_uuid)
    
    def mousePressEvent(self, event):
        """Handle mouse press to emit photoClicked signal or toggle selection if selectable."""
        if self.is_selectable:
            # Toggle selection state and update visual
            self.is_selected = not self.is_selected
            if self.is_selected:
                # apply selected style
                self.setStyleSheet(self.styleSheet() + self._selected_style)
            else:
                # reset style
                self.setStyleSheet(self.styleSheet().replace(self._selected_style, ""))
        else:
            self.photoClicked.emit(self.photo)
        super().mousePressEvent(event)
