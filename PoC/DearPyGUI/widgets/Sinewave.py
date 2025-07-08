# UI/widgets/Sinewave.py
import dearpygui.dearpygui as dpg
import numpy as np
import threading
import queue
import struct
import os
import time

# --- Konfigurasi (Sama dengan FFT.py) ---
FILENAME = "./live_acquisition_ui.bin"
SAMPLE_RATE = 20_000_000
POLLING_INTERVAL = 0.2

# --- Fungsi Helper (Sama dengan FFT.py) ---

def load_and_process_data(filepath, sr):
    """Memuat data dari file biner, memisahkan channel, dan menghapus DC offset."""
    try:
        if not os.path.exists(filepath):
            return None, None, None, None
        with open(filepath, "rb") as f:
            data = f.read()
        if not data:
            return np.array([]), np.array([]), 0, sr
        values = np.array(struct.unpack(f"<{len(data)//2}H", data), dtype=np.float32)
        ch1 = values[::2]
        ch2 = values[1::2]
        ch1 -= np.mean(ch1)
        ch2 -= np.mean(ch2)
        return ch1, ch2, len(ch1), sr
    except Exception as e:
        print(f"Error reading or processing file in Sinewave worker: {e}")
        return None, None, None, None

# --- Fungsi Worker Thread (Logika Real-time) ---

def sinewave_data_worker(result_queue: queue.Queue, stop_event: threading.Event):
    """
    Worker yang secara terus-menerus memantau file dan mengirimkan data waveform.
    """
    print(f"Sinewave worker started. Monitoring '{FILENAME}' for changes...")
    last_modified_time = 0

    while not stop_event.is_set():
        try:
            if not os.path.exists(FILENAME):
                # Tidak perlu mengirim status 'waiting' karena FFT sudah melakukannya
                time.sleep(1)
                continue

            current_mtime = os.path.getmtime(FILENAME)
            if current_mtime != last_modified_time:
                print(f"File '{FILENAME}' changed. Processing for Sinewave plot...")
                last_modified_time = current_mtime
                
                ch1_data, ch2_data, n_samples, sr = load_and_process_data(FILENAME, SAMPLE_RATE)

                if ch1_data is None or n_samples == 0:
                    continue
                
                # Buat sumbu waktu (x-axis)
                time_axis = np.linspace(0, n_samples / sr, n_samples, endpoint=False)
                
                # Kirim data waveform (bukan FFT)
                result_data = {
                    "status": "done",
                    "time_axis": time_axis,
                    "ch1_data": ch1_data,
                    "ch2_data": ch2_data
                }
                result_queue.put(result_data)
                print("Sinewave worker sent waveform data.")
            
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f"Error in Sinewave worker loop: {e}")
            time.sleep(1)
    
    print("Sinewave worker thread stopped.")

# --- Fungsi Pembuat Widget UI ---

def create_sinewave_widget():
    """Membuat widget UI untuk menampilkan waveform."""
    with dpg.group():
        dpg.add_text("Live Waveform Display", tag="sinewave_status_text")
        
        with dpg.plot(label="Time-Domain Waveform", height=-1, width=-1, tag="sinewave_plot"):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="sinewave_xaxis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude", tag="sinewave_yaxis")
            dpg.add_line_series([], [], label="CH1 (odd)", parent="sinewave_yaxis", tag="sinewave_ch1_series")
            dpg.add_line_series([], [], label="CH2 (even)", parent="sinewave_yaxis", tag="sinewave_ch2_series")