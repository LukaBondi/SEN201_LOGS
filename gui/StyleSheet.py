"""
StyleSheet.py
Author: Satwik Singh
Date: October 25, 2025

Purpose:
    Defines the visual styling for the Photo Catalog Application.
    Uses a warm, earthy color palette for a sophisticated look.
"""

# Color Palette
CREAM = "#DDD7B0"        # Lightest - backgrounds, highlights (darker beige)
LIGHT_BEIGE = "#EBE5C2"  # Light - secondary backgrounds
OLIVE_TAUPE = "#B9B28A"  # Medium - borders, accents
DARK_OLIVE = "#504B38"   # Darkest - text, primary elements


def getApplicationStyle():
    """
    Returns the complete stylesheet for the application.
    
    Returns:
        str: CSS-like stylesheet for PyQt6 widgets.
    """
    return f"""
        /* Main Window */
        QMainWindow {{
            background-color: {CREAM};
        }}
        
        /* Central Widget */
        QWidget {{
            background-color: {CREAM};
            color: {DARK_OLIVE};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 2px solid {OLIVE_TAUPE};
            background-color: {CREAM};
            border-radius: 4px;
        }}
        
        QTabBar::tab {{
            background-color: {LIGHT_BEIGE};
            color: {DARK_OLIVE};
            padding: 10px 20px;
            margin-right: 2px;
            border: 1px solid {OLIVE_TAUPE};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background-color: {CREAM};
            border-bottom: 2px solid {CREAM};
            font-weight: 600;
        }}
        
        QTabBar::tab:hover {{
            background-color: {OLIVE_TAUPE};
            color: {CREAM};
        }}
        
        /* Labels */
        QLabel {{
            color: {DARK_OLIVE};
            background-color: transparent;
        }}
        
        /* Group Boxes */
        QGroupBox {{
            background-color: {LIGHT_BEIGE};
            border: 2px solid {OLIVE_TAUPE};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 15px;
            font-weight: 600;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            color: {DARK_OLIVE};
            background-color: {OLIVE_TAUPE};
            border-radius: 3px;
            margin-left: 10px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {DARK_OLIVE};
            color: {CREAM};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            min-height: 25px;
        }}
        
        QPushButton:hover {{
            background-color: {OLIVE_TAUPE};
            color: {DARK_OLIVE};
        }}
        
        QPushButton:pressed {{
            background-color: {LIGHT_BEIGE};
            color: {DARK_OLIVE};
        }}
        
        QPushButton:disabled {{
            background-color: {LIGHT_BEIGE};
            color: {OLIVE_TAUPE};
        }}
        
        /* Line Edits */
        QLineEdit {{
            background-color: white;
            color: {DARK_OLIVE};
            border: 2px solid {OLIVE_TAUPE};
            border-radius: 4px;
            padding: 6px;
            selection-background-color: {OLIVE_TAUPE};
            selection-color: {CREAM};
        }}
        
        QLineEdit:focus {{
            border: 2px solid {DARK_OLIVE};
        }}
        
        QLineEdit:disabled {{
            background-color: {LIGHT_BEIGE};
            color: {OLIVE_TAUPE};
        }}
        
        /* Text Edits */
        QTextEdit {{
            background-color: white;
            color: {DARK_OLIVE};
            border: 2px solid {OLIVE_TAUPE};
            border-radius: 4px;
            padding: 6px;
            selection-background-color: {OLIVE_TAUPE};
            selection-color: {CREAM};
        }}
        
        QTextEdit:focus {{
            border: 2px solid {DARK_OLIVE};
        }}
        
        /* List Widgets */
        QListWidget {{
            background-color: white;
            color: {DARK_OLIVE};
            border: 2px solid {OLIVE_TAUPE};
            border-radius: 4px;
            padding: 4px;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-radius: 3px;
            margin: 2px;
        }}
        
        QListWidget::item:selected {{
            background-color: {OLIVE_TAUPE};
            color: {CREAM};
        }}
        
        QListWidget::item:hover {{
            background-color: {LIGHT_BEIGE};
        }}
        
        /* Combo Box */
        QComboBox {{
            background-color: white;
            color: {DARK_OLIVE};
            border: 2px solid {OLIVE_TAUPE};
            border-radius: 4px;
            padding: 6px;
            min-height: 25px;
        }}
        
        QComboBox:hover {{
            border: 2px solid {DARK_OLIVE};
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {DARK_OLIVE};
            margin-right: 5px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: white;
            color: {DARK_OLIVE};
            border: 2px solid {OLIVE_TAUPE};
            selection-background-color: {OLIVE_TAUPE};
            selection-color: {CREAM};
            padding: 4px;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {LIGHT_BEIGE};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {OLIVE_TAUPE};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {DARK_OLIVE};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {LIGHT_BEIGE};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {OLIVE_TAUPE};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {DARK_OLIVE};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Message Box */
        QMessageBox {{
            background-color: {CREAM};
        }}
        
        QMessageBox QLabel {{
            color: {DARK_OLIVE};
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
        }}
    """


def getTitleStyle():
    """
    Returns stylesheet for title labels.
    
    Returns:
        str: CSS for title styling.
    """
    return f"""
        font-size: 16pt;
        font-weight: bold;
        color: {DARK_OLIVE};
        padding: 10px;
        background-color: transparent;
    """


def getSubtitleStyle():
    """
    Returns stylesheet for subtitle labels.
    
    Returns:
        str: CSS for subtitle styling.
    """
    return f"""
        font-size: 12pt;
        font-weight: 600;
        color: {DARK_OLIVE};
        padding: 5px;
        background-color: transparent;
    """
