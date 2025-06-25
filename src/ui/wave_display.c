#include "wave_display.h"
#include <raylib.h>
#include <stddef.h>

void draw_wave_display(Rectangle area, unsigned short *buffer, size_t buffer_size) {
    DrawRectangleRec(area, Fade(BLACK, 0.5f));
    DrawRectangleLinesEx(area, 2, GRAY);
    DrawText("ADC Wave Display", area.x + 10, area.y + 10, 18, LIGHTGRAY);

    if (buffer_size < 2) return;

    Vector2 start_pos;
    Vector2 end_pos;
    float step_x = area.width / (float)(buffer_size - 1);
    const float max_adc_val = 65535.0f;

    for (size_t i = 0; i < buffer_size - 1; i++) {
        // Normalisasi nilai ADC (0-65535) ke rentang (0-1) lalu petakan ke tinggi area
        float normalized_y1 = 1.0f - ((float)buffer[i] / max_adc_val);
        float normalized_y2 = 1.0f - ((float)buffer[i+1] / max_adc_val);

        start_pos.x = area.x + i * step_x;
        start_pos.y = area.y + area.height * normalized_y1;
        end_pos.x = area.x + (i + 1) * step_x;
        end_pos.y = area.y + area.height * normalized_y2;
        
        DrawLineV(start_pos, end_pos, GREEN);
    }
}
