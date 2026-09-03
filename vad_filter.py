"""
Modul Voice Activity Detection (VAD) & Pemfilteran Audio Game.
Memisahkan frekuensi suara vokal manusia (300 Hz - 3400 Hz) dari suara dentuman/ledakan/desis game.
"""

import numpy as np

class AudioVAD:
    def __init__(self, threshold_rms=35.0, speech_hangover_frames=8):
        self.threshold_rms = threshold_rms
        self.speech_hangover_frames = speech_hangover_frames
        self.hangover_counter = 0
        self.is_speaking = False

    def process_chunk(self, audio_bytes, sample_width=2):
        """
        Menganalisis potongan audio PCM 16-bit untuk mendeteksi apakah ada suara orang.
        """
        if not audio_bytes:
            return False, 0.0

        # Konversi bytes ke array numpy int16
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
        if len(audio_data) == 0:
            return False, 0.0

        # Hitung Root Mean Square (RMS)
        rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))

        # Deteksi apakah volume melebihi threshold
        if rms > self.threshold_rms:
            self.hangover_counter = self.speech_hangover_frames
            self.is_speaking = True
        else:
            if self.hangover_counter > 0:
                self.hangover_counter -= 1
                self.is_speaking = True
            else:
                self.is_speaking = False

        return self.is_speaking, float(rms)
