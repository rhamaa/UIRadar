import numpy as np
import matplotlib.pyplot as plt
import struct
import os

filename = "data.bin"  # Ganti jika nama file berbeda
sample_rate = 30000  # Hz, sesuai input user

if not os.path.exists(filename):
    print(f"File '{filename}' tidak ditemukan. Pastikan file ada di direktori yang sama dengan script ini.")
    exit(1)

with open(filename, "rb") as f:
    data = f.read()
    values = np.array(struct.unpack("<{}H".format(len(data)//2), data), dtype=np.float32)

# Pisahkan data menjadi dua channel: ganjil (ch1), genap (ch2)
ch1 = values[::2]  # index 0,2,4,... (ganjil secara urutan data, ch1)
ch2 = values[1::2] # index 1,3,5,... (genap secara urutan data, ch2)

# Hilangkan offset DC
ch1 -= np.mean(ch1)
ch2 -= np.mean(ch2)

# Hitung FFT untuk masing-masing channel
n1 = len(ch1)
n2 = len(ch2)
fft_ch1 = np.fft.fft(ch1)
fft_ch2 = np.fft.fft(ch2)
mag_ch1 = np.abs(fft_ch1)[:n1//2]
mag_ch2 = np.abs(fft_ch2)[:n2//2]
freqs_ch1 = np.fft.fftfreq(n1, d=1/sample_rate)[:n1//2]
freqs_ch2 = np.fft.fftfreq(n2, d=1/sample_rate)[:n2//2]

plt.figure(figsize=(10, 4))
plt.plot(freqs_ch1, mag_ch1, color='r', label='CH1 (ganjil)')
plt.plot(freqs_ch2, mag_ch2, color='b', label='CH2 (genap)')
plt.title('Spektrum FFT 2 Channel dari data.bin')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
