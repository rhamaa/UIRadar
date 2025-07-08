# UI/main.py
import dearpygui.dearpygui as dpg
import threading
import queue
import time
import numpy as np

# Impor fungsi pembuat widget
from widgets.PPE import create_ppe_widget, ppe_data_worker
from widgets.FFT import create_fft_widget, fft_data_worker
from widgets.Sinewave import create_sinewave_widget, sinewave_data_worker
from widgets.file import create_file_explorer_widget
from widgets.controller import create_controller_widget

APP_SPACING = 8
APP_PADDING = 8

# --- Setup Threading ---
ppe_queue = queue.Queue()
fft_result_queue = queue.Queue()
# BARU: Queue terpisah untuk hasil sinewave
sinewave_result_queue = queue.Queue()

stop_event = threading.Event()
threads = []

def update_ui_from_queues():
    """Memeriksa semua queue dan mengupdate UI jika ada data baru."""
    # --- Update PPE ---
    try:
        x_data, y_data = ppe_queue.get_nowait(); dpg.set_value('ppi_series', [x_data, y_data])
    except queue.Empty: pass

    # --- Update FFT ---
    try:
        result = fft_result_queue.get_nowait()
        status = result.get("status")
        if status == "processing": dpg.set_value("fft_status_text", "File changed, processing...")
        elif status in ["error", "waiting"]: dpg.set_value("fft_status_text", result.get("message"))
        elif status == "done":
            update_time = time.strftime('%H:%M:%S'); dpg.set_value("fft_status_text", f"Plot updated at: {update_time}")
            dpg.set_value("fft_ch1_series", [result["freqs_ch1"].tolist(), result["mag_ch1"].tolist()])
            dpg.set_value("fft_ch2_series", [result["freqs_ch2"].tolist(), result["mag_ch2"].tolist()])
            sr = result["sample_rate"]; n_samples = result["n_samples"]
            freq_res = sr / n_samples if n_samples > 0 else 0
            plot_label = f'Live FFT Spectrum\nSR: {sr/1e6:.2f}MHz, N: {n_samples}, Res: {freq_res:.1f}Hz'
            dpg.configure_item("fft_plot", label=plot_label)
            dpg.set_axis_limits_auto("fft_yaxis")
    except queue.Empty: pass

    # BARU: Update Sinewave dari queue-nya sendiri
    try:
        result = sinewave_result_queue.get_nowait()
        status = result.get("status")
        if status == "done":
            dpg.set_value("sinewave_status_text", f"Waveform updated at: {time.strftime('%H:%M:%S')}")
            # Update data series dengan data waktu vs. amplitudo
            dpg.set_value("sinewave_ch1_series", [result["time_axis"].tolist(), result["ch1_data"].tolist()])
            dpg.set_value("sinewave_ch2_series", [result["time_axis"].tolist(), result["ch2_data"].tolist()])
            # Atur batas sumbu secara otomatis agar waveform terlihat jelas
            dpg.set_axis_limits_auto("sinewave_xaxis")
            dpg.set_axis_limits_auto("sinewave_yaxis")
    except queue.Empty: pass


def cleanup_and_exit():
    # ... (fungsi ini tidak berubah)
    print("Stopping worker threads...")
    stop_event.set()
    time.sleep(0.5)
    for t in threads:
        t.join()
    print("All threads stopped. Destroying context.")
    dpg.destroy_context()

# --- Konteks dan Layout (Tidak Berubah) ---
dpg.create_context()
def exit_on_esc(): dpg.stop_dearpygui()
with dpg.handler_registry(): dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=exit_on_esc)
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, APP_PADDING, APP_PADDING)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, APP_SPACING, APP_SPACING)
dpg.bind_theme(global_theme)
with dpg.window(tag="Primary Window"):
    with dpg.group(horizontal=True):
        with dpg.group(tag="left_column"):
            with dpg.child_window(label="PPI Desktop", tag="ppi_window"): create_ppe_widget()
            with dpg.child_window(label="FFT Desktop", tag="fft_window"): create_fft_widget()
        with dpg.group(tag="right_column"):
            with dpg.child_window(label="File Explorer", tag="file_explorer_window"): create_file_explorer_widget()
            with dpg.child_window(label="Sinewave", tag="sinewave_window"): create_sinewave_widget()
            with dpg.child_window(label="Controller", tag="controller_window"): create_controller_widget()

def resize_callback():
    # ... (fungsi ini tidak berubah)
    if not dpg.is_dearpygui_running(): return
    viewport_width = dpg.get_viewport_width(); viewport_height = dpg.get_viewport_height()
    spacing = APP_SPACING; left_width = int(viewport_width * 0.7)
    dpg.set_item_width("left_column", left_width); dpg.set_item_width("right_column", -1)
    available_height = viewport_height - (APP_PADDING * 2)
    left_col_height = available_height - spacing; right_col_height = available_height - (spacing * 2)
    dpg.set_item_height("ppi_window", int(left_col_height * 0.6))
    dpg.set_item_height("fft_window", int(left_col_height * 0.4))
    dpg.set_item_height("file_explorer_window", int(right_col_height * 0.35))
    dpg.set_item_height("sinewave_window", int(right_col_height * 0.35))
    dpg.set_item_height("controller_window", int(right_col_height * 0.30))

# --- Setup Viewport dan Jalankan Aplikasi ---
dpg.create_viewport(title='Real-time Spectrum & Waveform Analyzer', width=1280, height=720)
dpg.setup_dearpygui(); dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.set_viewport_resize_callback(resize_callback)
dpg.toggle_viewport_fullscreen(); resize_callback()

# --- Start Worker Threads ---
threads.append(threading.Thread(target=ppe_data_worker, args=(ppe_queue, stop_event), daemon=True))
threads.append(threading.Thread(target=fft_data_worker, args=(fft_result_queue, stop_event), daemon=True))
# PERHATIKAN PERUBAHAN DI SINI
threads.append(threading.Thread(target=sinewave_data_worker, args=(sinewave_result_queue, stop_event), daemon=True))

for t in threads: t.start()

# --- Render Loop Utama ---
while dpg.is_dearpygui_running():
    update_ui_from_queues()
    dpg.render_dearpygui_frame()

cleanup_and_exit()