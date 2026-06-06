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
    """
    Ask Colum (Jarvis/Friday-style AI) for a short, sharp, intelligent response.
    """
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
    - Use LifeOS data (sleep, focus, mood, screen time, tasks, history) to give specific, actionable advice.
    - If focus is low, suggest short deep work blocks.
    - If sleep is low, prioritize recovery.
    - If mood is low, recommend breaks and reduce load.
    - If screen time is high, suggest a walk or offline time.
    - For tasks, confirm additions clearly.
    - For settings (sleep, focus, mood, screen), confirm changes briefly.

    Example responses:
    - "Good morning, Kavish. Life score is 78. Focus is low — I'd suggest 20 minutes of deep work before meetings."
    - "Sleep set to 8 hours. I'll remind you to sleep by 11 PM."
    - "Task added: 'Write report', high priority, today."
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

    add_task_match = re.search(r"add task[:\s]+(.+)", clean_transcript)
    if add_task_match:
        task_name = add_task_match.group(1).strip()
        priority = "medium"
        if "high priority" in clean_transcript or "priority high" in clean_transcript:
            priority = "high"
        elif "low priority" in clean_transcript or "priority low" in clean_transcript:
            priority = "low"

        time_val = "Today"
        if "tomorrow" in clean_transcript:
            time_val = "Tomorrow"
        elif "this week" in clean_transcript:
            time_val = "This Week"

        return {
            "type": "add_task",
            "text": transcript,
            "action_data": {
                "task": task_name,
                "priority": priority,
                "time": time_val
            }
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
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "sleep" not in st.session_state:
        st.session_state.sleep = 7
    if "focus" not in st.session_state:
        st.session_state.focus = 60
    if "mood" not in st.session_state:
        st.session_state.mood = 7
    if "screen" not in st.session_state:
        st.session_state.screen = 4
    if "history" not in st.session_state:
        st.session_state.history = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


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


def save_daily_snapshot():
    snapshot = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sleep": s["sleep"],
        "focus": s["focus"],
        "mood": s["mood"],
        "screen": s["screen"],
        "life_score": compute_life_score(),
        "tasks_count": len(s["tasks"]),
        "tasks_completed": sum(1 for t in s["tasks"] if t["status"] == "completed")
    }
    s["history"].append(snapshot)


def build_ai_context() -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    tasks_text = "\n".join([
        f"- [{t['status']}] {t['task']} ({t['time']}, priority: {t.get('priority', 'medium')})"
        for t in s["tasks"]
    ])

    if not tasks_text:
        tasks_text = "- No tasks yet."

    history_last_7 = [h for h in s["history"] if h["date"] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]
    history_text = "\n".join([
        f"{h['date']}: sleep={h['sleep']}h, focus={h['focus']}%, mood={h['mood']}/10, screen={h['screen']}h, score={h['life_score']}"
        for h in history_last_7
    ])

    if not history_text:
        history_text = "- No historical data yet."

    context = (
        f"LifeOS Data for {today}:\n"
        f"- Sleep: {s['sleep']} hours\n"
        f"- Focus: {s['focus']}%\n"
        f"- Mood: {s['mood']}/10\n"
        f"- Screen time: {s['screen']} hours\n"
        f"- Life Score: {compute_life_score()}/100\n\n"
        f"Tasks:\n{tasks_text}\n\n"
        f"Last 7 days history:\n{history_text}"
    )

    return context


# =========================
# UI Configuration
# =========================

