import streamlit as st

st.set_page_config(
    page_title="LifeOS",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 LifeOS")
st.subheader("Your Personal AI Operating System")

name = st.text_input("What's your name?")
goal = st.text_input("What's your biggest goal right now?")

sleep = st.slider("Sleep Hours", 0, 12, 7)
focus = st.slider("Focus Level", 0, 100, 60)
mood = st.slider("Mood", 1, 10, 7)

if st.button("Analyze Me"):
    life_score = int((sleep * 10 + focus + mood * 10) / 3)

    st.success(f"Life Score: {life_score}/100")

    if life_score >= 85:
        st.write("🏆 Rank: A")
    elif life_score >= 70:
        st.write("🥈 Rank: B")
    else:
        st.write("⚠️ Rank: C")

    st.write(f"🎯 Goal: {goal}")
