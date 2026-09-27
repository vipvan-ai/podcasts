import os
import base64
import struct
from pathlib import Path
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")
AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Dual-Host Script for Gemini 3.8 Flash TTS featuring emotional cues ([laughs], [sighs], [chuckles], [pause])
DUAL_HOST_SCRIPT = """
[Host: Alex - Puck] [excitedly] Welcome back to Future Human Daily! I'm Alex Mercer, here with my co-host, Elena Vance. 

[Host: Elena - Kore] [cheerful] Hey everyone! Today we're diving into something that sounds straight out of sci-fi: Synthetic Telepathy.

[Host: Alex - Puck] [chuckles] Right! Imagine sitting across from someone, and without saying a single word... [pause] you transmit a vivid memory or a complex thought straight into their mind!

[Host: Elena - Kore] [sighs] [thoughtfully] It's mind-bending to think about. I mean... language has been our main communication tool for thousands of years, but it's so slow! 40 words a minute? That's a huge bottleneck!

[Host: Alex - Puck] [excitedly] Exactly! Modern Brain-Computer Interfaces like Neuralink and Synchron are breaking that bottleneck. They're reading action potentials directly from the cortex.

[Host: Elena - Kore] [laughs] So no more miscommunications or typing typos? Sign me up! 

[Host: Alex - Puck] [thoughtfully] Well, it raises huge privacy questions too. Who owns your neural logs if a computer can read your thoughts before you even speak?

[Host: Elena - Kore] [warmly] That is the million-dollar question. Until tomorrow, stay curious about the future!
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
    print(f"[Success] Dual Host Audio generated: {output_path} ({len(header + pcm_data) / 1024:.1f} KB)")
    return output_path

def generate_dual_host_demo():
    print("[Gemini 3.8 Dual-Host Engine] Generating dialogue narration with Alex & Elena...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # We can pass multi-speaker dialogue config or formatted prompt to Gemini 3.8
    response = client.models.generate_content(
        model='gemini-3.8-flash-tts',
        contents=DUAL_HOST_SCRIPT.strip(),
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"
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
            
        wav_path = str(AUDIO_DIR / "ep-001-dual-host.wav")
        save_pcm_to_wav(data, wav_path)
        
        # Copy to main ep-001.mp3
        main_mp3 = AUDIO_DIR / "ep-001.mp3"
        main_mp3.write_bytes(Path(wav_path).read_bytes())
        print("[Player Sync] Dual Host audio synchronized to player!")

if __name__ == "__main__":
    generate_dual_host_demo()
