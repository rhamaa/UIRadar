#include "ppi_speed_slider.h"
#include <raygui.h>
#include <raylib.h>

void draw_ppi_speed_slider(Rectangle area, float *speed) {
    DrawRectangleRec(area, Fade(PINK, 0.2f));
    DrawRectangleLinesEx(area, 2, DARKGRAY);
    DrawText("PPI Scaning\nSpeed Slider", area.x + 10, area.y + 10, 18, DARKGRAY);
    Rectangle sliderRect = {area.x + 10, area.y + area.height/2, area.width - 20, 20};
    GuiSlider(sliderRect, "Slow", "Fast", speed, 0.1f, 5.0f);
}
