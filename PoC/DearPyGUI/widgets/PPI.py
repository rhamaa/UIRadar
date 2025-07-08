# UI/widgets/PPI.py
import dearpygui.dearpygui as dpg
import numpy as np
import threading
import queue
import time
import math
import collections

# --- Konfigurasi ---
MAX_RADIUS = 100
RANGE_RINGS = 4
AZIMUTH_LABELS = [0, 30, 60, 90, 120, 150, 180]
SWEEP_HISTORY_LENGTH = 20
TARGETS = [(140, 70), (75, 50)]

# --- Helper ---
def polar_to_cartesian(center_x, center_y, angle_deg, radius):
    angle_rad = math.radians(angle_deg)
    return center_x + radius * math.cos(angle_rad), center_y + radius * math.sin(angle_rad)

def generate_arc_points(center, radius, start_deg, end_deg, segments=100):
    points = []
    start_rad, end_rad = math.radians(start_deg), math.radians(end_deg)
    for i in range(segments + 1):
        angle = start_rad + (end_rad - start_rad) * i / segments
        points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    return points

# --- Worker Thread (Tidak Berubah) ---
def ppi_data_worker(data_queue: queue.Queue, stop_event: threading.Event):
    print("PPI worker thread started (thematically aware).")
    current_angle, direction, last_time = 0, 1, time.time()
    sweep_history = collections.deque(maxlen=SWEEP_HISTORY_LENGTH)
    while not stop_event.is_set():
        current_time = time.time()
        delta_time, last_time = current_time - last_time, current_time
        current_angle += 90 * direction * delta_time
        # Perbaikan logika arah sapuan
        if current_angle > 180:
            current_angle = 180
            direction = -1
        elif current_angle < 0:
            current_angle = 0
            direction = 1 # Kembali ke kanan
        sweep_history.append(current_angle)
        data_to_send = {"angles": list(sweep_history), "targets": TARGETS}
        data_queue.put(data_to_send)
        time.sleep(0.016)
    print("PPI worker thread stopped.")

# --- Fungsi Pembuat Widget UI (DIUBAH) ---
def create_ppi_widget(colors: dict):
    """
    Membuat widget PPI menggunakan palet warna yang sudah ditentukan.
    """
    with dpg.plot(tag="ppi_plot", no_title=True, no_mouse_pos=True, height=-1, width=-1, equal_aspects=True):
        dpg.add_plot_axis(dpg.mvXAxis, no_gridlines=True, no_tick_marks=True, no_tick_labels=True, tag="ppi_xaxis")
        dpg.set_axis_limits("ppi_xaxis", -MAX_RADIUS - 10, MAX_RADIUS + 10)
        
        dpg.add_plot_axis(dpg.mvYAxis, no_gridlines=True, no_tick_marks=True, no_tick_labels=True, tag="ppi_yaxis")
        # DIUBAH: Gunakan tag yang benar "ppi_yaxis" bukan "yaxis"
        dpg.set_axis_limits("ppi_yaxis", -10, MAX_RADIUS + 10)

        center = (0, 0)
        
        background_points = generate_arc_points(center, MAX_RADIUS, 0, 180)
        dpg.draw_polygon(points=[center] + background_points, color=(0,0,0,0), fill=colors["scan_area"])

        ring_radii = np.linspace(0, MAX_RADIUS, RANGE_RINGS + 1)[1:]
        for r in ring_radii:
            ring_points = generate_arc_points(center, r, 0, 180)
            dpg.draw_polyline(ring_points, color=colors["grid_lines"], thickness=1)

        for angle in AZIMUTH_LABELS:
            pos = polar_to_cartesian(center[0], center[1], angle, MAX_RADIUS + 5)
            dpg.draw_text(pos, f"{angle}", color=colors["text"], size=10)

        dpg.add_draw_layer(tag="ppi_dynamic_layer")