#include "ui/wave_controls.h"
#include "raygui.h"

void draw_wave_controls(Rectangle area, bool *is_paused, bool *show_freq_analyzer) {
    // Gambar latar belakang panel kontrol
    DrawRectangleRec(area, Fade(BLACK, 0.5f));
    DrawRectangleLinesEx(area, 2, GRAY);

    // Tentukan layout tombol di dalam area secara vertikal
    float button_height = (area.height - 15) / 2;
    Rectangle freq_button_rect = { area.x + 5, area.y + 5, area.width - 10, button_height };
    Rectangle pause_button_rect = { area.x + 5, area.y + 10 + button_height, area.width - 10, button_height };

    // Tombol Frekuensi untuk membuka pop-up
    if (GuiButton(freq_button_rect, "Realtime Frekuensi")) {
        *show_freq_analyzer = true;
    }

    // Tombol Pause/Resume
    if (GuiButton(pause_button_rect, *is_paused ? "Resume" : "Pause")) {
        *is_paused = !(*is_paused);
    }
}
