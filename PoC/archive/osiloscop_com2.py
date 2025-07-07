import sys
import numpy as np
import serial
import time
import threading
import queue

# Import PySide6 components
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal

# Import Matplotlib components for embedding
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# --- Konfigurasi Aplikasi ---
# HARUS SESUAI dengan konfigurasi pengirim data ADC Anda (aplikasi PySide6 generator sinyal)
SERIAL_PORT_RECEIVER = 'COM2'  # Port yang akan dibaca oleh osiloskop ini
BAUD_RATE = 115200             # Kecepatan baud (harus sama dengan pengirim)
NUM_SAMPLES_PER_ACQUISITION = 8192 # Jumlah sampel yang diharapkan per paket
ADC_BITS = 16                  # Resolusi ADC dalam bit
VOLTAGE_RANGE_V = (-5, 5)      # Rentang tegangan input (min_V, max_V)
SAMPLING_RATE_HZ = 200000      # Laju sampling ADC dalam Hertz (harus sama dengan pengirim)

# --- Thread Penerima Data Serial ---
# Menggunakan QThread untuk integrasi yang lebih baik dengan loop event Qt
class SerialReceiverThread(QThread):
    data_received = Signal(np.ndarray) # Sinyal untuk mengirim data yang diterima ke thread utama
    error_occurred = Signal(str)       # Sinyal untuk melaporkan error

    def __init__(self, port_name, baud, num_samples, adc_bits):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud
        self.num_samples = num_samples
        self.adc_bits = adc_bits
        self.running = True

    def run(self):
        bytes_per_sample = self.adc_bits // 8
        expected_bytes_per_acquisition = self.num_samples * bytes_per_sample

        ser = None
        try:
            ser = serial.Serial(self.port_name, self.baud_rate, timeout=1) # Timeout untuk read
            print(f"[SERIAL THREAD] Serial port {self.port_name} berhasil dibuka.")
            ser.flushInput() # Bersihkan buffer input serial

            while self.running:
                received_bytes = ser.read(expected_bytes_per_acquisition)

                if len(received_bytes) == expected_bytes_per_acquisition:
                    received_digital_data = np.frombuffer(received_bytes, dtype=np.int16)
                    self.data_received.emit(received_digital_data) # Kirim data melalui sinyal
                elif len(received_bytes) > 0:
                    print(f"[SERIAL THREAD] Data diterima tidak lengkap ({len(received_bytes)} byte).")
                
                # Memberi kesempatan QThread untuk memproses event dan sinyal stop
                self.msleep(1) # Tidur singkat untuk menghindari 100% CPU usage

        except serial.SerialException as e:
            self.error_occurred.emit(f"Error serial port: {e}\nPastikan {self.port_name} tersedia dan tidak digunakan.")
        except Exception as e:
            self.error_occurred.emit(f"Terjadi kesalahan tak terduga di thread serial: {e}")
        finally:
            if ser and ser.is_open:
                ser.close()
                print(f"[SERIAL THREAD] Serial port {self.port_name} ditutup.")

    def stop(self):
        self.running = False
        self.wait() # Tunggu thread selesai

class OscilloscopeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiloskop Realtime (Membaca COM2)")
        self.setGeometry(100, 100, 1000, 600) # Ukuran jendela

        # --- Konfigurasi ADC (Konstan, harus cocok dengan pengirim) ---
        self.ADC_BITS = ADC_BITS
        self.SAMPLING_RATE_HZ = SAMPLING_RATE_HZ
        self.VOLTAGE_RANGE_V = VOLTAGE_RANGE_V
        self.NUM_SAMPLES_PER_ACQUISITION = NUM_SAMPLES_PER_ACQUISITION

        self.init_ui()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Aplikasi siap. Tekan 'Mulai Osiloskop' untuk memulai.")

        # Inisialisasi QTimer untuk update plot Matplotlib
        self.plot_update_timer = QTimer(self)
        self.plot_update_timer.timeout.connect(self.update_oscilloscope_plot)
        self.plot_update_interval_ms = 50 # Update plot setiap 50ms (20 FPS)

        self.serial_thread = None # Akan diinisialisasi saat memulai penerimaan

        # Faktor skala untuk mengkonversi nilai digital ADC ke tegangan
        v_min, v_max = self.VOLTAGE_RANGE_V
        adc_max_digital = (2**(self.ADC_BITS - 1)) - 1
        self.digital_to_volt_scale = v_max / adc_max_digital 

        # Inisialisasi data plot awal
        self.current_adc_data = np.zeros(self.NUM_SAMPLES_PER_ACQUISITION, dtype=np.int16)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Bagian Kontrol ---
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Mulai Osiloskop")
        self.start_button.clicked.connect(self.start_oscilloscope)
        self.stop_button = QPushButton("Hentikan Osiloskop")
        self.stop_button.clicked.connect(self.stop_oscilloscope)
        self.stop_button.setEnabled(False) # Awalnya dinonaktifkan

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        main_layout.addLayout(control_layout)

        # --- Panel Visualisasi Matplotlib ---
        visualization_panel_layout = QVBoxLayout()
        visualization_panel_layout.addWidget(QLabel("<h2>Tampilan Osiloskop (Gelombang Waktu)</h2>"))

        # Buat figure Matplotlib
        self.fig, self.ax_time = plt.subplots(1, 1, figsize=(9, 5)) # Hanya satu subplot untuk osiloskop
        self.canvas = FigureCanvas(self.fig) # Widget untuk menampilkan figure Matplotlib
        visualization_panel_layout.addWidget(self.canvas)

        # Tambahkan toolbar navigasi (opsional, tapi berguna)
        self.toolbar = NavigationToolbar(self.canvas, self)
        visualization_panel_layout.addWidget(self.toolbar)

        # Inisialisasi plot garis
        # Sumbu X akan mewakili waktu, bukan sampel, untuk tampilan osiloskop yang lebih intuitif
        # Durasi total satu akuisisi
        time_duration_per_acquisition = self.NUM_SAMPLES_PER_ACQUISITION / self.SAMPLING_RATE_HZ
        self.x_time_seconds = np.linspace(0, time_duration_per_acquisition, self.NUM_SAMPLES_PER_ACQUISITION, endpoint=False)

        self.line_time, = self.ax_time.plot(self.x_time_seconds, np.zeros(self.NUM_SAMPLES_PER_ACQUISITION), color='blue', label='Sinyal ADC')

        # Konfigurasi plot Osiloskop
        self.ax_time.set_title("Sinyal ADC - Domain Waktu (Osiloskop)")
        self.ax_time.set_xlabel("Waktu (detik)")
        self.ax_time.set_ylabel("Tegangan (V)")
        self.ax_time.set_ylim(self.VOLTAGE_RANGE_V[0] * 1.1, self.VOLTAGE_RANGE_V[1] * 1.1) # Sedikit lebih lebar dari rentang tegangan
        self.ax_time.grid(True)
        self.ax_time.legend()

        self.fig.tight_layout() # Sesuaikan layout

        main_layout.addLayout(visualization_panel_layout)

    def start_oscilloscope(self):
        try:
            # Hentikan thread sebelumnya jika ada
            if self.serial_thread and self.serial_thread.isRunning():
                self.serial_thread.stop()
                self.serial_thread.wait()

            # Mulai thread penerima serial baru
            self.serial_thread = SerialReceiverThread(
                SERIAL_PORT_RECEIVER, BAUD_RATE, 
                self.NUM_SAMPLES_PER_ACQUISITION, self.ADC_BITS
            )
            self.serial_thread.data_received.connect(self.handle_received_data)
            self.serial_thread.error_occurred.connect(self.show_error_message)
            self.serial_thread.start()

            self.plot_update_timer.start(self.plot_update_interval_ms) # Mulai timer untuk update plot
            self.status_bar.showMessage(f"Mulai osiloskop, membaca dari {SERIAL_PORT_RECEIVER}.")
            
            # Nonaktifkan/aktifkan tombol
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Terjadi Kesalahan", f"Terjadi kesalahan saat memulai osiloskop: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)

    def stop_oscilloscope(self):
        self.plot_update_timer.stop()
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop()
            self.serial_thread.wait()
        
        self.status_bar.showMessage("Osiloskop dihentikan.")

        # Aktifkan/nonaktifkan tombol
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def handle_received_data(self, digital_data):
        """
        Slot yang menerima data dari SerialReceiverThread.
        """
        self.current_adc_data = digital_data
        # print(f"Data diterima di main thread: {digital_data[:5]}...") # Untuk debug

    def update_oscilloscope_plot(self):
        """
        Fungsi ini dipanggil oleh QTimer untuk memperbarui plot Matplotlib.
        """
        if self.current_adc_data is None or len(self.current_adc_data) == 0:
            return # Tidak ada data untuk diplot

        # Konversi data digital ke tegangan untuk visualisasi
        analog_voltage_data = self.current_adc_data.astype(np.float32) * self.digital_to_volt_scale
        
        # Perbarui data plot
        self.line_time.set_ydata(analog_voltage_data)

        # Gambar ulang canvas Matplotlib
        self.canvas.draw()
        self.status_bar.showMessage(f"Plot diperbarui. Sampel terakhir: {analog_voltage_data[0]:.2f}V")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Kesalahan Serial", message)
        self.stop_oscilloscope() # Otomatis hentikan visualisasi jika ada error serial

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
