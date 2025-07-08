# UI/widgets/file.py
import dearpygui.dearpygui as dpg

def create_file_explorer_widget():
    """Membuat widget untuk File Explorer."""
    with dpg.group():
        dpg.add_text("File Explorer Placeholder")
        dpg.add_button(label="Open File")
        dpg.add_listbox(items=["file1.txt", "data.csv", "image.png"], num_items=5)