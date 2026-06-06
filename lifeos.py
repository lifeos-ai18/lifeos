import streamlit as st
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
import time

# =========================
# Local AI Assistant (Colum - JARVIS Style via Ollama)
# =========================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

try:
    import requests
except ImportError:
    st.error("❌ Please install requests: pip install requests")
    raise


def is_hey_colum(transcript: str) -> bool:
    t = transcript.lower().strip()
    return (
        t.startswith("hey colum") or
        t.startswith("hi colum") or
        t.startswith("hello colum") or
        t.startswith("colum") or
        t.startswith("hey, colum") or
        t.startswith("hi, colum")
    )


def ask_colum_jarvis(transcript: str, context: str, name: str = "Kavish", conversation_history: List[Dict] = None) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"

    system_prompt = f"""
    You are Colum, a JARVIS/Friday-style AI assistant for {name}.
    You are smart, calm, confident, and slightly futuristic — like Tony Stark's AI.

    Your style:
    - Short, clear, professional responses (1–4 sentences, max 2–3 bullet points).
    - No fluff, no long explanations.
    - Speak like a real AI assistant in the room with the user.
    - Use the user's name naturally when appropriate.
    - When the user says "Hey Colum", greet them briefly and then answer.

    When responding:
    - Use LifeOS data (sleep, focus, mood, screen time, tasks, history, level, XP, streaks) to give specific, actionable advice.
    - If focus is low, suggest short deep work blocks.
    - If sleep is low, prioritize recovery.
    - If mood is low, recommend breaks and reduce load.
    - If screen time is high, suggest a walk or offline time.
    - For missions/tasks, confirm additions clearly.
    - For settings (sleep, focus, mood, screen), confirm changes briefly.
    - Mention XP, streaks, and level when relevant.

    Example responses:
    - "Good morning, Kavish. LifeOS Level 7. Life score is 78. Focus is low — I'd suggest 20 minutes of deep work before meetings."
    - "Sleep set to 8 hours. You're on a 5-day streak. Keep it up."
    - "Mission added: 'Complete Deep Work Sprint', today. Reward: +20 XP."
    - "Your mood is 5/10. Take breaks and avoid overload today."

    Always stay in character as Colum — a futuristic AI assistant.
    """

    user_prompt = (
        f"LifeOS Context:\n{context}\n\n"
        f"{name} says: {transcript}"
    )

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    if conversation_history:
        for turn in conversation_history[-4:]:
            messages.append({
                "role": turn["role"],
                "content": turn["text"]
            })

    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 400,
        "stream": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code != 200:
            return f"Colum error (status {resp.status_code}): {resp.text}"
        data = resp.json()
        return data["message"]["content"].strip()
    except Exception as e:
        return f"Colum could not connect to Ollama: {e}\nMake sure Ollama is running and you pulled the model (e.g., `ollama pull llama3`)."


# =========================
# Voice Command Parser
# =========================

def parse_voice_command(transcript: str) -> Dict[str, Any]:
    transcript_lower = transcript.lower().strip()

    clean_transcript = transcript_lower
    if is_hey_colum(transcript_lower):
        clean_transcript = re.sub(
            r"^(hey\s*colum|hi\s*colum|hello\s*colum|colum)[,\s:]*",
            "",
            transcript_lower
        ).strip()

    sleep_match = re.search(r"set my sleep to\s+(\d+\.?\d*)\s*hours?", clean_transcript)
    if sleep_match:
        value = float(sleep_match.group(1))
        return {
            "type": "set_sleep",
            "text": transcript,
            "action_data": {"sleep": value}
        }

    focus_match = re.search(r"set my focus to\s+(\d+)\s*percent?", clean_transcript)
    if focus_match:
        value = int(focus_match.group(1))
        return {
            "type": "set_focus",
            "text": transcript,
            "action_data": {"focus": value}
        }

    mood_match = re.search(r"set my mood to\s+(\d+)\s*/\s*10?", clean_transcript)
    if mood_match:
        value = int(mood_match.group(1))
        return {
            "type": "set_mood",
            "text": transcript,
            "action_data": {"mood": value}
        }

    screen_match = re.search(r"set my screen time to\s+(\d+\.?\d*)\s*hours?", clean_transcript)
    if screen_match:
        value = float(screen_match.group(1))
        return {
            "type": "set_screen",
            "text": transcript,
            "action_data": {"screen": value}
        }

    add_mission_match = re.search(r"(add mission|add task)[\s:]+(.+)", clean_transcript)
    if add_mission_match:
        mission_name = add_mission_match.group(2).strip()
        return {
            "type": "add_mission",
            "text": transcript,
            "action_data": {"mission": mission_name}
        }

    return {
        "type": "question",
        "text": transcript,
        "action_data": {}
    }


