"""
Skrip Otomatisasi Kompilasi PyInstaller ke Standalone Windows .EXE.
Menyertakan semua aset web (HTML, CSS, JS) dan dependensi audio/native webview.
"""

import os
import sys
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def build():
    print("=" * 60)
    print("[BUILD] MEMULAI PROSES KOMPILASI KE WINDOWS STANDALONE .EXE")
    print("=" * 60)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")

    pyinstaller_cmd = [
        os.path.join(project_dir, ".venv", "Scripts", "pyinstaller.exe"),
        "--noconfirm",
        "--onedir",                       # Mode onedir jauh lebih cepat dibuka tanpa lag ekstrak
        "--windowed",                     # Tanpa konsol hitam (murni floating window)
        "--name", "VoiceTranslatorOverlay",
        "--add-data", f"{os.path.join(project_dir, 'index.html')};.",
        "--add-data", f"{os.path.join(project_dir, 'styles.css')};.",
        "--add-data", f"{os.path.join(project_dir, 'app.js')};.",
        "--hidden-import", "pyaudiowpatch",
        "--hidden-import", "deep_translator",
        "--hidden-import", "speech_recognition",
        "--hidden-import", "webview",
        "--hidden-import", "clr_loader",
        "--hidden-import", "pythonnet",
        "--hidden-import", "urllib.request",
        "--hidden-import", "http.server",
        "--collect-all", "deep_translator",
        "--collect-all", "speech_recognition",
        os.path.join(project_dir, "main.py")
    ]

    print("Perintah:", " ".join(pyinstaller_cmd))
    result = subprocess.run(pyinstaller_cmd, cwd=project_dir)
    
    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "VoiceTranslatorOverlay", "VoiceTranslatorOverlay.exe")
        print("\n" + "=" * 60)
        print("[SUKSES] KOMPILASI BERHASIL!")
        print(f"[PATH] File Executable: {exe_path}")
        print("=" * 60)
    else:
        print(f"\n[GAGAL] Kompilasi gagal dengan return code: {result.returncode}")

if __name__ == "__main__":
    build()
