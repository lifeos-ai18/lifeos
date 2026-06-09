import streamlit as st
import requests

st.set_page_config(
page_title="LifeOS",
page_icon="🧠",
layout="wide"
)

menu = st.sidebar.radio(
"LifeOS",
["Dashboard", "Colum AI", "Missions"]
)

st.title("🧠 LifeOS")
st.subheader("Powered by Colum AI")

name = st.text_input("Name", "Kavish")
sleep = st.slider("Sleep Hours", 0, 12, 7)
focus = st.slider("Focus %", 0, 100, 60)
mood = st.slider("Mood /10", 0, 10, 7)

life_score = int((sleep * 10 + focus + mood * 10) / 3)

if menu == "Dashboard":

```
st.header("📊 Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Life Score", life_score)

with col2:
    st.metric("Focus", f"{focus}%")

with col3:
    st.metric("Mood", f"{mood}/10")
```

elif menu == "Colum AI":

```
st.header("🤖 Chat with Colum")

prompt = st.text_input("Ask Colum")

if st.button("Send") and prompt:

    context = f"""
    User: {name}
    Sleep: {sleep}
    Focus: {focus}
    Mood: {mood}
    Life Score: {life_score}
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"You are Colum, a Jarvis-like AI.\n\nContext:\n{context}\n\nUser: {prompt}",
                "stream": False,
            },
            timeout=60,
        )

        data = response.json()
        st.success(data["response"])

    except Exception as e:
        st.error(f"Ollama Error: {e}")
```

elif menu == "Missions":

```
st.header("🎯 Missions")

mission = st.text_input("Mission Name")

if st.button("Add Mission"):
    st.success(f"Mission Added: {mission}")
```
