# UI/widgets/controller.py
import dearpygui.dearpygui as dpg

def create_controller_widget():
    """Membuat widget untuk Controller."""
    with dpg.group():
        dpg.add_text("System Controls")
        dpg.add_button(label="Start", width=-1)
        dpg.add_button(label="Stop", width=-1)
        dpg.add_separator()
        dpg.add_slider_float(label="Gain", default_value=1.0, max_value=10.0)
        dpg.add_input_text(label="IP Address", default_value="127.0.0.1")