st.set_page_config(
    page_title="LifeOS - Colum Jarvis AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Futuristic Jarvis-style UI
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

    .task-item {
        background: #111624;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin: 0.4rem 0;
        border: 1px solid #1f293b;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .task-item.completed {
        border-left: 4px solid #4ade80;
        opacity: 0.8;
    }

    .task-item.upcoming {
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

    .listening {
        color: #f472b6;
        font-weight: 600;
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
# Main UI
# =========================

st.markdown('<div class="app-header">🤖 LifeOS - Colum Jarvis AI</div>', unsafe_allow_html=True)
st.markdown("Say 'Hey Colum' to activate your Jarvis-style AI assistant. It responds like Friday/Jarvis from Marvel.")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")

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
            "today": {
                "sleep": s["sleep"],
                "focus": s["focus"],
                "mood": s["mood"],
                "screen": s["screen"],
                "life_score": compute_life_score(),
                "tasks": s["tasks"]
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

    st.markdown("---")
    st.markdown(
        f"""
        <div class="card">
            <div class="metric-label">Total Tasks</div>
            <div style="font-size:1.5rem;font-weight:700;">{len(s['tasks')}</div>
        </div>
        <div class="card">
            <div class="metric-label">Completed</div>
            <div style="font-size:1.5rem;font-weight:700;color:#4ade80;">
                {sum(1 for t in s['tasks'] if t['status'] == 'completed')}
            </div>
        </div>
        """
        , unsafe_allow_html=True
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
            # Optional: make Colum speak (text-to-speech)
            # st.markdown(
            #     f'<button onclick="startSpeaking(`{msg["text"]}`)">🔊 Speak</button>',
            #     unsafe_allow_html=True
            # )

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

            if command["type"] == "add_task":
                data = command["action_data"]
                s["tasks"].append({
                    "task": data["task"],
                    "time": data["time"],
                    "status": "upcoming",
                    "priority": data["priority"]
                })
                ai_text = f"✅ Task added: '{data['task']}', {data['priority']} priority, {data['time']}."
                s["chat_history"].append({"role": "user", "text": user_query})
                s["chat_history"].append({"role": "assistant", "text": ai_text})
                st.success("Task added!")
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
                ai_response = ask_colum_jarvis(user_query, context, "Kavish", s["chat_history"])

                s["chat_history"].append({"role": "user", "text": user_query})
                s["chat_history"].append({"role": "assistant", "text": ai_response})

                st.rerun()

    if st.button("🧹 Clear Chat"):
        s["chat_history"] = []
        st.rerun()

st.markdown("---")

st.markdown('<div class="section-title">➕ Add & Manage Tasks</div>', unsafe_allow_html=True)

col_add1, col_add2, col_add3 = st.columns([2, 1, 1])

with col_add1:
    new_task = st.text_input("Task Name", placeholder="e.g. Write report")

with col_add2:
    task_priority = st.selectbox(
        "Priority",
        ["high", "medium", "low"],
        index=1
    )

with col_add3:
    task_time = st.selectbox(
        "Time",
        ["Today", "Tomorrow", "This Week"],
        index=0
    )

if st.button("➕ Add Task"):
    if new_task.strip():
        s["tasks"].append({
            "task": new_task.strip(),
            "time": task_time,
            "status": "upcoming",
            "priority": task_priority
        })
        st.success("Task added!")
        st.rerun()
    else:
        st.warning("Please enter a task name.")

st.markdown('<br>', unsafe_allow_html=True)

if s["tasks"]:
    st.markdown('<div class="section-title">📋 Your Tasks</div>', unsafe_allow_html=True)

    for i, t in reversed(list(zip(range(len(s["tasks"])), s["tasks"]))):
        status_class = "completed" if t["status"] == "completed" else "upcoming"

        st.markdown(
            f"""
            <div class="task-item {status_class}">
                <div>
                    <strong>{t['task']}</strong>
                    <span style="color:#9aa0a6; margin-left:0.6rem;">
                        ({t['time']}, priority: {t['priority']})
                    </span>
                </div>
                <div>
                    {st.button("✅ Complete", key=f"complete_{i}") if t['status'] != 'completed' else ''}
                    {st.button("🗑️ Delete", key=f"delete_{i}")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.session_state.get(f"complete_{i}", False) and t["status"] != "completed":
            t["status"] = "completed"
            st.rerun()

        if st.session_state.get(f"delete_{i}", False):
            s["tasks"].pop(i)
            st.rerun()
else:
    st.info("📭 No tasks yet. Add your first task above.")

st.markdown("---")

st.markdown('<div class="section-title">📈 Last 7 Days History</div>', unsafe_allow_html=True)

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
        }

        st.dataframe(data, use_container_width=True)
    else:
        st.info("No data for the last 7 days yet. Save daily snapshots.")
else:
    st.info("No history yet. Save daily snapshots to build trends.")
