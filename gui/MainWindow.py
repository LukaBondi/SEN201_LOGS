"""
MainWindow.py
Author: LOGS Team
Date: October 25, 2025

Purpose:
    Main GUI window for the Photo Catalog Application.
    Provides interface for importing, searching, and managing photos.
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTextEdit,
                              QListWidget, QFileDialog, QMessageBox,
                              QTabWidget, QGroupBox, QScrollArea, QComboBox,
                              QInputDialog, QGridLayout, QFrame, QSplitter,
                              QDialog, QDialogButtonBox, QProgressDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

from src.PhotoImporter import PhotoImporter
from src.DatabaseManager import DatabaseManager
from src.SearchEngine import SearchEngine
from src.SimilaritySearch import SimilaritySearch
from src.FileScanner import scanDirectory
from gui.StyleSheet import getApplicationStyle, getTitleStyle, getSubtitleStyle
from gui.components.Sidebar import Sidebar
from gui.components.PhotoCard import PhotoCard
from gui.components.PhotoViewer import PhotoViewer
from gui.views.UploadView import UploadView
from gui.views.PhotoGridView import PhotoGridView
from gui.views.TagsView import TagsView
from gui.views.AlbumsView import AlbumsView
from gui.dialogs.ImportDialog import ImportDialog


class MainWindow(QMainWindow):
    """
    Main application window for the Photo Catalog.
    Integrates all modules into a cohesive user interface.
    """

    def __init__(self):
        """Initialize the main window and all components."""
        super().__init__()
        self.dbPath = os.path.join("data", "catalog.db")
        self._ensureDataDirectory()
        self._initializeModules()
        self._initializeUI()

    def _ensureDataDirectory(self):
        """Create data directory if it doesn't exist."""
        dataDir = os.path.dirname(self.dbPath)
        if not os.path.exists(dataDir):
            os.makedirs(dataDir)

    def _initializeModules(self):
        """Initialize all backend modules."""
        self.photoImporter = PhotoImporter(self.dbPath)
        self.dbManager = DatabaseManager(self.dbPath)
        self.searchEngine = SearchEngine(self.dbPath)
        self.similaritySearch = SimilaritySearch(self.dbPath)

    def _initializeUI(self):
        """Set up the user interface."""
        self.setWindowTitle("Photo Catalog - LOGS Project")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply custom stylesheet
        self.setStyleSheet(getApplicationStyle())

        # Create central widget and main layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QHBoxLayout(centralWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Create sidebar and main content area
        self._createSidebar()
        self._createMainContent()
        
        # Add to main layout
        mainLayout.addWidget(self.sidebar)
        mainLayout.addWidget(self.mainContent)
        
        # Set initial view
        self.currentView = "all_photos"
        self._showAllPhotos()

    def _createSidebar(self):
        """Create the left sidebar with navigation."""
        self.sidebar = Sidebar(self)
        self.sidebar.viewChanged.connect(self._switchView)

    def _createMainContent(self):
        """Create the main content area."""
        self.mainContent = QWidget()
        mainContentLayout = QVBoxLayout(self.mainContent)
        mainContentLayout.setContentsMargins(0, 0, 0, 0)
        mainContentLayout.setSpacing(16)
        
        # Top bar
        topBar = QWidget()
        topBar.setFixedHeight(80)
        topBar.setStyleSheet("background-color: #EBE5C2; border-bottom: 1px solid #B9B28A;")
        topBarLayout = QHBoxLayout(topBar)
        topBarLayout.setContentsMargins(30, 20, 30, 20)
        topBarLayout.setSpacing(15)
        
        # Search row (input, tag dropdown, button)
        searchRow = QWidget()
        searchRowLayout = QHBoxLayout(searchRow)
        searchRowLayout.setContentsMargins(0, 0, 0, 0)
        searchRowLayout.setSpacing(10)
        
        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("🔍 Search")
        self.searchInput.setFixedWidth(250)
        self.searchInput.setFixedHeight(40)
        self.searchInput.textChanged.connect(self._onNameSearch)
        searchRowLayout.addWidget(self.searchInput)
        
        self.tagsFilterCombo = QComboBox()
        self.tagsFilterCombo.addItem("TAGS ▼")
        self.tagsFilterCombo.setFixedWidth(120)
        self.tagsFilterCombo.setFixedHeight(40)
        self.tagsFilterCombo.currentIndexChanged.connect(self._onTagSearch)
        self._populateTagsDropdown()
        searchRowLayout.addWidget(self.tagsFilterCombo)
        
        self.searchBtn = QPushButton("SEARCH")
        self.searchBtn.setFixedWidth(120)
        self.searchBtn.setFixedHeight(40)
        self.searchBtn.setStyleSheet("""
            QPushButton {
                background-color: #B9B28A;
                color: #504B38;
                border: 2px solid #504B38;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: white;
            }
        """)
        self.searchBtn.clicked.connect(self._onExplicitSearch)
        searchRowLayout.addWidget(self.searchBtn)
        
        topBarLayout.addWidget(searchRow)
        topBarLayout.addStretch()
        
        # Upload button
        self.uploadBtn = QPushButton("UPLOAD")
        self.uploadBtn.setFixedWidth(120)
        self.uploadBtn.setFixedHeight(40)
        self.uploadBtn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #504B38;
                border: 2px solid #504B38;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: white;
            }
        """)
        self.uploadBtn.clicked.connect(self._openUploadDialog)
        topBarLayout.addWidget(self.uploadBtn)
        
        mainContentLayout.addWidget(topBar)
        
        # Content area (scrollable)
        self.contentScrollArea = QScrollArea()
        self.contentScrollArea.setWidgetResizable(True)
        self.contentScrollArea.setStyleSheet("border: none;")
        
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(30, 40, 30, 40)
        
        self.contentScrollArea.setWidget(self.contentWidget)
        mainContentLayout.addWidget(self.contentScrollArea)

    def _onTagSearch(self, index):
        # Ignore first item ("TAGS ▼")
        if index == 0:
            return
        tag = self.tagsFilterCombo.currentText()
        if tag == "TAGS ▼":
            return
        try:
            results = self.similaritySearch.findSimilarPhotosByTag(tag)
            self._showSearchResults(results)
        except Exception as e:
            errorLabel = QLabel(f"Error searching by tag: {str(e)}")
            errorLabel.setStyleSheet("color: red;")
            self.contentLayout.addWidget(errorLabel)

    def _onNameSearch(self, text):
        # Live search by name
        if not text.strip():
            self._showAllPhotos()
            return
        try:
            results = self.searchEngine.searchPhotos(title=text.strip(), tags=None)
            self._showSearchResults(results)
        except Exception as e:
            errorLabel = QLabel(f"Error searching by name: {str(e)}")
            errorLabel.setStyleSheet("color: red;")
            self.contentLayout.addWidget(errorLabel)

    def _onExplicitSearch(self):
        # Explicit search button click
        name = self.searchInput.text().strip()
        tagIndex = self.tagsFilterCombo.currentIndex()
        tag = self.tagsFilterCombo.currentText() if tagIndex > 0 else None
        try:
            if name and tag and tag != "TAGS ▼":
                # Search by both name and tag
                results = self.searchEngine.searchPhotos(title=name, tags=tag)
            elif name:
                results = self.searchEngine.searchPhotos(title=name, tags=None)
            elif tag and tag != "TAGS ▼":
                results = self.similaritySearch.findSimilarPhotosByTag(tag)
            else:
                self._showAllPhotos()
                return
            self._showSearchResults(results)
        except Exception as e:
            errorLabel = QLabel(f"Error searching: {str(e)}")
            errorLabel.setStyleSheet("color: red;")
            self.contentLayout.addWidget(errorLabel)

    def _showSearchResults(self, photos):
        # Clear current content area before showing search results only
        while self.contentLayout.count():
            item = self.contentLayout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Normalize incoming photo records to a format PhotoCard understands
        normalized = self._normalizePhotosForGrid(photos or [])

        # Show search results using PhotoGridView (do not append all photos)
        titleLabel = QLabel("Results from search")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)
        grid = PhotoGridView(normalized, "No results found.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        self.contentLayout.addWidget(grid)
        self.contentLayout.addStretch()
        # Note: intentionally NOT appending all photos below results to avoid confusion

    def _normalizePhotosForGrid(self, photos):
        """
        Normalize different photo tuple/dict shapes into a format
        compatible with PhotoCard (either full tuple with file_path at [2]
        or dict with keys: name, file_path, tags).

        Supported inputs:
        - SearchEngine: (id, name, tags, file_path)
        - SimilaritySearch.findSimilarPhotosByTag: (id, name, file_path, album, tags, description, date_added)
        - SimilaritySearch.findSimilarPhotos: dict with name, file_path, tags
        - Already-normalized dicts/tuples pass through
        """
        normalized = []
        for p in photos:
            try:
                if isinstance(p, tuple):
                    if len(p) == 4:
                        # From SearchEngine: (id, name, tags, file_path)
                        _id, name, tags, file_path = p
                        normalized.append({
                            "name": name,
                            "file_path": file_path,
                            "tags": tags or "",
                        })
                    else:
                        # Assume full tuple already compatible with PhotoCard
                        normalized.append(p)
                elif isinstance(p, dict):
                    # Ensure required keys exist
                    name = p.get("name") or p.get("title") or ""
                    file_path = p.get("file_path") or p.get("path") or ""
                    tags = p.get("tags") or ""
                    normalized.append({
                        "name": name,
                        "file_path": file_path,
                        "tags": tags,
                    })
                else:
                    # Unknown type; skip safely
                    continue
            except Exception:
                # If any mapping issue occurs, skip that record
                continue
        return normalized

    def _populateTagsDropdown(self):
        """Populate the tags dropdown with all available tags from database."""
        try:
            tags = self.dbManager.getAllTags()
            for tag in tags:
                self.tagsFilterCombo.addItem(tag)
        except Exception as e:
            print(f"Error populating tags dropdown: {str(e)}")

    def _switchView(self, viewName):
        """Switch between different views."""
        self.currentView = viewName
        
        # Update sidebar button styles
        self.sidebar.setActiveView(viewName)
        
        # Clear current content
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Show appropriate view
        if viewName == "all_photos":
            self._showAllPhotos()
        elif viewName == "upload":
            self._showUploadView()
        elif viewName == "albums":
            self._showAlbumsView()
        elif viewName == "favorites":
            self._showFavoritesView()
        elif viewName == "tags":
            self._showTagsView()

    def _showAllPhotos(self):
        """Display all photos in grid view using PhotoGridView."""
        titleLabel = QLabel("All Photos")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)
        try:
            photos = self.photoImporter.listImportedPhotos()
        except Exception as e:
            errorLabel = QLabel(f"Error loading photos: {str(e)}")
            errorLabel.setStyleSheet("color: red;")
            self.contentLayout.addWidget(errorLabel)
            return
        grid = PhotoGridView(photos, "No photos in catalog. Click UPLOAD to add photos.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        self.contentLayout.addWidget(grid)
        self.contentLayout.addStretch()

    def _createPhotoCard(self, photo):
        """
        Create a photo card widget using the PhotoCard component.
        
        Args:
            photo: Photo data (tuple or dict).
            
        Returns:
            PhotoCard: The created photo card widget.
        """
        card = PhotoCard(photo, self)
        card.photoClicked.connect(self._onPhotoCardClicked)
        card.deleteRequested.connect(self._onPhotoDeleteRequested)
        return card
    
    def _onPhotoDeleteRequested(self, file_path):
        """
        Handle photo deletion request from PhotoCard.
        
        Args:
            file_path (str): Path to the photo file to delete.
        """
        ok = self.photoImporter.removePhoto(file_path)
        if not ok:
            # Fallback delete via DatabaseManager if needed
            try:
                self.dbManager.deleteImage(os.path.basename(file_path))
            except Exception:
                pass
        self._refreshAfterDataChange()

    def _onPhotoCardClicked(self, photo):
        """Handle photo card click to show full viewer."""
        self._showPhotoViewer(photo)

    def _showPhotoViewer(self, photo):
        """Show photo viewer overlay."""
        # Remove any existing overlay
        if hasattr(self, 'viewerOverlay') and self.viewerOverlay:
            self.viewerOverlay.setParent(None)
            self.viewerOverlay = None
        
        # Create PhotoViewer component
        self.viewerOverlay = PhotoViewer(photo, self.dbManager, self.photoImporter, self)
        self.viewerOverlay.setGeometry(self.rect())
        
        # Connect signals
        self.viewerOverlay.closed.connect(self._onViewerClosed)
        self.viewerOverlay.favoriteToggled.connect(self._onViewerFavoriteToggled)
        self.viewerOverlay.photoDeleted.connect(self._onViewerPhotoDeleted)
        self.viewerOverlay.tagAdded.connect(self._onViewerTagAdded)
        
        self.viewerOverlay.show()
        self.viewerOverlay.raise_()

    def _onViewerClosed(self):
        """Handle viewer close."""
        if hasattr(self, 'viewerOverlay') and self.viewerOverlay:
            self.viewerOverlay.setParent(None)
            self.viewerOverlay = None

    def _onViewerFavoriteToggled(self, photo_id, new_state):
        """Handle favorite toggle from viewer."""
        # If we're on Favorites view and item was unfavorited, refresh view
        if getattr(self, 'currentView', None) == "favorites" and not new_state:
            self._onViewerClosed()
            self._refreshAfterDataChange()
        else:
            # Refresh the viewer with updated state
            if hasattr(self, 'viewerOverlay') and self.viewerOverlay:
                photo_data = self.viewerOverlay.photoData.copy()
                photo_data['favorite'] = 1 if new_state else 0
                self._showPhotoViewer(photo_data)

    def _onViewerPhotoDeleted(self, file_path):
        """Handle photo deletion from viewer."""
        self._onViewerClosed()
        self._refreshAfterDataChange()

    def _onViewerTagAdded(self, photo_id, file_path, new_tags):
        """Handle tag addition from viewer."""
        # Refresh viewer with updated tags
        if hasattr(self, 'viewerOverlay') and self.viewerOverlay:
            photo_data = self.viewerOverlay.photoData.copy()
            photo_data['tags'] = new_tags
            self._showPhotoViewer(photo_data)

    def _showUploadView(self):
        """Display the upload interface using UploadView component."""
        view = UploadView(self)
        view.uploadFileClicked.connect(self._uploadSingleFile)
        view.uploadFolderClicked.connect(self._uploadFolder)
        self.contentLayout.addWidget(view)

    def _uploadSingleFile(self):
        """Handle upload single file button click."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Photo",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp *.heic)"
        )
        
        if filePath:
            # Show import dialog
            self._showImportDialog(filePath)

    def _uploadFolder(self):
        """Handle upload folder button click."""
        dirPath = QFileDialog.getExistingDirectory(
            self,
            "Select Directory"
        )
        
        if dirPath:
            # Show bulk import confirmation
            self._performBulkImport(dirPath)

    def _showImportDialog(self, filePath):
        """Show dialog to add metadata for single photo import using ImportDialog component."""
        # Load existing albums
        try:
            albums = self.dbManager.getAllAlbums()
        except Exception:
            albums = []

        dialog = ImportDialog(self, filePath, albums)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            album = dialog.selectedAlbum()
            tags = dialog.tags()
            description = dialog.description()
            try:
                success = self.photoImporter.addPhoto(filePath, album, tags, description)
                if success:
                    QMessageBox.information(self, "Success", "Photo imported successfully!")
                    if self.currentView == "all_photos":
                        self._switchView("all_photos")
                else:
                    QMessageBox.warning(self, "Duplicate", "This photo is already in the catalog.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import photo:\n{str(e)}")

    def _performBulkImport(self, dirPath):
        """Perform bulk import from directory."""
        try:
            # Scan directory
            foundFiles = scanDirectory(dirPath)
            
            if not foundFiles:
                QMessageBox.information(self, "No Photos Found",
                                      f"No image files found in:\n{dirPath}")
                return
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Bulk Import",
                f"Found {len(foundFiles)} photo(s).\n\nImport all without metadata?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                imported = 0
                skipped = 0
                
                # Show progress
                progress = QProgressDialog("Importing photos...", "Cancel", 0, len(foundFiles), self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                
                for i, filePath in enumerate(foundFiles):
                    if progress.wasCanceled():
                        break
                    
                    progress.setValue(i)
                    success = self.photoImporter.addPhoto(filePath, "", [], "")
                    if success:
                        imported += 1
                    else:
                        skipped += 1
                
                progress.setValue(len(foundFiles))
                
                # Show results
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Imported: {imported} photo(s)\nSkipped (duplicates): {skipped}"
                )
                
                # Refresh view
                if self.currentView == "all_photos":
                    self._switchView("all_photos")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import:\n{str(e)}")


    def _showAlbumsView(self):
        """Display a list of album names using AlbumsView component."""
        try:
            albums = self.dbManager.getAllAlbums()
        except Exception:
            albums = []

        view = AlbumsView(albums, self)
        view.albumSelected.connect(self._showPhotosInAlbum)
        self.contentLayout.addWidget(view)

    def _showPhotosInAlbum(self, album):
        """Display all photos in the selected album."""
        # Track the current album for refresh after operations
        self.currentAlbumName = album
        # Clear current content
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        titleLabel = QLabel(f"Photos in Album: {album}")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)
        try:
            photos = self.dbManager.getPhotosByAlbum(album)
        except Exception:
            photos = []
        grid = PhotoGridView(photos, "This album has no photos yet.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        self.contentLayout.addWidget(grid)
        self.contentLayout.addStretch()

    def _refreshAfterDataChange(self):
        """Refresh the current view after data changes (delete/favorite/tag)."""
        try:
            if self.currentView == "all_photos":
                self._switchView("all_photos")
            elif self.currentView == "favorites":
                self._switchView("favorites")
            elif self.currentView == "albums":
                if hasattr(self, 'currentAlbumName') and self.currentAlbumName:
                    # Re-render photos in the selected album
                    self._showPhotosInAlbum(self.currentAlbumName)
                else:
                    self._switchView("albums")
            else:
                self._switchView(self.currentView)
        except Exception:
            # Fallback to all photos
            self._switchView("all_photos")

    def _showFavoritesView(self):
        """Display all photos marked as favorites using PhotoGridView."""
        titleLabel = QLabel("Favorites")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)

        try:
            photos = self.dbManager.getFavorites()
        except Exception:
            photos = []
        grid = PhotoGridView(photos, "No favorites yet. Open a photo and click 'Add to Favorites'.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        self.contentLayout.addWidget(grid)
        self.contentLayout.addStretch()

    def _showTagsView(self):
        """Display list of tags using TagsView and wire actions for create/delete."""
        # Fetch tags from DB
        try:
            tags = self.dbManager.getAllTags()
        except Exception:
            tags = []

        view = TagsView(tags, self)
        self.contentLayout.addWidget(view)

        def onCreate():
            text, ok = QInputDialog.getText(self, "Create Tag", "Tag name:")
            if ok:
                tag = text.strip()
                if tag:
                    self.dbManager.createTag(tag)
                    self._switchView("tags")

        def onDelete():
            try:
                currentTags = self.dbManager.getAllTags()
            except Exception:
                currentTags = []
            if not currentTags:
                QMessageBox.information(self, "Delete Tag", "No tags available to delete.")
                return
            tag, ok = QInputDialog.getItem(self, "Delete Tag", "Select a tag to delete:", currentTags, 0, False)
            if ok and tag:
                self.dbManager.deleteTag(tag)
                self._switchView("tags")

        view.createTagClicked.connect(onCreate)
        view.deleteTagClicked.connect(onDelete)

    def _onSearchChanged(self, text):
        """Handle search input changes."""
        # TODO: Implement live search filtering
        pass

    def _openUploadDialog(self):
        """Open upload dialog from top bar button."""
        self._switchView("upload")

    def _loadUploadAlbums(self):
        """Load albums into upload dropdown."""
        try:
            albums = self.dbManager.getAllAlbums()
            while self.uploadAlbumCombo.count() > 2:
                self.uploadAlbumCombo.removeItem(2)
            for album in albums:
                self.uploadAlbumCombo.addItem(album)
        except Exception as e:
            print(f"Error loading albums: {e}")

    def _onUploadAlbumChanged(self, text):
        """Handle album selection change in upload view."""
        if text == "-- Create New Album --":
            self.uploadNewAlbumInput.setVisible(True)
        else:
            self.uploadNewAlbumInput.setVisible(False)

    def _importSinglePhotoFromUpload(self):
        """Import photo from upload view."""
        filePath = self.uploadFileInput.text().strip()
        albumSelection = self.uploadAlbumCombo.currentText()
        
        if albumSelection == "-- No Album --":
            album = ""
        elif albumSelection == "-- Create New Album --":
            album = self.uploadNewAlbumInput.text().strip()
            if not album:
                QMessageBox.warning(self, "Missing Album Name", "Please enter a name for the new album.")
                return
        else:
            album = albumSelection
        
        tagsText = self.uploadTagsInput.text().strip()
        description = self.uploadDescInput.text().strip()
        
        if not filePath:
            QMessageBox.warning(self, "Missing Information", "Please select a photo file.")
            return
        
        if not os.path.exists(filePath):
            QMessageBox.critical(self, "File Not Found", f"The file does not exist:\n{filePath}")
            return
        
        tags = [tag.strip() for tag in tagsText.split(",") if tag.strip()]
        
        try:
            success = self.photoImporter.addPhoto(filePath, album, tags, description)
            if success:
                QMessageBox.information(self, "Success", "Photo imported successfully!")
                self.uploadFileInput.clear()
                self.uploadAlbumCombo.setCurrentIndex(0)
                self.uploadNewAlbumInput.clear()
                self.uploadNewAlbumInput.setVisible(False)
                self.uploadTagsInput.clear()
                self.uploadDescInput.clear()
                self._loadUploadAlbums()
            else:
                QMessageBox.warning(self, "Duplicate", "This photo is already in the catalog.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import photo:\n{str(e)}")

    def _createImportTab(self):
        """Create the import photos tab."""
        importWidget = QWidget()
        layout = QVBoxLayout(importWidget)

        # Title
        titleLabel = QLabel("Import Photos")
        titleLabel.setStyleSheet(getTitleStyle())
        layout.addWidget(titleLabel)

        # Single file import group
        singleFileGroup = QGroupBox("Import Single Photo")
        singleFileLayout = QVBoxLayout()

        filePathLayout = QHBoxLayout()
        self.filePathInput = QLineEdit()
        self.filePathInput.setPlaceholderText("Select a photo file...")
        browseButton = QPushButton("Browse...")
        browseButton.clicked.connect(self._browseSingleFile)
        filePathLayout.addWidget(QLabel("File:"))
        filePathLayout.addWidget(self.filePathInput)
        filePathLayout.addWidget(browseButton)
        singleFileLayout.addLayout(filePathLayout)

        albumLayout = QHBoxLayout()
        albumLayout.addWidget(QLabel("Album:"))
        self.albumComboBox = QComboBox()
        self.albumComboBox.setEditable(False)
        self.albumComboBox.addItem("-- No Album --")
        self.albumComboBox.addItem("-- Create New Album --")
        albumLayout.addWidget(self.albumComboBox)
        self.albumComboBox.currentTextChanged.connect(self._onAlbumSelectionChanged)
        singleFileLayout.addLayout(albumLayout)

        self.newAlbumInput = QLineEdit()
        self.newAlbumInput.setPlaceholderText("Enter new album name...")
        self.newAlbumInput.setVisible(False)
        singleFileLayout.addWidget(self.newAlbumInput)

        tagsLayout = QHBoxLayout()
        self.tagsInput = QLineEdit()
        self.tagsInput.setPlaceholderText("e.g., nature, landscape, sunset")
        tagsLayout.addWidget(QLabel("Tags:"))
        tagsLayout.addWidget(self.tagsInput)
        singleFileLayout.addLayout(tagsLayout)

        descLayout = QHBoxLayout()
        self.descInput = QLineEdit()
        self.descInput.setPlaceholderText("Optional description...")
        descLayout.addWidget(QLabel("Description:"))
        descLayout.addWidget(self.descInput)
        singleFileLayout.addLayout(descLayout)

        importButton = QPushButton("Import Photo")
        importButton.clicked.connect(self._importSinglePhoto)
        singleFileLayout.addWidget(importButton)

        singleFileGroup.setLayout(singleFileLayout)
        layout.addWidget(singleFileGroup)

        # Directory scan group
        dirScanGroup = QGroupBox("Scan Directory")
        dirScanLayout = QVBoxLayout()

        dirLayout = QHBoxLayout()
        self.dirPathInput = QLineEdit()
        self.dirPathInput.setPlaceholderText("Select a directory to scan...")
        browseDirButton = QPushButton("Browse...")
        browseDirButton.clicked.connect(self._browseDirectory)
        dirLayout.addWidget(QLabel("Directory:"))
        dirLayout.addWidget(self.dirPathInput)
        dirLayout.addWidget(browseDirButton)
        dirScanLayout.addLayout(dirLayout)

        scanButton = QPushButton("Scan & Import All Photos")
        scanButton.clicked.connect(self._scanAndImport)
        dirScanLayout.addWidget(scanButton)

        self.scanResultText = QTextEdit()
        self.scanResultText.setReadOnly(True)
        self.scanResultText.setMaximumHeight(150)
        dirScanLayout.addWidget(QLabel("Scan Results:"))
        dirScanLayout.addWidget(self.scanResultText)

        dirScanGroup.setLayout(dirScanLayout)
        layout.addWidget(dirScanGroup)

        layout.addStretch()
        self.tabWidget.addTab(importWidget, "Import")

    def _createSearchTab(self):
        """Create the search photos tab."""
        searchWidget = QWidget()
        layout = QVBoxLayout(searchWidget)

        # Title
        titleLabel = QLabel("Search Photos")
        titleLabel.setStyleSheet(getTitleStyle())
        layout.addWidget(titleLabel)

        # Search inputs
        searchGroup = QGroupBox("Search Criteria")
        searchLayout = QVBoxLayout()

        nameLayout = QHBoxLayout()
        self.searchNameInput = QLineEdit()
        self.searchNameInput.setPlaceholderText("Search by photo name...")
        nameLayout.addWidget(QLabel("Name:"))
        nameLayout.addWidget(self.searchNameInput)
        searchLayout.addLayout(nameLayout)

        tagsLayout = QHBoxLayout()
        self.searchTagsInput = QLineEdit()
        self.searchTagsInput.setPlaceholderText("Search by tags (comma-separated)...")
        tagsLayout.addWidget(QLabel("Tags:"))
        tagsLayout.addWidget(self.searchTagsInput)
        searchLayout.addLayout(tagsLayout)

        searchButton = QPushButton("Search")
        searchButton.clicked.connect(self._performSearch)
        searchLayout.addWidget(searchButton)

        searchGroup.setLayout(searchLayout)
        layout.addWidget(searchGroup)

        # Results
        resultsLabel = QLabel("Search Results:")
        layout.addWidget(resultsLabel)

        self.searchResultsList = QListWidget()
        self.searchResultsList.itemClicked.connect(self._displayPhotoDetails)
        layout.addWidget(self.searchResultsList)

        self.tabWidget.addTab(searchWidget, "Search")

    def _createBrowseTab(self):
        """Create the browse all photos tab."""
        browseWidget = QWidget()
        layout = QVBoxLayout(browseWidget)

        # Title
        titleLabel = QLabel("Browse All Photos")
        titleLabel.setStyleSheet(getTitleStyle())
        layout.addWidget(titleLabel)

        refreshButton = QPushButton("Refresh List")
        refreshButton.clicked.connect(self._refreshPhotoList)
        layout.addWidget(refreshButton)

        self.browseList = QListWidget()
        self.browseList.itemClicked.connect(self._displayPhotoDetails)
        layout.addWidget(self.browseList)

        # Photo details
        detailsGroup = QGroupBox("Photo Details")
        detailsLayout = QVBoxLayout()

        self.detailsText = QTextEdit()
        self.detailsText.setReadOnly(True)
        self.detailsText.setMaximumHeight(150)
        detailsLayout.addWidget(self.detailsText)

        deleteButton = QPushButton("Delete Selected Photo")
        deleteButton.clicked.connect(self._deletePhoto)
        detailsLayout.addWidget(deleteButton)

        detailsGroup.setLayout(detailsLayout)
        layout.addWidget(detailsGroup)

        self.tabWidget.addTab(browseWidget, "Browse")

        # Auto-refresh on tab load
        self._refreshPhotoList()

    def _createAlbumsTab(self):
        """Create the albums management tab."""
        albumsWidget = QWidget()
        layout = QVBoxLayout(albumsWidget)

        # Title
        titleLabel = QLabel("Manage Albums")
        titleLabel.setStyleSheet(getTitleStyle())
        layout.addWidget(titleLabel)

        # Album list
        albumListLabel = QLabel("Albums:")
        layout.addWidget(albumListLabel)

        self.albumsList = QListWidget()
        self.albumsList.itemClicked.connect(self._displayAlbumPhotos)
        layout.addWidget(self.albumsList)

        # Album management buttons
        buttonLayout = QHBoxLayout()
        refreshAlbumsButton = QPushButton("Refresh Albums")
        refreshAlbumsButton.clicked.connect(self._refreshAlbumsList)
        buttonLayout.addWidget(refreshAlbumsButton)

        renameAlbumButton = QPushButton("Rename Album")
        renameAlbumButton.clicked.connect(self._renameAlbum)
        buttonLayout.addWidget(renameAlbumButton)

        deleteAlbumButton = QPushButton("Delete Album")
        deleteAlbumButton.clicked.connect(self._deleteAlbum)
        buttonLayout.addWidget(deleteAlbumButton)

        layout.addLayout(buttonLayout)

        # Photos in album
        albumPhotosLabel = QLabel("Photos in Selected Album:")
        layout.addWidget(albumPhotosLabel)

        self.albumPhotosList = QListWidget()
        layout.addWidget(self.albumPhotosList)

        self.tabWidget.addTab(albumsWidget, "Albums")

        # Auto-refresh album list
        self._refreshAlbumsList()

    def _createSimilarityTab(self):
        """Create the similarity search tab."""
        similarityWidget = QWidget()
        layout = QVBoxLayout(similarityWidget)

        # Title
        titleLabel = QLabel("Find Similar Photos")
        titleLabel.setStyleSheet(getTitleStyle())
        layout.addWidget(titleLabel)

        # Reference photo selection
        refGroup = QGroupBox("Reference Photo")
        refLayout = QVBoxLayout()

        refPhotoLayout = QHBoxLayout()
        self.refPhotoInput = QLineEdit()
        self.refPhotoInput.setPlaceholderText("Enter photo name...")
        refPhotoLayout.addWidget(QLabel("Photo Name:"))
        refPhotoLayout.addWidget(self.refPhotoInput)
        refLayout.addLayout(refPhotoLayout)

        findButton = QPushButton("Find Similar Photos")
        findButton.clicked.connect(self._findSimilar)
        refLayout.addWidget(findButton)

        refGroup.setLayout(refLayout)
        layout.addWidget(refGroup)

        # Results
        resultsLabel = QLabel("Similar Photos:")
        layout.addWidget(resultsLabel)

        self.similarityResultsList = QListWidget()
        self.similarityResultsList.itemClicked.connect(self._displaySimilarPhotoDetails)
        layout.addWidget(self.similarityResultsList)

        self.tabWidget.addTab(similarityWidget, "Similarity Search")

    # Event handlers
    def _loadAlbums(self):
        """Load existing albums into the combo box."""
        try:
            albums = self.dbManager.getAllAlbums()
            # Clear existing items except the first two
            while self.albumComboBox.count() > 2:
                self.albumComboBox.removeItem(2)
            # Add existing albums
            for album in albums:
                self.albumComboBox.addItem(album)
        except Exception as e:
            print(f"Error loading albums: {e}")

    def _onAlbumSelectionChanged(self, text):
        """Handle album selection change."""
        if text == "-- Create New Album --":
            self.newAlbumInput.setVisible(True)
        else:
            self.newAlbumInput.setVisible(False)

    def _browseSingleFile(self):
        """Open file dialog to select a single photo."""
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Photo",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp *.heic)"
        )
        if filePath:
            self.filePathInput.setText(filePath)

    def _browseDirectory(self):
        """Open directory dialog to select a folder."""
        dirPath = QFileDialog.getExistingDirectory(
            self,
            "Select Directory"
        )
        if dirPath:
            self.dirPathInput.setText(dirPath)

    def _importSinglePhoto(self):
        """Import a single photo with metadata."""
        filePath = self.filePathInput.text().strip()
        albumSelection = self.albumComboBox.currentText()

        # Determine album name
        if albumSelection == "-- No Album --":
            album = ""
        elif albumSelection == "-- Create New Album --":
            album = self.newAlbumInput.text().strip()
            if not album:
                QMessageBox.warning(self, "Missing Album Name",
                                  "Please enter a name for the new album.")
                return
        else:
            album = albumSelection

        tagsText = self.tagsInput.text().strip()
        description = self.descInput.text().strip()

        if not filePath:
            QMessageBox.warning(self, "Missing Information",
                              "Please select a photo file.")
            return

        if not os.path.exists(filePath):
            QMessageBox.critical(self, "File Not Found",
                               f"The file does not exist:\n{filePath}")
            return

        # Process tags
        tags = [tag.strip() for tag in tagsText.split(",") if tag.strip()]

        try:
            success = self.photoImporter.addPhoto(filePath, album, tags, description)
            if success:
                QMessageBox.information(self, "Success",
                                      "Photo imported successfully!")
                # Clear inputs
                self.filePathInput.clear()
                self.albumComboBox.setCurrentIndex(0)
                self.newAlbumInput.clear()
                self.newAlbumInput.setVisible(False)
                self.tagsInput.clear()
                self.descInput.clear()
                # Refresh lists
                self._refreshPhotoList()
                self._loadAlbums()
                self._refreshAlbumsList()
            else:
                QMessageBox.warning(self, "Duplicate",
                                  "This photo is already in the catalog.")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to import photo:\n{str(e)}")

    def _scanAndImport(self):
        """Scan a directory and import all found photos."""
        dirPath = self.dirPathInput.text().strip()

        if not dirPath:
            QMessageBox.warning(self, "Missing Information",
                              "Please select a directory.")
            return

        if not os.path.exists(dirPath):
            QMessageBox.critical(self, "Directory Not Found",
                               f"The directory does not exist:\n{dirPath}")
            return

        try:
            # Scan directory
            foundFiles = scanDirectory(dirPath)
            self.scanResultText.clear()
            self.scanResultText.append(f"Found {len(foundFiles)} photo(s).\n")

            if not foundFiles:
                self.scanResultText.append("No photos found in the directory.")
                return

            # Import each file
            imported = 0
            skipped = 0
            for filePath in foundFiles:
                success = self.photoImporter.addPhoto(filePath, "", [], "")
                if success:
                    imported += 1
                    self.scanResultText.append(f"✓ Imported: {os.path.basename(filePath)}")
                else:
                    skipped += 1
                    self.scanResultText.append(f"⊗ Skipped (duplicate): {os.path.basename(filePath)}")

            self.scanResultText.append(f"\n--- Summary ---")
            self.scanResultText.append(f"Imported: {imported}")
            self.scanResultText.append(f"Skipped: {skipped}")

            # Refresh browse list
            self._refreshPhotoList()

        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to scan directory:\n{str(e)}")

    def _performSearch(self):
        """Perform a search based on user criteria."""
        name = self.searchNameInput.text().strip()
        tags = self.searchTagsInput.text().strip()

        if not name and not tags:
            QMessageBox.warning(self, "Missing Criteria",
                              "Please enter a name or tags to search.")
            return

        try:
            results = self.searchEngine.searchPhotos(title=name, tags=tags)
            self.searchResultsList.clear()

            if not results:
                self.searchResultsList.addItem("No photos found.")
                return

            for photoId, photoName, photoTags, filePath in results:
                displayText = f"{photoName} (Tags: {photoTags or 'None'})"
                self.searchResultsList.addItem(displayText)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Search failed:\n{str(e)}")

    def _refreshPhotoList(self):
        """Refresh the browse photo list."""
        try:
            photos = self.photoImporter.listImportedPhotos()
            self.browseList.clear()

            if not photos:
                self.browseList.addItem("No photos in catalog.")
                return

            for photo in photos:
                displayText = f"{photo['name']}"
                if photo.get('album'):
                    displayText += f" - Album: {photo['album']}"
                if photo.get('tags'):
                    displayText += f" (Tags: {photo['tags']})"
                self.browseList.addItem(displayText)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to load photos:\n{str(e)}")

    def _displayPhotoDetails(self, item):
        """Display details of the selected photo."""
        photoText = item.text()
        if photoText == "No photos in catalog." or photoText == "No photos found.":
            return

        # Extract photo name (before the first parenthesis)
        photoName = photoText.split(" (")[0]

        try:
            photos = self.photoImporter.listImportedPhotos()
            for photo in photos:
                if photo['name'] == photoName:
                    details = f"Name: {photo['name']}\n"
                    details += f"Path: {photo['file_path']}\n"
                    details += f"Album: {photo.get('album') or 'None'}\n"
                    details += f"Tags: {photo['tags'] or 'None'}\n"
                    details += f"Description: {photo['description'] or 'None'}\n"
                    details += f"Date Added: {photo['date_added']}"
                    self.detailsText.setText(details)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to load photo details:\n{str(e)}")

    def _deletePhoto(self):
        """Delete the currently selected photo."""
        currentItem = self.browseList.currentItem()
        if not currentItem:
            QMessageBox.warning(self, "No Selection",
                              "Please select a photo to delete.")
            return

        photoText = currentItem.text()
        if photoText == "No photos in catalog.":
            return

        photoName = photoText.split(" (")[0]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{photoName}' from the catalog?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Find the file path
                photos = self.photoImporter.listImportedPhotos()
                for photo in photos:
                    if photo['name'] == photoName:
                        success = self.photoImporter.removePhoto(photo['file_path'])
                        if success:
                            QMessageBox.information(self, "Success",
                                                  "Photo deleted successfully!")
                            self._refreshPhotoList()
                            self.detailsText.clear()
                        else:
                            QMessageBox.warning(self, "Error",
                                              "Failed to delete photo.")
                        break
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to delete photo:\n{str(e)}")

    def _findSimilar(self):
        """Find photos similar to the reference photo."""
        photoName = self.refPhotoInput.text().strip()

        if not photoName:
            QMessageBox.warning(self, "Missing Information",
                              "Please enter a photo name.")
            return

        try:
            similarPhotos = self.similaritySearch.findSimilarPhotos(photoName)
            self.similarityResultsList.clear()

            if not similarPhotos:
                self.similarityResultsList.addItem("No similar photos found.")
                return

            for photo in similarPhotos:
                displayText = f"{photo['name']} (Tags: {photo['tags'] or 'None'})"
                self.similarityResultsList.addItem(displayText)

        except ValueError as e:
            QMessageBox.warning(self, "Not Found", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Similarity search failed:\n{str(e)}")

    def _displaySimilarPhotoDetails(self, item):
        """Display details of a similar photo (placeholder)."""
        photoText = item.text()
        if photoText == "No similar photos found.":
            return

        photoName = photoText.split(" (")[0]
        QMessageBox.information(self, "Photo Info",
                              f"Selected: {photoName}\n\nView details in the Browse tab.")

    def _refreshAlbumsList(self):
        """Refresh the list of albums."""
        try:
            albums = self.dbManager.getAllAlbums()
            self.albumsList.clear()

            if not albums:
                self.albumsList.addItem("No albums created.")
                return

            for album in albums:
                # Get count of photos in album
                photos = self.dbManager.getPhotosByAlbum(album)
                displayText = f"{album} ({len(photos)} photo{'s' if len(photos) != 1 else ''})"
                self.albumsList.addItem(displayText)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to load albums:\n{str(e)}")

    def _displayAlbumPhotos(self, item):
        """Display all photos in the selected album."""
        albumText = item.text()
        if albumText == "No albums created.":
            return

        # Extract album name (before the parenthesis)
        albumName = albumText.split(" (")[0]

        try:
            photos = self.dbManager.getPhotosByAlbum(albumName)
            self.albumPhotosList.clear()

            if not photos:
                self.albumPhotosList.addItem("No photos in this album.")
                return

            for photo in photos:
                # photo tuple: (id, name, file_path, album, tags, description, date_added)
                photoName = photo[1]
                tags = photo[4] or "No tags"
                displayText = f"{photoName} (Tags: {tags})"
                self.albumPhotosList.addItem(displayText)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to load album photos:\n{str(e)}")

    def _renameAlbum(self):
        """Rename the selected album."""
        currentItem = self.albumsList.currentItem()
        if not currentItem:
            QMessageBox.warning(self, "No Selection",
                              "Please select an album to rename.")
            return

        albumText = currentItem.text()
        if albumText == "No albums created.":
            return

        oldName = albumText.split(" (")[0]

        newName, ok = QInputDialog.getText(
            self,
            "Rename Album",
            f"Enter new name for album '{oldName}':",
            QLineEdit.EchoMode.Normal,
            oldName
        )

        if ok and newName:
            newName = newName.strip()
            if newName == oldName:
                return

            try:
                self.dbManager.renameAlbum(oldName, newName)
                QMessageBox.information(self, "Success",
                                      f"Album renamed to '{newName}'.")
                self._refreshAlbumsList()
                self._loadAlbums()
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to rename album:\n{str(e)}")

    def _deleteAlbum(self):
        """Delete the selected album (removes album assignment from photos)."""
        currentItem = self.albumsList.currentItem()
        if not currentItem:
            QMessageBox.warning(self, "No Selection",
                              "Please select an album to delete.")
            return

        albumText = currentItem.text()
        if albumText == "No albums created.":
            return

        albumName = albumText.split(" (")[0]
