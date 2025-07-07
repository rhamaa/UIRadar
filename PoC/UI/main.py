# main.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout
)

# Impor semua kelas widget kustom Anda
from widgets.ppi_display import PPIDesktopWidget
from widgets.fft_display import FFTDesktopWidget
from widgets.file import FileExplorerWidget
from widgets.Sinewave import SinewaveWidget
from widgets.controller import ControllerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced UI")

        # Widget pusat dan layout utama
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        # Buat instance dari semua widget
        ppi_desktop = PPIDesktopWidget()
        fft_desktop = FFTDesktopWidget()
        file_explorer = FileExplorerWidget()
        sinewave = SinewaveWidget()
        controller = ControllerWidget()

        # Atur tata letak sesuai wireframe menggunakan grid
        # addWidget(widget, row, column, rowSpan, columnSpan)
        
        # Kolom Kiri
        layout.addWidget(ppi_desktop,   0, 0, 2, 1) # Memakan 2 baris, 1 kolom
        layout.addWidget(fft_desktop,   2, 0, 1, 1)

        # Kolom Kanan
        layout.addWidget(file_explorer, 0, 1, 1, 1)
        layout.addWidget(sinewave,      1, 1, 1, 1)
        layout.addWidget(controller,    2, 1, 1, 1)

        # Atur rasio ukuran kolom dan baris (opsional, untuk penyesuaian)
        layout.setColumnStretch(0, 3) # Kolom 0 (kiri) 3x lebih lebar dari kolom 1
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen() # Tampilkan dalam mode fullscreen
    sys.exit(app.exec())