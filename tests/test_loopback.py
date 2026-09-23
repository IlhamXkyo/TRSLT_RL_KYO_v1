"""
Modul Pengujian & Deteksi Perangkat Audio WASAPI Loopback (Windows).
Menangkap suara keluaran speaker/headphone (game/Discord) tanpa mengganggu audio asli.
"""

import sys
import os

# Pastikan output konsol Windows mendukung UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pyaudiowpatch as pyaudio
import numpy as np
import time

def scan_wasapi_loopback_devices():
    p = pyaudio.PyAudio()
    print("=" * 60)
    print("[SCAN] MEMINDAI PERANGKAT AUDIO SISTEM (WASAPI LOOPBACK)")
    print("=" * 60)

    try:
        # Dapatkan API WASAPI bawaan Windows
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError:
        print("[ERROR] Host API WASAPI tidak ditemukan di sistem Windows ini.")
        p.terminate()
        return None, None

    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    print(f"[OUTPUT DEFAULT] {default_speakers['name']}")

    # Cari perangkat loopback yang cocok dengan default speakers
    loopback_device = None
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                loopback_device = loopback
                break
        
        if loopback_device is None:
            # Fallback ke loopback pertama yang ditemukan
            for loopback in p.get_loopback_device_info_generator():
                loopback_device = loopback
                break
    else:
        loopback_device = default_speakers

    if loopback_device:
        print(f"[LOOPBACK DITEMUKAN] {loopback_device['name']} (Index: {loopback_device['index']})")
        print(f"  - Max Input Channels: {loopback_device['maxInputChannels']}")
        print(f"  - Default Sample Rate: {int(loopback_device['defaultSampleRate'])} Hz")
    else:
        print("[WARNING] Tidak ditemukan perangkat loopback aktif.")

    p.terminate()
    return default_speakers, loopback_device

def test_record_loopback(duration_seconds=3):
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        # Cari loopback device
        loopback_device = None
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                loopback_device = loopback
                break
        if loopback_device is None:
            for loopback in p.get_loopback_device_info_generator():
                loopback_device = loopback
                break

        if not loopback_device:
            print("[ERROR] Gagal memulai rekaman: Loopback device tidak ditemukan.")
            p.terminate()
            return

        sample_rate = int(loopback_device["defaultSampleRate"])
        channels = int(loopback_device["maxInputChannels"])
        chunk_size = 1024

        print(f"\n[RECORD TEST] Menguji Perekaman System Audio ({duration_seconds} detik)...")
        print("[INFO] Putar audio (YouTube / Game / Musik) di komputer untuk melihat indikator level suara.\n")

        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=loopback_device["index"],
            frames_per_buffer=chunk_size
        )

        start_time = time.time()
        max_rms = 0.0

        while time.time() - start_time < duration_seconds:
            data = stream.read(chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            # Hitung RMS (Volume Level)
            rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
            if rms > max_rms:
                max_rms = rms
            
            bars = int(min(30, rms / 150))
            meter = "#" * bars + "-" * (30 - bars)
            print(f"\rLevel Audio: [{meter}] RMS: {rms:6.1f}", end="", flush=True)

        print("\n\n[SELESAI] Pengujian loopback selesai!")
        print(f"[HASIL] Volume Maksimal Terdeteksi: {max_rms:.1f}")
        if max_rms > 30:
            print("[STATUS] SUKSES: Suara sistem output komputer berhasil disadap secara jernih!")
        else:
            print("[STATUS] INFO: Suara sistem tenang/senyap saat pengujian.")

        stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
    finally:
        p.terminate()

if __name__ == "__main__":
    scan_wasapi_loopback_devices()
    test_record_loopback(duration_seconds=3)
