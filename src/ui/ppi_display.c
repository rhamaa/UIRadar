#include "ppi_display.h"
#include <raylib.h>
#include <math.h>

// --- Dummy Target --- 
#define TARGET_ANGLE 45.0f
#define TARGET_DISTANCE_RATIO 0.6f

void draw_ppi_display(Rectangle area, float speed) {
    // Variabel statis untuk menyimpan posisi sudut dan arah sapuan
    static float ppi_angle = 0.0f;
    static int ppi_direction = 1; // 1: kanan->kiri, -1: kiri->kanan
    static float target_alpha = 0.0f; // Alpha untuk efek blip target

    // Tentukan pusat dan radius untuk setengah lingkaran di bagian bawah area
    Vector2 center = { area.x + area.width / 2, area.y + area.height - 20 };
    float radius = (area.width / 2 < area.height - 20) ? (area.width / 2 - 20) : (area.height - 30);
    if (radius < 10) radius = 10;

    // Gambar latar belakang dan judul
    DrawRectangleRec(area, Fade(BLACK, 0.7f));
    DrawRectangleLinesEx(area, 2, DARKGRAY);
    DrawText("PPI Display (Sector Scan)", area.x + 10, area.y + 10, 18, LIGHTGRAY);

    // Gambar grid setengah lingkaran
    DrawCircleSector(center, radius, 180, 360, 36, Fade(DARKGREEN, 0.4f));
    DrawRingLines(center, radius * 0.25f, radius * 0.25f, 180, 360, 36, LIGHTGRAY);
    DrawRingLines(center, radius * 0.5f, radius * 0.5f, 180, 360, 36, LIGHTGRAY);
    DrawRingLines(center, radius * 0.75f, radius * 0.75f, 180, 360, 36, LIGHTGRAY);
    DrawRingLines(center, radius, radius, 180, 360, 36, LIGHTGRAY);
    DrawLine(center.x - radius, center.y, center.x + radius, center.y, LIGHTGRAY); // Garis dasar

    // Gambar penanda derajat
    for (int i = 0; i <= 180; i += 30) {
        float angle_rad = i * DEG2RAD;
        Vector2 pos = {
            center.x + (radius + 10) * cosf(angle_rad),
            center.y - (radius + 10) * sinf(angle_rad)
        };
        DrawText(TextFormat("%d", i), pos.x - 10, pos.y - 10, 10, LIGHTGRAY);
    }

    // --- Logika Target ---
    float angle_change = ppi_direction * speed * 150.0f * GetFrameTime();
    float prev_angle = ppi_angle - angle_change;

    if ((ppi_direction == 1 && prev_angle < TARGET_ANGLE && ppi_angle >= TARGET_ANGLE) ||
        (ppi_direction == -1 && prev_angle > TARGET_ANGLE && ppi_angle <= TARGET_ANGLE)) {
        target_alpha = 1.0f; // Aktifkan blip
    }

    if (target_alpha > 0) {
        target_alpha -= 0.5f * GetFrameTime(); // Pudarkan dalam 2 detik
        if (target_alpha < 0) target_alpha = 0;

        float target_rad = TARGET_ANGLE * DEG2RAD;
        Vector2 target_pos = {
            center.x + radius * TARGET_DISTANCE_RATIO * cosf(target_rad),
            center.y - radius * TARGET_DISTANCE_RATIO * sinf(target_rad)
        };
        DrawCircleV(target_pos, 5, Fade(RED, target_alpha));
    }

    // --- Perbarui sudut sapuan ---
    ppi_angle += angle_change;

    if (ppi_angle >= 180.0f) {
        ppi_angle = 180.0f;
        ppi_direction = -1;
    } else if (ppi_angle <= 0.0f) {
        ppi_angle = 0.0f;
        ppi_direction = 1;
    }

    // --- Gambar garis sapuan ---
    float sweep_rad = ppi_angle * DEG2RAD;
    Vector2 endPoint = {
        center.x + radius * cosf(sweep_rad),
        center.y - radius * sinf(sweep_rad) 
    };
    DrawLineEx(center, endPoint, 2, Fade(GREEN, 0.9f));
    
    for (int i = 1; i <= 20; i++) {
        float trail_angle = ppi_angle - (i * ppi_direction * 0.5f);
        if (trail_angle > 180 || trail_angle < 0) continue;
        
        float trail_rad = trail_angle * DEG2RAD;
        Vector2 trail_end = {
            center.x + radius * cosf(trail_rad),
            center.y - radius * sinf(trail_rad)
        };
        DrawLineEx(center, trail_end, 2, Fade(GREEN, 0.5f - i * 0.025f));
    }
}
