# Kalkulator ROI Proyek

Aplikasi Streamlit untuk mengestimasi Return on Investment (ROI) dari implementasi sebuah proyek atau solusi baru.

## Fitur Utama

- Perhitungan ROI berdasarkan parameter finansial dan operasional.
- Pembuatan laporan PDF otomatis setelah perhitungan.
- Visualisasi data dengan grafik arus kas kumulatif dan sumber penghematan.
- **Backend terintegrasi menggunakan Supabase:**
  - Laporan PDF diunggah otomatis ke **Supabase Storage**.
  - Ringkasan data perhitungan disimpan di **database Supabase (PostgreSQL)**.

## Cara Penggunaan

1.  **Siapkan Proyek Supabase:**
    - Buat proyek baru di [supabase.com](https://supabase.com).
    - Buat tabel database menggunakan skrip SQL yang disediakan.
    - Buat bucket publik di Supabase Storage (misal: `laporan-pdf`).
    - Dapatkan URL Proyek dan Kunci API (anon public).

2.  **Konfigurasi Streamlit Secrets:**
    - Buat file `.streamlit/secrets.toml` di root proyek Anda.
    - Tambahkan kredensial Supabase Anda:
      ```toml
      [supabase]
      url = "URL_PROYEK_SUPABASE_ANDA"
      key = "KUNCI_ANON_PUBLIC_ANDA"
      ```

3.  **Instal Dependensi:**
    Pastikan semua dependensi terinstal dari file `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Jalankan Aplikasi:**
    ```bash
    streamlit run ROI_Calc.py
    ```

5.  **Gunakan Aplikasi:**
    - Isi informasi konsultan dan semua parameter input di sidebar.
    - Klik tombol "HITUNG ROI & SIMPAN LAPORAN".
    - Aplikasi akan menghitung ROI, membuat PDF, memungkinkan Anda mengunduhnya, dan secara otomatis mengunggah laporan serta menyimpan data ke Supabase.

## Struktur Penyimpanan di Supabase

-   **Storage:** File PDF akan disimpan di dalam bucket yang Anda tentukan dengan path yang terstruktur, misalnya: `laporan-pdf/240521 Proyek Alfa Jakarta/240521 Proyek Alfa Jakarta.pdf`.
-   **Database:** Setiap perhitungan yang sukses akan menambahkan satu baris data baru ke tabel `laporan_roi` Anda.