"""
TagsView Component

Displays the list of tags in a styled grid. Tags are clickable for editing/deleting.
Emits signals so the parent can handle persistence.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal


class TagsView(QWidget):
    tagClicked = pyqtSignal(str)  # Emits tag name when clicked

    def __init__(self, tags: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._tags = tags or []
        self._buildUI()

    def _buildUI(self):
        from PyQt6.QtCore import Qt

        root = QVBoxLayout(self)
        # Match the main content padding so titles and controls align across views
        root.setContentsMargins(5, 5, 30, 40)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        titleLabel = QLabel("Tags")
        titleLabel.setStyleSheet("font-size: 14pt; font-weight: 600; color: #504B38; margin-bottom: 20px;")
        root.addWidget(titleLabel)

        if not self._tags:
            # Show empty state
            emptyLabel = QLabel("No tags yet. Click 'CREATE TAG' to add one.")
            emptyLabel.setStyleSheet("color: #999; font-size: 11pt; font-style: italic; padding: 20px;")
            emptyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            root.addWidget(emptyLabel)
        else:
            tagsContainer = QWidget(self)
            grid = QGridLayout(tagsContainer)
            grid.setHorizontalSpacing(40)
            grid.setVerticalSpacing(24)
            grid.setContentsMargins(20, 10, 20, 10)

            for idx, tag in enumerate(self._tags):
                tagBtn = QPushButton(tag.upper())
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
                    QPushButton:hover {
                        background-color: #D6CFAA;
                        border-color: #3a4ca8;
                    }
                    """
                )
                # Connect click to emit the tag name
                tagBtn.clicked.connect(lambda checked, t=tag: self.tagClicked.emit(t))
                grid.addWidget(tagBtn, idx // 3, idx % 3)

            root.addWidget(tagsContainer)

        root.addStretch()
