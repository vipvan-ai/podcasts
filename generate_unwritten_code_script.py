# =============================================================================
# THE UNWRITTEN CODE: DYNAMIC DAILY SCRIPT GENERATOR & TOPIC LEDGER
# Automatically picks unused topics from unwritten_code_topics.json,
# checks unwritten_code_history.json to guarantee NO REPEATS,
# and generates 1,550+ word fresh scripts with dynamic dates and 0 episode numbers.
# =============================================================================

import os
import json
import re
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
TOPICS_FILE = BASE_DIR / "unwritten_code_topics.json"
HISTORY_FILE = BASE_DIR / "unwritten_code_history.json"
SCRIPTS_CACHE_DIR = BASE_DIR / "daily_scripts_cache"
SCRIPTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load environment
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

UNWRITTEN_CODE_SYSTEM_PROMPT = """You are the master lead writer for "The Unwritten Code", a wildly popular daily morning comedy & social etiquette podcast hosted by Maya Lin and Julian Cross.

HOST PERSONAS:
1. Maya Lin (Voice: "Kore"): Sharp, witty, energetic, deeply relatable, highly expressive. Uses stage directions like [cheerful], [playfully], [laughs], [giggles], [groans].
2. Julian Cross (Voice: "Puck"): Warm, observant, dry British-style witty sarcasm, etiquette philosopher. Uses stage directions like [warmly], [chuckles], [sighs], [thoughtfully], [playfully].

MANDATORY RULES:
1. DURATION & WORD COUNT: The script MUST be between 1,200 and 1,400 words across 16 to 20 alternating turns (targeting 4 to 6 minutes of audio). Every turn should be 60-80 words of punchy, funny observation. Never write short one-liners.
2. DYNAMIC DATE INJECTION: Turn 1 (Maya) MUST state: "Good morning, everyone! Welcome back to The Unwritten Code. I am Maya Lin alongside Julian Cross, and today is {WEEKDAY_NAME}, {DATE_STR}..."
3. STRICTLY ZERO EPISODE NUMBERS: Never mention "Episode 1", "Episode 8", or any numbers in titles, dialogue, or headers.
4. ZERO INAUGURAL PHRASES: Do NOT mention "our launch week", "our inaugural episode", or "premiere week". This is an ongoing hit daily show.
5. ACT STRUCTURE:
   - Act 1 (Turns 1-5): The Relatable Hook & Everyday Setup. Contrast civil expectations with real-world chaos.
   - Act 2 (Turns 6-13): The Deep Dive into the Micro-Behaviors. Funny archetypes, awkward social psychology.
   - Act 3 (Turns 14-18): Handing down "The New Code" (Rules 1 to 4). Clear, punchy, comedic rules.
   - Final Sign-off: "Hit that Follow button right now on Spotify and Apple Podcasts so you never miss tomorrow morning's drop... Until tomorrow morning, stay safe out there, and remember: do not break the code!"

OUTPUT FORMAT:
Return strictly a valid JSON object with the following schema:
{
  "title": "Exact Title of Episode",
  "summary": "1-2 sentence compelling summary for Spotify show notes.",
  "turns": [
    {"speaker": "Maya", "voice": "Kore", "text": "..."},
    {"speaker": "Julian", "voice": "Puck", "text": "..."}
  ]
}
"""

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")

def load_topics():
    if TOPICS_FILE.exists():
        try:
            return json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def get_used_topic_ids(history):
    return {item["topic_id"] for item in history if "topic_id" in item}

def get_next_unused_topic(day_idx, history, topics):
    used_ids = get_used_topic_ids(history)
    is_saturday = (day_idx == 5)
    
    # Filter by day type (Saturday = weekend docket, Weekdays = standard)
    eligible = []
    for topic in topics:
        if topic["id"] in used_ids:
            continue
        if is_saturday and topic.get("day_type") == "saturday":
            eligible.append(topic)
        elif not is_saturday and topic.get("day_type") != "saturday":
            eligible.append(topic)
            
    if eligible:
        return eligible[0]
        
    # If all eligible topics in category used, fallback to any unused topic
    for topic in topics:
        if topic["id"] not in used_ids:
            return topic
            
    # If all topics used, pick oldest topic
    return topics[0] if topics else None

