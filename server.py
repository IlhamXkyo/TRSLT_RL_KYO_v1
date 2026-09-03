"""
Server Lokal & Bridge Antarmuka Subtitle Game (Multi-threaded HTTP + Thread-safe SSE Queue).
Menjamin transmisi data subtitle dari background audio worker ke browser tidak pernah terputus.
"""

import sys
import os
import time
import json
import queue
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from audio_capture import LoopbackAudioCapture

# Pastikan konsol Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Tentukan direktori aset web (mendukung bundel PyInstaller .exe)
if getattr(sys, 'frozen', False):
    WEB_DIR = sys._MEIPASS
else:
    WEB_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8765
client_queues = []
client_lock = threading.Lock()
audio_capture = None

class OverlayServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/config":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                threshold = data.get("threshold")
                source_lang = data.get("source_lang")
                target_lang = data.get("target_lang")
                paused = data.get("paused")
                
                if audio_capture:
                    audio_capture.update_config(
                        threshold=threshold,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        paused=paused
                    )
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            return
            
        super().do_POST()

    def do_GET(self):
        if self.path == "/events":
            # Endpoint SSE dengan antrean per-client yang aman (thread-safe)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            # Setiap tab browser memiliki antrean pesan tersendiri
            msg_queue = queue.Queue(maxsize=100)
            with client_lock:
                client_queues.append(msg_queue)

            print(f"[SSE CLIENT CONNECTED] Klien browser terhubung. Total klien aktif: {len(client_queues)}")

            try:
                # Kirim pesan pembuka
                init_msg = json.dumps({
                    "type": "connected", 
                    "status": "WASAPI LIVE",
                    "threshold": audio_capture.threshold_rms if audio_capture else 70.0
                })
                self.wfile.write(f"data: {init_msg}\n\n".encode("utf-8"))
                self.wfile.flush()
                
                while True:
                    try:
                        # Ambil pesan dari antrean dengan batas timeout 15 detik
                        msg = msg_queue.get(timeout=15.0)
                        self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        # Kirim SSE keep-alive comment agar koneksi tidak diputus browser
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError):
                pass
            finally:
                with client_lock:
                    if msg_queue in client_queues:
                        client_queues.remove(msg_queue)
                print(f"[SSE CLIENT DISCONNECTED] Klien terputus. Sisa klien aktif: {len(client_queues)}")
            return

        super().do_GET()

def broadcast_subtitle(speaker, original_text, translated_text):
    """Mengirim subtitle langsung ke seluruh antarmuka web overlay yang aktif."""
    if not original_text or not translated_text:
        return
        
    payload = {
        "type": "subtitle",
        "speaker": speaker,
        "original": original_text,
        "translated": translated_text,
        "timestamp": time.strftime("%H:%M:%S")
    }
    msg_str = json.dumps(payload, ensure_ascii=False)
    
    with client_lock:
        for q in client_queues:
            try:
                q.put_nowait(msg_str)
            except queue.Full:
                pass

last_volume_broadcast = 0.0

def broadcast_volume(rms):
    """Mengirim volume audio secara berkala (dibatasi 10x/detik agar tidak membanjiri socket)."""
    global last_volume_broadcast
    now = time.time()
    
    # Throttle ke maksimal 10Hz dan hanya saat ada suara terdeteksi
    if now - last_volume_broadcast > 0.1 and rms > 30.0:
        last_volume_broadcast = now
        payload = {
            "type": "volume",
            "rms": round(rms, 1)
        }
        msg_str = json.dumps(payload)
        with client_lock:
            for q in client_queues:
                try:
                    q.put_nowait(msg_str)
                except queue.Full:
                    pass

def start_server():
    global audio_capture
    
    # 1. Inisialisasi Audio Capture Loopback
    audio_capture = LoopbackAudioCapture(
        broadcast_callback=broadcast_subtitle,
        volume_callback=broadcast_volume,
        threshold_rms=38.0
    )
    
    audio_started = audio_capture.start()
    if not audio_started:
        print("[WARNING] Tidak dapat menyadap audio loopback secara otomatis.")

    # 2. Gunakan ThreadingHTTPServer agar tiap koneksi browser punya worker thread mandiri
    server_address = ("", PORT)
    httpd = ThreadingHTTPServer(server_address, OverlayServerHandler)
    httpd.daemon_threads = True
    
    print("=" * 65)
    print(f"🎮 REAL-TIME GAME VOICE TRANSLATOR (WASAPI ACTIVE)")
    print(f"🌐 Buka Overlay di: http://localhost:{PORT}/index.html")
    print("=" * 65)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Menghentikan server...")
        if audio_capture:
            audio_capture.stop()
        httpd.server_close()

if __name__ == "__main__":
    start_server()
