#include "adlink_adc_dumy.h"
#include <math.h>

#define PI 3.1415926535
#define FREQUENCY 30000.0      // 30 kHz
#define SAMPLE_RATE 1000000.0  // 1 MHz sample rate
#define ADC_MAX_VALUE 65535    // 16-bit ADC

/**
 * @brief Menghasilkan satu sampel ADC 16-bit dummy.
 * 
 * Fungsi ini menyimulasikan pengambilan sampel dari sinyal sinus 30kHz.
 * Setiap kali dipanggil, ia mengembalikan nilai berikutnya dalam urutan gelombang.
 * @return unsigned short Nilai sampel ADC (0-65535).
 */
unsigned short get_dummy_adc_sample(void) {
    static long long sample_index = 0;

    // Hitung nilai sinus pada waktu saat ini
    double time = sample_index / SAMPLE_RATE;
    double sin_value = sin(2 * PI * FREQUENCY * time);

    // Pindahkan rentang [-1, 1] ke [0, 1] lalu skalakan ke [0, 65535]
    unsigned short adc_value = (unsigned short)((sin_value + 1.0) / 2.0 * ADC_MAX_VALUE);

    sample_index++;

    return adc_value;
}