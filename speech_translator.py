"""
Modul Transkripsi Audio Real-Time & Mesin Penerjemah Multi-Tier.
Dilengkapi perlindungan timeout jaringan (anti-WinError 10060), HTTPS secure endpoint,
dan penanganan pemulihan koneksi otomatis.
"""

import os
import io
import time
import socket
import urllib.error
import speech_recognition as sr
from deep_translator import GoogleTranslator, MyMemoryTranslator

# Atur default timeout socket global agar tidak pernah menggantung (hang) 21 detik di Windows
socket.setdefaulttimeout(5.0)

class SpeechTranslator:
    def __init__(self, source_lang="auto", target_lang="id"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.recognizer = sr.Recognizer()
        
        # Pengaturan agar lebih responsif terhadap vokal game
        self.recognizer.energy_threshold = 280
        self.recognizer.dynamic_energy_threshold = False
        
        # Cache terjemahan
        self.translation_cache = {}
        self.last_stt_time = 0.0

    def is_error_response(self, text):
        """Memeriksa apakah hasil terjemahan adalah pesan error server/HTML."""
        if not text:
            return True
        lower = text.lower()
        error_signatures = [
            "error 500", "server error", "that's an error", 
            "please try again later", "429", "too many requests", 
            "rate limit", "service unavailable", "bad gateway",
            "internal error", "error 403", "forbidden", "captcha",
            "that’s an error"
        ]
        for sig in error_signatures:
            if sig in lower:
                return True
        if "<html" in lower or "<!doctype" in lower or "<head" in lower:
            return True
        return False

    def translate(self, text, src="auto", dest="id"):
        """
        Penerjemah Multi-Tier:
        1. GoogleTranslator (DeepTranslator)
        2. Fallback: MyMemoryTranslator
        3. Fallback akhir: Kembalikan teks asli (jangan pernah menampilkan pesan error server ke layar!)
        """
        clean_text = text.strip()
        if not clean_text:
            return ""

        # Cek cache
        cache_key = f"{src}->{dest}:{clean_text}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        translated_result = None

        # Tier 1: Google Translator
        try:
            res = GoogleTranslator(source=src, target=dest).translate(clean_text)
            if res and not self.is_error_response(res):
                translated_result = res.strip()
        except Exception as e:
            pass # Silent fallback ke tier 2

        # Tier 2: MyMemory Translator jika Tier 1 gagal atau timeout
        if not translated_result:
            try:
                src_mm = "en-US" if src in ["auto", "en"] else src
                dest_mm = "id-ID" if dest == "id" else dest
                res = MyMemoryTranslator(source=src_mm, target=dest_mm).translate(clean_text)
                if res and not self.is_error_response(res):
                    translated_result = res.strip()
            except Exception as e:
                pass

        # Tier 3: Jika semua translator offline, gunakan teks asli agar tidak merusak tampilan UI
        if not translated_result or self.is_error_response(translated_result):
            translated_result = clean_text

        # Simpan di cache (maksimal 200 item)
        if len(self.translation_cache) > 200:
            self.translation_cache.clear()
        self.translation_cache[cache_key] = translated_result

        return translated_result

    def process_speech_chunk(self, raw_pcm_bytes, sample_rate, channels, source_lang=None, target_lang=None):
        """
        Menerima raw PCM bytes dari WASAPI Loopback, melakukan STT via HTTPS aman, lalu menerjemahkan.
        """
        if not raw_pcm_bytes:
            return None

        # Minimal gap 0.15 detik antar request untuk mencegah flood/throttle server
        now = time.time()
        if now - self.last_stt_time < 0.15:
            time.sleep(0.15)
        self.last_stt_time = time.time()

        src_lang = source_lang or self.source_lang
        dest_lang = target_lang or self.target_lang

        try:
            import numpy as np
            audio_array = np.frombuffer(raw_pcm_bytes, dtype=np.int16)
            
            # 1. Konversi Stereo ke Mono
            if channels == 2:
                mono_array = ((audio_array[0::2].astype(np.int32) + audio_array[1::2].astype(np.int32)) // 2).astype(np.int16)
            else:
                mono_array = audio_array

            # 2. Optimalisasi Downsampling ke 16.000 Hz untuk kecepatan transmisi maksimal
            if sample_rate == 48000:
                mono_array = mono_array[::3]
                target_rate = 16000
            elif sample_rate == 44100:
                target_rate = 44100
            else:
                target_rate = sample_rate

            # Minimal durasi audio 0.45 detik (7200 sampel pada 16kHz)
            if len(mono_array) < target_rate * 0.45:
                return None

            audio_data = sr.AudioData(mono_array.tobytes(), target_rate, 2)

            # 3. Speech-to-Text via HTTPS Endpoint (Mencegah blokir/timeout WinError 10060 dari ISP)
            original_text = ""
            try:
                lang_code = "en-US" if src_lang in ["auto", "en"] else src_lang
                try:
                    original_text = self.recognizer.recognize_google(
                        audio_data, 
                        language=lang_code,
                        endpoint="https://www.google.com/speech-api/v2/recognize"
                    )
                except Exception:
                    original_text = self.recognizer.recognize_google(
                        audio_data, 
                        language=lang_code
                    )
            except sr.UnknownValueError:
                # Suara hening atau hanya kebisingan latar/klik mouse
                return None
            except (socket.timeout, TimeoutError, OSError, ConnectionError, urllib.error.URLError) as e:
                # Timeout jaringan sesaat - ditangani dengan elegan tanpa crash
                print(f"[STT JARINGAN SIBUK] Timeout sesaat saat menghubungi server STT, melanjutkan ke audio berikutnya.")
                return None
            except sr.RequestError as e:
                print(f"[STT REQUEST ERROR] {e}")
                return None

            if not original_text or len(original_text.strip()) < 2:
                return None

            print(f"[WASAPI TERDENGAR] \"{original_text}\"")

            # 4. Terjemahkan ke Bahasa Target
            translated_text = self.translate(original_text, src="auto", dest=dest_lang)
            print(f"[HASIL TERJEMAHAN] \"{translated_text}\"")

            return {
                "success": True,
                "speaker": "Game/System Audio",
                "original_text": original_text,
                "translated_text": translated_text
            }

        except Exception as e:
            # Cegah pencetakan exception yang tidak perlu jika hanya timeout socket
            if "10060" in str(e) or "timed out" in str(e):
                print(f"[STT TIMEOUT] Server STT sedang sibuk, melewati chunk...")
            else:
                print(f"[PROCESS AUDIO ERROR] {e}")
            return None
