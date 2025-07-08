# UI/widgets/PPE.py
import dearpygui.dearpygui as dpg
import numpy as np
import threading
import time
import queue

# Worker function untuk simulasi update data PPI
def ppe_data_worker(data_queue: queue.Queue, stop_event: threading.Event):
    """Fungsi ini berjalan di thread terpisah untuk menghasilkan data PPI."""
    print("PPE worker thread started.")
    # Data polar (radius, theta)
    r = np.linspace(0, 10, 100)
    
    while not stop_event.is_set():
        try:
            # Simulasi data baru yang berputar
            theta = (time.time() * 0.5) % (2 * np.pi)
            x_data = r * np.cos(theta)
            y_data = r * np.sin(theta)

            # Masukkan data ke queue
            data_queue.put((x_data, y_data))
            time.sleep(0.05)  # Update ~20 kali per detik
        except Exception as e:
            print(f"Error in PPE worker: {e}")
            break
    print("PPE worker thread stopped.")

def create_ppe_widget():
    """Membuat widget untuk PPI Desktop."""
    with dpg.group():
        # Setup plot untuk PPI
        with dpg.plot(label="PPI Display", height=-1, width=-1):
            dpg.add_plot_legend()
            # Sumbu X dan Y dibuat sama untuk tampilan lingkaran yang benar
            dpg.add_plot_axis(dpg.mvXAxis, label="X", tag="ppi_xaxis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Y", tag="ppi_yaxis")
            dpg.set_axis_limits("ppi_xaxis", -12, 12)
            dpg.set_axis_limits("ppi_yaxis", -12, 12)
            
            # Data series yang akan diupdate
            dpg.add_line_series([], [], label="Radar Scan", parent="ppi_yaxis", tag="ppi_series")