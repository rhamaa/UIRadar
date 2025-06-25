#include "ui/freq_analyzer.h"
#include "raygui.h"
#include <stdio.h> // Untuk snprintf

void draw_freq_analyzer(bool *show_window) {
    if (*show_window) {
        // Kunci UI di belakang agar tidak bisa diklik
        GuiLock();

        // Definisikan ukuran dan posisi jendela pop-up
        float screen_w = GetScreenWidth();
        float screen_h = GetScreenHeight();
        Rectangle window_box = { (screen_w - 400) / 2, (screen_h - 300) / 2, 400, 300 };

        // GuiWindowBox mengembalikan true jika tombol close TIDAK ditekan
        // Jadi kita balik logikanya untuk menutup jendela
        *show_window = GuiWindowBox(window_box, "Frequency Analyzer");

        // Konten Placeholder di dalam jendela
        Rectangle graph_area = { window_box.x + 10, window_box.y + 40, window_box.width - 20, 150 };
        DrawRectangleRec(graph_area, GetColor(GuiGetStyle(DEFAULT, BACKGROUND_COLOR)));
        DrawRectangleLinesEx(graph_area, 1, GetColor(GuiGetStyle(DEFAULT, LINE_COLOR)));
        DrawText("FFT Graph Placeholder", graph_area.x + 10, graph_area.y + 10, 20, GRAY);

        // Placeholder untuk data
        char freq_text[32], amp_text[32], phase_text[32];
        snprintf(freq_text, 32, "Frequency: 3.00 kHz");
        snprintf(amp_text, 32, "Amplitude: 0.85 V");
        snprintf(phase_text, 32, "Phase: 45.0 deg");

        DrawText(freq_text, window_box.x + 15, graph_area.y + graph_area.height + 15, 20, RAYWHITE);
        DrawText(amp_text, window_box.x + 15, graph_area.y + graph_area.height + 45, 20, RAYWHITE);
        DrawText(phase_text, window_box.x + 15, graph_area.y + graph_area.height + 75, 20, RAYWHITE);

        // Buka kunci UI setelah selesai
        GuiUnlock();
    }
}
