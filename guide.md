# Panduan Lengkap YouTube Clipper Skill

Panduan penggunaan manual dari terminal (Powershell).

## Prasyarat

```powershell
cd D:\Youtube-clipper-skill
py --version   # Pastikan Python terinstal
```

---

## Langkah 1: Download Video

```powershell
py scripts/download_video.py <URL_YouTube>
```

**Contoh:**
```powershell
py scripts/download_video.py https://www.youtube.com/watch?v=ALnnrQsi_X0
```

**Hasil:** `ALnnrQsi_X0.mp4`

> **Catatan:** Subtitle saat ini dinonaktifkan untuk menghindari rate limit. Gunakan langkah 1b jika perlu subtitle.

### Langkah 1b: Download Subtitle Terpisah (Opsional)

Jika video tidak ada subtitle manual, gunakan auto-generated:

```powershell
# Lihat subtitle yang tersedia
py -m yt_dlp --list-subs <URL>

# Download subtitle auto-generated (contoh: Jepang)
py -m yt_dlp --write-auto-sub --sub-lang ja --skip-download <URL>
```

**Contoh:**
```powershell
py -m yt_dlp --write-auto-sub --sub-lang ja --skip-download https://www.youtube.com/watch?v=ALnnrQsi_X0
```

---

## Langkah 2: Analisis Subtitle

```powershell
py scripts/analyze_subtitles.py <Subtitle.vtt>
```

**Contoh:**
```powershell
py scripts/analyze_subtitles.py ALnnrQsi_X0.ja.vtt
```

**Hasil:** Output teks untuk dibaca AI.

---

## Langkah 3: Potong Video

```powershell
py scripts/clip_video.py <Video.mp4> <Mulai> <Akhir> <Output.mp4>
```

**Contoh:**
```powershell
py scripts/clip_video.py ALnnrQsi_X0.mp4 00:00:25 00:01:30 bab1.mp4
```

---

## Langkah 4: Ekstrak Subtitle

```powershell
py scripts/extract_subtitle_clip.py <Subtitle.vtt> <Mulai> <Akhir> <Output.srt>
```

**Contoh:**
```powershell
py scripts/extract_subtitle_clip.py ALnnrQsi_X0.ja.vtt 00:00:25 00:01:30 bab1.srt
```

---

## Langkah 5: Burn Subtitle

```powershell
py scripts/burn_subtitles.py <Video.mp4> <Subtitle.srt> <Output_Final.mp4>
```

**Contoh:**
```powershell
py scripts/burn_subtitles.py ALnnrQsi_X0.mp4 ALnnrQsi_X0.id.srt ALnnrQsi_X0_final.mp4
```

---

## Ringkasan

| Langkah | Script | Fungsi |
| :--- | :--- | :--- |
| 1 | `py scripts/download_video.py` | Unduh video |
| 1b | `py -m yt_dlp --write-auto-sub` | Unduh subtitle |
| 2 | `py scripts/analyze_subtitles.py` | Parsing subtitle |
| 3 | `py scripts/clip_video.py` | Potong video |
| 4 | `py scripts/extract_subtitle_clip.py` | Potong subtitle |
| 5 | `py scripts/burn_subtitles.py` | Tempel subtitle |

---

## Tips

1.  Selalu jalankan dari folder `D:\Youtube-clipper-skill`
2.  Gunakan `py` bukan `python` di Windows
3.  Folder `scripts` pakai "s" di akhir
4.  Jika kena rate limit (Error 429), tunggu 15-30 menit
5.  Untuk subtitle auto-generated, gunakan `--write-auto-sub`
