"""
PhotoViewer Component

A full-screen overlay component for viewing photo details with metadata,
tags management, favorites toggle, and delete functionality.

Author: Luka Bond
Date: 2024
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QGridLayout, QMessageBox, QTextEdit
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
            dbManager: Database manager instance (CatalogDatabase)
            photoImporter: Photo importer instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.catalogDb = dbManager  # CatalogDatabase instance
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
            file_path = photo.get('full_path', photo.get('file_path', ''))
            return {
                'id': photo.get('id'),
                'file_uuid': photo.get('file_uuid', ''),
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
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setStyleSheet("background-color: #1a1a1a;")
        self.imageLabel.setScaledContents(False)  # Don't stretch, we'll scale manually
        
        file_path = self.photoData['file_path']
        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
            self.originalPixmap = QPixmap(file_path)
            if not self.originalPixmap.isNull():
                # Initial display - will be properly scaled in resizeEvent
                self._updateImageDisplay()
            else:
                self.imageLabel.setText("📷 Cannot load image")
                self.imageLabel.setStyleSheet("color: white; font-size: 48pt;")
                self.originalPixmap = None
        else:
            self.imageLabel.setText("❌ Image not found")
            self.imageLabel.setStyleSheet("color: white; font-size: 48pt;")
            self.originalPixmap = None
        
        imageLayout.addWidget(self.imageLabel)
        return imageContainer
    
    def _updateImageDisplay(self):
        """Update the image display to fit the current container size."""
        if hasattr(self, 'originalPixmap') and self.originalPixmap and not self.originalPixmap.isNull():
            # Get the available size (subtract margins and some padding)
            available_width = self.width() - 500  # Account for info panel and margins
            available_height = self.height() - 150  # Account for top bar and margins
            
            # Scale to fit while maintaining aspect ratio
            scaled_pixmap = self.originalPixmap.scaled(
                available_width, available_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.imageLabel.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """Handle resize events to update image scaling."""
        super().resizeEvent(event)
        self._updateImageDisplay()
    
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
        
        # Container for description content (either text or edit field)
        self.descContainer = QWidget()
        self.descContainerLayout = QVBoxLayout(self.descContainer)
        self.descContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.descContainerLayout.setSpacing(5)
        
        description = self.photoData.get('description', '')
        
        if description:
            # Show existing description
            self.descValueLabel = QLabel(description)
            self.descValueLabel.setStyleSheet("""
                color: #2d2d2d;
                font-size: 10pt;
                margin-bottom: 10px;
            """)
            self.descValueLabel.setWordWrap(True)
            self.descContainerLayout.addWidget(self.descValueLabel)
        else:
            # Show "Add Description" button
            self.addDescBtn = QPushButton("+ Add Description")
            self.addDescBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F8F6EB;
                    color: #504B38;
                    border: 1px dashed #D6CFAA;
                    border-radius: 6px;
                    font-size: 9pt;
                    font-weight: 600;
                    padding: 6px 12px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #FFFFFF;
                    border-color: #B9B28A;
                }
            """)
            self.addDescBtn.clicked.connect(self._onAddDescriptionClicked)
            self.descContainerLayout.addWidget(self.addDescBtn)
        
        layout.addWidget(self.descContainer)
    
    def _addTagsSection(self, layout):
        """Add tags display section to layout."""
        tagsHeaderLabel = QLabel("TAGS")
        tagsHeaderLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 11pt;
            font-weight: 600;
            font-family: 'Times New Roman', serif;
            margin-bottom: 4px;
        """)
        layout.addWidget(tagsHeaderLabel)
        
        # Parse tags
        tags_val = self.photoData['tags']
        if tags_val:
            tags = [tag.strip() for tag in str(tags_val).split(',') if tag.strip()]
        else:
            tags = []
        
        if not tags:
            # Show a nice message when no tags exist
            noTagsLabel = QLabel("No tags yet")
            noTagsLabel.setStyleSheet("""
                color: #888;
                font-size: 9pt;
                font-style: italic;
                padding: 4px 0px;
            """)
            layout.addWidget(noTagsLabel)
        else:
            # Display tags as a clean bulleted list
            tagsText = ""
            for tag in tags:
                tagsText += f"• {tag}\n"
            
            tagsListLabel = QLabel(tagsText.strip())
            tagsListLabel.setStyleSheet("""
                QLabel {
                    color: #2d2d2d;
                    font-size: 10pt;
                    padding: 4px 8px;
                    background-color: #F8F6EB;
                    border-left: 3px solid #B9B28A;
                    border-radius: 4px;
                    line-height: 1.6;
                }
            """)
            tagsListLabel.setWordWrap(True)
            layout.addWidget(tagsListLabel)
    
    def _addFavoritesButton(self, layout):
        """Add favorites toggle button to layout."""
        favorite_val = bool(self.photoData.get('favorite', 0))
        self.favBtn = QPushButton("Remove from Favorites" if favorite_val else "Add to Favorites")
        self.favBtn.setStyleSheet("""
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
        self.favBtn.clicked.connect(self._onToggleFavorite)
        layout.addWidget(self.favBtn)
    
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
                # Add tag to photo (creates tag if needed)
                try:
                    file_uuid = self.photoData.get('file_uuid')
                    if not file_uuid:
                        QMessageBox.warning(self, "Error", "Photo UUID not found.")
                        return
                    
                    # Add the tag (this also creates the tag if it doesn't exist)
                    success = self.catalogDb.add_tag_to_photo(file_uuid, tag)
                    
                    if success:
                        # Fetch the actual current tags from the database
                        tags_list = self.catalogDb.get_photo_tags(file_uuid)
                        newTags = ', '.join(tags_list) if tags_list else ''
                        
                        # Emit signal to refresh viewer
                        photo_id = self.photoData.get('id')
                        file_path = self.photoData.get('file_path')
                        self.tagAdded.emit(photo_id, file_path, newTags)
                        self.close()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to add tag. It may already be on this photo.")
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
    
    def _onAddDescriptionClicked(self):
        """Handle 'Add Description' button click - show inline edit field."""
        # Clear the container
        while self.descContainerLayout.count():
            child = self.descContainerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create edit widget container
        editWidget = QWidget()
        editLayout = QVBoxLayout(editWidget)
        editLayout.setContentsMargins(0, 0, 0, 0)
        editLayout.setSpacing(8)
        
        # Text edit field
        from PyQt6.QtWidgets import QTextEdit
        self.descTextEdit = QTextEdit()
        self.descTextEdit.setPlaceholderText("Enter description...")
        self.descTextEdit.setMaximumHeight(100)
        self.descTextEdit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: #504B38;
                border: 1px solid #B9B28A;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }
        """)
        editLayout.addWidget(self.descTextEdit)
        
        # Buttons row
        buttonsWidget = QWidget()
        buttonsLayout = QHBoxLayout(buttonsWidget)
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.setSpacing(8)
        
        saveBtn = QPushButton("Save")
        saveBtn.setFixedSize(80, 30)
        saveBtn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        saveBtn.clicked.connect(self._onSaveDescription)
        buttonsLayout.addWidget(saveBtn)
        
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setFixedSize(80, 30)
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancelBtn.clicked.connect(self._onCancelDescriptionEdit)
        buttonsLayout.addWidget(cancelBtn)
        
        buttonsLayout.addStretch()
        editLayout.addWidget(buttonsWidget)
        
        self.descContainerLayout.addWidget(editWidget)
        self.descTextEdit.setFocus()
    
    def _onSaveDescription(self):
        """Save the description to database."""
        description = self.descTextEdit.toPlainText().strip()
        
        if not description:
            QMessageBox.warning(self, "Empty Description", "Please enter a description or click Cancel.")
            return
        
        file_uuid = self.photoData.get('file_uuid')
        if not file_uuid:
            QMessageBox.warning(self, "Error", "Photo UUID not found.")
            return
        
        try:
            # Update description in database
            success = self.catalogDb.update_photo(file_uuid, description=description)
            
            if success:
                # Update local data
                self.photoData['description'] = description
                
                # Clear the container and show the new description
                while self.descContainerLayout.count():
                    child = self.descContainerLayout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                self.descValueLabel = QLabel(description)
                self.descValueLabel.setStyleSheet("""
                    color: #2d2d2d;
                    font-size: 10pt;
                    margin-bottom: 10px;
                """)
                self.descValueLabel.setWordWrap(True)
                self.descContainerLayout.addWidget(self.descValueLabel)
            else:
                QMessageBox.warning(self, "Error", "Failed to save description.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save description: {str(e)}")
    
    def _onCancelDescriptionEdit(self):
        """Cancel description editing and restore 'Add Description' button."""
        # Clear the container
        while self.descContainerLayout.count():
            child = self.descContainerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Show "Add Description" button again
        self.addDescBtn = QPushButton("+ Add Description")
        self.addDescBtn.setStyleSheet("""
            QPushButton {
                background-color: #F8F6EB;
                color: #504B38;
                border: 1px dashed #D6CFAA;
                border-radius: 6px;
                font-size: 9pt;
                font-weight: 600;
                padding: 6px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
                border-color: #B9B28A;
            }
        """)
        self.addDescBtn.clicked.connect(self._onAddDescriptionClicked)
        self.descContainerLayout.addWidget(self.addDescBtn)
    
    def _onClose(self):
        """Handle close button click."""
        self.closed.emit()
        self.setParent(None)
    
    def _onToggleFavorite(self):
        """Handle favorite toggle."""
        photo_id = self.photoData.get('id')
        file_uuid = self.photoData.get('file_uuid')
        current_favorite = int(self.photoData.get('favorite', 0))
        target_state = not bool(current_favorite)
        
        try:
            # Persist via UUID when available
            if file_uuid:
                ok = self.catalogDb.update_photo(file_uuid, favorite=target_state)
            else:
                ok = False
            if not ok:
                QMessageBox.warning(self, "Favorites", "Failed to update favorite state.")
                return
            
            # Emit signal with updated state
            self.favoriteToggled.emit(photo_id, target_state)
            # Update local state and button label
            self.photoData['favorite'] = 1 if target_state else 0
            if hasattr(self, 'favBtn') and self.favBtn:
                self.favBtn.setText("Remove from Favorites" if target_state else "Add to Favorites")
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
            file_uuid = self.photoData.get('file_uuid', '')
            ok = self.catalogDb.delete_photo(file_uuid)
            if not ok:
                QMessageBox.warning(self, "Error", "Failed to delete photo.")
                return
            
            # Emit signal and close
            self.photoDeleted.emit(file_path)
            self.close()

