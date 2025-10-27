"""
PhotoGridView Component

A reusable grid view that arranges PhotoCard widgets in a 3-column grid.
Re-emits photoClicked and deleteRequested signals for parent wiring.
"""
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from gui.components.PhotoCard import PhotoCard


class PhotoGridView(QWidget):
    photoClicked = pyqtSignal(object)
    deleteRequested = pyqtSignal(str)

    def __init__(self, photos: list | None = None, emptyText: str | None = None, parent=None):
        super().__init__(parent)
        self._emptyText = emptyText or "No photos to display."
        self._gridWidget = QWidget(self)
        self._gridLayout = QGridLayout(self._gridWidget)
        self._gridLayout.setContentsMargins(10, 10, 10, 10)
        self._gridLayout.setHorizontalSpacing(24)
        self._gridLayout.setVerticalSpacing(24)

        self._container = QVBoxLayout(self)
        self._container.setContentsMargins(0, 0, 0, 0)
        self._container.setSpacing(0)

        self._container.addWidget(self._gridWidget)
        self._placeholder = None

        if photos is not None:
            self.setPhotos(photos)
        self._select_mode = False
        self._cards = []

    def clear(self):
        while self._gridLayout.count():
            item = self._gridLayout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        if self._placeholder is not None:
            self._placeholder.setParent(None)
            self._placeholder = None
        self._cards = []

    def setPhotos(self, photos: list):
        self.clear()
        if not photos:
            # Show placeholder centered
            self._placeholder = QLabel(self._emptyText)
            self._placeholder.setStyleSheet("color: #B9B28A; font-size: 12pt; padding: 40px;")
            self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._container.insertWidget(0, self._placeholder)
            return

        row, col = 0, 0
        for photo in photos:
            card = PhotoCard(photo, self)
            card.photoClicked.connect(self.photoClicked.emit)
            card.deleteRequested.connect(self.deleteRequested.emit)
            self._gridLayout.addWidget(card, row, col)
            self._cards.append(card)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def enableSelectionMode(self, enable: bool = True):
        """Enable or disable selection mode on cards."""
        self._select_mode = enable
        for card in getattr(self, '_cards', []):
            card.is_selectable = enable
            if not enable:
                # clear selection visual
                if card.is_selected:
                    card.is_selected = False
                    card.setStyleSheet(card.styleSheet().replace(getattr(card, '_selected_style', ''), ''))

    def getSelectedFilePaths(self) -> list:
        """Return file paths for currently selected cards."""
        selected = []
        for card in getattr(self, '_cards', []):
            if getattr(card, 'is_selected', False):
                selected.append(getattr(card, 'file_path', None))
        return [p for p in selected if p]
