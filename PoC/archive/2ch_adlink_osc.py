import sys
import numpy as np
import serial
import time
import threading
import queue

# Import PySide6 components
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QMessageBox, QSlider, QLineEdit
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
        self.setWindowTitle("Osiloskop Realtime (Membaca COM1)")
        self.setGeometry(100, 100, 1200, 800) # Ukuran jendela lebih besar untuk 2 plot

        # --- Konfigurasi ADC (Konstan, harus cocok dengan pengirim) ---
        self.ADC_BITS = DEFAULT_ADC_BITS
        self.SAMPLING_RATE_HZ = DEFAULT_SAMPLING_RATE_HZ
        self.VOLTAGE_RANGE_V = DEFAULT_VOLTAGE_RANGE_V
        
        # SAMPLES_PER_CHANNEL akan dihitung berdasarkan input NUM_SAMPLES_PER_ACQUISITION
        self.num_samples_per_acquisition = DEFAULT_NUM_SAMPLES_PER_ACQUISITION 
        self.samples_per_channel = self.num_samples_per_acquisition // 2

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

        # Inisialisasi data plot awal untuk kedua channel
        self.current_adc_data_ch0 = np.zeros(self.samples_per_channel, dtype=np.int16)
        self.current_adc_data_ch2 = np.zeros(self.samples_per_channel, dtype=np.int16)

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
        
        # Input untuk Jumlah Sampel Per Akuisisi (Total)
        control_layout.addStretch(1)
        control_layout.addWidget(QLabel("Total Sampel (per akuisisi):"))
        self.total_samples_input = QLineEdit(str(DEFAULT_NUM_SAMPLES_PER_ACQUISITION))
        self.total_samples_input.setValidator(QIntValidator(2, 200000)) # Min 2 (1 per channel), Max 200k
        self.total_samples_input.textChanged.connect(self.update_sample_parameters_ui)
        control_layout.addWidget(self.total_samples_input)

        # Slider untuk Zooming (Time Scale)
        control_layout.addWidget(QLabel("Skala Waktu (ms):"))
        self.time_scale_slider = QSlider(Qt.Horizontal)
        # Rentang slider akan diatur di update_sample_parameters_ui
        self.time_scale_slider.setTickPosition(QSlider.TicksBelow)
        self.time_scale_slider.setTickInterval(1) # Akan disesuaikan di update_sample_parameters_ui
        self.time_scale_slider.valueChanged.connect(self.update_time_scale_label)
        
        self.time_scale_label = QLabel("") # Label akan diisi di update_sample_parameters_ui
        control_layout.addWidget(self.time_scale_slider)
        control_layout.addWidget(self.time_scale_label)

        main_layout.addLayout(control_layout)

        # --- Panel Visualisasi Matplotlib ---
        visualization_panel_layout = QVBoxLayout()
        visualization_panel_layout.addWidget(QLabel("<h2>Tampilan Osiloskop (Gelombang Waktu)</h2>"))

        # Buat figure Matplotlib dengan HANYA 1 subplot untuk kedua channel
        self.fig, self.ax_time = plt.subplots(1, 1, figsize=(10, 6)) # Hanya satu subplot
        self.canvas = FigureCanvas(self.fig) # Widget untuk menampilkan figure Matplotlib
        visualization_panel_layout.addWidget(self.canvas)

        # Tambahkan toolbar navigasi (opsional, tapi berguna)
        self.toolbar = NavigationToolbar(self.canvas, self)
        visualization_panel_layout.addWidget(self.toolbar)

        # Inisialisasi plot garis untuk CH0 dan CH2 pada subplot yang sama
        # x_time_seconds akan diinisialisasi di update_sample_parameters_ui
        # Panggil update_sample_parameters_ui di sini untuk menginisialisasi x_time_seconds
        self.update_sample_parameters_ui() # PENTING: Panggil di sini sebelum plot lines dibuat
        
        # Menambahkan 'o-' untuk menampilkan titik dan garis yang menghubungkannya
        self.line_ch0, = self.ax_time.plot(self.x_time_seconds, np.zeros(self.samples_per_channel), 'o-', color='blue', markersize=3, label='Channel 0 (Biru)')
        self.line_ch2, = self.ax_time.plot(self.x_time_seconds, np.zeros(self.samples_per_channel), 'o-', color='red', markersize=3, label='Channel 2 (Merah)')

        # Konfigurasi plot Osiloskop
        self.ax_time.set_title("Sinyal ADC - Domain Waktu (CH0 & CH2)")
        self.ax_time.set_xlabel("Waktu (detik)")
        self.ax_time.set_ylabel("Tegangan (V)")
        self.ax_time.set_ylim(self.VOLTAGE_RANGE_V[0] * 1.1, self.VOLTAGE_RANGE_V[1] * 1.1)
        self.ax_time.grid(True)
        self.ax_time.legend(loc='upper right')

        self.fig.tight_layout() # Sesuaikan layout

        main_layout.addLayout(visualization_panel_layout)
        
    def update_sample_parameters_ui(self):
        """
        Memperbarui parameter terkait jumlah sampel dan skala waktu di UI dan plot.
        Dipanggil saat input jumlah sampel berubah.
        """
        try:
            new_num_samples_total = int(self.total_samples_input.text())
            if new_num_samples_total < 2 or new_num_samples_total % 2 != 0:
                raise ValueError("Jumlah sampel total harus genap dan minimal 2.")
            
            self.num_samples_per_acquisition = new_num_samples_total
            self.samples_per_channel = self.num_samples_per_acquisition // 2

            # Perbarui array waktu untuk plotting
            total_time_per_channel_ms = (self.samples_per_channel / self.SAMPLING_RATE_HZ) * 1000
            self.x_time_seconds = np.linspace(0, total_time_per_channel_ms / 1000, self.samples_per_channel, endpoint=False)
            
            # Perbarui data x pada plot (hanya jika line_ch0 sudah ada)
            if hasattr(self, 'line_ch0'): # Cek apakah plot lines sudah diinisialisasi
                self.line_ch0.set_xdata(self.x_time_seconds)
                self.line_ch2.set_xdata(self.x_time_seconds)

            # Perbarui rentang slider skala waktu
            self.time_scale_slider.setRange(1, int(total_time_per_channel_ms))
            # Atur nilai slider ke maksimum (tampilkan seluruh durasi) jika melebihi batas saat ini
            if self.time_scale_slider.value() > int(total_time_per_channel_ms):
                self.time_scale_slider.setValue(int(total_time_per_channel_ms))
            
            # Perbarui label skala waktu
            self.update_time_scale_label(self.time_scale_slider.value())

            # Perbarui batas X plot
            self.ax_time.set_xlim(0, total_time_per_channel_ms / 1000)
            self.canvas.draw_idle() # Gambar ulang kanvas

            # Reset data plot ke nol saat jumlah sampel berubah
            self.current_adc_data_ch0 = np.zeros(self.samples_per_channel, dtype=np.int16)
            self.current_adc_data_ch2 = np.zeros(self.samples_per_channel, dtype=np.int16)
            if hasattr(self, 'line_ch0'): # Cek lagi sebelum set_ydata
                self.line_ch0.set_ydata(np.zeros(self.samples_per_channel))
                self.line_ch2.set_ydata(np.zeros(self.samples_per_channel))
                self.canvas.draw_idle()

        except ValueError as e:
            # Tidak perlu QMessageBox, cukup update status bar atau log
            self.status_bar.showMessage(f"Input sampel tidak valid: {e}", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Kesalahan saat memperbarui parameter sampel: {e}", 3000)


    def update_time_scale_label(self, value):
        self.time_scale_label.setText(f"{value:.2f} ms")
        # Perbarui batas X (zoom) saat slider digeser
        end_time_s = value / 1000.0 # Konversi ms ke detik
        self.ax_time.set_xlim(0, end_time_s) # Hanya satu sumbu X yang diatur
        self.canvas.draw_idle() # Gambar ulang kanvas

    def start_oscilloscope(self):
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
            self.status_bar.showMessage(f"Mulai osiloskop, membaca dari {DEFAULT_SERIAL_PORT_RECEIVER} dengan {current_num_samples} sampel total.")
            
            # Nonaktifkan/aktifkan tombol dan input
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.time_scale_slider.setEnabled(True) # Aktifkan slider zoom
            self.total_samples_input.setEnabled(False) # Nonaktifkan input jumlah sampel saat berjalan

        except ValueError as e:
            QMessageBox.warning(self, "Input Tidak Valid", f"Jumlah sampel tidak valid: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Terjadi Kesalahan", f"Terjadi kesalahan saat memulai osiloskop: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)

    def stop_oscilloscope(self):
        self.plot_update_timer.stop()
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop()
            self.serial_thread.wait()
        
        self.status_bar.showMessage("Osiloskop dihentikan.")

        # Aktifkan/nonaktifkan tombol dan input
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.time_scale_slider.setEnabled(False) # Nonaktifkan slider zoom
        self.total_samples_input.setEnabled(True) # Aktifkan kembali input jumlah sampel

    def handle_received_data(self, digital_data):
        """
        Slot yang menerima data dari SerialReceiverThread.
        Data digital_data adalah array interleaved dari kedua channel.
        """
        # De-interleave data: sampel genap untuk CH0, sampel ganjil untuk CH2
        # Gunakan panjang data yang diterima untuk menghitung samples_per_channel
        samples_per_channel_received = len(digital_data) // 2
        self.current_adc_data_ch0 = digital_data[::2]
        self.current_adc_data_ch2 = digital_data[1::2]
        
        # Penting: Jika jumlah sampel berubah saat runtime, x_time_seconds perlu disesuaikan.
        # Namun, karena input num_samples dinonaktifkan saat streaming, ini seharusnya tidak terjadi.
        # Jika diaktifkan, logika di update_sample_parameters_ui harus dipanggil di sini.
        
        # print(f"CH0 diterima: {self.current_adc_data_ch0[:5]}...") # Untuk debug
        # print(f"CH2 diterima: {self.current_adc_data_ch2[:5]}...") # Untuk debug

    def update_oscilloscope_plot(self):
        """
        Fungsi ini dipanggil oleh QTimer untuk memperbarui plot Matplotlib.
        """
        # Pastikan panjang data sesuai dengan yang diharapkan setelah de-interleave
        if self.current_adc_data_ch0 is None or len(self.current_adc_data_ch0) != self.samples_per_channel:
            return # Tidak ada data atau panjang tidak sesuai

        # Konversi data digital ke tegangan untuk visualisasi
        analog_voltage_data_ch0 = self.current_adc_data_ch0.astype(np.float32) * self.digital_to_volt_scale
        analog_voltage_data_ch2 = self.current_adc_data_ch2.astype(np.float32) * self.digital_to_volt_scale
        
        # Perbarui data plot untuk CH0 dan CH2
        self.line_ch0.set_ydata(analog_voltage_data_ch0)
        self.line_ch2.set_ydata(analog_voltage_data_ch2)

        # Gambar ulang canvas Matplotlib
        self.canvas.draw()
        self.status_bar.showMessage(f"Plot diperbarui. CH0: {analog_voltage_data_ch0[0]:.2f}V, CH2: {analog_voltage_data_ch2[0]:.2f}V")

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
