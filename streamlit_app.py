import streamlit as st
from openai import OpenAI
import os

st.set_page_config(page_title="Health Bot", layout="centered")

# Load API Key from Streamlit Secrets
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


st.title("💊 AI Health Assistant")
st.write("Describe your symptoms or ask any health question.")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
user_input = st.chat_input("Enter your symptoms or question...")

if user_input:
    # Add user message to chat history
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    # Generate AI response
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant that replies in simple language."},
            *[
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state["messages"]
            ],
        ]
    )

    bot_reply = response.choices[0].message["content"]

    # Add bot message to history
    st.session_state["messages"].append({"role": "assistant", "content": bot_reply})

    # Display bot reply
    with st.chat_message("assistant"):
        st.write(bot_reply)













