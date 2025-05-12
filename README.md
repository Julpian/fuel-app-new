---
title: Dokumentasi Penggunaan Aplikasi Fuel Entry App
author: Lutfi (Pengembang)
date: 12 Mei 2025
geometry: margin=2cm
fontsize: 12pt
mainfont: Arial
---

# Dokumentasi Penggunaan Aplikasi Fuel Entry App

## 1. Deskripsi Aplikasi
**Fuel Entry App** adalah aplikasi berbasis web untuk mengelola data penggunaan bahan bakar kendaraan (unit) seperti truk atau alat berat. Aplikasi ini memungkinkan:

- Entri data harian (tanggal, HM akhir, unit).
- Tampilan riwayat data dengan filter unit.
- Ekspor data ke Excel atau PDF.
- Pengaturan data permanen (`PENJATAHAN`, `Max_Capacity`) di Code app.main.
- Reset data.

**Spesifikasi**:
- **URL**: [https://fuel-app-new-p3bc.vercel.app/](https://fuel-app-new-p3bc.vercel.app/)
- **Database**: Supabase, tabel `fuel_records` (kolom: `Date`, `"NO_UNIT"`, `HM_AWAL`, `HM_AKHIR`, `SELISIH`, `LITERAN`,  `PENJATAHAN`, `Max_Capacity`, `Buffer_Stock`, `is_new`).
- **Unit**: - .
- **Desain**: Minimalis, responsif (HP, tablet, laptop), dark mode, tombol gradasi, pagination (10 entri), notifikasi toast.

## 2. Fitur Utama
1. **Entri Data**: Input tanggal, HM Akhir, dan unit ke Supabase.
2. **Riwayat Data**: Tabel dengan kolom `Date`, `Unit`, `HM Awal`, `HM Akhir`, `Selisih`, `Literan`, `Penjatahan`, `Max Capacity`, `Buffer Stock`, filter unit, pagination.
3. **Ekspor Data**: Ekspor semua/unit ke Excel (CSV).
4. **Laporan PDF**: Buat PDF berdasarkan tanggal dan shift (1/2).
5. **Reset Data**: Hapus semua data, cadangan otomatis.
6. **Data Permanen**: Kelola `PENJATAHAN` dan `Max_Capacity` via Supabase.
7. **Desain UX**: Dark mode, tombol gradasi (biru, hijau, ungu, merah), responsif.

## 3. Cara Penggunaan

### 3.1 Akses Aplikasi
1. Buka browser (Chrome, Safari, dll.) di HP, tablet, atau laptop.
2. Kunjungi: [https://fuel-app-new-p3bc.vercel.app/](https://fuel-app-new-p3bc.vercel.app/).
3. Pilih unit (contoh: `DZ3007`) dari dropdown atau URL.
4. (Opsional) Aktifkan dark mode (klik ikon matahari/bulan).

### 3.2 Memasukkan Data Baru
1. **Panel Kiri (Pilih Unit)**:
   - Pilih unit (contoh: `DZ3007`).
   - Lihat **Data Terakhir** (contoh: `HM Awal = 200.0`).
2. **Tambah Data**:
   - **Tanggal**: Pilih (default: `2025-05-12`).
   - **HM Akhir**: Masukkan (contoh: `250.5`).
   - Klik **Simpan** (tombol biru, ikon disket).
3. Notifikasi:
   - Hijau: "Data berhasil disimpan!"
   - Merah: "Error, periksa input."
4. Data muncul di **Data Historis**.

### 3.3 Melihat Riwayat Data
1. **Panel Kanan (Data Historis)**:
   - Filter unit (contoh: `DZ3007`).
   - Tabel menampilkan: `Date`, `Unit`, `HM Awal`, `HM Akhir`, `Selisih`, `Literan`, `Penjatahan`, `Max Capacity`, `Buffer Stock`.
2. Navigasi:
   - **Next**: 10 entri berikutnya (tombol biru).
   - **Semua**: Tampilkan semua entri.
3. Baris baru: Kuning (light mode) atau oranye gelap (dark mode).

### 3.4 Ekspor Data
1. **Sidebar (Export & Laporan)**:
   - **Export All**: Klik tombol hijau (ikon Excel) untuk unduh CSV semua data.
   - **Export Unit**: Pilih unit (contoh: `DR0011`), klik tombol hijau untuk CSV unit.
2. File tersimpan (contoh: `fuel_records_all.csv`).

### 3.5 Membuat Laporan PDF
1. **Sidebar (Laporan PDF)**:
   - **Tanggal**: Pilih (contoh: `2025-05-12`).
   - **Shift**: Pilih `1` atau `2`.
   - Klik **Buat PDF** (tombol ungu).
2. File diunduh (contoh: `fuel_report_2025-05-12_shift1.pdf`).
3. Notifikasi: "PDF berhasil dibuat!"

### 3.6 Mereset Data
1. **Sidebar (Reset)**:
   - Baca: "Hapus semua data, backup dibuat."
   - Klik **Reset** (tombol merah, ikon sampah).
   - Konfirmasi: "Yakin hapus semua data?"
2. Data dihapus, cadangan CSV dibuat.
3. Notifikasi: "Data direset, backup tersimpan."

### 3.7 Mengelola Data Permanen (Supabase)
1. **Akses Supabase**:
   - Login: [https://app.supabase.com/](https://app.supabase.com/).
   - Buka tabel `fuel_records`.
2. **Hapus Data Lama**:
   - SQL: `TRUNCATE TABLE fuel_records CASCADE;`
   - Dashboard: Pilih semua baris, klik **Delete Selected Rows**.
   - Verifikasi: `SELECT COUNT(*) FROM fuel_records;` (harus `0`).
3. **Masukkan Data Baru** (contoh):
   ```sql
   INSERT INTO fuel_records (Date, "NO_UNIT", HM_AWAL, PENJATAHAN, Max_Capacity, is_new)
   VALUES
   ('2025-05-12', 'DR0011', 100.0, 65, 3000.0, FALSE),
   ('2025-05-12', 'DZ3007', 200.0, 60, 0.0, FALSE),
   ('2025-05-12', 'LD0152', 25.0, 12, 300.0, FALSE);
