# UI/widgets/base_widget.py

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

class BaseWidget(QWidget):
    """
    Widget dasar dengan gaya umum (background gelap dan judul)
    untuk digunakan oleh semua widget lainnya.
    """
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        # Atur background menjadi gelap
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(135, 135, 135))
        self.setPalette(palette)

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Judul Widget
        self.label = QLabel(title)
        self.label.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.label)
        self.setLayout(layout)