import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

st.title("Disease Bot")
st.write("Ask anything related to symptoms or diseases. (Educational info only)")

# ✅ Initialize chat history in session_state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a medical helper. Provide safe, helpful, non-diagnostic advice."}
    ]

# ✅ Show chat history on screen
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.write(f"🧑 **You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.write(f"🤖 **Bot:** {msg['content']}")

# User input box
user_input = st.text_input("Type your question:")

# ✅ When user submits
if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        # Call OpenAI with full conversation history
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )

        bot_reply = response.choices[0].message.content

        # Add bot reply to history
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        # Show immediately
        st.write(f"🤖 **Bot:** {bot_reply}")

    except Exception as e:
        st.error("Error contacting OpenAI API")
        st.exception(e)
