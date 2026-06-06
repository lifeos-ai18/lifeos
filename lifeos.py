import streamlit as st
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# =========================
# AI Assistant (LLM)
# =========================

# Configure your API key (set via environment variable or Streamlit secrets)
# Example: export OPENAI_API_KEY="your-key"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.warning("⚠️ OPENAI_API_KEY not set. AI assistant disabled. Set it via `export OPENAI_API_KEY='your-key'`")

from openai import OpenAI

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


def ask_ai_assistant(context: str, user_query: str = None) -> str:
    """
    Ask the AI assistant for personalized LifeOS advice.
    If user_query is provided, answer that; otherwise, generate advice from context.
    """
    if not client:
        return "AI assistant is unavailable (no API key)."

    system_prompt = """
    You are LifeOS AI, a super-intelligent personal productivity and wellness assistant.
    Analyze the user's LifeOS data (sleep, focus, mood, screen time, tasks) and provide:
    - Personalized, actionable advice
    - Priority recommendations for today
    - Wellness and productivity insights
    - Answers to any user question about their lifeOS

    Be concise, empathetic, and highly practical. Use bullet points for clarity.
    """

    user_prompt = context

    if user_query:
        user_prompt += f"\n\nUser question: {user_query}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4", "claude-3", etc.
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=600
    )

    return response.choices[0].message.content


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
        # Store daily snapshots: {date: {sleep, focus, mood, screen, life_score}}
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
    """Build a structured context for the AI assistant."""
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
    page_title="LifeOS AI - Super Personal Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700');

    body {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117;
        color: #e6e6e6;
    }

    .app-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }

    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #ffffff;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .card {
        background: #161b22;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border: 1px solid #232a35;
    }

    .metric-card {
        background: #1f2430;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #232a35;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #4ade80;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #9aa0a6;
    }

    .task-item {
        background: #161b22;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin: 0.4rem 0;
        border: 1px solid #232a35;
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
        background: #1f2430;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.6rem 0;
        border: 1px solid #232a35;
        line-height: 1.5;
    }

    .user-message {
        background: #161b22;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.6rem 0;
        border: 1px solid #232a35;
        line-height: 1.5;
    }

    .stButton>button {
        background: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
    }

    .stButton>button:hover {
        background: #1d4ed8;
    }

    .stTextInput>input, .stNumberInput>input {
        background: #161b22;
        border: 1px solid #232a35;
        color: #e6e6e6;
        border-radius: 8px;
    }

    .highlight {
        color: #4ade80;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# Main UI
# =========================

st.markdown('<div class="app-header">🧠 LifeOS AI - Super Personal Assistant</div>', unsafe_allow_html=True)
st.markdown("Your intelligent productivity & wellness dashboard")

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

# Row 1: Life Score + Inputs Summary
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
    st.markdown('<div class="section-title">Today’s Summary</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-title">🧠 LifeOS AI Assistant</div>', unsafe_allow_html=True)

    # Chat history
    for msg in s["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-message">🤖 {msg["text"]}</div>', unsafe_allow_html=True)

    user_query = st.text_input(
        "Ask LifeOS AI:",
        placeholder="e.g. What should I prioritize today? How can I improve my focus?",
        label_visibility="collapsed"
    )

    if st.button("🚀 Send"):
        if not user_query.strip():
            st.warning("Please enter a question.")
        else:
            context = build_ai_context()
            ai_response = ask_ai_assistant(context, user_query)

            s["chat_history"].append({"role": "user", "text": user_query})
            s["chat_history"].append({"role": "assistant", "text": ai_response})

            st.rerun()

    if st.button("🧹 Clear Chat"):
        s["chat_history"] = []
        st.rerun()

    if not OPENAI_API_KEY:
        st.info(
            "ℹ️ AI assistant is disabled because OPENAI_API_KEY is not set. "
            "Set it to get super AI advice."
        )

st.markdown("---")

# Row 2: Tasks
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
        idx = t["task"]  # using task text as key (simple approach)

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

        # Handle complete/delete
        if st.session_state.get(f"complete_{i}", False) and t["status"] != "completed":
            t["status"] = "completed"
            st.rerun()

        if st.session_state.get(f"delete_{i}", False):
            s["tasks"].pop(i)
            st.rerun()
else:
    st.info("📭 No tasks yet. Add your first task above.")

st.markdown("---")

# Row 3: History (last 7 days)
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
        st.info("No data for the last 7 days yet. Save daily snapshots to build history.")
else:
    st.info("No history yet. Save daily snapshots to build trends.")
