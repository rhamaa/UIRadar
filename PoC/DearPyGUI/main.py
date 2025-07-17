# main.py

import dearpygui.dearpygui as dpg
import threading
import queue
import time

# --- Impor dari file lokal --- #

# Impor konfigurasi terpusat
from config import APP_SPACING, APP_PADDING, THEME_COLORS

# Impor fungsi pembuat widget UI (hanya UI)
from widgets.PPI import create_ppi_widget
from widgets.FFT import create_fft_widget
from widgets.Sinewave import create_sinewave_widget
from widgets.file import create_file_explorer_widget
from widgets.controller import create_controller_widget

# Impor fungsi worker thread (hanya logika)
from functions.data_processing import ppi_data_worker, fft_data_worker, sinewave_data_worker, polar_to_cartesian

# --- Pengaturan Aplikasi --- #

# Setup antrian (queue) untuk komunikasi antar thread
ppi_queue = queue.Queue()
fft_result_queue = queue.Queue()
sinewave_result_queue = queue.Queue()

# Event untuk memberi sinyal berhenti ke semua thread
stop_event = threading.Event()
threads = []

# --- Fungsi Inti --- #

def update_ui_from_queues():
    """Memeriksa semua queue pada setiap frame dan mengupdate UI jika ada data baru."""
    # Update PPI (sapuan jarum & target)
    try:
        ppi_data = ppi_queue.get_nowait()
        dpg.delete_item("ppi_dynamic_layer", children_only=True)

        accent_color = THEME_COLORS["accent"]
        
        # Gambar jejak pudar (persistence)
        angles_history = ppi_data["angles"]
        history_len = len(angles_history)
        for i, angle in enumerate(angles_history):
            alpha = int(255 * ((i + 1) / history_len))
            faded_color = (*accent_color[:3], alpha)
            p0 = (0, 0)
            p1 = polar_to_cartesian(0, 0, angle - 0.5, 100)
            p2 = polar_to_cartesian(0, 0, angle + 0.5, 100)
            dpg.draw_polygon(points=[p0, p1, p2], color=faded_color, fill=faded_color, parent="ppi_dynamic_layer")
        
        # Gambar target
        for angle, radius in ppi_data["targets"]:
            target_pos = polar_to_cartesian(0, 0, angle, radius)
            dpg.draw_circle(center=target_pos, radius=2, color=THEME_COLORS["target"], fill=THEME_COLORS["target"], parent="ppi_dynamic_layer")

    except queue.Empty:
        pass # Tidak ada data baru, lanjutkan

    # Update plot FFT
    try:
        result = fft_result_queue.get_nowait()
        status = result.get("status")
        
        if status == "processing":
            dpg.set_value("fft_status_text", "File changed, processing...")
        elif status in ["error", "waiting"]:
            dpg.set_value("fft_status_text", result.get("message"))
        elif status == "done":
            update_time = time.strftime('%H:%M:%S')
            dpg.set_value("fft_status_text", f"Plot updated at: {update_time}")
            dpg.set_value("fft_ch1_series", [result["freqs_ch1"].tolist(), result["mag_ch1"].tolist()])
            dpg.set_value("fft_ch2_series", [result["freqs_ch2"].tolist(), result["mag_ch2"].tolist()])
            
            sr = result["sample_rate"]
            n_samples = result["n_samples"]
            freq_res = sr / n_samples if n_samples > 0 else 0
            plot_label = f'Live FFT Spectrum\nSR: {sr/1e6:.2f}MHz, N: {n_samples}, Res: {freq_res:.1f}Hz'
            dpg.configure_item("fft_plot", label=plot_label)
            dpg.set_axis_limits_auto("fft_yaxis")

    except queue.Empty:
        pass

    # Update plot Sinewave
    try:
        result = sinewave_result_queue.get_nowait()
        if result.get("status") == "done":
            dpg.set_value("sinewave_status_text", f"Waveform updated at: {time.strftime('%H:%M:%S')}")
            dpg.set_value("sinewave_ch1_series", [result["time_axis"].tolist(), result["ch1_data"].tolist()])
            dpg.set_value("sinewave_ch2_series", [result["time_axis"].tolist(), result["ch2_data"].tolist()])
            dpg.set_axis_limits_auto("sinewave_xaxis")
            dpg.set_axis_limits_auto("sinewave_yaxis")
    except queue.Empty:
        pass

