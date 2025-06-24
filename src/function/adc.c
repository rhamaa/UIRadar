#include <stdio.h>
#include <unistd.h> // Untuk usleep()
#include "adlink_adc_dumy.h"

int main() {
    printf("Membaca data dari ADC dummy... Tekan Ctrl+C untuk berhenti.\n");

    while (1) {
        // Ambil satu sampel dari ADC dummy
        unsigned short adc_sample = get_dummy_adc_sample();

        // Cetak nilai dalam format heksadesimal (4 digit, zero-padded)
        printf("Nilai ADC: 0x%04X\n", adc_sample);

        // Beri jeda agar output tidak terlalu cepat
        usleep(10000); // Jeda 10 milidetik
    }

    return 0;
}