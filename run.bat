@echo off
title Game Voice Translator Overlay
echo ========================================================
echo   GAME VOICE TRANSLATOR - WASAPI REAL-TIME LOOPBACK
echo ========================================================
echo.
echo [1/2] Menjalankan Audio Engine & Server Streaming...
start "" "http://localhost:8765/index.html"
.\.venv\Scripts\python.exe server.py
pause
