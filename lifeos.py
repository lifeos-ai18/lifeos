import streamlit as st
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

# =========================
# Local AI Assistant (Colum - Jarvis Style via Ollama)
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
    You are Colum, a Jarvis/Friday-style AI assistant for {name}.
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
    # Simple: level = 1 + xp // 50
    return 1 + xp // 50


def save_daily_snapshot():
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Update streak if new day
    if s["last_snapshot_date"] != today_str:
        if s["last_snapshot_date"] is not None:
            # New day
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
        f"- Level: {level}\n\n"
        f"Goals:\n{goals_text}\n\n"
        f"Missions:\n{missions_text}\n\n"
        f"Last 7 days history:\n{history_text}"
    )

    return context


# =========================
# UI Configuration
# =========================

st.set_page_config(
    page_title="LifeOS - Colum Jarvis AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Futuristic UI + Startup animations
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
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
    }

    .card {
        background: #111624;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border: 1px solid #1f293b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .metric-card {
        background: #151a2a;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #1f293b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4ade80;
        text-shadow: 0 0 12px #4ade80;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #9aa0a6;
    }

    .mission-item {
        background: #111624;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin: 0.4rem 0;
        border: 1px solid #1f293b;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .mission-item.completed {
        border-left: 4px solid #4ade80;
        opacity: 0.8;
    }

    .mission-item.upcoming {
        border-left: 4px solid #60a5fa;
    }

    .ai-message {
        background: #151a2a;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.6rem 0;
        border: 1px solid #1f293b;
        line-height: 1.5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .user-message {
        background: #111624;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.6rem 0;
        border: 1px solid #1f293b;
        line-height: 1.5;
    }

    .stButton>button {
        background: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(37,99,235,0.3);
    }

    .stButton>button:hover {
        background: #1d4ed8;
    }

    .stTextInput>input, .stNumberInput>input {
        background: #111624;
        border: 1px solid #1f293b;
        color: #e6e6e6;
        border-radius: 8px;
    }

    .highlight {
        color: #4ade80;
        font-weight: 600;
    }

    .welcome-box {
        background: linear-gradient(135deg, #111624 0%, #151a2a 100%);
        border: 1px solid #2563eb;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(37,99,235,0.2);
        margin: 2rem 0;
    }

    .welcome-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }

    .welcome-subtitle {
        font-size: 1.1rem;
        color: #9aa0a6;
        margin-bottom: 1.5rem;
    }

    .feature-list {
        text-align: left;
        margin: 0 auto;
        max-width: 600px;
        color: #d1d5db;
        line-height: 1.8;
    }

    .feature-list li {
        margin: 0.4rem 0;
    }

    .startup-screen {
        background: #0b0f19;
        color: #e6e6e6;
        text-align: center;
        padding: 4rem 2rem;
    }

    .startup-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
        text-shadow: 0 0 20px #2563eb;
    }

    .startup-line {
        font-size: 1.2rem;
        color: #9aa0a6;
        margin: 0.8rem 0;
    }

    .glow-btn {
        background: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 1rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 0 20px rgba(37,99,235,0.6);
        cursor: pointer;
    }

    .xp-bar {
        background: #1f293b;
        border-radius: 8px;
        height: 12px;
        width: 100%;
        overflow: hidden;
    }

    .xp-fill {
        background: linear-gradient(90deg, #4ade80, #2563eb);
        height: 100%;
    }
    </style>

    <script>
    let isListening = false;

    function startSpeaking(text) {
        if (!window.speechSynthesis) {
            return;
        }
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "en-US";
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        speechSynthesis.speak(utterance);
    }

    function startListening(callback) {
        if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
            callback("Speech recognition not supported in this browser.");
            return;
        }

        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            isListening = true;
            document.getElementById("voice-status").innerText = "🎤 Listening... say 'Hey Colum' + your question.";
        };

        recognition.onend = () => {
            isListening = false;
            document.getElementById("voice-status").innerText = "🔴 Not listening.";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            callback(transcript);
        };

        recognition.onerror = (event) => {
            callback("Error: " + event.error);
        };

        recognition.start();
    }

    window.startListening = startListening;
    window.startSpeaking = startSpeaking;
    </script>
    """,
    unsafe_allow_html=True
)


# =========================
# Startup Screen (Jarvis Style)
# =========================

if not s.get("startup_done", False):
    st.markdown(
        """
        <div class="startup-screen">
            <div class="startup-title">🤖 Initializing LifeOS...</div>
            <div class="startup-line">Loading User Profile...</div>
            <div class="startup-line">Loading AI Memory...</div>
            <div class="startup-line">Analyzing Daily Patterns...</div>
            <div class="startup-line" style="margin-top:2rem;color:#4ade80;">Welcome Back, Kavish.</div>
            <div class="startup-line" style="color:#9aa0a6;">BRO THIS FEELS INSANE 🤖</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🧠 Enter LifeOS", key="startup-enter", class_="glow-btn"):
        s["startup_done"] = True
        st.rerun()

