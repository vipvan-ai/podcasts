import asyncio
import edge_tts
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Clean, beautifully punctuated script formatted for natural human vocal cadence
CLEAN_SCRIPT = """
Imagine sitting across from someone you love. ... No words are spoken. ... No fingers tap on a screen. 

Yet, in a fraction of a second, an entire concept—a vivid memory, a precise emotional state, or a complex technical blueprint—is transmitted directly from your mind into theirs!

This isn't science fiction! It is the emerging science of Synthetic Telepathy, enabled by high-bandwidth Brain-Computer Interfaces.

Welcome to Future Human Daily! I'm your host, and today, we are exploring what happens when human thought escapes the boundaries of language.

For all of human history, communication has suffered from a fundamental bottleneck: bandwidth. ... 

Your brain processes thoughts at lightning speed—millions of neurons firing in high-dimensional complexity! But to share a thought, you must squeeze it down through your vocal cords or fingertips, at a painfully slow rate of roughly 40 to 60 words per minute.

Enter modern BCIs! Companies like Neuralink, Synchron, and Paradromics are developing ultra-thin neural threads capable of reading thousands of individual action potentials directly from the language cortex.

When neural implants can both read AND write signals to the cortex with sub-millisecond precision, we unlock direct brain-to-brain synthesis. 

Imagine empathy without translation: sharing the exact feeling of an emotion rather than trying to describe it in words. ... Or collaborative genius: where engineers, surgeons, and artists merge mental workspaces in real time!

Language was just our first operating system. ... The next OS will be direct neural resonance.

Thank you for joining today's journey into tomorrow on Future Human Daily. What thought would you share if words didn't exist? Connect with us, subscribe on Spotify or Apple Podcasts, and until tomorrow—stay curious about the future!
"""

async def generate_clean_audio():
    mp3_file = AUDIO_DIR / "ep-001.mp3"
    print("[Clean Audio Engine] Generating clean natural voice narration (en-US-AndrewNeural)...")
    
    for attempt in range(5):
        try:
            communicate = edge_tts.Communicate(CLEAN_SCRIPT.strip(), "en-US-AndrewNeural", rate="+4%", pitch="+2Hz")
            await communicate.save(str(mp3_file))
            if mp3_file.exists() and mp3_file.stat().st_size > 1000:
                print(f"[Success] Clean ep-001.mp3 generated successfully! ({mp3_file.stat().st_size / 1024:.1f} KB)")
                break
        except Exception as e:
            print(f"[Notice] Attempt {attempt + 1} connection retry ({e})...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(generate_clean_audio())
