"""
AlbumsView Component

Displays a vertical list of album names as buttons and emits albumSelected when clicked.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal


class AlbumsView(QWidget):
    albumSelected = pyqtSignal(str)

    def __init__(self, albums: list[str], parent=None):
        super().__init__(parent)
        self.albums = albums or []
        self._setupUI()

    def _setupUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 20, 40, 20)

        titleLabel = QLabel("Albums")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        layout.addWidget(titleLabel)

        for album in self.albums:
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
            layout.addWidget(albumBtn)

        layout.addStretch()
