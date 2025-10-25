"""
PhotoViewer Component

A full-screen overlay component for viewing photo details with metadata,
tags management, favorites toggle, and delete functionality.

Author: Copilot
Date: 2024
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QGridLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal


class PhotoViewer(QWidget):
    """
    Full-screen photo viewer overlay with metadata display and editing capabilities.
    
    Signals:
        closed: Emitted when the viewer is closed
        favoriteToggled(int, bool): Emitted when favorite status changes (photo_id, new_state)
        photoDeleted(str): Emitted when photo is deleted (file_path)
        tagAdded(int, str, str): Emitted when tag is added (photo_id, file_path, new_tags)
    """
    
    closed = pyqtSignal()
    favoriteToggled = pyqtSignal(int, bool)  # photo_id, new_favorite_state
    photoDeleted = pyqtSignal(str)  # file_path
    tagAdded = pyqtSignal(int, str, str)  # photo_id, file_path, new_tags
    
    def __init__(self, photo, dbManager, photoImporter, parent=None):
        """
        Initialize the PhotoViewer.
        
        Args:
            photo: Photo data (dict or tuple)
            dbManager: Database manager instance
            photoImporter: Photo importer instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.dbManager = dbManager
        self.photoImporter = photoImporter
        self.photoData = self._normalizePhotoData(photo)
        
        self._setupUI()
        
    def _normalizePhotoData(self, photo):
        """
        Normalize photo data from dict or tuple format to a consistent dict.
        
        Args:
            photo: Photo data (dict or tuple)
            
        Returns:
            dict: Normalized photo data
        """
        if isinstance(photo, dict):
            file_path = photo.get('file_path', '')
            return {
                'id': photo.get('id'),
                'name': photo.get('name', os.path.basename(file_path)),
                'file_path': file_path,
                'description': photo.get('description', ''),
                'tags': photo.get('tags', ''),
                'date_added': photo.get('date_added', 'xx/xx/xxxx'),
                'favorite': int(photo.get('favorite', 0)) if 'favorite' in photo else 0,
            }
        else:
            # Tuple layout from DB: (id, name, file_path, album, tags, description, date_added, favorite)
            file_path = photo[2] if len(photo) > 2 else ''
            return {
                'id': photo[0] if len(photo) > 0 else None,
                'name': photo[1] if len(photo) > 1 else 'Photo',
                'file_path': file_path,
                'description': photo[5] if len(photo) > 5 else '',
                'tags': photo[4] if len(photo) > 4 else '',
                'date_added': photo[6] if len(photo) > 6 else 'xx/xx/xxxx',
                'favorite': photo[7] if len(photo) > 7 else 0,
            }
    
    def _setupUI(self):
        """Set up the user interface."""
        # Full-screen overlay styling
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Main layout
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        # Top bar with close button
        topBar = self._createTopBar()
        mainLayout.addWidget(topBar)
        
        # Content area with image and info panel
        contentWidget = self._createContentArea()
        mainLayout.addWidget(contentWidget)
    
    def _createTopBar(self):
        """
        Create top bar with close button.
        
        Returns:
            QWidget: Top bar widget
        """
        topBar = QWidget()
        topBar.setFixedHeight(60)
        topBar.setStyleSheet("background-color: transparent;")
        topBarLayout = QHBoxLayout(topBar)
        topBarLayout.setContentsMargins(20, 10, 20, 10)
        
        topBarLayout.addStretch()
        
        closeBtn = QPushButton("✕")
        closeBtn.setFixedSize(40, 40)
        closeBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 32pt;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #B9B28A;
            }
        """)
        closeBtn.clicked.connect(self._onClose)
        topBarLayout.addWidget(closeBtn)
        
        return topBar
    
    def _createContentArea(self):
        """
        Create content area with image and info panel.
        
        Returns:
            QWidget: Content area widget
        """
        contentWidget = QWidget()
        contentWidget.setStyleSheet("background-color: transparent;")
        contentLayout = QHBoxLayout(contentWidget)
        contentLayout.setContentsMargins(40, 20, 40, 40)
        contentLayout.setSpacing(30)
        
        # Image container (left side)
        imageContainer = self._createImageContainer()
        contentLayout.addWidget(imageContainer, stretch=7)
        
        # Info panel (right side)
        infoPanel = self._createInfoPanel()
        contentLayout.addWidget(infoPanel, stretch=3)
        
        return contentWidget
    
    def _createImageContainer(self):
        """
        Create image display container.
        
        Returns:
            QFrame: Image container widget
        """
        imageContainer = QFrame()
        imageContainer.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 0px;
            }
        """)
        imageLayout = QVBoxLayout(imageContainer)
        imageLayout.setContentsMargins(10, 10, 10, 10)
        
        # Image label
        imageLabel = QLabel()
        imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        imageLabel.setStyleSheet("background-color: #1a1a1a;")
        
        file_path = self.photoData['file_path']
        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    800, 600,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                imageLabel.setPixmap(scaled_pixmap)
            else:
                imageLabel.setText("📷 Cannot load image")
                imageLabel.setStyleSheet("color: white; font-size: 48pt;")
        else:
            imageLabel.setText("❌ Image not found")
            imageLabel.setStyleSheet("color: white; font-size: 48pt;")
        
        imageLayout.addWidget(imageLabel)
        return imageContainer
    
    def _createInfoPanel(self):
        """
        Create info panel with metadata and controls.
        
        Returns:
            QFrame: Info panel widget
        """
        infoPanel = QFrame()
        infoPanel.setStyleSheet("""
            QFrame {
                background-color: #EBE5C2;
                border-radius: 0px;
            }
        """)
        infoPanel.setFixedWidth(400)
        infoPanelLayout = QVBoxLayout(infoPanel)
        infoPanelLayout.setContentsMargins(30, 30, 30, 30)
        infoPanelLayout.setSpacing(12)
        
        # Image name section
        self._addNameSection(infoPanelLayout)
        
        # Description section
        self._addDescriptionSection(infoPanelLayout)
        
        # Tags section
        self._addTagsSection(infoPanelLayout)
        
        # Favorites button
        self._addFavoritesButton(infoPanelLayout)
        
        # Delete button
        self._addDeleteButton(infoPanelLayout)
        
        # Add tag input section
        self._addTagInputSection(infoPanelLayout)
        
        infoPanelLayout.addStretch()
        
        # Date at bottom
        self._addDateLabel(infoPanelLayout)
        
        return infoPanel
    
    def _addNameSection(self, layout):
        """Add image name section to layout."""
        nameLabel = QLabel("IMAGE NAME")
        nameLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 11pt;
            font-weight: 600;
            font-family: 'Times New Roman', serif;
        """)
        layout.addWidget(nameLabel)
        
        nameValueLabel = QLabel(self.photoData['name'])
        nameValueLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 14pt;
            font-weight: 400;
            margin-bottom: 10px;
        """)
        nameValueLabel.setWordWrap(True)
        layout.addWidget(nameValueLabel)
    
    def _addDescriptionSection(self, layout):
        """Add description section to layout."""
        descLabel = QLabel("Description")
        descLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 11pt;
            font-weight: 400;
            font-family: 'Times New Roman', serif;
            font-style: italic;
        """)
        layout.addWidget(descLabel)
        
        descValueLabel = QLabel(self.photoData['description'] or 'A picture of leaves\ntaken in ........')
        descValueLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 10pt;
            margin-bottom: 10px;
        """)
        descValueLabel.setWordWrap(True)
        layout.addWidget(descValueLabel)
    
    def _addTagsSection(self, layout):
        """Add tags display section to layout."""
        tagsHeaderLabel = QLabel("TAGS")
        tagsHeaderLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 11pt;
            font-weight: 600;
            font-family: 'Times New Roman', serif;
        """)
        layout.addWidget(tagsHeaderLabel)
        
        # Parse tags
        tags_val = self.photoData['tags']
        if tags_val:
            tags = [tag.strip() for tag in str(tags_val).split(',') if tag.strip()]
        else:
            tags = []
        
        # Tags grid
        tagsContainer = QWidget()
        tagsGrid = QGridLayout(tagsContainer)
        tagsGrid.setContentsMargins(0, 0, 0, 0)
        tagsGrid.setHorizontalSpacing(8)
        tagsGrid.setVerticalSpacing(6)
        
        for idx, tag in enumerate(tags):
            chip = QFrame()
            chip.setStyleSheet("""
                QFrame {
                    background-color: #EBE5C2;
                    border: 1px solid #B9B28A;
                    border-radius: 12px;
                }
            """)
            chipLayout = QHBoxLayout(chip)
            chipLayout.setContentsMargins(10, 4, 10, 4)
            chipLayout.setSpacing(6)
            
            chipLabel = QLabel(tag)
            chipLabel.setStyleSheet("color: #2d2d2d; font-size: 9pt;")
            chipLayout.addWidget(chipLabel)
            
            # Remove button (not wired for now)
            removeBtn = QPushButton("×")
            removeBtn.setFixedSize(18, 18)
            removeBtn.setStyleSheet("""
                QPushButton { background: transparent; border: none; color: #504B38; font-size: 12pt; }
                QPushButton:hover { color: #c82333; }
            """)
            chipLayout.addWidget(removeBtn)
            
            tagsGrid.addWidget(chip, idx // 2, idx % 2)
        
        layout.addWidget(tagsContainer)
    
    def _addFavoritesButton(self, layout):
        """Add favorites toggle button to layout."""
        favorite_val = self.photoData['favorite']
        favBtn = QPushButton("Remove from Favorites" if favorite_val else "Add to Favorites")
        favBtn.setStyleSheet("""
            QPushButton {
                background-color: #FFD166;
                color: #2d2d2d;
                border: none;
                border-radius: 6px;
                font-size: 10pt;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #FFBE55; }
        """)
        favBtn.clicked.connect(self._onToggleFavorite)
        layout.addWidget(favBtn)
    
    def _addDeleteButton(self, layout):
        """Add delete button to layout."""
        deleteViewerBtn = QPushButton("Delete From Catalog")
        deleteViewerBtn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; color: white; border: none; border-radius: 6px;
                font-size: 10pt; font-weight: 600; padding: 8px 12px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        deleteViewerBtn.clicked.connect(self._onDelete)
        layout.addWidget(deleteViewerBtn)
    
    def _addTagInputSection(self, layout):
        """Add interactive tag input section to layout."""
        tagInputWidget = QWidget()
        tagInputLayout = QHBoxLayout(tagInputWidget)
        tagInputLayout.setContentsMargins(0, 0, 0, 0)
        tagInputLayout.setSpacing(5)
        
        # "Add Tag +" label
        addTagLabel = QLabel("Add Tag +")
        addTagLabel.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #504B38;
                font-size: 10pt;
                padding: 5px 0px;
            }
        """)
        addTagLabel.setCursor(Qt.CursorShape.PointingHandCursor)
        tagInputLayout.addWidget(addTagLabel)
        
        # Tag input field
        tagLineEdit = QLineEdit()
        tagLineEdit.setPlaceholderText("Enter tag...")
        tagLineEdit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: #504B38;
                border: 1px solid #B9B28A;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10pt;
            }
        """)
        tagLineEdit.hide()
        tagInputLayout.addWidget(tagLineEdit)
        
        # Confirm button
        confirmTagBtn = QPushButton("Confirm")
        confirmTagBtn.setFixedSize(120, 35)
        confirmTagBtn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 2px solid #1e7e34;
                border-radius: 6px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        confirmTagBtn.hide()
        tagInputLayout.addWidget(confirmTagBtn)
        
        # Cancel button
        cancelTagBtn = QPushButton("Cancel")
        cancelTagBtn.setFixedSize(120, 35)
        cancelTagBtn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: 2px solid #bd2130;
                border-radius: 6px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        cancelTagBtn.hide()
        tagInputLayout.addWidget(cancelTagBtn)
        
        tagInputLayout.addStretch()
        layout.addWidget(tagInputWidget)
        
        # Wire up tag input interactions
        def showTagInput(event):
            addTagLabel.hide()
            tagLineEdit.show()
            confirmTagBtn.show()
            cancelTagBtn.show()
            tagLineEdit.setFocus()
        
        def resetTagInput():
            tagLineEdit.clear()
            tagLineEdit.hide()
            confirmTagBtn.hide()
            cancelTagBtn.hide()
            addTagLabel.show()
        
        def confirmTag():
            tag = tagLineEdit.text().strip()
            if tag:
                currentTags = self.photoData['tags'] or ''
                newTags = (currentTags + ', ' + tag).strip(', ').strip()
                # Persist new tag
                try:
                    self.dbManager.createTag(tag)
                    photo_id = self.photoData['id']
                    file_path = self.photoData['file_path']
                    
                    if photo_id is not None:
                        self.dbManager.updatePhotoTags(photo_id, newTags)
                    elif file_path:
                        self.dbManager.updatePhotoTagsByPath(file_path, newTags)
                    
                    # Emit signal and close
                    self.tagAdded.emit(photo_id, file_path, newTags)
                    self.close()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to add tag: {str(e)}")
                return
            resetTagInput()
        
        addTagLabel.mousePressEvent = showTagInput
        confirmTagBtn.clicked.connect(confirmTag)
        cancelTagBtn.clicked.connect(resetTagInput)
    
    def _addDateLabel(self, layout):
        """Add date label to layout."""
        dateLabel = QLabel(f"Photo taken on\n{self.photoData['date_added']}")
        dateLabel.setStyleSheet("""
            color: #504B38;
            font-size: 8pt;
            font-style: italic;
        """)
        dateLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(dateLabel)
    
    def _onClose(self):
        """Handle close button click."""
        self.closed.emit()
        self.setParent(None)
    
    def _onToggleFavorite(self):
        """Handle favorite toggle."""
        photo_id = self.photoData['id']
        file_path = self.photoData['file_path']
        current_favorite = self.photoData['favorite']
        target_state = not bool(current_favorite)
        
        try:
            if photo_id is not None:
                self.dbManager.setFavoriteById(photo_id, target_state)
            elif file_path:
                self.dbManager.setFavoriteByPath(file_path, target_state)
            
            # Emit signal with updated state
            self.favoriteToggled.emit(photo_id, target_state)
        except Exception:
            pass
    
    def _onDelete(self):
        """Handle delete button click."""
        file_path = self.photoData['file_path']
        if not file_path:
            QMessageBox.warning(self, "Delete", "Missing file path for this photo.")
            return
        
        reply = QMessageBox.question(
            self, "Delete Photo",
            f"Remove '{os.path.basename(file_path)}' from catalog? This will not delete the file from disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            ok = self.photoImporter.removePhoto(file_path)
            if not ok:
                try:
                    self.dbManager.deleteImage(os.path.basename(file_path))
                except Exception:
                    pass
            
            # Emit signal and close
            self.photoDeleted.emit(file_path)
            self.close()
