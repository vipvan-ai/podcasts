import os
import sys

# -----------------------------------------------------------------------------
# WEEKDAY PODCAST CONFIGURATION & PROMPT BLUEPRINT
# Minimum Word Count: 2,300 - 2,700 words (24-28 alternating turns)
# Target Duration: 5:30 - 7:30 minutes
# Mandatory Rule: Accessible Everyman Hook with Relatable Everyday Analogies
# -----------------------------------------------------------------------------

WEEKDAY_SCRIPT_GUIDELINES = """
You are writing a script for "Future Human Daily", a 5 to 7 minute weekday science & tech podcast hosted by Alex Mercer & Dr. Elena Vance.

TARGET AUDIENCE:
General audience / everyday listeners. Do NOT assume the listener is science-savvy! 

MANDATORY SCRIPT STRUCTURE (2,300+ WORDS, 24-28 TURNS):

ACT 1: THE EVERYDAY HUMAN HOOK & SIMPLE ANALOGY (600 - 700 words / Turns 1-7)
- Turn 1 MUST use opening formula: "I am your host Alex Mercer with Dr. Elena Vance, and today is [Date], and you're listening to Future Human Daily. Today we are talking about [Topic]..."
- Connect the topic immediately to an everyday human situation (making coffee, stuck in traffic, typing on a phone, feeling tired, listening to a song).
- Dr. Elena Vance explains the core concept using a simple, intuitive metaphor (like comparing optical channels to water pipes, or quantum sensors to noise-canceling headphones).
- Alex Mercer asks the exact question the non-technical listener is thinking: "Wait, explain that in plain English—how does that affect my morning?"

ACT 2: THE SCIENCE & ENGINEERING REALITY CHECK (900 - 1,000 words / Turns 8-18)
- Elena breaks down how the tech actually works, but keeps the metaphors active.
- Alex raises practical questions, skepticisms, and real-world engineering hurdles.
- Playful back-and-forth banter: Alex and Elena playfully challenge each other's assumptions.

ACT 3: THE HUMAN IMPACT & FUTURE LANDSCAPE (700 - 800 words / Turns 19-26)
- How this technology changes daily human life, medicine, work, or privacy over the next 5-10 years.
- Closing handoff reminding listeners to subscribe and stay curious.
"""

def verify_script_word_count(script_turns):
    total_words = sum(len(turn["text"].split()) for turn in script_turns)
    num_turns = len(script_turns)
    est_duration_mins = total_words / 310.0 # ~310 words per minute for unhurried audio
    
    print("==========================================================", flush=True)
    print(f"WEEKDAY SCRIPT VERIFICATION AUDIT", flush=True)
    print("==========================================================", flush=True)
    print(f"Total Turns: {num_turns}", flush=True)
    print(f"Total Words: {total_words} words", flush=True)
    print(f"Estimated Audio Duration: {est_duration_mins:.2f} minutes ({int(est_duration_mins)}m {int((est_duration_mins%1)*60)}s)", flush=True)
    
    if total_words < 2200:
        print(f"[WARNING] Word count ({total_words}) is below 2,200 words! Expand script turns to hit 5:30+ minutes.", flush=True)
        return False
    else:
        print(f"[SUCCESS] Script meets 2,200+ word requirement for 5:30+ minutes duration!", flush=True)
        return True

if __name__ == "__main__":
    print(WEEKDAY_SCRIPT_GUIDELINES)
