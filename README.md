# Game Voice Translator Overlay (TRSLT_RL_KYO_v1)

Floating subtitle overlay translator real-time untuk game internasional, Discord voice chat, dan streaming audio Windows. Menangkap suara pembicara langsung lewat WASAPI Loopback, mengenali ucapan, menerjemahkannya ke Bahasa Indonesia, dan menampilkannya sebagai widget transparan di atas game.

---

## Fitur Utama

- **WASAPI System Audio Loopback**: Menangkap suara game atau obrolan suara langsung dari output audio sistem Windows tanpa perlu virtual audio cable.
- **Latensi Rendah**: Pemrosesan VAD (Voice Activity Detection) dan streaming transkripsi dengan latensi tanggap (<350ms).
- **Tembus Klik (Click-Through)**: Tombol pintas `Alt + C` membuat klik mouse tembus langsung ke game di belakang jendela subtitle.
- **3 Tema Visual**:
  1. **Cute**: Sudut membal empuk, palet pastel lembut, animasi spring bounce, font Quicksand.
  2. **Gaming HUD**: Sudut miring taktis, aksen oranye lava neon, efek scanline, font Rajdhani.
  3. **Modern Glass**: Efek frosted glass blur, aksen slate, dan font Inter.

---

## Kontrol & Interaktivitas Widget

- **Drag & Move**: Geser bilah atas widget untuk memindahkan posisi di layar.
- **Corner Resize**: Tarik sudut kanan bawah untuk mengubah ukuran jendela.
- **Gembok Posisi (`Alt + L`)**: Kunci posisi widget agar tidak sengaja tergeser saat sesi permainan berlangsung.
- **Click-Through Mode (`Alt + C`)**: Tembus klik mouse ke game di belakang widget.
- **Bersihkan Layar (`Alt + X`)**: Hapus riwayat chat atau subtitle seketika.
- **Drawer Pengaturan**:
  - Ganti pilihan 3 tema visual secara instan.
  - Pilihan bahasa input (Auto, EN, JP, KR, RU, ZH) dan bahasa target (ID, EN).
  - Slider transparansi (20% sampai 100%).
  - Slider ukuran font subtitle (12px sampai 24px).

---

## Cara Menjalankan

### 1. Jalankan Langsung (1-Klik di Windows)
Klik ganda file `run.bat` di folder utama repositori.

### 2. Jalankan via Terminal / PowerShell
```powershell
# Pasang dependensi
pip install -r requirements.txt

# Jalankan server penerjemah
python server.py
```

Setelah server aktif:
1. Buka browser atau jendela overlay di `http://127.0.0.1:8765/index.html`.
2. Status audio akan menampilkan **WASAPI LIVE**.
3. Putar audio bahasa asing di YouTube, Discord, atau game apa saja.
4. Terjemahan otomatis langsung muncul melayang di layar.

---

## Struktur Direktori

```plaintext
TRSLT_RL_KYO_v1/
├── audio_capture.py       # WASAPI Loopback capture engine
├── speech_translator.py   # Modul STT dan penerjemah dengan fallback
├── vad_filter.py          # Analisis energi suara (VAD)
├── server.py              # Backend HTTP server dan SSE event streaming
├── index.html             # Antarmuka floating overlay
├── styles.css             # Tema styling (Cute, HUD, Glass)
├── app.js                 # Logika client, hotkeys, dan event stream
├── tests/                 # Script uji diagnostik audio loopback
├── requirements.txt       # Daftar dependensi Python
├── run.bat                # Skrip peluncur otomatis Windows
├── .env.example           # Template konfigurasi port dan bahasa
├── LICENSE                # Lisensi resmi MIT
└── README.md              # Dokumentasi proyek
```

---

## Lisensi

Didistribusikan di bawah Lisensi MIT. Silakan baca file [LICENSE](LICENSE) untuk detail ketentuan lisensi.
