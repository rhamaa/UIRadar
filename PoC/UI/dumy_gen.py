# simulate_data.py

import numpy as np
import struct
import time
import os

# Path ke file, sesuaikan agar sama dengan yang di widget
# '..' berarti satu direktori di atas direktori saat ini
FILE_PATH = "../data.bin"

# Parameter simulasi
sample_rate = 20_000_000
duration = 0.001  # 1 ms data per update
num_samples = int(sample_rate * duration)
offset = 32768 # Offset untuk data 16-bit unsigned

print(f"Memulai simulasi data. Menulis ke: {os.path.abspath(FILE_PATH)}")
print("Tekan Ctrl+C untuk berhenti.")

try:
    while True:
        # Buat frekuensi acak agar plot terlihat dinamis
        freq1 = np.random.uniform(20_000, 100_000) # Frekuensi antara 20 kHz dan 100 kHz
        freq2 = np.random.uniform(20_000, 100_000)
        
        # Buat sinyal
        t = np.linspace(0, duration, num_samples, endpoint=False)
        signal1 = 3000 * np.sin(2 * np.pi * freq1 * t) + offset
        signal2 = 2000 * np.sin(2 * np.pi * freq2 * t) + offset

        # Gabungkan (interleave) kedua channel
        interleaved = np.empty((num_samples * 2,), dtype=np.uint16)
        interleaved[0::2] = signal1.astype(np.uint16)
        interleaved[1::2] = signal2.astype(np.uint16)

        # Tulis ke file biner (menimpa file yang ada)
        try:
            with open(FILE_PATH, "wb") as f:
                f.write(struct.pack(f'<{len(interleaved)}H', *interleaved))
        except IOError as e:
            print(f"Error menulis file: {e}")

        # Tunggu sejenak sebelum update berikutnya
        time.sleep(0.1) # Update file setiap 100 ms

except KeyboardInterrupt:
    print("\nSimulasi dihentikan.")
    # Hapus file saat selesai agar tidak mengganggu sesi berikutnya
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
        print(f"File '{FILE_PATH}' telah dihapus.")