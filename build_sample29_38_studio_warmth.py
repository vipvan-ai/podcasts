import soundfile as sf
import numpy as np
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def apply_broadcast_studio_warmth_eq(audio_samples, sample_rate=24000, low_boost_db=4.5, high_cut_hz=6800.0):
    if len(audio_samples) < 500:
        return audio_samples

    # 1. 80Hz High Pass to eliminate DC offset / sub-bass rumble
    b_hp, a_hp = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    audio_samples = signal.filtfilt(b_hp, a_hp, audio_samples)

    # 2. Steep 6.8kHz Low Pass filter to eliminate high-frequency hiss / sibilance scratch
    b_lp, a_lp = signal.butter(4, high_cut_hz / (sample_rate / 2), btype='low')
    audio_samples = signal.filtfilt(b_lp, a_lp, audio_samples)

    # 3. Warm 150Hz Peak Filter (+4.5 dB)
    f0 = 150.0
    Q = 0.9
    gain_db = low_boost_db
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sample_rate
    alpha = np.sin(w0) / (2 * Q)
    
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    b_eq = np.array([b0, b1, b2]) / a0
    a_eq = np.array([a0, a1, a2]) / a0

    audio_samples = signal.filtfilt(b_eq, a_eq, audio_samples)
    return audio_samples

def build_sample29():
    in_wav = AUDIO_DIR / "sample_17_weekend_recap_zero_kshhh.wav"
    if not in_wav.exists():
        print("Sample 17 WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1: data = np.mean(data, axis=1)

    print("==========================================================")
    print("Building Sample 29: Gemini 3.8 + Studio Warmth EQ Pass")
    print("==========================================================")

    # 4 main turns from sample 17
    main_gaps = [
        (0, 400800),         # Turn 1 (Veda)
        (415200, 664800),    # Turn 2 (Rami)
        (674400, 849600),    # Turn 3 (Veda)
        (864000, 1156800)    # Turn 4 (Rami)
    ]

    cleaned_turns = []
    silence_gap = np.zeros(int(sr * 0.35), dtype=np.float32)

    for idx, (s, e) in enumerate(main_gaps):
        turn_samples = data[s:e]
        
        # Apply Studio Warmth EQ Pass to Gemini 3.8 turns
        warm_turn = apply_broadcast_studio_warmth_eq(turn_samples, sr, low_boost_db=4.5, high_cut_hz=6800.0)

        # 25ms Cosine S-curve boundary fade
        fade_len = int(sr * 0.025)
        if len(warm_turn) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            warm_turn[:fade_len] *= fade_in
            warm_turn[-fade_len:] *= fade_out

        print(f" -> Turn {idx+1}: Studio Warmth EQ pass applied (+4.5dB @ 150Hz, 6.8kHz High-Cut)")
        cleaned_turns.append(warm_turn)
        cleaned_turns.append(silence_gap)

    full_track = np.concatenate(cleaned_turns)

    # Peak normalize
    max_p = np.max(np.abs(full_track))
    if max_p > 0: full_track = full_track * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_29_38_studio_warmth_veda_rami.mp3"
    out_wav = AUDIO_DIR / "sample_29_38_studio_warmth_veda_rami.wav"

    sf.write(str(out_wav), full_track, sr)
    sf.write(str(out_mp3), full_track, sr)

    duration = len(full_track) / sr
    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 29: {out_mp3}")
    print(f"Duration: {duration:.2f}s (4 turns, 3 transitions)")
    print("==========================================================")

if __name__ == "__main__":
    build_sample29()
