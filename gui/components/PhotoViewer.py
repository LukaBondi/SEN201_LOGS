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
    QFrame, QLineEdit, QGridLayout, QMessageBox, QTextEdit, QCompleter
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel


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
        self.photo_data = self._normalizePhotoData(photo)
        
        self._setupUi()
        
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
                'original_filename': photo.get('original_filename', ''),
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
                'original_filename': photo[8] if len(photo) > 8 else '',
                'file_path': file_path,
                'description': photo[5] if len(photo) > 5 else '',
                'tags': photo[4] if len(photo) > 4 else '',
                'date_added': photo[6] if len(photo) > 6 else 'xx/xx/xxxx',
                'favorite': photo[7] if len(photo) > 7 else 0,
            }
    
    def _setupUi(self):
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
        
        file_path = self.photo_data['file_path']
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
        """
        Add editable image name section to layout.
        
        Args:
            layout: Layout to add the name section to.
        """
        nameLabel = QLabel("IMAGE NAME")
        nameLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 11pt;
            font-weight: 600;
            font-family: 'Times New Roman', serif;
        """)
        layout.addWidget(nameLabel)
        
        # Container for dynamic name display/editing
        self.nameContainer = QWidget()
        self.nameContainerLayout = QVBoxLayout(self.nameContainer)
        self.nameContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.nameContainerLayout.setSpacing(4)
        
        # Row with name and edit button
        nameRow = QWidget()
        nameRowLayout = QHBoxLayout(nameRow)
        nameRowLayout.setContentsMargins(0, 0, 0, 0)
        nameRowLayout.setSpacing(8)
        
        # Display name
        self.nameValueLabel = QLabel(self.photo_data['name'])
        self.nameValueLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 14pt;
            font-weight: 400;
            margin-bottom: 4px;
        """)
        self.nameValueLabel.setWordWrap(True)
        nameRowLayout.addWidget(self.nameValueLabel, 1)
        
        # Edit button
        editNameBtn = QPushButton("Edit")
        editNameBtn.setFixedSize(60, 28)
        editNameBtn.setStyleSheet("""
            QPushButton {
                background-color: #F8F6EB;
                color: #504B38;
                border: 1px solid #D6CFAA;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: #FFFFFF;
            }
        """)
        editNameBtn.clicked.connect(self._onEditNameClicked)
        nameRowLayout.addWidget(editNameBtn, 0, Qt.AlignmentFlag.AlignTop)
        
        self.nameContainerLayout.addWidget(nameRow)
        
        # Original filename display (small text below, only if name was changed)
        self.originalFilenameLabel = QLabel()
        self.originalFilenameLabel.setStyleSheet("""
            color: #888;
            font-size: 9pt;
            font-style: italic;
            margin-bottom: 10px;
        """)
        self.originalFilenameLabel.setWordWrap(True)
        self._updateOriginalFilenameDisplay()
        self.nameContainerLayout.addWidget(self.originalFilenameLabel)
        
        layout.addWidget(self.nameContainer)
    
    def _updateOriginalFilenameDisplay(self):
        """
        Update the original filename label visibility and text.
        
        Shows original filename only if it differs from the current name.
        Hides the label if names are the same or no original exists.
        """
        original = self.photo_data.get('original_filename', '')
        current = self.photo_data.get('name', '')
        
        # Only show if original filename exists and is different from current name
        if original and original != current:
            # Remove extension from original filename for cleaner display
            original_without_ext = os.path.splitext(original)[0]
            if original_without_ext != current:
                self.originalFilenameLabel.setText(f"Original: {original}")
                self.originalFilenameLabel.setVisible(True)
            else:
                self.originalFilenameLabel.setVisible(False)
        else:
            self.originalFilenameLabel.setVisible(False)
    
    def _onEditNameClicked(self):
        """
        Switch to edit mode for photo name.
        
        Replaces the display label with an input field and Save/Cancel buttons.
        """
        # Clear the container
        while self.nameContainerLayout.count():
            child = self.nameContainerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create edit widget
        editWidget = QWidget()
        editLayout = QHBoxLayout(editWidget)
        editLayout.setContentsMargins(0, 0, 0, 0)
        editLayout.setSpacing(8)
        
        # Name input field
        self.nameLineEdit = QLineEdit()
        self.nameLineEdit.setText(self.photo_data.get('name', ''))
        self.nameLineEdit.setStyleSheet("""
            QLineEdit {
                color: #2d2d2d;
                font-size: 10pt;
                border: 1px solid #D6CFAA;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border-color: #B9B28A;
            }
        """)
        editLayout.addWidget(self.nameLineEdit, 1)
        
        # Save button
        saveBtn = QPushButton("Save")
        saveBtn.setStyleSheet("""
            QPushButton {
                background-color: #504B38;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: 600;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #3d3a2c;
            }
        """)
        saveBtn.clicked.connect(self._onSaveName)
        editLayout.addWidget(saveBtn)
        
        # Cancel button
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #504B38;
                border: 1px solid #D6CFAA;
                border-radius: 4px;
                font-size: 9pt;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #F8F6EB;
            }
        """)
        cancelBtn.clicked.connect(self._onCancelNameEdit)
        editLayout.addWidget(cancelBtn)
        
        self.nameContainerLayout.addWidget(editWidget)
        self.nameLineEdit.setFocus()
        self.nameLineEdit.selectAll()
    
    def _onSaveName(self):
        """
        Save the new photo name to database.
        
        Updates the photo name in the database and refreshes the display.
        Shows error message if save fails.
        """
        name = self.nameLineEdit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Empty Name", "Please enter a name or click Cancel.")
            return
        
        # Check if name actually changed - if not, just cancel
        current_name = self.photo_data.get('name', '')
        if name == current_name:
            # No change, just restore display mode
            self._onCancelNameEdit()
            return
        
        file_uuid = self.photo_data.get('file_uuid')
        if not file_uuid:
            QMessageBox.warning(self, "Error", "Photo UUID not found.")
            return
        
        try:
            # Update name in database
            success = self.catalogDb.update_photo(file_uuid, name=name)
            
            if success:
                # Update local data
                self.photo_data['name'] = name
                
                # Clear the container and show the new name with edit button
                while self.nameContainerLayout.count():
                    child = self.nameContainerLayout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                # Row with name and edit button
                nameRow = QWidget()
                nameRowLayout = QHBoxLayout(nameRow)
                nameRowLayout.setContentsMargins(0, 0, 0, 0)
                nameRowLayout.setSpacing(8)
                
                self.nameValueLabel = QLabel(name)
                self.nameValueLabel.setStyleSheet("""
                    color: #2d2d2d;
                    font-size: 14pt;
                    font-weight: 400;
                    margin-bottom: 4px;
                """)
                self.nameValueLabel.setWordWrap(True)
                nameRowLayout.addWidget(self.nameValueLabel, 1)
                
                # Edit button
                editNameBtn = QPushButton("Edit")
                editNameBtn.setFixedSize(60, 28)
                editNameBtn.setStyleSheet("""
                    QPushButton {
                        background-color: #F8F6EB;
                        color: #504B38;
                        border: 1px solid #D6CFAA;
                        border-radius: 4px;
                        font-size: 9pt;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #504B38;
                        color: #FFFFFF;
                    }
                """)
                editNameBtn.clicked.connect(self._onEditNameClicked)
                nameRowLayout.addWidget(editNameBtn, 0, Qt.AlignmentFlag.AlignTop)
                
                self.nameContainerLayout.addWidget(nameRow)
                
                # Recreate original filename label
                self.originalFilenameLabel = QLabel()
                self.originalFilenameLabel.setStyleSheet("""
                    color: #888;
                    font-size: 9pt;
                    font-style: italic;
                    margin-bottom: 10px;
                """)
                self.originalFilenameLabel.setWordWrap(True)
                self.nameContainerLayout.addWidget(self.originalFilenameLabel)
                
                # Update original filename display
                self._updateOriginalFilenameDisplay()
            else:
                QMessageBox.warning(self, "Error", "Failed to save name.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save name: {str(e)}")
    
    def _onCancelNameEdit(self):
        """
        Cancel name editing and restore display label with edit button.
        
        Discards any changes and returns to view mode.
        """
        # Clear the container
        while self.nameContainerLayout.count():
            child = self.nameContainerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Restore the name label with edit button
        name = self.photo_data.get('name', 'Untitled')
        
        # Row with name and edit button
        nameRow = QWidget()
        nameRowLayout = QHBoxLayout(nameRow)
        nameRowLayout.setContentsMargins(0, 0, 0, 0)
        nameRowLayout.setSpacing(8)
        
        self.nameValueLabel = QLabel(name)
        self.nameValueLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 14pt;
            font-weight: 400;
            margin-bottom: 4px;
        """)
        self.nameValueLabel.setWordWrap(True)
        nameRowLayout.addWidget(self.nameValueLabel, 1)
        
        # Edit button
        editNameBtn = QPushButton("Edit")
        editNameBtn.setFixedSize(60, 28)
        editNameBtn.setStyleSheet("""
            QPushButton {
                background-color: #F8F6EB;
                color: #504B38;
                border: 1px solid #D6CFAA;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: #FFFFFF;
            }
        """)
        editNameBtn.clicked.connect(self._onEditNameClicked)
        nameRowLayout.addWidget(editNameBtn, 0, Qt.AlignmentFlag.AlignTop)
        
        self.nameContainerLayout.addWidget(nameRow)
        
        # Recreate original filename label
        self.originalFilenameLabel = QLabel()
        self.originalFilenameLabel.setStyleSheet("""
            color: #888;
            font-size: 9pt;
            font-style: italic;
            margin-bottom: 10px;
        """)
        self.originalFilenameLabel.setWordWrap(True)
        self.nameContainerLayout.addWidget(self.originalFilenameLabel)
        
        # Update original filename display
        self._updateOriginalFilenameDisplay()
    
    def _addDescriptionSection(self, layout):
        """
        Add description section to layout.
        
        Args:
            layout: Layout to add the description section to.
        """
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
        
        description = self.photo_data.get('description') or ''
        
        if description:
            # Show existing description with edit button
            descRow = QWidget()
            descRowLayout = QHBoxLayout(descRow)
            descRowLayout.setContentsMargins(0, 0, 0, 0)
            descRowLayout.setSpacing(8)
            
            self.descValueLabel = QLabel(description)
            self.descValueLabel.setStyleSheet("""
                color: #2d2d2d;
                font-size: 10pt;
                margin-bottom: 10px;
            """)
            self.descValueLabel.setWordWrap(True)
            descRowLayout.addWidget(self.descValueLabel, 1)
            
            # Edit button
            editDescBtn = QPushButton("Edit")
            editDescBtn.setFixedSize(60, 28)
            editDescBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F8F6EB;
                    color: #504B38;
                    border: 1px solid #D6CFAA;
                    border-radius: 4px;
                    font-size: 9pt;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #504B38;
                    color: #FFFFFF;
                }
            """)
            editDescBtn.clicked.connect(self._onEditDescriptionClicked)
            descRowLayout.addWidget(editDescBtn, 0, Qt.AlignmentFlag.AlignTop)
            
            self.descContainerLayout.addWidget(descRow)
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
            self.addDescBtn.clicked.connect(lambda: self._onAddDescriptionClicked())
            self.descContainerLayout.addWidget(self.addDescBtn)
        
        layout.addWidget(self.descContainer)
    
    def _addTagsSection(self, layout):
        """
        Add tags display section to layout.
        
        Args:
            layout: Layout to add the tags section to.
        """
        tagsHeaderLabel = QLabel("TAGS")
        tagsHeaderLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 11pt;
            font-weight: 600;
            font-family: 'Times New Roman', serif;
            margin-bottom: 4px;
        """)
        layout.addWidget(tagsHeaderLabel)
        
        # Container for tags
        self.tagsContainer = QWidget()
        self.tagsContainerLayout = QVBoxLayout(self.tagsContainer)
        self.tagsContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsContainerLayout.setSpacing(5)
        
        # Parse tags
        tags_val = self.photo_data['tags']
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
            self.tagsContainerLayout.addWidget(noTagsLabel)
        else:
            # Display tags as removable chips
            for tag in tags:
                tagChip = self._createTagChip(tag)
                self.tagsContainerLayout.addWidget(tagChip)
        
        layout.addWidget(self.tagsContainer)
    
    def _createTagChip(self, tag):
        """
        Create a removable tag chip widget.
        
        Args:
            tag (str): Tag name to display.
            
        Returns:
            QWidget: Tag chip widget with remove button.
        """
        chipWidget = QWidget()
        chipLayout = QHBoxLayout(chipWidget)
        chipLayout.setContentsMargins(8, 4, 8, 4)
        chipLayout.setSpacing(8)
        
        chipWidget.setStyleSheet("""
            QWidget {
                background-color: #F8F6EB;
                border-left: 3px solid #B9B28A;
                border-radius: 4px;
            }
        """)
        
        # Tag name label
        tagLabel = QLabel(f"• {tag}")
        tagLabel.setStyleSheet("""
            color: #2d2d2d;
            font-size: 10pt;
            background-color: transparent;
        """)
        chipLayout.addWidget(tagLabel, 1)
        
        # Remove button
        removeBtn = QPushButton("×")
        removeBtn.setFixedSize(24, 24)
        removeBtn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        removeBtn.clicked.connect(lambda: self._onRemoveTag(tag))
        chipLayout.addWidget(removeBtn, 0, Qt.AlignmentFlag.AlignVCenter)
        
        return chipWidget
    
    def _onRemoveTag(self, tag):
        """
        Remove a tag from the photo.
        
        Args:
            tag (str): Tag name to remove.
        """
        file_uuid = self.photo_data.get('file_uuid')
        if not file_uuid:
            QMessageBox.warning(self, "Error", "Photo UUID not found.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Remove Tag",
            f"Remove tag '{tag}' from this photo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Remove tag from photo in database
            success = self.catalogDb.remove_tag_from_photo(file_uuid, tag)
            
            if success:
                # Update local data
                tags_val = self.photo_data['tags']
                if tags_val:
                    tags_list = [t.strip() for t in str(tags_val).split(',') if t.strip()]
                    tags_list = [t for t in tags_list if t != tag]
                    self.photo_data['tags'] = ','.join(tags_list) if tags_list else ''
                else:
                    self.photo_data['tags'] = ''
                
                # Refresh tags display
                self._refreshTagsDisplay()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove tag.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove tag: {str(e)}")
    
    def _refreshTagsDisplay(self):
        """
        Refresh the tags display after adding or removing tags.
        
        Clears the current tags container and rebuilds it with updated tags.
        Shows "No tags yet" message if no tags exist.
        """
        # Clear current tags display
        while self.tagsContainerLayout.count():
            child = self.tagsContainerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Parse updated tags
        tags_val = self.photo_data['tags']
        if tags_val:
            tags = [tag.strip() for tag in str(tags_val).split(',') if tag.strip()]
        else:
            tags = []
        
        if not tags:
            # Show "No tags yet" message
            noTagsLabel = QLabel("No tags yet")
            noTagsLabel.setStyleSheet("""
                color: #888;
                font-size: 9pt;
                font-style: italic;
                padding: 4px 0px;
            """)
            self.tagsContainerLayout.addWidget(noTagsLabel)
        else:
            # Display tags as removable chips
            for tag in tags:
                tagChip = self._createTagChip(tag)
                self.tagsContainerLayout.addWidget(tagChip)
    
    def _addFavoritesButton(self, layout):
        """
        Add favorites toggle button to layout.
        
        Args:
            layout: Layout to add the favorites button to.
        """
        favorite_val = bool(self.photo_data.get('favorite', 0))
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
        """
        Add delete button to layout.
        
        Args:
            layout: Layout to add the delete button to.
        """
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
        """
        Add interactive tag input section to layout.
        
        Args:
            layout: Layout to add the tag input section to.
        """
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
            
            # Set up autocomplete with existing tags
            try:
                tags_data = self.catalogDb.get_all_tags()
                # Extract tag names from dictionaries
                all_tags = [tag.get('name', tag) if isinstance(tag, dict) else tag for tag in tags_data]
                
                if all_tags:
                    # Create completer with existing tags
                    completer = QCompleter(all_tags)
                    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
                    completer.setFilterMode(Qt.MatchFlag.MatchContains)
                    
                    # Style the completer popup
                    completer.popup().setStyleSheet("""
                        QListView {
                            background-color: #FFFFFF;
                            border: 1px solid #D6CFAA;
                            border-radius: 4px;
                            padding: 4px;
                            color: #504B38;
                            font-size: 10pt;
                        }
                        QListView::item {
                            padding: 6px;
                            border-radius: 3px;
                        }
                        QListView::item:selected {
                            background-color: #F0EEDC;
                            color: #504B38;
                        }
                        QListView::item:hover {
                            background-color: #F8F6EB;
                        }
                    """)
                    
                    tagLineEdit.setCompleter(completer)
            except Exception:
                pass  # If we can't get tags, just continue without autocomplete
        
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
                    file_uuid = self.photo_data.get('file_uuid')
                    if not file_uuid:
                        QMessageBox.warning(self, "Error", "Photo UUID not found.")
                        return
                    
                    # Add the tag (this also creates the tag if it doesn't exist)
                    success = self.catalogDb.add_tag_to_photo(file_uuid, tag)
                    
                    if success:
                        # Fetch the actual current tags from the database
                        tags_list = self.catalogDb.get_photo_tags(file_uuid)
                        newTags = ', '.join(tags_list) if tags_list else ''
                        
                        # Update local data
                        self.photo_data['tags'] = newTags
                        
                        # Refresh tags display
                        self._refreshTagsDisplay()
                        
                        # Reset tag input
                        resetTagInput()
                        
                        # Emit signal to notify parent (but don't close viewer)
                        photo_id = self.photo_data.get('id')
                        file_path = self.photo_data.get('file_path')
                        self.tagAdded.emit(photo_id, file_path, newTags)
                    else:
                        QMessageBox.warning(
                            self, 
                            "Tag Already Added", 
                            f"Tag '{tag.lower()}' is already on this photo.\n\n"
                            "Note: Tags are case-insensitive, so 'Nature', 'NATURE', and 'nature' are treated as the same tag."
                        )
                        resetTagInput()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to add tag: {str(e)}")
                    resetTagInput()
                return
            resetTagInput()
        
        addTagLabel.mousePressEvent = showTagInput
        confirmTagBtn.clicked.connect(confirmTag)
        cancelTagBtn.clicked.connect(resetTagInput)
    
    def _addDateLabel(self, layout):
        """Add date label to layout."""
        dateLabel = QLabel(f"Photo taken on\n{self.photo_data['date_added']}")
        dateLabel.setStyleSheet("""
            color: #504B38;
            font-size: 8pt;
            font-style: italic;
        """)
        dateLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(dateLabel)
    
    def _onEditDescriptionClicked(self):
        """Handle 'Edit' button click for existing description."""
        existing_description = self.photo_data.get('description') or ''
        self._onAddDescriptionClicked(existing_description)
    
    def _onAddDescriptionClicked(self, existing_text=''):
        """Handle 'Add Description' button click - show inline edit field."""
        # Store original description for comparison (handle None values)
        self.originalDescription = self.photo_data.get('description') or ''
        
        # Ensure existing_text is never None
        if existing_text is None:
            existing_text = ''
        
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
        self.descTextEdit.setText(existing_text)  # Pre-populate with existing text
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
        
        # Check if description actually changed
        if description == self.originalDescription:
            # No change, just cancel
            self._onCancelDescriptionEdit()
            return
        
        if not description:
            QMessageBox.warning(self, "Empty Description", "Please enter a description or click Cancel.")
            return
        
        file_uuid = self.photo_data.get('file_uuid')
        if not file_uuid:
            QMessageBox.warning(self, "Error", "Photo UUID not found.")
            return
        
        try:
            # Update description in database
            success = self.catalogDb.update_photo(file_uuid, description=description)
            
            if success:
                # Update local data
                self.photo_data['description'] = description
                
                # Clear the container and show the new description with edit button
                while self.descContainerLayout.count():
                    child = self.descContainerLayout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                descRow = QWidget()
                descRowLayout = QHBoxLayout(descRow)
                descRowLayout.setContentsMargins(0, 0, 0, 0)
                descRowLayout.setSpacing(8)
                
                self.descValueLabel = QLabel(description)
                self.descValueLabel.setStyleSheet("""
                    color: #2d2d2d;
                    font-size: 10pt;
                    margin-bottom: 10px;
                """)
                self.descValueLabel.setWordWrap(True)
                descRowLayout.addWidget(self.descValueLabel, 1)
                
                # Edit button
                editDescBtn = QPushButton("Edit")
                editDescBtn.setFixedSize(60, 28)
                editDescBtn.setStyleSheet("""
                    QPushButton {
                        background-color: #F8F6EB;
                        color: #504B38;
                        border: 1px solid #D6CFAA;
                        border-radius: 4px;
                        font-size: 9pt;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #504B38;
                        color: #FFFFFF;
                    }
                """)
                editDescBtn.clicked.connect(self._onEditDescriptionClicked)
                descRowLayout.addWidget(editDescBtn, 0, Qt.AlignmentFlag.AlignTop)
                
                self.descContainerLayout.addWidget(descRow)
            else:
                QMessageBox.warning(self, "Error", "Failed to save description.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save description: {str(e)}")
    
    def _onCancelDescriptionEdit(self):
        """Cancel description editing and restore previous state."""
        # Clear the container
        while self.descContainerLayout.count():
            child = self.descContainerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        description = self.photo_data.get('description') or ''
        
        if description:
            # Restore the description label with edit button
            descRow = QWidget()
            descRowLayout = QHBoxLayout(descRow)
            descRowLayout.setContentsMargins(0, 0, 0, 0)
            descRowLayout.setSpacing(8)
            
            self.descValueLabel = QLabel(description)
            self.descValueLabel.setStyleSheet("""
                color: #2d2d2d;
                font-size: 10pt;
                margin-bottom: 10px;
            """)
            self.descValueLabel.setWordWrap(True)
            descRowLayout.addWidget(self.descValueLabel, 1)
            
            # Edit button
            editDescBtn = QPushButton("Edit")
            editDescBtn.setFixedSize(60, 28)
            editDescBtn.setStyleSheet("""
                QPushButton {
                    background-color: #F8F6EB;
                    color: #504B38;
                    border: 1px solid #D6CFAA;
                    border-radius: 4px;
                    font-size: 9pt;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #504B38;
                    color: #FFFFFF;
                }
            """)
            editDescBtn.clicked.connect(self._onEditDescriptionClicked)
            descRowLayout.addWidget(editDescBtn, 0, Qt.AlignmentFlag.AlignTop)
            
            self.descContainerLayout.addWidget(descRow)
        else:
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
            self.addDescBtn.clicked.connect(lambda: self._onAddDescriptionClicked())
            self.descContainerLayout.addWidget(self.addDescBtn)
    
    def _onClose(self):
        """Handle close button click."""
        self.closed.emit()
        self.setParent(None)
    
    def _onToggleFavorite(self):
        """Handle favorite toggle."""
        photo_id = self.photo_data.get('id')
        file_uuid = self.photo_data.get('file_uuid')
        current_favorite = int(self.photo_data.get('favorite', 0))
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
            self.photo_data['favorite'] = 1 if target_state else 0
            if hasattr(self, 'favBtn') and self.favBtn:
                self.favBtn.setText("Remove from Favorites" if target_state else "Add to Favorites")
        except Exception:
            pass
    
    def _onDelete(self):
        """Handle delete button click."""
        file_path = self.photo_data['file_path']
        if not file_path:
            QMessageBox.warning(self, "Delete", "Missing file path for this photo.")
            return
        
        reply = QMessageBox.question(
            self, "Delete Photo",
            f"Remove '{os.path.basename(file_path)}' from catalog? This will not delete the file from disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            file_uuid = self.photo_data.get('file_uuid', '')
            ok = self.catalogDb.delete_photo(file_uuid)
            if not ok:
                QMessageBox.warning(self, "Error", "Failed to delete photo.")
                return
            
            # Emit signal and close
            self.photoDeleted.emit(file_path)
            self.close()




