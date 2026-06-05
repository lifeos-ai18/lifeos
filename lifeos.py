import streamlit as st
import datetime as dt
import pandas as pd
import plotly.express as px
st.set_page_config(
    page_title="LifeOS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
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
    padding: 24px 28px;
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
""", unsafe_allow_html=True)

if "state" not in st.session_state:
    st.session_state.state = {
        "profile_set": False,
        "name": "",
        "email": "",
        "sleep": 6.5,
        "mood": 7,
        "focus": 78,
        "screen": 4.2,
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
        "memory": [
            "Prefers calm, minimal plans.",
            "Best focus window: mornings.",
            "Likes supportive reminders.",
        ],
        "last_command": "",
        "agent_reply": "",
        "wearable_connected": False,
        "wearable_source": "",
    }

s = st.session_state.state
now = dt.datetime.now()
greeting = "morning" if now.hour < 12 else "afternoon" if now.hour < 18 else "evening"

def agent_response(command: str) -> str:
    cmd = command.lower().strip()
    who = s["name"] or "there"
    if not cmd:
        return ""
    if any(x in cmd for x in ["plan my day", "plan day", "schedule"]):
        return f"{who}, I mapped a calm day: deep work first, a reset around lunch, and a light evening wind-down."
    if any(x in cmd for x in ["focus", "deep work", "concentrate"]):
        return f"{who}, start one 90-minute distraction-free block now. Put the phone away and finish the hardest task first."
    if any(x in cmd for x in ["rest", "break", "recover", "relax"]):
        return f"{who}, take a 20-minute walk, hydrate, and keep the next block lighter."
    if any(x in cmd for x in ["sleep", "tired", "under-slept"]):
        return f"{who}, protect sleep tonight: reduce screen time, end work earlier, and keep the room calm."
    if any(x in cmd for x in ["goal", "goals"]):
        return f"{who}, your priorities are Health, Deep Work, and Balance. Deep Work looks like the best next win."
    if any(x in cmd for x in ["fridge", "food", "meal"]):
        return f"{who}, I can help plan meals, but fridge data needs an explicit integration. For now I can track meals you enter."
    if any(x in cmd for x in ["wearable", "watch", "health"]):
        return f"{who}, your wearable can be connected through a consent-based integration so I can use sleep and activity data."
    return f"{who}, I heard '{command}'. I suggest turning it into one clear next action."

if "page" not in st.session_state:
    st.session_state.page = "Profile"

with st.sidebar:
    st.markdown("### LifeOS")
    st.caption("Your balanced AI operating system")
    page = st.selectbox("Mode", ["Profile", "Dashboard", "Plan Day", "Goals", "Memory", "Voice Agent", "Integrations"])
    st.session_state.page = page
    st.markdown("---")
    st.write("Today signals")
    st.progress(min(1, s["sleep"] / 8), text=f"Sleep {s['sleep']}h")
    st.progress(min(1, s["focus"] / 100), text=f"Focus {s['focus']}")
    st.progress(min(1, max(0, 1 - (s["screen"] / 12))), text=f"Screen {s['screen']}h")

if st.session_state.page == "Profile" and not s["profile_set"]:
    st.markdown(
        f"""
        <div class="hero">
            <div class="label">Welcome</div>
            <div style="font-size:2rem;font-weight:800;margin-top:6px;">Create your profile to personalize LifeOS.</div>
            <div class="small" style="margin-top:8px;">Enter your details and the app will adapt to you.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", placeholder="Your name")
            email = st.text_input("Email", placeholder="you@example.com")
        with col2:
            sleep = st.slider("Sleep hours", 0.0, 12.0, float(s["sleep"]))
            mood = st.slider("Mood", 1, 10, int(s["mood"]))
            focus = st.slider("Focus", 1, 100, int(s["focus"]))
            screen = st.slider("Screen time", 0.0, 16.0, float(s["screen"]))
        submitted = st.form_submit_button("Save profile")

    if submitted:
        s["name"] = name.strip()
        s["email"] = email.strip()
        s["sleep"] = sleep
        s["mood"] = mood
        s["focus"] = focus
        s["screen"] = screen
        s["profile_set"] = True
        st.success(f"Welcome, {s['name'] or 'user'} — your profile is saved.")
        st.rerun()

else:
    if not s["name"]:
        s["name"] = "user"

    st.markdown(
        f"""
        <div class="hero">
            <div class="label">Heyy, {s['name']}</div>
            <div style="font-size:2rem;font-weight:800;margin-top:6px;">LifeOS is keeping your day calm, clear, and on track.</div>
            <div class="small" style="margin-top:8px;">Personalized AI summary based on your own profile and connected data.</div>
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
            st.markdown(f"<div class='glass'><div class='label'>{label}</div><div class='metric'>{val}</div></div>", unsafe_allow_html=True)

    if s["wearable_connected"]:
        st.success(f"Wearable connected: {s['wearable_source']}")
    else:
        st.info("Wearable not connected yet. Open Integrations to simulate or connect later.")

    if st.session_state.page == "Dashboard":
        left, right = st.columns([1.2, 1])
        with left:
            st.markdown("<div class='glass'><h3>Focus Trend</h3></div>", unsafe_allow_html=True)
            df = pd.DataFrame({
                "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "Focus": [50, 65, 70, 60, 78, 82, 76]
            })
            fig = px.line(df, x="Day", y="Focus", markers=True)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f4f7fb",
                height=320,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<div class='glass' style='margin-top:16px;'><h3>Today</h3></div>", unsafe_allow_html=True)
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

    elif st.session_state.page == "Plan Day":
        st.markdown("<div class='glass'><h3>Optimized Schedule</h3></div>", unsafe_allow_html=True)
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

    elif st.session_state.page == "Goals":
        for g in s["goals"]:
            st.markdown(f"<div class='glass'><div class='label'>{g['title']}</div><div class='small'>{g['next']}</div></div>", unsafe_allow_html=True)
            st.progress(g["progress"] / 100)

    elif st.session_state.page == "Memory":
        st.markdown("<div class='glass'><h3>Personal Knowledge</h3></div>", unsafe_allow_html=True)
        for m in s["memory"]:
            st.markdown(f"<span class='chip'>{m}</span>", unsafe_allow_html=True)

    elif st.session_state.page == "Voice Agent":
        st.markdown("<div class='glass'><h3>Voice Agent</h3><p class='small'>Type a voice-style command: plan my day, what should I focus on, remind me to rest, sleep plan, wearable status, fridge meal help.</p></div>", unsafe_allow_html=True)
        command = st.text_input("Enter voice command", placeholder="e.g. plan my day", key="voice_command")
        run = st.button("Run command", type="primary")
        if run and command:
            s["last_command"] = command
            s["agent_reply"] = agent_response(command)
        if s["last_command"]:
            st.info(f"You said: {s['last_command']}")
        if s["agent_reply"]:
            st.success(s["agent_reply"])

    elif st.session_state.page == "Integrations":
        st.markdown("<div class='glass'><h3>Integrations</h3></div>", unsafe_allow_html=True)
        st.write("Wearable and phone data should be connected through user consent and external providers.")
        provider = st.selectbox("Wearable source", ["None", "Apple Health", "Fitbit", "Garmin", "Oura", "Whoop", "Terra API Demo"])
        if st.button("Connect wearable"):
            if provider != "None":
                s["wearable_connected"] = True
                s["wearable_source"] = provider
                st.success(f"Connected to {provider}.")
            else:
                st.warning("Choose a source first.")

        st.markdown("<div class='glass' style='margin-top:16px;'><h3>User data hooks</h3></div>", unsafe_allow_html=True)
        st.write("• Calendar sync placeholder")
        st.write("• Sleep and activity placeholder")
        st.write("• Meal/fridge input placeholder")
        st.write("• Phone activity summary placeholder")

    st.markdown("---")
    st.subheader("🧠 LifeOS Brain")

    if st.button("Generate AI Advice", type="primary"):
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

    life_score = (s["mood"] * 10 + s["focus"] + s["sleep"] * 10) / 3

    st.title("🧠 LifeOS")
    st.metric("🔥 Life Score", round(life_score))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚡ Focus", s["focus"])
    with col2:
        st.metric("😊 Mood", s["mood"])
    with col3:
        st.metric("😴 Sleep", s["sleep"])
