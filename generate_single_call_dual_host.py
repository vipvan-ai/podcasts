import os
import time
import base64
import struct
from pathlib import Path
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAqMBniCg-vSQPxvTeYibsvIzGmAxewPuc")
AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Full Conversational Script in 1 single prompt to stay within 1 request per minute
SINGLE_CALL_DUAL_HOST_SCRIPT = """
[Host Alex: Warm, charismatic, curious, relaxed pace]
[warmly] Have you ever tried explaining a vivid dream to your partner over morning coffee? [chuckles] You're standing there in your kitchen, hands waving around... trying to describe this incredible, cinematic world in your head... and all that comes out of your mouth is, "Well, there was a dog, and... I think it was blue?"

[Host Elena: Intimate, smooth, charming, clever, relaxed pace]
[soft giggle] Oh, absolutely! [sighs] Or that feeling when a song is completely stuck in your head, and you try humming it to your friend, and they just look at you like you've lost your mind! [giggles]

[Host Alex]
[laughs] Exactly! That frustration right there... that is the fundamental flaw of human language. We have billions of hyper-complex thoughts firing in our brains every single second... but to share them with someone we care about, we have to squeeze them through a tiny straw. Spoken words.

[Host Elena]
[thoughtfully] We squeeze all that rich human emotion down to roughly 40 words a minute. [sighs] It's almost tragic, isn't it? Half of what we actually feel gets lost in translation between the heart and the lips.

[Host Alex]
[whispers] But what if you didn't have to translate it at all? [pause] What if you could just... share the raw feeling?

[Host Elena]
[warmly] [softly] Welcome to Future Human Daily. I'm Dr. Elena Vance, here with Alex Mercer. Today, we're taking a slow, intimate look at Synthetic Telepathy—and how direct neural connections might change human intimacy forever.

[Host Alex]
[cheerful] Think about your phone right now, Elena. We send text messages with typos, misread tone in emails, and get into silly arguments over a misplaced emoji! [chuckles]

[Host Elena]
[laughs] Don't get me started on auto-correct! [chuckles] But seriously, Alex... current human technology is so clumsy. We stare at glowing glass rectangles all day, tapping our thumbs like cavemen with tiny stones.

[Host Alex]
[thoughtfully] Modern Brain-Computer Interfaces like Neuralink, Synchron, and Paradromics are changing that game. They're using microscopic neural threads in the cortex to read action potentials directly.

[Host Elena]
[intimately] But the real magic isn't just typing without your hands, Alex. The true magic is two-way neural resonance. [pause] Imagine sitting on the couch next to someone you love... no words, no screens. You don't just tell them you love them... you let them feel the exact warmth of your heart in real time.

[Host Alex]
[sighs] [warmly] Wow. Empathy without translation. Imagine how many relationship misunderstandings that could solve!

[Host Elena]
[playfully] [giggles] Well, unless you're secretly thinking about pizza while they're pouring their heart out! [laughs]

[Host Alex]
[laughs] Okay, valid point! Which brings us to the serious side... privacy. If someone can read your neural patterns, where does your private inner sanctuary end?

[Host Elena]
[thoughtfully] We will need neural firewalls. The same way you lock your phone today, you'll need cognitive security for your mind tomorrow.

[Host Alex]
[warmly] Language was just humanity's first operating system. The next OS will be direct heart-to-heart resonance.

[Host Elena]
[intimately] Thank you for relaxing with us today on Future Human Daily. What thought would you share if words didn't exist?

[Host Alex]
[cheerful] Subscribe on Spotify or Apple Podcasts, leave us a review, and until tomorrow... stay curious about the future.
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
    print(f"[Success] Audio saved: {output_path} ({len(header + pcm_data) / 1024:.1f} KB)")
    return output_path

def generate_single_call_audio():
    print("[Single-Call Engine] Generating dual-host audio in 1 request...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash-tts',
                contents=SINGLE_CALL_DUAL_HOST_SCRIPT.strip(),
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
                    
                out_file = str(AUDIO_DIR / "ep-001-audited-master.wav")
                save_pcm_to_wav(data, out_file)
                
                # Copy to main ep-001.mp3
                main_mp3 = AUDIO_DIR / "ep-001.mp3"
                main_mp3.write_bytes(Path(out_file).read_bytes())
                print("[Player Sync] Master audited dual-host audio updated for web player!")
                break
        except Exception as e:
            print(f"[Notice] Cooldown attempt {attempt+1}: {e}")
            print("Waiting 15 seconds for API quota window...")
            time.sleep(15)

if __name__ == "__main__":
    generate_single_call_audio()
