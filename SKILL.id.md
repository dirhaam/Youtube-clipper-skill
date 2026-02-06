---
name: youtube-clipper
description: >
  Alat kliping video YouTube cerdas. Unduh video dan subtitle, AI menganalisis dan membuat bab terperinci (tingkat beberapa menit),
  pengguna memilih segmen yang kemudian dipotong otomatis, diterjemahkan ke subtitle dwibahasa Inggris-Indonesia, membakar subtitle ke video, dan membuat ringkasan konten.
  Skenario penggunaan: Saat pengguna perlu memotong video YouTube, membuat klip video pendek, atau membuat versi subtitle dwibahasa.
  Kata kunci: kliping video, YouTube, terjemahan subtitle, subtitle dwibahasa, unduh video, clip video
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - AskUserQuestion
model: claude-sonnet-4-5-20250514
---

# Alat Kliping Video YouTube Cerdas

> **Instalasi**: Jika Anda menginstal skill ini dari GitHub, silakan merujuk ke [README.md](README.md#installation) untuk instruksi instalasi. Metode yang disarankan adalah `npx skills add https://github.com/op7418/Youtube-clipper-skill`.

## Alur Kerja

Anda akan menjalankan tugas kliping video YouTube mengikuti 6 tahap berikut:

### Tahap 1: Deteksi Lingkungan

**Tujuan**: Memastikan semua alat dan dependensi yang diperlukan sudah terinstal.

1.  Deteksi apakah yt-dlp tersedia
    ```bash
    yt-dlp --version
    ```

2.  Deteksi versi FFmpeg dan dukungan libass
    ```bash
    # Periksa FFmpeg standar
    ffmpeg -version

    # Verifikasi dukungan libass (diperlukan untuk membakar subtitle)
    ffmpeg -filters 2>&1 | grep subtitles
    ```

3.  Deteksi dependensi Python
    ```bash
    python3 -c "import yt_dlp; print('✅ yt-dlp available')"
    python3 -c "import pysrt; print('✅ pysrt available')"
    ```

**Jika deteksi lingkungan gagal**:
- yt-dlp tidak terinstal: Sarankan `pip install yt-dlp`
- FFmpeg tanpa libass: Sarankan instal pakat lengkap (ffmpeg-full)
- Dependensi Python hilang: Sarankan `pip install pysrt python-dotenv`

**Catatan**:
- FFmpeg Homebrew standar mungkin tidak menyertakan libass, yang berarti tidak bisa membakar subtitle.
- Anda harus lulus deteksi lingkungan sebelum melanjutkan.

---

### Tahap 2: Unduh Video

**Tujuan**: Mengunduh video YouTube dan subtitle bahasa Inggris.

1.  Tanyakan URL YouTube kepada pengguna.

2.  Panggil skrip download_video.py
    ```bash
    cd ~/.claude/skills/youtube-clipper
    python3 scripts/download_video.py <youtube_url>
    ```

3.  Skrip akan:
    - Mengunduh video (maksimal 1080p, format mp4)
    - Mengunduh subtitle bahasa Inggris (format VTT, subtitle otomatis sebagai cadangan)
    - Mengeluarkan jalur file dan informasi video

4.  Tampilkan kepada pengguna:
    - Judul Video
    - Durasi Video
    - Ukuran File
    - Jalur Unduhan

**Output**:
- File video: `<id>.mp4` (dinamai menggunakan ID video untuk menghindari masalah karakter khusus)
- File subtitle: `<id>.en.vtt`

---

### Tahap 3: Analisis Bab (Fitur Pembeda Utama)

**Tujuan**: Menggunakan Claude AI untuk menganalisis konten subtitle dan membuat bab terperinci (tingkat 2-5 menit).

1.  Panggil analyze_subtitles.py untuk mengurai subtitle VTT
    ```bash
    python3 scripts/analyze_subtitles.py <subtitle_path>
    ```

2.  Skrip akan mengeluarkan data subtitle terstruktur:
    - Teks subtitle lengkap (dengan stempel waktu)
    - Total durasi
    - Jumlah subtitle

3.  **Anda perlu melakukan Analisis AI** (Ini adalah langkah paling krusial):
    - Baca konten subtitle lengkap
    - Pahami semantik konten dan titik peralihan topik
    - Identifikasi posisi peralihan topik yang alami
    - Buat bab dengan granularitas 2-5 menit (hindari pemotongan kasar per setengah jam)

4.  Untuk setiap bab, buatkan:
    - **Judul**: Ringkasan tema yang ringkas (10-20 kata)
    - **Rentang Waktu**: Waktu mulai dan berakhir (Format: MM:SS atau HH:MM:SS)
    - **Ringkasan Inti**: 1-2 kalimat yang menjelaskan apa yang dibicarakan bagian ini (50-100 kata)
    - **Kata Kunci**: 3-5 kata konsep inti

5.  **Prinsip Pembuatan Bab**:
    - Granularitas: Setiap bab 2-5 menit (hindari terlalu pendek atau terlalu panjang)
    - Kelengkapan: Pastikan semua konten video tercakup, tidak ada yang terlewat
    - Bermakna: Setiap bab adalah topik yang relatif independen
    - Pemotongan Alami: Potong pada titik peralihan topik, jangan potong secara mekanis berdasarkan waktu

6.  Tampilkan daftar bab kepada pengguna:
    ```
    📊 Analisis Selesai, dibuat X bab:

    1. [00:00 - 03:15] AGI Bukan Titik Waktu, Tapi Kurva Eksponensial
       Inti: Kemampuan model AI mengganda setiap 4-12 bulan, para insinyur sudah menggunakan Claude untuk menulis kode
       Kata Kunci: AGI, Pertumbuhan Eksponensial, Claude Code

    2. [03:15 - 06:30] Kesenjangan China dalam AI
       Inti: Embargo chip menghambat China, optimasi benchmark DeepSeek tidak mencerminkan kemampuan sebenarnya
       Kata Kunci: China, Embargo Chip, DeepSeek

    ... (Semua bab)

    ✓ Semua konten tercakup, tidak ada yang terlewat
    ```

---

### Tahap 4: Pilihan Pengguna

**Tujuan**: Membiarkan pengguna memilih bab yang akan diklip dan opsi pemrosesan.

1.  Gunakan alat AskUserQuestion untuk membiarkan pengguna memilih bab
    - Sediakan nomor bab untuk dipilih pengguna
    - Dukung pilihan ganda (bisa memilih beberapa bab)

2.  Tanyakan opsi pemrosesan:
    - Apakah akan membuat subtitle dwibahasa? (Inggris + Indonesia)
    - Apakah akan membakar subtitle ke video? (Hardsub)
    - Apakah akan membuat ringkasan konten?

3.  Konfirmasi pilihan pengguna dan tampilkan rencana pemrosesan.

---

### Tahap 5: Pemrosesan Klip (Tahap Eksekusi Inti)

**Tujuan**: Menjalankan beberapa tugas pemrosesan secara paralel.

Untuk setiap bab yang dipilih pengguna, jalankan langkah-langkah berikut:

#### 5.1 Potong Klip Video
```bash
python3 scripts/clip_video.py <video_path> <start_time> <end_time> <output_path>
```
- Gunakan FFmpeg untuk pemotongan presisi
- Pertahankan kualitas video asli
- Output: `<Judul_Bab>_clip.mp4`

#### 5.2 Ekstrak Klip Subtitle
- Filter subtitle untuk rentang waktu tersebut dari subtitle lengkap
- Sesuaikan stempel waktu (kurangi waktu mulai, mulai dari 00:00:00)
- Konversi ke format SRT
- Output: `<Judul_Bab>_original.srt`

#### 5.3 Terjemahkan Subtitle (Jika pengguna memilih)
```bash
python3 scripts/translate_subtitles.py <subtitle_path>
```
- **Optimasi Terjemahan Batch**: Terjemahkan tiap batch 20 subtitle sekaligus (hemat 95% panggilan API)
- Strategi Terjemahan:
  - Pertahankan keakuratan istilah teknis
  - Gaya bahasa lisan (cocok untuk video pendek)
  - Ringkas dan lancar (hindari bertele-tele)
- Output: `<Judul_Bab>_translated.srt`

#### 5.4 Buat File Subtitle Dwibahasa (Jika pengguna memilih)
- Gabungkan subtitle Inggris dan Indonesia
- Format: SRT Dwibahasa (setiap subtitle berisi bahasa Inggris dan Indonesia)
- Gaya: Inggris di atas, Indonesia di bawah
- Output: `<Judul_Bab>_bilingual.srt`

#### 5.5 Bakar Subtitle ke Video (Jika pengguna memilih)
```bash
python3 scripts/burn_subtitles.py <video_path> <subtitle_path> <output_path>
```
- Gunakan ffmpeg (dukungan libass)
- **Gunakan direktori sementara untuk mengatasi masalah spasi pada jalur** (Penting!)
- Gaya Subtitle:
  - Ukuran Font: 24
  - Margin Bawah: 30
  - Warna: Teks putih + Stroke hitam
- Output: `<Judul_Bab>_with_subtitles.mp4`

#### 5.6 Buat Ringkasan Konten (Jika pengguna memilih)
```bash
python3 scripts/generate_summary.py <chapter_info>
```
- Berdasarkan judul bab, ringkasan, dan kata kunci
- Buat naskah yang cocok untuk media sosial
- Mencakup: Judul, Poin Inti, Platform yang Cocok (Instagram, TikTok, dll.)
- Output: `<Judul_Bab>_summary.md`

**Tampilan Progres**:
```
🎬 Mulai memproses Bab 1/3: AGI Bukan Titik Waktu...

1/6 Memotong klip video... ✅
2/6 Mengekstrak klip subtitle... ✅
3/6 Menerjemahkan subtitle ke Indonesia... [=====>    ] 50% (26/52)
4/6 Membuat file subtitle dwibahasa... ✅
5/6 Membakar subtitle ke video... ✅
6/6 Membuat ringkasan konten... ✅

✨ Bab 1 Selesai diproses
```

---

### Tahap 6: Hasil Output

**Tujuan**: Mengatur file output dan menampilkannya kepada pengguna.

1.  Buat direktori output
    ```
    ./youtube-clips/<TanggalWaktu>/
    ```
    Direktori output terletak di direktori kerja saat ini.

2.  Atur struktur file:
    ```
    <Judul_Bab>/
    ├── <Judul_Bab>_clip.mp4              # Klip asli (tanpa subtitle)
    ├── <Judul_Bab>_with_subtitles.mp4   # Versi bakar subtitle
    ├── <Judul_Bab>_bilingual.srt        # File subtitle dwibahasa
    └── <Judul_Bab>_summary.md           # Ringkasan konten
    ```

3.  Tampilkan kepada pengguna:
    - Jalur direktori output
    - Daftar file (dengan ukuran file)
    - Perintah pratinjau cepat

    ```
    ✨ Pemrosesan Selesai!

    📁 Direktori Output: ./youtube-clips/20260121_143022/

    Daftar File:
      🎬 AGI_Kurva_Eksponensial_Hardsub.mp4 (14 MB)
      📄 AGI_Kurva_Eksponensial_Dwibahasa.srt (2.3 KB)
      📝 AGI_Kurva_Eksponensial_Ringkasan.md (3.2 KB)

    Pratinjau Cepat:
    open ./youtube-clips/20260121_143022/AGI_Kurva_Eksponensial_Hardsub.mp4
    ```

4.  Tanyakan apakah ingin melanjutkan mengklip bab lain
    - Jika ya, kembali ke Tahap 4 (Pilihan Pengguna)
    - Jika tidak, akhiri Skill

---

## Poin Teknis Utama

### 1. Masalah Spasi Jalur FFmpeg
**Masalah**: Filter subtitles FFmpeg gagal mengurai jalur yang mengandung spasi.

**Solusi**: burn_subtitles.py menggunakan direktori sementara
- Buat direktori sementara tanpa spasi
- Salin file ke direktori sementara
- Jalankan FFmpeg
- Pindahkan file output kembali ke lokasi tujuan

### 2. Optimasi Terjemahan Batch
**Masalah**: Menerjemahkan satu per satu menghasilkan banyak panggilan API.

**Solusi**: Terjemahkan per batch 20 subtitle
- Hemat 95% panggilan API
- Tingkatkan kecepatan terjemahan
- Jaga konsistensi terjemahan

### 3. Kehalusan Analisis Bab
**Tujuan**: Menghasilkan bab dengan granularitas 2-5 menit, menghindari granularitas kasar setengah jam.

**Metode**:
- Pahami semantik subtitle, identifikasi peralihan topik
- Cari titik pemotongan topik yang alami
- Pastikan setiap bab memiliki pembahasan yang lengkap
- Hindari pemotongan mekanis berdasarkan waktu

### 4. FFmpeg vs ffmpeg-full
**Perbedaan**:
- FFmpeg Standar: Tanpa dukungan libass, tidak bisa membakar subtitle
- ffmpeg-full: Termasuk libass, mendukung pembakaran subtitle

**Jalur**:
- Standar: `/opt/homebrew/bin/ffmpeg`
- ffmpeg-full: `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` (Apple Silicon)

---

## Penanganan Kesalahan

### Masalah Lingkungan
- Alat hilang → Sarankan perintah instalasi
- FFmpeg tanpa libass → Pandu instalasi ffmpeg-full
- Dependensi Python hilang → Sarankan pip install

### Masalah Unduhan
- URL tidak valid → Sarankan periksa format URL
- Subtitle hilang → Coba subtitle otomatis
- Kesalahan jaringan → Sarankan coba lagi

### Masalah Pemrosesan
- FFmpeg gagal → Tampilkan pesan kesalahan detail
- Terjemahan gagal → Mekanisme coba lagi (maksimal 3 kali)
- Ruang disk penuh → Sarankan bersihkan ruang

---

## Standar Penamaan File Output

- Klip Video: `<Judul_Bab>_clip.mp4`
- File Subtitle: `<Judul_Bab>_bilingual.srt`
- Versi Bakar: `<Judul_Bab>_with_subtitles.mp4`
- Ringkasan: `<Judul_Bab>_summary.md`

**Pemrosesan Nama File**:
- Hapus karakter khusus (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`)
- Ganti spasi dengan garis bawah
- Batasi panjang (maksimal 100 karakter)

---

## Poin Penting Pengalaman Pengguna

1.  **Visibilitas Progres**: Tampilkan progres dan status setiap langkah
2.  **Ramah Kesalahan**: Pesan kesalahan yang jelas dan solusi
3.  **Kontrol**: Pengguna memilih bab dan opsi pemrosesan
4.  **Kualitas Tinggi**: Analisis bab bermakna, terjemahan akurat dan lancar
5.  **Kelengkapan**: Menyediakan beberapa versi (asli dan olahan)

---

## Mulai Eksekusi

Saat pengguna memicu Skill ini:
1. Segera mulai Tahap 1 (Deteksi Lingkungan)
2. Jalankan urutan 6 tahap
3. Otomatis masuk ke tahap berikutnya setelah setiap tahap selesai
4. Berikan solusi yang jelas saat menghadapi masalah
5. Terakhir tampilkan hasil output lengkap

Ingat: Nilai inti dari Skill ini terletak pada **Analisis Bab Presisi AI** dan **Pemrosesan Teknis Mulus**, memungkinkan pengguna mengekstrak klip video pendek berkualitas tinggi dari video panjang dengan cepat.
