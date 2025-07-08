# UI/main.py
import dearpygui.dearpygui as dpg
import threading
import queue
import time
import numpy as np
import math

# Impor fungsi pembuat widget
from widgets.PPI import create_ppi_widget, ppi_data_worker, polar_to_cartesian
from widgets.FFT import create_fft_widget, fft_data_worker
from widgets.Sinewave import create_sinewave_widget, sinewave_data_worker
from widgets.file import create_file_explorer_widget
from widgets.controller import create_controller_widget

APP_SPACING = 8
APP_PADDING = 8

# BARU: Definisikan palet warna yang konsisten dan cocok dengan tema DPG
THEME_COLORS = {
    "background": (21, 21, 21, 255),      # Latar belakang yang sangat gelap
    "scan_area": (37, 37, 38, 150),       # Area scan yang sedikit transparan
    "grid_lines": (255, 255, 255, 40),    # Garis putih yang sangat pudar
    "text": (255, 255, 255, 150),         # Teks putih yang tidak terlalu mencolok
    "accent": (0, 200, 119, 255),         # Warna hijau/teal untuk sapuan jarum
    "target": (255, 0, 0, 255),           # Merah terang untuk target
}

# --- Setup Threading ---
ppi_queue = queue.Queue()
fft_result_queue = queue.Queue()
sinewave_result_queue = queue.Queue()
stop_event = threading.Event()
threads = []

def update_ui_from_queues():
    """Memeriksa semua queue dan mengupdate UI jika ada data baru."""
    
    # DIUBAH: Logika update untuk PPI sekarang menggunakan palet warna yang sudah didefinisikan
    try:
        ppi_data = ppi_queue.get_nowait()
        dpg.delete_item("ppi_dynamic_layer", children_only=True)

        accent_color = THEME_COLORS["accent"]
        
        angles_history = ppi_data["angles"]
        history_len = len(angles_history)
        for i, angle in enumerate(angles_history):
            alpha = int(255 * ((i + 1) / history_len))
            faded_color = (*accent_color[:3], alpha)
            p0 = (0, 0)
            p1 = polar_to_cartesian(0, 0, angle - 0.5, 100)
            p2 = polar_to_cartesian(0, 0, angle + 0.5, 100)
            dpg.draw_polygon(points=[p0, p1, p2], color=faded_color, fill=faded_color, parent="ppi_dynamic_layer")
        
        for angle, radius in ppi_data["targets"]:
            target_pos = polar_to_cartesian(0, 0, angle, radius)
            dpg.draw_circle(center=target_pos, radius=2, color=THEME_COLORS["target"], fill=THEME_COLORS["target"], parent="ppi_dynamic_layer")

    except queue.Empty: pass

    # ... Sisa fungsi tidak berubah ...
    try:
        result = fft_result_queue.get_nowait()
        # ...
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
            dpg.configure_item("fft_plot", label=plot_label); dpg.set_axis_limits_auto("fft_yaxis")
    except queue.Empty: pass
    try:
        result = sinewave_result_queue.get_nowait()
        if result.get("status") == "done":
            dpg.set_value("sinewave_status_text", f"Waveform updated at: {time.strftime('%H:%M:%S')}")
            dpg.set_value("sinewave_ch1_series", [result["time_axis"].tolist(), result["ch1_data"].tolist()])
            dpg.set_value("sinewave_ch2_series", [result["time_axis"].tolist(), result["ch2_data"].tolist()])
            dpg.set_axis_limits_auto("sinewave_xaxis"); dpg.set_axis_limits_auto("sinewave_yaxis")
    except queue.Empty: pass

def cleanup_and_exit():
    print("Stopping worker threads..."); stop_event.set(); time.sleep(0.5)
    for t in threads: t.join()
    print("All threads stopped. Destroying context."); dpg.destroy_context()

dpg.create_context()
def exit_on_esc(): dpg.stop_dearpygui()
with dpg.handler_registry(): dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=exit_on_esc)
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, APP_PADDING, APP_PADDING)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, APP_SPACING, APP_SPACING)
        # BARU: Atur warna plot background untuk semua plot agar konsisten
        dpg.add_theme_color(dpg.mvPlotCol_PlotBg, THEME_COLORS["background"])
dpg.bind_theme(global_theme)

with dpg.window(tag="Primary Window"):
    with dpg.group(horizontal=True):
        with dpg.group(tag="left_column"):
            with dpg.child_window(label="PPI Desktop", tag="ppi_window", no_scrollbar=True):
                # DIUBAH: Kirim palet warna ke widget PPI
                create_ppi_widget(colors=THEME_COLORS)
            with dpg.child_window(label="FFT Desktop", tag="fft_window"): create_fft_widget()
        with dpg.group(tag="right_column"):
            with dpg.child_window(label="File Explorer", tag="file_explorer_window"): create_file_explorer_widget()
            with dpg.child_window(label="Sinewave", tag="sinewave_window"): create_sinewave_widget()
            with dpg.child_window(label="Controller", tag="controller_window"): create_controller_widget()

def resize_callback():
    # ... fungsi ini tidak berubah
    if not dpg.is_dearpygui_running(): return
    viewport_width=dpg.get_viewport_width(); viewport_height=dpg.get_viewport_height()
    spacing=APP_SPACING; left_width=int(viewport_width * 0.7)
    dpg.set_item_width("left_column", left_width); dpg.set_item_width("right_column", -1)
    available_height = viewport_height - (APP_PADDING * 2)
    left_col_height=available_height-spacing; right_col_height=available_height-(spacing * 2)
    dpg.set_item_height("ppi_window", int(left_col_height * 0.6))
    dpg.set_item_height("fft_window", int(left_col_height * 0.4))
    dpg.set_item_height("file_explorer_window", int(right_col_height * 0.35))
    dpg.set_item_height("sinewave_window", int(right_col_height * 0.35))
    dpg.set_item_height("controller_window", int(right_col_height * 0.30))

dpg.create_viewport(title='Real-time PPI Display & Analyzer', width=1280, height=720)
dpg.setup_dearpygui(); dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.set_viewport_resize_callback(resize_callback)
dpg.toggle_viewport_fullscreen(); resize_callback()
threads.append(threading.Thread(target=ppi_data_worker, args=(ppi_queue, stop_event), daemon=True))
threads.append(threading.Thread(target=fft_data_worker, args=(fft_result_queue, stop_event), daemon=True))
threads.append(threading.Thread(target=sinewave_data_worker, args=(sinewave_result_queue, stop_event), daemon=True))
for t in threads: t.start()
while dpg.is_dearpygui_running(): update_ui_from_queues(); dpg.render_dearpygui_frame()
cleanup_and_exit()