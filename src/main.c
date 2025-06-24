#include <raylib.h>
#define RAYGUI_IMPLEMENTATION
#include <raygui.h>
#include "function/sinus.h"
#include "ui/wave_display.h"
#include "ui/ppi_display.h"
#include "ui/ppi_speed_slider.h"
#include <stddef.h>
#include <math.h>

int main() {
    // Inisialisasi jendela Raylib

    // Layout constants
    const int screenWidth = 1000;
    const int screenHeight = 600;
    InitWindow(screenWidth, screenHeight, "UI Radar Layout Modular");
    SetTargetFPS(60);

    // Data untuk sinus
    #define SIN_WAVE_SAMPLES 400
    float waveBuffer[SIN_WAVE_SAMPLES];
    float amplitude = 80.0f;
    float freq = 2.0f;
    float phase = 0.0f;
    float sample_rate = 400.0f;
    float ppi_speed = 1.0f;

    while (!WindowShouldClose()) {
        // Update sinus (dummy: freq mengikuti ppi_speed)
        freq = 0.5f + 2.0f * ppi_speed; // contoh keterkaitan speed
        generate_sinus(waveBuffer, SIN_WAVE_SAMPLES, amplitude, freq, phase, sample_rate);

        // Layout rectangle
        Rectangle ppiRect = {30, 30, 540, 500};
        Rectangle waveRect = {600, 30, 350, 220};
        Rectangle sliderRect = {600, 280, 350, 160};

        BeginDrawing();
        ClearBackground(RAYWHITE);

        // Draw UI panels
        draw_ppi_display(ppiRect, ppi_speed);
        draw_wave_display(waveRect, waveBuffer, SIN_WAVE_SAMPLES);
        draw_ppi_speed_slider(sliderRect, &ppi_speed);

        EndDrawing();
    }

    CloseWindow();
    return 0;


    CloseWindow();

    return 0;
}