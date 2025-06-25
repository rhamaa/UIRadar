#include "ppi_speed_slider.h"
#include <raygui.h>
#include <raylib.h>

void draw_ppi_speed_slider(Rectangle area, float *speed) {
    DrawRectangleRec(area, Fade(BLACK, 0.5f));
    DrawRectangleLinesEx(area, 2, GRAY);
    DrawText("PPI Scan Speed", area.x + 10, area.y + 5, 14, LIGHTGRAY);
    Rectangle slider_rect = { area.x + 20, area.y + 25, area.width - 40, 20 };
        GuiSlider(slider_rect, "1x", "5x", speed, 1.0f, 5.0f);
}
