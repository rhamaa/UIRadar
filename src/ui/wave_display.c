#include "wave_display.h"
#include <raylib.h>
#include <stddef.h>

void draw_wave_display(Rectangle area, float *buffer, size_t n) {
    // Draw background
    DrawRectangleRec(area, Fade(GREEN, 0.3f));
    DrawRectangleLinesEx(area, 2, DARKGREEN);
    DrawText("Sine Display", area.x + 10, area.y + 10, 22, DARKGREEN);
    // Draw axis
    DrawLine(area.x, area.y + area.height/2, area.x + area.width, area.y + area.height/2, GRAY);
    // Draw waveform
    for (size_t i = 1; i < n; ++i) {
        float x0 = area.x + ((i-1) * area.width) / n;
        float y0 = area.y + area.height/2 - buffer[i-1];
        float x1 = area.x + (i * area.width) / n;
        float y1 = area.y + area.height/2 - buffer[i];
        DrawLine((int)x0, (int)y0, (int)x1, (int)y1, BLUE);
    }
}
