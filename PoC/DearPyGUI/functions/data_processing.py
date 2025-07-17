# functions/data_processing.py

import numpy as np
import threading
import queue
import struct
import os
import time
import math
import collections
from scipy.fft import fft, fftfreq

# Impor konfigurasi terpusat
from config import FILENAME, SAMPLE_RATE, POLLING_INTERVAL

# --- Helper Functions --- #

def polar_to_cartesian(center_x, center_y, angle_deg, radius):
    """Konversi koordinat polar ke Cartesian."""
    angle_rad = math.radians(angle_deg)
    return center_x + radius * math.cos(angle_rad), center_y + radius * math.sin(angle_rad)

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

# --- Worker Thread Functions --- #

def fft_data_worker(result_queue: queue.Queue, stop_event: threading.Event):
    """
    Worker yang memantau file dan memproses FFT jika ada perubahan.
    Menggunakan konfigurasi dari config.py.
    """
    print(f"FFT worker started. Monitoring '{FILENAME}' for changes...")
    last_modified_time = 0

    while not stop_event.is_set():
        try:
            if not os.path.exists(FILENAME):
                result_queue.put({"status": "waiting", "message": f"Menunggu file '{os.path.basename(FILENAME)}'..."})
                time.sleep(1)
                continue

            current_mtime = os.path.getmtime(FILENAME)

            if current_mtime != last_modified_time:
                print(f"File '{os.path.basename(FILENAME)}' changed. Processing FFT...")
                last_modified_time = current_mtime
                result_queue.put({"status": "processing"})
                
                ch1_data, ch2_data, n_samples, sr = load_and_process_data(FILENAME, SAMPLE_RATE)

                if ch1_data is None or n_samples == 0:
                    result_queue.put({"status": "error", "message": f"Gagal memproses file."})
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
            
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f"Error in FFT worker loop: {e}")
            result_queue.put({"status": "error", "message": f"Error: {e}"})
            time.sleep(1)
    
    print("FFT worker thread stopped.")

def sinewave_data_worker(result_queue: queue.Queue, stop_event: threading.Event):
    """
    Worker yang memantau file dan mengirimkan data waveform mentah.
    Menggunakan konfigurasi dari config.py.
    """
    print(f"Sinewave worker started. Monitoring '{FILENAME}' for changes...")
    last_modified_time = 0

    while not stop_event.is_set():
        try:
            if not os.path.exists(FILENAME):
                time.sleep(1)
                continue

            current_mtime = os.path.getmtime(FILENAME)
            if current_mtime != last_modified_time:
                print(f"File '{os.path.basename(FILENAME)}' changed. Processing for Sinewave...")
                last_modified_time = current_mtime
                
                ch1_data, ch2_data, n_samples, sr = load_and_process_data(FILENAME, SAMPLE_RATE)

                if ch1_data is None or n_samples == 0:
                    continue
                
                time_axis = np.linspace(0, n_samples / sr, n_samples, endpoint=False)
                
                result_data = {
                    "status": "done",
                    "time_axis": time_axis,
                    "ch1_data": ch1_data,
                    "ch2_data": ch2_data
                }
                result_queue.put(result_data)
            
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f"Error in Sinewave worker loop: {e}")
            time.sleep(1)
    
    print("Sinewave worker thread stopped.")

def ppi_data_worker(data_queue: queue.Queue, stop_event: threading.Event):
    """
    Worker yang menghasilkan data untuk sapuan jarum dan target di PPI.
    """
    print("PPI worker thread started.")
    # Konfigurasi PPI (bisa juga dipindah ke config.py jika perlu)
    SWEEP_HISTORY_LENGTH = 20 
    TARGETS = [(140, 70), (75, 50)]

    current_angle, direction, last_time = 0, 1, time.time()
    sweep_history = collections.deque(maxlen=SWEEP_HISTORY_LENGTH)
    
    while not stop_event.is_set():
        current_time = time.time()
        delta_time, last_time = current_time - last_time, current_time
        current_angle += 90 * direction * delta_time

        if current_angle > 180:
            current_angle = 180
            direction = -1
        elif current_angle < 0:
            current_angle = 0
            direction = 1
            
        sweep_history.append(current_angle)
        data_to_send = {"angles": list(sweep_history), "targets": TARGETS}
        data_queue.put(data_to_send)
        time.sleep(0.016) # ~60 FPS update rate
        
    print("PPI worker thread stopped.")
