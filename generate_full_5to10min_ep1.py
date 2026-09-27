import os
import base64
import struct
from pathlib import Path
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")
AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Full 7-8 Minute Dual-Host Script for Episode 001 featuring Alex Mercer & Dr. Elena Vance
FULL_EP001_5TO10MIN_SCRIPT = """
[Segment 1: Cold Open & The Hook]
[Host: Alex - Puck] [excitedly] Imagine sitting across from someone you love. ... [pause] No words are spoken. No fingers tap on a touchscreen. Yet, in a fraction of a second, an entire concept—a vivid childhood memory, a precise emotional state, or a complex architectural blueprint—is transmitted directly from your mind into theirs.

[Host: Elena - Kore] [sighs] [thoughtfully] It sounds like pure science fiction, Alex. But what we're talking about today isn't fantasy. It's the emerging reality of Synthetic Telepathy, driven by high-bandwidth Brain-Computer Interfaces.

[Host: Alex - Puck] [cheerful] Welcome to Future Human Daily! I'm your host, Alex Mercer, here with Dr. Elena Vance. Today, we're exploring what happens to human civilization when thought escapes the physical boundaries of spoken language.

[Segment 2: The Bandwidth Bottleneck]
[Host: Elena - Kore] [serious] To understand why this shift is so huge, Alex, we have to talk about human evolution's biggest bottleneck: language bandwidth. 

[Host: Alex - Puck] [thoughtfully] Right. Your brain processes thoughts at lightning speed, with billions of neurons firing in high-dimensional complexity every second. But how do we share those thoughts?

[Host: Elena - Kore] [chuckles] We squeeze them down through our vocal cords or our fingertips at a painfully slow speed—roughly 40 to 60 words per minute! It's like trying to download a 4K movie through a 1990s dial-up modem!

[Host: Alex - Puck] [laughs] Exactly! And every time you try to turn a complex feeling into words, half of the fidelity gets lost in translation. The receiver then has to unpack those words and reconstruct the idea in their own brain.

[Segment 3: Current BCI Milestones]
[Host: Elena - Kore] [excitedly] Enter modern Brain-Computer Interfaces! Over the past two years, companies like Neuralink, Synchron, and Paradromics have made incredible leaps. We're moving away from rigid external scalp sensors to ultra-thin neural threads inserted directly into the motor and language cortex.

[Host: Alex - Puck] [thoughtfully] And initial clinical trials focused on medical restoration—allowing paralysis patients to control digital cursors or type text with thought alone. But the technology reached a major turning point recently, didn't it?

[Host: Elena - Kore] [cheerful] Absolutely! Researchers have successfully decoded sub-vocal neural intent into instant data packets. That means the brain doesn't even need to move your mouth or hands; the neural firing pattern IS the signal.

[Segment 4: Brain-to-Brain Resonance & Empathy Without Translation]
[Host: Alex - Puck] [excitedly] But Elena, the true horizon here isn't just typing without hands. It's two-way neural loop communication—reading AND writing signals to the brain simultaneously!

[Host: Elena - Kore] [sighs] [thoughtfully] When you can write digital intent back into the cortex, you unlock direct brain-to-brain synthesis. Think about what that means for human empathy.

[Host: Alex - Puck] [thoughtfully] Empathy without translation! Instead of trying to explain grief, awe, or love through clumsy adjectives, you could allow another person to experience the exact resonance of your emotional state for a split second.

[Host: Elena - Kore] [excitedly] Or think about collaborative genius! Surgeons, aerospace engineers, and digital artists could merge their mental workspaces in real time. Three experts thinking together as a single super-mind!

[Segment 5: Neural Security, Ethics & Outro]
[Host: Alex - Puck] [serious] Of course, a breakthrough this powerful comes with profound ethical challenges. If a computer link can read your thoughts before you even speak them out loud, where does your private self end and the public network begin?

[Host: Elena - Kore] [thoughtfully] Exactly. Who owns your neural logs? Can your private thoughts be subpoenaed or targeted by cognitive advertising? Cognitive liberty will become the most important civil rights battle of the 21st century.

[Host: Alex - Puck] [cheerful] Language was just humanity's first operating system. The next OS will be direct neural resonance. 

[Host: Elena - Kore] [warmly] Thank you for joining us on today's journey into tomorrow on Future Human Daily! What thought would you share if words didn't exist?

[Host: Alex - Puck] [cheerful] Connect with us on social media, subscribe on Spotify or Apple Podcasts, and leave a review. Until tomorrow—stay curious about the future!
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
    print(f"[Success] Generated full 5-10 minute Dual Host audio: {output_path} ({len(header + pcm_data) / 1024:.1f} KB)")
    return output_path

def generate_full_5to10min_episode1():
    print("[Gemini 3.8 Full Episode Engine] Generating full 5-10 minute dual-host episode 001...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    response = client.models.generate_content(
        model='gemini-3.8-flash-tts',
        contents=FULL_EP001_5TO10MIN_SCRIPT.strip(),
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
            
        full_wav = str(AUDIO_DIR / "ep-001-full-5to10min.wav")
        save_pcm_to_wav(data, full_wav)
        
        # Copy to main ep-001.mp3 so web player plays the full masterclass episode
        main_mp3 = AUDIO_DIR / "ep-001.mp3"
        main_mp3.write_bytes(Path(full_wav).read_bytes())
        print("[Player Sync] Full 5-10 minute episode audio updated on player web app!")

if __name__ == "__main__":
    generate_full_5to10min_episode1()
