"""
Modul Audio Capture WASAPI Loopback (Windows).
Menyadap langsung aliran audio keluaran speaker/headphone komputer secara real-time
dengan kontrol antrean non-blocking dan pengaturan sensitivitas dinamis.
"""

import sys
import time
import queue
import threading
import numpy as np
import pyaudiowpatch as pyaudio
from speech_translator import SpeechTranslator

class LoopbackAudioCapture:
    def __init__(self, broadcast_callback, volume_callback=None, threshold_rms=38.0):
        self.broadcast_callback = broadcast_callback
        self.volume_callback = volume_callback
        self.threshold_rms = float(threshold_rms)
        self.running = False
        self.is_paused = False
        
        self.p = None
        self.stream = None
        self.audio_queue = queue.Queue(maxsize=3) # Maksimal 3 chunk agar subtitle tidak pernah delay
        self.translator = SpeechTranslator(source_lang="auto", target_lang="id")
        
        # Buffer penampung suara
        self.speech_buffer = []
        self.is_recording_speech = False
        self.silence_frames = 0
        self.sample_rate = 48000
        self.channels = 2

    def update_config(self, threshold=None, source_lang=None, target_lang=None, paused=None):
        """Memperbarui konfigurasi secara dinamis dari antarmuka Web GUI."""
        if threshold is not None:
            self.threshold_rms = float(threshold)
            print(f"[CONFIG UPDATE] Sensitivitas Ambang RMS diubah ke: {self.threshold_rms}")
        if source_lang is not None:
            self.translator.source_lang = source_lang
            print(f"[CONFIG UPDATE] Bahasa Sumber diubah ke: {source_lang}")
        if target_lang is not None:
            self.translator.target_lang = target_lang
            print(f"[CONFIG UPDATE] Bahasa Target diubah ke: {target_lang}")
        if paused is not None:
            self.is_paused = bool(paused)
            print(f"[CONFIG UPDATE] Status Sadap Audio Dijeda: {self.is_paused}")

    def find_loopback_device(self):
        """Mencari perangkat audio output default yang memiliki mode loopback."""
        self.p = pyaudio.PyAudio()
        try:
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self.p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            loopback_dev = None
            for dev in self.p.get_loopback_device_info_generator():
                if default_speakers["name"] in dev["name"]:
                    loopback_dev = dev
                    break
            
            if not loopback_dev:
                for dev in self.p.get_loopback_device_info_generator():
                    loopback_dev = dev
                    break
                    
            return default_speakers, loopback_dev
        except Exception as e:
            print(f"[WASAPI SCAN ERROR] {e}")
            return None, None

    def start(self):
        default_speakers, loopback_dev = self.find_loopback_device()
        if not loopback_dev:
            print("[AUDIO CAPTURE] Gagal menemukan perangkat loopback audio.")
            return False

        self.sample_rate = int(loopback_dev["defaultSampleRate"])
        self.channels = int(loopback_dev["maxInputChannels"])
        
        print(f"[AUDIO CAPTURE] Terhubung ke: {loopback_dev['name']}")
        print(f"[AUDIO CAPTURE] Sample Rate: {self.sample_rate} Hz, Channels: {self.channels}")

        self.running = True
        
        # Jalankan worker penerjemah di background
        self.worker_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.worker_thread.start()

        def audio_callback(in_data, frame_count, time_info, status):
            if not self.running:
                return (None, pyaudio.paAbort)
                
            if self.is_paused:
                return (None, pyaudio.paContinue)

            # Hitung volume (RMS)
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            if len(audio_data) > 0:
                rms = float(np.sqrt(np.mean(audio_data.astype(np.float64)**2)))
            else:
                rms = 0.0

            if self.volume_callback:
                self.volume_callback(rms)

            # Voice Activity Detection (VAD)
            silence_limit = int(self.sample_rate / frame_count * 0.65) # ~0.65 detik hening tanda selesai bicara
            max_speech_frames = int(self.sample_rate / frame_count * 5.5) # Maksimal 5.5 detik per kalimat

            if rms > self.threshold_rms:
                self.speech_buffer.append(in_data)
                self.is_recording_speech = True
                self.silence_frames = 0
                
                # Jika sudah mencapai durasi maksimal, langsung proses
                if len(self.speech_buffer) >= max_speech_frames:
                    full_chunk = b''.join(self.speech_buffer)
                    self._enqueue_audio(full_chunk)
                    self.speech_buffer = []
                    self.is_recording_speech = False
            else:
                if self.is_recording_speech:
                    self.speech_buffer.append(in_data)
                    self.silence_frames += 1
                    
                    if self.silence_frames > silence_limit:
                        # Pembicara selesai mengucapkan satu kalimat
                        min_frames = int(self.sample_rate / frame_count * 0.45) # Minimal 0.45 detik
                        if len(self.speech_buffer) >= min_frames:
                            full_chunk = b''.join(self.speech_buffer)
                            self._enqueue_audio(full_chunk)
                        
                        self.speech_buffer = []
                        self.is_recording_speech = False
                        self.silence_frames = 0

            return (None, pyaudio.paContinue)

        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=loopback_dev["index"],
                stream_callback=audio_callback,
                frames_per_buffer=1024
            )
            self.stream.start_stream()
            print("[AUDIO CAPTURE] Sedang mendengarkan suara sistem komputer (WASAPI Loopback)...")
            return True
        except Exception as e:
            print(f"[AUDIO CAPTURE ERROR] Gagal membuka stream: {e}")
            return False

    def _enqueue_audio(self, chunk):
        """Memasukkan audio ke antrean; jika antrean penuh, hapus yang tertua agar real-time."""
        if self.audio_queue.full():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                pass
        self.audio_queue.put(chunk)

    def _transcription_worker(self):
        """Worker thread mandiri untuk memproses transkripsi tanpa memblokir stream audio."""
        while self.running:
            try:
                audio_bytes = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                result = self.translator.process_speech_chunk(
                    audio_bytes, 
                    sample_rate=self.sample_rate, 
                    channels=self.channels
                )
                if result and result.get("success"):
                    self.broadcast_callback(
                        result["speaker"],
                        result["original_text"],
                        result["translated_text"]
                    )
            except Exception as e:
                if "10060" not in str(e):
                    print(f"[WORKER ERROR] {e}")

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        if self.p:
            try:
                self.p.terminate()
            except Exception:
                pass
