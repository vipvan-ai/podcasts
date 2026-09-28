import os
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"

def spectral_denoise(audio, sr=24000, n_fft=2048, hop_length=512):
    """Applies Spectral Subtraction Noise Reduction to remove background hiss."""
    # STFT
    frequencies, times, Zxx = signal.stft(audio, fs=sr, nperseg=n_fft, noverlap=n_fft-hop_length)
    magnitude = np.abs(Zxx)
    phase = np.angle(Zxx)

    # Estimate noise spectrum from the quietest 10% of frames
    frame_energies = np.sum(magnitude**2, axis=0)
    quiet_frames = np.argsort(frame_energies)[:max(1, len(frame_energies) // 10)]
    noise_profile = np.mean(magnitude[:, quiet_frames], axis=1, keepdims=True)

    # Spectral subtraction (over-subtraction factor alpha=1.5, spectral floor beta=0.02)
    alpha = 1.8
    beta = 0.02
    subtracted_magnitude = magnitude**2 - alpha * (noise_profile**2)
    subtracted_magnitude = np.maximum(subtracted_magnitude, beta * (magnitude**2))
    clean_magnitude = np.sqrt(subtracted_magnitude)

    # Reconstruct STFT with original phase
    Zxx_clean = clean_magnitude * np.exp(1j * phase)
    _, clean_audio = signal.istft(Zxx_clean, fs=sr, nperseg=n_fft, noverlap=n_fft-hop_length)
    
    # Match length
    if len(clean_audio) > len(audio):
        clean_audio = clean_audio[:len(audio)]
    elif len(clean_audio) < len(audio):
        clean_audio = np.pad(clean_audio, (0, len(audio) - len(clean_audio)))

    return clean_audio

def process_sample():
    in_file = AUDIO_DIR / "sample_11_veda_rami_natural_clean.mp3"
    if not in_file.exists():
        print("Input file not found!")
        return

    data, sr = sf.read(str(in_file))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print("==========================================================")
    print("Applying Spectral Subtraction De-Noising Pass")
    print("==========================================================")

    # 1. 80Hz High Pass
    b_hp, a_hp = signal.butter(2, 80 / (sr / 2), btype='high')
    audio_hp = signal.filtfilt(b_hp, a_hp, data)

    # 2. Spectral Subtraction De-noising
    clean_speech = spectral_denoise(audio_hp, sr=sr)

    # 3. Peak normalize to -1.0 dBFS
    max_p = np.max(np.abs(clean_speech))
    if max_p > 0:
        clean_speech = clean_speech * (0.891 / max_p)

    out_file = AUDIO_DIR / "sample_12_veda_rami_spectral_denoised.mp3"
    sf.write(str(out_file), clean_speech, sr)
    print(f"[COMPLETE] Spectral De-Noised Sample Saved: {out_file}")

if __name__ == "__main__":
    process_sample()
