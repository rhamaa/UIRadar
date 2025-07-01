import sys
import numpy as np
import serial
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QLineEdit, QPushButton, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator, QDoubleValidator # Import QDoubleValidator juga

class ADCSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulasi & Ekspor Data ADC (COM1)")
        self.setGeometry(100, 100, 600, 450) # x, y, width, height, sedikit lebih tinggi

        # --- Konfigurasi ADC (Konstan) ---
        self.ADC_BITS = 16
        self.SAMPLING_RATE_HZ = 200000 # 200 kHz, cukup untuk sinyal audio/RF simulasi
        self.VOLTAGE_RANGE_V = (-5, 5) # -5V hingga +5V

        self.init_ui()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Aplikasi siap.")

        # Inisialisasi QTimer untuk pengiriman berkelanjutan
        self.continuous_send_timer = QTimer(self)
        self.continuous_send_timer.timeout.connect(self._send_single_acquisition)
        self.is_sending_continuously = False

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Bagian Kontrol Sinyal ---
        signal_control_group = QVBoxLayout()
        signal_control_group.addWidget(QLabel("<h2>Kontrol Sinyal Simulasi</h2>"))

        # Amplitudo
        amplitude_layout = QHBoxLayout()
        amplitude_layout.addWidget(QLabel("Amplitudo Sinyal (Vp):"))
        self.amplitude_slider = QSlider(Qt.Horizontal)
        self.amplitude_slider.setRange(1, 50) # 0.1Vp to 5.0Vp (scaled by 0.1 later)
        self.amplitude_slider.setValue(25) # Default 2.5Vp
        self.amplitude_slider.setTickPosition(QSlider.TicksBelow)
        self.amplitude_slider.setTickInterval(5)
        self.amplitude_slider.valueChanged.connect(self.update_amplitude_label)
        self.amplitude_label = QLabel("2.5 Vp")
        amplitude_layout.addWidget(self.amplitude_slider)
        amplitude_layout.addWidget(self.amplitude_label)
        signal_control_group.addLayout(amplitude_layout)

        # Frekuensi
        frequency_layout = QHBoxLayout()
        frequency_layout.addWidget(QLabel("Frekuensi Sinyal (Hz):"))
        self.frequency_slider = QSlider(Qt.Horizontal)
        self.frequency_slider.setRange(100, 50000) # 100 Hz to 50 kHz
        self.frequency_slider.setValue(30000) # Default 30 kHz
        self.frequency_slider.setTickPosition(QSlider.TicksBelow)
        self.frequency_slider.setTickInterval(5000)
        self.frequency_slider.valueChanged.connect(self.update_frequency_label)
        self.frequency_label = QLabel("30000 Hz")
        frequency_layout.addWidget(self.frequency_slider)
        frequency_layout.addWidget(self.frequency_label)
        signal_control_group.addLayout(frequency_layout)

        main_layout.addLayout(signal_control_group)
        main_layout.addStretch(1) # Spasi

        # --- Bagian Kontrol Akuisisi & Ekspor ---
        acquisition_control_group = QVBoxLayout()
        acquisition_control_group.addWidget(QLabel("<h2>Pengaturan Akuisisi & Ekspor</h2>"))

        # Jumlah Sampel
        samples_layout = QHBoxLayout()
        samples_layout.addWidget(QLabel("Jumlah Sampel (per akuisisi):"))
        self.samples_input = QLineEdit("8192") # Default 8192 samples
        self.samples_input.setValidator(QIntValidator(1, 100000)) # Batasi input integer
        samples_layout.addWidget(self.samples_input)
        acquisition_control_group.addLayout(samples_layout)

        # Interval Pengiriman Berkelanjutan
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval Kirim Berkelanjutan (detik):"))
        self.interval_input = QLineEdit("0.5") # Default 0.5 detik
        # Validator untuk angka floating point (misal: 0.1, 1.5)
        self.interval_input.setValidator(QDoubleValidator(0.01, 60.0, 2)) # Min 0.01s, Max 60s, 2 desimal
        interval_layout.addWidget(self.interval_input)
        acquisition_control_group.addLayout(interval_layout)

        # Tombol Kirim Sekali
        self.send_once_button = QPushButton("Kirim Data ADC Sekali")
        self.send_once_button.clicked.connect(self._send_single_acquisition)
        acquisition_control_group.addWidget(self.send_once_button)

        # Tombol Mulai/Hentikan Kirim Berkelanjutan
        continuous_buttons_layout = QHBoxLayout()
        self.start_continuous_button = QPushButton("Mulai Kirim Berkelanjutan")
        self.start_continuous_button.clicked.connect(self._start_continuous_send)
        self.stop_continuous_button = QPushButton("Hentikan Kirim Berkelanjutan")
        self.stop_continuous_button.clicked.connect(self._stop_continuous_send)
        self.stop_continuous_button.setEnabled(False) # Awalnya dinonaktifkan

        continuous_buttons_layout.addWidget(self.start_continuous_button)
        continuous_buttons_layout.addWidget(self.stop_continuous_button)
        acquisition_control_group.addLayout(continuous_buttons_layout)

        main_layout.addLayout(acquisition_control_group)
        main_layout.addStretch(1) # Spasi

        # --- Bagian Output ---
        self.output_label = QLabel("Data ADC yang diekspor akan ditampilkan di sini (cuplikan).")
        self.output_label.setWordWrap(True)
        main_layout.addWidget(self.output_label)

        # Perbarui label awal
        self.update_amplitude_label(self.amplitude_slider.value())
        self.update_frequency_label(self.frequency_slider.value())

    def update_amplitude_label(self, value):
        amplitude_vp = value / 10.0
        self.amplitude_label.setText(f"{amplitude_vp:.1f} Vp")

    def update_frequency_label(self, value):
        self.frequency_label.setText(f"{value} Hz")

    def _send_single_acquisition(self):
        """
        Mensimulasikan akuisisi data ADC dan mengirimkannya melalui serial port.
        Fungsi ini dipanggil baik untuk pengiriman sekali maupun berkelanjutan.
        """
        if not self.is_sending_continuously: # Hanya ubah status bar jika bukan pengiriman berkelanjutan
            self.status_bar.showMessage("Mulai simulasi dan ekspor data...")
            self.send_once_button.setEnabled(False) # Nonaktifkan tombol saat proses

        try:
            # Ambil nilai dari UI
            # Nilai slider frekuensi dan amplitudo akan selalu dibaca yang terbaru
            amplitude_vp = self.amplitude_slider.value() / 10.0 # Peak Voltage
            frequency_hz = self.frequency_slider.value()
            num_samples = int(self.samples_input.text())

            # --- Simulasi ADC ---
            v_min, v_max = self.VOLTAGE_RANGE_V
            
            # Hitung faktor skala untuk konversi ADC
            adc_min_digital = -(2**(self.ADC_BITS - 1))
            adc_max_digital = (2**(self.ADC_BITS - 1)) - 1
            scale_factor = adc_max_digital / v_max # Asumsi 0V analog = 0 digital

            # Buat array waktu
            time_duration = num_samples / self.SAMPLING_RATE_HZ
            t = np.linspace(0, time_duration, num_samples, endpoint=False)

            # Hasilkan sinyal sinus analog
            simulated_analog_signal = amplitude_vp * np.sin(2 * np.pi * frequency_hz * t)
            
            # Kuantisasi sinyal analog ke nilai digital ADC
            digital_data_float = simulated_analog_signal * scale_factor
            exported_adc_array = np.round(digital_data_float).astype(np.int16)
            exported_adc_array = np.clip(exported_adc_array, adc_min_digital, adc_max_digital)

            # --- Ekspor Data ke Serial Port (COM1) ---
            serial_port_name = 'COM1' # Port yang diminta
            baud_rate = 115200 # Kecepatan baud

            ser = None
            try:
                ser = serial.Serial(serial_port_name, baud_rate, timeout=1)
                ser.flushOutput() # Bersihkan buffer output
                
                data_to_send = exported_adc_array.tobytes()
                bytes_sent = ser.write(data_to_send)
                
                if not self.is_sending_continuously:
                    self.status_bar.showMessage(f"Data berhasil diekspor ke {serial_port_name}. Dikirim {bytes_sent} byte.")
                else:
                    self.status_bar.showMessage(f"Mengirim data berkelanjutan ke {serial_port_name} (F: {frequency_hz}Hz, A: {amplitude_vp}Vp). Dikirim {bytes_sent} byte.")
                
                # Tampilkan cuplikan data yang diekspor
                display_snippet = exported_adc_array[:10].tolist() + ['...'] + exported_adc_array[-10:].tolist()
                self.output_label.setText(
                    f"Data ADC (array {num_samples} sampel, int16):\n"
                    f"[{', '.join(map(str, display_snippet))}]"
                )
                # print(f"Data ADC yang diekspor (array {num_samples} sampel, int16):\n{exported_adc_array}") # Untuk debug di konsol

            except serial.SerialException as e:
                # Jika terjadi error serial saat pengiriman berkelanjutan, hentikan timer
                if self.is_sending_continuously:
                    self._stop_continuous_send()
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText(f"Gagal membuka atau menulis ke serial port {serial_port_name}.")
                msg_box.setInformativeText(f"Error: {e}\n\nPastikan port tersedia dan tidak digunakan oleh aplikasi lain.")
                msg_box.setWindowTitle("Kesalahan Serial Port")
                msg_box.exec()
                self.status_bar.showMessage(f"Gagal ekspor: {e}", 5000)
            finally:
                if ser and ser.is_open:
                    ser.close()

        except ValueError:
            if self.is_sending_continuously:
                self._stop_continuous_send()
            QMessageBox.warning(self, "Input Tidak Valid", "Jumlah sampel atau interval harus berupa angka yang valid.")
            self.status_bar.showMessage("Ekspor dibatalkan: Input tidak valid.", 3000)
        except Exception as e:
            if self.is_sending_continuously:
                self._stop_continuous_send()
            QMessageBox.critical(self, "Terjadi Kesalahan", f"Terjadi kesalahan tak terduga: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)
        finally:
            if not self.is_sending_continuously: # Aktifkan kembali tombol hanya jika bukan pengiriman berkelanjutan
                self.send_once_button.setEnabled(True)

    def _start_continuous_send(self):
        try:
            interval_ms = float(self.interval_input.text()) * 1000 # Konversi detik ke milidetik
            if interval_ms <= 0:
                raise ValueError("Interval harus lebih besar dari 0.")

            self.continuous_send_timer.start(int(interval_ms))
            self.is_sending_continuously = True
            self.status_bar.showMessage(f"Mulai pengiriman data berkelanjutan setiap {interval_ms/1000:.2f} detik. Frekuensi dan Amplitudo dapat diubah.")
            
            # Nonaktifkan hanya tombol yang mengganggu pengiriman berkelanjutan
            self.send_once_button.setEnabled(False)
            self.start_continuous_button.setEnabled(False)
            self.stop_continuous_button.setEnabled(True)
            # Slider frekuensi dan amplitudo tetap AKTIF
            self.samples_input.setEnabled(False) # Jumlah sampel tidak bisa diubah saat streaming
            self.interval_input.setEnabled(False) # Interval tidak bisa diubah saat streaming

        except ValueError as e:
            QMessageBox.warning(self, "Input Tidak Valid", f"Interval tidak valid: {e}")
            self.status_bar.showMessage("Gagal memulai pengiriman berkelanjutan: Interval tidak valid.", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Terjadi Kesalahan", f"Terjadi kesalahan saat memulai pengiriman berkelanjutan: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)

    def _stop_continuous_send(self):
        self.continuous_send_timer.stop()
        self.is_sending_continuously = False
        self.status_bar.showMessage("Pengiriman data berkelanjutan dihentikan.")

        # Aktifkan kembali kontrol
        self.send_once_button.setEnabled(True)
        self.start_continuous_button.setEnabled(True)
        self.stop_continuous_button.setEnabled(False)
        self.amplitude_slider.setEnabled(True)
        self.frequency_slider.setEnabled(True)
        self.samples_input.setEnabled(True)
        self.interval_input.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ADCSimulatorApp()
    window.show()
    sys.exit(app.exec())