# =========================
# Session State Initialization
# =========================

def init_session_state():
    # Profile
    if "name" not in st.session_state:
        st.session_state.name = "Kavish"
    if "age" not in st.session_state:
        st.session_state.age = 20
    if "avatar" not in st.session_state:
        st.session_state.avatar = "👤"

    # Daily metrics
    if "sleep" not in st.session_state:
        st.session_state.sleep = 7
    if "focus" not in st.session_state:
        st.session_state.focus = 60
    if "mood" not in st.session_state:
        st.session_state.mood = 7
    if "screen" not in st.session_state:
        st.session_state.screen = 4

    # Goals
    if "goals" not in st.session_state:
        st.session_state.goals = []

    # Games: missions, XP, streak, level
    if "missions" not in st.session_state:
        st.session_state.missions = []
    if "xp" not in st.session_state:
        st.session_state.xp = 0
    if "streak" not in st.session_state:
        st.session_state.streak = 0
    if "last_snapshot_date" not in st.session_state:
        st.session_state.last_snapshot_date = None

    # History & chat
    if "history" not in st.session_state:
        st.session_state.history = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # App flow
    if "startup_done" not in st.session_state:
        st.session_state.startup_done = False
    if "onboarded" not in st.session_state:
        st.session_state.onboarded = False
    if "assessment_done" not in st.session_state:
        st.session_state.assessment_done = False


init_session_state()
s = st.session_state


# =========================
# Helper Functions
# =========================

def compute_life_score() -> int:
    return int(
        (s["sleep"] * 10 +
         s["focus"] +
         s["mood"] * 10) / 3
    )


def compute_level(xp: int) -> int:
    return 1 + xp // 50


def save_daily_snapshot():
    today_str = datetime.now().strftime("%Y-%m-%d")

    if s["last_snapshot_date"] != today_str:
        if s["last_snapshot_date"] is not None:
            s["streak"] += 1
        s["last_snapshot_date"] = today_str

    snapshot = {
        "date": today_str,
        "sleep": s["sleep"],
        "focus": s["focus"],
        "mood": s["mood"],
        "screen": s["screen"],
        "life_score": compute_life_score(),
        "missions_count": len(s["missions"]),
        "missions_completed": sum(1 for m in s["missions"] if m["status"] == "completed"),
        "xp": s["xp"],
        "streak": s["streak"],
        "level": compute_level(s["xp"])
    }
    s["history"].append(snapshot)


def build_ai_context() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    name = s["name"]
    level = compute_level(s["xp"])

    missions_text = "\n".join([
        f"- [{m['status']}] {m['mission']} ({m['time']})"
        for m in s["missions"]
    ])
    if not missions_text:
        missions_text = "- No missions yet."

    history_last_7 = [h for h in s["history"] if h["date"] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]
    history_text = "\n".join([
        f"{h['date']}: sleep={h['sleep']}h, focus={h['focus']}%, mood={h['mood']}/10, screen={h['screen']}h, score={h['life_score']}, XP={h['xp']}, streak={h['streak']}, level={h['level']}"
        for h in history_last_7
    ])
    if not history_text:
        history_text = "- No historical data yet."

    goals_text = "\n".join([f"- {g}" for g in s["goals"]])
    if not goals_text:
        goals_text = "- No goals yet."

    goals_full = ", ".join(s["goals"]) if s["goals"] else "No goals set"

    context = (
        f"LifeOS Data for {name} (Level {level}), {today}:\n"
        f"- Age: {s['age']}\n"
        f"- Sleep: {s['sleep']} hours\n"
        f"- Focus: {s['focus']}%\n"
        f"- Mood: {s['mood']}/10\n"
        f"- Screen time: {s['screen']} hours\n"
        f"- Life Score: {compute_life_score()}/100\n"
        f"- Total XP: {s['xp']}\n"
        f"- Streak: {s['streak']} days\n"
        f"- Level: {level}\n"
        f"- Goals: {goals_full}\n\n"
        f"Missions:\n{missions_text}\n\n"
        f"Last 7 days history:\n{history_text}"
    )

    return context


# =========================
# UI Configuration (JARVIS HUD Style)
# =========================

st.set_page_config(
    page_title="LifeOS - Colum JARVIS AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700');

    body {
        font-family: 'Inter', sans-serif;
        background-color: #0b0f19;
        color: #e6e6e6;
    }

    .app-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px #2563eb;
    }

    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
        margin-top
</parameter>
</function>
</tool_call>
