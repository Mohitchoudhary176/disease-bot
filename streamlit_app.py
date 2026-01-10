import streamlit as st
from openai import OpenAI
from PIL import Image
import io

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DiseaseBot", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------- SESSION STATE ----------------
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# ---------------- UI ----------------
st.title("🩺 DiseaseBot AI")
st.write("Describe symptoms or upload an image for possible diagnosis.")

uploaded_image = st.file_uploader(
    "Upload image (optional)",
    type=["jpg", "jpeg", "png"]
)

user_input = st.text_input("Enter symptoms or question")

# ---------------- DISPLAY CHAT HISTORY ----------------
for msg in st.session_state.conversation:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Bot:** {msg['content']}")

# ---------------- PROCESS INPUT ----------------
if st.button("Submit") and (user_input or uploaded_image):

    # Save user message
    if user_input:
        st.session_state.conversation.append({
            "role": "user",
            "content": user_input
        })

    # Prepare OpenAI input
    inputs = [
        {
            "role": "system",
            "content": (
                "You are a medical assistant AI. "
                "Analyze symptoms and images carefully. "
                "Provide possible disease, diagnosis, and advice. "
                "Always say this is not a substitute for a doctor."
            )
        }
    ]

    # Add chat history
    for msg in st.session_state.conversation:
        inputs.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add image if uploaded
    if uploaded_image:
        image_bytes = uploaded_image.read()
        inputs.append({
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_input or "Analyze this image"},
                {
                    "type": "input_image",
                    "image_base64": image_bytes
                }
            ]
        })

    # ---------------- OPENAI CALL ----------------
    response = client.responses.create(
        model="gpt-4o-mini",
        input=inputs
    )

    bot_reply = response.output_text

    # Save bot reply
    st.session_state.conversation.append({
        "role": "assistant",
        "content": bot_reply
    })

    st.rerun()




