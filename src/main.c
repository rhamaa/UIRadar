#include <raylib.h>
#define RAYGUI_IMPLEMENTATION
#include <raygui.h>
#include "function/adlink_adc_dumy.h"
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

    // Data untuk ADC
    const int ADC_SAMPLES = 500;
    unsigned short adcBuffer[ADC_SAMPLES];

    // PPI parameters
    float ppi_speed = 1.0f;

    while (!WindowShouldClose()) {
        // Update ADC (dummy: isi buffer dengan ADC samples)
        for (int i = 0; i < ADC_SAMPLES; i++) {
            adcBuffer[i] = get_dummy_adc_sample();
        }

        // Layout rectangle
        Rectangle ppiRect = {30, 30, 540, 500};
        Rectangle waveRect = {600, 30, 350, 220};
        Rectangle sliderRect = {600, 280, 350, 160};

        BeginDrawing();
        ClearBackground(RAYWHITE);

        // Draw UI panels
        draw_ppi_display(ppiRect, ppi_speed);
        draw_wave_display(waveRect, adcBuffer, ADC_SAMPLES);
        draw_ppi_speed_slider(sliderRect, &ppi_speed);

        EndDrawing();
    }

    CloseWindow();
    return 0;
}