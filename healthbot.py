import streamlit as st
from openai import openai

# Initialize client
client = OpenAI(api_key="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")

st.title("🩺 AI Medical Assistant (English + Hinglish)")
st.write("Type your **symptoms** OR upload a **medical report image**.")

# Text input
user_input = st.text_input("👉 Enter your symptoms or greeting here (English/Hinglish):")

# Image upload
uploaded_file = st.file_uploader("📤 Upload your report (JPG/PNG only)", type=["jpg","png","jpeg"])

# Process text input
if user_input:
    response = client.chat.completions.create(
        model="gpt-4o-mini",  
        messages=[
            {"role": "system", "content": "You are a friendly AI doctor. Reply in English or Hinglish. "
                                          "If user enters greetings (hlw, hello, namaste) → reply casually. "
                                          "If user enters symptoms → suggest possible diseases with disclaimer. "
                                          "Always say: '⚠️ Ye AI suggestion hai, doctor ki salah zaroori hai.'"},
            {"role": "user", "content": user_input}
        ]
    )
    st.write("🤖 Bot:", response.choices[0].message.content)

# Process uploaded report image
if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Report", use_column_width=True)
    response = client.chat.completions.create(
        model="gpt-4.1",  # vision-supported model
        messages=[
            {"role": "system", "content": "You are a medical AI. Analyze lab reports and explain in simple English + Hinglish. "
                                          "Always give disclaimer: '⚠️ Ye AI suggestion hai, doctor ki salah zaroori hai.'"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please analyze this medical report."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{uploaded_file.getvalue().decode('latin1')}" }}
                ]
            }
        ]
    )
    st.write("📄 Report Analysis:", response.choices[0].message.content)