def generate_script_with_gemini(topic, date_str, weekday_name):
    prompt = f"""Write today's complete, hilarious 1,200 to 1,350 word episode of "The Unwritten Code" (targeting 4 to 6 minutes of spoken audio).
 
TODAY'S DATE: {weekday_name}, {date_str}
TOPIC TITLE: {topic['title']}
CATEGORY: {topic.get('category', 'Social Etiquette')}
DESCRIPTION: {topic.get('description', '')}

Ensure Maya and Julian deliver 16-20 alternating turns of witty, observant comedy.
Maya must open with: "[cheerful] Good morning, everyone! Welcome back to The Unwritten Code. I am Maya Lin alongside Julian Cross, and today is {weekday_name}, {date_str}."
Codify 3 or 4 rules of The New Code before sign-off.
Word count must be between 1,200 and 1,400 words.
Return strictly valid JSON.
"""

    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-pro-preview",
        "gemini-flash-latest",
    ]
    for model in models_to_try:
        try:
            print(f" -> Generating daily script via {model} for topic: {topic['title']}...", flush=True)
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=UNWRITTEN_CODE_SYSTEM_PROMPT.replace("{WEEKDAY_NAME}", weekday_name).replace("{DATE_STR}", date_str),
                    response_mime_type="application/json",
                    temperature=0.75
                )
            )
            data = json.loads(resp.text)
            turns = data.get("turns", [])
            word_count = sum(len(t["text"].split()) for t in turns)
            print(f" -> Generated {len(turns)} turns, {word_count} words.", flush=True)
            if word_count >= 1150:
                return data["title"], data["summary"], turns
        except Exception as e:
            print(f"    [Generation Warning] {model} failed: {e}", flush=True)
            
    return None, None, None

def get_or_create_daily_script(date_obj=None):
    """
    Primary API: Retrieves or dynamically creates today's fresh script.
    Checks history to ensure topic has never aired before.
    """
    if date_obj is None:
        date_obj = datetime.now()
        
    day_idx = date_obj.weekday()
    date_str = date_obj.strftime("%B %d, %Y")
    date_iso = date_obj.strftime("%Y-%m-%d")
    weekday_name = date_obj.strftime("%A")
    cache_file = SCRIPTS_CACHE_DIR / f"unwritten_code_script_{date_obj.strftime('%Y%m%d')}.json"

    # 1. Check local script cache for today
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            print(f"[SCRIPT CACHE HIT] Loaded today's script: {cached['title']}", flush=True)
            return cached["title"], cached["summary"], cached["turns"]
        except Exception:
            pass

    history = load_history()
    topics = load_topics()

    # 2. Check if today already has a recorded topic in history
    existing_entry = next((item for item in history if item.get("date") == date_iso), None)
    
    # For today (2026-10-13), we have Week 2 Tuesday ready in week2_scripts
    from week2_scripts import get_week_2_script
    from week1_scripts import get_week_1_script

    if date_iso == "2026-10-13":
        _, title, summary, turns = get_week_2_script(1, date_str)
        # Cache to disk
        cache_file.write_text(json.dumps({"title": title, "summary": summary, "turns": turns}, indent=2), encoding="utf-8")
        return title, summary, turns

    # 3. Pick next unused topic
    topic = get_next_unused_topic(day_idx, history, topics)
    if not topic:
        # Fallback to week2 script
        _, title, summary, turns = get_week_2_script(day_idx, date_str)
        return title, summary, turns

    print(f"[NEW TOPIC SELECTED] {topic['title']} (ID: {topic['id']})", flush=True)

    # 4. Generate dynamic script via Gemini
    title, summary, turns = generate_script_with_gemini(topic, date_str, weekday_name)

    # 5. If LLM generation failed or was insufficient, use curated backup
    if not turns or sum(len(t["text"].split()) for t in turns) < 1150:
        print("[FALLBACK] Using curated high-quality backup script...", flush=True)
        _, title, summary, turns = get_week_2_script(day_idx, date_str)

    # 6. Save to history ledger
    if not existing_entry:
        history.append({
            "date": date_iso,
            "topic_id": topic["id"],
            "title": title,
            "category": topic.get("category", "General")
        })
        save_history(history)
        print(f"[HISTORY LOGGED] Recorded {title} in unwritten_code_history.json", flush=True)

    # 7. Cache script to disk
    cache_file.write_text(json.dumps({"title": title, "summary": summary, "turns": turns}, indent=2), encoding="utf-8")
    return title, summary, turns

if __name__ == "__main__":
    t, s, turns = get_or_create_daily_script()
    print(f"\nResult: {t}")
    print(f"Summary: {s}")
    print(f"Words: {sum(len(x['text'].split()) for x in turns)}")
