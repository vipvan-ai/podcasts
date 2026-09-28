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

DIALOGUE = [
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[cheerful] Welcome back to Future Human Daily, everyone! Today we are diving straight into the wild intersection of generative AI and bio-science—specifically, designing synthetic proteins from scratch."
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[chuckles] Oh, I've been waiting all week to talk about this! What machine learning models are doing with de novo protein design right now is honestly dizzying."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[playfully] Right? I mean, did you see the latest breakthrough where AI designed a completely custom enzyme that never existed in four billion years of biological evolution?"
    },
    {
        "speaker": "Alex",
        "voice": "Puck",
        "text": "[amazed] Stop, I replayed that lab demo twice! [chuckles] When the researchers synthesized the AI sequence in a test tube, it actually worked on the very first try."
    },
    {
        "speaker": "Elena",
        "voice": "Kore",
        "text": "[thoughtfully] It really blurs the line between discovering nature and compiling biological software, so grab your coffee, folks, because we have a lot to unpack today."
    }
]

def apply_alex_warmth(samples, sample_rate=24000):
    b_highcut, a_highcut = signal.butter(2, 7500 / (sample_rate / 2), btype='low')
    samples = signal.filtfilt(b_highcut, a_highcut, samples)
    f0, Q, gain_db = 150.0, 1.0, 4.0
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
    return signal.filtfilt(b, a, samples)

def build_alex_elena_sample():
    print("==========================================================", flush=True)
    print("Building Alex (Puck + Warmth) & Elena (Kore) Bio-Science", flush=True)
    print("==========================================================", flush=True)
    sample_rate = 24000
    combined = []
    silence = np.zeros(int(sample_rate * 0.35), dtype=np.float32)
    b_hp, a_hp = signal.butter(2, 80 / (sample_rate / 2), btype='high')

    TTS_MODELS = [
        'gemini-3.8-flash-lite-tts',
        'gemini-3.1-flash-tts-preview',
        'gemini-2.5-flash-preview-tts'
    ]

    for idx, turn in enumerate(DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]

        raw_bytes = None
        for model in TTS_MODELS:
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
                    print(f" -> Synthesized [{speaker} ({voice})] via {model}", flush=True)
                    break
            except Exception as e:
                time.sleep(2)

        if raw_bytes:
            s = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            s -= np.mean(s)
            s = signal.filtfilt(b_hp, a_hp, s)

            if speaker == "Alex":
                s = apply_alex_warmth(s, sample_rate)

            # 20ms fade
            fade_len = int(sample_rate * 0.02)
            if len(s) > 2 * fade_len:
                fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
                fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
                s[:fade_len] *= fade_in
                s[-fade_len:] *= fade_out

            combined.append(s)
            combined.append(silence)
            time.sleep(2)

    full = np.concatenate(combined)
    max_p = np.max(np.abs(full))
    if max_p > 0: full = full * (0.891 / max_p)

    out_file = AUDIO_DIR / "sample_15_alex_elena_bioscience.mp3"
    sf.write(str(out_file), full, sample_rate)
    print(f"[COMPLETE] Saved: {out_file}", flush=True)

if __name__ == "__main__":
    build_alex_elena_sample()
