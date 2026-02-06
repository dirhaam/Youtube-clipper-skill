# Panduan Menjalankan GUI YouTube Clipper

Aplikasi ini sekarang memiliki antarmuka Web (GUI) agar Anda tidak perlu mengetik perintah panjang di terminal.

## Cara Menjalankan

1.  Buka terminal di folder skill:
    ```powershell
    cd D:\Youtube-clipper-skill
    ```

2.  Jalankan aplikasi:
    ```powershell
    py app.py
    ```

3.  Buka browser dan akses:
    👉 **http://localhost:5000**

## Fitur GUI

Semua fitur di terminal sekarang ada tombolnya:

1.  **📥 Download Video**: Masukkan URL, klik Download.
2.  **📊 Analyze**: Pilih file VTT, klik Analyze (hasil muncul di output).
3.  **✂️ Clip Video**: Pilih video, isi waktu mulai/akhir.
4.  **🔤 Extract Subtitle**: Ambil subtitle untuk klip.
5.  **🎬 Burn Subtitle**: Tempel subtitle permanen.
6.  **📁 File Browser**: Lihat file, copy nama file, atau hapus file sampah.

> **Catatan:** Biarkan terminal tetap terbuka selama Anda menggunakan aplikasi web ini. Terminal akan menampilkan log proses di latar belakang.

## Workflow dengan AI (Untuk Timing)

Aplikasi ini bekerja sama dengan AI (saya) untuk menentukan pemotongan video yang presisi:

1.  Buka Tab **Analyze** -> Upload file VTT -> Klik **Analyze**.
2.  Copy seluruh teks yang muncul di kotak Output.
3.  **Paste ke Chat** dengan saya.
4.  Saya akan memberikan tabel **Waktu Mulai** dan **Waktu Akhir** untuk setiap bab.
5.  Gunakan waktu tersebut di Tab **✂️ Clip Video** dan **🔤 Extract Subtitle**.
