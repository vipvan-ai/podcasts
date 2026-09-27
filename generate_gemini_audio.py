import os
import re
import base64
import struct
from pathlib import Path
from google import genai
from google.genai import types

# Load API key from env or short_stories .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Episode 001 Narration Script for Google Gemini TTS
SCRIPT_TEXT = """
Imagine sitting across from someone you love. No words are spoken. No fingers tap on a screen. Yet in a fraction of a second, an entire concept—a vivid memory, a precise emotional state, or a complex technical blueprint—is transmitted directly from your mind into theirs.

This isn't science fiction. It is the emerging science of Synthetic Telepathy, enabled by high-bandwidth Brain-Computer Interfaces.

Welcome to Future Human Daily. I'm your host, and today, we're exploring what happens when human thought escapes the boundaries of language.

For all of human history, communication has suffered from a fundamental bottleneck: bandwidth. Your brain processes thoughts at lightning speed, with millions of neurons firing in high-dimensional complexity. But to share a thought, you must squeeze it down through vocal cords or fingertips at a painfully slow rate of roughly 40 to 60 words per minute.

Enter modern BCIs. Companies like Neuralink, Synchron, and Paradromics are developing ultra-thin neural threads capable of reading thousands of individual action potentials directly from the language cortex.

When neural implants can both read and write signals to the cortex with sub-millisecond precision, we unlock direct brain-to-brain synthesis. Imagine empathy without translation: sharing the exact feeling of an emotion rather than trying to describe it in words. Or collaborative genius: where engineers, surgeons, and artists merge mental workspaces in real time.

Language was just our first operating system. The next OS will be direct neural resonance.

Thank you for joining today's journey into tomorrow on Future Human Daily. What thought would you share if words didn't exist? Connect with us, subscribe on Spotify or Apple Podcasts, and until tomorrow—stay curious about the future.
"""

def save_pcm_to_wav(pcm_data: bytes, output_path: str, sample_rate: int = 24000) -> str:
    """Wraps raw PCM bytes in a WAV container header so it plays in all browsers."""
    num_channels = 1
    bytes_per_sample = 2  # 16-bit
    
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
    print(f"[Success] Gemini TTS audio saved to {output_path} ({len(header + pcm_data) / 1024:.1f} KB)")
    return output_path

def generate_gemini_audio(voice_name="Puck"):
    print(f"[Google Voice Engine] Generating narration with Gemini 3.1 Flash TTS (Voice: {voice_name})...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    response = client.models.generate_content(
        model='gemini-3.1-flash-tts-preview',
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
        mime_type = part.inline_data.mime_type
        data = part.inline_data.data
        if isinstance(data, str):
            data = base64.b64decode(data)
            
        wav_path = str(AUDIO_DIR / f"ep-001-gemini-{voice_name.lower()}.wav")
        if "pcm" in mime_type.lower() or "l16" in mime_type.lower():
            rate = 24000
            rate_match = re.search(r'rate=(\d+)', mime_type)
            if rate_match:
                rate = int(rate_match.group(1))
            save_pcm_to_wav(data, wav_path, rate)
        else:
            with open(wav_path, "wb") as f:
                f.write(data)
            print(f"[Success] Saved audio to {wav_path}")
            
        # Also copy as main ep-001.wav/mp3
        main_path = str(AUDIO_DIR / "ep-001.wav")
        with open(main_path, "wb") as f:
            f.write(open(wav_path, "rb").read())
        return wav_path

if __name__ == "__main__":
    # Test generating with Puck or Fenrir voice
    generate_gemini_audio("Puck")
