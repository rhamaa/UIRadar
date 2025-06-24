# Proyek UI Radar Sederhana

Ini adalah aplikasi desktop sederhana yang dibangun menggunakan C, Raylib, dan Raygui untuk menampilkan antarmuka pengguna (UI) modular yang terdiri dari:
- **Tampilan Radar PPI**: Simulasi sapuan (sweep) radar Plan Position Indicator.
- **Tampilan Gelombang Sinus**: Visualisasi data gelombang sinus seperti osiloskop.
- **Slider Kecepatan**: Kontrol interaktif untuk mengatur kecepatan sapuan radar.

## Fitur
- Arsitektur kode modular, memisahkan logika UI dari data.
- Penggunaan Raylib untuk rendering grafis dan Raygui untuk komponen UI.
- Sistem build sederhana menggunakan `make`.

## Dependensi
- `gcc` atau compiler C lainnya.
- `make`.
- Library Raylib dan Raygui (sudah termasuk di dalam direktori `lib`).

## Cara Membangun dan Menjalankan

1.  **Kompilasi Proyek:**
    Buka terminal di direktori root proyek dan jalankan perintah `make`.
    ```sh
    make
    ```

2.  **Menjalankan Aplikasi:**
    Setelah kompilasi berhasil, sebuah file eksekusi bernama `main` akan dibuat. Jalankan dengan perintah:
    ```sh
    ./main
    ```

3.  **Membersihkan Hasil Build:**
    Untuk menghapus file-file hasil kompilasi, jalankan:
    ```sh
    make clean
    ```

## Struktur Proyek
```
/UIRadar
├── build/         # Direktori output untuk file objek
├── lib/           # Library eksternal (raylib, raygui)
├── src/           # Kode sumber proyek
│   ├── function/  # Logika generator data (misal: sinus.c)
│   └── ui/        # Modul-modul komponen UI
├── Makefile       # Aturan untuk membangun proyek
└── main           # File eksekusi (hasil build)
```
