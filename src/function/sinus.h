#ifndef SINUS_H
#define SINUS_H

#include <stddef.h>

// Fungsi dummy generator sinus
// buffer: array untuk output data
// n: jumlah sample
// amplitude: amplitudo gelombang
// freq: frekuensi gelombang (Hz)
// phase: fasa awal (radian)
// sample_rate: sample rate (Hz)
void generate_sinus(float *buffer, size_t n, float amplitude, float freq, float phase, float sample_rate);

#endif // SINUS_H
