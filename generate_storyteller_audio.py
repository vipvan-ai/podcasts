import asyncio
import edge_tts
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT_TEXT = """
Imagine sitting across from someone you love. ... No words are spoken. ... No fingers tap on a screen. 

Yet, in a fraction of a second, an entire concept—a vivid memory, a precise emotional state, or a complex technical blueprint—is transmitted directly from your mind into theirs!

This isn't science fiction. It is the emerging science of Synthetic Telepathy, enabled by high-bandwidth Brain-Computer Interfaces.

Welcome to Future Human Daily. I'm your host, and today, we are exploring what happens when human thought escapes the boundaries of language.

For all of human history, communication has suffered from a fundamental bottleneck: bandwidth. ... 

Your brain processes thoughts at lightning speed—millions of neurons firing in high-dimensional complexity! But to share a thought, you must squeeze it down through your vocal cords or fingertips, at a painfully slow rate of roughly 40 to 60 words per minute.

Enter modern BCIs. Companies like Neuralink, Synchron, and Paradromics are developing ultra-thin neural threads capable of reading thousands of individual action potentials directly from the language cortex.

When neural implants can both read AND write signals to the cortex with sub-millisecond precision, we unlock direct brain-to-brain synthesis. 

Imagine empathy without translation: sharing the exact feeling of an emotion rather than trying to describe it in words. ... Or collaborative genius: where engineers, surgeons, and artists merge mental workspaces in real time!

Language was just our first operating system. ... The next OS will be direct neural resonance.

Thank you for joining today's journey into tomorrow on Future Human Daily. What thought would you share if words didn't exist? Connect with us, subscribe on Spotify or Apple Podcasts, and until tomorrow—stay curious about the future.
"""

async def generate_storyteller_voice(voice="en-US-ChristopherNeural", filename="ep-001-christopher.mp3"):
    output_path = AUDIO_DIR / filename
    print(f"[Storyteller Audio Engine] Generating narration with {voice}...")
    
    for attempt in range(5):
        try:
            communicate = edge_tts.Communicate(SCRIPT_TEXT.strip(), voice, rate="+2%", pitch="+1Hz")
            await communicate.save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"[Success] Saved storyteller voice ({voice}) to {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")
                
                # Copy as main ep-001.mp3
                main_mp3 = AUDIO_DIR / "ep-001.mp3"
                main_mp3.write_bytes(output_path.read_bytes())
                break
        except Exception as e:
            print(f"[Retry {attempt+1}] {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    # en-US-ChristopherNeural is the premier storytelling / documentary voice used in short_stories
    asyncio.run(generate_storyteller_voice("en-US-ChristopherNeural", "ep-001.mp3"))
