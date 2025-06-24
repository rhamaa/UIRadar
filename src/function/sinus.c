#include "sinus.h"
#include <math.h>

void generate_sinus(float *buffer, size_t n, float amplitude, float freq, float phase, float sample_rate) {
    for (size_t i = 0; i < n; ++i) {
        float t = (float)i / sample_rate;
        buffer[i] = amplitude * sinf(2.0f * 3.14159265f * freq * t + phase);
    }
}
