import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def fix_intra_sentence_phrase_noise(audio, sr=24000):
    """Surgically duck-filters room noise during intra-sentence phrase pauses."""
    # 1. High Pass 80Hz filter
    b, a = signal.butter(2, 80 / (sr / 2), btype='high')
    audio = signal.filtfilt(b, a, audio)

    # 2. Windowed RMS energy envelope (15ms window)
    win_samples = int(sr * 0.015)
    num_wins = len(audio) // win_samples
    envelope = np.zeros(len(audio), dtype=np.float32)

    for i in range(num_wins):
        start = i * win_samples
        end = start + win_samples
        rms = np.sqrt(np.mean(audio[start:end]**2))
        envelope[start:end] = rms

    # Tail samples
    if len(audio) > num_wins * win_samples:
        envelope[num_wins * win_samples:] = np.sqrt(np.mean(audio[num_wins * win_samples:]**2))

    # Smooth the envelope with a 30ms moving average to avoid choppy gating
    smooth_win = int(sr * 0.03)
    envelope = np.convolve(envelope, np.ones(smooth_win)/smooth_win, mode='same')

    # 3. Apply Adaptive Downward Expander (Gain Curve)
    # Speech threshold at -38 dBFS (0.0125). Below threshold, attenuate smoothly.
    thresh = 0.0125
    gain = np.ones_like(audio, dtype=np.float32)
    
    below_mask = envelope < thresh
    # Soft ratio expansion
    ratio = (envelope[below_mask] / thresh) ** 1.5
    gain[below_mask] = np.clip(ratio, 0.02, 1.0)

    # Smooth the gain curve to prevent clicks
    gain_smooth_win = int(sr * 0.02)
    gain = np.convolve(gain, np.ones(gain_smooth_win)/gain_smooth_win, mode='same')

    clean_audio = audio * gain
    return clean_audio

def process_full_track():
    in_file = AUDIO_DIR / "sample_09_veda_rami_bioscience_ai.mp3"
    if not in_file.exists():
        print("Input file not found!")
        return

    data, sr = sf.read(str(in_file))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print("==========================================================")
    print("Applying Intra-Sentence Phrase Pause Noise Expander")
    print("==========================================================")

    clean_track = fix_intra_sentence_phrase_noise(data, sr)

    # Peak normalize
    max_p = np.max(np.abs(clean_track))
    if max_p > 0:
        clean_track = clean_track * (0.891 / max_p)

    out_file = AUDIO_DIR / "sample_14_veda_rami_no_intraturn_noise.mp3"
    sf.write(str(out_file), clean_track, sr)
    print(f"[COMPLETE] Intra-Turn Noise Expander Saved: {out_file}")

if __name__ == "__main__":
    process_full_track()
