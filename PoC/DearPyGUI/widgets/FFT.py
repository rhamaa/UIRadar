# UI/widgets/FFT.py
import dearpygui.dearpygui as dpg
import numpy as np
import threading
import queue
import struct
import os
import time
from scipy.fft import fft, fftfreq

# --- Konfigurasi ---
# Nama file yang akan dipantau
FILENAME = "live_acquisition_ui.bin"
SAMPLE_RATE = 20_000_000  # 20 MHz
POLLING_INTERVAL = 0.2  # Detik. Seberapa sering memeriksa file (5 kali per detik)

# --- Fungsi Helper (Tidak Berubah) ---

def load_and_process_data(filepath, sr):
    """Memuat data dari file biner, memisahkan channel, dan menghapus DC offset."""
    try:
        if not os.path.exists(filepath):
            return None, None, None, None

        with open(filepath, "rb") as f:
            data = f.read()
        
        if not data: # Jika file kosong
            return np.array([]), np.array([]), 0, sr

        values = np.array(struct.unpack(f"<{len(data)//2}H", data), dtype=np.float32)
        ch1 = values[::2]
        ch2 = values[1::2]
        ch1 -= np.mean(ch1)
        ch2 -= np.mean(ch2)
        return ch1, ch2, len(ch1), sr
    except Exception as e:
        print(f"Error reading or processing file {filepath}: {e}")
        return None, None, None, None


def compute_fft(channel, sample_rate):
    """Menghitung FFT untuk satu channel."""
    n = len(channel)
    if n == 0:
        return np.array([]), np.array([])
    fft_vals = fft(channel)
    magnitudes = np.abs(fft_vals)[:n//2]
    frequencies = fftfreq(n, d=1/sample_rate)[:n//2]
    return frequencies, magnitudes

# --- Fungsi Worker Thread (Logika Real-time Baru) ---

def fft_data_worker(result_queue: queue.Queue, stop_event: threading.Event):
    """
    Worker yang secara terus-menerus memantau file dan memprosesnya jika ada perubahan.
    """
    print(f"FFT worker started. Monitoring '{FILENAME}' for changes...")
    last_modified_time = 0

    while not stop_event.is_set():
        try:
            # Cek apakah file ada
            if not os.path.exists(FILENAME):
                result_queue.put({"status": "waiting", "message": f"Menunggu file '{FILENAME}'..."})
                time.sleep(1) # Tunggu lebih lama jika file tidak ada
                continue

            # Dapatkan waktu modifikasi terakhir file
            current_mtime = os.path.getmtime(FILENAME)

            # Jika file telah dimodifikasi
            if current_mtime != last_modified_time:
                print(f"File '{FILENAME}' changed. Processing...")
                last_modified_time = current_mtime # Update waktu terakhir
                
                result_queue.put({"status": "processing"})
                
                ch1_data, ch2_data, n_samples, sr = load_and_process_data(FILENAME, SAMPLE_RATE)

                if ch1_data is None or n_samples == 0:
                    result_queue.put({"status": "error", "message": f"Gagal memproses file '{FILENAME}'."})
                    continue

                freqs_ch1, mag_ch1 = compute_fft(ch1_data, sr)
                freqs_ch2, mag_ch2 = compute_fft(ch2_data, sr)
                
                result_data = {
                    "status": "done",
                    "freqs_ch1": freqs_ch1, "mag_ch1": mag_ch1,
                    "freqs_ch2": freqs_ch2, "mag_ch2": mag_ch2,
                    "n_samples": n_samples, "sample_rate": sr
                }
                result_queue.put(result_data)
                print("FFT worker finished job and sent results.")
            
            # Tunggu sejenak sebelum memeriksa lagi untuk efisiensi CPU
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f"Error in FFT worker loop: {e}")
            result_queue.put({"status": "error", "message": f"Error: {e}"})
            time.sleep(1) # Tunggu sebentar jika ada error
    
    print("FFT worker thread stopped.")

# --- Fungsi Pembuat Widget UI (Disederhanakan) ---

def create_fft_widget():
    """Membuat widget UI untuk FFT Desktop. Tombol tidak lagi diperlukan."""
    with dpg.group():
        dpg.add_text(f"Monitoring '{FILENAME}'...", tag="fft_status_text")
        
        with dpg.plot(label="Live FFT Spectrum", height=-1, width=-1, tag="fft_plot"):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)", tag="fft_xaxis", log_scale=True)
            dpg.set_axis_limits("fft_xaxis", 1e3, 1e7)
            dpg.add_plot_axis(dpg.mvYAxis, label="Magnitude", tag="fft_yaxis")
            dpg.add_line_series([], [], label="CH1 (odd)", parent="fft_yaxis", tag="fft_ch1_series")
            dpg.add_line_series([], [], label="CH2 (even)", parent="fft_yaxis", tag="fft_ch2_series")