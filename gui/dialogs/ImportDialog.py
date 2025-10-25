"""
ImportDialog Component

Dialog to collect metadata for importing a single photo: album selection/creation,
tags, and description.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QComboBox,
    QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt
import os


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

        self._buildUI()

    def _buildUI(self):
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
