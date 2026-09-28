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

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

DIALOGUE_NATURAL = [
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "Welcome back to Future Human Daily, everyone. Today we are diving straight into the wild intersection of generative AI and bio-science—specifically, designing synthetic proteins from scratch."
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "Oh, I have been waiting all week to talk about this! What machine learning models are doing with de novo protein design right now is honestly dizzying."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "Right? I mean, did you see the latest breakthrough where AI designed a completely custom enzyme that never existed in four billion years of biological evolution?"
    },
    {
        "speaker": "Rami",
        "voice": "Rami",
        "text": "Stop, I replayed that lab demo twice! When the researchers synthesized the AI sequence in a test tube, it actually worked on the very first try."
    },
    {
        "speaker": "Veda",
        "voice": "Veda",
        "text": "It really blurs the line between discovering nature and compiling biological software, so grab your coffee, folks, because we have a lot to unpack today."
    }
]

def clean_samples(samples, sample_rate=24000):
    b, a = signal.butter(2, 80 / (sample_rate / 2), btype='high')
    samples = signal.filtfilt(b, a, samples)

    abs_s = np.abs(samples)
    idx = np.where(abs_s > 0.005)[0]
    if len(idx) > 0:
        start_i = max(0, idx[0] - int(sample_rate * 0.01))
        end_i = min(len(samples), idx[-1] + int(sample_rate * 0.03))
        samples = samples[start_i:end_i]

    fade_len = int(sample_rate * 0.04)
    if len(samples) > 2 * fade_len:
        fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
        fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
        samples[:fade_len] *= fade_in
        samples[-fade_len:] *= fade_out

    return samples

def generate_natural_sample():
    print("==========================================================", flush=True)
    print("Building Natural Clean Sample (No Effect Tags)", flush=True)
    print("==========================================================", flush=True)
    
    sample_rate = 24000
    combined = []
    silence = np.zeros(int(sample_rate * 0.40), dtype=np.float32)

    for idx, turn in enumerate(DIALOGUE_NATURAL):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]

        raw_bytes = None
        for model in ['gemini-3.8-flash-lite-tts', 'gemini-3.8-flash-tts']:
            try:
                resp = client.models.generate_content(
                    model=model,
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
                    print(f" -> Turn {idx+1} [{speaker}] via {model}", flush=True)
                    break
            except Exception as e:
                time.sleep(2)

        if raw_bytes:
            s = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            cleaned = clean_samples(s, sample_rate)
            combined.append(cleaned)
            combined.append(silence)
            time.sleep(2)

    full = np.concatenate(combined)
    max_p = np.max(np.abs(full))
    if max_p > 0: full = full * (0.891 / max_p)

    out_path = AUDIO_DIR / "sample_11_veda_rami_natural_clean.mp3"
    sf.write(str(out_path), full, sample_rate)
    print(f"[COMPLETE] Saved to {out_path}", flush=True)

if __name__ == "__main__":
    generate_natural_sample()
