#include "ppi_display.h"
#include <raylib.h>
#include <math.h>

void draw_ppi_display(Rectangle area, float speed) {
    // Draw background
    DrawRectangleRec(area, Fade(PINK, 0.3f));
    DrawRectangleLinesEx(area, 2, MAROON);
    DrawText("PPI RADAR", area.x + area.width/2 - 80, area.y + area.height/2 - 20, 32, MAROON);
    // Dummy sweep effect
    static float sweep_angle = 0.0f;
    sweep_angle += speed;
    if (sweep_angle > 360.0f) sweep_angle -= 360.0f;
    float cx = area.x + area.width/2;
    float cy = area.y + area.height/2;
    float r = (area.width < area.height ? area.width : area.height) / 2 - 10;
    DrawCircleLines(cx, cy, r, DARKGRAY);
    DrawLine(cx, cy, cx + r*cosf(sweep_angle*3.14159f/180.0f), cy + r*sinf(sweep_angle*3.14159f/180.0f), GREEN);
}
