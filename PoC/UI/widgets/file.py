# UI/widgets/file.py

from .base_widget import BaseWidget

class FileExplorerWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__("File Explorer", parent)
        # TODO: Tambahkan komponen spesifik untuk File Explorer di sini