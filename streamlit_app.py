import streamlit as st
from openai import OpenAI
import os

# Get API key from Streamlit Secrets or Environment
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="Disease Bot", page_icon="🧪")
st.title("🧪 Disease Prediction Chatbot")

st.write("Ask me symptoms and I will try to guess possible diseases. (Not a doctor!)")

# Session for chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show old messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Take user input
user_input = st.chat_input("Describe your symptoms...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # AI response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages
    )

    bot_reply = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    with st.chat_message("assistant"):
        st.write(bot_reply)







