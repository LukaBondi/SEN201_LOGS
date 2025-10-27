"""
AlbumsView Component

Displays a vertical list of album names as buttons and emits albumSelected when clicked.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import pyqtSignal


class AlbumsView(QWidget):
    albumSelected = pyqtSignal(str)
    createAlbumRequested = pyqtSignal()
    selectPhotosRequested = pyqtSignal(str)

    def __init__(self, albums: list[str], parent=None):
        super().__init__(parent)
        self.albums = albums or []
        self._setupUI()

    def _setupUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        # Match the main content padding so titles line up with other views
        layout.setContentsMargins(5, 5, 30, 40)

        titleLabel = QLabel("Albums")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        layout.addWidget(titleLabel)
        for album in self.albums:
            row = QHBoxLayout()
            albumBtn = QPushButton(album)
            albumBtn.setStyleSheet(
                """
                QPushButton {
                    background-color: #B9B28A;
                    color: #504B38;
                    border: none;
                    border-radius: 8px;
                    font-size: 14pt;
                    font-weight: 600;
                    padding: 16px 0px;
                }
                QPushButton:hover {
                    background-color: #504B38;
                    color: #F8F3D9;
                }
                """
            )
            albumBtn.clicked.connect(lambda checked=False, a=album: self.albumSelected.emit(a))
            row.addWidget(albumBtn)
            # Add 'Select Photos' button per album
            selectBtn = QPushButton("Select Photos")
            selectBtn.setFixedWidth(120)
            selectBtn.clicked.connect(lambda checked=False, a=album: self.selectPhotosRequested.emit(a))
            row.addWidget(selectBtn)
            layout.addLayout(row)

        # Create album button at bottom
        createBtn = QPushButton("+ Create New Album")
        createBtn.setStyleSheet("font-weight: 600; background-color: #fff; color: #504B38; border: 1px solid #B9B28A; padding: 8px;")
        createBtn.clicked.connect(lambda: self.createAlbumRequested.emit())
        layout.addWidget(createBtn)
        layout.addStretch()
