import sys
import numpy as np
import serial
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QLineEdit, QPushButton, QStatusBar, QMessageBox,
    QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator, QDoubleValidator

class RFIQSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulasi Generator Sinyal RF (I/Q) - (COM1)")
        self.setGeometry(100, 100, 800, 700)

        # --- Konfigurasi ADC (Konstan) ---
        self.ADC_BITS = 16
        self.SAMPLING_RATE_HZ = 200000 # 200 kHz
        self.VOLTAGE_RANGE_V = (-5, 5)

        self.init_ui()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Aplikasi siap.")

        self.continuous_send_timer = QTimer(self)
        self.continuous_send_timer.timeout.connect(self._send_single_acquisition)
        self.is_sending_continuously = False

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Bagian Kontrol Sinyal Channel 0 (In-phase) ---
        ch0_group_box = QGroupBox("Channel 0 (In-phase / Sine)")
        ch0_layout = QVBoxLayout()

        # Amplitudo Channel 0
        amplitude_layout_ch0 = QHBoxLayout()
        amplitude_layout_ch0.addWidget(QLabel("Amplitudo Sinyal (Vp):"))
        self.amplitude_slider_ch0 = QSlider(Qt.Horizontal)
        self.amplitude_slider_ch0.setRange(1, 50)
        self.amplitude_slider_ch0.setValue(25)
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
        self.frequency_slider_ch0.setRange(100, 50000)
        self.frequency_slider_ch0.setValue(30000)
        self.frequency_slider_ch0.setTickPosition(QSlider.TicksBelow)
        self.frequency_slider_ch0.setTickInterval(5000)
        self.frequency_slider_ch0.valueChanged.connect(self.update_frequency_label_ch0)
        self.frequency_label_ch0 = QLabel("30000 Hz")
        frequency_layout_ch0.addWidget(self.frequency_slider_ch0)
        frequency_layout_ch0.addWidget(self.frequency_label_ch0)
        ch0_layout.addLayout(frequency_layout_ch0)

        ch0_group_box.setLayout(ch0_layout)
        main_layout.addWidget(ch0_group_box)

        # --- Bagian Kontrol Sinyal Channel 2 (Quadrature) ---
        ch2_group_box = QGroupBox("Channel 2 (Quadrature) - Mengikuti Channel 0")
        ch2_layout = QVBoxLayout()

        # Amplitudo Channel 2
        amplitude_layout_ch2 = QHBoxLayout()
        amplitude_layout_ch2.addWidget(QLabel("Amplitudo Sinyal (Vp):"))
        self.amplitude_slider_ch2 = QSlider(Qt.Horizontal)
        self.amplitude_slider_ch2.setRange(1, 50)
        self.amplitude_slider_ch2.setValue(25)
        self.amplitude_slider_ch2.setEnabled(False)
        self.amplitude_label_ch2 = QLabel("2.5 Vp")
        amplitude_layout_ch2.addWidget(self.amplitude_slider_ch2)
        amplitude_layout_ch2.addWidget(self.amplitude_label_ch2)
        ch2_layout.addLayout(amplitude_layout_ch2)

        # Frekuensi Channel 2
        frequency_layout_ch2 = QHBoxLayout()
        frequency_layout_ch2.addWidget(QLabel("Frekuensi Sinyal (Hz):"))
        self.frequency_slider_ch2 = QSlider(Qt.Horizontal)
        self.frequency_slider_ch2.setRange(100, 50000)
        self.frequency_slider_ch2.setValue(30000)
        self.frequency_slider_ch2.setEnabled(False)
        self.frequency_label_ch2 = QLabel("30000 Hz")
        frequency_layout_ch2.addWidget(self.frequency_slider_ch2)
        frequency_layout_ch2.addWidget(self.frequency_label_ch2)
        ch2_layout.addLayout(frequency_layout_ch2)

        ch2_group_box.setLayout(ch2_layout)
        main_layout.addWidget(ch2_group_box)

        main_layout.addStretch(1)

        # --- Bagian Kontrol Akuisisi & Ekspor ---
        acquisition_control_group = QGroupBox("Pengaturan Akuisisi & Ekspor")
        acquisition_layout = QVBoxLayout()

        samples_layout = QHBoxLayout()
        samples_layout.addWidget(QLabel("Jumlah Sampel (per Channel):"))
        self.samples_per_channel_input = QLineEdit("8192")
        self.samples_per_channel_input.setValidator(QIntValidator(1, 50000))
        samples_layout.addWidget(self.samples_per_channel_input)
        acquisition_layout.addLayout(samples_layout)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval Kirim Berkelanjutan (detik):"))
        self.interval_input = QLineEdit("0.5")
        self.interval_input.setValidator(QDoubleValidator(0.01, 60.0, 2))
        interval_layout.addWidget(self.interval_input)
        acquisition_layout.addLayout(interval_layout)

        self.send_once_button = QPushButton("Kirim Data ADC Sekali")
        self.send_once_button.clicked.connect(self._send_single_acquisition)
        acquisition_layout.addWidget(self.send_once_button)

        continuous_buttons_layout = QHBoxLayout()
        self.start_continuous_button = QPushButton("Mulai Kirim Berkelanjutan")
        self.start_continuous_button.clicked.connect(self._start_continuous_send)
        self.stop_continuous_button = QPushButton("Hentikan Kirim Berkelanjutan")
        self.stop_continuous_button.clicked.connect(self._stop_continuous_send)
        self.stop_continuous_button.setEnabled(False)

        continuous_buttons_layout.addWidget(self.start_continuous_button)
        continuous_buttons_layout.addWidget(self.stop_continuous_button)
        acquisition_layout.addLayout(continuous_buttons_layout)

        acquisition_control_group.setLayout(acquisition_layout)
        main_layout.addWidget(acquisition_control_group)
        main_layout.addStretch(1)

        self.output_label = QLabel("Data ADC yang diekspor akan ditampilkan di sini (cuplikan).")
        self.output_label.setWordWrap(True)
        main_layout.addWidget(self.output_label)

        self.update_amplitude_label_ch0(self.amplitude_slider_ch0.value())
        self.update_frequency_label_ch0(self.frequency_slider_ch0.value())

    def update_amplitude_label_ch0(self, value):
        """Updates amplitude labels and slider for both channels based on Ch0's slider."""
        amplitude_vp = value / 10.0
        text = f"{amplitude_vp:.1f} Vp"
        self.amplitude_label_ch0.setText(text)
        self.amplitude_label_ch2.setText(text)
        self.amplitude_slider_ch2.setValue(value)

    def update_frequency_label_ch0(self, value):
        """Updates frequency labels and slider for both channels based on Ch0's slider."""
        text = f"{value} Hz"
        self.frequency_label_ch0.setText(text)
        self.frequency_label_ch2.setText(text)
        self.frequency_slider_ch2.setValue(value)

    def _send_single_acquisition(self):
        if not self.is_sending_continuously:
            self.status_bar.showMessage("Mulai simulasi dan ekspor data I/Q...")
            self.send_once_button.setEnabled(False)

        try:
            # Ambil nilai dasar dari UI untuk Channel 0
            base_amplitude_vp = self.amplitude_slider_ch0.value() / 10.0
            base_frequency_hz = self.frequency_slider_ch0.value()

            # --- Variasi Realistis untuk Sinyal RF ---
            # Tambahkan sedikit variasi acak pada amplitudo dan frekuensi setiap kali dikirim
            # untuk mensimulasikan jitter dan noise.
            amplitude_variation = base_amplitude_vp * np.random.uniform(-0.02, 0.02) # Variasi +/- 2%
            frequency_variation = base_frequency_hz * np.random.uniform(-0.001, 0.001) # Variasi +/- 0.1%

            amplitude_vp_ch0 = base_amplitude_vp + amplitude_variation
            frequency_hz_ch0 = base_frequency_hz + frequency_variation

            # Channel 2 (Quadrature) menggunakan parameter yang sama dengan Channel 0 (In-phase)
            amplitude_vp_ch2 = amplitude_vp_ch0
            frequency_hz_ch2 = frequency_hz_ch0

            num_samples_per_channel = int(self.samples_per_channel_input.text())
            total_samples_to_send = num_samples_per_channel * 2

            v_min, v_max = self.VOLTAGE_RANGE_V
            adc_min_digital = -(2**(self.ADC_BITS - 1))
            adc_max_digital = (2**(self.ADC_BITS - 1)) - 1
            scale_factor = adc_max_digital / v_max

            time_duration_per_channel = num_samples_per_channel / self.SAMPLING_RATE_HZ
            t = np.linspace(0, time_duration_per_channel, num_samples_per_channel, endpoint=False)

            # Hasilkan sinyal In-phase (sinus) untuk Channel 0
            simulated_analog_signal_ch0 = amplitude_vp_ch0 * np.sin(2 * np.pi * frequency_hz_ch0 * t)
            digital_data_float_ch0 = simulated_analog_signal_ch0 * scale_factor
            exported_adc_array_ch0 = np.round(digital_data_float_ch0).astype(np.int16)
            exported_adc_array_ch0 = np.clip(exported_adc_array_ch0, adc_min_digital, adc_max_digital)

            # Hasilkan sinyal Quadrature (cosinus, beda fasa 90 derajat) untuk Channel 2
            simulated_analog_signal_ch2 = amplitude_vp_ch2 * np.cos(2 * np.pi * frequency_hz_ch2 * t) # Menggunakan cos() untuk beda fasa 90 derajat
            digital_data_float_ch2 = simulated_analog_signal_ch2 * scale_factor
            exported_adc_array_ch2 = np.round(digital_data_float_ch2).astype(np.int16)
            exported_adc_array_ch2 = np.clip(exported_adc_array_ch2, adc_min_digital, adc_max_digital)

            interleaved_data = np.empty(total_samples_to_send, dtype=np.int16)
            interleaved_data[::2] = exported_adc_array_ch0
            interleaved_data[1::2] = exported_adc_array_ch2

            serial_port_name = 'COM1'
            baud_rate = 115200

            ser = None
            try:
                ser = serial.Serial(serial_port_name, baud_rate, timeout=1)
                ser.flushOutput()

                data_to_send = interleaved_data.tobytes()
                bytes_sent = ser.write(data_to_send)

                if not self.is_sending_continuously:
                    self.status_bar.showMessage(f"Data I/Q berhasil diekspor ke {serial_port_name}. Dikirim {bytes_sent} byte.")
                else:
                    # Tampilkan nilai dengan presisi untuk menunjukkan variasi
                    freq_display = f"{frequency_hz_ch0:,.2f} Hz"
                    amp_display = f"{amplitude_vp_ch0:.3f} Vp"
                    self.status_bar.showMessage(f"Mengirim I/Q ke {serial_port_name} (f: {freq_display}, A: {amp_display}). Dikirim {bytes_sent} byte.")

                display_snippet_ch0 = exported_adc_array_ch0[:5].tolist() + ['...'] + exported_adc_array_ch0[-5:].tolist()
                display_snippet_ch2 = exported_adc_array_ch2[:5].tolist() + ['...'] + exported_adc_array_ch2[-5:].tolist()
                self.output_label.setText(
                    f"Data ADC CH0 (In-phase) ({num_samples_per_channel} sampel, int16):\n"
                    f"[{', '.join(map(str, display_snippet_ch0))}]\n"
                    f"Data ADC CH2 (Quadrature) ({num_samples_per_channel} sampel, int16):\n"
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
            self.status_bar.showMessage(f"Mulai pengiriman data berkelanjutan setiap {interval_ms/1000:.2f} detik.")

            self.send_once_button.setEnabled(False)
            self.start_continuous_button.setEnabled(False)
            self.stop_continuous_button.setEnabled(True)

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

        self.send_once_button.setEnabled(True)
        self.start_continuous_button.setEnabled(True)
        self.stop_continuous_button.setEnabled(False)

        self.amplitude_slider_ch0.setEnabled(True)
        self.frequency_slider_ch0.setEnabled(True)
        self.amplitude_slider_ch2.setEnabled(False)
        self.samples_per_channel_input.setEnabled(True)
        self.interval_input.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RFIQSimulatorApp()
    window.show()
    sys.exit(app.exec())