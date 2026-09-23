# Game Voice Translator Overlay

A lightweight, real-time in-game voice communication subtitle and translation overlay for Windows.

The application captures incoming team audio directly from your audio output device using Windows WASAPI Loopback, isolates voice activity, translates speech into Indonesian, and displays subtitles in an always-on-top transparent overlay without game performance degradation.

## Features

- **System Audio Loopback**: Captures Discord, game voice chat, or system audio directly via WASAPI Loopback without requiring virtual audio cables.
- **Voice Activity Detection**: Filters out loud game sound effects (gunfire, explosions) to process only vocal frequencies.
- **Always-On-Top Transparent Overlay**: Minimalist HUD window built with WebView2 that floats seamlessly above borderless full-screen games.
- **Low Resource Usage**: Optimized memory footprint to ensure game frame rates remain unaffected.
- **Customizable Appearance**: Adjustable font size, background opacity, text color, and hotkey toggles.

## Prerequisites

- Windows 10 or 11 (64-bit)
- Python 3.10 or higher
- Microsoft Edge WebView2 Runtime

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/IlhamXkyo/TRSLT_RL_KYO_v1.git
   cd TRSLT_RL_KYO_v1
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```bash
   python main.py
   ```

## Hotkeys

- `Ctrl + Shift + H`: Toggle overlay visibility.
- `Ctrl + Shift + C`: Clear subtitle history.
- `Ctrl + Shift + Q`: Exit application.

## Tech Stack

- Python 3.10+
- PyAudio / WASAPI Loopback
- Microsoft Edge WebView2
- Whisper / Translation API

## License

MIT License. See LICENSE for details.
