       import streamlit as st
import datetime as dt
import google.generativeai as genai

st.set_page_config(
    page_title="LifeOS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
if "state" not in st.session_state:
    st.session_state.state = {
        "name": "user",
        "goals": [
            {"title": "Health", "progress": 72, "next": "Walk 30 min after lunch"},
            {"title": "Deep Work", "progress": 61, "next": "Complete one focused 90-min block"},
            {"title": "Balance", "progress": 54, "next": "Call a friend tonight"},
        ],
        "tasks": [
            {"task": "Review top priorities", "time": "08:30", "status": "done"},
            {"task": "Deep work sprint", "time": "10:00", "status": "upcoming"},
            {"task": "Workout", "time": "18:30", "status": "upcoming"},
        ],
        "events": [
            {"time": "09:30", "title": "Team sync"},
            {"time": "13:00", "title": "Lunch break"},
            {"time": "20:00", "title": "Reading + wind down"},
        ],
        "sleep": 7.4,
        "mood": 7,
        "focus": 78,
        "screen": 5.6,
        "work_hours": 6.8,
        "exercise": 32,
        "social": 1.2,
        "memory": [
            "Prefers calm, minimal plans.",
            "Best focus window: mornings.",
            "Likes supportive reminders.",
        ],
    }

css = """
<style>
    .stApp {
        background: radial-gradient(circle at top, #1b2340 0%, #0b1020 45%, #060913 100%);
        color: #f4f7fb;
    }
    [data-testid='stSidebar'] {
        background: rgba(8,12,24,0.72);
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .glass {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        backdrop-filter: blur(16px);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 20px 60px rgba(0,0,0,.28);
    }
    .hero {
        padding: 22px 26px;
        border-radius: 28px;
        background: linear-gradient(135deg, rgba(118,96,255,.22), rgba(0,212,255,.10));
        border: 1px solid rgba(255,255,255,0.10);
    }
    .small { opacity:.78; font-size: .92rem; }
    .metric { font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .label {
        font-size: .82rem;
        opacity: .75;
        text-transform: uppercase;
        letter-spacing: .08em;
    }
    .chip {
        display:inline-block;
        padding: 6px 10px;
        margin: 4px 6px 0 0;
        border-radius: 999px;
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.10);
    }
</style>
"""

st.markdown(css, unsafe_allow_html=True)

s = st.session_state.state
now = dt.datetime.now()

with st.sidebar:
    st.markdown("### LifeOS")
    st.caption("Your balanced AI operating system")
    mode = st.selectbox("Mode", ["Dashboard", "Plan Day", "Goals", "Memory", "Voice Mode"])
    st.markdown("---")
    st.write("Today signals")
    st.progress(min(1, s["sleep"] / 8), text=f"Sleep {s['sleep']}h")
    st.progress(min(1, s["focus"] / 100), text=f"Focus {s['focus']}")
    st.progress(min(1, max(0, 1 - (s["screen"] / 12))), text=f"Screen {s['screen']}h")

greeting = "morning" if now.hour < 12 else "afternoon" if now.hour < 18 else "evening"

st.markdown(
    f"""
    <div class="hero">
        <div class="label">Good {greeting}, {s['name']}</div>
        <div style="font-size:2rem;font-weight:800;margin-top:6px;">
            LifeOS is keeping your day calm, clear, and on track.
        </div>
        <div class="small" style="margin-top:8px;">
            AI summary: you are slightly under-slept, focus is strong, and today should prioritize one deep-work block plus one recovery block.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
for col, label, val in [
    (c1, "Sleep", f"{s['sleep']}h"),
    (c2, "Mood", f"{s['mood']}/10"),
    (c3, "Focus", f"{s['focus']}/100"),
    (c4, "Screen Time", f"{s['screen']}h"),
]:
    with col:
        st.markdown(
            f"<div class='glass'><div class='label'>{label}</div><div class='metric'>{val}</div></div>",
            unsafe_allow_html=True,
        )

if mode == "Dashboard":
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("<div class='glass'><h3>Today</h3></div>", unsafe_allow_html=True)
        for item in s["tasks"]:
            st.write(f"• {item['time']} — {item['task']} ({item['status']})")
        st.markdown("<div class='glass' style='margin-top:16px;'><h3>Upcoming events</h3></div>", unsafe_allow_html=True)
        for e in s["events"]:
            st.write(f"• {e['time']} — {e['title']}")
    with right:
        st.markdown("<div class='glass'><h3>Balance engine</h3></div>", unsafe_allow_html=True)
        st.write("• Work is high but acceptable.")
        st.write("• Add a 20-minute walk to reduce stress.")
        st.write("• Keep evening low-stimulation.")
        st.markdown("<div class='glass' style='margin-top:16px;'><h3>Recommended</h3></div>", unsafe_allow_html=True)
        st.write("1. Finish the highest-value task first.")
        st.write("2. Take a break every 90 minutes.")
        st.write("3. End the day with a light review.")

elif mode == "Plan Day":
    st.markdown("<div class='glass'><h3>Optimized schedule</h3></div>", unsafe_allow_html=True)
    schedule = [
        ("08:00", "Wake, hydrate, stretch"),
        ("08:30", "Plan top 3 priorities"),
        ("09:00", "Deep work block"),
        ("10:30", "Short break"),
        ("11:00", "Second focus block"),
        ("13:00", "Lunch and reset"),
        ("18:30", "Workout"),
        ("21:30", "Wind down and sleep prep"),
    ]
    for t, task in schedule:
        st.write(f"• {t} — {task}")

elif mode == "Goals":
    for g in s["goals"]:
        st.markdown(
            f"<div class='glass'><div class='label'>{g['title']}</div><div class='small'>{g['next']}</div></div>",
            unsafe_allow_html=True,
        )
        st.progress(g["progress"] / 100)

elif mode == "Memory":
    st.markdown("<div class='glass'><h3>Personal knowledge</h3></div>", unsafe_allow_html=True)
    for m in s["memory"]:
        st.markdown(f"<span class='chip'>{m}</span>", unsafe_allow_html=True)

else:
    st.markdown(
        "<div class='glass'><h3>Voice assistant</h3><p class='small'>Use voice-style commands like: plan my day, what should I focus on, remind me to rest, reschedule my evening workout.</p></div>",
        unsafe_allow_html=True,
    )
    query = st.text_input("Say something to LifeOS")
    if query:
        st.info(f"LifeOS: I understood '{query}'. I would respond with a calm, action-oriented plan.")# ==========================
# IMPORTS
# ==========================

import streamlit as st
import datetime as dt
import google.generativeai as genai


# ==========================
# AI CONFIG
# ==========================

GEMINI_API_KEY = "YOUR_API_KEY_HERE"

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


# ==========================
# AI FUNCTIONS
# ==========================

def get_lifeos_advice(state):
    prompt = f"""
    You are LifeOS.

    User: {state['name']}

    Sleep: {state['sleep']} hours
    Mood: {state['mood']}/10
    Focus: {state['focus']}/100

    Goals:
    {state['goals']}

    Tasks:
    {state['tasks']}

    Give:
    1. Daily Summary
    2. Top Priority
    3. Health Suggestion
    4. Productivity Suggestion

    Keep it short.
    """

    response = model.generate_content(prompt)
    return response.text


# ==========================
# STREAMLIT CONFIG
# ==========================

st.set_page_config(
    page_title="LifeOS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================
# SESSION STATE
# ==========================

if "state" not in st.session_state:
    st.session_state.state = {
        # your existing data here
    }

s = st.session_state.state


# ==========================
# AI MEMORY
# ==========================

if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = None


# ==========================
# UI
# ==========================

# Hero Section
# Metrics
# Sidebar
# Dashboard


# ==========================
# DASHBOARD MODE
# ==========================

if mode == "Dashboard":

    left, right = st.columns([1.2, 1])

    with left:
        # tasks
        pass

    with right:

        st.markdown("### 🧠 LifeOS Brain")

        if st.button("Generate AI Advice"):
if st.button("Generate AI Advice"):
    st.success("""
🧠 Daily Summary:
Focus levels are good today.

🎯 Top Priority:
Complete your Deep Work Sprint.

💪 Health Suggestion:
Take a 20-minute walk.

⚡ Productivity Tip:
Work in one 90-minute distraction-free block.
""")

# ==========================
# AI CONFIG
# ==========================

GEMINI_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ==========================
# AI FUNCTIONS
# ==========================

def get_lifeos_advice(state):
    prompt = f"""
    You are LifeOS - a calm, supportive AI operating system for personal balance.

    User: {state['name']}

    Sleep: {state['sleep']} hours
    Mood: {state['mood']}/10
    Focus: {state['focus']}/100
    Screen Time: {state['screen']}h
    Work Hours: {state['work_hours']}h
    Exercise: {state['exercise']}min
    Social: {state['social']}h

    Goals:
    {state['goals']}

    Tasks:
    {state['tasks']}

    Events:
    {state['events']}

    Personal Memory:
    {state['memory']}

    Give me:
    1. Daily Summary (2-3 sentences)
    2. Top Priority (1 task)
    3. Health Suggestion (1 short tip)
    4. Productivity Suggestion (1 short tip)

    Keep it short, calm, and action-oriented. Max 150 words.
    """

    response = model.generate_content(prompt)
    return response.text


# ==========================
# STREAMLIT CONFIG
# ==========================

st.set_page_config(
    page_title="LifeOS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================
# CSS STYLING
# ==========================
css = """
<style>
    .stApp {
        background: radial-gradient(circle at top, #1b2340 0%, #0b1020 45%, #060913 100%);
        color: #f4f7fb;
    }
</style>
"""st.markdown(css, unsafe_allow_html=True)

st.markdown("---")
st.subheader("🧠 LifeOS Brain")

if st.button("Generate AI Advice"):
    st.success("AI Brain Connected")
    
            with st.spinner("LifeOS is thinking..."):

                st.session_state.ai_summary = get_lifeos_advice(s)

        if st.session_state.ai_summary:

            st.success(st.session_state.ai_summary)st.markdown("---")
st.subheader("🧠 LifeOS Brain")

if st.button("Generate AI Advice"):
    st.success("AI Brain Connected Successfully")
