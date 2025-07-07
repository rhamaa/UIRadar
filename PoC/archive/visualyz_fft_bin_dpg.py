import numpy as np
import struct
import os
from dearpygui import dearpygui as dpg
from scipy.fft import fft, fftfreq

# --- Configuration ---
filename = "90khz.bin"  # Change if your file name is different
sample_rate = 20_000_000  # 20 MHz, corresponding to PCI-9846H hardware

# --- Data Loading and Processing ---
def load_and_process_data(filepath, sr):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found. Make sure the file is in the same directory as this script.")
        return None, None, None, None

    with open(filepath, "rb") as f:
        data = f.read()
        values = np.array(struct.unpack("<{}H".format(len(data)//2), data), dtype=np.float32)

    ch1 = values[::2]
    ch2 = values[1::2]

    ch1 -= np.mean(ch1)
    ch2 -= np.mean(ch2)

    return ch1, ch2, len(ch1), sr

def compute_fft(channel, sample_rate):
    n = len(channel)
    if n == 0:
        return np.array([]), np.array([])

    fft_vals = fft(channel)
    mag = np.abs(fft_vals)[:n//2]
    freqs = fftfreq(n, d=1/sample_rate)[:n//2]
    return freqs, mag

# --- DearPyGui Setup ---
dpg.create_context()
dpg.create_viewport(title='FFT Spectrum Analyzer', width=1200, height=700)

freqs_ch1_dpg = []
mag_ch1_dpg = []
freqs_ch2_dpg = []
mag_ch2_dpg = []

# --- Main Plotting Function ---
def plot_fft_spectrum():
    global freqs_ch1_dpg, mag_ch1_dpg, freqs_ch2_dpg, mag_ch2_dpg

    ch1_data, ch2_data, n_samples, sr = load_and_process_data(filename, sample_rate)

    if ch1_data is None or ch2_data is None:
        with dpg.window(label="Error", width=400, height=100, pos=(400, 300), show=True, tag="error_window"):
            dpg.add_text(f"File '{filename}' not found or could not be processed.")
            dpg.add_text("Please ensure the file is in the correct directory.")
        return

    freqs_ch1, mag_ch1 = compute_fft(ch1_data, sr)
    freqs_ch2, mag_ch2 = compute_fft(ch2_data, sr)

    freqs_ch1_dpg = freqs_ch1.tolist()
    mag_ch1_dpg = mag_ch1.tolist()
    freqs_ch2_dpg = freqs_ch2.tolist()
    mag_ch2_dpg = mag_ch2.tolist()

    if n_samples > 0:
        freq_res = sr / n_samples
        nyquist = sr / 2
        plot_label = f'FFT Spectrum (2 Channel)\nSample Rate: {sr/1e6:.2f} MHz, Buffer: {n_samples}, Resolution: {freq_res:.1f} Hz, Nyquist: {nyquist/1e6:.2f} MHz'
    else:
        plot_label = 'FFT Spectrum (No Data)'

    with dpg.window(label="FFT Spectrum", tag="main_window", width=1180, height=650, pos=(0,0)):
        dpg.add_text("FFT Spectrum Visualization", parent="main_window")

        with dpg.plot(label=plot_label, height=-1, width=-1, tag="spectrum_plot"):
            dpg.add_plot_legend()

            x_axis_tag = "x_axis"
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag=x_axis_tag)
            dpg.set_axis_limits(x_axis_tag, 1e3, 1e5)

            y_axis_tag = "y_axis"
            dpg.add_plot_axis(dpg.mvYAxis, label="Magnitude", tag=y_axis_tag)

            all_magnitudes = []
            if len(mag_ch1) > 0:
                all_magnitudes.extend(mag_ch1.tolist())
            if len(mag_ch2) > 0:
                all_magnitudes.extend(mag_ch2.tolist())

            if all_magnitudes:
                min_mag = min(all_magnitudes)
                max_mag = max(all_magnitudes)
                
                padding = (max_mag - min_mag) * 0.1
                min_plot_mag = min_mag - padding
                max_plot_mag = max_mag + padding

                if min_plot_mag < 0:
                    min_plot_mag = 0
                
                dpg.set_axis_limits(y_axis_tag, min_plot_mag, max_plot_mag)

                num_ticks = 7
                tick_values = np.linspace(min_plot_mag, max_plot_mag, num_ticks)
                
                # --- PERBAIKAN DI SINI ---
                # Pastikan tick_labels adalah tuple dari tuple
                tick_labels = tuple((f"{val:.2f}", val) for val in tick_values) 
                
                dpg.set_axis_ticks(y_axis_tag, tick_labels)
            
            dpg.add_line_series(freqs_ch1_dpg, mag_ch1_dpg, label="CH1 (odd)", parent=y_axis_tag, tag="ch1_series")
            dpg.add_line_series(freqs_ch2_dpg, mag_ch2_dpg, label="CH2 (even)", parent=y_axis_tag, tag="ch2_series")

# --- Initialize and Run DearPyGui ---
plot_fft_spectrum()

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()