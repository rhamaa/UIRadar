#include "ppi_display.h"
#include <raylib.h>
#include <math.h>

// Definisikan struct untuk target radar
typedef struct {
    float angle;
    float distance_ratio;
    float alpha; // Untuk efek fade
} RadarTarget;

// Jumlah target
#define NUM_TARGETS 3

void draw_ppi_display(Rectangle area, float speed) {
    // Variabel statis untuk sapuan dan target
    static float ppi_angle = 0.0f;
    static int ppi_direction = 1;
    static RadarTarget targets[NUM_TARGETS] = {
        {45.0f, 0.60f, 0.0f},  // Target 1
        {135.0f, 0.85f, 0.0f}, // Target 2
        {90.0f, 0.40f, 0.0f}   // Target 3 (baru)
    };

    // Tentukan pusat dan radius
    Vector2 center = { area.x + area.width / 2, area.y + area.height - 20 };
    float radius = (area.width / 2 < area.height - 20) ? (area.width / 2 - 20) : (area.height - 30);
    if (radius < 10) radius = 10;

    // Gambar UI dasar
    DrawRectangleRec(area, Fade(BLACK, 0.7f));
    DrawRectangleLinesEx(area, 2, DARKGRAY);
    DrawText("PPI Display (Sector Scan)", area.x + 10, area.y + 10, 18, LIGHTGRAY);

    // Gambar grid dan penanda derajat
    DrawCircleSector(center, radius, 180, 360, 36, Fade(DARKGREEN, 0.4f));
    for (int i = 1; i <= 4; i++) {
        DrawRingLines(center, radius * (i * 0.25f), radius * (i * 0.25f), 180, 360, 36, LIGHTGRAY);
    }
    DrawLine(center.x - radius, center.y, center.x + radius, center.y, LIGHTGRAY);
    for (int i = 0; i <= 180; i += 30) {
        float angle_rad = i * DEG2RAD;
        Vector2 pos = { center.x + (radius + 10) * cosf(angle_rad), center.y - (radius + 10) * sinf(angle_rad) };
        DrawText(TextFormat("%d", i), pos.x - 10, pos.y - 10, 10, LIGHTGRAY);
    }

    // --- Logika dan Gambar Target (Refactored) ---
    float angle_change = ppi_direction * speed * 150.0f * GetFrameTime();
    float prev_angle = ppi_angle - angle_change;

    for (int i = 0; i < NUM_TARGETS; i++) {
        // Cek jika sapuan melewati target
        if ((ppi_direction == 1 && prev_angle < targets[i].angle && ppi_angle >= targets[i].angle) ||
            (ppi_direction == -1 && prev_angle > targets[i].angle && ppi_angle <= targets[i].angle)) {
            targets[i].alpha = 1.0f; // Aktifkan blip
        }

        // Gambar dan pudarkan target jika aktif
        if (targets[i].alpha > 0) {
            targets[i].alpha -= 0.5f * GetFrameTime(); // Pudarkan dalam 2 detik
            if (targets[i].alpha < 0) targets[i].alpha = 0;

            float target_rad = targets[i].angle * DEG2RAD;
            Vector2 target_pos = { 
                center.x + radius * targets[i].distance_ratio * cosf(target_rad), 
                center.y - radius * targets[i].distance_ratio * sinf(target_rad) 
            };
            DrawCircleV(target_pos, 5, Fade(RED, targets[i].alpha));
        }
    }

    // --- Perbarui dan Gambar Sapuan Radar ---
    ppi_angle += angle_change;
    if (ppi_angle >= 180.0f) { ppi_angle = 180.0f; ppi_direction = -1; }
    if (ppi_angle <= 0.0f)   { ppi_angle = 0.0f;   ppi_direction = 1; }

    float sweep_rad = ppi_angle * DEG2RAD;
    Vector2 endPoint = { center.x + radius * cosf(sweep_rad), center.y - radius * sinf(sweep_rad) };
    DrawLineEx(center, endPoint, 2, Fade(GREEN, 0.9f));

    // Gambar jejak sapuan
    for (int i = 1; i <= 20; i++) {
        float trail_angle = ppi_angle - (i * ppi_direction * 0.5f);
        if (trail_angle > 180 || trail_angle < 0) continue;
        float trail_rad = trail_angle * DEG2RAD;
        Vector2 trail_end = { center.x + radius * cosf(trail_rad), center.y - radius * sinf(trail_rad) };
        DrawLineEx(center, trail_end, 2, Fade(GREEN, 0.5f - i * 0.025f));
    }
}
