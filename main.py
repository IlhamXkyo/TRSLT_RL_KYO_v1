"""
Entry Point Aplikasi Desktop Game Voice Translator Overlay.
Menggunakan Win32 Native Message Loop (WM_NCLBUTTONDOWN) untuk Window Dragging & Resizing.
Menjamin 0% CPU lag, 100% responsif, dan bebas dari freezing / Not Responding.
"""

import sys
import os
import time
import ctypes
import threading
import webview
from server import start_server, PORT

# Pastikan konsol UTF-8 jika dijalankan dengan konsol atau arahkan ke log jika windowed
if sys.platform == "win32":
    if sys.stdout is None or sys.stderr is None:
        try:
            log_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            log_path = os.path.join(log_dir, "overlay_debug.log")
            log_file = open(log_path, "a", encoding="utf-8", buffering=1)
            if sys.stdout is None:
                sys.stdout = log_file
            if sys.stderr is None:
                sys.stderr = log_file
        except Exception:
            if sys.stdout is None:
                sys.stdout = open(os.devnull, "w")
            if sys.stderr is None:
                sys.stderr = open(os.devnull, "w")
    else:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

WM_NCLBUTTONDOWN = 0x00A1
HTCAPTION = 2
HTBOTTOMRIGHT = 17

class DesktopWindowApi:
    def __init__(self):
        self.hwnd = None

    def _get_hwnd(self):
        if not self.hwnd:
            self.hwnd = ctypes.windll.user32.FindWindowW(None, "Game Voice Translator Overlay")
        return self.hwnd

    def start_drag(self):
        """
        Memicu native Windows window dragging langsung via Win32 OS.
        Dipanggil HANYA SEKALI saat mousedown; Windows yang menangani pergerakan bebasnya.
        """
        try:
            hwnd = self._get_hwnd()
            if hwnd:
                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)
        except Exception:
            pass

    def start_resize(self):
        """
        Memicu native Windows corner resizing langsung via Win32 OS.
        Dipanggil HANYA SEKALI saat mousedown pada gripper pojok.
        """
        try:
            hwnd = self._get_hwnd()
            if hwnd:
                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTBOTTOMRIGHT, 0)
        except Exception:
            pass

def run_backend():
    """Menjalankan server backend dan penangkap suara WASAPI di thread terpisah."""
    start_server()

def main():
    # 1. Jalankan backend server di thread background
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Tunggu sejenak agar server siap
    time.sleep(0.8)

    # 2. Inisialisasi API Jendela Native Win32
    api = DesktopWindowApi()

    # 3. Buat jendela Desktop Floating Overlay
    # easy_drag=False agar tidak bentrok dengan handler native Win32 kami yang presisi
    window = webview.create_window(
        title="Game Voice Translator Overlay",
        url=f"http://127.0.0.1:{PORT}/index.html",
        width=480,
        height=260,
        x=120,
        y=120,
        resizable=True,
        frameless=True,       # Murni frameless tanpa batas OS
        on_top=True,          # ALWAYS ON TOP (selalu mengambang di atas game)
        transparent=True,     # Transparansi penuh
        easy_drag=False,      # Drag ditangani langsung via Win32 API WM_NCLBUTTONDOWN
        background_color='#000000',
        js_api=api
    )

    # 4. Jalankan GUI native WebView2
    webview.start(gui="edgechromium")

if __name__ == "__main__":
    main()
