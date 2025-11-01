import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Disease Detection Bot", page_icon="🧑‍⚕️")

st.title("🧑‍⚕️ Symptom to Disease Detector")
st.write("Describe your symptoms and I will predict possible diseases, causes & advice.")

# SESSION STATE
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {
            "role": "system",
            "content": (
                "You are a medical diagnosis assistant. "
                "Your job is to analyze symptoms, predict possible diseases, "
                "give probability scores, causes, tests, and treatments."
            )
        }
    ]

# SHOW CHAT HISTORY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# USER INPUT
user_input = st.chat_input("Describe your symptoms...")

if user_input:
    # show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # add to conversation for memory
    st.session_state.conversation.append({"role": "user", "content": user_input})

    # AI RESPONSE
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.conversation
        )
        bot_reply = response.choices[0].message["content"]
        st.write(bot_reply)

    # store reply
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.session_state.conversation.append({"role": "assistant", "content": bot_reply})

# CLEAR CHAT BUTTON
if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.session_state.conversation = [
        {
            "role": "system",
            "content": (
                "You are a medical diagnosis assistant. "
                "Your job is to analyze symptoms, predict possible diseases, "
                "give probability scores, causes, tests, and treatments."
            )
        }
    ]
    st.rerun()



