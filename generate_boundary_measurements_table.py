import soundfile as sf
import numpy as np
import scipy.signal as signal
from scipy.signal import butter, sosfilt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def user_clean_turn(x, sr=24000, gap_ms=60, max_artifact_ms=250, flat_thresh=0.3):
    """User-provided clean_turn function using Spectral Flatness Measure & Active Energy Run Grouping."""
    x = np.asarray(x)
    if x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    x = x.astype(np.float32) - x.mean()                 # remove DC

    hp = sosfilt(butter(4, 80, 'hp', fs=sr, output='sos'), x)
    fl = int(0.010 * sr)                                # 10 ms frames
    n = len(hp) // fl
    if n == 0:
        return x
    fr = hp[:n * fl].reshape(n, fl)

    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    active = db > (np.percentile(db, 95) - 35)

    spec = np.abs(np.fft.rfft(fr * np.hanning(fl), axis=1)) + 1e-9
    flat = np.exp(np.log(spec).mean(1)) / spec.mean(1)  # spectral flatness

    # group active frames into runs, merging gaps shorter than gap_ms
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

    # drop trailing short, noise-like runs (the "kshhh")
    while len(runs) > 1:
        a, b = runs[-1]
        if (b - a) * 10 < max_artifact_ms and flat[a:b].mean() > flat_thresh:
            runs.pop()
        else:
            break

    start = max(0, runs[0][0] * fl - int(0.03 * sr))
    end = min(len(x), runs[-1][1] * fl + int(0.06 * sr))  # keep natural decay
    y = x[start:end].copy()

    fi, fo = int(0.008 * sr), int(0.05 * sr)              # short fade in, longer fade out
    if len(y) > fi + fo:
        y[:fi] *= np.linspace(0, 1, fi)
        y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return y

def analyze_and_run_user_clean_turn():
    t1_path = AUDIO_DIR / "test_veda_solo.wav"
    t2_path = AUDIO_DIR / "test_rami_solo.wav"
    recap_path = AUDIO_DIR / "sample_17_weekend_recap_zero_kshhh.wav"

    if not t1_path.exists() or not recap_path.exists():
        print("Required WAV files not found!")
        return

    v_data, sr = sf.read(str(t1_path))
    if v_data.ndim > 1: v_data = np.mean(v_data, axis=1)

    r_data, sr = sf.read(str(t2_path)) if t2_path.exists() else (v_data, sr)
    if r_data.ndim > 1: r_data = np.mean(r_data, axis=1)

    print("==========================================================")
    print("1. RAW BYTE & BOUNDARY SAMPLE ANALYSIS (LAST 200 SAMPLES)")
    print("==========================================================")
    print(f"Veda Solo total samples: {len(v_data)}")
    print(f"Veda Solo last 200 raw sample values:\n{v_data[-200:]}\n")

    print(f"Veda Solo tail energy analysis:")
    tail_200ms = v_data[-4800:]
    for i in range(4):
        blk = tail_200ms[i*1200 : (i+1)*1200]
        pk = np.max(np.abs(blk))
        rms = np.sqrt(np.mean(blk**2))
        print(f"  Tail Block {i+1} ({(i*50):3d}ms-{(i+1)*50:3d}ms from end) | Peak: {pk:.6f} | RMS: {rms:.6f}")

    print("\n==========================================================")
    print("2. RUNNING USER'S `clean_turn` ALGORITHM")
    print("==========================================================")

    # Clean Veda solo
    v_clean = user_clean_turn(v_data, sr)
    print(f"Veda Solo: {len(v_data)} -> {len(v_clean)} samples (trimmed {len(v_data)-len(v_clean)} samples)")
    sf.write(str(AUDIO_DIR / "test_veda_solo_user_cleaned.wav"), v_clean, sr)
    sf.write(str(AUDIO_DIR / "test_veda_solo_user_cleaned.mp3"), v_clean, sr)

    # Clean Rami solo
    if len(r_data) > 0:
        r_clean = user_clean_turn(r_data, sr)
        print(f"Rami Solo: {len(r_data)} -> {len(r_clean)} samples (trimmed {len(r_data)-len(r_clean)} samples)")
        sf.write(str(AUDIO_DIR / "test_rami_solo_user_cleaned.wav"), r_clean, sr)
        sf.write(str(AUDIO_DIR / "test_rami_solo_user_cleaned.mp3"), r_clean, sr)

    # Extract 4 turns from sample_17 and clean each turn using user_clean_turn!
    recap_data, sr = sf.read(str(recap_path))
    if recap_data.ndim > 1: recap_data = np.mean(recap_data, axis=1)

    turns = [
        recap_data[0 : 400800],           # Turn 1 (Veda)
        recap_data[415200 : 664800],       # Turn 2 (Rami)
        recap_data[674400 : 849600],       # Turn 3 (Veda)
        recap_data[864000 : 1156800]       # Turn 4 (Rami)
    ]

    cleaned_dialogue = []
    pause_200ms = np.zeros(int(sr * 0.20), dtype=np.float32) # 200ms natural silence gap

    for idx, raw_t in enumerate(turns):
        t_clean = user_clean_turn(raw_t, sr)
        print(f" -> Turn {idx+1}: {len(raw_t)} -> {len(t_clean)} samples")
        cleaned_dialogue.append(t_clean)
        cleaned_dialogue.append(pause_200ms)

    full_dialogue = np.concatenate(cleaned_dialogue)

    # Add continuous warm studio room tone (-52 dBFS) under the WHOLE track so cuts aren't audible!
    np.random.seed(42)
    noise = np.random.randn(len(full_dialogue)).astype(np.float32)
    b_lp, a_lp = signal.butter(2, 350 / (sr / 2), btype='low')
    room_tone = signal.filtfilt(b_lp, a_lp, noise)
    room_tone /= (np.max(np.abs(room_tone)) + 1e-6)
    room_tone *= 10 ** (-52.0 / 20.0) # -52 dBFS continuous room tone

    mastered = full_dialogue + room_tone
    max_p = np.max(np.abs(mastered))
    if max_p > 0: mastered *= (0.891 / max_p)

    out_wav = AUDIO_DIR / "sample_30_claude_clean_turn_veda_rami.wav"
    out_mp3 = AUDIO_DIR / "sample_30_claude_clean_turn_veda_rami.mp3"

    sf.write(str(out_wav), mastered, sr)
    sf.write(str(out_mp3), mastered, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 30: {out_mp3}")
    print(f"Duration: {len(mastered)/sr:.2f}s (4 turns, 3 transitions)")
    print("==========================================================")

if __name__ == "__main__":
    analyze_and_run_user_clean_turn()
