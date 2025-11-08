"""
ImportDialog Component

Dialog to collect metadata for importing a single photo: album selection/creation,
tags, and description.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QComboBox,
    QLineEdit, QDialogButtonBox, QCompleter
)
from PyQt6.QtCore import Qt
import os

class CommaSeparatedCompleter(QCompleter):
    """Completer that operates on the last comma-separated token in a QLineEdit.

    This allows autocomplete suggestions to continue working after the user types
    a comma to enter multiple tags (e.g. "nature, sun" still suggests "sunset").
    """
    def splitPath(self, path: str):  # type: ignore[override]
        # Only use the last token (after the final comma) as the completion prefix.
        last_token = path.split(',')[-1].strip()
        return [last_token]

    def pathFromIndex(self, index):  # type: ignore[override]
        # Replace just the last token with the selected completion while preserving prior tags.
        completion = super().pathFromIndex(index)
        widget = self.widget()
        if widget is None:
            return completion
        current_text = widget.text()
        parts = [p.strip() for p in current_text.split(',')]
        parts[-1] = completion.strip()
        # Reconstruct comma + space separated list.
        new_text = ', '.join([p for p in parts if p])
        return new_text


class ImportDialog(QDialog):
    def __init__(self, parent, filePath: str, albums: list[str] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Import Photo")
        self.setFixedWidth(500)
        self.setStyleSheet("background-color: #F8F3D9;")

        self._filePath = filePath
        self._albums = albums or []

        self._selectedAlbum = ""
        self._newAlbumName = ""
        self._tagsText = ""
        self._description = ""

        self._buildUi()

    def _buildUi(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # File name
        fileNameLabel = QLabel(f"File: {os.path.basename(self._filePath)}")
        fileNameLabel.setStyleSheet(
            "font-weight: 600; color: #504B38; font-size: 11pt; margin-bottom: 10px;"
        )
        layout.addWidget(fileNameLabel)

        # Album selection
        albumLayout = QHBoxLayout()
        albumLayout.setSpacing(10)
        albumLayout.addWidget(QLabel("Album:"))

        self.albumCombo = QComboBox()
        self.albumCombo.addItem("-- No Album --")
        self.albumCombo.addItem("-- Create New Album --")
        for a in self._albums:
            self.albumCombo.addItem(a)
        albumLayout.addWidget(self.albumCombo)
        layout.addLayout(albumLayout)

        # New album input
        self.newAlbumInput = QLineEdit()
        self.newAlbumInput.setPlaceholderText("Enter new album name...")
        self.newAlbumInput.setVisible(False)
        layout.addWidget(self.newAlbumInput)

        def onAlbumChanged(text):
            self.newAlbumInput.setVisible(text == "-- Create New Album --")
        self.albumCombo.currentTextChanged.connect(onAlbumChanged)

        # Tags
        tagsLayout = QHBoxLayout()
        tagsLayout.setSpacing(10)
        tagsLayout.addWidget(QLabel("Tags:"))
        self.tagsInput = QLineEdit()
        self.tagsInput.setPlaceholderText("e.g., nature, landscape, sunset")
        
        # Set up autocomplete for tags if parent has catalogDb
        try:
            if hasattr(self.parent(), 'catalogDb'):
                catalogDb = self.parent().catalogDb
                tags_data = catalogDb.get_all_tags()
                # Extract tag names from dictionaries
                all_tags = [tag.get('name', tag) if isinstance(tag, dict) else tag for tag in tags_data]
                
                if all_tags:
                    # Create completer with existing tags
                    completer = CommaSeparatedCompleter(all_tags)
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

                    self.tagsInput.setCompleter(completer)
        except Exception:
            pass  # If we can't get tags, just continue without autocomplete
        
        tagsLayout.addWidget(self.tagsInput)
        layout.addLayout(tagsLayout)

        # Description
        descLayout = QHBoxLayout()
        descLayout.setSpacing(10)
        descLayout.addWidget(QLabel("Description:"))
        self.descInput = QLineEdit()
        self.descInput.setPlaceholderText("Optional description...")
        descLayout.addWidget(self.descInput)
        layout.addLayout(descLayout)

        # Buttons
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttonBox.accepted.connect(self._onAccept)
        buttonBox.rejected.connect(self.reject)
        # Style the dialog buttons so they are visible on the light dialog background
        buttonBox.setStyleSheet(
            """
            QPushButton {
                background-color: #B9B28A;
                color: #2d2d2d;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: #F8F3D9;
            }
            """
        )
        layout.addWidget(buttonBox)

    def _onAccept(self):
        albumSelection = self.albumCombo.currentText()
        if albumSelection == "-- No Album --":
            self._selectedAlbum = ""
        elif albumSelection == "-- Create New Album --":
            self._selectedAlbum = self.newAlbumInput.text().strip()
            if not self._selectedAlbum:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Missing Album Name", "Please enter a name for the new album.")
                return
        else:
            self._selectedAlbum = albumSelection

        self._tagsText = self.tagsInput.text().strip()
        self._description = self.descInput.text().strip()
        self.accept()

    def selectedAlbum(self) -> str:
        return self._selectedAlbum

    def tags(self) -> list[str]:
        if not self._tagsText:
            return []
        return [t.strip() for t in self._tagsText.split(',') if t.strip()]

    def description(self) -> str:
        return self._description

    def filePath(self) -> str:
        return self._filePath

