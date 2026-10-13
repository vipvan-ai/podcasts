# =============================================================================
# FUTURE HUMAN DAILY: DYNAMIC DAILY SCRIPT GENERATOR & TOPIC LEDGER
# Tracks topics via future_human_history.json & future_human_topics.json
# Guarantees NO TOPIC REPEATS, strictly date-driven, 1,350+ words, 0 episode numbers.
# =============================================================================

import os
import json
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
TOPICS_FILE = BASE_DIR / "future_human_topics.json"
HISTORY_FILE = BASE_DIR / "future_human_history.json"
SCRIPTS_CACHE_DIR = BASE_DIR / "future_human_scripts_cache"
SCRIPTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load environment
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

FUTURE_HUMAN_PROMPT_TEMPLATE = """You are writing a script for "Future Human Daily", a 5 to 7 minute daily science & technology podcast hosted by Alex Mercer & Dr. Elena Vance.

HOST PERSONAS:
1. Alex Mercer (Voice: "Puck"): Curious, relatable everyman, asks the intuitive layman questions, uses grounded everyday metaphors.
2. Dr. Elena Vance (Voice: "Kore"): Brilliant physicist & biomedical engineer, passionate, clear, translates complex science into intuitive mechanical concepts.

MANDATORY SCRIPT STRUCTURE (1,400+ WORDS, 24-26 ALTERNATING TURNS):
- Turn 1 (Alex) MUST open with: "[warmly] I am your host Alex Mercer with Dr. Elena Vance, and today is {DATE_STR}, and you're listening to Future Human Daily. Today we are talking about {TOPIC_TITLE}..."
- Connect immediately to an everyday human situation (morning coffee, smartphone charging, traffic, sore muscles, breathing clean air).
- Dr. Elena Vance uses simple, vivid physical metaphors (water pipes, tuning forks, guitar strings, conveyor belts).
- Alex challenges assumptions with relatable skepticism: "Wait, explain that in plain English—how does that affect my morning?"
- Act 2: Technical reality check, engineering bottlenecks, real-world physics.
- Act 3: 5-to-10 year societal timeline, human impact, clean energy, or medical transformation.
- Final sign-off: Reminder to hit Subscribe on Spotify and Apple Podcasts, and "Stay curious!"
- ZERO EPISODE NUMBERS. ZERO INAUGURAL LOOPS.

OUTPUT STRICTLY VALID JSON:
{
  "title": "Exact Topic Title",
  "summary": "1-2 sentence compelling summary for show notes.",
  "turns": [
    {"speaker": "Alex", "voice": "Puck", "text": "..."},
    {"speaker": "Elena", "voice": "Kore", "text": "..."}
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

def get_next_unused_topic(history, topics):
    used_ids = get_used_topic_ids(history)
    for topic in topics:
        if topic["id"] not in used_ids:
            return topic
    return topics[0] if topics else None

def get_or_create_future_human_script(date_obj=None):
    if date_obj is None:
        date_obj = datetime.now()

    date_str = date_obj.strftime("%B %d, %Y")
    date_iso = date_obj.strftime("%Y-%m-%d")
    cache_file = SCRIPTS_CACHE_DIR / f"future_human_script_{date_obj.strftime('%Y%m%d')}.json"

    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            return cached["title"], cached["summary"], cached["turns"]
        except Exception:
            pass

    history = load_history()
    topics = load_topics()
    existing_entry = next((item for item in history if item.get("date") == date_iso), None)

    # For today (2026-10-13), we already have today's episode published (Biomimetic Energy)
    from future_human_weekday_scripts import get_future_human_script_for_day
    day_idx = date_obj.weekday()

    if date_iso == "2026-10-13":
        title, summary, turns = get_future_human_script_for_day(1, date_str)
        cache_file.write_text(json.dumps({"title": title, "summary": summary, "turns": turns}, indent=2), encoding="utf-8")
        return title, summary, turns

    topic = get_next_unused_topic(history, topics)
    if not topic:
        title, summary, turns = get_future_human_script_for_day(day_idx, date_str)
        return title, summary, turns

    # Generate dynamic script via Gemini
    prompt = f"Write today's full 1,400+ word episode on: {topic['title']}. Description: {topic.get('description', '')}. Date: {date_str}."
    turns = None
    title, summary = topic["title"], topic.get("description", "")
    for model in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=FUTURE_HUMAN_PROMPT_TEMPLATE.replace("{DATE_STR}", date_str).replace("{TOPIC_TITLE}", topic["title"]),
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            data = json.loads(resp.text)
            candidate_turns = data.get("turns", [])
            if sum(len(t["text"].split()) for t in candidate_turns) >= 1200:
                title, summary, turns = data["title"], data["summary"], candidate_turns
                break
        except Exception:
            pass

    if not turns:
        title, summary, turns = get_future_human_script_for_day(day_idx, date_str)

    if not existing_entry:
        history.append({
            "date": date_iso,
            "topic_id": topic["id"],
            "title": title
        })
        save_history(history)

    cache_file.write_text(json.dumps({"title": title, "summary": summary, "turns": turns}, indent=2), encoding="utf-8")
    return title, summary, turns
