import os
import time
import base64
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio" / "voice_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

DIALOGUE = [
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[upbeat] Welcome back to Future Human Daily, everyone! Today we are diving straight into the wild intersection of generative AI and bio-science—specifically, designing synthetic proteins from scratch."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[chuckles] Oh, I've been waiting all week to talk about this! What machine learning models are doing with de novo protein design right now is honestly dizzying."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[playfully] Right? I mean, did you see the latest breakthrough where AI designed a completely custom enzyme that never existed in four billion years of biological evolution?"
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "[amazed] Stop, I replayed that lab demo twice! [chuckles] When the researchers synthesized the AI sequence in a test tube, it actually worked on the very first try."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "[thoughtfully] It really blurs the line between discovering nature and compiling biological software, so grab your coffee, folks, because we have a lot to unpack today."
    }
]

def clean_turn_audio(samples, sample_rate=24000):
    """Surgically trims trailing noise floor and applies smooth 50ms boundary fades."""
    if len(samples) < 1000:
        return samples

    # 1. High Pass 80Hz Butterworth Filter to strip DC offset & sub-bass thumps
    b, a = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    samples = signal.filtfilt(b, a, samples)

    # 2. Trim trailing silence/noise floor: find last sample with amplitude > -40dB (0.01)
    threshold = 0.01
    abs_samples = np.abs(samples)
    nonzero_indices = np.where(abs_samples > threshold)[0]
    
    if len(nonzero_indices) > 0:
        last_speech_idx = min(len(samples), nonzero_indices[-1] + int(sample_rate * 0.05)) # Keep 50ms after speech ends
        samples = samples[:last_speech_idx]
    
    first_speech_idx = max(0, nonzero_indices[0] - int(sample_rate * 0.01)) if len(nonzero_indices) > 0 else 0
    samples = samples[first_speech_idx:]

    # 3. Apply 50ms Cosine S-Curve Fade-In and Fade-Out
    fade_len = int(sample_rate * 0.05) # 50ms
    if len(samples) > 2 * fade_len:
        fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
        fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
        samples[:fade_len] *= fade_in
        samples[-fade_len:] *= fade_out

    return samples

def build_perfect_clean_sample():
    print("==========================================================")
    print("Building Perfect Clean Transitions (Zero Clicks / Pops)")
    print("==========================================================")

    sample_rate = 24000
    combined_audio = []
    silence_gap = np.zeros(int(sample_rate * 0.40), dtype=np.float32) # 400ms pure zero silence gap

    for idx, turn in enumerate(DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]

        # Synthesize via gemini-3.8-flash-lite-tts or gemini-3.8-flash-tts
        raw_bytes = None
        for model_name in ['gemini-3.8-flash-lite-tts', 'gemini-3.8-flash-tts']:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                            )
                        )
                    )
                )
                part = resp.candidates[0].content.parts[0]
                if part.inline_data:
                    data = part.inline_data.data
                    if isinstance(data, str): data = base64.b64decode(data)
                    raw_bytes = data
                    print(f" -> Turn {idx+1} [{speaker}] synthesized via {model_name}")
                    break
            except Exception as e:
                time.sleep(2)

        if not raw_bytes:
            print(f"Failed turn {idx+1}")
            continue

        raw_samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        cleaned_samples = clean_turn_audio(raw_samples, sample_rate)

        combined_audio.append(cleaned_samples)
        combined_audio.append(silence_gap)
        time.sleep(2)

    full_track = np.concatenate(combined_audio)
    
    # Peak normalize to -1.0 dBFS
    max_peak = np.max(np.abs(full_track))
    if max_peak > 0:
        full_track = full_track * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_10_veda_rami_perfect_clean.mp3"
    sf.write(str(out_file), full_track, sample_rate)
    
    print("==========================================================")
    print(f"[COMPLETE] Perfect Clean Sample Saved: {out_file}")
    print(f"Duration: {len(full_track)/sample_rate:.2f}s")
    print("==========================================================")

if __name__ == "__main__":
    build_perfect_clean_sample()
