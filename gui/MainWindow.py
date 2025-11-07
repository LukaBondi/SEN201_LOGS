"""
MainWindow.py
Author: Satwik Singh
Date: October 25, 2025

Purpose:
    Main GUI window for the Photo Catalog Application.
    Provides interface for importing, searching, and managing photos.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTextEdit,
                              QListWidget, QFileDialog, QMessageBox,
                              QTabWidget, QGroupBox, QScrollArea, QComboBox,
                              QInputDialog, QGridLayout, QFrame, QSplitter,
                              QDialog, QDialogButtonBox, QProgressDialog, QCheckBox,
                              QListWidgetItem, QMenu)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QIcon

from src.photo_importer import PhotoImporter
from src.catalog_database import CatalogDatabase
# Removed unavailable modules: SearchEngine, SimilaritySearch, FileScanner.
# Provide a lightweight local directory scan helper.

from gui.StyleSheet import getApplicationStyle, getTitleStyle, getSubtitleStyle
from gui.components.Sidebar import Sidebar
from gui.components.PhotoCard import PhotoCard
from gui.components.PhotoViewer import PhotoViewer
from gui.views.PhotoGridView import PhotoGridView
from gui.views.TagsView import TagsView
from gui.views.AlbumsView import AlbumsView
from gui.dialogs.ImportDialog import ImportDialog

def scanDirectory(dirPath):
    """Return list of Path objects for supported image files in dir (non-recursive)."""
    p = Path(dirPath)
    supported = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic'}
    files = []
    for ext in supported:
        files.extend(p.glob(f"*{ext}"))
        files.extend(p.glob(f"*{ext.upper()}"))
    return files
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
        """Initialize required backend modules (simplified)."""
        self.catalogDb = CatalogDatabase(self.dbPath)
        self.photoImporter = PhotoImporter(self.catalogDb)
        # Remove legacy attributes for clarity
        # self.dbManager, self.searchEngine, self.similaritySearch are deprecated.

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
        topBar.setFixedHeight(85)
        # Remove bottom border to avoid the thin line under the toolbar
        topBar.setStyleSheet("background-color: #EBE5C2;")
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
        self.searchInput.setFixedWidth(300)
        self.searchInput.setFixedHeight(42)
        # Polished input style
        self.searchInput.setStyleSheet("""
            QLineEdit {
                background-color: #F8F6EB;
                border: 1px solid #D6CFAA;
                border-radius: 8px;
                padding: 8px 12px;
                color: #504B38;
            }
            QLineEdit:focus {
                border: 1px solid #B9B28A;
                background-color: #FFFFFF;
            }
        """)
        # Remove live search - only search on button click
        # self.searchInput.textChanged.connect(self._onNameSearch)
        searchRowLayout.addWidget(self.searchInput)
        
        # Tags filter button with custom dropdown
        self.tagsFilterBtn = QPushButton("TAGS ▼")
        self.tagsFilterBtn.setFixedWidth(140)
        self.tagsFilterBtn.setFixedHeight(42)
        self.tagsFilterBtn.setStyleSheet("""
            QPushButton {
                background-color: #F8F6EB;
                border: 1px solid #D6CFAA;
                border-radius: 8px;
                padding: 6px 10px;
                color: #504B38;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
            }
        """)
        self.tagsFilterBtn.clicked.connect(self._showTagsFilterPopup)
        self.selectedTags = []  # Track selected tags
        searchRowLayout.addWidget(self.tagsFilterBtn)
        
        self.searchBtn = QPushButton("SEARCH")
        self.searchBtn.setFixedWidth(120)
        self.searchBtn.setFixedHeight(42)
        self.searchBtn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #E6E0C7, stop:1 #D9D2AA);
                color: #504B38;
                border: 1px solid #B9B28A;
                border-radius: 8px;
                font-weight: 700;
                padding: 8px 10px;
            }
            QPushButton:hover {
                background-color: #B9B28A;
                color: #F8F3D9;
            }
        """)
        self.searchBtn.clicked.connect(self._onExplicitSearch)
        searchRowLayout.addWidget(self.searchBtn)
        
        topBarLayout.addWidget(searchRow)
        topBarLayout.addStretch()
        
        # Upload button with dropdown menu
        self.uploadBtn = QPushButton("UPLOAD")
        self.uploadBtn.setFixedWidth(120)
        self.uploadBtn.setFixedHeight(42)
        self.uploadBtn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #504B38;
                border: 1px dashed #CFC6A3;
                border-radius: 8px;
                font-weight: 700;
                padding: 8px 10px;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
                color: #333;
            }
            QPushButton::menu-indicator {
                image: none;
            }
        """)
        
        # Create dropdown menu
        from PyQt6.QtWidgets import QMenu
        uploadMenu = QMenu(self)
        uploadMenu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #CFC6A3;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                color: #504B38;
                font-weight: 600;
            }
            QMenu::item:selected {
                background-color: #F0EEDC;
                border-radius: 4px;
            }
        """)
        
        uploadFileAction = uploadMenu.addAction("UPLOAD FILE")
        uploadFileAction.triggered.connect(self._uploadSingleFile)
        
        uploadFolderAction = uploadMenu.addAction("UPLOAD FOLDER")
        uploadFolderAction.triggered.connect(self._uploadFolder)
        
        self.uploadBtn.setMenu(uploadMenu)
        topBarLayout.addWidget(self.uploadBtn)
        
        # Create Tag button (only visible in tags view)
        self.createTagBtn = QPushButton("CREATE TAG")
        self.createTagBtn.setFixedWidth(120)
        self.createTagBtn.setFixedHeight(42)
        self.createTagBtn.setStyleSheet("""
            QPushButton {
                background-color: #B9B28A;
                color: #2d2d2d;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                padding: 8px 10px;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: #F8F3D9;
            }
        """)
        self.createTagBtn.clicked.connect(self._onCreateTagFromTopBar)
        self.createTagBtn.setVisible(False)  # Hidden by default
        topBarLayout.addWidget(self.createTagBtn)
        
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
        """Deprecated - kept for compatibility. Use _performTagSearch instead."""
        pass

    def _onNameSearch(self, text):
        # Live search by name
        if not text.strip():
            self._showAllPhotos()
            return
        try:
            results = self.catalogDb.search_photos_by_name(text.strip())
            # Annotate with album list for badges
            for p in results:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
            self._showSearchResults(results)
        except Exception as e:
            errorLabel = QLabel(f"Error searching by name: {str(e)}")
            errorLabel.setStyleSheet("color: red;")
            self.contentLayout.addWidget(errorLabel)

    def _onExplicitSearch(self):
        # Explicit search button click
        name = self.searchInput.text().strip()
        
        try:
            if name and self.selectedTags:
                # Search by both name and tags
                # Get photos matching name first
                name_results = self.catalogDb.search_photos_by_name(name)
                
                # Filter by tags (require all selected tags)
                all_results = []
                seen_uuids = set()
                
                for photo in name_results:
                    photo_tags = photo.get('tags', '')
                    if isinstance(photo_tags, str):
                        photo_tags_list = [t.strip() for t in photo_tags.split(',') if t.strip()]
                    else:
                        photo_tags_list = photo_tags or []
                    
                    # Check if photo has ALL of the selected tags
                    if all(tag in photo_tags_list for tag in self.selectedTags):
                        photo_id = photo.get('file_uuid')
                        if photo_id and photo_id not in seen_uuids:
                            seen_uuids.add(photo_id)
                            all_results.append(photo)
                
                # Annotate with album list for badges
                for p in all_results:
                    try:
                        p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                    except Exception:
                        p['albums'] = []
                
                results = all_results
            elif name:
                results = self.catalogDb.search_photos_by_name(name)
                # Annotate with album list for badges
                for p in results:
                    try:
                        p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                    except Exception:
                        p['albums'] = []
            elif self.selectedTags:
                # Use the tag search method
                self._performTagSearch()
                return
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

        # Header row with title and back button
        headerRow = QWidget()
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(15)
        
        titleLabel = QLabel("Results from search")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38;")
        headerLayout.addWidget(titleLabel)
        
        headerLayout.addStretch()
        
        # Back to All Photos button
        backBtn = QPushButton("← Back to All Photos")
        backBtn.setFixedWidth(160)
        backBtn.setFixedHeight(40)
        backBtn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #504B38;
                border: 1px solid #D6CFAA;
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 10px;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
                color: #333;
            }
        """)
        backBtn.clicked.connect(lambda: self._switchView("all_photos"))
        headerLayout.addWidget(backBtn)
        
        self.contentLayout.addWidget(headerRow)
        
        # Show search results using PhotoGridView
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
        or dict with keys: name, file_path, tags, file_uuid).

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
                            "file_uuid": _id,  # id is the file_uuid
                            "name": name,
                            "file_path": file_path,
                            "tags": tags or "",
                        })
                    else:
                        # Assume full tuple already compatible with PhotoCard
                        normalized.append(p)
                elif isinstance(p, dict):
                    # Ensure required keys exist
                    file_uuid = p.get("file_uuid") or p.get("id") or ""
                    name = p.get("name") or p.get("title") or ""
                    # Check for full_path first (from search_photos_by_tags), then file_path, then path
                    file_path = p.get("full_path") or p.get("file_path") or p.get("path") or ""
                    tags = p.get("tags") or ""
                    normalized.append({
                        "file_uuid": file_uuid,
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

    def _showTagsFilterPopup(self):
        """Show a dropdown menu with tag search and checkboxes for filtering."""
        # Create a custom widget for the menu
        menuWidget = QWidget()
        menuWidget.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        menuWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        menuWidget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #D6CFAA;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(menuWidget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Search input for filtering tags
        tagSearchInput = QLineEdit()
        tagSearchInput.setPlaceholderText("🔍 Search tags...")
        tagSearchInput.setStyleSheet("""
            QLineEdit {
                background-color: #F8F6EB;
                border: 1px solid #D6CFAA;
                border-radius: 6px;
                padding: 6px 10px;
                color: #504B38;
            }
            QLineEdit:focus {
                border: 1px solid #B9B28A;
            }
        """)
        layout.addWidget(tagSearchInput)
        
        # Scroll area for tags list
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setMaximumHeight(250)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scrollArea.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F8F6EB;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #D6CFAA;
                border-radius: 4px;
            }
        """)
        
        # Container for checkboxes
        tagsContainer = QWidget()
        tagsLayout = QVBoxLayout(tagsContainer)
        tagsLayout.setContentsMargins(0, 0, 0, 0)
        tagsLayout.setSpacing(2)
        
        scrollArea.setWidget(tagsContainer)
        layout.addWidget(scrollArea)
        
        # Get all tags from database
        try:
            tags_data = self.catalogDb.get_all_tags()
            # Extract tag names from dictionaries
            all_tags = [tag.get('name', tag) if isinstance(tag, dict) else tag for tag in tags_data]
        except Exception:
            all_tags = []
        
        if not all_tags:
            noTagsLabel = QLabel("No tags available")
            noTagsLabel.setStyleSheet("color: #999; padding: 10px; font-style: italic;")
            tagsLayout.addWidget(noTagsLabel)
        else:
            # Create checkboxes for each tag
            tag_checkboxes = {}
            for tag in all_tags:
                checkbox = QCheckBox(tag)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        padding: 5px;
                        color: #504B38;
                        spacing: 8px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        border-radius: 3px;
                        border: 1px solid #D6CFAA;
                        background-color: #FFFFFF;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #4a5cb8;
                        border-color: #4a5cb8;
                    }
                    QCheckBox::indicator:hover {
                        border-color: #B9B28A;
                    }
                    QCheckBox:hover {
                        background-color: #F0EEDC;
                        border-radius: 4px;
                    }
                """)
                
                # Check if tag is already selected
                if tag in self.selectedTags:
                    checkbox.setChecked(True)
                
                tagsLayout.addWidget(checkbox)
                tag_checkboxes[tag] = checkbox
            
            tagsLayout.addStretch()
            
            # Filter tags based on search input
            def filterTags(searchText):
                searchText = searchText.lower()
                for tag, checkbox in tag_checkboxes.items():
                    # Show/hide based on search
                    checkbox.setVisible(searchText in tag.lower())
            
            tagSearchInput.textChanged.connect(filterTags)
        
        # Buttons
        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(8)
        
        clearBtn = QPushButton("Clear")
        clearBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #D6CFAA;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
            }
        """)
        if all_tags:
            clearBtn.clicked.connect(lambda: [cb.setChecked(False) for cb in tag_checkboxes.values()])
        buttonsLayout.addWidget(clearBtn)
        
        buttonsLayout.addStretch()
        
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #D6CFAA;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
            }
        """)
        cancelBtn.clicked.connect(menuWidget.close)
        buttonsLayout.addWidget(cancelBtn)
        
        applyBtn = QPushButton("Apply")
        applyBtn.setStyleSheet("""
            QPushButton {
                background-color: #4a5cb8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3a4ca8;
            }
        """)
        
        def applySelection():
            if all_tags:
                # Get selected tags
                self.selectedTags = [tag for tag, cb in tag_checkboxes.items() if cb.isChecked()]
                
                # Update button text
                if self.selectedTags:
                    if len(self.selectedTags) == 1:
                        self.tagsFilterBtn.setText(f"TAG: {self.selectedTags[0][:8]}...")
                    else:
                        self.tagsFilterBtn.setText(f"{len(self.selectedTags)} TAGS ▼")
                else:
                    self.tagsFilterBtn.setText("TAGS ▼")
                
                # Don't trigger search automatically - wait for SEARCH button click
            
            menuWidget.close()
        
        applyBtn.clicked.connect(applySelection)
        buttonsLayout.addWidget(applyBtn)
        
        layout.addLayout(buttonsLayout)
        
        # Position the menu below the button
        menuWidget.setFixedWidth(300)
        buttonPos = self.tagsFilterBtn.mapToGlobal(self.tagsFilterBtn.rect().bottomLeft())
        menuWidget.move(buttonPos.x(), buttonPos.y() + 5)
        
        # Show the menu
        menuWidget.show()
        tagSearchInput.setFocus()

    def _performTagSearch(self):
        """Perform search with selected tags."""
        if not self.selectedTags:
            self._showAllPhotos()
            return
        
        try:
            # Get photos that have ALL of the selected tags (AND logic)
            all_results = self.catalogDb.search_photos_by_tags(self.selectedTags, require_all=True)
            
            # Annotate with album list for badges
            for p in all_results:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
            
            self._showSearchResults(all_results)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to search by tags:\n{str(e)}")

    def _switchView(self, viewName):
        """Switch between different views."""
        self.currentView = viewName
        
        # Update sidebar button styles
        self.sidebar.setActiveView(viewName)
        
        # Show/hide top bar buttons based on view
        if viewName == "all_photos":
            # All Photos: Show search bar and upload button
            self.searchInput.setVisible(True)
            self.tagsFilterBtn.setVisible(True)
            self.searchBtn.setVisible(True)
            self.uploadBtn.setVisible(True)
            self.createTagBtn.setVisible(False)
        elif viewName == "tags":
            # Tags: Show upload and create tag buttons only
            self.searchInput.setVisible(False)
            self.tagsFilterBtn.setVisible(False)
            self.searchBtn.setVisible(False)
            self.uploadBtn.setVisible(True)
            self.createTagBtn.setVisible(True)
        else:
            # Albums, Favorites: Show only upload button
            self.searchInput.setVisible(False)
            self.tagsFilterBtn.setVisible(False)
            self.searchBtn.setVisible(False)
            self.uploadBtn.setVisible(True)
            self.createTagBtn.setVisible(False)
        
        # Clear current content
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Show appropriate view
        if viewName == "all_photos":
            self._showAllPhotos()
        elif viewName == "albums":
            self._showAlbumsView()
        elif viewName == "favorites":
            self._showFavoritesView()
        elif viewName == "tags":
            self._showTagsView()

    def _showAllPhotos(self):
        """Display all photos in grid view using PhotoGridView."""
        # Title and delete button row
        headerRow = QWidget()
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(15)
        
        titleLabel = QLabel("All Photos")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38;")
        headerLayout.addWidget(titleLabel)
        
        headerLayout.addStretch()
        
        # Add delete button (same size as upload button)
        deleteBtn = QPushButton("Delete Photos")
        deleteBtn.setFixedWidth(120)
        deleteBtn.setFixedHeight(40)
        deleteBtn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 10px;
                font-weight: 700;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        deleteBtn.clicked.connect(self._beginDeleteFromAllPhotos)
        headerLayout.addWidget(deleteBtn)
        
        self.contentLayout.addWidget(headerRow)
        
        try:
            photos = self.catalogDb.get_all_photos()
            # Annotate with album list for badges
            for p in photos:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
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
    
    def _onPhotoDeleteRequested(self, file_uuid: str):
        """
        Handle photo deletion request from PhotoCard.
        
        Args:
            file_uuid (str): UUID of the photo to delete.
        """
        try:
            ok = self.catalogDb.delete_photo(file_uuid)
            if not ok:
                QMessageBox.warning(self, "Delete Failed", "Photo could not be deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete photo:\n{e}")
        self._refreshAfterDataChange()

    def _onPhotoCardClicked(self, photo):
        """Handle photo card click to show full viewer with fresh data from database."""
        # Get file_uuid from the clicked photo
        file_uuid = photo.get('file_uuid') if isinstance(photo, dict) else None
        
        if file_uuid:
            # Fetch fresh data from database
            fresh_photo = self.catalogDb.get_photo_by_uuid(file_uuid)
            if fresh_photo:
                # Add albums info
                try:
                    fresh_photo['albums'] = self.catalogDb.get_photo_albums(file_uuid)
                except Exception:
                    fresh_photo['albums'] = []
                self._showPhotoViewer(fresh_photo)
            else:
                # Fallback to original photo data if fetch fails
                self._showPhotoViewer(photo)
        else:
            # No UUID available, use original photo data
            self._showPhotoViewer(photo)

    def _showPhotoViewer(self, photo):
        """Show photo viewer overlay."""
        # Remove any existing overlay
        if hasattr(self, 'viewerOverlay') and self.viewerOverlay:
            self.viewerOverlay.setParent(None)
            self.viewerOverlay = None
        
        # Create PhotoViewer component
        self.viewerOverlay = PhotoViewer(photo, self.catalogDb, self.photoImporter, self)
        self.viewerOverlay.setGeometry(self.rect())
        
        # Connect signals
        self.viewerOverlay.closed.connect(self._onViewerClosed)
        self.viewerOverlay.favoriteToggled.connect(self._onViewerFavoriteToggled)
        self.viewerOverlay.photoDeleted.connect(self._onViewerPhotoDeleted)
        self.viewerOverlay.tagAdded.connect(self._onViewerTagAdded)
        
        self.viewerOverlay.show()
        self.viewerOverlay.raise_()

    def _showImportDialog(self, filePath: str):
        """Show the ImportDialog for a single file and handle result."""
        try:
            dlg = ImportDialog(self, filePath, [a.get('name') for a in self.catalogDb.get_all_albums()])
            result = dlg.exec()
            if result == QDialog.DialogCode.Accepted:
                album = dlg.selectedAlbum()
                tags = dlg.tags()
                description = dlg.description()
                status = self.photoImporter.import_photo(Path(filePath), album=album, tags=tags, description=description)
                if status == self.photoImporter.SUCCESS:
                    QMessageBox.information(self, "Imported", "Photo imported successfully.")
                    # Always return to all photos view after successful import
                    self._switchView("all_photos")
                else:
                    QMessageBox.warning(self, "Duplicate", "This photo is already in the catalog.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import photo:\n{str(e)}")

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
        # Fetch fresh photo data from database and refresh viewer
        if hasattr(self, 'viewerOverlay') and self.viewerOverlay:
            file_uuid = self.viewerOverlay.photoData.get('file_uuid')
            if file_uuid:
                # Fetch complete fresh data from database
                fresh_photo = self.catalogDb.get_photo_by_uuid(file_uuid)
                if fresh_photo:
                    # Add albums info
                    try:
                        fresh_photo['albums'] = self.catalogDb.get_photo_albums(file_uuid)
                    except Exception:
                        fresh_photo['albums'] = []
                    self._showPhotoViewer(fresh_photo)
                else:
                    # Fallback: just update tags in existing data
                    photo_data = self.viewerOverlay.photoData.copy()
                    photo_data['tags'] = new_tags
                    self._showPhotoViewer(photo_data)
            else:
                # No UUID, fallback to old method
                photo_data = self.viewerOverlay.photoData.copy()
                photo_data['tags'] = new_tags
                self._showPhotoViewer(photo_data)

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
        
        if not dirPath:
            return
        
        # Check if folder has any supported image files before proceeding
        has_images = False
        for file_path in Path(dirPath).rglob('*'):
            if file_path.is_file() and self.photoImporter._is_supported_format(file_path):
                has_images = True
                break
        
        if not has_images:
            QMessageBox.warning(
                self,
                "Empty Folder",
                "The selected folder contains no supported image files.\n\n"
                "No album was created and nothing was imported."
            )
            return
        
        # Get default album name from folder name
        default_album_name = os.path.basename(dirPath)
        
        # Create custom dialog for album name and description
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Folder")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        titleLabel = QLabel(f"Import photos from: {default_album_name}")
        titleLabel.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 10px;")
        layout.addWidget(titleLabel)
        
        # Album name input
        albumLayout = QHBoxLayout()
        albumLayout.addWidget(QLabel("Album Name:"))
        albumInput = QLineEdit()
        albumInput.setText(default_album_name)
        albumInput.setPlaceholderText("Enter album name...")
        albumLayout.addWidget(albumInput)
        layout.addLayout(albumLayout)
        
        # Description input
        descLayout = QVBoxLayout()
        descLayout.addWidget(QLabel("Description (applies to all photos):"))
        descInput = QTextEdit()
        descInput.setPlaceholderText("Optional description for all imported photos...")
        descInput.setMaximumHeight(100)
        descLayout.addWidget(descInput)
        layout.addLayout(descLayout)
        
        # Info text
        infoLabel = QLabel(
            "• All photos in the folder (including subfolders) will be imported\n"
            "• They will be added to the specified album\n"
            "• All photos will have the same description\n"
            "• Tags can be added individually after import"
        )
        infoLabel.setStyleSheet("color: #666; font-size: 10pt; margin-top: 10px;")
        layout.addWidget(infoLabel)
        
        # Buttons
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #D6CFAA;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
            }
        """)
        cancelBtn.clicked.connect(dialog.reject)
        proceedBtn = QPushButton("Import")
        proceedBtn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #449d44;
            }
        """)
        proceedBtn.setDefault(True)
        proceedBtn.clicked.connect(dialog.accept)
        buttonLayout.addWidget(cancelBtn)
        buttonLayout.addWidget(proceedBtn)
        layout.addLayout(buttonLayout)
        
        # Show dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get values
        album_name = albumInput.text().strip()
        description = descInput.toPlainText().strip()
        
        if not album_name:
            QMessageBox.warning(self, "Missing Album Name", "Please enter an album name.")
            return
        
        # Show progress dialog
        progress = QProgressDialog("Scanning and importing photos...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Import folder using PhotoImporter
        try:
            imported_uuids = self.photoImporter.import_folder(
                Path(dirPath),
                album=album_name,
                description=description
            )
            
            progress.close()
            
            # Check if any photos were actually imported
            total_imported = len(imported_uuids)
            if total_imported > 0:
                # Only create album if photos were successfully imported
                self.catalogDb.create_album(album_name)
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Successfully imported {total_imported} photo(s) into album '{album_name}'"
                )
                # Always return to all photos view after import
                self._switchView("all_photos")
            else:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    "No new photos were imported. All photos may already exist in the catalog.\n\n"
                    "No album was created."
                )
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Failed to import folder:\n{str(e)}")


    def _showAlbumsView(self):
        """Display a list of album names using AlbumsView component."""
        try:
            albums = [a.get('name') for a in self.catalogDb.get_all_albums()]
        except Exception:
            albums = []

        view = AlbumsView(albums, self)
        view.albumSelected.connect(self._showPhotosInAlbum)
        view.createAlbumRequested.connect(self._onCreateAlbumRequested)
        view.selectPhotosRequested.connect(self._onSelectPhotosRequested)
        view.deleteAlbumRequested.connect(self._deleteAlbumFromAlbumsView)
        self.contentLayout.addWidget(view)

    def _onCreateAlbumRequested(self):
        """Prompt for album name and create it."""
        name, ok = QInputDialog.getText(self, "Create Album", "Album name:")
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter an album name.")
            return
        try:
            self.catalogDb.create_album(name)
            QMessageBox.information(self, "Album Created", f"Album '{name}' created.")
            # Refresh albums view
            self._switchView("albums")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create album:\n{str(e)}")

    def _onSelectPhotosRequested(self, album: str):
        """Begin the select-photos-to-album flow for the given album."""
        # Show a temporary panel that lists all photos in selectable mode
        try:
            # Load only photos that are not already in the target album
            photos = self.catalogDb.get_photos_not_in_album(album)
            for p in photos:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load photos:\n{str(e)}")
            return

        # Clear current content and show selection UI
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        titleLabel = QLabel(f"Select photos to add to album: {album}")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)

        grid = PhotoGridView(photos, "No photos found.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        grid.setPhotos(photos)
        grid.enableSelectionMode(True)
        self.contentLayout.addWidget(grid)

        # Action buttons
        actions = QWidget()
        actionsLayout = QHBoxLayout(actions)
        addBtn = QPushButton("Add Selected to Album")
        addBtn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #449d44;
            }
        """)
        addBtn.clicked.connect(lambda: self._addSelectedToAlbum(grid, album))
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #D6CFAA;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
            }
        """)
        cancelBtn.clicked.connect(lambda: self._switchView("albums"))
        actionsLayout.addWidget(addBtn)
        actionsLayout.addWidget(cancelBtn)
        self.contentLayout.addWidget(actions)
        self.contentLayout.addStretch()

    def _addSelectedToAlbum(self, grid: 'PhotoGridView', album: str):
        """Assign the selected photos in the grid to the given album."""
        selected = grid.getSelectedFileUUIDs()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select one or more photos to add.")
            return
        try:
            # Ensure album exists
            self.catalogDb.create_album(album)
            for file_uuid in selected:
                self.catalogDb.add_photo_to_album(file_uuid, album)
            QMessageBox.information(self, "Success", f"Added {len(selected)} photo(s) to '{album}'.")
            # Return to albums view
            self._switchView("albums")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to assign photos to album:\n{str(e)}")

    def _showPhotosInAlbum(self, album):
        """Display all photos in the selected album."""
        # Track the current album for refresh after operations
        self.currentAlbumName = album
        # Clear current content
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Header row with title and back button
        headerRow = QWidget()
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(15)
        
        titleLabel = QLabel(f"Photos in Album: {album}")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38;")
        headerLayout.addWidget(titleLabel)
        
        headerLayout.addStretch()
        
        # Back to Albums button
        backBtn = QPushButton("← Back to Albums")
        backBtn.setFixedWidth(160)
        backBtn.setFixedHeight(40)
        backBtn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #504B38;
                border: 1px solid #D6CFAA;
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 10px;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
                color: #333;
            }
        """)
        backBtn.clicked.connect(lambda: self._switchView("albums"))
        headerLayout.addWidget(backBtn)
        
        self.contentLayout.addWidget(headerRow)
        
        # Add actions row for album
        actionsRow = QWidget()
        actionsLayout = QHBoxLayout(actionsRow)
        actionsLayout.setContentsMargins(0, 10, 0, 10)
        removeBtn = QPushButton("Remove Photos")
        removeBtn.setStyleSheet("""
            QPushButton {
                background-color: #f0ad4e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ec971f;
            }
        """)
        removeBtn.clicked.connect(lambda: self._beginRemoveFromAlbum(album))
        actionsLayout.addWidget(removeBtn)
        deleteBtn = QPushButton("Delete Album")
        deleteBtn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        deleteBtn.clicked.connect(lambda: self._deleteAlbumFromView(album))
        actionsLayout.addWidget(deleteBtn)
        actionsLayout.addStretch()
        self.contentLayout.addWidget(actionsRow)
        try:
            photos = self.catalogDb.get_album_photos(album)
            for p in photos:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
        except Exception:
            photos = []
        grid = PhotoGridView(photos, "This album has no photos yet.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        self.contentLayout.addWidget(grid)
        self.contentLayout.addStretch()

    def _beginRemoveFromAlbum(self, album: str):
        """Start multi-select removal flow for a given album."""
        try:
            photos = self.catalogDb.get_album_photos(album)
            for p in photos:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load album photos:\n{str(e)}")
            return
        # Clear content
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        titleLabel = QLabel(f"Remove photos from album: {album}")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)
        grid = PhotoGridView(photos, "No photos in this album.", self)
        grid.setPhotos(photos)
        grid.enableSelectionMode(True)
        self.contentLayout.addWidget(grid)
        actions = QWidget()
        actionsLayout = QHBoxLayout(actions)
        removeBtn = QPushButton("Remove Selected")
        removeBtn.setStyleSheet("""
            QPushButton {
                background-color: #f0ad4e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ec971f;
            }
        """)
        removeBtn.clicked.connect(lambda: self._removeSelectedFromAlbum(grid, album))
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #D6CFAA;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
            }
        """)
        cancelBtn.clicked.connect(lambda: self._showPhotosInAlbum(album))
        actionsLayout.addWidget(removeBtn)
        actionsLayout.addWidget(cancelBtn)
        self.contentLayout.addWidget(actions)
        self.contentLayout.addStretch()

    def _removeSelectedFromAlbum(self, grid: 'PhotoGridView', album: str):
        uuids = grid.getSelectedFileUUIDs()
        if not uuids:
            QMessageBox.information(self, "No Selection", "Select photos to remove.")
            return
        removed = 0
        for u in uuids:
            try:
                if self.catalogDb.remove_photo_from_album(u, album):
                    removed += 1
            except Exception:
                pass
        QMessageBox.information(self, "Removed", f"Removed {removed} photo(s) from '{album}'.")
        self._showPhotosInAlbum(album)

    def _beginDeleteFromAllPhotos(self):
        """Start multi-select deletion flow for all photos."""
        try:
            photos = self.catalogDb.get_all_photos()
            for p in photos:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load photos:\n{str(e)}")
            return
        
        # Clear content
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        titleLabel = QLabel("Select photos to delete")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        self.contentLayout.addWidget(titleLabel)
        
        # Warning message
        warningLabel = QLabel("⚠️ Selected photos will be permanently deleted from the catalog!")
        warningLabel.setStyleSheet("""
            color: #dc3545;
            font-weight: bold;
            font-size: 10pt;
            padding: 8px;
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
        """)
        self.contentLayout.addWidget(warningLabel)
        
        grid = PhotoGridView(photos, "No photos in catalog.", self)
        grid.setPhotos(photos)
        grid.enableSelectionMode(True)
        self.contentLayout.addWidget(grid)
        
        actions = QWidget()
        actionsLayout = QHBoxLayout(actions)
        deleteBtn = QPushButton("Delete Selected")
        deleteBtn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        deleteBtn.clicked.connect(lambda: self._deleteSelectedPhotos(grid))
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #D6CFAA;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #F0EEDC;
            }
        """)
        cancelBtn.clicked.connect(lambda: self._switchView("all_photos"))
        actionsLayout.addWidget(deleteBtn)
        actionsLayout.addWidget(cancelBtn)
        actionsLayout.addStretch()
        self.contentLayout.addWidget(actions)
        self.contentLayout.addStretch()

    def _deleteSelectedPhotos(self, grid: 'PhotoGridView'):
        """Delete selected photos from the catalog."""
        uuids = grid.getSelectedFileUUIDs()
        if not uuids:
            QMessageBox.information(self, "No Selection", "Please select photos to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete {len(uuids)} photo(s) from the catalog?\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        deleted = 0
        for u in uuids:
            try:
                if self.catalogDb.delete_photo(u):
                    deleted += 1
            except Exception:
                pass
        
        QMessageBox.information(self, "Deleted", f"Successfully deleted {deleted} photo(s) from catalog.")
        self._switchView("all_photos")

    def _deleteAlbumFromView(self, album_name: str):
        """Delete an album from the album view, keeping all photos in catalog."""
        reply = QMessageBox.question(
            self,
            "Confirm Album Deletion",
            f"Are you sure you want to delete the album '{album_name}'?\n\n"
            "Note: This will only delete the album. All photos will remain in the catalog.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.catalogDb.delete_album(album_name)
                if success:
                    QMessageBox.information(self, "Success",
                                          f"Album '{album_name}' deleted successfully!")
                    # Return to albums view after deletion
                    self._switchView("albums")
                else:
                    QMessageBox.warning(self, "Error",
                                      "Failed to delete album.")
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to delete album:\n{str(e)}")

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
            photos = self.catalogDb.get_favorite_photos()
            for p in photos:
                try:
                    p['albums'] = self.catalogDb.get_photo_albums(p.get('file_uuid', ''))
                except Exception:
                    p['albums'] = []
        except Exception:
            photos = []
        grid = PhotoGridView(photos, "No favorites yet. Open a photo and click 'Add to Favorites'.", self)
        grid.photoClicked.connect(self._onPhotoCardClicked)
        grid.deleteRequested.connect(self._onPhotoDeleteRequested)
        self.contentLayout.addWidget(grid)
        self.contentLayout.addStretch()

    def _showTagsView(self):
        """Display list of tags using TagsView and wire actions for tag clicks."""
        # Fetch tags from DB
        try:
            tags_data = self.catalogDb.get_all_tags()
            # Extract tag names from dictionaries
            tags = [tag.get('name', tag) if isinstance(tag, dict) else tag for tag in tags_data]
        except Exception:
            tags = []

        view = TagsView(tags, self)
        self.contentLayout.addWidget(view)

        def onTagClicked(tag_name: str):
            """Handle tag click - show edit/delete dialog."""
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Edit Tag: {tag_name}")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # Tag name input
            nameLayout = QHBoxLayout()
            nameLayout.addWidget(QLabel("Tag Name:"))
            nameInput = QLineEdit()
            nameInput.setText(tag_name)
            nameInput.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #D6CFAA;
                    border-radius: 4px;
                    font-size: 11pt;
                }
            """)
            nameLayout.addWidget(nameInput)
            layout.addLayout(nameLayout)
            
            # Buttons
            buttonLayout = QHBoxLayout()
            buttonLayout.addStretch()
            
            deleteBtn = QPushButton("Delete Tag")
            deleteBtn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            deleteBtn.clicked.connect(lambda: self._deleteTagFromDialog(dialog, tag_name))
            buttonLayout.addWidget(deleteBtn)
            
            cancelBtn = QPushButton("Cancel")
            cancelBtn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #666;
                    border: 1px solid #D6CFAA;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #F0EEDC;
                }
            """)
            cancelBtn.clicked.connect(dialog.reject)
            buttonLayout.addWidget(cancelBtn)
            
            saveBtn = QPushButton("Save")
            saveBtn.setStyleSheet("""
                QPushButton {
                    background-color: #4a5cb8;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #3a4ca8;
                }
            """)
            saveBtn.clicked.connect(lambda: self._saveTagFromDialog(dialog, tag_name, nameInput.text().strip()))
            buttonLayout.addWidget(saveBtn)
            
            layout.addLayout(buttonLayout)
            
            dialog.exec()

        view.tagClicked.connect(onTagClicked)

    def _onCreateTagFromTopBar(self):
        """Handle create tag button click from top bar."""
        text, ok = QInputDialog.getText(self, "Create Tag", "Tag name:")
        if ok:
            tag = text.strip()
            if tag:
                try:
                    self.catalogDb.create_tag(tag)
                    QMessageBox.information(self, "Success", f"Tag '{tag}' created successfully!")
                    self._switchView("tags")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create tag:\n{str(e)}")

    def _saveTagFromDialog(self, dialog, old_name: str, new_name: str):
        """Save tag name change."""
        if not new_name:
            QMessageBox.warning(self, "Empty Name", "Tag name cannot be empty.")
            return
        
        if new_name == old_name:
            dialog.accept()
            return
        
        try:
            # Update tag name in database
            # Note: This assumes you have an update_tag method. If not, we'll delete and recreate
            # For now, let's use a simple approach: delete old and create new
            # But first check if new name already exists
            existing_tags = [tag.get('name', tag) if isinstance(tag, dict) else tag 
                           for tag in self.catalogDb.get_all_tags()]
            if new_name in existing_tags:
                QMessageBox.warning(self, "Duplicate", f"Tag '{new_name}' already exists.")
                return
            
            # Get all photos with this tag
            photos_with_tag = self.catalogDb.search_photos_by_tags([old_name])
            
            # Delete old tag
            self.catalogDb.delete_tag(old_name)
            
            # Create new tag
            self.catalogDb.create_tag(new_name)
            
            # Re-add tag to photos
            for photo in photos_with_tag:
                file_uuid = photo.get('file_uuid', '')
                if file_uuid:
                    # Get current tags
                    current_tags = photo.get('tags', '').split(',')
                    current_tags = [t.strip() for t in current_tags if t.strip() and t.strip() != old_name]
                    current_tags.append(new_name)
                    # Update photo tags
                    self.catalogDb.update_photo_tags(file_uuid, ','.join(current_tags))
            
            QMessageBox.information(self, "Success", f"Tag renamed from '{old_name}' to '{new_name}'!")
            dialog.accept()
            self._switchView("tags")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update tag:\n{str(e)}")

    def _deleteTagFromDialog(self, dialog, tag_name: str):
        """Delete tag from dialog."""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the tag '{tag_name}'?\n\n"
            "This will remove it from all photos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.catalogDb.delete_tag(tag_name)
                QMessageBox.information(self, "Success", f"Tag '{tag_name}' deleted successfully!")
                dialog.accept()
                self._switchView("tags")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete tag:\n{str(e)}")

    # --- Interactive bulk import helpers ---
    def _startInteractiveBulkImport(self, files: list[str]):
        """Initialize state for non-blocking interactive bulk import."""
        if not files:
            QMessageBox.information(self, "Import", "No files to import.")
            return
        self._bulk_queue = list(files)
        self._bulk_total = len(files)
        self._bulk_imported = 0
        self._bulk_skipped = 0
        # Persistent progress dialog
        self._bulk_progress = QProgressDialog("Importing photos...", "Cancel", 0, self._bulk_total, self)
        # Make the progress dialog non-modal so the per-file ImportDialog can receive focus
        self._bulk_progress.setWindowModality(Qt.WindowModality.NonModal)
        self._bulk_progress.setValue(0)
        # Start processing
        QTimer.singleShot(0, self._processNextInteractiveImport)

    def _processNextInteractiveImport(self):
        """Process the next file in the interactive import queue."""
        if not getattr(self, '_bulk_queue', None):
            # Finished
            try:
                self._bulk_progress.close()
            except Exception:
                pass
            QMessageBox.information(self, "Import Complete", f"Imported: {self._bulk_imported} photo(s)\nSkipped: {self._bulk_skipped}")
            if getattr(self, 'currentView', None) == 'all_photos':
                self._switchView('all_photos')
            return

        if self._bulk_progress.wasCanceled():
            # Stop the queue
            self._bulk_queue = []
            self._bulk_progress.close()
            QMessageBox.information(self, "Import Cancelled", f"Imported: {self._bulk_imported} photo(s)\nSkipped: {self._bulk_skipped}")
            return

        filePath = self._bulk_queue.pop(0)
        currentIndex = self._bulk_imported + self._bulk_skipped + 1
        self._bulk_progress.setLabelText(f"Importing {currentIndex} of {self._bulk_total}: {os.path.basename(filePath)}")
        self._bulk_progress.setValue(currentIndex - 1)

        # Show ImportDialog non-blocking: we show it and connect to its finished signal
        dialog = ImportDialog(self, filePath, [a.get('name') for a in self.catalogDb.get_all_albums()])
        # When dialog is finished, handle result
        def on_finished(result):
            try:
                if result == QDialog.DialogCode.Accepted:
                    album = dialog.selectedAlbum()
                    tags = dialog.tags()
                    description = dialog.description()
                    try:
                        status = self.photoImporter.import_photo(Path(filePath), album=album, tags=tags, description=description)
                        if status == self.photoImporter.SUCCESS:
                            self._bulk_imported += 1
                        else:
                            self._bulk_skipped += 1
                    except Exception:
                        self._bulk_skipped += 1
                else:
                    # Treat rejection as skip/stop: here we'll stop the entire batch
                    # To allow skipping a single file while continuing, change this logic
                    self._bulk_queue = []
                # Continue to next file
                QTimer.singleShot(0, self._processNextInteractiveImport)
            finally:
                try:
                    dialog.deleteLater()
                except Exception:
                    pass

        dialog.finished.connect(on_finished)
        dialog.show()

    def _onSearchChanged(self, text):
        """Handle search input changes."""
        # TODO: Implement live search filtering
        pass

    def _loadUploadAlbums(self):
        """Load albums into upload dropdown."""
        try:
            albums = [a.get('name') for a in self.catalogDb.get_all_albums()]
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
            status = self.photoImporter.import_photo(Path(filePath), album=album, tags=tags, description=description)
            if status == self.photoImporter.SUCCESS:
                QMessageBox.information(self, "Success", "Photo imported successfully!")
                self.uploadFileInput.clear()
                self.uploadAlbumCombo.setCurrentIndex(0)
                self.uploadNewAlbumInput.clear()
                self.uploadNewAlbumInput.setVisible(False)
                self.uploadTagsInput.clear()
                self.uploadDescInput.clear()
                self._loadUploadAlbums()
            elif status == self.photoImporter.DUPLICATE:
                QMessageBox.warning(self, "Duplicate", "This photo is already in the catalog.")
            else:
                QMessageBox.warning(self, "Import Skipped", "Photo could not be imported (copy error or unsupported format).")
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
            albums = [a.get('name') for a in self.catalogDb.get_all_albums()]
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
            status = self.photoImporter.import_photo(Path(filePath), album=album, tags=tags, description=description)
            if status == self.photoImporter.SUCCESS:
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
            elif status == self.photoImporter.DUPLICATE:
                QMessageBox.warning(self, "Duplicate",
                                  "This photo is already in the catalog.")
            else:
                QMessageBox.warning(self, "Import Skipped", "Photo could not be imported (copy error or unsupported format).")
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
                try:
                    status = self.photoImporter.import_photo(Path(filePath), album="", tags=[], description="")
                    if status == self.photoImporter.SUCCESS:
                        imported += 1
                        self.scanResultText.append(f"✓ Imported: {os.path.basename(filePath)}")
                    elif status == self.photoImporter.DUPLICATE:
                        skipped += 1
                        self.scanResultText.append(f"⊗ Skipped (duplicate): {os.path.basename(filePath)}")
                    else:
                        skipped += 1
                        self.scanResultText.append(f"⊗ Skipped (error/unsupported): {os.path.basename(filePath)}")
                except Exception:
                    skipped += 1
                    self.scanResultText.append(f"⊗ Skipped (exception): {os.path.basename(filePath)}")

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
            photos = self.catalogDb.get_all_photos()
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
            photos = self.catalogDb.get_all_photos()
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
                photos = self.catalogDb.get_all_photos()
                for photo in photos:
                    if photo['name'] == photoName:
                        success = self.catalogDb.delete_photo(photo['file_uuid'])
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
            albums = [a.get('name') for a in self.catalogDb.get_all_albums()]
            self.albumsList.clear()

            if not albums:
                self.albumsList.addItem("No albums created.")
                return

            for album in albums:
                # Get count of photos in album
                photos = self.catalogDb.get_album_photos(album)
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
            photos = self.catalogDb.get_album_photos(albumName)
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
                self.catalogDb.update_album(oldName, newName)
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
        
        reply = QMessageBox.question(
            self,
            "Confirm Album Deletion",
            f"Are you sure you want to delete the album '{albumName}'?\n\n"
            "Note: This will only delete the album. All photos will remain in the catalog.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.catalogDb.delete_album(albumName)
                if success:
                    QMessageBox.information(self, "Success",
                                          f"Album '{albumName}' deleted successfully!")
                    self._refreshAlbumsList()
                    self._loadAlbums()
                else:
                    QMessageBox.warning(self, "Error",
                                      "Failed to delete album.")
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to delete album:\n{str(e)}")

    def _deleteAlbumFromAlbumsView(self, album_name: str):
        """Delete an album from the albums list view, keeping all photos in catalog."""
        reply = QMessageBox.question(
            self,
            "Confirm Album Deletion",
            f"Are you sure you want to delete the album '{album_name}'?\n\n"
            "Note: This will only delete the album. All photos will remain in the catalog.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.catalogDb.delete_album(album_name)
                if success:
                    QMessageBox.information(self, "Success",
                                          f"Album '{album_name}' deleted successfully!")
                    # Refresh the albums view
                    self._switchView("albums")
                else:
                    QMessageBox.warning(self, "Error",
                                      "Failed to delete album.")
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to delete album:\n{str(e)}")


