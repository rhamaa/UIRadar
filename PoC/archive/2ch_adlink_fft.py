import sys
import numpy as np
import serial
import time
import threading
import queue

# Import PySide6 components
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QIntValidator # Import QIntValidator

# Import Matplotlib components for embedding
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# --- Konfigurasi Aplikasi (Default Values) ---
# Ini adalah nilai default awal, akan diubah oleh input pengguna
DEFAULT_SERIAL_PORT_RECEIVER = 'COM2'  # Port yang akan dibaca oleh osiloskop ini
DEFAULT_BAUD_RATE = 115200             # Kecepatan baud (harus sama dengan pengirim)
DEFAULT_NUM_SAMPLES_PER_ACQUISITION = 16384 # TOTAL sampel default (misal: 8192 CH0 + 8192 CH2)
DEFAULT_ADC_BITS = 16                  # Resolusi ADC dalam bit
DEFAULT_VOLTAGE_RANGE_V = (-5, 5)      # Rentang tegangan input (min_V, max_V)
DEFAULT_SAMPLING_RATE_HZ = 200000      # Laju sampling ADC dalam Hertz (harus sama dengan pengirim)

# --- Thread Penerima Data Serial ---
class SerialReceiverThread(QThread):
    data_received = Signal(np.ndarray) # Sinyal untuk mengirim data yang diterima ke thread utama
    error_occurred = Signal(str)       # Sinyal untuk melaporkan error

    def __init__(self, port_name, baud, num_samples, adc_bits):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud
        self.num_samples = num_samples # Ini adalah total sampel yang diharapkan
        self.adc_bits = adc_bits
        self.running = True
        self.ser = None # Inisialisasi serial port di sini

    def run(self):
        bytes_per_sample = self.adc_bits // 8
        expected_bytes_per_acquisition = self.num_samples * bytes_per_sample

        try:
            self.ser = serial.Serial(self.port_name, self.baud_rate, timeout=1) # Timeout untuk read
            print(f"[SERIAL THREAD] Serial port {self.port_name} berhasil dibuka.")
            self.ser.flushInput() # Bersihkan buffer input serial

            while self.running:
                received_bytes = self.ser.read(expected_bytes_per_acquisition)

                if len(received_bytes) == expected_bytes_per_acquisition:
                    # Data diterima sebagai array interleaved
                    received_digital_data = np.frombuffer(received_bytes, dtype=np.int16)
                    self.data_received.emit(received_digital_data) # Kirim data melalui sinyal
                elif len(received_bytes) > 0:
                    print(f"[SERIAL THREAD] Data diterima tidak lengkap ({len(received_bytes)} byte).")
                
                self.msleep(1) # Tidur singkat untuk menghindari 100% CPU usage

        except serial.SerialException as e:
            self.error_occurred.emit(f"Error serial port: {e}\nPastikan {self.port_name} tersedia dan tidak digunakan.")
        except Exception as e:
            self.error_occurred.emit(f"Terjadi kesalahan tak terduga di thread serial: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print(f"[SERIAL THREAD] Serial port {self.port_name} ditutup.")

    def stop(self):
        self.running = False
        self.wait() # Tunggu thread selesai

class OscilloscopeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualisasi FFT Realtime (Membaca COM1)")
        self.setGeometry(100, 100, 900, 600) # Ukuran jendela disesuaikan untuk satu plot

        # --- Konfigurasi ADC (Konstan, harus cocok dengan pengirim) ---
        self.ADC_BITS = DEFAULT_ADC_BITS
        self.SAMPLING_RATE_HZ = DEFAULT_SAMPLING_RATE_HZ
        self.VOLTAGE_RANGE_V = DEFAULT_VOLTAGE_RANGE_V
        
        # SAMPLES_PER_CHANNEL akan dihitung berdasarkan input NUM_SAMPLES_PER_ACQUISITION
        self.num_samples_per_acquisition = DEFAULT_NUM_SAMPLES_PER_ACQUISITION 
        self.samples_per_channel = self.num_samples_per_acquisition // 2

        self.init_ui()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Aplikasi siap. Tekan 'Mulai Visualisasi FFT' untuk memulai.")

        # Inisialisasi QTimer untuk update plot Matplotlib
        self.plot_update_timer = QTimer(self)
        self.plot_update_timer.timeout.connect(self.update_fft_plot) # Mengubah koneksi ke update_fft_plot
        self.plot_update_interval_ms = 50 # Update plot setiap 50ms (20 FPS)

        self.serial_thread = None # Akan diinisialisasi saat memulai penerimaan

        # Faktor skala untuk mengkonversi nilai digital ADC ke tegangan
        v_min, v_max = self.VOLTAGE_RANGE_V
        adc_max_digital = (2**(self.ADC_BITS - 1)) - 1
        self.digital_to_volt_scale = v_max / adc_max_digital 

        # Inisialisasi data plot awal untuk Channel 0 dan Channel 2
        self.current_adc_data_ch0 = np.zeros(self.samples_per_channel, dtype=np.int16)
        self.current_adc_data_ch2 = np.zeros(self.samples_per_channel, dtype=np.int16)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Bagian Kontrol ---
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Mulai Visualisasi FFT")
        self.start_button.clicked.connect(self.start_fft_visualizer)
        self.stop_button = QPushButton("Hentikan Visualisasi FFT")
        self.stop_button.clicked.connect(self.stop_fft_visualizer)
        self.stop_button.setEnabled(False) # Awalnya dinonaktifkan

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        
        # Input untuk Jumlah Sampel Per Akuisisi (Total)
        control_layout.addStretch(1)
        control_layout.addWidget(QLabel("Total Sampel (per akuisisi):"))
        self.total_samples_input = QLineEdit(str(DEFAULT_NUM_SAMPLES_PER_ACQUISITION))
        self.total_samples_input.setValidator(QIntValidator(2, 200000)) # Min 2 (1 per channel), Max 200k
        self.total_samples_input.textChanged.connect(self.update_sample_parameters_ui)
        control_layout.addWidget(self.total_samples_input)

        main_layout.addLayout(control_layout)

        # --- Panel Visualisasi Matplotlib ---
        visualization_panel_layout = QVBoxLayout()
        visualization_panel_layout.addWidget(QLabel("<h2>Tampilan FFT Magnitude (Channel 0 & 2)</h2>")) # Judul diubah

        # Buat figure Matplotlib dengan HANYA 1 subplot untuk FFT
        self.fig, self.ax_fft = plt.subplots(1, 1, figsize=(10, 6)) # Hanya satu subplot untuk FFT
        self.canvas = FigureCanvas(self.fig) # Widget untuk menampilkan figure Matplotlib
        visualization_panel_layout.addWidget(self.canvas)

        # Tambahkan toolbar navigasi (opsional, tapi berguna)
        self.toolbar = NavigationToolbar(self.canvas, self)
        visualization_panel_layout.addWidget(self.toolbar)

        # Inisialisasi plot FFT
        # x_freq akan diinisialisasi di update_sample_parameters_ui
        self.update_sample_parameters_ui() # PENTING: Panggil di sini sebelum plot lines dibuat
        
        # Menambahkan dua plot FFT, satu untuk CH0 dan satu untuk CH2
        self.line_fft_ch0, = self.ax_fft.plot(self.x_freq, np.zeros(self.samples_per_channel // 2), color='blue', label='FFT Magnitude (CH0)')
        self.line_fft_ch2, = self.ax_fft.plot(self.x_freq, np.zeros(self.samples_per_channel // 2), color='red', label='FFT Magnitude (CH2)') # Plot untuk CH2

        # Konfigurasi plot FFT (Domain Frekuensi)
        self.ax_fft.set_title("FFT Magnitude (Channel 0 & Channel 2)") # Judul diubah
        self.ax_fft.set_xlabel("Frekuensi (Hz)")
        self.ax_fft.set_ylabel("Magnitude")
        self.ax_fft.set_xlim(0, self.SAMPLING_RATE_HZ / 2) # Batas frekuensi hingga Nyquist
        self.ax_fft.set_ylim(0, 1) # Skala awal, akan disesuaikan secara dinamis
        self.ax_fft.grid(True)
        self.ax_fft.legend(loc='upper right')

        self.fig.tight_layout() # Sesuaikan layout

        main_layout.addLayout(visualization_panel_layout)
        
    def update_sample_parameters_ui(self):
        """
        Memperbarui parameter terkait jumlah sampel di UI dan plot.
        Dipanggil saat input jumlah sampel berubah.
        """
        try:
            new_num_samples_total = int(self.total_samples_input.text())
            if new_num_samples_total < 2 or new_num_samples_total % 2 != 0:
                raise ValueError("Jumlah sampel total harus genap dan minimal 2.")
            
            self.num_samples_per_acquisition = new_num_samples_total
            self.samples_per_channel = self.num_samples_per_acquisition // 2

            # Perbarui x_freq untuk plot FFT
            self.x_freq = np.fft.fftfreq(self.samples_per_channel, d=1.0/self.SAMPLING_RATE_HZ)[:self.samples_per_channel // 2]
            
            if hasattr(self, 'line_fft_ch0'): # Cek apakah plot lines sudah diinisialisasi
                self.line_fft_ch0.set_xdata(self.x_freq)
                self.line_fft_ch2.set_xdata(self.x_freq) # Perbarui x_data untuk CH2
                self.ax_fft.set_xlim(0, self.SAMPLING_RATE_HZ / 2) # Pastikan batas FFT sesuai
                self.ax_fft.set_ylim(0, 1) # Reset Y limit FFT

            self.canvas.draw_idle() # Gambar ulang kanvas

            # Reset data plot ke nol saat jumlah sampel berubah
            self.current_adc_data_ch0 = np.zeros(self.samples_per_channel, dtype=np.int16)
            self.current_adc_data_ch2 = np.zeros(self.samples_per_channel, dtype=np.int16) # Reset data CH2
            if hasattr(self, 'line_fft_ch0'): # Cek lagi sebelum set_ydata
                self.line_fft_ch0.set_ydata(np.zeros(self.samples_per_channel // 2))
                self.line_fft_ch2.set_ydata(np.zeros(self.samples_per_channel // 2)) # Reset data CH2
                self.canvas.draw_idle()

        except ValueError as e:
            self.status_bar.showMessage(f"Input sampel tidak valid: {e}", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Kesalahan saat memperbarui parameter sampel: {e}", 3000)

    def start_fft_visualizer(self):
        try:
            # Ambil jumlah sampel terbaru dari input field
            current_num_samples = int(self.total_samples_input.text())
            if current_num_samples < 2 or current_num_samples % 2 != 0:
                raise ValueError("Jumlah sampel total harus genap dan minimal 2.")

            # Hentikan thread sebelumnya jika ada
            if self.serial_thread and self.serial_thread.isRunning():
                self.serial_thread.stop()
                self.serial_thread.wait()

            # Mulai thread penerima serial baru dengan jumlah sampel yang diperbarui
            self.serial_thread = SerialReceiverThread(
                DEFAULT_SERIAL_PORT_RECEIVER, DEFAULT_BAUD_RATE, 
                current_num_samples, self.ADC_BITS
            )
            self.serial_thread.data_received.connect(self.handle_received_data)
            self.serial_thread.error_occurred.connect(self.show_error_message)
            self.serial_thread.start()

            self.plot_update_timer.start(self.plot_update_interval_ms) # Mulai timer untuk update plot
            self.status_bar.showMessage(f"Mulai visualisasi FFT, membaca dari {DEFAULT_SERIAL_PORT_RECEIVER} dengan {current_num_samples} sampel total.")
            
            # Nonaktifkan/aktifkan tombol dan input
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.total_samples_input.setEnabled(False) # Nonaktifkan input jumlah sampel saat berjalan

        except ValueError as e:
            QMessageBox.warning(self, "Input Tidak Valid", f"Jumlah sampel tidak valid: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Terjadi Kesalahan", f"Terjadi kesalahan saat memulai visualisasi FFT: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)

    def stop_fft_visualizer(self):
        self.plot_update_timer.stop()
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop()
            self.serial_thread.wait()
        
        self.status_bar.showMessage("Visualisasi FFT dihentikan.")

        # Aktifkan/nonaktifkan tombol dan input
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.total_samples_input.setEnabled(True) # Aktifkan kembali input jumlah sampel

    def handle_received_data(self, digital_data):
        """
        Slot yang menerima data dari SerialReceiverThread.
        Data digital_data adalah array interleaved dari kedua channel.
        """
        # De-interleave data: sampel genap untuk CH0, sampel ganjil untuk CH2
        # Kita memerlukan kedua channel untuk FFT
        self.current_adc_data_ch0 = digital_data[::2]
        self.current_adc_data_ch2 = digital_data[1::2]
        
        # print(f"CH0 diterima untuk FFT: {self.current_adc_data_ch0[:5]}...") # Untuk debug
        # print(f"CH2 diterima untuk FFT: {self.current_adc_data_ch2[:5]}...") # Untuk debug

    def update_fft_plot(self):
        """
        Fungsi ini dipanggil oleh QTimer untuk memperbarui plot Matplotlib.
        """
        # Pastikan panjang data sesuai dengan yang diharapkan setelah de-interleave
        if self.current_adc_data_ch0 is None or len(self.current_adc_data_ch0) != self.samples_per_channel or \
           self.current_adc_data_ch2 is None or len(self.current_adc_data_ch2) != self.samples_per_channel:
            return # Tidak ada data atau panjang tidak sesuai

        # Konversi data digital ke tegangan untuk perhitungan FFT
        analog_voltage_data_ch0 = self.current_adc_data_ch0.astype(np.float32) * self.digital_to_volt_scale
        analog_voltage_data_ch2 = self.current_adc_data_ch2.astype(np.float32) * self.digital_to_volt_scale
        
        # --- Perhitungan dan Plot FFT (untuk Channel 0) ---
        fft_result_ch0 = np.fft.fft(analog_voltage_data_ch0)
        fft_magnitude_ch0 = np.abs(fft_result_ch0[:self.samples_per_channel // 2])
        
        # --- Perhitungan dan Plot FFT (untuk Channel 2) ---
        fft_result_ch2 = np.fft.fft(analog_voltage_data_ch2)
        fft_magnitude_ch2 = np.abs(fft_result_ch2[:self.samples_per_channel // 2])
        
        # Perbarui data plot FFT untuk kedua channel
        self.line_fft_ch0.set_ydata(fft_magnitude_ch0)
        self.line_fft_ch2.set_ydata(fft_magnitude_ch2)

        # Sesuaikan batas Y untuk FFT jika magnitude berubah drastis
        # Ambil nilai maksimum dari kedua FFT
        current_fft_max = max(fft_magnitude_ch0.max(), fft_magnitude_ch2.max())
        if current_fft_max > self.ax_fft.get_ylim()[1] * 0.9 or \
           (current_fft_max < self.ax_fft.get_ylim()[1] * 0.5 and current_fft_max > 0):
             self.ax_fft.set_ylim(0, current_fft_max * 1.2 if current_fft_max > 0 else 1)
             self.fig.canvas.draw_idle() # Panggil draw_idle jika batas sumbu berubah

        # Gambar ulang canvas Matplotlib
        self.canvas.draw()
        self.status_bar.showMessage(f"Plot FFT diperbarui. Puncak CH0: {fft_magnitude_ch0.max():.2f}, Puncak CH2: {fft_magnitude_ch2.max():.2f}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Kesalahan Serial", message)
        self.stop_fft_visualizer() # Otomatis hentikan visualisasi jika ada error serial

    def closeEvent(self, event):
        # Pastikan thread serial berhenti saat aplikasi ditutup
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop()
            self.serial_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OscilloscopeApp()
    window.show()
    sys.exit(app.exec())
