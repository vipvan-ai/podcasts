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
    'gemini-3.1-flash-tts-preview',
    'gemini-2.5-flash-preview-tts',
    'gemini-2.5-pro-preview-tts',
    'gemini-3.8-flash-tts'
]

TEST_TEXT = "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today on Future Human Daily we are diving deep into cellular reprogramming and biological age clocks."

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
                print(f" -> Successfully synthesized with {voice_name} via {model_name}")
                return data
        except Exception as e:
            print(f" -> Model {model_name} rate limit / error for {voice_name}: {e}. Retrying next...")
            time.sleep(2)
    return None

def apply_studio_warmth_eq(audio_samples, sample_rate=24000):
    # Apply Broadcast Studio Proximity EQ (Low-shelf boost + 140Hz warm peak)
    # 1. Low shelf boost around 120Hz (+3.5 dB)
    # 2. Subtle high-cut above 7500Hz to remove digital sibilance harshness
    b_highcut, a_highcut = signal.butter(2, 7500 / (sample_rate / 2), btype='low')
    audio_samples = signal.filtfilt(b_highcut, a_highcut, audio_samples)

    # Low peak warm boost at 150Hz
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

    warm_samples = signal.filtfilt(b, a, audio_samples)
    return warm_samples

def generate_all_samples():
    print("==========================================================")
    print("Generating Alex Mercer Voice Comparison Samples")
    print("==========================================================")

    # 1. Puck (Current Raw)
    raw_puck = synthesize_turn("Puck", TEST_TEXT)
    if raw_puck:
        samples_puck = np.frombuffer(raw_puck, dtype=np.int16).astype(np.float32) / 32768.0
        # normalize
        samples_puck /= (np.max(np.abs(samples_puck)) + 1e-6)
        samples_puck *= 0.89
        sf.write(str(AUDIO_DIR / "sample_01_puck_current.mp3"), samples_puck, 24000)
        
        # 2. Puck (Enhanced Warmth EQ)
        puck_warm = apply_studio_warmth_eq(samples_puck)
        puck_warm /= (np.max(np.abs(puck_warm)) + 1e-6)
        puck_warm *= 0.89
        sf.write(str(AUDIO_DIR / "sample_02_puck_studio_warmth.mp3"), puck_warm, 24000)

    time.sleep(3)

    # 3. Fenrir (Deep Baritone)
    raw_fenrir = synthesize_turn("Fenrir", TEST_TEXT)
    if raw_fenrir:
        samples_fenrir = np.frombuffer(raw_fenrir, dtype=np.int16).astype(np.float32) / 32768.0
        samples_fenrir /= (np.max(np.abs(samples_fenrir)) + 1e-6)
        samples_fenrir *= 0.89
        sf.write(str(AUDIO_DIR / "sample_03_fenrir_deep_baritone.mp3"), samples_fenrir, 24000)

    time.sleep(3)

    # 4. Orus (Smooth Broadcast)
    raw_orus = synthesize_turn("Orus", TEST_TEXT)
    if raw_orus:
        samples_orus = np.frombuffer(raw_orus, dtype=np.int16).astype(np.float32) / 32768.0
        samples_orus /= (np.max(np.abs(samples_orus)) + 1e-6)
        samples_orus *= 0.89
        sf.write(str(AUDIO_DIR / "sample_04_orus_smooth_broadcast.mp3"), samples_orus, 24000)

    time.sleep(3)

    # 5. Zephyr (Balanced Male)
    raw_zephyr = synthesize_turn("Zephyr", TEST_TEXT)
    if raw_zephyr:
        samples_zephyr = np.frombuffer(raw_zephyr, dtype=np.int16).astype(np.float32) / 32768.0
        samples_zephyr /= (np.max(np.abs(samples_zephyr)) + 1e-6)
        samples_zephyr *= 0.89
        sf.write(str(AUDIO_DIR / "sample_05_zephyr_balanced.mp3"), samples_zephyr, 24000)

    print("\n[COMPLETE] All voice comparison samples written to audio/voice_samples/")

if __name__ == "__main__":
    generate_all_samples()
