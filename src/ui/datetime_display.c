#include "ui/datetime_display.h"
#include "raygui.h"
#include <time.h>
#include <stdio.h>

void draw_datetime_display(Rectangle area) {
    time_t now = time(NULL);
    struct tm *local = localtime(&now);

    char date_str[11];
    char time_str[9];

    strftime(date_str, sizeof(date_str), "%Y-%m-%d", local);
    strftime(time_str, sizeof(time_str), "%H:%M:%S", local);

    // Layout untuk dua kotak (tanggal dan waktu) secara vertikal
    float box_height = (area.height - 10) / 2;
    Rectangle date_box = { area.x, area.y, area.width, box_height };
    Rectangle time_box = { area.x, area.y + box_height + 10, area.width, box_height };

    // Gambar kotak dengan style terminal
    // GuiTextBox adalah cara mudah untuk mendapatkan kotak dengan border dan teks
    // Kita akan menonaktifkannya agar tidak bisa diedit
    GuiDisable();
    GuiTextBox(date_box, date_str, 11, false);
    GuiTextBox(time_box, time_str, 9, false);
    GuiEnable();
}