def cleanup_and_exit():
    """Memberhentikan thread worker dengan aman dan menutup Dear PyGui."""
    print("Stopping worker threads...")
    stop_event.set()
    time.sleep(0.5) # Beri waktu agar thread bisa berhenti
    for t in threads:
        t.join()
    print("All threads stopped. Destroying context.")
    dpg.destroy_context()

# --- Pengaturan UI (Layout dan Tema) --- #

dpg.create_context()

# Atur callback untuk keluar dengan tombol Esc
def exit_on_esc():
    dpg.stop_dearpygui()

with dpg.handler_registry():
    dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=exit_on_esc)

# Definisikan tema global untuk konsistensi
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, APP_PADDING, APP_PADDING)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, APP_SPACING, APP_SPACING)
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, THEME_COLORS["background"])
dpg.bind_theme(global_theme)

# Buat layout utama window
with dpg.window(tag="Primary Window"):
    with dpg.group(horizontal=True):
        # Kolom kiri (70% lebar)
        with dpg.group(tag="left_column"):
            with dpg.child_window(label="PPI Desktop", tag="ppi_window", no_scrollbar=True):
                create_ppi_widget(colors=THEME_COLORS)
            with dpg.child_window(label="FFT Desktop", tag="fft_window"):
                create_fft_widget()
        # Kolom kanan (sisa lebar)
        with dpg.group(tag="right_column"):
            with dpg.child_window(label="File Explorer", tag="file_explorer_window"):
                create_file_explorer_widget()
            with dpg.child_window(label="Sinewave", tag="sinewave_window"):
                create_sinewave_widget()
            with dpg.child_window(label="Controller", tag="controller_window"):
                create_controller_widget()

# Callback untuk menyesuaikan ukuran layout saat window di-resize
def resize_callback():
    if not dpg.is_dearpygui_running():
        return
    
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()
    
    spacing = APP_SPACING
    left_width = int(viewport_width * 0.7)
    
    dpg.set_item_width("left_column", left_width)
    dpg.set_item_width("right_column", -1)
    
    available_height = viewport_height - (APP_PADDING * 2)
    left_col_height = available_height - spacing
    right_col_height = available_height - (spacing * 2)
    
    dpg.set_item_height("ppi_window", int(left_col_height * 0.6))
    dpg.set_item_height("fft_window", int(left_col_height * 0.4))
    dpg.set_item_height("file_explorer_window", int(right_col_height * 0.35))
    dpg.set_item_height("sinewave_window", int(right_col_height * 0.35))
    dpg.set_item_height("controller_window", int(right_col_height * 0.30))

# --- Inisialisasi dan Loop Utama --- #

dpg.create_viewport(title='Real-time Radar UI & Spectrum Analyzer', width=1280, height=720)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.set_viewport_resize_callback(resize_callback)

# Mulai dalam mode fullscreen dan panggil resize sekali untuk mengatur layout awal
dpg.toggle_viewport_fullscreen()
resize_callback()

# Buat dan mulai semua worker thread
threads.append(threading.Thread(target=ppi_data_worker, args=(ppi_queue, stop_event), daemon=True))
threads.append(threading.Thread(target=fft_data_worker, args=(fft_result_queue, stop_event), daemon=True))
threads.append(threading.Thread(target=sinewave_data_worker, args=(sinewave_result_queue, stop_event), daemon=True))

for t in threads:
    t.start()

# Loop render utama Dear PyGui
while dpg.is_dearpygui_running():
    update_ui_from_queues() # Ambil data dari worker
    dpg.render_dearpygui_frame() # Gambar frame baru

# Cleanup setelah loop selesai
cleanup_and_exit()