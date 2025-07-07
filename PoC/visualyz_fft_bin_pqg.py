import sys
import os
import struct
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

# --- Konfigurasi Awal (sama seperti skrip asli) ---
FILENAME = "90khz.bin"
SAMPLE_RATE = 20_000_000  # 20 MHz

# --------------------------------------------------------------------
# BAGIAN I: Logika Pemrosesan Data (diambil dari skrip asli)
# --------------------------------------------------------------------
def process_binary_data(filename, sample_rate):
    """
    Fungsi ini membaca file binari, memprosesnya, dan mengembalikan 
    data frekuensi dan magnitudo untuk di-plot.
    Mengembalikan None jika terjadi error.
    """
    if not os.path.exists(filename):
        # Menggunakan return tuple untuk error handling yang lebih baik
        return "error", f"File '{filename}' tidak ditemukan."

    try:
        with open(filename, "rb") as f:
            data_bytes = f.read()
            if not data_bytes:
                return "error", f"File '{filename}' kosong."
            
            # Unpack data: '<' little-endian, 'H' unsigned short (2 bytes)
            num_samples = len(data_bytes) // 2
            values = np.array(struct.unpack(f"<{num_samples}H", data_bytes), dtype=np.float32)

        # Pisahkan data menjadi dua channel
        ch1 = values[::2]
        ch2 = values[1::2]

        # Pastikan kedua channel punya panjang yang sama
        min_len = min(len(ch1), len(ch2))
        ch1, ch2 = ch1[:min_len], ch2[:min_len]

        if len(ch1) == 0:
            return "error", "Tidak ada data yang valid setelah dipisahkan antar channel."

        # Hilangkan offset DC
        ch1 -= np.mean(ch1)
        ch2 -= np.mean(ch2)

        # Hitung FFT
        def compute_fft(channel, fs):
            n = len(channel)
            fft_vals = np.fft.fft(channel)
            mag = np.abs(fft_vals)[:n // 2]
            freqs = np.fft.fftfreq(n, d=1 / fs)[:n // 2]
            return freqs, mag, n

        freqs_ch1, mag_ch1, n1 = compute_fft(ch1, sample_rate)
        freqs_ch2, mag_ch2, n2 = compute_fft(ch2, sample_rate)

        # Siapkan informasi untuk judul plot
        freq_res = sample_rate / n1
        nyquist = sample_rate / 2
        
        info_title = (
            f'Spektrum FFT 2 Channel\nSample Rate: {sample_rate/1e6:.2f} MHz, '
            f'Buffer: {n1}, Resolusi: {freq_res:.1f} Hz, Nyquist: {nyquist/1e6:.2f} MHz'
        )

        return "success", (freqs_ch1, mag_ch1, freqs_ch2, mag_ch2, info_title)

    except Exception as e:
        return "error", f"Terjadi kesalahan saat memproses file: {e}"


# --------------------------------------------------------------------
# BAGIAN II: GUI dengan PySide6 dan PyQtGraph
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFT Spectrum Analyzer - PyQtGraph & PySide6")
        self.setGeometry(100, 100, 1000, 600) # x, y, width, height

        # Buat widget plot dari pyqtgraph
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        # Panggil fungsi untuk memproses dan menampilkan data
        self.load_and_plot_data()

    def load_and_plot_data(self):
        """Memuat data dari file dan menampilkannya di plot widget."""
        status, result = process_binary_data(FILENAME, SAMPLE_RATE)

        if status == "error":
            # Tampilkan pesan error jika file tidak ada atau masalah lain
            QMessageBox.critical(self, "Error", result)
            return

        # Unpack hasil yang sukses
        freqs_ch1, mag_ch1, freqs_ch2, mag_ch2, title_text = result
        
        # Konfigurasi plot (ini adalah pengganti dari perintah matplotlib)
        
        # 1. Tambahkan legend (harus ditambahkan sebelum plot dengan argumen 'name')
        self.plot_widget.addLegend()

        # 2. Plot data
        # plt.plot(freqs_ch1, mag_ch1, color='r', label='CH1 (ganjil)') ->
        self.plot_widget.plot(
            freqs_ch1, mag_ch1, 
            pen={'color': 'r', 'width': 1.5}, 
            name='CH1 (ganjil)'
        )
        
        # plt.plot(freqs_ch2, mag_ch2, color='b', label='CH2 (genap)') ->
        self.plot_widget.plot(
            freqs_ch2, mag_ch2, 
            pen={'color': 'b', 'width': 1.5}, 
            name='CH2 (genap)'
        )

        # 3. Atur judul dan label
        # plt.title(...) ->
        self.plot_widget.setTitle(title_text, size='12pt')
        # plt.xlabel(...) ->
        self.plot_widget.setLabel('bottom', 'Frequency (Hz)')
        # plt.ylabel(...) ->
        self.plot_widget.setLabel('left', 'Magnitude')

        # 4. Tampilkan grid
        # plt.grid(True) ->
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # 5. Atur batas sumbu x
        # plt.xlim(1e3, 1e5) ->
        self.plot_widget.setXRange(1e3, 1e5)
        
        # 6. (Opsional) Mengaktifkan Log Mode untuk sumbu x agar lebih jelas
        self.plot_widget.setLogMode(x=True, y=False)
        
        print("Plotting berhasil ditampilkan di window PyQtGraph.")


if __name__ == "__main__":
    # --- Membuat file dummy jika '90khz.bin' tidak ada ---
    if not os.path.exists(FILENAME):
        print(f"File '{FILENAME}' tidak ditemukan. Membuat file dummy untuk demonstrasi...")
        # Parameter untuk sinyal dummy
        sr = SAMPLE_RATE
        duration = 0.01  # 10 ms
        num_samples_total = int(sr * duration)
        t = np.linspace(0, duration, num_samples_total, endpoint=False)
        
        # Buat sinyal 90 kHz untuk CH1 dan 50 kHz untuk CH2
        signal1 = (np.sin(2 * np.pi * 90e3 * t) * 10000 + 32768).astype(np.uint16)
        signal2 = (np.sin(2 * np.pi * 50e3 * t) * 8000 + 32768).astype(np.uint16)
        
        # Interleave (gabungkan) kedua channel
        interleaved_data = np.empty((signal1.size + signal2.size,), dtype=np.uint16)
        interleaved_data[0::2] = signal1
        interleaved_data[1::2] = signal2
        
        # Tulis ke file biner
        with open(FILENAME, "wb") as f:
            f.write(interleaved_data.tobytes())
        print(f"File dummy '{FILENAME}' berhasil dibuat.")


    # --- Jalankan aplikasi PySide6 ---
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())