# config.py
import os

# --- Konfigurasi Aplikasi ---

# Tentukan direktori root proyek secara dinamis
# Ini adalah direktori tempat file main.py berada
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Konfigurasi Pemantauan File ---
# Nama file data yang akan dipantau. Path ini sekarang absolut dan andal.
FILENAME = os.path.join(PROJECT_ROOT, "live_acquisition_ui.bin")

# Rate sampling data dari akuisisi (dalam Hz)
SAMPLE_RATE = 20_000_000  # 20 MHz

# Seberapa sering (dalam detik) memeriksa pembaruan file
POLLING_INTERVAL = 0.2  # 5 kali per detik

# --- Konfigurasi Tampilan ---
APP_SPACING = 8
APP_PADDING = 8

# Palet warna yang konsisten untuk tema aplikasi
THEME_COLORS = {
    "background": (21, 21, 21, 255),      # Latar belakang yang sangat gelap
    "scan_area": (37, 37, 38, 150),       # Area scan yang sedikit transparan
    "grid_lines": (255, 255, 255, 40),    # Garis putih yang sangat pudar
    "text": (255, 255, 255, 150),         # Teks putih yang tidak terlalu mencolok
    "accent": (0, 200, 119, 255),         # Warna hijau/teal untuk sapuan jarum
    "target": (255, 0, 0, 255),           # Merah terang untuk target
}
