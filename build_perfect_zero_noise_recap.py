import soundfile as sf
import numpy as np
import noisereduce as nr
import scipy.signal as signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def process_spectral_clean_recap():
    in_wav = AUDIO_DIR / "sample_17_weekend_recap_zero_kshhh.wav"
    if not in_wav.exists():
        print("Source WAV not found!")
        return

    data, sr = sf.read(str(in_wav))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print("==========================================================")
    print("Applying Spectral Denoising & Zero-Noise Cross-Fade")
    print("==========================================================")

    # 1. High-Pass filter at 80Hz to strip sub-bass rumble
    b_hp, a_hp = signal.butter(2, 80 / (sr / 2), btype='high')
    data = signal.filtfilt(b_hp, a_hp, data)

    # 2. Extract stationary noise profile from silence gaps
    # Gap regions are where amplitude < 0.001
    silence_mask = np.abs(data) < 0.001
    noise_clip = data[silence_mask]
    
    if len(noise_clip) > sr:
        # Spectral noise reduction using noisereduce package
        print(" -> Running Spectral Subtraction Denoising...")
        clean_data = nr.reduce_noise(y=data, sr=sr, y_noise=noise_clip[:sr*2], prop_decrease=0.85, stationary=True)
    else:
        print(" -> Running Stationary Spectral Denoising...")
        clean_data = nr.reduce_noise(y=data, sr=sr, prop_decrease=0.85, stationary=True)

    # 3. Apply soft downward expander (gate) to force true silence during pauses
    win_len = int(sr * 0.02) # 20ms
    num_wins = len(clean_data) // win_len
    env = np.zeros_like(clean_data)

    for i in range(num_wins):
        s = i * win_len
        e = s + win_len
        env[s:e] = np.sqrt(np.mean(clean_data[s:e]**2))

    # Smooth energy envelope (50ms)
    smooth_win = int(sr * 0.05)
    env = np.convolve(env, np.ones(smooth_win)/smooth_win, mode='same')

    # Gate threshold at -36 dBFS (0.015)
    thresh = 0.015
    gain = np.ones_like(clean_data)
    below = env < thresh
    gain[below] = np.clip((env[below] / thresh)**2, 0.0, 1.0)

    # Smooth gain transition to avoid clicks (30ms window)
    gain_win = int(sr * 0.03)
    gain = np.convolve(gain, np.ones(gain_win)/gain_win, mode='same')

    final_audio = clean_data * gain

    # Peak normalize to -1.0 dBFS (0.891)
    max_p = np.max(np.abs(final_audio))
    if max_p > 0:
        final_audio = final_audio * (0.891 / max_p)

    out_mp3 = AUDIO_DIR / "sample_19_spectral_denoised_zero_kshhh.mp3"
    out_wav = AUDIO_DIR / "sample_19_spectral_denoised_zero_kshhh.wav"

    sf.write(str(out_wav), final_audio, sr)
    sf.write(str(out_mp3), final_audio, sr)

    print("==========================================================")
    print(f"[COMPLETE] Saved Sample 19: {out_mp3}")
    print(f"Duration: {len(final_audio)/sr:.2f}s")
    print("==========================================================")

if __name__ == "__main__":
    process_spectral_clean_recap()
