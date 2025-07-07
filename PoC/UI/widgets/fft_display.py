# UI/widgets/fft_display.py

import os
import struct
import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from .base_widget import BaseWidget

class FFTDesktopWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__("FFT Spectrum Analyzer (Live)", parent)

        # --- Konfigurasi ---
        # Path ke file data, relatif terhadap lokasi eksekusi main.py
        # '..' berarti satu direktori di atas
        self.data_file_path = "../data.bin"
        self.sample_rate = 20_000_000  # 20 MHz
        self.refresh_interval_ms = 100 # Refresh setiap 100 ms (10 FPS)

        # Setup Canvas Matplotlib
        self.figure = Figure(figsize=(5, 3), facecolor='#303030')
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        # Ambil layout dari BaseWidget dan tambahkan canvas
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout(self)
            self.setLayout(layout)
        layout.addWidget(self.canvas)
        
        # Setup Timer untuk update plot secara berkala
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(self.refresh_interval_ms)

        # Lakukan plot awal saat widget dibuat
        self.update_plot()

    def update_plot(self):
        """
        Slot yang dipanggil oleh QTimer.
        Fungsi ini membaca data dan menggambar ulang plot.
        """
        # Baca data dari file
        values = self.read_data_file()

        # Hitung FFT dan gambar di canvas
        self.compute_and_plot_fft(values)

    def read_data_file(self):
        """Membaca data dari file biner. Mengembalikan array numpy atau array nol jika gagal."""
        try:
            # Periksa apakah file ada dan tidak kosong
            if not os.path.exists(self.data_file_path) or os.path.getsize(self.data_file_path) < 2:
                # Jika tidak ada atau terlalu kecil, anggap sinyalnya nol
                return np.zeros(512, dtype=np.float32) # Kembalikan array nol kecil

            with open(self.data_file_path, "rb") as f:
                data = f.read()
            
            # Unpack data: '<' little-endian, 'H' unsigned short (2 bytes)
            num_samples = len(data) // 2
            # Pastikan kita hanya unpack byte yang lengkap
            values = np.array(struct.unpack(f"<{num_samples}H", data[:num_samples*2]), dtype=np.float32)
            return values

        except (IOError, struct.error) as e:
            # Jika ada error saat membaca (misal file sedang di-lock) atau unpack
            print(f"Warning: Gagal membaca atau memproses '{self.data_file_path}'. Error: {e}")
            return np.zeros(512, dtype=np.float32) # Kembalikan array nol

    def compute_and_plot_fft(self, values):
        """Menghitung FFT dan menggambar hasilnya di canvas Matplotlib."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#383838')

        # Jika tidak ada data (hanya array nol), plot akan kosong
        if np.all(values == 0):
            ax.text(0.5, 0.5, "Menunggu Sinyal...\n(File tidak ditemukan atau kosong)",
                    ha='center', va='center', color='orange', fontsize=12)
            n_buffer = len(values)
        else:
            # Proses FFT seperti biasa
            ch1 = values[::2]
            ch2 = values[1::2]
            ch1 = ch1 - np.mean(ch1)
            ch2 = ch2 - np.mean(ch2)

            def compute_fft(channel, sample_rate):
                n = len(channel)
                if n == 0: return np.array([]), np.array([]), 0
                fft_vals = np.fft.fft(channel)
                mag = np.abs(fft_vals)[:n//2]
                freqs = np.fft.fftfreq(n, d=1/self.sample_rate)[:n//2]
                return freqs, mag, n

            freqs_ch1, mag_ch1, n1 = compute_fft(ch1, self.sample_rate)
            freqs_ch2, mag_ch2, n2 = compute_fft(ch2, self.sample_rate)

            ax.plot(freqs_ch1, mag_ch1, color='#FF5733', label='CH1')
            ax.plot(freqs_ch2, mag_ch2, color='#33CFFF', label='CH2')
            n_buffer = n1 if n1 > 0 else len(values)
        
        # Pengaturan Tampilan Plot
        freq_res = self.sample_rate / n_buffer if n_buffer > 0 else 0
        nyquist = self.sample_rate / 2
        title_text = f'SR: {self.sample_rate/1e6:.1f}MHz, Buffer: {n_buffer}, Res: {freq_res:.1f}Hz'
        
        ax.set_title(title_text, color='white', fontsize=9)
        ax.set_xlabel('Frequency (Hz)', color='white')
        ax.set_ylabel('Magnitude', color='white')
        ax.grid(True, linestyle='--', color='gray', alpha=0.6)
        ax.legend()
        ax.set_xlim(1e3, 1e5) # Batasi dari 1 kHz sampai 100 kHz
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        for spine in ax.spines.values():
            spine.set_edgecolor('gray')
        
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor('#404040')
            for text in legend.get_texts():
                text.set_color('white')

        self.figure.tight_layout()
        self.canvas.draw()