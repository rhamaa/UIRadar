import sys
import numpy as np
import serial
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QLineEdit, QPushButton, QStatusBar, QMessageBox,
    QGroupBox # Untuk mengelompokkan kontrol setiap channel
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator, QDoubleValidator

class ADCSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulasi Generator Sinyal Dual Channel (COM1)")
        self.setGeometry(100, 100, 800, 700) # Ukuran jendela lebih besar

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

        # --- Bagian Kontrol Sinyal Channel 0 ---
        ch0_group_box = QGroupBox("Channel 0 (In-phase)")
        ch0_layout = QVBoxLayout()

        # Amplitudo Channel 0
        amplitude_layout_ch0 = QHBoxLayout()
        amplitude_layout_ch0.addWidget(QLabel("Amplitudo Sinyal (Vp):"))
        self.amplitude_slider_ch0 = QSlider(Qt.Horizontal)
        self.amplitude_slider_ch0.setRange(1, 50) # 0.1Vp to 5.0Vp
        self.amplitude_slider_ch0.setValue(25) # Default 2.5Vp
        self.amplitude_slider_ch0.setTickPosition(QSlider.TicksBelow)
        self.amplitude_slider_ch0.setTickInterval(5)
        self.amplitude_slider_ch0.valueChanged.connect(self.update_amplitude_label_ch0)
        self.amplitude_label_ch0 = QLabel("2.5 Vp")
        amplitude_layout_ch0.addWidget(self.amplitude_slider_ch0)
        amplitude_layout_ch0.addWidget(self.amplitude_label_ch0)
        ch0_layout.addLayout(amplitude_layout_ch0)

        # Frekuensi Channel 0
        frequency_layout_ch0 = QHBoxLayout()
        frequency_layout_ch0.addWidget(QLabel("Frekuensi Sinyal (Hz):"))
        self.frequency_slider_ch0 = QSlider(Qt.Horizontal)
        self.frequency_slider_ch0.setRange(100, 50000) # 100 Hz to 50 kHz
        self.frequency_slider_ch0.setValue(30000) # Default 30 kHz
        self.frequency_slider_ch0.setTickPosition(QSlider.TicksBelow)
        self.frequency_slider_ch0.setTickInterval(5000)
        self.frequency_slider_ch0.valueChanged.connect(self.update_frequency_label_ch0)
        self.frequency_label_ch0 = QLabel("30000 Hz")
        frequency_layout_ch0.addWidget(self.frequency_slider_ch0)
        frequency_layout_ch0.addWidget(self.frequency_label_ch0)
        ch0_layout.addLayout(frequency_layout_ch0)
        
        ch0_group_box.setLayout(ch0_layout)
        main_layout.addWidget(ch0_group_box)

        # --- Bagian Kontrol Sinyal Channel 2 ---
        ch2_group_box = QGroupBox("Channel 2 (Quadrature)")
        ch2_layout = QVBoxLayout()

        # Amplitudo Channel 2
        amplitude_layout_ch2 = QHBoxLayout()
        amplitude_layout_ch2.addWidget(QLabel("Amplitudo Sinyal (Vp):"))
        self.amplitude_slider_ch2 = QSlider(Qt.Horizontal)
        self.amplitude_slider_ch2.setRange(1, 50) # 0.1Vp to 5.0Vp
        self.amplitude_slider_ch2.setValue(25) # Default 2.5Vp
        self.amplitude_slider_ch2.setTickPosition(QSlider.TicksBelow)
        self.amplitude_slider_ch2.setTickInterval(5)
        self.amplitude_slider_ch2.valueChanged.connect(self.update_amplitude_label_ch2)
        self.amplitude_label_ch2 = QLabel("2.5 Vp")
        amplitude_layout_ch2.addWidget(self.amplitude_slider_ch2)
        amplitude_layout_ch2.addWidget(self.amplitude_label_ch2)
        ch2_layout.addLayout(amplitude_layout_ch2)

        # Frekuensi Channel 2
        frequency_layout_ch2 = QHBoxLayout()
        frequency_layout_ch2.addWidget(QLabel("Frekuensi Sinyal (Hz):"))
        self.frequency_slider_ch2 = QSlider(Qt.Horizontal)
        self.frequency_slider_ch2.setRange(100, 50000) # 100 Hz to 50 kHz
        self.frequency_slider_ch2.setValue(30000) # Default 30 kHz
        self.frequency_slider_ch2.setTickPosition(QSlider.TicksBelow)
        self.frequency_slider_ch2.setTickInterval(5000)
        self.frequency_slider_ch2.valueChanged.connect(self.update_frequency_label_ch2)
        self.frequency_label_ch2 = QLabel("30000 Hz")
        frequency_layout_ch2.addWidget(self.frequency_slider_ch2)
        frequency_layout_ch2.addWidget(self.frequency_label_ch2)
        ch2_layout.addLayout(frequency_layout_ch2)
        
        ch2_group_box.setLayout(ch2_layout)
        main_layout.addWidget(ch2_group_box)

        main_layout.addStretch(1) # Spasi

        # --- Bagian Kontrol Akuisisi & Ekspor ---
        acquisition_control_group = QGroupBox("Pengaturan Akuisisi & Ekspor")
        acquisition_layout = QVBoxLayout()

        # Jumlah Sampel Per Channel
        samples_layout = QHBoxLayout()
        samples_layout.addWidget(QLabel("Jumlah Sampel (per Channel):"))
        self.samples_per_channel_input = QLineEdit("8192") # Default 8192 samples per channel
        self.samples_per_channel_input.setValidator(QIntValidator(1, 50000)) # Batasi input integer per channel
        samples_layout.addWidget(self.samples_per_channel_input)
        acquisition_layout.addLayout(samples_layout)

        # Interval Pengiriman Berkelanjutan
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval Kirim Berkelanjutan (detik):"))
        self.interval_input = QLineEdit("0.5") # Default 0.5 detik
        self.interval_input.setValidator(QDoubleValidator(0.01, 60.0, 2)) # Min 0.01s, Max 60s, 2 desimal
        interval_layout.addWidget(self.interval_input)
        acquisition_layout.addLayout(interval_layout)

        # Tombol Kirim Sekali
        self.send_once_button = QPushButton("Kirim Data ADC Sekali")
        self.send_once_button.clicked.connect(self._send_single_acquisition)
        acquisition_layout.addWidget(self.send_once_button)

        # Tombol Mulai/Hentikan Kirim Berkelanjutan
        continuous_buttons_layout = QHBoxLayout()
        self.start_continuous_button = QPushButton("Mulai Kirim Berkelanjutan")
        self.start_continuous_button.clicked.connect(self._start_continuous_send)
        self.stop_continuous_button = QPushButton("Hentikan Kirim Berkelanjutan")
        self.stop_continuous_button.clicked.connect(self._stop_continuous_send)
        self.stop_continuous_button.setEnabled(False) # Awalnya dinonaktifkan

        continuous_buttons_layout.addWidget(self.start_continuous_button)
        continuous_buttons_layout.addWidget(self.stop_continuous_button)
        acquisition_layout.addLayout(continuous_buttons_layout)
        
        acquisition_control_group.setLayout(acquisition_layout)
        main_layout.addWidget(acquisition_control_group)
        main_layout.addStretch(1) # Spasi

        # --- Bagian Output ---
        self.output_label = QLabel("Data ADC yang diekspor akan ditampilkan di sini (cuplikan).")
        self.output_label.setWordWrap(True)
        main_layout.addWidget(self.output_label)

        # Perbarui label awal
        self.update_amplitude_label_ch0(self.amplitude_slider_ch0.value())
        self.update_frequency_label_ch0(self.frequency_slider_ch0.value())
        self.update_amplitude_label_ch2(self.amplitude_slider_ch2.value())
        self.update_frequency_label_ch2(self.frequency_slider_ch2.value())

    # --- Fungsi Update Label Channel 0 ---
    def update_amplitude_label_ch0(self, value):
        amplitude_vp = value / 10.0
        self.amplitude_label_ch0.setText(f"{amplitude_vp:.1f} Vp")

    def update_frequency_label_ch0(self, value):
        self.frequency_label_ch0.setText(f"{value} Hz")

    # --- Fungsi Update Label Channel 2 ---
    def update_amplitude_label_ch2(self, value):
        amplitude_vp = value / 10.0
        self.amplitude_label_ch2.setText(f"{amplitude_vp:.1f} Vp")

    def update_frequency_label_ch2(self, value):
        self.frequency_label_ch2.setText(f"{value} Hz")

    def _send_single_acquisition(self):
        """
        Mensimulasikan akuisisi data ADC untuk dua channel dan mengirimkannya
        melalui serial port dalam format interleaved binary.
        Fungsi ini dipanggil baik untuk pengiriman sekali maupun berkelanjutan.
        """
        if not self.is_sending_continuously:
            self.status_bar.showMessage("Mulai simulasi dan ekspor data dual channel...")
            self.send_once_button.setEnabled(False)

        try:
            # Ambil nilai dari UI untuk Channel 0
            amplitude_vp_ch0 = self.amplitude_slider_ch0.value() / 10.0
            frequency_hz_ch0 = self.frequency_slider_ch0.value()
            
            # Ambil nilai dari UI untuk Channel 2
            amplitude_vp_ch2 = self.amplitude_slider_ch2.value() / 10.0
            frequency_hz_ch2 = self.frequency_slider_ch2.value()
            
            num_samples_per_channel = int(self.samples_per_channel_input.text())
            total_samples_to_send = num_samples_per_channel * 2 # Total sampel untuk kedua channel

            # --- Simulasi ADC ---
            v_min, v_max = self.VOLTAGE_RANGE_V
            
            adc_min_digital = -(2**(self.ADC_BITS - 1))
            adc_max_digital = (2**(self.ADC_BITS - 1)) - 1
            scale_factor = adc_max_digital / v_max

            # Buat array waktu untuk satu channel
            time_duration_per_channel = num_samples_per_channel / self.SAMPLING_RATE_HZ
            t = np.linspace(0, time_duration_per_channel, num_samples_per_channel, endpoint=False)

            # Hasilkan sinyal sinus analog untuk Channel 0
            simulated_analog_signal_ch0 = amplitude_vp_ch0 * np.sin(2 * np.pi * frequency_hz_ch0 * t)
            digital_data_float_ch0 = simulated_analog_signal_ch0 * scale_factor
            exported_adc_array_ch0 = np.round(digital_data_float_ch0).astype(np.int16)
            exported_adc_array_ch0 = np.clip(exported_adc_array_ch0, adc_min_digital, adc_max_digital)

            # Hasilkan sinyal sinus analog untuk Channel 2
            simulated_analog_signal_ch2 = amplitude_vp_ch2 * np.sin(2 * np.pi * frequency_hz_ch2 * t)
            digital_data_float_ch2 = simulated_analog_signal_ch2 * scale_factor
            exported_adc_array_ch2 = np.round(digital_data_float_ch2).astype(np.int16)
            exported_adc_array_ch2 = np.clip(exported_adc_array_ch2, adc_min_digital, adc_max_digital)

            # --- Interleave Data ---
            # Gabungkan data CH0 dan CH2 secara bergantian
            interleaved_data = np.empty(total_samples_to_send, dtype=np.int16)
            interleaved_data[::2] = exported_adc_array_ch0  # Sampel genap untuk CH0
            interleaved_data[1::2] = exported_adc_array_ch2 # Sampel ganjil untuk CH2
            
            # --- Ekspor Data ke Serial Port (COM1) ---
            serial_port_name = 'COM1'
            baud_rate = 115200

            ser = None
            try:
                ser = serial.Serial(serial_port_name, baud_rate, timeout=1)
                ser.flushOutput()
                
                data_to_send = interleaved_data.tobytes() # Kirim array interleaved sebagai byte
                bytes_sent = ser.write(data_to_send)
                
                if not self.is_sending_continuously:
                    self.status_bar.showMessage(f"Data dual channel berhasil diekspor ke {serial_port_name}. Dikirim {bytes_sent} byte (total {total_samples_to_send} sampel).")
                else:
                    self.status_bar.showMessage(f"Mengirim berkelanjutan ke {serial_port_name} (CH0: {frequency_hz_ch0}Hz/{amplitude_vp_ch0}Vp, CH2: {frequency_hz_ch2}Hz/{amplitude_vp_ch2}Vp). Dikirim {bytes_sent} byte.")
                
                # Tampilkan cuplikan data yang diekspor (dari CH0 dan CH2)
                display_snippet_ch0 = exported_adc_array_ch0[:5].tolist() + ['...'] + exported_adc_array_ch0[-5:].tolist()
                display_snippet_ch2 = exported_adc_array_ch2[:5].tolist() + ['...'] + exported_adc_array_ch2[-5:].tolist()
                self.output_label.setText(
                    f"Data ADC CH0 (array {num_samples_per_channel} sampel, int16):\n"
                    f"[{', '.join(map(str, display_snippet_ch0))}]\n"
                    f"Data ADC CH2 (array {num_samples_per_channel} sampel, int16):\n"
                    f"[{', '.join(map(str, display_snippet_ch2))}]\n"
                    f"Data dikirim sebagai interleaved binary ({total_samples_to_send} total sampel)."
                )

            except serial.SerialException as e:
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

        except ValueError as e:
            if self.is_sending_continuously:
                self._stop_continuous_send()
            QMessageBox.warning(self, "Input Tidak Valid", f"Jumlah sampel atau interval tidak valid: {e}")
            self.status_bar.showMessage("Ekspor dibatalkan: Input tidak valid.", 3000)
        except Exception as e:
            if self.is_sending_continuously:
                self._stop_continuous_send()
            QMessageBox.critical(self, "Terjadi Kesalahan", f"Terjadi kesalahan tak terduga: {e}")
            self.status_bar.showMessage(f"Kesalahan: {e}", 5000)
        finally:
            if not self.is_sending_continuously:
                self.send_once_button.setEnabled(True)

    def _start_continuous_send(self):
        try:
            interval_ms = float(self.interval_input.text()) * 1000
            if interval_ms <= 0:
                raise ValueError("Interval harus lebih besar dari 0.")

            self.continuous_send_timer.start(int(interval_ms))
            self.is_sending_continuously = True
            self.status_bar.showMessage(f"Mulai pengiriman data berkelanjutan setiap {interval_ms/1000:.2f} detik. Pengaturan channel dapat diubah.")
            
            # Nonaktifkan tombol yang mengganggu pengiriman berkelanjutan
            self.send_once_button.setEnabled(False)
            self.start_continuous_button.setEnabled(False)
            self.stop_continuous_button.setEnabled(True)
            
            # Pengaturan frekuensi dan amplitudo tetap AKTIF
            # Jumlah sampel dan interval TIDAK BISA DIUBAH saat streaming
            self.samples_per_channel_input.setEnabled(False)
            self.interval_input.setEnabled(False)

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
        
        # Aktifkan kembali semua slider dan input
        self.amplitude_slider_ch0.setEnabled(True)
        self.frequency_slider_ch0.setEnabled(True)
        self.amplitude_slider_ch2.setEnabled(True)
        self.frequency_slider_ch2.setEnabled(True)
        self.samples_per_channel_input.setEnabled(True)
        self.interval_input.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ADCSimulatorApp()
    window.show()
    sys.exit(app.exec())
