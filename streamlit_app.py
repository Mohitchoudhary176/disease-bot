import streamlit as st
from openai import OpenAI
import os

st.set_page_config(page_title="DiseaseBot", page_icon="🩺")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------- SESSION MEMORY --------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a medical assistant. "
                "Talk naturally like ChatGPT. "
                "Ask symptoms, suggest possible diseases, "
                "basic diagnosis and guidance. "
                "Always say you are not a doctor."
            )
        }
    ]

# -------- UI --------
st.title("🩺 DiseaseBot")
st.caption("AI Health Assistant (Not a Doctor)")

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

user_input = st.chat_input("Say hello or describe symptoms")

# -------- CHAT LOGIC --------
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages
    )

    reply = response.choices[0].message.content

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    with st.chat_message("assistant"):
        st.markdown(reply)





