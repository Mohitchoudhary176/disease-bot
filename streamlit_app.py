import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
import os

# ------------------ CONFIG ------------------
st.set_page_config(page_title="DiseaseBot", page_icon="🩺")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------ SESSION STATE ------------------
if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {
            "role": "system",
            "content": (
                "You are a medical assistant. "
                "Ask symptoms, suggest possible diseases, diagnosis steps, "
                "and basic guidance. Always say this is not a doctor."
            )
        }
    ]

# ------------------ UI ------------------
st.title("🩺 DiseaseBot")
st.caption("AI Health Assistant (Not a Doctor)")

# Show chat history
for msg in st.session_state.conversation:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ------------------ INPUTS ------------------
user_text = st.chat_input("Describe symptoms or ask a health question")
uploaded_image = st.file_uploader("Upload image (optional)", type=["jpg", "jpeg", "png"])

# ------------------ IMAGE → BASE64 ------------------
def image_to_base64(image_file):
    image = Image.open(image_file).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()

# ------------------ HANDLE INPUT ------------------
if user_text or uploaded_image:

    user_content = []

    if user_text:
        user_content.append({"type": "text", "text": user_text})

    if uploaded_image:
        image_b64 = image_to_base64(uploaded_image)
        user_content.append({
            "type": "input_image",
            "image_base64": image_b64
        })

    st.session_state.conversation.append({
        "role": "user",
        "content": user_text if user_text else "Uploaded an image"
    })

    with st.chat_message("user"):
        st.markdown(user_text if user_text else "🖼️ Image uploaded")

    # ------------------ OPENAI CALL ------------------
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[{
            "role": "user",
            "content": user_content
        }]
    )

    bot_reply = response.output_text

    st.session_state.conversation.append({
        "role": "assistant",
        "content": bot_reply
    })

    with st.chat_message("assistant"):
        st.markdown(bot_reply)

