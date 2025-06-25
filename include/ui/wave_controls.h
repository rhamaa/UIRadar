#ifndef WAVE_CONTROLS_H
#define WAVE_CONTROLS_H

#include <raylib.h>
#include <stdbool.h> // Diperlukan untuk tipe data bool

// Fungsi untuk menggambar kontrol wave display (tombol pause, dll.)
void draw_wave_controls(Rectangle area, bool *is_paused, bool *show_freq_analyzer);

#endif // WAVE_CONTROLS_H
