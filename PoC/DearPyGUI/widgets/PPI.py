# widgets/PPI.py

import dearpygui.dearpygui as dpg
import numpy as np
import math

# Impor helper dari lokasi baru
from functions.data_processing import polar_to_cartesian

# --- Helper Khusus UI --- #

def generate_arc_points(center, radius, start_deg, end_deg, segments=100):
    """Menghasilkan titik-titik untuk menggambar busur."""
    points = []
    start_rad, end_rad = math.radians(start_deg), math.radians(end_deg)
    for i in range(segments + 1):
        angle = start_rad + (end_rad - start_rad) * i / segments
        points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    return points

# --- Fungsi Pembuat Widget UI --- #

def create_ppi_widget(colors: dict):
    """
    Membuat widget PPI menggunakan palet warna yang sudah ditentukan.
    Fungsi ini sekarang hanya fokus pada penggambaran elemen statis.
    """
    # Konfigurasi tampilan PPI (bisa dipindah ke config.py jika lebih kompleks)
    MAX_RADIUS = 100
    RANGE_RINGS = 4
    AZIMUTH_LABELS = [0, 30, 60, 90, 120, 150, 180]

    with dpg.plot(tag="ppi_plot", no_title=True, no_mouse_pos=True, height=-1, width=-1, equal_aspects=True):
        dpg.add_plot_axis(dpg.mvXAxis, no_gridlines=True, no_tick_marks=True, no_tick_labels=True, tag="ppi_xaxis")
        dpg.set_axis_limits("ppi_xaxis", -MAX_RADIUS - 10, MAX_RADIUS + 10)
        
        dpg.add_plot_axis(dpg.mvYAxis, no_gridlines=True, no_tick_marks=True, no_tick_labels=True, tag="ppi_yaxis")
        dpg.set_axis_limits("ppi_yaxis", -10, MAX_RADIUS + 10)

        center = (0, 0)
        
        # Gambar latar belakang area scan
        background_points = generate_arc_points(center, MAX_RADIUS, 0, 180)
        dpg.draw_polygon(points=[center] + background_points, color=(0,0,0,0), fill=colors["scan_area"])

        # Gambar cincin jarak (range rings)
        ring_radii = np.linspace(0, MAX_RADIUS, RANGE_RINGS + 1)[1:]
        for r in ring_radii:
            ring_points = generate_arc_points(center, r, 0, 180)
            dpg.draw_polyline(ring_points, color=colors["grid_lines"], thickness=1)

        # Gambar label sudut (azimuth)
        for angle in AZIMUTH_LABELS:
            pos = polar_to_cartesian(center[0], center[1], angle, MAX_RADIUS + 5)
            dpg.draw_text(pos, f"{angle}", color=colors["text"], size=10)

        # Siapkan layer untuk gambar dinamis (sapuan jarum dan target)
        dpg.add_draw_layer(tag="ppi_dynamic_layer")