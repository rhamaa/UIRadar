# UI/widgets/controller.py

from .base_widget import BaseWidget

class ControllerWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__("Controller", parent)
        # TODO: Tambahkan komponen spesifik untuk Controller di sini