#include <raylib.h>
#define RAYGUI_IMPLEMENTATION
#include <raygui.h>

// Include the UI modules and the new ADC dummy function
#include "function/adlink_adc_dumy.h"

// Include the terminal style header
#include "styles/terminal/style_terminal.h"
#include "ui/wave_display.h"
#include "ui/ppi_display.h"
#include "ui/ppi_speed_slider.h"
#include "ui/wave_controls.h"
#include "ui/datetime_display.h"
#include "ui/freq_analyzer.h"
#include <stdbool.h>
#include <stddef.h>
#include <math.h>

#define ADC_SAMPLES 500 // Definisikan sebagai konstanta preprocessor

int main() {
    // Inisialisasi jendela Raylib

    // Inisialisasi window dalam mode layar penuh
    const int screenWidth = GetMonitorWidth(0);
    const int screenHeight = GetMonitorHeight(0);
    InitWindow(screenWidth, screenHeight, "UI Radar with ADC Data");
    ToggleFullscreen();
    GuiLoadStyleTerminal(); // Load the terminal style
    SetTargetFPS(60);

    // Inisialisasi variabel
    unsigned short adcBuffer[ADC_SAMPLES] = {0};
    float ppi_speed = 1.0f;
    bool is_wave_paused = false;
    bool show_freq_analyzer = false;

    while (!WindowShouldClose()) {
        // Hanya baca data ADC baru jika tidak sedang di-pause
        if (!is_wave_paused) {
            for (int i = 0; i < ADC_SAMPLES; i++) {
                adcBuffer[i] = get_dummy_adc_sample();
            }
        }

        // Tentukan tata letak UI baru berdasarkan sketsa
        float screen_w = GetScreenWidth();
        float screen_h = GetScreenHeight();
        float padding = 10.0f;

        // Panel Atas untuk PPI
        float ppi_panel_h = screen_h * 0.65f;
        Rectangle ppiRect = { padding, padding, screen_w - (2 * padding), ppi_panel_h };

        // Panel Bawah untuk semua kontrol
        float bottom_panel_y = ppi_panel_h + (2 * padding);
        float bottom_panel_h = screen_h - bottom_panel_y - padding;

        // Definisikan kolom-kolom di panel bawah
        float datetime_panel_w = 150.0f;
        float controls_panel_w = 180.0f;
        float wave_panel_w = screen_w - datetime_panel_w - controls_panel_w - (4 * padding);

        Rectangle datetimeRect = { padding, bottom_panel_y, datetime_panel_w, bottom_panel_h };
        Rectangle waveRect = { datetimeRect.x + datetime_panel_w + padding, bottom_panel_y, wave_panel_w, bottom_panel_h };
        
        // Kolom paling kanan dibagi dua secara vertikal untuk tombol dan slider
        float controls_panel_h = bottom_panel_h * 0.6f;
        float slider_panel_h = bottom_panel_h - controls_panel_h - padding;
        
        Rectangle controlsRect = { waveRect.x + wave_panel_w + padding, bottom_panel_y, controls_panel_w, controls_panel_h };
        Rectangle sliderRect = { waveRect.x + wave_panel_w + padding, controlsRect.y + controls_panel_h + padding, controls_panel_w, slider_panel_h };

        BeginDrawing();
        ClearBackground(BLACK);

        // Gambar semua panel UI
        draw_ppi_display(ppiRect, ppi_speed);
        draw_datetime_display(datetimeRect);
        draw_wave_display(waveRect, adcBuffer, ADC_SAMPLES);
        draw_wave_controls(controlsRect, &is_wave_paused, &show_freq_analyzer);
        draw_ppi_speed_slider(sliderRect, &ppi_speed);

        // Gambar jendela pop-up jika diperlukan (akan mengunci UI lain)
        draw_freq_analyzer(&show_freq_analyzer);

        EndDrawing();
    }

    CloseWindow();
    return 0;
}