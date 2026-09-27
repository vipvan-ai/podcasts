import os
import re
import base64
import struct
from pathlib import Path
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")
AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT_TEXT = """
Welcome to Future Human Daily on Gemini 3.8 Flash TTS! Today we are testing high-bandwidth neural narration for long-form podcasts. 
With Gemini 3.8 Flash TTS, we can create extended length audio episodes with natural emotional pacing, dynamic breathing, and significantly higher free tier API limits.
"""

def save_pcm_to_wav(pcm_data: bytes, output_path: str, sample_rate: int = 24000) -> str:
    num_channels = 1
    bytes_per_sample = 2
    byte_rate = sample_rate * num_channels * bytes_per_sample
    block_align = num_channels * bytes_per_sample
    data_len = len(pcm_data)
    file_len = 36 + data_len
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', file_len, b'WAVE', b'fmt ', 16, 
        1, num_channels, sample_rate, byte_rate, 
        block_align, bytes_per_sample * 8, b'data', data_len
    )
    
    with open(output_path, "wb") as f:
        f.write(header + pcm_data)
    print(f"[Success] Audio saved to {output_path} ({len(header + pcm_data) / 1024:.1f} KB)")
    return output_path

def test_gemini_38(model_name="gemini-3.8-flash-tts", voice_name="Puck"):
    print(f"Testing Model: {model_name} with Voice: {voice_name}...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=SCRIPT_TEXT.strip(),
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )
        )
        
        part = response.candidates[0].content.parts[0]
        if part.inline_data:
            data = part.inline_data.data
            if isinstance(data, str):
                data = base64.b64decode(data)
            out_wav = str(AUDIO_DIR / f"test-{model_name.replace('/', '_')}-{voice_name.lower()}.wav")
            save_pcm_to_wav(data, out_wav)
            return True
        else:
            print("No inline audio data returned.")
            return False
    except Exception as e:
        print(f"Error testing {model_name}: {e}")
        return False

if __name__ == "__main__":
    print("--- Testing Gemini 3.8 Flash TTS ---")
    test_gemini_38("gemini-3.8-flash-tts", "Puck")
    print("\n--- Testing Gemini 3.8 Flash Lite TTS ---")
    test_gemini_38("gemini-3.8-flash-lite-tts", "Puck")
