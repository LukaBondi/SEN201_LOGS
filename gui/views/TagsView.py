"""
TagsView Component

Displays the list of tags in a styled grid and provides Create/Delete actions.
Emits signals so the parent can handle persistence.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal


class TagsView(QWidget):
    createTagClicked = pyqtSignal()
    deleteTagClicked = pyqtSignal()

    def __init__(self, tags: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._tags = tags or []
        self._buildUI()

    def _buildUI(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titleLabel = QLabel("Tags")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        root.addWidget(titleLabel)

        tagsContainer = QWidget(self)
        grid = QGridLayout(tagsContainer)
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(24)
        grid.setContentsMargins(20, 10, 20, 10)

        for idx, tag in enumerate(self._tags):
            tagBtn = QPushButton(tag.upper())
            tagBtn.setEnabled(False)
            tagBtn.setFixedSize(260, 56)
            tagBtn.setStyleSheet(
                """
                QPushButton {
                    background-color: #EBE5C2;
                    color: #504B38;
                    border: 2px solid #504B38;
                    border-radius: 16px;
                    font-size: 11pt;
                    font-weight: 600;
                }
                """
            )
            grid.addWidget(tagBtn, idx // 3, idx % 3)

        root.addWidget(tagsContainer)

        # Bottom actions
        actions = QWidget(self)
        actionsLayout = QHBoxLayout(actions)
        actionsLayout.setSpacing(30)
        actionsLayout.setContentsMargins(20, 20, 20, 20)

        createBtn = QPushButton("CREATE TAG")
        deleteBtn = QPushButton("DELETE TAG")
        for btn in (createBtn, deleteBtn):
            btn.setFixedSize(260, 56)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #B9B28A;
                    color: #2d2d2d;
                    border: none;
                    border-radius: 12px;
                    font-size: 12pt;
                    font-weight: 600;
                    font-family: 'Times New Roman', serif;
                }
                QPushButton:hover { background-color: #504B38; color: #F8F3D9; }
                """
            )
            actionsLayout.addWidget(btn)

        createBtn.clicked.connect(self.createTagClicked.emit)
        deleteBtn.clicked.connect(self.deleteTagClicked.emit)

        root.addWidget(actions)
