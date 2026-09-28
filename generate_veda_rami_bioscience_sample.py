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

# Load .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

TTS_MODELS = [
    'gemini-3.8-flash-tts',
    'gemini-3.8-flash-lite-tts',
    'gemini-3.1-flash-tts-preview'
]

# Bio Science & AI Interactive Dialogue matching AI Studio Playground style
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

def synthesize_turn(voice_name, text):
    for model_name in TTS_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    )
                )
            )
            part = resp.candidates[0].content.parts[0]
            if part.inline_data:
                data = part.inline_data.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                print(f" -> Synthesized [{voice_name}] via {model_name}: {text[:45]}...")
                return data
        except Exception as e:
            print(f" -> Model {model_name} rate limit / error: {e}. Trying next...")
            time.sleep(2)
    return None

def build_bioscience_sample():
    print("==========================================================")
    print("Synthesizing Veda & Rami Bio-Science / AI Dialogue Sample")
    print("==========================================================")
    
    combined_samples = []
    sample_rate = 24000
    pause_samples = int(sample_rate * 0.35)

    for idx, turn in enumerate(DIALOGUE):
        speaker = turn["speaker"]
        voice = turn["voice"]
        text = turn["text"]
        
        raw_pcm = synthesize_turn(voice, text)
        if not raw_pcm:
            print(f"Failed turn {idx+1}")
            continue

        samples = np.frombuffer(raw_pcm, dtype=np.int16).astype(np.float32) / 32768.0

        # DC offset
        samples -= np.mean(samples)

        # 20ms Cosine Fade
        fade_len = int(sample_rate * 0.02)
        if len(samples) > 2 * fade_len:
            fade_in = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            fade_out = 0.5 * (1 + np.cos(np.pi * np.arange(fade_len) / fade_len))
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

        combined_samples.append(samples)
        combined_samples.append(np.zeros(pause_samples, dtype=np.float32))
        time.sleep(2)

    full_audio = np.concatenate(combined_samples)
    
    # Peak normalize
    max_peak = np.max(np.abs(full_audio))
    if max_peak > 0:
        full_audio = full_audio * (0.891 / max_peak)

    out_file = AUDIO_DIR / "sample_09_veda_rami_bioscience_ai.mp3"
    sf.write(str(out_file), full_audio, sample_rate)
    
    duration = len(full_audio) / sample_rate
    print("==========================================================")
    print(f"[COMPLETE] Bio-Science AI Sample Saved: {out_file}")
    print(f"Duration: {duration:.2f}s")
    print("==========================================================")

if __name__ == "__main__":
    build_bioscience_sample()
