import streamlit as st
from openai import OpenAI
from PIL import Image
import base64, io, os

st.set_page_config(page_title="DiseaseBot", page_icon="🩺")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are a medical assistant. "
                        "Have natural conversation like ChatGPT. "
                        "Ask symptoms, suggest possible diseases, diagnosis, "
                        "and basic guidance. Always say you are not a doctor."
                    )
                }
            ]
        }
    ]

# ---------------- UI ----------------
st.title("🩺 DiseaseBot")
st.caption("AI Health Assistant (Not a Doctor)")

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"][0]["text"])

user_text = st.chat_input("Say hello or describe symptoms")
uploaded_image = st.file_uploader("Upload image (optional)", type=["jpg", "png", "jpeg"])

# ---------------- IMAGE → BASE64 ----------------
def to_base64(file):
    img = Image.open(file).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()

# ---------------- HANDLE INPUT ----------------
if user_text or uploaded_image:

    user_content = []

    if user_text:
        user_content.append({
            "type": "text",
            "text": user_text
        })

    if uploaded_image:
        user_content.append({
            "type": "input_image",
            "image_base64": to_base64(uploaded_image)
        })

    st.session_state.messages.append({
        "role": "user",
        "content": user_content
    })

    with st.chat_message("user"):
        st.markdown(user_text if user_text else "🖼️ Image uploaded")

    response = client.responses.create(
        model="gpt-4o-mini",
        input=st.session_state.messages
    )

    reply = response.output_text

    st.session_state.messages.append({
        "role": "assistant",
        "content": [{"type": "text", "text": reply}]
    })

    with st.chat_message("assistant"):
        st.markdown(reply)



