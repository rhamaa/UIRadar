import numpy as np
import struct
import time

FILENAME = "./live_acquisition_ui.bin"
SAMPLE_RATE = 20_000_000
NUM_SAMPLES = 4096  # Jumlah sampel per channel

print(f"Starting simulation. Writing to '{FILENAME}' every 2 seconds.")
print("Run main.py in another terminal to see the live updates.")
print("Press Ctrl+C to stop.")

try:
    while True:
        # Buat sinyal gabungan dengan frekuensi yang sedikit berubah
        freq1 = 90000 + np.random.randint(-1000, 1000)
        freq2 = 150000 + np.random.randint(-2000, 2000)
        
        t = np.linspace(0, NUM_SAMPLES / SAMPLE_RATE, NUM_SAMPLES, endpoint=False)
        
        # Buat data untuk dua channel
        signal1 = (1000 * np.sin(2 * np.pi * freq1 * t)).astype(np.uint16)
        signal2 = (800 * np.sin(2 * np.pi * freq2 * t)).astype(np.uint16)
        
        # Gabungkan (interleave) data seperti hardware asli
        interleaved_data = np.empty((NUM_SAMPLES * 2,), dtype=np.uint16)
        interleaved_data[0::2] = signal1
        interleaved_data[1::2] = signal2

        # Tulis data ke file biner
        with open(FILENAME, "wb") as f:
            f.write(struct.pack(f'<{len(interleaved_data)}H', *interleaved_data))
        
        print(f"File updated at {time.strftime('%H:%M:%S')} with freqs ~{freq1/1000:.1f}kHz and ~{freq2/1000:.1f}kHz")
        
        # Tunggu sebelum update berikutnya
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nSimulation stopped.")