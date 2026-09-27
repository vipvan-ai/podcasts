import os
import re
import time
import base64
import struct
from pathlib import Path
from google import genai
from google.genai import types

# API Key from short_stories .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")
AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Emotionally annotated narrative script (Gemini 3.1 TTS parses bracket tags like [excitedly], [pause], [thoughtfully], [whispers])
EMOTIONAL_NARRATION_SCRIPT = """
[peacefully] Imagine sitting across from someone you love. [pause] No words are spoken. [pause] No fingers tap on a screen. 

[excitedly] Yet in a fraction of a second, an entire concept—a vivid memory, a precise emotional state, or a complex technical blueprint—is transmitted directly from your mind into theirs!

[thoughtfully] This isn't science fiction. It is the emerging science of Synthetic Telepathy, enabled by high-bandwidth Brain-Computer Interfaces.

[cheerfully] Welcome to Future Human Daily! I'm your host, and today, we are exploring what happens when human thought escapes the boundaries of language.

[serious] For all of human history, communication has suffered from a fundamental bottleneck: bandwidth. 

Your brain processes thoughts at lightning speed—millions of neurons firing in high-dimensional complexity! But to share a thought, you must squeeze it down through your vocal cords or fingertips, at a painfully slow rate of roughly 40 to 60 words per minute.

[excitedly] Enter modern BCIs! Companies like Neuralink, Synchron, and Paradromics are developing ultra-thin neural threads capable of reading thousands of individual action potentials directly from the language cortex.

[thoughtfully] When neural implants can both read AND write signals to the cortex with sub-millisecond precision, we unlock direct brain-to-brain synthesis. 

[empathetic] Imagine empathy without translation: sharing the exact feeling of an emotion rather than trying to describe it in words. [pause] Or collaborative genius: where engineers, surgeons, and artists merge mental workspaces in real time!

[peacefully] Language was just our first operating system. [pause] The next OS will be direct neural resonance.

[warmly] Thank you for joining today's journey into tomorrow on Future Human Daily. What thought would you share if words didn't exist? Subscribe on Spotify or Apple Podcasts, and until tomorrow—stay curious about the future.
"""

def save_pcm_to_wav(pcm_data: bytes, output_path: str, sample_rate: int = 24000) -> str:
    """Wraps raw PCM bytes in a WAV container header."""
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
    print(f"[Success] Saved Google Gemini TTS audio to {output_path} ({len(header + pcm_data) / 1024:.1f} KB)")
    return output_path

def generate_gemini_speech(voice_name="Puck"):
    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"[Google Gemini TTS] Generating story narration with voice: {voice_name}...")
    
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-tts-preview',
                contents=EMOTIONAL_NARRATION_SCRIPT.strip(),
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
                
                output_wav = str(AUDIO_DIR / f"ep-001-gemini-{voice_name.lower()}.wav")
                save_pcm_to_wav(data, output_wav)
                
                # Copy as main ep-001.mp3/wav
                main_mp3 = AUDIO_DIR / "ep-001.mp3"
                with open(main_mp3, "wb") as f:
                    f.write(open(output_wav, "rb").read())
                return output_wav
        except Exception as e:
            print(f"[Attempt {attempt + 1}] Gemini API rate limit or error: {e}")
            time.sleep(15)

if __name__ == "__main__":
    generate_gemini_speech("Puck")