else:
    # =========================
    # Main LifeOS Dashboard
    # =========================

    level = compute_level(s["xp"])
    xp = s["xp"]

    # Top-right profile
    st.markdown(
        f"""
        <div style="float:right;text-align:right;">
            <div style="font-size:1.1rem;font-weight:600;color:#ffffff;">👤 {s['name']}</div>
            <div style="font-size:0.9rem;color:#4ade80;">LifeOS Level {level}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="app-header">🧠 LifeOS - Colum Jarvis AI</div>', unsafe_allow_html=True)
    st.markdown("Your personal AI operating system. Say 'Hey Colum' to activate your Jarvis-style assistant.")

    # Onboarding / Profile
    if not s.get("onboarded", False):
        st.markdown('<div class="section-title">⚡ Set Up Your Profile</div>', unsafe_allow_html=True)
        st.markdown("Enter your details to build your LifeOS profile.")

        s["name"] = st.text_input("Name", value=s["name"])
        s["age"] = st.number_input("Age", min_value=1, max_value=120, value=s["age"])
        s["avatar"] = st.text_input("Avatar", value=s["avatar"])

        goals_input = st.text_input("Goals (comma-separated)", value=", ".join(s["goals"]))
        if goals_input:
            s["goals"] = [g.strip() for g in goals_input.split(",") if g.strip()]

        if st.button("✅ Continue to Assessment"):
            s["onboarded"] = True
            st.rerun()

    # Assessment
    elif not s.get("assessment_done", False):
        st.markdown('<div class="section-title">⚡ Quick Assessment</div>', unsafe_allow_html=True)
        st.markdown("Answer a few questions to set your initial LifeOS profile.")

        s["sleep"] = st.number_input(
            "😴 How many hours did you sleep last night?",
            min_value=0,
            max_value=24,
            value=s["sleep"],
            step=0.5
        )

        s["focus"] = st.number_input(
            "🎯 What's your typical focus level today? (%)",
            min_value=0,
            max_value=100,
            value=s["focus"],
            step=1
        )

        s["mood"] = st.number_input(
            "❤️ How's your mood today? (1–10)",
            min_value=1,
            max_value=10,
            value=s["mood"],
            step=1
        )

        s["screen"] = st.number_input(
            "📱 Estimated screen time today (hours)?",
            min_value=0,
            max_value=24,
            value=s["screen"],
            step=0.5
        )

        if st.button("✅ Complete Assessment"):
            s["assessment_done"] = True
            save_daily_snapshot()
            st.success("Assessment complete! Welcome to LifeOS.")
            st.rerun()

    else:
        # Sidebar
        with st.sidebar:
            st.title("⚙️ Settings")

            st.markdown(f'<div class="section-title">{s["avatar"]} {s["name"]}</div>', unsafe_allow_html=True)
            st.markdown(f"<div style='color:#4ade80;'>LifeOS Level {level} • {xp} XP • 🔥 {s['streak']} Day Streak</div>", unsafe_allow_html=True)

            # XP Bar
            next_level_xp = level * 50
            prev_level_xp = (level - 1) * 50
            xp_in_level = xp - prev_level_xp
            xp_capacity = next_level_xp - prev_level_xp
            xp_percent = min(100, max(0, (xp_in_level / xp_capacity) * 100)) if xp_capacity > 0 else 0

            st.markdown(
                f"""
                <div class="xp-bar">
                    <div class="xp-fill" style="width:{xp_percent}%"></div>
                </div>
                <div style="font-size:0.8rem;color:#9aa0a6;margin-top:0.4rem;">
                    {xp} XP / {next_level_xp} XP (Level {level})
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown('<div class="section-title">Daily Inputs</div>', unsafe_allow_html=True)

            s["sleep"] = st.number_input(
                "😴 Sleep (hours)",
                min_value=0,
                max_value=24,
                value=s["sleep"],
                step=0.5
            )

            s["focus"] = st.number_input(
                "🎯 Focus (%)",
                min_value=0,
                max_value=100,
                value=s["focus"],
                step=1
            )

            s["mood"] = st.number_input(
                "❤️ Mood (1–10)",
                min_value=1,
                max_value=10,
                value=s["mood"],
                step=1
            )

            s["screen"] = st.number_input(
                "📱 Screen time (hours)",
                min_value=0,
                max_value=24,
                value=s["screen"],
                step=0.5
            )

            st.markdown('<div class="section-title">AI Settings</div>', unsafe_allow_html=True)

            st.text_input(
                "Ollama URL",
                value=OLLAMA_BASE_URL,
                disabled=True,
                help="Current Ollama base URL (env: OLLAMA_BASE_URL)"
            )

            st.text_input(
                "AI Model",
                value=OLLAMA_MODEL,
                disabled=True,
                help="Current model (env: OLLAMA_MODEL, default: llama3)"
            )

            st.markdown('<div class="section-title">Actions</div>', unsafe_allow_html=True)

            if st.button("💾 Save Daily Snapshot"):
                save_daily_snapshot()
                st.success("Daily snapshot saved!")

            if st.button("📤 Export to JSON"):
                data = {
                    "profile": {
                        "name": s["name"],
                        "age": s["age"],
                        "avatar": s["avatar"]
                    },
                    "today": {
                        "sleep": s["sleep"],
                        "focus": s["focus"],
                        "mood": s["mood"],
                        "screen": s["screen"],
                        "life_score": compute_life_score(),
                        "missions": s["missions"],
                        "xp": s["xp"],
                        "streak": s["streak"],
                        "level": level
                    },
                    "history": s["history"]
                }
                json_str = json.dumps(data, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"lifeos_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

        # Main content
        st.markdown('<br>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            life_score = compute_life_score()
            st.markdown(
                f"""
                <div class="card metric-card">
                    <div class="metric-value">{life_score}</div>
                    <div class="metric-label">Life Score /100</div>
                </div>
                <div style="text-align:center;margin-top:0.8rem;color:#9aa0a6;">
                    🔥 {s['streak']} Day Streak • Level {level} • {xp} XP
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown('<div class="section-title">Today's Summary</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="card">
                    😴 Sleep: <span class="highlight">{s['sleep']}h</span><br>
                    🎯 Focus: <span class="highlight">{s['focus']}%</span><br>
                    ❤️ Mood: <span class="highlight">{s['mood']}/10</span><br>
                    📱 Screen: <span class="highlight">{s['screen']}h</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown('<div class="section-title">🤖 Colum Jarvis AI</div>', unsafe_allow_html=True)

            st.markdown(
                '<div id="voice-status" style="margin-bottom:0.6rem;color:#9aa0a6;">🔴 Not listening.</div>',
                unsafe_allow_html=True
            )

            # Chat history
            for msg in s["chat_history"]:
                if msg["role"] == "user":
                    st.markdown(f'<div class="user-message">👤 {msg["text"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ai-message">🤖 Colum: {msg["text"]}</div>', unsafe_allow_html=True)

            user_query = st.text_input(
                "Talk to Colum (say 'Hey Colum' + your question):",
                placeholder="e.g. 'Hey Colum, what should I prioritize today?'",
                label_visibility="collapsed"
            )

            col_voice1, col_voice2 = st.columns([3, 1])

            with col_voice2:
                if st.button("🎤 Start Voice"):
                    st.session_state["voice_requested"] = True

            if st.session_state.get("voice_requested", False):
                st.session_state["voice_requested"] = False
                st.markdown(
                    """
                    <script>
                    window.startListening(function(transcript) {
                        document.querySelector('input[type="text"]').value = transcript;
                    });
                    </script>
                    """,
                    unsafe_allow_html=True
                )

            if st.button("🚀 Send"):
                if not user_query.strip():
                    st.warning("Please enter a message or use voice.")
                else:
                    command = parse_voice_command(user_query)

                    if command["type"] == "add_mission":
                        mission_name = command["action_data"]["mission"]
                        s["missions"].append({
                            "mission": mission_name,
                            "time": "Today",
                            "status": "upcoming"
                        })
                        s["xp"] += 10
                        ai_text = f"✅ Mission added: '{mission_name}', today. Reward: +10 XP."
                        s["chat_history"].append({"role": "user", "text": user_query})
                        s["chat_history"].append({"role": "assistant", "text": ai_text})
                        st.success("Mission added!")
                        st.rerun()

                    elif command["type"] == "set_sleep":
                        s["sleep"] = command["action_data"]["sleep"]
                        ai_text = f"✅ Sleep set to {command['action_data']['sleep']} hours."
                        s["chat_history"].append({"role": "user", "text": user_query})
                        s["chat_history"].append({"role": "assistant", "text": ai_text})
                        st.success(f"Sleep set to {s['sleep']}h")
                        st.rerun()

                    elif command["type"] == "set_focus":
                        s["focus"] = command["action_data"]["focus"]
                        ai_text = f"✅ Focus set to {command['action_data']['focus']}%."
                        s["chat_history"].append({"role": "user", "text": user_query})
                        s["chat_history"].append({"role": "assistant", "text": ai_text})
                        st.success(f"Focus set to {s['focus']}%")
                        st.rerun()

                    elif command["type"] == "set_mood":
                        s["mood"] = command["action_data"]["mood"]
                        ai_text = f"✅ Mood set to {command['action_data']['mood']}/10."
                        s["chat_history"].append({"role": "user", "text": user_query})
                        s["chat_history"].append({"role": "assistant", "text": ai_text})
                        st.success(f"Mood set to {s['mood']}/10")
                        st.rerun()

                    elif command["type"] == "set_screen":
                        s["screen"] = command["action_data"]["screen"]
                        ai_text = f"✅ Screen time set to {command['action_data']['screen']} hours."
                        s["chat_history"].append({"role": "user", "text": user_query})
                        s["chat_history"].append({"role": "assistant", "text": ai_text})
                        st.success(f"Screen time set to {s['screen']}h")
                        st.rerun()

                    else:
                        context = build_ai_context()
                        ai_response = ask_colum_jarvis(user_query, context, s["name"], s["chat_history"])

                        s["chat_history"].append({"role": "user", "text": user_query})
                        s["chat_history"].append({"role": "assistant", "text": ai_response})

                        st.rerun()

            if st.button("🧹 Clear Chat"):
                s["chat_history"] = []
                st.rerun()

        st.markdown("---")

        # Daily Mission System
        st.markdown('<div class="section-title">Today's Mission</div>', unsafe_allow_html=True)

        col_m1, col_m2, col_m3 = st.columns([2, 1, 1])

        with col_m1:
            new_mission = st.text_input("Mission Name", placeholder="e.g. Complete Deep Work Sprint")

        with col_m2:
            mission_time = st.selectbox(
                "Time",
                ["Today", "Tomorrow", "This Week"],
                index=0
            )

        if st.button("➕ Add Mission"):
            if new_mission.strip():
                s["missions"].append({
                    "mission": new_mission.strip(),
                    "time": mission_time,
                    "status": "upcoming"
                })
                st.success("Mission added!")
                st.rerun()
            else:
                st.warning("Please enter a mission name.")

        st.markdown('<br>', unsafe_allow_html=True)

        if s["missions"]:
            st.markdown('<div class="section-title">📋 Your Missions</div>', unsafe_allow_html=True)

            for i, m in reversed(list(zip(range(len(s["missions"])), s["missions"]))):
                status_class = "completed" if m["status"] == "completed" else "upcoming"

                st.markdown(
                    f"""
                    <div class="mission-item {status_class}">
                        <div>
                            <strong>{m['mission']}</strong>
                            <span style="color:#9aa0a6; margin-left:0.6rem;">
                                ({m['time']})
                            </span>
                        </div>
                        <div>
                            {st.button("✅ Complete", key=f"complete_m_{i}") if m['status'] != 'completed' else ''}
                            {st.button("🗑️ Delete", key=f"delete_m_{i}")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if m["status"] != "completed" and st.session_state.get(f"complete_m_{i}", False):
                    m["status"] = "completed"
                    s["xp"] += 20
                    st.success("Mission completed! +20 XP")
                    st.rerun()

                if st.session_state.get(f"delete_m_{i}", False):
                    s["missions"].pop(i)
                    st.rerun()
        else:
            st.info("📭 No missions yet. Add your first mission above.")

        st.markdown("---")

        # Progress Tracking + History
        st.markdown('<div class="section-title">📈 Progress Tracking (Last 7 Days)</div>', unsafe_allow_html=True)

        if s["history"]:
            history_last_7 = sorted(
                [h for h in s["history"] if h["date"] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")],
                key=lambda x: x["date"]
            )

            if history_last_7:
                data = {
                    "Date": [h["date"] for h in history_last_7],
                    "Sleep (h)": [h["sleep"] for h in history_last_7],
                    "Focus (%)": [h["focus"] for h in history_last_7],
                    "Mood (1–10)": [h["mood"] for h in history_last_7],
                    "Screen (h)": [h["screen"] for h in history_last_7],
                    "Life Score": [h["life_score"] for h in history_last_7],
                    "XP": [h["xp"] for h in history_last_7],
                    "Streak": [h["streak"] for h in history_last_7],
                    "Level": [h["level"] for h in history_last_7],
                }

                st.dataframe(data, use_container_width=True)
            else:
                st.info("No data for the last 7 days yet. Save daily snapshots.")
        else:
            st.info("No history yet. Save daily snapshots to build trends.")
