import streamlit as st
from openai import OpenAI
import base64

st.set_page_config(page_title="Disease Detector AI", page_icon="🧑‍⚕️")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("🧑‍⚕️ AI Health Diagnosis Assistant")
st.write("Describe your symptoms, upload photo, or speak using microphone.")

# Save messages for history
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {
            "role": "system",
            "content": (
                "You are a medical diagnosis assistant. "
                "When a user provides symptoms or image, respond with:\n"
                "1. Possible diseases with probability\n"
                "2. Causes\n"
                "3. Required tests\n"
                "4. Medicines or home treatment\n"
                "Use simple language."
            ),
        }
    ]

if "messages" not in st.session_state:
    st.session_state.messages = []


# Show messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Photo Upload
uploaded_image = st.file_uploader("📷 Upload a medical photo (rash, wound, eye, skin etc.)", type=["jpg", "jpeg", "png"])

if uploaded_image:
    st.image(uploaded_image, width=250)
    img_bytes = uploaded_image.read()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    st.session_state.conversation.append(
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Analyze this medical image."},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{img_base64}",
                },
            ],
        }
    )

    response = client.responses.create(
        model="gpt-4o-mini",
        messages=st.session_state.conversation
    )

    bot_reply = response.output_text
    with st.chat_message("assistant"):
        st.write(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})


# Voice Input
audio = st.audio_input("🎤 Speak Your Symptoms")

if audio:
    audio_bytes = audio.read()
    with open("audio.wav", "wb") as f:
        f.write(audio_bytes)

    transcript = client.audio.transcriptions.create(
        file=open("audio.wav","rb"),
        model="gpt-4o-mini-tts"
    )

    spoken_text = transcript.text
    with st.chat_message("user"):
        st.write(spoken_text)

    st.session_state.conversation.append({"role": "user", "content": spoken_text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.conversation
    )

    bot_reply = response.choices[0].message.content

    with st.chat_message("assistant"):
        st.write(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})


# Text Input Chat
user_text = st.chat_input("Describe your symptoms")

if user_text:
    with st.chat_message("user"):
        st.write(user_text)

    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.conversation.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.conversation
    )

    bot_reply = response.choices[0].message.content

    with st.chat_message("assistant"):
        st.write(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.session_state.conversation.append({"role": "assistant", "content": bot_reply})


# Clear chat button
if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.session_state.conversation = st.session_state.conversation[:1]
    st.rerun()




