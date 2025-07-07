# UI/widgets/Sinewave.py

from .base_widget import BaseWidget
from PySide6.QtCore import QThread, Signal, QObject, Qt
from PySide6.QtWidgets import QPushButton, QLabel, QVBoxLayout

class Worker(QObject):
    """
    Worker yang berjalan di thread terpisah untuk melakukan counting.
    """
    # Signal untuk mengirim angka baru ke thread utama
    new_count = Signal(int)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True

    def run(self):
        """Tugas counting tak terhingga."""
        count = 0
        while self._is_running:
            # Kirim sinyal berisi angka saat ini
            self.new_count.emit(count)
            count += 1
        # Kirim sinyal selesai setelah loop berhenti
        self.finished.emit()

    def stop(self):
        """Mengubah flag untuk menghentikan loop di method run()."""
        self._is_running = False


class SinewaveWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__("Sinewave", parent)

        # Gunakan layout yang sudah ada dari BaseWidget
        layout = self.layout()

        # Atur ulang label judul
        self.label.setText("High Speed Counter")
        
        # Buat label untuk menampilkan angka counting
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("color: #00ff00; font-size: 28pt; font-weight: bold;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Buat tombol Start dan Stop
        self.start_button = QPushButton("Start Counting")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False) # Awalnya nonaktif

        # Hubungkan tombol ke fungsinya
        self.start_button.clicked.connect(self.run_task)
        self.stop_button.clicked.connect(self.stop_task)

        # Tambahkan komponen baru ke layout
        layout.addWidget(self.count_label)
        layout.addStretch()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

    def run_task(self):
        """Menginisialisasi dan menjalankan worker di thread baru."""
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        # Hubungkan sinyal dari worker ke slot di widget
        self.thread.started.connect(self.worker.run)
        self.worker.new_count.connect(self.update_count)
        
        # Logika untuk membersihkan thread setelah selesai
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.reset_buttons)

        # Mulai thread
        self.thread.start()

        # Atur state tombol
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_task(self):
        """Memberi sinyal pada worker untuk berhenti."""
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.stop_button.setText("Stopping...")

    def update_count(self, count):
        """Slot untuk mengupdate label angka (aman dari thread lain)."""
        self.count_label.setText(str(count))

    def reset_buttons(self):
        """Mengembalikan state tombol seperti semula."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stop")