# widgets/Sinewave.py

import dearpygui.dearpygui as dpg

# --- Fungsi Pembuat Widget UI --- #

def create_sinewave_widget():
    """Membuat widget UI untuk menampilkan waveform mentah."""
    with dpg.group():
        dpg.add_text("Live Waveform Display", tag="sinewave_status_text")
        
        with dpg.plot(label="Time-Domain Waveform", height=-1, width=-1, tag="sinewave_plot"):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="sinewave_xaxis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude", tag="sinewave_yaxis")
            dpg.add_line_series([], [], label="CH1 (odd)", parent="sinewave_yaxis", tag="sinewave_ch1_series")
            dpg.add_line_series([], [], label="CH2 (even)", parent="sinewave_yaxis", tag="sinewave_ch2_series")