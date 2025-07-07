# UI/widgets/fft_display.py

from .base_widget import BaseWidget

class FFTDesktopWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__("FFT Desktop", parent)
        # TODO: Tambahkan komponen spesifik untuk FFT di sini