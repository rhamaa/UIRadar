import numpy as np
import matplotlib.pyplot as plt
import struct
import os

filename = "data.bin"  # Ganti jika nama file berbeda
sample_rate = 20_000_000  # 20 MHz, sesuai hardware PCI-9846H

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
def compute_fft(channel, sample_rate):
    n = len(channel)
    fft_vals = np.fft.fft(channel)
    mag = np.abs(fft_vals)[:n//2]
    freqs = np.fft.fftfreq(n, d=1/sample_rate)[:n//2]
    return freqs, mag, n

freqs_ch1, mag_ch1, n1 = compute_fft(ch1, sample_rate)
freqs_ch2, mag_ch2, n2 = compute_fft(ch2, sample_rate)

# Info resolusi dan Nyquist
freq_res = sample_rate / n1
nyquist = sample_rate / 2

plt.figure(figsize=(12, 5))
plt.plot(freqs_ch1, mag_ch1, color='r', label='CH1 (ganjil)')
plt.plot(freqs_ch2, mag_ch2, color='b', label='CH2 (genap)')
plt.title(f'Spektrum FFT 2 Channel\nSample Rate: {sample_rate/1e6:.2f} MHz, Buffer: {n1}, Resolusi: {freq_res:.1f} Hz, Nyquist: {nyquist/1e6:.2f} MHz')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.xlim(1e3, 1e5)  # Batasi dari 1 kHz sampai 100 kHz
plt.show()
