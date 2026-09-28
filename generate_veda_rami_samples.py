import os
import time
import base64
import numpy as np
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
    'gemini-3.1-flash-tts-preview',
    'gemini-2.5-flash-preview-tts'
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
                print(f" -> Successfully synthesized {voice_name} via {model_name}")
                return data
        except Exception as e:
            print(f" -> Model {model_name} error/rate-limit for {voice_name}: {e}. Retrying next...")
            time.sleep(2)
    return None

def generate_veda_and_rami_samples():
    print("==========================================================")
    print("Generating Veda & Rami Voice Samples")
    print("==========================================================")

    # 1. Veda Solo
    veda_text = "[cheerful] Hello! I am Dr. Elena Vance, testing the Veda voice profile. Today we are exploring the frontiers of biotechnology and artificial intelligence."
    raw_veda = synthesize_turn("Veda", veda_text)
    if raw_veda:
        samples_veda = np.frombuffer(raw_veda, dtype=np.int16).astype(np.float32) / 32768.0
        samples_veda /= (np.max(np.abs(samples_veda)) + 1e-6)
        samples_veda *= 0.89
        sf.write(str(AUDIO_DIR / "sample_06_veda_female.mp3"), samples_veda, 24000)

    time.sleep(3)

    # 2. Rami Solo
    rami_text = "[warmly] Hey everyone! I am Alex Mercer, testing the Rami voice profile. Welcome to Future Human Daily."
    raw_rami = synthesize_turn("Rami", rami_text)
    if raw_rami:
        samples_rami = np.frombuffer(raw_rami, dtype=np.int16).astype(np.float32) / 32768.0
        samples_rami /= (np.max(np.abs(samples_rami)) + 1e-6)
        samples_rami *= 0.89
        sf.write(str(AUDIO_DIR / "sample_07_rami_male.mp3"), samples_rami, 24000)

    time.sleep(3)

    # 3. Rami & Veda Dialogue Sample
    if raw_rami and raw_veda:
        rami_turn2 = synthesize_turn("Rami", "[excitedly] Veda's voice sounds super smooth, Elena! What do you think about testing this out for Future Human Daily?")
        time.sleep(2)
        veda_turn2 = synthesize_turn("Veda", "[chuckles] Well, Alex, I must admit, it has a very natural and pleasant cadence for our daily discussions.")
        
        dialogue_chunks = []
        if raw_rami:
            s_rami = np.frombuffer(raw_rami, dtype=np.int16).astype(np.float32) / 32768.0
            dialogue_chunks.append(s_rami)
            dialogue_chunks.append(np.zeros(int(24000 * 0.35), dtype=np.float32))
        if raw_veda:
            s_veda = np.frombuffer(raw_veda, dtype=np.int16).astype(np.float32) / 32768.0
            dialogue_chunks.append(s_veda)
            dialogue_chunks.append(np.zeros(int(24000 * 0.35), dtype=np.float32))
        if rami_turn2:
            s_r2 = np.frombuffer(rami_turn2, dtype=np.int16).astype(np.float32) / 32768.0
            dialogue_chunks.append(s_r2)
            dialogue_chunks.append(np.zeros(int(24000 * 0.35), dtype=np.float32))
        if veda_turn2:
            s_v2 = np.frombuffer(veda_turn2, dtype=np.int16).astype(np.float32) / 32768.0
            dialogue_chunks.append(s_v2)

        full_dialogue = np.concatenate(dialogue_chunks)
        full_dialogue /= (np.max(np.abs(full_dialogue)) + 1e-6)
        full_dialogue *= 0.89
        sf.write(str(AUDIO_DIR / "sample_08_rami_veda_duo.mp3"), full_dialogue, 24000)

    print("\n[COMPLETE] Veda and Rami samples saved to audio/voice_samples/")

if __name__ == "__main__":
    generate_veda_and_rami_samples()
