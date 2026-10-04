import os
import numpy as np
import scipy.signal as signal
from scipy.signal import butter, sosfilt
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
CACHE_DIR = AUDIO_DIR / "trailer_cache"

TRAILER_TURNS = [
    ("turn_1_Kore.npy", "Maya"),
    ("turn_2_Puck.npy", "Julian"),
    ("turn_3_Kore.npy", "Maya"),
    ("turn_4_Puck.npy", "Julian"),
    ("turn_5_Kore.npy", "Maya"),
    ("turn_6_Puck.npy", "Julian"),
    ("turn_7_Kore.npy", "Maya"),
    ("turn_8_Puck.npy", "Julian"),
]

def clean_turn(x, sr=24000, gap_ms=60, max_artifact_ms=250, flat_thresh=0.3):
    """
    Future Human Daily Spectral Flatness Measure & Active Energy Run Grouping.
    Surgically eliminates Gemini buffer tail bursts and 'kshhh' transition noise.
    """
    x = np.asarray(x)
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    x = x.astype(np.float32) - x.mean()                 # remove DC

    hp = sosfilt(butter(4, 80, 'hp', fs=sr, output='sos'), x)
    fl = int(0.010 * sr)                                # 10 ms frames
    n = len(hp) // fl
    if n == 0: return x
    fr = hp[:n * fl].reshape(n, fl)

    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    active = db > (np.percentile(db, 95) - 35)

    spec = np.abs(np.fft.rfft(fr * np.hanning(fl), axis=1)) + 1e-9
    flat = np.exp(np.log(spec).mean(1)) / spec.mean(1)  # spectral flatness

    runs, s, last = [], None, None
    gap = gap_ms // 10
    for i, a in enumerate(active):
        if a:
            if s is None: s = i
            last = i
        elif s is not None and i - last > gap:
            runs.append((s, last + 1)); s = None
    if s is not None: runs.append((s, last + 1))
    if not runs: return x

    # drop trailing short, noise-like runs (the Gemini 'kshhh' / tail burst)
    while len(runs) > 1:
        a, b = runs[-1]
        if (b - a) * 10 < max_artifact_ms and flat[a:b].mean() > flat_thresh:
            print(f"    [clean_turn] Dropped noisy tail artifact run: frames {a}-{b} (flatness={flat[a:b].mean():.2f})")
            runs.pop()
        else:
            break

    start = max(0, runs[0][0] * fl - int(0.03 * sr))
    end = min(len(x), runs[-1][1] * fl + int(0.06 * sr))  # keep natural vocal decay
    y = x[start:end].copy()

    fi, fo = int(0.008 * sr), int(0.05 * sr)              # short fade in, longer fade out
    if len(y) > fi + fo:
        y[:fi] *= np.linspace(0, 1, fi)
        y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return y

def apply_studio_warmth_eq(audio_samples, sample_rate=24000):
    """Broadcast Studio Proximity EQ Pass (+4.0 dB @ 150Hz, 7.5kHz sibilance control)."""
    b_highcut, a_highcut = signal.butter(2, 7500 / (sample_rate / 2), btype='low')
    audio_samples = signal.filtfilt(b_highcut, a_highcut, audio_samples)

    f0 = 150.0
    Q = 1.0
    gain_db = 4.0
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / sample_rate
    alpha = np.sin(w0) / (2 * Q)
    
    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    return signal.filtfilt(b, a, audio_samples)

def build_perfect_clean_trailer():
    print("==========================================================")
    print("Remastering Trailer with Future Human Daily clean_turn & Room Tone")
    print("==========================================================")
    sample_rate = 24000
    audio_chunks = []
    pause_gap = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

    for idx, (filename, speaker) in enumerate(TRAILER_TURNS):
        file_path = CACHE_DIR / filename
        if not file_path.exists():
            print(f"Error: {file_path} missing!")
            return
        
        raw_samples = np.load(str(file_path))
        print(f"\nProcessing Turn {idx+1}/8 [{speaker}]: raw len={len(raw_samples)}")

        # 1. Surgical clean_turn from Future Human Daily
        cleaned = clean_turn(raw_samples, sample_rate)
        print(f"  -> Cleaned len: {len(cleaned)} (removed {len(raw_samples) - len(cleaned)} samples of boundary noise)")

        # 2. Studio Warmth EQ for Julian (Puck)
        if speaker == "Julian":
            cleaned = apply_studio_warmth_eq(cleaned, sample_rate)

        audio_chunks.append(cleaned)
        if idx < len(TRAILER_TURNS) - 1:
            audio_chunks.append(pause_gap)

    speech_track = np.concatenate(audio_chunks)

    # 3. Future Human Daily Continuous Studio Room Tone Bed (-52 dBFS noise floor)
    # Eliminates any digital void sensation between turns
    total_len = len(speech_track)
    np.random.seed(42)
    room_noise = np.random.normal(0, 1.0, total_len).astype(np.float32)
    b_room, a_room = signal.butter(2, [120 / (sample_rate / 2), 3500 / (sample_rate / 2)], btype='band')
    filtered_room = signal.filtfilt(b_room, a_room, room_noise)
    room_target_amp = 10 ** (-52.0 / 20.0) # ~0.00251
    filtered_room = filtered_room * (room_target_amp / (np.max(np.abs(filtered_room)) + 1e-9))

    # Mix speech track with continuous studio room bed
    full_audio = speech_track + filtered_room

    # 4. Peak normalize to -1.0 dBFS
    max_peak = np.max(np.abs(full_audio))
    if max_peak > 0:
        target_peak = 10 ** (-1.0 / 20.0) # ~0.89125
        full_audio = full_audio * (target_peak / max_peak)

    out_wav = AUDIO_DIR / "unwritten_code_trailer.wav"
    out_mp3 = AUDIO_DIR / "unwritten_code_trailer.mp3"

    sf.write(str(out_wav), full_audio, sample_rate)
    sf.write(str(out_mp3), full_audio, sample_rate)

    duration = len(full_audio) / sample_rate
    print("\n==========================================================")
    print(f"[COMPLETE] Perfectly Clean Trailer saved!")
    print(f"WAV: {out_wav}")
    print(f"MP3: {out_mp3}")
    print(f"Duration: {duration:.2f}s (~{int(duration // 60)}m {int(duration % 60)}s)")
    print("==========================================================")

if __name__ == "__main__":
    build_perfect_clean_trailer()
