"""
UploadView Component

Centered upload UI with two large buttons: Upload File and Upload Folder.
Emits signals for button clicks so the MainWindow can handle actions.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal


class UploadView(QWidget):
    uploadFileClicked = pyqtSignal()
    uploadFolderClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setupUi()

    def _setupUi(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        # Top stretch to center vertically
        mainLayout.addStretch(1)

        centerContainer = QWidget(self)
        centerLayout = QVBoxLayout(centerContainer)
        centerLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        centerLayout.setSpacing(30)

        # Upload File button
        uploadFileBtn = QPushButton("UPLOAD FILE")
        uploadFileBtn.setFixedSize(420, 110)
        uploadFileBtn.setStyleSheet(
            """
            QPushButton {
                background-color: #B9B28A;
                color: #2d2d2d;
                border: none;
                border-radius: 12px;
                font-size: 28pt;
                font-weight: 600;
                font-family: 'Times New Roman', serif;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: #F8F3D9;
            }
            """
        )
        uploadFileBtn.clicked.connect(self.uploadFileClicked.emit)
        centerLayout.addWidget(uploadFileBtn, alignment=Qt.AlignmentFlag.AlignCenter)

        # OR label
        orLabel = QLabel("OR")
        orLabel.setStyleSheet(
            """
            font-size: 24pt;
            font-weight: 400;
            color: #2d2d2d;
            font-family: 'Times New Roman', serif;
            padding: 30px 0px;
            """
        )
        orLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        centerLayout.addWidget(orLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Upload Folder button
        uploadFolderBtn = QPushButton("UPLOAD FOLDER")
        uploadFolderBtn.setFixedSize(420, 110)
        uploadFolderBtn.setStyleSheet(
            """
            QPushButton {
                background-color: #B9B28A;
                color: #2d2d2d;
                border: none;
                border-radius: 12px;
                font-size: 28pt;
                font-weight: 600;
                font-family: 'Times New Roman', serif;
            }
            QPushButton:hover {
                background-color: #504B38;
                color: #F8F3D9;
            }
            """
        )
        uploadFolderBtn.clicked.connect(self.uploadFolderClicked.emit)
        centerLayout.addWidget(uploadFolderBtn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Middle container to main layout
        mainLayout.addWidget(centerContainer, alignment=Qt.AlignmentFlag.AlignCenter)

        # Bottom stretch
        mainLayout.addStretch(1)



